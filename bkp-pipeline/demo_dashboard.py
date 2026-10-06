#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Demo do Dashboard Interativo CRM CRM
Script de demonstração com dados sintéticos
"""

import os
import sys
from datetime import datetime

# Adicionar o diretório atual ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dashboard_interativo import DashboardCRM

def main():
    """
    Função principal para demonstrar o dashboard
    """
    print("\n" + "="*60)
    print("🚀 DEMO - Dashboard Interativo CRM CRM")
    print("="*60)
    print("\n📊 Funcionalidades implementadas:")
    print("   ✅ Painel com segmentos, funil, scores, ROI")
    print("   ✅ Risco de churn e ranking dos leads")
    print("   ✅ Tooltips em português para todos os elementos")
    print("   ✅ Exportação HTML para compartilhamento offline")
    print("   ✅ Interface amigável para decisores não técnicos")
    print("   ✅ Call-to-actions inteligentes")
    
    print("\n📝 Recursos do dashboard:")
    print("   🎯 Funil de vendas interativo")
    print("   📊 Análise detalhada por segmentos")
    print("   🏆 Ranking dos melhores leads")
    print("   💰 Análise de ROI por origem")
    print("   ⚠️ Monitoramento de risco de churn")
    print("   📥 Exportação HTML para uso offline")
    
    print("\n🖥️ Tecnologias utilizadas:")
    print("   - Dash (framework web interativo)")
    print("   - Plotly (visualizações avançadas)")
    print("   - Pandas (processamento de dados)")
    print("   - Machine Learning integrado")
    
    # Verificar se existe arquivo de dados
    data_files = [
        'dataset_unificado_20250611_160521_61aac20d.csv',
        'synthetic_crm_data.csv'
    ]
    
    data_path = None
    for file in data_files:
        if os.path.exists(file):
            data_path = file
            print(f"\n📄 Usando arquivo de dados: {file}")
            break
    
    if not data_path:
        print("\n🧩 Nenhum arquivo de dados encontrado. Usando dados sintéticos.")
    
    print("\n🚀 Iniciando dashboard...")
    print("🌍 Acesse: http://127.0.0.1:8050")
    print("\n📱 Controles disponíveis:")
    print("   - Botão 'Atualizar Dados' para recarregar")
    print("   - Botão 'Exportar HTML' para gerar versão offline")
    print("   - Hover nos gráficos para tooltips detalhados")
    print("   - Tabela de ranking com filtros e ordenação")
    
    print("\n✍️ Pressione Ctrl+C para parar o servidor")
    print("="*60)
    
    # Criar e executar dashboard
    try:
        dashboard = DashboardCRM(data_path=data_path)
        dashboard.run(debug=False, port=8050, host='127.0.0.1')
    except KeyboardInterrupt:
        print("\n\n📺 Dashboard encerrado pelo usuário.")
        print("🚀 Obrigado por usar o Dashboard CRM CRM!")
    except Exception as e:
        print(f"\n❌ Erro ao executar dashboard: {e}")
        print("\n🔧 Soluções:")
        print("   1. Instale as dependências: pip install -r requirements.txt")
        print("   2. Verifique se o Python é versão 3.8 ou superior")
        print("   3. Certifique-se de que a porta 8050 está livre")

if __name__ == '__main__':
    main()

