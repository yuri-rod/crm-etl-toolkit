"""
Configuração e fixtures para testes end-to-end
Sistema ETL Inteligente - CRM Tools
"""

import pytest
import os
import tempfile
import shutil
import subprocess
import time
import requests
import logging
from pathlib import Path
from typing import Generator, Dict, Any
from playwright.sync_api import Playwright, Browser, BrowserContext, Page
from pages import ETLPage
from playwright.sync_api import sync_playwright

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configurações globais
BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")
HEADLESS = os.getenv("HEADLESS", "false").lower() == "true"
SLOW_MO = int(os.getenv("SLOW_MO", "0"))
TIMEOUT = int(os.getenv("TIMEOUT", "30000"))

# Arquivos de teste
TEST_FILES_DIR = Path(__file__).parent.parent.parent  # Diretório raiz do projeto


@pytest.fixture(scope="session")
def browser_config() -> Dict[str, Any]:
    """Configuração do browser para os testes"""
    return {
        "headless": HEADLESS,
        "slow_mo": SLOW_MO,
        "args": [
            "--disable-blink-features=AutomationControlled",
            "--disable-extensions",
            "--disable-plugins",
            "--disable-dev-shm-usage",
            "--no-sandbox",
            "--disable-setuid-sandbox",
            "--disable-gpu",
        ]
    }


@pytest.fixture(scope="session")
def server_process():
    """Inicia o servidor da aplicação para os testes"""
    logger.info("🚀 Iniciando servidor da aplicação...")
    
    # Verifica se o servidor já está rodando
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            logger.info("✅ Servidor já está rodando")
            yield
            return
    except requests.exceptions.RequestException:
        pass
    
    # Inicia o servidor
    server_script = TEST_FILES_DIR / "backend" / "api_server.py"
    if not server_script.exists():
        pytest.skip("Servidor não encontrado")
    
    try:
        # Executa o servidor em background
        process = subprocess.Popen([
            "python", str(server_script), 
            "--host", "127.0.0.1", 
            "--port", "8000"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Aguarda o servidor inicializar
        for attempt in range(30):  # 30 segundos máximo
            try:
                response = requests.get(f"{BASE_URL}/health", timeout=2)
                if response.status_code == 200:
                    logger.info("✅ Servidor iniciado com sucesso")
                    break
            except requests.exceptions.RequestException:
                time.sleep(1)
        else:
            process.terminate()
            pytest.skip("Falha ao iniciar servidor")
        
        yield process
        
        # Finaliza o servidor
        logger.info("🛑 Finalizando servidor...")
        process.terminate()
        process.wait(timeout=10)
        
    except Exception as e:
        logger.error(f"❌ Erro ao gerenciar servidor: {e}")
        pytest.skip(f"Erro no servidor: {e}")


@pytest.fixture(scope="session")
def playwright() -> Generator[Playwright, None, None]:
    """Fixture do Playwright"""
    with sync_playwright() as p:
        yield p


@pytest.fixture(scope="session")
def browser(playwright: Playwright, browser_config: Dict[str, Any]) -> Generator[Browser, None, None]:
    """Fixture do browser"""
    browser = playwright.chromium.launch(**browser_config)
    yield browser
    browser.close()


@pytest.fixture
def context(browser: Browser) -> Generator[BrowserContext, None, None]:
    """Fixture do contexto do browser"""
    context = browser.new_context(
        viewport={"width": 1920, "height": 1080},
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        extra_http_headers={
            "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8"
        }
    )
    
    # Configurações de timeout
    context.set_default_timeout(TIMEOUT)
    context.set_default_navigation_timeout(TIMEOUT)
    
    yield context
    context.close()


@pytest.fixture
def page(context: BrowserContext) -> Generator[Page, None, None]:
    """Fixture da página"""
    page = context.new_page()
    
    # Console listener para debugging
    page.on("console", lambda msg: logger.info(f"CONSOLE: {msg.text}"))
    
    # Error listener
    page.on("pageerror", lambda error: logger.error(f"PAGE ERROR: {error}"))
    
    yield page
    page.close()


@pytest.fixture
def etl_page(page: Page, server_process) -> ETLPage:
    """Fixture da página ETL"""
    return ETLPage(page, BASE_URL)


@pytest.fixture(scope="session")
def test_files() -> Dict[str, str]:
    """Cria arquivos de teste temporários"""
    temp_dir = tempfile.mkdtemp()
    logger.info(f"📁 Criando arquivos de teste em: {temp_dir}")
    
    # Arquivo CSV de teste
    csv_content = """nome,email,telefone,empresa,qualidade_lead
João Silva,joao@empresa.com,11999999999,Empresa A,Alto
Maria Santos,maria@empresa.com,11888888888,Empresa B,Médio  
Pedro Costa,pedro@empresa.com,11777777777,Empresa C,Baixo
Ana Paula,ana@empresa.com,11666666666,Empresa D,Alto
Carlos Lima,carlos@empresa.com,11555555555,Empresa E,Médio"""
    
    csv_file = os.path.join(temp_dir, "leads_test.csv")
    with open(csv_file, 'w', encoding='utf-8') as f:
        f.write(csv_content)
    
    # Arquivo Excel de teste
    try:
        import pandas as pd
        df = pd.read_csv(csv_file)
        excel_file = os.path.join(temp_dir, "leads_test.xlsx")
        df.to_excel(excel_file, index=False)
    except ImportError:
        logger.warning("pandas não disponível - arquivo Excel não será criado")
        excel_file = None
    
    files = {
        "csv": csv_file,
        "excel": excel_file,
        "temp_dir": temp_dir
    }
    
    yield files
    
    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def sample_csv_file(test_files: Dict[str, str]) -> str:
    """Retorna o caminho do arquivo CSV de teste"""
    return test_files["csv"]


@pytest.fixture
def sample_excel_file(test_files: Dict[str, str]) -> str:
    """Retorna o caminho do arquivo Excel de teste"""
    if test_files["excel"] is None:
        pytest.skip("pandas não disponível")
    return test_files["excel"]


@pytest.fixture
def download_dir() -> Generator[str, None, None]:
    """Diretório temporário para downloads"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture(autouse=True)
def setup_test_environment(request):
    """Setup automático para cada teste"""
    logger.info(f"🧪 Iniciando teste: {request.node.name}")
    yield
    logger.info(f"✅ Finalizando teste: {request.node.name}")


@pytest.fixture
def mobile_context(browser: Browser) -> Generator[BrowserContext, None, None]:
    """Contexto mobile para testes responsivos"""
    device = playwright.devices["iPhone 13"]
    context = browser.new_context(**device)
    yield context
    context.close()


@pytest.fixture
def tablet_context(browser: Browser) -> Generator[BrowserContext, None, None]:
    """Contexto tablet para testes responsivos"""
    device = playwright.devices["iPad"]
    context = browser.new_context(**device)
    yield context
    context.close()


# Hooks do pytest
def pytest_configure(config):
    """Configuração global do pytest"""
    # Criar diretórios necessários
    reports_dir = Path("reports")
    screenshots_dir = Path("screenshots")
    
    reports_dir.mkdir(exist_ok=True)
    screenshots_dir.mkdir(exist_ok=True)
    
    logger.info("🔧 Configuração de testes iniciada")


def pytest_runtest_makereport(item, call):
    """Hook para capturar falhas e tirar screenshots"""
    if call.when == "call" and call.excinfo is not None:
        # Captura screenshot em falhas
        try:
            page = item.funcargs.get('page')
            if page:
                screenshot_name = f"failure_{item.name}_{int(time.time())}"
                page.screenshot(path=f"screenshots/{screenshot_name}.png", full_page=True)
                logger.info(f"📸 Screenshot salvo: {screenshot_name}.png")
        except Exception as e:
            logger.warning(f"Erro ao capturar screenshot: {e}")


# Marcadores customizados
def pytest_collection_modifyitems(config, items):
    """Modifica itens da coleção de testes"""
    # Adiciona marcadores automaticamente baseado no nome do arquivo/teste
    for item in items:
        if "smoke" in item.nodeid:
            item.add_marker(pytest.mark.smoke)
        if "upload" in item.nodeid:
            item.add_marker(pytest.mark.upload)
        if "download" in item.nodeid:
            item.add_marker(pytest.mark.download)
        if "mobile" in item.nodeid:
            item.add_marker(pytest.mark.mobile)


# Configuração de retry para testes instáveis
def pytest_runtest_setup(item):
    """Setup antes de cada teste"""
    # Adiciona retry automático para testes marcados como instáveis
    if "flaky" in item.keywords:
        item.add_marker(pytest.mark.flaky(reruns=3, reruns_delay=2))
