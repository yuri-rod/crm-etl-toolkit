"""
Testes End-to-End (E2E) - Sistema ETL Inteligente
CRM Tools - CRM ETL

Este pacote contém todos os testes end-to-end para verificar
o funcionamento completo da aplicação web.

Estrutura:
- test_smoke.py: Testes básicos e críticos
- test_full_pipeline.py: Testes completos da pipeline
- test_responsive.py: Testes de design responsivo
- pages/: Page Objects para reutilização
- conftest.py: Configurações e fixtures

Para executar:
    python run_tests.py --suite smoke --browser chromium
"""

__version__ = "1.0.0"
__author__ = "CRM ETL"
__title__ = "Sistema ETL Inteligente - E2E Tests"
