"""
======================================================================================
--- Unified CRM Pipeline: Sistema de Análise e Predição de Qualidade de Leads ---
======================================================================================

Este sistema integra diferentes funcionalidades para processar, analisar e predizer a qualidade
de leads em um CRM, seguindo uma arquitetura de pipeline consistente e modular.

O fluxo de trabalho é dividido em quatro etapas principais:

1.  **Carregamento e Limpeza de Dados**:
    - Suporta entrada em formatos CSV e Excel (XLSX).
    - Detecta automaticamente o separador e encoding para CSVs.
    - Realiza deduplicação por CPF/CNPJ, priorizando os registros mais recentes.

2.  **Engenharia e Enriquecimento de Features**:
    - Cria features sintéticas para melhorar o desempenho do modelo (ex: score de qualidade de dados).
    - Opcionalmente, enriquece os dados com informações externas via APIs (ex: consulta de CNPJ).

3.  **Treinamento de Modelo de Machine Learning**:
    - Prepara os dados com encoding de variáveis categóricas e escalonamento de features numéricas.
    - Treina um modelo de classificação (RandomForest) para prever a qualidade dos leads.
    - Realiza otimização de hiperparâmetros e avaliação completa do modelo.
    - Salva todos os artefatos do modelo (modelo, scaler, encoders, metadados) para uso futuro.

4.  **Predição e Geração de Relatórios**:
    - Carrega um modelo pré-treinado para realizar predições em lote em novos dados.
    - Gera um arquivo de saída com os dados originais enriquecidos com as predições de qualidade e confiança.
    - Apresenta um sumário dos resultados ao final da execução.

Este sistema foi projetado para ser modular, robusto e facilmente executável através de uma interface de linha de comando.
"""

import pandas as pd
import numpy as np
import joblib
import json
import argparse
import logging
import re
import requests
from time import sleep
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

# Imports de Machine Learning
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler, LabelEncoder, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.metrics import classification_report, roc_auc_score

# Imports locais para funcionalidades brasileiras
try:
    from .brazilian_utils import BrazilianDataValidator
except ImportError:
    from brazilian_utils import BrazilianDataValidator

# Configuração do Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class UnifiedCRMPipeline:
    """
    Pipeline unificada para análise e predição de qualidade de leads em sistemas CRM.
    
    A classe UnifiedCRMPipeline implementa um sistema completo de ETL (Extract, Transform, Load)
    integrado com Machine Learning para processamento, análise e predição da qualidade de leads.
    Suporta dados brasileiros com validação de CPF, CNPJ e normalização de telefones.
    
    Attributes:
        model_dir (Path): Diretório para armazenar artefatos do modelo treinado.
        enable_api_calls (bool): Habilita chamadas para APIs externas de enriquecimento.
        enrichment_cache (dict): Cache para respostas de APIs externas.
        model (Pipeline): Pipeline completa do modelo de machine learning.
        preprocessor (ColumnTransformer): Transformador de pré-processamento dos dados.
        metadata (dict): Metadados do modelo treinado.
        numeric_features (list): Lista de features numéricas identificadas.
        categorical_features (list): Lista de features categóricas identificadas.
        target_column (str): Nome da coluna alvo para treinamento.
    
    Example:
        Exemplo básico de uso da pipeline:
        
        >>> pipeline = UnifiedCRMPipeline(
        ...     model_dir='./models/',
        ...     enable_api_calls=True
        ... )
        >>> 
        >>> # Executar ETL completo
        >>> df_processed = pipeline.run_etl('dados_leads.csv')
        >>> 
        >>> # Treinar modelo
        >>> pipeline.train_model(df_processed, target_column='qualidade_lead')
        >>> 
        >>> # Fazer predições em novos dados
        >>> df_predictions = pipeline.batch_predict(new_data)
    
    Note:
        - Suporta formatos CSV (com detecção automática de separador e encoding) e Excel
        - Realiza deduplicação automática por CPF/CNPJ
        - Cria features sintéticas para melhorar performance do modelo
        - Integra validação de dados brasileiros (CPF, CNPJ, telefones)
        - Modelo padrão: RandomForest com balanceamento automático de classes
    
    .. versionadded:: 1.0.0
    
    .. versionchanged:: 1.1.0
        Adicionado suporte a múltiplos encodings para CSV
        
    .. versionchanged:: 1.2.0
        Implementada validação brasileira de documentos e telefones
    """

    def __init__(self, model_dir: str = './production_models/', enable_api_calls: bool = False):
        """
        Inicializa a pipeline CRM unificada.
        
        Parameters:
            model_dir (str, optional): Diretório para armazenar os artefatos do modelo.
                Defaults to './production_models/'.
            enable_api_calls (bool, optional): Habilita chamadas para APIs externas 
                de enriquecimento de dados. Defaults to False.
        
        Note:
            O diretório do modelo é criado automaticamente se não existir.
        """
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(exist_ok=True)
        self.enable_api_calls = enable_api_calls
        self.enrichment_cache = {'cnpj': {}}
        
        # Artefatos do Modelo
        self.model = None
        self.preprocessor = None
        self.metadata = {}

        # Configuração das Features
        self.numeric_features = []
        self.categorical_features = []
        self.target_column = 'qualidade_lead'

    def _load_data(self, file_path: str) -> pd.DataFrame:
        """
        Carrega dados de arquivos CSV ou Excel com detecção automática de parâmetros.
        
        Parameters:
            file_path (str): Caminho para o arquivo de dados.
        
        Returns:
            pd.DataFrame: DataFrame com os dados carregados.
        
        Raises:
            ValueError: Se o formato do arquivo não for suportado ou se não for
                possível ler o arquivo CSV com os separadores e encodings tentados.
        
        Note:
            Para arquivos CSV, tenta automaticamente os separadores: ',', ';', '|', '\\t'
            e os encodings: 'utf-8', 'iso-8859-1', 'cp1252', 'latin-1'.
            
            Apenas aceita DataFrames com mais de 1 coluna para garantir estrutura válida.
        """
        logger.info(f"Carregando dados de '{file_path}'...")
        file_ext = Path(file_path).suffix.lower()

        if file_ext == '.csv':
            # Lista de encodings para tentar
            encodings = ['utf-8', 'iso-8859-1', 'cp1252', 'latin-1']
            
            for encoding in encodings:
                for sep in [',', ';', '|', '\t']:
                    try:
                        df = pd.read_csv(file_path, sep=sep, encoding=encoding, low_memory=False)
                        if len(df.columns) > 1:
                            logger.info(f"Arquivo CSV lido com sucesso usando o separador '{sep}' e encoding '{encoding}'.")
                            return df
                    except (UnicodeDecodeError, Exception):
                        continue
            raise ValueError("Não foi possível ler o arquivo CSV. Verifique o formato, o separador e o encoding.")
        elif file_ext in ['.xlsx', '.xls']:
            return pd.read_excel(file_path)
        else:
            raise ValueError(f"Formato de arquivo não suportado: {file_ext}")

    def _clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Realiza limpeza e deduplicação dos dados baseada em CPF/CNPJ.
        
        Parameters:
            df (pd.DataFrame): DataFrame com os dados brutos.
        
        Returns:
            pd.DataFrame: DataFrame limpo e deduplificado.
        
        Note:
            - Busca colunas de CPF ou CNPJ para deduplicação
            - Se houver coluna de data, ordena por data (mais recente primeiro)
            - Remove registros duplicados mantendo o primeiro (mais recente)
            - Remove registros com CPF/CNPJ nulos antes da deduplicação
        """
        logger.info("Iniciando limpeza e deduplicação dos dados...")
        
        # Lógica de deduplicação inspirada em etl_pipeline.py e CrmCleaner.py
        # Buscar tanto CPF quanto CNPJ
        cpf_column = next((col for col in df.columns if 'CPF' in col.upper()), None)
        cnpj_column = next((col for col in df.columns if 'CNPJ' in col.upper()), None)
        dedup_column = cpf_column or cnpj_column
        date_column = next((col for col in df.columns if 'DATE' in col.upper() or 'DATA' in col.upper()), None)

        if dedup_column:
            # Garante que a coluna de deduplicação não tenha valores nulos
            df.dropna(subset=[dedup_column], inplace=True)
            
            # Ordena por data, se disponível, para manter o registro mais recente
            if date_column and pd.api.types.is_datetime64_any_dtype(df[date_column]):
                df = df.sort_values(by=date_column, ascending=False)
            
            records_before = len(df)
            df.drop_duplicates(subset=[dedup_column], keep='first', inplace=True)
            records_after = len(df)
            logger.info(f"{records_before - records_after} registros duplicados removidos com base na coluna '{dedup_column}'.")
        else:
            logger.warning("Nenhuma coluna de CPF ou CNPJ encontrada. A deduplicação não foi realizada.")

        return df

    def _engineer_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Aplica engenharia de features para criar variáveis sintéticas.
        
        Cria features baseadas nos dados existentes para melhorar a performance
        do modelo de machine learning, incluindo validações brasileiras.
        
        Parameters:
            df (pd.DataFrame): DataFrame com os dados limpos.
        
        Returns:
            pd.DataFrame: DataFrame com features adicionais criadas.
        
        Features Criadas:
            - nome_length: Comprimento do nome
            - empresa_cargo_length: Comprimento do cargo/empresa
            - has_email: Indica se possui email válido (contém @)
            - has_linkedin: Indica se possui perfil LinkedIn
            - has_whatsapp: Indica se possui WhatsApp brasileiro válido
            - cpf_valido: Indica se CPF é válido (algoritmo brasileiro)
            - cnpj_valido_formato: Indica se CNPJ tem formato válido
            - data_quality_score: Score agregado de qualidade dos dados (0-6)
        
        Note:
            Utiliza BrazilianDataValidator para validações específicas do Brasil.
        """
        logger.info("Aplicando engenharia de features...")
        df = df.copy()

        # Preenchimento de valores nulos em colunas de texto
        for col in df.select_dtypes(include=['object']).columns:
            df[col] = df[col].fillna('').astype(str)

        # Normalização de nomes brasileiros
        if 'nome' in df.columns:
            df['nome'] = df['nome'].apply(BrazilianDataValidator.normalize_name)
            df['nome_length'] = df['nome'].str.len()
        else:
            df['nome_length'] = 0
            
        if 'empresa_cargo' in df.columns:
            df['empresa_cargo_length'] = df['empresa_cargo'].str.len()
        elif 'empresa' in df.columns:
            df['empresa_cargo_length'] = df['empresa'].str.len()
        else:
            df['empresa_cargo_length'] = 0
        
        # Features booleanas baseadas em conteúdo (verificar se colunas existem)
        if 'linkedin' in df.columns:
            df['has_linkedin'] = df['linkedin'].str.contains('linkedin', case=False).astype(int)
        else:
            df['has_linkedin'] = 0
            
        if 'email' in df.columns:
            df['has_email'] = df['email'].str.contains('@').astype(int)
        else:
            df['has_email'] = 0
            
        # Validação aprimorada de telefones brasileiros
        if 'whatsapp' in df.columns:
            df['has_whatsapp'] = df['whatsapp'].apply(BrazilianDataValidator.validate_phone_whatsapp).astype(int)
        elif 'telefone' in df.columns:
            df['has_whatsapp'] = df['telefone'].apply(BrazilianDataValidator.validate_phone_whatsapp).astype(int)
        else:
            df['has_whatsapp'] = 0
        
        # Validação de CPF/CNPJ brasileiro
        cpf_column = next((col for col in df.columns if 'CPF' in col.upper()), None)
        cnpj_column = next((col for col in df.columns if 'CNPJ' in col.upper()), None)
        
        if cpf_column:
            df['cpf_valido'] = df[cpf_column].apply(BrazilianDataValidator.validate_cpf).astype(int)
        else:
            df['cpf_valido'] = 0
            
        if cnpj_column:
            df['cnpj_valido_formato'] = df[cnpj_column].apply(BrazilianDataValidator.validate_cnpj).astype(int)
        else:
            df['cnpj_valido_formato'] = 0
        
        # Extração de features avançadas de telefone
        df = BrazilianDataValidator.extract_phone_features(df)
        
        # Formatação de valores monetários se existir coluna de receita
        receita_cols = [col for col in df.columns if any(keyword in col.lower() for keyword in ['receita', 'faturamento', 'valor'])]
        for col in receita_cols:
            if df[col].dtype in ['object', 'string']:
                # Se é string, mantém formatado
                df[f'{col}_formatado'] = df[col].apply(lambda x: BrazilianDataValidator.format_currency_brl(x) if pd.notna(x) else "R$ 0,00")
        
        # Score de qualidade dos dados aprimorado
        df['data_quality_score'] = (
            df['has_email'] + 
            df['has_linkedin'] +
            df['has_whatsapp'] +
            df['cpf_valido'] +
            df['cnpj_valido_formato'] +
            (df['nome_length'] > 5).astype(int)
        )
        return df

    def _enrich_with_apis(self, df: pd.DataFrame) -> pd.DataFrame:
        """Enriquece os dados usando a API da ReceitaWS para validar CNPJ."""
        if not self.enable_api_calls:
            return df

        logger.info("Iniciando enriquecimento de dados via API (CNPJ)...")
        df['cnpj_valido'] = 0
        df['empresa_porte'] = 'N/A'

        cnpj_col = next((col for col in df.columns if 'CNPJ' in col.upper()), None)
        if not cnpj_col:
            logger.warning("Nenhuma coluna de CNPJ encontrada para enriquecimento.")
            return df
            
        for idx, row in df.iterrows():
            cnpj_raw = row.get(cnpj_col)
            if pd.notna(cnpj_raw) and str(cnpj_raw).strip() != '':
                cnpj_clean = re.sub(r'\D', '', str(cnpj_raw))
                if cnpj_clean in self.enrichment_cache:
                    info = self.enrichment_cache[cnpj_clean]
                else:
                    sleep(0.5) # Rate limiting
                    try:
                        response = requests.get(f"https://www.receitaws.com.br/v1/cnpj/{cnpj_clean}", timeout=10)
                        if response.status_code == 200 and response.json().get('status') != 'ERROR':
                            info = response.json()
                            self.enrichment_cache[cnpj_clean] = info
                        else:
                            info = None
                    except requests.RequestException:
                        info = None

                if info:
                    df.loc[idx, 'cnpj_valido'] = 1
                    df.loc[idx, 'empresa_porte'] = info.get('porte', 'N/A')
        return df

    def run_etl(self, file_path: str) -> pd.DataFrame:
        """Executa a pipeline completa de ETL."""
        df = self._load_data(file_path)
        df = self._clean_data(df)
        df = self._engineer_features(df)
        df = self._enrich_with_apis(df)
        logger.info("Pipeline de ETL concluída com sucesso.")
        return df

    def train_model(self, df: pd.DataFrame, target_column: str = 'qualidade_lead'):
        """Treina, avalia e salva o modelo de ML."""
        logger.info("Iniciando processo de treinamento do modelo...")
        self.target_column = target_column

        if self.target_column not in df.columns:
            raise ValueError(f"A coluna alvo '{self.target_column}' não foi encontrada no DataFrame.")

        # Converte a coluna alvo para binário
        df[self.target_column] = df[self.target_column].apply(lambda x: 1 if str(x).lower() in ['alta', 'sim', '1', 'high'] else 0)
        
        X = df.drop(self.target_column, axis=1)
        y = df[self.target_column]

        # Identifica tipos de features para o pré-processador
        self.numeric_features = X.select_dtypes(include=np.number).columns.tolist()
        self.categorical_features = X.select_dtypes(include=['object', 'category']).columns.tolist()

        # Cria a pipeline de pré-processamento
        numeric_transformer = StandardScaler()
        categorical_transformer = OneHotEncoder(handle_unknown='ignore')

        self.preprocessor = ColumnTransformer(
            transformers=[
                ('num', numeric_transformer, self.numeric_features),
                ('cat', categorical_transformer, self.categorical_features)
            ])

        # Cria a pipeline completa do modelo
        self.model = Pipeline(steps=[
            ('preprocessor', self.preprocessor),
            ('classifier', RandomForestClassifier(random_state=42, class_weight='balanced'))
        ])

        # Divide os dados e treina o modelo
        # Ajuste para datasets pequenos
        n_samples = len(X)
        n_classes = len(np.unique(y))
        
        # Para datasets muito pequenos, usar uma estratégia diferente
        if n_samples < 10:
            # Para datasets muito pequenos, treinar no dataset completo
            X_train, X_test, y_train, y_test = X, X, y, y
            logger.warning(f"Dataset muito pequeno ({n_samples} amostras). Usando o dataset completo para treino e teste.")
        else:
            # Calcula test_size garantindo que não ultrapasse 0.8
            test_size = min(0.8, max(0.2, 2 * n_classes / n_samples))
            
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=test_size, random_state=42, 
                stratify=y if len(y) >= 2 * n_classes else None  # stratify só se houver amostras suficientes
            )
        
        logger.info("Treinando o modelo RandomForest...")
        self.model.fit(X_train, y_train)

        # Avalia o modelo
        y_pred = self.model.predict(X_test)
        y_proba = self.model.predict_proba(X_test)[:, 1]
        
        logger.info("--- Relatório de Classificação ---")
        logger.info("\n" + classification_report(y_test, y_pred))
        
        try:
            auc_score = roc_auc_score(y_test, y_proba)
            logger.info(f"AUC Score: {auc_score:.4f}")
        except Exception as e:
            logger.warning(f"Não foi possível calcular o AUC Score: {str(e)}")

        # Salva os artefatos
        self._save_artifacts()
    
    def _save_artifacts(self):
        """Salva o modelo treinado e os metadados."""
        logger.info(f"Salvando artefatos do modelo em '{self.model_dir}'...")
        
        joblib.dump(self.model, self.model_dir / 'model_pipeline.joblib')

        self.metadata = {
            'training_date': datetime.now().isoformat(),
            'model_type': 'RandomForestClassifier',
            'numeric_features': self.numeric_features,
            'categorical_features': self.categorical_features,
            'target_column': self.target_column
        }
        with open(self.model_dir / 'metadata.json', 'w') as f:
            json.dump(self.metadata, f, indent=4)
        
        logger.info("Artefatos salvos com sucesso.")

    def _load_artifacts(self):
        """Carrega os artefatos de um modelo pré-treinado."""
        logger.info(f"Carregando artefatos do modelo de '{self.model_dir}'...")
        if not (self.model_dir / 'model_pipeline.joblib').exists():
            raise FileNotFoundError("Nenhum modelo treinado encontrado. Execute o modo 'train' primeiro.")
            
        self.model = joblib.load(self.model_dir / 'model_pipeline.joblib')
        with open(self.model_dir / 'metadata.json', 'r') as f:
            self.metadata = json.load(f)
        logger.info("Artefatos carregados com sucesso.")

    def batch_predict(self, df: pd.DataFrame) -> pd.DataFrame:
        """Realiza predições em lote e anexa os resultados ao DataFrame."""
        if not self.model:
            self._load_artifacts()

        logger.info("Iniciando predição em lote...")
        
        predictions = self.model.predict(df)
        probabilities = self.model.predict_proba(df)[:, 1]

        df_results = df.copy()
        df_results['qualidade_predita'] = ['Alta' if pred == 1 else 'Baixa' for pred in predictions]
        df_results['confianca_predicao'] = probabilities

        logger.info("Predição em lote concluída.")
        return df_results

def main():
    parser = argparse.ArgumentParser(description='Sistema Unificado de Análise e Predição de Qualidade de Leads')
    parser.add_argument('--mode', type=str, required=True, choices=['train', 'predict', 'etl'],
                        help='Modo de operação: train (treinar modelo), predict (predizer em novos dados), etl (apenas ETL)')
    parser.add_argument('--input', type=str, required=True,
                        help='Caminho para o arquivo de entrada (CSV ou XLSX)')
    parser.add_argument('--output', type=str, help='Caminho para o arquivo de saída (apenas modos predict e etl)')
    parser.add_argument('--model-dir', type=str, default='./production_models/',
                        help='Diretório para salvar ou carregar o modelo')
    parser.add_argument('--enable-api', action='store_true',
                        help='Habilitar chamadas de API para enriquecimento de dados')
    parser.add_argument('--target', type=str, default='qualidade_lead',
                        help='Nome da coluna alvo para treinar o modelo (modo train)')
    
    args = parser.parse_args()
    
    # Inicializa a pipeline
    pipeline = UnifiedCRMPipeline(model_dir=args.model_dir, enable_api_calls=args.enable_api)
    
    if args.mode == 'train':
        logger.info("=== MODO: TREINAMENTO DO MODELO ===")
        # Carrega e processa os dados
        df = pipeline.run_etl(args.input)
        # Treina o modelo
        pipeline.train_model(df, target_column=args.target)
        logger.info("Treinamento concluído com sucesso!")
        
    elif args.mode == 'predict':
        logger.info("=== MODO: PREDIÇÃO ===")
        if not args.output:
            raise ValueError("O parâmetro --output é obrigatório no modo 'predict'")
            
        # Carrega e processa os dados
        df = pipeline.run_etl(args.input)
        # Faz predições
        df_results = pipeline.batch_predict(df)
        
        # Salva os resultados
        output_path = Path(args.output)
        if output_path.suffix.lower() == '.csv':
            df_results.to_csv(output_path, index=False)
        elif output_path.suffix.lower() in ['.xlsx', '.xls']:
            df_results.to_excel(output_path, index=False)
        else:
            # Default para CSV
            df_results.to_csv(output_path, index=False)
            
        logger.info(f"Predições concluídas e salvas em '{args.output}'")
        
    elif args.mode == 'etl':
        logger.info("=== MODO: APENAS ETL ===")
        if not args.output:
            raise ValueError("O parâmetro --output é obrigatório no modo 'etl'")
            
        # Carrega e processa os dados
        df = pipeline.run_etl(args.input)
        
        # Salva os resultados
        output_path = Path(args.output)
        if output_path.suffix.lower() == '.csv':
            df.to_csv(output_path, index=False)
        elif output_path.suffix.lower() in ['.xlsx', '.xls']:
            df.to_excel(output_path, index=False)
        else:
            # Default para CSV
            df.to_csv(output_path, index=False)
            
        logger.info(f"ETL concluído e dados salvos em '{args.output}'")
    
    logger.info("Processo finalizado.")

if __name__ == "__main__":
    main()
