#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Consolidate All Data into Main Padronizado File
================================================
This script ensures that CRM_Dados_Padronizados contains ALL data from:
- Updated backup files (03/09/2025)
- All other export files
- Maintains "Valuation" terminology (not translated)

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
from dataclasses import dataclass
import unicodedata
from unidecode import unidecode

# Excel formatting
from openpyxl import load_workbook, Workbook
from openpyxl.styles import Font, PatternFill, Border, Side, Alignment, NamedStyle
from openpyxl.formatting.rule import ColorScaleRule
from openpyxl.utils.dataframe import dataframe_to_rows

warnings.filterwarnings('ignore')

class DataNormalizer:
    """Normalizes Brazilian data according to standards"""
    
    def __init__(self):
        self.estados_map = self._create_states_map()
        self.cities_corrections = self._create_cities_corrections()
        self.markets_map = self._create_markets_map()
        
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

class DataConsolidator:
    """Consolidates all data sources into main file"""
    
    def __init__(self, export_path: str = "exports"):
        self.export_path = Path(export_path)
        self.normalizer = DataNormalizer()
        self.timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
    def load_all_json_data(self) -> Dict[str, pd.DataFrame]:
        """Loads all JSON data files from the exports directory"""
        print("\n🔄 Loading all JSON data files...")
        
        datasets = {}
        
        # Primary data sources (updated on 03/09)
        json_files = {
            'crm_valuation': 'crm-valuation-20250903-2314.json',
            'valuation': 'valuation-20250903-2315.json',
            'payments': 'payments-20250903-2315.json',
            'opoderdoequitygpt': 'opoderdoequitygpt-20250903-2315.json',
            'paymentLinks': 'paymentLinks-20250903-2315.json',
            'senseMetrics': 'senseMetrics-20250903-2315.json',
            'crmMetrics': 'crmMetrics-20250903-2315.json'
        }
        
        for name, filename in json_files.items():
            file_path = self.export_path / filename
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                datasets[name] = pd.DataFrame(data)
                print(f"  ✅ Loaded {name}: {len(datasets[name])} records")
            else:
                print(f"  ⚠️ File not found: {filename}")
        
        # Also check for additional analysis files
        additional_files = [
            'avaliacoes_detalhadas_20250903_214328.json',
            'analises_gpt_20250903_214328.json'
        ]
        
        for filename in additional_files:
            file_path = self.export_path / filename
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                name = filename.split('_20250903')[0]
                datasets[name] = pd.DataFrame(data)
                print(f"  ✅ Loaded {name}: {len(datasets[name])} records")
        
        return datasets
    
    def process_companies_data(self, datasets: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """Processes and consolidates company data"""
        print("\n📊 Processing Companies (Empresas) data...")
        
        # Start with CRM valuation as base
        if 'crm_valuation' not in datasets:
            print("  ❌ CRM Valuation data not found!")
            return pd.DataFrame()
        
        df = datasets['crm_valuation'].copy()
        
        # Rename columns to Portuguese (except Valuation)
        column_mapping = {
            'ID': 'ID_Empresa',
            'Nome da Startup': 'Nome_Empresa',
            'Site': 'Website',
            'Cidade/Estado': 'Cidade_Estado',
            'Estágio Operacional': 'Estagio_Operacional',
            'Modelo de Negócio': 'Modelo_Negocio',
            'Mercado': 'Mercado',
            'Estágio de Investimento': 'Estagio_Investimento',
            'Captação': 'Pretende_Captar',
            'MRR': 'MRR',
            'LTM': 'Faturamento_LTM'
        }
        
        # Apply column mapping
        df = df.rename(columns=column_mapping)
        
        # Split city/state
        if 'Cidade_Estado' in df.columns:
            city_state = df['Cidade_Estado'].apply(self.normalizer.split_city_state)
            df['Cidade'] = city_state.apply(lambda x: x[0])
            df['Estado'] = city_state.apply(lambda x: x[1])
            df = df.drop('Cidade_Estado', axis=1)
        
        # Normalize fields
        if 'Nome_Empresa' in df.columns:
            df['Nome_Empresa'] = df['Nome_Empresa'].apply(self.normalizer.capitalize_name)
        
        if 'Mercado' in df.columns:
            df['Mercado'] = df['Mercado'].apply(self.normalizer.normalize_market)
        
        # Remove duplicates
        df = df.drop_duplicates(subset=['ID_Empresa'], keep='first')
        
        print(f"  ✅ Processed {len(df)} unique companies")
        
        return df
    
    def process_valuations_data(self, datasets: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """Processes valuation data - KEEPING 'Valuation' NAME"""
        print("\n📊 Processing Valuation data (NOT translating to Avaliações)...")
        
        all_valuations = []
        
        # Main CRM valuation data
        if 'crm_valuation' in datasets:
            df = datasets['crm_valuation'].copy()
            
            # Keep essential valuation columns
            valuation_cols = {
                'ID': 'ID_Valuation',
                'Nome da Startup': 'Nome_Empresa',
                'Data de Valuation': 'Data_Valuation',  # Keep Valuation term
                'Valuation': 'Valor_Valuation',  # Keep Valuation term
                'Tipo de Valuation': 'Tipo_Valuation',  # Keep Valuation term
                'Nome do Respondente': 'Nome_Respondente',
                'Email': 'Email_Respondente',
                'Telefone': 'Telefone_Respondente'
            }
            
            df = df[list(valuation_cols.keys())].rename(columns=valuation_cols)
            
            # Normalize dates
            if 'Data_Valuation' in df.columns:
                df['Data_Valuation'] = df['Data_Valuation'].apply(self.normalizer.normalize_date)
            
            # Normalize names
            if 'Nome_Empresa' in df.columns:
                df['Nome_Empresa'] = df['Nome_Empresa'].apply(self.normalizer.capitalize_name)
            if 'Nome_Respondente' in df.columns:
                df['Nome_Respondente'] = df['Nome_Respondente'].apply(self.normalizer.capitalize_name)
            
            all_valuations.append(df)
        
        # Additional valuation data
        if 'valuation' in datasets:
            df_val = datasets['valuation'].copy()
            # Process additional valuation data if needed
            if not df_val.empty and 'ID' in df_val.columns:
                # Map columns if they exist
                if all(col in df_val.columns for col in ['ID', 'valuation_value']):
                    df_val = df_val[['ID', 'valuation_value']].rename(columns={
                        'ID': 'ID_Valuation',
                        'valuation_value': 'Valor_Valuation_Adicional'
                    })
                    all_valuations.append(df_val)
        
        # Combine all valuation data
        if all_valuations:
            result = pd.concat(all_valuations, ignore_index=True)
            result = result.drop_duplicates(subset=['ID_Valuation'], keep='first')
            print(f"  ✅ Processed {len(result)} valuation records")
            return result
        
        return pd.DataFrame()
    
    def process_contacts_data(self, datasets: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """Processes contact data"""
        print("\n📊 Processing Contacts (Contatos) data...")
        
        if 'crm_valuation' not in datasets:
            return pd.DataFrame()
        
        df = datasets['crm_valuation'].copy()
        
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
        
        print(f"  ✅ Processed {len(df_contacts)} unique contacts")
        
        return df_contacts
    
    def create_comprehensive_excel(self, datasets: Dict[str, pd.DataFrame]):
        """Creates the main comprehensive Excel file with all data"""
        output_file = self.export_path / f"CRM_Dados_Padronizados_COMPLETO_{self.timestamp}.xlsx"
        
        print(f"\n📝 Creating comprehensive Excel file...")
        
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
            
            # 2. VALUATION sheet (NOT Avaliações)
            if not valuations_df.empty:
                valuations_df.to_excel(writer, sheet_name='Valuation', index=False)  # Using 'Valuation' not 'Avaliações'
                print(f"  ✅ Added 'Valuation' sheet: {len(valuations_df)} records")
            
            # 3. Contacts sheet
            if not contacts_df.empty:
                contacts_df.to_excel(writer, sheet_name='Contatos', index=False)
                print(f"  ✅ Added 'Contatos' sheet: {len(contacts_df)} records")
            
            # 4. Payments data
            if 'payments' in datasets and not datasets['payments'].empty:
                payments_df = datasets['payments'].copy()
                payments_df.to_excel(writer, sheet_name='Pagamentos', index=False)
                print(f"  ✅ Added 'Pagamentos' sheet: {len(payments_df)} records")
            
            # 5. Metrics sheets
            if 'senseMetrics' in datasets and not datasets['senseMetrics'].empty:
                datasets['senseMetrics'].to_excel(writer, sheet_name='Sense_Metrics', index=False)
                print(f"  ✅ Added 'Sense_Metrics' sheet: {len(datasets['senseMetrics'])} records")
            
            if 'crmMetrics' in datasets and not datasets['crmMetrics'].empty:
                datasets['crmMetrics'].to_excel(writer, sheet_name='CRM_Metrics', index=False)
                print(f"  ✅ Added 'CRM_Metrics' sheet: {len(datasets['crmMetrics'])} records")
            
            # 6. O Poder do Equity GPT
            if 'opoderdoequitygpt' in datasets and not datasets['opoderdoequitygpt'].empty:
                datasets['opoderdoequitygpt'].to_excel(writer, sheet_name='O_Poder_Equity_GPT', index=False)
                print(f"  ✅ Added 'O_Poder_Equity_GPT' sheet: {len(datasets['opoderdoequitygpt'])} records")
            
            # 7. Summary Report
            summary_data = {
                'Dataset': ['Empresas', 'Valuation', 'Contatos', 'Pagamentos', 
                           'Sense Metrics', 'CRM Metrics', 'O Poder Equity GPT'],
                'Registros': [
                    len(companies_df),
                    len(valuations_df),
                    len(contacts_df),
                    len(datasets.get('payments', pd.DataFrame())),
                    len(datasets.get('senseMetrics', pd.DataFrame())),
                    len(datasets.get('crmMetrics', pd.DataFrame())),
                    len(datasets.get('opoderdoequitygpt', pd.DataFrame()))
                ],
                'Status': ['✅ Completo'] * 7
            }
            summary_df = pd.DataFrame(summary_data)
            summary_df.to_excel(writer, sheet_name='Resumo', index=False)
            
            # 8. Data quality report
            quality_data = {
                'Métrica': [
                    'Total de Registros',
                    'Empresas Únicas',
                    'Valuations Processadas',
                    'Contatos Únicos',
                    'Data de Processamento',
                    'Versão'
                ],
                'Valor': [
                    len(companies_df) + len(valuations_df) + len(contacts_df),
                    len(companies_df),
                    len(valuations_df),
                    len(contacts_df),
                    datetime.now().strftime('%d/%m/%Y, %H:%M:%S'),
                    '2.0 - Completo'
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
        
        # Apply formatting to all sheets
        for sheet_name in wb.sheetnames:
            ws = wb[sheet_name]
            
            # Format headers
            for cell in ws[1]:
                cell.font = header_font
                cell.fill = header_fill
                cell.alignment = header_alignment
            
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
    print("\n" + "=" * 60)
    print("DATA CONSOLIDATION - COMPLETE INTEGRATION")
    print("=" * 60)
    print(f"Starting at: {datetime.now().strftime('%d/%m/%Y, %H:%M:%S')}")
    print("\n⚠️ IMPORTANT: Keeping 'Valuation' terminology (not translating)")
    
    try:
        # Initialize consolidator
        consolidator = DataConsolidator()
        
        # Load all data
        datasets = consolidator.load_all_json_data()
        
        if not datasets:
            print("\n❌ No data files found!")
            return 1
        
        # Create comprehensive Excel file
        output_file = consolidator.create_comprehensive_excel(datasets)
        
        # Summary
        print("\n" + "=" * 60)
        print("✅ DATA CONSOLIDATION COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        
        total_records = sum(len(df) for df in datasets.values())
        print(f"\n📊 Final Statistics:")
        print(f"  • Total records processed: {total_records:,}")
        print(f"  • Data sources consolidated: {len(datasets)}")
        print(f"  • Output file: {output_file.name}")
        print(f"  • Sheet name for valuations: 'Valuation' (not translated)")
        
    except Exception as e:
        print(f"\n❌ Error during consolidation: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
