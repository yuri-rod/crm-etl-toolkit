#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de Instalação Inteligente de Dependências
CRM ETL

Este script instala automaticamente as dependências necessárias
para a ferramenta ETL unificada, adaptando-se ao ambiente do usuário.
"""

import subprocess
import sys
import os
import importlib
from typing import List, Dict, Tuple

def verificar_python_version():
    """Verifica se a versão do Python é compatível"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8+ é necessário. Versão atual:", f"{version.major}.{version.minor}")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} detectado")
    return True

def verificar_pip():
    """Verifica se pip está disponível"""
    try:
        subprocess.run([sys.executable, "-m", "pip", "--version"], 
                      capture_output=True, check=True)
        print("✅ pip disponível")
        return True
    except subprocess.CalledProcessError:
        print("❌ pip não encontrado")
        return False

def instalar_pacote(pacote: str, versao: str = None) -> bool:
    """Instala um pacote específico"""
    try:
        package_spec = f"{pacote}>={versao}" if versao else pacote
        print(f"📦 Instalando {package_spec}...")
        
        result = subprocess.run([
            sys.executable, "-m", "pip", "install", package_spec
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ {pacote} instalado com sucesso")
            return True
        else:
            print(f"❌ Erro ao instalar {pacote}: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Erro inesperado ao instalar {pacote}: {e}")
        return False

def verificar_pacote_instalado(pacote: str) -> bool:
    """Verifica se um pacote já está instalado"""
    try:
        importlib.import_module(pacote)
        return True
    except ImportError:
        return False

def main():
    """Função principal de instalação"""
    print("🚀 Iniciando instalação de dependências para Pipeline ETL com IA")
    print("=" * 60)
    
    # Verificações básicas
    if not verificar_python_version():
        sys.exit(1)
    
    if not verificar_pip():
        sys.exit(1)
    
    # Dependências obrigatórias
    dependencias_obrigatorias = {
        'pandas': '1.5.0',
        'numpy': '1.21.0',
        'sklearn': '1.0.0',  # scikit-learn
        'sqlalchemy': '1.4.0',
        'requests': '2.25.0',
        'tqdm': '4.62.0'
    }
    
    # Dependências opcionais com descrição
    dependencias_opcionais = {
        'transformers': {
            'versao': '4.20.0',
            'descricao': 'Modelos de IA locais (NLP)',
            'categoria': 'IA'
        },
        'torch': {
            'versao': '1.12.0',
            'descricao': 'Backend para modelos de IA',
            'categoria': 'IA'
        },
        'anthropic': {
            'versao': '0.5.0',
            'descricao': 'API do Claude (Anthropic)',
            'categoria': 'IA'
        },
        'openai': {
            'versao': '0.27.0',
            'descricao': 'API do OpenAI (GPT)',
            'categoria': 'IA'
        },
        'pyarrow': {
            'versao': '8.0.0',
            'descricao': 'Suporte a formato Parquet',
            'categoria': 'Dados'
        },
        'polars': {
            'versao': '0.18.0',
            'descricao': 'DataFrame engine alternativo (rápido)',
            'categoria': 'Dados'
        },
        'duckdb': {
            'versao': '0.8.0',
            'descricao': 'SQL engine in-memory',
            'categoria': 'Dados'
        },
        'psutil': {
            'versao': '5.8.0',
            'descricao': 'Monitoramento do sistema',
            'categoria': 'Monitoramento'
        },
        'memory_profiler': {
            'versao': '0.60.0',
            'descricao': 'Profiling de memória',
            'categoria': 'Monitoramento'
        },
        'pyyaml': {
            'versao': '6.0',
            'descricao': 'Arquivos de configuração YAML',
            'categoria': 'Configuração'
        },
        'schedule': {
            'versao': '1.2.0',
            'descricao': 'Agendamento de tarefas',
            'categoria': 'Utilitários'
        },
        'chardet': {
            'versao': '5.0.0',
            'descricao': 'Detecção automática de encoding',
            'categoria': 'Utilitários'
        },
        'openpyxl': {
            'versao': '3.0.0',
            'descricao': 'Arquivos Excel (.xlsx)',
            'categoria': 'Formatos'
        },
        'boto3': {
            'versao': '1.20.0',
            'descricao': 'AWS S3 e outros serviços',
            'categoria': 'Cloud'
        }
    }
    
    print("\n📋 INSTALANDO DEPENDÊNCIAS OBRIGATÓRIAS")
    print("-" * 40)
    
    # Instalar dependências obrigatórias
    falhas_obrigatorias = []
    for pacote, versao in dependencias_obrigatorias.items():
        # Verificar nomes especiais
        nome_import = 'sklearn' if pacote == 'sklearn' else pacote
        
        if verificar_pacote_instalado(nome_import):
            print(f"✅ {pacote} já instalado")
        else:
            # scikit-learn tem nome diferente para instalação
            nome_install = 'scikit-learn' if pacote == 'sklearn' else pacote
            if not instalar_pacote(nome_install, versao):
                falhas_obrigatorias.append(pacote)
    
    if falhas_obrigatorias:
        print(f"\n❌ Falha ao instalar dependências obrigatórias: {', '.join(falhas_obrigatorias)}")
        print("A ferramenta pode não funcionar completamente.")
    else:
        print("\n✅ Todas as dependências obrigatórias foram instaladas!")
    
    print("\n🔧 DEPENDÊNCIAS OPCIONAIS")
    print("-" * 40)
    print("As dependências opcionais adicionam funcionalidades específicas.")
    print("Você pode pular qualquer uma e instalar depois conforme necessário.\n")
    
    # Agrupar por categoria
    categorias = {}
    for pacote, info in dependencias_opcionais.items():
        categoria = info['categoria']
        if categoria not in categorias:
            categorias[categoria] = []
        categorias[categoria].append((pacote, info))
    
    # Instalar por categoria
    for categoria, pacotes in categorias.items():
        print(f"\n📂 Categoria: {categoria}")
        print("-" * 30)
        
        for pacote, info in pacotes:
            print(f"\n🔍 {pacote} - {info['descricao']}")
            
            if verificar_pacote_instalado(pacote):
                print(f"✅ Já instalado")
                continue
            
            # Perguntar ao usuário (modo interativo)
            if sys.stdin.isatty():  # Terminal interativo
                resposta = input(f"Instalar {pacote}? (s/N): ").lower().strip()
                if resposta in ['s', 'sim', 'y', 'yes']:
                    instalar_pacote(pacote, info['versao'])
                else:
                    print(f"⏭️ Pulando {pacote}")
            else:
                # Modo não-interativo: instalar dependências básicas
                if categoria in ['Configuração', 'Utilitários', 'Formatos']:
                    instalar_pacote(pacote, info['versao'])
                else:
                    print(f"⏭️ Pulando {pacote} (modo não-interativo)")
    
    print("\n" + "=" * 60)
    print("🎉 INSTALAÇÃO CONCLUÍDA!")
    print("\n📝 PRÓXIMOS PASSOS:")
    print("1. Configure suas chaves de API (opcional):")
    print("   export ANTHROPIC_API_KEY='sua_chave_claude'")
    print("   export OPENAI_API_KEY='sua_chave_openai'")
    print("\n2. Copie e ajuste o arquivo de configuração:")
    print("   cp config_exemplo.yaml minha_config.yaml")
    print("\n3. Execute a ferramenta:")
    print("   python ferramenta_etl_ai_unificada.py")
    print("\n4. Consulte a documentação:")
    print("   cat LEIA_ME_FERRAMENTA_UNIFICADA.md")
    print("\n✨ CRM ETL - Pipeline ETL com IA pronta para uso!")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Instalação cancelada pelo usuário")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Erro inesperado: {e}")
        sys.exit(1)