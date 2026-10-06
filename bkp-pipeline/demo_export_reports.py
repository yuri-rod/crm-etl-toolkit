#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Demonstração do Sistema de Exportação de Relatórios Automáticos
Este script demonstra como usar o módulo export_reports para gerar relatórios completos
"""

import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta
import json
from pathlib import Path

# Importar o módulo de exportação
from export_reports import ReportExporter, ReportConfig, generate_reports

def create_sample_data(n_leads=50):
    """
    Cria dados sintéticos para demonstração
    
    Args:
        n_leads: Número de leads a criar
        
    Returns:
        DataFrame com dados sintéticos
    """
    np.random.seed(42)  # Para reprodutibilidade
    
    # Listas para geração aleatória
    companies = [
        'TechCorp Inc', 'Digital Solutions Ltd', 'Innovation Labs', 'Future Systems',
        'Smart Technologies', 'Global Dynamics', 'NextGen Corp', 'Advanced Solutions',
        'Quantum Technologies', 'Cyber Innovations', 'Data Systems Inc', 'Cloud First Ltd',
        'AI Ventures', 'Digital Transform Co', 'Tech Leaders Inc'
    ]
    
    industries = [
        'Technology', 'Finance', 'Healthcare', 'Manufacturing', 'Retail',
        'Education', 'Energy', 'Transportation', 'Real Estate', 'Media'
    ]
    
    company_sizes = ['CRM', 'Medium', 'Large', 'Enterprise']
    
    first_names = [
        'John', 'Jane', 'Carlos', 'Ana', 'Mike', 'Sarah', 'Roberto', 'Maria',
        'David', 'Laura', 'Pedro', 'Carla', 'Paulo', 'Fernanda', 'Ricardo'
    ]
    
    last_names = [
        'Silva', 'Santos', 'Oliveira', 'Souza', 'Costa', 'Ferreira', 'Rodrigues',
        'Johnson', 'Smith', 'Brown', 'Davis', 'Wilson', 'Moore', 'Taylor', 'Anderson'
    ]
    
    # Gerar dados
    data = []
    
    for i in range(n_leads):
        # Dados básicos
        first_name = np.random.choice(first_names)
        last_name = np.random.choice(last_names)
        company = np.random.choice(companies)
        
        # Simular alguns dados faltantes
        email = f"{first_name.lower()}.{last_name.lower()}@{company.lower().replace(' ', '').replace('inc', '').replace('ltd', '').replace('corp', '')}.com"
        if np.random.random() < 0.05:  # 5% de chance de email faltante
            email = None
        
        contact_name = f"{first_name} {last_name}"
        if np.random.random() < 0.03:  # 3% de chance de nome faltante
            contact_name = None
        
        # Métricas de engagement
        engagement_score = np.random.beta(2, 5)  # Distribuição enviesada para baixo
        
        # Revenue baseado no tamanho da empresa
        company_size = np.random.choice(company_sizes, p=[0.4, 0.3, 0.2, 0.1])
        if company_size == 'CRM':
            revenue = np.random.lognormal(10, 1)  # Menor revenue
        elif company_size == 'Medium':
            revenue = np.random.lognormal(12, 1)
        elif company_size == 'Large':
            revenue = np.random.lognormal(14, 1)
        else:  # Enterprise
            revenue = np.random.lognormal(16, 1)
        
        # Última interação
        days_ago = np.random.exponential(30)  # Média de 30 dias
        last_interaction = datetime.now() - timedelta(days=int(days_ago))
        
        # Score baseado em vários fatores
        base_score = 0.3
        base_score += engagement_score * 0.3
        base_score += min(revenue / 1000000, 1) * 0.2  # Normalizar revenue
        base_score += (1 / (1 + days_ago/30)) * 0.2  # Decaimento temporal
        
        # Adicionar ruído
        base_score += np.random.normal(0, 0.1)
        base_score = max(0, min(1, base_score))  # Clipar entre 0 e 1
        
        lead_data = {
            'email': email,
            'company': company if np.random.random() > 0.02 else None,  # 2% de empresas faltantes
            'contact_name': contact_name,
            'industry': np.random.choice(industries),
            'company_size': company_size,
            'revenue': revenue,
            'engagement_score': engagement_score,
            'last_interaction': last_interaction.strftime('%Y-%m-%d'),
            'lead_score': base_score,
            'source': np.random.choice(['Website', 'Social Media', 'Email Campaign', 'Referral', 'Event']),
            'phone': f"+55 11 9{np.random.randint(1000, 9999)}-{np.random.randint(1000, 9999)}" if np.random.random() > 0.1 else None
        }
        
        data.append(lead_data)
    
    return pd.DataFrame(data)

def create_sample_predictions(df):
    """
    Cria predições sintéticas dos modelos ML
    
    Args:
        df: DataFrame com dados dos leads
        
    Returns:
        Dicionário com predições
    """
    n_leads = len(df)
    
    # Predições correlacionadas com o lead_score
    base_scores = df['lead_score'].values if 'lead_score' in df.columns else np.random.random(n_leads)
    
    predictions = {
        'conversion_probability': np.clip(
            base_scores + np.random.normal(0, 0.15, n_leads), 0, 1
        ),
        'churn_risk': np.clip(
            (1 - base_scores) + np.random.normal(0, 0.2, n_leads), 0, 1
        ),
        'revenue_prediction': np.maximum(
            base_scores * 100000 * np.random.lognormal(0, 0.5, n_leads), 1000
        ),
        'engagement_forecast': np.clip(
            base_scores * 0.8 + np.random.normal(0, 0.1, n_leads), 0, 1
        )
    }
    
    return predictions

def demonstrate_basic_export():
    """
    Demonstração básica da exportação de relatórios
    """
    print("\n" + "="*60)
    print("DEMONSTRAÇÃO BÁSICA - EXPORTAÇÃO DE RELATÓRIOS")
    print("="*60)
    
    # Criar dados de exemplo
    print("\n1. Criando dados sintéticos...")
    df = create_sample_data(30)
    predictions = create_sample_predictions(df)
    
    print(f"   - {len(df)} leads gerados")
    print(f"   - {len(predictions)} tipos de predição criados")
    
    # Usar função de conveniência
    print("\n2. Gerando relatórios completos...")
    files = generate_reports(df, predictions)
    
    print("\n3. Arquivos gerados:")
    for file_type, filepath in files.items():
        print(f"   - {file_type}: {Path(filepath).name}")
    
    return files

def demonstrate_custom_config():
    """
    Demonstração com configuração personalizada
    """
    print("\n" + "="*60)
    print("DEMONSTRAÇÃO AVANÇADA - CONFIGURAÇÃO PERSONALIZADA")
    print("="*60)
    
    # Configuração personalizada
    custom_config = ReportConfig(
        output_dir="custom_reports",
        max_top_leads=20,
        csv_encoding="utf-8",
        include_predictions=True,
        include_validation_warnings=True
    )
    
    # Criar dados maiores
    print("\n1. Criando dataset maior...")
    df = create_sample_data(100)
    predictions = create_sample_predictions(df)
    
    print(f"   - {len(df)} leads gerados")
    
    # Criar exporter personalizado
    print("\n2. Configurando exporter personalizado...")
    exporter = ReportExporter(custom_config)
    
    # Gerar relatórios
    print("\n3. Gerando relatórios com configuração personalizada...")
    files = exporter.generate_complete_report(df, predictions)
    
    print("\n4. Arquivos gerados:")
    for file_type, filepath in files.items():
        print(f"   - {file_type}: {Path(filepath).name}")
    
    # Mostrar métricas
    print("\n5. Métricas do relatório:")
    for metric, value in exporter.metrics.items():
        print(f"   - {metric}: {value}")
    
    return files, exporter

def demonstrate_individual_exports():
    """
    Demonstração de exportações individuais
    """
    print("\n" + "="*60)
    print("DEMONSTRAÇÃO - EXPORTAÇÕES INDIVIDUAIS")
    print("="*60)
    
    # Criar dados
    df = create_sample_data(25)
    predictions = create_sample_predictions(df)
    
    # Criar exporter
    exporter = ReportExporter(ReportConfig(output_dir="individual_exports"))
    
    # Preparar dados enriquecidos
    print("\n1. Preparando dados enriquecidos...")
    enriched_df = exporter.prepare_enriched_data(df, predictions)
    
    print(f"   - Colunas adicionadas: {len(enriched_df.columns) - len(df.columns)}")
    print(f"   - Novas colunas: {[col for col in enriched_df.columns if col not in df.columns]}")
    
    # Exportações individuais
    print("\n2. Exportando arquivos individuais...")
    
    files = {}
    
    # CSV enriquecido
    files['csv'] = exporter.export_enriched_csv(enriched_df, "demo_enriched.csv")
    print(f"   - CSV enriquecido: {Path(files['csv']).name}")
    
    # Top leads
    files['top_leads'] = exporter.export_top_leads(enriched_df, "demo_top_leads.csv")
    print(f"   - Top leads: {Path(files['top_leads']).name}")
    
    # Warnings
    files['warnings'] = exporter.export_validation_warnings(enriched_df, "demo_warnings.csv")
    print(f"   - Warnings: {Path(files['warnings']).name}")
    
    # Predições
    files['predictions'] = exporter.export_predictions(predictions, "demo_predictions.json")
    print(f"   - Predições: {Path(files['predictions']).name}")
    
    # Sumários
    files['markdown'] = exporter.generate_markdown_summary(enriched_df, predictions, "demo_summary.md")
    print(f"   - Sumário MD: {Path(files['markdown']).name}")
    
    files['html'] = exporter.generate_html_summary(enriched_df, predictions, "demo_summary.html")
    print(f"   - Sumário HTML: {Path(files['html']).name}")
    
    return files, enriched_df

def analyze_sample_output(files, df=None):
    """
    Analisa os arquivos de saída gerados
    
    Args:
        files: Dicionário com caminhos dos arquivos
        df: DataFrame usado (opcional)
    """
    print("\n" + "="*60)
    print("ANÁLISE DOS ARQUIVOS GERADOS")
    print("="*60)
    
    for file_type, filepath in files.items():
        print(f"\n--- {file_type.upper()} ---")
        path = Path(filepath)
        
        if path.exists():
            size_kb = path.stat().st_size / 1024
            print(f"Arquivo: {path.name}")
            print(f"Tamanho: {size_kb:.1f} KB")
            
            if path.suffix == '.csv':
                try:
                    temp_df = pd.read_csv(filepath, encoding='utf-8-sig')
                    print(f"Linhas: {len(temp_df)}")
                    print(f"Colunas: {len(temp_df.columns)}")
                    print(f"Primeiras colunas: {list(temp_df.columns[:5])}")
                except Exception as e:
                    print(f"Erro ao ler CSV: {e}")
            
            elif path.suffix == '.json':
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        json_data = json.load(f)
                    print(f"Chaves principais: {list(json_data.keys())}")
                    if 'predictions' in json_data:
                        print(f"Tipos de predição: {list(json_data['predictions'].keys())}")
                except Exception as e:
                    print(f"Erro ao ler JSON: {e}")
            
            elif path.suffix in ['.md', '.html']:
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                    print(f"Tamanho do conteúdo: {len(content)} caracteres")
                    print(f"Linhas: {len(content.splitlines())}")
                except Exception as e:
                    print(f"Erro ao ler arquivo: {e}")
        else:
            print(f"ERRO: Arquivo não encontrado - {filepath}")

def show_data_quality_summary(df):
    """
    Mostra resumo da qualidade dos dados
    
    Args:
        df: DataFrame para analisar
    """
    print("\n" + "="*60)
    print("RESUMO DA QUALIDADE DOS DADOS")
    print("="*60)
    
    print(f"\nTotal de leads: {len(df)}")
    
    # Análise de dados faltantes
    print("\nDados faltantes por coluna:")
    missing_data = df.isnull().sum()
    for col, missing in missing_data.items():
        if missing > 0:
            pct = (missing / len(df)) * 100
            print(f"  - {col}: {missing} ({pct:.1f}%)")
    
    # Distribuição de scores
    if 'lead_score' in df.columns:
        print("\nDistribuição de Lead Scores:")
        score_ranges = pd.cut(df['lead_score'], bins=[0, 0.2, 0.4, 0.6, 0.8, 1.0], 
                             labels=['0-20%', '20-40%', '40-60%', '60-80%', '80-100%'])
        score_dist = score_ranges.value_counts().sort_index()
        for range_name, count in score_dist.items():
            pct = (count / len(df)) * 100
            print(f"  - {range_name}: {count} leads ({pct:.1f}%)")
    
    # Distribuição por indústria
    if 'industry' in df.columns:
        print("\nTop 5 indústrias:")
        industry_dist = df['industry'].value_counts().head(5)
        for industry, count in industry_dist.items():
            pct = (count / len(df)) * 100
            print(f"  - {industry}: {count} leads ({pct:.1f}%)")

def main():
    """
    Função principal da demonstração
    """
    print("\n📈 SISTEMA DE EXPORTAÇÃO DE RELATÓRIOS AUTOMÁTICOS")
    print("Sistema completo para geração de relatórios enriquecidos de leads")
    
    try:
        # Demonstração básica
        basic_files = demonstrate_basic_export()
        
        # Demonstração avançada
        custom_files, custom_exporter = demonstrate_custom_config()
        
        # Demonstração individual
        individual_files, enriched_df = demonstrate_individual_exports()
        
        # Análise dos resultados
        analyze_sample_output(basic_files)
        
        # Resumo da qualidade dos dados
        show_data_quality_summary(enriched_df)
        
        print("\n" + "="*60)
        print("✅ DEMONSTRAÇÃO CONCLUÍDA COM SUCESSO!")
        print("="*60)
        
        print("\n📁 ARQUIVOS DISPONÍVEIS:")
        
        # Listar todos os diretórios criados
        output_dirs = ['reports', 'custom_reports', 'individual_exports']
        for dir_name in output_dirs:
            if Path(dir_name).exists():
                files_in_dir = list(Path(dir_name).glob('*'))
                if files_in_dir:
                    print(f"\n{dir_name}/")
                    for file_path in sorted(files_in_dir):
                        size_kb = file_path.stat().st_size / 1024
                        print(f"  - {file_path.name} ({size_kb:.1f} KB)")
        
        print("\n🚀 FUNCIONALIDADES IMPLEMENTADAS:")
        print("  ✓ CSV padronizado e enriquecido com tags/status/segmentos/timestamps")
        print("  ✓ Arquivo de top leads (configurável)")
        print("  ✓ Arquivo de predições dos modelos ML (JSON)")
        print("  ✓ Arquivo de warnings de validação")
        print("  ✓ Sumário em Markdown para acompanhamento rápido")
        print("  ✓ Sumário em HTML com visualização rica")
        print("  ✓ Configuração personalizável")
        print("  ✓ Métricas automáticas de qualidade")
        print("  ✓ Validação automática de dados")
        print("  ✓ Segmentação automática de leads")
        print("  ✓ Geração automática de tags")
        
    except Exception as e:
        print(f"\n❌ ERRO durante a demonstração: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

