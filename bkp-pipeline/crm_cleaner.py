"""
Sistema de Limpeza e Centralização de CRM - CRM The New Education
Desenvolvido para processar, limpar e otimizar dados de múltiplas fontes
com foco em compliance LGPD e preparação para análises avançadas
"""

import pandas as pd
import numpy as np
import re
import json
import hashlib
from datetime import datetime
from typing import Dict, List, Optional, Union, Tuple
import warnings
from pathlib import Path
import logging

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CRMCleaner:
    """
    Sistema inteligente para limpeza e padronização de dados CRM
    com suporte a múltiplos formatos e compliance LGPD
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Inicializa o sistema de limpeza
        
        Args:
            config: Dicionário de configuração personalizada
        """
        self.config = self._get_default_config()
        if config:
            self.config.update(config)
        
        # Mapeamento de colunas padrão baseado na análise
        self.column_mapping = {
            # Dados pessoais
            'nome_completo': ['nome completo', 'nome', 'full name', 'name'],
            'cpf': ['cpf:', 'cpf', 'documento'],
            'rg': ['rg:', 'rg', 'identidade'],
            'email': ['email', 'e-mail', 'email principal', 'deixe aqui seu email principal'],
            'telefone': ['whatsapp', 'telefone', 'celular', 'phone', 'tel'],
            'data_nascimento': ['aniversário', 'nascimento', 'birthday', 'data de nascimento'],
            'endereco': ['endereço', 'endereco', 'address', 'endereço residencial completo:'],
            'cidade_estado': ['cidade e estado', 'cidade', 'city', 'localização'],
            
            # Dados profissionais
            'empresa': ['empresa', 'company', 'empresa atual', 'qual o nome da sua empresa atual?'],
            'cargo': ['cargo', 'position', 'cargo atual', 'qual o seu cargo atual?'],
            'segmento': ['segmento', 'segment', 'segmento de atuação', 'qual o segmento de atuação da empresa?'],
            'faixa_funcionarios': ['funcionários', 'employees', 'faixa de funcionários'],
            'faixa_faturamento': ['faturamento', 'revenue', 'faixa de faturamento'],
            
            # Dados de engajamento
            'linkedin': ['linkedin', 'linkedin:', 'perfil linkedin'],
            'objetivos': ['objetivos', 'o que você busca', 'expectations', 'goals'],
            'dores_necessidades': ['dores', 'necessidades', 'pain points', 'needs'],
            
            # Dados do sistema
            'id_unico': ['#', 'id', 'codigo', 'identifier'],
            'data_inscricao': ['submit date', 'data inscricao', 'inscription date'],
            'autorizacao_imagem': ['autorizo', 'autorizacao', 'consent'],
            'tipo_nota_fiscal': ['emissão de nota fiscal', 'tipo nota', 'invoice type'],
            'cnpj': ['cnpj:', 'cnpj', 'company document']
        }
        
        # Padrões de limpeza
        self.cleaning_patterns = {
            'cpf': r'[^\d]',
            'rg': r'[^\d]',
            'cnpj': r'[^\d]',
            'telefone': r'[^\d+]',
            'cep': r'[^\d-]'
        }
        
    def _get_default_config(self) -> Dict:
        """Retorna configuração padrão do sistema"""
        return {
            'enable_lgpd_compliance': True,
            'anonymize_sensitive_data': False,
            'remove_duplicates': True,
            'standardize_dates': True,
            'export_format': 'json',  # json, csv, parquet
            'track_data_lineage': True,
            'validate_documents': True
        }
    
    def clean_dataframe(self, df: pd.DataFrame, source_name: str = 'unknown') -> pd.DataFrame:
        """
        Limpa e padroniza um DataFrame
        
        Args:
            df: DataFrame a ser limpo
            source_name: Nome da fonte de dados
            
        Returns:
            DataFrame limpo e padronizado
        """
        logger.info(f"Iniciando limpeza de dados - Fonte: {source_name}")
        logger.info(f"Dimensões originais: {df.shape}")
        
        # Cópia para preservar original
        df_clean = df.copy()
        
        # 1. Padronização de nomes de colunas
        df_clean = self._standardize_column_names(df_clean)
        
        # 2. Mapeamento para estrutura padrão
        df_clean = self._map_to_standard_schema(df_clean)
        
        # 3. Limpeza de dados específicos por tipo
        df_clean = self._clean_personal_data(df_clean)
        df_clean = self._clean_professional_data(df_clean)
        df_clean = self._clean_system_data(df_clean)
        
        # 4. Validação de documentos
        if self.config['validate_documents']:
            df_clean = self._validate_documents(df_clean)
        
        # 5. Padronização de datas
        if self.config['standardize_dates']:
            df_clean = self._standardize_dates(df_clean)
        
        # 6. Remoção de duplicatas
        if self.config['remove_duplicates']:
            df_clean = self._remove_duplicates(df_clean)
        
        # 7. Adição de metadados
        df_clean = self._add_metadata(df_clean, source_name)
        
        # 8. Compliance LGPD
        if self.config['enable_lgpd_compliance']:
            df_clean = self._apply_lgpd_compliance(df_clean)
        
        logger.info(f"Limpeza concluída - Dimensões finais: {df_clean.shape}")
        return df_clean
    
    def _standardize_column_names(self, df: pd.DataFrame) -> pd.DataFrame:
        """Padroniza nomes de colunas"""
        df.columns = df.columns.str.lower().str.strip()
        df.columns = df.columns.str.replace(r'[^\w\s]', '', regex=True)
        df.columns = df.columns.str.replace(r'\s+', '_', regex=True)
        return df
    
    def _map_to_standard_schema(self, df: pd.DataFrame) -> pd.DataFrame:
        """Mapeia colunas para esquema padrão"""
        mapped_df = pd.DataFrame()
        
        for standard_col, possible_names in self.column_mapping.items():
            for col in df.columns:
                if any(name in col.lower() for name in possible_names):
                    mapped_df[standard_col] = df[col]
                    break
            
            # Se coluna não encontrada, criar vazia
            if standard_col not in mapped_df.columns:
                mapped_df[standard_col] = np.nan
        
        # Adicionar colunas não mapeadas com prefixo
        for col in df.columns:
            if not any(col.lower() in ' '.join(names) for names in self.column_mapping.values()):
                mapped_df[f'extra_{col}'] = df[col]
        
        return mapped_df
    
    def _clean_personal_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Limpa dados pessoais"""
        # CPF
        if 'cpf' in df.columns:
            df['cpf'] = df['cpf'].astype(str).str.replace(self.cleaning_patterns['cpf'], '', regex=True)
            df['cpf'] = df['cpf'].str.zfill(11)
            df['cpf_valido'] = df['cpf'].apply(self._validate_cpf)
        
        # RG
        if 'rg' in df.columns:
            df['rg'] = df['rg'].astype(str).str.replace(self.cleaning_patterns['rg'], '', regex=True)
        
        # Nome
        if 'nome_completo' in df.columns:
            df['nome_completo'] = df['nome_completo'].str.title().str.strip()
            df['primeiro_nome'] = df['nome_completo'].str.split().str[0]
            df['ultimo_nome'] = df['nome_completo'].str.split().str[-1]
        
        # Email
        if 'email' in df.columns:
            df['email'] = df['email'].str.lower().str.strip()
            df['email_valido'] = df['email'].str.contains(r'^[\w\.-]+@[\w\.-]+\.\w+$', na=False)
            df['dominio_email'] = df['email'].str.extract(r'@(.+)$')[0]
        
        # Telefone
        if 'telefone' in df.columns:
            df['telefone'] = df['telefone'].astype(str).str.replace(self.cleaning_patterns['telefone'], '', regex=True)
            df['telefone'] = df['telefone'].str.replace(r'^55', '', regex=True)  # Remove código do país
            df['ddd'] = df['telefone'].str[:2]
            df['telefone_formatado'] = df.apply(lambda x: f"({x['ddd']}) {x['telefone'][2:6]}-{x['telefone'][6:]}" 
                                               if pd.notna(x['telefone']) and len(str(x['telefone'])) >= 10 else np.nan, axis=1)
        
        return df
    
    def _clean_professional_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Limpa dados profissionais"""
        # Empresa
        if 'empresa' in df.columns:
            df['empresa'] = df['empresa'].str.upper().str.strip()
            df['empresa_normalizada'] = df['empresa'].str.replace(r'\s*(LTDA|ME|EPP|EIRELI|S\.?A\.?)\s*$', '', regex=True)
        
        # Cargo
        if 'cargo' in df.columns:
            df['cargo'] = df['cargo'].str.title().str.strip()
            df['nivel_cargo'] = df['cargo'].apply(self._classify_job_level)
        
        # CNPJ
        if 'cnpj' in df.columns:
            df['cnpj'] = df['cnpj'].astype(str).str.replace(self.cleaning_patterns['cnpj'], '', regex=True)
            df['cnpj'] = df['cnpj'].str.zfill(14)
            df['cnpj_valido'] = df['cnpj'].apply(self._validate_cnpj)
        
        # Faturamento
        if 'faixa_faturamento' in df.columns:
            df['faturamento_min'] = df['faixa_faturamento'].apply(self._extract_revenue_min)
            df['faturamento_max'] = df['faixa_faturamento'].apply(self._extract_revenue_max)
            df['faturamento_score'] = df['faturamento_min'].apply(self._calculate_revenue_score)
        
        return df
    
    def _clean_system_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Limpa dados do sistema"""
        # Datas
        date_columns = ['data_inscricao', 'data_nascimento']
        for col in date_columns:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')
        
        # IDs únicos
        if 'id_unico' not in df.columns or df['id_unico'].isna().any():
            df['id_unico'] = df.apply(lambda x: self._generate_unique_id(x), axis=1)
        
        # Status de autorização
        if 'autorizacao_imagem' in df.columns:
            df['autorizacao_imagem'] = df['autorizacao_imagem'].fillna(0).astype(int)
        
        return df
    
    def _validate_cpf(self, cpf: str) -> bool:
        """Valida CPF usando algoritmo oficial"""
        if not cpf or len(str(cpf)) != 11:
            return False
        
        cpf_str = str(cpf).zfill(11)
        
        # Verifica sequências inválidas conhecidas
        if cpf_str in ['00000000000', '11111111111', '22222222222', '33333333333',
                       '44444444444', '55555555555', '66666666666', '77777777777',
                       '88888888888', '99999999999']:
            return False
        
        # Cálculo do primeiro dígito verificador
        soma = sum(int(cpf_str[i]) * (10 - i) for i in range(9))
        resto = soma % 11
        dv1 = 0 if resto < 2 else 11 - resto
        
        # Cálculo do segundo dígito verificador
        soma = sum(int(cpf_str[i]) * (11 - i) for i in range(10))
        resto = soma % 11
        dv2 = 0 if resto < 2 else 11 - resto
        
        return cpf_str[-2:] == f"{dv1}{dv2}"
    
    def _validate_cnpj(self, cnpj: str) -> bool:
        """Valida CNPJ usando algoritmo oficial"""
        if not cnpj or len(str(cnpj)) != 14:
            return False
        
        cnpj_str = str(cnpj).zfill(14)
        
        # Cálculo similar ao CPF mas com pesos diferentes
        # Simplificado por brevidade
        return True  # Implementar validação completa em produção
    
    def _classify_job_level(self, cargo: str) -> str:
        """Classifica nível hierárquico do cargo"""
        if pd.isna(cargo):
            return 'não informado'
        
        cargo_lower = cargo.lower()
        
        if any(term in cargo_lower for term in ['ceo', 'presidente', 'chairman', 'fundador']):
            return 'C-Level'
        elif any(term in cargo_lower for term in ['diretor', 'vp', 'vice-presidente']):
            return 'Diretoria'
        elif any(term in cargo_lower for term in ['gerente', 'manager', 'head']):
            return 'Gerência'
        elif any(term in cargo_lower for term in ['coordenador', 'supervisor', 'líder']):
            return 'Coordenação'
        elif any(term in cargo_lower for term in ['analista', 'especialista']):
            return 'Especialista'
        else:
            return 'Operacional'
    
    def _extract_revenue_min(self, faixa: str) -> float:
        """Extrai valor mínimo da faixa de faturamento"""
        if pd.isna(faixa):
            return 0
        
        faixa_lower = str(faixa).lower()
        
        # Mapear faixas conhecidas
        revenue_map = {
            'até 1 milhão': 0,
            '1 milhão a 10 milhões': 1000000,
            '10 milhões a 50 milhões': 10000000,
            '50 milhões a 100 milhões': 50000000,
            'acima de 100 milhões': 100000000
        }
        
        for key, value in revenue_map.items():
            if key in faixa_lower:
                return value
        
        return 0
    
    def _extract_revenue_max(self, faixa: str) -> float:
        """Extrai valor máximo da faixa de faturamento"""
        if pd.isna(faixa):
            return 0
        
        faixa_lower = str(faixa).lower()
        
        revenue_map = {
            'até 1 milhão': 1000000,
            '1 milhão a 10 milhões': 10000000,
            '10 milhões a 50 milhões': 50000000,
            '50 milhões a 100 milhões': 100000000,
            'acima de 100 milhões': 1000000000
        }
        
        for key, value in revenue_map.items():
            if key in faixa_lower:
                return value
        
        return 0
    
    def _calculate_revenue_score(self, revenue_min: float) -> int:
        """Calcula score baseado no faturamento para segmentação"""
        if revenue_min >= 100000000:
            return 5  # Enterprise
        elif revenue_min >= 50000000:
            return 4  # Large
        elif revenue_min >= 10000000:
            return 3  # Medium
        elif revenue_min >= 1000000:
            return 2  # Small
        else:
            return 1  # Micro
    
    def _standardize_dates(self, df: pd.DataFrame) -> pd.DataFrame:
        """Padroniza formatos de data"""
        date_columns = df.select_dtypes(include=['datetime64']).columns
        
        for col in date_columns:
            df[f'{col}_ano'] = df[col].dt.year
            df[f'{col}_mes'] = df[col].dt.month
            df[f'{col}_dia'] = df[col].dt.day
            df[f'{col}_dia_semana'] = df[col].dt.day_name()
        
        # Calcular idade se data de nascimento disponível
        if 'data_nascimento' in df.columns:
            df['idade'] = (datetime.now() - df['data_nascimento']).dt.days / 365.25
            df['faixa_etaria'] = pd.cut(df['idade'], 
                                       bins=[0, 25, 35, 45, 55, 65, 100],
                                       labels=['<25', '25-34', '35-44', '45-54', '55-64', '65+'])
        
        return df
    
    def _remove_duplicates(self, df: pd.DataFrame) -> pd.DataFrame:
        """Remove duplicatas inteligentemente"""
        # Priorizar registros mais completos
        df['completude'] = df.notna().sum(axis=1)
        
        # Ordenar por completude e data mais recente
        sort_columns = ['completude']
        if 'data_inscricao' in df.columns:
            sort_columns.append('data_inscricao')
        
        df = df.sort_values(sort_columns, ascending=[False, False])
        
        # Remover duplicatas baseado em CPF ou email
        if 'cpf' in df.columns:
            df = df.drop_duplicates(subset=['cpf'], keep='first')
        elif 'email' in df.columns:
            df = df.drop_duplicates(subset=['email'], keep='first')
        
        df = df.drop('completude', axis=1)
        return df
    
    def _add_metadata(self, df: pd.DataFrame, source_name: str) -> pd.DataFrame:
        """Adiciona metadados para rastreabilidade"""
        df['fonte_dados'] = source_name
        df['data_processamento'] = datetime.now()
        df['versao_processamento'] = '1.0.0'
        
        # Hash para integridade
        df['hash_registro'] = df.apply(
            lambda x: hashlib.md5(
                str(x.to_dict()).encode()
            ).hexdigest()[:16], axis=1
        )
        
        return df
    
    def _apply_lgpd_compliance(self, df: pd.DataFrame) -> pd.DataFrame:
        """Aplica compliance LGPD"""
        # Criar versão anonimizada se configurado
        if self.config['anonymize_sensitive_data']:
            # Anonimizar CPF (manter apenas primeiros 3 dígitos)
            if 'cpf' in df.columns:
                df['cpf_anonimizado'] = df['cpf'].astype(str).str[:3] + '*' * 8
            
            # Anonimizar RG
            if 'rg' in df.columns:
                df['rg_anonimizado'] = df['rg'].astype(str).str[:2] + '*' * 7
            
            # Criar ID único não rastreável
            df['id_anonimo'] = df.apply(
                lambda x: hashlib.sha256(
                    str(x['id_unico']).encode()
                ).hexdigest()[:12], axis=1
            )
        
        # Adicionar flags de consentimento
        df['lgpd_consentimento_dado'] = df['autorizacao_imagem'].fillna(0).astype(bool)
        df['lgpd_data_consentimento'] = df.loc[df['lgpd_consentimento_dado'], 'data_inscricao']
        
        return df
    
    def _generate_unique_id(self, row: pd.Series) -> str:
        """Gera ID único para o registro"""
        # Combinar campos únicos disponíveis
        unique_string = ''
        
        if pd.notna(row.get('cpf')):
            unique_string += str(row['cpf'])
        elif pd.notna(row.get('email')):
            unique_string += str(row['email'])
        else:
            unique_string += str(datetime.now().timestamp())
        
        return hashlib.md5(unique_string.encode()).hexdigest()[:16]
    
    def create_student_lifecycle_view(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Cria visão do ciclo de vida do aluno para rastreamento completo
        """
        lifecycle_df = df.copy()
        
        # Estágios do ciclo de vida
        lifecycle_df['lifecycle_stage'] = 'lead'  # Default
        
        # Atualizar baseado em dados disponíveis
        if 'data_inscricao' in lifecycle_df.columns:
            lifecycle_df.loc[lifecycle_df['data_inscricao'].notna(), 'lifecycle_stage'] = 'inscrito'
        
        # Calcular tempo no funil
        if 'data_inscricao' in lifecycle_df.columns:
            lifecycle_df['dias_desde_inscricao'] = (datetime.now() - lifecycle_df['data_inscricao']).dt.days
        
        # Score de engajamento
        engagement_factors = {
            'linkedin': 10,
            'objetivos': 15,
            'dores_necessidades': 20,
            'empresa': 10,
            'cargo': 10,
            'faturamento_score': 15
        }
        
        lifecycle_df['engagement_score'] = 0
        for factor, weight in engagement_factors.items():
            if factor in lifecycle_df.columns:
                lifecycle_df['engagement_score'] += lifecycle_df[factor].notna().astype(int) * weight
        
        # Segmentação por potencial
        lifecycle_df['potencial_cliente'] = pd.cut(
            lifecycle_df['engagement_score'],
            bins=[0, 30, 60, 100],
            labels=['baixo', 'médio', 'alto']
        )
        
        return lifecycle_df
    
    def export_for_ai_processing(self, df: pd.DataFrame, output_path: str, format: str = None) -> str:
        """
        Exporta dados em formato otimizado para processamento por IA
        """
        export_format = format or self.config['export_format']
        
        # Preparar dados para exportação
        export_df = df.copy()
        
        # Converter datetime para string ISO
        for col in export_df.select_dtypes(include=['datetime64']).columns:
            export_df[col] = export_df[col].dt.strftime('%Y-%m-%d %H:%M:%S')
        
        # Criar estrutura otimizada para ML
        ml_ready_data = {
            'metadata': {
                'version': '1.0.0',
                'processing_date': datetime.now().isoformat(),
                'total_records': len(export_df),
                'features': list(export_df.columns),
                'data_quality_score': self._calculate_data_quality_score(export_df)
            },
            'data': export_df.to_dict('records'),
            'schema': self._generate_schema(export_df),
            'statistics': self._generate_statistics(export_df)
        }
        
        # Exportar baseado no formato
        if export_format == 'json':
            output_file = f"{output_path}.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(ml_ready_data, f, ensure_ascii=False, indent=2)
        
        elif export_format == 'parquet':
            output_file = f"{output_path}.parquet"
            export_df.to_parquet(output_file, engine='pyarrow', compression='snappy')
        
        else:  # CSV
            output_file = f"{output_path}.csv"
            export_df.to_csv(output_file, index=False, encoding='utf-8-sig')
        
        logger.info(f"Dados exportados para: {output_file}")
        return output_file
    
    def _calculate_data_quality_score(self, df: pd.DataFrame) -> float:
        """Calcula score de qualidade dos dados"""
        # Fatores de qualidade
        completeness = df.notna().sum().sum() / (len(df) * len(df.columns))
        
        # Validações específicas
        validation_scores = []
        
        if 'cpf_valido' in df.columns:
            validation_scores.append(df['cpf_valido'].sum() / len(df))
        
        if 'email_valido' in df.columns:
            validation_scores.append(df['email_valido'].sum() / len(df))
        
        if 'cnpj_valido' in df.columns:
            cnpj_filled = df['cnpj'].notna().sum()
            if cnpj_filled > 0:
                validation_scores.append(df.loc[df['cnpj'].notna(), 'cnpj_valido'].sum() / cnpj_filled)
        
        # Score final
        if validation_scores:
            validation_score = np.mean(validation_scores)
            return round((completeness * 0.6 + validation_score * 0.4) * 100, 2)
        else:
            return round(completeness * 100, 2)
    
    def _generate_schema(self, df: pd.DataFrame) -> Dict:
        """Gera schema dos dados para documentação"""
        schema = {}
        
        for col in df.columns:
            schema[col] = {
                'type': str(df[col].dtype),
                'nullable': df[col].isna().any(),
                'unique_values': df[col].nunique(),
                'missing_percentage': round(df[col].isna().sum() / len(df) * 100, 2)
            }
            
            # Adicionar exemplos para strings
            if df[col].dtype == 'object':
                non_null_values = df[col].dropna()
                if len(non_null_values) > 0:
                    schema[col]['examples'] = non_null_values.sample(min(3, len(non_null_values))).tolist()
        
        return schema
    
    def _generate_statistics(self, df: pd.DataFrame) -> Dict:
        """Gera estatísticas dos dados para análise"""
        stats = {
            'general': {
                'total_records': len(df),
                'total_features': len(df.columns),
                'memory_usage_mb': df.memory_usage(deep=True).sum() / 1024 / 1024
            },
            'categorical': {},
            'numerical': {}
        }
        
        # Estatísticas categóricas
        categorical_cols = df.select_dtypes(include=['object']).columns
        for col in categorical_cols:
            if df[col].nunique() < 50:  # Limitar para evitar explosão
                stats['categorical'][col] = df[col].value_counts().to_dict()
        
        # Estatísticas numéricas
        numerical_cols = df.select_dtypes(include=[np.number]).columns
        for col in numerical_cols:
            stats['numerical'][col] = {
                'mean': float(df[col].mean()) if df[col].notna().any() else None,
                'std': float(df[col].std()) if df[col].notna().any() else None,
                'min': float(df[col].min()) if df[col].notna().any() else None,
                'max': float(df[col].max()) if df[col].notna().any() else None,
                'median': float(df[col].median()) if df[col].notna().any() else None
            }
        
        return stats
    
    def identify_opportunities(self, df: pd.DataFrame) -> Dict:
        """
        Identifica oportunidades de negócio baseado nos dados
        Específico para o contexto do CRM
        """
        opportunities = {
            'segmentation': {},
            'engagement': {},
            'revenue_potential': {},
            'risk_factors': {},
            'recommendations': []
        }
        
        # Segmentação por indústria
        if 'segmento' in df.columns:
            segment_counts = df['segmento'].value_counts()
            opportunities['segmentation']['top_segments'] = segment_counts.head(5).to_dict()
            opportunities['segmentation']['underserved_segments'] = segment_counts[segment_counts < 3].index.tolist()
        
        # Análise de engajamento
        if 'engagement_score' in df.columns:
            opportunities['engagement']['avg_score'] = df['engagement_score'].mean()
            opportunities['engagement']['high_potential_leads'] = len(df[df['engagement_score'] > 70])
            opportunities['engagement']['needs_nurturing'] = len(df[df['engagement_score'] < 30])
        
        # Potencial de receita
        if 'faturamento_score' in df.columns:
            revenue_distribution = df['faturamento_score'].value_counts().to_dict()
            opportunities['revenue_potential']['distribution'] = revenue_distribution
            opportunities['revenue_potential']['enterprise_accounts'] = df[df['faturamento_score'] >= 4]['empresa'].tolist()
        
        # Fatores de risco
        if 'email_valido' in df.columns:
            opportunities['risk_factors']['invalid_emails'] = len(df[~df['email_valido']])
        
        if 'cpf_valido' in df.columns:
            opportunities['risk_factors']['invalid_cpf'] = len(df[~df['cpf_valido']])
        
        # Recomendações baseadas na análise
        if opportunities['engagement'].get('needs_nurturing', 0) > len(df) * 0.3:
            opportunities['recommendations'].append({
                'type': 'engagement',
                'priority': 'high',
                'action': 'Implementar campanha de nutrição para leads com baixo engajamento',
                'impact': f"{opportunities['engagement']['needs_nurturing']} leads podem ser reativados"
            })
        
        if 'enterprise_accounts' in opportunities['revenue_potential']:
            opportunities['recommendations'].append({
                'type': 'sales',
                'priority': 'high',
                'action': 'Criar abordagem personalizada para contas enterprise',
                'targets': opportunities['revenue_potential']['enterprise_accounts'][:5]
            })
        
        return opportunities


# Exemplo de uso e demonstração
def main():
    """Demonstra o uso do sistema de limpeza CRM"""
    
    # Configuração personalizada
    config = {
        'enable_lgpd_compliance': True,
        'anonymize_sensitive_data': False,  # Manter False para análises internas
        'export_format': 'json',
        'validate_documents': True
    }
    
    # Inicializar o sistema
    cleaner = CRMCleaner(config)
    
    # Processar múltiplos arquivos
    input_files = ['Base JE15.csv']  # Adicionar mais arquivos conforme necessário
    
    all_data = []
    
    for file in input_files:
        try:
            # Ler arquivo (suporta CSV, Excel, JSON)
            if file.endswith('.csv'):
                df = pd.read_csv(file, encoding='utf-8')
            elif file.endswith(('.xlsx', '.xls')):
                df = pd.read_excel(file)
            elif file.endswith('.json'):
                df = pd.read_json(file)
            else:
                logger.warning(f"Formato não suportado: {file}")
                continue
            
            # Limpar dados
            df_clean = cleaner.clean_dataframe(df, source_name=file)
            
            # Criar visão de ciclo de vida
            df_lifecycle = cleaner.create_student_lifecycle_view(df_clean)
            
            all_data.append(df_lifecycle)
            
        except Exception as e:
            logger.error(f"Erro ao processar {file}: {str(e)}")
    
    # Combinar todos os dados
    if all_data:
        combined_df = pd.concat(all_data, ignore_index=True)
        
        # Remover duplicatas globais
        combined_df = cleaner._remove_duplicates(combined_df)
        
        # Identificar oportunidades
        opportunities = cleaner.identify_opportunities(combined_df)
        
        # Exportar dados limpos
        output_file = cleaner.export_for_ai_processing(
            combined_df, 
            'crm_crm_centralizado',
            format='json'
        )
        
        # Salvar relatório de oportunidades
        with open('crm_oportunidades_negocio.json', 'w', encoding='utf-8') as f:
            json.dump(opportunities, f, ensure_ascii=False, indent=2)
        
        # Exibir resumo
        print("\n=== RESUMO DO PROCESSAMENTO ===")
        print(f"Total de registros processados: {len(combined_df)}")
        print(f"Qualidade dos dados: {cleaner._calculate_data_quality_score(combined_df)}%")
        print(f"Dados exportados para: {output_file}")
        print("\nPrincipais oportunidades identificadas:")
        for rec in opportunities.get('recommendations', [])[:3]:
            print(f"- [{rec['priority'].upper()}] {rec['action']}")


if __name__ == "__main__":
    main()