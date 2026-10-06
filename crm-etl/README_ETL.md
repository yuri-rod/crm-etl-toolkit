# 📊 Componentes ETL para Qualificação de Leads

Este documento descreve os componentes ETL (Extract, Transform, Load) adaptados do projeto AI/ML Dataset para o sistema de qualificação de leads.

## 🚀 Visão Geral

Os componentes ETL foram otimizados para processar dados de leads brasileiros, com validação completa de documentos, padronização de campos e geração automática de features para modelos de Machine Learning.

## 📁 Arquivos Principais

### 1. **processador_dados_leads.py**
Pipeline ETL completo com as seguintes funcionalidades:
- ✅ Carregamento flexível de arquivos CSV/Excel
- ✅ Padronização automática de nomes de colunas
- ✅ Validação de CPF, CNPJ e email
- ✅ Limpeza e formatação de dados
- ✅ Feature engineering para qualificação de leads
- ✅ Cálculo de scores de qualidade
- ✅ Exportação com metadados detalhados

### 2. **validacao_brasileira.py**
Módulo especializado em validações brasileiras:
- CPF: validação completa com dígitos verificadores
- CNPJ: validação completa com dígitos verificadores
- Telefone: validação de formato brasileiro (fixo/celular)
- CEP: validação e formatação
- Email: validação de formato
- Utilitários: formatação e extração de dados

### 3. **column_mapping_config.json**
Mapeamento completo de colunas em português:
```json
{
  "canonical_mapping": {
    "nome_completo": { ... },
    "cpf": { ... },
    "empresa_nome": { ... },
    "segmento_atuacao": { ... }
    // ... mais campos
  }
}
```

### 4. **exemplo_processar_leads.py**
Script de demonstração com exemplos práticos de uso.

## 🔧 Como Usar

### Instalação
```bash
# Instalar dependências
pip install -r requirements.txt
```

### Uso Básico
```python
from processador_dados_leads import ProcessadorDadosLeads

# Criar processador
processador = ProcessadorDadosLeads()

# Processar dados
resultado = processador.executar_pipeline_completo(
    diretorio_entrada="data",
    pattern="*.csv"
)
```

### Exemplo com Dados Reais
```bash
# Criar e processar dados de exemplo
python exemplo_processar_leads.py
```

## 📊 Features Geradas para ML

O processador gera automaticamente as seguintes features:

### Features de Completude
- `completude_criticos`: Score de campos críticos preenchidos (0-1)
- `completude_importantes`: Score de campos importantes preenchidos (0-1)

### Features de Validação
- `cpf_valido`: CPF válido (0/1)
- `cnpj_valido`: CNPJ válido (0/1)
- `email_valido`: Email válido (0/1)

### Features de Engajamento
- `score_engajamento`: Baseado em campos opcionais preenchidos (0-1)
- `score_porte_empresa`: Porte da empresa (1-7)
- `score_recencia`: Recência do lead (0-1)

### Score Final
- `score_qualidade_lead`: Score geral de qualidade (0-1)
- `classificacao_lead`: Classificação (Baixa/Média/Alta/Muito Alta)

## 🎯 Integração com ML

### Carregar Dados Processados
```python
import pandas as pd

# Carregar dados
df = pd.read_csv('data/leads_processados_*.csv')

# Selecionar features para ML
features = [
    'completude_criticos', 'completude_importantes',
    'email_valido', 'score_engajamento', 
    'score_porte_empresa', 'score_recencia'
]

X = df[features]
y = df['classificacao_lead']  # Ou seu target customizado
```

### Pipeline Completo
```python
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier

# Dividir dados
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# Treinar modelo
model = RandomForestClassifier()
model.fit(X_train, y_train)

# Avaliar
score = model.score(X_test, y_test)
print(f"Acurácia: {score:.2f}")
```

## 📈 Fluxo de Dados

```
Arquivos CSV → Carregamento → Padronização → Validação
                                    ↓
                              Limpeza de Dados
                                    ↓
                            Feature Engineering
                                    ↓
                          Cálculo de Scores
                                    ↓
                        Dataset Final + Metadados
```

## 🔍 Validações Disponíveis

### Documentos
- **CPF**: Validação completa incluindo dígitos verificadores
- **CNPJ**: Validação completa incluindo dígitos verificadores
- **RG**: Formatação (sem validação de dígitos)

### Contato
- **Email**: Validação de formato (regex)
- **Telefone**: Validação de formato brasileiro
- **CEP**: Validação de 8 dígitos

## 📝 Personalização

### Adicionar Novos Campos
Edite o método `_criar_mapeamento_colunas()` em `processador_dados_leads.py`:

```python
def _criar_mapeamento_colunas(self):
    return {
        # ... campos existentes ...
        'novo_campo': 'novo_campo_padronizado',
        'outro_campo': 'outro_campo_padronizado'
    }
```

### Adicionar Novas Features
Edite o método `adicionar_features_qualidade()`:

```python
# Adicionar nova feature
df_features['nova_feature'] = df_features['campo'].apply(
    lambda x: calcular_algo(x)
)
```

### Modificar Scores
Ajuste os pesos no cálculo do `score_qualidade_lead`:

```python
df_features['score_qualidade_lead'] = (
    df_features.get('completude_criticos', 0) * 0.3 +  # Ajustar peso
    df_features.get('completude_importantes', 0) * 0.2 +
    # ... outros componentes ...
)
```

## 🐛 Troubleshooting

### Erro: "Nenhum arquivo encontrado"
- Verifique se o diretório `data/` existe
- Confirme que há arquivos CSV no diretório
- Use o padrão correto (ex: `"leads_*.csv"`)

### Erro de codificação
O processador tenta automaticamente:
- UTF-8
- Latin-1
- CP1252

Se continuar com erro, converta o arquivo para UTF-8.

### Campos não reconhecidos
- Verifique o `column_mapping_config.json`
- Adicione mapeamentos customizados se necessário
- Campos não mapeados são preservados com nome limpo

## 📚 Próximos Passos

1. **Testar com dados reais**: Execute o processador com seus arquivos de leads
2. **Ajustar features**: Personalize as features baseado no seu negócio
3. **Integrar com modelo ML**: Use as features geradas para treinar seu modelo
4. **Criar API**: Exponha o processamento via API REST para integração
5. **Automatizar**: Configure jobs para processar novos leads automaticamente

## 🤝 Suporte

Para dúvidas ou problemas:
1. Verifique os logs em `processamento_dados.log`
2. Execute o script de exemplo para validar a instalação
3. Consulte os metadados gerados junto com os arquivos processados

---

*Componentes adaptados do projeto AI/ML Dataset (2025-06-05) para o Sistema de Qualificação de Leads*
