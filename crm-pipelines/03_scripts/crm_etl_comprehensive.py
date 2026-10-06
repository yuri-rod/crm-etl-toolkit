#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comprehensive CRM Data ETL Processor
=====================================
Enhanced ETL pipeline that includes ALL data sources:
- CRM Valuation data (25,484 records)
- Separate Valuation data (2,000 records) - NEW
- GPT Interactions (25 records) - NEW
- Payment Links - NEW
- All payment and metric data

Features:
- Includes previously missing datasets
- Portuguese to English field translation
- Brazilian date/currency/phone formatting (dd/mm/yyyy, 24-hour)
- Data validation and cleaning
- Professional Excel formatting with charts
- Complete data consolidation report

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

class ComprehensiveCRMProcessor:
    """Enhanced ETL processor including all data sources"""
    
    def __init__(self, data_dir: str = "."):
        self.data_dir = Path(data_dir)
        self.field_translations = self._create_field_mapping()
        self.market_translations = self._create_market_mapping()
        self.stage_translations = self._create_stage_mapping()
        self.quality_metrics = {}
        self.consolidation_report = []
        
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
    
    def load_all_json_files(self) -> Dict[str, List[Dict]]:
        """Load ALL JSON files from the data directory"""
        data_files = {}
        
        # CRM Valuation - Merge all versions, remove duplicates
        crm_files = list(self.data_dir.glob("crm-valuation-*.json"))
        all_crm_data = []
        crm_ids = set()
        
        for f in crm_files:
            try:
                with open(f, 'r', encoding='utf-8') as file:
                    data = json.load(file)
                    for record in data:
                        if record.get('ID') not in crm_ids:
                            all_crm_data.append(record)
                            crm_ids.add(record.get('ID'))
                print(f"✓ Loaded CRM data from {f.name}")
            except Exception as e:
                print(f"✗ Error loading {f}: {e}")
        
        data_files['crm'] = all_crm_data
        print(f"  → Total unique CRM records: {len(all_crm_data)}")
        
        # Separate Valuation data (NEW!)
        valuation_files = list(self.data_dir.glob("valuation-*.json"))
        valuation_data = []
        for f in valuation_files:
            try:
                with open(f, 'r', encoding='utf-8') as file:
                    data = json.load(file)
                    valuation_data.extend(data)
                print(f"✓ Loaded valuation data from {f.name}: {len(data)} records")
            except Exception as e:
                print(f"✗ Error loading {f}: {e}")
        
        data_files['valuation-detailed'] = valuation_data
        print(f"  → Total valuation records: {len(valuation_data)}")
        
        # GPT Interactions (NEW!)
        gpt_files = list(self.data_dir.glob("opoderdoequitygpt-*.json"))
        if gpt_files:
            try:
                with open(gpt_files[-1], 'r', encoding='utf-8') as f:
                    data_files['gpt-interactions'] = json.load(f)
                print(f"✓ Loaded {len(data_files['gpt-interactions'])} GPT interaction records")
            except Exception as e:
                print(f"✗ Error loading GPT data: {e}")
        
        # Payments
        payments_files = list(self.data_dir.glob("payments-*.json"))
        if payments_files:
            try:
                with open(payments_files[-1], 'r', encoding='utf-8') as f:
                    data_files['payments'] = json.load(f)
                print(f"✓ Loaded {len(data_files['payments'])} payment records")
            except Exception as e:
                print(f"✗ Error loading payments: {e}")
        
        # Payment Links (NEW!)
        links_files = list(self.data_dir.glob("paymentLinks-*.json"))
        if links_files:
            try:
                with open(links_files[-1], 'r', encoding='utf-8') as f:
                    data_files['paymentLinks'] = json.load(f)
                print(f"✓ Loaded {len(data_files['paymentLinks'])} payment link records")
            except Exception as e:
                print(f"✗ Error loading payment links: {e}")
        
        # Metrics
        sense_files = list(self.data_dir.glob("senseMetrics-*.json"))
        if sense_files:
            try:
                with open(sense_files[-1], 'r', encoding='utf-8') as f:
                    data_files['senseMetrics'] = json.load(f)
                print(f"✓ Loaded {len(data_files['senseMetrics'])} sense metric records")
            except Exception as e:
                print(f"✗ Error loading sense metrics: {e}")
        
        crm_files = list(self.data_dir.glob("crmMetrics-*.json"))
        if crm_files:
            try:
                with open(crm_files[-1], 'r', encoding='utf-8') as f:
                    data_files['crmMetrics'] = json.load(f)
                print(f"✓ Loaded {len(data_files['crmMetrics'])} CRM metric records")
            except Exception as e:
                print(f"✗ Error loading CRM metrics: {e}")
        
        return data_files
    
    def clean_brazilian_date(self, date_str: str) -> Optional[str]:
        """Convert Brazilian date format to dd/mm/yyyy HH:MM format"""
        if not date_str or pd.isna(date_str):
            return None
        
        try:
            date_str = str(date_str).strip()
            
            # Handle various date formats
            if ', ' in date_str:
                # Format: "13/02/2025, 09:35:59"
                date_part, time_part = date_str.split(', ')
                dt = datetime.strptime(f"{date_part} {time_part}", '%d/%m/%Y %H:%M:%S')
            elif '/' in date_str and len(date_str) == 10:
                # Format: "13/02/2025"
                dt = datetime.strptime(date_str, '%d/%m/%Y')
            elif date_str.isdigit():
                # Unix timestamp
                dt = datetime.fromtimestamp(int(date_str) / 1000)
            else:
                return date_str
            
            # Format as dd/mm/yyyy HH:MM (24-hour)
            return dt.strftime('%d/%m/%Y %H:%M')
        except:
            return date_str
    
    def clean_brazilian_phone(self, phone_str: str) -> Optional[str]:
        """Standardize Brazilian phone numbers"""
        if not phone_str or pd.isna(phone_str):
            return None
        
        digits = re.sub(r'\D', '', str(phone_str))
        
        if len(digits) == 11 and digits.startswith('55'):
            area_code = digits[2:4]
            number = digits[4:]
            return f"+55 ({area_code}) {number[:5]}-{number[5:]}"
        elif len(digits) in [10, 11]:
            if len(digits) == 10:
                area_code = digits[:2]
                number = digits[2:]
                return f"({area_code}) {number[:4]}-{number[4:]}"
            else:
                area_code = digits[:2]
                number = digits[2:]
                return f"({area_code}) {number[:5]}-{number[5:]}"
        
        return phone_str
    
    def clean_brazilian_currency(self, amount: Any) -> float:
        """Convert Brazilian currency values to float"""
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
        """Normalize Portuguese text"""
        if not text or pd.isna(text):
            return ""
        
        text = unicodedata.normalize('NFD', str(text))
        text = ''.join(char for char in text if unicodedata.category(char) != 'Mn')
        text = text.strip()
        text = re.sub(r'\s+', ' ', text)
        
        return text
    
    def validate_email(self, email: str) -> bool:
        """Validate email format"""
        if not email or pd.isna(email):
            return False
        
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(email_regex, str(email)))
    
    def parse_location(self, location_str: str) -> Tuple[str, str]:
        """Parse Brazilian city/state format"""
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
                'created_date': datetime.now().strftime('%d/%m/%Y %H:%M'),
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
            invalid_emails=0,
            invalid_phones=0,
            missing_critical_fields=total_records - complete_records,
            data_completeness_score=(complete_records / total_records * 100) if total_records > 0 else 0
        )
        
        self.consolidation_report.append(f"Companies: Processed {total_records} records from CRM data")
        
        return df
    
    def process_detailed_valuations(self, valuation_data: List[Dict]) -> pd.DataFrame:
        """Process separate detailed valuation data (NEW!)"""
        if not valuation_data:
            return pd.DataFrame()
        
        valuations = []
        for record in valuation_data:
            # Note: The JSON has flat structure with dots in keys, not nested objects
            # Extract city and state from flat fields
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
                
                # Financial data - using flat structure with dots in keys
                'valuation_amount': self.clean_brazilian_currency(record.get('valuation', 0)),
                'valuation_type': record.get('valuationType', ''),
                'planned_revenue': self.clean_brazilian_currency(record.get('financials.currentPlannedRevenue', 0)),
                'planned_ebitda': self.clean_brazilian_currency(record.get('financials.currentPlannedEBITDA', 0)),
                'planned_investments': self.clean_brazilian_currency(record.get('financials.currentPlannedInvestments', 0)),
                'yearly_investments': self.clean_brazilian_currency(record.get('financials.yearlyPlannedInvestments', 0)),
                'current_debt': self.clean_brazilian_currency(record.get('financials.currentDebt', 0)),
                'fixed_assets': self.clean_brazilian_currency(record.get('financials.fixedAssets', 0)),
                'stock_cash_values': self.clean_brazilian_currency(record.get('financials.stockAndCashValues', 0)),
                
                # Timeframes - also flat structure
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
        
        # Data quality metrics
        total_records = len(df)
        complete_records = df.dropna(subset=['company_name', 'valuation_amount']).shape[0]
        invalid_emails = (~df['email'].apply(self.validate_email)).sum()
        
        self.quality_metrics['detailed-valuations'] = DataQualityMetrics(
            total_records=total_records,
            complete_records=complete_records,
            duplicates_found=df.duplicated(subset=['email']).sum(),
            invalid_emails=invalid_emails,
            invalid_phones=df['whatsapp'].isna().sum(),
            missing_critical_fields=total_records - complete_records,
            data_completeness_score=(complete_records / total_records * 100) if total_records > 0 else 0
        )
        
        self.consolidation_report.append(f"Detailed Valuations: Added {total_records} NEW records from separate valuation data")
        
        return df
    
    def process_gpt_interactions(self, gpt_data: List[Dict]) -> pd.DataFrame:
        """Process GPT interaction data (NEW!)"""
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
        
        # Data quality metrics
        total_records = len(df)
        complete_records = df.dropna(subset=['user_name', 'email']).shape[0]
        invalid_emails = (~df['email'].apply(self.validate_email)).sum()
        
        self.quality_metrics['gpt-interactions'] = DataQualityMetrics(
            total_records=total_records,
            complete_records=complete_records,
            duplicates_found=df.duplicated(subset=['email']).sum(),
            invalid_emails=invalid_emails,
            invalid_phones=0,
            missing_critical_fields=total_records - complete_records,
            data_completeness_score=(complete_records / total_records * 100) if total_records > 0 else 0
        )
        
        self.consolidation_report.append(f"GPT Interactions: Added {total_records} NEW interaction records")
        
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
                'role': 'Primary Contact',
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
        
        self.consolidation_report.append(f"Contacts: Processed {total_records} records from CRM data")
        
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
                        'created_date': datetime.now().strftime('%d/%m/%Y %H:%M'),
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
            
            self.consolidation_report.append(f"Payments: Processed {total_records} payment records")
        
        return df
    
    def process_payment_links(self, links_data: List[Dict]) -> pd.DataFrame:
        """Process payment links data (NEW!)"""
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
        self.consolidation_report.append(f"Payment Links: Added {len(df)} NEW payment link records")
        
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
                    'report_date': datetime.now().strftime('%d/%m/%Y %H:%M'),
                    'data_source': 'senseMetrics'
                }
                metrics.append(metric)
        
        # Process CRM metrics
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
        self.consolidation_report.append(f"Metrics: Processed {len(df)} metric records")
        
        return df
    
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
                
                # Format date columns (dd/mm/yyyy HH:MM)
                if cell.column in [14, 16]:  # valuation_date, created_date
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
    
    def create_detailed_valuations_worksheet(self, wb: Workbook, df: pd.DataFrame):
        """Create worksheet for detailed valuation data (NEW!)"""
        if df.empty:
            return
        
        ws = wb.create_sheet("Detailed Valuations")
        
        # Write data
        for r in dataframe_to_rows(df, index=False, header=True):
            ws.append(r)
        
        # Apply header styling
        for cell in ws[1]:
            cell.style = "header_style"
        
        # Apply data styling
        for row in ws.iter_rows(min_row=2):
            for cell in row:
                cell.style = "data_style"
                
                # Format currency columns
                currency_cols = [12, 13, 14, 15, 16, 17, 18, 19]  # Financial columns
                if cell.column in currency_cols:
                    cell.number_format = 'R$ #,##0.00'
                
                # Format date columns
                date_cols = [10, 25, 26]  # foundation_date, timestamp, created_date
                if cell.column in date_cols:
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
        
        ws.freeze_panes = 'A2'
    
    def create_gpt_interactions_worksheet(self, wb: Workbook, df: pd.DataFrame):
        """Create worksheet for GPT interactions (NEW!)"""
        if df.empty:
            return
        
        ws = wb.create_sheet("GPT Interactions")
        
        # Write data
        for r in dataframe_to_rows(df, index=False, header=True):
            ws.append(r)
        
        # Apply header styling
        for cell in ws[1]:
            cell.style = "header_style"
        
        # Apply data styling
        for row in ws.iter_rows(min_row=2):
            for cell in row:
                cell.style = "data_style"
                
                # Format date column
                if cell.column == 4:  # created_date
                    cell.number_format = 'DD/MM/YYYY HH:MM'
                
                # Highlight consent status
                if cell.column == 6:  # consent_given
                    if cell.value:
                        cell.fill = PatternFill("solid", fgColor="D7FFD7")
                    else:
                        cell.fill = PatternFill("solid", fgColor="FFD7D7")
        
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
                if cell.column == 9:  # created_date
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
            if row <= len(df) + 1 and not df.iloc[row-2]['email_valid']:
                for col in range(1, 11):
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
            if row <= len(df) + 1:
                if df.iloc[row-2]['payment_status']:
                    for col in range(1, 11):
                        ws.cell(row=row, column=col).fill = PatternFill("solid", fgColor="D7FFD7")
                else:
                    for col in range(1, 11):
                        ws.cell(row=row, column=col).fill = PatternFill("solid", fgColor="FFD7D7")
        
        ws.freeze_panes = 'A2'
    
    def create_payment_links_worksheet(self, wb: Workbook, df: pd.DataFrame):
        """Create worksheet for payment links (NEW!)"""
        if df.empty:
            return
        
        ws = wb.create_sheet("Payment Links")
        
        # Write data
        for r in dataframe_to_rows(df, index=False, header=True):
            ws.append(r)
        
        # Apply styling
        for cell in ws[1]:
            cell.style = "header_style"
        
        for row in ws.iter_rows(min_row=2):
            for cell in row:
                cell.style = "data_style"
                
                # Format date column
                if cell.column == 5:  # created_date
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
        
        ws.freeze_panes = 'A2'
    
    def create_consolidation_report_worksheet(self, wb: Workbook):
        """Create consolidation report worksheet (NEW!)"""
        ws = wb.create_sheet("Consolidation Report")
        
        # Title
        ws['A1'] = "Data Consolidation Report"
        ws['A1'].font = Font(bold=True, size=16, color="366092")
        ws.merge_cells('A1:D1')
        
        ws['A3'] = datetime.now().strftime('Generated: %d/%m/%Y %H:%M')
        ws['A3'].font = Font(italic=True)
        
        # Data Sources Summary
        ws['A5'] = "DATA SOURCES PROCESSED:"
        ws['A5'].font = Font(bold=True, size=12)
        
        row = 7
        for report_line in self.consolidation_report:
            ws[f'A{row}'] = f"✓ {report_line}"
            row += 1
        
        # New Data Added
        row += 2
        ws[f'A{row}'] = "NEW DATA ADDED (Not in Original Excel):"
        ws[f'A{row}'].font = Font(bold=True, size=12, color="00AA00")
        
        row += 2
        new_data_items = [
            "• Detailed Valuations: 2,000 records with comprehensive financial data",
            "• GPT Interactions: 25 user interaction records",
            "• Payment Links: 3 payment link records",
            "• Enhanced date/time formatting: dd/mm/yyyy HH:MM (24-hour)"
        ]
        
        for item in new_data_items:
            ws[f'A{row}'] = item
            ws[f'A{row}'].font = Font(color="00AA00")
            row += 1
        
        # Data Quality Summary
        row += 2
        ws[f'A{row}'] = "DATA QUALITY SUMMARY:"
        ws[f'A{row}'].font = Font(bold=True, size=12)
        
        row += 2
        ws[f'A{row}'] = "Dataset"
        ws[f'B{row}'] = "Records"
        ws[f'C{row}'] = "Completeness"
        ws[f'D{row}'] = "Status"
        
        for cell in [ws[f'A{row}'], ws[f'B{row}'], ws[f'C{row}'], ws[f'D{row}']]:
            cell.font = Font(bold=True)
            cell.fill = PatternFill("solid", fgColor="DDDDDD")
        
        row += 1
        for dataset, metrics in self.quality_metrics.items():
            ws[f'A{row}'] = dataset.replace('-', ' ').title()
            ws[f'B{row}'] = metrics.total_records
            ws[f'C{row}'] = f"{metrics.data_completeness_score:.1f}%"
            
            status_cell = ws[f'D{row}']
            if metrics.data_completeness_score >= 90:
                status_cell.value = "Excellent"
                status_cell.fill = PatternFill("solid", fgColor="00FF00")
            elif metrics.data_completeness_score >= 70:
                status_cell.value = "Good"
                status_cell.fill = PatternFill("solid", fgColor="FFFF00")
            else:
                status_cell.value = "Needs Review"
                status_cell.fill = PatternFill("solid", fgColor="FF0000")
            
            row += 1
        
        # Auto-adjust column widths
        for column_letter in ['A', 'B', 'C', 'D']:
            max_length = 30
            ws.column_dimensions[column_letter].width = max_length
    
    def create_analytics_worksheet(self, wb: Workbook, companies_df: pd.DataFrame, 
                                 payments_df: pd.DataFrame, valuations_df: pd.DataFrame):
        """Create enhanced analytics dashboard"""
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
            ws[f'A{row}'] = "Total Companies (CRM):"
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
        
        # New valuations data
        if not valuations_df.empty:
            row += 2
            ws[f'A{row}'] = "DETAILED VALUATIONS (NEW):"
            ws[f'A{row}'].font = Font(bold=True, color="00AA00")
            
            row += 1
            ws[f'A{row}'] = "Total Records:"
            ws[f'B{row}'] = len(valuations_df)
            ws[f'C{row}'] = "Unique Companies:"
            ws[f'D{row}'] = valuations_df['company_name'].nunique()
            
            row += 1
            ws[f'A{row}'] = "Avg Valuation:"
            ws[f'B{row}'] = valuations_df['valuation_amount'].mean()
            ws[f'B{row}'].number_format = 'R$ #,##0.00'
            ws[f'C{row}'] = "Total Planned Revenue:"
            ws[f'D{row}'] = valuations_df['planned_revenue'].sum()
            ws[f'D{row}'].number_format = 'R$ #,##0.00'
        
        if not payments_df.empty:
            row += 2
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
        
        # Geographic distribution
        row += 2
        if not companies_df.empty and 'state' in companies_df.columns:
            ws[f'A{row}'] = "TOP STATES BY COMPANIES"
            ws[f'A{row}'].font = Font(bold=True, size=12)
            ws.merge_cells(f'A{row}:F{row}')
            
            state_dist = companies_df['state'].value_counts()
            row += 2
            for state, count in state_dist.head(10).items():
                if state:
                    ws[f'A{row}'] = state
                    ws[f'B{row}'] = count
                    ws[f'C{row}'] = f"{(count/len(companies_df)*100):.1f}%"
                    row += 1
        
        # Auto-adjust column widths
        for column_letter in ['A', 'B', 'C', 'D', 'E', 'F']:
            ws.column_dimensions[column_letter].width = 25
    
    def create_data_quality_worksheet(self, wb: Workbook):
        """Create comprehensive data quality report"""
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
            ws.cell(row=row, column=1, value=dataset_name.replace('-', ' ').title())
            ws.cell(row=row, column=2, value=metrics.total_records)
            ws.cell(row=row, column=3, value=metrics.complete_records)
            ws.cell(row=row, column=4, value=metrics.duplicates_found)
            ws.cell(row=row, column=5, value=metrics.invalid_emails)
            ws.cell(row=row, column=6, value=metrics.invalid_phones)
            ws.cell(row=row, column=7, value=f"{metrics.data_completeness_score:.1f}%")
            
            # Color-code completeness score
            score_cell = ws.cell(row=row, column=7)
            if metrics.data_completeness_score >= 90:
                score_cell.fill = PatternFill("solid", fgColor="00FF00")
            elif metrics.data_completeness_score >= 70:
                score_cell.fill = PatternFill("solid", fgColor="FFFF00")
            else:
                score_cell.fill = PatternFill("solid", fgColor="FF0000")
            
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
            "7. Implement data quality monitoring dashboard",
            "8. Integrate all data sources into unified system"
        ]
        
        for i, rec in enumerate(recommendations, 1):
            ws[f'A{row + i}'] = rec
        
        # Auto-adjust column widths
        for column_letter in ['A', 'B', 'C', 'D', 'E', 'F', 'G']:
            ws.column_dimensions[column_letter].width = 25
    
    def run_comprehensive_etl(self) -> str:
        """Execute the comprehensive ETL pipeline with ALL data sources"""
        print("\n🚀 Starting COMPREHENSIVE CRM Data ETL Pipeline...")
        print("="*60)
        
        # Load all data sources
        print("\n📂 Loading ALL data sources...")
        data_files = self.load_all_json_files()
        
        if not data_files:
            print("❌ No data files found!")
            return None
        
        # Process all data
        print("\n🔄 Processing data...")
        
        # Original CRM data
        companies_df = self.process_companies_data(data_files.get('crm', []))
        print(f"✓ Processed {len(companies_df)} companies from CRM")
        
        contacts_df = self.process_contacts_data(data_files.get('crm', []))
        print(f"✓ Processed {len(contacts_df)} contacts")
        
        # NEW: Detailed valuation data
        valuations_df = self.process_detailed_valuations(data_files.get('valuation-detailed', []))
        print(f"✓ Processed {len(valuations_df)} detailed valuations (NEW!)")
        
        # NEW: GPT interactions
        gpt_df = self.process_gpt_interactions(data_files.get('gpt-interactions', []))
        print(f"✓ Processed {len(gpt_df)} GPT interactions (NEW!)")
        
        # Payments
        payments_df = self.process_payments_data(data_files.get('payments', []))
        print(f"✓ Processed {len(payments_df)} payments")
        
        # NEW: Payment Links
        links_df = self.process_payment_links(data_files.get('paymentLinks', []))
        print(f"✓ Processed {len(links_df)} payment links (NEW!)")
        
        # Metrics
        metrics_df = self.process_metrics_data(
            data_files.get('senseMetrics', []), 
            data_files.get('crmMetrics', [])
        )
        print(f"✓ Processed {len(metrics_df)} metric records")
        
        # Create Excel workbook
        print("\n📊 Creating comprehensive Excel workbook...")
        wb = self.create_styled_workbook()
        
        # Remove default sheet
        if "Sheet" in wb.sheetnames:
            wb.remove(wb["Sheet"])
        
        # Create all worksheets
        self.create_companies_worksheet(wb, companies_df)
        print("✓ Created Companies worksheet")
        
        self.create_detailed_valuations_worksheet(wb, valuations_df)
        print("✓ Created Detailed Valuations worksheet (NEW!)")
        
        self.create_gpt_interactions_worksheet(wb, gpt_df)
        print("✓ Created GPT Interactions worksheet (NEW!)")
        
        self.create_contacts_worksheet(wb, contacts_df)
        print("✓ Created Contacts worksheet")
        
        self.create_payments_worksheet(wb, payments_df)
        print("✓ Created Payments worksheet")
        
        self.create_payment_links_worksheet(wb, links_df)
        print("✓ Created Payment Links worksheet (NEW!)")
        
        self.create_analytics_worksheet(wb, companies_df, payments_df, valuations_df)
        print("✓ Created Enhanced Analytics Dashboard")
        
        self.create_data_quality_worksheet(wb)
        print("✓ Created Data Quality Report")
        
        self.create_consolidation_report_worksheet(wb)
        print("✓ Created Consolidation Report (NEW!)")
        
        # Save workbook
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"CRM_Data_COMPREHENSIVE_ETL_{timestamp}.xlsx"
        filepath = self.data_dir / filename
        
        wb.save(filepath)
        print(f"\n✅ COMPREHENSIVE ETL Complete! File saved as: {filename}")
        print(f"📍 Location: {filepath}")
        
        # Print summary
        print("\n" + "="*60)
        print("📈 COMPREHENSIVE DATA SUMMARY:")
        print("="*60)
        print(f"Companies (CRM): {len(companies_df)}")
        print(f"Detailed Valuations (NEW): {len(valuations_df)}")
        print(f"GPT Interactions (NEW): {len(gpt_df)}")
        print(f"Contacts: {len(contacts_df)}")
        print(f"Payments: {len(payments_df)}")
        print(f"Payment Links (NEW): {links_df}")
        print(f"Service Metrics: {len(metrics_df)}")
        
        print("\n💎 DATA QUALITY SCORES:")
        print("-"*30)
        for dataset, metrics in self.quality_metrics.items():
            print(f"{dataset.replace('-', ' ').title()}: {metrics.data_completeness_score:.1f}%")
        
        print("\n🆕 NEW DATA INCLUDED:")
        print("-"*30)
        print(f"• {len(valuations_df)} detailed valuation records")
        print(f"• {len(gpt_df)} GPT interaction records")
        print(f"• {len(links_df)} payment link records")
        print("• Enhanced date/time formatting (dd/mm/yyyy HH:MM)")
        print("• Comprehensive consolidation report")
        
        return str(filepath)


def main():
    """Main execution function"""
    # Initialize processor
    processor = ComprehensiveCRMProcessor(".")
    
    # Run comprehensive ETL pipeline
    result_file = processor.run_comprehensive_etl()
    
    if result_file:
        print(f"\n🎉 Success! Your COMPREHENSIVE CRM data is ready!")
        print(f"📂 Open: {result_file}")
        print("\n⚠️  This file includes ALL data sources, including previously missing:")
        print("   • 2,000 detailed valuation records")
        print("   • 25 GPT interaction records")
        print("   • Payment links data")
        print("   • Complete consolidation report")
    else:
        print("❌ ETL pipeline failed!")


if __name__ == "__main__":
    main()
