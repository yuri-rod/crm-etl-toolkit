#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de Demonstração do Sistema Avançado de ML Analytics
Executa uma análise completa e gera relatórios detalhados
"""

import pandas as pd
import numpy as np
from advanced_ml_analytics import AdvancedMLAnalytics
import os
from datetime import datetime

def demonstrate_individual_models(analytics):
    """
    Demonstra cada modelo individualmente
    """
    print("\n" + "=" * 60)
    print("DEMONSTRAÇÃO INDIVIDUAL DOS MODELOS")
    print("=" * 60)
    
    # 1. Lead Scoring
    print("\n📊 1. LEAD SCORING E CLASSIFICAÇÃO")
    print("-" * 40)
    
    # Gera scores para alguns leads
    sample_leads = analytics.df.head(10)
    scores = analytics.generate_lead_scores(sample_leads)
    
    if scores is not None:
        for i, (idx, row) in enumerate(sample_leads.iterrows()):
            score_data = scores.iloc[i]
            print(f"Lead {i+1} ({row['nome'][:20]}):")
            print(f"  Score: {score_data['lead_score']}/100")
            print(f"  Qualidade: {'Alta' if score_data['lead_quality'] == 1 else 'Baixa'}")
            print(f"  Probabilidade: {score_data['quality_probability']:.3f}")
            print()
    
    # 2. Análise de ROI
    print("\n💰 2. ANÁLISE DE ROI - TOP OPORTUNIDADES")
    print("-" * 40)
    
    top_roi = analytics.df.nlargest(5, 'roi_opportunity_score')
    for i, (idx, row) in enumerate(top_roi.iterrows(), 1):
        print(f"{i}. {row['nome'][:25]}")
        print(f"   ROI Predito: R$ {row['predicted_roi']:.0f}")
        print(f"   Prob. Conversão: {row['conversion_probability']:.3f}")
        print(f"   Score Oportunidade: {row['roi_opportunity_score']:.0f}")
        print(f"   Categoria: {row['opportunity_category']}")
        print()
    
    # 3. Churn Risk
    print("\n⚠️ 3. LEADS EM RISCO DE CHURN")
    print("-" * 40)
    
    high_churn = analytics.df[analytics.df['churn_risk_predicted'] > 0.7].head(5)
    for i, (idx, row) in enumerate(high_churn.iterrows(), 1):
        print(f"{i}. {row['nome'][:25]}")
        print(f"   Risco de Churn: {row['churn_risk_predicted']:.3f}")
        print(f"   Dias sem contato: {row['days_since_contact']}")
        print(f"   Recomendações: {', '.join(row['churn_recommendations'][:2])}")
        print()
    
    # 4. Segmentação
    print("\n🎯 4. SEGMENTAÇÃO POR PERSONAS")
    print("-" * 40)
    
    if 'segmentation' in analytics.models:
        persona_stats = analytics.models['segmentation']['persona_stats']
        for persona, stats in persona_stats.iterrows():
            print(f"{persona}:")
            print(f"  Quantidade: {stats['Quantidade']} leads")
            print(f"  ROI Médio: R$ {stats['ROI_Médio']:.0f}")
            print(f"  Conversão Média: {stats['Conversão_Média']:.3f}")
            print(f"  Descrição: {analytics.personas.get(persona, 'N/A')}")
            print()
    
    # 5. Análise de Funil
    print("\n🔍 5. ANÁLISE CRÍTICA DO FUNIL")
    print("-" * 40)
    
    if 'funnel_analysis' in analytics.models:
        funnel_data = analytics.models['funnel_analysis']
        
        print("Pontos Críticos Identificados:")
        for point in funnel_data['critical_points'][:3]:
            print(f"  • {point}")
        
        print("\nRecomendações Prioritárias:")
        for rec in funnel_data['recommendations'][:3]:
            print(f"  • {rec}")
        
        print("\nLeads em Risco por Estágio:")
        for stage, count in funnel_data['at_risk_leads'].items():
            print(f"  {stage}: {count} leads")

def generate_business_insights(analytics):
    """
    Gera insights de negócio baseados nos modelos
    """
    print("\n" + "=" * 60)
    print("INSIGHTS DE NEGÓCIO")
    print("=" * 60)
    
    df = analytics.df
    
    # Análise de conversão por segmento
    print("\n📈 PERFORMANCE POR SEGMENTO")
    print("-" * 40)
    
    segment_performance = df.groupby('segmento_categoria').agg({
        'conversion_probability': 'mean',
        'predicted_roi': 'mean',
        'churn_risk_predicted': 'mean',
        'nome': 'count'
    }).round(3)
    
    segment_performance.columns = ['Conv_Rate', 'ROI_Medio', 'Churn_Risk', 'Total_Leads']
    segment_performance = segment_performance.sort_values('Conv_Rate', ascending=False)
    
    for segment, data in segment_performance.iterrows():
        print(f"{segment}:")
        print(f"  Total de Leads: {data['Total_Leads']}")
        print(f"  Taxa de Conversão: {data['Conv_Rate']:.3f}")
        print(f"  ROI Médio: R$ {data['ROI_Medio']:.0f}")
        print(f"  Risco de Churn: {data['Churn_Risk']:.3f}")
        print()
    
    # Recomendações estratégicas
    print("\n💡 RECOMENDAÇÕES ESTRATÉGICAS")
    print("-" * 40)
    
    total_leads = len(df)
    high_quality_leads = (df['lead_quality'] == 1).sum()
    high_roi_leads = (df['opportunity_category'] == 'HIGH_VALUE').sum()
    high_risk_leads = (df['churn_risk_predicted'] > 0.7).sum()
    
    print(f"1. FOCO EM QUALIDADE:")
    print(f"   • {high_quality_leads}/{total_leads} leads são de alta qualidade ({(high_quality_leads/total_leads)*100:.1f}%)")
    print(f"   • Concentrar esforços nos {high_quality_leads} leads de maior potencial")
    print()
    
    print(f"2. OPORTUNIDADES DE ROI:")
    print(f"   • {high_roi_leads} leads identificados como alto valor")
    print(f"   • ROI médio potencial: R$ {df['predicted_roi'].mean():.0f}")
    print(f"   • Priorizar contato com leads de categoria HIGH_VALUE e MEDIUM_HIGH")
    print()
    
    print(f"3. RETENÇÃO E CHURN:")
    print(f"   • {high_risk_leads} leads em alto risco de churn")
    print(f"   • Implementar ações imediatas de retenção")
    print(f"   • Reduzir tempo de resposta para leads com >30 dias sem contato")
    print()
    
    # Identificar padrões de sucesso
    success_patterns = df[df['conversion_probability'] > 0.8]
    if len(success_patterns) > 0:
        print(f"4. PADRÕES DE SUCESSO:")
        print(f"   • Leads com alta conversão têm em média:")
        print(f"     - Score de qualidade: {success_patterns['data_quality_score'].mean():.1f}/5")
        print(f"     - Presença no LinkedIn: {success_patterns['has_linkedin'].mean()*100:.0f}%")
        print(f"     - Email válido: {success_patterns['has_email'].mean()*100:.0f}%")
        print(f"     - Segmento mais comum: {success_patterns['segmento_categoria'].mode().iloc[0]}")
        print()

def create_action_plan(analytics):
    """
    Cria plano de ação baseado nas análises
    """
    print("\n" + "=" * 60)
    print("PLANO DE AÇÃO RECOMENDADO")
    print("=" * 60)
    
    df = analytics.df
    
    # Ações imediatas (próximos 7 dias)
    print("\n🚨 AÇÕES IMEDIATAS (7 dias)")
    print("-" * 40)
    
    # Leads em risco crítico
    critical_leads = df[(df['churn_risk_predicted'] > 0.8) | (df['days_since_contact'] > 90)]
    print(f"1. Contatar {len(critical_leads)} leads em risco crítico")
    
    # Top oportunidades
    top_opportunities = df[df['opportunity_category'] == 'HIGH_VALUE']
    print(f"2. Priorizar {len(top_opportunities)} leads de alto valor")
    
    # Leads sem contato recente
    no_recent_contact = df[df['days_since_contact'] > 60]
    print(f"3. Reativar {len(no_recent_contact)} leads sem contato recente")
    
    # Ações de médio prazo (próximos 30 dias)
    print("\n📅 AÇÕES DE MÉDIO PRAZO (30 dias)")
    print("-" * 40)
    
    # Qualificação de leads
    low_quality = df[df['data_quality_score'] < 3]
    print(f"1. Qualificar {len(low_quality)} leads com dados incompletos")
    
    # Segmentação por persona
    print(f"2. Implementar abordagens específicas por persona:")
    if 'segmentation' in analytics.models:
        persona_stats = analytics.models['segmentation']['persona_stats']
        for persona in persona_stats.index:
            count = persona_stats.loc[persona, 'Quantidade']
            print(f"   • {persona}: {count} leads")
    
    # Otimização de funil
    if 'funnel_analysis' in analytics.models:
        funnel_issues = len(analytics.models['funnel_analysis']['critical_points'])
        print(f"3. Otimizar {funnel_issues} pontos críticos no funil de vendas")
    
    # Ações estratégicas (próximos 90 dias)
    print("\n🎯 AÇÕES ESTRATÉGICAS (90 dias)")
    print("-" * 40)
    
    print("1. Implementar sistema de scoring automático")
    print("2. Desenvolver campanhas específicas por persona")
    print("3. Estabelecer métricas de acompanhamento de churn")
    print("4. Criar processo de qualificação contínua de leads")
    print("5. Integrar predições de ROI na tomada de decisão")
    
    # Métricas de acompanhamento
    print("\n📊 MÉTRICAS DE ACOMPANHAMENTO")
    print("-" * 40)
    
    current_conversion = df['conversion_probability'].mean()
    current_roi = df['predicted_roi'].mean()
    current_churn = df['churn_risk_predicted'].mean()
    
    print(f"Metas sugeridas:")
    print(f"• Aumentar taxa de conversão de {current_conversion:.3f} para {current_conversion*1.2:.3f} (+20%)")
    print(f"• Aumentar ROI médio de R$ {current_roi:.0f} para R$ {current_roi*1.15:.0f} (+15%)")
    print(f"• Reduzir risco de churn de {current_churn:.3f} para {current_churn*0.8:.3f} (-20%)")
    print(f"• Melhorar qualidade de dados para score médio >4.0")

def main():
    """
    Função principal de demonstração
    """
    print("🚀 DEMONSTRAÇÃO COMPLETA - SISTEMA AVANÇADO DE ML ANALYTICS")
    print("=" * 70)
    print(f"Iniciado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Inicializa o sistema
    analytics = AdvancedMLAnalytics()
    
    # Carrega dados
    data_path = "./dataset_unificado_20250611_160521_61aac20d.csv"
    
    if not os.path.exists(data_path):
        print(f"❌ Arquivo de dados não encontrado: {data_path}")
        print("   Certifique-se de que o arquivo está no diretório correto.")
        return False
    
    print("📂 Carregando e preparando dados...")
    if not analytics.load_and_prepare_data(data_path):
        print("❌ Falha ao carregar dados")
        return False
    
    print("\n🔄 Executando análise completa...")
    if not analytics.run_complete_analysis():
        print("❌ Falha na análise")
        return False
    
    # Demonstrações específicas
    demonstrate_individual_models(analytics)
    generate_business_insights(analytics)
    create_action_plan(analytics)
    
    # Resumo final
    print("\n" + "=" * 70)
    print("RESUMO DA DEMONSTRAÇÃO")
    print("=" * 70)
    
    print(f"✅ Dados processados: {len(analytics.df)} leads")
    print(f"✅ Modelos treinados: {len(analytics.models)}")
    print(f"✅ Relatórios gerados: ./ml_models/")
    
    print("\nModelos implementados:")
    for i, model_name in enumerate(analytics.models.keys(), 1):
        print(f"  {i}. {model_name.replace('_', ' ').title()}")
    
    print(f"\n🎉 Demonstração concluída com sucesso!")
    print(f"📊 Verifique os arquivos gerados em: ./ml_models/")
    print(f"📄 Relatório completo: ./ml_models/comprehensive_ml_report.txt")
    
    return True

if __name__ == "__main__":
    success = main()
    if success:
        print("\n✨ Sistema pronto para uso em produção!")
    else:
        print("\n❌ Demonstração falhou. Verifique os logs acima.")

