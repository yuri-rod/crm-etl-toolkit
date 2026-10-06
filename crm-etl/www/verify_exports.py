#!/usr/bin/env python3
"""
Script para verificar a integridade dos arquivos exportados CSV e XLSX
"""

import pandas as pd

def main():
    print('=== VERIFICACAO DOS ARQUIVOS DE SAIDA ===')
    
    # Carrega o arquivo original para comparar
    df_original = pd.read_excel('./test_data/test_file.xlsx')
    print(f'Arquivo original: {df_original.shape[0]} linhas, {df_original.shape[1]} colunas')
    
    # Verifica CSV
    print('\n--- Arquivo CSV ---')
    df_csv = pd.read_csv('./results_predictions.csv')
    print(f'Shape: {df_csv.shape}')
    print(f'Colunas: {list(df_csv.columns)}')
    print(f'Coluna qualidade_predita presente: {"qualidade_predita" in df_csv.columns}')
    print(f'Numero de linhas igual ao input: {df_csv.shape[0] == df_original.shape[0]}')
    print(f'Tipos de dados:')
    for col, dtype in df_csv.dtypes.items():
        print(f'  {col}: {dtype}')
    
    # Verifica XLSX
    print('\n--- Arquivo XLSX ---')
    df_xlsx = pd.read_excel('./results_predictions.xlsx')
    print(f'Shape: {df_xlsx.shape}')
    print(f'Colunas: {list(df_xlsx.columns)}')
    print(f'Coluna qualidade_predita presente: {"qualidade_predita" in df_xlsx.columns}')
    print(f'Numero de linhas igual ao input: {df_xlsx.shape[0] == df_original.shape[0]}')
    print(f'Tipos de dados:')
    for col, dtype in df_xlsx.dtypes.items():
        print(f'  {col}: {dtype}')
    
    # Verifica conteúdo das predições
    print('\n--- Conteudo das Predicoes ---')
    print('CSV - qualidade_predita:')
    print(df_csv['qualidade_predita'].value_counts())
    print('\nXLSX - qualidade_predita:')
    print(df_xlsx['qualidade_predita'].value_counts())
    
    # Verifica se os dados são idênticos
    print(f'\nArquivos CSV e XLSX sao identicos: {df_csv.equals(df_xlsx)}')
    
    # Verificações específicas dos tipos
    print('\n--- Verificacao de Tipos Corretos ---')
    # Verificar se temos floats, ints e strings como esperado
    numeric_cols = ['nome_length', 'empresa_cargo_length', 'has_linkedin', 'has_email', 
                   'has_whatsapp', 'data_quality_score', 'confianca_predicao']
    
    string_cols = ['nome', 'email', 'telefone', 'empresa', 'qualidade_predita']
    
    for col in numeric_cols:
        if col in df_csv.columns:
            print(f'  {col}: {df_csv[col].dtype} (numeric: {pd.api.types.is_numeric_dtype(df_csv[col])})')
    
    for col in string_cols:
        if col in df_csv.columns:
            print(f'  {col}: {df_csv[col].dtype} (string: {pd.api.types.is_string_dtype(df_csv[col]) or df_csv[col].dtype == "object"})')
    
    # Mostra alguns exemplos de dados
    print('\n--- Exemplos de Dados (CSV) ---')
    print(df_csv.head())

if __name__ == "__main__":
    main()
