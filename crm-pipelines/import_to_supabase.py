#!/usr/bin/env python3
"""
Import Firebase data to Supabase PostgreSQL
"""

import json
import psycopg2
from psycopg2.extras import Json, execute_batch
from datetime import datetime
import sys

# Supabase connection configuration
SUPABASE_CONFIG = {
    'host': 'aws-0-us-east-1.pooler.supabase.com',  # Using pooler connection
    'port': '6543',  # Pooler port
    'database': 'postgres',
    'user': 'postgres.kihyqokxcvtmvqsgbocm',
    'password': 'p0i7iTT8J1nyVxmZ'
}

def connect_to_supabase():
    """Create connection to Supabase PostgreSQL"""
    try:
        conn = psycopg2.connect(
            host=SUPABASE_CONFIG['host'],
            port=SUPABASE_CONFIG['port'],
            database=SUPABASE_CONFIG['database'],
            user=SUPABASE_CONFIG['user'],
            password=SUPABASE_CONFIG['password'],
            sslmode='require'
        )
        print("✅ Connected to Supabase successfully!")
        return conn
    except Exception as e:
        print(f"❌ Failed to connect to Supabase: {e}")
        sys.exit(1)

def import_valuations(conn):
    """Import valuation data to Supabase"""
    print("\n📊 Importing valuations...")
    
    try:
        # Load valuation data
        with open('firebase_export_valuation.json', 'r', encoding='utf-8') as f:
            valuations = json.load(f)
        
        print(f"Found {len(valuations)} valuations to import")
        
        cur = conn.cursor()
        
        # Prepare data for batch insert
        records = []
        skipped = 0
        
        for val in valuations[:1000]:  # Start with first 1000 for testing
            try:
                # Extract nested data
                overview = val.get('overview', {})
                financials = val.get('financials', {})
                
                # Skip if missing critical data
                if not overview.get('email'):
                    skipped += 1
                    continue
                
                # Convert timestamp to datetime if exists
                created_at = None
                if 'timestamp' in val:
                    try:
                        created_at = datetime.fromtimestamp(val['timestamp'] / 1000)
                    except:
                        created_at = datetime.now()
                
                record = (
                    val.get('id', val.get('_id')),  # id
                    None,  # user_id (will be linked later)
                    None,  # company_id (will be linked later)
                    overview.get('company', overview.get('startup', 'Unknown')),  # company_name
                    overview.get('email'),  # email
                    overview.get('fullName'),  # full_name
                    overview.get('whatsapp'),  # whatsapp
                    overview.get('website'),  # website
                    overview.get('foundationDate'),  # foundation_date
                    overview.get('city'),  # city
                    overview.get('state'),  # state
                    overview.get('market'),  # market
                    financials.get('currentRevenue'),  # current_revenue
                    financials.get('currentEBITDA'),  # current_ebitda
                    financials.get('currentPlannedRevenue'),  # planned_revenue
                    financials.get('currentPlannedEBITDA'),  # planned_ebitda
                    financials.get('fixedAssets'),  # fixed_assets
                    financials.get('currentInvestments'),  # current_investments
                    financials.get('currentPlannedInvestments'),  # planned_investments
                    financials.get('yearlyPlannedInvestments'),  # yearly_investments
                    Json(financials.get('growthRates', [])),  # growth_rates
                    financials.get('stockAndCashValues'),  # stock_cash_value
                    financials.get('currentDebt'),  # current_debt
                    val.get('valuation'),  # valuation_amount
                    'CRM' if 'scorecard' in val else 'SENSE',  # valuation_method
                    Json({
                        'scorecard': val.get('scorecard', {}),
                        'risksFactors': val.get('risksFactors', {}),
                        'funding': val.get('funding', {})
                    }),  # valuation_details
                    'completed',  # status
                    'unknown',  # payment_status
                    created_at,  # created_at
                    created_at,  # updated_at
                    created_at  # completed_at
                )
                
                records.append(record)
                
            except Exception as e:
                print(f"Error processing valuation: {e}")
                skipped += 1
                continue
        
        if records:
            # Create insert query
            insert_query = """
                INSERT INTO public.valuations (
                    id, user_id, company_id, company_name, email, full_name,
                    whatsapp, website, foundation_date, city, state, market,
                    current_revenue, current_ebitda, planned_revenue, planned_ebitda,
                    fixed_assets, current_investments, planned_investments, 
                    yearly_investments, growth_rates, stock_cash_value, current_debt,
                    valuation_amount, valuation_method, valuation_details,
                    status, payment_status, created_at, updated_at, completed_at
                ) VALUES (
                    gen_random_uuid(), %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s,
                    %s, %s, %s,
                    %s, %s, %s, %s,
                    %s, %s, %s,
                    %s, %s, %s, %s, %s
                )
                ON CONFLICT (id) DO UPDATE SET
                    company_name = EXCLUDED.company_name,
                    email = EXCLUDED.email,
                    valuation_amount = EXCLUDED.valuation_amount
            """
            
            # Execute batch insert
            print(f"Inserting {len(records)} valuations...")
            execute_batch(cur, insert_query, records, page_size=100)
            conn.commit()
            
            print(f"✅ Successfully imported {len(records)} valuations")
            print(f"⚠️ Skipped {skipped} records due to missing data")
        
        cur.close()
        
    except Exception as e:
        print(f"❌ Error importing valuations: {e}")
        conn.rollback()

def import_payments(conn):
    """Import payment data to Supabase"""
    print("\n💳 Importing payments...")
    
    try:
        # Load payment data
        with open('firebase_export_payments.json', 'r', encoding='utf-8') as f:
            payments = json.load(f)
        
        print(f"Found {len(payments)} payments to import")
        
        cur = conn.cursor()
        
        # Prepare data for batch insert
        records = []
        
        for payment in payments[:100]:  # Start with first 100 for testing
            try:
                # Extract analysis data
                analysis = payment.get('analysis', {})
                
                record = (
                    payment.get('_id'),  # Using firebase ID
                    None,  # user_id (will be linked later)
                    None,  # valuation_id (will be linked later)
                    payment.get('_id'),  # order_id
                    payment.get('email'),  # customer_id (using email)
                    analysis.get('totalValue', 0),  # amount
                    'BRL',  # currency
                    'completed',  # status
                    'unknown',  # payment_method
                    Json(payment.get('valuations', {})),  # metadata
                    Json(payment),  # pagarme_response (full payment data)
                    datetime.now(),  # created_at
                    datetime.now()  # updated_at
                )
                
                records.append(record)
                
            except Exception as e:
                print(f"Error processing payment: {e}")
                continue
        
        if records:
            # Create insert query
            insert_query = """
                INSERT INTO public.transactions (
                    id, user_id, valuation_id, order_id, customer_id,
                    amount, currency, status, payment_method,
                    metadata, pagarme_response, created_at, updated_at
                ) VALUES (
                    gen_random_uuid(), %s, %s, %s, %s,
                    %s, %s, %s, %s,
                    %s, %s, %s, %s
                )
                ON CONFLICT (order_id) DO UPDATE SET
                    amount = EXCLUDED.amount,
                    status = EXCLUDED.status
            """
            
            # Execute batch insert
            print(f"Inserting {len(records)} payments...")
            execute_batch(cur, insert_query, records, page_size=100)
            conn.commit()
            
            print(f"✅ Successfully imported {len(records)} payments")
        
        cur.close()
        
    except Exception as e:
        print(f"❌ Error importing payments: {e}")
        conn.rollback()

def verify_import(conn):
    """Verify imported data"""
    print("\n🔍 Verifying imported data...")
    
    cur = conn.cursor()
    
    tables = ['valuations', 'transactions', 'ebitda_multiples']
    
    for table in tables:
        try:
            cur.execute(f"SELECT COUNT(*) FROM public.{table}")
            count = cur.fetchone()[0]
            print(f"  {table}: {count} records")
        except Exception as e:
            print(f"  {table}: Error - {e}")
    
    cur.close()

def main():
    """Main import function"""
    print("🚀 Starting Firebase to Supabase import...")
    
    # Connect to Supabase
    conn = connect_to_supabase()
    
    try:
        # Import valuations
        import_valuations(conn)
        
        # Import payments
        import_payments(conn)
        
        # Verify import
        verify_import(conn)
        
        print("\n✅ Import completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Import failed: {e}")
        conn.rollback()
    
    finally:
        conn.close()
        print("\n👋 Database connection closed")

if __name__ == "__main__":
    main()
