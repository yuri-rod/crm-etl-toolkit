"""
Classe base para Page Objects - Padrão de design para testes end-to-end
Sistema ETL Inteligente - CRM Tools
"""

from abc import ABC
from typing import Optional, Dict, Any
from playwright.sync_api import Page, Locator, expect
import time
import logging

logger = logging.getLogger(__name__)


class BasePage(ABC):
    """
    Classe base para Page Objects, fornecendo funcionalidades comuns
    para todas as páginas da aplicação
    """
    
    def __init__(self, page: Page, base_url: str = "http://localhost:8000"):
        self.page = page
        self.base_url = base_url
        self.timeout = 30000
        
    def navigate_to(self, url: str = "") -> None:
        """Navega para uma URL específica"""
        full_url = f"{self.base_url}{url}"
        logger.info(f"Navegando para: {full_url}")
        self.page.goto(full_url)
        
    def wait_for_load(self, timeout: int = 30000) -> None:
        """Aguarda o carregamento completo da página"""
        self.page.wait_for_load_state("networkidle", timeout=timeout)
        
    def wait_for_selector(self, selector: str, timeout: int = None) -> Locator:
        """Aguarda um seletor aparecer na página"""
        timeout = timeout or self.timeout
        return self.page.wait_for_selector(selector, timeout=timeout)
        
    def click_element(self, selector: str, timeout: int = None) -> None:
        """Clica em um elemento"""
        timeout = timeout or self.timeout
        element = self.wait_for_selector(selector, timeout)
        element.click()
        
    def fill_input(self, selector: str, value: str, timeout: int = None) -> None:
        """Preenche um campo de entrada"""
        timeout = timeout or self.timeout
        element = self.wait_for_selector(selector, timeout)
        element.clear()
        element.fill(value)
        
    def get_text(self, selector: str, timeout: int = None) -> str:
        """Obtém o texto de um elemento"""
        timeout = timeout or self.timeout
        element = self.wait_for_selector(selector, timeout)
        return element.text_content() or ""
        
    def is_visible(self, selector: str) -> bool:
        """Verifica se um elemento está visível"""
        try:
            return self.page.locator(selector).is_visible()
        except:
            return False
            
    def is_enabled(self, selector: str) -> bool:
        """Verifica se um elemento está habilitado"""
        try:
            return self.page.locator(selector).is_enabled()
        except:
            return False
            
    def wait_for_text(self, selector: str, expected_text: str, timeout: int = None) -> None:
        """Aguarda até que um elemento contenha um texto específico"""
        timeout = timeout or self.timeout
        self.page.wait_for_function(
            f"document.querySelector('{selector}')?.textContent?.includes('{expected_text}')",
            timeout=timeout
        )
        
    def take_screenshot(self, name: str = None) -> bytes:
        """Tira uma captura de tela"""
        if name:
            path = f"screenshots/{name}.png"
            return self.page.screenshot(path=path, full_page=True)
        return self.page.screenshot(full_page=True)
        
    def scroll_to_element(self, selector: str) -> None:
        """Rola a página até um elemento"""
        element = self.page.locator(selector)
        element.scroll_into_view_if_needed()
        
    def wait_for_download(self, timeout: int = 60000):
        """Aguarda um download ser iniciado"""
        with self.page.expect_download(timeout=timeout) as download_info:
            yield
        return download_info.value
        
    def wait_for_notification(self, message: str = None, timeout: int = None) -> bool:
        """Aguarda uma notificação aparecer"""
        timeout = timeout or self.timeout
        notification_selector = ".notification"
        
        try:
            self.wait_for_selector(notification_selector, timeout=timeout)
            if message:
                self.wait_for_text(notification_selector, message, timeout=timeout)
            return True
        except:
            return False
            
    def dismiss_notification(self) -> None:
        """Fecha uma notificação se estiver visível"""
        notification_close = ".notification button"
        if self.is_visible(notification_close):
            self.click_element(notification_close)
            
    def wait_for_progress_complete(self, timeout: int = 120000) -> None:
        """Aguarda uma barra de progresso completar (100%)"""
        # Aguarda a barra de progresso aparecer
        progress_container = "#progressContainer"
        self.wait_for_selector(progress_container, timeout=10000)
        
        # Aguarda o progresso completar
        completed = False
        start_time = time.time()
        
        while not completed and (time.time() - start_time) * 1000 < timeout:
            try:
                progress_fill = self.page.locator("#progressFill")
                if progress_fill.is_visible():
                    style = progress_fill.get_attribute("style")
                    if "width: 100%" in style or "width:100%" in style:
                        completed = True
                        break
                time.sleep(1)
            except:
                time.sleep(1)
                
        if not completed:
            raise TimeoutError(f"Progress não completou em {timeout}ms")
            
    def get_element_attribute(self, selector: str, attribute: str) -> str:
        """Obtém um atributo de um elemento"""
        element = self.page.locator(selector)
        return element.get_attribute(attribute) or ""
        
    def upload_file(self, file_input_selector: str, file_path: str) -> None:
        """Faz upload de um arquivo"""
        file_input = self.page.locator(file_input_selector)
        file_input.set_input_files(file_path)
        
    def verify_element_text(self, selector: str, expected_text: str) -> None:
        """Verifica se um elemento contém o texto esperado"""
        element = self.page.locator(selector)
        expect(element).to_contain_text(expected_text)
        
    def verify_element_visible(self, selector: str) -> None:
        """Verifica se um elemento está visível"""
        element = self.page.locator(selector)
        expect(element).to_be_visible()
        
    def verify_element_enabled(self, selector: str) -> None:
        """Verifica se um elemento está habilitado"""
        element = self.page.locator(selector)
        expect(element).to_be_enabled()
        
    def verify_page_title(self, expected_title: str) -> None:
        """Verifica o título da página"""
        expect(self.page).to_have_title(expected_title)
        
    def verify_url_contains(self, expected_url_part: str) -> None:
        """Verifica se a URL contém uma parte específica"""
        expect(self.page).to_have_url(lambda url: expected_url_part in url)
        
    def log_step(self, message: str) -> None:
        """Registra um passo do teste"""
        logger.info(f"STEP: {message}")
        
    def log_assertion(self, message: str) -> None:
        """Registra uma asserção do teste"""
        logger.info(f"ASSERT: {message}")
