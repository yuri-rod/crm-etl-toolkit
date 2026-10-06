#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Supabase CRM Data ETL Pipeline
===============================
Migrates CRM data from Excel/JSON sources to Supabase database
with deduplication and data quality management.

Author: AI Assistant  
Date: 04/09/2025
"""

import json
import pandas as pd
import numpy as np
import re
from datetime import datetime, date
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import warnings
from dataclasses import dataclass, field
import os
from dotenv import load_dotenv
import psycopg
from psycopg import sql
from psycopg.rows import dict_row
import hashlib
import unicodedata
import logging
from rapidfuzz import fuzz, process

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('supabase_etl.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

warnings.filterwarnings('ignore')

@dataclass
class ETLConfig:
    """Configuration for ETL process"""
    supabase_url: str = field(default_factory=lambda: os.getenv('SUPABASE_URL', ''))
    supabase_key: str = field(default_factory=lambda: os.getenv('SUPABASE_SERVICE_KEY', ''))
    db_host: str = field(default_factory=lambda: os.getenv('DB_HOST', 'localhost'))
    db_port: int = field(default_factory=lambda: int(os.getenv('DB_PORT', '5432')))
    db_name: str = field(default_factory=lambda: os.getenv('DB_NAME', 'postgres'))
    db_user: str = field(default_factory=lambda: os.getenv('DB_USER', 'postgres'))
    db_password: str = field(default_factory=lambda: os.getenv('DB_PASSWORD', ''))
    tenant_id: str = field(default_factory=lambda: os.getenv('TENANT_ID', ''))
    batch_size: int = 1000
    
    def get_db_connection_string(self) -> str:
        """Build database connection string"""
        # If using Supabase, extract connection details from URL
        if self.supabase_url:
            # Supabase URL format: https://<project-ref>.supabase.co
            project_ref = self.supabase_url.split('//')[1].split('.')[0]
            return f"postgresql://{self.db_user}:{self.db_password}@db.{project_ref}.supabase.co:5432/{self.db_name}"
        else:
            return f"postgresql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"

class DataNormalizer:
    """Utility class for data normalization"""
    
    @staticmethod
    def normalize_text(text: Optional[str]) -> Optional[str]:
        """Normalize text for comparison"""
        if not text:
            return None
        
        # Remove accents
        text = unicodedata.normalize('NFKD', str(text))
        text = ''.join(char for char in text if not unicodedata.combining(char))
        
        # Convert to lowercase and remove extra spaces
        text = ' '.join(text.lower().split())
        
        return text
    
    @staticmethod
    def normalize_email(email: Optional[str]) -> Optional[str]:
        """Normalize email address"""
        if not email:
            return None
        
        email = str(email).lower().strip()
        
        # Basic email validation
        if '@' not in email:
            return None
        
        return email
    
    @staticmethod
    def normalize_phone(phone: Optional[str]) -> Optional[str]:
        """Normalize phone number (keep only digits)"""
        if not phone:
            return None
        
        # Remove all non-digit characters
        phone = re.sub(r'[^0-9]', '', str(phone))
        
        # Brazilian phone format validation
        if len(phone) < 10:
            return None
        
        return phone
    
    @staticmethod
    def normalize_cnpj(cnpj: Optional[str]) -> Optional[str]:
        """Normalize CNPJ (Brazilian company ID)"""
        if not cnpj:
            return None
        
        # Keep only digits
        cnpj = re.sub(r'[^0-9]', '', str(cnpj))
        
        # CNPJ should have 14 digits
        if len(cnpj) != 14:
            return None
        
        return cnpj
    
    @staticmethod
    def parse_brl_amount(amount: Optional[str]) -> Optional[float]:
        """Parse Brazilian Real amount"""
        if not amount:
            return None
        
        try:
            # Remove currency symbol and spaces
            amount = str(amount).replace('R$', '').strip()
            
            # Handle Brazilian number format (1.234.567,89)
            amount = amount.replace('.', '')  # Remove thousand separator
            amount = amount.replace(',', '.')  # Replace decimal comma with dot
            
            return float(amount)
        except:
            return None
    
    @staticmethod
    def parse_date_ddmmyyyy(date_str: Optional[str]) -> Optional[date]:
        """Parse date in DD/MM/YYYY format"""
        if not date_str:
            return None
        
        try:
            # Handle dates with time component
            date_str = str(date_str).split(' ')[0]
            
            # Parse DD/MM/YYYY
            parts = date_str.split('/')
            if len(parts) == 3:
                day, month, year = int(parts[0]), int(parts[1]), int(parts[2])
                return date(year, month, day)
        except:
            pass
        
        return None
    
    @staticmethod
    def extract_domain(url: Optional[str]) -> Optional[str]:
        """Extract domain from URL"""
        if not url:
            return None
        
        url = str(url).lower().strip()
        
        # Remove protocol
        url = re.sub(r'^https?://', '', url)
        # Remove www
        url = re.sub(r'^www\.', '', url)
        # Get domain only
        url = url.split('/')[0].split('?')[0]
        
        return url if url else None

class DeduplicationEngine:
    """Handle deduplication logic"""
    
    def __init__(self, similarity_threshold: float = 0.85):
        self.similarity_threshold = similarity_threshold
    
    def generate_fingerprint(self, record: Dict[str, Any], entity_type: str) -> str:
        """Generate a unique fingerprint for deduplication"""
        if entity_type == 'company':
            # Priority: CNPJ > Domain > Normalized Name
            if record.get('cnpj'):
                return f"cnpj:{record['cnpj']}"
            elif record.get('website'):
                domain = DataNormalizer.extract_domain(record['website'])
                if domain:
                    return f"domain:{domain}"
            elif record.get('legal_name'):
                normalized = DataNormalizer.normalize_text(record['legal_name'])
                return f"name:{normalized}"
        
        elif entity_type == 'contact':
            # Priority: Email > Phone > Name+Company
            if record.get('email'):
                return f"email:{DataNormalizer.normalize_email(record['email'])}"
            elif record.get('phone'):
                return f"phone:{DataNormalizer.normalize_phone(record['phone'])}"
            elif record.get('full_name') and record.get('company_name'):
                name = DataNormalizer.normalize_text(record['full_name'])
                company = DataNormalizer.normalize_text(record['company_name'])
                return f"name_company:{name}:{company}"
        
        # Fallback to hash of all fields
        hash_input = json.dumps(record, sort_keys=True, default=str)
        return f"hash:{hashlib.md5(hash_input.encode()).hexdigest()}"
    
    def find_duplicates(self, records: List[Dict[str, Any]], entity_type: str) -> Dict[str, List[Dict[str, Any]]]:
        """Group duplicate records by fingerprint"""
        duplicates = {}
        
        for record in records:
            fingerprint = self.generate_fingerprint(record, entity_type)
            if fingerprint not in duplicates:
                duplicates[fingerprint] = []
            duplicates[fingerprint].append(record)
        
        return duplicates
    
    def select_best_record(self, duplicates: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Select the best record from duplicates based on completeness and recency"""
        if len(duplicates) == 1:
            return duplicates[0]
        
        # Score each record
        scored_records = []
        for record in duplicates:
            score = 0
            
            # Completeness score (number of non-null fields)
            score += sum(1 for v in record.values() if v is not None and str(v).strip())
            
            # Date recency score
            if 'valuation_date' in record and record['valuation_date']:
                try:
                    date_obj = DataNormalizer.parse_date_ddmmyyyy(record['valuation_date'])
                    if date_obj:
                        days_ago = (date.today() - date_obj).days
                        score += max(0, 1000 - days_ago)  # More recent = higher score
                except:
                    pass
            
            # Valuation amount as tiebreaker
            if 'valuation_amount' in record and record['valuation_amount']:
                amount = DataNormalizer.parse_brl_amount(record['valuation_amount'])
                if amount:
                    score += min(amount / 1000000, 100)  # Cap at 100 points
            
            scored_records.append((score, record))
        
        # Return record with highest score
        scored_records.sort(key=lambda x: x[0], reverse=True)
        return scored_records[0][1]

class SupabaseETL:
    """Main ETL processor for Supabase migration"""
    
    def __init__(self, config: ETLConfig):
        self.config = config
        self.conn = None
        self.normalizer = DataNormalizer()
        self.dedup_engine = DeduplicationEngine()
        self.tenant_id = None
        
    def connect(self):
        """Establish database connection"""
        try:
            self.conn = psycopg.connect(
                self.config.get_db_connection_string(),
                row_factory=dict_row
            )
            logger.info("Successfully connected to database")
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise
    
    def disconnect(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")
    
    def setup_tenant(self, tenant_name: str) -> str:
        """Setup or get tenant"""
        with self.conn.cursor() as cur:
            # Check if tenant exists
            if self.config.tenant_id:
                cur.execute(
                    "SELECT id FROM tenants WHERE id = %s",
                    (self.config.tenant_id,)
                )
            else:
                cur.execute(
                    "SELECT id FROM tenants WHERE slug = %s",
                    (tenant_name.lower().replace(' ', '-'),)
                )
            
            result = cur.fetchone()
            
            if result:
                self.tenant_id = result['id']
            else:
                # Create new tenant
                cur.execute(
                    """
                    INSERT INTO tenants (name, slug)
                    VALUES (%s, %s)
                    RETURNING id
                    """,
                    (tenant_name, tenant_name.lower().replace(' ', '-'))
                )
                self.tenant_id = cur.fetchone()['id']
                
                # Initialize default stages and sectors
                cur.execute("SELECT seed_default_stages(%s)", (self.tenant_id,))
                cur.execute("SELECT seed_default_sectors(%s)", (self.tenant_id,))
                
                self.conn.commit()
                logger.info(f"Created new tenant: {tenant_name}")
            
            return self.tenant_id
    
    def load_excel_data(self, file_path: str) -> pd.DataFrame:
        """Load data from Excel file"""
        try:
            df = pd.read_excel(file_path)
            logger.info(f"Loaded {len(df)} records from {file_path}")
            return df
        except Exception as e:
            logger.error(f"Failed to load Excel file: {e}")
            raise
    
    def load_json_data(self, file_path: str) -> List[Dict[str, Any]]:
        """Load data from JSON file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            logger.info(f"Loaded {len(data)} records from {file_path}")
            return data
        except Exception as e:
            logger.error(f"Failed to load JSON file: {e}")
            raise
    
    def process_companies(self, df: pd.DataFrame) -> Dict[str, str]:
        """Process and insert companies, return mapping of company names to IDs"""
        company_map = {}
        
        # Get unique companies
        companies = []
        for _, row in df.iterrows():
            company_name = row.get('Nome_Empresa') or row.get('company')
            if company_name and pd.notna(company_name):
                companies.append({
                    'legal_name': str(company_name).strip(),
                    'website': row.get('Website') if pd.notna(row.get('Website')) else None,
                    'city': row.get('Cidade') if pd.notna(row.get('Cidade')) else None,
                    'state': row.get('Estado') if pd.notna(row.get('Estado')) else None,
                    'business_model': row.get('Modelo_Negocio') if pd.notna(row.get('Modelo_Negocio')) else None,
                    'source_row': row.to_dict()
                })
        
        # Deduplicate companies
        dedup_groups = self.dedup_engine.find_duplicates(companies, 'company')
        
        with self.conn.cursor() as cur:
            for fingerprint, duplicates in dedup_groups.items():
                best_record = self.dedup_engine.select_best_record(duplicates)
                
                # Parse location
                city = best_record.get('city', '')
                state = None
                if city and '/' in str(city):
                    parts = str(city).rsplit('/', 1)
                    city = parts[0].strip()
                    if len(parts) > 1:
                        state_raw = parts[1].strip()[:2].upper()
                        # Validate Brazilian state codes
                        if state_raw in ['AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 
                                        'MA', 'MT', 'MS', 'MG', 'PA', 'PB', 'PR', 'PE', 'PI', 
                                        'RJ', 'RN', 'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO']:
                            state = state_raw
                
                # Check if company exists
                cur.execute(
                    """
                    SELECT id FROM companies 
                    WHERE tenant_id = %s 
                    AND legal_name = %s 
                    AND deleted_at IS NULL
                    """,
                    (self.tenant_id, best_record['legal_name'])
                )
                
                existing = cur.fetchone()
                
                if existing:
                    company_id = existing['id']
                    # Update existing company
                    cur.execute(
                        """
                        UPDATE companies 
                        SET website = COALESCE(%s, website),
                            city = COALESCE(%s, city),
                            state = COALESCE(%s, state),
                            business_model = COALESCE(%s, business_model),
                            updated_at = NOW()
                        WHERE id = %s
                        """,
                        (
                            best_record.get('website'),
                            city,
                            state,
                            best_record.get('business_model'),
                            company_id
                        )
                    )
                else:
                    # Insert new company
                    cur.execute(
                        """
                        INSERT INTO companies (
                            tenant_id, legal_name, website, city, state, 
                            business_model, source_system
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                        RETURNING id
                        """,
                        (
                            self.tenant_id,
                            best_record['legal_name'],
                            best_record.get('website'),
                            city,
                            state,
                            best_record.get('business_model'),
                            'excel_import'
                        )
                    )
                    company_id = cur.fetchone()['id']
                
                # Map all duplicate names to the same company ID
                for dup in duplicates:
                    company_map[dup['legal_name']] = company_id
                
                # Process stage if available
                stage_name = best_record['source_row'].get('Estagio_Operacional')
                if stage_name and pd.notna(stage_name):
                    cur.execute(
                        """
                        SELECT id FROM stages 
                        WHERE tenant_id = %s AND name = %s
                        """,
                        (self.tenant_id, stage_name)
                    )
                    stage = cur.fetchone()
                    
                    if not stage:
                        # Create new stage
                        cur.execute(
                            """
                            INSERT INTO stages (tenant_id, name, order_index)
                            VALUES (%s, %s, 999)
                            RETURNING id
                            """,
                            (self.tenant_id, stage_name)
                        )
                        stage = cur.fetchone()
                    
                    # Update company stage
                    cur.execute(
                        """
                        UPDATE companies 
                        SET current_stage_id = %s 
                        WHERE id = %s
                        """,
                        (stage['id'], company_id)
                    )
                
                # Process sector if available
                sector_name = best_record['source_row'].get('Mercado')
                if sector_name and pd.notna(sector_name):
                    cur.execute(
                        """
                        SELECT id FROM sectors 
                        WHERE tenant_id = %s AND name = %s
                        """,
                        (self.tenant_id, sector_name)
                    )
                    sector = cur.fetchone()
                    
                    if not sector:
                        # Create new sector
                        cur.execute(
                            """
                            INSERT INTO sectors (tenant_id, name)
                            VALUES (%s, %s)
                            RETURNING id
                            """,
                            (self.tenant_id, sector_name)
                        )
                        sector = cur.fetchone()
                    
                    # Link company to sector
                    cur.execute(
                        """
                        INSERT INTO company_sectors (company_id, sector_id, is_primary)
                        VALUES (%s, %s, true)
                        ON CONFLICT (company_id, sector_id) DO NOTHING
                        """,
                        (company_id, sector['id'])
                    )
        
        self.conn.commit()
        logger.info(f"Processed {len(company_map)} unique companies from {len(companies)} records")
        
        return company_map
    
    def process_contacts(self, df: pd.DataFrame, company_map: Dict[str, str]):
        """Process and insert contacts"""
        contacts = []
        
        for _, row in df.iterrows():
            contact_name = row.get('Nome do Respondente')
            email = row.get('Email')
            phone = row.get('Telefone')
            company_name = row.get('Nome_Empresa') or row.get('company')
            
            if (contact_name and pd.notna(contact_name)) or (email and pd.notna(email)):
                contacts.append({
                    'full_name': str(contact_name).strip() if pd.notna(contact_name) else 'Unknown',
                    'email': self.normalizer.normalize_email(str(email)) if pd.notna(email) else None,
                    'phone': self.normalizer.normalize_phone(str(phone)) if pd.notna(phone) else None,
                    'company_name': str(company_name).strip() if pd.notna(company_name) else None,
                    'company_id': company_map.get(str(company_name).strip()) if pd.notna(company_name) else None
                })
        
        # Deduplicate contacts
        dedup_groups = self.dedup_engine.find_duplicates(contacts, 'contact')
        
        with self.conn.cursor() as cur:
            for fingerprint, duplicates in dedup_groups.items():
                best_record = self.dedup_engine.select_best_record(duplicates)
                
                # Check if contact exists
                if best_record.get('email'):
                    cur.execute(
                        """
                        SELECT id FROM contacts 
                        WHERE tenant_id = %s 
                        AND email = %s 
                        AND deleted_at IS NULL
                        """,
                        (self.tenant_id, best_record['email'])
                    )
                    existing = cur.fetchone()
                else:
                    existing = None
                
                if existing:
                    contact_id = existing['id']
                    # Update existing contact
                    cur.execute(
                        """
                        UPDATE contacts 
                        SET full_name = COALESCE(%s, full_name),
                            phone = COALESCE(%s, phone),
                            primary_company_id = COALESCE(%s, primary_company_id),
                            updated_at = NOW()
                        WHERE id = %s
                        """,
                        (
                            best_record['full_name'],
                            best_record.get('phone'),
                            best_record.get('company_id'),
                            contact_id
                        )
                    )
                else:
                    # Insert new contact
                    cur.execute(
                        """
                        INSERT INTO contacts (
                            tenant_id, full_name, email, phone, 
                            primary_company_id, source_system
                        ) VALUES (%s, %s, %s, %s, %s, %s)
                        RETURNING id
                        """,
                        (
                            self.tenant_id,
                            best_record['full_name'],
                            best_record.get('email'),
                            best_record.get('phone'),
                            best_record.get('company_id'),
                            'excel_import'
                        )
                    )
                    contact_id = cur.fetchone()['id']
                
                # Link contact to company
                if best_record.get('company_id'):
                    cur.execute(
                        """
                        INSERT INTO contact_companies (
                            contact_id, company_id, is_primary_contact
                        ) VALUES (%s, %s, true)
                        ON CONFLICT (contact_id, company_id) DO NOTHING
                        """,
                        (contact_id, best_record['company_id'])
                    )
        
        self.conn.commit()
        logger.info(f"Processed {len(dedup_groups)} unique contacts from {len(contacts)} records")
    
    def process_valuations(self, df: pd.DataFrame, company_map: Dict[str, str]):
        """Process and insert valuations"""
        with self.conn.cursor() as cur:
            valuations_inserted = 0
            
            for _, row in df.iterrows():
                company_name = row.get('Nome_Empresa') or row.get('company')
                company_id = company_map.get(str(company_name).strip()) if pd.notna(company_name) else None
                
                if not company_id:
                    continue
                
                # Parse valuation data
                valuation_date = self.normalizer.parse_date_ddmmyyyy(
                    str(row.get('Data de Valuation')) if pd.notna(row.get('Data de Valuation')) else None
                )
                
                if not valuation_date:
                    continue
                
                valuation_amount = self.normalizer.parse_brl_amount(
                    str(row.get('Resultado_Valuation')) if pd.notna(row.get('Resultado_Valuation')) else None
                )
                
                valuation_type = str(row.get('Tipo de Valuation')).lower() if pd.notna(row.get('Tipo de Valuation')) else 'other'
                if valuation_type == 'empreendedor':
                    valuation_type = 'sense'
                elif valuation_type not in ['sense', 'pre-money', 'post-money', 'assessment']:
                    valuation_type = 'other'
                
                fundraising = row.get('Pretende_Captar')
                fundraising_interest = None
                if pd.notna(fundraising):
                    fundraising_str = str(fundraising).lower()
                    if 'sim' in fundraising_str or 'pretende' in fundraising_str:
                        fundraising_interest = True
                    elif 'não' in fundraising_str or 'nao' in fundraising_str:
                        fundraising_interest = False
                
                # Check if valuation exists
                cur.execute(
                    """
                    SELECT id FROM valuations 
                    WHERE company_id = %s 
                    AND valuation_date = %s
                    """,
                    (company_id, valuation_date)
                )
                
                if not cur.fetchone():
                    # Insert valuation
                    cur.execute(
                        """
                        INSERT INTO valuations (
                            tenant_id, company_id, valuation_date, 
                            valuation_amount, valuation_type, 
                            investment_stage, fundraising_interest,
                            source_reference
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        """,
                        (
                            self.tenant_id,
                            company_id,
                            valuation_date,
                            valuation_amount,
                            valuation_type,
                            row.get('Estagio_Investimento') if pd.notna(row.get('Estagio_Investimento')) else None,
                            fundraising_interest,
                            'excel_import'
                        )
                    )
                    valuations_inserted += 1
                
                # Process financial snapshot if MRR or LTM available
                mrr = self.normalizer.parse_brl_amount(
                    str(row.get('MRR')) if pd.notna(row.get('MRR')) else None
                )
                ltm = self.normalizer.parse_brl_amount(
                    str(row.get('Faturamento_LTM')) if pd.notna(row.get('Faturamento_LTM')) else None
                )
                
                if mrr or ltm:
                    # Check if financial snapshot exists
                    cur.execute(
                        """
                        SELECT id FROM financial_snapshots 
                        WHERE company_id = %s 
                        AND period_start = %s
                        """,
                        (company_id, valuation_date)
                    )
                    
                    if not cur.fetchone():
                        # Insert financial snapshot
                        cur.execute(
                            """
                            INSERT INTO financial_snapshots (
                                tenant_id, company_id, 
                                period_start, period_end, period_type,
                                mrr, arr, ltm_revenue
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                            """,
                            (
                                self.tenant_id,
                                company_id,
                                valuation_date,
                                valuation_date,
                                'monthly',
                                mrr,
                                mrr * 12 if mrr else None,
                                ltm
                            )
                        )
        
        self.conn.commit()
        logger.info(f"Processed {valuations_inserted} valuations")
    
    def refresh_materialized_views(self):
        """Refresh all materialized views"""
        with self.conn.cursor() as cur:
            cur.execute("REFRESH MATERIALIZED VIEW CONCURRENTLY mv_company_kpis")
            cur.execute("REFRESH MATERIALIZED VIEW CONCURRENTLY mv_pipeline_overview")
        self.conn.commit()
        logger.info("Refreshed materialized views")
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate ETL report"""
        report = {}
        
        with self.conn.cursor() as cur:
            # Company statistics
            cur.execute(
                """
                SELECT 
                    COUNT(*) as total,
                    COUNT(DISTINCT city) as unique_cities,
                    COUNT(DISTINCT state) as unique_states
                FROM companies 
                WHERE tenant_id = %s AND deleted_at IS NULL
                """,
                (self.tenant_id,)
            )
            report['companies'] = cur.fetchone()
            
            # Contact statistics
            cur.execute(
                """
                SELECT 
                    COUNT(*) as total,
                    COUNT(email) as with_email,
                    COUNT(phone) as with_phone
                FROM contacts 
                WHERE tenant_id = %s AND deleted_at IS NULL
                """,
                (self.tenant_id,)
            )
            report['contacts'] = cur.fetchone()
            
            # Valuation statistics
            cur.execute(
                """
                SELECT 
                    COUNT(*) as total,
                    MIN(valuation_amount) as min_amount,
                    MAX(valuation_amount) as max_amount,
                    AVG(valuation_amount) as avg_amount,
                    MIN(valuation_date) as earliest_date,
                    MAX(valuation_date) as latest_date
                FROM valuations 
                WHERE tenant_id = %s
                """,
                (self.tenant_id,)
            )
            report['valuations'] = cur.fetchone()
            
            # Financial statistics
            cur.execute(
                """
                SELECT 
                    COUNT(*) as total,
                    AVG(mrr) as avg_mrr,
                    AVG(ltm_revenue) as avg_ltm
                FROM financial_snapshots 
                WHERE tenant_id = %s
                """,
                (self.tenant_id,)
            )
            report['financials'] = cur.fetchone()
        
        return report

def main():
    """Main ETL execution"""
    # Configuration
    config = ETLConfig()
    
    # If no config in env, prompt for connection details
    if not config.supabase_url and not config.db_host:
        print("\n=== Supabase CRM ETL Configuration ===\n")
        print("Please provide your Supabase connection details:")
        config.supabase_url = input("Supabase URL (e.g., https://xxx.supabase.co): ").strip()
        config.db_password = input("Database Password: ").strip()
        config.db_user = 'postgres'
        config.db_name = 'postgres'
    
    # Initialize ETL
    etl = SupabaseETL(config)
    
    try:
        # Connect to database
        etl.connect()
        
        # Setup tenant
        tenant_name = input("\nEnter tenant name (e.g., 'My Company'): ").strip() or "Default Tenant"
        etl.setup_tenant(tenant_name)
        
        # Process Excel data
        excel_file = "CRM_Dados_Padronizados_COMPLETO_20250904_002307_deduplicated.xlsx"
        
        if Path(excel_file).exists():
            logger.info(f"Processing Excel file: {excel_file}")
            
            # Load data
            df = etl.load_excel_data(excel_file)
            
            # Process in order
            logger.info("Processing companies...")
            company_map = etl.process_companies(df)
            
            logger.info("Processing contacts...")
            etl.process_contacts(df, company_map)
            
            logger.info("Processing valuations and financials...")
            etl.process_valuations(df, company_map)
            
            # Refresh materialized views
            logger.info("Refreshing materialized views...")
            etl.refresh_materialized_views()
            
            # Generate report
            report = etl.generate_report()
            
            print("\n" + "="*50)
            print("ETL PROCESS COMPLETED SUCCESSFULLY")
            print("="*50)
            print(f"\nTenant ID: {etl.tenant_id}")
            print(f"\nStatistics:")
            print(f"  Companies: {report['companies']['total']}")
            print(f"    - Cities: {report['companies']['unique_cities']}")
            print(f"    - States: {report['companies']['unique_states']}")
            print(f"\n  Contacts: {report['contacts']['total']}")
            print(f"    - With Email: {report['contacts']['with_email']}")
            print(f"    - With Phone: {report['contacts']['with_phone']}")
            print(f"\n  Valuations: {report['valuations']['total']}")
            if report['valuations']['avg_amount']:
                print(f"    - Average: R$ {report['valuations']['avg_amount']:,.2f}")
                print(f"    - Range: R$ {report['valuations']['min_amount']:,.2f} - R$ {report['valuations']['max_amount']:,.2f}")
            print(f"\n  Financial Snapshots: {report['financials']['total']}")
            if report['financials']['avg_mrr']:
                print(f"    - Avg MRR: R$ {report['financials']['avg_mrr']:,.2f}")
            if report['financials']['avg_ltm']:
                print(f"    - Avg LTM: R$ {report['financials']['avg_ltm']:,.2f}")
            
        else:
            logger.error(f"Excel file not found: {excel_file}")
    
    except Exception as e:
        logger.error(f"ETL process failed: {e}", exc_info=True)
        raise
    
    finally:
        etl.disconnect()

if __name__ == "__main__":
    main()
