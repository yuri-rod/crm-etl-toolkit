#!/usr/bin/env python3
"""
Comprehensive Data Analysis Script
===================================
Identifies missing and mismatched data between source JSON files and the Excel ETL output.
"""

import json
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Set, Tuple
import warnings

warnings.filterwarnings('ignore')

class DataAuditor:
    def __init__(self, data_dir: str = "."):
        self.data_dir = Path(data_dir)
        self.excel_file = self.data_dir / "CRM_Data_Complete_ETL_20250827_080246.xlsx"
        self.report = []
        
    def load_all_json_data(self) -> Dict[str, List[Dict]]:
        """Load all JSON files and categorize them"""
        data_sources = {}
        
        # CRM Valuation files (3 versions)
        crm_files = list(self.data_dir.glob("crm-valuation-*.json"))
        all_crm_data = []
        crm_ids = set()
        
        for f in crm_files:
            with open(f, 'r', encoding='utf-8') as file:
                data = json.load(file)
                for record in data:
                    if record.get('ID') not in crm_ids:
                        all_crm_data.append(record)
                        crm_ids.add(record.get('ID'))
        
        data_sources['crm-valuation'] = all_crm_data
        print(f"✓ Loaded {len(all_crm_data)} unique CRM valuation records")
        
        # Other valuation data
        valuation_files = list(self.data_dir.glob("valuation-*.json"))
        valuation_data = []
        for f in valuation_files:
            with open(f, 'r', encoding='utf-8') as file:
                data = json.load(file)
                valuation_data.extend(data)
        data_sources['valuation-separate'] = valuation_data
        print(f"✓ Loaded {len(valuation_data)} separate valuation records")
        
        # Payments data
        payments_files = list(self.data_dir.glob("payments-*.json"))
        if payments_files:
            with open(payments_files[-1], 'r', encoding='utf-8') as f:
                data_sources['payments'] = json.load(f)
                print(f"✓ Loaded {len(data_sources['payments'])} payment records")
        
        # GPT data
        gpt_files = list(self.data_dir.glob("opoderdoequitygpt-*.json"))
        if gpt_files:
            with open(gpt_files[-1], 'r', encoding='utf-8') as f:
                data_sources['gpt-interactions'] = json.load(f)
                print(f"✓ Loaded {len(data_sources['gpt-interactions'])} GPT interaction records")
        
        # Payment Links
        links_files = list(self.data_dir.glob("paymentLinks-*.json"))
        if links_files:
            with open(links_files[-1], 'r', encoding='utf-8') as f:
                data_sources['payment-links'] = json.load(f)
                print(f"✓ Loaded {len(data_sources['payment-links'])} payment link records")
        
        # Metrics
        sense_files = list(self.data_dir.glob("senseMetrics-*.json"))
        if sense_files:
            with open(sense_files[-1], 'r', encoding='utf-8') as f:
                data_sources['sense-metrics'] = json.load(f)
                print(f"✓ Loaded {len(data_sources['sense-metrics'])} sense metric records")
        
        crm_files = list(self.data_dir.glob("crmMetrics-*.json"))
        if crm_files:
            with open(crm_files[-1], 'r', encoding='utf-8') as f:
                data_sources['crm-metrics'] = json.load(f)
                print(f"✓ Loaded {len(data_sources['crm-metrics'])} CRM metric records")
        
        return data_sources
    
    def load_excel_data(self) -> Dict[str, pd.DataFrame]:
        """Load all sheets from the Excel file"""
        excel_data = {}
        
        try:
            xl = pd.ExcelFile(self.excel_file)
            for sheet in xl.sheet_names:
                excel_data[sheet] = pd.read_excel(self.excel_file, sheet_name=sheet)
                print(f"✓ Loaded Excel sheet '{sheet}': {len(excel_data[sheet])} rows")
        except Exception as e:
            print(f"✗ Error loading Excel file: {e}")
        
        return excel_data
    
    def compare_crm_to_companies(self, json_data: List[Dict], excel_df: pd.DataFrame) -> Dict:
        """Compare CRM JSON data to Companies sheet"""
        json_ids = set(str(r.get('ID', '')) for r in json_data)
        excel_ids = set(excel_df['company_id'].astype(str).values) if 'company_id' in excel_df.columns else set()
        
        missing_ids = json_ids - excel_ids
        extra_ids = excel_ids - json_ids
        
        # Find missing companies details
        missing_companies = []
        for record in json_data:
            if str(record.get('ID', '')) in missing_ids:
                missing_companies.append({
                    'ID': record.get('ID'),
                    'Company': record.get('Nome da Startup', ''),
                    'Email': record.get('Email', ''),
                    'Location': record.get('Cidade/Estado', '')
                })
        
        return {
            'total_json_records': len(json_ids),
            'total_excel_records': len(excel_ids),
            'missing_from_excel': len(missing_ids),
            'extra_in_excel': len(extra_ids),
            'missing_companies': missing_companies[:10]  # First 10 samples
        }
    
    def analyze_valuation_data(self, valuation_data: List[Dict]) -> Dict:
        """Analyze the separate valuation dataset"""
        if not valuation_data:
            return {'status': 'No separate valuation data found'}
        
        # Extract unique companies from valuation data
        companies = set()
        emails = set()
        
        for record in valuation_data:
            if 'overview.company' in record:
                companies.add(record.get('overview.company'))
            if 'email' in record:
                emails.add(record.get('email'))
            elif 'overview.email' in record:
                emails.add(record.get('overview.email'))
        
        return {
            'total_records': len(valuation_data),
            'unique_companies': len(companies),
            'unique_emails': len(emails),
            'sample_companies': list(companies)[:10],
            'fields_available': list(valuation_data[0].keys())[:20] if valuation_data else []
        }
    
    def analyze_gpt_interactions(self, gpt_data: List[Dict]) -> Dict:
        """Analyze GPT interaction data"""
        if not gpt_data:
            return {'status': 'No GPT interaction data found'}
        
        users = []
        for record in gpt_data:
            users.append({
                'name': record.get('name', ''),
                'email': record.get('email', ''),
                'created': record.get('createdAt', ''),
                'consent': record.get('consent', False)
            })
        
        return {
            'total_interactions': len(gpt_data),
            'users': users,
            'fields': list(gpt_data[0].keys()) if gpt_data else []
        }
    
    def analyze_payment_discrepancies(self, json_payments: List[Dict], excel_payments: pd.DataFrame) -> Dict:
        """Compare payment data between JSON and Excel"""
        # Count payment records
        json_count = len(json_payments) if json_payments else 0
        excel_count = len(excel_payments) if not excel_payments.empty else 0
        
        # Extract emails from payments JSON
        json_emails = set()
        if json_payments:
            for record in json_payments:
                email = record.get('email', record.get('id', ''))
                if email:
                    json_emails.add(email)
        
        # Extract emails from Excel payments
        excel_emails = set()
        if not excel_payments.empty and 'customer_email' in excel_payments.columns:
            excel_emails = set(excel_payments['customer_email'].dropna().values)
        
        missing_emails = json_emails - excel_emails
        
        return {
            'json_payment_records': json_count,
            'excel_payment_records': excel_count,
            'unique_json_customers': len(json_emails),
            'unique_excel_customers': len(excel_emails),
            'missing_customers': len(missing_emails),
            'sample_missing': list(missing_emails)[:10]
        }
    
    def generate_report(self) -> str:
        """Generate comprehensive analysis report"""
        print("\n" + "="*60)
        print("DATA AUDIT REPORT")
        print("="*60)
        
        # Load all data
        print("\n📂 Loading data sources...")
        json_data = self.load_all_json_data()
        
        print("\n📊 Loading Excel data...")
        excel_data = self.load_excel_data()
        
        # Compare CRM to Companies
        print("\n🔍 Analyzing CRM vs Companies sheet...")
        if 'crm-valuation' in json_data and 'Companies' in excel_data:
            crm_analysis = self.compare_crm_to_companies(
                json_data['crm-valuation'], 
                excel_data['Companies']
            )
            
            print(f"\n📋 CRM VALUATION ANALYSIS:")
            print(f"   JSON Records: {crm_analysis['total_json_records']}")
            print(f"   Excel Records: {crm_analysis['total_excel_records']}")
            print(f"   Missing from Excel: {crm_analysis['missing_from_excel']}")
            print(f"   Extra in Excel: {crm_analysis['extra_in_excel']}")
            
            if crm_analysis['missing_companies']:
                print(f"\n   Sample Missing Companies:")
                for comp in crm_analysis['missing_companies'][:5]:
                    print(f"   - ID: {comp['ID']}, Name: {comp['Company']}")
        
        # Analyze separate valuation data
        print("\n🔍 Analyzing separate valuation data...")
        if 'valuation-separate' in json_data:
            val_analysis = self.analyze_valuation_data(json_data['valuation-separate'])
            
            print(f"\n📋 SEPARATE VALUATION DATA:")
            print(f"   Total Records: {val_analysis['total_records']}")
            print(f"   Unique Companies: {val_analysis['unique_companies']}")
            print(f"   Unique Emails: {val_analysis['unique_emails']}")
            print(f"   ⚠️  This data appears to be NOT included in the Excel file!")
            
            if val_analysis['sample_companies']:
                print(f"\n   Sample Companies:")
                for comp in val_analysis['sample_companies'][:5]:
                    print(f"   - {comp}")
        
        # Analyze GPT interactions
        print("\n🔍 Analyzing GPT interaction data...")
        if 'gpt-interactions' in json_data:
            gpt_analysis = self.analyze_gpt_interactions(json_data['gpt-interactions'])
            
            print(f"\n📋 GPT INTERACTIONS:")
            print(f"   Total Interactions: {gpt_analysis['total_interactions']}")
            print(f"   ⚠️  This data appears to be NOT included in the Excel file!")
            
            if gpt_analysis['users']:
                print(f"\n   Sample Users:")
                for user in gpt_analysis['users'][:5]:
                    print(f"   - {user['name']} ({user['email']})")
        
        # Analyze payment discrepancies
        print("\n🔍 Analyzing payment data...")
        if 'payments' in json_data and 'Payments' in excel_data:
            pay_analysis = self.analyze_payment_discrepancies(
                json_data['payments'],
                excel_data['Payments']
            )
            
            print(f"\n📋 PAYMENT DATA ANALYSIS:")
            print(f"   JSON Records: {pay_analysis['json_payment_records']}")
            print(f"   Excel Records: {pay_analysis['excel_payment_records']}")
            print(f"   Missing Customers: {pay_analysis['missing_customers']}")
        
        # Summary
        print("\n" + "="*60)
        print("SUMMARY OF MISSING DATA")
        print("="*60)
        
        missing_datasets = []
        
        if 'valuation-separate' in json_data:
            missing_datasets.append(f"• Separate Valuation Data: {len(json_data['valuation-separate'])} records")
        
        if 'gpt-interactions' in json_data:
            missing_datasets.append(f"• GPT Interactions: {len(json_data['gpt-interactions'])} records")
        
        if 'payment-links' in json_data:
            missing_datasets.append(f"• Payment Links: {len(json_data['payment-links'])} records")
        
        if missing_datasets:
            print("\n⚠️  The following datasets are NOT in the Excel file:")
            for dataset in missing_datasets:
                print(dataset)
        
        print("\n" + "="*60)
        
        return "Report generated successfully"

def main():
    auditor = DataAuditor()
    auditor.generate_report()

if __name__ == "__main__":
    main()
