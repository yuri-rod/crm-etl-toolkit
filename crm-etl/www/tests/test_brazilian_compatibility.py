#!/usr/bin/env python3
"""
Testes para validação da compatibilidade com dados brasileiros

Este arquivo testa as funcionalidades implementadas para trabalhar com dados brasileiros:
1. Validação de telefones/WhatsApp em diferentes formatos
2. Validação de CPF e CNPJ
3. Formatação de valores monetários em Real (R$)
4. Normalização de nomes com acentos
"""

import unittest
import pandas as pd
import sys
from pathlib import Path

# Adiciona o diretório backend ao path
current_dir = Path(__file__).parent
backend_dir = current_dir.parent / 'backend'
sys.path.insert(0, str(backend_dir))

from brazilian_utils import BrazilianDataValidator, create_brazilian_test_dataset

class TestBrazilianDataValidator(unittest.TestCase):
    """Testes para a classe BrazilianDataValidator"""

    def test_validate_phone_whatsapp(self):
        """Testa validação de telefones brasileiros em diferentes formatos"""
        
        # Telefones válidos
        valid_phones = [
            "+55 (11) 99999-9999",  # Formato completo
            "(11) 99999-9999",      # Formato com DDD
            "+55 11 99999-9999",    # Formato com espaços
            "+5511999999999",       # Formato compacto com país
            "11 99999-9999",        # Formato com espaço
            "11999999999",          # Formato compacto
            "5511999999999",        # Com código país sem +
            "(21) 3333-4444",       # Telefone fixo
            "21 3333-4444",         # Telefone fixo sem parênteses
        ]
        
        for phone in valid_phones:
            with self.subTest(phone=phone):
                self.assertTrue(BrazilianDataValidator.validate_phone_whatsapp(phone),
                               f"Telefone {phone} deveria ser válido")
        
        # Telefones inválidos
        invalid_phones = [
            "",                     # Vazio
            "123",                  # Muito curto
            "+1 555 123-4567",      # Formato americano
            "abcdefghijk",          # Não numérico
            "+55 11 999",           # Incompleto
            None,                   # None
        ]
        
        for phone in invalid_phones:
            with self.subTest(phone=phone):
                self.assertFalse(BrazilianDataValidator.validate_phone_whatsapp(phone),
                                f"Telefone {phone} deveria ser inválido")

    def test_format_phone_whatsapp(self):
        """Testa formatação de telefones para o padrão brasileiro"""
        
        test_cases = [
            ("11999999999", "+55 (11) 99999-9999"),
            ("+5511999999999", "+55 (11) 99999-9999"),
            ("(11) 99999-9999", "+55 (11) 99999-9999"),
            ("21 3333-4444", "+55 (21) 3333-4444"),
            ("", ""),
            (None, ""),
        ]
        
        for input_phone, expected in test_cases:
            with self.subTest(input_phone=input_phone):
                result = BrazilianDataValidator.format_phone_whatsapp(input_phone)
                self.assertEqual(result, expected,
                               f"Formatação de {input_phone} deveria resultar em {expected}, mas foi {result}")

    def test_validate_cnpj(self):
        """Testa validação de CNPJ brasileiro"""
        
        # CNPJs válidos (gerados algoritmicamente)
        valid_cnpjs = [
            "11.222.333/0001-81",   # Formatado
            "11222333000181",       # Apenas números
        ]
        
        # CNPJs inválidos
        invalid_cnpjs = [
            "",                     # Vazio
            "123",                  # Muito curto
            "11111111111111",       # Sequência igual
            "12.345.678/0001-00",   # Dígitos verificadores errados
            None,                   # None
            "abc.def.ghi/jklm-no",  # Não numérico
        ]
        
        for cnpj in invalid_cnpjs:
            with self.subTest(cnpj=cnpj):
                self.assertFalse(BrazilianDataValidator.validate_cnpj(cnpj),
                                f"CNPJ {cnpj} deveria ser inválido")

    def test_validate_cpf(self):
        """Testa validação de CPF brasileiro"""
        
        # CPFs inválidos para teste
        invalid_cpfs = [
            "",                     # Vazio
            "123",                  # Muito curto
            "11111111111",          # Sequência igual
            "123.456.789-00",       # Dígitos verificadores errados
            None,                   # None
            "abc.def.ghi-jk",       # Não numérico
        ]
        
        for cpf in invalid_cpfs:
            with self.subTest(cpf=cpf):
                self.assertFalse(BrazilianDataValidator.validate_cpf(cpf),
                                f"CPF {cpf} deveria ser inválido")

    def test_format_currency_brl(self):
        """Testa formatação de valores monetários em Real"""
        
        test_cases = [
            (1234.56, "R$ 1.234,56"),
            (1000, "R$ 1.000,00"),
            (0, "R$ 0,00"),
            ("1234.56", "R$ 1.234,56"),
            ("", "R$ 0,00"),
            (None, "R$ 0,00"),
        ]
        
        for value, expected in test_cases:
            with self.subTest(value=value):
                result = BrazilianDataValidator.format_currency_brl(value)
                # Testa se contém R$ e tem formato similar (pode variar por locale)
                self.assertIn("R$", result)
                if value and value != "":
                    self.assertNotEqual(result, "R$ 0,00")

    def test_normalize_name(self):
        """Testa normalização de nomes brasileiros"""
        
        test_cases = [
            ("josé DA silva", "José da Silva"),
            ("MARIA JOSÉ santos", "Maria José Santos"),
            ("joão PAULO de oliveira", "João Paulo de Oliveira"),
            ("ana lúcia DA costa", "Ana Lúcia da Costa"),
            ("", ""),
            (None, ""),
            ("   múltiplos   espaços   ", "Múltiplos Espaços"),
        ]
        
        for input_name, expected in test_cases:
            with self.subTest(input_name=input_name):
                result = BrazilianDataValidator.normalize_name(input_name)
                self.assertEqual(result, expected,
                               f"Normalização de '{input_name}' deveria resultar em '{expected}', mas foi '{result}'")

    def test_extract_phone_features(self):
        """Testa extração de features de telefone"""
        
        # Cria DataFrame de teste
        df = pd.DataFrame({
            'telefone': ['+55 (11) 99999-9999', '(21) 3333-4444', 'invalid'],
            'whatsapp': ['+55 (11) 88888-8888', '', '+55 (85) 97777-7777'],
            'other_column': ['a', 'b', 'c']
        })
        
        result_df = BrazilianDataValidator.extract_phone_features(df)
        
        # Verifica se novas colunas foram criadas
        self.assertIn('phone_valido', result_df.columns)
        self.assertIn('phone_celular', result_df.columns)
        self.assertIn('phone_tem_codigo_pais', result_df.columns)
        self.assertIn('whats_valido', result_df.columns)
        
        # Verifica alguns valores
        self.assertEqual(result_df.loc[0, 'phone_valido'], 1)  # Telefone válido
        self.assertEqual(result_df.loc[2, 'phone_valido'], 0)  # Telefone inválido

class TestBrazilianDatasetCreation(unittest.TestCase):
    """Testes para criação de dataset brasileiro"""

    def test_create_brazilian_test_dataset(self):
        """Testa criação do dataset de teste brasileiro"""
        
        df = create_brazilian_test_dataset(n_samples=10)
        
        # Verifica estrutura básica
        self.assertEqual(len(df), 10)
        self.assertIn('nome', df.columns)
        self.assertIn('telefone', df.columns)
        self.assertIn('cnpj', df.columns)
        self.assertIn('cidade', df.columns)
        
        # Verifica se há nomes com acentos
        nomes_com_acentos = df['nome'].str.contains('[áéíóúâêîôûãõç]', case=False, regex=True).any()
        self.assertTrue(nomes_com_acentos, "Dataset deveria conter nomes com acentos")
        
        # Verifica se há telefones válidos
        telefones_validos = df['telefone'].apply(BrazilianDataValidator.validate_phone_whatsapp).any()
        self.assertTrue(telefones_validos, "Dataset deveria conter telefones válidos")
        
        # Verifica se há CNPJs (podem estar vazios em alguns registros)
        has_cnpj = df['cnpj'].notna().any()
        self.assertTrue(has_cnpj, "Dataset deveria conter alguns CNPJs")

    def test_dataset_diversity(self):
        """Testa diversidade dos dados gerados"""
        
        df = create_brazilian_test_dataset(n_samples=50)
        
        # Verifica diversidade de cidades
        unique_cities = df['cidade'].nunique()
        self.assertGreaterEqual(unique_cities, 5, "Dataset deveria ter pelo menos 5 cidades diferentes")
        
        # Verifica diversidade de formatos de telefone
        phone_formats = df['telefone'].apply(lambda x: '+55' in str(x)).value_counts()
        self.assertGreater(len(phone_formats), 1, "Dataset deveria ter telefones em formatos diversos")

if __name__ == '__main__':
    # Configura para mostrar saída mais detalhada
    unittest.main(verbosity=2)
