#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CRM Data ETL Processor
======================
Comprehensive ETL pipeline for startup valuation CRM data transformation.
Converts Portuguese JSON exports to beautifully formatted English Excel files.

Features:
- Portuguese to English field translation
- Brazilian date/currency/phone formatting
- Data validation and cleaning
- Professional Excel formatting with charts
- Duplicate detection and data quality reports

Author: AI Assistant
Date: August 27, 2025
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

# Excel formatting
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Border, Side, Alignment, NamedStyle
from openpyxl.formatting.rule import ColorScaleRule, DataBarRule
from openpyxl.chart import BarChart, PieChart, LineChart, Reference
from openpyxl.utils.dataframe import dataframe_to_rows
from openpyxl.worksheet.table import Table, TableStyleInfo

warnings.filterwarnings('ignore')

@dataclass
class DataQualityMetrics:
    """Data quality metrics for reporting"""
    total_records: int
    complete_records: int
    duplicates_found: int
    invalid_emails: int
    invalid_phones: int
    missing_critical_fields: int
    data_completeness_score: float

class CRMDataProcessor:
    """Main ETL processor for CRM data transformation"""
    
    def __init__(self, data_dir: str):
        self.data_dir = Path(data_dir)
        self.field_translations = self._create_field_mapping()
        self.market_translations = self._create_market_mapping()
        self.stage_translations = self._create_stage_mapping()
        self.quality_metrics = {}
        
    def _create_field_mapping(self) -> Dict[str, str]:
        """Create comprehensive Portuguese to English field mapping"""
        return {
            # Company/Startup Fields
            'ID': 'company_id',
            'Nome da Startup': 'company_name',
            'Site': 'website',
            'Cidade/Estado': 'location',
            'Estágio Operacional': 'operational_stage',
            'Modelo de Negócio': 'business_model',
            'Mercado': 'market_sector',
            'Estágio de Investimento': 'investment_stage',
            
            # Contact Fields
            'Nome do Respondente': 'contact_name',
            'Email': 'email',
            'Telefone': 'phone',
            
            # Financial Fields
            'Valuation': 'valuation_amount',
            'MRR': 'monthly_recurring_revenue',
            'LTM': 'last_twelve_months_revenue',
            'Captação': 'fundraising_interest',
            'Tipo de Valuation': 'valuation_type',
            'Data de Valuation': 'valuation_date',
            
            # Payment Fields
            'paid': 'payment_status',
            'amount': 'payment_amount',
            'type': 'service_type',
            'date': 'payment_date',
            
            # GPT/Analytics Fields
            'createdAt': 'created_date',
            'name': 'user_name',
            'consent': 'consent_given',
            'questions': 'questions_asked',
            
            # Metrics Fields
            'totalValuations': 'total_valuations',
            'averageValuation': 'average_valuation',
            'averageRevenue': 'average_revenue',
            'totalPaidValuations': 'total_paid_valuations',
            'totalPaidValue': 'total_paid_value'
        }
    
    def _create_market_mapping(self) -> Dict[str, str]:
        """Map Portuguese market sectors to English"""
        return {
            'Edtech': 'Education Technology',
            'Fintech': 'Financial Technology',
            'Healthtech': 'Healthcare Technology',
            'Foodtech': 'Food Technology',
            'Martech': 'Marketing Technology',
            'Proptech': 'Property Technology',
            'Insurtech': 'Insurance Technology',
            'Agtech': 'Agriculture Technology',
            'Telecom': 'Telecommunications',
            'Entretenimento': 'Entertainment',
            'Outros': 'Other'
        }
    
    def _create_stage_mapping(self) -> Dict[str, str]:
        """Map Portuguese operational stages to English"""
        return {
            'Planejamento': 'Planning',
            'Validação': 'Validation',
            'Tração': 'Traction',
            'Operação': 'Operation',
            'Pré-Seed': 'Pre-Seed',
            'Seed': 'Seed',
            'Série A': 'Series A',
            'Série B': 'Series B',
            'Investimento Anjo': 'Angel Investment',
            'Aceleração': 'Acceleration',
            'Nenhuma das Anteriores': 'None of the Above'
        }
    
    def load_json_files(self) -> Dict[str, List[Dict]]:
        """Load all JSON files from the data directory"""
        data_files = {}
        
        # Find latest version of each file type
        file_patterns = [
            'crm-valuation-*.json',
            'payments-*.json',
            'paymentLinks-*.json',
            'senseMetrics-*.json',
            'crmMetrics-*.json',
            'opoderdoequitygpt-*.json'
        ]
        
        for pattern in file_patterns:
            files = list(self.data_dir.glob(pattern))
            if files:
                # Get the latest file (assuming timestamp in filename)
                latest_file = sorted(files)[-1]
                file_type = pattern.split('-')[0]
                
                try:
                    with open(latest_file, 'r', encoding='utf-8') as f:
                        data_files[file_type] = json.load(f)
                    print(f"✓ Loaded {len(data_files[file_type])} records from {latest_file.name}")
                except Exception as e:
                    print(f"✗ Error loading {latest_file}: {e}")
                    data_files[file_type] = []
        
        return data_files
    
    def clean_brazilian_date(self, date_str: str) -> Optional[datetime]:
        """Convert Brazilian date format (DD/MM/YYYY, HH:MM:SS) to datetime"""
        if not date_str or pd.isna(date_str):
            return None
        
        try:
            # Handle various Brazilian date formats
            date_str = str(date_str).strip()
            
            # Format: "13/02/2025, 09:35:59"
            if ', ' in date_str:
                date_part, time_part = date_str.split(', ')
                datetime_str = f"{date_part} {time_part}"
                return datetime.strptime(datetime_str, '%d/%m/%Y %H:%M:%S')
            
            # Format: "13/02/2025"
            elif '/' in date_str and len(date_str) == 10:
                return datetime.strptime(date_str, '%d/%m/%Y')
            
            # Unix timestamp
            elif date_str.isdigit():
                return datetime.fromtimestamp(int(date_str) / 1000)
            
            return None
        except ValueError:
            return None
    
    def clean_brazilian_phone(self, phone_str: str) -> Optional[str]:
        """Standardize Brazilian phone numbers to +55 (XX) XXXXX-XXXX format"""
        if not phone_str or pd.isna(phone_str):
            return None
        
        # Remove all non-digits
        digits = re.sub(r'\D', '', str(phone_str))
        
        # Brazilian mobile: 11 digits (country code + area code + number)
        if len(digits) == 11 and digits.startswith('55'):
            area_code = digits[2:4]
            number = digits[4:]
            return f"+55 ({area_code}) {number[:5]}-{number[5:]}"
        
        # Local format: 10 or 11 digits
        elif len(digits) in [10, 11]:
            if len(digits) == 10:
                area_code = digits[:2]
                number = digits[2:]
                return f"({area_code}) {number[:4]} {number[4:]}"
            else:
                area_code = digits[:2]
                number = digits[2:]
                return f"({area_code}) {number[:5]} {number[5:]}"
        
        return phone_str  # Return original if can't parse
    
    def clean_brazilian_currency(self, amount: Any) -> float:
        """Convert Brazilian currency values to float"""
        if pd.isna(amount) or amount is None:
            return 0.0
        
        if isinstance(amount, (int, float)):
            return float(amount)
        
        # Handle string currency values
        amount_str = str(amount).replace('R$', '').replace('.', '').replace(',', '.')
        amount_str = re.sub(r'[^\d.,]', '', amount_str)
        
        try:
            return float(amount_str)
        except ValueError:
            return 0.0
    
    def normalize_text(self, text: str) -> str:
        """Normalize Portuguese text (remove accents, proper casing)"""
        if not text or pd.isna(text):
            return ""
        
        # Remove accents
        text = unicodedata.normalize('NFD', str(text))
        text = ''.join(char for char in text if unicodedata.category(char) != 'Mn')
        
        # Clean up common issues
        text = text.strip()
        text = re.sub(r'\s+', ' ', text)  # Multiple spaces to single
        
        return text
    
    def validate_email(self, email: str) -> bool:
        """Validate email format"""
        if not email or pd.isna(email):
            return False
        
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(email_regex, str(email)))
    
    def parse_location(self, location_str: str) -> Tuple[str, str]:
        """Parse Brazilian city/state format: 'São Paulo/SP' -> ('São Paulo', 'SP')"""
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
        """Process CRM valuation data into companies dataframe"""
        if not crm_data:
            return pd.DataFrame()
        
        companies = []
        for record in crm_data:
            # Parse location
            city, state = self.parse_location(record.get('Cidade/Estado', ''))
            
            company = {
                'company_id': record.get('ID', ''),
                'company_name': self.normalize_text(record.get('Nome da Startup', '')),
                'website': record.get('Site', ''),
                'city': city,
                'state': state,
                'operational_stage': self.stage_translations.get(
                    record.get('Estágio Operacional', ''), 
                    record.get('Estágio Operacional', '')
                ),
                'business_model': record.get('Modelo de Negócio', ''),
                'market_sector': self.market_translations.get(
                    record.get('Mercado', ''), 
                    record.get('Mercado', '')
                ),
                'investment_stage': self.stage_translations.get(
                    record.get('Estágio de Investimento', ''), 
                    record.get('Estágio de Investimento', '')
                ),
                'valuation_amount': self.clean_brazilian_currency(record.get('Valuation', 0)),
                'monthly_recurring_revenue': self.clean_brazilian_currency(record.get('MRR', 0)),
                'last_twelve_months_revenue': self.clean_brazilian_currency(record.get('LTM', 0)),
                'fundraising_interest': record.get('Captação', ''),
                'valuation_type': record.get('Tipo de Valuation', ''),
                'valuation_date': self.clean_brazilian_date(record.get('Data de Valuation', '')),
                'created_date': datetime.now(),
                'data_source': 'crm-valuation'
            }
            companies.append(company)
        
        df = pd.DataFrame(companies)
        
        # Calculate data quality metrics
        total_records = len(df)
        complete_records = df.dropna(subset=['company_name', 'valuation_amount']).shape[0]
        
        self.quality_metrics['companies'] = DataQualityMetrics(
            total_records=total_records,
            complete_records=complete_records,
            duplicates_found=df.duplicated(subset=['company_name']).sum(),
            invalid_emails=0,  # No emails in companies table
            invalid_phones=0,  # No phones in companies table
            missing_critical_fields=total_records - complete_records,
            data_completeness_score=(complete_records / total_records * 100) if total_records > 0 else 0
        )
        
        return df
    
    def process_contacts_data(self, crm_data: List[Dict]) -> pd.DataFrame:
        """Process CRM data to extract contact information"""
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
                'role': 'Primary Contact',  # Assumed role
                'is_primary': True,
                'email_valid': self.validate_email(record.get('Email', '')),
                'created_date': self.clean_brazilian_date(record.get('Data de Valuation', '')),
                'data_source': 'crm-valuation'
            }
            contacts.append(contact)
        
        df = pd.DataFrame(contacts)
        
        # Calculate data quality metrics
        total_records = len(df)
        complete_records = df.dropna(subset=['contact_name', 'email']).shape[0]
        invalid_emails = (~df['email_valid']).sum()
        
        self.quality_metrics['contacts'] = DataQualityMetrics(
            total_records=total_records,
            complete_records=complete_records,
            duplicates_found=df.duplicated(subset=['email']).sum(),
            invalid_emails=invalid_emails,
            invalid_phones=df['phone'].isna().sum(),
            missing_critical_fields=total_records - complete_records,
            data_completeness_score=(complete_records / total_records * 100) if total_records > 0 else 0
        )
        
        return df
    
    def process_payments_data(self, payments_data: List[Dict]) -> pd.DataFrame:
        """Process payment data with nested valuation information"""
        if not payments_data:
            return pd.DataFrame()
        
        payments = []
        for record in payments_data:
            base_data = {
                'customer_email': record.get('email', record.get('id', '')),
                'analysis_paid': record.get('analysis.paid', False)
            }
            
            # Process nested valuation payments
            for key, value in record.items():
                if key.startswith('valuations.') and key.endswith('.date'):
                    valuation_id = key.split('.')[1]
                    
                    payment = {
                        'payment_id': f"payment_{valuation_id}",
                        'customer_email': base_data['customer_email'],
                        'valuation_id': valuation_id,
                        'payment_date': self.clean_brazilian_date(value),
                        'payment_amount': self.clean_brazilian_currency(
                            record.get(f'valuations.{valuation_id}.amount', 0)
                        ),
                        'payment_status': record.get(f'valuations.{valuation_id}.paid', False),
                        'service_type': record.get(f'valuations.{valuation_id}.type', ''),
                        'analysis_paid': base_data['analysis_paid'],
                        'created_date': datetime.now(),
                        'data_source': 'payments'
                    }
                    payments.append(payment)
        
        df = pd.DataFrame(payments)
        
        if not df.empty:
            # Calculate data quality metrics
            total_records = len(df)
            complete_records = df.dropna(subset=['customer_email', 'payment_amount']).shape[0]
            
            self.quality_metrics['payments'] = DataQualityMetrics(
                total_records=total_records,
                complete_records=complete_records,
                duplicates_found=df.duplicated(subset=['valuation_id']).sum(),
                invalid_emails=(~df['customer_email'].apply(self.validate_email)).sum(),
                invalid_phones=0,
                missing_critical_fields=total_records - complete_records,
                data_completeness_score=(complete_records / total_records * 100) if total_records > 0 else 0
            )
        
        return df
    
    def process_metrics_data(self, sense_data: List[Dict], crm_data: List[Dict]) -> pd.DataFrame:
        """Process sense and CRM metrics data"""
        metrics = []
        
        # Process Sense metrics
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
                    'report_date': datetime.now(),
                    'data_source': 'senseMetrics'
                }
                metrics.append(metric)
        
        # Process CRM metrics
        for record in crm_data:
            if record.get('id') == 'bigNumbers':
                metric = {
                    'service_type': 'CRM',
                    'total_valuations': record.get('totalValuations', 0),
                    'average_valuation': 0,  # Not available in CRM data
                    'average_revenue': 0,    # Not available in CRM data
                    'average_ebitda': 0,     # Not available in CRM data
                    'total_paid_valuations': record.get('totalPaidValuations', 0),
                    'total_paid_value': record.get('totalPaidValue', 0),
                    'report_date': datetime.now(),
                    'data_source': 'crmMetrics'
                }
                metrics.append(metric)
        
        return pd.DataFrame(metrics)
    
    def create_styled_workbook(self) -> Workbook:
        """Create a workbook with professional styling"""
        wb = Workbook()
        
        # Define styles
        header_style = NamedStyle(name="header_style")
        header_style.font = Font(bold=True, color="FFFFFF", size=12)
        header_style.fill = PatternFill("solid", fgColor="366092")
        header_style.alignment = Alignment(horizontal="center", vertical="center")
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
    
    def create_companies_worksheet(self, wb: Workbook, df: pd.DataFrame):
        """Create beautifully formatted Companies worksheet"""
        if df.empty:
            return
        
        ws = wb.create_sheet("Companies", 0)
        
        # Write data
        for r in dataframe_to_rows(df, index=False, header=True):
            ws.append(r)
        
        # Apply header styling
        for cell in ws[1]:
            cell.style = "header_style"
        
        # Apply data styling and formatting
        for row in ws.iter_rows(min_row=2):
            for cell in row:
                cell.style = "data_style"
                
                # Format currency columns
                if cell.column in [10, 11, 12]:  # valuation_amount, MRR, LTM
                    cell.number_format = 'R$ #,##0.00'
                
                # Format date columns
                if cell.column in [13, 14]:  # valuation_date, created_date
                    cell.number_format = 'DD/MM/YYYY HH:MM'
        
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
        
        # Add conditional formatting for valuation amounts
        ws.conditional_formatting.add(
            f'J2:J{len(df)+1}',
            ColorScaleRule(start_type='min', start_color='FFFFFF',
                          mid_type='percentile', mid_value=50, mid_color='FFFF99',
                          end_type='max', end_color='00FF00')
        )
        
        # Freeze panes
        ws.freeze_panes = 'A2'
    
    def create_contacts_worksheet(self, wb: Workbook, df: pd.DataFrame):
        """Create beautifully formatted Contacts worksheet"""
        if df.empty:
            return
        
        ws = wb.create_sheet("Contacts")
        
        # Write data
        for r in dataframe_to_rows(df, index=False, header=True):
            ws.append(r)
        
        # Apply styling
        for cell in ws[1]:
            cell.style = "header_style"
        
        for row in ws.iter_rows(min_row=2):
            for cell in row:
                cell.style = "data_style"
                
                # Format date columns
                if cell.column in [8, 9]:  # created_date
                    cell.number_format = 'DD/MM/YYYY HH:MM'
        
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
        
        # Add conditional formatting for email validation
        for row in range(2, len(df) + 2):
            if not df.iloc[row-2]['email_valid']:
                for col in range(1, 10):
                    ws.cell(row=row, column=col).fill = PatternFill("solid", fgColor="FFD7D7")
        
        ws.freeze_panes = 'A2'
    
    def create_payments_worksheet(self, wb: Workbook, df: pd.DataFrame):
        """Create beautifully formatted Payments worksheet"""
        if df.empty:
            return
        
        ws = wb.create_sheet("Payments")
        
        # Write data
        for r in dataframe_to_rows(df, index=False, header=True):
            ws.append(r)
        
        # Apply styling
        for cell in ws[1]:
            cell.style = "header_style"
        
        for row in ws.iter_rows(min_row=2):
            for cell in row:
                cell.style = "data_style"
                
                # Format currency columns
                if cell.column == 5:  # payment_amount
                    cell.number_format = 'R$ #,##0.00'
                
                # Format date columns
                if cell.column in [4, 9]:  # payment_date, created_date
                    cell.number_format = 'DD/MM/YYYY HH:MM'
        
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
        
        # Color-code payment status
        for row in range(2, len(df) + 2):
            if df.iloc[row-2]['payment_status']:
                for col in range(1, 11):
                    ws.cell(row=row, column=col).fill = PatternFill("solid", fgColor="D7FFD7")
            else:
                for col in range(1, 11):
                    ws.cell(row=row, column=col).fill = PatternFill("solid", fgColor="FFD7D7")
        
        ws.freeze_panes = 'A2'
    
    def create_analytics_worksheet(self, wb: Workbook, companies_df: pd.DataFrame, 
                                 payments_df: pd.DataFrame, metrics_df: pd.DataFrame):
        """Create analytics dashboard worksheet with charts and insights"""
        ws = wb.create_sheet("Analytics Dashboard")
        
        # Title
        ws['A1'] = "CRM Analytics Dashboard"
        ws['A1'].font = Font(bold=True, size=16, color="366092")
        ws.merge_cells('A1:F1')
        
        # Key metrics summary
        row = 3
        ws[f'A{row}'] = "KEY PERFORMANCE INDICATORS"
        ws[f'A{row}'].font = Font(bold=True, size=12)
        ws.merge_cells(f'A{row}:F{row}')
        
        row += 2
        if not companies_df.empty:
            ws[f'A{row}'] = "Total Companies:"
            ws[f'B{row}'] = len(companies_df)
            ws[f'C{row}'] = "Average Valuation:"
            ws[f'D{row}'] = companies_df['valuation_amount'].mean()
            ws[f'D{row}'].number_format = 'R$ #,##0.00'
            
            row += 1
            ws[f'A{row}'] = "Total MRR:"
            ws[f'B{row}'] = companies_df['monthly_recurring_revenue'].sum()
            ws[f'B{row}'].number_format = 'R$ #,##0.00'
            ws[f'C{row}'] = "Average MRR:"
            ws[f'D{row}'] = companies_df['monthly_recurring_revenue'].mean()
            ws[f'D{row}'].number_format = 'R$ #,##0.00'
        
        if not payments_df.empty:
            row += 1
            ws[f'A{row}'] = "Total Revenue:"
            ws[f'B{row}'] = payments_df['payment_amount'].sum()
            ws[f'B{row}'].number_format = 'R$ #,##0.00'
            ws[f'C{row}'] = "Payment Rate:"
            payment_rate = (payments_df['payment_status'].sum() / len(payments_df) * 100) if len(payments_df) > 0 else 0
            ws[f'D{row}'] = f"{payment_rate:.1f}%"
        
        # Market distribution
        row += 3
        if not companies_df.empty and 'market_sector' in companies_df.columns:
            ws[f'A{row}'] = "MARKET DISTRIBUTION"
            ws[f'A{row}'].font = Font(bold=True, size=12)
            ws.merge_cells(f'A{row}:F{row}')
            
            market_dist = companies_df['market_sector'].value_counts()
            row += 2
            for market, count in market_dist.head(10).items():
                ws[f'A{row}'] = market
                ws[f'B{row}'] = count
                ws[f'C{row}'] = f"{(count/len(companies_df)*100):.1f}%"
                row += 1
        
        # Operational stage distribution
        row += 2
        if not companies_df.empty and 'operational_stage' in companies_df.columns:
            ws[f'A{row}'] = "OPERATIONAL STAGE DISTRIBUTION"
            ws[f'A{row}'].font = Font(bold=True, size=12)
            ws.merge_cells(f'A{row}:F{row}')
            
            stage_dist = companies_df['operational_stage'].value_counts()
            row += 2
            for stage, count in stage_dist.items():
                ws[f'A{row}'] = stage
                ws[f'B{row}'] = count
                ws[f'C{row}'] = f"{(count/len(companies_df)*100):.1f}%"
                row += 1
        
        # Geographic distribution
        row += 2
        if not companies_df.empty and 'state' in companies_df.columns:
            ws[f'A{row}'] = "TOP STATES BY COMPANIES"
            ws[f'A{row}'].font = Font(bold=True, size=12)
            ws.merge_cells(f'A{row}:F{row}')
            
            state_dist = companies_df['state'].value_counts()
            row += 2
            for state, count in state_dist.head(10).items():
                if state:  # Skip empty states
                    ws[f'A{row}'] = state
                    ws[f'B{row}'] = count
                    ws[f'C{row}'] = f"{(count/len(companies_df)*100):.1f}%"
                    row += 1
        
        # Auto-adjust column widths
        for column_letter in ['A', 'B', 'C', 'D', 'E', 'F']:
            max_length = 0
            for cell in ws[column_letter]:
                try:
                    if hasattr(cell, 'value') and cell.value is not None:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 30)
            ws.column_dimensions[column_letter].width = adjusted_width
    
    def create_data_quality_worksheet(self, wb: Workbook):
        """Create data quality report worksheet"""
        ws = wb.create_sheet("Data Quality Report")
        
        # Title
        ws['A1'] = "Data Quality Assessment Report"
        ws['A1'].font = Font(bold=True, size=16, color="366092")
        ws.merge_cells('A1:G1')
        
        # Headers
        headers = ['Dataset', 'Total Records', 'Complete Records', 'Duplicates Found', 
                  'Invalid Emails', 'Invalid Phones', 'Completeness Score (%)']
        
        for col, header in enumerate(headers, 1):
            ws.cell(row=3, column=col, value=header)
            ws.cell(row=3, column=col).style = "header_style"
        
        # Data
        row = 4
        for dataset_name, metrics in self.quality_metrics.items():
            ws.cell(row=row, column=1, value=dataset_name.title())
            ws.cell(row=row, column=2, value=metrics.total_records)
            ws.cell(row=row, column=3, value=metrics.complete_records)
            ws.cell(row=row, column=4, value=metrics.duplicates_found)
            ws.cell(row=row, column=5, value=metrics.invalid_emails)
            ws.cell(row=row, column=6, value=metrics.invalid_phones)
            ws.cell(row=row, column=7, value=f"{metrics.data_completeness_score:.1f}%")
            
            # Color-code completeness score
            score_cell = ws.cell(row=row, column=7)
            if metrics.data_completeness_score >= 90:
                score_cell.fill = PatternFill("solid", fgColor="00FF00")  # Green
            elif metrics.data_completeness_score >= 70:
                score_cell.fill = PatternFill("solid", fgColor="FFFF00")  # Yellow
            else:
                score_cell.fill = PatternFill("solid", fgColor="FF0000")  # Red
            
            row += 1
        
        # Recommendations
        row += 2
        ws[f'A{row}'] = "RECOMMENDATIONS FOR DATA IMPROVEMENT:"
        ws[f'A{row}'].font = Font(bold=True, size=12)
        ws.merge_cells(f'A{row}:G{row}')
        
        recommendations = [
            "1. Implement email validation at data entry point",
            "2. Standardize phone number format collection",
            "3. Make key fields mandatory in forms",
            "4. Set up automated duplicate detection",
            "5. Regular data cleaning and validation processes",
            "6. Training for data entry personnel",
            "7. Implement data quality monitoring dashboard"
        ]
        
        for i, rec in enumerate(recommendations, 1):
            ws[f'A{row + i}'] = rec
        
        # Auto-adjust column widths
        for column_letter in ['A', 'B', 'C', 'D', 'E', 'F', 'G']:
            max_length = 0
            for cell in ws[column_letter]:
                try:
                    if hasattr(cell, 'value') and cell.value is not None:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 40)
            ws.column_dimensions[column_letter].width = adjusted_width
    
    def create_field_mapping_worksheet(self, wb: Workbook):
        """Create Portuguese-English field mapping reference"""
        ws = wb.create_sheet("Field Mapping Reference")
        
        # Title
        ws['A1'] = "Portuguese to English Field Translation Reference"
        ws['A1'].font = Font(bold=True, size=16, color="366092")
        ws.merge_cells('A1:D1')
        
        # Headers
        ws['A3'] = "Portuguese Field Name"
        ws['B3'] = "English Field Name"
        ws['C3'] = "Category"
        ws['D3'] = "Description"
        
        for cell in ws[3]:
            cell.style = "header_style"
        
        # Field mappings with categories
        mappings = [
            ("ID", "company_id", "Identifier", "Unique company identifier"),
            ("Nome da Startup", "company_name", "Company", "Startup company name"),
            ("Site", "website", "Company", "Company website URL"),
            ("Cidade/Estado", "location", "Geography", "City and state location"),
            ("Estágio Operacional", "operational_stage", "Business", "Current operational stage"),
            ("Modelo de Negócio", "business_model", "Business", "Business model type"),
            ("Mercado", "market_sector", "Business", "Market sector/industry"),
            ("Nome do Respondente", "contact_name", "Contact", "Primary contact person name"),
            ("Email", "email", "Contact", "Contact email address"),
            ("Telefone", "phone", "Contact", "Contact phone number"),
            ("Valuation", "valuation_amount", "Financial", "Company valuation amount"),
            ("MRR", "monthly_recurring_revenue", "Financial", "Monthly recurring revenue"),
            ("LTM", "last_twelve_months_revenue", "Financial", "Last 12 months revenue"),
            ("Captação", "fundraising_interest", "Investment", "Fundraising interest status"),
            ("Data de Valuation", "valuation_date", "Temporal", "Date of valuation assessment")
        ]
        
        row = 4
        for pt_field, en_field, category, description in mappings:
            ws.cell(row=row, column=1, value=pt_field)
            ws.cell(row=row, column=2, value=en_field)
            ws.cell(row=row, column=3, value=category)
            ws.cell(row=row, column=4, value=description)
            row += 1
        
        # Auto-adjust column widths
        for column_letter in ['A', 'B', 'C', 'D']:
            max_length = 0
            for cell in ws[column_letter]:
                try:
                    if hasattr(cell, 'value') and cell.value is not None:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)
            ws.column_dimensions[column_letter].width = adjusted_width
    
    def run_etl_pipeline(self) -> str:
        """Execute the complete ETL pipeline"""
        print("🚀 Starting CRM Data ETL Pipeline...")
        print("=" * 50)
        
        # Load data
        print("📂 Loading data files...")
        data_files = self.load_json_files()
        
        if not data_files:
            print("❌ No data files found!")
            return None
        
        # Process data
        print("\n🔄 Processing data...")
        
        companies_df = self.process_companies_data(data_files.get('crm', []))
        print(f"✓ Processed {len(companies_df)} companies")
        
        contacts_df = self.process_contacts_data(data_files.get('crm', []))
        print(f"✓ Processed {len(contacts_df)} contacts")
        
        payments_df = self.process_payments_data(data_files.get('payments', []))
        print(f"✓ Processed {len(payments_df)} payments")
        
        metrics_df = self.process_metrics_data(
            data_files.get('senseMetrics', []), 
            data_files.get('crmMetrics', [])
        )
        print(f"✓ Processed {len(metrics_df)} metric records")
        
        # Create Excel workbook
        print("\n📊 Creating Excel workbook...")
        wb = self.create_styled_workbook()
        
        # Remove default sheet
        if "Sheet" in wb.sheetnames:
            wb.remove(wb["Sheet"])
        
        # Create worksheets
        self.create_companies_worksheet(wb, companies_df)
        print("✓ Created Companies worksheet")
        
        self.create_contacts_worksheet(wb, contacts_df)
        print("✓ Created Contacts worksheet")
        
        self.create_payments_worksheet(wb, payments_df)
        print("✓ Created Payments worksheet")
        
        self.create_analytics_worksheet(wb, companies_df, payments_df, metrics_df)
        print("✓ Created Analytics Dashboard")
        
        self.create_data_quality_worksheet(wb)
        print("✓ Created Data Quality Report")
        
        self.create_field_mapping_worksheet(wb)
        print("✓ Created Field Mapping Reference")
        
        # Save workbook
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"CRM_Data_Complete_ETL_{timestamp}.xlsx"
        filepath = self.data_dir / filename
        
        wb.save(filepath)
        print(f"\n✅ ETL Complete! File saved as: {filename}")
        print(f"📍 Location: {filepath}")
        
        # Print summary
        print("\n📈 DATA SUMMARY:")
        print("-" * 30)
        print(f"Companies: {len(companies_df)}")
        print(f"Contacts: {len(contacts_df)}")
        print(f"Payments: {len(payments_df)}")
        print(f"Service Metrics: {len(metrics_df)}")
        
        print("\n💎 DATA QUALITY SCORES:")
        print("-" * 30)
        for dataset, metrics in self.quality_metrics.items():
            print(f"{dataset.title()}: {metrics.data_completeness_score:.1f}%")
        
        return str(filepath)


def main():
    """Main execution function"""
    # Initialize processor
    processor = CRMDataProcessor("exports")
    
    # Run ETL pipeline
    result_file = processor.run_etl_pipeline()
    
    if result_file:
        print(f"\n🎉 Success! Your beautifully organized CRM data is ready!")
        print(f"📂 Open: {result_file}")
    else:
        print("❌ ETL pipeline failed!")


if __name__ == "__main__":
    main()
