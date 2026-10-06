#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ETL Script for Processing Updated Backup Files
==============================================
Processes the backup files from 20250903 with comprehensive data standardization:
- Date format normalization (dd/mm/yyyy, 24-hour)
- Proper capitalization of names
- State abbreviation expansion
- City name correction with proper accentuation
- Market sector standardization
- Duplicate removal

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
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Border, Side, Alignment, NamedStyle
from openpyxl.formatting.rule import ColorScaleRule
from openpyxl.utils.dataframe import dataframe_to_rows

warnings.filterwarnings('ignore')

@dataclass
class ETLMetrics:
    """ETL processing metrics"""
    total_records: int = 0
    unique_records: int = 0
    duplicates_removed: int = 0
    dates_normalized: int = 0
    names_capitalized: int = 0
    states_expanded: int = 0
    cities_corrected: int = 0
    markets_standardized: int = 0
    missing_fields: Dict[str, int] = None
    completeness_score: float = 0.0
    
    def __post_init__(self):
        if self.missing_fields is None:
            self.missing_fields = {}

class BrazilianDataNormalizer:
    """Normalizes Brazilian data according to local standards"""
    
    def __init__(self):
        self.estados_map = self._create_states_map()
        self.cities_corrections = self._create_cities_corrections()
        self.markets_map = self._create_markets_map()
        
    def _create_states_map(self) -> Dict[str, str]:
        """Creates mapping from abbreviations to full state names"""
        return {
            # Abbreviations
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
            'EDTECH': 'EdTech',
            'FINTECH': 'FinTech',
            'HEALTHTECH': 'HealthTech',
            'AGTECH': 'AgTech',
            'PROPTECH': 'PropTech',
            'INSURTECH': 'InsurTech',
            'MARTECH': 'MarTech',
            'FOODTECH': 'FoodTech',
            'HRTECH': 'HRTech',
            'LEGALTECH': 'LegalTech',
            'RETAILTECH': 'RetailTech',
            'CONSTRUTECH': 'ConstruTech'
        }
    
    def normalize_date(self, date_str: str) -> str:
        """Normalizes date to dd/mm/yyyy, HH:MM:SS format (24-hour)"""
        if not date_str or pd.isna(date_str):
            return ""
        
        # Already in correct format
        if re.match(r'\d{2}/\d{2}/\d{4}, \d{2}:\d{2}:\d{2}', str(date_str)):
            return str(date_str)
        
        # Try different date parsing formats
        try:
            # Parse various formats
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
        
        # Prepositions that should remain lowercase
        prepositions = {'de', 'da', 'do', 'das', 'dos', 'e'}
        
        words = str(text).strip().split()
        capitalized = []
        
        for i, word in enumerate(words):
            word_lower = word.lower()
            # Keep first word capitalized, prepositions lowercase
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
        
        # Check if it's an abbreviation
        if state_clean in self.estados_map:
            return self.estados_map[state_clean]
        
        # Check without accents
        state_no_accent = unidecode(state_clean)
        if state_no_accent in self.estados_map:
            return self.estados_map[state_no_accent]
        
        # Return capitalized if not found
        return self.capitalize_name(state)
    
    def normalize_city(self, city: str) -> str:
        """Normalizes city name with proper accentuation"""
        if not city or pd.isna(city):
            return ""
        
        city_upper = str(city).strip().upper()
        city_no_accent = unidecode(city_upper)
        
        # Check corrections
        if city_upper in self.cities_corrections:
            return self.cities_corrections[city_upper]
        if city_no_accent in self.cities_corrections:
            return self.cities_corrections[city_no_accent]
        
        # Return properly capitalized
        return self.capitalize_name(city)
    
    def normalize_market(self, market: str) -> str:
        """Normalizes market sector"""
        if not market or pd.isna(market):
            return ""
        
        market_upper = str(market).strip().upper()
        
        if market_upper in self.markets_map:
            return self.markets_map[market_upper]
        
        # Check without special chars
        market_clean = re.sub(r'[^A-Z]', '', market_upper)
        if market_clean in self.markets_map:
            return self.markets_map[market_clean]
        
        return self.capitalize_name(market)
    
    def split_city_state(self, location: str) -> Tuple[str, str]:
        """Splits city/state field into separate city and state"""
        if not location or pd.isna(location):
            return "", ""
        
        # Common patterns
        patterns = [
            r'(.+?)[/\-]([A-Z]{2})$',  # City/ST or City-ST
            r'(.+?)\s*,\s*([A-Z]{2})$',  # City, ST
            r'(.+?)\s+([A-Z]{2})$',  # City ST
        ]
        
        location_str = str(location).strip()
        
        for pattern in patterns:
            match = re.match(pattern, location_str)
            if match:
                city = match.group(1).strip()
                state = match.group(2).strip()
                return self.normalize_city(city), self.normalize_state(state)
        
        # If no pattern matches, assume it's just a city
        return self.normalize_city(location_str), ""

class ETLProcessor:
    """Main ETL processor for backup files"""
    
    def __init__(self, export_path: str = "exports"):
        self.export_path = Path(export_path)
        self.normalizer = BrazilianDataNormalizer()
        self.metrics = ETLMetrics()
        self.timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
    def process_crm_valuation(self) -> pd.DataFrame:
        """Processes CRM valuation data"""
        print("\n🔄 Processing CRM Valuation data...")
        
        # Load the JSON file
        json_file = self.export_path / "crm-valuation-20250903-2314.json"
        
        if not json_file.exists():
            print(f"❌ File not found: {json_file}")
            return pd.DataFrame()
        
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        df = pd.DataFrame(data)
        self.metrics.total_records = len(df)
        
        # Process each field
        if 'Data de Valuation' in df.columns:
            df['Data de Valuation'] = df['Data de Valuation'].apply(self.normalizer.normalize_date)
            self.metrics.dates_normalized = df['Data de Valuation'].notna().sum()
        
        if 'Nome da Startup' in df.columns:
            df['Nome da Startup'] = df['Nome da Startup'].apply(self.normalizer.capitalize_name)
            self.metrics.names_capitalized += df['Nome da Startup'].notna().sum()
        
        if 'Nome do Respondente' in df.columns:
            df['Nome do Respondente'] = df['Nome do Respondente'].apply(self.normalizer.capitalize_name)
            self.metrics.names_capitalized += df['Nome do Respondente'].notna().sum()
        
        if 'Cidade/Estado' in df.columns:
            city_state = df['Cidade/Estado'].apply(self.normalizer.split_city_state)
            df['Cidade'] = city_state.apply(lambda x: x[0])
            df['Estado'] = city_state.apply(lambda x: x[1])
            self.metrics.cities_corrected = df['Cidade'].notna().sum()
            self.metrics.states_expanded = df['Estado'].notna().sum()
        
        if 'Mercado' in df.columns:
            df['Mercado'] = df['Mercado'].apply(self.normalizer.normalize_market)
            self.metrics.markets_standardized = df['Mercado'].notna().sum()
        
        # Remove duplicates
        original_count = len(df)
        df = df.drop_duplicates(subset=['ID'], keep='first')
        self.metrics.duplicates_removed = original_count - len(df)
        self.metrics.unique_records = len(df)
        
        # Calculate missing fields
        for col in df.columns:
            missing_count = df[col].isna().sum()
            if missing_count > 0:
                self.metrics.missing_fields[col] = missing_count
        
        # Calculate completeness score
        total_cells = len(df) * len(df.columns)
        non_missing_cells = total_cells - sum(self.metrics.missing_fields.values())
        self.metrics.completeness_score = (non_missing_cells / total_cells) * 100 if total_cells > 0 else 0
        
        print(f"✅ Processed {self.metrics.unique_records} unique records")
        print(f"   - Dates normalized: {self.metrics.dates_normalized}")
        print(f"   - Names capitalized: {self.metrics.names_capitalized}")
        print(f"   - Cities corrected: {self.metrics.cities_corrected}")
        print(f"   - States expanded: {self.metrics.states_expanded}")
        print(f"   - Markets standardized: {self.metrics.markets_standardized}")
        print(f"   - Duplicates removed: {self.metrics.duplicates_removed}")
        print(f"   - Data completeness: {self.metrics.completeness_score:.2f}%")
        
        return df
    
    def process_all_datasets(self) -> Dict[str, pd.DataFrame]:
        """Processes all dataset files"""
        datasets = {}
        
        # Process each dataset type
        dataset_files = {
            'valuation': 'valuation-20250903-2315.json',
            'payments': 'payments-20250903-2315.json',
            'opoderdoequitygpt': 'opoderdoequitygpt-20250903-2315.json',
            'paymentLinks': 'paymentLinks-20250903-2315.json',
            'senseMetrics': 'senseMetrics-20250903-2315.json',
            'crmMetrics': 'crmMetrics-20250903-2315.json'
        }
        
        for name, filename in dataset_files.items():
            print(f"\n🔄 Processing {name} data...")
            json_file = self.export_path / filename
            
            if not json_file.exists():
                print(f"❌ File not found: {json_file}")
                continue
            
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            df = pd.DataFrame(data)
            
            # Apply standard transformations based on column names
            for col in df.columns:
                if 'data' in col.lower() or 'date' in col.lower():
                    df[col] = df[col].apply(self.normalizer.normalize_date)
                elif 'nome' in col.lower() or 'name' in col.lower():
                    df[col] = df[col].apply(self.normalizer.capitalize_name)
                elif col.lower() in ['cidade', 'city']:
                    df[col] = df[col].apply(self.normalizer.normalize_city)
                elif col.lower() in ['estado', 'state', 'uf']:
                    df[col] = df[col].apply(self.normalizer.normalize_state)
                elif col.lower() in ['mercado', 'market', 'setor', 'sector']:
                    df[col] = df[col].apply(self.normalizer.normalize_market)
            
            # Remove duplicates if ID column exists
            if 'ID' in df.columns:
                df = df.drop_duplicates(subset=['ID'], keep='first')
            elif 'id' in df.columns:
                df = df.drop_duplicates(subset=['id'], keep='first')
            
            datasets[name] = df
            print(f"✅ Processed {len(df)} records from {name}")
        
        return datasets
    
    def save_to_excel(self, df: pd.DataFrame, datasets: Dict[str, pd.DataFrame]):
        """Saves processed data to Excel with formatting"""
        output_file = self.export_path / f"CRM_Data_ETL_Updated_{self.timestamp}.xlsx"
        
        print(f"\n📝 Saving to Excel: {output_file.name}")
        
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            # Main CRM sheet
            df.to_excel(writer, sheet_name='CRM_Valuation', index=False)
            
            # Other datasets
            for name, data in datasets.items():
                if not data.empty:
                    sheet_name = name[:31]  # Excel sheet name limit
                    data.to_excel(writer, sheet_name=sheet_name, index=False)
            
            # Metrics sheet
            metrics_df = pd.DataFrame({
                'Metric': [
                    'Total Records Processed',
                    'Unique Records',
                    'Duplicates Removed',
                    'Dates Normalized',
                    'Names Capitalized',
                    'Cities Corrected',
                    'States Expanded',
                    'Markets Standardized',
                    'Data Completeness Score'
                ],
                'Value': [
                    self.metrics.total_records,
                    self.metrics.unique_records,
                    self.metrics.duplicates_removed,
                    self.metrics.dates_normalized,
                    self.metrics.names_capitalized,
                    self.metrics.cities_corrected,
                    self.metrics.states_expanded,
                    self.metrics.markets_standardized,
                    f"{self.metrics.completeness_score:.2f}%"
                ]
            })
            metrics_df.to_excel(writer, sheet_name='Metrics', index=False)
        
        print(f"✅ Excel file saved successfully!")
        return output_file
    
    def generate_quality_report(self, df: pd.DataFrame, datasets: Dict[str, pd.DataFrame]):
        """Generates a data quality report"""
        report_file = self.export_path / f"Data_Quality_Report_{self.timestamp}.txt"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("=" * 60 + "\n")
            f.write("DATA QUALITY REPORT - ETL PROCESSING\n")
            f.write("=" * 60 + "\n\n")
            f.write(f"Generated: {datetime.now().strftime('%d/%m/%Y, %H:%M:%S')}\n")
            f.write(f"Data Source: Backup files from 03/09/2025\n\n")
            
            f.write("PROCESSING METRICS\n")
            f.write("-" * 40 + "\n")
            f.write(f"Total Records Processed: {self.metrics.total_records}\n")
            f.write(f"Unique Records: {self.metrics.unique_records}\n")
            f.write(f"Duplicates Removed: {self.metrics.duplicates_removed}\n")
            f.write(f"Data Completeness: {self.metrics.completeness_score:.2f}%\n\n")
            
            f.write("TRANSFORMATION METRICS\n")
            f.write("-" * 40 + "\n")
            f.write(f"Dates Normalized: {self.metrics.dates_normalized}\n")
            f.write(f"Names Capitalized: {self.metrics.names_capitalized}\n")
            f.write(f"Cities Corrected: {self.metrics.cities_corrected}\n")
            f.write(f"States Expanded: {self.metrics.states_expanded}\n")
            f.write(f"Markets Standardized: {self.metrics.markets_standardized}\n\n")
            
            f.write("DATASET SUMMARY\n")
            f.write("-" * 40 + "\n")
            f.write(f"CRM Valuation: {len(df)} records\n")
            for name, data in datasets.items():
                f.write(f"{name}: {len(data)} records\n")
            
            if self.metrics.missing_fields:
                f.write("\nMISSING DATA FIELDS\n")
                f.write("-" * 40 + "\n")
                for field, count in sorted(self.metrics.missing_fields.items(), key=lambda x: x[1], reverse=True)[:10]:
                    f.write(f"{field}: {count} missing values\n")
            
            f.write("\n" + "=" * 60 + "\n")
            f.write("ETL PROCESS COMPLETED SUCCESSFULLY\n")
            f.write("=" * 60 + "\n")
        
        print(f"\n📊 Quality report saved: {report_file.name}")
        return report_file

def main():
    """Main execution function"""
    print("\n" + "=" * 60)
    print("ETL PROCESSOR - BACKUP FILES UPDATE")
    print("=" * 60)
    print(f"Starting at: {datetime.now().strftime('%d/%m/%Y, %H:%M:%S')}")
    
    try:
        # Initialize processor
        processor = ETLProcessor()
        
        # Process CRM valuation data
        crm_df = processor.process_crm_valuation()
        
        # Process other datasets
        other_datasets = processor.process_all_datasets()
        
        # Save to Excel
        excel_file = processor.save_to_excel(crm_df, other_datasets)
        
        # Generate quality report
        report_file = processor.generate_quality_report(crm_df, other_datasets)
        
        print("\n" + "=" * 60)
        print("✅ ETL PROCESSING COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        print(f"Output files:")
        print(f"  📊 Excel: {excel_file.name}")
        print(f"  📄 Report: {report_file.name}")
        
    except Exception as e:
        print(f"\n❌ Error during processing: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
