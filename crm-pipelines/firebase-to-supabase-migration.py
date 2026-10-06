#!/usr/bin/env python3
"""
Firebase Firestore to Supabase PostgreSQL Migration Script
Exports Firestore data and converts to PostgreSQL-compatible format
"""

import json
import os
import sys
from datetime import datetime
from typing import Dict, List, Any
import firebase_admin
from firebase_admin import credentials, firestore
import psycopg2
from psycopg2.extras import Json
import pandas as pd

class FirestoreToSupabaseMigrator:
    def __init__(self, firebase_creds_path: str, supabase_config: Dict[str, str]):
        """
        Initialize migrator with Firebase and Supabase credentials
        
        Args:
            firebase_creds_path: Path to Firebase service account JSON
            supabase_config: Dict with Supabase connection details
        """
        # Initialize Firebase
        cred = credentials.Certificate(firebase_creds_path)
        firebase_admin.initialize_app(cred)
        self.db = firestore.client()
        
        # Supabase connection string
        self.supabase_conn_string = (
            f"postgresql://{supabase_config['user']}:{supabase_config['password']}"
            f"@{supabase_config['host']}:{supabase_config['port']}/{supabase_config['database']}"
        )
        
        # Collection mappings
        self.collection_mappings = {
            'users': 'profiles',
            'valuations': 'valuations',
            'companies': 'companies',
            'transactions': 'transactions'
        }
        
    def export_firestore_collection(self, collection_name: str) -> List[Dict]:
        """Export all documents from a Firestore collection"""
        print(f"Exporting collection: {collection_name}")
        docs = self.db.collection(collection_name).stream()
        
        exported_data = []
        for doc in docs:
            data = doc.to_dict()
            data['_firestore_id'] = doc.id  # Preserve original ID
            exported_data.append(data)
            
        print(f"Exported {len(exported_data)} documents from {collection_name}")
        return exported_data
    
    def transform_user_data(self, firestore_user: Dict) -> Dict:
        """Transform Firestore user document to Supabase profile format"""
        return {
            'id': firestore_user.get('uid', firestore_user.get('_firestore_id')),
            'email': firestore_user.get('email'),
            'full_name': firestore_user.get('displayName', firestore_user.get('fullName')),
            'company_name': firestore_user.get('companyName'),
            'phone': firestore_user.get('phone'),
            'whatsapp': firestore_user.get('whatsapp'),
            'role': firestore_user.get('role', 'user'),
            'created_at': firestore_user.get('createdAt', datetime.now())
        }
    
    def transform_valuation_data(self, firestore_val: Dict) -> Dict:
        """Transform Firestore valuation document to Supabase format"""
        # Extract financial data
        financials = firestore_val.get('financials', {})
        overview = firestore_val.get('overview', {})
        
        return {
            'id': firestore_val.get('_firestore_id'),
            'user_id': firestore_val.get('userId'),
            'company_name': overview.get('company'),
            'email': overview.get('email'),
            'full_name': overview.get('fullName'),
            'whatsapp': overview.get('whatsapp'),
            'website': overview.get('website'),
            'foundation_date': overview.get('foundationDate'),
            'city': overview.get('city'),
            'state': overview.get('state'),
            'market': overview.get('market'),
            'current_revenue': financials.get('currentRevenue'),
            'current_ebitda': financials.get('currentEBITDA'),
            'planned_revenue': financials.get('currentPlannedRevenue'),
            'planned_ebitda': financials.get('currentPlannedEBITDA'),
            'fixed_assets': financials.get('fixedAssets'),
            'current_investments': financials.get('currentInvestments'),
            'planned_investments': financials.get('currentPlannedInvestments'),
            'yearly_investments': financials.get('yearlyPlannedInvestments'),
            'growth_rates': Json(financials.get('growthRates', [])),
            'stock_cash_value': financials.get('stockAndCashValues'),
            'current_debt': financials.get('currentDebt'),
            'valuation_amount': firestore_val.get('valuation'),
            'valuation_method': firestore_val.get('method', 'CRM'),
            'valuation_details': Json(firestore_val.get('details', {})),
            'status': firestore_val.get('status', 'completed'),
            'created_at': firestore_val.get('createdAt', datetime.now())
        }
    
    def transform_company_data(self, firestore_company: Dict) -> Dict:
        """Transform Firestore company document to Supabase format"""
        return {
            'id': firestore_company.get('_firestore_id'),
            'user_id': firestore_company.get('userId'),
            'name': firestore_company.get('name'),
            'cnpj': firestore_company.get('cnpj'),
            'website': firestore_company.get('website'),
            'foundation_date': firestore_company.get('foundationDate'),
            'city': firestore_company.get('city'),
            'state': firestore_company.get('state'),
            'country': firestore_company.get('country', 'Brazil'),
            'market': firestore_company.get('market'),
            'segment': firestore_company.get('segment'),
            'description': firestore_company.get('description'),
            'employee_count': firestore_company.get('employeeCount'),
            'created_at': firestore_company.get('createdAt', datetime.now())
        }
    
    def save_to_json(self, data: List[Dict], filename: str):
        """Save data to JSON file for backup"""
        output_path = f"firestore_export_{filename}.json"
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)
        print(f"Saved backup to {output_path}")
    
    def insert_to_supabase(self, table_name: str, data: List[Dict]):
        """Insert data into Supabase PostgreSQL"""
        if not data:
            print(f"No data to insert into {table_name}")
            return
            
        conn = psycopg2.connect(self.supabase_conn_string)
        cur = conn.cursor()
        
        try:
            # Get column names from first record
            columns = list(data[0].keys())
            columns_str = ', '.join(columns)
            placeholders = ', '.join(['%s'] * len(columns))
            
            # Prepare insert query
            query = f"""
                INSERT INTO public.{table_name} ({columns_str})
                VALUES ({placeholders})
                ON CONFLICT (id) DO UPDATE SET
                {', '.join([f"{col} = EXCLUDED.{col}" for col in columns if col != 'id'])}
            """
            
            # Insert each record
            for record in data:
                values = [record.get(col) for col in columns]
                cur.execute(query, values)
            
            conn.commit()
            print(f"Successfully inserted {len(data)} records into {table_name}")
            
        except Exception as e:
            conn.rollback()
            print(f"Error inserting into {table_name}: {e}")
            raise
        finally:
            cur.close()
            conn.close()
    
    def migrate_all(self):
        """Run complete migration"""
        print("Starting Firebase to Supabase migration...")
        
        # Export and transform users
        print("\n1. Migrating Users...")
        users = self.export_firestore_collection('users')
        self.save_to_json(users, 'users')
        transformed_users = [self.transform_user_data(u) for u in users]
        # self.insert_to_supabase('profiles', transformed_users)
        
        # Export and transform valuations
        print("\n2. Migrating Valuations...")
        valuations = self.export_firestore_collection('valuations')
        self.save_to_json(valuations, 'valuations')
        transformed_valuations = [self.transform_valuation_data(v) for v in valuations]
        # self.insert_to_supabase('valuations', transformed_valuations)
        
        # Export and transform companies
        print("\n3. Migrating Companies...")
        companies = self.export_firestore_collection('companies')
        self.save_to_json(companies, 'companies')
        transformed_companies = [self.transform_company_data(c) for c in companies]
        # self.insert_to_supabase('companies', transformed_companies)
        
        # Export transactions
        print("\n4. Migrating Transactions...")
        transactions = self.export_firestore_collection('transactions')
        self.save_to_json(transactions, 'transactions')
        # self.insert_to_supabase('transactions', transactions)
        
        print("\n✅ Migration complete! Check the JSON files for exported data.")
        print("Uncomment the insert_to_supabase lines to import to Supabase.")

def main():
    # Configuration
    FIREBASE_CREDS = "smart-money-education-e3565532c51b.json"  # Your Firebase service account
    
    # Supabase connection configuration
    SUPABASE_CONFIG = {
        'host': 'db.kihyqokxcvtmvqsgbocm.supabase.co',
        'port': '5432',
        'database': 'postgres',
        'user': 'postgres',
        'password': 'p0i7iTT8J1nyVxmZ'
    }
    
    # Check if Firebase credentials exist
    if not os.path.exists(FIREBASE_CREDS):
        print(f"Error: Firebase credentials file not found: {FIREBASE_CREDS}")
        print("Please ensure the service account JSON file is in the current directory")
        sys.exit(1)
    
    # Initialize and run migration
    migrator = FirestoreToSupabaseMigrator(FIREBASE_CREDS, SUPABASE_CONFIG)
    migrator.migrate_all()

if __name__ == "__main__":
    main()
