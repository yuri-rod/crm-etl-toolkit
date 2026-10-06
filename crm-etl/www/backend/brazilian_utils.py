"""
Utilitários para Compatibilidade com Dados Brasileiros

Este módulo contém funções e validações específicas para dados brasileiros,
incluindo validação de telefones, formatação de moeda, e processamento de nomes acentuados.
"""

import re
import locale
from typing import Union, Optional
import pandas as pd


class BrazilianDataValidator:
    """Classe para validação e formatação de dados brasileiros."""
    
    @staticmethod
    def validate_phone_whatsapp(phone: str) -> bool:
        """
        Valida telefones brasileiros em diferentes formatos:
        - +55 (11) 99999-9999
        - (11) 99999-9999
        - 11 99999-9999
        - +5511999999999
        - 5511999999999
        - 11999999999
        """
        if not phone or pd.isna(phone):
            return False
            
        # Remove espaços e caracteres não numéricos para análise
        phone_clean = re.sub(r'[^\d+]', '', str(phone))
        
        # Padrões aceitos para telefones brasileiros
        patterns = [
            r'^\+55\s*\(\d{2}\)\s*\d{4,5}-?\d{4}$',  # +55 (11) 99999-9999
            r'^\+55\s*\d{2}\s*\d{4,5}-?\d{4}$',       # +55 11 99999-9999
            r'^\+55\d{10,11}$',                       # +5511999999999
            r'^\(\d{2}\)\s*\d{4,5}-?\d{4}$',          # (11) 99999-9999
            r'^\d{2}\s*\d{4,5}-?\d{4}$',              # 11 99999-9999
            r'^55\d{10,11}$',                         # 5511999999999
            r'^\d{10,11}$',                           # 11999999999
        ]
        
        phone_str = str(phone).strip()
        return any(re.match(pattern, phone_str) for pattern in patterns)
    
    @staticmethod
    def format_phone_whatsapp(phone: str) -> str:
        """
        Formata telefone brasileiro para o padrão: +55 (XX) 9XXXX-XXXX
        """
        if not phone or pd.isna(phone):
            return ""
            
        # Remove todos os caracteres não numéricos
        digits_only = re.sub(r'\D', '', str(phone))
        
        # Analisa os dígitos para extrair componentes
        if len(digits_only) == 13 and digits_only.startswith('55'):
            # 5511999999999 -> +55 (11) 99999-9999
            country = digits_only[:2]
            area = digits_only[2:4]
            number = digits_only[4:]
        elif len(digits_only) == 11:
            # 11999999999 -> +55 (11) 99999-9999
            country = '55'
            area = digits_only[:2]
            number = digits_only[2:]
        elif len(digits_only) == 10:
            # 1199999999 -> +55 (11) 9999-9999
            country = '55'
            area = digits_only[:2]
            number = digits_only[2:]
        else:
            return phone  # Retorna original se não conseguir processar
        
        # Formata o número
        if len(number) == 9:
            # Celular: 9XXXX-XXXX
            formatted_number = f"{number[:5]}-{number[5:]}"
        elif len(number) == 8:
            # Fixo: XXXX-XXXX
            formatted_number = f"{number[:4]}-{number[4:]}"
        else:
            return phone  # Retorna original se não conseguir processar
            
        return f"+{country} ({area}) {formatted_number}"
    
    @staticmethod
    def validate_cnpj(cnpj: str) -> bool:
        """
        Valida CNPJ brasileiro usando o algoritmo oficial.
        """
        if not cnpj or pd.isna(cnpj):
            return False
            
        # Remove caracteres não numéricos
        cnpj_clean = re.sub(r'\D', '', str(cnpj))
        
        # Verifica se tem 14 dígitos
        if len(cnpj_clean) != 14:
            return False
            
        # Verifica se não é uma sequência de números iguais
        if len(set(cnpj_clean)) == 1:
            return False
        
        # Algoritmo de validação do CNPJ
        def calculate_digit(cnpj_partial: str, weights: list) -> str:
            total = sum(int(digit) * weight for digit, weight in zip(cnpj_partial, weights))
            remainder = total % 11
            return '0' if remainder < 2 else str(11 - remainder)
        
        # Pesos para cálculo dos dígitos verificadores
        weights_first = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        weights_second = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        
        # Calcula primeiro dígito verificador
        first_digit = calculate_digit(cnpj_clean[:12], weights_first)
        
        # Calcula segundo dígito verificador
        second_digit = calculate_digit(cnpj_clean[:12] + first_digit, weights_second)
        
        # Verifica se os dígitos calculados conferem
        return cnpj_clean[-2:] == first_digit + second_digit
    
    @staticmethod
    def validate_cpf(cpf: str) -> bool:
        """
        Valida CPF brasileiro usando o algoritmo oficial.
        """
        if not cpf or pd.isna(cpf):
            return False
            
        # Remove caracteres não numéricos
        cpf_clean = re.sub(r'\D', '', str(cpf))
        
        # Verifica se tem 11 dígitos
        if len(cpf_clean) != 11:
            return False
            
        # Verifica se não é uma sequência de números iguais
        if len(set(cpf_clean)) == 1:
            return False
        
        # Algoritmo de validação do CPF
        def calculate_digit(cpf_partial: str) -> str:
            total = sum(int(digit) * weight for digit, weight in zip(cpf_partial, range(len(cpf_partial) + 1, 1, -1)))
            remainder = total % 11
            return '0' if remainder < 2 else str(11 - remainder)
        
        # Calcula primeiro dígito verificador
        first_digit = calculate_digit(cpf_clean[:9])
        
        # Calcula segundo dígito verificador  
        second_digit = calculate_digit(cpf_clean[:9] + first_digit)
        
        # Verifica se os dígitos calculados conferem
        return cpf_clean[-2:] == first_digit + second_digit
    
    @staticmethod
    def format_currency_brl(value: Union[float, int, str], include_symbol: bool = True) -> str:
        """
        Formata valores monetários em Real brasileiro (R$).
        
        Args:
            value: Valor a ser formatado
            include_symbol: Se deve incluir o símbolo R$
            
        Returns:
            String formatada (ex: "R$ 1.234,56")
        """
        if pd.isna(value) or value == "":
            return "R$ 0,00" if include_symbol else "0,00"
        
        try:
            # Converte para float se necessário
            if isinstance(value, str):
                # Remove caracteres não numéricos exceto vírgula e ponto
                clean_value = re.sub(r'[^\d,.-]', '', value)
                # Substitui vírgula por ponto para conversão
                clean_value = clean_value.replace(',', '.')
                numeric_value = float(clean_value)
            else:
                numeric_value = float(value)
            
            # Formata usando locale brasileiro ou manualmente
            try:
                # Tenta usar locale brasileiro
                locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
                formatted = locale.currency(numeric_value, grouping=True, symbol=False)
            except (locale.Error, AttributeError):
                # Formatação manual se locale não estiver disponível
                formatted = f"{numeric_value:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
            
            return f"R$ {formatted}" if include_symbol else formatted
            
        except (ValueError, TypeError):
            return "R$ 0,00" if include_symbol else "0,00"
    
    @staticmethod
    def normalize_name(name: str) -> str:
        """
        Normaliza nomes brasileiros mantendo acentos e formatação adequada.
        """
        if not name or pd.isna(name):
            return ""
            
        name_str = str(name).strip()
        
        # Remove espaços extras
        normalized = re.sub(r'\s+', ' ', name_str)
        
        # Primeira letra de cada palavra em maiúscula, exceto preposições
        prepositions = {'de', 'da', 'do', 'das', 'dos', 'e', 'em', 'na', 'no', 'para', 'por'}
        words = normalized.lower().split()
        
        result = []
        for i, word in enumerate(words):
            if i == 0 or word not in prepositions:
                result.append(word.capitalize())
            else:
                result.append(word)
        
        return ' '.join(result)
    
    @staticmethod
    def extract_phone_features(df: pd.DataFrame, phone_columns: list = None) -> pd.DataFrame:
        """
        Extrai features relacionadas a telefones brasileiros.
        
        Args:
            df: DataFrame com dados
            phone_columns: Lista de colunas que contêm telefones
            
        Returns:
            DataFrame com novas features de telefone
        """
        if phone_columns is None:
            phone_columns = [col for col in df.columns if any(
                keyword in col.lower() for keyword in ['telefone', 'whatsapp', 'phone', 'fone']
            )]
        
        df_result = df.copy()
        
        for col in phone_columns:
            if col in df.columns:
                col_name = col.replace('telefone', 'phone').replace('whatsapp', 'whats')
                
                # Feature: telefone válido
                df_result[f'{col_name}_valido'] = df[col].apply(
                    BrazilianDataValidator.validate_phone_whatsapp
                ).astype(int)
                
                # Feature: é celular (tem 9 dígitos no número)
                df_result[f'{col_name}_celular'] = df[col].apply(
                    lambda x: 1 if x and len(re.sub(r'\D', '', str(x))) >= 10 and 
                    re.sub(r'\D', '', str(x))[-9:-8] == '9' else 0
                )
                
                # Feature: tem código do país
                df_result[f'{col_name}_tem_codigo_pais'] = df[col].apply(
                    lambda x: 1 if x and ('+55' in str(x) or str(x).startswith('55')) else 0
                )
        
        return df_result


def create_brazilian_test_dataset(n_samples: int = 100) -> pd.DataFrame:
    """
    Cria um dataset de teste com dados brasileiros típicos.
    
    Args:
        n_samples: Número de amostras a gerar
        
    Returns:
        DataFrame com dados de teste brasileiros
    """
    import random
    import uuid
    from datetime import datetime, timedelta
    
    # Nomes brasileiros com acentos
    nomes = [
        "José da Silva", "Maria José Santos", "João Paulo Oliveira", "Ana Lúcia Costa",
        "Carlos Eduardo Ferreira", "Lúcia Helena Rodrigues", "Antônio Carlos Almeida",
        "Márcia Regina Pereira", "Paulo César Lima", "Fátima Aparecida Moura",
        "Luís Fernando Cardoso", "Cláudia Cristina Barbosa", "Sérgio Luís Gomes",
        "Valéria Cristine Souza", "André Luís Martins", "Mônica Regina Dias",
        "Fábio Alexandre Costa", "Patrícia Fernanda Lima", "Rodrigo José Nunes",
        "Simone Aparecida Rocha", "Márcio Antônio Silva", "Luciane Cristina Pinto"
    ]
    
    # Cidades brasileiras
    cidades = [
        "São Paulo", "Rio de Janeiro", "Brasília", "Salvador", "Fortaleza",
        "Belo Horizonte", "Manaus", "Curitiba", "Recife", "Goiânia",
        "Belém", "Porto Alegre", "Guarulhos", "Campinas", "São Luís",
        "São Gonçalo", "Maceió", "Duque de Caxias", "Nova Iguaçu", "Teresina"
    ]
    
    # Estados
    estados = [
        "SP", "RJ", "DF", "BA", "CE", "MG", "AM", "PR", "PE", "GO",
        "PA", "RS", "SC", "MA", "PB", "AL", "RN", "MT", "MS", "PI"
    ]
    
    # Códigos de área por região
    ddd_mapping = {
        "São Paulo": ["11", "12", "13", "14", "15", "16", "17", "18", "19"],
        "Rio de Janeiro": ["21", "22", "24"],
        "Brasília": ["61"],
        "Salvador": ["71", "73", "74", "75", "77"],
        "Fortaleza": ["85", "88"],
        "Belo Horizonte": ["31", "32", "33", "34", "35", "37", "38"],
        "Manaus": ["92", "97"],
        "Curitiba": ["41", "42", "43", "44", "45", "46"],
        "Recife": ["81", "87"],
        "Goiânia": ["62", "64"]
    }
    
    def generate_cnpj():
        """Gera CNPJ válido"""
        def calculate_digit(cnpj_partial: str, weights: list) -> str:
            total = sum(int(digit) * weight for digit, weight in zip(cnpj_partial, weights))
            remainder = total % 11
            return '0' if remainder < 2 else str(11 - remainder)
        
        # Gera os primeiros 12 dígitos
        cnpj_base = ''.join([str(random.randint(0, 9)) for _ in range(12)])
        
        # Calcula dígitos verificadores
        weights_first = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        weights_second = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        
        first_digit = calculate_digit(cnpj_base, weights_first)
        second_digit = calculate_digit(cnpj_base + first_digit, weights_second)
        
        cnpj_complete = cnpj_base + first_digit + second_digit
        return f"{cnpj_complete[:2]}.{cnpj_complete[2:5]}.{cnpj_complete[5:8]}/{cnpj_complete[8:12]}-{cnpj_complete[12:]}"
    
    def generate_phone(cidade):
        """Gera telefone brasileiro válido"""
        # Seleciona DDD baseado na cidade
        if cidade in ddd_mapping:
            ddd = random.choice(ddd_mapping[cidade])
        else:
            ddd = random.choice(["11", "21", "31", "41", "51", "61", "71", "81", "85", "62"])
        
        # Gera número de celular (9 dígitos iniciando com 9)
        if random.random() < 0.8:  # 80% celular
            numero = "9" + ''.join([str(random.randint(0, 9)) for _ in range(8)])
        else:  # 20% fixo
            numero = ''.join([str(random.randint(1, 9))] + [str(random.randint(0, 9)) for _ in range(7)])
        
        # Varia formato
        formato = random.choice([
            f"+55 ({ddd}) {numero[:5]}-{numero[5:]}",
            f"({ddd}) {numero[:5]}-{numero[5:]}",
            f"+55{ddd}{numero}",
            f"{ddd} {numero[:5]}-{numero[5:]}",
            f"{ddd}{numero}"
        ])
        
        return formato
    
    # Gera dataset
    data = []
    for i in range(n_samples):
        cidade = random.choice(cidades)
        nome = random.choice(nomes)
        
        record = {
            'id': i + 1,
            'nome': nome,
            'email': f"{nome.lower().replace(' ', '.').replace('ã', 'a').replace('ç', 'c').replace('é', 'e').replace('í', 'i').replace('ó', 'o').replace('ú', 'u').replace('â', 'a')}@empresa{random.randint(1,100)}.com.br",
            'telefone': generate_phone(cidade),
            'whatsapp': generate_phone(cidade) if random.random() < 0.7 else "",
            'cidade': cidade,
            'estado': random.choice(estados),
            'cnpj': generate_cnpj() if random.random() < 0.6 else "",
            'empresa': f"Empresa {random.choice(['Tech', 'Solutions', 'Sistemas', 'Consultoria', 'Serviços'])} {random.choice(['Ltda', 'S.A.', 'ME', 'EIRELI'])}",
            'cargo': random.choice(["Diretor", "Gerente", "Coordenador", "Analista", "Assistente", "Supervisor"]),
            'receita_anual': random.randint(50000, 5000000),
            'data_contato': (datetime.now() - timedelta(days=random.randint(1, 365))).strftime('%Y-%m-%d'),
            'qualidade_lead': random.choice(['Alta', 'Baixa', 'Alta', 'Baixa', 'Alta'])  # 60% Alta
        }
        data.append(record)
    
    return pd.DataFrame(data)
