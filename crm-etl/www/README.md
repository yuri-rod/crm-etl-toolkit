# Sistema CRM Unificado com Inteligência Artificial

**CRM ETL** - Sistema completo de análise e predição de qualidade de leads para CRM

## 📋 Visão Geral

O Sistema CRM Unificado é uma solução completa que integra ETL (Extract, Transform, Load) inteligente, Machine Learning e APIs de enriquecimento de dados para análise e predição de qualidade de leads em sistemas CRM.

### ✨ Principais Funcionalidades

- 📊 **Pipeline ETL Inteligente**: Processamento automatizado de dados CSV/XLSX com detecção de separadores e encoding
- 🤖 **Machine Learning**: Modelos preditivos para classificação de qualidade de leads
- 🌐 **Interface Web**: Dashboard responsivo para upload e monitoramento de pipelines
- 🔗 **API RESTful**: Backend FastAPI com documentação automática
- 🇧🇷 **Compatibilidade Brasileira**: Validação de CPF, CNPJ, telefones e normalização de dados
- ⚡ **Processamento em Tempo Real**: Monitoramento de progresso via polling
- 📈 **Enriquecimento de Dados**: Integração com APIs externas (ReceitaWS)

### 🏗️ Arquitetura do Sistema

1. **Frontend Web**: Interface HTML/JavaScript responsiva
2. **Backend API**: Servidor FastAPI com processamento assíncrono
3. **Pipeline ETL**: Classe `UnifiedCRMPipeline` para processamento de dados
4. **Modelos ML**: RandomForest com otimização automática de hiperparâmetros
5. **Validadores**: Módulos especializados para dados brasileiros

## 📋 Requisitos do Sistema

### Requisitos Básicos
- **Python**: 3.8 ou superior
- **Memória RAM**: Mínimo 4GB (recomendado 8GB)
- **Espaço em Disco**: 500MB livres
- **Sistema Operacional**: Windows 10+, Linux (Ubuntu 18.04+), macOS 10.14+

### Dependências Python
```bash
# Core Dependencies
pandas>=2.1.0
numpy>=1.24.0
scikit-learn>=1.3.0

# API Server
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
python-multipart>=0.0.6

# Data Processing
openpyxl>=3.1.0
requests>=2.31.0
joblib>=1.3.0

# Testing (opcional)
pytest>=7.0.0
pytest-asyncio>=0.21.0
```

## 🛠 Instruções de Setup Completo

### Passo 1: Preparar Ambiente

#### Windows
```batch
# Verificar versão do Python
python --version

# Criar ambiente virtual (recomendado)
python -m venv venv
venv\Scripts\activate

# Atualizar pip
python -m pip install --upgrade pip
```

#### Linux/macOS
```bash
# Verificar versão do Python
python3 --version

# Instalar venv se necessário (Ubuntu/Debian)
sudo apt-get install python3-venv

# Criar ambiente virtual
python3 -m venv venv
source venv/bin/activate

# Atualizar pip
pip install --upgrade pip
```

### Passo 2: Instalar Sistema

#### Opção A: Instalação Automática
```bash
# Instalar todas as dependências automaticamente
pip install -r requirements.txt
```

#### Opção B: Instalação Manual por Categoria
```bash
# Core - Processamento de dados
pip install pandas==2.1.3 numpy==1.24.3 scikit-learn==1.3.2

# API Server - Backend FastAPI
pip install fastapi==0.104.1 uvicorn[standard]==0.24.0 python-multipart==0.0.6

# Dados - Leitura de arquivos
pip install openpyxl==3.1.2 requests==2.31.0 joblib==1.3.2

# Testes (opcional)
pip install pytest==7.4.3 pytest-asyncio==0.21.1
```

### Passo 3: Verificar Instalação

```bash
# Verificar todas as dependências
python -c "import pandas, numpy, sklearn, fastapi, uvicorn; print('✅ Instalação OK')"

# Verificar estrutura de arquivos
ls -la backend/
ls -la www/
```

### Passo 4: Configuração Inicial

```bash
# Criar diretórios necessários
mkdir -p data/input data/output temp production_models

# Definir permissões (Linux/macOS)
chmod +x backend/*.py
```

### Passo 5: Inicialização do Sistema

#### Desenvolvimento (Recomendado para testes)
```bash
# Iniciar servidor em modo desenvolvimento
cd backend
uvicorn api_server:app --reload --host 127.0.0.1 --port 8000

# Ou usando Python diretamente
python backend/api_server.py
```

#### Produção
```bash
# Iniciar servidor em modo produção
uvicorn backend.api_server:app --host 0.0.0.0 --port 8000 --workers 4
```

### Passo 6: Verificar Sistema

**URLs de Acesso:**
- 🌐 **Interface Web**: http://127.0.0.1:8000/
- 📚 **Documentação API**: http://127.0.0.1:8000/docs
- ❤️ **Health Check**: http://127.0.0.1:8000/health
- 🔍 **Redoc API**: http://127.0.0.1:8000/redoc

## 📁 Estrutura do Projeto

```
crm-etl-system/
├── backend/
│   └── api_server.py          # Servidor FastAPI
├── www/
│   └── index.html             # Interface web
├── data/
│   ├── input/                 # Arquivos de entrada
│   └── output/                # Resultados processados
├── temp/                      # Arquivos temporários
├── start_system.py           # Script de inicialização
├── requirements.txt          # Dependências
└── README.md                 # Esta documentação
```

## 🔧 Como Usar

### 1. Upload de Dados
- Arraste um arquivo CSV ou XLSX para a área de upload
- Ou clique para selecionar manualmente
- Formatos suportados: `.csv`, `.xlsx`, `.xls`

### 2. Configurar Pipeline
- **Modo**: Treinamento ou Predição em Lote
- **Coluna Alvo**: Nome da coluna target (para treinamento)
- **Diretório Modelo**: Local para salvar/carregar modelos
- **Enriquecimento**: Ativação de APIs externas

### 3. Executar Processing
- Clique em "Executar Pipeline"
- Acompanhe o progresso na barra em tempo real
- Visualize as métricas no dashboard

### 4. Download Resultados
- Após conclusão, clique em "Exportar Resultados"
- O arquivo será baixado automaticamente
- Formato: CSV com separador `;` e encoding UTF-8

## 📊 API Endpoints

### POST /etl/run
Executa uma pipeline ETL.

**Parâmetros (FormData):**
- `file`: Arquivo de dados (CSV/XLSX)
- `mode`: "train" ou "batch-predict"
- `target_column`: Nome da coluna target
- `enable_enrichment`: Boolean para enriquecimento
- `output_filename`: Nome do arquivo de saída

**Resposta:**
```json
{
  "pipeline_id": "abc12345",
  "status": "iniciada",
  "message": "Pipeline iniciada com sucesso..."
}
```

### GET /etl/status/{pipeline_id}
Monitora status de uma pipeline.

**Resposta:**
```json
{
  "status": "processando",
  "progress": 45.0,
  "message": "CRM - Processando features...",
  "details": {...}
}
```

### GET /etl/download/{pipeline_id}
Download de resultados processados.

**Resposta:** Arquivo CSV para download

## 🎯 Fluxo de Processamento

1. **Upload** - Arquivo enviado via FormData
2. **Validação** - Verificação de formato e tamanho
3. **Processamento** - Pipeline ETL em background
4. **Monitoramento** - Status atualizado via polling
5. **Resultados** - Arquivo disponível para download

## 🔄 Monitoramento em Tempo Real

O sistema usa polling para atualizar o progresso:
- Verificação a cada 2 segundos
- Status: iniciando → carregando → processando → concluida
- Barra de progresso atualizada automaticamente
- Notificações em tempo real

## 🚨 Tratamento de Erros

- **Upload**: Validação de formato de arquivo
- **Processamento**: Logs detalhados de erros
- **API**: Códigos HTTP apropriados
- **Frontend**: Notificações visuais de erro

## ⚙️ Configurações Avançadas

### Variáveis de Ambiente (opcional)
```bash
export CRM_HOST=127.0.0.1
export CRM_PORT=8000
export CRM_DEBUG=true
```

### Customização de Porta
```bash
python start_system.py --dev --port 3000 --host 0.0.0.0
```

## 🧪 Comandos de Teste Completos

### 🗺 Visão Geral dos Testes

O sistema possui uma suíte completa de testes organizados em múltiplas categorias:

- **Unit Tests**: Testes unitários para funções individuais
- **Integration Tests**: Testes de integração entre componentes
- **End-to-End Tests**: Testes completos da pipeline
- **Performance Tests**: Benchmarks e testes de performance
- **Compatibility Tests**: Testes de compatibilidade com dados brasileiros

### 1️⃣ Executar Todos os Testes

```bash
# Executar toda a suíte de testes
pytest tests/ -v --tb=short

# Com relatório de cobertura
pytest tests/ --cov=backend --cov-report=html --cov-report=term

# Execução paralela (mais rápido)
pytest tests/ -n 4 -v
```

### 2️⃣ Testes por Categoria

#### Testes de Importação de Dados (CSV/XLSX)
```bash
# Testes do método _load_data da UnifiedCRMPipeline
pytest tests/test_unified_crm_pipeline_load_data.py -v

# Testes de benchmark e performance
pytest tests/test_benchmark_load_data.py -v -s

# Saida esperada:
# ✅ Separador vírgula (','): 2 registros, 4 colunas em 0.006s
# ✅ Separador ponto e vírgula (';'): 2 registros, 4 colunas em 0.003s
# ✅ Encoding iso-8859-1: 2 registros carregados em 0.004s
```

#### Testes de Limpeza e Transformação
```bash
# Testes completos de ETL e Machine Learning
pytest tests/test_cleaning_transformation_scoring.py -v

# Teste específico de deduplicação
pytest tests/test_cleaning_transformation_scoring.py::TestCleaningTransformationScoring::test_clean_data_cpf_deduplication -v

# Teste de feature engineering
pytest tests/test_cleaning_transformation_scoring.py::TestCleaningTransformationScoring::test_engineer_features_creation -v
```

#### Testes de Compatibilidade Brasileira
```bash
# Testes de CPF, CNPJ, telefones brasileiros
pytest tests/test_brazilian_compatibility.py -v

# Executar apenas testes de validação de CPF
pytest tests/test_brazilian_compatibility.py -k "cpf" -v

# Executar apenas testes de validação de CNPJ
pytest tests/test_brazilian_compatibility.py -k "cnpj" -v
```

#### Testes End-to-End (E2E)
```bash
# Testes completos da pipeline via API
pytest tests/e2e/ -v

# Teste completo da pipeline
pytest tests/e2e/test_full_pipeline.py -v

# Testes de responsividade da interface
pytest tests/e2e/test_responsive.py -v
```

### 3️⃣ Testes Específicos por Função

#### Testar Detecção de Separadores CSV
```bash
# Teste com diferentes separadores (,) (;) (|) (\t)
pytest tests/test_unified_crm_pipeline_load_data.py::TestUnifiedCRMPipelineLoadData::test_automatic_separator_detection -v -s
```

#### Testar Encoding de Arquivos
```bash
# Teste com ISO-8859-1 e caracteres acentuados
pytest tests/test_unified_crm_pipeline_load_data.py::TestUnifiedCRMPipelineLoadData::test_load_csv_iso_encoding_with_accents -v
```

#### Testar Modelo de Machine Learning
```bash
# Teste de treinamento com ROC AUC > 0.7
pytest tests/test_cleaning_transformation_scoring.py::TestCleaningTransformationScoring::test_train_model_balanced_dataset_auc_threshold -v -s
```

### 4️⃣ Testes de Performance e Benchmark

```bash
# Benchmark completo com diferentes cenários
pytest tests/test_benchmark_load_data.py::TestBenchmarkLoadData::test_comprehensive_separator_detection -v -s

# Teste de performance com arquivo grande (1000 registros)
pytest tests/test_benchmark_load_data.py::TestBenchmarkLoadData::test_performance_large_file -v -s

# Saída esperada:
# 📅 Arquivo com 1,000 registros carregado em 0.005s
# ⚡ Performance: 222,132 registros/segundo
# 💾 Memória: 0.24 MB
```

### 5️⃣ Testes de API (Requer servidor rodando)

```bash
# Iniciar servidor em background para testes
uvicorn backend.api_server:app --host 127.0.0.1 --port 8000 &
API_PID=$!

# Executar testes de API
pytest tests/e2e/test_full_pipeline.py -v

# Finalizar servidor após testes
kill $API_PID
```

### 6️⃣ Testes Manuais via Interface Web

#### Checklist de Testes Manuais

1. **Upload de Arquivo**
   ```
   ✅ Arrastar arquivo CSV para área de upload
   ✅ Selecionar arquivo XLSX via clique
   ✅ Validar aceitação de formatos (.csv, .xlsx, .xls)
   ✅ Rejeitar formatos inválidos (.txt, .doc)
   ```

2. **Configuração da Pipeline**
   ```
   ✅ Selecionar modo "Treinamento"
   ✅ Selecionar modo "Predição em Lote"
   ✅ Definir coluna alvo
   ✅ Ativar/desativar enriquecimento
   ```

3. **Monitoramento de Progresso**
   ```
   ✅ Barra de progresso atualiza em tempo real
   ✅ Status muda: iniciando → carregando → processando → concluída
   ✅ Mensagens de status são informativas
   ✅ Detalhes técnicos visíveis
   ```

4. **Download de Resultados**
   ```
   ✅ Botão de download aparece após conclusão
   ✅ Arquivo é baixado automaticamente
   ✅ Formato CSV com separação correta
   ✅ Encoding UTF-8 preservado
   ```

### 7️⃣ Comandos de Debug e Diagnóstico

```bash
# Verificar cobertura de testes
pytest tests/ --cov=backend --cov-report=term-missing

# Executar testes com debug verbose
pytest tests/ -v -s --tb=long

# Executar apenas testes que falharam anteriormente
pytest --lf -v

# Gerar relatório HTML de cobertura
pytest tests/ --cov=backend --cov-report=html
# Abrir htmlcov/index.html no navegador

# Profile de performance dos testes
pytest tests/ --profile
```

### 8️⃣ Testes de Carga e Stress

```bash
# Teste com arquivo grande (criar 10k registros)
python -c "
import pandas as pd
import numpy as np

data = {
    'nome': [f'Usuario_{i}' for i in range(10000)],
    'email': [f'user{i}@test.com' for i in range(10000)],
    'qualidade_lead': np.random.choice(['alta', 'baixa'], 10000)
}
pd.DataFrame(data).to_csv('test_large.csv', index=False)
print('Arquivo de teste criado: test_large.csv')
"

# Executar teste de performance
python backend/unificado.py --mode etl --input test_large.csv --output results_large.csv
```

### 9️⃣ Validação de Instalação

```bash
# Script de validação rápida
python -c "
try:
    from backend.unificado import UnifiedCRMPipeline
    pipeline = UnifiedCRMPipeline()
    print('✅ UnifiedCRMPipeline importada com sucesso')
    
    import pandas as pd
    import numpy as np
    import sklearn
    print('✅ Dependências ML OK')
    
    import fastapi
    import uvicorn
    print('✅ Dependências API OK')
    
    print('🎉 Sistema pronto para uso!')
except Exception as e:
    print(f'❌ Erro na validação: {e}')
"
```

## 📈 Métricas e Dashboard

O dashboard ao vivo mostra:
- Jobs ativos no sistema
- Pipelines concluídas hoje
- Uso de CPU e memória
- Contagem de erros
- Uptime do sistema
- Feed de atividades recentes

## 🔧 Troubleshooting

### Problema: "Pipeline não encontrada"
- Verifique se o pipeline_id está correto
- Pipeline pode ter expirado (>24h)

### Problema: "Arquivo não suportado"
- Use apenas CSV, XLSX ou XLS
- Verifique codificação do arquivo

### Problema: "Erro ao iniciar servidor"
- Verifique se a porta está livre
- Execute `python start_system.py --test`
- Reinstale dependências se necessário

## 👥 Como Contribuir / Boas Práticas de Código

### 🚀 Contribuindo para o Projeto

Agradecemos seu interesse em contribuir com o Sistema CRM Unificado! Este documento fornece diretrizes para manter a qualidade e consistência do código.

### 📋 Requisitos para Contribuição

1. **Fork** do repositório
2. **Clone** do seu fork localmente
3. **Branch** para sua feature/correção: `git checkout -b feature/nome-da-feature`
4. **Commits** seguindo as convenções abaixo
5. **Pull Request** com descrição detalhada

### 📏 Padrões de Código

#### Estilo Python (PEP 8)
```python
# Bom ✅
class UnifiedCRMPipeline:
    """Docstring no formato Sphinx."""
    
    def __init__(self, model_dir: str = './models/'):
        self.model_dir = Path(model_dir)
    
    def _load_data(self, file_path: str) -> pd.DataFrame:
        """Método privado com tipo hint."""
        return pd.read_csv(file_path)

# Evitar ❌
class pipeline:
    def __init__(self,modelDir):
        self.modelDir=modelDir
```

#### Documentação (Sphinx)
```python
def processo_dados(self, df: pd.DataFrame, opcoes: dict = None) -> pd.DataFrame:
    """
    Processa DataFrame aplicando transformações definidas.
    
    Parameters:
        df (pd.DataFrame): DataFrame com dados brutos.
        opcoes (dict, optional): Opções de processamento. Defaults to None.
    
    Returns:
        pd.DataFrame: DataFrame processado.
    
    Raises:
        ValueError: Se o DataFrame estiver vazio.
    
    Example:
        >>> pipeline = UnifiedCRMPipeline()
        >>> df_processado = pipeline.processo_dados(df_raw)
    """
```

#### Type Hints (Obrigatório)
```python
from typing import Dict, List, Optional, Union
from pathlib import Path

def validar_arquivo(caminho: Union[str, Path]) -> bool:
    """Valida se arquivo existe e é legível."""
    return Path(caminho).exists()

def obter_configuracao() -> Dict[str, Any]:
    """Retorna configuração do sistema."""
    return {'debug': True, 'timeout': 30}
```

### 🧪 Testes Obrigatórios

#### Cobertura Mínima: 80%
```python
# tests/test_nova_feature.py
import pytest
from unittest.mock import patch, MagicMock

class TestNovaFeature:
    """Testes para nova funcionalidade."""
    
    @pytest.fixture
    def pipeline(self):
        """Fixture para instância da pipeline."""
        return UnifiedCRMPipeline()
    
    def test_funcao_basica(self, pipeline):
        """Teste do fluxo principal."""
        resultado = pipeline.nova_funcao('parametro')
        assert resultado is not None
        assert isinstance(resultado, pd.DataFrame)
    
    def test_tratamento_erro(self, pipeline):
        """Teste de tratamento de erro."""
        with pytest.raises(ValueError, match="Parâmetro inválido"):
            pipeline.nova_funcao('')
    
    @patch('requests.get')
    def test_api_externa(self, mock_get, pipeline):
        """Teste com mock de API externa."""
        mock_get.return_value.json.return_value = {'status': 'ok'}
        resultado = pipeline.chamar_api_externa()
        assert resultado['status'] == 'ok'
```

#### Executar Testes Antes do PR
```bash
# Todos os testes
pytest tests/ -v --cov=backend --cov-report=term

# Apenas novos testes
pytest tests/test_nova_feature.py -v

# Lint do código
flake8 backend/ --max-line-length=120
black backend/ --check
```

### 📝 Convenções de Commit

#### Formato: `tipo(escopo): descrição`

```bash
# Features
git commit -m "feat(pipeline): adicionar suporte a arquivos JSON"
git commit -m "feat(api): implementar endpoint de health check"

# Corrections
git commit -m "fix(data): corrigir bug na detecção de encoding"
git commit -m "fix(ml): resolver erro de división por zero no AUC"

# Documentation
git commit -m "docs(readme): atualizar instruções de instalação"
git commit -m "docs(api): adicionar exemplos de uso da API"

# Tests
git commit -m "test(etl): adicionar testes para validação de CPF"
git commit -m "test(integration): implementar testes e2e completos"

# Refactoring
git commit -m "refactor(clean): extrair função de deduplicação"
git commit -m "refactor(features): simplificar engenharia de features"

# Performance
git commit -m "perf(load): otimizar carregamento de arquivos grandes"

# Configuration
git commit -m "config(ci): adicionar GitHub Actions para testes"
```

### 🔄 Fluxo de Trabalho (Git Flow)

```bash
# 1. Sincronizar com main
git checkout main
git pull origin main

# 2. Criar branch para feature
git checkout -b feature/nova-funcionalidade

# 3. Desenvolver com commits atômicos
git add arquivo_alterado.py
git commit -m "feat(feature): implementar parte 1 da funcionalidade"

# 4. Manter branch atualizada
git checkout main
git pull origin main
git checkout feature/nova-funcionalidade
git merge main

# 5. Push e PR
git push origin feature/nova-funcionalidade
# Criar PR via interface GitHub/GitLab
```

### 📁 Estrutura de Arquivos

```
# Organização recomendada para novas features
backend/
├── unificado.py              # Classe principal
├── brazilian_utils.py        # Utilitários brasileiros
├── api_server.py             # Servidor FastAPI
└── nova_feature/
    ├── __init__.py
    ├── processador.py        # Lógica principal
    ├── validadores.py        # Validações
    └── utils.py              # Utilitários da feature

tests/
├── test_unificado.py         # Testes da classe principal
├── test_brazilian_utils.py   # Testes dos utilitários
└── test_nova_feature/
    ├── __init__.py
    ├── test_processador.py
    └── test_validadores.py
```

### 🎨 Padrões de Interface

#### Mensagens de Log
```python
# Bom ✅
logger.info("Iniciando processamento de arquivo: %s", file_path)
logger.warning("Nenhuma coluna de CPF encontrada. Pulando validação.")
logger.error("Falha ao conectar com API externa: %s", str(e))

# Evitar ❌
print("carregando arquivo...")
logger.info(f"Processando {file_path}")  # f-strings só para variáveis simples
```

#### Tratamento de Erros
```python
# Bom ✅
try:
    df = pd.read_csv(file_path)
except FileNotFoundError:
    logger.error("Arquivo não encontrado: %s", file_path)
    raise ValueError(f"Arquivo '{file_path}' não existe")
except pd.errors.EmptyDataError:
    logger.warning("Arquivo vazio: %s", file_path)
    return pd.DataFrame()
except Exception as e:
    logger.exception("Erro inesperado ao ler arquivo")
    raise

# Evitar ❌
try:
    df = pd.read_csv(file_path)
except:
    pass  # Nunca ignorar erros silenciosamente
```

### ⚙️ Configuração do Ambiente de Desenvolvimento

#### Ferramentas Recomendadas
```bash
# Instalar ferramentas de desenvolvimento
pip install black flake8 mypy pre-commit

# Configurar pre-commit hooks
pre-commit install

# Formatar código automaticamente
black backend/ tests/

# Verificar tipos
mypy backend/

# Lint
flake8 backend/ --max-line-length=120 --ignore=E203,W503
```

#### Arquivo .pre-commit-config.yaml
```yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.1.0
    hooks:
      - id: black
        language_version: python3.8
  
  - repo: https://github.com/PyCQA/flake8
    rev: 6.0.0
    hooks:
      - id: flake8
        args: [--max-line-length=120]
  
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.0.1
    hooks:
      - id: mypy
```

### 📉 Checklist de Pull Request

#### Antes de Submeter
- [ ] **Código**: Segue PEP 8 e padrões do projeto
- [ ] **Testes**: Cobertura ≥ 80% para código novo
- [ ] **Documentação**: Docstrings Sphinx em todas as funções públicas
- [ ] **Type Hints**: Todos os parâmetros e retornos tipados
- [ ] **Logs**: Mensagens informativas em pontos críticos
- [ ] **Tratamento de Erro**: Exceções específicas e mensagens claras
- [ ] **Performance**: Código otimizado para arquivos grandes
- [ ] **Compatibilidade**: Funciona com Python 3.8+
- [ ] **Testes**: Passam localmente: `pytest tests/ -v`
- [ ] **Lint**: Sem warnings: `flake8 backend/`

#### Template de PR
```markdown
## Descrição
Breve descrição das mudanças implementadas.

## Tipo de Mudança
- [ ] Bug fix (mudança que corrige um problema)
- [ ] Nova feature (mudança que adiciona funcionalidade)
- [ ] Breaking change (mudança que quebra compatibilidade)
- [ ] Documentação

## Como Testar
1. Instalar dependências: `pip install -r requirements.txt`
2. Executar testes: `pytest tests/test_nova_feature.py -v`
3. Testar manualmente: [instruções específicas]

## Checklist
- [ ] Testes passam localmente
- [ ] Código segue padrões do projeto
- [ ] Documentação atualizada
- [ ] Sem breaking changes (ou documentadas)
```

### 📚 Recursos para Desenvolvedores

#### Documentação Técnica
- **Sphinx**: https://www.sphinx-doc.org/
- **PEP 8**: https://pep8.org/
- **Type Hints**: https://docs.python.org/3/library/typing.html
- **Pandas**: https://pandas.pydata.org/docs/
- **Scikit-learn**: https://scikit-learn.org/stable/

#### Comunidade
- **Issues**: Reportar bugs e solicitar features
- **Discussions**: Dúvidas e ideias
- **Wiki**: Documentação avançada e tutoriais

### 🕰️ Roadmap de Contribuições

#### Prioridade Alta
- Suporte a mais formatos de arquivo (JSON, Parquet)
- Integração com mais APIs brasileiras
- Dashboard em tempo real com métricas avançadas
- Otimização para arquivos muito grandes (> 1GB)

#### Prioridade Média
- Sistema de configuração via arquivo
- Suporte a múltiplos modelos de ML
- Cache inteligente para APIs externas
- Relatórios em PDF/Excel

#### Prioridade Baixa
- Interface web mobile-first
- Suporte a outras línguas além de português
- Plugin system para extensões
- Deployment automatizado (Docker, Kubernetes)

---

## 📁 Static Assets & App Engine Configuration

### Static Directory Structure

The project is now organized with a dedicated `static/` directory structure for optimal deployment on Google App Engine and other cloud platforms:

```
www/
├── static/                               # Static assets directory
│   ├── img/                             # Image assets
│   │   ├── crm-tools-logo-v02.png       # Header navigation logo
│   │   ├── crm-logo.svg                 # Hero section logo
│   │   └── 24_02_2025_powered-by-crm... # Footer branding
│   ├── index.html                       # Main frontend application
│   └── README.md                        # Static assets documentation
├── app.yaml                             # App Engine configuration
└── backend/                             # Backend API server
```

### App Engine Static File Handlers

The `www/app.yaml` file is configured with the following static file handlers for optimal performance:

```yaml
handlers:
  # Root handler - serves main index.html
  - url: /
    static_files: static/index.html
    upload: static/index.html
    secure: always

  # Static directory - serves all static assets
  - url: /static
    static_dir: static
    secure: always

  # Asset-specific handler - CSS, JS, images, etc.
  - url: /(.*\.(css|js|png|jpg|jpeg|gif|ico|svg))$
    static_files: static/\1
    upload: static/.*\.(css|js|png|jpg|jpeg|gif|ico|svg)$
    secure: always
```

### Deployment Guidelines for Contributors

#### Where to Place Frontend Assets:
1. **HTML files**: Place in `www/static/`
2. **Images**: Place in `www/static/img/`
3. **CSS files**: Place in `www/static/css/` (if external)
4. **JavaScript files**: Place in `www/static/js/` (if external)

#### Important Path Rules:
- **Always use absolute paths** starting with `/static/` for asset references
- Example: `<img src="/static/img/logo.png">` ✅
- Avoid: `<img src="logo.png">` or `<img src="../img/logo.png">` ❌

#### App Engine Benefits:
- **CDN Integration**: Static assets are served through Google's global CDN
- **Automatic Caching**: Browser caching headers are set automatically
- **High Availability**: Static content served independently of backend
- **Cost Optimization**: Static requests don't consume backend instances

#### Testing Static Assets Locally:
```bash
# Navigate to www directory
cd www

# Serve static files locally (for testing)
python -m http.server 8080

# Access at: http://localhost:8080/static/index.html
```

#### Production Deployment:
```bash
# Deploy to App Engine from www directory
cd www
gcloud app deploy app.yaml

# All static files in static/ directory will be deployed
# and served automatically with proper caching headers
```

This structure ensures that frontend assets are properly organized, efficiently served, and easily deployable to production environments.

---

## 📢 Suporte

Sistema desenvolvido pela **CRM ETL**

- Website: [crm.com.br](https://crm.com.br)
- Localização: São Paulo - SP, Brasil

---

**CRM ETL** - Transformando dados em insights inteligentes! 🚀
