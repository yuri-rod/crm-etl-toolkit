"""
Exemplo prático de teste end-to-end
Sistema ETL Inteligente - CRM Tools

Este arquivo demonstra como criar testes E2E simples.
Use como referência para criar novos testes.
"""

import pytest
from pages import ETLPage


class TestExample:
    """Exemplo de classe de teste"""
    
    def test_basic_page_load(self, etl_page: ETLPage):
        """
        Exemplo: Teste básico de carregamento de página
        
        Este teste demonstra:
        - Como usar fixture etl_page
        - Como navegar para página
        - Como verificar elementos
        """
        # Carregar página
        etl_page.load_page()
        
        # Verificar que carregou corretamente
        etl_page.verify_page_loaded()
        
        # Verificar elemento específico
        etl_page.verify_element_visible(etl_page.SELECTORS['hero_title'])
        
        # Obter texto de elemento
        title_text = etl_page.get_text(etl_page.SELECTORS['hero_title'])
        assert "Sistema ETL" in title_text
        
        # Log de sucesso
        etl_page.log_assertion("Teste básico passou com sucesso")
    
    def test_upload_interface(self, etl_page: ETLPage):
        """
        Exemplo: Teste da interface de upload
        
        Este teste demonstra:
        - Como interagir com elementos
        - Como verificar estados
        """
        etl_page.load_page()
        
        # Verificar que área de upload está visível
        etl_page.verify_element_visible(etl_page.SELECTORS['upload_area'])
        
        # Verificar que botão execute está habilitado
        etl_page.verify_element_enabled(etl_page.SELECTORS['execute_btn'])
        
        # Expandir configurações
        etl_page.click_element(etl_page.SELECTORS['config_header'])
        etl_page.verify_element_visible(etl_page.SELECTORS['config_content'])
        
    @pytest.mark.smoke
    def test_smoke_example(self, etl_page: ETLPage):
        """
        Exemplo: Teste smoke (crítico)
        
        Marcado com @pytest.mark.smoke para ser executado
        nos testes básicos
        """
        etl_page.load_page()
        etl_page.verify_page_loaded()
        
        # Verificar elementos essenciais
        essential_elements = [
            'hero_title',
            'upload_area', 
            'execute_btn',
            'live_dashboard'
        ]
        
        for element in essential_elements:
            etl_page.verify_element_visible(etl_page.SELECTORS[element])
            
        etl_page.log_assertion("Elementos essenciais verificados")
    
    def test_with_file_upload_example(self, etl_page: ETLPage, sample_csv_file: str):
        """
        Exemplo: Teste com upload de arquivo
        
        Este teste demonstra:
        - Como usar fixture de arquivo de teste
        - Como fazer upload
        - Como verificar resultado
        """
        etl_page.load_page()
        
        # Upload do arquivo de teste
        etl_page.upload_file(sample_csv_file)
        
        # Verificar que upload text foi atualizado
        upload_text = etl_page.get_text(etl_page.SELECTORS['upload_text'])
        assert "leads_test.csv" in upload_text
        assert "sucesso" in upload_text.lower()
        
    @pytest.mark.mobile
    def test_mobile_example(self, mobile_context):
        """
        Exemplo: Teste mobile
        
        Este teste demonstra:
        - Como usar fixture mobile_context
        - Como testar em dispositivo móvel
        """
        page = mobile_context.new_page()
        etl_page = ETLPage(page)
        
        try:
            etl_page.load_page()
            etl_page.verify_page_loaded()
            
            # Verificar que elementos estão visíveis em mobile
            etl_page.verify_element_visible(etl_page.SELECTORS['hero_title'])
            
            # Scroll para área de upload
            etl_page.scroll_to_upload()
            etl_page.verify_element_visible(etl_page.SELECTORS['upload_area'])
            
        finally:
            page.close()
    
    def test_with_screenshot_example(self, etl_page: ETLPage):
        """
        Exemplo: Teste que tira screenshot
        
        Este teste demonstra:
        - Como tirar screenshots
        - Como usar para documentação
        """
        etl_page.load_page()
        etl_page.verify_page_loaded()
        
        # Tirar screenshot da página inicial
        etl_page.take_screenshot("homepage_example")
        
        # Expandir configurações e tirar outro screenshot
        etl_page.click_element(etl_page.SELECTORS['config_header'])
        etl_page.take_screenshot("config_expanded_example")
        
        etl_page.log_assertion("Screenshots capturados")
    
    def test_dashboard_example(self, etl_page: ETLPage):
        """
        Exemplo: Teste do dashboard ao vivo
        
        Este teste demonstra:
        - Como ativar dashboard
        - Como verificar métricas
        """
        etl_page.load_page()
        
        # Ativar dashboard ao vivo
        etl_page.toggle_live_dashboard()
        
        # Verificar que foi ativado
        button_text = etl_page.get_text(etl_page.SELECTORS['live_toggle'])
        assert "ativo" in button_text.lower()
        
        # Verificar métricas básicas
        metrics = [
            'live_active_jobs',
            'live_cpu_usage', 
            'live_memory_usage',
            'live_uptime'
        ]
        
        for metric in metrics:
            etl_page.verify_element_visible(etl_page.SELECTORS[metric])
            value = etl_page.get_text(etl_page.SELECTORS[metric])
            # Verificar que não está vazio
            assert value.strip() != ""
    
    def test_custom_assertions_example(self, etl_page: ETLPage):
        """
        Exemplo: Teste com asserções customizadas
        
        Este teste demonstra:
        - Como criar verificações específicas
        - Como validar dados da aplicação
        """
        etl_page.load_page()
        
        # Verificação de título específica
        title = etl_page.get_text(etl_page.SELECTORS['hero_title'])
        assert "Sistema ETL Inteligente" in title, f"Título incorreto: {title}"
        
        # Verificação de múltiplos badges
        badges = etl_page.page.locator(etl_page.SELECTORS['hero_badges'])
        badge_count = badges.count()
        assert badge_count == 4, f"Esperado 4 badges, encontrado {badge_count}"
        
        # Verificar textos específicos dos badges
        expected_badges = ["IA Generativa", "Tempo Real", "ML Automático", "Pipeline ETL"]
        for i in range(badge_count):
            badge_text = badges.nth(i).text_content()
            assert badge_text in expected_badges, f"Badge inesperado: {badge_text}"
        
        etl_page.log_assertion("Validações customizadas passaram")


# Exemplo de como executar apenas este arquivo:
# python -m pytest example_test.py --browser=chromium -v

# Exemplo de como executar teste específico:
# python -m pytest example_test.py::TestExample::test_basic_page_load --browser=chromium -v

# Exemplo de como executar com interface gráfica:
# python -m pytest example_test.py --browser=chromium --headed=true -v
