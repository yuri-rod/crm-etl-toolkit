#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unified CRM Lead Quality Pipeline
Combines ETL, ML Training, and Inference capabilities
"""

import pandas as pd
import numpy as np
import joblib
import json
import argparse
import logging
from datetime import datetime
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
    Unified pipeline for CRM lead quality prediction
    Handles ETL, training, and inference
    """
    
    def __init__(self, model_dir: str = './production_models/'):
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(exist_ok=True)
        
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
        ]
    
    def extract_and_transform_data(self, file_path: str, target_column: str = None) -> pd.DataFrame:
        """
        ETL: Extract data from CSV and apply transformations
        """
        logger.info(f"Loading data from {file_path}")
        
        try:
            # Load CSV
            df = pd.read_csv(file_path, encoding='utf-8')
            logger.info(f"Loaded {len(df)} records")
            
            # Basic data validation
            required_cols = ['nome', 'empresa_cargo', 'segmento', 'cidade_estado']
            missing_cols = [col for col in required_cols if col not in df.columns]
            if missing_cols:
                raise ValueError(f"Missing required columns: {missing_cols}")
            
            # Apply feature engineering
            df = self._engineer_features(df)
            
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
            
            logger.info("Feature engineering completed successfully")
            return df
            
        except Exception as e:
            logger.error(f"Error in ETL process: {e}")
            raise
    
    def _engineer_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Apply feature engineering transformations
        """
        df = df.copy()
        
        # Fill missing values
        string_cols = df.select_dtypes(include=['object']).columns
        for col in string_cols:
            df[col] = df[col].fillna('').astype(str)
        
        # Length-based features
        df['nome_length'] = df['nome'].str.len()
        df['empresa_cargo_length'] = df['empresa_cargo'].str.len()
        df['segmento_length'] = df['segmento'].str.len()
        
        # Boolean features based on content
        df['has_linkedin'] = df['linkedin'].str.contains('linkedin', case=False, na=False).astype(int)
        df['has_cnpj'] = (df['cnpj'].astype(str).str.len() > 10).astype(int)
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
        except:
            df['aniversario_mes'] = 0
        
        # Data quality score
        df['data_quality_score'] = (
            df['has_email'] + df['has_whatsapp'] + df['has_linkedin'] +
            (df['nome_length'] > 5).astype(int) +
            (df['segmento_length'] > 3).astype(int)
        )
        
        # Add arquivo_fonte for compatibility
        if 'arquivo_fonte' not in df.columns:
            df['arquivo_fonte'] = 'UNKNOWN'
        
        return df
    
    def _categorize_segment(self, segment: str) -> str:
        """
        Categorize business segments
        """
        segment = str(segment).lower()
        
        if any(word in segment for word in ['tech', 'tecnologia', 'software', 'digital']):
            return 'TECNOLOGIA'
        elif any(word in segment for word in ['constru', 'engenharia', 'obra']):
            return 'CONSTRUCAO'
        elif any(word in segment for word in ['educa', 'ensino', 'escola']):
            return 'EDUCACAO'
        elif any(word in segment for word in ['saude', 'medic', 'hospital']):
            return 'SAUDE'
        elif any(word in segment for word in ['financ', 'invest', 'banco']):
            return 'FINANCAS'
        elif any(word in segment for word in ['comercio', 'venda', 'varejo']):
            return 'COMERCIO'
        else:
            return 'OUTROS'
    
    def prepare_features(self, df: pd.DataFrame, fit_encoders: bool = False) -> np.ndarray:
        """
        Prepare features for ML model
        """
        df_processed = df.copy()
        
        # Apply label encoding
        for col in self.categorical_columns:
            if col in df_processed.columns:
                # Standardize values
                df_processed[col] = df_processed[col].astype(str).str.upper().str.strip()
                df_processed[col] = df_processed[col].replace(['NAN', 'NONE', ''], 'DESCONHECIDO')
                
                if fit_encoders:
                    # Create and fit encoder
                    encoder = LabelEncoder()
                    df_processed[f'{col}_encoded'] = encoder.fit_transform(df_processed[col])
                    self.label_encoders[col] = encoder
                else:
                    # Use existing encoder
                    if col in self.label_encoders:
                        encoder = self.label_encoders[col]
                        # Handle unseen values
                        def safe_transform(value):
                            if value in encoder.classes_:
                                return encoder.transform([value])[0]
                            else:
                                return encoder.transform([encoder.classes_[0]])[0]
                        
                        df_processed[f'{col}_encoded'] = df_processed[col].apply(safe_transform)
                    else:
                        df_processed[f'{col}_encoded'] = 0
        
        # Handle arquivo_fonte_encoded
        if 'arquivo_fonte' in df_processed.columns:
            if fit_encoders:
                if 'arquivo_fonte' not in self.label_encoders:
                    encoder = LabelEncoder()
                    df_processed['arquivo_fonte_encoded'] = encoder.fit_transform(df_processed['arquivo_fonte'])
                    self.label_encoders['arquivo_fonte'] = encoder
            else:
                df_processed['arquivo_fonte_encoded'] = 0
        else:
            df_processed['arquivo_fonte_encoded'] = 0
        
        # Select features
        X = df_processed[self.feature_names].copy()
        
        # Handle missing values and infinities
        X = X.replace([np.inf, -np.inf], np.nan)
        X = X.fillna(0)
        
        return X
    
    def train_model(self, df: pd.DataFrame, target_column: str, 
                   test_size: float = 0.2, optimize_hyperparams: bool = True) -> Dict[str, Any]:
        """
        Train the lead quality prediction model
        """
        logger.info("Starting model training...")
        
        # Prepare features and target
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
        
        # Scale features
        self.scaler = StandardScaler()
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Train model
        if optimize_hyperparams and len(X_train) > 50:
            logger.info("Optimizing hyperparameters...")
            param_grid = {
                'n_estimators': [50, 100, 200],
                'max_depth': [3, 5, 7, None],
                'min_samples_split': [2, 5, 10],
                'class_weight': ['balanced', None]
            }
            
            rf = RandomForestClassifier(random_state=42)
            grid_search = GridSearchCV(
                rf, param_grid, cv=min(5, len(X_train) // 10),
                scoring='roc_auc', n_jobs=-1
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
        y_pred_proba = self.model.predict_proba(X_test_scaled)[:, 1]
        
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
                'parse_csv_data',
                'create_synthetic_features',
                'label_encode_categorical',
                'feature_selection',
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
        
        logger.info(f"\nClassification Report:")
        logger.info(f"\n{classification_report(y_test, y_pred)}")
        
        return {
            'model': self.model,
            'metrics': self.metadata['performance_metrics'],
            'feature_importance': feature_importance
        }
    
    def _save_model_artifacts(self):
        """
        Save all model artifacts to disk
        """
        logger.info(f"Saving model artifacts to {self.model_dir}")
        
        # Save model
        joblib.dump(self.model, self.model_dir / 'trained_model.pkl')
        
        # Save scaler
        joblib.dump(self.scaler, self.model_dir / 'scaler.pkl')
        
        # Save label encoders
        joblib.dump(self.label_encoders, self.model_dir / 'label_encoders.pkl')
        
        # Save metadata
        # Convert label encoders to serializable format
        metadata_copy = self.metadata.copy()
        metadata_copy['label_encoders'] = {}
        for col, encoder in self.label_encoders.items():
            metadata_copy['label_encoders'][col] = encoder.classes_.tolist()
        
        with open(self.model_dir / 'model_metadata.json', 'w', encoding='utf-8') as f:
            json.dump(metadata_copy, f, indent=2, ensure_ascii=False)
        
        logger.info("All artifacts saved successfully")
    
    def load_model_artifacts(self):
        """
        Load trained model artifacts
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
            logger.error(f"Error loading model artifacts: {e}")
            return False
    
    def predict_lead_quality(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Predict lead quality for new data
        """
        if self.model is None:
            if not self.load_model_artifacts():
                raise ValueError("No trained model found. Please train a model first.")
        
        # Prepare features
        X = self.prepare_features(df, fit_encoders=False)
        X_scaled = self.scaler.transform(X)
        
        # Make predictions
        predictions = self.model.predict(X_scaled)
        probabilities = self.model.predict_proba(X_scaled)
        
        # Format results
        results = []
        for i, (pred, proba) in enumerate(zip(predictions, probabilities)):
            quality = "Alta" if pred == 1 else "Baixa"
            confidence = max(proba)
            
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
                result['empresa'] = df.iloc[i]['empresa_cargo']
            
            results.append(result)
        
        return results
    
    def batch_predict(self, input_file: str, output_file: str = None) -> str:
        """
        Process a batch of leads from CSV file
        """
        logger.info(f"Processing batch predictions from {input_file}")
        
        # Load and process data
        df = self.extract_and_transform_data(input_file)
        
        # Make predictions
        results = self.predict_lead_quality(df)
        
        # Create results DataFrame
        results_df = pd.DataFrame(results)
        
        # Merge with original data
        if len(df) == len(results_df):
            output_df = pd.concat([df.reset_index(drop=True), results_df], axis=1)
        else:
            output_df = results_df
        
        # Save results
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"lead_predictions_{timestamp}.csv"
        
        output_df.to_csv(output_file, index=False, encoding='utf-8')
        logger.info(f"Predictions saved to {output_file}")
        
        # Summary
        high_quality_count = sum(1 for r in results if r['quality_prediction'] == 'Alta')
        logger.info(f"Processed {len(results)} leads:")
        logger.info(f"  High Quality: {high_quality_count}")
        logger.info(f"  Low Quality: {len(results) - high_quality_count}")
        
        return output_file


def main():
    """
    Main CLI interface
    """
    parser = argparse.ArgumentParser(description='CRM Lead Quality Pipeline')
    parser.add_argument('mode', choices=['train', 'predict', 'batch'], 
                       help='Operation mode')
    parser.add_argument('--data', required=True, 
                       help='Input CSV file path')
    parser.add_argument('--target', default='qualidade_lead',
                       help='Target column name for training')
    parser.add_argument('--model-dir', default='./production_models/',
                       help='Directory to save/load model artifacts')
    parser.add_argument('--output', help='Output file path for predictions')
    parser.add_argument('--test-size', type=float, default=0.2,
                       help='Test set size for training')
    parser.add_argument('--optimize', action='store_true',
                       help='Optimize hyperparameters during training')
    
    args = parser.parse_args()
    
    # Initialize pipeline
    pipeline = CRMLeadPipeline(model_dir=args.model_dir)
    
    try:
        if args.mode == 'train':
            # Load and transform data
            logger.info("Starting training mode...")
            df = pipeline.extract_and_transform_data(args.data, args.target)
            
            # Train model
            results = pipeline.train_model(
                df, args.target, 
                test_size=args.test_size,
                optimize_hyperparams=args.optimize
            )
            
            logger.info("Training completed successfully!")
            
        elif args.mode == 'predict':
            # Load data and make predictions
            logger.info("Starting prediction mode...")
            df = pipeline.extract_and_transform_data(args.data)
            
            # Make predictions
            results = pipeline.predict_lead_quality(df)
            
            # Display results
            for result in results[:10]:  # Show first 10
                logger.info(f"Lead {result['lead_index']}: "
                          f"{result['quality_prediction']} "
                          f"(confidence: {result['confidence']:.3f})")
            
            if len(results) > 10:
                logger.info(f"... and {len(results) - 10} more leads")
                
        elif args.mode == 'batch':
            # Batch processing
            logger.info("Starting batch processing mode...")
            output_file = pipeline.batch_predict(args.data, args.output)
            logger.info(f"Batch processing completed! Results saved to {output_file}")
    
    except Exception as e:
        logger.error(f"Pipeline error: {e}")
        raise


if __name__ == "__main__":
    main()
