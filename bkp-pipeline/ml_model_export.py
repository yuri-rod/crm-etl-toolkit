#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Exportação de Modelos para Produção
Salva modelos treinados, encoders e configurações para uso em produção
"""

import pandas as pd
import numpy as np
import pickle
import joblib
import json
from datetime import datetime
import os
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from ml_transformation import MLDataTransformer

class ModelExporter:
    """
    Classe para exportar modelos e configurações para produção
    """
    
    def __init__(self, data_path, export_dir='./production_models/'):
        self.data_path = data_path
        self.export_dir = export_dir
        self.transformer = None
        self.best_model = None
        self.scaler = None
        self.model_metadata = {}
        
    def prepare_production_model(self):
        """
        Prepara o melhor modelo para produção
        """
        print("Preparando modelo para produção...")
        
        # Inicializa e executa transformação completa
        self.transformer = MLDataTransformer(self.data_path)
        
        # Executa pipeline completo
        self.transformer.load_and_parse_data()
        self.transformer.create_synthetic_features()
        self.transformer.encode_categorical_features()
        self.transformer.select_features(k=13)
        datasets = self.transformer.split_and_normalize_data()
        
        # Treina o melhor modelo (RandomForest baseado nos resultados anteriores)
        self.best_model = RandomForestClassifier(
            n_estimators=100,
            max_depth=5,
            random_state=42,
            class_weight='balanced'
        )
        
        # Combina treino e validação para modelo final
        X_full_train = pd.concat([datasets['X_train'], datasets['X_val']])
        y_full_train = np.concatenate([datasets['y_train'], datasets['y_val']])
        
        # Treina modelo final
        self.best_model.fit(X_full_train, y_full_train)
        
        # Armazena scaler
        self.scaler = self.transformer.scaler
        
        # Prepara metadados
        self.model_metadata = {
            'model_type': 'RandomForest',
            'model_params': self.best_model.get_params(),
            'feature_names': datasets['feature_names'],
            'label_encoders': {k: list(v.classes_) for k, v in self.transformer.label_encoders.items()},
            'training_date': datetime.now().isoformat(),
            'training_samples': len(X_full_train),
            'feature_count': len(datasets['feature_names']),
            'target_classes': [0, 1],
            'data_processing_steps': [
                'parse_csv_data',
                'create_synthetic_features',
                'label_encode_categorical',
                'feature_selection',
                'standard_scaling'
            ]
        }
        
        print(f"✅ Modelo preparado com {len(datasets['feature_names'])} features")
        return True
    
    def export_model_artifacts(self):
        """
        Exporta todos os artefatos necessários para produção
        """
        print(f"Exportando artefatos para {self.export_dir}...")
        
        # Cria diretório se não existir
        os.makedirs(self.export_dir, exist_ok=True)
        
        # 1. Salva o modelo treinado
        model_path = f"{self.export_dir}trained_model.pkl"
        joblib.dump(self.best_model, model_path)
        print(f"  ✅ Modelo salvo: {model_path}")
        
        # 2. Salva o scaler
        scaler_path = f"{self.export_dir}scaler.pkl"
        joblib.dump(self.scaler, scaler_path)
        print(f"  ✅ Scaler salvo: {scaler_path}")
        
        # 3. Salva os label encoders
        encoders_path = f"{self.export_dir}label_encoders.pkl"
        joblib.dump(self.transformer.label_encoders, encoders_path)
        print(f"  ✅ Label encoders salvos: {encoders_path}")
        
        # 4. Salva metadados
        metadata_path = f"{self.export_dir}model_metadata.json"
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(self.model_metadata, f, indent=2, ensure_ascii=False)
        print(f"  ✅ Metadados salvos: {metadata_path}")
        
        return {
            'model': model_path,
            'scaler': scaler_path,
            'encoders': encoders_path,
            'metadata': metadata_path
        }
    
    def create_inference_script(self):
        """
        Cria script de inferência para produção
        """
        inference_script = '''
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
        df['has_whatsapp'] = df['whatsapp'].astype(str).str.contains(r'\\+55|55', na=False).astype(int)
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
'''
        
        inference_path = f"{self.export_dir}inference.py"
        with open(inference_path, 'w', encoding='utf-8') as f:
            f.write(inference_script)
        
        print(f"  ✅ Script de inferência criado: {inference_path}")
        return inference_path
    
    def create_deployment_guide(self):
        """
        Cria guia de implantação
        """
        guide = f'''
# Guia de Implantação - Modelo CRM Lead Quality

## Arquivos Necessários
- `trained_model.pkl`: Modelo treinado RandomForest
- `scaler.pkl`: StandardScaler para normalização
- `label_encoders.pkl`: Encoders para variáveis categóricas
- `model_metadata.json`: Metadados e configurações
- `inference.py`: Script de predição

## Requisitos do Sistema
```
pandas>=1.3.0
numpy>=1.21.0
scikit-learn>=1.0.0
joblib>=1.0.0
```

## Uso Básico

```python
from inference import CRMLeadPredictor
import pandas as pd

# Inicializa preditor
predictor = CRMLeadPredictor()

# Prepara dados
new_leads = pd.DataFrame({{
    'nome': ['Cliente Exemplo'],
    'empresa_cargo': ['Empresa X - Diretor'],
    'segmento': ['Tecnologia'],
    'linkedin': ['linkedin.com/in/cliente'],
    'cnpj': ['12345678000199'],
    'whatsapp': ['+5511999999999'],
    'email': ['cliente@empresa.com'],
    'cidade_estado': ['São Paulo - SP'],
    'estado_civil': ['Casado'],
    'aniversario': ['15/03/1985']
}})

# Faz predição
results = predictor.predict_lead_quality(new_leads)
print(results)
```

## Interpretação dos Resultados
- `quality_prediction`: "Alta" ou "Baixa" qualidade
- `confidence`: Confiança da predição (0-1)
- `probability_high_quality`: Probabilidade de ser lead de alta qualidade
- `probability_low_quality`: Probabilidade de ser lead de baixa qualidade

## Monitoramento em Produção
1. Acompanhar distribuição das predições
2. Validar performance com feedback real
3. Retreinar modelo periodicamente
4. Monitorar drift dos dados de entrada

## Modelo Treinado em: {self.model_metadata['training_date']}
## Features: {len(self.model_metadata['feature_names'])}
## Amostras de Treino: {self.model_metadata['training_samples']}
'''
        
        guide_path = f"{self.export_dir}DEPLOYMENT_GUIDE.md"
        with open(guide_path, 'w', encoding='utf-8') as f:
            f.write(guide)
        
        print(f"  ✅ Guia de implantação criado: {guide_path}")
        return guide_path

def main():
    """
    Função principal para exportar modelo completo
    """
    print("Exportando Modelo para Produção")
    print("=" * 40)
    
    # Configura exportador
    exporter = ModelExporter("dataset_unificado_20250611_160521_61aac20d.csv")
    
    try:
        # 1. Prepara modelo
        exporter.prepare_production_model()
        
        # 2. Exporta artefatos
        artifacts = exporter.export_model_artifacts()
        
        # 3. Cria script de inferência
        inference_script = exporter.create_inference_script()
        
        # 4. Cria guia de implantação
        guide = exporter.create_deployment_guide()
        
        print(f"\n✅ Exportação concluída com sucesso!")
        print(f"📁 Artefatos salvos em: {exporter.export_dir}")
        print(f"🤖 Modelo: {artifacts['model']}")
        print(f"📊 Script de inferência: {inference_script}")
        print(f"📖 Guia de implantação: {guide}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro na exportação: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    main()

