# Sistema ETL Unificado com Inteligência Artificial

## Visão Geral

Esta é uma ferramenta ETL (Extract, Transform, Load) de próxima geração que integra todas as funcionalidades do projeto TODOSETL com as mais modernas capacidades de IA para processamento de dados. Desenvolvida especificamente para **CRM ETL**, a ferramenta oferece processamento inteligente, auto-reparação e interface conversacional.

## 🚀 Características Principais

### 1. Pipeline ETL Auto-Reparável
- **Detecção Automática de Erros**: Identifica problemas em tempo real
- **Correção Automática**: Tenta corrigir erros de encoding, separadores e formatos
- **Recuperação de Falhas**: Sistema resiliente que se recupera automaticamente

### 2. IA Generativa Integrada
- **Processamento de Linguagem Natural**: Interface conversacional para criação de pipelines
- **Geração Automática de Código**: Cria transformações SQL baseadas em solicitações em português
- **Integração com LLMs**: Suporte para Claude, OpenAI e modelos locais

### 3. Processamento Multimodal
- **Dados Estruturados**: CSV, Excel, Parquet, JSON
- **Dados Semi-estruturados**: APIs REST, XML
- **Dados Não-estruturados**: Texto, documentos (com IA)
- **Conectores Inteligentes**: Bancos de dados, APIs, S3, sistemas locais

### 4. Monitoramento Inteligente
- **Detecção de Anomalias**: Identifica padrões incomuns nos dados
- **Métricas em Tempo Real**: CPU, memória, qualidade dos dados
- **Alertas Automáticos**: Notificações proativas de problemas

### 5. Engenharia de Features Automatizada
- **Features Temporais**: Extração automática de informações de data/hora
- **Features de Qualidade**: Scores baseados em completude e consistência
- **Features de Texto**: Análise automática de campos textuais
- **Features de Interação**: Combinações inteligentes entre variáveis

## 📋 Pré-requisitos

### Dependências Obrigatórias
```bash
pip install pandas numpy scikit-learn sqlalchemy requests tqdm
```

### Dependências Opcionais (para funcionalidades avançadas)
```bash
# Para processamento de IA local
pip install transformers torch

# Para APIs de IA
pip install anthropic openai

# Para formatos avançados
pip install pyarrow polars duckdb

# Para monitoramento
pip install psutil memory-profiler

# Para configurações YAML
pip install pyyaml

# Para agendamento
pip install schedule

# Para detecção de encoding
pip install chardet

# Para Excel
pip install openpyxl

# Para AWS S3
pip install boto3
```

### Instalação Completa
```bash
# Instalar todas as dependências
pip install -r requirements.txt
```

## 🔧 Configuração

### 1. Configuração Básica
Copie o arquivo `config_exemplo.yaml` e ajuste conforme suas necessidades:

```bash
cp config_exemplo.yaml minha_config.yaml
```

### 2. Variáveis de Ambiente (Opcional)
Para usar APIs de IA, configure as chaves:

```bash
# Para Claude (Anthropic)
export ANTHROPIC_API_KEY="sua_chave_aqui"

# Para OpenAI
export OPENAI_API_KEY="sua_chave_aqui"
```

### 3. Estrutura de Diretórios
```
projeto/
├── ferramenta_etl_ai_unificada.py
├── config_exemplo.yaml
├── minha_config.yaml
├── data/
│   ├── input/
│   └── output/
├── models/ (para modelos locais)
└── logs/
```

## 🚀 Como Usar

### 1. Uso Básico - Interface Programática

```python
import asyncio
from ferramenta_etl_ai_unificada import (
    IntelligentETLPipeline, 
    PipelineConfig, 
    AIModelConfig,
    ProcessingMode,
    DataType
)

# Configuração da pipeline
pipeline_config = PipelineConfig(
    name="Minha_Pipeline",
    description="Pipeline para processamento de leads",
    mode=ProcessingMode.BATCH,
    data_type=DataType.STRUCTURED,
    ai_enabled=True,
    auto_repair=True,
    monitoring_enabled=True
)

# Configuração de IA
ai_config = AIModelConfig(
    claude_api_key="sua_chave_claude",  # ou None
    openai_api_key="sua_chave_openai",  # ou None
    use_local_models=False,
    max_tokens=2048,
    temperature=0.7
)

# Criar e executar pipeline
async def main():
    pipeline = IntelligentETLPipeline(pipeline_config, ai_config)
    
    # Executar pipeline completa
    report = await pipeline.run_full_pipeline(
        source="data/input/leads.csv",
        output_path="data/output/leads_processados.xlsx",
        transformations=[
            "Filtrar registros com valor maior que 1000",
            "Criar coluna de score de qualidade",
            "Ordenar por data de cadastro decrescente"
        ]
    )
    
    print("Pipeline executada com sucesso!")
    print(f"Registros processados: {report['data_overview']['total_records']}")
    
    # Limpeza
    pipeline.cleanup_resources()

# Executar
asyncio.run(main())
```

### 2. Uso com Arquivo de Configuração

```python
from ferramenta_etl_ai_unificada import create_pipeline_from_config
import asyncio

async def main():
    # Criar pipeline a partir de configuração
    pipeline = create_pipeline_from_config("minha_config.yaml")
    
    # Executar
    report = await pipeline.run_full_pipeline(
        source="data/leads.csv",
        output_path="data/output/resultado.xlsx"
    )
    
    pipeline.cleanup_resources()

asyncio.run(main())
```

### 3. Processamento com IA Conversacional

```python
async def exemplo_ai():
    pipeline = IntelligentETLPipeline(config, ai_config)
    
    # Carregar dados
    df = pipeline.intelligent_data_loading("data/leads.csv")
    
    # Usar IA para análise
    resposta = await pipeline.process_with_ai(
        "Analise este dataset e sugira 3 transformações para melhorar a qualidade dos dados",
        data_context=f"Dataset com {len(df)} registros e colunas: {list(df.columns)}"
    )
    
    print("Sugestões da IA:")
    print(resposta)
```

### 4. Processamento de Diferentes Fontes

```python
# Fonte: Arquivo local
report1 = await pipeline.run_full_pipeline(
    source="data/leads.csv",
    output_path="output1.xlsx"
)

# Fonte: Banco de dados
database_config = {
    'type': 'database',
    'connection_string': 'postgresql://user:pass@localhost/db',
    'query': 'SELECT * FROM leads WHERE status = "ativo"'
}

report2 = await pipeline.run_full_pipeline(
    source=database_config,
    output_path="output2.xlsx"
)

# Fonte: API REST
api_config = {
    'type': 'api',
    'url': 'https://api.empresa.com/leads',
    'headers': {'Authorization': 'Bearer TOKEN'}
}

report3 = await pipeline.run_full_pipeline(
    source=api_config,
    output_path="output3.xlsx"
)
```

## 🔍 Funcionalidades Detalhadas

### Detecção Automática de Schema
```python
# A pipeline detecta automaticamente:
schema = pipeline.auto_detect_schema("arquivo.csv")
print(schema)
# Retorna:
# {
#   'columns': ['nome', 'email', 'telefone'],
#   'dtypes': {'nome': 'object', 'email': 'object'},
#   'null_counts': {'nome': 0, 'email': 5},
#   'ai_suggestions': {'transformations': '...'}
# }
```

### Limpeza Inteligente
```python
# Limpeza automática com IA
df_limpo = pipeline.ai_data_cleaning(df_original)

# Features incluídas:
# - Detecção de outliers (Isolation Forest)
# - Imputação inteligente de valores faltantes
# - Padronização de formatos (CPF, telefone, email)
# - Deduplicação baseada em similaridade
```

### Engenharia de Features
```python
# Criação automática de features
df_enriquecido = pipeline.ai_feature_engineering(df)

# Features criadas automaticamente:
# - Features temporais (ano, mês, dia da semana)
# - Score de qualidade dos dados
# - Features de texto (comprimento, padrões)
# - Features de interação entre variáveis
```

### Transformações com Linguagem Natural
```python
# Transformações usando português natural
df_transformado = pipeline.ai_transformation_engine(
    df, 
    "Filtrar clientes com faturamento maior que 50000 e criar coluna de categoria baseada no valor"
)
```

## 📊 Relatórios e Monitoramento

### Relatório Automático
Após cada execução, a pipeline gera um relatório completo:

```json
{
  "pipeline_info": {
    "name": "Minha_Pipeline",
    "execution_timestamp": "2024-01-25T10:30:00",
    "ai_enabled": true
  },
  "data_overview": {
    "total_records": 10000,
    "total_columns": 25,
    "memory_usage_mb": 45.2
  },
  "data_quality": {
    "missing_values": {"nome": 0, "email": 150},
    "duplicate_records": 25,
    "outliers_detected": 12
  },
  "performance_metrics": {
    "processing_time": 120.5,
    "cpu_usage": 45.2,
    "memory_usage": 78.1
  },
  "ai_insights": {
    "recommendations": [
      "Considerar normalização de colunas numéricas",
      "Verificar valores faltantes em email"
    ]
  }
}
```

### Monitoramento em Tempo Real
```python
# O monitoramento roda automaticamente em background
# Métricas coletadas:
# - Uso de CPU e memória
# - Tempo de processamento
# - Número de erros
# - Qualidade dos dados

# Alertas automáticos quando:
# - CPU > 90%
# - Memória > 85%
# - Muitos erros detectados
```

## 🛠️ Personalização e Extensões

### 1. Transformações Customizadas
```python
# Adicionar suas próprias transformações
def minha_transformacao(df):
    # Sua lógica aqui
    return df_modificado

# Registrar na pipeline
pipeline.register_custom_transformation("minha_func", minha_transformacao)
```

### 2. Conectores Customizados
```python
# Criar conector para fonte de dados específica
def meu_conector(config):
    # Lógica de conexão
    return dataframe

pipeline.register_data_source("meu_tipo", meu_conector)
```

### 3. Modelos de IA Customizados
```python
# Usar seu próprio modelo
pipeline.ai_config.local_model_path = "./meu_modelo/"
pipeline.ai_config.use_local_models = True
```

## 🔒 Segurança e Privacidade

### Dados Sensíveis
- ✅ Nunca armazena dados sensíveis
- ✅ Processamento local por padrão
- ✅ APIs de IA opcionais
- ✅ Logs com dados mascarados

### Validação de Código
- ✅ Whitelist de operações permitidas
- ✅ Sandbox para execução de transformações
- ✅ Validação de entrada para evitar injection

### Conformidade CRM
- ✅ Padrões de codificação da empresa
- ✅ Documentação em português
- ✅ Cores e identidade visual da marca
- ✅ Logs e relatórios profissionais

## 🚨 Solução de Problemas

### Problemas Comuns

**1. Erro de encoding**
```
Erro: 'utf-8' codec can't decode...
Solução: A pipeline detecta e corrige automaticamente
```

**2. Separador de CSV incorreto**
```
Erro: Apenas 1 coluna detectada...
Solução: Detecção automática de separador ativada
```

**3. Dependências faltando**
```
Erro: No module named 'transformers'
Solução: pip install transformers (funcionalidade será limitada)
```

**4. APIs de IA não funcionando**
```
Erro: API key not found
Solução: Configure ANTHROPIC_API_KEY ou OPENAI_API_KEY
```

### Logs Detalhados
```python
# Verificar logs para debugging
tail -f etl_ai_pipeline.log

# Ou ativar debug mode
logging.getLogger().setLevel(logging.DEBUG)
```

## 📈 Performance e Otimização

### Configurações de Performance
```python
# Ajustar workers paralelos
config.parallel_workers = 8  # baseado no seu CPU

# Ajustar tamanho do chunk
config.chunk_size = 50000  # para datasets grandes

# Ativar cache
pipeline.cache_enabled = True
```

### Otimizações Automáticas
- ✅ Detecção automática de tipos de dados otimizados
- ✅ Conversão para formatos eficientes (Parquet)
- ✅ Processamento em chunks para grandes volumes
- ✅ Garbage collection automático

## 🔄 Atualizações e Versionamento

### Histórico de Versões
- **v1.0.0**: Versão inicial com IA integrada
- **v1.1.0**: Suporte a processamento multimodal
- **v1.2.0**: Auto-reparação avançada

### Roadmap
- 🔄 Processamento em streaming
- 🔄 Interface web visual
- 🔄 Integração com mais fontes de dados
- 🔄 Modelos de IA específicos para domínio

## 📞 Suporte

### Documentação
- README completo: Este arquivo
- Exemplos: Pasta `/examples/`
- Configuração: `config_exemplo.yaml`

### Contato CRM
- **Email**: tech@crm.com.br
- **Projeto**: CRM ETL
- **Versão**: 1.0.0

---

**Desenvolvido com ❤️ para CRM ETL**

*"Transformando dados em insights inteligentes para a nova economia"*