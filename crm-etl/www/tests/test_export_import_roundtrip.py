#!/usr/bin/env python3
"""
Testes pytest para verificar a integridade de exportação e importação (round-trip)
dos dados processados pela pipeline unificada.

Este módulo testa:
1. Exportação para CSV e XLSX
2. Importação dos arquivos exportados
3. Verificação de integridade dos dados (colunas, tipos, valores)
"""

import pytest
import pandas as pd
import tempfile
import os
from pathlib import Path
import sys

# Adiciona o diretório backend ao path para importar o módulo
sys.path.append(str(Path(__file__).parent.parent / 'backend'))
from unificado import UnifiedCRMPipeline


class TestExportImportRoundTrip:
    """Testes para verificar a integridade dos dados em operações de round-trip."""
    
    @pytest.fixture
    def pipeline(self):
        """Fixture que cria uma instância da pipeline para testes."""
        return UnifiedCRMPipeline(enable_api_calls=False)
    
    @pytest.fixture
    def sample_data(self):
        """Fixture que cria dados de exemplo para testes."""
        return pd.DataFrame({
            'nome': ['João Silva', 'Maria Santos', 'Pedro Costa'],
            'email': ['joao@email.com', 'maria@empresa.com', 'pedro@tech.com'],
            'telefone': ['11999999999', '21888888888', '31777777777'],
            'empresa': ['Tech Corp', 'Data Ltd', 'AI Solutions'],
            'qualidade_lead': ['alta', 'baixa', 'alta']
        })
    
    def test_csv_round_trip(self, pipeline, sample_data):
        """
        Testa o round-trip completo para arquivos CSV:
        DataFrame → ETL → Predict → CSV → Import → Verificação
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            # 1. Salva dados originais
            input_file = tmpdir / 'input.xlsx'
            sample_data.to_excel(input_file, index=False)
            
            # 2. Treina modelo com dados de exemplo
            df_processed = pipeline.run_etl(str(input_file))
            pipeline.train_model(df_processed, target_column='qualidade_lead')
            
            # 3. Executa predição
            df_predictions = pipeline.batch_predict(df_processed)
            
            # 4. Exporta para CSV
            output_csv = tmpdir / 'output.csv'
            df_predictions.to_csv(output_csv, index=False)
            
            # 5. Importa novamente
            df_reimported = pd.read_csv(output_csv)
            
            # 6. Verificações de integridade
            assert len(df_reimported) == len(sample_data), "Número de linhas deve ser preservado"
            assert 'qualidade_predita' in df_reimported.columns, "Coluna qualidade_predita deve estar presente"
            assert 'confianca_predicao' in df_reimported.columns, "Coluna confianca_predicao deve estar presente"
            
            # Verifica se os tipos estão corretos
            assert pd.api.types.is_numeric_dtype(df_reimported['confianca_predicao']), "confianca_predicao deve ser numérica"
            assert pd.api.types.is_string_dtype(df_reimported['qualidade_predita']) or df_reimported['qualidade_predita'].dtype == 'object', "qualidade_predita deve ser string/object"
            
            # Verifica valores das predições
            pred_values = df_reimported['qualidade_predita'].unique()
            assert all(val in ['Alta', 'Baixa'] for val in pred_values), "Predições devem ser 'Alta' ou 'Baixa'"
            
            # Verifica range de confiança
            assert df_reimported['confianca_predicao'].min() >= 0.0, "Confiança mínima deve ser >= 0"
            assert df_reimported['confianca_predicao'].max() <= 1.0, "Confiança máxima deve ser <= 1"
    
    def test_xlsx_round_trip(self, pipeline, sample_data):
        """
        Testa o round-trip completo para arquivos XLSX:
        DataFrame → ETL → Predict → XLSX → Import → Verificação
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            # 1. Salva dados originais
            input_file = tmpdir / 'input.xlsx'
            sample_data.to_excel(input_file, index=False)
            
            # 2. Treina modelo com dados de exemplo
            df_processed = pipeline.run_etl(str(input_file))
            pipeline.train_model(df_processed, target_column='qualidade_lead')
            
            # 3. Executa predição
            df_predictions = pipeline.batch_predict(df_processed)
            
            # 4. Exporta para XLSX
            output_xlsx = tmpdir / 'output.xlsx'
            df_predictions.to_excel(output_xlsx, index=False)
            
            # 5. Importa novamente
            df_reimported = pd.read_excel(output_xlsx)
            
            # 6. Verificações de integridade (mesmas do CSV)
            assert len(df_reimported) == len(sample_data), "Número de linhas deve ser preservado"
            assert 'qualidade_predita' in df_reimported.columns, "Coluna qualidade_predita deve estar presente"
            assert 'confianca_predicao' in df_reimported.columns, "Coluna confianca_predicao deve estar presente"
            
            # Verifica se os tipos estão corretos
            assert pd.api.types.is_numeric_dtype(df_reimported['confianca_predicao']), "confianca_predicao deve ser numérica"
            assert pd.api.types.is_string_dtype(df_reimported['qualidade_predita']) or df_reimported['qualidade_predita'].dtype == 'object', "qualidade_predita deve ser string/object"
    
    def test_csv_xlsx_equivalence(self, pipeline, sample_data):
        """
        Testa se a exportação em CSV e XLSX produz resultados equivalentes
        após reimportação.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            # 1. Prepara dados e treina modelo
            input_file = tmpdir / 'input.xlsx'
            sample_data.to_excel(input_file, index=False)
            
            df_processed = pipeline.run_etl(str(input_file))
            pipeline.train_model(df_processed, target_column='qualidade_lead')
            df_predictions = pipeline.batch_predict(df_processed)
            
            # 2. Exporta para ambos os formatos
            output_csv = tmpdir / 'output.csv'
            output_xlsx = tmpdir / 'output.xlsx'
            
            df_predictions.to_csv(output_csv, index=False)
            df_predictions.to_excel(output_xlsx, index=False)
            
            # 3. Importa ambos
            df_csv = pd.read_csv(output_csv)
            df_xlsx = pd.read_excel(output_xlsx)
            
            # 4. Verifica equivalência
            assert df_csv.shape == df_xlsx.shape, "Shape deve ser idêntico entre CSV e XLSX"
            assert list(df_csv.columns) == list(df_xlsx.columns), "Colunas devem ser idênticas"
            
            # Verifica se valores numéricos são equivalentes (com tolerância para float)
            for col in df_csv.columns:
                if pd.api.types.is_numeric_dtype(df_csv[col]):
                    pd.testing.assert_series_equal(df_csv[col], df_xlsx[col], check_names=False, rtol=1e-10)
                else:
                    pd.testing.assert_series_equal(df_csv[col], df_xlsx[col], check_names=False)
    
    def test_data_type_preservation(self, pipeline, sample_data):
        """
        Testa se os tipos de dados são preservados após round-trip.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            input_file = tmpdir / 'input.xlsx'
            sample_data.to_excel(input_file, index=False)
            
            # Processa dados
            df_processed = pipeline.run_etl(str(input_file))
            pipeline.train_model(df_processed, target_column='qualidade_lead')
            df_predictions = pipeline.batch_predict(df_processed)
            
            # Exporta e importa
            output_file = tmpdir / 'output.csv'
            df_predictions.to_csv(output_file, index=False)
            df_reimported = pd.read_csv(output_file)
            
            # Verifica tipos específicos
            expected_numeric_cols = [
                'nome_length', 'empresa_cargo_length', 'has_linkedin', 
                'has_email', 'has_whatsapp', 'data_quality_score', 
                'confianca_predicao'
            ]
            
            expected_string_cols = [
                'nome', 'email', 'empresa', 'qualidade_predita'
            ]
            
            for col in expected_numeric_cols:
                if col in df_reimported.columns:
                    assert pd.api.types.is_numeric_dtype(df_reimported[col]), f"Coluna {col} deve ser numérica"
            
            for col in expected_string_cols:
                if col in df_reimported.columns:
                    assert (pd.api.types.is_string_dtype(df_reimported[col]) or 
                           df_reimported[col].dtype == 'object'), f"Coluna {col} deve ser string/object"
    
    def test_empty_dataframe_handling(self, pipeline):
        """
        Testa o comportamento com DataFrames vazios.
        """
        empty_df = pd.DataFrame(columns=['nome', 'email', 'telefone', 'empresa', 'qualidade_lead'])
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            input_file = tmpdir / 'empty_input.xlsx'
            empty_df.to_excel(input_file, index=False)
            
            # Deve lidar com dados vazios sem falhar
            try:
                df_processed = pipeline.run_etl(str(input_file))
                assert len(df_processed) == 0, "DataFrame vazio deve permanecer vazio após ETL"
            except Exception as e:
                pytest.fail(f"Pipeline não deve falhar com DataFrame vazio: {str(e)}")
    
    @pytest.mark.parametrize("file_format", ['.csv', '.xlsx'])
    def test_special_characters_handling(self, pipeline, file_format):
        """
        Testa se caracteres especiais são preservados durante round-trip.
        """
        special_data = pd.DataFrame({
            'nome': ['José da Silva', 'María González', 'François Müller'],
            'email': ['jose@açaí.com', 'maria@niño.es', 'francois@café.fr'],
            'telefone': ['11999999999', '21888888888', '31777777777'],
            'empresa': ['Açaí & Cia', 'Niño Solutions', 'Café François'],
            'qualidade_lead': ['alta', 'baixa', 'alta']
        })
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            input_file = tmpdir / f'input{file_format}'
            if file_format == '.csv':
                special_data.to_csv(input_file, index=False, encoding='utf-8')
            else:
                special_data.to_excel(input_file, index=False)
            
            # Processa dados
            df_processed = pipeline.run_etl(str(input_file))
            
            # Verifica se caracteres especiais foram preservados
            assert 'José da Silva' in df_processed['nome'].values, "Caracteres especiais devem ser preservados"
            assert 'açaí' in df_processed['email'].iloc[0].lower(), "Caracteres especiais em emails devem ser preservados"


if __name__ == "__main__":
    # Executa os testes se o arquivo for executado diretamente
    pytest.main([__file__, "-v"])
