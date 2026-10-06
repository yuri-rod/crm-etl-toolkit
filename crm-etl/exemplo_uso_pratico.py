#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Exemplo Prático de Uso da Ferramenta ETL Unificada com IA
CRM ETL

Este exemplo demonstra como usar a ferramenta ETL unificada
para processar dados de leads de forma inteligente.
"""

import asyncio
import pandas as pd
import os
from datetime import datetime, timedelta
import random
from pathlib import Path

# Importar nossa ferramenta unificada
from ferramenta_etl_ai_unificada import (
    IntelligentETLPipeline,
    PipelineConfig,
    AIModelConfig,
    ProcessingMode,
    DataType
)

def criar_dados_exemplo():
    """Cria um dataset de exemplo para demonstração"""
    print("📊 Criando dados de exemplo...")
    
    # Dados simulados de leads
    nomes = [
        "João Silva", "Maria Santos", "Pedro Oliveira", "Ana Costa",
        "Carlos Ferreira", "Julia Rodrigues", "Bruno Almeida", "Fernanda Lima",
        "Roberto Souza", "Camila Pereira", "Lucas Barbosa", "Patricia Gomes",
        "Ricardo Martins", "Monica Ribeiro", "Felipe Carvalho", "Beatriz Nunes"
    ]
    
    empresas = [
        "Tech Solutions", "Data Corp", "AI Innovations", "Smart Systems",
        "Digital Wave", "Future Tech", "Cloud Masters", "Cyber Solutions",
        "Quantum Data", "Neural Networks", "Blockchain Inc", "IoT Dynamics"
    ]
    
    cargos = [
        "Desenvolvedor", "Analista de Dados", "Gerente de TI", "CTO",
        "Product Manager", "Data Scientist", "DevOps Engineer", "Arquiteto de Software"
    ]
    
    dominios = ["gmail.com", "empresa.com", "tech.com.br", "outlook.com", "yahoo.com.br"]
    
    # Gerar dados
    dados = []
    for i in range(50):
        nome = random.choice(nomes)
        empresa = random.choice(empresas)
        cargo = random.choice(cargos)
        
        # Email com alguns erros propositais
        email_base = nome.lower().replace(" ", ".").replace("ç", "c").replace("ã", "a")
        dominio = random.choice(dominios)
        email = f"{email_base}@{dominio}"
        
        # Telefone com formatos diferentes
        ddd = random.choice(["11", "21", "31", "41", "51"])
        numero = f"{random.randint(90000, 99999)}{random.randint(1000, 9999)}"
        telefone_formats = [
            f"({ddd}) {numero[:5]}-{numero[5:]}",
            f"{ddd}{numero}",
            f"+55{ddd}{numero}",
            f"{ddd} {numero[:5]} {numero[5:]}"
        ]
        telefone = random.choice(telefone_formats)
        
        # Outros campos
        valor_contrato = random.randint(5000, 100000)
        data_cadastro = datetime.now() - timedelta(days=random.randint(1, 365))
        status = random.choice(["ativo", "inativo", "pendente", "convertido"])
        
        # LinkedIn com alguns vazios
        linkedin = f"https://linkedin.com/in/{email_base}" if random.random() > 0.3 else ""
        
        # Qualidade do lead (para treinamento de modelo)
        qualidade = "alta" if valor_contrato > 50000 and status == "ativo" else "baixa"
        
        dados.append({
            "nome": nome,
            "email": email,
            "telefone": telefone,
            "empresa": empresa,
            "cargo": cargo,
            "valor_contrato": valor_contrato,
            "data_cadastro": data_cadastro,
            "status": status,
            "linkedin": linkedin,
            "qualidade_lead": qualidade
        })
    
    # Adicionar alguns registros com dados faltantes
    for i in range(10):
        dados.append({
            "nome": random.choice(nomes),
            "email": "" if random.random() > 0.7 else f"teste{i}@exemplo.com",
            "telefone": "" if random.random() > 0.8 else f"11999999{i:03d}",
            "empresa": random.choice(empresas),
            "cargo": "",
            "valor_contrato": None if random.random() > 0.6 else random.randint(1000, 50000),
            "data_cadastro": datetime.now() - timedelta(days=random.randint(1, 30)),
            "status": "pendente",
            "linkedin": "",
            "qualidade_lead": "baixa"
        })
    
    df = pd.DataFrame(dados)
    
    # Salvar dados de exemplo
    Path("data").mkdir(exist_ok=True)
    df.to_csv("data/leads_exemplo.csv", index=False, encoding='utf-8-sig', sep=';')
    print(f"✅ Dados de exemplo criados: {len(df)} registros em 'data/leads_exemplo.csv'")
    
    return df

async def exemplo_basico():
    """Exemplo básico de uso da pipeline"""
    print("\n🚀 EXEMPLO 1: Processamento Básico")
    print("=" * 50)
    
    # Configuração básica
    config = PipelineConfig(
        name="Exemplo_Basico",
        description="Processamento básico de leads",
        ai_enabled=True,
        auto_repair=True,
        monitoring_enabled=True
    )
    
    ai_config = AIModelConfig(
        use_local_models=False,  # Usar apenas processamento local
        max_tokens=1024
    )
    
    # Criar pipeline
    pipeline = IntelligentETLPipeline(config, ai_config)
    
    try:
        # Executar pipeline completa
        report = await pipeline.run_full_pipeline(
            source="data/leads_exemplo.csv",
            output_path="data/output/leads_processados_basico.xlsx"
        )
        
        print("✅ Pipeline básica executada com sucesso!")
        print(f"📊 Registros processados: {report['data_overview']['total_records']}")
        print(f"📈 Colunas geradas: {report['data_overview']['total_columns']}")
        print(f"🎯 Qualidade dos dados: {report['data_quality']['missing_percentage']}")
        
    except Exception as e:
        print(f"❌ Erro no exemplo básico: {e}")
    finally:
        pipeline.cleanup_resources()

async def exemplo_transformacoes():
    """Exemplo com transformações customizadas"""
    print("\n🔧 EXEMPLO 2: Transformações Customizadas")
    print("=" * 50)
    
    config = PipelineConfig(
        name="Exemplo_Transformacoes",
        description="Pipeline com transformações customizadas",
        ai_enabled=True
    )
    
    ai_config = AIModelConfig(use_local_models=False)
    pipeline = IntelligentETLPipeline(config, ai_config)
    
    try:
        # Transformações em linguagem natural
        transformacoes = [
            "Filtrar registros com valor maior que 20000",
            "Ordenar por data de cadastro decrescente",
            "Criar coluna de score de qualidade baseada em completude"
        ]
        
        report = await pipeline.run_full_pipeline(
            source="data/leads_exemplo.csv",
            output_path="data/output/leads_transformados.xlsx",
            transformations=transformacoes
        )
        
        print("✅ Pipeline com transformações executada!")
        print(f"🔄 Transformações aplicadas: {len(transformacoes)}")
        
    except Exception as e:
        print(f"❌ Erro nas transformações: {e}")
    finally:
        pipeline.cleanup_resources()

async def exemplo_fontes_multiplas():
    """Exemplo com múltiplas fontes de dados"""
    print("\n🔗 EXEMPLO 3: Múltiplas Fontes de Dados")
    print("=" * 50)
    
    config = PipelineConfig(
        name="Exemplo_Multiplas_Fontes",
        description="Processamento de múltiplas fontes"
    )
    
    ai_config = AIModelConfig(use_local_models=False)
    pipeline = IntelligentETLPipeline(config, ai_config)
    
    try:
        # Fonte 1: Arquivo CSV
        print("📁 Processando fonte 1: Arquivo CSV")
        report1 = await pipeline.run_full_pipeline(
            source="data/leads_exemplo.csv",
            output_path="data/output/fonte1_csv.xlsx"
        )
        
        # Fonte 2: DataFrame em memória
        print("💾 Processando fonte 2: DataFrame em memória")
        df_memoria = pd.DataFrame({
            'nome': ['Cliente A', 'Cliente B'],
            'email': ['clientea@test.com', 'clienteb@test.com'],
            'valor': [15000, 25000]
        })
        
        report2 = await pipeline.run_full_pipeline(
            source=df_memoria,
            output_path="data/output/fonte2_memoria.xlsx"
        )
        
        print("✅ Múltiplas fontes processadas com sucesso!")
        
    except Exception as e:
        print(f"❌ Erro com múltiplas fontes: {e}")
    finally:
        pipeline.cleanup_resources()

def exemplo_analise_dados():
    """Exemplo de análise dos dados processados"""
    print("\n📈 EXEMPLO 4: Análise dos Dados Processados")
    print("=" * 50)
    
    try:
        # Ler dados processados
        arquivo_processado = "data/output/leads_processados_basico.xlsx"
        
        if os.path.exists(arquivo_processado):
            df = pd.read_excel(arquivo_processado, sheet_name="Dados")
            
            print(f"📊 Análise do arquivo: {arquivo_processado}")
            print(f"Total de registros: {len(df)}")
            print(f"Total de colunas: {len(df.columns)}")
            
            # Análise de qualidade
            print("\n🎯 Qualidade dos Dados:")
            missing_data = df.isnull().sum()
            for col in missing_data[missing_data > 0].index:
                pct = (missing_data[col] / len(df)) * 100
                print(f"  - {col}: {missing_data[col]} valores faltantes ({pct:.1f}%)")
            
            # Análise de features criadas
            print("\n🔧 Features Criadas Automaticamente:")
            features_ai = [col for col in df.columns if any(suffix in col for suffix in 
                          ['_length', '_score', '_quality', '_has_', '_is_', '_count'])]
            for feature in features_ai[:10]:  # Mostrar apenas as primeiras 10
                print(f"  - {feature}")
            
            # Estatísticas dos valores
            if 'valor_contrato' in df.columns:
                print(f"\n💰 Análise de Valores:")
                print(f"  - Valor médio: R$ {df['valor_contrato'].mean():,.2f}")
                print(f"  - Valor mediano: R$ {df['valor_contrato'].median():,.2f}")
                print(f"  - Maior valor: R$ {df['valor_contrato'].max():,.2f}")
        else:
            print("❌ Arquivo processado não encontrado. Execute o exemplo básico primeiro.")
            
    except Exception as e:
        print(f"❌ Erro na análise: {e}")

async def exemplo_com_ia():
    """Exemplo usando IA (se disponível)"""
    print("\n🤖 EXEMPLO 5: Processamento com IA (Se Disponível)")
    print("=" * 50)
    
    # Verificar se há chaves de IA configuradas
    claude_key = os.getenv('ANTHROPIC_API_KEY')
    openai_key = os.getenv('OPENAI_API_KEY')
    
    if not claude_key and not openai_key:
        print("ℹ️ Nenhuma chave de IA configurada.")
        print("Para usar IA, configure:")
        print("  export ANTHROPIC_API_KEY='sua_chave'")
        print("  export OPENAI_API_KEY='sua_chave'")
        return
    
    config = PipelineConfig(
        name="Exemplo_IA",
        description="Pipeline com IA avançada",
        ai_enabled=True
    )
    
    ai_config = AIModelConfig(
        claude_api_key=claude_key,
        openai_api_key=openai_key,
        max_tokens=2048,
        temperature=0.7
    )
    
    pipeline = IntelligentETLPipeline(config, ai_config)
    
    try:
        # Carregar dados
        df = pipeline.intelligent_data_loading("data/leads_exemplo.csv")
        
        # Usar IA para análise
        contexto = f"Dataset com {len(df)} registros e colunas: {list(df.columns)}"
        
        resposta = await pipeline.process_with_ai(
            "Analise este dataset de leads e sugira 3 transformações específicas para melhorar a qualidade e valor dos dados para análise de vendas",
            data_context=contexto
        )
        
        print("🧠 Sugestões da IA:")
        print(resposta)
        
        # Aplicar pipeline com as sugestões
        report = await pipeline.run_full_pipeline(
            source=df,
            output_path="data/output/leads_com_ia.xlsx",
            transformations=[
                "Criar score de prioridade baseado em valor e engajamento",
                "Categorizar leads por potencial de conversão"
            ]
        )
        
        print("✅ Pipeline com IA executada!")
        
    except Exception as e:
        print(f"❌ Erro no exemplo com IA: {e}")
    finally:
        pipeline.cleanup_resources()

async def main():
    """Função principal que executa todos os exemplos"""
    print("🎯 EXEMPLOS PRÁTICOS - FERRAMENTA ETL UNIFICADA COM IA")
    print("CRM ETL")
    print("=" * 60)
    
    # Criar diretórios necessários
    Path("data/output").mkdir(parents=True, exist_ok=True)
    
    # Criar dados de exemplo
    criar_dados_exemplo()
    
    # Executar exemplos
    try:
        await exemplo_basico()
        await exemplo_transformacoes()
        await exemplo_fontes_multiplas()
        exemplo_analise_dados()
        await exemplo_com_ia()
        
        print("\n🎉 TODOS OS EXEMPLOS EXECUTADOS COM SUCESSO!")
        print("\n📁 Arquivos gerados em 'data/output/':")
        output_dir = Path("data/output")
        if output_dir.exists():
            for arquivo in output_dir.glob("*"):
                print(f"  - {arquivo.name}")
        
        print("\n📚 Para mais informações, consulte:")
        print("  - LEIA_ME_FERRAMENTA_UNIFICADA.md")
        print("  - config_exemplo.yaml")
        
        print("\n✨ CRM ETL - Pipeline ETL com IA")
        
    except Exception as e:
        print(f"\n❌ Erro geral nos exemplos: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n❌ Execução cancelada pelo usuário")
    except Exception as e:
        print(f"\n\n❌ Erro inesperado: {e}")
        print("Verifique se todas as dependências estão instaladas:")
        print("python instalar_dependencias.py")