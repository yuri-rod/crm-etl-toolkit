"""
Configuração do Playwright para testes end-to-end
Sistema ETL Inteligente - CRM Tools
"""

from playwright.sync_api import Playwright

# Configurações do Playwright
PLAYWRIGHT_CONFIG = {
    'base_url': 'http://localhost:8000',
    'timeout': 30000,  # 30 segundos
    'screenshot_mode': 'only-on-failure',
    'video_mode': 'retain-on-failure',
    'trace_mode': 'retain-on-failure',
    'headless': True,  # Para CI/CD
    'slow_mo': 0,  # Sem delay para CI
}

# Configurações para diferentes ambientes
ENVIRONMENTS = {
    'local': {
        'base_url': 'http://localhost:8000',
        'headless': False,
        'slow_mo': 100,  # Delay para debugging local
    },
    'ci': {
        'base_url': 'http://localhost:8000',
        'headless': True,
        'slow_mo': 0,
    },
    'staging': {
        'base_url': 'https://staging.example.com',
        'headless': True,
        'slow_mo': 0,
    }
}

# Browser configurations
BROWSER_CONFIGS = [
    {'browser': 'chromium', 'viewport': {'width': 1920, 'height': 1080}},
    {'browser': 'firefox', 'viewport': {'width': 1920, 'height': 1080}},
    {'browser': 'webkit', 'viewport': {'width': 1920, 'height': 1080}},
]

# Mobile configurations for responsive testing
MOBILE_CONFIGS = [
    {'device': 'iPhone 13'},
    {'device': 'iPad'},
    {'device': 'Pixel 5'},
]

def get_config(env='local'):
    """Retorna configuração para ambiente específico"""
    return ENVIRONMENTS.get(env, ENVIRONMENTS['local'])
