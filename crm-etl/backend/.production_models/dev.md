
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
new_leads = pd.DataFrame({
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
})

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

## Modelo Treinado em: 2025-06-11T16:10:19.391574
## Features: 13
## Amostras de Treino: 36
