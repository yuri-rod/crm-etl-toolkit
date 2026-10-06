#!/usr/bin/env python3
"""
Script de configuração inicial para testes end-to-end
Sistema ETL Inteligente - CRM Tools

Este script prepara o ambiente para executar testes E2E pela primeira vez.
"""

import os
import sys
import subprocess
from pathlib import Path

def print_header():
    """Imprime cabeçalho do script"""
    print("🚀 Sistema ETL Inteligente - Setup E2E Tests")
    print("=" * 50)
    print("CRM ETL")
    print("=" * 50)

def check_python_version():
    """Verifica a versão do Python"""
    print("🔍 Verificando versão do Python...")
    
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ é necessário. Versão atual:", sys.version)
        return False
    
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detectado")
    return True

def install_dependencies():
    """Instala as dependências Python"""
    print("\n📦 Instalando dependências Python...")
    
    requirements_file = Path(__file__).parent / "requirements.txt"
    
    if not requirements_file.exists():
        print("❌ Arquivo requirements.txt não encontrado")
        return False
    
    try:
        subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", str(requirements_file)
        ], check=True)
        print("✅ Dependências instaladas com sucesso")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro ao instalar dependências: {e}")
        return False

def install_playwright_browsers():
    """Instala os browsers do Playwright"""
    print("\n🌐 Instalando browsers do Playwright...")
    
    browsers = ["chromium", "firefox", "webkit"]
    
    for browser in browsers:
        print(f"Instalando {browser}...")
        try:
            subprocess.run([
                "playwright", "install", browser, "--with-deps"
            ], check=True)
            print(f"✅ {browser} instalado")
        except subprocess.CalledProcessError as e:
            print(f"❌ Erro ao instalar {browser}: {e}")
            return False
    
    print("✅ Todos os browsers instalados com sucesso")
    return True

def create_directories():
    """Cria diretórios necessários"""
    print("\n📁 Criando diretórios necessários...")
    
    root_dir = Path(__file__).parent.parent.parent
    directories = [
        "reports",
        "screenshots", 
        "production_models",
        "logs",
        "data",
        "data/input",
        "data/output",
        "temp"
    ]
    
    for directory in directories:
        dir_path = root_dir / directory
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"✅ {directory}")
    
    print("✅ Diretórios criados com sucesso")
    return True

def test_installation():
    """Testa se a instalação está funcionando"""
    print("\n🧪 Testando instalação...")
    
    try:
        # Testar imports
        import pytest
        import playwright
        from playwright.sync_api import sync_playwright
        
        print("✅ Imports básicos funcionando")
        
        # Testar Playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto("data:text/html,<h1>Test</h1>")
            title = page.title()
            browser.close()
            
        print("✅ Playwright funcionando")
        
        # Testar pytest
        test_dir = Path(__file__).parent
        result = subprocess.run([
            sys.executable, "-m", "pytest", "--collect-only", "-q"
        ], cwd=test_dir, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Pytest encontrou os testes")
        else:
            print("⚠️ Pytest teve avisos, mas deve funcionar")
        
        return True
        
    except ImportError as e:
        print(f"❌ Erro de import: {e}")
        return False
    except Exception as e:
        print(f"❌ Erro no teste: {e}")
        return False

def show_next_steps():
    """Mostra próximos passos"""
    print("\n🎉 Setup concluído com sucesso!")
    print("\n📋 Próximos passos:")
    print("1. Execute testes básicos:")
    print("   python run_tests.py --suite smoke --browser chromium")
    print()
    print("2. Execute com interface gráfica (debug):")
    print("   python run_tests.py --suite smoke --browser chromium --headed")
    print()
    print("3. Execute todos os testes:")
    print("   python run_tests.py --suite all --browser all")
    print()
    print("4. Veja a documentação completa:")
    print("   cat README.md")
    print()
    print("🚀 Happy Testing!")

def main():
    """Função principal"""
    print_header()
    
    # Verificações
    if not check_python_version():
        return 1
    
    # Instalações
    if not install_dependencies():
        return 1
    
    if not install_playwright_browsers():
        return 1
    
    if not create_directories():
        return 1
    
    # Teste final
    if not test_installation():
        print("\n⚠️ Instalação pode ter problemas, mas você pode tentar executar os testes")
    
    # Próximos passos
    show_next_steps()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
