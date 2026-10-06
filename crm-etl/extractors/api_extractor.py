"""
Extractor para APIs REST.
Implementa extração de dados de APIs com retry logic e exponential backoff.
"""
from typing import Any, Dict, List, Optional, Union, Callable
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import time
import json
from datetime import datetime
from .base import BaseExtractor


class APIExtractor(BaseExtractor):
    """
    Extractor especializado para APIs REST.
    Implementa retry logic com exponential backoff e tratamento de rate limits.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Inicializa o extractor de API.
        
        Args:
            config: Configurações incluindo:
                - base_url: URL base da API
                - headers: Headers HTTP customizados
                - auth: Autenticação (token, api_key, etc.)
                - timeout: Timeout das requisições em segundos
                - max_retries: Número máximo de tentativas
                - backoff_factor: Fator de exponential backoff
                - retry_statuses: Lista de status HTTP para retry
                - rate_limit_delay: Delay entre requisições (segundos)
        """
        super().__init__(config)
        
        # Configurações da API
        self.base_url = self.config.get('base_url', '')
        self.headers = self.config.get('headers', {})
        self.auth = self.config.get('auth', None)
        self.timeout = self.config.get('timeout', 30)
        self.rate_limit_delay = self.config.get('rate_limit_delay', 0)
        
        # Configurações de retry
        self.max_retries = self.config.get('max_retries', 3)
        self.backoff_factor = self.config.get('backoff_factor', 2)
        self.retry_statuses = self.config.get('retry_statuses', [429, 500, 502, 503, 504])
        
        # Configura sessão com retry
        self.session = self._create_session()
        
        # Timestamp da última requisição
        self._last_request_time = None
        
    def _create_session(self) -> requests.Session:
        """
        Cria uma sessão HTTP com configurações de retry.
        
        Returns:
            Sessão configurada
        """
        session = requests.Session()
        
        # Configura retry strategy
        retry_strategy = Retry(
            total=self.max_retries,
            status_forcelist=self.retry_statuses,
            backoff_factor=self.backoff_factor,
            allowed_methods=["GET", "POST", "PUT", "DELETE", "HEAD", "OPTIONS"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # Configura headers padrão
        session.headers.update(self.headers)
        
        # Configura autenticação se fornecida
        if self.auth:
            if isinstance(self.auth, dict):
                if 'bearer' in self.auth:
                    session.headers['Authorization'] = f"Bearer {self.auth['bearer']}"
                elif 'api_key' in self.auth:
                    session.headers['X-API-Key'] = self.auth['api_key']
                elif 'username' in self.auth and 'password' in self.auth:
                    session.auth = (self.auth['username'], self.auth['password'])
                    
        return session
        
    def _apply_rate_limit(self):
        """Aplica rate limiting entre requisições."""
        if self.rate_limit_delay > 0 and self._last_request_time:
            elapsed = time.time() - self._last_request_time
            if elapsed < self.rate_limit_delay:
                sleep_time = self.rate_limit_delay - elapsed
                self.logger.debug(f"Aplicando rate limit: aguardando {sleep_time:.2f}s")
                time.sleep(sleep_time)
                
    def _make_request(self, method: str, url: str, **kwargs) -> requests.Response:
        """
        Faz uma requisição HTTP com retry logic.
        
        Args:
            method: Método HTTP (GET, POST, etc.)
            url: URL completa ou endpoint
            **kwargs: Argumentos adicionais para requests
            
        Returns:
            Response da requisição
            
        Raises:
            RequestException: Se a requisição falhar após todos os retries
        """
        # Constrói URL completa se necessário
        if not url.startswith(('http://', 'https://')):
            url = f"{self.base_url.rstrip('/')}/{url.lstrip('/')}"
            
        # Aplica rate limiting
        self._apply_rate_limit()
        
        # Adiciona timeout se não especificado
        if 'timeout' not in kwargs:
            kwargs['timeout'] = self.timeout
            
        attempt = 0
        last_exception = None
        
        while attempt <= self.max_retries:
            try:
                self.logger.info(f"Requisição {method} para: {url} (tentativa {attempt + 1})")
                
                response = self.session.request(method, url, **kwargs)
                response.raise_for_status()
                
                self._last_request_time = time.time()
                self.logger.info(f"Requisição bem-sucedida: {response.status_code}")
                
                return response
                
            except requests.exceptions.HTTPError as e:
                status_code = e.response.status_code if e.response else None
                
                if status_code in self.retry_statuses and attempt < self.max_retries:
                    wait_time = self.backoff_factor ** attempt
                    self.logger.warning(f"Erro HTTP {status_code}, tentando novamente em {wait_time}s")
                    time.sleep(wait_time)
                    attempt += 1
                    last_exception = e
                else:
                    self.logger.error(f"Erro HTTP não recuperável: {str(e)}")
                    raise
                    
            except requests.exceptions.RequestException as e:
                if attempt < self.max_retries:
                    wait_time = self.backoff_factor ** attempt
                    self.logger.warning(f"Erro de requisição, tentando novamente em {wait_time}s: {str(e)}")
                    time.sleep(wait_time)
                    attempt += 1
                    last_exception = e
                else:
                    self.logger.error(f"Erro de requisição após {self.max_retries} tentativas: {str(e)}")
                    raise
                    
        # Se chegou aqui, todas as tentativas falharam
        if last_exception:
            raise last_exception
            
    def _extract_impl(self, endpoint: str = '', method: str = 'GET', **kwargs) -> Any:
        """
        Implementa a extração de dados da API.
        
        Args:
            endpoint: Endpoint da API (pode ser URL completa)
            method: Método HTTP
            **kwargs: Parâmetros adicionais (params, data, json, etc.)
            
        Returns:
            Dados extraídos da API
        """
        try:
            response = self._make_request(method, endpoint, **kwargs)
            
            # Tenta decodificar como JSON
            content_type = response.headers.get('Content-Type', '')
            if 'application/json' in content_type:
                data = response.json()
                self.logger.info(f"Resposta JSON recebida com sucesso")
            else:
                data = response.text
                self.logger.info(f"Resposta em formato texto recebida")
                
            # Adiciona metadados da resposta
            if isinstance(data, dict):
                data['_metadata'] = {
                    'status_code': response.status_code,
                    'headers': dict(response.headers),
                    'timestamp': datetime.now().isoformat(),
                    'url': response.url
                }
                
            return data
            
        except Exception as e:
            self.logger.error(f"Erro ao extrair dados da API: {str(e)}")
            raise
            
    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None, **kwargs) -> Any:
        """
        Faz uma requisição GET.
        
        Args:
            endpoint: Endpoint da API
            params: Parâmetros de query
            **kwargs: Argumentos adicionais
            
        Returns:
            Dados da resposta
        """
        return self.extract(endpoint=endpoint, method='GET', params=params, **kwargs)
        
    def post(self, endpoint: str, data: Optional[Any] = None, json: Optional[Any] = None, **kwargs) -> Any:
        """
        Faz uma requisição POST.
        
        Args:
            endpoint: Endpoint da API
            data: Dados do corpo (form-data)
            json: Dados do corpo (JSON)
            **kwargs: Argumentos adicionais
            
        Returns:
            Dados da resposta
        """
        return self.extract(endpoint=endpoint, method='POST', data=data, json=json, **kwargs)
        
    def paginate(self, endpoint: str, page_param: str = 'page', 
                 per_page: int = 100, max_pages: Optional[int] = None,
                 response_key: Optional[str] = None) -> List[Any]:
        """
        Extrai dados paginados da API.
        
        Args:
            endpoint: Endpoint da API
            page_param: Nome do parâmetro de página
            per_page: Itens por página
            max_pages: Número máximo de páginas
            response_key: Chave no response que contém os dados
            
        Returns:
            Lista com todos os dados paginados
        """
        self.logger.info(f"Iniciando extração paginada de: {endpoint}")
        
        all_data = []
        page = 1
        
        while True:
            # Verifica limite de páginas
            if max_pages and page > max_pages:
                self.logger.info(f"Limite de {max_pages} páginas atingido")
                break
                
            # Faz requisição da página
            params = {page_param: page, 'per_page': per_page}
            response = self.get(endpoint, params=params)
            
            # Extrai dados da resposta
            if response_key and isinstance(response, dict):
                page_data = response.get(response_key, [])
            else:
                page_data = response
                
            # Verifica se há dados
            if not page_data or (isinstance(page_data, list) and len(page_data) == 0):
                self.logger.info(f"Sem mais dados na página {page}")
                break
                
            # Adiciona dados
            if isinstance(page_data, list):
                all_data.extend(page_data)
            else:
                all_data.append(page_data)
                
            self.logger.info(f"Página {page} extraída: {len(page_data)} itens")
            page += 1
            
        self.logger.info(f"Extração paginada concluída: {len(all_data)} itens totais")
        return all_data
        
    def health_check(self, endpoint: str = '/health') -> bool:
        """
        Verifica se a API está disponível.
        
        Args:
            endpoint: Endpoint de health check
            
        Returns:
            True se a API está respondendo
        """
        try:
            response = self._make_request('GET', endpoint)
            return response.status_code in [200, 204]
        except Exception as e:
            self.logger.error(f"Health check falhou: {str(e)}")
            return False
