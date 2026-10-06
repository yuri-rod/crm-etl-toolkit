"""
Page Object para a página principal do Sistema ETL Inteligente
CRM Tools - CRM ETL
"""

from typing import Optional, Dict, Any
from playwright.sync_api import Page, expect
from .base_page import BasePage
import time


class ETLPage(BasePage):
    """Page Object para a interface principal do Sistema ETL"""
    
    # Seletores da página
    SELECTORS = {
        # Cabeçalho
        'logo': '.logo img',
        'nav_docs': 'a[href="#"]:has-text("Documentação")',
        'nav_about': 'a[href="#"]:has-text("Sobre")',
        
        # Hero section
        'hero_title': '.hero h1',
        'hero_description': '.hero p',
        'hero_badges': '.hero-badge',
        
        # Upload section
        'upload_area': '.upload-area',
        'file_input': '#fileInput',
        'upload_text': '#uploadText',
        'upload_icon': '.upload-icon',
        
        # Progress
        'progress_container': '#progressContainer',
        'progress_fill': '#progressFill',
        'progress_text': '#progressText',
        
        # Configurações avançadas
        'config_header': '.section-header[onclick="toggleAdvancedConfig()"]',
        'config_content': '#advancedConfigContent',
        'config_toggle_icon': '#configToggleIcon',
        'mode_select': '#mode',
        'target_input': '#target',
        'model_dir_input': '#modelDir',
        'output_input': '#output',
        'enrich_checkbox': '#enrich',
        
        # Botões de ação
        'execute_btn': '#executeBtn',
        'export_btn': '#exportBtn',
        'btn_text': '#btnText',
        'spinner': '#spinner',
        
        # Seção de resultados
        'results_section': '#resultsSection',
        'results_grid': '#resultsGrid',
        'total_records': '#totalRecords',
        'duplicates_removed': '#duplicatesRemoved',
        'features_created': '#featuresCreated',
        'model_accuracy': '#modelAccuracy',
        'generated_files': '#generatedFiles',
        
        # Dashboard ao vivo
        'live_dashboard': '#liveDashboard',
        'live_toggle': '#liveToggle',
        'live_active_jobs': '#liveActiveJobs',
        'live_completed_today': '#liveCompletedToday',
        'live_cpu_usage': '#liveCpuUsage',
        'live_memory_usage': '#liveMemoryUsage',
        'live_error_count': '#liveErrorCount',
        'live_uptime': '#liveUptime',
        'activity_log': '#activityLog',
        
        # Notificações
        'notification': '.notification',
        'notification_close': '.notification button',
        
        # Footer
        'footer': '.brand-footer',
        'footer_logo': '.brand-footer img',
    }
    
    def __init__(self, page: Page, base_url: str = "http://localhost:8000"):
        super().__init__(page, base_url)
        
    def load_page(self) -> None:
        """Carrega a página principal do ETL"""
        self.log_step("Carregando página principal do ETL")
        self.navigate_to("/")
        self.wait_for_load()
        
    def verify_page_loaded(self) -> None:
        """Verifica se a página foi carregada corretamente"""
        self.log_assertion("Verificando se a página foi carregada")
        self.verify_page_title("CRM Tools - Sistema ETL Inteligente | CRM ETL")
        self.verify_element_visible(self.SELECTORS['hero_title'])
        self.verify_element_text(self.SELECTORS['hero_title'], "Sistema ETL Inteligente")
        
    def verify_header_elements(self) -> None:
        """Verifica elementos do cabeçalho"""
        self.log_assertion("Verificando elementos do cabeçalho")
        self.verify_element_visible(self.SELECTORS['logo'])
        self.verify_element_visible(self.SELECTORS['nav_docs'])
        self.verify_element_visible(self.SELECTORS['nav_about'])
        
    def verify_hero_section(self) -> None:
        """Verifica a seção hero"""
        self.log_assertion("Verificando seção hero")
        self.verify_element_visible(self.SELECTORS['hero_title'])
        self.verify_element_visible(self.SELECTORS['hero_description'])
        
        # Verifica badges
        badges = self.page.locator(self.SELECTORS['hero_badges'])
        expect(badges).to_have_count(4)
        
    def upload_file(self, file_path: str) -> None:
        """Faz upload de um arquivo"""
        self.log_step(f"Fazendo upload do arquivo: {file_path}")
        
        # Aguarda a área de upload estar visível
        self.verify_element_visible(self.SELECTORS['upload_area'])
        
        # Faz o upload
        super().upload_file(self.SELECTORS['file_input'], file_path)
        
        # Verifica se o upload foi bem sucedido
        self.wait_for_notification("Arquivo carregado com sucesso!", timeout=10000)
        
    def configure_pipeline(self, 
                         mode: str = "train", 
                         target_column: str = "qualidade_lead",
                         model_dir: str = "./production_models/",
                         output_filename: str = "predictions_output.csv",
                         enable_enrichment: bool = False) -> None:
        """Configura os parâmetros da pipeline"""
        self.log_step("Configurando parâmetros da pipeline")
        
        # Expande configurações avançadas se necessário
        if not self.is_visible(self.SELECTORS['config_content']):
            self.click_element(self.SELECTORS['config_header'])
            self.wait_for_selector(self.SELECTORS['config_content'])
            
        # Configura modo
        self.page.locator(self.SELECTORS['mode_select']).select_option(mode)
        
        # Configura coluna alvo (apenas para treinamento)
        if mode == "train":
            self.fill_input(self.SELECTORS['target_input'], target_column)
            
        # Configura diretório do modelo
        self.fill_input(self.SELECTORS['model_dir_input'], model_dir)
        
        # Configura arquivo de saída (apenas para predição)
        if mode == "batch-predict":
            self.fill_input(self.SELECTORS['output_input'], output_filename)
            
        # Configura enriquecimento
        enrich_checkbox = self.page.locator(self.SELECTORS['enrich_checkbox'])
        if enable_enrichment != enrich_checkbox.is_checked():
            enrich_checkbox.click()
            
    def execute_pipeline(self) -> None:
        """Executa a pipeline"""
        self.log_step("Executando pipeline")
        
        # Verifica se o botão está habilitado
        self.verify_element_enabled(self.SELECTORS['execute_btn'])
        
        # Clica no botão executar
        self.click_element(self.SELECTORS['execute_btn'])
        
        # Verifica se a execução iniciou
        self.wait_for_notification("Iniciando pipeline de ETL...", timeout=10000)
        
    def wait_for_pipeline_completion(self, timeout: int = 120000) -> None:
        """Aguarda a conclusão da pipeline"""
        self.log_step("Aguardando conclusão da pipeline")
        
        # Aguarda a barra de progresso aparecer e completar
        self.wait_for_progress_complete(timeout=timeout)
        
        # Aguarda notificação de sucesso
        self.wait_for_notification("Pipeline executada com sucesso!", timeout=30000)
        
        # Verifica se a seção de resultados apareceu
        self.verify_element_visible(self.SELECTORS['results_section'])
        self.verify_element_visible(self.SELECTORS['export_btn'])
        
    def verify_results_displayed(self) -> Dict[str, str]:
        """Verifica e retorna os resultados exibidos"""
        self.log_assertion("Verificando resultados exibidos")
        
        # Verifica se a seção de resultados está visível
        self.verify_element_visible(self.SELECTORS['results_section'])
        
        # Coleta métricas
        results = {}
        metrics_selectors = {
            'total_records': self.SELECTORS['total_records'],
            'duplicates_removed': self.SELECTORS['duplicates_removed'],
            'features_created': self.SELECTORS['features_created'],
            'model_accuracy': self.SELECTORS['model_accuracy']
        }
        
        for metric_name, selector in metrics_selectors.items():
            self.verify_element_visible(selector)
            results[metric_name] = self.get_text(selector)
            
        # Verifica se há arquivos gerados
        self.verify_element_visible(self.SELECTORS['generated_files'])
        generated_files_text = self.get_text(self.SELECTORS['generated_files'])
        assert "concluído com sucesso" in generated_files_text.lower()
        
        return results
        
    def export_results(self) -> str:
        """Exporta os resultados e retorna o nome do arquivo baixado"""
        self.log_step("Exportando resultados")
        
        # Verifica se o botão de exportar está disponível
        self.verify_element_visible(self.SELECTORS['export_btn'])
        self.verify_element_enabled(self.SELECTORS['export_btn'])
        
        # Configura listener para download
        with self.page.expect_download(timeout=60000) as download_info:
            # Clica no botão exportar
            self.click_element(self.SELECTORS['export_btn'])
            
        # Obtém informações do download
        download = download_info.value
        
        # Verifica notificação de sucesso
        self.wait_for_notification("Arquivo baixado com sucesso!", timeout=10000)
        
        return download.suggested_filename
        
    def toggle_live_dashboard(self) -> None:
        """Alterna o modo ao vivo do dashboard"""
        self.log_step("Alternando dashboard ao vivo")
        
        self.click_element(self.SELECTORS['live_toggle'])
        
        # Verifica se o modo foi ativado
        button_text = self.get_text(self.SELECTORS['live_toggle'])
        if "Ativo" in button_text:
            self.log_assertion("Dashboard ao vivo ativado")
            self.wait_for_notification("Dashboard ao vivo ativado!", timeout=10000)
        else:
            self.log_assertion("Dashboard ao vivo desativado")
            
    def verify_live_metrics_updating(self, duration: int = 10) -> None:
        """Verifica se as métricas ao vivo estão sendo atualizadas"""
        self.log_assertion("Verificando atualização de métricas ao vivo")
        
        # Coleta valores iniciais
        initial_values = {}
        metrics_selectors = {
            'active_jobs': self.SELECTORS['live_active_jobs'],
            'completed_today': self.SELECTORS['live_completed_today'],
            'cpu_usage': self.SELECTORS['live_cpu_usage'],
            'memory_usage': self.SELECTORS['live_memory_usage'],
            'uptime': self.SELECTORS['live_uptime']
        }
        
        for metric_name, selector in metrics_selectors.items():
            initial_values[metric_name] = self.get_text(selector)
            
        # Aguarda alguns segundos
        time.sleep(duration)
        
        # Verifica se pelo menos uma métrica foi atualizada
        updated = False
        for metric_name, selector in metrics_selectors.items():
            current_value = self.get_text(selector)
            if current_value != initial_values[metric_name]:
                updated = True
                break
                
        assert updated, "Nenhuma métrica foi atualizada durante o período observado"
        
    def verify_activity_log_updates(self) -> None:
        """Verifica se o log de atividades está sendo atualizado"""
        self.log_assertion("Verificando atualizações no log de atividades")
        
        # Verifica se há pelo menos uma atividade
        activities = self.page.locator(f"{self.SELECTORS['activity_log']} .activity-item")
        expect(activities).to_have_count_greater_than(0)
        
    def scroll_to_results(self) -> None:
        """Rola a página até a seção de resultados"""
        self.scroll_to_element(self.SELECTORS['results_section'])
        
    def scroll_to_upload(self) -> None:
        """Rola a página até a seção de upload"""
        self.scroll_to_element(self.SELECTORS['upload_area'])
        
    def take_full_screenshot(self, name: str) -> bytes:
        """Tira uma captura de tela da página completa"""
        return self.take_screenshot(name)
        
    def verify_responsive_design(self) -> None:
        """Verifica elementos de design responsivo"""
        self.log_assertion("Verificando design responsivo")
        
        # Verifica se elementos principais estão visíveis
        essential_elements = [
            self.SELECTORS['hero_title'],
            self.SELECTORS['upload_area'],
            self.SELECTORS['execute_btn'],
            self.SELECTORS['footer']
        ]
        
        for selector in essential_elements:
            self.verify_element_visible(selector)
