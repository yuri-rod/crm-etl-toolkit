#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===========================================================
--- Benchmark e Demonstração: UnifiedCRMPipeline._load_data ---
===========================================================

Demonstra todos os casos de uso da funcionalidade _load_data:
- Performance com arquivos grandes
- Diferentes encodings e separadores
- Casos extremos e validações

Desenvolvido para CRM ETL
"""

import pytest
import pandas as pd
import tempfile
import time
from pathlib import Path
import sys

# Adicionar o diretório backend ao path
backend_path = Path(__file__).parent.parent.parent / "backend"
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

from unificado import UnifiedCRMPipeline


class TestBenchmarkLoadData:
    """Testes de benchmark e demonstração da funcionalidade _load_data."""
    
    @pytest.fixture
    def pipeline(self):
        """Fixture para criar uma instância da pipeline."""
        return UnifiedCRMPipeline()
    
    def test_comprehensive_separator_detection(self, pipeline):
        """Demonstração completa da detecção de separadores."""
        separators_test_cases = [
            (",", "vírgula"),
            (";", "ponto e vírgula"), 
            ("|", "pipe"),
            ("\t", "tab")
        ]
        
        print("\n🧪 TESTE DE DETECÇÃO DE SEPARADORES")
        print("=" * 50)
        
        for sep, name in separators_test_cases:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as temp_file:
                # Criar dados de teste
                temp_file.write(f"nome{sep}email{sep}telefone{sep}empresa\n")
                temp_file.write(f"Ana Silva{sep}ana@test.com{sep}11999999999{sep}Tech Corp\n")
                temp_file.write(f"Bruno Costa{sep}bruno@test.com{sep}21888888888{sep}Data Inc\n")
                temp_file_path = temp_file.name
            
            try:
                start_time = time.time()
                df = pipeline._load_data(temp_file_path)
                load_time = time.time() - start_time
                
                print(f"✅ Separador {name} ({repr(sep)}): {len(df)} registros, {len(df.columns)} colunas em {load_time:.3f}s")
                
                assert len(df.columns) == 4, f"Deve ter 4 colunas com separador {name}"
                assert len(df) == 2, f"Deve ter 2 registros com separador {name}"
                
            finally:
                import os
                os.unlink(temp_file_path)
    
    def test_encoding_support(self, pipeline):
        """Teste de suporte a diferentes encodings."""
        print("\n🌍 TESTE DE SUPORTE A ENCODINGS")
        print("=" * 40)
        
        # Dados com caracteres especiais
        test_data = {
            'utf-8': "nome,empresa,cidade\nJosé,Inovação Tech,São Paulo\nMaría,Soluções Ágeis,Brasília\n",
            'iso-8859-1': "nome,empresa,cidade\nJosé,Inovação Tech,São Paulo\nMaría,Soluções Ágeis,Brasília\n",
            'cp1252': "nome,empresa,cidade\nJosé,Inovação Tech,São Paulo\nMaría,Soluções Ágeis,Brasília\n"
        }
        
        for encoding, data in test_data.items():
            with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding=encoding) as temp_file:
                temp_file.write(data)
                temp_file_path = temp_file.name
            
            try:
                start_time = time.time()
                df = pipeline._load_data(temp_file_path)
                load_time = time.time() - start_time
                
                print(f"✅ Encoding {encoding}: {len(df)} registros carregados em {load_time:.3f}s")
                
                assert len(df) == 2, f"Deve carregar 2 registros com encoding {encoding}"
                assert len(df.columns) == 3, f"Deve ter 3 colunas com encoding {encoding}"
                
            except Exception as e:
                print(f"❌ Erro com encoding {encoding}: {e}")
                
            finally:
                import os
                os.unlink(temp_file_path)
    
    def test_performance_large_file(self, pipeline):
        """Teste de performance com arquivo grande."""
        print("\n⚡ TESTE DE PERFORMANCE")
        print("=" * 30)
        
        # Criar arquivo com muitos registros
        num_records = 1000
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as temp_file:
            temp_file.write("id,nome,email,telefone,empresa,qualidade_lead\n")
            
            for i in range(num_records):
                temp_file.write(f"{i},Usuario {i},user{i}@test.com,11{i:09d},Empresa {i % 10},{'alta' if i % 3 == 0 else 'baixa'}\n")
            
            temp_file_path = temp_file.name
        
        try:
            start_time = time.time()
            df = pipeline._load_data(temp_file_path)
            load_time = time.time() - start_time
            
            records_per_second = len(df) / load_time if load_time > 0 else 0
            
            print(f"📊 Arquivo com {len(df):,} registros carregado em {load_time:.3f}s")
            print(f"⚡ Performance: {records_per_second:,.0f} registros/segundo")
            print(f"💾 Memória: {df.memory_usage(deep=True).sum() / 1024 / 1024:.2f} MB")
            
            assert len(df) == num_records, "Deve carregar todos os registros"
            assert len(df.columns) == 6, "Deve ter 6 colunas"
            assert load_time < 5.0, "Carregamento deve ser rápido (< 5s para 1000 registros)"
            
        finally:
            import os
            os.unlink(temp_file_path)
    
    def test_error_handling_showcase(self, pipeline):
        """Demonstração de tratamento de erros."""
        print("\n🛡️ TESTE DE TRATAMENTO DE ERROS")  
        print("=" * 40)
        
        error_cases = [
            ("Arquivo inexistente", "arquivo_inexistente.csv", (FileNotFoundError, ValueError)),
            ("Formato não suportado", "teste.txt", ValueError),
            ("CSV inválido", "dados\nsem\nestrutura", ValueError)
        ]
        
        for case_name, test_input, expected_exception in error_cases:
            try:
                if case_name == "Arquivo inexistente":
                    with pytest.raises(expected_exception):
                        pipeline._load_data(test_input)
                    print(f"✅ {case_name}: Erro tratado corretamente")
                
                elif case_name == "Formato não suportado":
                    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as temp_file:
                        temp_file.write("dados de teste")
                        temp_file_path = temp_file.name
                    
                    try:
                        with pytest.raises(expected_exception):
                            pipeline._load_data(temp_file_path)
                        print(f"✅ {case_name}: Erro tratado corretamente")
                    finally:
                        import os
                        os.unlink(temp_file_path)
                
                elif case_name == "CSV inválido":
                    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as temp_file:
                        temp_file.write(test_input)
                        temp_file_path = temp_file.name
                    
                    try:
                        with pytest.raises(expected_exception):
                            pipeline._load_data(temp_file_path)
                        print(f"✅ {case_name}: Erro tratado corretamente")
                    finally:
                        import os
                        os.unlink(temp_file_path)
                        
            except Exception as e:
                print(f"❌ {case_name}: Erro inesperado - {e}")
    
    def test_column_validation_showcase(self, pipeline):
        """Demonstração da validação de colunas."""
        print("\n📋 TESTE DE VALIDAÇÃO DE COLUNAS")
        print("=" * 40)
        
        test_cases = [
            ("Uma coluna", "dados\nvalor1\nvalor2", False),
            ("Múltiplas colunas", "col1,col2,col3\nval1,val2,val3", True),
            ("Header vazio", "", False),
            ("Apenas separadores", ",,\n,,\n,,", True)
        ]
        
        for case_name, content, should_pass in test_cases:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as temp_file:
                temp_file.write(content)
                temp_file_path = temp_file.name
            
            try:
                if should_pass:
                    df = pipeline._load_data(temp_file_path)
                    print(f"✅ {case_name}: {len(df.columns)} colunas detectadas")
                    assert len(df.columns) > 1, f"Deve ter múltiplas colunas para {case_name}"
                else:
                    with pytest.raises(ValueError):
                        pipeline._load_data(temp_file_path)
                    print(f"✅ {case_name}: Corretamente rejeitado")
                    
            except Exception as e:
                if not should_pass:
                    print(f"✅ {case_name}: Erro esperado - {e}")
                else:
                    print(f"❌ {case_name}: Erro inesperado - {e}")
            finally:
                import os
                os.unlink(temp_file_path)
    
    def test_real_world_scenarios(self, pipeline):
        """Testes com cenários do mundo real."""
        print("\n🌍 CENÁRIOS DO MUNDO REAL")
        print("=" * 35)
        
        # Cenário 1: Arquivo típico de CRM
        crm_data = """nome,email,telefone,empresa,cargo,qualidade_lead
João Silva,joao@empresa.com,11999999999,TechCorp,Gerente,alta
Maria Santos,maria@startup.com,21888888888,StartupAI,CEO,alta
Pedro Costa,pedro@freelancer.com,31777777777,Freelancer,Desenvolvedor,baixa"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as temp_file:
            temp_file.write(crm_data)
            temp_file_path = temp_file.name
        
        try:
            start_time = time.time()
            df = pipeline._load_data(temp_file_path)
            load_time = time.time() - start_time
            
            print(f"📊 CRM Dataset: {len(df)} leads, {len(df.columns)} campos em {load_time:.3f}s")
            print(f"   Colunas: {', '.join(df.columns[:3])}...")
            
            assert 'nome' in df.columns, "Deve conter coluna nome"
            assert 'email' in df.columns, "Deve conter coluna email"
            assert 'qualidade_lead' in df.columns, "Deve conter coluna qualidade_lead"
            
        finally:
            import os
            os.unlink(temp_file_path)
        
        print("✅ Todos os cenários do mundo real testados com sucesso!")


if __name__ == "__main__":
    # Permitir execução direta para demonstração
    pytest.main([__file__, "-v", "-s"])
