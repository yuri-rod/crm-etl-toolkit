#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Enhanced ETL Processor with Brazilian Real Formatting and Date/Time Splitting
==============================================================================
This script processes CRM data with the following enhancements:
- Formats monetary values as Brazilian Real (R$ X.XXX.XXX,XX)
- Splits datetime columns into separate date (dd/mm/yyyy) and time (HH:MM:SS) columns
- Removes duplicate records keeping only the most recent entry
- Maintains comprehensive ETL logging

Author: AI Assistant
Date: September 4, 2025
"""

import json
import pandas as pd
import numpy as np
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import warnings
from dataclasses import dataclass, field
import unicodedata
from unidecode import unidecode
import locale

# Excel formatting
from openpyxl import load_workbook, Workbook
from openpyxl.styles import Font, PatternFill, Border, Side, Alignment, NamedStyle
from openpyxl.formatting.rule import ColorScaleRule
from openpyxl.utils.dataframe import dataframe_to_rows

warnings.filterwarnings('ignore')

@dataclass
class ETLTransformationLog:
    """Tracks all ETL transformations applied"""
    monetary_columns_formatted: List[str] = field(default_factory=list)
    datetime_columns_split: List[str] = field(default_factory=list)
    duplicates_removed: int = 0
    original_row_count: Dict[str, int] = field(default_factory=dict)
    final_row_count: Dict[str, int] = field(default_factory=dict)
    processing_timestamp: str = ""
    transformations_applied: List[str] = field(default_factory=list)

class EnhancedDataNormalizer:
    """Enhanced normalizer with monetary formatting and date/time splitting"""
    
    def __init__(self):
        self.estados_map = self._create_states_map()
        self.cities_corrections = self._create_cities_corrections()
        self.markets_map = self._create_markets_map()
        self.etl_log = ETLTransformationLog()
        
    def _create_states_map(self) -> Dict[str, str]:
        """Creates mapping from abbreviations to full state names"""
        return {
            'AC': 'Acre', 'AL': 'Alagoas', 'AP': 'Amapá', 'AM': 'Amazonas',
            'BA': 'Bahia', 'CE': 'Ceará', 'DF': 'Distrito Federal',
            'ES': 'Espírito Santo', 'GO': 'Goiás', 'MA': 'Maranhão',
            'MT': 'Mato Grosso', 'MS': 'Mato Grosso do Sul',
            'MG': 'Minas Gerais', 'PA': 'Pará', 'PB': 'Paraíba',
            'PR': 'Paraná', 'PE': 'Pernambuco', 'PI': 'Piauí',
            'RJ': 'Rio de Janeiro', 'RN': 'Rio Grande do Norte',
            'RS': 'Rio Grande do Sul', 'RO': 'Rondônia', 'RR': 'Roraima',
            'SC': 'Santa Catarina', 'SP': 'São Paulo', 'SE': 'Sergipe',
            'TO': 'Tocantins'
        }
    
    def _create_cities_corrections(self) -> Dict[str, str]:
        """Creates corrections for common city names"""
        return {
            'SAO PAULO': 'São Paulo',
            'RIO DE JANEIRO': 'Rio de Janeiro',
            'BELO HORIZONTE': 'Belo Horizonte',
            'BRASILIA': 'Brasília',
            'PORTO ALEGRE': 'Porto Alegre',
            'CURITIBA': 'Curitiba',
            'FLORIANOPOLIS': 'Florianópolis',
            'SAO JOSE DOS CAMPOS': 'São José dos Campos',
            'RIBEIRAO PRETO': 'Ribeirão Preto',
            'VITORIA': 'Vitória',
            'GOIANIA': 'Goiânia',
            'BELEM': 'Belém',
            'SAO LUIS': 'São Luís',
            'JOAO PESSOA': 'João Pessoa',
            'CUIABA': 'Cuiabá',
            'MACAPA': 'Macapá',
            'SAO BERNARDO DO CAMPO': 'São Bernardo do Campo',
            'SANTO ANDRE': 'Santo André',
            'SAO CAETANO DO SUL': 'São Caetano do Sul',
            'MACEIO': 'Maceió'
        }
    
    def _create_markets_map(self) -> Dict[str, str]:
        """Creates standardization for market sectors"""
        return {
            'EDTECH': 'EdTech', 'FINTECH': 'FinTech',
            'HEALTHTECH': 'HealthTech', 'AGTECH': 'AgTech',
            'PROPTECH': 'PropTech', 'INSURTECH': 'InsurTech',
            'MARTECH': 'MarTech', 'FOODTECH': 'FoodTech',
            'HRTECH': 'HRTech', 'LEGALTECH': 'LegalTech',
            'RETAILTECH': 'RetailTech', 'CONSTRUTECH': 'ConstruTech'
        }
    
    def format_brazilian_currency(self, value: Any) -> str:
        """
        Formats numeric value as Brazilian Real (R$ X.XXX.XXX,XX)
        """
        if pd.isna(value) or value == "" or value is None:
            return ""
        
        try:
            # Convert to float first
            num_value = float(value)
            
            # Format with Brazilian locale
            # Split into integer and decimal parts
            integer_part = int(num_value)
            decimal_part = int((num_value - integer_part) * 100)
            
            # Format integer part with thousand separators
            integer_str = f"{integer_part:,}".replace(",", ".")
            
            # Combine with decimal part
            formatted = f"R$ {integer_str},{decimal_part:02d}"
            
            return formatted
        except:
            return str(value)
    
    def split_datetime(self, datetime_str: str) -> Tuple[str, str]:
        """
        Splits datetime string into date (dd/mm/yyyy) and time (HH:MM:SS)
        Returns tuple of (date, time)
        """
        if not datetime_str or pd.isna(datetime_str):
            return "", ""
        
        datetime_str = str(datetime_str).strip()
        
        # Check if already in the correct format
        if ", " in datetime_str:
            parts = datetime_str.split(", ")
            if len(parts) == 2:
                return parts[0], parts[1]
        
        # Try to parse different datetime formats
        formats = [
            '%d/%m/%Y, %H:%M:%S',
            '%Y-%m-%d %H:%M:%S',
            '%m/%d/%Y, %I:%M:%S %p',
            '%d/%m/%Y %H:%M:%S'
        ]
        
        for fmt in formats:
            try:
                dt = datetime.strptime(datetime_str, fmt)
                date_str = dt.strftime('%d/%m/%Y')
                time_str = dt.strftime('%H:%M:%S')
                return date_str, time_str
            except:
                continue
        
        # If no format matches, return original
        return datetime_str, ""
    
    def normalize_date(self, date_str: str) -> str:
        """Normalizes date to dd/mm/yyyy, HH:MM:SS format (24-hour)"""
        if not date_str or pd.isna(date_str):
            return ""
        
        if re.match(r'\d{2}/\d{2}/\d{4}, \d{2}:\d{2}:\d{2}', str(date_str)):
            return str(date_str)
        
        try:
            for fmt in ['%Y-%m-%d %H:%M:%S', '%d/%m/%Y %H:%M:%S', '%m/%d/%Y, %I:%M:%S %p']:
                try:
                    dt = datetime.strptime(str(date_str), fmt)
                    return dt.strftime('%d/%m/%Y, %H:%M:%S')
                except:
                    continue
        except:
            pass
        
        return str(date_str)
    
    def capitalize_name(self, text: str) -> str:
        """Properly capitalizes names, considering Portuguese prepositions"""
        if not text or pd.isna(text):
            return ""
        
        prepositions = {'de', 'da', 'do', 'das', 'dos', 'e'}
        words = str(text).strip().split()
        capitalized = []
        
        for i, word in enumerate(words):
            word_lower = word.lower()
            if i == 0 or word_lower not in prepositions:
                capitalized.append(word.capitalize())
            else:
                capitalized.append(word_lower)
        
        return ' '.join(capitalized)
    
    def normalize_state(self, state: str) -> str:
        """Normalizes state to full name"""
        if not state or pd.isna(state):
            return ""
        
        state_clean = str(state).strip().upper()
        
        if state_clean in self.estados_map:
            return self.estados_map[state_clean]
        
        state_no_accent = unidecode(state_clean)
        if state_no_accent in self.estados_map:
            return self.estados_map[state_no_accent]
        
        return self.capitalize_name(state)
    
    def normalize_city(self, city: str) -> str:
        """Normalizes city name with proper accentuation"""
        if not city or pd.isna(city):
            return ""
        
        city_upper = str(city).strip().upper()
        city_no_accent = unidecode(city_upper)
        
        if city_upper in self.cities_corrections:
            return self.cities_corrections[city_upper]
        if city_no_accent in self.cities_corrections:
            return self.cities_corrections[city_no_accent]
        
        return self.capitalize_name(city)
    
    def normalize_market(self, market: str) -> str:
        """Normalizes market sector"""
        if not market or pd.isna(market):
            return ""
        
        market_upper = str(market).strip().upper()
        
        if market_upper in self.markets_map:
            return self.markets_map[market_upper]
        
        market_clean = re.sub(r'[^A-Z]', '', market_upper)
        if market_clean in self.markets_map:
            return self.markets_map[market_clean]
        
        return self.capitalize_name(market)
    
    def split_city_state(self, location: str) -> Tuple[str, str]:
        """Splits city/state field into separate city and state"""
        if not location or pd.isna(location):
            return "", ""
        
        patterns = [
            r'(.+?)[/\-]([A-Z]{2})$',
            r'(.+?)\s*,\s*([A-Z]{2})$',
            r'(.+?)\s+([A-Z]{2})$',
        ]
        
        location_str = str(location).strip()
        
        for pattern in patterns:
            match = re.match(pattern, location_str)
            if match:
                city = match.group(1).strip()
                state = match.group(2).strip()
                return self.normalize_city(city), self.normalize_state(state)
        
        return self.normalize_city(location_str), ""

class EnhancedDataConsolidator:
    """Enhanced data consolidator with all requested transformations"""
    
    def __init__(self, export_path: str = r"exports"):
        self.export_path = Path(export_path)
        self.normalizer = EnhancedDataNormalizer()
        self.timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
    def load_all_json_data(self) -> Dict[str, pd.DataFrame]:
        """Loads all JSON data files"""
        print("\n📂 Loading JSON data files...")
        
        datasets = {}
        json_files = list(self.export_path.glob("*.json"))
        
        for json_file in json_files:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                if data:
                    df = pd.DataFrame(data)
                    # Simplify the key extraction
                    key = json_file.stem.replace('crm_export_', '').replace('2024_', '')
                    # Special handling for crm-valuation files (most recent)
                    if 'crm-valuation' in json_file.stem and '2314' in json_file.stem:
                        key = 'crm_valuation'  # Use this as the main CRM valuation source
                    datasets[key] = df
                    print(f"  ✅ Loaded {key}: {len(df)} records")
            except Exception as e:
                print(f"  ❌ Error loading {json_file.name}: {str(e)}")
        
        return datasets
    
    def apply_monetary_formatting(self, df: pd.DataFrame, columns: List[str]) -> pd.DataFrame:
        """Apply Brazilian Real formatting to monetary columns"""
        for col in columns:
            if col in df.columns:
                # Keep original numeric values for calculations
                df[f'{col}_numeric'] = df[col].apply(lambda x: float(x) if pd.notna(x) and x != "" else 0)
                # Add formatted version
                df[col] = df[f'{col}_numeric'].apply(self.normalizer.format_brazilian_currency)
                self.normalizer.etl_log.monetary_columns_formatted.append(col)
                self.normalizer.etl_log.transformations_applied.append(f"Formatted {col} as Brazilian Real")
        return df
    
    def split_datetime_columns(self, df: pd.DataFrame, datetime_columns: List[str]) -> pd.DataFrame:
        """Split datetime columns into separate date and time columns"""
        for col in datetime_columns:
            if col in df.columns:
                # Create new columns for date and time
                date_col = col.replace('_Valuation', '').replace('Data', 'Data')
                time_col = col.replace('Data de', 'Horário de').replace('Data_', 'Horário_')
                
                # Split the datetime
                split_values = df[col].apply(self.normalizer.split_datetime)
                df[col] = split_values.apply(lambda x: x[0])  # Date only
                df[time_col] = split_values.apply(lambda x: x[1])  # Time only
                
                # Track in log
                self.normalizer.etl_log.datetime_columns_split.append(col)
                self.normalizer.etl_log.transformations_applied.append(f"Split {col} into date and time")
                
                # Reorder columns to put time column right after date column
                cols = list(df.columns)
                date_idx = cols.index(col)
                cols.remove(time_col)
                cols.insert(date_idx + 1, time_col)
                df = df[cols]
        
        return df
    
    def remove_duplicates_keep_latest(self, df: pd.DataFrame, date_column: str) -> pd.DataFrame:
        """Remove duplicates keeping only the most recent entry"""
        if df.empty or date_column not in df.columns:
            return df
        
        original_count = len(df)
        
        # Convert date column to datetime for comparison
        df['_temp_datetime'] = pd.to_datetime(df[date_column], format='%d/%m/%Y', errors='coerce')
        
        # Identify columns to check for duplicates (all except date columns)
        duplicate_check_cols = [col for col in df.columns 
                               if col not in ['_temp_datetime', date_column] 
                               and 'horário' not in col.lower()
                               and 'data' not in col.lower()]
        
        # Sort by datetime descending (most recent first)
        df = df.sort_values('_temp_datetime', ascending=False)
        
        # Remove duplicates keeping first (most recent)
        if duplicate_check_cols:
            df = df.drop_duplicates(subset=duplicate_check_cols, keep='first')
        
        # Remove temporary column
        df = df.drop('_temp_datetime', axis=1)
        
        removed_count = original_count - len(df)
        self.normalizer.etl_log.duplicates_removed += removed_count
        
        if removed_count > 0:
            self.normalizer.etl_log.transformations_applied.append(
                f"Removed {removed_count} duplicate records, keeping most recent"
            )
        
        return df
    
    def process_companies_data(self, datasets: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """Processes company data with all transformations"""
        print("\n📊 Processing Companies (Empresas) data with enhancements...")
        
        if 'crm_valuation' not in datasets:
            return pd.DataFrame()
        
        df = datasets['crm_valuation'].copy()
        
        # Store original count
        self.normalizer.etl_log.original_row_count['Empresas'] = len(df)
        
        # Rename columns to standardized names
        column_mapping = {
            'ID': 'ID_Empresa',
            'Nome da Startup': 'Nome_Empresa',
            'Estágio Operacional': 'Estagio_Operacional',
            'Site': 'Website',
            'Nome do Respondente': 'Nome do Respondente',
            'Email': 'Email',
            'Telefone': 'Telefone',
            'Valuation': 'Resultado_Valuation',  # Fixed: was 'Resultado Valuation'
            'Captação': 'Pretende_Captar',  # Fixed: was 'Captando Agora'
            'Tipo de Valuation': 'Tipo de Valuation',
            'Modelo de Negócio': 'Modelo_Negocio',
            'Mercado': 'Mercado',
            'Estágio de Investimento': 'Estagio_Investimento',  # Fixed
            'MRR': 'MRR',
            'LTM': 'Faturamento_LTM',  # Fixed: was 'Faturamento LTM'
            'Cidade/Estado': 'Cidade_Estado',
            'Data de Valuation': 'Data de Valuation'
        }
        
        # Apply column renaming
        df = df.rename(columns=column_mapping)
        
        # Split City/State
        if 'Cidade_Estado' in df.columns:
            city_state = df['Cidade_Estado'].apply(self.normalizer.split_city_state)
            df['Cidade'] = city_state.apply(lambda x: x[0])
            df['Estado'] = city_state.apply(lambda x: x[1])
            df = df.drop('Cidade_Estado', axis=1)
        
        # Apply normalizations
        if 'Nome_Empresa' in df.columns:
            df['Nome_Empresa'] = df['Nome_Empresa'].apply(self.normalizer.capitalize_name)
        if 'Nome do Respondente' in df.columns:
            df['Nome do Respondente'] = df['Nome do Respondente'].apply(self.normalizer.capitalize_name)
        if 'Mercado' in df.columns:
            df['Mercado'] = df['Mercado'].apply(self.normalizer.normalize_market)
        
        # Split datetime columns
        df = self.split_datetime_columns(df, ['Data de Valuation'])
        
        # Apply monetary formatting
        monetary_columns = ['Resultado_Valuation', 'MRR', 'Faturamento_LTM']
        df = self.apply_monetary_formatting(df, monetary_columns)
        
        # Remove duplicates keeping most recent
        df = self.remove_duplicates_keep_latest(df, 'Data de Valuation')
        
        # Store final count
        self.normalizer.etl_log.final_row_count['Empresas'] = len(df)
        
        # Select final columns in correct order
        final_columns = [
            'Data de Valuation', 'Horário de Valuation',
            'Nome_Empresa', 'Estagio_Operacional', 'Website',
            'Nome do Respondente', 'Email', 'Telefone',
            'Resultado_Valuation', 'Pretende_Captar',
            'Tipo de Valuation', 'Modelo_Negocio', 'Mercado',
            'Estagio_Investimento', 'MRR', 'Faturamento_LTM',
            'Cidade', 'Estado'
        ]
        
        # Keep numeric columns for internal use but don't show them
        for col in final_columns[:]:
            if col not in df.columns:
                final_columns.remove(col)
        
        df = df[final_columns]
        
        print(f"  ✅ Processed {len(df)} company records")
        print(f"  💰 Formatted {len(self.normalizer.etl_log.monetary_columns_formatted)} monetary columns")
        print(f"  📅 Split {len(self.normalizer.etl_log.datetime_columns_split)} datetime columns")
        print(f"  🗑️ Removed {self.normalizer.etl_log.duplicates_removed} duplicates")
        
        return df
    
    def process_valuations_data(self, datasets: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """Processes valuation data with all transformations"""
        print("\n📊 Processing Valuations (Valuation) data with enhancements...")
        
        all_valuations = []
        
        # Store original count
        original_total = 0
        
        # Process CRM valuation data
        if 'crm_valuation' in datasets:
            df = datasets['crm_valuation'].copy()
            original_total += len(df)
            
            valuation_df = pd.DataFrame({
                'Nome_Empresa': df.get('Nome da Startup', ''),
                'Data_Valuation': df.get('Data de Valuation', ''),
                'Resultado_Valuation': df.get('Valuation', 0),  # Fixed: was 'Resultado Valuation'
                'Tipo_Valuation': df.get('Tipo de Valuation', ''),
                'Nome_Respondente': df.get('Nome do Respondente', ''),
                'Email_Respondente': df.get('Email', ''),
                'Telefone_Respondente': df.get('Telefone', ''),
                'ID_Valuation': df.get('ID', '')
            })
            
            # Apply name normalization
            valuation_df['Nome_Empresa'] = valuation_df['Nome_Empresa'].apply(self.normalizer.capitalize_name)
            valuation_df['Nome_Respondente'] = valuation_df['Nome_Respondente'].apply(self.normalizer.capitalize_name)
            
            all_valuations.append(valuation_df)
        
        # Process CRM metrics if available
        if 'crmMetrics' in datasets:
            df_crm = datasets['crmMetrics'].copy()
            original_total += len(df_crm)
            
            if 'metrics' in df_crm.columns:
                for _, row in df_crm.iterrows():
                    if isinstance(row['metrics'], dict):
                        valuation_data = {
                            'Nome_Empresa': self.normalizer.capitalize_name(row.get('companyName', '')),
                            'Data_Valuation': self.normalizer.normalize_date(row.get('timestamp', '')),
                            'Resultado_Valuation': row['metrics'].get('valuation', 0),
                            'Tipo_Valuation': 'CRM Analysis',
                            'Nome_Respondente': '',
                            'Email_Respondente': '',
                            'Telefone_Respondente': '',
                            'ID_Valuation': f"crm_{row.get('id', '')}"
                        }
                        all_valuations.append(pd.DataFrame([valuation_data]))
        
        # Combine all valuation data
        if all_valuations:
            result = pd.concat(all_valuations, ignore_index=True)
            
            self.normalizer.etl_log.original_row_count['Valuation'] = original_total
            
            # Split datetime columns
            result = self.split_datetime_columns(result, ['Data_Valuation'])
            
            # Apply monetary formatting
            result = self.apply_monetary_formatting(result, ['Resultado_Valuation'])
            
            # Remove duplicates based on ID_Valuation
            result = result.drop_duplicates(subset=['ID_Valuation'], keep='first')
            
            # Remove duplicates keeping most recent
            date_col = 'Data_Valuation' if 'Data_Valuation' in result.columns else None
            if date_col:
                dup_count_before = self.normalizer.etl_log.duplicates_removed
                result = self.remove_duplicates_keep_latest(result, date_col)
                dup_count_after = self.normalizer.etl_log.duplicates_removed
            
            # Store final count
            self.normalizer.etl_log.final_row_count['Valuation'] = len(result)
            
            # Reorder columns
            final_columns = [
                'Nome_Empresa', 'Data_Valuation', 'Horário_Valuation',
                'Resultado_Valuation', 'Tipo_Valuation',
                'Nome_Respondente', 'Email_Respondente', 'Telefone_Respondente'
            ]
            
            # Keep only columns that exist
            final_columns = [col for col in final_columns if col in result.columns]
            result = result[final_columns]
            
            print(f"  ✅ Processed {len(result)} valuation records")
            return result
        
        return pd.DataFrame()
    
    def process_contacts_data(self, datasets: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """Processes contact data"""
        print("\n📊 Processing Contacts (Contatos) data...")
        
        if 'crm_valuation' not in datasets:
            return pd.DataFrame()
        
        df = datasets['crm_valuation'].copy()
        
        # Store original count
        self.normalizer.etl_log.original_row_count['Contatos'] = len(df)
        
        # Extract contact information
        contact_cols = {
            'ID': 'ID_Empresa',
            'Nome do Respondente': 'Nome_Contato',
            'Email': 'Email',
            'Telefone': 'Telefone',
            'Nome da Startup': 'Nome_Empresa'
        }
        
        # Select and rename columns
        available_cols = [col for col in contact_cols.keys() if col in df.columns]
        df_contacts = df[available_cols].rename(columns=contact_cols)
        
        # Normalize names
        if 'Nome_Contato' in df_contacts.columns:
            df_contacts['Nome_Contato'] = df_contacts['Nome_Contato'].apply(self.normalizer.capitalize_name)
        if 'Nome_Empresa' in df_contacts.columns:
            df_contacts['Nome_Empresa'] = df_contacts['Nome_Empresa'].apply(self.normalizer.capitalize_name)
        
        # Remove duplicates
        df_contacts = df_contacts.drop_duplicates(subset=['Email'], keep='first')
        
        # Store final count
        self.normalizer.etl_log.final_row_count['Contatos'] = len(df_contacts)
        
        print(f"  ✅ Processed {len(df_contacts)} unique contacts")
        
        return df_contacts
    
    def generate_etl_report(self) -> pd.DataFrame:
        """Generate comprehensive ETL transformation report"""
        log = self.normalizer.etl_log
        log.processing_timestamp = datetime.now().strftime('%d/%m/%Y, %H:%M:%S')
        
        report_data = {
            'Transformation Type': [],
            'Details': [],
            'Count': []
        }
        
        # Monetary formatting
        if log.monetary_columns_formatted:
            report_data['Transformation Type'].append('Monetary Formatting')
            report_data['Details'].append(', '.join(log.monetary_columns_formatted))
            report_data['Count'].append(len(log.monetary_columns_formatted))
        
        # DateTime splitting
        if log.datetime_columns_split:
            report_data['Transformation Type'].append('DateTime Splitting')
            report_data['Details'].append(', '.join(log.datetime_columns_split))
            report_data['Count'].append(len(log.datetime_columns_split))
        
        # Duplicate removal
        if log.duplicates_removed > 0:
            report_data['Transformation Type'].append('Duplicates Removed')
            report_data['Details'].append('Kept most recent entries')
            report_data['Count'].append(log.duplicates_removed)
        
        # Row count changes
        for sheet_name in log.original_row_count.keys():
            original = log.original_row_count.get(sheet_name, 0)
            final = log.final_row_count.get(sheet_name, 0)
            if original != final:
                report_data['Transformation Type'].append(f'{sheet_name} Reduction')
                report_data['Details'].append(f'From {original} to {final} rows')
                report_data['Count'].append(original - final)
        
        return pd.DataFrame(report_data)
    
    def create_comprehensive_excel(self, datasets: Dict[str, pd.DataFrame]):
        """Creates the main comprehensive Excel file with all data"""
        output_file = self.export_path / f"CRM_Dados_Padronizados_COMPLETO_{self.timestamp}.xlsx"
        
        print(f"\n📝 Creating enhanced comprehensive Excel file...")
        
        # Process all data types
        companies_df = self.process_companies_data(datasets)
        valuations_df = self.process_valuations_data(datasets)
        contacts_df = self.process_contacts_data(datasets)
        
        # Create Excel writer
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            
            # 1. Companies sheet
            if not companies_df.empty:
                companies_df.to_excel(writer, sheet_name='Empresas', index=False)
                print(f"  ✅ Added 'Empresas' sheet: {len(companies_df)} records")
            
            # 2. VALUATION sheet
            if not valuations_df.empty:
                valuations_df.to_excel(writer, sheet_name='Valuation', index=False)
                print(f"  ✅ Added 'Valuation' sheet: {len(valuations_df)} records")
            
            # 3. Contacts sheet
            if not contacts_df.empty:
                contacts_df.to_excel(writer, sheet_name='Contatos', index=False)
                print(f"  ✅ Added 'Contatos' sheet: {len(contacts_df)} records")
            
            # 4. Summary Report
            summary_data = {
                'Dataset': ['Empresas', 'Valuation', 'Contatos'],
                'Registros Originais': [
                    self.normalizer.etl_log.original_row_count.get('Empresas', 0),
                    self.normalizer.etl_log.original_row_count.get('Valuation', 0),
                    self.normalizer.etl_log.original_row_count.get('Contatos', 0)
                ],
                'Registros Finais': [
                    len(companies_df),
                    len(valuations_df),
                    len(contacts_df)
                ],
                'Duplicados Removidos': [
                    self.normalizer.etl_log.original_row_count.get('Empresas', 0) - len(companies_df),
                    self.normalizer.etl_log.original_row_count.get('Valuation', 0) - len(valuations_df),
                    self.normalizer.etl_log.original_row_count.get('Contatos', 0) - len(contacts_df)
                ],
                'Status': ['✅ Completo'] * 3
            }
            summary_df = pd.DataFrame(summary_data)
            summary_df.to_excel(writer, sheet_name='Resumo', index=False)
            
            # 5. ETL Transformation Report
            etl_report = self.generate_etl_report()
            etl_report.to_excel(writer, sheet_name='Relatório_ETL', index=False)
            
            # 6. Data quality report
            quality_data = {
                'Métrica': [
                    'Total de Registros Processados',
                    'Empresas Únicas',
                    'Valuations Processadas',
                    'Contatos Únicos',
                    'Colunas Monetárias Formatadas',
                    'Colunas DateTime Divididas',
                    'Total de Duplicados Removidos',
                    'Data de Processamento',
                    'Versão'
                ],
                'Valor': [
                    len(companies_df) + len(valuations_df) + len(contacts_df),
                    len(companies_df),
                    len(valuations_df),
                    len(contacts_df),
                    len(self.normalizer.etl_log.monetary_columns_formatted),
                    len(self.normalizer.etl_log.datetime_columns_split),
                    self.normalizer.etl_log.duplicates_removed,
                    datetime.now().strftime('%d/%m/%Y, %H:%M:%S'),
                    '3.0 - Enhanced with BRL formatting'
                ]
            }
            quality_df = pd.DataFrame(quality_data)
            quality_df.to_excel(writer, sheet_name='Relatório_Qualidade', index=False)
        
        # Apply formatting
        print("\n🎨 Applying Excel formatting...")
        self.format_excel(output_file)
        
        print(f"\n✅ File created successfully: {output_file.name}")
        return output_file
    
    def format_excel(self, file_path: Path):
        """Applies formatting to the Excel file"""
        wb = load_workbook(file_path)
        
        # Header style
        header_font = Font(bold=True, color="FFFFFF", size=11)
        header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
        header_alignment = Alignment(horizontal="center", vertical="center")
        
        # Currency style for monetary columns
        currency_alignment = Alignment(horizontal="right", vertical="center")
        
        # Apply formatting to all sheets
        for sheet_name in wb.sheetnames:
            ws = wb[sheet_name]
            
            # Format headers
            for cell in ws[1]:
                cell.font = header_font
                cell.fill = header_fill
                cell.alignment = header_alignment
            
            # Apply specific formatting to monetary columns
            for col_idx, col in enumerate(ws.iter_cols(min_row=1, max_row=1), 1):
                col_name = col[0].value
                if col_name and ('valuation' in str(col_name).lower() or 
                               'mrr' in str(col_name).lower() or 
                               'faturamento' in str(col_name).lower()):
                    for row in ws.iter_rows(min_row=2, min_col=col_idx, max_col=col_idx):
                        for cell in row:
                            cell.alignment = currency_alignment
            
            # Auto-adjust column widths
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
            
            # Freeze top row
            ws.freeze_panes = 'A2'
        
        wb.save(file_path)
        print("  ✅ Formatting applied successfully")

def main():
    """Main execution function"""
    print("\n" + "=" * 70)
    print("ENHANCED DATA CONSOLIDATION - WITH BRAZILIAN REAL FORMATTING")
    print("=" * 70)
    print(f"Starting at: {datetime.now().strftime('%d/%m/%Y, %H:%M:%S')}")
    print("\n⚡ ENHANCEMENTS APPLIED:")
    print("  • Monetary values formatted as Brazilian Real (R$ X.XXX.XXX,XX)")
    print("  • DateTime columns split into Date and Time")
    print("  • Duplicate removal keeping most recent entries")
    print("  • Comprehensive ETL logging")
    
    try:
        # Initialize consolidator
        consolidator = EnhancedDataConsolidator()
        
        # Load all data
        datasets = consolidator.load_all_json_data()
        
        if not datasets:
            print("\n❌ No data files found!")
            return 1
        
        # Create comprehensive Excel file
        output_file = consolidator.create_comprehensive_excel(datasets)
        
        # Summary
        log = consolidator.normalizer.etl_log
        print("\n" + "=" * 70)
        print("✅ ENHANCED DATA CONSOLIDATION COMPLETED SUCCESSFULLY!")
        print("=" * 70)
        
        print(f"\n📊 TRANSFORMATION STATISTICS:")
        print(f"  • Monetary columns formatted: {len(log.monetary_columns_formatted)}")
        print(f"  • DateTime columns split: {len(log.datetime_columns_split)}")
        print(f"  • Total duplicates removed: {log.duplicates_removed}")
        
        print(f"\n📈 ROW COUNT CHANGES:")
        for sheet in log.original_row_count.keys():
            original = log.original_row_count[sheet]
            final = log.final_row_count[sheet]
            reduction = ((original - final) / original * 100) if original > 0 else 0
            print(f"  • {sheet}: {original:,} → {final:,} ({reduction:.1f}% reduction)")
        
        print(f"\n📁 OUTPUT FILE: {output_file.name}")
        print(f"  • Date format: dd/mm/yyyy (Brazilian standard)")
        print(f"  • Time format: HH:MM:SS (24-hour)")
        print(f"  • Currency: R$ (Brazilian Real)")
        
    except Exception as e:
        print(f"\n❌ Error during consolidation: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
