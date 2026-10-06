"""
Extractor para arquivos JSON.
Implementa extração de dados de arquivos JSON com suporte a diferentes estruturas.
"""
from typing import Any, Dict, List, Optional, Union
import json
import pandas as pd
from pathlib import Path
import ijson
from .base import BaseExtractor


class JSONExtractor(BaseExtractor):
    """
    Extractor especializado para arquivos JSON.
    Suporta JSON simples, arrays e streaming para arquivos grandes.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Inicializa o extractor JSON.
        
        Args:
            config: Configurações incluindo:
                - encoding: Encoding do arquivo (padrão: 'utf-8')
                - parse_float: Função para parse de floats
                - normalize: Se deve normalizar JSON aninhados
                - max_level: Nível máximo de normalização
                - stream: Se deve usar streaming para arquivos grandes
                - array_path: Path para array dentro do JSON (para streaming)
        """
        super().__init__(config)
        
        # Configurações específicas do JSON
        self.encoding = self.config.get('encoding', 'utf-8')
        self.parse_float = self.config.get('parse_float', None)
        self.normalize = self.config.get('normalize', True)
        self.max_level = self.config.get('max_level', 3)
        self.stream = self.config.get('stream', False)
        self.array_path = self.config.get('array_path', None)
        
    def _extract_impl(self, file_path: Union[str, Path], **kwargs) -> Union[Dict, List, pd.DataFrame]:
        """
        Implementa a extração de dados do JSON.
        
        Args:
            file_path: Caminho do arquivo JSON
            **kwargs: Parâmetros adicionais
            
        Returns:
            Dados extraídos (dict, list ou DataFrame)
            
        Raises:
            FileNotFoundError: Se o arquivo não existe
            ValueError: Se o arquivo não pode ser lido
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Arquivo JSON não encontrado: {file_path}")
            
        if not file_path.suffix.lower() in ['.json', '.jsonl']:
            self.logger.warning(f"Arquivo pode não ser JSON: {file_path.suffix}")
            
        self.logger.info(f"Extraindo dados do arquivo JSON: {file_path}")
        
        try:
            # Verifica se é JSONL (JSON Lines)
            if file_path.suffix.lower() == '.jsonl' or self.config.get('json_lines', False):
                return self._extract_jsonl(file_path, **kwargs)
                
            # Verifica se deve usar streaming
            file_size_mb = file_path.stat().st_size / (1024 * 1024)
            if self.stream or file_size_mb > 100:  # Usa streaming para arquivos > 100MB
                self.logger.info(f"Usando streaming para arquivo grande ({file_size_mb:.2f} MB)")
                return self._extract_streaming(file_path, **kwargs)
                
            # Extração normal
            with open(file_path, 'r', encoding=self.encoding) as f:
                data = json.load(f, parse_float=self.parse_float)
                
            self.logger.info(f"JSON extraído com sucesso")
            
            # Normaliza se configurado
            if self.normalize and isinstance(data, (dict, list)):
                return self._normalize_json(data)
                
            return data
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Erro ao decodificar JSON: {str(e)}")
            raise ValueError(f"Arquivo JSON inválido: {str(e)}")
        except Exception as e:
            self.logger.error(f"Erro ao extrair JSON: {str(e)}")
            raise
            
    def _extract_jsonl(self, file_path: Path, **kwargs) -> pd.DataFrame:
        """
        Extrai dados de arquivo JSON Lines.
        
        Args:
            file_path: Caminho do arquivo
            **kwargs: Parâmetros adicionais
            
        Returns:
            DataFrame com dados do JSONL
        """
        self.logger.info("Extraindo arquivo JSON Lines")
        
        data = []
        with open(file_path, 'r', encoding=self.encoding) as f:
            for line_num, line in enumerate(f, 1):
                try:
                    obj = json.loads(line.strip(), parse_float=self.parse_float)
                    data.append(obj)
                except json.JSONDecodeError as e:
                    self.logger.warning(f"Erro na linha {line_num}: {str(e)}")
                    
        self.logger.info(f"JSONL extraído: {len(data)} linhas válidas")
        
        if self.normalize:
            return pd.json_normalize(data, max_level=self.max_level)
        else:
            return pd.DataFrame(data)
            
    def _extract_streaming(self, file_path: Path, **kwargs) -> List[Dict]:
        """
        Extrai dados usando streaming para arquivos grandes.
        
        Args:
            file_path: Caminho do arquivo
            **kwargs: Parâmetros adicionais
            
        Returns:
            Lista com objetos extraídos
        """
        self.logger.info("Iniciando extração com streaming")
        
        data = []
        with open(file_path, 'rb') as f:
            # Define o path para iterar
            if self.array_path:
                parser = ijson.items(f, self.array_path)
            else:
                # Tenta detectar se é array no root
                parser = ijson.items(f, 'item')
                
            for obj in parser:
                data.append(obj)
                
                # Log de progresso a cada 1000 itens
                if len(data) % 1000 == 0:
                    self.logger.debug(f"Extraídos {len(data)} itens...")
                    
        self.logger.info(f"Streaming concluído: {len(data)} itens extraídos")
        return data
        
    def _normalize_json(self, data: Union[Dict, List]) -> pd.DataFrame:
        """
        Normaliza estrutura JSON para DataFrame.
        
        Args:
            data: Dados JSON
            
        Returns:
            DataFrame normalizado
        """
        self.logger.info("Normalizando estrutura JSON")
        
        if isinstance(data, list):
            df = pd.json_normalize(data, max_level=self.max_level)
        elif isinstance(data, dict):
            # Se for um dict com uma chave que contém array
            for key, value in data.items():
                if isinstance(value, list):
                    self.logger.info(f"Normalizando array na chave '{key}'")
                    df = pd.json_normalize(value, max_level=self.max_level)
                    break
            else:
                # Normaliza o dict diretamente
                df = pd.json_normalize([data], max_level=self.max_level)
        else:
            raise ValueError(f"Tipo de dados não suportado para normalização: {type(data)}")
            
        self.logger.info(f"JSON normalizado: {df.shape[0]} linhas, {df.shape[1]} colunas")
        return df
        
    def extract_nested(self, file_path: Union[str, Path], 
                      record_path: Union[str, List[str]],
                      meta: Optional[List[Union[str, List[str]]]] = None,
                      **kwargs) -> pd.DataFrame:
        """
        Extrai dados aninhados do JSON.
        
        Args:
            file_path: Caminho do arquivo
            record_path: Path para os registros aninhados
            meta: Campos de metadados para incluir
            **kwargs: Parâmetros adicionais
            
        Returns:
            DataFrame com dados aninhados normalizados
        """
        file_path = Path(file_path)
        self.logger.info(f"Extraindo dados aninhados de: {record_path}")
        
        with open(file_path, 'r', encoding=self.encoding) as f:
            data = json.load(f, parse_float=self.parse_float)
            
        df = pd.json_normalize(
            data,
            record_path=record_path,
            meta=meta,
            max_level=self.max_level,
            **kwargs
        )
        
        self.logger.info(f"Dados aninhados extraídos: {df.shape[0]} linhas")
        return df
        
    def get_file_structure(self, file_path: Union[str, Path], max_depth: int = 3) -> Dict[str, Any]:
        """
        Analisa a estrutura do arquivo JSON.
        
        Args:
            file_path: Caminho do arquivo
            max_depth: Profundidade máxima para análise
            
        Returns:
            Dicionário com estrutura do JSON
        """
        file_path = Path(file_path)
        
        with open(file_path, 'r', encoding=self.encoding) as f:
            # Lê apenas o início do arquivo para análise
            sample = f.read(10000)
            
        try:
            # Tenta fazer parse do sample
            data = json.loads(sample)
        except:
            # Se falhar, tenta ler o arquivo completo
            with open(file_path, 'r', encoding=self.encoding) as f:
                data = json.load(f)
                
        structure = self._analyze_structure(data, max_depth)
        
        self.logger.info(f"Estrutura do JSON analisada: {structure['type']}")
        return structure
        
    def _analyze_structure(self, data: Any, max_depth: int, current_depth: int = 0) -> Dict[str, Any]:
        """
        Analisa recursivamente a estrutura de dados JSON.
        
        Args:
            data: Dados para analisar
            max_depth: Profundidade máxima
            current_depth: Profundidade atual
            
        Returns:
            Dicionário com análise da estrutura
        """
        if current_depth >= max_depth:
            return {'type': type(data).__name__, 'truncated': True}
            
        if isinstance(data, dict):
            return {
                'type': 'dict',
                'keys': list(data.keys()),
                'structure': {
                    k: self._analyze_structure(v, max_depth, current_depth + 1)
                    for k, v in list(data.items())[:10]  # Limita a 10 chaves
                }
            }
        elif isinstance(data, list):
            if data:
                return {
                    'type': 'list',
                    'length': len(data),
                    'item_type': self._analyze_structure(data[0], max_depth, current_depth + 1)
                }
            else:
                return {'type': 'list', 'length': 0}
        else:
            return {'type': type(data).__name__}
