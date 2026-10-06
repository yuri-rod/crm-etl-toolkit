#!/usr/bin/env python3
"""
Remove duplicate emails from CRM Excel file, keeping records with best data quality.
Data quality is determined by:
1. Completeness (number of non-null fields)
2. Most recent valuation date
3. Highest valuation result (as tiebreaker)
"""

import pandas as pd
import numpy as np
from datetime import datetime
import warnings
import re

warnings.filterwarnings('ignore')

def parse_valuation_value(val):
    """Parse Brazilian currency format to float."""
    if pd.isna(val):
        return 0
    if isinstance(val, (int, float)):
        return float(val)
    # Remove currency symbol and convert Brazilian number format
    val_str = str(val)
    val_str = val_str.replace('R$', '').replace(' ', '')
    val_str = val_str.replace('.', '').replace(',', '.')
    try:
        return float(val_str)
    except:
        return 0

def calculate_quality_score(row):
    """
    Calculate a quality score for each record based on:
    1. Completeness (number of non-null fields)
    2. Valuation date (more recent is better)
    3. Valuation result (higher is better)
    """
    # Count non-null fields
    completeness = row.notna().sum()
    
    # Parse date (format: dd/mm/yyyy)
    date_score = 0
    if pd.notna(row['Data de Valuation']):
        try:
            # Try to parse the date
            if isinstance(row['Data de Valuation'], str):
                parts = row['Data de Valuation'].split('/')
                if len(parts) == 3:
                    day, month, year = parts
                    # Create a score based on date (more recent = higher score)
                    date_score = int(year) * 10000 + int(month) * 100 + int(day)
            elif pd.api.types.is_datetime64_any_dtype(type(row['Data de Valuation'])):
                # If it's already a datetime
                date_score = row['Data de Valuation'].year * 10000 + \
                            row['Data de Valuation'].month * 100 + \
                            row['Data de Valuation'].day
        except:
            date_score = 0
    
    # Parse valuation result
    valuation_score = parse_valuation_value(row['Resultado_Valuation'])
    
    # Combine scores (weighted)
    # Completeness is most important, then date, then valuation amount
    total_score = (completeness * 1000000) + (date_score * 10) + (valuation_score / 1000000)
    
    return total_score

def remove_duplicates(input_file, output_file):
    """Remove duplicate emails, keeping the best quality record."""
    
    print("=" * 60)
    print("REMOVING DUPLICATES FROM CRM DATA")
    print("=" * 60)
    
    # Read the Excel file
    print(f"\n1. Reading file: {input_file}")
    df = pd.read_excel(input_file)
    initial_count = len(df)
    print(f"   Total records: {initial_count:,}")
    print(f"   Total columns: {len(df.columns)}")
    
    # Check for duplicates
    print("\n2. Analyzing duplicates...")
    duplicate_mask = df.duplicated(subset=['Email'], keep=False)
    duplicate_records = df[duplicate_mask]
    unique_emails_with_duplicates = df[duplicate_mask]['Email'].nunique()
    
    print(f"   Records with duplicate emails: {len(duplicate_records):,}")
    print(f"   Unique emails that have duplicates: {unique_emails_with_duplicates:,}")
    
    # Calculate quality scores for all records
    print("\n3. Calculating quality scores for all records...")
    df['quality_score'] = df.apply(calculate_quality_score, axis=1)
    
    # Sort by email and quality score (descending)
    df_sorted = df.sort_values(['Email', 'quality_score'], ascending=[True, False])
    
    # Keep only the first (best) record for each email
    print("\n4. Selecting best record for each email...")
    df_deduplicated = df_sorted.drop_duplicates(subset=['Email'], keep='first')
    
    # Remove the quality_score column before saving
    df_deduplicated = df_deduplicated.drop('quality_score', axis=1)
    
    # Statistics
    final_count = len(df_deduplicated)
    removed_count = initial_count - final_count
    
    print(f"\n5. Results:")
    print(f"   Original records: {initial_count:,}")
    print(f"   Final records: {final_count:,}")
    print(f"   Records removed: {removed_count:,}")
    print(f"   Reduction: {(removed_count/initial_count)*100:.2f}%")
    
    # Save to new Excel file
    print(f"\n6. Saving deduplicated data to: {output_file}")
    df_deduplicated.to_excel(output_file, index=False, engine='openpyxl')
    print(f"   File saved successfully!")
    
    # Show some examples of removed duplicates
    print("\n7. Examples of removed duplicates:")
    examples = df[df['Email'].isin(['email3@gmail.com', 'angelolparente@yahoo.com.br'])]
    
    for email in ['email3@gmail.com', 'angelolparente@yahoo.com.br']:
        email_records = examples[examples['Email'] == email]
        if len(email_records) > 0:
            print(f"\n   Email: {email}")
            print(f"   Original records: {len(email_records)}")
            kept_record = df_deduplicated[df_deduplicated['Email'] == email]
            if not kept_record.empty:
                kept = kept_record.iloc[0]
                print(f"   Kept record:")
                print(f"     - Nome_Empresa: {kept['Nome_Empresa']}")
                print(f"     - Data de Valuation: {kept['Data de Valuation']}")
                print(f"     - Resultado_Valuation: {kept['Resultado_Valuation']}")
                non_null = kept.notna().sum()
                print(f"     - Completeness: {non_null}/{len(kept)} fields filled")
    
    return df_deduplicated

if __name__ == "__main__":
    # File paths
    input_file = "CRM_Dados_Padronizados_COMPLETO_20250904_002307.xlsx"
    output_file = "CRM_Dados_Padronizados_COMPLETO_20250904_002307_deduplicated.xlsx"
    
    # Remove duplicates
    result_df = remove_duplicates(input_file, output_file)
    
    print("\n" + "=" * 60)
    print("PROCESS COMPLETED SUCCESSFULLY!")
    print("=" * 60)
