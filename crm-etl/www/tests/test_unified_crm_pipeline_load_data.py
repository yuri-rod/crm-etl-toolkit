#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=======================================================
--- Testes Unitários: UnifiedCRMPipeline._load_data ---
=======================================================

Casos de teste para validação de importação de CSV/XLSX:
1. CSV com separador vírgula (,)
2. CSV com separador ponto e vírgula (;)
3. CSV com encoding ISO-8859-1 e caracteres acentuados
4. Arquivo XLSX
5. Detecção automática de separadores
6. Validação de número de colunas > 1
7. Tratamento de erros para formatos inválidos

Desenvolvido para CRM ETL
"""

import pytest
import pandas as pd
import tempfile
import os
from pathlib import Path
import sys

# Adicionar o diretório backend ao path para importar o módulo
backend_path = Path(__file__).parent.parent.parent / "backend"
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

# Importar a classe que será testada
from unificado import UnifiedCRMPipeline


class TestUnifiedCRMPipelineLoadData:
    """Classe de testes para o método _load_data da UnifiedCRMPipeline."""
    
    @pytest.fixture
    def pipeline(self):
        """Fixture para criar uma instância da pipeline."""
        return UnifiedCRMPipeline()
    
    @pytest.fixture
    def test_data_dir(self):
        """Fixture para obter o diretório de dados de teste."""
        return Path(__file__).parent.parent / "test_data"
    
    def test_load_csv_comma_separator(self, pipeline, test_data_dir):
        """Teste: Carregamento de CSV com separador vírgula (,)"""
        file_path = test_data_dir / "test_comma_separator.csv"
        
        # Executar o método
        df = pipeline._load_data(str(file_path))
        
        # Verificações
        assert isinstance(df, pd.DataFrame), "Resultado deve ser um DataFrame"
        assert len(df.columns) > 1, "DataFrame deve ter mais de 1 coluna"
        assert len(df) == 3, "DataFrame deve ter 3 registros"
        assert 'nome' in df.columns, "Deve conter coluna 'nome'"
        assert 'email' in df.columns, "Deve conter coluna 'email'"
        assert 'qualidade_lead' in df.columns, "Deve conter coluna 'qualidade_lead'"
        
        # Verificar dados específicos
        assert df.iloc[0]['nome'] == 'João Silva', "Primeiro registro deve ser 'João Silva'"
        assert df.iloc[1]['email'] == 'maria@email.com', "Email do segundo registro deve estar correto"
    
    def test_load_csv_semicolon_separator(self, pipeline, test_data_dir):
        """Teste: Carregamento de CSV com separador ponto e vírgula (;)"""
        file_path = test_data_dir / "test_semicolon_separator.csv"
        
        # Executar o método
        df = pipeline._load_data(str(file_path))
        
        # Verificações
        assert isinstance(df, pd.DataFrame), "Resultado deve ser um DataFrame"
        assert len(df.columns) > 1, "DataFrame deve ter mais de 1 coluna"
        assert len(df) == 3, "DataFrame deve ter 3 registros"
        assert 'nome' in df.columns, "Deve conter coluna 'nome'"
        assert 'empresa' in df.columns, "Deve conter coluna 'empresa'"
        
        # Verificar detecção automática do separador
        assert df.iloc[0]['nome'] == 'Ana Costa', "Primeiro registro deve ser 'Ana Costa'"
        assert df.iloc[2]['empresa'] == 'Design Studio', "Empresa do terceiro registro deve estar correta"
    
    def test_load_csv_iso_encoding_with_accents(self, pipeline, test_data_dir):
        """Teste: Carregamento de CSV com encoding ISO-8859-1 e caracteres acentuados"""
        file_path = test_data_dir / "test_iso_encoding.csv"
        
        # Executar o método (deve funcionar mesmo com encoding diferente)
        df = pipeline._load_data(str(file_path))
        
        # Verificações
        assert isinstance(df, pd.DataFrame), "Resultado deve ser um DataFrame"
        assert len(df.columns) > 1, "DataFrame deve ter mais de 1 coluna"
        assert len(df) == 4, "DataFrame deve ter 4 registros"
        
        # Verificar se caracteres acentuados foram preservados (pode variar dependendo do encoding)
        nomes = df['nome'].tolist()
        assert any('José' in nome or 'Jose' in nome for nome in nomes), "Deve conter nome com José"
        assert any('María' in nome or 'Maria' in nome for nome in nomes), "Deve conter nome com María"
    
    def test_load_xlsx_file(self, pipeline, test_data_dir):
        """Teste: Carregamento de arquivo XLSX"""
        file_path = test_data_dir / "test_file.xlsx"
        
        # Executar o método
        df = pipeline._load_data(str(file_path))
        
        # Verificações
        assert isinstance(df, pd.DataFrame), "Resultado deve ser um DataFrame"
        assert len(df.columns) > 1, "DataFrame deve ter mais de 1 coluna"
        assert len(df) == 4, "DataFrame deve ter 4 registros"
        assert 'nome' in df.columns, "Deve conter coluna 'nome'"
        assert 'email' in df.columns, "Deve conter coluna 'email'"
        
        # Verificar dados específicos
        assert df.iloc[0]['nome'] == 'Roberto Silva', "Primeiro registro deve ser 'Roberto Silva'"
        assert df.iloc[1]['empresa'] == 'Spreadsheet Ltd', "Empresa do segundo registro deve estar correta"
    
    def test_automatic_separator_detection(self, pipeline):
        """Teste: Detecção automática de separadores CSV"""
        # Criar arquivo temporário com separador pipe (|)
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as temp_file:
            temp_file.write("nome|email|telefone\n")
            temp_file.write("Teste|teste@email.com|11999999999\n")
            temp_file.write("Usuario|usuario@test.com|21888888888\n")
            temp_file_path = temp_file.name
        
        try:
            # Executar o método
            df = pipeline._load_data(temp_file_path)
            
            # Verificações
            assert isinstance(df, pd.DataFrame), "Resultado deve ser um DataFrame"
            assert len(df.columns) == 3, "DataFrame deve ter exatamente 3 colunas"
            assert len(df) == 2, "DataFrame deve ter 2 registros"
            assert 'nome' in df.columns, "Deve conter coluna 'nome'"
            assert 'email' in df.columns, "Deve conter coluna 'email'"
            assert 'telefone' in df.columns, "Deve conter coluna 'telefone'"
            
        finally:
            # Limpar arquivo temporário
            os.unlink(temp_file_path)
    
    def test_column_count_validation(self, pipeline, test_data_dir):
        """Teste: Validação de número de colunas > 1"""
        file_path = test_data_dir / "test_single_column.csv"
        
        # Deve continuar tentando outros separadores, mas eventualmente falhar
        # porque nenhum separador resulta em mais de 1 coluna
        with pytest.raises(ValueError, match="Não foi possível ler o arquivo CSV"):
            pipeline._load_data(str(file_path))
    
    def test_invalid_csv_format(self, pipeline, test_data_dir):
        """Teste: Tratamento de arquivo CSV com formato inválido"""
        file_path = test_data_dir / "test_invalid_format.csv"
        
        # Deve falhar pois não consegue encontrar um separador válido
        with pytest.raises(ValueError, match="Não foi possível ler o arquivo CSV"):
            pipeline._load_data(str(file_path))
    
    def test_unsupported_file_format(self, pipeline):
        """Teste: Tratamento de formato de arquivo não suportado"""
        # Criar arquivo temporário com extensão não suportada
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as temp_file:
            temp_file.write("dados de teste")
            temp_file_path = temp_file.name
        
        try:
            with pytest.raises(ValueError, match="Formato de arquivo não suportado"):
                pipeline._load_data(temp_file_path)
        finally:
            os.unlink(temp_file_path)
    
    def test_nonexistent_file(self, pipeline):
        """Teste: Tratamento de arquivo inexistente"""
        nonexistent_file = "arquivo_que_nao_existe.csv"
        
        with pytest.raises((FileNotFoundError, ValueError)):
            pipeline._load_data(nonexistent_file)
    
    def test_csv_with_tab_separator(self, pipeline):
        """Teste: CSV com separador tab (\\t)"""
        # Criar arquivo temporário com separador tab
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as temp_file:
            temp_file.write("nome\temail\ttelefone\tqualidade\n")
            temp_file.write("Ana Silva\tana@test.com\t11999999999\talta\n")
            temp_file.write("Bruno Costa\tbruno@test.com\t21888888888\tbaixa\n")
            temp_file_path = temp_file.name
        
        try:
            # Executar o método
            df = pipeline._load_data(temp_file_path)
            
            # Verificações
            assert isinstance(df, pd.DataFrame), "Resultado deve ser um DataFrame"
            assert len(df.columns) == 4, "DataFrame deve ter 4 colunas"
            assert len(df) == 2, "DataFrame deve ter 2 registros"
            assert df.iloc[0]['nome'] == 'Ana Silva', "Primeiro nome deve ser 'Ana Silva'"
            assert df.iloc[1]['email'] == 'bruno@test.com', "Email deve estar correto"
            
        finally:
            os.unlink(temp_file_path)
    
    def test_empty_csv_file(self, pipeline):
        """Teste: Arquivo CSV vazio"""
        # Criar arquivo temporário vazio
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as temp_file:
            temp_file.write("")  # Arquivo vazio
            temp_file_path = temp_file.name
        
        try:
            with pytest.raises(ValueError, match="Não foi possível ler o arquivo CSV"):
                pipeline._load_data(temp_file_path)
        finally:
            os.unlink(temp_file_path)
    
    def test_csv_with_only_header(self, pipeline):
        """Teste: CSV apenas com cabeçalho (sem dados)"""
        # Criar arquivo temporário apenas com cabeçalho
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as temp_file:
            temp_file.write("nome,email,telefone\n")  # Apenas header
            temp_file_path = temp_file.name
        
        try:
            # Executar o método
            df = pipeline._load_data(temp_file_path)
            
            # Verificações
            assert isinstance(df, pd.DataFrame), "Resultado deve ser um DataFrame"
            assert len(df.columns) == 3, "DataFrame deve ter 3 colunas"
            assert len(df) == 0, "DataFrame deve ter 0 registros (apenas header)"
            
        finally:
            os.unlink(temp_file_path)


if __name__ == "__main__":
    # Permitir execução direta do arquivo para debugging
    import sys
    pytest.main([__file__] + sys.argv[1:])
