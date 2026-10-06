"""
Testes unitários para os extractors refatorados.
"""
import unittest
from unittest.mock import Mock, patch, MagicMock
import pandas as pd
from pathlib import Path
import tempfile
import json
import sqlite3
import os

# Adiciona o diretório do projeto ao path
import sys
sys.path.append(str(Path(__file__).parent.parent))

from etl.extractors import ExtractorFactory, BaseExtractor
from etl.extractors.csv_extractor import CSVExtractor
from etl.extractors.excel_extractor import ExcelExtractor
from etl.extractors.api_extractor import APIExtractor
from etl.extractors.sqlite_extractor import SQLiteExtractor
from etl.extractors.json_extractor import JSONExtractor
from etl.schemas import SchemaValidator, DataSchema, ValidationError


class TestExtractorFactory(unittest.TestCase):
    """Testes para o ExtractorFactory."""
    
    def test_create_csv_extractor(self):
        """Testa criação de CSV extractor."""
        extractor = ExtractorFactory.create('csv')
        self.assertIsInstance(extractor, CSVExtractor)
        
    def test_create_excel_extractor(self):
        """Testa criação de Excel extractor."""
        extractor = ExtractorFactory.create('excel')
        self.assertIsInstance(extractor, ExcelExtractor)
        
    def test_create_api_extractor(self):
        """Testa criação de API extractor."""
        extractor = ExtractorFactory.create('api')
        self.assertIsInstance(extractor, APIExtractor)
        
    def test_create_invalid_type(self):
        """Testa erro com tipo inválido."""
        with self.assertRaises(ValueError):
            ExtractorFactory.create('invalid_type')
            
    def test_create_from_file_csv(self):
        """Testa criação baseada em arquivo CSV."""
        extractor = ExtractorFactory.create_from_file('test.csv')
        self.assertIsInstance(extractor, CSVExtractor)
        
    def test_create_from_file_excel(self):
        """Testa criação baseada em arquivo Excel."""
        extractor = ExtractorFactory.create_from_file('test.xlsx')
        self.assertIsInstance(extractor, ExcelExtractor)
        
    def test_list_types(self):
        """Testa listagem de tipos disponíveis."""
        types = ExtractorFactory.list_types()
        self.assertIn('csv', types)
        self.assertIn('excel', types)
        self.assertIn('api', types)
        self.assertIn('sqlite', types)
        self.assertIn('json', types)


class TestCSVExtractor(unittest.TestCase):
    """Testes para o CSVExtractor."""
    
    def setUp(self):
        """Configuração inicial dos testes."""
        self.temp_dir = tempfile.mkdtemp()
        self.csv_file = Path(self.temp_dir) / 'test.csv'
        
        # Cria arquivo CSV de teste
        with open(self.csv_file, 'w', encoding='utf-8') as f:
            f.write('id,nome,valor\n')
            f.write('1,Produto A,100.50\n')
            f.write('2,Produto B,200.75\n')
            
    def tearDown(self):
        """Limpeza após os testes."""
        import shutil
        shutil.rmtree(self.temp_dir)
        
    def test_extract_csv(self):
        """Testa extração básica de CSV."""
        extractor = CSVExtractor({'cache_enabled': False})
        df = extractor.extract(file_path=self.csv_file)
        
        self.assertIsInstance(df, pd.DataFrame)
        self.assertEqual(len(df), 2)
        self.assertListEqual(list(df.columns), ['id', 'nome', 'valor'])
        
    def test_extract_csv_with_delimiter(self):
        """Testa CSV com delimitador customizado."""
        # Cria CSV com ponto-vírgula
        csv_file = Path(self.temp_dir) / 'test_semicolon.csv'
        with open(csv_file, 'w', encoding='utf-8') as f:
            f.write('id;nome;valor\n')
            f.write('1;Produto A;100.50\n')
            
        extractor = CSVExtractor({
            'delimiter': ';',
            'cache_enabled': False
        })
        df = extractor.extract(file_path=csv_file)
        
        self.assertEqual(len(df), 1)
        self.assertEqual(df.iloc[0]['nome'], 'Produto A')
        
    def test_file_not_found(self):
        """Testa erro quando arquivo não existe."""
        extractor = CSVExtractor({'cache_enabled': False})
        
        with self.assertRaises(FileNotFoundError):
            extractor.extract(file_path='arquivo_inexistente.csv')
            
    def test_get_file_info(self):
        """Testa obtenção de informações do arquivo."""
        extractor = CSVExtractor({'cache_enabled': False})
        info = extractor.get_file_info(self.csv_file)
        
        self.assertIn('file_path', info)
        self.assertIn('file_size', info)
        self.assertIn('columns', info)
        self.assertEqual(info['n_columns'], 3)


class TestAPIExtractor(unittest.TestCase):
    """Testes para o APIExtractor."""
    
    @patch('requests.Session.request')
    def test_get_request(self, mock_request):
        """Testa requisição GET."""
        # Configura mock
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {'Content-Type': 'application/json'}
        mock_response.json.return_value = {'data': 'test'}
        mock_response.url = 'https://api.test.com/endpoint'
        mock_request.return_value = mock_response
        
        extractor = APIExtractor({
            'base_url': 'https://api.test.com',
            'cache_enabled': False
        })
        
        result = extractor.get('/endpoint')
        
        self.assertEqual(result['data'], 'test')
        self.assertIn('_metadata', result)
        mock_request.assert_called_once()
        
    @patch('requests.Session.request')
    def test_retry_on_error(self, mock_request):
        """Testa retry logic."""
        # Primeira chamada falha, segunda sucede
        mock_response_fail = Mock()
        mock_response_fail.status_code = 500
        mock_response_fail.raise_for_status.side_effect = Exception("Server Error")
        
        mock_response_success = Mock()
        mock_response_success.status_code = 200
        mock_response_success.headers = {'Content-Type': 'application/json'}
        mock_response_success.json.return_value = {'data': 'success'}
        
        mock_request.side_effect = [mock_response_fail, mock_response_success]
        
        extractor = APIExtractor({
            'base_url': 'https://api.test.com',
            'max_retries': 2,
            'backoff_factor': 0.1,  # Reduz tempo de espera para teste
            'cache_enabled': False
        })
        
        with patch('time.sleep'):  # Evita espera real
            result = extractor.get('/endpoint')
            
        self.assertEqual(result['data'], 'success')
        self.assertEqual(mock_request.call_count, 2)
        
    def test_health_check(self):
        """Testa health check."""
        with patch('requests.Session.request') as mock_request:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_request.return_value = mock_response
            
            extractor = APIExtractor({
                'base_url': 'https://api.test.com',
                'cache_enabled': False
            })
            
            is_healthy = extractor.health_check()
            self.assertTrue(is_healthy)


class TestSQLiteExtractor(unittest.TestCase):
    """Testes para o SQLiteExtractor."""
    
    def setUp(self):
        """Configuração inicial dos testes."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_file = Path(self.temp_dir) / 'test.db'
        
        # Cria banco de teste
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE produtos (
                id INTEGER PRIMARY KEY,
                nome TEXT NOT NULL,
                preco REAL NOT NULL
            )
        ''')
        cursor.execute("INSERT INTO produtos (nome, preco) VALUES ('Produto A', 100.50)")
        cursor.execute("INSERT INTO produtos (nome, preco) VALUES ('Produto B', 200.75)")
        conn.commit()
        conn.close()
        
    def tearDown(self):
        """Limpeza após os testes."""
        import shutil
        shutil.rmtree(self.temp_dir)
        
    def test_extract_table(self):
        """Testa extração de tabela completa."""
        extractor = SQLiteExtractor({
            'db_path': self.db_file,
            'cache_enabled': False
        })
        
        df = extractor.extract_table('produtos')
        
        self.assertIsInstance(df, pd.DataFrame)
        self.assertEqual(len(df), 2)
        self.assertListEqual(list(df.columns), ['id', 'nome', 'preco'])
        
    def test_execute_query(self):
        """Testa execução de query customizada."""
        extractor = SQLiteExtractor({
            'db_path': self.db_file,
            'cache_enabled': False
        })
        
        df = extractor.execute_query("SELECT * FROM produtos WHERE preco > 150")
        
        self.assertEqual(len(df), 1)
        self.assertEqual(df.iloc[0]['nome'], 'Produto B')
        
    def test_list_tables(self):
        """Testa listagem de tabelas."""
        extractor = SQLiteExtractor({
            'db_path': self.db_file,
            'cache_enabled': False
        })
        
        tables = extractor.list_tables()
        self.assertIn('produtos', tables)
        
    def test_get_table_info(self):
        """Testa obtenção de informações da tabela."""
        extractor = SQLiteExtractor({
            'db_path': self.db_file,
            'cache_enabled': False
        })
        
        info = extractor.get_table_info('produtos')
        
        self.assertEqual(info['table_name'], 'produtos')
        self.assertEqual(info['row_count'], 2)
        self.assertEqual(len(info['columns']), 3)


class TestJSONExtractor(unittest.TestCase):
    """Testes para o JSONExtractor."""
    
    def setUp(self):
        """Configuração inicial dos testes."""
        self.temp_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        """Limpeza após os testes."""
        import shutil
        shutil.rmtree(self.temp_dir)
        
    def test_extract_simple_json(self):
        """Testa extração de JSON simples."""
        json_file = Path(self.temp_dir) / 'test.json'
        data = {'nome': 'Teste', 'valor': 123}
        
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(data, f)
            
        extractor = JSONExtractor({
            'cache_enabled': False,
            'normalize': False
        })
        
        result = extractor.extract(file_path=json_file)
        self.assertEqual(result, data)
        
    def test_extract_array_json(self):
        """Testa extração de array JSON com normalização."""
        json_file = Path(self.temp_dir) / 'array.json'
        data = [
            {'id': 1, 'nome': 'Item 1'},
            {'id': 2, 'nome': 'Item 2'}
        ]
        
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(data, f)
            
        extractor = JSONExtractor({
            'cache_enabled': False,
            'normalize': True
        })
        
        result = extractor.extract(file_path=json_file)
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(len(result), 2)
        
    def test_extract_jsonl(self):
        """Testa extração de arquivo JSONL."""
        jsonl_file = Path(self.temp_dir) / 'test.jsonl'
        
        with open(jsonl_file, 'w', encoding='utf-8') as f:
            f.write('{"id": 1, "nome": "Item 1"}\n')
            f.write('{"id": 2, "nome": "Item 2"}\n')
            
        extractor = JSONExtractor({
            'cache_enabled': False,
            'json_lines': True
        })
        
        result = extractor.extract(file_path=jsonl_file)
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(len(result), 2)
        
    def test_get_file_structure(self):
        """Testa análise de estrutura JSON."""
        json_file = Path(self.temp_dir) / 'complex.json'
        data = {
            'metadata': {'version': '1.0'},
            'items': [
                {'id': 1, 'details': {'name': 'Item 1'}}
            ]
        }
        
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(data, f)
            
        extractor = JSONExtractor({'cache_enabled': False})
        structure = extractor.get_file_structure(json_file)
        
        self.assertEqual(structure['type'], 'dict')
        self.assertIn('metadata', structure['keys'])
        self.assertIn('items', structure['keys'])


class TestSchemaValidation(unittest.TestCase):
    """Testes para validação de schemas."""
    
    def test_dataframe_validation_success(self):
        """Testa validação bem-sucedida de DataFrame."""
        schema = DataSchema(
            name='test',
            version='1.0',
            fields={'id': 'int64', 'nome': 'object'},
            required_fields=['id', 'nome']
        )
        
        df = pd.DataFrame({
            'id': [1, 2],
            'nome': ['A', 'B']
        })
        
        validator = SchemaValidator()
        result = validator.validate(df, schema)
        self.assertTrue(result)
        
    def test_dataframe_validation_missing_field(self):
        """Testa validação com campo faltando."""
        schema = DataSchema(
            name='test',
            version='1.0',
            fields={'id': 'int64', 'nome': 'object'},
            required_fields=['id', 'nome', 'valor']
        )
        
        df = pd.DataFrame({
            'id': [1, 2],
            'nome': ['A', 'B']
        })
        
        validator = SchemaValidator()
        with self.assertRaises(ValidationError):
            validator.validate(df, schema)
            
    def test_dict_validation_json_schema(self):
        """Testa validação de dicionário com JSON Schema."""
        schema = {
            "type": "object",
            "properties": {
                "id": {"type": "number"},
                "nome": {"type": "string"}
            },
            "required": ["id", "nome"]
        }
        
        data = {"id": 1, "nome": "Teste"}
        
        validator = SchemaValidator()
        result = validator.validate(data, schema)
        self.assertTrue(result)


class TestCache(unittest.TestCase):
    """Testes para funcionalidade de cache."""
    
    def setUp(self):
        """Configuração inicial."""
        self.temp_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        """Limpeza após testes."""
        import shutil
        shutil.rmtree(self.temp_dir)
        
    def test_cache_save_and_retrieve(self):
        """Testa salvamento e recuperação do cache."""
        # Cria CSV de teste
        csv_file = Path(self.temp_dir) / 'test.csv'
        with open(csv_file, 'w') as f:
            f.write('id,valor\n1,100\n')
            
        extractor = CSVExtractor({
            'cache_enabled': True,
            'cache_dir': Path(self.temp_dir) / 'cache',
            'cache_ttl': 3600
        })
        
        # Primeira extração - deve cachear
        df1 = extractor.extract(file_path=csv_file)
        
        # Segunda extração - deve vir do cache
        df2 = extractor.extract(file_path=csv_file)
        
        # Verifica se são iguais
        pd.testing.assert_frame_equal(df1, df2)
        
        # Verifica se cache foi criado
        cache_dir = Path(self.temp_dir) / 'cache'
        self.assertTrue(cache_dir.exists())
        self.assertTrue(any(cache_dir.glob('*.pkl')))
        
    def test_cache_expiration(self):
        """Testa expiração do cache."""
        csv_file = Path(self.temp_dir) / 'test.csv'
        with open(csv_file, 'w') as f:
            f.write('id,valor\n1,100\n')
            
        extractor = CSVExtractor({
            'cache_enabled': True,
            'cache_dir': Path(self.temp_dir) / 'cache',
            'cache_ttl': 0  # Expira imediatamente
        })
        
        # Primeira extração
        df1 = extractor.extract(file_path=csv_file)
        
        # Segunda extração - cache deve ter expirado
        with patch.object(extractor, '_extract_impl') as mock_extract:
            mock_extract.return_value = df1
            extractor.extract(file_path=csv_file)
            
            # Verifica se _extract_impl foi chamado (não usou cache)
            mock_extract.assert_called_once()


if __name__ == '__main__':
    unittest.main()
