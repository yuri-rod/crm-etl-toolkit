#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Main CRM Analytics Pipeline

This script orchestrates the entire end-to-end process of lead data processing,
from initial cleaning and enrichment to advanced machine learning analysis and
the generation of comprehensive reports and business insights.

Workflow:
1.  **Data Loading**: Loads lead data from a CSV or generates realistic synthetic data.
2.  **ETL & Enrichment**: Cleans and enriches the data using the LeadEnrichment module.
    - Normalizes names, positions, and company info.
    - Validates and enriches CNPJ, LinkedIn, and addresses (if APIs are enabled).
    - Classifies segments and areas of interest.
3.  **Advanced ML Analysis**: Applies a suite of machine learning models.
    - Scores and classifies leads (0-100).
    - Predicts conversion probability and churn risk.
    - Analyzes ROI and identifies high-value opportunities.
    - Segments leads into actionable personas.
4.  **Reporting & Insights**: Generates reports and a final action plan.
    - Exports enriched data, top leads, and validation warnings to CSV.
    - Creates summary reports in HTML and Markdown.
    - Provides actionable business insights and a strategic plan.
"""

import pandas as pd
import numpy as np
import os
import json
from datetime import datetime
import warnings

warnings.filterwarnings('ignore')

# Import core logic from existing modules
from lead_enrichment import LeadEnrichment
from advanced_ml_analytics import AdvancedMLAnalytics
from export_reports import ReportExporter, ReportConfig

def generate_synthetic_data(n_leads=200):
    """
    Generates realistic, synthetic CRM data for demonstration.
    This function combines the best aspects of the data generation logic
    from the provided demo scripts.
    """
    print(f"🔄 Generating {n_leads} synthetic leads for demonstration...")
    np.random.seed(42)
    
    # Realistic data components
    first_names = ['Ana', 'Carlos', 'Maria', 'João', 'Fernanda', 'Ricardo', 'Juliana', 'Pedro']
    last_names = ['Silva', 'Santos', 'Oliveira', 'Souza', 'Costa', 'Ferreira', 'Almeida']
    positions = ['CEO', 'Diretor de Vendas', 'Gerente de TI', 'Analista de Marketing', 'CTO', 'Coordenador RH']
    
    company_types = {
        'Technology': ['Software', 'SaaS', 'IT Services'],
        'Finance': ['Banking', 'Fintech', 'Insurance'],
        'Healthcare': ['Hospital', 'Pharma', 'Clinic'],
        'Retail': ['E-commerce', 'Fashion', 'Grocery']
    }
    
    data = []
    for i in range(n_leads):
        first_name = np.random.choice(first_names)
        last_name = np.random.choice(last_names)
        industry = np.random.choice(list(company_types.keys()))
        company_type = np.random.choice(company_types[industry])
        company_name = f"{np.random.choice(['Global', 'Smart', 'Pro'])} {company_type} {np.random.choice(['Solutions', 'Group', 'Inc'])}"
        
        # Simulate some missing data
        email = f"{first_name.lower()}.{last_name.lower()}@{company_name.lower().replace(' ', '')}.com"
        if np.random.random() < 0.08: email = None
        
        cnpj = f"{np.random.randint(10, 99)}.{np.random.randint(100, 999)}.{np.random.randint(100, 999)}/0001-{np.random.randint(10, 99)}"
        if np.random.random() < 0.3: cnpj = ''

        lead = {
            'id': f'lead_{i+1:03d}',
            'nome_completo': f"{first_name} {last_name}",
            'cargo': np.random.choice(positions),
            'nome_empresa': f"{company_name} LTDA",
            'email': email,
            'cnpj': cnpj,
            'linkedin': f"https://linkedin.com/in/{first_name.lower()}-{last_name.lower()}" if np.random.random() > 0.2 else '',
            'endereco': "Av. Paulista, 1000, São Paulo, SP",
            'autorizacao_imagem': np.random.choice(['sim', 'não', 'aceito']),
            'segmento_empresa': industry
        }
        data.append(lead)
        
    df = pd.DataFrame(data)
    print(f"✅ {len(df)} synthetic leads created.")
    return df

def run_etl_and_enrichment(df: pd.DataFrame, enable_api_calls: bool = False) -> pd.DataFrame:
    """
    Executes the data cleaning and enrichment pipeline.
    This function encapsulates the logic from 'enrichment_integration.py'.
    """
    print("\n--- STAGE 1: ETL & LEAD ENRICHMENT ---")
    
    # Initialize the enrichment module
    enricher = LeadEnrichment(enable_api_calls=enable_api_calls)
    
    # Process each lead
    records = df.to_dict('records')
    enriched_records = [enricher.enrich_lead(record) for record in records]
    
    enriched_df = pd.DataFrame(enriched_records)
    
    # Report on enrichment
    validated_cnpjs = enriched_df['cnpj_valido'].sum() if 'cnpj_valido' in enriched_df.columns else 0
    geocoded_addresses = enriched_df['latitude'].notna().sum() if 'latitude' in enriched_df.columns else 0
    
    print(f"✅ Enrichment complete.")
    print(f"   - Validated CNPJs: {validated_cnpjs}/{len(df)}")
    if enable_api_calls:
        print(f"   - Geocoded Addresses: {geocoded_addresses}/{len(df)}")
    
    return enriched_df

def run_advanced_ml_analysis(df: pd.DataFrame, data_path_for_ml: str) -> AdvancedMLAnalytics:
    """
    Executes the advanced machine learning analysis pipeline.
    This function utilizes 'advanced_ml_analytics.py'.
    """
    print("\n--- STAGE 2: ADVANCED ML ANALYSIS ---")
    
    # Save the enriched data for the ML module to load
    df.to_csv(data_path_for_ml, index=False)

    analytics_system = AdvancedMLAnalytics()
    
    # Load data and run all models
    if analytics_system.load_and_prepare_data(data_path_for_ml):
        analytics_system.run_complete_analysis()
        print("✅ ML analysis complete. All models trained and results generated.")
        return analytics_system
    else:
        print("❌ Failed to run ML analysis.")
        return None

def generate_reports_and_insights(analytics_system: AdvancedMLAnalytics):
    """
    Generates final reports and business insights.
    This function uses 'export_reports.py' and insight logic from the demos.
    """
    print("\n--- STAGE 3: REPORTING & INSIGHTS ---")
    
    if not analytics_system or analytics_system.df is None:
        print("❌ Cannot generate reports. ML analysis did not complete.")
        return

    # Use the dataframe with all predictions from the analytics system
    final_df = analytics_system.df
    
    # Configure and run the report exporter
    report_config = ReportConfig(
        output_dir="final_reports",
        include_predictions=False # Predictions are already in the dataframe from ML module
    )
    exporter = ReportExporter(report_config)
    
    # Generate a separate predictions dictionary for the exporter
    pred_cols = [col for col in final_df.columns if 'predicted' in col or 'probability' in col or 'score' in col]
    predictions = final_df[pred_cols].to_dict('list')

    generated_files = exporter.generate_complete_report(final_df, predictions)
    print(f"✅ {len(generated_files)} report files generated in '{report_config.output_dir}/'")

    # --- Generate Final Business Insights & Action Plan ---
    print("\n💡 FINAL BUSINESS INSIGHTS & ACTION PLAN")
    print("-" * 50)
    
    df = final_df
    total_leads = len(df)
    high_quality_leads = (df['lead_quality'] == 1).sum() if 'lead_quality' in df.columns else 0
    high_roi_leads = (df['opportunity_category'] == 'HIGH_VALUE').sum() if 'opportunity_category' in df.columns else 0
    high_churn_risk = (df['churn_risk_predicted'] > 0.7).sum() if 'churn_risk_predicted' in df.columns else 0

    print("📊 Executive Summary:")
    print(f"  - Analyzed {total_leads} leads.")
    print(f"  - Identified {high_quality_leads} high-quality leads ({(high_quality_leads/total_leads)*100:.1f}%).")
    print(f"  - Found {high_roi_leads} high-value ROI opportunities ({(high_roi_leads/total_leads)*100:.1f}%).")
    print(f"  - Flagged {high_churn_risk} leads with a high risk of churn ({(high_churn_risk/total_leads)*100:.1f}%).")

    print("\n🚨 Immediate Actions (Next 7 Days):")
    critical_churn_leads = df[df['churn_risk_predicted'] > 0.8] if 'churn_risk_predicted' in df.columns else pd.DataFrame()
    top_opportunities = df[df['opportunity_category'] == 'HIGH_VALUE'] if 'opportunity_category' in df.columns else pd.DataFrame()
    print(f"  1. **Contact {len(critical_churn_leads)} leads** at critical churn risk immediately.")
    print(f"  2. **Prioritize outreach** for the {len(top_opportunities)} leads identified as 'HIGH_VALUE' opportunities.")

    print("\n🎯 Strategic Recommendations (Next 90 Days):")
    print("  1. **Focus Sales Efforts**: Direct sales and marketing towards the personas and segments with the highest predicted ROI and conversion rates.")
    print("  2. **Implement Retention Campaigns**: Create targeted campaigns for leads with medium-to-high churn risk scores.")
    print("  3. **Automate & Integrate**: Use the generated scores and predictions to automate lead routing and prioritization within the live CRM system.")

def main():
    """
    Main function to execute the entire pipeline.
    """
    print("🚀 Starting CRM Analytics Pipeline...")
    print("=" * 60)
    
    # --- Configuration ---
    # Set to True to make real API calls for CNPJ and Geocoding.
    # Keep as False to run a faster, local-only version.
    ENABLE_API_ENRICHMENT = False 
    
    # Use a specific data file or generate synthetic data
    INPUT_FILE = None # e.g., 'path/to/your/leads.csv'
    
    # --- Execution ---
    if INPUT_FILE and os.path.exists(INPUT_FILE):
        print(f"📂 Loading data from '{INPUT_FILE}'...")
        initial_df = pd.read_csv(INPUT_FILE)
    else:
        initial_df = generate_synthetic_data(n_leads=250)

    # Temporary file to pass data between stages
    enriched_data_path = 'temp_enriched_data_for_ml.csv'

    # Stage 1: ETL & Enrichment
    enriched_df = run_etl_and_enrichment(initial_df, enable_api_calls=ENABLE_API_ENRICHMENT)
    
    # Stage 2: Machine Learning Analysis
    analytics_system = run_advanced_ml_analysis(enriched_df, enriched_data_path)
    
    # Stage 3: Reporting & Insights
    if analytics_system:
        generate_reports_and_insights(analytics_system)
    
    # Clean up temporary file
    if os.path.exists(enriched_data_path):
        os.remove(enriched_data_path)
        
    print("\n" + "=" * 60)
    print("🎉 CRM Analytics Pipeline Finished Successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()