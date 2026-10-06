"""
Classe base para todos os extractors.
Implementa funcionalidades comuns como validação, cache e logging.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
import logging
import json
import hashlib
from pathlib import Path
from datetime import datetime, timedelta
import pickle
from ..base import ExtractBase
from ..schemas import SchemaValidator


class BaseExtractor(ExtractBase):
    """
    Classe base para todos os extractors.
    Fornece funcionalidades comuns como cache, validação e logging estruturado.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Inicializa o extractor base.
        
        Args:
            config: Configurações do extractor incluindo:
                - cache_enabled: Se o cache está habilitado
                - cache_ttl: Tempo de vida do cache em segundos
                - cache_dir: Diretório para armazenar cache
                - schema: Schema para validação dos dados
                - log_level: Nível de logging
        """
        super().__init__(config)
        
        # Configurações de cache
        self.cache_enabled = self.config.get('cache_enabled', True)
        self.cache_ttl = self.config.get('cache_ttl', 3600)  # 1 hora padrão
        self.cache_dir = Path(self.config.get('cache_dir', '.cache/extractors'))
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Schema de validação
        self.schema = self.config.get('schema')
        self.validator = SchemaValidator() if self.schema else None
        
        # Configuração de logging estruturado
        self._setup_structured_logging()
        
    def _setup_structured_logging(self):
        """Configura logging estruturado em português."""
        self.logger.handlers.clear()
        
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%d/%m/%Y %H:%M:%S'
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        
        log_level = self.config.get('log_level', 'INFO')
        self.logger.setLevel(getattr(logging, log_level.upper()))
        
    def _get_cache_key(self, params: Dict[str, Any]) -> str:
        """
        Gera uma chave única para o cache baseada nos parâmetros.
        
        Args:
            params: Parâmetros da extração
            
        Returns:
            Chave hash para o cache
        """
        params_str = json.dumps(params, sort_keys=True)
        return hashlib.md5(params_str.encode()).hexdigest()
        
    def _get_from_cache(self, cache_key: str) -> Optional[Any]:
        """
        Recupera dados do cache se ainda válidos.
        
        Args:
            cache_key: Chave do cache
            
        Returns:
            Dados do cache ou None se não encontrado/expirado
        """
        if not self.cache_enabled:
            return None
            
        cache_file = self.cache_dir / f"{cache_key}.pkl"
        
        if not cache_file.exists():
            self.logger.debug(f"Cache não encontrado para chave: {cache_key}")
            return None
            
        try:
            with open(cache_file, 'rb') as f:
                cached_data = pickle.load(f)
                
            # Verifica se o cache expirou
            if datetime.now() > cached_data['expiry']:
                self.logger.info("Cache expirado, removendo arquivo")
                cache_file.unlink()
                return None
                
            self.logger.info("Dados recuperados do cache com sucesso")
            return cached_data['data']
            
        except Exception as e:
            self.logger.error(f"Erro ao ler cache: {str(e)}")
            return None
            
    def _save_to_cache(self, cache_key: str, data: Any):
        """
        Salva dados no cache.
        
        Args:
            cache_key: Chave do cache
            data: Dados para armazenar
        """
        if not self.cache_enabled:
            return
            
        cache_file = self.cache_dir / f"{cache_key}.pkl"
        
        try:
            cache_data = {
                'data': data,
                'expiry': datetime.now() + timedelta(seconds=self.cache_ttl),
                'created_at': datetime.now()
            }
            
            with open(cache_file, 'wb') as f:
                pickle.dump(cache_data, f)
                
            self.logger.info("Dados salvos no cache com sucesso")
            
        except Exception as e:
            self.logger.error(f"Erro ao salvar cache: {str(e)}")
            
    def validate_data(self, data: Any) -> bool:
        """
        Valida os dados extraídos usando o schema configurado.
        
        Args:
            data: Dados para validar
            
        Returns:
            True se os dados são válidos
            
        Raises:
            ValidationError: Se os dados não são válidos
        """
        if not self.validator or not self.schema:
            return True
            
        try:
            self.validator.validate(data, self.schema)
            self.logger.info("Dados validados com sucesso")
            return True
        except Exception as e:
            self.logger.error(f"Erro na validação dos dados: {str(e)}")
            raise
            
    def extract(self, **kwargs) -> Any:
        """
        Extrai dados com suporte a cache e validação.
        
        Args:
            **kwargs: Parâmetros específicos do extractor
            
        Returns:
            Dados extraídos e validados
        """
        # Gera chave de cache
        cache_key = self._get_cache_key(kwargs)
        
        # Tenta recuperar do cache
        cached_data = self._get_from_cache(cache_key)
        if cached_data is not None:
            return cached_data
            
        # Extrai dados usando método específico
        self.logger.info(f"Iniciando extração de dados - {self.__class__.__name__}")
        try:
            data = self._extract_impl(**kwargs)
            
            # Valida dados se schema configurado
            if self.schema:
                self.validate_data(data)
                
            # Salva no cache
            self._save_to_cache(cache_key, data)
            
            self.logger.info("Extração concluída com sucesso")
            return data
            
        except Exception as e:
            self.logger.error(f"Erro durante extração: {str(e)}")
            raise
            
    @abstractmethod
    def _extract_impl(self, **kwargs) -> Any:
        """
        Implementação específica da extração.
        Deve ser implementado por cada extractor concreto.
        
        Args:
            **kwargs: Parâmetros específicos do extractor
            
        Returns:
            Dados extraídos
        """
        pass
        
    def clear_cache(self):
        """Limpa todo o cache do extractor."""
        if not self.cache_dir.exists():
            return
            
        for cache_file in self.cache_dir.glob("*.pkl"):
            try:
                cache_file.unlink()
            except Exception as e:
                self.logger.error(f"Erro ao remover arquivo de cache: {str(e)}")
                
        self.logger.info("Cache limpo com sucesso")
