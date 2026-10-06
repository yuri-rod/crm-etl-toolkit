"""
Testes Smoke - Funcionalidades críticas do sistema
Sistema ETL Inteligente - CRM Tools
"""

import pytest
from pages import ETLPage


@pytest.mark.smoke
class TestSmokeSuite:
    """Suite de testes smoke para funcionalidades críticas"""
    
    def test_homepage_loads(self, etl_page: ETLPage):
        """
        Teste: Página principal carrega corretamente
        
        Verifica:
        - Título da página
        - Elementos principais visíveis
        - Seção hero carregada
        """
        # Carregar página
        etl_page.load_page()
        
        # Verificar carregamento
        etl_page.verify_page_loaded()
        etl_page.verify_header_elements()
        etl_page.verify_hero_section()
        
    def test_upload_interface_available(self, etl_page: ETLPage):
        """
        Teste: Interface de upload está disponível
        
        Verifica:
        - Área de upload visível
        - Campo de arquivo presente
        - Configurações acessíveis
        """
        etl_page.load_page()
        
        # Verificar elementos de upload
        etl_page.verify_element_visible(etl_page.SELECTORS['upload_area'])
        etl_page.verify_element_visible(etl_page.SELECTORS['upload_icon'])
        etl_page.verify_element_visible(etl_page.SELECTORS['execute_btn'])
        
        # Verificar que botão está habilitado
        etl_page.verify_element_enabled(etl_page.SELECTORS['execute_btn'])
        
    def test_configuration_panel_accessible(self, etl_page: ETLPage):
        """
        Teste: Painel de configuração é acessível
        
        Verifica:
        - Configurações avançadas podem ser expandidas
        - Campos de configuração visíveis
        - Opções de modo disponíveis
        """
        etl_page.load_page()
        
        # Expandir configurações avançadas
        etl_page.click_element(etl_page.SELECTORS['config_header'])
        etl_page.verify_element_visible(etl_page.SELECTORS['config_content'])
        
        # Verificar campos de configuração
        etl_page.verify_element_visible(etl_page.SELECTORS['mode_select'])
        etl_page.verify_element_visible(etl_page.SELECTORS['target_input'])
        etl_page.verify_element_visible(etl_page.SELECTORS['model_dir_input'])
        
    def test_live_dashboard_available(self, etl_page: ETLPage):
        """
        Teste: Dashboard ao vivo está disponível
        
        Verifica:
        - Dashboard visível
        - Métricas básicas presentes
        - Botão de ativação funcional
        """
        etl_page.load_page()
        
        # Verificar elementos do dashboard
        etl_page.verify_element_visible(etl_page.SELECTORS['live_dashboard'])
        etl_page.verify_element_visible(etl_page.SELECTORS['live_toggle'])
        
        # Verificar métricas
        metrics = [
            'live_active_jobs', 'live_completed_today', 
            'live_cpu_usage', 'live_memory_usage', 
            'live_error_count', 'live_uptime'
        ]
        
        for metric in metrics:
            etl_page.verify_element_visible(etl_page.SELECTORS[metric])
            
    def test_responsive_layout(self, etl_page: ETLPage):
        """
        Teste: Layout responsivo funciona
        
        Verifica:
        - Elementos principais visíveis em desktop
        - Layout se adapta ao viewport
        """
        etl_page.load_page()
        
        # Verificar design responsivo
        etl_page.verify_responsive_design()
        
        # Verificar que elementos essenciais estão visíveis
        essential_selectors = [
            'hero_title', 'upload_area', 'execute_btn', 'footer'
        ]
        
        for selector in essential_selectors:
            etl_page.verify_element_visible(etl_page.SELECTORS[selector])


@pytest.mark.smoke
@pytest.mark.upload
class TestUploadSmoke:
    """Testes smoke específicos para upload"""
    
    def test_file_upload_interface(self, etl_page: ETLPage, sample_csv_file: str):
        """
        Teste: Interface de upload de arquivo funciona
        
        Verifica:
        - Upload de arquivo funciona
        - Notificação de sucesso aparece
        - Interface atualiza após upload
        """
        etl_page.load_page()
        
        # Fazer upload
        etl_page.upload_file(sample_csv_file)
        
        # Verificar que upload text foi atualizado
        upload_text = etl_page.get_text(etl_page.SELECTORS['upload_text'])
        assert "leads_test.csv" in upload_text
        assert "sucesso" in upload_text.lower()


@pytest.mark.smoke  
@pytest.mark.api
class TestAPIConnectivity:
    """Testes smoke para conectividade com API"""
    
    def test_api_health_check(self, etl_page: ETLPage):
        """
        Teste: API está respondendo
        
        Verifica através da interface que a API está operacional
        """
        etl_page.load_page()
        
        # Se a página carregar, a API básica está funcionando
        etl_page.verify_page_loaded()
        
        # Verificar que não há erros de console críticos
        # (isso é verificado automaticamente pelo fixture de página)
        
    def test_live_dashboard_activation(self, etl_page: ETLPage):
        """
        Teste: Dashboard ao vivo consegue se conectar
        
        Verifica:
        - Dashboard pode ser ativado
        - Notificação de ativação aparece
        - Métricas começam a atualizar
        """
        etl_page.load_page()
        
        # Ativar dashboard ao vivo
        etl_page.toggle_live_dashboard()
        
        # Verificar que foi ativado
        button_text = etl_page.get_text(etl_page.SELECTORS['live_toggle'])
        assert "ativo" in button_text.lower()


@pytest.mark.smoke
class TestCriticalUserJourney:
    """Teste da jornada crítica do usuário"""
    
    def test_basic_user_flow(self, etl_page: ETLPage, sample_csv_file: str):
        """
        Teste: Fluxo básico do usuário funciona
        
        Simula o caminho crítico:
        1. Carrega página
        2. Faz upload de arquivo  
        3. Configura pipeline básica
        4. Verifica que pode executar
        
        Não executa a pipeline completa para manter o teste rápido
        """
        # Passo 1: Carregar página
        etl_page.load_page()
        etl_page.verify_page_loaded()
        
        # Passo 2: Upload de arquivo
        etl_page.upload_file(sample_csv_file)
        
        # Passo 3: Configurar pipeline (configurações básicas)
        etl_page.configure_pipeline(
            mode="train",
            target_column="qualidade_lead"
        )
        
        # Passo 4: Verificar que botão de execução está habilitado
        etl_page.verify_element_enabled(etl_page.SELECTORS['execute_btn'])
        
        # Verificar que chegamos até aqui sem erros
        etl_page.log_assertion("Fluxo crítico do usuário completado com sucesso")
