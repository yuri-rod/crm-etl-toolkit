#!/usr/bin/env python3
"""
Exemplo prático de uso do sistema com dados brasileiros

Este script demonstra o uso completo do pipeline com dados brasileiros,
incluindo validação de telefones, CNPJs e formatação monetária.
"""

import pandas as pd
from pathlib import Path
import sys

# Adiciona o backend ao path
backend_dir = Path(__file__).parent / 'backend'
sys.path.insert(0, str(backend_dir))

from brazilian_utils import create_brazilian_test_dataset, BrazilianDataValidator
from unificado import UnifiedCRMPipeline

def demonstrar_validacoes_brasileiras():
    """Demonstra as validações específicas para dados brasileiros"""
    
    print("=" * 60)
    print("DEMONSTRAÇÃO: Validações Brasileiras")
    print("=" * 60)
    
    # Exemplos de telefones
    print("\n1. Validação de Telefones Brasileiros")
    print("-" * 40)
    
    telefones_teste = [
        "+55 (11) 99999-9999",  # Formato completo
        "(11) 99999-9999",      # Sem código país
        "+5511999999999",       # Compacto
        "11 99999-9999",        # Com espaços
        "+1 555-123-4567",      # Formato americano (inválido)
        "123456",               # Muito curto (inválido)
    ]
    
    for telefone in telefones_teste:
        valido = BrazilianDataValidator.validate_phone_whatsapp(telefone)
        formatado = BrazilianDataValidator.format_phone_whatsapp(telefone)
        status = "✓ Válido" if valido else "✗ Inválido"
        print(f"{telefone:<20} | {status:<10} | Formatado: {formatado}")
    
    # Exemplos de CNPJ
    print("\n2. Validação de CNPJs")
    print("-" * 25)
    
    # Gera um dataset pequeno para obter CNPJs válidos
    df_sample = create_brazilian_test_dataset(n_samples=3)
    cnpjs_teste = df_sample['cnpj'].dropna().tolist()
    cnpjs_teste.extend(["12.345.678/0001-00", "123", ""])  # Adiciona inválidos
    
    for cnpj in cnpjs_teste:
        if cnpj:
            valido = BrazilianDataValidator.validate_cnpj(cnpj)
            status = "✓ Válido" if valido else "✗ Inválido"
            print(f"{cnpj:<20} | {status}")
    
    # Exemplos de formatação monetária
    print("\n3. Formatação Monetária em Real (R$)")
    print("-" * 35)
    
    valores_teste = [1234.56, 1000000, 500.00, "1234,56", 0, None]
    
    for valor in valores_teste:
        formatado = BrazilianDataValidator.format_currency_brl(valor)
        print(f"{str(valor):<15} | {formatado}")
    
    # Exemplos de normalização de nomes
    print("\n4. Normalização de Nomes Brasileiros")
    print("-" * 35)
    
    nomes_teste = [
        "josé DA silva",
        "MARIA josé SANTOS",
        "joão paulo DE oliveira",
        "ANA lúcia da COSTA",
        "   múltiplos    espaços   "
    ]
    
    for nome in nomes_teste:
        normalizado = BrazilianDataValidator.normalize_name(nome)
        print(f"'{nome}' -> '{normalizado}'")

def demonstrar_pipeline_completo():
    """Demonstra o uso do pipeline completo com dados brasileiros"""
    
    print("\n" + "=" * 60)
    print("DEMONSTRAÇÃO: Pipeline Completo com Dados Brasileiros")
    print("=" * 60)
    
    # Gera dataset brasileiro de teste
    print("\n1. Gerando dataset brasileiro de teste...")
    df = create_brazilian_test_dataset(n_samples=20)
    
    print(f"Dataset gerado com {len(df)} registros")
    print(f"Colunas: {', '.join(df.columns)}")
    
    # Salva o dataset temporariamente
    test_file = "temp_brazilian_dataset.csv"
    df.to_csv(test_file, index=False, encoding='utf-8')
    print(f"Dataset salvo temporariamente em: {test_file}")
    
    # Inicializa pipeline
    print("\n2. Inicializando pipeline brasileiro...")
    pipeline = UnifiedCRMPipeline(enable_api_calls=False)  # Desabilita API para demo
    
    # Executa ETL
    print("\n3. Executando ETL com validações brasileiras...")
    df_processed = pipeline.run_etl(test_file)
    
    print(f"Processamento concluído! Dataset processado com {len(df_processed)} registros")
    
    # Mostra estatísticas do processamento
    print("\n4. Estatísticas de Validação:")
    print("-" * 30)
    
    if 'has_whatsapp' in df_processed.columns:
        telefones_validos = df_processed['has_whatsapp'].sum()
        print(f"Telefones válidos: {telefones_validos}/{len(df_processed)}")
    
    if 'cpf_valido' in df_processed.columns:
        cpfs_validos = df_processed['cpf_valido'].sum()
        print(f"CPFs válidos: {cpfs_validos}/{len(df_processed)}")
    
    if 'cnpj_valido_formato' in df_processed.columns:
        cnpjs_validos = df_processed['cnpj_valido_formato'].sum()
        print(f"CNPJs válidos: {cnpjs_validos}/{len(df_processed)}")
    
    if 'data_quality_score' in df_processed.columns:
        score_medio = df_processed['data_quality_score'].mean()
        print(f"Score médio de qualidade: {score_medio:.2f}")
    
    # Mostra algumas amostras processadas
    print("\n5. Amostras de dados processados:")
    print("-" * 35)
    
    # Seleciona colunas interessantes para mostrar
    colunas_mostrar = ['nome', 'telefone', 'has_whatsapp', 'data_quality_score']
    colunas_existentes = [col for col in colunas_mostrar if col in df_processed.columns]
    
    if colunas_existentes:
        print(df_processed[colunas_existentes].head())
    
    # Limpa arquivo temporário
    try:
        Path(test_file).unlink()
        print(f"\nArquivo temporário {test_file} removido.")
    except:
        pass

def demonstrar_features_telefone():
    """Demonstra extração de features avançadas de telefone"""
    
    print("\n" + "=" * 60)
    print("DEMONSTRAÇÃO: Features Avançadas de Telefone")
    print("=" * 60)
    
    # Cria dataset de teste com telefones diversos
    df_teste = pd.DataFrame({
        'nome': ['João Silva', 'Maria Santos', 'Pedro Costa'],
        'telefone': ['+55 (11) 99999-9999', '(21) 3333-4444', 'telefone_inválido'],
        'whatsapp': ['+55 (11) 88888-8888', '', '+55 (85) 97777-7777']
    })
    
    print("Dataset original:")
    print(df_teste)
    
    # Extrai features de telefone
    df_com_features = BrazilianDataValidator.extract_phone_features(df_teste)
    
    print("\nDataset com features de telefone:")
    
    # Mostra apenas as colunas relacionadas a telefone
    phone_columns = [col for col in df_com_features.columns 
                    if any(keyword in col for keyword in ['phone', 'whats', 'telefone'])]
    
    if phone_columns:
        print(df_com_features[phone_columns])
    else:
        print("Nenhuma feature de telefone foi extraída.")

def main():
    """Função principal que executa todas as demonstrações"""
    
    print("SISTEMA DE COMPATIBILIDADE COM DADOS BRASILEIROS")
    print("=" * 60)
    print("Este exemplo demonstra as funcionalidades específicas")
    print("para trabalhar com dados brasileiros no sistema CRM.")
    print("=" * 60)
    
    try:
        # Executa demonstrações
        demonstrar_validacoes_brasileiras()
        demonstrar_pipeline_completo()
        demonstrar_features_telefone()
        
        print("\n" + "=" * 60)
        print("DEMONSTRAÇÃO CONCLUÍDA COM SUCESSO!")
        print("=" * 60)
        print("\nFuncionalidades demonstradas:")
        print("✓ Validação de telefones brasileiros (+55, DDD, etc.)")
        print("✓ Validação de CPF e CNPJ")
        print("✓ Formatação de valores monetários em Real (R$)")
        print("✓ Normalização de nomes com acentos")
        print("✓ Extração de features avançadas de telefone")
        print("✓ Pipeline completo com dados brasileiros")
        
    except Exception as e:
        print(f"\nERRO durante a demonstração: {e}")
        print("Verifique se todos os módulos estão instalados corretamente.")
    
    print("\n" + "=" * 60)
    print("Para usar em produção, execute:")
    print("python create_brazilian_dataset.py -o dados_brasileiros.csv")
    print("python backend/unificado.py --mode etl --input dados_brasileiros.csv --output processados.csv")
    print("=" * 60)

if __name__ == "__main__":
    main()
