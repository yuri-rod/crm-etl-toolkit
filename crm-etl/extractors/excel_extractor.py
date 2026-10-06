"""
Extractor para arquivos Excel.
Implementa extração de dados de arquivos Excel (.xlsx, .xls).
"""
from typing import Any, Dict, List, Optional, Union
import pandas as pd
from pathlib import Path
from .base import BaseExtractor


class ExcelExtractor(BaseExtractor):
    """
    Extractor especializado para arquivos Excel.
    Suporta múltiplas planilhas e diferentes configurações de leitura.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Inicializa o extractor Excel.
        
        Args:
            config: Configurações incluindo:
                - sheet_name: Nome ou índice da planilha (padrão: 0)
                - header: Linha do cabeçalho (padrão: 0)
                - usecols: Colunas a serem lidas
                - dtype: Tipos de dados específicos
                - parse_dates: Colunas para parse de datas
                - engine: Engine de leitura ('openpyxl', 'xlrd', etc.)
        """
        super().__init__(config)
        
        # Configurações específicas do Excel
        self.sheet_name = self.config.get('sheet_name', 0)
        self.header = self.config.get('header', 0)
        self.usecols = self.config.get('usecols', None)
        self.dtype = self.config.get('dtype', None)
        self.parse_dates = self.config.get('parse_dates', None)
        self.engine = self.config.get('engine', None)
        self.na_values = self.config.get('na_values', None)
        
    def _extract_impl(self, file_path: Union[str, Path], **kwargs) -> Union[pd.DataFrame, Dict[str, pd.DataFrame]]:
        """
        Implementa a extração de dados do Excel.
        
        Args:
            file_path: Caminho do arquivo Excel
            **kwargs: Parâmetros adicionais para pd.read_excel
            
        Returns:
            DataFrame ou dicionário de DataFrames (se múltiplas planilhas)
            
        Raises:
            FileNotFoundError: Se o arquivo não existe
            ValueError: Se o arquivo não pode ser lido
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Arquivo Excel não encontrado: {file_path}")
            
        if not file_path.suffix.lower() in ['.xlsx', '.xls', '.xlsm', '.xlsb']:
            self.logger.warning(f"Arquivo pode não ser Excel: {file_path.suffix}")
            
        self.logger.info(f"Extraindo dados do arquivo Excel: {file_path}")
        
        try:
            # Prepara parâmetros para leitura
            read_params = {
                'io': file_path,
                'sheet_name': self.sheet_name,
                'header': self.header,
                'usecols': self.usecols,
                'dtype': self.dtype,
                'parse_dates': self.parse_dates,
                'engine': self.engine,
                'na_values': self.na_values,
                **kwargs  # Permite sobrescrever configurações
            }
            
            # Remove parâmetros None
            read_params = {k: v for k, v in read_params.items() if v is not None}
            
            # Lê o Excel
            result = pd.read_excel(**read_params)
            
            # Se retornou múltiplas planilhas
            if isinstance(result, dict):
                self.logger.info(f"Excel extraído com sucesso: {len(result)} planilhas")
                for sheet_name, df in result.items():
                    self.logger.info(f"  - Planilha '{sheet_name}': {len(df)} linhas, {len(df.columns)} colunas")
                    self._log_dataframe_info(df)
            else:
                self.logger.info(f"Excel extraído com sucesso: {len(result)} linhas, {len(result.columns)} colunas")
                self._log_dataframe_info(result)
                
            return result
            
        except Exception as e:
            self.logger.error(f"Erro ao extrair Excel: {str(e)}")
            raise
            
    def _log_dataframe_info(self, df: pd.DataFrame):
        """
        Registra informações sobre o DataFrame extraído.
        
        Args:
            df: DataFrame para análise
        """
        self.logger.debug(f"  Shape: {df.shape}")
        self.logger.debug(f"  Colunas: {', '.join(df.columns.tolist()[:10])}" + 
                         ("..." if len(df.columns) > 10 else ""))
        
        # Verifica valores nulos
        null_counts = df.isnull().sum()
        if null_counts.any():
            cols_with_nulls = null_counts[null_counts > 0].index.tolist()
            self.logger.debug(f"  Colunas com valores nulos: {', '.join(cols_with_nulls[:5])}" +
                            ("..." if len(cols_with_nulls) > 5 else ""))
                            
    def list_sheets(self, file_path: Union[str, Path]) -> List[str]:
        """
        Lista todas as planilhas disponíveis no arquivo Excel.
        
        Args:
            file_path: Caminho do arquivo
            
        Returns:
            Lista com nomes das planilhas
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {file_path}")
            
        self.logger.info(f"Listando planilhas do arquivo: {file_path}")
        
        try:
            # Usa openpyxl para arquivos .xlsx
            if file_path.suffix.lower() == '.xlsx':
                from openpyxl import load_workbook
                wb = load_workbook(file_path, read_only=True)
                sheets = wb.sheetnames
                wb.close()
            else:
                # Para outros formatos, usa pandas
                xl_file = pd.ExcelFile(file_path, engine=self.engine)
                sheets = xl_file.sheet_names
                
            self.logger.info(f"Planilhas encontradas: {sheets}")
            return sheets
            
        except Exception as e:
            self.logger.error(f"Erro ao listar planilhas: {str(e)}")
            raise
            
    def extract_sheet(self, file_path: Union[str, Path], sheet_name: Union[str, int]) -> pd.DataFrame:
        """
        Extrai uma planilha específica do Excel.
        
        Args:
            file_path: Caminho do arquivo
            sheet_name: Nome ou índice da planilha
            
        Returns:
            DataFrame com dados da planilha
        """
        self.logger.info(f"Extraindo planilha '{sheet_name}'")
        
        # Sobrescreve configuração temporariamente
        original_sheet = self.sheet_name
        self.sheet_name = sheet_name
        
        try:
            df = self._extract_impl(file_path)
            return df
        finally:
            self.sheet_name = original_sheet
            
    def extract_all_sheets(self, file_path: Union[str, Path]) -> Dict[str, pd.DataFrame]:
        """
        Extrai todas as planilhas do Excel.
        
        Args:
            file_path: Caminho do arquivo
            
        Returns:
            Dicionário com DataFrames de todas as planilhas
        """
        self.logger.info("Extraindo todas as planilhas")
        
        # Desabilita cache temporariamente
        original_cache = self.cache_enabled
        self.cache_enabled = False
        
        try:
            return self._extract_impl(file_path, sheet_name=None)
        finally:
            self.cache_enabled = original_cache
            
    def get_file_info(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Obtém informações sobre o arquivo Excel.
        
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
            'file_type': file_path.suffix.lower()
        }
        
        try:
            # Lista planilhas
            sheets = self.list_sheets(file_path)
            info['sheets'] = sheets
            info['n_sheets'] = len(sheets)
            
            # Informações básicas da primeira planilha
            if sheets:
                df_sample = pd.read_excel(file_path, sheet_name=sheets[0], nrows=0)
                info['columns_first_sheet'] = df_sample.columns.tolist()
                info['n_columns_first_sheet'] = len(df_sample.columns)
                
        except Exception as e:
            self.logger.warning(f"Não foi possível obter todas as informações: {str(e)}")
            
        return info
