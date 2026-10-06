import pandas as pd
import os
import json
from pathlib import Path
import chardet
from collections import defaultdict

def detect_encoding(file_path):
    """Detecta a codificação do arquivo CSV"""
    with open(file_path, 'rb') as f:
        raw_data = f.read(10000)  # Lê os primeiros 10KB
        result = chardet.detect(raw_data)
        return result['encoding']

def analyze_csv_structure(file_path):
    """Analisa a estrutura de um arquivo CSV"""
    try:
        # Detecta codificação
        encoding = detect_encoding(file_path)
        print(f"Analisando {file_path} com codificação {encoding}")
        
        # Tenta diferentes separadores
        separators = [',', ';', '\t', '|']
        best_df = None
        best_separator = None
        max_columns = 0
        
        for sep in separators:
            try:
                df = pd.read_csv(file_path, encoding=encoding, sep=sep, nrows=5)
                if len(df.columns) > max_columns:
                    max_columns = len(df.columns)
                    best_df = df
                    best_separator = sep
            except:
                continue
        
        if best_df is None:
            return None
            
        # Lê o arquivo completo com o melhor separador
        df = pd.read_csv(file_path, encoding=encoding, sep=best_separator)
        
        analysis = {
            'file_name': os.path.basename(file_path),
            'file_path': file_path,
            'encoding': encoding,
            'separator': best_separator,
            'total_rows': len(df),
            'total_columns': len(df.columns),
            'columns': list(df.columns),
            'column_types': df.dtypes.to_dict(),
            'sample_data': df.head(3).to_dict('records'),
            'missing_values': df.isnull().sum().to_dict(),
            'file_size': os.path.getsize(file_path)
        }
        
        return analysis
        
    except Exception as e:
        print(f"Erro ao analisar {file_path}: {str(e)}")
        return {
            'file_name': os.path.basename(file_path),
            'file_path': file_path,
            'error': str(e)
        }

def find_base_je_files():
    """Encontra todos os arquivos Base JE*.csv"""
    base_je_files = []
    
    # Procura no diretório atual
    current_dir_files = list(Path('.').glob('Base JE*.csv'))
    base_je_files.extend(current_dir_files)
    
    # Procura em subdiretórios específicos se existirem
    possible_dirs = ['data', 'raw', 'ATUAL', 'csv_files']
    for dir_name in possible_dirs:
        if os.path.exists(dir_name):
            dir_files = list(Path(dir_name).glob('Base JE*.csv'))
            base_je_files.extend(dir_files)
    
    return sorted(list(set(base_je_files)))

def compare_column_structures(analyses):
    """Compara as estruturas de colunas entre os arquivos"""
    all_columns = set()
    column_frequency = defaultdict(int)
    column_types_by_file = {}
    
    # Coleta todas as colunas e suas frequências
    for analysis in analyses:
        if 'columns' in analysis:
            file_columns = set(analysis['columns'])
            all_columns.update(file_columns)
            
            for col in file_columns:
                column_frequency[col] += 1
            
            column_types_by_file[analysis['file_name']] = analysis.get('column_types', {})
    
    # Analisa diferenças de nomenclatura
    naming_variations = defaultdict(list)
    for col in all_columns:
        # Agrupa colunas similares (variações de nome)
        base_name = col.lower().strip().replace('_', '').replace(' ', '')
        naming_variations[base_name].append(col)
    
    comparison = {
        'total_unique_columns': len(all_columns),
        'column_frequency': dict(column_frequency),
        'columns_in_all_files': [col for col, freq in column_frequency.items() if freq == len(analyses)],
        'columns_in_some_files': [col for col, freq in column_frequency.items() if freq < len(analyses)],
        'naming_variations': {k: v for k, v in naming_variations.items() if len(v) > 1},
        'column_types_by_file': column_types_by_file
    }
    
    return comparison

def main():
    """Função principal"""
    print("=== ANÁLISE DAS ESTRUTURAS DE COLUNAS DOS ARQUIVOS CSV BASE JE ===")
    print()
    
    # Encontra todos os arquivos Base JE
    base_je_files = find_base_je_files()
    
    if not base_je_files:
        print("Nenhum arquivo Base JE*.csv encontrado no diretório atual.")
        return
    
    print(f"Encontrados {len(base_je_files)} arquivos Base JE:")
    for file in base_je_files:
        print(f"  - {file}")
    print()
    
    # Analisa cada arquivo
    analyses = []
    for file_path in base_je_files:
        analysis = analyze_csv_structure(str(file_path))
        if analysis:
            analyses.append(analysis)
    
    # Compara estruturas
    comparison = compare_column_structures([a for a in analyses if 'columns' in a])
    
    # Salva resultados
    results = {
        'individual_analyses': analyses,
        'structure_comparison': comparison,
        'summary': {
            'total_files_analyzed': len(analyses),
            'files_with_errors': len([a for a in analyses if 'error' in a]),
            'unique_encodings': list(set([a.get('encoding', 'unknown') for a in analyses])),
            'unique_separators': list(set([a.get('separator', 'unknown') for a in analyses]))
        }
    }
    
    # Salva em arquivo JSON
    with open('csv_structure_analysis.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False, default=str)
    
    # Gera relatório de texto
    generate_text_report(results)
    
    print("Análise concluída!")
    print("Resultados salvos em:")
    print("  - csv_structure_analysis.json (dados completos)")
    print("  - csv_analysis_report.txt (relatório legível)")

def generate_text_report(results):
    """Gera um relatório em texto legível"""
    with open('csv_analysis_report.txt', 'w', encoding='utf-8') as f:
        f.write("RELATÓRIO DE ANÁLISE DAS ESTRUTURAS DOS ARQUIVOS CSV BASE JE\n")
        f.write("=" * 60 + "\n\n")
        
        # Resumo geral
        summary = results['summary']
        f.write(f"RESUMO GERAL\n")
        f.write(f"-" * 20 + "\n")
        f.write(f"Total de arquivos analisados: {summary['total_files_analyzed']}\n")
        f.write(f"Arquivos com erros: {summary['files_with_errors']}\n")
        f.write(f"Codificações encontradas: {', '.join(summary['unique_encodings'])}\n")
        f.write(f"Separadores encontrados: {', '.join(summary['unique_separators'])}\n\n")
        
        # Análise de cada arquivo
        f.write("ANÁLISE INDIVIDUAL DOS ARQUIVOS\n")
        f.write("-" * 35 + "\n")
        for analysis in results['individual_analyses']:
            f.write(f"\nArquivo: {analysis['file_name']}\n")
            if 'error' in analysis:
                f.write(f"  ERRO: {analysis['error']}\n")
            else:
                f.write(f"  Codificação: {analysis.get('encoding', 'N/A')}\n")
                f.write(f"  Separador: {repr(analysis.get('separator', 'N/A'))}\n")
                f.write(f"  Linhas: {analysis.get('total_rows', 'N/A')}\n")
                f.write(f"  Colunas: {analysis.get('total_columns', 'N/A')}\n")
                f.write(f"  Tamanho: {analysis.get('file_size', 0) / 1024:.1f} KB\n")
                if 'columns' in analysis:
                    f.write(f"  Nomes das colunas: {', '.join(analysis['columns'][:10])}")
                    if len(analysis['columns']) > 10:
                        f.write(f" ... (+{len(analysis['columns']) - 10} mais)")
                    f.write("\n")
        
        # Comparação de estruturas
        comparison = results['structure_comparison']
        f.write(f"\n\nCOMPARAÇÃO DE ESTRUTURAS\n")
        f.write("-" * 25 + "\n")
        f.write(f"Total de colunas únicas: {comparison['total_unique_columns']}\n")
        f.write(f"Colunas presentes em todos os arquivos: {len(comparison['columns_in_all_files'])}\n")
        f.write(f"Colunas presentes em alguns arquivos: {len(comparison['columns_in_some_files'])}\n\n")
        
        # Colunas comuns
        if comparison['columns_in_all_files']:
            f.write("COLUNAS PRESENTES EM TODOS OS ARQUIVOS:\n")
            for col in comparison['columns_in_all_files']:
                f.write(f"  - {col}\n")
            f.write("\n")
        
        # Variações de nomenclatura
        if comparison['naming_variations']:
            f.write("POSSÍVEIS VARIAÇÕES DE NOMENCLATURA:\n")
            for base_name, variations in comparison['naming_variations'].items():
                f.write(f"  {base_name}: {', '.join(variations)}\n")
            f.write("\n")
        
        # Frequência de colunas
        f.write("FREQUÊNCIA DAS COLUNAS (ordenado por frequência):\n")
        sorted_freq = sorted(comparison['column_frequency'].items(), key=lambda x: x[1], reverse=True)
        for col, freq in sorted_freq[:20]:  # Top 20
            f.write(f"  {col}: {freq} arquivo(s)\n")
        if len(sorted_freq) > 20:
            f.write(f"  ... (+{len(sorted_freq) - 20} colunas com menor frequência)\n")

if __name__ == "__main__":
    main()

