#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd

# Dados para o arquivo Excel
dados_xlsx = {
    'nome': ['Roberto Silva', 'Fernanda Costa', 'Miguel Santos', 'Carla Oliveira'],
    'email': ['roberto@email.com', 'fernanda@empresa.com', 'miguel@tech.com', 'carla@corp.com'],
    'telefone': ['11555555555', '21444444444', '31333333333', '41222222222'],
    'empresa': ['Excel Corp', 'Spreadsheet Ltd', 'Data Analytics', 'Business Solutions'],
    'qualidade_lead': ['alta', 'baixa', 'alta', 'baixa']
}

# Criar DataFrame
df = pd.DataFrame(dados_xlsx)

# Salvar como Excel
df.to_excel('test_data/test_file.xlsx', index=False, engine='openpyxl')

print("Arquivo XLSX criado com sucesso!")
print(f"Arquivo contém {len(df)} registros e {len(df.columns)} colunas")
print("Colunas:", list(df.columns))
