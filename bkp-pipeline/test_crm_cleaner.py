#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Testes básicos para o CRM Cleaner

Este arquivo contém testes de validação e funcionalidade
para garantir que o CRMCleaner está funcionando corretamente.

Autor: CRM Team
Versão: 2.0
Data: Dezembro 2024
"""

import unittest
import pandas as pd
from datetime import datetime
from crm_crm_cleaner import CRMCleaner, BrazilianValidators, LGPDCompliance, ColumnMapper

class TestCRMCleaner(unittest.TestCase):
    """Testes para o CRM Cleaner"""
    
    def setUp(self):
        """Configuração inicial dos testes"""
        self.cleaner = CRMCleaner(enable_lgpd=True, anonymize_sensitive=True)
        self.validators = BrazilianValidators()
        self.lgpd = LGPDCompliance()
        self.mapper = ColumnMapper()
    
    def test_cpf_validation(self):
        """Testa validação de CPF"""
        # CPFs válidos
        valid_cpfs = [
            "11144477735",
            "111.444.777-35",
            "52998224725",
        ]
        
        for cpf in valid_cpfs:
            self.assertTrue(
                self.validators.validate_cpf(cpf),
                f"CPF {cpf} deveria ser válido"
            )
        
        # CPFs inválidos
        invalid_cpfs = [
            "11111111111",  # Todos iguais
            "123456789",    # Muito curto
            "12345678901",  # Dígito verificador errado
            "111.444.777-34"  # Dígito verificador errado
        ]
        
        for cpf in invalid_cpfs:
            self.assertFalse(
                self.validators.validate_cpf(cpf),
                f"CPF {cpf} deveria ser inválido"
            )
    
    def test_phone_validation(self):
        """Testa validação de telefone"""
        # Telefones válidos
        valid_phones = [
            "+5511999887766",
            "11999887766",
            "+55 11 99988-7766",
            "(11) 99988-7766"
        ]
        
        for phone in valid_phones:
            is_valid, formatted = self.validators.validate_phone(phone)
            self.assertTrue(is_valid, f"Telefone {phone} deveria ser válido")
            self.assertTrue(formatted.startswith("+55"), f"Telefone formatado deveria começar com +55")
    
    def test_date_parsing(self):
        """Testa parsing de datas"""
        # Formatos de data válidos
        valid_dates = [
            ("25/12/1990", datetime(1990, 12, 25)),
            ("25121990", datetime(1990, 12, 25)),
            ("25-12-1990", datetime(1990, 12, 25)),
            ("1990-12-25", datetime(1990, 12, 25))
        ]
        
        for date_str, expected in valid_dates:
            parsed = self.cleaner.parse_date(date_str)
            self.assertEqual(
                parsed.date() if parsed else None,
                expected.date(),
                f"Data {date_str} não foi parseada corretamente"
            )
    
    def test_email_cleaning(self):
        """Testa limpeza de e-mail"""
        test_cases = [
            ("TESTE@EXEMPLO.COM", "teste@exemplo.com", True),
            ("  usuario@dominio.com.br  ", "usuario@dominio.com.br", True),
            ("email_invalido", "email_invalido", False),
            ("@dominio.com", "@dominio.com", False)
        ]
        
        for input_email, expected_clean, expected_valid in test_cases:
            clean_email, is_valid, _ = self.cleaner.clean_email(input_email)
            self.assertEqual(clean_email, expected_clean, f"Email {input_email} não foi limpo corretamente")
            self.assertEqual(is_valid, expected_valid, f"Validação de {input_email} incorreta")
    
    def test_address_normalization(self):
        """Testa normalização de endereços"""
        test_cases = [
            ("Rua das Flores, 123", "R. DAS FLORES, 123"),
            ("AVENIDA PAULISTA 1000", "AV. PAULISTA 1000"),
            ("Travessa do Socorro 45", "TV. DO SOCORRO 45")
        ]
        
        for input_addr, expected in test_cases:
            normalized = self.validators.normalize_address(input_addr)
            self.assertEqual(normalized, expected, f"Endereço {input_addr} não foi normalizado corretamente")
    
    def test_cep_extraction(self):
        """Testa extração de CEP"""
        test_cases = [
            ("Rua das Flores 123, CEP 12345-678", "12345-678"),
            ("Endereço completo 12345678", "12345-678"),
            ("Sem CEP válido", None)
        ]
        
        for input_text, expected in test_cases:
            extracted = self.validators.extract_cep(input_text)
            self.assertEqual(extracted, expected, f"CEP não extraído corretamente de {input_text}")
    
    def test_lgpd_anonymization(self):
        """Testa anonimização LGPD"""
        # Teste CPF
        cpf = "12345678901"
        anonymized_cpf = self.lgpd.anonymize_cpf(cpf)
        self.assertTrue(anonymized_cpf.endswith("01"), "CPF anonimizado deveria manter últimos dígitos")
        self.assertIn("***", anonymized_cpf, "CPF anonimizado deveria conter máscaras")
        
        # Teste email
        email = "usuario@exemplo.com"
        anonymized_email = self.lgpd.anonymize_email(email)
        self.assertTrue(anonymized_email.endswith("@exemplo.com"), "Email anonimizado deveria manter domínio")
        self.assertIn("*", anonymized_email, "Email anonimizado deveria conter máscaras")
    
    def test_column_mapping(self):
        """Testa mapeamento de colunas"""
        test_columns = [
            "Nome completo",
            "CPF:",
            "Deixe aqui seu email principal",
            "WhatsApp",
            "#"
        ]
        
        mapping = self.mapper.map_columns(test_columns)
        
        # Verifica se as principais colunas foram mapeadas
        expected_mappings = {
            "Nome completo": "nome_completo",
            "CPF:": "cpf",
            "#": "id"
        }
        
        for original, expected in expected_mappings.items():
            self.assertEqual(
                mapping.get(original), 
                expected, 
                f"Coluna {original} não foi mapeada corretamente"
            )
    
    def test_dataframe_processing(self):
        """Testa processamento completo de DataFrame"""
        # Cria DataFrame de teste
        test_data = {
            "#": ["test001", "test002"],
            "Nome completo": ["João Silva", "Maria Santos"],
            "CPF:": ["11144477735", "52998224725"],
            "Deixe aqui seu email principal": ["joao@teste.com", "maria@teste.com"],
            "WhatsApp": ["+5511999887766", "11888776655"]
        }
        
        df = pd.DataFrame(test_data)
        
        # Processa DataFrame
        result_df = self.cleaner.process_dataframe(df, "test_file.csv")
        
        # Verifica se o resultado não está vazio
        self.assertFalse(result_df.empty, "DataFrame processado não deveria estar vazio")
        
        # Verifica se colunas padronizadas foram criadas
        expected_columns = [
            "id", "nome_completo", "cpf", "email", "telefone",
            "cpf_valido", "email_valido", "telefone_valido",
            "record_hash", "arquivo_origem"
        ]
        
        for col in expected_columns:
            self.assertIn(col, result_df.columns, f"Coluna {col} deveria estar presente no resultado")
        
        # Verifica se validações foram aplicadas
        self.assertTrue(
            result_df["cpf_valido"].any(),
            "Pelo menos um CPF deveria ser válido"
        )
        self.assertTrue(
            result_df["email_valido"].any(),
            "Pelo menos um email deveria ser válido"
        )
    
    def test_duplicate_detection(self):
        """Testa detecção de duplicatas"""
        # Cria DataFrame com duplicatas
        test_data = {
            "nome_completo": ["João Silva", "João Silva", "Maria Santos"],
            "cpf": ["11144477735", "11144477735", "52998224725"],
            "email": ["joao@teste.com", "joao@teste.com", "maria@teste.com"]
        }
        
        df = pd.DataFrame(test_data)
        
        # Processa DataFrame
        result_df = self.cleaner.process_dataframe(df, "test_duplicates.csv")
        
        # Verifica se duplicatas foram detectadas
        duplicate_count = result_df["is_duplicate"].sum()
        self.assertGreater(duplicate_count, 0, "Duplicatas deveriam ter sido detectadas")
        
        # Remove duplicatas
        deduplicated_df = self.cleaner.remove_duplicates(result_df)
        
        # Verifica se duplicatas foram removidas
        self.assertLess(
            len(deduplicated_df), 
            len(result_df),
            "DataFrame deduplicated deveria ter menos registros"
        )

def run_basic_tests():
    """Executa testes básicos e imprime resultados"""
    print("=== CRM Cleaner - Testes Básicos ===")
    print("Executando testes de validação...\n")
    
    # Executa testes unitários
    suite = unittest.TestLoader().loadTestsFromTestCase(TestCRMCleaner)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Imprime resumo
    print(f"\n=== RESUMO DOS TESTES ===")
    print(f"Testes executados: {result.testsRun}")
    print(f"Sucessos: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Falhas: {len(result.failures)}")
    print(f"Erros: {len(result.errors)}")
    
    if result.failures:
        print("\nFALHAS:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback}")
    
    if result.errors:
        print("\nERROS:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback}")
    
    return result.wasSuccessful()

def test_sample_data():
    """Testa com dados de exemplo"""
    print("\n=== Teste com Dados de Exemplo ===")
    
    # Cria dados de exemplo baseados nas análises reais
    sample_data = {
        "#": ["r7qz156s776k5vhvkr7qz15h5n8l6gyl", "6et0h17kgvqqx4xj6et0h64bcmbfkim4"],
        "Nome completo": ["TANIA FATIMA RICONI TACCA", "Paulo Teixeira Giordani"],
        "CPF:": ["83819622934", "21847014836"],
        "RG:": ["68508142-PR", "38671522-1"],
        "Estado Civil:": ["Casada", "Casado"],
        "Agora, nos conte como quer seu nome no crachá?": ["Tania Tacca", "Paulo Giordani"],
        "{{field:86f9256513e5d6db}}, qual é o dia do seu aniversário?": ["24/08/1977", "22111980"],
        "Deixe aqui seu email principal": ["triconitacca@hotmail.com", "paulo@brasilsync.com.br"],
        "Endereço residencial completo: ": [
            "Rua Cinderela, 313 - Jardim Social - Cantagalo - PR - CEP 85160000",
            "Rua Bernardo Fontaniello 43"
        ],
        "Cidade e Estado ": ["Cantagalo - PR", "Andradas Minas Gerais"],
        "WhatsApp": ["'+5542991467078", "'+5535999351487"],
        "Qual o nome da sua empresa e cargo que atual?": ["TR RICONI - TRANSPORTES - SOCIA", "Brasilsync - Sócio"],
        "Qual o seguimento de atuação da empresa?": ["Transportes de cargas", "Desenvolvimento de Software para Setor Café"],
        "Deixe aqui o seu LinkedIn:": ["Tania Fatima Riconi Tacca", "linkedin.com/in/paulo-teixeira-giordani-4b5b15260"],
        "CNPJ:": ["39346470000147", "20.167.882/0001-91"],
        "Emissão de nota fiscal.": ["Pessoa Física", "Pessoa Física"]
    }
    
    df = pd.DataFrame(sample_data)
    
    # Inicializa cleaner
    cleaner = CRMCleaner(enable_lgpd=True, anonymize_sensitive=False)
    
    print(f"Dados originais: {len(df)} registros")
    print(f"Colunas originais: {len(df.columns)}")
    
    # Processa dados
    cleaned_df = cleaner.process_dataframe(df, "sample_data.csv")
    
    print(f"\nDados processados: {len(cleaned_df)} registros")
    print(f"Colunas processadas: {len(cleaned_df.columns)}")
    
    # Mostra algumas estatísticas
    stats = cleaner.generate_report()
    print(f"\nEstatísticas:")
    print(f"- CPFs válidos: {stats['estatisticas']['processados'] - stats['estatisticas']['cpfs_invalidos']}")
    print(f"- CPFs inválidos: {stats['estatisticas']['cpfs_invalidos']}")
    print(f"- Emails válidos: {stats['estatisticas']['processados'] - stats['estatisticas']['emails_invalidos']}")
    print(f"- Emails inválidos: {stats['estatisticas']['emails_invalidos']}")
    print(f"- Telefones válidos: {stats['estatisticas']['processados'] - stats['estatisticas']['telefones_invalidos']}")
    print(f"- Telefones inválidos: {stats['estatisticas']['telefones_invalidos']}")
    
    # Mostra algumas amostras dos dados limpos
    print(f"\nAmostras dos dados limpos:")
    if 'nome_completo' in cleaned_df.columns:
        print(f"Nomes: {cleaned_df['nome_completo'].tolist()}")
    if 'cpf' in cleaned_df.columns:
        print(f"CPFs: {cleaned_df['cpf'].tolist()}")
    if 'telefone' in cleaned_df.columns:
        print(f"Telefones: {cleaned_df['telefone'].tolist()}")
    
    return True

if __name__ == "__main__":
    # Executa testes básicos
    tests_passed = run_basic_tests()
    
    # Testa com dados de exemplo
    sample_test_passed = test_sample_data()
    
    # Resultado final
    if tests_passed and sample_test_passed:
        print("\n🎉 TODOS OS TESTES PASSARAM! O CRM Cleaner está funcionando corretamente.")
    else:
        print("\n❌ ALGUNS TESTES FALHARAM. Verifique os logs acima.")

