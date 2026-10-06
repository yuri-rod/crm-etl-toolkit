"""
Extractor para arquivos CSV.
Implementa extração de dados de arquivos CSV com suporte a diferentes configurações.
"""
from typing import Any, Dict, List, Optional, Union
import pandas as pd
from pathlib import Path
from .base import BaseExtractor


class CSVExtractor(BaseExtractor):
    """
    Extractor especializado para arquivos CSV.
    Suporta diferentes encodings, delimitadores e opções de parsing.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Inicializa o extractor CSV.
        
        Args:
            config: Configurações incluindo:
                - delimiter: Delimitador do CSV (padrão: ',')
                - encoding: Encoding do arquivo (padrão: 'utf-8')
                - header: Linha do cabeçalho (padrão: 0)
                - parse_dates: Colunas para parse de datas
                - dtype: Tipos de dados específicos
                - chunksize: Tamanho do chunk para arquivos grandes
        """
        super().__init__(config)
        
        # Configurações específicas do CSV
        self.delimiter = self.config.get('delimiter', ',')
        self.encoding = self.config.get('encoding', 'utf-8')
        self.header = self.config.get('header', 0)
        self.parse_dates = self.config.get('parse_dates', None)
        self.dtype = self.config.get('dtype', None)
        self.chunksize = self.config.get('chunksize', None)
        self.na_values = self.config.get('na_values', None)
        
    def _extract_impl(self, file_path: Union[str, Path], **kwargs) -> pd.DataFrame:
        """
        Implementa a extração de dados do CSV.
        
        Args:
            file_path: Caminho do arquivo CSV
            **kwargs: Parâmetros adicionais para pd.read_csv
            
        Returns:
            DataFrame com os dados do CSV
            
        Raises:
            FileNotFoundError: Se o arquivo não existe
            ValueError: Se o arquivo não pode ser lido
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Arquivo CSV não encontrado: {file_path}")
            
        if not file_path.suffix.lower() in ['.csv', '.txt', '.tsv']:
            self.logger.warning(f"Arquivo pode não ser CSV: {file_path.suffix}")
            
        self.logger.info(f"Extraindo dados do arquivo CSV: {file_path}")
        
        try:
            # Prepara parâmetros para leitura
            read_params = {
                'filepath_or_buffer': file_path,
                'sep': self.delimiter,
                'encoding': self.encoding,
                'header': self.header,
                'dtype': self.dtype,
                'parse_dates': self.parse_dates,
                'na_values': self.na_values,
                **kwargs  # Permite sobrescrever configurações
            }
            
            # Remove parâmetros None
            read_params = {k: v for k, v in read_params.items() if v is not None}
            
            # Leitura com ou sem chunks
            if self.chunksize:
                self.logger.info(f"Lendo arquivo em chunks de {self.chunksize} linhas")
                chunks = []
                for chunk in pd.read_csv(**read_params, chunksize=self.chunksize):
                    chunks.append(chunk)
                df = pd.concat(chunks, ignore_index=True)
            else:
                df = pd.read_csv(**read_params)
                
            self.logger.info(f"CSV extraído com sucesso: {len(df)} linhas, {len(df.columns)} colunas")
            
            # Informações sobre o DataFrame
            self._log_dataframe_info(df)
            
            return df
            
        except UnicodeDecodeError as e:
            self.logger.error(f"Erro de encoding ao ler CSV: {str(e)}")
            self.logger.info("Tentando detectar encoding automaticamente...")
            
            # Tenta detectar encoding
            import chardet
            with open(file_path, 'rb') as f:
                result = chardet.detect(f.read(10000))
                detected_encoding = result['encoding']
                
            self.logger.info(f"Encoding detectado: {detected_encoding}")
            
            # Tenta novamente com encoding detectado
            read_params['encoding'] = detected_encoding
            return pd.read_csv(**read_params)
            
        except Exception as e:
            self.logger.error(f"Erro ao extrair CSV: {str(e)}")
            raise
            
    def _log_dataframe_info(self, df: pd.DataFrame):
        """
        Registra informações sobre o DataFrame extraído.
        
        Args:
            df: DataFrame para análise
        """
        self.logger.info("Informações do DataFrame:")
        self.logger.info(f"  - Shape: {df.shape}")
        self.logger.info(f"  - Colunas: {', '.join(df.columns.tolist())}")
        self.logger.info(f"  - Tipos de dados: {df.dtypes.value_counts().to_dict()}")
        
        # Verifica valores nulos
        null_counts = df.isnull().sum()
        if null_counts.any():
            self.logger.warning(f"  - Valores nulos encontrados: {null_counts[null_counts > 0].to_dict()}")
            
    def extract_sample(self, file_path: Union[str, Path], n_rows: int = 5) -> pd.DataFrame:
        """
        Extrai uma amostra do CSV para preview.
        
        Args:
            file_path: Caminho do arquivo
            n_rows: Número de linhas para amostra
            
        Returns:
            DataFrame com amostra dos dados
        """
        self.logger.info(f"Extraindo amostra de {n_rows} linhas")
        
        # Desabilita cache temporariamente
        original_cache = self.cache_enabled
        self.cache_enabled = False
        
        try:
            df = self._extract_impl(file_path, nrows=n_rows)
            return df
        finally:
            self.cache_enabled = original_cache
            
    def get_file_info(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Obtém informações sobre o arquivo CSV sem carregar todos os dados.
        
        Args:
            file_path: Caminho do arquivo
            
        Returns:
            Dicionário com informações do arquivo
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {file_path}")
            
        info = {
            'file_path': str(file_path),
            'file_size': file_path.stat().st_size,
            'file_size_mb': round(file_path.stat().st_size / (1024 * 1024), 2),
            'encoding': self.encoding,
            'delimiter': self.delimiter
        }
        
        # Tenta obter informações básicas
        try:
            # Lê apenas o cabeçalho
            df_head = pd.read_csv(
                file_path,
                nrows=0,
                sep=self.delimiter,
                encoding=self.encoding
            )
            info['columns'] = df_head.columns.tolist()
            info['n_columns'] = len(df_head.columns)
            
            # Conta linhas (pode ser lento para arquivos grandes)
            with open(file_path, 'r', encoding=self.encoding) as f:
                info['n_rows'] = sum(1 for line in f) - 1  # Exclui cabeçalho
                
        except Exception as e:
            self.logger.warning(f"Não foi possível obter todas as informações: {str(e)}")
            
        return info
