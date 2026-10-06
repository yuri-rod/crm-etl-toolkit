#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple CRM Lead Quality Predictor
Lightweight inference-only version
"""

import pandas as pd
import numpy as np
import joblib
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

class CRMLeadPredictor:
    """
    Lightweight predictor for CRM lead quality
    """
    
    def __init__(self, model_dir: str = './production_models/'):
        self.model_dir = Path(model_dir)
        self.model = None
        self.scaler = None
        self.label_encoders = None
        self.metadata = None
        self.load_artifacts()
    
    def load_artifacts(self):
        """Load all model artifacts"""
        try:
            self.model = joblib.load(self.model_dir / 'trained_model.pkl')
            self.scaler = joblib.load(self.model_dir / 'scaler.pkl')
            self.label_encoders = joblib.load(self.model_dir / 'label_encoders.pkl')
            
            with open(self.model_dir / 'model_metadata.json', 'r', encoding='utf-8') as f:
                self.metadata = json.load(f)
                
            print(f"✅ Model loaded: {self.metadata['model_type']}")
            print(f"   Trained on: {self.metadata['training_date']}")
            print(f"   Features: {len(self.metadata['feature_names'])}")
            
        except Exception as e:
            raise Exception(f"Error loading model artifacts: {e}")
    
    def preprocess_data(self, raw_data: pd.DataFrame) -> pd.DataFrame:
        """Process raw data for prediction"""
        df = raw_data.copy()
        
        # Fill missing values
        string_cols = df.select_dtypes(include=['object']).columns
        for col in string_cols:
            df[col] = df[col].fillna('').astype(str)
        
        # Feature engineering (same as training)
        df['nome_length'] = df['nome'].str.len()
        df['empresa_cargo_length'] = df['empresa_cargo'].str.len()
        df['segmento_length'] = df['segmento'].str.len()
        
        df['has_linkedin'] = df['linkedin'].str.contains('linkedin', case=False, na=False).astype(int)
        df['has_cnpj'] = (df['cnpj'].astype(str).str.len() > 10).astype(int)
        df['has_whatsapp'] = df['whatsapp'].str.contains(r'\+55|55', na=False).astype(int)
        df['has_email'] = df['email'].str.contains('@', na=False).astype(int)
        
        df['estado'] = df['cidade_estado'].str.extract(r'([A-Z]{2})$')
        df['estado'] = df['estado'].fillna('OUTROS')
        
        df['segmento_categoria'] = df['segmento'].apply(self._categorize_segment)
        
        try:
            df['aniversario_mes'] = pd.to_datetime(df['aniversario'], errors='coerce').dt.month
            df['aniversario_mes'] = df['aniversario_mes'].fillna(0).astype(int)
        except:
            df['aniversario_mes'] = 0
        
        df['data_quality_score'] = (
            df['has_email'] + df['has_whatsapp'] + df['has_linkedin'] +
            (df['nome_length'] > 5).astype(int) +
            (df['segmento_length'] > 3).astype(int)
        )
        
        # Apply label encoding
        categorical_columns = ['estado_civil', 'estado', 'segmento_categoria']
        for col in categorical_columns:
            if col in df.columns and col in self.label_encoders:
                df[col] = df[col].astype(str).str.upper().str.strip()
                df[col] = df[col].replace(['NAN', 'NONE', ''], 'DESCONHECIDO')
                
                encoder = self.label_encoders[col]
                def safe_transform(value):
                    if value in encoder.classes_:
                        return encoder.transform([value])[0]
                    else:
                        return encoder.transform([encoder.classes_[0]])[0]
                
                df[f'{col}_encoded'] = df[col].apply(safe_transform)
        
        df['arquivo_fonte_encoded'] = 0
        
        # Select features
        feature_cols = self.metadata['feature_names']
        X = df[feature_cols].copy()
        X = X.replace([np.inf, -np.inf], np.nan).fillna(0)
        
        return X
    
    def _categorize_segment(self, segment: str) -> str:
        """Categorize business segments"""
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
    
    def predict(self, raw_data: pd.DataFrame) -> List[Dict[str, Any]]:
        """Make predictions on raw data"""
        X_processed = self.preprocess_data(raw_data)
        X_scaled = self.scaler.transform(X_processed)
        
        predictions = self.model.predict(X_scaled)
        probabilities = self.model.predict_proba(X_scaled)
        
        results = []
        for i, (pred, proba) in enumerate(zip(predictions, probabilities)):
            quality = "Alta" if pred == 1 else "Baixa"
            confidence = max(proba)
            
            results.append({
                'lead_index': i,
                'quality_prediction': quality,
                'confidence': float(confidence),
                'probability_high_quality': float(proba[1]),
                'probability_low_quality': float(proba[0])
            })
        
        return results

# Quick usage example
if __name__ == "__main__":
    predictor = CRMLeadPredictor()
    
    # Example data
    sample_data = pd.DataFrame({
        'nome': ['João Silva'],
        'empresa_cargo': ['Tech Solutions - CEO'],
        'segmento': ['Tecnologia'],
        'linkedin': ['linkedin.com/in/joao'],
        'cnpj': ['12345678000199'],
        'whatsapp': ['+5511999999999'],
        'email': ['joao@techsolutions.com'],
        'cidade_estado': ['São Paulo - SP'],
        'estado_civil': ['Casado'],
        'aniversario': ['15/05/1985']
    })
    
    predictions = predictor.predict(sample_data)
    
    print("Exemplo de predição:")
    for pred in predictions:
        print(f"Lead {pred['lead_index']}: {pred['quality_prediction']} (confiança: {pred['confidence']:.2f})")