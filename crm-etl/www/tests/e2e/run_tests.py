#!/usr/bin/env python3
"""
Script para executar testes end-to-end localmente
Sistema ETL Inteligente - CRM Tools

Uso:
    python run_tests.py --suite smoke --browser chromium
    python run_tests.py --suite all --browser all --headed
    python run_tests.py --help
"""

import argparse
import os
import sys
import subprocess
import time
import requests
import webbrowser
from pathlib import Path
from typing import List, Optional

# Configurações
DEFAULT_BASE_URL = "http://localhost:8000"
DEFAULT_TIMEOUT = 30
SUPPORTED_BROWSERS = ["chromium", "firefox", "webkit"]
TEST_SUITES = ["smoke", "regression", "mobile", "all"]

def setup_environment():
    """Configura o ambiente para os testes"""
    print("🔧 Configurando ambiente para testes...")
    
    # Criar diretórios necessários
    directories = [
        "reports", "screenshots", "production_models", 
        "logs", "data/input", "data/output", "temp"
    ]
    
    root_dir = Path(__file__).parent.parent.parent
    for directory in directories:
        (root_dir / directory).mkdir(parents=True, exist_ok=True)
    
    print("✅ Ambiente configurado com sucesso")

def check_dependencies():
    """Verifica se as dependências estão instaladas"""
    print("🔍 Verificando dependências...")
    
    try:
        import pytest
        import playwright
        from playwright.sync_api import sync_playwright
        print("✅ Dependências básicas encontradas")
        return True
    except ImportError as e:
        print(f"❌ Dependência não encontrada: {e}")
        print("Execute: pip install -r tests/e2e/requirements.txt")
        return False

def install_browsers(browsers: List[str]):
    """Instala os browsers do Playwright"""
    print(f"🌐 Instalando browsers: {', '.join(browsers)}")
    
    for browser in browsers:
        if browser in SUPPORTED_BROWSERS:
            cmd = f"playwright install {browser} --with-deps"
            print(f"Executando: {cmd}")
            try:
                subprocess.run(cmd, shell=True, check=True)
                print(f"✅ {browser} instalado com sucesso")
            except subprocess.CalledProcessError as e:
                print(f"❌ Erro ao instalar {browser}: {e}")
                return False
    
    return True

def check_server(base_url: str, timeout: int = DEFAULT_TIMEOUT) -> bool:
    """Verifica se o servidor está rodando"""
    print(f"🔍 Verificando servidor em {base_url}...")
    
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Servidor está rodando")
            return True
    except requests.exceptions.RequestException:
        pass
    
    print("❌ Servidor não está respondendo")
    return False

def start_server():
    """Inicia o servidor da aplicação"""
    print("🚀 Iniciando servidor da aplicação...")
    
    server_script = Path(__file__).parent.parent.parent / "backend" / "api_server.py"
    
    if not server_script.exists():
        print(f"❌ Servidor não encontrado em: {server_script}")
        return None
    
    try:
        # Inicia servidor em processo separado
        process = subprocess.Popen([
            sys.executable, str(server_script),
            "--host", "127.0.0.1",
            "--port", "8000"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Aguarda servidor inicializar
        print("⏳ Aguardando servidor inicializar...")
        for attempt in range(30):
            if check_server(DEFAULT_BASE_URL):
                print("✅ Servidor iniciado com sucesso")
                return process
            time.sleep(1)
        
        # Se chegou aqui, servidor não iniciou
        process.terminate()
        print("❌ Servidor não conseguiu inicializar em 30 segundos")
        return None
        
    except Exception as e:
        print(f"❌ Erro ao iniciar servidor: {e}")
        return None

def run_test_suite(suite: str, browsers: List[str], headed: bool = False, 
                  base_url: str = DEFAULT_BASE_URL) -> bool:
    """Executa uma suite de testes"""
    print(f"🧪 Executando suite: {suite}")
    
    success = True
    results = []
    
    # Mapear suites para arquivos de teste
    suite_files = {
        "smoke": ["test_smoke.py"],
        "regression": ["test_full_pipeline.py"],
        "mobile": ["test_responsive.py"],
        "all": ["test_smoke.py", "test_full_pipeline.py", "test_responsive.py"]
    }
    
    test_files = suite_files.get(suite, [suite])  # Permite arquivo específico
    
    for browser in browsers:
        for test_file in test_files:
            print(f"\n📋 Executando {test_file} no {browser}...")
            
            # Configurar comando pytest
            cmd = [
                sys.executable, "-m", "pytest",
                test_file,
                f"--browser={browser}",
                f"--headed={'false' if not headed else 'true'}",
                f"--html=../../reports/{suite}-{browser}-{test_file.replace('.py', '')}.html",
                "--self-contained-html",
                "-v",
                "--tb=short"
            ]
            
            # Adicionar marcadores específicos
            if "mobile" in test_file or suite == "mobile":
                cmd.extend(["-m", "mobile"])
            
            # Configurar variáveis de ambiente
            env = os.environ.copy()
            env.update({
                "BASE_URL": base_url,
                "HEADLESS": "false" if headed else "true",
                "TIMEOUT": "30000"
            })
            
            try:
                # Executar teste
                result = subprocess.run(
                    cmd, 
                    cwd=Path(__file__).parent,
                    env=env,
                    capture_output=False  # Mostra output em tempo real
                )
                
                if result.returncode == 0:
                    print(f"✅ {test_file} no {browser}: PASSOU")
                    results.append(f"✅ {test_file} ({browser})")
                else:
                    print(f"❌ {test_file} no {browser}: FALHOU")
                    results.append(f"❌ {test_file} ({browser})")
                    success = False
                    
            except Exception as e:
                print(f"❌ Erro ao executar {test_file}: {e}")
                results.append(f"❌ {test_file} ({browser}) - Erro: {e}")
                success = False
    
    # Resumo dos resultados
    print("\n" + "="*60)
    print("📊 RESUMO DOS RESULTADOS")
    print("="*60)
    for result in results:
        print(result)
    print("="*60)
    
    return success

def open_reports():
    """Abre os relatórios no navegador"""
    reports_dir = Path(__file__).parent.parent.parent / "reports"
    
    if not reports_dir.exists():
        print("❌ Diretório de relatórios não encontrado")
        return
    
    html_files = list(reports_dir.glob("*.html"))
    
    if not html_files:
        print("❌ Nenhum relatório HTML encontrado")
        return
    
    print(f"📄 Encontrados {len(html_files)} relatórios")
    
    # Abrir o relatório mais recente
    latest_report = max(html_files, key=os.path.getmtime)
    print(f"🌐 Abrindo relatório: {latest_report.name}")
    
    try:
        webbrowser.open(f"file://{latest_report.absolute()}")
    except Exception as e:
        print(f"❌ Erro ao abrir navegador: {e}")
        print(f"📄 Relatório disponível em: {latest_report.absolute()}")

def main():
    """Função principal"""
    parser = argparse.ArgumentParser(
        description="Executor de testes end-to-end para Sistema ETL Inteligente",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  python run_tests.py --suite smoke --browser chromium
  python run_tests.py --suite all --browser all --headed
  python run_tests.py --suite regression --browser firefox --no-server
  python run_tests.py test_smoke.py --browser webkit
        """
    )
    
    parser.add_argument("--suite", 
                       choices=TEST_SUITES + ["custom"],
                       default="smoke",
                       help="Suite de testes para executar")
    
    parser.add_argument("--browser",
                       choices=SUPPORTED_BROWSERS + ["all"],
                       default="chromium",
                       help="Browser(s) para usar nos testes")
    
    parser.add_argument("--headed",
                       action="store_true",
                       help="Executar com interface gráfica (útil para debug)")
    
    parser.add_argument("--no-server",
                       action="store_true",
                       help="Não iniciar servidor (assume que já está rodando)")
    
    parser.add_argument("--base-url",
                       default=DEFAULT_BASE_URL,
                       help="URL base do servidor")
    
    parser.add_argument("--install-browsers",
                       action="store_true",
                       help="Instalar browsers do Playwright")
    
    parser.add_argument("--open-reports",
                       action="store_true",
                       help="Abrir relatórios no navegador após execução")
    
    parser.add_argument("test_file",
                       nargs="?",
                       help="Arquivo de teste específico para executar")
    
    args = parser.parse_args()
    
    print("🚀 Sistema ETL Inteligente - Executor de Testes E2E")
    print("=" * 55)
    
    # Verificar dependências
    if not check_dependencies():
        return 1
    
    # Instalar browsers se solicitado
    if args.install_browsers:
        browsers_to_install = SUPPORTED_BROWSERS if args.browser == "all" else [args.browser]
        if not install_browsers(browsers_to_install):
            return 1
        return 0
    
    # Configurar ambiente
    setup_environment()
    
    # Determinar browsers
    browsers = SUPPORTED_BROWSERS if args.browser == "all" else [args.browser]
    
    # Determinar suite
    suite = args.test_file if args.test_file else args.suite
    
    # Gerenciar servidor
    server_process = None
    if not args.no_server:
        if not check_server(args.base_url):
            server_process = start_server()
            if not server_process:
                print("❌ Não foi possível iniciar o servidor")
                return 1
    else:
        if not check_server(args.base_url):
            print(f"⚠️  Aviso: Servidor não está respondendo em {args.base_url}")
    
    try:
        # Executar testes
        success = run_test_suite(
            suite=suite,
            browsers=browsers,
            headed=args.headed,
            base_url=args.base_url
        )
        
        # Abrir relatórios se solicitado
        if args.open_reports:
            open_reports()
        
        # Resultado final
        if success:
            print("\n🎉 Todos os testes passaram com sucesso!")
            return 0
        else:
            print("\n❌ Alguns testes falharam. Verifique os relatórios.")
            return 1
            
    finally:
        # Finalizar servidor se foi iniciado por este script
        if server_process:
            print("\n🛑 Finalizando servidor...")
            server_process.terminate()
            try:
                server_process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                server_process.kill()
            print("✅ Servidor finalizado")

if __name__ == "__main__":
    sys.exit(main())
