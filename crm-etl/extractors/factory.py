"""
Factory pattern para criação de extractors.
Centraliza a criação de extractors específicos baseado no tipo de fonte.
"""
from typing import Any, Dict, Optional, Type, Union
from pathlib import Path
from .base import BaseExtractor
from .csv_extractor import CSVExtractor
from .excel_extractor import ExcelExtractor
from .api_extractor import APIExtractor
from .sqlite_extractor import SQLiteExtractor
from .json_extractor import JSONExtractor


class ExtractorFactory:
    """
    Factory para criar extractors específicos.
    Implementa o padrão factory para centralizar a criação de extractors.
    """
    
    # Mapeamento de tipos para classes
    _extractors: Dict[str, Type[BaseExtractor]] = {
        'csv': CSVExtractor,
        'excel': ExcelExtractor,
        'xlsx': ExcelExtractor,
        'xls': ExcelExtractor,
        'api': APIExtractor,
        'rest': APIExtractor,
        'sqlite': SQLiteExtractor,
        'sqlite3': SQLiteExtractor,
        'db': SQLiteExtractor,
        'json': JSONExtractor,
        'jsonl': JSONExtractor,
    }
    
    @classmethod
    def create(cls, source_type: str, config: Optional[Dict[str, Any]] = None) -> BaseExtractor:
        """
        Cria um extractor baseado no tipo de fonte.
        
        Args:
            source_type: Tipo da fonte de dados
            config: Configurações do extractor
            
        Returns:
            Instância do extractor apropriado
            
        Raises:
            ValueError: Se o tipo não é suportado
        """
        source_type = source_type.lower()
        
        if source_type not in cls._extractors:
            raise ValueError(
                f"Tipo de fonte '{source_type}' não suportado. "
                f"Tipos disponíveis: {list(cls._extractors.keys())}"
            )
            
        extractor_class = cls._extractors[source_type]
        return extractor_class(config)
        
    @classmethod
    def create_from_file(cls, file_path: Union[str, Path], 
                        config: Optional[Dict[str, Any]] = None) -> BaseExtractor:
        """
        Cria um extractor baseado na extensão do arquivo.
        
        Args:
            file_path: Caminho do arquivo
            config: Configurações do extractor
            
        Returns:
            Instância do extractor apropriado
            
        Raises:
            ValueError: Se a extensão não é suportada
        """
        file_path = Path(file_path)
        extension = file_path.suffix.lower().lstrip('.')
        
        if not extension:
            raise ValueError(f"Arquivo sem extensão: {file_path}")
            
        # Mapeia extensões para tipos
        extension_map = {
            'csv': 'csv',
            'tsv': 'csv',
            'txt': 'csv',  # Assume CSV para .txt
            'xlsx': 'excel',
            'xls': 'excel',
            'xlsm': 'excel',
            'xlsb': 'excel',
            'json': 'json',
            'jsonl': 'jsonl',
            'db': 'sqlite',
            'sqlite': 'sqlite',
            'sqlite3': 'sqlite',
        }
        
        if extension not in extension_map:
            raise ValueError(
                f"Extensão '{extension}' não suportada. "
                f"Extensões disponíveis: {list(extension_map.keys())}"
            )
            
        source_type = extension_map[extension]
        
        # Adiciona configurações específicas baseadas na extensão
        config = config or {}
        
        if extension == 'tsv':
            config.setdefault('delimiter', '\t')
        elif extension == 'jsonl':
            config['json_lines'] = True
            
        return cls.create(source_type, config)
        
    @classmethod
    def register(cls, source_type: str, extractor_class: Type[BaseExtractor]):
        """
        Registra um novo tipo de extractor.
        
        Args:
            source_type: Tipo da fonte
            extractor_class: Classe do extractor
        """
        if not issubclass(extractor_class, BaseExtractor):
            raise ValueError("Extractor deve herdar de BaseExtractor")
            
        cls._extractors[source_type.lower()] = extractor_class
        
    @classmethod
    def list_types(cls) -> list:
        """
        Lista todos os tipos de extractors disponíveis.
        
        Returns:
            Lista de tipos suportados
        """
        return list(cls._extractors.keys())
        
    @classmethod
    def get_extractor_info(cls, source_type: str) -> Dict[str, Any]:
        """
        Obtém informações sobre um tipo de extractor.
        
        Args:
            source_type: Tipo da fonte
            
        Returns:
            Dicionário com informações do extractor
        """
        source_type = source_type.lower()
        
        if source_type not in cls._extractors:
            raise ValueError(f"Tipo '{source_type}' não encontrado")
            
        extractor_class = cls._extractors[source_type]
        
        return {
            'type': source_type,
            'class': extractor_class.__name__,
            'module': extractor_class.__module__,
            'doc': extractor_class.__doc__ or 'Sem documentação disponível'
        }


# Funções de conveniência
def create_extractor(source_type: str, config: Optional[Dict[str, Any]] = None) -> BaseExtractor:
    """
    Cria um extractor usando a factory.
    
    Args:
        source_type: Tipo da fonte
        config: Configurações
        
    Returns:
        Extractor criado
    """
    return ExtractorFactory.create(source_type, config)


def create_extractor_from_file(file_path: Union[str, Path], 
                              config: Optional[Dict[str, Any]] = None) -> BaseExtractor:
    """
    Cria um extractor baseado em arquivo.
    
    Args:
        file_path: Caminho do arquivo
        config: Configurações
        
    Returns:
        Extractor criado
    """
    return ExtractorFactory.create_from_file(file_path, config)
