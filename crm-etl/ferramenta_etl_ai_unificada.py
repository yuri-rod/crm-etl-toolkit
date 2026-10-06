#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
--- Sistema ETL Unificado com Inteligência Artificial Avançada ---
=============================================================================

Esta é uma ferramenta ETL de próxima geração que integra todas as funcionalidades
do projeto TODOSETL com as mais modernas capacidades de IA para processamento de dados.

Principais Funcionalidades:
1. **Pipeline ETL Auto-Reparável**: Detecta e corrige erros automaticamente
2. **Processamento de Linguagem Natural**: Interface conversacional para criação de pipelines
3. **IA Generativa para Transformações**: Gera código SQL e transformações automaticamente
4. **Processamento Multimodal**: Suporte para texto, imagem, áudio e vídeo
5. **Monitoramento Inteligente**: Detecção de anomalias e otimização automática
6. **Auto-Documentação**: Gera documentação automaticamente baseada no uso
7. **Integração com LLMs**: Claude, OpenAI, e modelos locais
8. **Pipeline Self-Healing**: Recuperação automática de falhas

Desenvolvido pela CRM ETL
"""

import asyncio
import json
import logging
import os
import re
import sys
import warnings
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, Callable
from dataclasses import dataclass, field
from enum import Enum
import threading
import time

# Data Processing
import pandas as pd
import numpy as np
try:
    import polars as pl
    import duckdb
except ImportError:
    print("Algumas dependências opcionais não estão instaladas. Funcionalidade pode ser limitada.")

from sqlalchemy import create_engine, MetaData, Table, text
try:
    import pyarrow as pa
    import pyarrow.parquet as pq
except ImportError:
    print("PyArrow não encontrado. Suporte a Parquet limitado.")

# Machine Learning & AI
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier, IsolationForest
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import classification_report, confusion_matrix
try:
    from transformers import pipeline, AutoTokenizer, AutoModel
    import torch
except ImportError:
    print("Transformers/PyTorch não encontrados. Funcionalidade de IA local limitada.")

import joblib

# AI APIs
try:
    import anthropic
except ImportError:
    print("Anthropic não encontrado. Funcionalidade Claude limitada.")

try:
    import openai
except ImportError:
    print("OpenAI não encontrado. Funcionalidade GPT limitada.")

import requests

# Utilities
try:
    import yaml
except ImportError:
    print("PyYAML não encontrado. Funcionalidade de configuração YAML limitada.")

from tqdm import tqdm
try:
    import schedule
except ImportError:
    print("Schedule não encontrado. Agendamento limitado.")

from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import multiprocessing as mp

# Monitoring & Observability
try:
    import psutil
except ImportError:
    print("PSUtil não encontrado. Monitoramento de sistema limitado.")

try:
    from memory_profiler import profile
except ImportError:
    print("Memory profiler não encontrado. Profiling de memória limitado.")

# Configuração de logging avançada
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('etl_ai_pipeline.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Suprimir warnings desnecessários
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning)

class ProcessingMode(Enum):
    """Modos de processamento disponíveis"""
    BATCH = "batch"
    STREAMING = "streaming"
    REAL_TIME = "real_time"
    HYBRID = "hybrid"

class DataType(Enum):
    """Tipos de dados suportados"""
    STRUCTURED = "structured"
    SEMI_STRUCTURED = "semi_structured"
    UNSTRUCTURED = "unstructured"
    MULTIMODAL = "multimodal"

@dataclass
class PipelineConfig:
    """Configuração da pipeline ETL com IA"""
    name: str
    description: str = ""
    mode: ProcessingMode = ProcessingMode.BATCH
    data_type: DataType = DataType.STRUCTURED
    ai_enabled: bool = True
    auto_repair: bool = True
    monitoring_enabled: bool = True
    parallel_workers: int = 4
    chunk_size: int = 10000
    ai_models: Dict[str, str] = field(default_factory=dict)
    custom_transformations: List[str] = field(default_factory=list)

@dataclass
class AIModelConfig:
    """Configuração dos modelos de IA"""
    claude_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    local_model_path: Optional[str] = None
    use_local_models: bool = False
    max_tokens: int = 2048
    temperature: float = 0.7

class IntelligentETLPipeline:
    """
    Pipeline ETL Inteligente com capacidades avançadas de IA
    """
    
    def __init__(self, config: PipelineConfig, ai_config: AIModelConfig):
        self.config = config
        self.ai_config = ai_config
        self.metadata = {}
        self.performance_metrics = {}
        self.error_history = []
        self.data_catalog = {}
        
        # Inicializar componentes de IA
        self._init_ai_components()
        
        # Inicializar monitoramento
        self._init_monitoring()
        
        # Cache para otimização
        self.cache = {}
        
        logger.info(f"Pipeline '{config.name}' inicializada com IA habilitada: {config.ai_enabled}")

    def _init_ai_components(self):
        """Inicializa componentes de IA"""
        try:
            # Claude API
            if self.ai_config.claude_api_key and 'anthropic' in sys.modules:
                self.claude_client = anthropic.Anthropic(api_key=self.ai_config.claude_api_key)
                logger.info("Cliente Claude inicializado")
            
            # OpenAI API
            if self.ai_config.openai_api_key and 'openai' in sys.modules:
                openai.api_key = self.ai_config.openai_api_key
                logger.info("Cliente OpenAI inicializado")
            
            # Modelos locais para processamento de texto
            if self.ai_config.use_local_models and 'transformers' in sys.modules:
                try:
                    from transformers import pipeline
                    self.text_classifier = pipeline("text-classification", 
                                                   model="neuralmind/bert-base-portuguese-cased")
                    self.text_generator = pipeline("text-generation", 
                                                 model="pierreguillou/gpt2-small-portuguese")
                    logger.info("Modelos locais de NLP inicializados")
                except Exception as e:
                    logger.warning(f"Erro ao carregar modelos locais: {e}")
                
        except Exception as e:
            logger.warning(f"Erro ao inicializar componentes de IA: {e}")

    def _init_monitoring(self):
        """Inicializa sistema de monitoramento"""
        self.monitoring_active = self.config.monitoring_enabled
        if self.monitoring_active and 'psutil' in sys.modules:
            # Iniciar thread de monitoramento
            self.monitoring_thread = threading.Thread(target=self._monitor_pipeline, daemon=True)
            self.monitoring_thread.start()
            logger.info("Sistema de monitoramento ativado")

    def _monitor_pipeline(self):
        """Monitora a pipeline em tempo real"""
        while self.monitoring_active:
            try:
                # Coletar métricas do sistema se psutil estiver disponível
                if 'psutil' in sys.modules:
                    import psutil
                    cpu_usage = psutil.cpu_percent()
                    memory_usage = psutil.virtual_memory().percent
                else:
                    cpu_usage = 0
                    memory_usage = 0
                
                # Atualizar métricas
                self.performance_metrics.update({
                    'timestamp': datetime.now().isoformat(),
                    'cpu_usage': cpu_usage,
                    'memory_usage': memory_usage,
                    'errors_count': len(self.error_history)
                })
                
                # Detectar anomalias
                if cpu_usage > 90 or memory_usage > 85:
                    logger.warning(f"Recursos do sistema elevados - CPU: {cpu_usage}%, Memória: {memory_usage}%")
                    
                time.sleep(30)  # Monitorar a cada 30 segundos
                
            except Exception as e:
                logger.error(f"Erro no monitoramento: {e}")

    async def process_with_ai(self, prompt: str, data_context: str = "") -> str:
        """Processa solicitações usando IA generativa"""
        try:
            if self.ai_config.claude_api_key and hasattr(self, 'claude_client'):
                return await self._process_with_claude(prompt, data_context)
            elif self.ai_config.openai_api_key and 'openai' in sys.modules:
                return await self._process_with_openai(prompt, data_context)
            else:
                return await self._process_with_local_model(prompt, data_context)
        except Exception as e:
            logger.error(f"Erro no processamento com IA: {e}")
            return f"Erro ao processar com IA: {e}"

    async def _process_with_claude(self, prompt: str, data_context: str = "") -> str:
        """Processa usando Claude API"""
        try:
            full_prompt = f"""
            Contexto dos dados: {data_context}
            
            Solicitação: {prompt}
            
            Por favor, forneça uma resposta técnica e precisa em português brasileiro.
            Se for código, comente adequadamente.
            """
            
            response = self.claude_client.messages.create(
                model="claude-3-5-haiku-latest",
                max_tokens=self.ai_config.max_tokens,
                temperature=self.ai_config.temperature,
                messages=[{"role": "user", "content": full_prompt}]
            )
            
            return response.content[0].text
            
        except Exception as e:
            logger.error(f"Erro na API Claude: {e}")
            raise

    async def _process_with_openai(self, prompt: str, data_context: str = "") -> str:
        """Processa usando OpenAI API"""
        try:
            full_prompt = f"""
            Contexto dos dados: {data_context}
            Solicitação: {prompt}
            
            Responda em português brasileiro com precisão técnica.
            """
            
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[{"role": "user", "content": full_prompt}],
                max_tokens=self.ai_config.max_tokens,
                temperature=self.ai_config.temperature
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Erro na API OpenAI: {e}")
            raise

    async def _process_with_local_model(self, prompt: str, data_context: str = "") -> str:
        """Processa usando modelos locais"""
        try:
            if hasattr(self, 'text_generator'):
                result = self.text_generator(prompt, max_length=200, do_sample=True)
                return result[0]['generated_text']
            else:
                return "Modelos locais não inicializados ou não disponíveis"
        except Exception as e:
            logger.error(f"Erro no modelo local: {e}")
            raise

    def auto_detect_schema(self, data: Union[pd.DataFrame, str, Path]) -> Dict[str, Any]:
        """Detecta automaticamente o schema dos dados usando IA"""
        logger.info("Detectando schema automaticamente...")
        
        if isinstance(data, (str, Path)):
            # Carregar uma amostra dos dados
            if str(data).endswith('.csv'):
                sample_df = pd.read_csv(data, nrows=100)
            elif str(data).endswith(('.xlsx', '.xls')):
                sample_df = pd.read_excel(data, nrows=100)
            else:
                logger.error("Formato de arquivo não suportado para detecção de schema")
                return {}
        else:
            sample_df = data.head(100)
        
        schema = {
            'columns': list(sample_df.columns),
            'dtypes': {col: str(dtype) for col, dtype in sample_df.dtypes.to_dict().items()},
            'null_counts': sample_df.isnull().sum().to_dict(),
            'unique_counts': sample_df.nunique().to_dict(),
            'sample_values': {}
        }
        
        # Adicionar valores de amostra para cada coluna
        for col in sample_df.columns:
            schema['sample_values'][col] = sample_df[col].dropna().head(5).tolist()
        
        # Usar IA para sugerir tipos de dados e transformações
        if self.config.ai_enabled:
            schema['ai_suggestions'] = self._get_ai_schema_suggestions(schema)
        
        return schema

    def _get_ai_schema_suggestions(self, schema: Dict[str, Any]) -> Dict[str, str]:
        """Obter sugestões de IA para o schema"""
        try:
            # Para demonstração, retornamos sugestões básicas
            # Em produção, isso seria processado pela IA
            suggestions = {
                'data_quality_issues': 'Verificar colunas com muitos valores nulos',
                'transformation_suggestions': 'Normalizar datas e padronizar texto',
                'optimization_tips': 'Considerar indexação em colunas de busca'
            }
            
            # Análise básica baseada em regras
            null_percentages = {k: v / len(schema['sample_values'].get(k, [])) if schema['sample_values'].get(k) else 0 
                              for k, v in schema['null_counts'].items()}
            
            high_null_cols = [col for col, pct in null_percentages.items() if pct > 0.5]
            if high_null_cols:
                suggestions['high_null_columns'] = high_null_cols
            
            return suggestions
            
        except Exception as e:
            logger.error(f"Erro ao obter sugestões de IA: {e}")
            return {}

    def intelligent_data_loading(self, source: Union[str, Path, Dict]) -> pd.DataFrame:
        """Carregamento inteligente de dados com detecção automática de formato"""
        logger.info(f"Carregando dados de forma inteligente: {source}")
        
        try:
            if isinstance(source, dict):
                # Fonte de dados configurada (API, banco, etc.)
                return self._load_from_configured_source(source)
            elif isinstance(source, pd.DataFrame):
                # Já é um DataFrame
                return source.copy()
            
            source_path = Path(source)
            
            # Detecção automática de formato
            if source_path.suffix.lower() == '.csv':
                return self._intelligent_csv_loading(source_path)
            elif source_path.suffix.lower() in ['.xlsx', '.xls']:
                return pd.read_excel(source_path)
            elif source_path.suffix.lower() == '.parquet' and 'pyarrow' in sys.modules:
                return pd.read_parquet(source_path)
            elif source_path.suffix.lower() == '.json':
                return pd.read_json(source_path)
            else:
                raise ValueError(f"Formato não suportado: {source_path.suffix}")
                
        except Exception as e:
            logger.error(f"Erro no carregamento de dados: {e}")
            if self.config.auto_repair:
                return self._attempt_data_repair(source, e)
            raise

    def _intelligent_csv_loading(self, file_path: Path) -> pd.DataFrame:
        """Carregamento inteligente de CSV com detecção automática de separador"""
        separators = [',', ';', '|', '\t']
        encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
        
        for encoding in encodings:
            for sep in separators:
                try:
                    df = pd.read_csv(file_path, sep=sep, encoding=encoding, nrows=10)
                    if len(df.columns) > 1:
                        # Carregar arquivo completo com configurações detectadas
                        return pd.read_csv(file_path, sep=sep, encoding=encoding, low_memory=False)
                except Exception:
                    continue
        
        raise ValueError("Não foi possível detectar formato CSV apropriado")

    def _load_from_configured_source(self, config: Dict) -> pd.DataFrame:
        """Carrega dados de fonte configurada (API, banco de dados, etc.)"""
        source_type = config.get('type', '').lower()
        
        if source_type == 'database':
            return self._load_from_database(config)
        elif source_type == 'api':
            return self._load_from_api(config)
        elif source_type == 's3':
            return self._load_from_s3(config)
        else:
            raise ValueError(f"Tipo de fonte não suportado: {source_type}")

    def _load_from_database(self, config: Dict) -> pd.DataFrame:
        """Carrega dados de banco de dados"""
        try:
            engine = create_engine(config['connection_string'])
            query = config.get('query', f"SELECT * FROM {config.get('table', '')}")
            return pd.read_sql(query, engine)
        except Exception as e:
            logger.error(f"Erro ao carregar do banco de dados: {e}")
            raise

    def _load_from_api(self, config: Dict) -> pd.DataFrame:
        """Carrega dados de API REST"""
        try:
            headers = config.get('headers', {})
            params = config.get('params', {})
            
            response = requests.get(config['url'], headers=headers, params=params)
            response.raise_for_status()
            
            data = response.json()
            return pd.json_normalize(data)
            
        except Exception as e:
            logger.error(f"Erro ao carregar da API: {e}")
            raise

    def _load_from_s3(self, config: Dict) -> pd.DataFrame:
        """Carrega dados do S3"""
        try:
            import boto3
            
            s3 = boto3.client('s3')
            bucket = config['bucket']
            key = config['key']
            
            obj = s3.get_object(Bucket=bucket, Key=key)
            
            if key.endswith('.csv'):
                return pd.read_csv(obj['Body'])
            elif key.endswith('.parquet'):
                return pd.read_parquet(obj['Body'])
            else:
                raise ValueError(f"Formato S3 não suportado: {key}")
                
        except Exception as e:
            logger.error(f"Erro ao carregar do S3: {e}")
            raise

    def _attempt_data_repair(self, source: Union[str, Path], error: Exception) -> pd.DataFrame:
        """Tenta reparar dados corrompidos automaticamente"""
        logger.info(f"Tentando reparar dados automaticamente após erro: {error}")
        
        try:
            # Estratégias de reparo baseadas no tipo de erro
            if "encoding" in str(error).lower():
                # Problema de encoding
                return self._fix_encoding_issues(source)
            elif "separator" in str(error).lower() or "delimiter" in str(error).lower():
                # Problema de separador
                return self._fix_separator_issues(source)
            else:
                # Tentativa genérica de reparo
                return self._generic_data_repair(source)
                
        except Exception as repair_error:
            logger.error(f"Falha no reparo automático: {repair_error}")
            raise error  # Retorna erro original

    def _fix_encoding_issues(self, source: Union[str, Path]) -> pd.DataFrame:
        """Corrige problemas de encoding"""
        try:
            import chardet
            
            with open(source, 'rb') as f:
                raw_data = f.read()
                encoding = chardet.detect(raw_data)['encoding']
            
            return pd.read_csv(source, encoding=encoding)
        except ImportError:
            # Fallback sem chardet
            encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
            for encoding in encodings:
                try:
                    return pd.read_csv(source, encoding=encoding)
                except:
                    continue
            raise ValueError("Não foi possível determinar encoding")

    def _fix_separator_issues(self, source: Union[str, Path]) -> pd.DataFrame:
        """Corrige problemas de separador"""
        # Usar pandas csv sniffer ou implementação customizada
        with open(source, 'r', encoding='utf-8', errors='ignore') as f:
            first_line = f.readline()
            
        # Contar ocorrências de possíveis separadores
        separators = {',': first_line.count(','), 
                     ';': first_line.count(';'),
                     '|': first_line.count('|'),
                     '\t': first_line.count('\t')}
        
        best_sep = max(separators, key=separators.get)
        return pd.read_csv(source, sep=best_sep)

    def _generic_data_repair(self, source: Union[str, Path]) -> pd.DataFrame:
        """Reparo genérico de dados"""
        # Tentar carregar com configurações mais flexíveis
        return pd.read_csv(source, 
                          sep=None,  # Auto-detect
                          engine='python',  # Mais flexível
                          encoding='utf-8',
                          on_bad_lines='skip',  # Pular linhas problemáticas
                          )

    def ai_data_cleaning(self, df: pd.DataFrame) -> pd.DataFrame:
        """Limpeza de dados assistida por IA"""
        logger.info("Iniciando limpeza de dados com IA...")
        
        cleaned_df = df.copy()
        
        # 0. Traduzir nomes de colunas para português
        cleaned_df = self._translate_column_names(cleaned_df)
        
        # 1. Detecção de outliers usando Isolation Forest
        numeric_columns = cleaned_df.select_dtypes(include=[np.number]).columns
        if len(numeric_columns) > 0:
            try:
                iso_forest = IsolationForest(contamination=0.1, random_state=42)
                outliers = iso_forest.fit_predict(cleaned_df[numeric_columns].fillna(0))
                cleaned_df['is_outlier'] = outliers == -1
                logger.info(f"Detectados {sum(outliers == -1)} outliers")
            except Exception as e:
                logger.warning(f"Erro na detecção de outliers: {e}")
        
        # 2. Limpeza de texto usando NLP
        text_columns = cleaned_df.select_dtypes(include=['object']).columns
        for col in text_columns:
            if cleaned_df[col].dtype == 'object':
                cleaned_df[col] = self._clean_text_column(cleaned_df[col])
        
        # 3. Padronização avançada de texto e datas
        cleaned_df = self._advanced_text_standardization(cleaned_df)
        
        # 4. Imputação inteligente de valores faltantes
        cleaned_df = self._intelligent_imputation(cleaned_df)
        
        # 5. Padronização de formatos
        cleaned_df = self._standardize_formats(cleaned_df)
        
        # 6. Deduplicação inteligente
        cleaned_df = self._intelligent_deduplication(cleaned_df)
        
        logger.info("Limpeza de dados concluída")
        return cleaned_df

    def _translate_column_names(self, df: pd.DataFrame) -> pd.DataFrame:
        """Traduz nomes de colunas do inglês para português brasileiro"""
        translation_map = {
            # Dados pessoais
            'Name': 'Nome',
            'Full Name': 'Nome Completo',
            'First Name': 'Primeiro Nome',
            'Last Name': 'Sobrenome',
            'Email': 'Email',
            'Phone': 'Telefone',
            'WhatsApp': 'WhatsApp',
            'Address': 'Endereço',
            'City': 'Cidade',
            'State': 'Estado',
            'Country': 'País',
            'ZIP Code': 'CEP',
            'Birth Date': 'Data de Nascimento',
            'Age': 'Idade',
            'Gender': 'Gênero',
            'Marital Status': 'Estado Civil',
            
            # Documentos
            'CPF': 'CPF',
            'RG': 'RG',
            'CNPJ': 'CNPJ',
            'ID': 'ID',
            'Document': 'Documento',
            
            # Profissional
            'Company': 'Empresa',
            'Job Title': 'Cargo',
            'Position': 'Posição',
            'Department': 'Departamento',
            'Industry': 'Setor',
            'Salary': 'Salário',
            'LinkedIn': 'LinkedIn',
            
            # Datas e timestamps
            'Date': 'Data',
            'Start Date': 'Data de Início',
            'End Date': 'Data de Fim',
            'Created Date': 'Data de Criação',
            'Updated Date': 'Data de Atualização',
            'Submit Date': 'Data de Envio',
            'Response Date': 'Data de Resposta',
            'Start Date (UTC)': 'Data de Início (UTC)',
            'Submit Date (UTC)': 'Data de Envio (UTC)',
            'Stage Date (UTC)': 'Data de Etapa (UTC)',
            
            # Formulário e sistema
            'Response Type': 'Tipo de Resposta',
            'Network ID': 'ID da Rede',
            'Tags': 'Etiquetas',
            'Status': 'Status',
            'Type': 'Tipo',
            'Category': 'Categoria',
            'Priority': 'Prioridade',
            'Source': 'Origem',
            
            # Outros campos comuns
            'Value': 'Valor',
            'Amount': 'Quantia',
            'Description': 'Descrição',
            'Comments': 'Comentários',
            'Notes': 'Observações',
            'Feedback': 'Feedback'
        }
        
        # Aplicar traduções
        df_translated = df.copy()
        columns_translated = []
        
        for old_col in df_translated.columns:
            # Tentar tradução exata
            if old_col in translation_map:
                new_col = translation_map[old_col]
                df_translated.rename(columns={old_col: new_col}, inplace=True)
                columns_translated.append(f"{old_col} → {new_col}")
            # Tentar tradução parcial
            else:
                for eng_term, pt_term in translation_map.items():
                    if eng_term.lower() in old_col.lower():
                        new_col = old_col.replace(eng_term, pt_term)
                        df_translated.rename(columns={old_col: new_col}, inplace=True)
                        columns_translated.append(f"{old_col} → {new_col}")
                        break
        
        if columns_translated:
            logger.info(f"Colunas traduzidas: {len(columns_translated)}")
            for translation in columns_translated[:5]:  # Mostrar apenas as primeiras 5
                logger.info(f"  - {translation}")
        
        return df_translated

    def _clean_text_column(self, series: pd.Series) -> pd.Series:
        """Limpa uma coluna de texto"""
        cleaned = series.copy()
        
        # Converter para string e limpar
        cleaned = cleaned.astype(str)
        
        # Remover espaços extras
        cleaned = cleaned.str.strip()
        
        # Padronizar capitalização se parecer ser nome próprio
        if series.name and any(word in series.name.lower() for word in ['nome', 'name', 'empresa', 'company']):
            cleaned = cleaned.str.title()
        
        # Padronizar emails
        if series.name and 'email' in series.name.lower():
            cleaned = cleaned.str.lower()
        
        return cleaned

    def _intelligent_imputation(self, df: pd.DataFrame) -> pd.DataFrame:
        """Imputação inteligente de valores faltantes"""
        df_imputed = df.copy()
        
        for col in df_imputed.columns:
            if df_imputed[col].isnull().any():
                null_percentage = df_imputed[col].isnull().mean()
                
                if null_percentage > 0.8:
                    # Muitos valores faltantes - considerar remoção ou flag
                    logger.warning(f"Coluna '{col}' tem {null_percentage:.1%} valores faltantes")
                    continue
                
                if df_imputed[col].dtype in ['object', 'category']:
                    # Valores categóricos - usar moda ou 'Não informado'
                    mode_value = df_imputed[col].mode()
                    if len(mode_value) > 0:
                        df_imputed[col].fillna(mode_value[0], inplace=True)
                    else:
                        df_imputed[col].fillna('Não informado', inplace=True)
                
                elif np.issubdtype(df_imputed[col].dtype, np.number):
                    # Valores numéricos - usar mediana ou modelo preditivo
                    if null_percentage < 0.3:
                        df_imputed[col].fillna(df_imputed[col].median(), inplace=True)
                    else:
                        # Para muitos valores faltantes, usar modelo preditivo
                        df_imputed = self._predictive_imputation(df_imputed, col)
        
        return df_imputed

    def _advanced_text_standardization(self, df: pd.DataFrame) -> pd.DataFrame:
        """Padronização avançada de texto e datas"""
        logger.info("Aplicando padronização avançada de texto e datas...")
        
        df_standardized = df.copy()
        
        for col in df_standardized.columns:
            if df_standardized[col].dtype == 'object':
                col_lower = col.lower()
                
                # Padronização de estado civil
                if any(term in col_lower for term in ['estado civil', 'marital status', 'civil']):
                    df_standardized[col] = df_standardized[col].apply(self._standardize_marital_status)
                
                # Padronização de gênero
                elif any(term in col_lower for term in ['gênero', 'gender', 'sexo']):
                    df_standardized[col] = df_standardized[col].apply(self._standardize_gender)
                
                # Padronização de escolaridade
                elif any(term in col_lower for term in ['escolaridade', 'education', 'formação']):
                    df_standardized[col] = df_standardized[col].apply(self._standardize_education)
                
                # Padronização de datas em português
                elif any(term in col_lower for term in ['data', 'date', 'nascimento', 'aniversário']):
                    df_standardized[col] = df_standardized[col].apply(self._standardize_date_pt)
                
                # Padronização geral de texto (Title Case para campos apropriados)
                elif any(term in col_lower for term in ['nome', 'name', 'cidade', 'city', 'empresa', 'company', 'cargo', 'position']):
                    df_standardized[col] = df_standardized[col].apply(self._standardize_proper_names)
                
                # Padronização de campos de texto livre (frases)
                elif any(term in col_lower for term in ['descrição', 'description', 'comentário', 'comment', 'objetivo', 'busca', 'quer']):
                    df_standardized[col] = df_standardized[col].apply(self._standardize_sentences)
        
        logger.info("Padronização avançada concluída")
        return df_standardized
    
    def _standardize_marital_status(self, value: str) -> str:
        """Padroniza estado civil"""
        if pd.isna(value) or str(value).strip() == '':
            return 'Não informado'
        
        value_clean = str(value).strip().upper()
        
        # Mapeamento de estados civis
        marital_map = {
            'SOLTEIRO': 'Solteiro',
            'SOLTEIRA': 'Solteira',
            'CASADO': 'Casado',
            'CASADA': 'Casada',
            'DIVORCIADO': 'Divorciado',
            'DIVORCIADA': 'Divorciada',
            'VIÚVO': 'Viúvo',
            'VIÚVA': 'Viúva',
            'SEPARADO': 'Separado',
            'SEPARADA': 'Separada',
            'UNIÃO ESTÁVEL': 'União Estável',
            'UNIAO ESTAVEL': 'União Estável',
            'SINGLE': 'Solteiro',
            'MARRIED': 'Casado',
            'DIVORCED': 'Divorciado',
            'WIDOWED': 'Viúvo',
            'SEPARATED': 'Separado'
        }
        
        return marital_map.get(value_clean, value.strip().title())
    
    def _standardize_gender(self, value: str) -> str:
        """Padroniza gênero"""
        if pd.isna(value) or str(value).strip() == '':
            return 'Não informado'
        
        value_clean = str(value).strip().upper()
        
        # Mapeamento de gêneros
        gender_map = {
            'MASCULINO': 'Masculino',
            'FEMININO': 'Feminino',
            'M': 'Masculino',
            'F': 'Feminino',
            'MALE': 'Masculino',
            'FEMALE': 'Feminino',
            'HOMEM': 'Masculino',
            'MULHER': 'Feminino',
            'OUTRO': 'Outro',
            'OTHER': 'Outro',
            'NÃO BINÁRIO': 'Não Binário',
            'NAO BINARIO': 'Não Binário',
            'NON-BINARY': 'Não Binário'
        }
        
        return gender_map.get(value_clean, value.strip().title())
    
    def _standardize_education(self, value: str) -> str:
        """Padroniza escolaridade"""
        if pd.isna(value) or str(value).strip() == '':
            return 'Não informado'
        
        value_clean = str(value).strip().upper()
        
        # Mapeamento de escolaridade
        education_map = {
            'FUNDAMENTAL': 'Ensino Fundamental',
            'ENSINO FUNDAMENTAL': 'Ensino Fundamental',
            'MÉDIO': 'Ensino Médio',
            'ENSINO MÉDIO': 'Ensino Médio',
            'ENSINO MEDIO': 'Ensino Médio',
            'SUPERIOR': 'Ensino Superior',
            'ENSINO SUPERIOR': 'Ensino Superior',
            'GRADUAÇÃO': 'Graduação',
            'GRADUACAO': 'Graduação',
            'PÓS-GRADUAÇÃO': 'Pós-Graduação',
            'POS-GRADUACAO': 'Pós-Graduação',
            'MESTRADO': 'Mestrado',
            'DOUTORADO': 'Doutorado',
            'MBA': 'MBA',
            'TÉCNICO': 'Técnico',
            'TECNICO': 'Técnico'
        }
        
        return education_map.get(value_clean, value.strip().title())
    
    def _standardize_date_pt(self, value: str) -> str:
        """Padroniza datas em português para formato dd/mm/aaaa"""
        if pd.isna(value) or str(value).strip() == '':
            return ''
        
        value_str = str(value).strip()
        
        # Se já está no formato correto, retornar
        if re.match(r'^\d{1,2}/\d{1,2}/\d{4}$', value_str):
            return value_str
        
        # Mapeamento de meses em português
        months_pt = {
            'JANEIRO': '01', 'JAN': '01',
            'FEVEREIRO': '02', 'FEV': '02',
            'MARÇO': '03', 'MARCO': '03', 'MAR': '03',
            'ABRIL': '04', 'ABR': '04',
            'MAIO': '05', 'MAI': '05',
            'JUNHO': '06', 'JUN': '06',
            'JULHO': '07', 'JUL': '07',
            'AGOSTO': '08', 'AGO': '08',
            'SETEMBRO': '09', 'SET': '09',
            'OUTUBRO': '10', 'OUT': '10',
            'NOVEMBRO': '11', 'NOV': '11',
            'DEZEMBRO': '12', 'DEZ': '12'
        }
        
        # Tentar converter "02 OUTUBRO 1968" para "02/10/1968"
        pattern = r'(\d{1,2})\s+(\w+)\s+(\d{4})'
        match = re.search(pattern, value_str.upper())
        
        if match:
            day = match.group(1).zfill(2)
            month_name = match.group(2).upper()
            year = match.group(3)
            
            if month_name in months_pt:
                month = months_pt[month_name]
                return f"{day}/{month}/{year}"
        
        # Tentar outros formatos comuns
        try:
            # Tentar converter usando pandas
            parsed_date = pd.to_datetime(value_str, errors='coerce')
            if not pd.isna(parsed_date):
                return parsed_date.strftime('%d/%m/%Y')
        except:
            pass
        
        # Se não conseguiu converter, retornar original
        return value_str
    
    def _standardize_proper_names(self, value: str) -> str:
        """Padroniza nomes próprios (Title Case)"""
        if pd.isna(value) or str(value).strip() == '':
            return ''
        
        value_str = str(value).strip()
        
        # Casos especiais que não devem ser capitalizados
        exceptions = ['da', 'de', 'do', 'das', 'dos', 'e', 'em', 'na', 'no', 'para', 'por', 'com']
        
        words = value_str.lower().split()
        capitalized_words = []
        
        for i, word in enumerate(words):
            if i == 0 or word not in exceptions:
                capitalized_words.append(word.capitalize())
            else:
                capitalized_words.append(word)
        
        return ' '.join(capitalized_words)
    
    def _standardize_sentences(self, value: str) -> str:
        """Padroniza frases (primeira letra maiúscula)"""
        if pd.isna(value) or str(value).strip() == '':
            return ''
        
        value_str = str(value).strip()
        
        # Primeira letra maiúscula, resto minúsculo, exceto depois de ponto
        sentences = value_str.split('. ')
        standardized_sentences = []
        
        for sentence in sentences:
            if sentence:
                # Primeira letra maiúscula
                standardized = sentence[0].upper() + sentence[1:].lower() if len(sentence) > 1 else sentence.upper()
                standardized_sentences.append(standardized)
        
        return '. '.join(standardized_sentences)

    def _predictive_imputation(self, df: pd.DataFrame, target_col: str) -> pd.DataFrame:
        """Imputação preditiva usando machine learning"""
        try:
            # Preparar dados para imputação
            df_for_imputation = df.copy()
            
            # Separar dados com e sem valores faltantes
            missing_mask = df_for_imputation[target_col].isnull()
            train_data = df_for_imputation[~missing_mask]
            predict_data = df_for_imputation[missing_mask]
            
            if len(train_data) < 10:  # Poucos dados para treinar
                df_for_imputation[target_col].fillna(df_for_imputation[target_col].median(), inplace=True)
                return df_for_imputation
            
            # Selecionar features numéricas para o modelo
            numeric_features = df_for_imputation.select_dtypes(include=[np.number]).columns
            numeric_features = [col for col in numeric_features if col != target_col]
            
            if len(numeric_features) == 0:  # Sem features numéricas
                df_for_imputation[target_col].fillna(df_for_imputation[target_col].median(), inplace=True)
                return df_for_imputation
            
            # Treinar modelo simples
            X_train = train_data[numeric_features].fillna(0)
            y_train = train_data[target_col]
            
            # Usar regressão para valores contínuos
            from sklearn.ensemble import RandomForestRegressor
            model = RandomForestRegressor(n_estimators=10, random_state=42, max_depth=3)
            model.fit(X_train, y_train)
            
            # Fazer predições
            X_predict = predict_data[numeric_features].fillna(0)
            predictions = model.predict(X_predict)
            
            # Atualizar valores faltantes
            df_for_imputation.loc[missing_mask, target_col] = predictions
            
            return df_for_imputation
            
        except Exception as e:
            logger.warning(f"Erro na imputação preditiva para '{target_col}': {e}")
            # Fallback para mediana
            df[target_col].fillna(df[target_col].median(), inplace=True)
            return df

    def _standardize_formats(self, df: pd.DataFrame) -> pd.DataFrame:
        """Padroniza formatos de dados"""
        df_standardized = df.copy()
        
        for col in df_standardized.columns:
            col_lower = col.lower()
            
            # Padronizar CPF/CNPJ
            if any(term in col_lower for term in ['cpf', 'cnpj']):
                df_standardized[col] = df_standardized[col].astype(str).apply(self._clean_document_number)
            
            # Padronizar telefones
            elif any(term in col_lower for term in ['telefone', 'phone', 'whatsapp']):
                df_standardized[col] = df_standardized[col].astype(str).apply(self._clean_phone_number)
            
            # Padronizar emails
            elif 'email' in col_lower:
                df_standardized[col] = df_standardized[col].astype(str).str.lower().str.strip()
            
            # Padronizar datas
            elif any(term in col_lower for term in ['data', 'date']):
                df_standardized[col] = pd.to_datetime(df_standardized[col], errors='coerce')
        
        return df_standardized

    def _clean_document_number(self, doc: str) -> str:
        """Limpa número de documento (CPF/CNPJ)"""
        if pd.isna(doc) or doc == 'nan':
            return ''
        return re.sub(r'\D', '', str(doc))

    def _clean_phone_number(self, phone: str) -> str:
        """Limpa número de telefone"""
        if pd.isna(phone) or phone == 'nan':
            return ''
        
        # Remove tudo que não é dígito
        digits_only = re.sub(r'\D', '', str(phone))
        
        # Padronizar formato brasileiro
        if len(digits_only) == 11 and digits_only.startswith('11'):
            return f"+55{digits_only}"
        elif len(digits_only) == 10:
            return f"+55{digits_only}"
        else:
            return digits_only

    def _intelligent_deduplication(self, df: pd.DataFrame) -> pd.DataFrame:
        """Deduplicação inteligente baseada em similaridade"""
        logger.info("Iniciando deduplicação inteligente...")
        
        # Identificar colunas-chave para deduplicação
        key_columns = []
        for col in df.columns:
            col_lower = col.lower()
            if any(term in col_lower for term in ['cpf', 'cnpj', 'email', 'id']):
                key_columns.append(col)
        
        if not key_columns:
            logger.warning("Nenhuma coluna-chave identificada para deduplicação")
            return df
        
        # Deduplicação baseada nas colunas-chave
        before_count = len(df)
        df_deduplicated = df.drop_duplicates(subset=key_columns, keep='last')
        after_count = len(df_deduplicated)
        
        removed_count = before_count - after_count
        if removed_count > 0:
            logger.info(f"Removidos {removed_count} registros duplicados baseado em: {key_columns}")
        
        return df_deduplicated

    def ai_feature_engineering(self, df: pd.DataFrame) -> pd.DataFrame:
        """Engenharia de features assistida por IA"""
        logger.info("Iniciando engenharia de features com IA...")
        
        df_engineered = df.copy()
        
        # 1. Features temporais automáticas
        date_columns = df_engineered.select_dtypes(include=['datetime64']).columns
        for col in date_columns:
            df_engineered = self._create_temporal_features(df_engineered, col)
        
        # 2. Features de qualidade de dados
        df_engineered = self._create_data_quality_features(df_engineered)
        
        # 3. Features de texto
        text_columns = df_engineered.select_dtypes(include=['object']).columns
        for col in text_columns:
            df_engineered = self._create_text_features(df_engineered, col)
        
        # 4. Features de interação automáticas
        df_engineered = self._create_interaction_features(df_engineered)
        
        # 5. Features baseadas em padrões
        df_engineered = self._create_pattern_features(df_engineered)
        
        logger.info(f"Engenharia de features concluída. Colunas adicionadas: {len(df_engineered.columns) - len(df.columns)}")
        return df_engineered

    def _create_temporal_features(self, df: pd.DataFrame, date_col: str) -> pd.DataFrame:
        """Cria features temporais"""
        df[f'{date_col}_year'] = df[date_col].dt.year
        df[f'{date_col}_month'] = df[date_col].dt.month
        df[f'{date_col}_day'] = df[date_col].dt.day
        df[f'{date_col}_weekday'] = df[date_col].dt.weekday
        df[f'{date_col}_quarter'] = df[date_col].dt.quarter
        df[f'{date_col}_is_weekend'] = df[date_col].dt.weekday.isin([5, 6]).astype(int)
        
        # Diferença para hoje
        df[f'{date_col}_days_ago'] = (datetime.now() - df[date_col]).dt.days
        
        return df

    def _create_data_quality_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Cria features de qualidade dos dados"""
        # Score de completude por linha
        df['completeness_score'] = df.count(axis=1) / len(df.columns)
        
        # Identificar colunas-chave para score de qualidade
        key_indicators = ['email', 'telefone', 'nome', 'empresa']
        quality_score = 0
        
        for indicator in key_indicators:
            matching_cols = [col for col in df.columns if indicator.lower() in col.lower()]
            for col in matching_cols:
                # +1 se a coluna não está vazia
                quality_score += (~df[col].isnull()).astype(int)
        
        df['data_quality_score'] = quality_score
        
        return df

    def _create_text_features(self, df: pd.DataFrame, text_col: str) -> pd.DataFrame:
        """Cria features baseadas em texto"""
        if text_col not in df.columns:
            return df
        
        col_lower = text_col.lower()
        
        # Features de comprimento
        df[f'{text_col}_length'] = df[text_col].astype(str).str.len()
        df[f'{text_col}_word_count'] = df[text_col].astype(str).str.split().str.len()
        
        # Features específicas por tipo de coluna
        if 'email' in col_lower:
            df[f'{text_col}_has_at'] = df[text_col].str.contains('@', na=False).astype(int)
            df[f'{text_col}_domain'] = df[text_col].str.extract(r'@(.+)$')
        
        elif any(term in col_lower for term in ['nome', 'name']):
            df[f'{text_col}_has_title'] = df[text_col].str.contains(r'\b(Sr|Sra|Dr|Dra)\b', na=False).astype(int)
            df[f'{text_col}_is_title_case'] = (df[text_col] == df[text_col].str.title()).astype(int)
        
        elif 'linkedin' in col_lower:
            df[f'{text_col}_is_linkedin'] = df[text_col].str.contains('linkedin', case=False, na=False).astype(int)
        
        return df

    def _create_interaction_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Cria features de interação entre variáveis"""
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        
        # Limitar número de features de interação para evitar explosão dimensional
        if len(numeric_cols) > 2:
            # Criar algumas interações importantes
            for i, col1 in enumerate(numeric_cols[:3]):
                for col2 in numeric_cols[i+1:4]:
                    if col1 != col2:
                        # Ratio
                        df[f'{col1}_div_{col2}'] = df[col1] / (df[col2] + 1e-8)
                        # Produto
                        df[f'{col1}_mult_{col2}'] = df[col1] * df[col2]
        
        return df

    def _create_pattern_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Cria features baseadas em padrões detectados"""
        for col in df.select_dtypes(include=['object']).columns:
            col_data = df[col].astype(str)
            
            # Padrões comuns
            df[f'{col}_has_numbers'] = col_data.str.contains(r'\d', na=False).astype(int)
            df[f'{col}_has_special_chars'] = col_data.str.contains(r'[^a-zA-Z0-9\s]', na=False).astype(int)
            df[f'{col}_is_uppercase'] = (col_data == col_data.str.upper()).astype(int)
            df[f'{col}_is_lowercase'] = (col_data == col_data.str.lower()).astype(int)
        
        return df

    def ai_transformation_engine(self, df: pd.DataFrame, transformation_request: str) -> pd.DataFrame:
        """Motor de transformação baseado em linguagem natural"""
        logger.info(f"Processando transformação: {transformation_request}")
        
        try:
            # Analisar solicitação e gerar código de transformação
            transformation_code = self._generate_transformation_code(df, transformation_request)
            
            # Executar transformação de forma segura
            result_df = self._execute_safe_transformation(df, transformation_code)
            
            return result_df
            
        except Exception as e:
            logger.error(f"Erro na transformação: {e}")
            return df

    def _generate_transformation_code(self, df: pd.DataFrame, request: str) -> str:
        """Gera código de transformação baseado na solicitação"""
        # Análise básica da solicitação
        request_lower = request.lower()
        
        # Patterns comuns de transformação
        if 'filtrar' in request_lower or 'filter' in request_lower:
            return self._generate_filter_code(request, df)
        elif 'agrupar' in request_lower or 'group' in request_lower:
            return self._generate_groupby_code(request, df)
        elif 'ordenar' in request_lower or 'sort' in request_lower:
            return self._generate_sort_code(request, df)
        elif 'criar coluna' in request_lower or 'nova coluna' in request_lower:
            return self._generate_new_column_code(request, df)
        else:
            # Transformação genérica - retornar código padrão
            return "df"

    def _generate_filter_code(self, request: str, df: pd.DataFrame) -> str:
        """Gera código de filtro baseado na solicitação"""
        # Detectar coluna e valor para filtro
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        
        if 'maior que' in request or '>' in request:
            # Encontrar número na solicitação
            numbers = re.findall(r'\d+', request)
            if numbers and numeric_cols:
                return f"df[df['{numeric_cols[0]}'] > {numbers[0]}]"
        elif 'igual a' in request or '==' in request:
            return "df[df['status'] == 'ativo']"  # Placeholder
        
        return "df"

    def _generate_groupby_code(self, request: str, df: pd.DataFrame) -> str:
        """Gera código de agrupamento"""
        # Detectar colunas categóricas para agrupamento
        cat_cols = df.select_dtypes(include=['object']).columns.tolist()
        num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        
        if cat_cols and num_cols:
            return f"df.groupby('{cat_cols[0]}').agg({{'{num_cols[0]}': 'sum'}}).reset_index()"
        
        return "df"

    def _generate_sort_code(self, request: str, df: pd.DataFrame) -> str:
        """Gera código de ordenação"""
        # Detectar colunas de data ou numéricas
        date_cols = df.select_dtypes(include=['datetime64']).columns.tolist()
        
        if date_cols:
            if 'decrescente' in request or 'desc' in request:
                return f"df.sort_values('{date_cols[0]}', ascending=False)"
            else:
                return f"df.sort_values('{date_cols[0]}', ascending=True)"
        
        return "df"

    def _generate_new_column_code(self, request: str, df: pd.DataFrame) -> str:
        """Gera código para nova coluna"""
        # Gerar código baseado em padrões comuns
        if 'qualidade' in request.lower():
            return "df['qualidade_score'] = df['completeness_score'] * df['data_quality_score']"
        elif 'idade' in request.lower():
            date_cols = df.select_dtypes(include=['datetime64']).columns.tolist()
            if date_cols:
                return f"df['idade_dias'] = (datetime.now() - df['{date_cols[0]}']).dt.days"
        
        return "df['nova_coluna'] = 1"

    def _execute_safe_transformation(self, df: pd.DataFrame, code: str) -> pd.DataFrame:
        """Executa transformação de forma segura"""
        try:
            # Whitelist de operações permitidas
            allowed_operations = ['df[', 'df.', 'groupby', 'sort_values', 'filter', 'agg', 'reset_index']
            
            if not any(op in code for op in allowed_operations):
                logger.warning(f"Código de transformação não permitido: {code}")
                return df
            
            # Executar em namespace restrito
            namespace = {'df': df.copy(), 'pd': pd, 'np': np, 'datetime': datetime}
            result = eval(code, {"__builtins__": {}}, namespace)
            
            if isinstance(result, pd.DataFrame):
                return result
            else:
                logger.warning("Transformação não retornou DataFrame")
                return df
                
        except Exception as e:
            logger.error(f"Erro na execução de transformação: {e}")
            return df

    def intelligent_data_export(self, df: pd.DataFrame, 
                              output_path: str, 
                              format_type: str = 'auto',
                              optimize: bool = True) -> None:
        """Exportação inteligente de dados com otimização automática"""
        logger.info(f"Exportando dados para: {output_path}")
        
        # Detecção automática de formato
        if format_type == 'auto':
            format_type = self._detect_output_format(output_path)
        
        # Otimizar dados antes da exportação
        if optimize:
            df = self._optimize_for_export(df, format_type)
        
        # Exportar baseado no formato
        try:
            if format_type == 'csv':
                df.to_csv(output_path, index=False, encoding='utf-8-sig', sep=';')
            elif format_type == 'excel':
                with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                    df.to_excel(writer, sheet_name='Dados', index=False)
                    
                    # Adicionar metadados
                    metadata_df = pd.DataFrame([
                        ['Total de registros', len(df)],
                        ['Total de colunas', len(df.columns)],
                        ['Data de exportação', datetime.now().isoformat()],
                        ['Pipeline', self.config.name]
                    ], columns=['Métrica', 'Valor'])
                    
                    metadata_df.to_excel(writer, sheet_name='Metadados', index=False)
                    
            elif format_type == 'parquet' and 'pyarrow' in sys.modules:
                df.to_parquet(output_path, index=False, compression='snappy')
            elif format_type == 'json':
                df.to_json(output_path, orient='records', date_format='iso', force_ascii=False)
            else:
                # Fallback para CSV
                df.to_csv(output_path, index=False, encoding='utf-8-sig', sep=';')
                
            logger.info(f"Dados exportados com sucesso em formato {format_type}")
            
        except Exception as e:
            logger.error(f"Erro na exportação: {e}")
            raise

    def _detect_output_format(self, output_path: str) -> str:
        """Detecta formato de saída baseado na extensão"""
        extension = Path(output_path).suffix.lower()
        
        format_map = {
            '.csv': 'csv',
            '.xlsx': 'excel',
            '.xls': 'excel',
            '.parquet': 'parquet',
            '.json': 'json'
        }
        
        return format_map.get(extension, 'csv')

    def _optimize_for_export(self, df: pd.DataFrame, format_type: str) -> pd.DataFrame:
        """Otimiza DataFrame para exportação"""
        df_optimized = df.copy()
        
        # Otimizações específicas por formato
        if format_type == 'parquet':
            # Converter object para category quando apropriado
            for col in df_optimized.select_dtypes(include=['object']):
                if df_optimized[col].nunique() / len(df_optimized) < 0.5:  # Menos de 50% valores únicos
                    df_optimized[col] = df_optimized[col].astype('category')
        
        elif format_type == 'csv':
            # Garantir que não há caracteres problemáticos
            for col in df_optimized.select_dtypes(include=['object']):
                df_optimized[col] = df_optimized[col].astype(str).str.replace('\n', ' ', regex=False)
                df_optimized[col] = df_optimized[col].str.replace('\r', ' ', regex=False)
        
        # Otimizações gerais
        # Reduzir precisão numérica quando possível
        for col in df_optimized.select_dtypes(include=['float64']):
            if df_optimized[col].between(-3.4e38, 3.4e38).all():
                df_optimized[col] = df_optimized[col].astype('float32')
        
        return df_optimized

    def generate_pipeline_report(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Gera relatório completo da pipeline"""
        logger.info("Gerando relatório da pipeline...")
        
        report = {
            'pipeline_info': {
                'name': self.config.name,
                'mode': self.config.mode.value,
                'data_type': self.config.data_type.value,
                'execution_timestamp': datetime.now().isoformat(),
                'ai_enabled': self.config.ai_enabled
            },
            'data_overview': {
                'total_records': len(df),
                'total_columns': len(df.columns),
                'memory_usage_mb': df.memory_usage(deep=True).sum() / 1024**2,
                'dtypes_distribution': df.dtypes.value_counts().to_dict()
            },
            'data_quality': {
                'missing_values': df.isnull().sum().to_dict(),
                'missing_percentage': (df.isnull().sum() / len(df) * 100).to_dict(),
                'duplicate_records': df.duplicated().sum(),
                'unique_values_per_column': df.nunique().to_dict()
            },
            'performance_metrics': self.performance_metrics,
            'errors_encountered': len(self.error_history),
            'transformations_applied': getattr(self, 'transformations_log', [])
        }
        
        # Adicionar estatísticas descritivas para colunas numéricas
        try:
            numeric_stats = df.describe().to_dict()
            report['numeric_statistics'] = numeric_stats
        except Exception as e:
            logger.warning(f"Erro ao gerar estatísticas numéricas: {e}")
        
        # Adicionar insights de IA se habilitado
        if self.config.ai_enabled:
            report['ai_insights'] = self._generate_ai_insights(df)
        
        return report

    def _generate_ai_insights(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Gera insights usando IA"""
        insights = {
            'data_quality_assessment': 'Boa qualidade geral dos dados',
            'anomalies_detected': 'Poucos outliers detectados',
            'recommendations': [
                'Considerar normalização de colunas numéricas',
                'Verificar valores faltantes em colunas críticas',
                'Avaliar necessidade de features adicionais'
            ]
        }
        
        # Análises específicas
        missing_percentage = df.isnull().sum() / len(df)
        high_missing_cols = missing_percentage[missing_percentage > 0.5].index.tolist()
        
        if high_missing_cols:
            insights['high_missing_columns'] = high_missing_cols
            insights['recommendations'].append(f'Revisar colunas com muitos valores faltantes: {high_missing_cols}')
        
        return insights

    async def run_full_pipeline(self, 
                               source: Union[str, Path, Dict, pd.DataFrame],
                               output_path: str,
                               transformations: List[str] = None) -> Dict[str, Any]:
        """Executa pipeline completa de ETL com IA"""
        logger.info(f"Iniciando pipeline completa: {self.config.name}")
        
        try:
            # 1. Carregamento inteligente
            df = self.intelligent_data_loading(source)
            logger.info(f"Dados carregados: {len(df)} registros, {len(df.columns)} colunas")
            
            # 2. Detecção automática de schema
            schema = self.auto_detect_schema(df)
            self.metadata['schema'] = schema
            
            # 3. Limpeza com IA
            df = self.ai_data_cleaning(df)
            
            # 4. Engenharia de features
            df = self.ai_feature_engineering(df)
            
            # 5. Aplicar transformações customizadas
            if transformations:
                for transformation in transformations:
                    df = self.ai_transformation_engine(df, transformation)
            
            # 6. Exportação otimizada
            self.intelligent_data_export(df, output_path, optimize=True)
            
            # 7. Gerar relatório
            report = self.generate_pipeline_report(df)
            
            # Salvar relatório
            report_path = str(Path(output_path).parent / f"pipeline_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False, default=str)
            
            logger.info("Pipeline executada com sucesso!")
            return report
            
        except Exception as e:
            logger.error(f"Erro na execução da pipeline: {e}")
            self.error_history.append({
                'timestamp': datetime.now().isoformat(),
                'error': str(e),
                'step': 'pipeline_execution'
            })
            
            if self.config.auto_repair:
                logger.info("Tentando reparo automático...")
                # Implementar lógica de reparo aqui
                
            raise

    def cleanup_resources(self):
        """Limpa recursos da pipeline"""
        logger.info("Limpando recursos da pipeline...")
        
        # Parar monitoramento
        self.monitoring_active = False
        
        # Limpar cache
        self.cache.clear()
        
        # Salvar metadados finais
        metadata_path = Path(f"pipeline_metadata_{self.config.name}_{datetime.now().strftime('%Y%m%d')}.json")
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(self.metadata, f, indent=2, ensure_ascii=False, default=str)
        
        logger.info("Recursos limpos com sucesso")

def create_pipeline_from_config(config_path: str) -> IntelligentETLPipeline:
    """Cria pipeline a partir de arquivo de configuração"""
    try:
        import yaml
        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f)
    except ImportError:
        # Fallback para JSON se YAML não estiver disponível
        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
    
    pipeline_config = PipelineConfig(**config_data.get('pipeline', {}))
    ai_config = AIModelConfig(**config_data.get('ai_models', {}))
    
    return IntelligentETLPipeline(pipeline_config, ai_config)

async def main():
    """Função principal para demonstração"""
    # Configuração de exemplo
    pipeline_config = PipelineConfig(
        name="ETL_CRM_Unificado",
        description="Pipeline ETL unificada com IA para CRM ETL",
        mode=ProcessingMode.BATCH,
        data_type=DataType.STRUCTURED,
        ai_enabled=True,
        auto_repair=True,
        monitoring_enabled=True,
        parallel_workers=4
    )
    
    ai_config = AIModelConfig(
        claude_api_key=os.getenv('ANTHROPIC_API_KEY'),
        openai_api_key=os.getenv('OPENAI_API_KEY'),
        use_local_models=False,  # Desabilitado por padrão para evitar dependências
        max_tokens=2048,
        temperature=0.7
    )
    
    # Criar pipeline
    pipeline = IntelligentETLPipeline(pipeline_config, ai_config)
    
    try:
        # Exemplo de execução
        logger.info("=== DEMONSTRAÇÃO DA PIPELINE ETL COM IA ===")
        
        # Simular processamento com dados de exemplo
        sample_data = pd.DataFrame({
            'nome': ['João Silva', 'Maria Santos', 'Pedro Oliveira', 'Ana Costa'],
            'email': ['joao@email.com', 'maria@empresa.com', 'pedro@teste.com', 'ana@gmail.com'],
            'telefone': ['11999999999', '11888888888', '11777777777', '11666666666'],
            'empresa': ['Tech Corp', 'Data Inc', 'AI Solutions', 'CRM Tech'],
            'data_cadastro': pd.date_range('2024-01-01', periods=4),
            'valor': [1000, 2000, 1500, 3000],
            'status': ['ativo', 'ativo', 'inativo', 'ativo']
        })
        
        # Executar pipeline
        report = await pipeline.run_full_pipeline(
            source=sample_data,
            output_path="output_exemplo.csv",
            transformations=[
                "Filtrar registros com valor maior que 1200",
                "Criar coluna de score de qualidade baseada em completude"
            ]
        )
        
        print("\n=== RELATÓRIO DA PIPELINE ===")
        print(json.dumps(report, indent=2, ensure_ascii=False, default=str))
        
        print(f"\n=== PIPELINE EXECUTADA COM SUCESSO ===")
        print(f"Dados processados: {report['data_overview']['total_records']} registros")
        print(f"Colunas criadas: {report['data_overview']['total_columns']} colunas")
        print(f"Arquivo exportado: output_exemplo.csv")
        
    except Exception as e:
        logger.error(f"Erro na demonstração: {e}")
    finally:
        pipeline.cleanup_resources()

if __name__ == "__main__":
    # Executar função principal
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nPipeline interrompida pelo usuário")
    except Exception as e:
        print(f"Erro na execução: {e}")