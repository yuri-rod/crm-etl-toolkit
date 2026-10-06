"""
Extractor para bancos de dados SQLite.
Implementa extração de dados de arquivos SQLite.
"""
from typing import Any, Dict, List, Optional, Union
import sqlite3
import pandas as pd
from pathlib import Path
from contextlib import contextmanager
from .base import BaseExtractor


class SQLiteExtractor(BaseExtractor):
    """
    Extractor especializado para bancos de dados SQLite.
    Suporta queries customizadas e extração de tabelas completas.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Inicializa o extractor SQLite.
        
        Args:
            config: Configurações incluindo:
                - db_path: Caminho do arquivo SQLite
                - timeout: Timeout de conexão em segundos
                - check_same_thread: Se False, permite conexões multi-thread
                - parse_dates: Colunas para parse de datas
        """
        super().__init__(config)
        
        # Configurações do SQLite
        self.db_path = self.config.get('db_path')
        self.timeout = self.config.get('timeout', 10.0)
        self.check_same_thread = self.config.get('check_same_thread', True)
        self.parse_dates = self.config.get('parse_dates', None)
        
    @contextmanager
    def _get_connection(self, db_path: Optional[Union[str, Path]] = None):
        """
        Context manager para conexão com SQLite.
        
        Args:
            db_path: Caminho do banco (usa self.db_path se não fornecido)
            
        Yields:
            Conexão SQLite
        """
        db_path = db_path or self.db_path
        if not db_path:
            raise ValueError("Caminho do banco de dados não especificado")
            
        db_path = Path(db_path)
        if not db_path.exists():
            raise FileNotFoundError(f"Banco de dados não encontrado: {db_path}")
            
        self.logger.info(f"Conectando ao banco SQLite: {db_path}")
        
        conn = None
        try:
            conn = sqlite3.connect(
                str(db_path),
                timeout=self.timeout,
                check_same_thread=self.check_same_thread
            )
            # Habilita row factory para retornar dicts
            conn.row_factory = sqlite3.Row
            yield conn
        finally:
            if conn:
                conn.close()
                self.logger.info("Conexão SQLite fechada")
                
    def _extract_impl(self, query: Optional[str] = None, 
                     table_name: Optional[str] = None,
                     db_path: Optional[Union[str, Path]] = None,
                     params: Optional[Union[List, Dict]] = None,
                     **kwargs) -> pd.DataFrame:
        """
        Implementa a extração de dados do SQLite.
        
        Args:
            query: Query SQL para executar
            table_name: Nome da tabela (alternativa à query)
            db_path: Caminho do banco (opcional, usa config se não fornecido)
            params: Parâmetros para a query
            **kwargs: Argumentos adicionais para pd.read_sql
            
        Returns:
            DataFrame com os dados extraídos
            
        Raises:
            ValueError: Se nem query nem table_name forem fornecidos
        """
        if not query and not table_name:
            raise ValueError("Deve fornecer 'query' ou 'table_name'")
            
        # Se forneceu table_name, cria query
        if table_name and not query:
            query = f"SELECT * FROM {table_name}"
            
        with self._get_connection(db_path) as conn:
            try:
                self.logger.info(f"Executando query: {query[:100]}...")
                
                # Prepara parâmetros para read_sql
                read_params = {
                    'sql': query,
                    'con': conn,
                    'params': params,
                    'parse_dates': self.parse_dates,
                    **kwargs
                }
                
                # Remove parâmetros None
                read_params = {k: v for k, v in read_params.items() if v is not None}
                
                # Executa query
                df = pd.read_sql(**read_params)
                
                self.logger.info(f"Query executada com sucesso: {len(df)} linhas, {len(df.columns)} colunas")
                self._log_dataframe_info(df)
                
                return df
                
            except Exception as e:
                self.logger.error(f"Erro ao executar query: {str(e)}")
                raise
                
    def _log_dataframe_info(self, df: pd.DataFrame):
        """
        Registra informações sobre o DataFrame extraído.
        
        Args:
            df: DataFrame para análise
        """
        self.logger.debug(f"  Shape: {df.shape}")
        if len(df.columns) <= 20:
            self.logger.debug(f"  Colunas: {', '.join(df.columns.tolist())}")
        else:
            self.logger.debug(f"  Total de colunas: {len(df.columns)}")
            
    def list_tables(self, db_path: Optional[Union[str, Path]] = None) -> List[str]:
        """
        Lista todas as tabelas do banco SQLite.
        
        Args:
            db_path: Caminho do banco (opcional)
            
        Returns:
            Lista com nomes das tabelas
        """
        query = """
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name NOT LIKE 'sqlite_%'
        ORDER BY name
        """
        
        with self._get_connection(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            tables = [row[0] for row in cursor.fetchall()]
            
        self.logger.info(f"Tabelas encontradas: {tables}")
        return tables
        
    def get_table_info(self, table_name: str, db_path: Optional[Union[str, Path]] = None) -> Dict[str, Any]:
        """
        Obtém informações sobre uma tabela específica.
        
        Args:
            table_name: Nome da tabela
            db_path: Caminho do banco (opcional)
            
        Returns:
            Dicionário com informações da tabela
        """
        info = {'table_name': table_name}
        
        with self._get_connection(db_path) as conn:
            # Schema da tabela
            cursor = conn.cursor()
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            
            info['columns'] = [
                {
                    'name': col[1],
                    'type': col[2],
                    'nullable': not col[3],
                    'default': col[4],
                    'primary_key': bool(col[5])
                }
                for col in columns
            ]
            
            # Contagem de linhas
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            info['row_count'] = cursor.fetchone()[0]
            
            # Índices
            cursor.execute(f"PRAGMA index_list({table_name})")
            info['indexes'] = [idx[1] for idx in cursor.fetchall()]
            
        self.logger.info(f"Informações da tabela '{table_name}': {info['row_count']} linhas, {len(info['columns'])} colunas")
        return info
        
    def extract_table(self, table_name: str, db_path: Optional[Union[str, Path]] = None,
                     limit: Optional[int] = None, offset: Optional[int] = None) -> pd.DataFrame:
        """
        Extrai dados de uma tabela específica.
        
        Args:
            table_name: Nome da tabela
            db_path: Caminho do banco (opcional)
            limit: Limite de linhas
            offset: Offset para paginação
            
        Returns:
            DataFrame com dados da tabela
        """
        query = f"SELECT * FROM {table_name}"
        
        if limit or offset:
            query += f" LIMIT {limit or -1} OFFSET {offset or 0}"
            
        return self._extract_impl(query=query, db_path=db_path)
        
    def execute_query(self, query: str, db_path: Optional[Union[str, Path]] = None,
                     params: Optional[Union[List, Dict]] = None) -> pd.DataFrame:
        """
        Executa uma query customizada.
        
        Args:
            query: Query SQL
            db_path: Caminho do banco (opcional)
            params: Parâmetros para a query
            
        Returns:
            DataFrame com resultado da query
        """
        return self._extract_impl(query=query, db_path=db_path, params=params)
        
    def get_database_info(self, db_path: Optional[Union[str, Path]] = None) -> Dict[str, Any]:
        """
        Obtém informações gerais sobre o banco de dados.
        
        Args:
            db_path: Caminho do banco (opcional)
            
        Returns:
            Dicionário com informações do banco
        """
        db_path = Path(db_path or self.db_path)
        
        info = {
            'db_path': str(db_path),
            'file_size': db_path.stat().st_size,
            'file_size_mb': round(db_path.stat().st_size / (1024 * 1024), 2)
        }
        
        with self._get_connection(db_path) as conn:
            cursor = conn.cursor()
            
            # Versão do SQLite
            cursor.execute("SELECT sqlite_version()")
            info['sqlite_version'] = cursor.fetchone()[0]
            
            # Lista de tabelas
            info['tables'] = self.list_tables(db_path)
            info['n_tables'] = len(info['tables'])
            
            # Total de linhas em todas as tabelas
            total_rows = 0
            for table in info['tables']:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                total_rows += cursor.fetchone()[0]
            info['total_rows'] = total_rows
            
        self.logger.info(f"Banco de dados: {info['n_tables']} tabelas, {info['total_rows']} linhas totais")
        return info
