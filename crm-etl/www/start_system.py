#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=================================================
--- Script de Inicialização CRM ETL System ---
=================================================

Script para inicializar o Sistema ETL Inteligente da CRM ETL.
Verifica dependências, configura ambiente e inicia o servidor backend.

Uso:
    python start_system.py --dev          # Modo desenvolvimento
    python start_system.py --prod         # Modo produção
    python start_system.py --install      # Instalar dependências
"""

import os
import sys
import subprocess
import argparse
import logging
from pathlib import Path

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def print_crm_header():
    """Exibe header do CRM"""
    print("=" * 70)
    print("🚀 CRM ETL - ETL System Launcher")
    print("   Sistema ETL Inteligente com IA Generativa")
    print("   Frontend ↔ Backend Integration")
    print("=" * 70)

def check_python_version():
    """Verifica versão do Python"""
    if sys.version_info < (3, 8):
        logger.error("Python 3.8+ é obrigatório")
        logger.error(f"   Versão atual: {sys.version}")
        sys.exit(1)
    
    logger.info(f"✅ Python {sys.version.split()[0]} - OK")

def install_dependencies():
    """Instala dependências necessárias"""
    logger.info("📦 Instalando dependências...")
    
    # Dependências básicas necessárias
    basic_deps = [
        "fastapi==0.104.1",
        "uvicorn[standard]==0.24.0",
        "python-multipart==0.0.6",
        "pandas==2.1.3",
        "numpy==1.24.3",
        "openpyxl==3.1.2",
        "python-dotenv==1.0.0"
    ]
    
    try:
        logger.info("Instalando dependências básicas...")
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "--upgrade"
        ] + basic_deps)
        
        logger.info("✅ Dependências instaladas com sucesso!")
        return True
        
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Erro na instalação: {e}")
        return False

def setup_directories():
    """Configura diretórios necessários"""
    logger.info("📁 Configurando diretórios...")
    
    directories = [
        "backend",
        "www",
        "production_models",
        "logs",
        "data/input",
        "data/output",
        "temp"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        logger.info(f"   ✅ {directory}")

def check_files():
    """Verifica se arquivos necessários existem"""
    logger.info("📄 Verificando arquivos do sistema...")
    
    required_files = [
        ("backend/api_server.py", "Servidor Backend FastAPI"),
        ("www/index.html", "Interface Web Frontend")
    ]
    
    missing_files = []
    for file_path, description in required_files:
        if not Path(file_path).exists():
            missing_files.append((file_path, description))
        else:
            logger.info(f"   ✅ {description}")
    
    if missing_files:
        logger.error("❌ Arquivos faltando:")
        for file_path, description in missing_files:
            logger.error(f"   - {file_path}: {description}")
        return False
    
    return True

def start_server(host="127.0.0.1", port=8000, reload=False):
    """Inicia o servidor FastAPI"""
    logger.info("🚀 Iniciando servidor CRM ETL...")
    logger.info(f"   Modo: {'Desenvolvimento' if reload else 'Produção'}")
    logger.info(f"   Endereço: http://{host}:{port}")
    logger.info(f"   Documentação API: http://{host}:{port}/docs")
    logger.info(f"   Interface Web: http://{host}:{port}/")
    
    try:
        # Mudar para diretório backend
        backend_dir = Path("backend")
        if not backend_dir.exists():
            logger.error("❌ Diretório backend não encontrado!")
            return False
        
        # Comando uvicorn para executar o servidor
        cmd = [
            sys.executable, "-m", "uvicorn",
            "api_server:app",
            "--host", host,
            "--port", str(port)
        ]
        
        if reload:
            cmd.extend(["--reload", "--log-level", "debug"])
        
        # Mostrar comando que será executado
        logger.info("📡 Comando: " + " ".join(cmd))
        logger.info("=" * 70)
        
        # Executar servidor no diretório backend
        os.chdir(backend_dir)
        subprocess.run(cmd)
        
    except KeyboardInterrupt:
        logger.info("\n🛑 Servidor interrompido pelo usuário")
    except Exception as e:
        logger.error(f"❌ Erro ao iniciar servidor: {e}")
        return False
    
    return True

def run_tests():
    """Executa testes básicos do sistema"""
    logger.info("🧪 Executando testes básicos...")
    
    try:
        # Testar importações básicas
        import pandas as pd
        logger.info("   ✅ Pandas - OK")
        
        import numpy as np
        logger.info("   ✅ NumPy - OK")
        
        # Verificar se consegue importar FastAPI
        try:
            from fastapi import FastAPI
            logger.info("   ✅ FastAPI - OK")
        except ImportError:
            logger.warning("   ⚠️ FastAPI não disponível")
            return False
        
        # Verificar estrutura de arquivos
        if not check_files():
            return False
        
        logger.info("✅ Todos os testes básicos passaram!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Erro nos testes: {e}")
        return False

def show_help():
    """Mostra informações de ajuda"""
    print("\n📚 COMO USAR O SISTEMA CRM ETL:")
    print("\n1. Instalar dependências:")
    print("   python start_system.py --install")
    print("\n2. Executar testes:")
    print("   python start_system.py --test")
    print("\n3. Iniciar em desenvolvimento:")
    print("   python start_system.py --dev")
    print("\n4. Iniciar em produção:")
    print("   python start_system.py --prod")
    print("\n🌐 ENDPOINTS DISPONÍVEIS:")
    print("   • Interface Web: http://127.0.0.1:8000/")
    print("   • Documentação API: http://127.0.0.1:8000/docs")
    print("   • POST /etl/run - Executar pipeline ETL")
    print("   • GET /etl/status/{id} - Status da pipeline")
    print("   • GET /etl/download/{id} - Download de resultados")
    print("   • GET /health - Health check")

def main():
    """Função principal"""
    parser = argparse.ArgumentParser(
        description="Inicializador do Sistema ETL CRM ETL",
        epilog="Transformando dados em insights inteligentes!"
    )
    
    parser.add_argument(
        "--dev", action="store_true",
        help="Executar em modo desenvolvimento (auto-reload)"
    )
    
    parser.add_argument(
        "--prod", action="store_true",
        help="Executar em modo produção"
    )
    
    parser.add_argument(
        "--install", action="store_true",
        help="Instalar dependências necessárias"
    )
    
    parser.add_argument(
        "--test", action="store_true",
        help="Executar testes básicos do sistema"
    )
    
    parser.add_argument(
        "--port", type=int, default=8000,
        help="Porta do servidor (padrão: 8000)"
    )
    
    parser.add_argument(
        "--host", default="127.0.0.1",
        help="Host do servidor (padrão: 127.0.0.1)"
    )
    
    args = parser.parse_args()
    
    print_crm_header()
    
    # Verificar versão do Python
    check_python_version()
    
    # Configurar diretórios
    setup_directories()
    
    # Instalar dependências se solicitado
    if args.install:
        if install_dependencies():
            logger.info("🎉 Instalação concluída! Execute --test para verificar.")
        else:
            logger.error("❌ Falha na instalação")
            sys.exit(1)
        return
    
    # Executar testes se solicitado
    if args.test:
        if run_tests():
            logger.info("🎉 Sistema pronto para uso!")
            show_help()
        else:
            logger.error("❌ Testes falharam. Execute --install primeiro.")
            sys.exit(1)
        return
    
    # Verificar se arquivos existem antes de iniciar servidor
    if not check_files():
        logger.error("❌ Arquivos necessários não encontrados!")
        logger.info("💡 Certifique-se de que os arquivos backend/api_server.py e www/index.html existem.")
        sys.exit(1)
    
    # Iniciar servidor
    if args.dev or args.prod:
        start_server(host=args.host, port=args.port, reload=args.dev)
    else:
        logger.info("ℹ️ Nenhuma ação especificada.")
        show_help()

if __name__ == "__main__":
    main()
