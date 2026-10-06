#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Processador ETL CRM Completo - Versão PT-BR
============================================
Pipeline ETL aprimorado com:
- Nomes de colunas em português brasileiro
- Verificação e remoção de duplicatas
- Preparação para deploy no Supabase
- Relatório de qualidade de dados

Autor: AI Assistant
Data: Setembro 4, 2025
"""

import json
import pandas as pd
import numpy as np
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import warnings
from dataclasses import dataclass
import unicodedata
import hashlib

# Excel formatting
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Border, Side, Alignment, NamedStyle
from openpyxl.formatting.rule import ColorScaleRule, DataBarRule
from openpyxl.utils.dataframe import dataframe_to_rows

warnings.filterwarnings('ignore')

@dataclass
class DataQualityMetrics:
    """Métricas de qualidade de dados"""
    total_records: int
    unique_records: int
    duplicates_removed: int
    complete_records: int
    invalid_emails: int
    invalid_phones: int
    missing_critical_fields: int
    data_completeness_score: float

class CRMProcessorPTBR:
    """Processador ETL com colunas em PT-BR e verificação de duplicatas"""
    
    def __init__(self, data_dir: str = "."):
        self.data_dir = Path(data_dir)
        self.quality_metrics = {}
        self.consolidation_report = []
        self.duplicate_report = []
        
    def get_ptbr_columns_companies(self) -> Dict[str, str]:
        """Mapeamento de colunas em PT-BR para empresas"""
        return {
            'company_id': 'id_empresa',
            'company_name': 'nome_empresa',
            'website': 'site',
            'city': 'cidade',
            'state': 'estado',
            'operational_stage': 'estagio_operacional',
            'business_model': 'modelo_negocio',
            'market_sector': 'setor_mercado',
            'investment_stage': 'estagio_investimento',
            'valuation_amount': 'valor_avaliacao',
            'monthly_recurring_revenue': 'receita_recorrente_mensal',
            'last_twelve_months_revenue': 'receita_ultimos_12_meses',
            'fundraising_interest': 'interesse_captacao',
            'valuation_type': 'tipo_avaliacao',
            'valuation_date': 'data_avaliacao',
            'created_date': 'data_criacao',
            'data_source': 'fonte_dados'
        }
    
    def get_ptbr_columns_contacts(self) -> Dict[str, str]:
        """Mapeamento de colunas em PT-BR para contatos"""
        return {
            'contact_id': 'id_contato',
            'company_id': 'id_empresa',
            'contact_name': 'nome_contato',
            'email': 'email',
            'phone': 'telefone',
            'role': 'cargo',
            'is_primary': 'contato_principal',
            'email_valid': 'email_valido',
            'created_date': 'data_criacao',
            'data_source': 'fonte_dados'
        }
    
    def get_ptbr_columns_valuations(self) -> Dict[str, str]:
        """Mapeamento de colunas em PT-BR para avaliações detalhadas"""
        return {
            'valuation_id': 'id_avaliacao',
            'company_name': 'nome_empresa',
            'full_name': 'nome_completo',
            'email': 'email',
            'whatsapp': 'whatsapp',
            'website': 'site',
            'city': 'cidade',
            'state': 'estado',
            'market': 'mercado',
            'company_type': 'tipo_empresa',
            'foundation_date': 'data_fundacao',
            'valuation_amount': 'valor_avaliacao',
            'valuation_type': 'tipo_avaliacao',
            'planned_revenue': 'receita_planejada',
            'planned_ebitda': 'ebitda_planejado',
            'planned_investments': 'investimentos_planejados',
            'yearly_investments': 'investimentos_anuais',
            'current_debt': 'divida_atual',
            'fixed_assets': 'ativos_fixos',
            'stock_cash_values': 'valores_estoque_caixa',
            'receipt_days': 'dias_recebimento',
            'suppliers_days': 'dias_fornecedores',
            'stock_days': 'dias_estoque',
            'working_capital_days': 'dias_capital_giro',
            'privacy_accepted': 'privacidade_aceita',
            'timestamp': 'timestamp',
            'created_date': 'data_criacao',
            'data_source': 'fonte_dados'
        }
    
    def get_ptbr_columns_payments(self) -> Dict[str, str]:
        """Mapeamento de colunas em PT-BR para pagamentos"""
        return {
            'payment_id': 'id_pagamento',
            'customer_email': 'email_cliente',
            'valuation_id': 'id_avaliacao',
            'payment_date': 'data_pagamento',
            'payment_amount': 'valor_pagamento',
            'payment_status': 'status_pagamento',
            'service_type': 'tipo_servico',
            'analysis_paid': 'analise_paga',
            'created_date': 'data_criacao',
            'data_source': 'fonte_dados'
        }
    
    def get_ptbr_columns_gpt(self) -> Dict[str, str]:
        """Mapeamento de colunas em PT-BR para interações GPT"""
        return {
            'interaction_id': 'id_interacao',
            'user_name': 'nome_usuario',
            'email': 'email',
            'created_date': 'data_criacao',
            'spreadsheet_id': 'id_planilha',
            'consent_given': 'consentimento_dado',
            'data_source': 'fonte_dados'
        }
    
    def get_ptbr_columns_payment_links(self) -> Dict[str, str]:
        """Mapeamento de colunas em PT-BR para links de pagamento"""
        return {
            'link_id': 'id_link',
            'link_url': 'url_link',
            'email': 'email',
            'status': 'status',
            'created_date': 'data_criacao',
            'data_source': 'fonte_dados'
        }
    
    def get_ptbr_columns_metrics(self) -> Dict[str, str]:
        """Mapeamento de colunas em PT-BR para métricas"""
        return {
            'service_type': 'tipo_servico',
            'total_valuations': 'total_avaliacoes',
            'average_valuation': 'avaliacao_media',
            'average_revenue': 'receita_media',
            'average_ebitda': 'ebitda_medio',
            'total_paid_valuations': 'total_avaliacoes_pagas',
            'total_paid_value': 'valor_total_pago',
            'report_date': 'data_relatorio',
            'data_source': 'fonte_dados'
        }
    
    def create_record_hash(self, record: Dict, key_fields: List[str]) -> str:
        """Cria hash único para identificar duplicatas"""
        key_values = []
        for field in key_fields:
            value = record.get(field, '')
            if pd.notna(value):
                key_values.append(str(value).lower().strip())
            else:
                key_values.append('')
        
        hash_string = '|'.join(key_values)
        return hashlib.md5(hash_string.encode()).hexdigest()
    
    def remove_duplicates(self, df: pd.DataFrame, key_columns: List[str], 
                         dataset_name: str) -> pd.DataFrame:
        """Remove duplicatas e registra no relatório"""
        if df.empty:
            return df
        
        initial_count = len(df)
        
        # Criar hash para cada registro
        df['_hash'] = df.apply(
            lambda row: self.create_record_hash(row.to_dict(), key_columns),
            axis=1
        )
        
        # Remover duplicatas baseadas no hash
        df_unique = df.drop_duplicates(subset=['_hash'], keep='first')
        df_unique = df_unique.drop('_hash', axis=1)
        
        duplicates_removed = initial_count - len(df_unique)
        
        if duplicates_removed > 0:
            self.duplicate_report.append({
                'dataset': dataset_name,
                'initial_count': initial_count,
                'unique_count': len(df_unique),
                'duplicates_removed': duplicates_removed,
                'key_columns': ', '.join(key_columns)
            })
            
            print(f"  ⚠️ Removidas {duplicates_removed} duplicatas de {dataset_name}")
        
        return df_unique
    
    def load_all_json_files(self) -> Dict[str, List[Dict]]:
        """Carrega todos os arquivos JSON"""
        data_files = {}
        
        # CRM Valuation - Merge e remove duplicatas
        crm_files = list(self.data_dir.glob("crm-valuation-*.json"))
        all_crm_data = []
        crm_ids = set()
        
        for f in crm_files:
            try:
                with open(f, 'r', encoding='utf-8') as file:
                    data = json.load(file)
                    for record in data:
                        record_id = record.get('ID')
                        if record_id and record_id not in crm_ids:
                            all_crm_data.append(record)
                            crm_ids.add(record_id)
                print(f"✓ Carregado {f.name}")
            except Exception as e:
                print(f"✗ Erro ao carregar {f}: {e}")
        
        data_files['crm'] = all_crm_data
        print(f"  → Total de registros CRM únicos: {len(all_crm_data)}")
        
        # Valuation detalhado
        valuation_files = list(self.data_dir.glob("valuation-*.json"))
        valuation_data = []
        valuation_ids = set()
        
        for f in valuation_files:
            try:
                with open(f, 'r', encoding='utf-8') as file:
                    data = json.load(file)
                    for record in data:
                        record_id = record.get('id', '')
                        if record_id not in valuation_ids:
                            valuation_data.append(record)
                            valuation_ids.add(record_id)
                print(f"✓ Carregado {f.name}: {len(data)} registros")
            except Exception as e:
                print(f"✗ Erro: {e}")
        
        data_files['valuation-detailed'] = valuation_data
        print(f"  → Total de avaliações únicas: {len(valuation_data)}")
        
        # Outros arquivos...
        other_files = {
            'gpt-interactions': 'opoderdoequitygpt-*.json',
            'payments': 'payments-*.json',
            'paymentLinks': 'paymentLinks-*.json',
            'senseMetrics': 'senseMetrics-*.json',
            'crmMetrics': 'crmMetrics-*.json'
        }
        
        for key, pattern in other_files.items():
            files = list(self.data_dir.glob(pattern))
            if files:
                try:
                    with open(files[-1], 'r', encoding='utf-8') as f:
                        data_files[key] = json.load(f)
                    print(f"✓ Carregado {len(data_files[key])} registros de {key}")
                except Exception as e:
                    print(f"✗ Erro ao carregar {key}: {e}")
        
        return data_files
    
    def clean_brazilian_date(self, date_str: str) -> Optional[str]:
        """Converte formato brasileiro de data para dd/mm/yyyy HH:MM"""
        if not date_str or pd.isna(date_str):
            return None
        
        try:
            date_str = str(date_str).strip()
            
            if ', ' in date_str:
                date_part, time_part = date_str.split(', ')
                dt = datetime.strptime(f"{date_part} {time_part}", '%d/%m/%Y %H:%M:%S')
            elif '/' in date_str and len(date_str) == 10:
                dt = datetime.strptime(date_str, '%d/%m/%Y')
            elif date_str.isdigit():
                dt = datetime.fromtimestamp(int(date_str) / 1000)
            else:
                return date_str
            
            return dt.strftime('%d/%m/%Y %H:%M')
        except:
            return date_str
    
    def clean_brazilian_phone(self, phone_str: str) -> Optional[str]:
        """Padroniza telefones brasileiros"""
        if not phone_str or pd.isna(phone_str):
            return None
        
        digits = re.sub(r'\D', '', str(phone_str))
        
        if len(digits) == 13 and digits.startswith('55'):
            # +55 11 99999-9999
            area = digits[2:4]
            number = digits[4:]
            return f"+55 ({area}) {number[:5]}-{number[5:]}"
        elif len(digits) in [10, 11]:
            if len(digits) == 10:
                area = digits[:2]
                number = digits[2:]
                return f"({area}) {number[:4]}-{number[4:]}"
            else:
                area = digits[:2]
                number = digits[2:]
                return f"({area}) {number[:5]}-{number[5:]}"
        
        return phone_str
    
    def clean_brazilian_currency(self, amount: Any) -> float:
        """Converte valores monetários brasileiros para float"""
        if pd.isna(amount) or amount is None:
            return 0.0
        
        if isinstance(amount, (int, float)):
            return float(amount)
        
        amount_str = str(amount).replace('R$', '').replace('.', '').replace(',', '.')
        amount_str = re.sub(r'[^\d.,]', '', amount_str)
        
        try:
            return float(amount_str)
        except ValueError:
            return 0.0
    
    def normalize_text(self, text: str) -> str:
        """Normaliza texto português"""
        if not text or pd.isna(text):
            return ""
        
        text = unicodedata.normalize('NFD', str(text))
        text = ''.join(char for char in text if unicodedata.category(char) != 'Mn')
        text = text.strip()
        text = re.sub(r'\s+', ' ', text)
        
        return text
    
    def validate_email(self, email: str) -> bool:
        """Valida formato de email"""
        if not email or pd.isna(email):
            return False
        
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(email_regex, str(email)))
    
    def parse_location(self, location_str: str) -> Tuple[str, str]:
        """Analisa formato cidade/estado brasileiro"""
        if not location_str or pd.isna(location_str):
            return "", ""
        
        location_str = str(location_str).strip()
        if '/' in location_str:
            parts = location_str.split('/')
            city = parts[0].strip()
            state = parts[1].strip().upper() if len(parts) > 1 else ""
            return city, state
        
        return location_str, ""
    
    def process_companies_data(self, crm_data: List[Dict]) -> pd.DataFrame:
        """Processa dados de empresas do CRM"""
        if not crm_data:
            return pd.DataFrame()
        
        companies = []
        for record in crm_data:
            city, state = self.parse_location(record.get('Cidade/Estado', ''))
            
            company = {
                'company_id': record.get('ID', ''),
                'company_name': self.normalize_text(record.get('Nome da Startup', '')),
                'website': record.get('Site', ''),
                'city': city,
                'state': state,
                'operational_stage': record.get('Estágio Operacional', ''),
                'business_model': record.get('Modelo de Negócio', ''),
                'market_sector': record.get('Mercado', ''),
                'investment_stage': record.get('Estágio de Investimento', ''),
                'valuation_amount': self.clean_brazilian_currency(record.get('Valuation', 0)),
                'monthly_recurring_revenue': self.clean_brazilian_currency(record.get('MRR', 0)),
                'last_twelve_months_revenue': self.clean_brazilian_currency(record.get('LTM', 0)),
                'fundraising_interest': record.get('Captação', ''),
                'valuation_type': record.get('Tipo de Valuation', ''),
                'valuation_date': self.clean_brazilian_date(record.get('Data de Valuation', '')),
                'created_date': datetime.now().strftime('%d/%m/%Y %H:%M'),
                'data_source': 'crm-valuation'
            }
            companies.append(company)
        
        df = pd.DataFrame(companies)
        
        # Remover duplicatas
        df = self.remove_duplicates(
            df, 
            ['company_id', 'company_name'], 
            'Empresas'
        )
        
        # Renomear colunas para PT-BR
        df = df.rename(columns=self.get_ptbr_columns_companies())
        
        # Calcular métricas
        total_records = len(df)
        unique_records = df['id_empresa'].nunique()
        complete_records = df.dropna(subset=['nome_empresa', 'valor_avaliacao']).shape[0]
        
        self.quality_metrics['empresas'] = DataQualityMetrics(
            total_records=total_records,
            unique_records=unique_records,
            duplicates_removed=total_records - unique_records,
            complete_records=complete_records,
            invalid_emails=0,
            invalid_phones=0,
            missing_critical_fields=total_records - complete_records,
            data_completeness_score=(complete_records / total_records * 100) if total_records > 0 else 0
        )
        
        self.consolidation_report.append(f"Empresas: {total_records} registros processados")
        
        return df
    
    def process_detailed_valuations(self, valuation_data: List[Dict]) -> pd.DataFrame:
        """Processa dados de avaliações detalhadas"""
        if not valuation_data:
            return pd.DataFrame()
        
        valuations = []
        for record in valuation_data:
            # Campos flat com pontos
            city = record.get('overview.city', '')
            state = record.get('overview.state', '')
            
            valuation = {
                'valuation_id': record.get('id', ''),
                'company_name': self.normalize_text(record.get('overview.company', record.get('company', ''))),
                'full_name': self.normalize_text(record.get('overview.fullName', '')),
                'email': record.get('overview.email', record.get('email', '')),
                'whatsapp': self.clean_brazilian_phone(record.get('overview.whatsapp', '')),
                'website': record.get('overview.website', ''),
                'city': city,
                'state': state,
                'market': record.get('overview.market', ''),
                'company_type': record.get('overview.type', ''),
                'foundation_date': self.clean_brazilian_date(record.get('overview.foundationDate', '')),
                'valuation_amount': self.clean_brazilian_currency(record.get('valuation', 0)),
                'valuation_type': record.get('valuationType', ''),
                'planned_revenue': self.clean_brazilian_currency(record.get('financials.currentPlannedRevenue', 0)),
                'planned_ebitda': self.clean_brazilian_currency(record.get('financials.currentPlannedEBITDA', 0)),
                'planned_investments': self.clean_brazilian_currency(record.get('financials.currentPlannedInvestments', 0)),
                'yearly_investments': self.clean_brazilian_currency(record.get('financials.yearlyPlannedInvestments', 0)),
                'current_debt': self.clean_brazilian_currency(record.get('financials.currentDebt', 0)),
                'fixed_assets': self.clean_brazilian_currency(record.get('financials.fixedAssets', 0)),
                'stock_cash_values': self.clean_brazilian_currency(record.get('financials.stockAndCashValues', 0)),
                'receipt_days': record.get('financials.timeframes.receipt', 0),
                'suppliers_days': record.get('financials.timeframes.suppliers', 0),
                'stock_days': record.get('financials.timeframes.stock', 0),
                'working_capital_days': record.get('financials.timeframes.workingCapital', 0),
                'privacy_accepted': record.get('privacy', False),
                'timestamp': self.clean_brazilian_date(str(record.get('timestamp', ''))),
                'created_date': datetime.now().strftime('%d/%m/%Y %H:%M'),
                'data_source': 'valuation-detailed'
            }
            valuations.append(valuation)
        
        df = pd.DataFrame(valuations)
        
        # Remover duplicatas
        df = self.remove_duplicates(
            df,
            ['valuation_id', 'company_name', 'email'],
            'Avaliações Detalhadas'
        )
        
        # Renomear colunas para PT-BR
        df = df.rename(columns=self.get_ptbr_columns_valuations())
        
        # Métricas
        total_records = len(df)
        unique_records = df['id_avaliacao'].nunique()
        complete_records = df.dropna(subset=['nome_empresa', 'valor_avaliacao']).shape[0]
        invalid_emails = (~df['email'].apply(self.validate_email)).sum()
        
        self.quality_metrics['avaliacoes_detalhadas'] = DataQualityMetrics(
            total_records=total_records,
            unique_records=unique_records,
            duplicates_removed=total_records - unique_records,
            complete_records=complete_records,
            invalid_emails=invalid_emails,
            invalid_phones=df['whatsapp'].isna().sum(),
            missing_critical_fields=total_records - complete_records,
            data_completeness_score=(complete_records / total_records * 100) if total_records > 0 else 0
        )
        
        self.consolidation_report.append(f"Avaliações Detalhadas: {total_records} registros processados")
        
        return df
    
    def process_contacts_data(self, crm_data: List[Dict]) -> pd.DataFrame:
        """Processa dados de contatos"""
        if not crm_data:
            return pd.DataFrame()
        
        contacts = []
        for record in crm_data:
            contact = {
                'contact_id': f"contact_{record.get('ID', '')}",
                'company_id': record.get('ID', ''),
                'contact_name': self.normalize_text(record.get('Nome do Respondente', '')),
                'email': record.get('Email', '').lower().strip(),
                'phone': self.clean_brazilian_phone(record.get('Telefone', '')),
                'role': 'Contato Principal',
                'is_primary': True,
                'email_valid': self.validate_email(record.get('Email', '')),
                'created_date': self.clean_brazilian_date(record.get('Data de Valuation', '')),
                'data_source': 'crm-valuation'
            }
            contacts.append(contact)
        
        df = pd.DataFrame(contacts)
        
        # Remover duplicatas
        df = self.remove_duplicates(
            df,
            ['company_id', 'email'],
            'Contatos'
        )
        
        # Renomear colunas para PT-BR
        df = df.rename(columns=self.get_ptbr_columns_contacts())
        
        # Métricas
        total_records = len(df)
        unique_records = df['email'].nunique()
        complete_records = df.dropna(subset=['nome_contato', 'email']).shape[0]
        invalid_emails = (~df['email_valido']).sum()
        
        self.quality_metrics['contatos'] = DataQualityMetrics(
            total_records=total_records,
            unique_records=unique_records,
            duplicates_removed=total_records - unique_records,
            complete_records=complete_records,
            invalid_emails=invalid_emails,
            invalid_phones=df['telefone'].isna().sum(),
            missing_critical_fields=total_records - complete_records,
            data_completeness_score=(complete_records / total_records * 100) if total_records > 0 else 0
        )
        
        self.consolidation_report.append(f"Contatos: {total_records} registros processados")
        
        return df
    
    def process_payments_data(self, payments_data: List[Dict]) -> pd.DataFrame:
        """Processa dados de pagamentos"""
        if not payments_data:
            return pd.DataFrame()
        
        payments = []
        payment_ids = set()
        
        for record in payments_data:
            base_data = {
                'customer_email': record.get('email', record.get('id', '')),
                'analysis_paid': record.get('analysis.paid', False)
            }
            
            for key, value in record.items():
                if key.startswith('valuations.') and key.endswith('.date'):
                    valuation_id = key.split('.')[1]
                    
                    # Evitar duplicatas
                    payment_id = f"payment_{valuation_id}"
                    if payment_id not in payment_ids:
                        payment = {
                            'payment_id': payment_id,
                            'customer_email': base_data['customer_email'],
                            'valuation_id': valuation_id,
                            'payment_date': self.clean_brazilian_date(value),
                            'payment_amount': self.clean_brazilian_currency(
                                record.get(f'valuations.{valuation_id}.amount', 0)
                            ),
                            'payment_status': record.get(f'valuations.{valuation_id}.paid', False),
                            'service_type': record.get(f'valuations.{valuation_id}.type', ''),
                            'analysis_paid': base_data['analysis_paid'],
                            'created_date': datetime.now().strftime('%d/%m/%Y %H:%M'),
                            'data_source': 'payments'
                        }
                        payments.append(payment)
                        payment_ids.add(payment_id)
        
        df = pd.DataFrame(payments)
        
        if not df.empty:
            # Remover duplicatas
            df = self.remove_duplicates(
                df,
                ['payment_id', 'valuation_id'],
                'Pagamentos'
            )
            
            # Renomear colunas para PT-BR
            df = df.rename(columns=self.get_ptbr_columns_payments())
            
            # Métricas
            total_records = len(df)
            unique_records = df['id_pagamento'].nunique()
            complete_records = df.dropna(subset=['email_cliente', 'valor_pagamento']).shape[0]
            
            self.quality_metrics['pagamentos'] = DataQualityMetrics(
                total_records=total_records,
                unique_records=unique_records,
                duplicates_removed=total_records - unique_records,
                complete_records=complete_records,
                invalid_emails=(~df['email_cliente'].apply(self.validate_email)).sum(),
                invalid_phones=0,
                missing_critical_fields=total_records - complete_records,
                data_completeness_score=(complete_records / total_records * 100) if total_records > 0 else 0
            )
            
            self.consolidation_report.append(f"Pagamentos: {total_records} registros processados")
        
        return df
    
    def process_gpt_interactions(self, gpt_data: List[Dict]) -> pd.DataFrame:
        """Processa interações GPT"""
        if not gpt_data:
            return pd.DataFrame()
        
        interactions = []
        for record in gpt_data:
            interaction = {
                'interaction_id': record.get('id', ''),
                'user_name': self.normalize_text(record.get('name', '')),
                'email': record.get('email', '').lower().strip(),
                'created_date': self.clean_brazilian_date(record.get('createdAt', '')),
                'spreadsheet_id': record.get('spreadsheetId', ''),
                'consent_given': record.get('consent', False),
                'data_source': 'gpt-interactions'
            }
            interactions.append(interaction)
        
        df = pd.DataFrame(interactions)
        
        # Remover duplicatas
        df = self.remove_duplicates(
            df,
            ['interaction_id', 'email'],
            'Interações GPT'
        )
        
        # Renomear colunas para PT-BR
        df = df.rename(columns=self.get_ptbr_columns_gpt())
        
        # Métricas
        total_records = len(df)
        unique_records = df['id_interacao'].nunique()
        complete_records = df.dropna(subset=['nome_usuario', 'email']).shape[0]
        invalid_emails = (~df['email'].apply(self.validate_email)).sum()
        
        self.quality_metrics['interacoes_gpt'] = DataQualityMetrics(
            total_records=total_records,
            unique_records=unique_records,
            duplicates_removed=total_records - unique_records,
            complete_records=complete_records,
            invalid_emails=invalid_emails,
            invalid_phones=0,
            missing_critical_fields=total_records - complete_records,
            data_completeness_score=(complete_records / total_records * 100) if total_records > 0 else 0
        )
        
        self.consolidation_report.append(f"Interações GPT: {total_records} registros processados")
        
        return df
    
    def process_payment_links(self, links_data: List[Dict]) -> pd.DataFrame:
        """Processa links de pagamento"""
        if not links_data:
            return pd.DataFrame()
        
        links = []
        for record in links_data:
            link = {
                'link_id': record.get('id', ''),
                'link_url': record.get('url', ''),
                'email': record.get('email', ''),
                'status': record.get('status', ''),
                'created_date': self.clean_brazilian_date(record.get('createdAt', '')),
                'data_source': 'payment-links'
            }
            links.append(link)
        
        df = pd.DataFrame(links)
        
        # Remover duplicatas
        df = self.remove_duplicates(
            df,
            ['link_id'],
            'Links de Pagamento'
        )
        
        # Renomear colunas para PT-BR
        df = df.rename(columns=self.get_ptbr_columns_payment_links())
        
        self.consolidation_report.append(f"Links de Pagamento: {len(df)} registros processados")
        
        return df
    
    def process_metrics_data(self, sense_data: List[Dict], crm_data: List[Dict]) -> pd.DataFrame:
        """Processa dados de métricas"""
        metrics = []
        
        for record in sense_data:
            if record.get('id') == 'bigNumbers':
                metric = {
                    'service_type': 'Sense',
                    'total_valuations': record.get('totalValuations', 0),
                    'average_valuation': record.get('averageValuation', 0),
                    'average_revenue': record.get('averageRevenue', 0),
                    'average_ebitda': record.get('averageEBITDA', 0),
                    'total_paid_valuations': record.get('totalPaidValuations', 0),
                    'total_paid_value': record.get('totalPaidValue', 0),
                    'report_date': datetime.now().strftime('%d/%m/%Y %H:%M'),
                    'data_source': 'senseMetrics'
                }
                metrics.append(metric)
        
        for record in crm_data:
            if record.get('id') == 'bigNumbers':
                metric = {
                    'service_type': 'CRM',
                    'total_valuations': record.get('totalValuations', 0),
                    'average_valuation': 0,
                    'average_revenue': 0,
                    'average_ebitda': 0,
                    'total_paid_valuations': record.get('totalPaidValuations', 0),
                    'total_paid_value': record.get('totalPaidValue', 0),
                    'report_date': datetime.now().strftime('%d/%m/%Y %H:%M'),
                    'data_source': 'crmMetrics'
                }
                metrics.append(metric)
        
        df = pd.DataFrame(metrics)
        
        # Renomear colunas para PT-BR
        df = df.rename(columns=self.get_ptbr_columns_metrics())
        
        self.consolidation_report.append(f"Métricas: {len(df)} registros processados")
        
        return df
    
    def create_styled_workbook(self) -> Workbook:
        """Cria workbook com estilos profissionais"""
        wb = Workbook()
        
        # Definir estilos
        header_style = NamedStyle(name="header_style")
        header_style.font = Font(bold=True, color="FFFFFF", size=12)
        header_style.fill = PatternFill("solid", fgColor="366092")
        header_style.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        header_style.border = Border(
            left=Side(style='thin'), right=Side(style='thin'),
            top=Side(style='thin'), bottom=Side(style='thin')
        )
        
        data_style = NamedStyle(name="data_style")
        data_style.font = Font(size=10)
        data_style.alignment = Alignment(horizontal="left", vertical="center")
        data_style.border = Border(
            left=Side(style='thin'), right=Side(style='thin'),
            top=Side(style='thin'), bottom=Side(style='thin')
        )
        
        wb.add_named_style(header_style)
        wb.add_named_style(data_style)
        
        return wb
    
    def create_worksheet_generic(self, wb: Workbook, df: pd.DataFrame, 
                                sheet_name: str, currency_cols: List[str] = None,
                                date_cols: List[str] = None):
        """Cria worksheet genérica formatada"""
        if df.empty:
            return
        
        ws = wb.create_sheet(sheet_name)
        
        # Escrever dados
        for r in dataframe_to_rows(df, index=False, header=True):
            ws.append(r)
        
        # Aplicar estilos no cabeçalho
        for cell in ws[1]:
            cell.style = "header_style"
        
        # Aplicar estilos nos dados
        for row in ws.iter_rows(min_row=2):
            for cell in row:
                cell.style = "data_style"
                
                # Formatar colunas de moeda
                if currency_cols and cell.column_letter in currency_cols:
                    cell.number_format = 'R$ #,##0.00'
                
                # Formatar colunas de data
                if date_cols and cell.column_letter in date_cols:
                    cell.number_format = 'DD/MM/YYYY HH:MM'
        
        # Ajustar largura das colunas
        for column in ws.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)
            ws.column_dimensions[column_letter].width = adjusted_width
        
        # Congelar painéis
        ws.freeze_panes = 'A2'
    
    def create_duplicate_report_worksheet(self, wb: Workbook):
        """Cria worksheet com relatório de duplicatas"""
        ws = wb.create_sheet("Relatório de Duplicatas")
        
        # Título
        ws['A1'] = "Relatório de Remoção de Duplicatas"
        ws['A1'].font = Font(bold=True, size=16, color="366092")
        ws.merge_cells('A1:E1')
        
        ws['A3'] = datetime.now().strftime('Gerado em: %d/%m/%Y %H:%M')
        ws['A3'].font = Font(italic=True)
        
        # Cabeçalhos
        headers = ['Dataset', 'Registros Iniciais', 'Registros Únicos', 
                  'Duplicatas Removidas', 'Campos Chave']
        
        for col, header in enumerate(headers, 1):
            ws.cell(row=5, column=col, value=header)
            ws.cell(row=5, column=col).style = "header_style"
        
        # Dados
        row = 6
        total_duplicates = 0
        
        for report in self.duplicate_report:
            ws.cell(row=row, column=1, value=report['dataset'])
            ws.cell(row=row, column=2, value=report['initial_count'])
            ws.cell(row=row, column=3, value=report['unique_count'])
            ws.cell(row=row, column=4, value=report['duplicates_removed'])
            ws.cell(row=row, column=5, value=report['key_columns'])
            
            total_duplicates += report['duplicates_removed']
            
            # Destacar linhas com duplicatas
            if report['duplicates_removed'] > 0:
                for col in range(1, 6):
                    ws.cell(row=row, column=col).fill = PatternFill("solid", fgColor="FFE6E6")
            
            row += 1
        
        # Total
        row += 1
        ws.cell(row=row, column=1, value="TOTAL")
        ws.cell(row=row, column=1).font = Font(bold=True)
        ws.cell(row=row, column=4, value=total_duplicates)
        ws.cell(row=row, column=4).font = Font(bold=True)
        
        # Ajustar larguras
        for column_letter in ['A', 'B', 'C', 'D', 'E']:
            ws.column_dimensions[column_letter].width = 25
    
    def create_supabase_prep_worksheet(self, wb: Workbook):
        """Cria worksheet com preparação para Supabase"""
        ws = wb.create_sheet("Prep Supabase")
        
        # Título
        ws['A1'] = "Preparação para Deploy no Supabase"
        ws['A1'].font = Font(bold=True, size=16, color="366092")
        ws.merge_cells('A1:D1')
        
        ws['A3'] = "ESTRUTURA DE TABELAS RECOMENDADA"
        ws['A3'].font = Font(bold=True, size=12)
        
        # Recomendações de estrutura
        row = 5
        tables = [
            ('empresas', 'Tabela principal de empresas', 'id_empresa (PK)', 'índices: nome_empresa, email'),
            ('contatos', 'Contatos das empresas', 'id_contato (PK), id_empresa (FK)', 'índices: email, telefone'),
            ('avaliacoes', 'Avaliações detalhadas', 'id_avaliacao (PK), id_empresa (FK)', 'índices: data_avaliacao, valor_avaliacao'),
            ('pagamentos', 'Histórico de pagamentos', 'id_pagamento (PK), id_avaliacao (FK)', 'índices: data_pagamento, status_pagamento'),
            ('interacoes_gpt', 'Logs de interações GPT', 'id_interacao (PK)', 'índices: email, data_criacao'),
            ('metricas', 'Métricas agregadas', 'id (PK)', 'índices: tipo_servico, data_relatorio')
        ]
        
        headers = ['Tabela', 'Descrição', 'Chaves', 'Índices Recomendados']
        for col, header in enumerate(headers, 1):
            ws.cell(row=row, column=col, value=header)
            ws.cell(row=row, column=col).style = "header_style"
        
        row += 1
        for table_name, desc, keys, indices in tables:
            ws.cell(row=row, column=1, value=table_name)
            ws.cell(row=row, column=2, value=desc)
            ws.cell(row=row, column=3, value=keys)
            ws.cell(row=row, column=4, value=indices)
            row += 1
        
        # Best Practices
        row += 2
        ws.cell(row=row, column=1, value="MELHORES PRÁTICAS PARA DEPLOY")
        ws.cell(row=row, column=1).font = Font(bold=True, size=12)
        
        row += 2
        practices = [
            "1. Validação de Dados:",
            "   • Verificar duplicatas antes do import (FEITO ✓)",
            "   • Validar emails e telefones (FEITO ✓)",
            "   • Normalizar texto e remover acentos problemáticos",
            "",
            "2. Estrutura de Banco:",
            "   • Usar UUIDs para chaves primárias",
            "   • Implementar foreign keys para integridade referencial",
            "   • Criar índices para campos de busca frequente",
            "",
            "3. Segurança:",
            "   • Implementar RLS (Row Level Security)",
            "   • Criptografar dados sensíveis",
            "   • Usar políticas de acesso granulares",
            "",
            "4. Performance:",
            "   • Batch inserts de 1000 registros por vez",
            "   • Usar transações para operações críticas",
            "   • Implementar cache para queries frequentes",
            "",
            "5. Migração:",
            "   • Fazer backup antes de qualquer operação",
            "   • Testar em ambiente de staging primeiro",
            "   • Usar migrations versionadas",
            "",
            "6. Monitoramento:",
            "   • Implementar logs de auditoria",
            "   • Monitorar performance de queries",
            "   • Configurar alertas para erros"
        ]
        
        for practice in practices:
            ws.cell(row=row, column=1, value=practice)
            if practice.startswith("   •"):
                ws.cell(row=row, column=1).font = Font(italic=True, size=9)
            elif practice and not practice.startswith(" "):
                ws.cell(row=row, column=1).font = Font(bold=True)
            row += 1
        
        # Ajustar larguras
        ws.column_dimensions['A'].width = 30
        ws.column_dimensions['B'].width = 35
        ws.column_dimensions['C'].width = 30
        ws.column_dimensions['D'].width = 35
    
    def create_data_quality_worksheet(self, wb: Workbook):
        """Cria relatório de qualidade de dados"""
        ws = wb.create_sheet("Qualidade de Dados")
        
        # Título
        ws['A1'] = "Relatório de Qualidade de Dados"
        ws['A1'].font = Font(bold=True, size=16, color="366092")
        ws.merge_cells('A1:H1')
        
        # Cabeçalhos
        headers = ['Dataset', 'Total', 'Únicos', 'Duplicatas', 
                  'Completos', 'Emails Inválidos', 'Telefones Faltando', 'Score (%)']
        
        for col, header in enumerate(headers, 1):
            ws.cell(row=3, column=col, value=header)
            ws.cell(row=3, column=col).style = "header_style"
        
        # Dados
        row = 4
        for dataset_name, metrics in self.quality_metrics.items():
            ws.cell(row=row, column=1, value=dataset_name.replace('_', ' ').title())
            ws.cell(row=row, column=2, value=metrics.total_records)
            ws.cell(row=row, column=3, value=metrics.unique_records)
            ws.cell(row=row, column=4, value=metrics.duplicates_removed)
            ws.cell(row=row, column=5, value=metrics.complete_records)
            ws.cell(row=row, column=6, value=metrics.invalid_emails)
            ws.cell(row=row, column=7, value=metrics.invalid_phones)
            ws.cell(row=row, column=8, value=f"{metrics.data_completeness_score:.1f}%")
            
            # Colorir score
            score_cell = ws.cell(row=row, column=8)
            if metrics.data_completeness_score >= 90:
                score_cell.fill = PatternFill("solid", fgColor="C6EFCE")
            elif metrics.data_completeness_score >= 70:
                score_cell.fill = PatternFill("solid", fgColor="FFEB9C")
            else:
                score_cell.fill = PatternFill("solid", fgColor="FFC7CE")
            
            row += 1
        
        # Ajustar larguras
        for col in range(1, 9):
            column_letter = chr(64 + col)  # Convert number to letter (A, B, C...)
            ws.column_dimensions[column_letter].width = 18
    
    def run_comprehensive_etl(self) -> str:
        """Executa pipeline ETL completo com colunas PT-BR"""
        print("\n🚀 Iniciando Pipeline ETL Completo (PT-BR)...")
        print("="*60)
        
        # Carregar dados
        print("\n📂 Carregando arquivos de dados...")
        data_files = self.load_all_json_files()
        
        if not data_files:
            print("❌ Nenhum arquivo de dados encontrado!")
            return None
        
        # Processar dados
        print("\n🔄 Processando dados...")
        
        companies_df = self.process_companies_data(data_files.get('crm', []))
        print(f"✓ Processadas {len(companies_df)} empresas")
        
        contacts_df = self.process_contacts_data(data_files.get('crm', []))
        print(f"✓ Processados {len(contacts_df)} contatos")
        
        valuations_df = self.process_detailed_valuations(data_files.get('valuation-detailed', []))
        print(f"✓ Processadas {len(valuations_df)} avaliações detalhadas")
        
        gpt_df = self.process_gpt_interactions(data_files.get('gpt-interactions', []))
        print(f"✓ Processadas {len(gpt_df)} interações GPT")
        
        payments_df = self.process_payments_data(data_files.get('payments', []))
        print(f"✓ Processados {len(payments_df)} pagamentos")
        
        links_df = self.process_payment_links(data_files.get('paymentLinks', []))
        print(f"✓ Processados {len(links_df)} links de pagamento")
        
        metrics_df = self.process_metrics_data(
            data_files.get('senseMetrics', []), 
            data_files.get('crmMetrics', [])
        )
        print(f"✓ Processadas {len(metrics_df)} métricas")
        
        # Criar workbook
        print("\n📊 Criando arquivo Excel...")
        wb = self.create_styled_workbook()
        
        # Remover sheet padrão
        if "Sheet" in wb.sheetnames:
            wb.remove(wb["Sheet"])
        
        # Criar worksheets
        self.create_worksheet_generic(wb, companies_df, "Empresas")
        self.create_worksheet_generic(wb, valuations_df, "Avaliações Detalhadas")
        self.create_worksheet_generic(wb, contacts_df, "Contatos")
        self.create_worksheet_generic(wb, payments_df, "Pagamentos")
        self.create_worksheet_generic(wb, gpt_df, "Interações GPT")
        self.create_worksheet_generic(wb, links_df, "Links Pagamento")
        self.create_worksheet_generic(wb, metrics_df, "Métricas")
        
        # Relatórios especiais
        self.create_duplicate_report_worksheet(wb)
        self.create_data_quality_worksheet(wb)
        self.create_supabase_prep_worksheet(wb)
        
        # Salvar arquivo
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"CRM_Dados_PTBR_Final_{timestamp}.xlsx"
        filepath = self.data_dir / filename
        
        wb.save(filepath)
        
        # Exportar CSVs para Supabase
        csv_dir = self.data_dir / f"supabase_import_{timestamp}"
        csv_dir.mkdir(exist_ok=True)
        
        # Salvar CSVs
        companies_df.to_csv(csv_dir / "empresas.csv", index=False, encoding='utf-8-sig')
        valuations_df.to_csv(csv_dir / "avaliacoes.csv", index=False, encoding='utf-8-sig')
        contacts_df.to_csv(csv_dir / "contatos.csv", index=False, encoding='utf-8-sig')
        payments_df.to_csv(csv_dir / "pagamentos.csv", index=False, encoding='utf-8-sig')
        gpt_df.to_csv(csv_dir / "interacoes_gpt.csv", index=False, encoding='utf-8-sig')
        links_df.to_csv(csv_dir / "links_pagamento.csv", index=False, encoding='utf-8-sig')
        metrics_df.to_csv(csv_dir / "metricas.csv", index=False, encoding='utf-8-sig')
        
        print(f"\n✅ ETL Completo! Arquivo salvo: {filename}")
        print(f"📍 Local: {filepath}")
        print(f"📂 CSVs para Supabase: {csv_dir}")
        
        # Resumo
        print("\n" + "="*60)
        print("📈 RESUMO DOS DADOS:")
        print("="*60)
        print(f"Empresas: {len(companies_df)} registros")
        print(f"Avaliações Detalhadas: {len(valuations_df)} registros")
        print(f"Contatos: {len(contacts_df)} registros")
        print(f"Pagamentos: {len(payments_df)} registros")
        print(f"Interações GPT: {len(gpt_df)} registros")
        print(f"Links de Pagamento: {len(links_df)} registros")
        print(f"Métricas: {len(metrics_df)} registros")
        
        if self.duplicate_report:
            print("\n⚠️  DUPLICATAS REMOVIDAS:")
            print("-"*30)
            for report in self.duplicate_report:
                print(f"{report['dataset']}: {report['duplicates_removed']} duplicatas")
        
        print("\n💎 SCORES DE QUALIDADE:")
        print("-"*30)
        for dataset, metrics in self.quality_metrics.items():
            print(f"{dataset.replace('_', ' ').title()}: {metrics.data_completeness_score:.1f}%")
        
        return str(filepath)


def main():
    """Função principal de execução"""
    processor = CRMProcessorPTBR(".")
    result_file = processor.run_comprehensive_etl()
    
    if result_file:
        print(f"\n🎉 Sucesso! Dados prontos para Supabase!")
        print(f"📂 Abrir: {result_file}")
        print("\n📌 Próximos passos para Supabase:")
        print("   1. Revisar os CSVs gerados")
        print("   2. Criar as tabelas no Supabase conforme recomendado")
        print("   3. Importar os CSVs usando Supabase Dashboard ou API")
        print("   4. Verificar integridade dos dados após import")
    else:
        print("❌ Pipeline ETL falhou!")


if __name__ == "__main__":
    main()
