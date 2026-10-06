#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Criar arquivo CSV com encoding ISO-8859-1 e caracteres acentuados
import os

# Dados com acentos para testar encoding
dados_iso = """nome;email;telefone;empresa;qualidade_lead
José da Silva;jose@email.com;11999999999;Tecnología Ltda;alta
María González;maria@empresa.com;21888888888;Inovação & Cia;baixa
André Müller;andre@tech.com;31777777777;Soluções Ágeis;alta
Renée François;renee@global.com;41666666666;Stratégie Corp;baixa
"""

# Escrever arquivo com encoding ISO-8859-1
with open('test_data/test_iso_encoding.csv', 'w', encoding='iso-8859-1') as f:
    f.write(dados_iso)

print("Arquivo ISO-8859-1 criado com sucesso!")

# Verificar se o arquivo foi criado corretamente
with open('test_data/test_iso_encoding.csv', 'r', encoding='iso-8859-1') as f:
    print("Conteúdo do arquivo:")
    print(f.read())
