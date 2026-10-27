#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=================================================
--- Inicializador do Sistema CRM ETL ---
=================================================

Script para inicializar facilmente o Sistema ETL Inteligente da CRM ETL.
Verifica dependências, configura ambiente e inicia o servidor.

Uso:
    python start_crm_system.py --dev          # Modo desenvolvimento
    python start_crm_system.py --prod         # Modo produção
    python start_crm_system.py --install      # Instalar dependências
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
PROJECT_ROOT = Path(__file__).resolve().parent
BACKEND_DIR = PROJECT_ROOT / "backend"

def print_crm_header():
    """Exibe header do CRM"""
    print("=" * 60)
    print("CRM ETL - ETL System Launcher")
    print("   Sistema ETL Inteligente com IA Generativa")
    print("=" * 60)

def check_python_version():
    """Verifica versão do Python"""
    if sys.version_info < (3, 8):
        logger.error("Python 3.8+ é obrigatório")
        logger.error(f"   Versão atual: {sys.version}")
        sys.exit(1)
    
    logger.info(f"Python {sys.version.split()[0]} - OK")

def check_dependencies():
    """Verifica dependências básicas"""
    required_packages = [
        'pandas', 'numpy', 'scikit-learn', 
        'fastapi', 'uvicorn', 'requests'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            if package == 'scikit-learn':
                import sklearn
            else:
                __import__(package)
            logger.info(f"{package} - OK")
        except ImportError:
            missing_packages.append(package)
            logger.warning(f"{package} - Não instalado")
    
    if missing_packages:
        logger.error("Dependências faltando. Execute:")
        logger.error("   python start_crm_system.py --install")
        return False
    
    return True

def install_dependencies():
    """Instala as dependências locais declaradas em requirements-prod.txt."""
    logger.info("Instalando dependências...")
    
    requirements_file = PROJECT_ROOT / "requirements-prod.txt"
    if not requirements_file.exists():
        logger.error("Arquivo requirements-prod.txt não encontrado")
        return False
    
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", str(requirements_file)
        ])

        return True
        
    except subprocess.CalledProcessError as e:
        logger.error(f"[ERROR] Erro na instalação: {e}")
        return False

def setup_environment():
    """Configura ambiente e diretórios"""
    logger.info("[CONFIG] Configurando ambiente...")
    
    # Criar diretórios necessários
    directories = [
        "backend/production_models",
        "backend/logs",
        "data/input",
        "data/output",
        "temp"
    ]
    
    for directory in directories:
        (PROJECT_ROOT / directory).mkdir(parents=True, exist_ok=True)
        logger.info(f"[DIR] Diretório criado: {directory}")
    
    # Verificar variáveis de ambiente para IA
    api_keys_info = []
    
    if os.getenv("ANTHROPIC_API_KEY"):
        api_keys_info.append("[OK] ANTHROPIC_API_KEY configurada")
    else:
        api_keys_info.append("[WARN] ANTHROPIC_API_KEY não configurada (IA limitada)")
    
    if os.getenv("OPENAI_API_KEY"):
        api_keys_info.append("[OK] OPENAI_API_KEY configurada")
    else:
        api_keys_info.append("[WARN] OPENAI_API_KEY não configurada (IA limitada)")
    
    for info in api_keys_info:
        logger.info(info)
    
    if not any("[OK]" in info for info in api_keys_info):
        logger.warning("[WARN] Nenhuma API de IA configurada - funcionalidades limitadas")
        logger.info("[INFO] Configure as variáveis de ambiente:")
        logger.info("   export ANTHROPIC_API_KEY='sua_chave_aqui'")
        logger.info("   export OPENAI_API_KEY='sua_chave_aqui'")

def check_backend_files():
    """Verifica se arquivos do backend existem"""
    backend_files = [
        "backend/unificado.py",
        "backend/api_server.py",
        "backend/ai_rule_generator.py",
        "backend/simple_inference.py"
    ]
    
    missing_files = []
    for file_path in backend_files:
        if not (PROJECT_ROOT / file_path).exists():
            missing_files.append(file_path)
    
    if missing_files:
        logger.error("[ERROR] Arquivos do backend faltando:")
        for file_path in missing_files:
            logger.error(f"   {file_path}")
        return False
    
    logger.info("[OK] Todos os arquivos do backend encontrados")
    return True

def start_server(dev_mode=False, port=8000, host="127.0.0.1"):
    """Inicia o servidor FastAPI"""
    logger.info(f"[START] Iniciando servidor CRM ETL...")
    logger.info(f"   Modo: {'Desenvolvimento' if dev_mode else 'Produção'}")
    logger.info(f"   Endereço: http://{host}:{port}")
    logger.info(f"   Documentação: http://{host}:{port}/docs")
    
    try:
        # Comando uvicorn
        cmd = [
            sys.executable, "-m", "uvicorn",
            "api_server:app",
            "--host", host,
            "--port", str(port)
        ]
        
        if dev_mode:
            cmd.extend(["--reload", "--log-level", "debug"])
        
        # Executar servidor
        logger.info("=" * 60)
        return subprocess.run(cmd, cwd=BACKEND_DIR).returncode
        
    except KeyboardInterrupt:
        logger.info("[STOP] Servidor interrompido pelo usuário")
        return 0
    except Exception as e:
        logger.error(f"[ERROR] Erro ao iniciar servidor: {e}")
        return 1

def run_tests():
    """Executa testes básicos do sistema"""
    logger.info("[TEST] Executando testes básicos...")
    
    try:
        # Teste de importação
        sys.path.insert(0, str(BACKEND_DIR))
        
        import unificado
        logger.info("[OK] Teste importação unificado.py - OK")
        
        import ai_rule_generator
        logger.info("[OK] Teste importação ai_rule_generator.py - OK")
        
        import api_server
        logger.info("[OK] Teste importação api_server.py - OK")
        
        # Teste instanciação
        pipeline = unificado.UnifiedCRMPipeline(model_dir=str(BACKEND_DIR / "production_models"))
        logger.info("[OK] Teste instanciação UnifiedCRMPipeline - OK")
        
        generator = ai_rule_generator.AIRuleGenerator()
        logger.info("[OK] Teste instanciação AIRuleGenerator - OK")
        
        logger.info("[OK] Todos os testes básicos passaram!")
        return True
        
    except Exception as e:
        logger.error(f"[ERROR] Erro nos testes: {e}")
        return False

def main():
    """Função principal"""
    parser = argparse.ArgumentParser(
        description="Inicializador do Sistema ETL CRM ETL"
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
        help="Instalar dependências"
    )
    
    parser.add_argument(
        "--test", action="store_true",
        help="Executar testes básicos"
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
    
    # Instalar dependências se solicitado
    if args.install:
        if install_dependencies():
            logger.info("[OK] Instalação concluída!")
        else:
            logger.error("[ERROR] Falha na instalação")
            sys.exit(1)
        return
    
    # Executar testes se solicitado
    if args.test:
        if not check_dependencies():
            sys.exit(1)
        if not check_backend_files():
            sys.exit(1)
        if run_tests():
            logger.info("[OK] Sistema pronto para uso!")
        else:
            sys.exit(1)
        return
    
    # Verificar dependências
    if not check_dependencies():
        sys.exit(1)
    
    # Verificar arquivos do backend
    if not check_backend_files():
        sys.exit(1)
    
    # Configurar ambiente
    setup_environment()
    
    # Iniciar servidor
    if args.dev or args.prod:
        return start_server(dev_mode=args.dev, port=args.port, host=args.host)
    else:
        logger.info("[INFO] Para iniciar o servidor:")
        logger.info("   python start_crm_system.py --dev   # Desenvolvimento")
        logger.info("   python start_crm_system.py --prod  # Produção")
        logger.info("")
        logger.info("[INFO] Para instalar dependências:")
        logger.info("   python start_crm_system.py --install")
        logger.info("")
        logger.info("[INFO] Para executar testes:")
        logger.info("   python start_crm_system.py --test")

if __name__ == "__main__":
    raise SystemExit(main())
