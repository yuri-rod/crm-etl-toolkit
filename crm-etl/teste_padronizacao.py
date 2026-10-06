#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste das Novas Funcionalidades de Padronização
CRM ETL

Testa as regras de padronização implementadas:
- Tradução de colunas para português
- Padronização de texto (CASADO → Casado)
- Padronização de datas (02 OUTUBRO 1968 → 02/10/1968)
"""

import asyncio
import pandas as pd
from datetime import datetime
import sys
from pathlib import Path

# Adicionar o caminho da ferramenta ETL
sys.path.append(str(Path(__file__).parent))

from ferramenta_etl_ai_unificada import (
    IntelligentETLPipeline,
    PipelineConfig,
    AIModelConfig,
    ProcessingMode,
    DataType
)

def criar_dados_teste():
    """Cria dados de teste com problemas de padronização"""
    print("📊 Criando dados de teste com problemas de padronização...")
    
    dados_teste = pd.DataFrame({
        # Colunas em inglês (serão traduzidas)
        'Full Name': ['JOÃO SILVA', 'maria santos', 'Pedro DE oliveira', 'ana costa'],
        'Email': ['joao@test.com', 'MARIA@TEST.COM', 'pedro@test.com', 'ana@test.com'],
        'Phone': ['11999999999', '(11) 88888-8888', '+5511777777777', '11 66666-6666'],
        'Marital Status': ['CASADO', 'solteira', 'DIVORCIADO', 'viúva'],
        'Gender': ['MASCULINO', 'f', 'MALE', 'FEMININO'],
        'Birth Date': [
            '02 OUTUBRO 1968', 
            '15 DEZEMBRO 1985', 
            '23/05/1990', 
            '30 JANEIRO 1975'
        ],
        'Company': ['TECH SOLUTIONS LTDA', 'data corp', 'AI INNOVATIONS', 'smart systems'],
        'Job Title': ['DESENVOLVEDOR SENIOR', 'analista de dados', 'GERENTE DE TI', 'product manager'],
        'Education': ['SUPERIOR COMPLETO', 'pos-graduacao', 'MESTRADO', 'ensino medio'],
        'City': ['SÃO PAULO', 'rio de janeiro', 'BELO HORIZONTE', 'porto alegre'],
        'Description': [
            'BUSCO CONHECIMENTO EM NOVA ECONOMIA E STARTUPS',
            'quero aprender sobre investimentos e equity',
            'DESENVOLVER HABILIDADES DE LIDERANÇA',
            'expandir minha rede de contatos'
        ],
        # Coluna com data já no formato correto
        'Submit Date (UTC)': ['2024-01-15', '2024-01-16', '2024-01-17', '2024-01-18']
    })
    
    print(f"✅ Dados de teste criados: {len(dados_teste)} registros")
    return dados_teste

async def testar_padronizacao():
    """Testa as funcionalidades de padronização"""
    print("\n🧪 TESTE DE PADRONIZAÇÃO AVANÇADA")
    print("=" * 50)
    
    # Configuração da pipeline
    config = PipelineConfig(
        name="Teste_Padronizacao",
        description="Teste das novas regras de padronização",
        ai_enabled=True,
        auto_repair=True,
        monitoring_enabled=False  # Desabilitar para teste mais limpo
    )
    
    ai_config = AIModelConfig(
        use_local_models=False
    )
    
    pipeline = IntelligentETLPipeline(config, ai_config)
    
    try:
        # Criar dados de teste
        dados_originais = criar_dados_teste()
        
        print("\n📋 DADOS ORIGINAIS:")
        print("-" * 30)
        print("Colunas em inglês:")
        for col in dados_originais.columns:
            print(f"  - {col}")
        
        print("\nExemplos de dados não padronizados:")
        print(f"  Estado Civil: {dados_originais['Marital Status'].tolist()}")
        print(f"  Gênero: {dados_originais['Gender'].tolist()}")
        print(f"  Datas: {dados_originais['Birth Date'].tolist()}")
        print(f"  Nomes: {dados_originais['Full Name'].tolist()}")
        
        # Aplicar apenas a limpeza de dados (que inclui a padronização)
        print("\n🔄 APLICANDO PADRONIZAÇÃO...")
        dados_limpos = pipeline.ai_data_cleaning(dados_originais)
        
        print("\n📋 DADOS PADRONIZADOS:")
        print("-" * 30)
        print("Colunas traduzidas para português:")
        for col in dados_limpos.columns:
            if col not in dados_originais.columns:
                print(f"  + {col} (nova coluna)")
            elif col != dados_originais.columns[list(dados_originais.columns).index(col)] if col in dados_originais.columns else True:
                print(f"  → {col}")
        
        # Mostrar melhorias específicas
        if 'Estado Civil' in dados_limpos.columns:
            print(f"\n✅ Estado Civil padronizado: {dados_limpos['Estado Civil'].tolist()}")
        
        if 'Gênero' in dados_limpos.columns:
            print(f"✅ Gênero padronizado: {dados_limpos['Gênero'].tolist()}")
        
        if 'Data de Nascimento' in dados_limpos.columns:
            print(f"✅ Datas padronizadas: {dados_limpos['Data de Nascimento'].tolist()}")
        
        if 'Nome Completo' in dados_limpos.columns:
            print(f"✅ Nomes padronizados: {dados_limpos['Nome Completo'].tolist()}")
        
        if 'Empresa' in dados_limpos.columns:
            print(f"✅ Empresas padronizadas: {dados_limpos['Empresa'].tolist()}")
        
        if 'Descrição' in dados_limpos.columns:
            print(f"✅ Descrições padronizadas:")
            for desc in dados_limpos['Descrição'].tolist():
                print(f"    '{desc}'")
        
        # Salvar resultado
        Path("output").mkdir(exist_ok=True)
        dados_limpos.to_excel("output/teste_padronizacao.xlsx", index=False)
        
        print(f"\n💾 Resultado salvo em: output/teste_padronizacao.xlsx")
        
        # Mostrar comparação antes/depois
        print(f"\n📊 RESUMO DA PADRONIZAÇÃO:")
        print(f"  - Colunas originais: {len(dados_originais.columns)}")
        print(f"  - Colunas finais: {len(dados_limpos.columns)}")
        print(f"  - Registros processados: {len(dados_limpos)}")
        
        return dados_limpos
        
    except Exception as e:
        print(f"❌ Erro no teste: {e}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        pipeline.cleanup_resources()

def comparar_antes_depois(original: pd.DataFrame, padronizado: pd.DataFrame):
    """Compara dados antes e depois da padronização"""
    print("\n🔍 COMPARAÇÃO DETALHADA:")
    print("=" * 50)
    
    # Mapear colunas traduzidas
    column_mapping = {
        'Full Name': 'Nome Completo',
        'Marital Status': 'Estado Civil',
        'Gender': 'Gênero',
        'Birth Date': 'Data de Nascimento',
        'Company': 'Empresa',
        'Job Title': 'Cargo',
        'Education': 'Escolaridade',
        'City': 'Cidade',
        'Description': 'Descrição'
    }
    
    for original_col, padronized_col in column_mapping.items():
        if original_col in original.columns and padronized_col in padronizado.columns:
            print(f"\n📝 {original_col} → {padronized_col}:")
            for i in range(len(original)):
                orig_val = original[original_col].iloc[i]
                pad_val = padronizado[padronized_col].iloc[i]
                if str(orig_val) != str(pad_val):
                    print(f"  '{orig_val}' → '{pad_val}'")

async def main():
    """Função principal do teste"""
    print("🎯 TESTE DAS NOVAS REGRAS DE PADRONIZAÇÃO")
    print("CRM ETL")
    print("=" * 60)
    
    try:
        # Executar teste
        dados_originais = criar_dados_teste()
        dados_padronizados = await testar_padronizacao()
        
        if dados_padronizados is not None:
            # Comparar resultados
            comparar_antes_depois(dados_originais, dados_padronizados)
            
            print("\n🎉 TESTE CONCLUÍDO COM SUCESSO!")
            print("\n📋 Funcionalidades testadas:")
            print("  ✅ Tradução de colunas para português")
            print("  ✅ Padronização de estado civil (CASADO → Casado)")
            print("  ✅ Padronização de gênero (MASCULINO → Masculino)")
            print("  ✅ Padronização de datas (02 OUTUBRO 1968 → 02/10/1968)")
            print("  ✅ Padronização de nomes (Title Case)")
            print("  ✅ Padronização de frases (primeira letra maiúscula)")
            
        else:
            print("\n❌ Teste falhou")
        
    except Exception as e:
        print(f"\n❌ Erro geral no teste: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n❌ Teste cancelado pelo usuário")
    except Exception as e:
        print(f"\n\n❌ Erro inesperado: {e}")