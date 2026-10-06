#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MÓDULO DE VALIDAÇÃO DE DOCUMENTOS BRASILEIROS
=============================================

Funções para validação de CPF, CNPJ e outros documentos brasileiros.
Integrado ao sistema de qualificação de leads.

Autor: Sistema de Qualificação de Leads
Data: 2025-07-24
Versão: 1.0.0
"""

import re


def validar_cpf(cpf):
    """
    Valida CPF brasileiro.
    
    Args:
        cpf (str): CPF a ser validado
        
    Returns:
        bool: True se válido, False caso contrário
    """
    if not cpf or cpf == 'nan' or cpf == '':
        return False
    
    # Remove caracteres não numéricos
    cpf = re.sub(r'[^0-9]', '', str(cpf))
    
    # Verifica se tem 11 dígitos
    if len(cpf) != 11:
        return False
    
    # Verifica se todos os dígitos são iguais
    if len(set(cpf)) == 1:
        return False
    
    # Calcula primeiro dígito verificador
    soma = 0
    for i in range(9):
        soma += int(cpf[i]) * (10 - i)
    resto = 11 - (soma % 11)
    if resto >= 10:
        resto = 0
    if resto != int(cpf[9]):
        return False
    
    # Calcula segundo dígito verificador
    soma = 0
    for i in range(10):
        soma += int(cpf[i]) * (11 - i)
    resto = 11 - (soma % 11)
    if resto >= 10:
        resto = 0
    if resto != int(cpf[10]):
        return False
    
    return True


def formatar_cpf(cpf):
    """
    Formata CPF para o padrão XXX.XXX.XXX-XX.
    
    Args:
        cpf (str): CPF a ser formatado
        
    Returns:
        str: CPF formatado ou string vazia se inválido
    """
    if not cpf:
        return ''
    
    # Remove caracteres não numéricos
    cpf = re.sub(r'[^0-9]', '', str(cpf))
    
    if len(cpf) != 11:
        return ''
    
    return f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}"


def validar_cnpj(cnpj):
    """
    Valida CNPJ brasileiro.
    
    Args:
        cnpj (str): CNPJ a ser validado
        
    Returns:
        bool: True se válido, False caso contrário
    """
    if not cnpj or cnpj == 'nan' or cnpj == '':
        return False
    
    # Remove caracteres não numéricos
    cnpj = re.sub(r'[^0-9]', '', str(cnpj))
    
    # Verifica se tem 14 dígitos
    if len(cnpj) != 14:
        return False
    
    # Verifica se todos os dígitos são iguais
    if len(set(cnpj)) == 1:
        return False
    
    # Valida dígitos verificadores
    tamanho = len(cnpj) - 2
    numeros = cnpj[:tamanho]
    digitos = cnpj[tamanho:]
    soma = 0
    pos = tamanho - 7
    
    for i in range(tamanho, 0, -1):
        soma += int(numeros[tamanho - i]) * pos
        pos -= 1
        if pos < 2:
            pos = 9
    
    resultado = 0 if soma % 11 < 2 else 11 - soma % 11
    if resultado != int(digitos[0]):
        return False
    
    tamanho += 1
    numeros = cnpj[:tamanho]
    soma = 0
    pos = tamanho - 7
    
    for i in range(tamanho, 0, -1):
        soma += int(numeros[tamanho - i]) * pos
        pos -= 1
        if pos < 2:
            pos = 9
    
    resultado = 0 if soma % 11 < 2 else 11 - soma % 11
    if resultado != int(digitos[1]):
        return False
    
    return True


def formatar_cnpj(cnpj):
    """
    Formata CNPJ para o padrão XX.XXX.XXX/XXXX-XX.
    
    Args:
        cnpj (str): CNPJ a ser formatado
        
    Returns:
        str: CNPJ formatado ou string vazia se inválido
    """
    if not cnpj:
        return ''
    
    # Remove caracteres não numéricos
    cnpj = re.sub(r'[^0-9]', '', str(cnpj))
    
    if len(cnpj) != 14:
        return ''
    
    return f"{cnpj[:2]}.{cnpj[2:5]}.{cnpj[5:8]}/{cnpj[8:12]}-{cnpj[12:]}"


def validar_telefone_brasileiro(telefone):
    """
    Valida telefone brasileiro (fixo ou celular).
    
    Args:
        telefone (str): Telefone a ser validado
        
    Returns:
        bool: True se válido, False caso contrário
    """
    if not telefone or telefone == 'nan' or telefone == '':
        return False
    
    # Remove caracteres não numéricos
    telefone = re.sub(r'[^0-9]', '', str(telefone))
    
    # Verifica se tem 10 ou 11 dígitos (com DDD)
    if len(telefone) not in [10, 11]:
        return False
    
    # Verifica se o DDD é válido (11-99)
    ddd = int(telefone[:2])
    if ddd < 11 or ddd > 99:
        return False
    
    # Para celular (11 dígitos), o primeiro dígito após DDD deve ser 9
    if len(telefone) == 11 and telefone[2] != '9':
        return False
    
    return True


def formatar_telefone(telefone):
    """
    Formata telefone brasileiro.
    
    Args:
        telefone (str): Telefone a ser formatado
        
    Returns:
        str: Telefone formatado ou string vazia se inválido
    """
    if not telefone:
        return ''
    
    # Remove caracteres não numéricos
    telefone = re.sub(r'[^0-9]', '', str(telefone))
    
    if len(telefone) == 10:  # Fixo
        return f"({telefone[:2]}) {telefone[2:6]}-{telefone[6:]}"
    elif len(telefone) == 11:  # Celular
        return f"({telefone[:2]}) {telefone[2:7]}-{telefone[7:]}"
    else:
        return ''


def validar_cep(cep):
    """
    Valida CEP brasileiro.
    
    Args:
        cep (str): CEP a ser validado
        
    Returns:
        bool: True se válido, False caso contrário
    """
    if not cep or cep == 'nan' or cep == '':
        return False
    
    # Remove caracteres não numéricos
    cep = re.sub(r'[^0-9]', '', str(cep))
    
    # Verifica se tem 8 dígitos
    return len(cep) == 8


def formatar_cep(cep):
    """
    Formata CEP para o padrão XXXXX-XXX.
    
    Args:
        cep (str): CEP a ser formatado
        
    Returns:
        str: CEP formatado ou string vazia se inválido
    """
    if not cep:
        return ''
    
    # Remove caracteres não numéricos
    cep = re.sub(r'[^0-9]', '', str(cep))
    
    if len(cep) != 8:
        return ''
    
    return f"{cep[:5]}-{cep[5:]}"


def extrair_estado_de_cidade_estado(cidade_estado):
    """
    Extrai a sigla do estado de um campo cidade/estado.
    
    Args:
        cidade_estado (str): String no formato "Cidade/Estado" ou "Cidade - Estado"
        
    Returns:
        str: Sigla do estado ou string vazia se não encontrado
    """
    if not cidade_estado or cidade_estado == 'nan' or cidade_estado == '':
        return ''
    
    # Lista de estados brasileiros
    estados = [
        'AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA',
        'MT', 'MS', 'MG', 'PA', 'PB', 'PR', 'PE', 'PI', 'RJ', 'RN',
        'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO'
    ]
    
    # Busca por padrão de estado no final da string
    cidade_estado = str(cidade_estado).strip()
    
    # Tenta encontrar estado após separadores comuns
    for separador in ['/', '-', ',']:
        partes = cidade_estado.split(separador)
        if len(partes) >= 2:
            possivel_estado = partes[-1].strip().upper()
            if possivel_estado in estados:
                return possivel_estado
    
    # Busca direta pela sigla no final
    ultimo_token = cidade_estado.split()[-1].upper()
    if ultimo_token in estados:
        return ultimo_token
    
    return ''


def validar_email(email):
    """
    Valida formato de email.
    
    Args:
        email (str): Email a ser validado
        
    Returns:
        bool: True se válido, False caso contrário
    """
    if not email or email == 'nan' or email == '':
        return False
    
    # Padrão básico de email
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, str(email).lower()))


def validar_documento_por_tipo(documento, tipo='auto'):
    """
    Valida documento brasileiro baseado no tipo ou detecta automaticamente.
    
    Args:
        documento (str): Documento a ser validado
        tipo (str): 'cpf', 'cnpj', 'auto' (detecta automaticamente)
        
    Returns:
        tuple: (bool válido, str tipo_detectado)
    """
    if not documento:
        return False, None
    
    # Remove caracteres não numéricos
    documento_limpo = re.sub(r'[^0-9]', '', str(documento))
    
    if tipo == 'auto':
        if len(documento_limpo) == 11:
            return validar_cpf(documento), 'cpf'
        elif len(documento_limpo) == 14:
            return validar_cnpj(documento), 'cnpj'
        else:
            return False, None
    elif tipo == 'cpf':
        return validar_cpf(documento), 'cpf'
    elif tipo == 'cnpj':
        return validar_cnpj(documento), 'cnpj'
    else:
        return False, None


# Exemplo de uso
if __name__ == "__main__":
    print("=== TESTE DE VALIDAÇÕES ===\n")
    
    # Teste CPF
    cpfs_teste = ['111.444.777-35', '123.456.789-09', '111.111.111-11', '12345678901']
    print("CPFs:")
    for cpf in cpfs_teste:
        valido = validar_cpf(cpf)
        formatado = formatar_cpf(cpf) if valido else "Inválido"
        print(f"  {cpf} -> Válido: {valido}, Formatado: {formatado}")
    
    # Teste CNPJ
    print("\nCNPJs:")
    cnpjs_teste = ['11.222.333/0001-81', '11.111.111/1111-11', '12345678000100']
    for cnpj in cnpjs_teste:
        valido = validar_cnpj(cnpj)
        formatado = formatar_cnpj(cnpj) if valido else "Inválido"
        print(f"  {cnpj} -> Válido: {valido}, Formatado: {formatado}")
    
    # Teste Telefone
    print("\nTelefones:")
    telefones_teste = ['11987654321', '1133334444', '987654321', '+5511987654321']
    for tel in telefones_teste:
        valido = validar_telefone_brasileiro(tel)
        formatado = formatar_telefone(tel) if valido else "Inválido"
        print(f"  {tel} -> Válido: {valido}, Formatado: {formatado}")
