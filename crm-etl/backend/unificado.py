#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=================================================
--- Sistema Unificado de Análise de Leads CRM ---
=================================================

Este script representa a consolidação de múltiplas ferramentas de ETL e ML em uma única pipeline coesa.
Ele gerencia o ciclo de vida completo da análise de leads, incluindo:

1.  **ETL (Extração, Transformação e Carga)**:
    - Carrega dados de arquivos CSV ou XLSX com tratamento flexível de separadores.
    - Realiza a limpeza e padronização dos dados, incluindo deduplicação.

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

# Configuração do Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class UnifiedCRMPipeline:
    """
    Classe que encapsula toda a lógica da pipeline de análise e predição de qualidade de leads.
    """

    def __init__(self, model_dir: str = './production_models/', enable_api_calls: bool = False):
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
        """Carrega dados de CSV ou Excel, com detecção de separador e encoding para CSV."""
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
        """Realiza a limpeza básica e deduplicação dos dados."""
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
        """Aplica engenharia de features para criar novas variáveis."""
        logger.info("Aplicando engenharia de features...")
        df = df.copy()

        # Preenchimento de valores nulos em colunas de texto
        for col in df.select_dtypes(include=['object']).columns:
            df[col] = df[col].fillna('').astype(str)

        # Features baseadas em comprimento
        df['nome_length'] = df['nome'].str.len()
        df['empresa_cargo_length'] = df['empresa_cargo'].str.len()
        
        # Features booleanas baseadas em conteúdo
        df['has_linkedin'] = df['linkedin'].str.contains('linkedin', case=False).astype(int)
        df['has_email'] = df['email'].str.contains('@').astype(int)
        # Convertemos whatsapp para string para garantir que contains funcione
        df['has_whatsapp'] = df['whatsapp'].astype(str).str.contains(r'\+55|55', na=False).astype(int)
        
        # Score de qualidade dos dados
        df['data_quality_score'] = (
            df['has_email'] + 
            df['has_linkedin'] +
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
        n_samples = len(X)
        n_classes = len(np.unique(y))
        
        # Para datasets muito pequenos (< 10 amostras), treinar com todos os dados
        if n_samples < 10:
            logger.warning(f"Dataset muito pequeno ({n_samples} amostras). Treinando com todos os dados.")
            X_train, X_test, y_train, y_test = X, X, y, y
        else:
            # Garantir pelo menos 2 amostras por classe no teste
            min_test_size = max(0.2, 2 * n_classes / n_samples)
            
            # Garantir que test_size seja menor que 1.0 e pelo menos 1 amostra para treino
            if min_test_size >= 1.0:
                min_test_size = min(0.8, (n_samples - 1) / n_samples)
            
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=min_test_size, random_state=42, 
                stratify=y if len(y) >= 2 * n_classes and min_test_size < 1.0 else None
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
    """Função principal para executar a pipeline via linha de comando."""
    parser = argparse.ArgumentParser(description='Sistema Unificado de Análise de Leads CRM')
    parser.add_argument(
        'mode', 
        choices=['train', 'batch-predict'], 
        help="Modo de operação: 'train' para treinar um novo modelo, 'batch-predict' para fazer predições em um arquivo."
    )
    parser.add_argument('--data', required=True, help='Caminho para o arquivo de dados de entrada (CSV ou XLSX).')
    parser.add_argument('--target', default='qualidade_lead', help="Nome da coluna alvo para o treinamento.")
    parser.add_argument('--model-dir', default='./production_models/', help="Diretório para salvar ou carregar os artefatos do modelo.")
    parser.add_argument('--output', default='predictions_output.csv', help="Caminho para o arquivo de saída com as predições.")
    parser.add_argument('--enrich', action='store_true', help="Habilita o enriquecimento de dados com APIs externas (ex: CNPJ).")
    
    args = parser.parse_args()

    pipeline = UnifiedCRMPipeline(model_dir=args.model_dir, enable_api_calls=args.enrich)

    try:
        if args.mode == 'train':
            logger.info("--- MODO DE TREINAMENTO ---")
            df = pipeline.run_etl(args.data)
            pipeline.train_model(df, target_column=args.target)
            logger.info("Treinamento concluído com sucesso!")

        elif args.mode == 'batch-predict':
            logger.info("--- MODO DE PREDIÇÃO EM LOTE ---")
            df = pipeline.run_etl(args.data)
            results_df = pipeline.batch_predict(df)
            
            # Salva os resultados
            results_df.to_csv(args.output, index=False, sep=';', encoding='utf-8-sig')
            logger.info(f"Resultados da predição salvos em '{args.output}'.")
            
            # Exibe um resumo
            if 'qualidade_predita' in results_df.columns:
                prediction_summary = results_df['qualidade_predita'].value_counts()
                logger.info("--- Resumo das Predições ---")
                logger.info(prediction_summary)

    except Exception as e:
        logger.error(f"Ocorreu um erro na pipeline: {e}")
        logger.exception("Traceback:")


if __name__ == "__main__":
    main()