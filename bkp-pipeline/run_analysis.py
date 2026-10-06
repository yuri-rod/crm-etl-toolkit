"""
Simple script to process any CSV file with the CRM System
"""
import pandas as pd
import json
from datetime import datetime
import os

# Import our modules (simplified version for local use)
from crm_cleaner import CRMCleaner
from analytics_engine import CRMAnalyticsEngine

def process_new_csv(csv_file_path):
    """
    Process a new CSV file through the complete CRM pipeline
    """
    print(f"\n{'='*60}")
    print(f"🚀 PROCESSANDO ARQUIVO: {csv_file_path}")
    print(f"{'='*60}\n")
    
    # Step 1: Initialize the cleaner
    print("📊 Etapa 1: Limpando dados...")
    cleaner = CRMCleaner()
    
    # Read the CSV
    try:
        df = pd.read_csv(csv_file_path, encoding='utf-8')
    except:
        df = pd.read_csv(csv_file_path, encoding='latin-1')
    
    print(f"✓ Arquivo carregado: {len(df)} registros encontrados")
    
    # Clean the data
    df_clean = cleaner.clean_dataframe(df, source_name=os.path.basename(csv_file_path))
    print(f"✓ Dados limpos: {len(df_clean)} registros processados")
    
    # Step 2: Export cleaned data
    print("\n💾 Etapa 2: Salvando dados limpos...")
    output_file = cleaner.export_for_ai_processing(
        df_clean, 
        f'output/{os.path.splitext(os.path.basename(csv_file_path))[0]}_cleaned'
    )
    print(f"✓ Dados salvos em: {output_file}")
    
    # Step 3: Run analytics
    print("\n🤖 Etapa 3: Executando análise com IA...")
    analytics = CRMAnalyticsEngine()
    results = analytics.analyze_complete_dataset(output_file)
    
    # Step 4: Show results
    print("\n📈 RESULTADOS DA ANÁLISE:")
    print(f"{'='*60}")
    
    # Show key metrics
    metrics = results.get('roi_analysis', {}).get('metrics', {})
    print(f"\n💰 MÉTRICAS FINANCEIRAS:")
    print(f"   • ROI Projetado: {results.get('roi_analysis', {}).get('investment_return', {}).get('roi_percentage', 0):.1f}%")
    print(f"   • CAC: R$ {metrics.get('cac', 0):.2f}")
    print(f"   • LTV Médio: R$ {metrics.get('avg_ltv', 0):,.2f}")
    
    # Show segments
    print(f"\n🎯 SEGMENTAÇÃO:")
    segments = results.get('segmentation', {}).get('segments', [])
    for segment in segments[:3]:
        print(f"   • {segment['name']}: {segment['size']} leads ({segment['percentage']:.1f}%)")
    
    # Show top insights
    print(f"\n💡 TOP INSIGHTS:")
    for i, insight in enumerate(results.get('insights', [])[:3], 1):
        print(f"   {i}. {insight['insight']}")
        print(f"      → Ação: {insight['recommendation']}")
    
    # Show ML predictions
    predictions = results.get('predictions', {})
    if predictions:
        print(f"\n🔮 PREDIÇÕES ML:")
        conv_summary = predictions.get('summary', {}).get('conversion', {})
        if conv_summary:
            print(f"   • Leads alta conversão: {conv_summary.get('high_probability_count', 0)}")
            print(f"   • Probabilidade média: {conv_summary.get('avg_probability', 0)*100:.1f}%")
    
    # Save full results
    results_file = f'output/{os.path.splitext(os.path.basename(csv_file_path))[0]}_analysis_results.json'
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2, default=str)
    
    print(f"\n✅ Análise completa salva em: {results_file}")
    
    # Generate executive report
    report = analytics.generate_executive_report(results)
    report_file = f'output/{os.path.splitext(os.path.basename(csv_file_path))[0]}_executive_report.md'
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"📄 Relatório executivo: {report_file}")
    
    print(f"\n{'='*60}")
    print("🎉 PROCESSAMENTO CONCLUÍDO COM SUCESSO!")
    print(f"{'='*60}\n")
    
    return df_clean, results

# Main execution
if __name__ == "__main__":
    # Create output directory if it doesn't exist
    os.makedirs('output', exist_ok=True)
    
    # Process your new CSV file
    csv_file = "Base JE16.csv"  # Change this to your file name
    
    if os.path.exists(csv_file):
        cleaned_data, analysis_results = process_new_csv(csv_file)
        
        # Optional: Show a sample of cleaned data
        print("\n📋 AMOSTRA DOS DADOS LIMPOS:")
        print(cleaned_data.head())
    else:
        print(f"❌ Arquivo '{csv_file}' não encontrado!")
        print("Por favor, coloque seu arquivo CSV na mesma pasta do script.")