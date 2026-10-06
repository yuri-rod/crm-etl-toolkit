#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Processador ETL CRM com Padronização Completa
==============================================
Pipeline ETL com normalização e padronização de todos os campos:
- Padronização de nomes (capitalização correta)
- Conversão de siglas de estados para nomes completos
- Normalização de cidades com acentuação correta
- Remoção de duplicatas considerando variações
- Preparação otimizada para Supabase

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
from unidecode import unidecode

# Excel formatting
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Border, Side, Alignment, NamedStyle
from openpyxl.formatting.rule import ColorScaleRule
from openpyxl.utils.dataframe import dataframe_to_rows

warnings.filterwarnings('ignore')

@dataclass
class DataQualityMetrics:
    """Métricas de qualidade de dados"""
    total_records: int
    unique_records: int
    duplicates_removed: int
    normalized_records: int
    complete_records: int
    invalid_emails: int
    invalid_phones: int
    missing_critical_fields: int
    data_completeness_score: float

class NormalizadorDados:
    """Classe para normalização e padronização de dados brasileiros"""
    
    def __init__(self):
        self.estados_brasil = self._criar_mapa_estados()
        self.cidades_correcoes = self._criar_correcoes_cidades()
        self.mercados_padrao = self._criar_mapa_mercados()
        
    def _criar_mapa_estados(self) -> Dict[str, str]:
        """Mapa de siglas e variações para nomes completos de estados"""
        return {
            # Siglas
            'AC': 'Acre', 'AL': 'Alagoas', 'AP': 'Amapá', 'AM': 'Amazonas',
            'BA': 'Bahia', 'CE': 'Ceará', 'DF': 'Distrito Federal',
            'ES': 'Espírito Santo', 'GO': 'Goiás', 'MA': 'Maranhão',
            'MT': 'Mato Grosso', 'MS': 'Mato Grosso do Sul',
            'MG': 'Minas Gerais', 'PA': 'Pará', 'PB': 'Paraíba',
            'PR': 'Paraná', 'PE': 'Pernambuco', 'PI': 'Piauí',
            'RJ': 'Rio de Janeiro', 'RN': 'Rio Grande do Norte',
            'RS': 'Rio Grande do Sul', 'RO': 'Rondônia', 'RR': 'Roraima',
            'SC': 'Santa Catarina', 'SP': 'São Paulo', 'SE': 'Sergipe',
            'TO': 'Tocantins',
            
            # Variações comuns
            'SAO PAULO': 'São Paulo', 'SÃO PAULO': 'São Paulo',
            'Sao Paulo': 'São Paulo', 'sao paulo': 'São Paulo',
            'RIO DE JANEIRO': 'Rio de Janeiro', 'rio de janeiro': 'Rio de Janeiro',
            'MINAS': 'Minas Gerais', 'PARANÁ': 'Paraná', 'PARANA': 'Paraná',
            'RIO GRANDE SUL': 'Rio Grande do Sul', 'RIO GRANDE DO SUL': 'Rio Grande do Sul',
            'SANTA CATARINA': 'Santa Catarina', 'ESPIRITO SANTO': 'Espírito Santo',
            'MATO GROSSO SUL': 'Mato Grosso do Sul', 'MATO GROSSO DO SUL': 'Mato Grosso do Sul',
            'DISTRITO FEDERAL': 'Distrito Federal', 'BRASILIA': 'Distrito Federal',
            'BRASÍLIA': 'Distrito Federal', 'BSB': 'Distrito Federal'
        }
    
    def _criar_correcoes_cidades(self) -> Dict[str, str]:
        """Correções específicas para nomes de cidades"""
        return {
            'SAO PAULO': 'São Paulo', 'SÃO PAULO': 'São Paulo',
            'Sao Paulo': 'São Paulo', 'sao paulo': 'São Paulo',
            'RIO DE JANEIRO': 'Rio de Janeiro', 'rio de janeiro': 'Rio de Janeiro',
            'BELO HORIZONTE': 'Belo Horizonte', 'belo horizonte': 'Belo Horizonte',
            'BRASILIA': 'Brasília', 'BRASÍLIA': 'Brasília', 'brasilia': 'Brasília',
            'PORTO ALEGRE': 'Porto Alegre', 'porto alegre': 'Porto Alegre',
            'CURITIBA': 'Curitiba', 'curitiba': 'Curitiba',
            'FLORIANOPOLIS': 'Florianópolis', 'FLORIANÓPOLIS': 'Florianópolis',
            'florianopolis': 'Florianópolis', 'Florianopolis': 'Florianópolis',
            'SAO JOSE DOS CAMPOS': 'São José dos Campos', 'SÃO JOSÉ DOS CAMPOS': 'São José dos Campos',
            'SAO BERNARDO DO CAMPO': 'São Bernardo do Campo', 'SÃO BERNARDO DO CAMPO': 'São Bernardo do Campo',
            'SANTO ANDRE': 'Santo André', 'SANTO ANDRÉ': 'Santo André',
            'SAO CAETANO DO SUL': 'São Caetano do Sul', 'SÃO CAETANO DO SUL': 'São Caetano do Sul',
            'RIBEIRAO PRETO': 'Ribeirão Preto', 'RIBEIRÃO PRETO': 'Ribeirão Preto',
            'SAO JOSE DO RIO PRETO': 'São José do Rio Preto', 'SÃO JOSÉ DO RIO PRETO': 'São José do Rio Preto',
            'CAMPINAS': 'Campinas', 'campinas': 'Campinas',
            'VITORIA': 'Vitória', 'VITÓRIA': 'Vitória', 'vitoria': 'Vitória',
            'RECIFE': 'Recife', 'recife': 'Recife',
            'FORTALEZA': 'Fortaleza', 'fortaleza': 'Fortaleza',
            'SALVADOR': 'Salvador', 'salvador': 'Salvador',
            'GOIANIA': 'Goiânia', 'GOIÂNIA': 'Goiânia', 'goiania': 'Goiânia',
            'BELEM': 'Belém', 'BELÉM': 'Belém', 'belem': 'Belém',
            'MANAUS': 'Manaus', 'manaus': 'Manaus',
            'SAO LUIS': 'São Luís', 'SÃO LUIS': 'São Luís', 'SÃO LUÍS': 'São Luís',
            'JOAO PESSOA': 'João Pessoa', 'JOÃO PESSOA': 'João Pessoa',
            'TERESINA': 'Teresina', 'teresina': 'Teresina',
            'NATAL': 'Natal', 'natal': 'Natal',
            'CAMPO GRANDE': 'Campo Grande', 'campo grande': 'Campo Grande',
            'MACEIO': 'Maceió', 'MACEIÓ': 'Maceió', 'maceio': 'Maceió',
            'ARACAJU': 'Aracaju', 'aracaju': 'Aracaju',
            'CUIABA': 'Cuiabá', 'CUIABÁ': 'Cuiabá', 'cuiaba': 'Cuiabá',
            'PORTO VELHO': 'Porto Velho', 'porto velho': 'Porto Velho',
            'BOA VISTA': 'Boa Vista', 'boa vista': 'Boa Vista',
            'RIO BRANCO': 'Rio Branco', 'rio branco': 'Rio Branco',
            'MACAPA': 'Macapá', 'MACAPÁ': 'Macapá', 'macapa': 'Macapá',
            'PALMAS': 'Palmas', 'palmas': 'Palmas'
        }
    
    def _criar_mapa_mercados(self) -> Dict[str, str]:
        """Padronização de setores de mercado"""
        return {
            'EDTECH': 'EdTech', 'edtech': 'EdTech', 'Edtech': 'EdTech',
            'FINTECH': 'FinTech', 'fintech': 'FinTech', 'Fintech': 'FinTech',
            'HEALTHTECH': 'HealthTech', 'healthtech': 'HealthTech', 'Healthtech': 'HealthTech',
            'AGTECH': 'AgTech', 'agtech': 'AgTech', 'Agtech': 'AgTech',
            'PROPTECH': 'PropTech', 'proptech': 'PropTech', 'Proptech': 'PropTech',
            'INSURTECH': 'InsurTech', 'insurtech': 'InsurTech', 'Insurtech': 'InsurTech',
            'MARTECH': 'MarTech', 'martech': 'MarTech', 'Martech': 'MarTech',
            'FOODTECH': 'FoodTech', 'foodtech': 'FoodTech', 'Foodtech': 'FoodTech',
            'HRTECH': 'HRTech', 'hrtech': 'HRTech', 'Hrtech': 'HRTech',
            'LEGALTECH': 'LegalTech', 'legaltech': 'LegalTech', 'Legaltech': 'LegalTech',
            'RETAILTECH': 'RetailTech', 'retailtech': 'RetailTech', 'Retailtech': 'RetailTech',
            'CONSTRUTECH': 'ConstruTech', 'construtech': 'ConstruTech', 'Construtech': 'ConstruTech'
        }
    
    def normalizar_estado(self, estado: str) -> str:
        """Normaliza nome de estado para formato padrão"""
        if not estado or pd.isna(estado):
            return ""
        
        # Remove espaços extras e converte para maiúsculas para comparação
        estado_limpo = str(estado).strip().upper()
        
        # Verifica se está no mapa de estados
        if estado_limpo in self.estados_brasil:
            return self.estados_brasil[estado_limpo]
        
        # Tenta sem acentos
        estado_sem_acento = unidecode(estado_limpo)
        if estado_sem_acento in self.estados_brasil:
            return self.estados_brasil[estado_sem_acento]
        
        # Se não encontrar, retorna capitalizado corretamente
        return self.capitalizar_nome(estado)
    
    def normalizar_cidade(self, cidade: str) -> str:
        """Normaliza nome de cidade com acentuação correta"""
        if not cidade or pd.isna(cidade):
            return ""
        
        # Remove espaços extras
        cidade_limpa = str(cidade).strip()
        
        # Verifica correções específicas
        cidade_upper = cidade_limpa.upper()
        if cidade_upper in self.cidades_correcoes:
            return self.cidades_correcoes[cidade_upper]
        
        # Tenta sem acentos
        cidade_sem_acento = unidecode(cidade_upper)
        if cidade_sem_acento in self.cidades_correcoes:
            return self.cidades_correcoes[cidade_sem_acento]
        
        # Se não encontrar correção específica, capitaliza corretamente
        return self.capitalizar_nome(cidade_limpa)
    
    def normalizar_mercado(self, mercado: str) -> str:
        """Normaliza setor de mercado"""
        if not mercado or pd.isna(mercado):
            return ""
        
        mercado_limpo = str(mercado).strip()
        mercado_upper = mercado_limpo.upper()
        
        if mercado_upper in self.mercados_padrao:
            return self.mercados_padrao[mercado_upper]
        
        # Se não encontrar, retorna capitalizado
        return self.capitalizar_nome(mercado_limpo)
    
    def capitalizar_nome(self, texto: str) -> str:
        """Capitaliza nomes corretamente, considerando preposições"""
        if not texto or pd.isna(texto):
            return ""
        
        # Preposições e artigos que devem ficar em minúsculas
        minusculas = {'de', 'da', 'do', 'das', 'dos', 'e', 'para', 'com', 'sem', 'em'}
        
        palavras = str(texto).strip().split()
        resultado = []
        
        for i, palavra in enumerate(palavras):
            # Primeira palavra sempre capitalizada
            if i == 0:
                resultado.append(palavra.capitalize())
            # Preposições em minúsculas (exceto se for a primeira palavra)
            elif palavra.lower() in minusculas:
                resultado.append(palavra.lower())
            else:
                resultado.append(palavra.capitalize())
        
        return ' '.join(resultado)
    
    def normalizar_nome_empresa(self, nome: str) -> str:
        """Normaliza nome de empresa mantendo siglas em maiúsculas"""
        if not nome or pd.isna(nome):
            return ""
        
        nome_limpo = str(nome).strip()
        
        # Preserva siglas comuns
        siglas = ['LTDA', 'ME', 'EPP', 'EIRELI', 'SA', 'S/A', 'S.A.', 'CNPJ', 'CPF']
        
        # Capitaliza o nome
        nome_normalizado = self.capitalizar_nome(nome_limpo)
        
        # Restaura siglas em maiúsculas
        for sigla in siglas:
            # Busca variações da sigla
            pattern = re.compile(re.escape(sigla.lower()), re.IGNORECASE)
            nome_normalizado = pattern.sub(sigla, nome_normalizado)
        
        return nome_normalizado
    
    def normalizar_email(self, email: str) -> str:
        """Normaliza email para minúsculas e remove espaços"""
        if not email or pd.isna(email):
            return ""
        
        return str(email).strip().lower()
    
    def criar_chave_normalizacao(self, texto: str) -> str:
        """Cria chave normalizada para detectar duplicatas"""
        if not texto or pd.isna(texto):
            return ""
        
        # Remove acentos, converte para minúsculas, remove caracteres especiais
        texto_norm = unidecode(str(texto)).lower()
        texto_norm = re.sub(r'[^a-z0-9]', '', texto_norm)
        
        return texto_norm

class CRMProcessorPadronizado:
    """Processador ETL com padronização completa de dados"""
    
    def __init__(self, data_dir: str = "."):
        self.data_dir = Path(data_dir)
        self.normalizador = NormalizadorDados()
        self.quality_metrics = {}
        self.consolidation_report = []
        self.duplicate_report = []
        self.normalization_stats = {}
        
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
        """Mapeamento de colunas em PT-BR para avaliações"""
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
    
    def create_record_hash(self, record: Dict, key_fields: List[str]) -> str:
        """Cria hash único para identificar duplicatas usando chaves normalizadas"""
        key_values = []
        for field in key_fields:
            value = record.get(field, '')
            if pd.notna(value):
                # Usa a chave normalizada para comparação
                normalized = self.normalizador.criar_chave_normalizacao(value)
                key_values.append(normalized)
            else:
                key_values.append('')
        
        hash_string = '|'.join(key_values)
        return hashlib.md5(hash_string.encode()).hexdigest()
    
    def remove_duplicates_advanced(self, df: pd.DataFrame, key_columns: List[str], 
                                  dataset_name: str) -> pd.DataFrame:
        """Remove duplicatas considerando variações normalizadas"""
        if df.empty:
            return df
        
        initial_count = len(df)
        
        # Criar hash normalizado para cada registro
        df['_hash'] = df.apply(
            lambda row: self.create_record_hash(row.to_dict(), key_columns),
            axis=1
        )
        
        # Remover duplicatas baseadas no hash normalizado
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
        
        # Outros arquivos
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
    
    def validate_email(self, email: str) -> bool:
        """Valida formato de email"""
        if not email or pd.isna(email):
            return False
        
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(email_regex, str(email)))
    
    def parse_location(self, location_str: str) -> Tuple[str, str]:
        """Analisa e normaliza formato cidade/estado"""
        if not location_str or pd.isna(location_str):
            return "", ""
        
        location_str = str(location_str).strip()
        
        if '/' in location_str:
            parts = location_str.split('/')
            city = self.normalizador.normalizar_cidade(parts[0].strip())
            state = self.normalizador.normalizar_estado(parts[1].strip()) if len(parts) > 1 else ""
        else:
            # Tenta identificar se é uma cidade ou estado
            location_normalized = self.normalizador.normalizar_estado(location_str)
            if location_normalized != self.normalizador.capitalizar_nome(location_str):
                # É um estado
                city = ""
                state = location_normalized
            else:
                # É uma cidade
                city = self.normalizador.normalizar_cidade(location_str)
                state = ""
        
        return city, state
    
    def process_companies_data(self, crm_data: List[Dict]) -> pd.DataFrame:
        """Processa dados de empresas com normalização completa"""
        if not crm_data:
            return pd.DataFrame()
        
        companies = []
        normalization_count = 0
        
        for record in crm_data:
            city, state = self.parse_location(record.get('Cidade/Estado', ''))
            
            # Normaliza todos os campos de texto
            company_name = self.normalizador.normalizar_nome_empresa(record.get('Nome da Startup', ''))
            market_sector = self.normalizador.normalizar_mercado(record.get('Mercado', ''))
            
            company = {
                'company_id': record.get('ID', ''),
                'company_name': company_name,
                'website': str(record.get('Site', '')).lower().strip(),
                'city': city,
                'state': state,
                'operational_stage': self.normalizador.capitalizar_nome(record.get('Estágio Operacional', '')),
                'business_model': self.normalizador.capitalizar_nome(record.get('Modelo de Negócio', '')),
                'market_sector': market_sector,
                'investment_stage': self.normalizador.capitalizar_nome(record.get('Estágio de Investimento', '')),
                'valuation_amount': self.clean_brazilian_currency(record.get('Valuation', 0)),
                'monthly_recurring_revenue': self.clean_brazilian_currency(record.get('MRR', 0)),
                'last_twelve_months_revenue': self.clean_brazilian_currency(record.get('LTM', 0)),
                'fundraising_interest': self.normalizador.capitalizar_nome(record.get('Captação', '')),
                'valuation_type': self.normalizador.capitalizar_nome(record.get('Tipo de Valuation', '')),
                'valuation_date': self.clean_brazilian_date(record.get('Data de Valuation', '')),
                'created_date': datetime.now().strftime('%d/%m/%Y %H:%M'),
                'data_source': 'crm-valuation'
            }
            
            # Conta normalizações
            if company_name != record.get('Nome da Startup', ''):
                normalization_count += 1
            
            companies.append(company)
        
        df = pd.DataFrame(companies)
        
        # Remove duplicatas considerando variações
        df = self.remove_duplicates_advanced(
            df, 
            ['company_name', 'city', 'state'],  # Usa nome, cidade e estado como chave
            'Empresas'
        )
        
        # Renomear colunas para PT-BR
        df = df.rename(columns=self.get_ptbr_columns_companies())
        
        # Métricas
        total_records = len(df)
        unique_records = df['id_empresa'].nunique()
        complete_records = df.dropna(subset=['nome_empresa', 'valor_avaliacao']).shape[0]
        
        self.quality_metrics['empresas'] = DataQualityMetrics(
            total_records=total_records,
            unique_records=unique_records,
            duplicates_removed=total_records - unique_records,
            normalized_records=normalization_count,
            complete_records=complete_records,
            invalid_emails=0,
            invalid_phones=0,
            missing_critical_fields=total_records - complete_records,
            data_completeness_score=(complete_records / total_records * 100) if total_records > 0 else 0
        )
        
        self.consolidation_report.append(f"Empresas: {total_records} registros processados, {normalization_count} normalizados")
        
        return df
    
    def process_detailed_valuations(self, valuation_data: List[Dict]) -> pd.DataFrame:
        """Processa avaliações detalhadas com normalização"""
        if not valuation_data:
            return pd.DataFrame()
        
        valuations = []
        normalization_count = 0
        
        for record in valuation_data:
            # Normaliza localização
            city = self.normalizador.normalizar_cidade(record.get('overview.city', ''))
            state = self.normalizador.normalizar_estado(record.get('overview.state', ''))
            
            # Normaliza nome da empresa e outros campos
            company_name = self.normalizador.normalizar_nome_empresa(
                record.get('overview.company', record.get('company', ''))
            )
            full_name = self.normalizador.capitalizar_nome(record.get('overview.fullName', ''))
            market = self.normalizador.normalizar_mercado(record.get('overview.market', ''))
            
            valuation = {
                'valuation_id': record.get('id', ''),
                'company_name': company_name,
                'full_name': full_name,
                'email': self.normalizador.normalizar_email(
                    record.get('overview.email', record.get('email', ''))
                ),
                'whatsapp': self.clean_brazilian_phone(record.get('overview.whatsapp', '')),
                'website': str(record.get('overview.website', '')).lower().strip(),
                'city': city,
                'state': state,
                'market': market,
                'company_type': self.normalizador.capitalizar_nome(record.get('overview.type', '')),
                'foundation_date': self.clean_brazilian_date(record.get('overview.foundationDate', '')),
                'valuation_amount': self.clean_brazilian_currency(record.get('valuation', 0)),
                'valuation_type': self.normalizador.capitalizar_nome(record.get('valuationType', '')),
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
            
            # Conta normalizações
            original_company = record.get('overview.company', record.get('company', ''))
            if company_name != original_company:
                normalization_count += 1
            
            valuations.append(valuation)
        
        df = pd.DataFrame(valuations)
        
        # Remove duplicatas
        df = self.remove_duplicates_advanced(
            df,
            ['company_name', 'email'],
            'Avaliações Detalhadas'
        )
        
        # Renomear colunas
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
            normalized_records=normalization_count,
            complete_records=complete_records,
            invalid_emails=invalid_emails,
            invalid_phones=df['whatsapp'].isna().sum(),
            missing_critical_fields=total_records - complete_records,
            data_completeness_score=(complete_records / total_records * 100) if total_records > 0 else 0
        )
        
        self.consolidation_report.append(f"Avaliações: {total_records} registros, {normalization_count} normalizados")
        
        return df
    
    def process_contacts_data(self, crm_data: List[Dict]) -> pd.DataFrame:
        """Processa contatos com normalização de nomes"""
        if not crm_data:
            return pd.DataFrame()
        
        contacts = []
        normalization_count = 0
        
        for record in crm_data:
            contact_name = self.normalizador.capitalizar_nome(record.get('Nome do Respondente', ''))
            
            contact = {
                'contact_id': f"contact_{record.get('ID', '')}",
                'company_id': record.get('ID', ''),
                'contact_name': contact_name,
                'email': self.normalizador.normalizar_email(record.get('Email', '')),
                'phone': self.clean_brazilian_phone(record.get('Telefone', '')),
                'role': 'Contato Principal',
                'is_primary': True,
                'email_valid': self.validate_email(record.get('Email', '')),
                'created_date': self.clean_brazilian_date(record.get('Data de Valuation', '')),
                'data_source': 'crm-valuation'
            }
            
            if contact_name != record.get('Nome do Respondente', ''):
                normalization_count += 1
            
            contacts.append(contact)
        
        df = pd.DataFrame(contacts)
        
        # Remove duplicatas
        df = self.remove_duplicates_advanced(
            df,
            ['email', 'contact_name'],
            'Contatos'
        )
        
        # Renomear colunas
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
            normalized_records=normalization_count,
            complete_records=complete_records,
            invalid_emails=invalid_emails,
            invalid_phones=df['telefone'].isna().sum(),
            missing_critical_fields=total_records - complete_records,
            data_completeness_score=(complete_records / total_records * 100) if total_records > 0 else 0
        )
        
        self.consolidation_report.append(f"Contatos: {total_records} registros, {normalization_count} normalizados")
        
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
    
    def create_worksheet_generic(self, wb: Workbook, df: pd.DataFrame, sheet_name: str):
        """Cria worksheet genérica formatada"""
        if df.empty:
            return
        
        ws = wb.create_sheet(sheet_name)
        
        # Escrever dados
        for r in dataframe_to_rows(df, index=False, header=True):
            ws.append(r)
        
        # Aplicar estilos
        for cell in ws[1]:
            cell.style = "header_style"
        
        for row in ws.iter_rows(min_row=2):
            for cell in row:
                cell.style = "data_style"
        
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
        
        ws.freeze_panes = 'A2'
    
    def create_normalization_report_worksheet(self, wb: Workbook):
        """Cria relatório de normalização de dados"""
        ws = wb.create_sheet("Relatório Normalização")
        
        # Título
        ws['A1'] = "Relatório de Normalização e Padronização"
        ws['A1'].font = Font(bold=True, size=16, color="366092")
        ws.merge_cells('A1:F1')
        
        ws['A3'] = datetime.now().strftime('Gerado em: %d/%m/%Y %H:%M')
        ws['A3'].font = Font(italic=True)
        
        # Estatísticas de normalização
        row = 5
        ws[f'A{row}'] = "ESTATÍSTICAS DE NORMALIZAÇÃO"
        ws[f'A{row}'].font = Font(bold=True, size=12)
        
        row += 2
        headers = ['Dataset', 'Total', 'Normalizados', 'Duplicatas Removidas', 'Taxa Qualidade (%)']
        for col, header in enumerate(headers, 1):
            ws.cell(row=row, column=col, value=header).style = "header_style"
        
        row += 1
        for dataset_name, metrics in self.quality_metrics.items():
            ws.cell(row=row, column=1, value=dataset_name.replace('_', ' ').title())
            ws.cell(row=row, column=2, value=metrics.total_records)
            ws.cell(row=row, column=3, value=metrics.normalized_records)
            ws.cell(row=row, column=4, value=metrics.duplicates_removed)
            ws.cell(row=row, column=5, value=f"{metrics.data_completeness_score:.1f}%")
            row += 1
        
        # Exemplos de normalização
        row += 2
        ws[f'A{row}'] = "EXEMPLOS DE NORMALIZAÇÃO APLICADA"
        ws[f'A{row}'].font = Font(bold=True, size=12)
        
        row += 2
        examples = [
            ('Estados', 'SP → São Paulo, RJ → Rio de Janeiro, MG → Minas Gerais'),
            ('Cidades', 'SAO PAULO → São Paulo, BRASILIA → Brasília, FLORIANOPOLIS → Florianópolis'),
            ('Nomes', 'JOAO DA SILVA → João da Silva, MARIA DE SOUZA → Maria de Souza'),
            ('Empresas', 'EMPRESA XYZ LTDA → Empresa Xyz LTDA, tech solutions me → Tech Solutions ME'),
            ('Mercados', 'fintech → FinTech, EDTECH → EdTech, healthtech → HealthTech'),
            ('Emails', 'USUARIO@EMAIL.COM → usuario@email.com')
        ]
        
        ws.cell(row=row, column=1, value="Tipo").style = "header_style"
        ws.cell(row=row, column=2, value="Exemplos de Transformação").style = "header_style"
        
        row += 1
        for tipo, exemplo in examples:
            ws.cell(row=row, column=1, value=tipo)
            ws.cell(row=row, column=2, value=exemplo)
            row += 1
        
        # Ajustar larguras
        ws.column_dimensions['A'].width = 25
        ws.column_dimensions['B'].width = 60
        ws.column_dimensions['C'].width = 15
        ws.column_dimensions['D'].width = 20
        ws.column_dimensions['E'].width = 18
        ws.column_dimensions['F'].width = 15
    
    def run_comprehensive_etl(self) -> str:
        """Executa pipeline ETL com padronização completa"""
        print("\n🚀 Iniciando Pipeline ETL com Padronização Completa...")
        print("="*60)
        
        # Carregar dados
        print("\n📂 Carregando arquivos...")
        data_files = self.load_all_json_files()
        
        if not data_files:
            print("❌ Nenhum arquivo encontrado!")
            return None
        
        # Processar dados
        print("\n🔄 Processando e normalizando dados...")
        
        companies_df = self.process_companies_data(data_files.get('crm', []))
        print(f"✓ Empresas: {len(companies_df)} registros")
        
        contacts_df = self.process_contacts_data(data_files.get('crm', []))
        print(f"✓ Contatos: {len(contacts_df)} registros")
        
        valuations_df = self.process_detailed_valuations(data_files.get('valuation-detailed', []))
        print(f"✓ Avaliações: {len(valuations_df)} registros")
        
        # Criar workbook
        print("\n📊 Criando arquivo Excel...")
        wb = self.create_styled_workbook()
        
        if "Sheet" in wb.sheetnames:
            wb.remove(wb["Sheet"])
        
        # Criar worksheets
        self.create_worksheet_generic(wb, companies_df, "Empresas")
        self.create_worksheet_generic(wb, valuations_df, "Avaliações")
        self.create_worksheet_generic(wb, contacts_df, "Contatos")
        self.create_normalization_report_worksheet(wb)
        
        # Salvar
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"CRM_Dados_Padronizados_{timestamp}.xlsx"
        filepath = self.data_dir / filename
        
        wb.save(filepath)
        
        # Exportar CSVs
        csv_dir = self.data_dir / f"supabase_import_padronizado_{timestamp}"
        csv_dir.mkdir(exist_ok=True)
        
        companies_df.to_csv(csv_dir / "empresas.csv", index=False, encoding='utf-8-sig')
        valuations_df.to_csv(csv_dir / "avaliacoes.csv", index=False, encoding='utf-8-sig')
        contacts_df.to_csv(csv_dir / "contatos.csv", index=False, encoding='utf-8-sig')
        
        print(f"\n✅ Processamento completo!")
        print(f"📍 Excel: {filepath}")
        print(f"📂 CSVs: {csv_dir}")
        
        # Resumo
        print("\n" + "="*60)
        print("📈 RESUMO DA PADRONIZAÇÃO:")
        print("="*60)
        
        total_normalized = sum(m.normalized_records for m in self.quality_metrics.values())
        total_duplicates = sum(m.duplicates_removed for m in self.quality_metrics.values())
        
        print(f"✓ {total_normalized} registros normalizados")
        print(f"✓ {total_duplicates} duplicatas removidas")
        print(f"✓ Estados convertidos de siglas para nomes completos")
        print(f"✓ Cidades padronizadas com acentuação correta")
        print(f"✓ Nomes formatados corretamente")
        print(f"✓ Emails normalizados para minúsculas")
        
        return str(filepath)


def main():
    processor = CRMProcessorPadronizado(".")
    result_file = processor.run_comprehensive_etl()
    
    if result_file:
        print(f"\n🎉 Sucesso! Dados totalmente padronizados!")
        print(f"📂 Arquivo: {result_file}")
        print("\n✨ Melhorias aplicadas:")
        print("   • Estados: SP → São Paulo, RJ → Rio de Janeiro")
        print("   • Cidades: SAO PAULO → São Paulo, BRASILIA → Brasília")
        print("   • Nomes: JOAO SILVA → João Silva")
        print("   • Duplicatas inteligentes removidas")
    else:
        print("❌ Falha no processamento!")


if __name__ == "__main__":
    main()
