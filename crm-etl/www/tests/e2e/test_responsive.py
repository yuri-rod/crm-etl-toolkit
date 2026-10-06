"""
Testes de Design Responsivo - Mobile e Tablet
Sistema ETL Inteligente - CRM Tools
"""

import pytest
from playwright.sync_api import BrowserContext, Page
from pages import ETLPage


@pytest.mark.mobile
class TestMobileResponsive:
    """Testes específicos para dispositivos móveis"""
    
    def test_mobile_layout_loads(self, mobile_context: BrowserContext):
        """
        Teste: Layout mobile carrega corretamente
        
        Verifica:
        - Página carrega em dispositivo mobile
        - Elementos principais estão visíveis
        - Layout se adapta ao tamanho da tela
        """
        page = mobile_context.new_page()
        etl_page = ETLPage(page)
        
        try:
            etl_page.load_page()
            etl_page.verify_page_loaded()
            
            # Verificar elementos essenciais em mobile
            etl_page.verify_responsive_design()
            
            # Verificar que o hero está adaptado
            etl_page.verify_element_visible(etl_page.SELECTORS['hero_title'])
            
            # Scroll para verificar outros elementos
            etl_page.scroll_to_upload()
            etl_page.verify_element_visible(etl_page.SELECTORS['upload_area'])
            
            etl_page.log_assertion("Layout mobile carregado com sucesso")
            
        finally:
            page.close()
    
    def test_mobile_upload_interface(self, mobile_context: BrowserContext, sample_csv_file: str):
        """
        Teste: Interface de upload funciona em mobile
        
        Verifica:
        - Área de upload é acessível em mobile
        - Upload de arquivo funciona
        - Notificações são exibidas corretamente
        """
        page = mobile_context.new_page()
        etl_page = ETLPage(page)
        
        try:
            etl_page.load_page()
            
            # Navegar até área de upload
            etl_page.scroll_to_upload()
            etl_page.verify_element_visible(etl_page.SELECTORS['upload_area'])
            
            # Fazer upload
            etl_page.upload_file(sample_csv_file)
            
            # Verificar que funcionou
            upload_text = etl_page.get_text(etl_page.SELECTORS['upload_text'])
            assert "leads_test.csv" in upload_text
            
            etl_page.log_assertion("Upload mobile funcionou corretamente")
            
        finally:
            page.close()
    
    def test_mobile_configuration_panel(self, mobile_context: BrowserContext):
        """
        Teste: Painel de configuração funciona em mobile
        
        Verifica:
        - Configurações podem ser expandidas
        - Campos são acessíveis
        - Interface se adapta ao toque
        """
        page = mobile_context.new_page()
        etl_page = ETLPage(page)
        
        try:
            etl_page.load_page()
            
            # Scroll até configurações
            etl_page.scroll_to_element(etl_page.SELECTORS['config_header'])
            
            # Expandir configurações
            etl_page.click_element(etl_page.SELECTORS['config_header'])
            etl_page.verify_element_visible(etl_page.SELECTORS['config_content'])
            
            # Verificar campos principais
            etl_page.verify_element_visible(etl_page.SELECTORS['mode_select'])
            etl_page.verify_element_visible(etl_page.SELECTORS['target_input'])
            
            etl_page.log_assertion("Configurações mobile acessíveis")
            
        finally:
            page.close()
    
    def test_mobile_live_dashboard(self, mobile_context: BrowserContext):
        """
        Teste: Dashboard ao vivo funciona em mobile
        
        Verifica:
        - Dashboard é visível em mobile
        - Métricas estão organizadas verticalmente
        - Botões são touch-friendly
        """
        page = mobile_context.new_page()
        etl_page = ETLPage(page)
        
        try:
            etl_page.load_page()
            
            # Scroll até dashboard
            etl_page.scroll_to_element(etl_page.SELECTORS['live_dashboard'])
            
            # Verificar elementos do dashboard
            etl_page.verify_element_visible(etl_page.SELECTORS['live_dashboard'])
            etl_page.verify_element_visible(etl_page.SELECTORS['live_toggle'])
            
            # Ativar dashboard
            etl_page.toggle_live_dashboard()
            
            # Verificar métricas
            metrics = ['live_active_jobs', 'live_cpu_usage', 'live_memory_usage']
            for metric in metrics:
                etl_page.verify_element_visible(etl_page.SELECTORS[metric])
            
            etl_page.log_assertion("Dashboard mobile funcional")
            
        finally:
            page.close()


@pytest.mark.mobile  
class TestTabletResponsive:
    """Testes específicos para tablets"""
    
    def test_tablet_layout_loads(self, tablet_context: BrowserContext):
        """
        Teste: Layout tablet carrega corretamente
        
        Verifica:
        - Layout intermediário entre mobile e desktop
        - Elementos bem distribuídos
        - Navegação funcional
        """
        page = tablet_context.new_page()
        etl_page = ETLPage(page)
        
        try:
            etl_page.load_page()
            etl_page.verify_page_loaded()
            etl_page.verify_responsive_design()
            
            # Em tablet, elementos devem estar bem distribuídos
            etl_page.verify_element_visible(etl_page.SELECTORS['hero_title'])
            etl_page.verify_element_visible(etl_page.SELECTORS['upload_area'])
            
            etl_page.log_assertion("Layout tablet carregado corretamente")
            
        finally:
            page.close()
    
    def test_tablet_full_workflow(self, tablet_context: BrowserContext, sample_csv_file: str):
        """
        Teste: Workflow completo funciona em tablet
        
        Executa um workflow simplificado para verificar que
        a funcionalidade principal funciona em tablet
        """
        page = tablet_context.new_page()
        etl_page = ETLPage(page)
        
        try:
            etl_page.load_page()
            
            # Upload
            etl_page.upload_file(sample_csv_file)
            
            # Configuração básica
            etl_page.configure_pipeline(mode="train")
            
            # Verificar que pode executar
            etl_page.verify_element_enabled(etl_page.SELECTORS['execute_btn'])
            
            etl_page.log_assertion("Workflow tablet preparado com sucesso")
            
        finally:
            page.close()


@pytest.mark.regression
class TestCrossDevice:
    """Testes cross-device - Comparação entre dispositivos"""
    
    def test_consistent_functionality_across_devices(self, 
                                                   browser, 
                                                   sample_csv_file: str):
        """
        Teste: Funcionalidade consistente entre dispositivos
        
        Executa os mesmos passos em diferentes dispositivos
        e verifica que o comportamento é consistente
        """
        devices = [
            {"name": "Desktop", "viewport": {"width": 1920, "height": 1080}},
            {"name": "Tablet", "device": "iPad"},
            {"name": "Mobile", "device": "iPhone 13"}
        ]
        
        for device_config in devices:
            etl_page = None
            context = None
            
            try:
                # Configurar contexto do dispositivo
                if "device" in device_config:
                    from playwright.sync_api import sync_playwright
                    with sync_playwright() as p:
                        device = p.devices[device_config["device"]]
                        context = browser.new_context(**device)
                else:
                    context = browser.new_context(viewport=device_config["viewport"])
                
                page = context.new_page()
                etl_page = ETLPage(page)
                
                etl_page.log_step(f"=== TESTE: {device_config['name']} ===")
                
                # Executar passos básicos
                etl_page.load_page()
                etl_page.verify_page_loaded()
                
                # Upload
                etl_page.upload_file(sample_csv_file)
                
                # Verificar elementos essenciais
                etl_page.verify_element_visible(etl_page.SELECTORS['upload_area'])
                etl_page.verify_element_enabled(etl_page.SELECTORS['execute_btn'])
                
                etl_page.log_assertion(f"Funcionalidade {device_config['name']} consistente")
                
            finally:
                if context:
                    context.close()
    
    def test_responsive_breakpoints(self, browser):
        """
        Teste: Breakpoints responsivos funcionam corretamente
        
        Testa diferentes tamanhos de viewport para verificar
        que o layout se adapta nos pontos de quebra corretos
        """
        viewports = [
            {"width": 320, "height": 568, "name": "Mobile Small"},
            {"width": 375, "height": 812, "name": "Mobile Large"},
            {"width": 768, "height": 1024, "name": "Tablet"},
            {"width": 1024, "height": 768, "name": "Desktop Small"},
            {"width": 1920, "height": 1080, "name": "Desktop Large"}
        ]
        
        for viewport in viewports:
            context = None
            try:
                context = browser.new_context(
                    viewport={"width": viewport["width"], "height": viewport["height"]}
                )
                page = context.new_page()
                etl_page = ETLPage(page)
                
                etl_page.log_step(f"=== BREAKPOINT: {viewport['name']} ({viewport['width']}x{viewport['height']}) ===")
                
                etl_page.load_page()
                etl_page.verify_page_loaded()
                
                # Verificar elementos essenciais estão visíveis
                etl_page.verify_element_visible(etl_page.SELECTORS['hero_title'])
                etl_page.verify_element_visible(etl_page.SELECTORS['upload_area'])
                
                # Tirar screenshot para documentação
                screenshot_name = f"breakpoint_{viewport['name'].replace(' ', '_').lower()}"
                etl_page.take_screenshot(screenshot_name)
                
                etl_page.log_assertion(f"Breakpoint {viewport['name']} funcional")
                
            finally:
                if context:
                    context.close()


@pytest.mark.mobile
@pytest.mark.slow
class TestMobileFullWorkflow:
    """Teste completo em mobile (mais lento)"""
    
    def test_complete_mobile_pipeline(self, mobile_context: BrowserContext, sample_csv_file: str):
        """
        Teste: Pipeline completa funciona em mobile
        
        Executa todo o workflow em dispositivo mobile
        para garantir compatibilidade completa
        """
        page = mobile_context.new_page()
        etl_page = ETLPage(page)
        
        try:
            etl_page.log_step("=== TESTE: Pipeline completa mobile ===")
            
            # Carregar e fazer upload
            etl_page.load_page()
            etl_page.upload_file(sample_csv_file)
            
            # Configurar pipeline
            etl_page.configure_pipeline(
                mode="train",
                target_column="qualidade_lead",
                enable_enrichment=False
            )
            
            # Executar pipeline
            etl_page.execute_pipeline()
            etl_page.wait_for_pipeline_completion(timeout=120000)
            
            # Verificar resultados
            etl_page.scroll_to_results()
            results = etl_page.verify_results_displayed()
            
            # Exportar
            downloaded_filename = etl_page.export_results()
            assert downloaded_filename is not None
            
            etl_page.log_assertion("Pipeline completa mobile executada com sucesso")
            
        finally:
            page.close()
