#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unified CRM Lead Quality Pipeline
Combines ETL, ML Training, and Inference capabilities with enhanced data handling and optional API enrichment.
"""

import pandas as pd
import numpy as np
import joblib
import json
import argparse
import logging
import re # For CNPJ cleaning and regex in feature engineering
import requests # For external API calls (CNPJ)
from time import sleep # For API rate limiting
from datetime import datetime, timedelta # For timestamping and date parsing
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any

# ML imports
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score
import warnings
warnings.filterwarnings('ignore')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class CRMLeadPipeline:
    """
    Unified pipeline for CRM lead quality prediction.
    Handles ETL, training, and inference with enhanced data parsing and optional API enrichment.
    """
    
    def __init__(self, model_dir: str = './production_models/', enable_api_calls: bool = False):
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(exist_ok=True)
        self.enable_api_calls = enable_api_calls # Control API calls
        
        # Model artifacts
        self.model = None
        self.scaler = None
        self.label_encoders = {}
        self.metadata = {}
        
        # Feature configuration
        self.categorical_columns = ['estado_civil', 'estado', 'segmento_categoria']
        self.feature_names = [
            'nome_length', 'empresa_cargo_length', 'segmento_length',
            'has_linkedin', 'has_cnpj', 'has_whatsapp', 'has_email',
            'aniversario_mes', 'data_quality_score',
            'estado_civil_encoded', 'estado_encoded', 'segmento_categoria_encoded',
            'arquivo_fonte_encoded'
            # Add potentially new features from API enrichment here if they become common
        ]

        # Enrichment cache
        self.enrichment_cache = {
            'cnpj': {},
            'geocoding': {},
            'linkedin': {} # Placeholder, not implemented in this script
        }
    
    def load_and_parse_data(self, file_path: str) -> pd.DataFrame:
        """
        Loads and parses CRM data from various formats (CSV, XLSX/XLS).
        Handles different CSV separators and single-column data parsing.
        """
        logger.info(f"Loading data from {file_path}")
        
        file_ext = Path(file_path).suffix.lower()
        
        if file_ext == '.csv':
            # Try different separators
            for sep in ['|', ',', ';', '\t']:
                try:
                    df = pd.read_csv(file_path, sep=sep, encoding='utf-8')
                    if len(df.columns) > 1: # Assume success if more than one column is parsed
                        break
                except Exception as e:
                    logger.debug(f"Failed to read CSV with separator '{sep}': {e}")
            # Handle special parsing if all content is in a single column
            if len(df.columns) == 1:
                df = self._parse_single_column_data(df)
                
        elif file_ext in ['.xlsx', '.xls']:
            df = pd.read_excel(file_path)
        else:
            raise ValueError(f"Unsupported file format: {file_ext}")
            
        logger.info(f"Loaded {len(df)} records with {len(df.columns)} columns")
        return df
        
    def _parse_single_column_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Parses data when all content is unexpectedly in a single column, splitting by comma.
        Assumes a specific order of fields.
        """
        records = []
        data_column = df.columns[0]
        
        for idx, row in df.iterrows():
            if pd.notna(row[data_column]):
                data_string = str(row[data_column])
                fields = data_string.split(',')
                
                # Assuming a fixed order as per unified_crm_ml_system.py
                if len(fields) >= 15: # Ensure enough fields for basic lead info
                    record = {
                        'id': fields[0].strip(),
                        'nome': fields[1].strip(),
                        'cpf': fields[2].strip(),
                        'rg': fields[3].strip(),
                        'estado_civil': fields[4].strip(),
                        'nome_cracha': fields[5].strip(),
                        'aniversario': fields[6].strip(),
                        'email': fields[7].strip(),
                        'endereco': fields[8].strip(),
                        'cidade_estado': fields[9].strip(),
                        'whatsapp': fields[10].strip(),
                        'empresa_cargo': fields[11].strip(),
                        'segmento': fields[12].strip(),
                        'linkedin': fields[13].strip(),
                        'cnpj': fields[14].strip(),
                    }
                    records.append(record)
                elif len(fields) > 0: # Basic fallback for partial data if structure isn't fixed
                     logger.warning(f"Row {idx} has fewer than 15 fields, attempting partial parse: {data_string[:50]}...")
                     record = {'id': fields[0].strip() if len(fields) > 0 else '',
                               'nome': fields[1].strip() if len(fields) > 1 else '',
                               'email': fields[7].strip() if len(fields) > 7 else '',
                               'cnpj': fields[14].strip() if len(fields) > 14 else '',
                               'cidade_estado': fields[9].strip() if len(fields) > 9 else '',
                               # ... other fields can be added with checks
                              }
                     records.append(record)

        if not records:
            logger.warning("No records parsed from single column data.")
            return pd.DataFrame() # Return empty DataFrame if no records were extracted
        return pd.DataFrame(records)
        
    def extract_and_transform_data(self, file_path: str, target_column: str = None) -> pd.DataFrame:
        """
        ETL: Extract data from CSV/XLSX and apply transformations, including feature engineering
        and optional API enrichment.
        """
        logger.info(f"Loading data from {file_path}")
        
        try:
            # Load CSV/XLSX using the refined loader
            df = self.load_and_parse_data(file_path)
            logger.info(f"Loaded {len(df)} records")
            
            # Basic data validation for essential columns
            required_cols = ['nome', 'empresa_cargo', 'segmento', 'cidade_estado']
            missing_cols = [col for col in required_cols if col not in df.columns]
            if missing_cols:
                logger.warning(f"Missing required columns for feature engineering: {missing_cols}. Some features may be incomplete.")
                # Attempt to proceed by adding missing columns as empty
                for col in missing_cols:
                    df[col] = ''
            
            # Apply feature engineering
            df = self._engineer_features(df)

            # Apply API enrichment if enabled
            if self.enable_api_calls:
                df = self._enrich_with_apis(df)
            
            # Handle target variable if provided (for training)
            if target_column and target_column in df.columns:
                # Convert target to binary if needed
                if df[target_column].dtype == 'object':
                    unique_vals = df[target_column].unique()
                    logger.info(f"Target variable unique values: {unique_vals}")
                    # Map common quality indicators to binary
                    quality_mapping = {
                        'alta': 1, 'high': 1, 'boa': 1, 'good': 1, 'sim': 1, 'yes': 1,
                        'baixa': 0, 'low': 0, 'ruim': 0, 'bad': 0, 'não': 0, 'no': 0
                    }
                    df[target_column] = df[target_column].str.lower().map(quality_mapping)
                    df[target_column] = df[target_column].fillna(0).astype(int)
            
            logger.info("Feature engineering and enrichment completed successfully")
            return df
            
        except Exception as e:
            logger.error(f"Error in ETL process: {e}")
            raise
    
    def _engineer_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Apply feature engineering transformations.
        This consolidates logic from `crm_pipeline.py` and `unified_crm_ml_system.py`.
        """
        df = df.copy()
        
        # Ensure common columns exist, fill with empty string if not
        for col in ['nome', 'empresa_cargo', 'segmento', 'linkedin', 'cnpj', 'whatsapp', 'email', 'cidade_estado', 'aniversario', 'estado_civil', 'arquivo_fonte']:
            if col not in df.columns:
                df[col] = ''

        # Fill missing values for object columns
        string_cols = df.select_dtypes(include=['object']).columns
        for col in string_cols:
            df[col] = df[col].fillna('').astype(str)
        
        # Length-based features
        df['nome_length'] = df['nome'].str.len()
        df['empresa_cargo_length'] = df['empresa_cargo'].str.len()
        df['segmento_length'] = df['segmento'].str.len()
        
        # Boolean features based on content
        df['has_linkedin'] = df['linkedin'].str.contains('linkedin', case=False, na=False).astype(int)
        df['has_cnpj'] = (df['cnpj'].astype(str).str.replace(r'\D', '', regex=True).str.len() >= 14).astype(int) # Robust CNPJ check
        df['has_whatsapp'] = df['whatsapp'].astype(str).str.contains(r'\+55|55', na=False).astype(int)
        df['has_email'] = df['email'].astype(str).str.contains('@', na=False).astype(int)
        
        # Extract state from cidade_estado
        df['estado'] = df['cidade_estado'].astype(str).str.extract(r'([A-Z]{2})$')
        df['estado'] = df['estado'].fillna('OUTROS')
        
        # Categorize segments
        df['segmento_categoria'] = df['segmento'].apply(self._categorize_segment)
        
        # Extract month from birthday
        try:
            df['aniversario_mes'] = pd.to_datetime(df['aniversario'], errors='coerce').dt.month
            df['aniversario_mes'] = df['aniversario_mes'].fillna(0).astype(int)
        except Exception as e:
            logger.warning(f"Could not parse 'aniversario' column: {e}. Setting to 0.")
            df['aniversario_mes'] = 0
        
        # Data quality score
        df['data_quality_score'] = (
            df['has_email'] + df['has_whatsapp'] + df['has_linkedin'] +
            (df['nome_length'] > 5).astype(int) +
            (df['segmento_length'] > 3).astype(int)
        )
        
        # Add arquivo_fonte for compatibility if not present
        if 'arquivo_fonte' not in df.columns:
            df['arquivo_fonte'] = 'UNKNOWN'
        
        return df
    
    def _categorize_segment(self, segment: str) -> str:
        """
        Categorize business segments.
        """
        segment = str(segment).lower()
        
        segment_mapping = {
            'TECNOLOGIA': ['tech', 'tecnologia', 'software', 'digital'],
            'CONSTRUCAO': ['constru', 'engenharia', 'obra'],
            'EDUCACAO': ['educa', 'ensino', 'escola'],
            'SAUDE': ['saude', 'medic', 'hospital'],
            'FINANCAS': ['financ', 'invest', 'banco'],
            'COMERCIO': ['comercio', 'venda', 'varejo']
        }
        
        for category, keywords in segment_mapping.items():
            if any(keyword in segment for keyword in keywords):
                return category
                
        return 'OUTROS'

    def _enrich_with_apis(self, df: pd.DataFrame) -> pd.DataFrame:
        """Enrich data using external APIs (e.g., CNPJ, Geocoding)."""
        logger.info("Starting API enrichment...")
        
        # Ensure new columns exist for API enrichment results
        for col in ['empresa_porte', 'empresa_situacao']:
            if col not in df.columns:
                df[col] = '' # Initialize with empty string

        for idx, row in df.iterrows():
            cnpj_raw = row.get('cnpj')
            if pd.notna(cnpj_raw) and str(cnpj_raw).strip() != '':
                cnpj_info = self._get_cnpj_info(cnpj_raw) # Use existing cache logic
                if cnpj_info.get('is_valid'):
                    df.loc[idx, 'empresa_porte'] = cnpj_info.get('porte', '')
                    df.loc[idx, 'empresa_situacao'] = cnpj_info.get('situacao', '')
        
        logger.info("API enrichment completed.")
        return df
        
    def _get_cnpj_info(self, cnpj: str) -> Dict:
        """
        Fetches CNPJ information from ReceitaWS API, with caching and rate limiting.
        """
        cnpj_clean = re.sub(r'\D', '', str(cnpj))
        
        if cnpj_clean in self.enrichment_cache['cnpj']:
            logger.debug(f"CNPJ {cnpj_clean} found in cache.")
            return self.enrichment_cache['cnpj'][cnpj_clean]
            
        # Basic validation for CNPJ length before calling API
        if len(cnpj_clean) != 14:
            logger.warning(f"Invalid CNPJ format for API call: {cnpj_clean}")
            return {'is_valid': False}

        try:
            sleep(0.5)  # Rate limiting for public API
            url = f"https://www.receitaws.com.br/v1/cnpj/{cnpj_clean}"
            response = requests.get(url, timeout=10)
            response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
            
            data = response.json()
            # Check if API returned an error
            if data.get('status') == 'ERROR':
                logger.warning(f"CNPJ API error for {cnpj_clean}: {data.get('message')}")
                result = {'is_valid': False, 'message': data.get('message')}
            else:
                result = {
                    'is_valid': True,
                    'porte': data.get('porte', ''),
                    'situacao': data.get('situacao', ''),
                    'nome_fantasia': data.get('fantasia', data.get('nome', '')), # Prioritize fantasia
                    'capital_social': data.get('capital_social', '')
                }
            self.enrichment_cache['cnpj'][cnpj_clean] = result
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error calling CNPJ API for {cnpj_clean}: {e}")
            self.enrichment_cache['cnpj'][cnpj_clean] = {'is_valid': False, 'error': str(e)}
            return {'is_valid': False}
        except json.JSONDecodeError:
            logger.error(f"Failed to decode JSON from CNPJ API for {cnpj_clean}. Response: {response.text[:100]}...")
            self.enrichment_cache['cnpj'][cnpj_clean] = {'is_valid': False, 'error': 'JSON decode error'}
            return {'is_valid': False}
        except Exception as e:
            logger.error(f"Unexpected error in CNPJ API call for {cnpj_clean}: {e}")
            self.enrichment_cache['cnpj'][cnpj_clean] = {'is_valid': False, 'error': str(e)}
            return {'is_valid': False}
        
    def prepare_features(self, df: pd.DataFrame, fit_encoders: bool = False) -> pd.DataFrame:
        """
        Prepare features for ML model, including label encoding and scaling.
        Ensures consistency between training and inference.
        """
        df_processed = df.copy()
        
        # Apply label encoding for defined categorical columns
        for col in self.categorical_columns:
            if col in df_processed.columns:
                # Standardize values
                df_processed[col] = df_processed[col].astype(str).str.upper().str.strip()
                df_processed[col] = df_processed[col].replace(['NAN', 'NONE', ''], 'DESCONHECIDO')
                
                if fit_encoders:
                    # Create and fit encoder during training
                    encoder = LabelEncoder()
                    df_processed[f'{col}_encoded'] = encoder.fit_transform(df_processed[col])
                    self.label_encoders[col] = encoder
                else:
                    # Use existing encoder for inference
                    if col in self.label_encoders:
                        encoder = self.label_encoders[col]
                        # Handle unseen values during inference
                        def safe_transform(value):
                            if value in encoder.classes_:
                                return encoder.transform([value])[0]
                            else:
                                # Map unseen values to a default (e.g., the first class or a specific 'unseen' class)
                                # Using first class as a common practice, but consider a dedicated 'unseen' category if appropriate
                                return encoder.transform([encoder.classes_[0]])[0] 
                        
                        df_processed[f'{col}_encoded'] = df_processed[col].apply(safe_transform)
                    else:
                        # If encoder for a column is missing during inference, default to 0
                        logger.warning(f"Label encoder for '{col}' not found during inference. Setting '{col}_encoded' to 0.")
                        df_processed[f'{col}_encoded'] = 0
        
        # Handle 'arquivo_fonte_encoded' specifically
        if 'arquivo_fonte' in df_processed.columns:
            if fit_encoders:
                if 'arquivo_fonte' not in self.label_encoders:
                    encoder = LabelEncoder()
                    df_processed['arquivo_fonte_encoded'] = encoder.fit_transform(df_processed['arquivo_fonte'])
                    self.label_encoders['arquivo_fonte'] = encoder
                else: # If already exists but fit_encoders is true, re-fit
                    encoder = self.label_encoders['arquivo_fonte']
                    df_processed['arquivo_fonte_encoded'] = encoder.fit_transform(df_processed['arquivo_fonte'])
            else:
                if 'arquivo_fonte' in self.label_encoders:
                    encoder = self.label_encoders['arquivo_fonte']
                    def safe_transform_af(value):
                        if value in encoder.classes_:
                            return encoder.transform([value])[0]
                        else:
                            return encoder.transform([encoder.classes_[0]])[0]
                    df_processed['arquivo_fonte_encoded'] = df_processed['arquivo_fonte'].apply(safe_transform_af)
                else:
                    df_processed['arquivo_fonte_encoded'] = 0 # Default if no encoder for arquivo_fonte
        else:
            df_processed['arquivo_fonte_encoded'] = 0
        
        # Select features based on `self.feature_names`
        # Ensure all feature columns exist, fill with 0 if missing (e.g., new API enrichment features)
        for feature in self.feature_names:
            if feature not in df_processed.columns:
                df_processed[feature] = 0 # Default missing features to 0
                logger.warning(f"Feature '{feature}' was missing and imputed with 0.")

        X = df_processed[self.feature_names].copy()
        
        # Handle missing values and infinities for numerical features
        X = X.replace([np.inf, -np.inf], np.nan)
        X = X.fillna(0) # Fill NaNs with 0 after feature engineering and encoding

        return X
    
    def train_model(self, df: pd.DataFrame, target_column: str, 
                   test_size: float = 0.2, optimize_hyperparams: bool = True) -> Dict[str, Any]:
        """
        Train the lead quality prediction model.
        Includes data splitting, scaling, model training (with optional hyperparameter optimization),
        and evaluation.
        """
        logger.info("Starting model training...")
        
        # Prepare features and target. `fit_encoders=True` to learn transformations
        X = self.prepare_features(df, fit_encoders=True)
        
        if target_column not in df.columns:
            raise ValueError(f"Target column '{target_column}' not found in data")
        
        y = df[target_column].astype(int)
        
        logger.info(f"Features shape: {X.shape}")
        logger.info(f"Target distribution: {y.value_counts().to_dict()}")
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42, stratify=y
        )
        
        # Scale features. `fit_transform` on train, `transform` on test
        self.scaler = StandardScaler()
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Train model
        if optimize_hyperparams and len(X_train) > 50: # Only optimize if enough data
            logger.info("Optimizing hyperparameters...")
            param_grid = {
                'n_estimators': [50, 100, 200],
                'max_depth': [3, 5, 7, None],
                'min_samples_split': [2, 5, 10],
                'class_weight': ['balanced', None]
            }
            
            rf = RandomForestClassifier(random_state=42)
            grid_search = GridSearchCV(
                rf, param_grid, cv=min(5, len(X_train) // 10), # Cross-validation folds
                scoring='roc_auc', n_jobs=-1 # Use ROC AUC for scoring
            )
            
            grid_search.fit(X_train_scaled, y_train)
            self.model = grid_search.best_estimator_
            best_params = grid_search.best_params_
            logger.info(f"Best parameters: {best_params}")
        else:
            logger.info("Training with default parameters...")
            self.model = RandomForestClassifier(
                n_estimators=100, max_depth=5, class_weight='balanced', random_state=42
            )
            self.model.fit(X_train_scaled, y_train)
            best_params = self.model.get_params()
        
        # Evaluate model
        train_score = self.model.score(X_train_scaled, y_train)
        test_score = self.model.score(X_test_scaled, y_test)
        
        # Cross validation
        cv_scores = cross_val_score(self.model, X_train_scaled, y_train, cv=5)
        
        # Predictions for detailed metrics
        y_pred = self.model.predict(X_test_scaled)
        y_pred_proba = self.model.predict_proba(X_test_scaled)[:, 1] # Probability of positive class
        
        # Calculate metrics
        auc_score = roc_auc_score(y_test, y_pred_proba)
        
        # Feature importance
        feature_importance = dict(zip(self.feature_names, self.model.feature_importances_))
        feature_importance = dict(sorted(feature_importance.items(), key=lambda x: x[1], reverse=True))
        
        # Store metadata
        self.metadata = {
            'model_type': 'RandomForest',
            'model_params': best_params,
            'feature_names': self.feature_names,
            'training_date': datetime.now().isoformat(),
            'training_samples': len(df),
            'feature_count': len(self.feature_names),
            'target_classes': [0, 1],
            'data_processing_steps': [
                'load_and_parse_data', # New consolidated step
                'create_synthetic_features',
                'api_enrichment_optional', # New step
                'label_encode_categorical',
                'feature_selection_implicit', # No explicit feature selection other than `self.feature_names`
                'standard_scaling'
            ],
            'performance_metrics': {
                'train_accuracy': float(train_score),
                'test_accuracy': float(test_score),
                'cv_mean': float(cv_scores.mean()),
                'cv_std': float(cv_scores.std()),
                'auc_score': float(auc_score)
            },
            'feature_importance': feature_importance
        }
        
        # Save model artifacts
        self._save_model_artifacts()
        
        # Print results
        logger.info("="*50)
        logger.info("MODEL TRAINING RESULTS")
        logger.info("="*50)
        logger.info(f"Training Accuracy: {train_score:.3f}")
        logger.info(f"Test Accuracy: {test_score:.3f}")
        logger.info(f"Cross-validation: {cv_scores.mean():.3f} ± {cv_scores.std():.3f}")
        logger.info(f"AUC Score: {auc_score:.3f}")
        logger.info("\nTop 5 Important Features:")
        for feature, importance in list(feature_importance.items())[:5]:
            logger.info(f"  {feature}: {importance:.3f}")
        
        logger.info(f"\nClassification Report:\n{classification_report(y_test, y_pred)}") # Corrected formatting
        
        return {
            'model': self.model,
            'metrics': self.metadata['performance_metrics'],
            'feature_importance': feature_importance
        }
    
    def _save_model_artifacts(self):
        """
        Save all model artifacts (model, scaler, label encoders, metadata) to disk.
        """
        logger.info(f"Saving model artifacts to {self.model_dir}")
        
        # Save model
        joblib.dump(self.model, self.model_dir / 'trained_model.pkl')
        
        # Save scaler
        joblib.dump(self.scaler, self.model_dir / 'scaler.pkl')
        
        # Save label encoders
        joblib.dump(self.label_encoders, self.model_dir / 'label_encoders.pkl')
        
        # Save metadata
        # Convert label encoders to serializable format (list of classes)
        metadata_copy = self.metadata.copy()
        metadata_copy['label_encoders_classes'] = {} # Renamed key to be explicit
        for col, encoder in self.label_encoders.items():
            metadata_copy['label_encoders_classes'][col] = encoder.classes_.tolist()
        
        with open(self.model_dir / 'model_metadata.json', 'w', encoding='utf-8') as f:
            json.dump(metadata_copy, f, indent=2, ensure_ascii=False)
        
        logger.info("All artifacts saved successfully")
    
    def load_model_artifacts(self):
        """
        Load trained model artifacts (model, scaler, label encoders, metadata).
        """
        try:
            self.model = joblib.load(self.model_dir / 'trained_model.pkl')
            self.scaler = joblib.load(self.model_dir / 'scaler.pkl')
            self.label_encoders = joblib.load(self.model_dir / 'label_encoders.pkl')
            
            with open(self.model_dir / 'model_metadata.json', 'r', encoding='utf-8') as f:
                self.metadata = json.load(f)
            
            logger.info(f"✅ Model loaded: {self.metadata['model_type']}")
            logger.info(f"   Trained on: {self.metadata['training_date']}")
            logger.info(f"   Features: {len(self.metadata['feature_names'])}")
            return True
            
        except Exception as e:
            logger.error(f"Error loading model artifacts: {e}. Please ensure a model has been trained and saved correctly.")
            self.model = None
            self.scaler = None
            self.label_encoders = {}
            self.metadata = {}
            return False
    
    def predict_lead_quality(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Predict lead quality for new data.
        Automatically loads model artifacts if not already loaded.
        """
        if self.model is None:
            if not self.load_model_artifacts():
                raise ValueError("No trained model found. Please train a model first or ensure artifacts exist.")
        
        # Prepare features for prediction. `fit_encoders=False` to use learned transformations
        X = self.prepare_features(df, fit_encoders=False)
        
        # Ensure the feature columns match those the model was trained on
        if set(X.columns) != set(self.metadata['feature_names']):
            logger.warning("Feature columns in input data do not exactly match features used for training. "
                           "Attempting to align, but results might be affected.")
            # Reindex X to match the order and presence of features from metadata
            X = X.reindex(columns=self.metadata['feature_names'], fill_value=0)

        X_scaled = self.scaler.transform(X)
        
        # Make predictions
        predictions = self.model.predict(X_scaled)
        probabilities = self.model.predict_proba(X_scaled)
        
        # Format results
        results = []
        for i, (pred, proba) in enumerate(zip(predictions, probabilities)):
            quality = "Alta" if pred == 1 else "Baixa"
            confidence = max(proba) # Confidence of the predicted class
            
            result = {
                'lead_index': i,
                'quality_prediction': quality,
                'confidence': float(confidence),
                'probability_high_quality': float(proba[1]),
                'probability_low_quality': float(proba[0])
            }
            
            # Add lead info if available
            if 'nome' in df.columns and i < len(df):
                result['nome'] = df.iloc[i]['nome']
            if 'empresa_cargo' in df.columns and i < len(df):
                result['empresa_cargo'] = df.iloc[i]['empresa_cargo'] # Changed 'empresa' to 'empresa_cargo' for consistency
            if 'email' in df.columns and i < len(df): # Add email for better identification
                result['email'] = df.iloc[i]['email']
            
            results.append(result)
        
        return results
    
    def batch_predict(self, input_file: str, output_file: str = None) -> str:
        """
        Processes a batch of leads from a CSV/XLSX file and saves predictions.
        """
        logger.info(f"Processing batch predictions from {input_file}")
        
        # Load and process data, without a target column
        df = self.extract_and_transform_data(input_file, target_column=None)
        
        if df.empty:
            logger.warning(f"No valid data found in '{input_file}' for batch prediction.")
            return None

        # Make predictions
        results = self.predict_lead_quality(df)
        
        # Create results DataFrame
        results_df = pd.DataFrame(results)
        
        # Merge with original data to keep all input columns plus predictions
        # Use a common index to ensure correct merging
        output_df = df.reset_index(drop=True).merge(results_df, left_index=True, right_on='lead_index', how='left')
        output_df = output_df.drop(columns=['lead_index']) # Drop redundant index column
        
        # Save results
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"lead_predictions_{timestamp}.csv"
        
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True) # Ensure output directory exists
        
        output_df.to_csv(output_path, index=False, encoding='utf-8-sig') # Use utf-8-sig for better Excel compatibility
        logger.info(f"Predictions saved to '{output_path}'.")
        
        # Summary
        high_quality_count = sum(1 for r in results if r['quality_prediction'] == 'Alta')
        logger.info(f"Processed {len(results)} leads:")
        logger.info(f"  High Quality: {high_quality_count}")
        logger.info(f"  Low Quality: {len(results) - high_quality_count}")
        
        return str(output_path)


def main():
    """
    Main CLI interface for the CRM Lead Quality Pipeline.
    """
    parser = argparse.ArgumentParser(description='Unified CRM Lead Quality Pipeline')
    parser.add_argument('mode', choices=['train', 'predict', 'batch'], 
                       help='Operation mode: "train" a new model, "predict" a single lead (for demo/testing), or "batch" process a file.')
    parser.add_argument('--data', required=True, 
                       help='Input CSV/XLSX file path for training or prediction.')
    parser.add_argument('--target', default='qualidade_lead',
                       help='Target column name for training (e.g., "qualidade_lead"). Only relevant for "train" mode.')
    parser.add_argument('--model-dir', default='./production_models/',
                       help='Directory to save/load model artifacts (default: ./production_models/).')
    parser.add_argument('--output', 
                       help='Output file path for batch predictions (default: lead_predictions_TIMESTAMP.csv). Only relevant for "batch" mode.')
    parser.add_argument('--test-size', type=float, default=0.2,
                       help='Test set size for training (default: 0.2). Only relevant for "train" mode.')
    parser.add_argument('--optimize', action='store_true',
                       help='Enable hyperparameter optimization during training. Only relevant for "train" mode.')
    parser.add_argument('--enable-api-enrichment', action='store_true',
                       help='Enable external API calls for data enrichment (e.g., CNPJ info).')
    
    args = parser.parse_args()
    
    # Initialize pipeline with API enrichment flag
    pipeline = CRMLeadPipeline(model_dir=args.model_dir, enable_api_calls=args.enable_api_enrichment)
    
    try:
        if args.mode == 'train':
            logger.info("Starting training mode...")
            df = pipeline.extract_and_transform_data(args.data, args.target)
            
            # Ensure target column has variation for training
            if df[args.target].nunique() < 2:
                raise ValueError(f"Target column '{args.target}' has less than 2 unique classes after processing. Cannot train a classifier.")

            results = pipeline.train_model(
                df, args.target, 
                test_size=args.test_size,
                optimize_hyperparams=args.optimize
            )
            logger.info("Training completed successfully!")
            
        elif args.mode == 'predict':
            logger.info("Starting single prediction mode (for demonstration)...")
            # For a single prediction, we might want to pass a small DataFrame
            # For simplicity, if --data points to a file, we will load the first row for demo.
            # In a real API, you'd likely get a JSON payload for a single lead.
            df = pipeline.load_and_parse_data(args.data) # Load the whole file first for extraction
            if df.empty:
                logger.error("No data found for single prediction.")
                return
            
            sample_lead_df = df.head(1) # Take the first lead for a "single" prediction demo
            logger.info(f"Predicting for sample lead: {sample_lead_df.to_dict('records')[0]}")

            predictions = pipeline.predict_lead_quality(sample_lead_df)
            
            if predictions:
                for result in predictions: # Only one result for single prediction
                    logger.info(f"Lead Prediction: {result['quality_prediction']} "
                               f"(confidence: {result['confidence']:.3f})")
                    if 'nome' in result:
                        logger.info(f"  Name: {result['nome']}")
                    if 'empresa_cargo' in result:
                        logger.info(f"  Company/Role: {result['empresa_cargo']}")
                    if 'email' in result:
                        logger.info(f"  Email: {result['email']}")
            else:
                logger.info("No prediction results for the sample lead.")
                
        elif args.mode == 'batch':
            logger.info("Starting batch processing mode...")
            output_file = pipeline.batch_predict(args.data, args.output)
            if output_file:
                logger.info(f"Batch processing completed! Results saved to '{output_file}'")
            else:
                logger.warning("Batch processing finished, but no output file was generated.")
    
    except Exception as e:
        logger.exception(f"Pipeline error: {e}") # Use logger.exception to log traceback


if __name__ == "__main__":
    main()