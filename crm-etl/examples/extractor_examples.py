"""
Exemplos de uso dos novos extractors refatorados.
Demonstra as diferentes formas de extrair dados de múltiplas fontes.
"""
import sys
from pathlib import Path

# Adiciona o diretório pai ao path
sys.path.append(str(Path(__file__).parent.parent))

from etl.extractors import ExtractorFactory
from etl.extract import Extract, create_extractor, extract_from_file
from etl.schemas import DataSchema, COMMON_SCHEMAS
import pandas as pd


def exemplo_csv():
    """Exemplo de extração de dados CSV."""
    print("\n=== Exemplo CSV ===")
    
    # Método 1: Usando factory diretamente
    csv_extractor = ExtractorFactory.create('csv', {
        'delimiter': ',',
        'encoding': 'utf-8',
        'cache_enabled': True,
        'log_level': 'INFO'
    })
    
    # Simula extração (substitua pelo caminho real)
    # df = csv_extractor.extract(file_path='data/vendas.csv')
    print("CSV Extractor criado com sucesso")
    
    # Método 2: Usando Extract wrapper
    extractor = Extract('csv', {
        'delimiter': ';',
        'parse_dates': ['data_venda']
    })
    # df = extractor.extract(file_path='data/vendas.csv')
    
    # Método 3: Função utilitária
    # df = extract_from_file('data/vendas.csv')
    

def exemplo_excel():
    """Exemplo de extração de dados Excel."""
    print("\n=== Exemplo Excel ===")
    
    # Configuração para Excel
    config = {
        'sheet_name': 'Vendas',
        'header': 0,
        'usecols': ['A:F'],
        'parse_dates': ['Data'],
        'cache_enabled': True,
        'cache_ttl': 7200  # 2 horas
    }
    
    excel_extractor = ExtractorFactory.create('excel', config)
    
    # Lista planilhas disponíveis
    # sheets = excel_extractor.list_sheets('relatorio.xlsx')
    # print(f"Planilhas disponíveis: {sheets}")
    
    # Extrai planilha específica
    # df = excel_extractor.extract_sheet('relatorio.xlsx', 'Vendas')
    
    print("Excel Extractor configurado")


def exemplo_api():
    """Exemplo de extração de dados de API."""
    print("\n=== Exemplo API ===")
    
    # Configuração para API com autenticação
    config = {
        'base_url': 'https://api.exemplo.com/v1',
        'auth': {
            'bearer': 'seu_token_aqui'
        },
        'headers': {
            'Accept': 'application/json',
            'User-Agent': 'ETL-Extractor/1.0'
        },
        'timeout': 30,
        'max_retries': 3,
        'backoff_factor': 2,
        'rate_limit_delay': 1,  # 1 segundo entre requisições
        'cache_enabled': True,
        'cache_ttl': 3600
    }
    
    api_extractor = ExtractorFactory.create('api', config)
    
    # Exemplos de uso
    # 1. GET simples
    # data = api_extractor.get('/users')
    
    # 2. GET com parâmetros
    # data = api_extractor.get('/products', params={'category': 'electronics'})
    
    # 3. POST com dados
    # response = api_extractor.post('/orders', json={'product_id': 123, 'quantity': 2})
    
    # 4. Paginação automática
    # all_users = api_extractor.paginate('/users', per_page=100, max_pages=10)
    
    print("API Extractor configurado com retry logic")


def exemplo_sqlite():
    """Exemplo de extração de dados SQLite."""
    print("\n=== Exemplo SQLite ===")
    
    # Configuração para SQLite
    config = {
        'db_path': 'database/vendas.db',
        'timeout': 30,
        'parse_dates': ['created_at', 'updated_at'],
        'cache_enabled': True
    }
    
    db_extractor = ExtractorFactory.create('sqlite', config)
    
    # Lista tabelas
    # tables = db_extractor.list_tables()
    # print(f"Tabelas: {tables}")
    
    # Informações de uma tabela
    # info = db_extractor.get_table_info('vendas')
    # print(f"Estrutura da tabela: {info}")
    
    # Extrai dados com query
    # df = db_extractor.execute_query('''
    #     SELECT v.*, c.nome as cliente_nome
    #     FROM vendas v
    #     JOIN clientes c ON v.cliente_id = c.id
    #     WHERE v.data >= date('now', '-30 days')
    # ''')
    
    # Extrai tabela completa
    # df = db_extractor.extract_table('produtos', limit=1000)
    
    print("SQLite Extractor configurado")


def exemplo_json():
    """Exemplo de extração de dados JSON."""
    print("\n=== Exemplo JSON ===")
    
    # Configuração para JSON
    config = {
        'encoding': 'utf-8',
        'normalize': True,  # Normaliza estruturas aninhadas
        'max_level': 3,     # Profundidade máxima de normalização
        'stream': False,    # Use True para arquivos grandes
        'cache_enabled': True
    }
    
    json_extractor = ExtractorFactory.create('json', config)
    
    # Extração simples
    # data = json_extractor.extract(file_path='config.json')
    
    # Extração de estrutura aninhada
    # df = json_extractor.extract_nested(
    #     'data/pedidos.json',
    #     record_path=['itens'],
    #     meta=['pedido_id', 'cliente', 'data']
    # )
    
    # Análise de estrutura
    # structure = json_extractor.get_file_structure('complex_data.json')
    # print(f"Estrutura: {structure}")
    
    print("JSON Extractor configurado")


def exemplo_validacao():
    """Exemplo de validação com schemas."""
    print("\n=== Exemplo de Validação ===")
    
    # Define um schema customizado
    schema_vendas = DataSchema(
        name='vendas',
        version='1.0',
        fields={
            'id': 'int64',
            'produto': 'object',
            'quantidade': 'int64',
            'preco': 'float64',
            'data_venda': 'datetime64[ns]'
        },
        required_fields=['id', 'produto', 'quantidade', 'preco'],
        constraints={
            'quantidade': {'min': 1},
            'preco': {'min': 0.01},
            'id': {'unique': True, 'not_null': True}
        }
    )
    
    # Extractor com validação
    config = {
        'schema': schema_vendas,
        'cache_enabled': True
    }
    
    extractor = create_extractor('csv', config)
    
    # Dados serão validados automaticamente na extração
    # df = extractor.extract(file_path='vendas.csv')
    
    print("Validação de schema configurada")


def exemplo_cache():
    """Exemplo de uso de cache."""
    print("\n=== Exemplo de Cache ===")
    
    # Configuração com cache personalizado
    config = {
        'cache_enabled': True,
        'cache_ttl': 7200,  # 2 horas
        'cache_dir': '.cache/extractors',
        'log_level': 'DEBUG'
    }
    
    # Primeira extração - dados serão cacheados
    extractor = create_extractor('csv', config)
    # df1 = extractor.extract(file_path='large_file.csv')
    # print("Primeira extração - dados cacheados")
    
    # Segunda extração - dados virão do cache
    # df2 = extractor.extract(file_path='large_file.csv')
    # print("Segunda extração - dados do cache")
    
    # Limpar cache se necessário
    # extractor.get_extractor().clear_cache()
    
    print("Cache configurado e funcionando")


def exemplo_factory_pattern():
    """Exemplo do padrão factory."""
    print("\n=== Exemplo Factory Pattern ===")
    
    # Lista tipos disponíveis
    tipos = ExtractorFactory.list_types()
    print(f"Tipos de extractors disponíveis: {tipos}")
    
    # Informações sobre um tipo
    info = ExtractorFactory.get_extractor_info('api')
    print(f"\nInformações do API Extractor:")
    print(f"  Classe: {info['class']}")
    print(f"  Módulo: {info['module']}")
    
    # Cria extractor pelo tipo de arquivo
    # csv_ext = ExtractorFactory.create_from_file('vendas.csv')
    # excel_ext = ExtractorFactory.create_from_file('relatorio.xlsx')
    # json_ext = ExtractorFactory.create_from_file('config.json')
    
    print("\nFactory pattern funcionando corretamente")


def main():
    """Executa todos os exemplos."""
    print("=== EXEMPLOS DE USO DOS EXTRACTORS ===")
    
    exemplo_csv()
    exemplo_excel()
    exemplo_api()
    exemplo_sqlite()
    exemplo_json()
    exemplo_validacao()
    exemplo_cache()
    exemplo_factory_pattern()
    
    print("\n=== RESUMO DAS MELHORIAS ===")
    print("✓ Suporte para múltiplas fontes (CSV, Excel, API, SQLite, JSON)")
    print("✓ Retry logic com exponential backoff para APIs")
    print("✓ Validação com schemas")
    print("✓ Logging estruturado em português")
    print("✓ Factory pattern para criação de extractors")
    print("✓ Cache local para otimização")
    print("\nTodos os extractors estão prontos para uso!")


if __name__ == "__main__":
    main()
