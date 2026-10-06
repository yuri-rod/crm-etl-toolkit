#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comprehensive ETL Data Cleaner and Standardizer
================================================
Applies complete ETL processing to ALL files in the exports folder:
- Cleans and validates data
- Standardizes formats (dates, names, locations)
- Removes duplicates and invalid entries
- Ensures data consistency across all sources
- Generates quality reports

Author: AI Assistant
Date: September 4, 2025
"""

import json
import pandas as pd
import numpy as np
import re
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Set
import warnings
from dataclasses import dataclass, field
import unicodedata
from unidecode import unidecode
import hashlib

# Excel formatting
from openpyxl import load_workbook, Workbook
from openpyxl.styles import Font, PatternFill, Border, Side, Alignment, NamedStyle
from openpyxl.formatting.rule import DataBarRule, ColorScaleRule
from openpyxl.utils.dataframe import dataframe_to_rows

warnings.filterwarnings('ignore')

@dataclass
class ETLStats:
    """Track ETL processing statistics"""
    files_processed: int = 0
    total_records_before: int = 0
    total_records_after: int = 0
    duplicates_removed: int = 0
    invalid_records_removed: int = 0
    dates_standardized: int = 0
    names_cleaned: int = 0
    locations_normalized: int = 0
    emails_validated: int = 0
    phones_formatted: int = 0
    missing_values_filled: int = 0
    data_quality_issues: List[str] = field(default_factory=list)

class DataStandardizer:
    """Comprehensive data standardization and cleaning"""
    
    def __init__(self):
        self.estados_brasil = self._init_estados()
        self.cidades_brasil = self._init_cidades()
        self.mercados_tech = self._init_mercados()
        self.stats = ETLStats()
        
    def _init_estados(self) -> Dict[str, str]:
        """Initialize Brazilian states mapping"""
        return {
            # Abbreviations to full names
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
            
            # Common variations
            'SAO PAULO': 'São Paulo', 'SAOPAULO': 'São Paulo',
            'RIO': 'Rio de Janeiro', 'RIODEJANEIRO': 'Rio de Janeiro',
            'BELO HORIZONTE': 'Minas Gerais', 'BH': 'Minas Gerais',
            'BRASILIA': 'Distrito Federal', 'BSB': 'Distrito Federal',
            'DISTRITO FEDERAL': 'Distrito Federal'
        }
    
    def _init_cidades(self) -> Dict[str, str]:
        """Initialize city corrections with proper accentuation"""
        return {
            # Capital cities
            'SAO PAULO': 'São Paulo', 'SAOPAULO': 'São Paulo',
            'RIO DE JANEIRO': 'Rio de Janeiro', 'RIODEJANEIRO': 'Rio de Janeiro',
            'BELO HORIZONTE': 'Belo Horizonte', 'BELOHORIZONTE': 'Belo Horizonte',
            'BRASILIA': 'Brasília', 'BRASÍLIA': 'Brasília',
            'PORTO ALEGRE': 'Porto Alegre', 'PORTOALEGRE': 'Porto Alegre',
            'CURITIBA': 'Curitiba', 'FLORIANOPOLIS': 'Florianópolis',
            'VITORIA': 'Vitória', 'GOIANIA': 'Goiânia',
            'BELEM': 'Belém', 'SAO LUIS': 'São Luís',
            'JOAO PESSOA': 'João Pessoa', 'JOAOPESSOA': 'João Pessoa',
            'CUIABA': 'Cuiabá', 'MACAPA': 'Macapá',
            'MACEIO': 'Maceió', 'ARACAJU': 'Aracaju',
            
            # Major cities
            'SAO JOSE DOS CAMPOS': 'São José dos Campos',
            'RIBEIRAO PRETO': 'Ribeirão Preto',
            'SAO BERNARDO DO CAMPO': 'São Bernardo do Campo',
            'SANTO ANDRE': 'Santo André',
            'SAO CAETANO DO SUL': 'São Caetano do Sul',
            'CAMPINAS': 'Campinas', 'GUARULHOS': 'Guarulhos',
            'OSASCO': 'Osasco', 'SOROCABA': 'Sorocaba',
            'JUNDIAI': 'Jundiaí', 'PIRACICABA': 'Piracicaba',
            'BAURU': 'Bauru', 'SAO JOSE DO RIO PRETO': 'São José do Rio Preto',
            'SANTOS': 'Santos', 'MOGI DAS CRUZES': 'Mogi das Cruzes',
            'DIADEMA': 'Diadema', 'CARAPICUIBA': 'Carapicuíba'
        }
    
    def _init_mercados(self) -> Dict[str, str]:
        """Initialize market/sector standardization"""
        return {
            'EDTECH': 'EdTech', 'FINTECH': 'FinTech', 
            'HEALTHTECH': 'HealthTech', 'AGTECH': 'AgTech',
            'PROPTECH': 'PropTech', 'INSURTECH': 'InsurTech',
            'MARTECH': 'MarTech', 'FOODTECH': 'FoodTech',
            'HRTECH': 'HRTech', 'LEGALTECH': 'LegalTech',
            'RETAILTECH': 'RetailTech', 'CONSTRUTECH': 'ConstruTech',
            'BIOTECH': 'BioTech', 'CLEANTECH': 'CleanTech',
            'GOVTECH': 'GovTech', 'AUTOTECH': 'AutoTech',
            'LOGTECH': 'LogTech', 'REGTECH': 'RegTech'
        }
    
    def clean_text(self, text: Any) -> str:
        """Clean and normalize text fields"""
        if pd.isna(text) or text is None:
            return ""
        
        # Convert to string and strip
        text = str(text).strip()
        
        # Remove multiple spaces
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters at start/end
        text = re.sub(r'^[^\w]+|[^\w]+$', '', text)
        
        return text
    
    def standardize_date(self, date_value: Any) -> str:
        """Standardize date to dd/mm/yyyy, HH:MM:SS format"""
        if pd.isna(date_value) or not date_value:
            return ""
        
        # Already in correct format
        if re.match(r'^\d{2}/\d{2}/\d{4}, \d{2}:\d{2}:\d{2}$', str(date_value)):
            return str(date_value)
        
        # Try various date formats
        formats = [
            '%Y-%m-%d %H:%M:%S',
            '%d/%m/%Y %H:%M:%S',
            '%m/%d/%Y, %I:%M:%S %p',
            '%Y/%m/%d %H:%M:%S',
            '%d-%m-%Y %H:%M:%S',
            '%Y-%m-%d',
            '%d/%m/%Y',
            '%m/%d/%Y'
        ]
        
        for fmt in formats:
            try:
                dt = datetime.strptime(str(date_value).strip(), fmt)
                self.stats.dates_standardized += 1
                return dt.strftime('%d/%m/%Y, %H:%M:%S')
            except:
                continue
        
        # If no format matches, return original
        return str(date_value)
    
    def clean_name(self, name: Any) -> str:
        """Clean and properly capitalize names"""
        if pd.isna(name) or not name:
            return ""
        
        name = self.clean_text(name)
        
        # Remove titles
        titles = ['DR', 'DR.', 'DRA', 'DRA.', 'SR', 'SR.', 'SRA', 'SRA.', 'PROF', 'PROF.']
        for title in titles:
            name = re.sub(f'^{title}\\s+', '', name.upper())
        
        # Proper capitalization with Portuguese prepositions
        prepositions = {'de', 'da', 'do', 'das', 'dos', 'e'}
        words = name.split()
        capitalized = []
        
        for i, word in enumerate(words):
            word_lower = word.lower()
            if i == 0 or word_lower not in prepositions:
                # Handle names with apostrophes
                if "'" in word:
                    parts = word.split("'")
                    word = "'".join([p.capitalize() for p in parts])
                else:
                    word = word.capitalize()
            else:
                word = word_lower
            capitalized.append(word)
        
        self.stats.names_cleaned += 1
        return ' '.join(capitalized)
    
    def validate_email(self, email: Any) -> str:
        """Validate and clean email addresses"""
        if pd.isna(email) or not email:
            return ""
        
        email = str(email).strip().lower()
        
        # Basic email validation
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        
        if re.match(email_pattern, email):
            self.stats.emails_validated += 1
            return email
        
        # Try to fix common issues
        email = re.sub(r'\s+', '', email)  # Remove spaces
        email = re.sub(r'\.{2,}', '.', email)  # Fix multiple dots
        
        if re.match(email_pattern, email):
            self.stats.emails_validated += 1
            return email
        
        self.stats.data_quality_issues.append(f"Invalid email: {email}")
        return ""
    
    def format_phone(self, phone: Any) -> str:
        """Format Brazilian phone numbers"""
        if pd.isna(phone) or not phone:
            return ""
        
        # Remove all non-digits
        phone = re.sub(r'\D', '', str(phone))
        
        # Brazilian phone patterns
        if len(phone) == 11:  # Mobile with area code
            formatted = f"({phone[:2]}) {phone[2:7]}-{phone[7:]}"
            self.stats.phones_formatted += 1
            return formatted
        elif len(phone) == 10:  # Landline with area code
            formatted = f"({phone[:2]}) {phone[2:6]}-{phone[6:]}"
            self.stats.phones_formatted += 1
            return formatted
        elif len(phone) == 9:  # Mobile without area code
            formatted = f"{phone[:5]}-{phone[5:]}"
            self.stats.phones_formatted += 1
            return formatted
        elif len(phone) == 8:  # Landline without area code
            formatted = f"{phone[:4]}-{phone[4:]}"
            self.stats.phones_formatted += 1
            return formatted
        
        return str(phone)  # Return original if doesn't match patterns
    
    def normalize_location(self, city: Any, state: Any = None) -> Tuple[str, str]:
        """Normalize city and state names"""
        normalized_city = ""
        normalized_state = ""
        
        # Process city
        if city:
            city_upper = self.clean_text(city).upper()
            city_no_accent = unidecode(city_upper)
            
            # Check corrections
            if city_upper in self.cidades_brasil:
                normalized_city = self.cidades_brasil[city_upper]
            elif city_no_accent in self.cidades_brasil:
                normalized_city = self.cidades_brasil[city_no_accent]
            else:
                normalized_city = self.clean_name(city)
            
            self.stats.locations_normalized += 1
        
        # Process state
        if state:
            state_upper = self.clean_text(state).upper()
            state_no_accent = unidecode(state_upper)
            
            if state_upper in self.estados_brasil:
                normalized_state = self.estados_brasil[state_upper]
            elif state_no_accent in self.estados_brasil:
                normalized_state = self.estados_brasil[state_no_accent]
            elif len(state_upper) == 2 and state_upper in self.estados_brasil:
                normalized_state = self.estados_brasil[state_upper]
            else:
                normalized_state = self.clean_name(state)
            
            self.stats.locations_normalized += 1
        
        return normalized_city, normalized_state
    
    def split_city_state(self, location: Any) -> Tuple[str, str]:
        """Split combined city/state field"""
        if pd.isna(location) or not location:
            return "", ""
        
        location = self.clean_text(location)
        
        # Try different patterns
        patterns = [
            r'(.+?)[/\-]([A-Z]{2})$',  # City/ST or City-ST
            r'(.+?),\s*([A-Z]{2})$',   # City, ST
            r'(.+?)\s+([A-Z]{2})$',    # City ST
        ]
        
        for pattern in patterns:
            match = re.match(pattern, location)
            if match:
                city = match.group(1).strip()
                state = match.group(2).strip()
                return self.normalize_location(city, state)
        
        # If no pattern matches, assume it's just a city
        return self.normalize_location(location)
    
    def normalize_market(self, market: Any) -> str:
        """Normalize market/sector names"""
        if pd.isna(market) or not market:
            return ""
        
        market = self.clean_text(market)
        market_upper = market.upper()
        market_no_space = re.sub(r'\s+', '', market_upper)
        
        # Check mappings
        if market_upper in self.mercados_tech:
            return self.mercados_tech[market_upper]
        elif market_no_space in self.mercados_tech:
            return self.mercados_tech[market_no_space]
        
        # Return cleaned original
        return self.clean_name(market)
    
    def validate_cnpj(self, cnpj: Any) -> str:
        """Validate and format Brazilian CNPJ"""
        if pd.isna(cnpj) or not cnpj:
            return ""
        
        # Remove all non-digits
        cnpj = re.sub(r'\D', '', str(cnpj))
        
        # CNPJ must have 14 digits
        if len(cnpj) == 14:
            # Format: XX.XXX.XXX/XXXX-XX
            formatted = f"{cnpj[:2]}.{cnpj[2:5]}.{cnpj[5:8]}/{cnpj[8:12]}-{cnpj[12:]}"
            return formatted
        
        return ""
    
    def clean_monetary_value(self, value: Any) -> float:
        """Clean and standardize monetary values"""
        if pd.isna(value) or value == "" or value is None:
            return 0.0
        
        # Convert to string and clean
        value_str = str(value)
        
        # Remove currency symbols and text
        value_str = re.sub(r'[R$\s]', '', value_str)
        value_str = re.sub(r'reais?|real', '', value_str, flags=re.IGNORECASE)
        
        # Handle Brazilian number format (1.000,00)
        if ',' in value_str and '.' in value_str:
            value_str = value_str.replace('.', '').replace(',', '.')
        elif ',' in value_str:
            value_str = value_str.replace(',', '.')
        
        try:
            return float(value_str)
        except:
            return 0.0

class ComprehensiveETL:
    """Main ETL processor for comprehensive data cleaning"""
    
    def __init__(self, export_path: str = r"exports"):
        self.export_path = Path(export_path)
        self.standardizer = DataStandardizer()
        self.timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.processed_data = {}
        
    def process_json_file(self, file_path: Path) -> pd.DataFrame:
        """Process a single JSON file"""
        print(f"  📄 Processing: {file_path.name}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if not data:
                return pd.DataFrame()
            
            df = pd.DataFrame(data)
            self.standardizer.stats.files_processed += 1
            self.standardizer.stats.total_records_before += len(df)
            
            # Apply cleaning based on column names
            df = self.clean_dataframe(df)
            
            self.standardizer.stats.total_records_after += len(df)
            
            return df
            
        except Exception as e:
            print(f"    ❌ Error processing {file_path.name}: {str(e)}")
            return pd.DataFrame()
    
    def process_csv_file(self, file_path: Path) -> pd.DataFrame:
        """Process a single CSV file"""
        print(f"  📄 Processing: {file_path.name}")
        
        try:
            df = pd.read_csv(file_path, encoding='utf-8')
            
            if df.empty:
                return pd.DataFrame()
            
            self.standardizer.stats.files_processed += 1
            self.standardizer.stats.total_records_before += len(df)
            
            # Apply cleaning
            df = self.clean_dataframe(df)
            
            self.standardizer.stats.total_records_after += len(df)
            
            return df
            
        except Exception as e:
            print(f"    ❌ Error processing {file_path.name}: {str(e)}")
            return pd.DataFrame()
    
    def clean_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Apply comprehensive cleaning to a dataframe"""
        if df.empty:
            return df
        
        original_count = len(df)
        
        # Clean column names
        df.columns = [col.strip().replace(' ', '_') for col in df.columns]
        
        # Process each column based on its name/type
        for col in df.columns:
            col_lower = col.lower()
            
            # Date columns
            if any(term in col_lower for term in ['data', 'date', 'criado', 'created', 'atualizado', 'updated']):
                df[col] = df[col].apply(self.standardizer.standardize_date)
            
            # Name columns
            elif any(term in col_lower for term in ['nome', 'name', 'respondente', 'contato']):
                df[col] = df[col].apply(self.standardizer.clean_name)
            
            # Email columns
            elif 'email' in col_lower or 'e-mail' in col_lower:
                df[col] = df[col].apply(self.standardizer.validate_email)
            
            # Phone columns
            elif any(term in col_lower for term in ['telefone', 'phone', 'celular', 'tel']):
                df[col] = df[col].apply(self.standardizer.format_phone)
            
            # City columns
            elif any(term in col_lower for term in ['cidade', 'city']):
                df[col] = df[col].apply(lambda x: self.standardizer.normalize_location(x, None)[0])
            
            # State columns
            elif any(term in col_lower for term in ['estado', 'state', 'uf']):
                df[col] = df[col].apply(lambda x: self.standardizer.normalize_location(None, x)[1])
            
            # Combined city/state
            elif 'cidade/estado' in col_lower or 'cidade_estado' in col_lower:
                city_state = df[col].apply(self.standardizer.split_city_state)
                df['Cidade_Clean'] = city_state.apply(lambda x: x[0])
                df['Estado_Clean'] = city_state.apply(lambda x: x[1])
            
            # Market/sector columns
            elif any(term in col_lower for term in ['mercado', 'market', 'setor', 'sector']):
                df[col] = df[col].apply(self.standardizer.normalize_market)
            
            # CNPJ columns
            elif 'cnpj' in col_lower:
                df[col] = df[col].apply(self.standardizer.validate_cnpj)
            
            # Monetary columns
            elif any(term in col_lower for term in ['valor', 'value', 'mrr', 'ltm', 'faturamento', 'revenue', 'valuation']):
                df[col] = df[col].apply(self.standardizer.clean_monetary_value)
            
            # Text columns - general cleaning
            elif df[col].dtype == 'object':
                df[col] = df[col].apply(self.standardizer.clean_text)
        
        # Remove completely duplicate rows
        before_dedup = len(df)
        df = df.drop_duplicates()
        self.standardizer.stats.duplicates_removed += (before_dedup - len(df))
        
        # Remove rows with all null values
        df = df.dropna(how='all')
        
        # Fill missing values for specific columns
        if 'ID' in df.columns or 'id' in df.columns:
            # Remove duplicates based on ID
            id_col = 'ID' if 'ID' in df.columns else 'id'
            df = df.drop_duplicates(subset=[id_col], keep='first')
        
        # Track invalid records removed
        records_removed = original_count - len(df)
        if records_removed > 0:
            self.standardizer.stats.invalid_records_removed += records_removed
        
        return df
    
    def process_all_files(self):
        """Process all JSON and CSV files in the directory"""
        print("\n🔄 Processing all files for ETL cleaning and standardization...")
        
        all_data = {}
        
        # Process JSON files
        print("\n📊 Processing JSON files...")
        json_files = list(self.export_path.glob("*.json"))
        for json_file in json_files:
            df = self.process_json_file(json_file)
            if not df.empty:
                base_name = json_file.stem
                all_data[base_name] = df
        
        # Process CSV files
        print("\n📊 Processing CSV files...")
        csv_files = list(self.export_path.glob("*.csv"))
        for csv_file in csv_files:
            df = self.process_csv_file(csv_file)
            if not df.empty:
                base_name = csv_file.stem
                # Don't overwrite if JSON version exists (JSON preferred)
                if base_name not in all_data:
                    all_data[base_name] = df
        
        self.processed_data = all_data
        return all_data
    
    def create_master_excel(self):
        """Create master Excel file with all cleaned data"""
        output_file = self.export_path / f"CRM_MASTER_CLEAN_ETL_{self.timestamp}.xlsx"
        
        print(f"\n📝 Creating master cleaned Excel file...")
        
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            # Write all cleaned data
            for name, df in self.processed_data.items():
                # Clean sheet name
                sheet_name = re.sub(r'[^\w\s-]', '', name)[:31]
                
                df.to_excel(writer, sheet_name=sheet_name, index=False)
                print(f"  ✅ Added sheet '{sheet_name}': {len(df)} records")
            
            # Add data quality report
            quality_report = self.generate_quality_report()
            quality_report.to_excel(writer, sheet_name='Quality_Report', index=False)
            
            # Add statistics
            stats_df = self.generate_statistics()
            stats_df.to_excel(writer, sheet_name='ETL_Statistics', index=False)
        
        # Apply formatting
        self.format_excel(output_file)
        
        return output_file
    
    def generate_quality_report(self) -> pd.DataFrame:
        """Generate data quality report"""
        issues = self.standardizer.stats.data_quality_issues[:100]  # First 100 issues
        
        if not issues:
            issues = ['No major quality issues found']
        
        report_data = {
            'Issue_Type': ['Data Quality Issues'] * len(issues),
            'Description': issues,
            'Timestamp': [datetime.now().strftime('%d/%m/%Y, %H:%M:%S')] * len(issues)
        }
        
        return pd.DataFrame(report_data)
    
    def generate_statistics(self) -> pd.DataFrame:
        """Generate ETL statistics"""
        stats = self.standardizer.stats
        
        stats_data = {
            'Metric': [
                'Files Processed',
                'Total Records Before',
                'Total Records After',
                'Duplicates Removed',
                'Invalid Records Removed',
                'Dates Standardized',
                'Names Cleaned',
                'Locations Normalized',
                'Emails Validated',
                'Phones Formatted',
                'Processing Date',
                'Data Quality Score'
            ],
            'Value': [
                stats.files_processed,
                stats.total_records_before,
                stats.total_records_after,
                stats.duplicates_removed,
                stats.invalid_records_removed,
                stats.dates_standardized,
                stats.names_cleaned,
                stats.locations_normalized,
                stats.emails_validated,
                stats.phones_formatted,
                datetime.now().strftime('%d/%m/%Y, %H:%M:%S'),
                f"{(stats.total_records_after / stats.total_records_before * 100):.2f}%" if stats.total_records_before > 0 else "100%"
            ]
        }
        
        return pd.DataFrame(stats_data)
    
    def format_excel(self, file_path: Path):
        """Apply professional formatting to Excel file"""
        wb = load_workbook(file_path)
        
        # Define styles
        header_font = Font(bold=True, color="FFFFFF", size=11)
        header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
        header_alignment = Alignment(horizontal="center", vertical="center")
        
        # Apply to all sheets
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
            
            # Freeze top row
            ws.freeze_panes = 'A2'
            
            # Add borders
            thin_border = Border(
                left=Side(style='thin', color='E0E0E0'),
                right=Side(style='thin', color='E0E0E0'),
                top=Side(style='thin', color='E0E0E0'),
                bottom=Side(style='thin', color='E0E0E0')
            )
            
            for row in ws.iter_rows(min_row=2):
                for cell in row:
                    cell.border = thin_border
        
        wb.save(file_path)
        print("  ✅ Professional formatting applied")
    
    def run_etl(self):
        """Main ETL execution"""
        print("\n" + "=" * 70)
        print("COMPREHENSIVE ETL - DATA CLEANING AND STANDARDIZATION")
        print("=" * 70)
        print(f"Starting at: {datetime.now().strftime('%d/%m/%Y, %H:%M:%S')}")
        print(f"Processing directory: {self.export_path}")
        
        # Process all files
        self.process_all_files()
        
        # Create master Excel
        output_file = self.create_master_excel()
        
        # Generate summary
        stats = self.standardizer.stats
        
        print("\n" + "=" * 70)
        print("✅ ETL PROCESSING COMPLETED SUCCESSFULLY!")
        print("=" * 70)
        
        print(f"\n📊 ETL STATISTICS:")
        print(f"  • Files Processed: {stats.files_processed}")
        print(f"  • Records Before: {stats.total_records_before:,}")
        print(f"  • Records After: {stats.total_records_after:,}")
        print(f"  • Duplicates Removed: {stats.duplicates_removed:,}")
        print(f"  • Invalid Records: {stats.invalid_records_removed:,}")
        
        print(f"\n🔧 STANDARDIZATIONS APPLIED:")
        print(f"  • Dates Standardized: {stats.dates_standardized:,}")
        print(f"  • Names Cleaned: {stats.names_cleaned:,}")
        print(f"  • Locations Normalized: {stats.locations_normalized:,}")
        print(f"  • Emails Validated: {stats.emails_validated:,}")
        print(f"  • Phones Formatted: {stats.phones_formatted:,}")
        
        if stats.total_records_before > 0:
            quality_score = (stats.total_records_after / stats.total_records_before) * 100
            print(f"\n📈 DATA QUALITY SCORE: {quality_score:.2f}%")
        
        print(f"\n📁 OUTPUT FILE: {output_file.name}")
        
        return output_file

def main():
    """Main execution"""
    try:
        etl = ComprehensiveETL()
        output_file = etl.run_etl()
        return 0
    except Exception as e:
        print(f"\n❌ Error during ETL processing: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit(main())
