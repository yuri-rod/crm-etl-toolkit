#!/usr/bin/env python3
"""
Script para criar dataset de teste com dados brasileiros

Este script gera um dataset de teste contendo:
- Nomes brasileiros com acentos
- Cidades brasileiras
- CNPJs válidos
- Telefones regionais em vários formatos
- Valores monetários em Real (R$)
"""

import argparse
from pathlib import Path
import sys
import os

# Adiciona o diretório backend ao path para importar módulos
current_dir = Path(__file__).parent
backend_dir = current_dir / 'backend'
sys.path.insert(0, str(backend_dir))

from brazilian_utils import create_brazilian_test_dataset, BrazilianDataValidator

def main():
    parser = argparse.ArgumentParser(description='Gera dataset de teste com dados brasileiros')
    parser.add_argument('--output', '-o', type=str, required=True,
                        help='Caminho para o arquivo de saída (CSV ou XLSX)')
    parser.add_argument('--samples', '-s', type=int, default=100,
                        help='Número de amostras a gerar (padrão: 100)')
    parser.add_argument('--format-phones', action='store_true',
                        help='Formatar todos os telefones para o padrão brasileiro')
    parser.add_argument('--format-currency', action='store_true',
                        help='Formatar valores monetários em Real (R$)')
    
    args = parser.parse_args()
    
    print(f"Gerando dataset brasileiro com {args.samples} amostras...")
    
    # Gera o dataset
    df = create_brazilian_test_dataset(n_samples=args.samples)
    
    # Formata telefones se solicitado
    if args.format_phones:
        print("Formatando telefones para o padrão brasileiro...")
        if 'telefone' in df.columns:
            df['telefone'] = df['telefone'].apply(BrazilianDataValidator.format_phone_whatsapp)
        if 'whatsapp' in df.columns:
            df['whatsapp'] = df['whatsapp'].apply(
                lambda x: BrazilianDataValidator.format_phone_whatsapp(x) if x else ""
            )
    
    # Formata valores monetários se solicitado
    if args.format_currency:
        print("Formatando valores monetários em Real (R$)...")
        if 'receita_anual' in df.columns:
            df['receita_anual_formatado'] = df['receita_anual'].apply(
                BrazilianDataValidator.format_currency_brl
            )
    
    # Salva o arquivo
    output_path = Path(args.output)
    
    if output_path.suffix.lower() == '.csv':
        df.to_csv(output_path, index=False, encoding='utf-8')
        print(f"Dataset salvo como CSV: {output_path}")
    elif output_path.suffix.lower() in ['.xlsx', '.xls']:
        df.to_excel(output_path, index=False)
        print(f"Dataset salvo como Excel: {output_path}")
    else:
        # Default para CSV
        output_path = output_path.with_suffix('.csv')
        df.to_csv(output_path, index=False, encoding='utf-8')
        print(f"Dataset salvo como CSV: {output_path}")
    
    print("\n=== Resumo do Dataset Gerado ===")
    print(f"Total de registros: {len(df)}")
    print(f"Colunas: {', '.join(df.columns)}")
    print(f"\nPrimeiras 5 linhas:")
    print(df.head())
    
    print("\n=== Validação dos Dados Brasileiros ===")
    
    # Validação de telefones
    if 'telefone' in df.columns:
        telefones_validos = df['telefone'].apply(BrazilianDataValidator.validate_phone_whatsapp).sum()
        print(f"Telefones válidos: {telefones_validos}/{len(df)} ({telefones_validos/len(df)*100:.1f}%)")
    
    # Validação de CNPJs
    if 'cnpj' in df.columns:
        cnpjs_validos = df['cnpj'].apply(
            lambda x: BrazilianDataValidator.validate_cnpj(x) if x else False
        ).sum()
        total_cnpjs = df['cnpj'].apply(lambda x: bool(x and str(x).strip())).sum()
        if total_cnpjs > 0:
            print(f"CNPJs válidos: {cnpjs_validos}/{total_cnpjs} ({cnpjs_validos/total_cnpjs*100:.1f}%)")
    
    # Mostrar formatos de telefone
    print("\n=== Exemplos de Formatos de Telefone ===")
    telefone_samples = df['telefone'].dropna().head(10)
    for i, tel in enumerate(telefone_samples, 1):
        is_valid = "✓" if BrazilianDataValidator.validate_phone_whatsapp(tel) else "✗"
        print(f"{i:2d}. {tel:<20} {is_valid}")

if __name__ == "__main__":
    main()
