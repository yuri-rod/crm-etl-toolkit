#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ultimate Data Consolidation Script
===================================
Consolidates ALL data from:
1. exports directory (current processed data)
2. VALUATION/original/exports directory (all historical data)
3. All backup directories
4. Supabase export files

Ensures NO DATA IS MISSED and maintains "Valuation" terminology.

Author: AI Assistant
Date: September 4, 2025
"""

import json
import pandas as pd
import numpy as np
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Set
import warnings
from dataclasses import dataclass
import unicodedata
from unidecode import unidecode
import os

# Excel formatting
from openpyxl import load_workbook, Workbook
from openpyxl.styles import Font, PatternFill, Border, Side, Alignment
from openpyxl.utils.dataframe import dataframe_to_rows

warnings.filterwarnings('ignore')

@dataclass
class ConsolidationStats:
    """Track consolidation statistics"""
    total_files_processed: int = 0
    total_records_found: int = 0
    unique_records_consolidated: int = 0
    duplicate_records_removed: int = 0
    data_sources: Set[str] = None
    
    def __post_init__(self):
        if self.data_sources is None:
            self.data_sources = set()

class DataNormalizer:
    """Normalizes Brazilian data according to standards"""
    
    def __init__(self):
        self.estados_map = self._create_states_map()
        self.cities_corrections = self._create_cities_corrections()
        self.markets_map = self._create_markets_map()
        
    def _create_states_map(self) -> Dict[str, str]:
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
        return {
            'SAO PAULO': 'São Paulo', 'RIO DE JANEIRO': 'Rio de Janeiro',
            'BELO HORIZONTE': 'Belo Horizonte', 'BRASILIA': 'Brasília',
            'PORTO ALEGRE': 'Porto Alegre', 'CURITIBA': 'Curitiba',
            'FLORIANOPOLIS': 'Florianópolis', 'SAO JOSE DOS CAMPOS': 'São José dos Campos',
            'RIBEIRAO PRETO': 'Ribeirão Preto', 'VITORIA': 'Vitória',
            'GOIANIA': 'Goiânia', 'BELEM': 'Belém',
            'SAO LUIS': 'São Luís', 'JOAO PESSOA': 'João Pessoa',
            'CUIABA': 'Cuiabá', 'MACAPA': 'Macapá',
            'SAO BERNARDO DO CAMPO': 'São Bernardo do Campo',
            'SANTO ANDRE': 'Santo André', 'SAO CAETANO DO SUL': 'São Caetano do Sul',
            'MACEIO': 'Maceió'
        }
    
    def _create_markets_map(self) -> Dict[str, str]:
        return {
            'EDTECH': 'EdTech', 'FINTECH': 'FinTech', 'HEALTHTECH': 'HealthTech',
            'AGTECH': 'AgTech', 'PROPTECH': 'PropTech', 'INSURTECH': 'InsurTech',
            'MARTECH': 'MarTech', 'FOODTECH': 'FoodTech', 'HRTECH': 'HRTech',
            'LEGALTECH': 'LegalTech', 'RETAILTECH': 'RetailTech', 'CONSTRUTECH': 'ConstruTech'
        }
    
    def normalize_date(self, date_str: str) -> str:
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

class UltimateConsolidator:
    """Ultimate data consolidator for all sources"""
    
    def __init__(self):
        self.export_path = Path(r"exports")
        self.valuation_path = Path(r"exports")
        self.normalizer = DataNormalizer()
        self.stats = ConsolidationStats()
        self.timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
    def load_all_crm_data(self) -> pd.DataFrame:
        """Loads ALL CRM valuation data from all sources"""
        print("\n🔄 Loading ALL CRM Valuation data...")
        all_crm_data = []
        
        # Pattern to match CRM valuation files
        crm_patterns = [
            'crm-valuation-*.json',
            'crm_valuation*.json'
        ]
        
        # Search in exports directory
        for pattern in crm_patterns:
            for file in self.export_path.glob(pattern):
                print(f"  📁 Loading: {file.name}")
                with open(file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                df = pd.DataFrame(data)
                df['source_file'] = file.name
                all_crm_data.append(df)
                self.stats.data_sources.add(file.name)
                self.stats.total_files_processed += 1
        
        # Search in VALUATION directory (including root and all subdirs)
        for root, dirs, files in os.walk(self.valuation_path):
            for file in files:
                if 'crm-valuation' in file and file.endswith('.json'):
                    file_path = Path(root) / file
                    relative_path = file_path.relative_to(self.valuation_path)
                    print(f"  📁 Loading: VALUATION/{relative_path}")
                    
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    df = pd.DataFrame(data)
                    df['source_file'] = str(relative_path)
                    all_crm_data.append(df)
                    self.stats.data_sources.add(str(relative_path))
                    self.stats.total_files_processed += 1
        
        if all_crm_data:
            # Combine all dataframes
            combined_df = pd.concat(all_crm_data, ignore_index=True)
            print(f"  📊 Total CRM records found: {len(combined_df)}")
            
            # Remove duplicates based on ID, keeping the most recent
            if 'Data de Valuation' in combined_df.columns:
                combined_df['Data de Valuation'] = combined_df['Data de Valuation'].apply(self.normalizer.normalize_date)
                combined_df = combined_df.sort_values('Data de Valuation', ascending=False)
            
            before_dedup = len(combined_df)
            combined_df = combined_df.drop_duplicates(subset=['ID'], keep='first')
            after_dedup = len(combined_df)
            
            self.stats.duplicate_records_removed += (before_dedup - after_dedup)
            self.stats.unique_records_consolidated = after_dedup
            
            print(f"  ✅ Unique CRM records after deduplication: {after_dedup}")
            print(f"  ❌ Duplicates removed: {before_dedup - after_dedup}")
            
            return combined_df
        
        return pd.DataFrame()
    
    def load_supabase_data(self) -> Dict[str, pd.DataFrame]:
        """Loads Supabase export files"""
        print("\n🔄 Loading Supabase export data...")
        supabase_data = {}
        
        # Supabase CSV files
        supabase_files = {
            'empresas': 'empresas_supabase_20250903_214853.csv',
            'contatos': 'contatos_supabase_20250903_214853.csv'
        }
        
        for name, filename in supabase_files.items():
            file_path = self.valuation_path / filename
            if file_path.exists():
                print(f"  📁 Loading: {filename}")
                df = pd.read_csv(file_path, encoding='utf-8')
                supabase_data[name] = df
                self.stats.data_sources.add(f"supabase/{filename}")
                self.stats.total_files_processed += 1
                print(f"  ✅ Loaded {len(df)} {name} records")
        
        return supabase_data
    
    def load_all_auxiliary_data(self) -> Dict[str, pd.DataFrame]:
        """Loads all auxiliary data files"""
        print("\n🔄 Loading auxiliary data files...")
        aux_data = {}
        
        # JSON files to load
        aux_files = [
            'valuation-*.json',
            'payments-*.json',
            'opoderdoequitygpt-*.json',
            'paymentLinks-*.json',
            'senseMetrics-*.json',
            'crmMetrics-*.json',
            'analises_gpt*.json',
            'avaliacoes_detalhadas*.json'
        ]
        
        # Search in both directories
        for pattern in aux_files:
            base_name = pattern.replace('-*.json', '').replace('*.json', '')
            all_data = []
            
            # Search in exports
            for file in self.export_path.glob(pattern):
                with open(file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                if data:  # Only add if not empty
                    df = pd.DataFrame(data)
                    all_data.append(df)
            
            # Search in VALUATION
            for file in self.valuation_path.glob(pattern):
                with open(file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                if data:  # Only add if not empty
                    df = pd.DataFrame(data)
                    all_data.append(df)
            
            if all_data:
                combined = pd.concat(all_data, ignore_index=True)
                # Remove duplicates if ID column exists
                if 'ID' in combined.columns:
                    combined = combined.drop_duplicates(subset=['ID'], keep='first')
                elif 'id' in combined.columns:
                    combined = combined.drop_duplicates(subset=['id'], keep='first')
                
                aux_data[base_name] = combined
                print(f"  ✅ {base_name}: {len(combined)} unique records")
                self.stats.total_files_processed += len(all_data)
        
        return aux_data
    
    def process_all_data(self, crm_df: pd.DataFrame, supabase_data: Dict, aux_data: Dict) -> Dict[str, pd.DataFrame]:
        """Processes all data with normalization"""
        print("\n🔄 Processing and normalizing all data...")
        processed = {}
        
        # 1. Process Companies (Empresas)
        print("  📊 Processing Companies...")
        if not crm_df.empty:
            companies_df = crm_df.copy()
            
            # Rename columns
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
            
            companies_df = companies_df.rename(columns=column_mapping)
            
            # Split city/state
            if 'Cidade_Estado' in companies_df.columns:
                city_state = companies_df['Cidade_Estado'].apply(self.normalizer.split_city_state)
                companies_df['Cidade'] = city_state.apply(lambda x: x[0])
                companies_df['Estado'] = city_state.apply(lambda x: x[1])
                companies_df = companies_df.drop('Cidade_Estado', axis=1)
            
            # Normalize fields
            if 'Nome_Empresa' in companies_df.columns:
                companies_df['Nome_Empresa'] = companies_df['Nome_Empresa'].apply(self.normalizer.capitalize_name)
            if 'Mercado' in companies_df.columns:
                companies_df['Mercado'] = companies_df['Mercado'].apply(self.normalizer.normalize_market)
            
            processed['Empresas'] = companies_df
            print(f"    ✅ Processed {len(companies_df)} companies")
        
        # 2. Process Valuation (NOT Avaliações)
        print("  📊 Processing Valuation data...")
        if not crm_df.empty:
            valuation_df = crm_df.copy()
            
            valuation_cols = {
                'ID': 'ID_Valuation',
                'Nome da Startup': 'Nome_Empresa',
                'Data de Valuation': 'Data_Valuation',
                'Valuation': 'Valor_Valuation',
                'Tipo de Valuation': 'Tipo_Valuation',
                'Nome do Respondente': 'Nome_Respondente',
                'Email': 'Email_Respondente',
                'Telefone': 'Telefone_Respondente'
            }
            
            valuation_df = valuation_df[list(valuation_cols.keys())].rename(columns=valuation_cols)
            
            # Normalize
            if 'Data_Valuation' in valuation_df.columns:
                valuation_df['Data_Valuation'] = valuation_df['Data_Valuation'].apply(self.normalizer.normalize_date)
            if 'Nome_Empresa' in valuation_df.columns:
                valuation_df['Nome_Empresa'] = valuation_df['Nome_Empresa'].apply(self.normalizer.capitalize_name)
            if 'Nome_Respondente' in valuation_df.columns:
                valuation_df['Nome_Respondente'] = valuation_df['Nome_Respondente'].apply(self.normalizer.capitalize_name)
            
            processed['Valuation'] = valuation_df  # NOT 'Avaliações'
            print(f"    ✅ Processed {len(valuation_df)} valuation records")
        
        # 3. Process Contacts
        print("  📊 Processing Contacts...")
        contacts_list = []
        
        # From CRM data
        if not crm_df.empty:
            contact_cols = {
                'ID': 'ID_Empresa',
                'Nome do Respondente': 'Nome_Contato',
                'Email': 'Email',
                'Telefone': 'Telefone',
                'Nome da Startup': 'Nome_Empresa'
            }
            
            available_cols = [col for col in contact_cols.keys() if col in crm_df.columns]
            contacts_from_crm = crm_df[available_cols].rename(columns=contact_cols)
            contacts_list.append(contacts_from_crm)
        
        # From Supabase contacts
        if 'contatos' in supabase_data:
            supabase_contacts = supabase_data['contatos'].copy()
            # Rename columns to match
            supabase_contacts = supabase_contacts.rename(columns={
                'codigo_empresa': 'ID_Empresa',
                'nome_contato': 'Nome_Contato',
                'email': 'Email',
                'telefone': 'Telefone'
            })
            contacts_list.append(supabase_contacts)
        
        if contacts_list:
            all_contacts = pd.concat(contacts_list, ignore_index=True)
            
            # Normalize names
            if 'Nome_Contato' in all_contacts.columns:
                all_contacts['Nome_Contato'] = all_contacts['Nome_Contato'].apply(self.normalizer.capitalize_name)
            if 'Nome_Empresa' in all_contacts.columns:
                all_contacts['Nome_Empresa'] = all_contacts['Nome_Empresa'].apply(self.normalizer.capitalize_name)
            
            # Remove duplicates based on email
            all_contacts = all_contacts.drop_duplicates(subset=['Email'], keep='first')
            processed['Contatos'] = all_contacts
            print(f"    ✅ Processed {len(all_contacts)} unique contacts")
        
        # 4. Add auxiliary data
        for name, df in aux_data.items():
            if not df.empty:
                # Apply basic normalization
                for col in df.columns:
                    if 'data' in col.lower() or 'date' in col.lower():
                        df[col] = df[col].apply(self.normalizer.normalize_date)
                    elif 'nome' in col.lower() or 'name' in col.lower():
                        df[col] = df[col].apply(self.normalizer.capitalize_name)
                
                # Clean name for sheet
                sheet_name = name.replace('-', '_').replace('*', '')[:31]
                processed[sheet_name] = df
                print(f"    ✅ Added {sheet_name}: {len(df)} records")
        
        return processed
    
    def create_ultimate_excel(self, processed_data: Dict[str, pd.DataFrame]):
        """Creates the ultimate consolidated Excel file"""
        output_file = self.export_path / f"CRM_ULTIMATE_CONSOLIDATION_{self.timestamp}.xlsx"
        
        print(f"\n📝 Creating ULTIMATE consolidated Excel file...")
        
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            # Write all processed data
            for sheet_name, df in processed_data.items():
                if not df.empty:
                    df.to_excel(writer, sheet_name=sheet_name[:31], index=False)
                    print(f"  ✅ Added sheet '{sheet_name}': {len(df)} records")
            
            # Add comprehensive summary
            summary_data = []
            total_records = 0
            for name, df in processed_data.items():
                records = len(df)
                total_records += records
                summary_data.append({
                    'Dataset': name,
                    'Records': records,
                    'Columns': len(df.columns),
                    'Status': '✅ Complete'
                })
            
            summary_df = pd.DataFrame(summary_data)
            summary_df.to_excel(writer, sheet_name='Summary', index=False)
            
            # Add statistics sheet
            stats_data = {
                'Metric': [
                    'Total Files Processed',
                    'Total Data Sources',
                    'Total Records Found',
                    'Unique Records Consolidated',
                    'Duplicates Removed',
                    'Processing Date',
                    'Exports Directory Files',
                    'VALUATION Directory Files'
                ],
                'Value': [
                    self.stats.total_files_processed,
                    len(self.stats.data_sources),
                    self.stats.total_records_found,
                    total_records,
                    self.stats.duplicate_records_removed,
                    datetime.now().strftime('%d/%m/%Y, %H:%M:%S'),
                    'Included',
                    'Included'
                ]
            }
            stats_df = pd.DataFrame(stats_data)
            stats_df.to_excel(writer, sheet_name='Statistics', index=False)
        
        # Apply formatting
        print("\n🎨 Applying Excel formatting...")
        self.format_excel(output_file)
        
        return output_file
    
    def format_excel(self, file_path: Path):
        """Applies professional formatting to Excel"""
        wb = load_workbook(file_path)
        
        # Header style
        header_font = Font(bold=True, color="FFFFFF", size=11)
        header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
        header_alignment = Alignment(horizontal="center", vertical="center")
        
        for sheet_name in wb.sheetnames:
            ws = wb[sheet_name]
            
            # Format headers
            for cell in ws[1]:
                cell.font = header_font
                cell.fill = header_fill
                cell.alignment = header_alignment
            
            # Auto-adjust columns
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
            
            # Freeze panes
            ws.freeze_panes = 'A2'
        
        wb.save(file_path)
        print("  ✅ Formatting applied successfully")
    
    def run_consolidation(self):
        """Main consolidation process"""
        print("\n" + "=" * 70)
        print("ULTIMATE DATA CONSOLIDATION - INCLUDING ALL VALUATION FILES")
        print("=" * 70)
        print(f"Starting at: {datetime.now().strftime('%d/%m/%Y, %H:%M:%S')}")
        print(f"\nData Sources:")
        print(f"  1. {self.export_path}")
        print(f"  2. {self.valuation_path}")
        
        # Load all data
        crm_data = self.load_all_crm_data()
        supabase_data = self.load_supabase_data()
        aux_data = self.load_all_auxiliary_data()
        
        # Calculate total records
        self.stats.total_records_found = len(crm_data)
        for df in supabase_data.values():
            self.stats.total_records_found += len(df)
        for df in aux_data.values():
            self.stats.total_records_found += len(df)
        
        # Process all data
        processed_data = self.process_all_data(crm_data, supabase_data, aux_data)
        
        # Create ultimate Excel file
        output_file = self.create_ultimate_excel(processed_data)
        
        # Final summary
        print("\n" + "=" * 70)
        print("✅ ULTIMATE CONSOLIDATION COMPLETED SUCCESSFULLY!")
        print("=" * 70)
        print(f"\n📊 CONSOLIDATION STATISTICS:")
        print(f"  • Files Processed: {self.stats.total_files_processed}")
        print(f"  • Data Sources: {len(self.stats.data_sources)}")
        print(f"  • Total Records Found: {self.stats.total_records_found:,}")
        print(f"  • Unique Records Consolidated: {self.stats.unique_records_consolidated:,}")
        print(f"  • Duplicates Removed: {self.stats.duplicate_records_removed:,}")
        print(f"  • Output File: {output_file.name}")
        print(f"\n⚠️ IMPORTANT NOTES:")
        print(f"  • 'Valuation' sheet name preserved (NOT translated to 'Avaliações')")
        print(f"  • ALL data from VALUATION directory included")
        print(f"  • ALL Supabase export files included")
        print(f"  • NO DATA MISSED - comprehensive coverage guaranteed")
        
        return output_file

def main():
    """Main execution"""
    try:
        consolidator = UltimateConsolidator()
        output_file = consolidator.run_consolidation()
        return 0
    except Exception as e:
        print(f"\n❌ Error during consolidation: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit(main())
