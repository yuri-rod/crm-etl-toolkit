#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EXEMPLO DE USO DO PROCESSADOR DE LEADS
======================================

Demonstra como usar o processador de dados para preparar
leads para qualificação automática com ML.

Autor: Sistema de Qualificação de Leads
Data: 2025-07-24
"""

from processador_dados_leads import ProcessadorDadosLeads
from pathlib import Path
import pandas as pd


def exemplo_basico():
    """Exemplo básico de processamento de leads."""
    print("=== EXEMPLO BÁSICO DE PROCESSAMENTO ===\n")
    
    # Inicializar processador
    processador = ProcessadorDadosLeads()
    
    # Criar diretório de dados se não existir
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    
    # Processar todos os CSVs no diretório data/
    try:
        resultado = processador.executar_pipeline_completo(
            diretorio_entrada="data",
            pattern="*.csv"
        )
        
        print(f"\n✅ Processamento concluído!")
        print(f"📁 Arquivo gerado: {resultado['caminho_csv']}")
        print(f"📊 Total de registros: {resultado['total_registros']}")
        
    except FileNotFoundError:
        print("⚠️ Nenhum arquivo CSV encontrado no diretório 'data/'")
        print("💡 Adicione arquivos CSV de leads ao diretório para processar")


def exemplo_com_dados_especificos():
    """Exemplo processando arquivos específicos."""
    print("\n=== EXEMPLO COM ARQUIVOS ESPECÍFICOS ===\n")
    
    processador = ProcessadorDadosLeads()
    
    # Processar apenas arquivos que começam com "leads_"
    try:
        resultado = processador.executar_pipeline_completo(
            diretorio_entrada="data",
            pattern="leads_*.csv"
        )
        
        # Carregar dados processados
        df = pd.read_csv(resultado['caminho_csv'])
        
        print("\n📊 Análise dos dados processados:")
        print(f"  • Total de leads: {len(df)}")
        print(f"  • Leads de alta qualidade: {len(df[df['classificacao_lead'] == 'Alta'])}")
        print(f"  • Leads de muito alta qualidade: {len(df[df['classificacao_lead'] == 'Muito Alta'])}")
        print(f"  • Score médio de qualidade: {df['score_qualidade_lead'].mean():.2f}")
        
    except Exception as e:
        print(f"❌ Erro: {str(e)}")


def exemplo_analise_features():
    """Exemplo de análise das features geradas."""
    print("\n=== ANÁLISE DE FEATURES PARA ML ===\n")
    
    # Procurar arquivo mais recente de leads processados
    data_dir = Path("data")
    arquivos_processados = list(data_dir.glob("leads_processados_*.csv"))
    
    if not arquivos_processados:
        print("❌ Nenhum arquivo de leads processados encontrado")
        print("💡 Execute primeiro o processamento básico")
        return
    
    # Carregar arquivo mais recente
    arquivo_mais_recente = max(arquivos_processados, key=lambda f: f.stat().st_mtime)
    df = pd.read_csv(arquivo_mais_recente)
    
    print(f"📁 Analisando: {arquivo_mais_recente.name}")
    print(f"📊 Total de registros: {len(df)}\n")
    
    # Features numéricas para ML
    features_ml = [
        'completude_criticos',
        'completude_importantes',
        'cpf_valido',
        'cnpj_valido',
        'email_valido',
        'score_engajamento',
        'score_porte_empresa',
        'score_recencia',
        'score_qualidade_lead'
    ]
    
    print("🔬 Features disponíveis para ML:")
    for feature in features_ml:
        if feature in df.columns:
            print(f"  • {feature}:")
            print(f"    - Média: {df[feature].mean():.3f}")
            print(f"    - Min/Max: {df[feature].min():.3f} / {df[feature].max():.3f}")
            print(f"    - Valores únicos: {df[feature].nunique()}")
    
    # Correlação com score de qualidade
    print("\n📈 Correlação com score_qualidade_lead:")
    for feature in features_ml[:-1]:  # Excluir o próprio score_qualidade_lead
        if feature in df.columns:
            corr = df[feature].corr(df['score_qualidade_lead'])
            print(f"  • {feature}: {corr:.3f}")
    
    # Distribuição de classificação
    print("\n🎯 Distribuição de classificação de leads:")
    print(df['classificacao_lead'].value_counts().to_string())
    
    # Sugestão de próximos passos
    print("\n💡 Próximos passos sugeridos:")
    print("  1. Use estas features para treinar um modelo de classificação")
    print("  2. Considere adicionar features específicas do seu negócio")
    print("  3. Valide os scores com feedback real de vendas")


def criar_dados_exemplo():
    """Cria um arquivo CSV de exemplo para demonstração."""
    print("\n=== CRIANDO DADOS DE EXEMPLO ===\n")
    
    # Criar diretório data se não existir
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    
    # Criar dados de exemplo
    dados_exemplo = {
        'Nome completo': [
            'João Silva Santos', 'Maria Oliveira', 'Pedro Costa', 
            'Ana Paula Souza', 'Carlos Alberto', 'Fernanda Lima'
        ],
        'Email': [
            'joao.silva@email.com', 'maria@empresa.com.br', 'pedro.costa@gmail.com',
            'ana.paula@corp.com', 'carlos@email.com', 'fernanda@empresa.com'
        ],
        'CPF:': [
            '111.444.777-35', '123.456.789-09', '987.654.321-00',
            '456.789.123-00', '789.123.456-00', '321.654.987-00'
        ],
        'WhatsApp': [
            '11987654321', '21998765432', '31987654321',
            '41998765432', '51987654321', '61998765432'
        ],
        'Qual o nome da sua empresa atual?': [
            'Tech Solutions Ltda', 'Comércio ABC', 'Indústria XYZ',
            'Consultoria Beta', 'Serviços Gamma', 'Varejo Delta'
        ],
        'Qual o segmento de atuação da empresa?': [
            'Tecnologia', 'Varejo', 'Indústria', 
            'Consultoria', 'Serviços', 'Comércio'
        ],
        'Qual o seu cargo atual?': [
            'Diretor', 'Gerente', 'Coordenador',
            'Analista', 'Supervisor', 'CEO'
        ],
        'Qual a faixa de funcionários da empresa em que você atua': [
            '51-200', '11-50', '201-500',
            '1-10', '51-200', '11-50'
        ],
        'Submit Date (UTC)': [
            '2025-07-20', '2025-07-21', '2025-07-22',
            '2025-07-23', '2025-07-24', '2025-07-24'
        ]
    }
    
    # Criar DataFrame e salvar
    df = pd.DataFrame(dados_exemplo)
    arquivo_exemplo = data_dir / "leads_exemplo.csv"
    df.to_csv(arquivo_exemplo, index=False, encoding='utf-8')
    
    print(f"✅ Arquivo de exemplo criado: {arquivo_exemplo}")
    print(f"📊 Total de registros: {len(df)}")
    print("\n💡 Agora você pode executar o processamento!")


if __name__ == "__main__":
    print("🚀 DEMONSTRAÇÃO DO PROCESSADOR DE LEADS\n")
    
    # Verificar se existe diretório de dados
    if not Path("data").exists() or not list(Path("data").glob("*.csv")):
        print("📝 Criando dados de exemplo...")
        criar_dados_exemplo()
        print("\n" + "="*50 + "\n")
    
    # Executar exemplos
    exemplo_basico()
    print("\n" + "="*50 + "\n")
    
    exemplo_com_dados_especificos()
    print("\n" + "="*50 + "\n")
    
    exemplo_analise_features()
    
    print("\n✨ Demonstração concluída!")
    print("\n📚 Para integrar com seu modelo ML:")
    print("   1. Carregue o arquivo de leads processados")
    print("   2. Use as features numéricas para treinar/prever")
    print("   3. Use 'classificacao_lead' como referência inicial")
