import json
import pandas as pd

def analyze_structure_differences():
    """Analisa as diferenças estruturais entre os arquivos CSV"""
    
    # Carrega os dados da análise
    with open('csv_structure_analysis.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print("=== MAPEAMENTO DETALHADO DAS ESTRUTURAS DE COLUNAS DOS ARQUIVOS CSV BASE JE ===")
    print("=" * 80)
    print()
    
    # Análise das diferenças de estrutura por período
    analyses = data['individual_analyses']
    comparison = data['structure_comparison']
    
    # Agrupa por número de colunas
    files_by_columns = {}
    for analysis in analyses:
        if 'columns' in analysis:
            col_count = analysis['total_columns']
            if col_count not in files_by_columns:
                files_by_columns[col_count] = []
            files_by_columns[col_count].append(analysis)
    
    print("1. EVOLUÇÃO DA ESTRUTURA DOS FORMULÁRIOS")
    print("-" * 50)
    for col_count in sorted(files_by_columns.keys()):
        files = files_by_columns[col_count]
        print(f"\n{col_count} colunas ({len(files)} arquivo(s)):")
        for file in files:
            print(f"  - {file['file_name']} ({file['total_rows']} registros)")
    
    # Colunas que variam entre formulários
    print("\n\n2. DIFERENÇAS DE NOMENCLATURA E CAMPOS")
    print("-" * 50)
    
    # Identifica colunas presentes apenas em alguns arquivos
    partial_columns = [col for col, freq in comparison['column_frequency'].items() 
                      if freq < len(analyses) and freq > 1]
    
    print(f"\nColunas presentes em alguns arquivos (mas não todos):")
    for col in partial_columns:
        freq = comparison['column_frequency'][col]
        print(f"  - '{col}' (presente em {freq}/{len(analyses)} arquivos)")
    
    # Identifica colunas únicas
    unique_columns = [col for col, freq in comparison['column_frequency'].items() if freq == 1]
    print(f"\nColunas presentes em apenas 1 arquivo:")
    for col in unique_columns:
        # Encontra qual arquivo tem essa coluna
        for analysis in analyses:
            if 'columns' in analysis and col in analysis['columns']:
                print(f"  - '{col}' (apenas em {analysis['file_name']})")
                break
    
    # Análise de variações de nomenclatura
    print("\n\n3. ANÁLISE DE VARIAÇÕES DE NOMENCLATURA")
    print("-" * 50)
    
    # Grupos similares de perguntas
    empresa_questions = []
    cargo_questions = []
    segmento_questions = []
    
    for col in comparison['column_frequency'].keys():
        col_lower = col.lower()
        if 'empresa' in col_lower:
            empresa_questions.append(col)
        elif 'cargo' in col_lower:
            cargo_questions.append(col)
        elif 'segmento' in col_lower or 'seguimento' in col_lower:
            segmento_questions.append(col)
    
    if empresa_questions:
        print("\nPerguntas sobre EMPRESA:")
        for q in empresa_questions:
            freq = comparison['column_frequency'][q]
            print(f"  - '{q}' ({freq} arquivo(s))")
    
    if cargo_questions:
        print("\nPerguntas sobre CARGO:")
        for q in cargo_questions:
            freq = comparison['column_frequency'][q]
            print(f"  - '{q}' ({freq} arquivo(s))")
    
    if segmento_questions:
        print("\nPerguntas sobre SEGMENTO:")
        for q in segmento_questions:
            freq = comparison['column_frequency'][q]
            print(f"  - '{q}' ({freq} arquivo(s))")
    
    # Análise de formatos de data
    print("\n\n4. ANÁLISE DE FORMATOS DE DADOS")
    print("-" * 50)
    
    # Analisa as amostras de dados para identificar formatos
    date_formats = set()
    cpf_formats = set()
    phone_formats = set()
    
    for analysis in analyses:
        if 'sample_data' in analysis:
            for sample in analysis['sample_data']:
                # Formatos de data de aniversário
                birthday_field = '{{field:86f9256513e5d6db}}, qual é o dia do seu aniversário?'
                if birthday_field in sample and sample[birthday_field]:
                    date_formats.add(str(sample[birthday_field]))
                
                # Formatos de CPF
                if 'CPF:' in sample and sample['CPF:']:
                    cpf_formats.add(str(sample['CPF:']))
                
                # Formatos de telefone
                if 'WhatsApp' in sample and sample['WhatsApp']:
                    phone_formats.add(str(sample['WhatsApp']))
    
    print("\nFormatos de Data de Aniversário encontrados:")
    for fmt in sorted(list(date_formats)[:10]):  # Primeiros 10
        print(f"  - {fmt}")
    
    print("\nFormatos de CPF encontrados:")
    for fmt in sorted(list(cpf_formats)[:5]):  # Primeiros 5
        print(f"  - {fmt}")
    
    print("\nFormatos de Telefone encontrados:")
    for fmt in sorted(list(phone_formats)[:5]):  # Primeiros 5
        print(f"  - {fmt}")
    
    # Mapeamento de padronização recomendado
    print("\n\n5. MAPEAMENTO PARA PADRONIZAÇÃO AUTOMÁTICA")
    print("-" * 60)
    
    print("\nCOLUNAS CORE (presentes em todos os arquivos):")
    core_columns = comparison['columns_in_all_files']
    for i, col in enumerate(core_columns, 1):
        print(f"  {i:2d}. {col}")
    
    print("\nRECOMENDAÇÕES DE PADRONIZAÇÃO:")
    print("  1. Nomenclatura das colunas:")
    print("     - Remover caracteres especiais (: e espaços extras)")
    print("     - Padronizar case (ex: snake_case ou camelCase)")
    print("     - Substituir campos template {{field:...}} por nomes descritivos")
    
    print("\n  2. Formatos de dados:")
    print("     - CPF: remover pontuação, manter apenas números")
    print("     - Telefone: padronizar formato internacional (+55...)")
    print("     - Data de aniversário: converter para formato ISO (YYYY-MM-DD)")
    print("     - RG: padronizar formato por estado")
    
    print("\n  3. Estrutura unificada sugerida:")
    print("     - Manter as 20 colunas presentes em todos os arquivos")
    print("     - Adicionar colunas opcionais para campos específicos de algumas bases")
    print("     - Criar campos normalizados para empresa/cargo/segmento")
    
    return {
        'files_by_columns': files_by_columns,
        'core_columns': core_columns,
        'partial_columns': partial_columns,
        'unique_columns': unique_columns,
        'total_unique_columns': comparison['total_unique_columns']
    }

if __name__ == "__main__":
    result = analyze_structure_differences()
    print(f"\n\nRESUMO EXECUTIVO:")
    print(f"- Total de arquivos analisados: 17")
    print(f"- Total de colunas únicas: {result['total_unique_columns']}")
    print(f"- Colunas presentes em todos: {len(result['core_columns'])}")
    print(f"- Colunas presentes parcialmente: {len(result['partial_columns'])}")
    print(f"- Colunas únicas (1 arquivo): {len(result['unique_columns'])}")
    print(f"- Variações de estrutura: {len(result['files_by_columns'])} grupos diferentes")

