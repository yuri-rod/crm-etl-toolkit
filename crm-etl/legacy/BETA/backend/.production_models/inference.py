
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de Inferência para Produção
Utiliza modelo treinado para fazer predições em novos dados
"""

import pandas as pd
import numpy as np
import joblib
import json
from datetime import datetime

class CRMLeadPredictor:
    """
    Classe para predição de qualidade de leads do CRM
    """
    
    def __init__(self, model_dir='./production_models/'):
        self.model_dir = model_dir
        self.model = None
        self.scaler = None
        self.label_encoders = None
        self.metadata = None
        self.load_artifacts()
    
    def load_artifacts(self):
        """Carrega todos os artefatos do modelo"""
        try:
            # Carrega modelo
            self.model = joblib.load(f"{self.model_dir}trained_model.pkl")
            
            # Carrega scaler
            self.scaler = joblib.load(f"{self.model_dir}scaler.pkl")
            
            # Carrega encoders
            self.label_encoders = joblib.load(f"{self.model_dir}label_encoders.pkl")
            
            # Carrega metadados
            with open(f"{self.model_dir}model_metadata.json", 'r', encoding='utf-8') as f:
                self.metadata = json.load(f)
                
            print(f"✅ Modelo carregado: {self.metadata['model_type']}")
            print(f"   Treinado em: {self.metadata['training_date']}")
            print(f"   Features: {len(self.metadata['feature_names'])}")
            
        except Exception as e:
            raise Exception(f"Erro ao carregar artefatos: {e}")
    
    def preprocess_data(self, raw_data):
        """Processa dados brutos para formato esperado pelo modelo"""
        df = raw_data.copy()
        
        # Recria features sintéticas (mesmo processo do treinamento)
        df['nome_length'] = df['nome'].astype(str).str.len()
        df['empresa_cargo_length'] = df['empresa_cargo'].astype(str).str.len()
        df['segmento_length'] = df['segmento'].astype(str).str.len()
        
        df['has_linkedin'] = df['linkedin'].astype(str).str.contains('linkedin', case=False, na=False).astype(int)
        df['has_cnpj'] = (df['cnpj'].astype(str).str.len() > 10).astype(int)
        df['has_whatsapp'] = df['whatsapp'].astype(str).str.contains(r'\+55|55', na=False).astype(int)
        df['has_email'] = df['email'].astype(str).str.contains('@', na=False).astype(int)
        
        df['estado'] = df['cidade_estado'].astype(str).str.extract(r'([A-Z]{2})$')
        df['estado'] = df['estado'].fillna('OUTROS')
        
        # Categoriza segmento
        def categorize_segment(segment):
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
        
        df['segmento_categoria'] = df['segmento'].apply(categorize_segment)
        
        try:
            df['aniversario_mes'] = pd.to_datetime(df['aniversario'], errors='coerce').dt.month
            df['aniversario_mes'] = df['aniversario_mes'].fillna(0).astype(int)
        except:
            df['aniversario_mes'] = 0
        
        df['data_quality_score'] = (
            df['has_email'] + 
            df['has_whatsapp'] + 
            df['has_linkedin'] + 
            (df['nome_length'] > 5).astype(int) +
            (df['segmento_length'] > 3).astype(int)
        )
        
        # Aplica label encoding
        categorical_columns = ['estado_civil', 'estado', 'segmento_categoria']
        
        for col in categorical_columns:
            if col in df.columns and col in self.label_encoders:
                # Padroniza valores
                df[col] = df[col].astype(str).str.upper().str.strip()
                df[col] = df[col].replace(['NAN', 'NONE', ''], 'DESCONHECIDO')
                
                # Aplica encoding
                encoder = self.label_encoders[col]
                
                # Trata valores não vistos durante o treinamento
                def safe_transform(value):
                    if value in encoder.classes_:
                        return encoder.transform([value])[0]
                    else:
                        # Usa a primeira classe como padrão
                        return encoder.transform([encoder.classes_[0]])[0]
                
                df[f'{col}_encoded'] = df[col].apply(safe_transform)
        
        # Adiciona arquivo_fonte_encoded (sempre 0 para novos dados)
        df['arquivo_fonte_encoded'] = 0
        
        # Seleciona apenas as features esperadas pelo modelo
        feature_cols = self.metadata['feature_names']
        X = df[feature_cols].copy()
        
        # Remove valores infinitos e NaN
        X = X.replace([np.inf, -np.inf], np.nan)
        X = X.fillna(0)
        
        return X
    
    def predict(self, raw_data, return_proba=False):
        """Faz predição para novos dados"""
        # Preprocessa dados
        X_processed = self.preprocess_data(raw_data)
        
        # Normaliza
        X_scaled = self.scaler.transform(X_processed)
        
        # Predição
        if return_proba:
            predictions = self.model.predict_proba(X_scaled)
            return predictions
        else:
            predictions = self.model.predict(X_scaled)
            return predictions
    
    def predict_lead_quality(self, raw_data):
        """Prediz qualidade do lead com interpretação"""
        probabilities = self.predict(raw_data, return_proba=True)
        predictions = self.predict(raw_data, return_proba=False)
        
        results = []
        for i, (pred, proba) in enumerate(zip(predictions, probabilities)):
            quality = "Alta" if pred == 1 else "Baixa"
            confidence = max(proba)
            
            results.append({
                'lead_index': i,
                'quality_prediction': quality,
                'confidence': confidence,
                'probability_high_quality': proba[1],
                'probability_low_quality': proba[0]
            })
        
        return results

# Exemplo de uso
if __name__ == "__main__":
    # Inicializa preditor
    predictor = CRMLeadPredictor()
    
    # Exemplo de dados novos
    new_data = pd.DataFrame({
        'nome': ['João Silva'],
        'empresa_cargo': ['Tech Solutions - CEO'],
        'segmento': ['Tecnologia'],
        'linkedin': ['linkedin.com/in/joao'],
        'cnpj': ['12345678000199'],
        'whatsapp': ['+5511999999999'],
        'email': ['joao@techsolutions.com'],
        'cidade_estado': ['São Paulo - SP'],
        'estado_civil': ['Casado'],
        'aniversario': ['15/03/1985']
    })
    
    # Faz predição
    results = predictor.predict_lead_quality(new_data)
    
    print("Predições:")
    for result in results:
        print(f"  Qualidade: {result['quality_prediction']}")
        print(f"  Confiança: {result['confidence']:.3f}")
        print(f"  Prob. Alta Qualidade: {result['probability_high_quality']:.3f}")
