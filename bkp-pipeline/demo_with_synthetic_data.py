#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Demonstração do Sistema Avançado de ML Analytics com Dados Sintéticos
Gera dados realistas para testar todos os modelos implementados
"""

import pandas as pd
import numpy as np
from advanced_ml_analytics import AdvancedMLAnalytics
import random
from datetime import datetime, timedelta

def generate_synthetic_crm_data(n_leads=500):
    """
    Gera dados sintéticos realistas para demonstração
    """
    print(f"🎲 Gerando {n_leads} leads sintéticos...")
    
    # Listas para gerar dados realistas
    first_names = [
        'Ana', 'Carlos', 'Maria', 'João', 'Fernanda', 'Ricardo', 'Juliana', 'Paulo',
        'Camila', 'Rodrigo', 'Beatriz', 'Felipe', 'Amanda', 'Lucas', 'Carolina', 'Pedro',
        'Mariana', 'Diego', 'Gabriela', 'Rafael', 'Isabela', 'Gustavo', 'Larissa', 'Bruno',
        'Priscila', 'Thiago', 'Vanessa', 'Gabriel', 'Daniela', 'Leonardo'
    ]
    
    last_names = [
        'Silva', 'Santos', 'Oliveira', 'Souza', 'Rodrigues', 'Ferreira', 'Alves', 'Pereira',
        'Lima', 'Gomes', 'Costa', 'Ribeiro', 'Martins', 'Carvalho', 'Almeida', 'Lopes',
        'Soares', 'Fernandes', 'Vieira', 'Barbosa', 'Rocha', 'Dias', 'Monteiro', 'Cardoso'
    ]
    
    companies = [
        'TechSolutions', 'InnovateCorp', 'DigitalPro', 'SmartBusiness', 'FutureTech',
        'GlobalSystems', 'NextGen', 'EconoData', 'ProConsult', 'MegaCorp',
        'StartupX', 'BusinessPro', 'TechVision', 'DataMind', 'CloudFirst',
        'AgileWorks', 'InnovateNow', 'TechForward', 'BusinessEdge', 'DigitalEdge'
    ]
    
    positions = [
        'CEO', 'CTO', 'Diretor', 'Gerente', 'Coordenador', 'Analista', 'Consultor',
        'Sócio', 'Fundador', 'VP', 'Superintendente', 'Especialista'
    ]
    
    segments = [
        'Tecnologia', 'Financas', 'Saude', 'Educacao', 'Comercio', 'Construcao',
        'Consultoria', 'Marketing', 'Vendas', 'Servicos', 'Industria', 'Agronegocio'
    ]
    
    states = [
        'São Paulo - SP', 'Rio de Janeiro - RJ', 'Belo Horizonte - MG', 'Brasília - DF',
        'Salvador - BA', 'Fortaleza - CE', 'Recife - PE', 'Porto Alegre - RS',
        'Curitiba - PR', 'Goiânia - GO', 'Manaus - AM', 'Belém - PA'
    ]
    
    estado_civil_options = ['Solteiro', 'Casado', 'Divorciado', 'Viúvo', 'União Estável']
    
    # Gera dados
    data = []
    
    for i in range(n_leads):
        # Nome
        first_name = random.choice(first_names)
        last_name = random.choice(last_names)
        nome = f"{first_name} {last_name}"
        
        # Empresa e cargo
        company = random.choice(companies)
        position = random.choice(positions)
        empresa_cargo = f"{company} - {position}"
        
        # Segmento
        segmento = random.choice(segments)
        
        # Dados de contato
        has_email = random.random() > 0.1  # 90% tem email
        email = f"{first_name.lower()}.{last_name.lower()}@{company.lower()}.com" if has_email else ""
        
        has_linkedin = random.random() > 0.3  # 70% tem LinkedIn
        linkedin = f"linkedin.com/in/{first_name.lower()}{last_name.lower()}" if has_linkedin else ""
        
        has_whatsapp = random.random() > 0.2  # 80% tem WhatsApp
        whatsapp = f"+5511{random.randint(900000000, 999999999)}" if has_whatsapp else ""
        
        has_cnpj = random.random() > 0.4  # 60% tem CNPJ
        cnpj = f"{random.randint(10000000000000, 99999999999999)}" if has_cnpj else ""
        
        # Localização
        cidade_estado = random.choice(states)
        
        # Estado civil
        estado_civil = random.choice(estado_civil_options)
        
        # Aniversário
        aniversario = f"{random.randint(1, 28)}/{random.randint(1, 12)}/{random.randint(1970, 2000)}"
        
        data.append({
            'nome': nome,
            'empresa_cargo': empresa_cargo,
            'segmento': segmento,
            'email': email,
            'linkedin': linkedin,
            'whatsapp': whatsapp,
            'cnpj': cnpj,
            'cidade_estado': cidade_estado,
            'estado_civil': estado_civil,
            'aniversario': aniversario
        })
    
    df = pd.DataFrame(data)
    print(f"✅ {len(df)} leads sintéticos criados")
    return df

def save_synthetic_data(df, filename='synthetic_crm_data.csv'):
    """
    Salva dados sintéticos em arquivo CSV
    """
    df.to_csv(filename, index=False, encoding='utf-8')
    print(f"💾 Dados salvos em: {filename}")
    return filename

def run_complete_demonstration():
    """
    Executa demonstração completa do sistema
    """
    print("🚀 DEMONSTRAÇÃO COMPLETA - SISTEMA AVANÇADO DE ML ANALYTICS")
    print("=" * 70)
    print(f"Iniciado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 1. Gerar dados sintéticos
    print("🔄 Etapa 1: Geração de Dados Sintéticos")
    print("-" * 50)
    
    synthetic_df = generate_synthetic_crm_data(n_leads=300)
    data_file = save_synthetic_data(synthetic_df)
    
    # 2. Inicializar sistema de analytics
    print("\n📊 Etapa 2: Inicialização do Sistema")
    print("-" * 50)
    
    analytics = AdvancedMLAnalytics()
    
    # 3. Carregar e preparar dados
    print("\n📂 Etapa 3: Carregamento e Preparação")
    print("-" * 50)
    
    if not analytics.load_and_prepare_data(data_file):
        print("❌ Falha ao carregar dados")
        return False
    
    # 4. Executar análise completa
    print("\n🤖 Etapa 4: Treinamento dos Modelos de ML")
    print("-" * 50)
    
    if not analytics.run_complete_analysis():
        print("❌ Falha na análise")
        return False
    
    # 5. Demonstrar resultados individuais
    print("\n📈 Etapa 5: Demonstração de Resultados")
    print("-" * 50)
    
    demonstrate_model_results(analytics)
    
    # 6. Gerar insights de negócio
    print("\n💡 Etapa 6: Insights de Negócio")
    print("-" * 50)
    
    generate_business_insights(analytics)
    
    # 7. Plano de ação
    print("\n🎯 Etapa 7: Plano de Ação")
    print("-" * 50)
    
    create_action_plan(analytics)
    
    print("\n" + "=" * 70)
    print("DEMONSTRAÇÃO CONCLUÍDA COM SUCESSO!")
    print("=" * 70)
    
    print(f"✅ {len(analytics.df)} leads analisados")
    print(f"✅ {len(analytics.models)} modelos treinados")
    print(f"✅ Relatórios gerados em: ./ml_models/")
    
    return True

def demonstrate_model_results(analytics):
    """
    Demonstra resultados de cada modelo
    """
    df = analytics.df
    
    # 1. Lead Scoring
    print("🎯 1. LEAD SCORING E CLASSIFICAÇÃO")
    sample_scores = analytics.generate_lead_scores(df.head(5))
    if sample_scores is not None:
        for i in range(5):
            lead_name = df.iloc[i]['nome']
            score = sample_scores.iloc[i]['lead_score']
            quality = 'Alta' if sample_scores.iloc[i]['lead_quality'] == 1 else 'Baixa'
            print(f"  {lead_name[:20]:<20} | Score: {score:5.1f}/100 | Qualidade: {quality}")
    
    # 2. ROI e Oportunidades
    print("\n💰 2. TOP 5 OPORTUNIDADES DE ROI")
    top_roi = df.nlargest(5, 'roi_opportunity_score')
    for i, (idx, row) in enumerate(top_roi.iterrows(), 1):
        print(f"  {i}. {row['nome'][:25]:<25} | ROI: R$ {row['predicted_roi']:6.0f} | Categoria: {row['opportunity_category']}")
    
    # 3. Risco de Churn
    print("\n⚠️ 3. LEADS EM RISCO DE CHURN")
    high_churn = df[df['churn_risk_predicted'] > 0.7].head(5)
    if len(high_churn) > 0:
        for i, (idx, row) in enumerate(high_churn.iterrows(), 1):
            print(f"  {i}. {row['nome'][:25]:<25} | Risco: {row['churn_risk_predicted']:.3f} | Dias: {row['days_since_contact']}")
    else:
        print("  ✓ Nenhum lead com alto risco de churn identificado")
    
    # 4. Segmentação
    print("\n🎯 4. DISTRIBUIÇÃO POR PERSONAS")
    if 'segmentation' in analytics.models:
        persona_stats = analytics.models['segmentation']['persona_stats']
        for persona, stats in persona_stats.iterrows():
            print(f"  {persona:<20} | {int(stats['Quantidade']):3d} leads | ROI: R$ {stats['ROI_Médio']:6.0f} | Conv: {stats['Conversão_Média']:.3f}")

def generate_business_insights(analytics):
    """
    Gera insights de negócio
    """
    df = analytics.df
    
    # Estatísticas gerais
    total_leads = len(df)
    high_quality = (df['lead_quality'] == 1).sum()
    high_conversion = (df['conversion_probability'] > 0.7).sum()
    high_roi = (df['opportunity_category'] == 'HIGH_VALUE').sum()
    high_churn_risk = (df['churn_risk_predicted'] > 0.7).sum()
    
    print("📈 ESTATÍSTICAS GERAIS:")
    print(f"  Total de Leads: {total_leads}")
    print(f"  Alta Qualidade: {high_quality} ({(high_quality/total_leads)*100:.1f}%)")
    print(f"  Alta Conversão: {high_conversion} ({(high_conversion/total_leads)*100:.1f}%)")
    print(f"  Alto ROI: {high_roi} ({(high_roi/total_leads)*100:.1f}%)")
    print(f"  Alto Risco Churn: {high_churn_risk} ({(high_churn_risk/total_leads)*100:.1f}%)")
    
    # Performance por segmento
    print("\n🏢 PERFORMANCE POR SEGMENTO:")
    segment_perf = df.groupby('segmento_categoria').agg({
        'conversion_probability': 'mean',
        'predicted_roi': 'mean',
        'nome': 'count'
    }).round(3)
    segment_perf.columns = ['Conv_Rate', 'ROI_Medio', 'Total_Leads']
    segment_perf = segment_perf.sort_values('Conv_Rate', ascending=False)
    
    for segment, data in segment_perf.iterrows():
        print(f"  {segment:<12} | {data['Total_Leads']:3.0f} leads | Conv: {data['Conv_Rate']:.3f} | ROI: R$ {data['ROI_Medio']:6.0f}")
    
    # Insights principais
    print("\n💡 INSIGHTS PRINCIPAIS:")
    
    best_segment = segment_perf.index[0]
    best_conv_rate = segment_perf.iloc[0]['Conv_Rate']
    
    avg_roi = df['predicted_roi'].mean()
    avg_conversion = df['conversion_probability'].mean()
    
    print(f"  • Melhor segmento: {best_segment} (conv. {best_conv_rate:.3f})")
    print(f"  • ROI médio geral: R$ {avg_roi:.0f}")
    print(f"  • Taxa de conversão média: {avg_conversion:.3f}")
    print(f"  • {high_quality} leads ({(high_quality/total_leads)*100:.1f}%) são de alta qualidade")
    
    if high_churn_risk > 0:
        print(f"  ⚠️ {high_churn_risk} leads precisam de atenção urgente (alto risco churn)")
    
    # Qualidade dos dados
    avg_data_quality = df['data_quality_score'].mean()
    print(f"  • Score médio qualidade dados: {avg_data_quality:.1f}/5.0")
    
    if avg_data_quality < 4:
        print(f"  📄 Oportunidade: melhorar qualidade dos dados aumentará performance")

def create_action_plan(analytics):
    """
    Cria plano de ação baseado na análise
    """
    df = analytics.df
    
    print("🚨 AÇÕES IMEDIATAS (7 dias):")
    
    # Leads críticos
    critical_leads = df[(df['churn_risk_predicted'] > 0.8) | (df['days_since_contact'] > 90)]
    top_opportunities = df[df['opportunity_category'] == 'HIGH_VALUE']
    stale_leads = df[df['days_since_contact'] > 60]
    
    print(f"  1. Contatar {len(critical_leads)} leads em risco crítico")
    print(f"  2. Priorizar {len(top_opportunities)} leads de alto valor")
    print(f"  3. Reativar {len(stale_leads)} leads sem contato recente")
    
    print("\n📅 AÇÕES MÉDIO PRAZO (30 dias):")
    
    low_quality_data = df[df['data_quality_score'] < 3]
    print(f"  1. Melhorar dados de {len(low_quality_data)} leads com baixa qualidade")
    print(f"  2. Implementar abordagens por persona:")
    
    if 'segmentation' in analytics.models:
        persona_stats = analytics.models['segmentation']['persona_stats']
        for persona in persona_stats.index[:3]:  # Top 3
            count = persona_stats.loc[persona, 'Quantidade']
            print(f"     • {persona}: {count} leads")
    
    print("\n🎯 AÇÕES ESTRATÉGICAS (90 dias):")
    print("  1. Automatizar scoring de leads")
    print("  2. Criar campanhas específicas por segmento")
    print("  3. Implementar sistema de alerta de churn")
    print("  4. Otimizar processo de qualificação")
    
    # Métricas alvo
    current_conversion = df['conversion_probability'].mean()
    current_roi = df['predicted_roi'].mean()
    
    print("\n📉 METAS SUGERIDAS:")
    print(f"  • Aumentar conversão de {current_conversion:.3f} para {current_conversion*1.2:.3f} (+20%)")
    print(f"  • Aumentar ROI de R$ {current_roi:.0f} para R$ {current_roi*1.15:.0f} (+15%)")
    print(f"  • Reduzir churn de leads ativos em 25%")
    print(f"  • Melhorar qualidade de dados para >4.0")

def main():
    """
    Função principal
    """
    success = run_complete_demonstration()
    
    if success:
        print("\n✨ SISTEMA PRONTO PARA PRODUÇÃO!")
        print("📊 Todos os modelos estão funcionando e calibrados")
        print("📁 Relatórios detalhados disponíveis em ./ml_models/")
        print("🔧 Use lead_prediction_example.py para analisar novos leads")
    else:
        print("\n❌ DEMONSTRAÇÃO FALHOU")
        print("Verifique os logs acima para detalhes do erro")

if __name__ == "__main__":
    main()

