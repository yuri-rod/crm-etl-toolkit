#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gerador de Regras ETL com IA - Claude Integration
CRM ETL

Este módulo usa IA generativa (Claude) para converter requisitos em linguagem natural
em código Python funcional para transformações ETL.

Exemplo de uso:
    "Padronizar datas brasileiras para formato dd/mm/aaaa"
    → Código Python automático para transformar datas
"""

import os
import re
import ast
import sys
import json
import logging
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import anthropic
from pathlib import Path

# Importar acelerador GPU
try:
    from gpu_accelerator import GPUAccelerator, GPUAccelerationConfig, GPUDataProcessor
    GPU_AVAILABLE = True
except ImportError:
    GPU_AVAILABLE = False
    logging.info("GPU Accelerator não disponível para AI Rule Generator")

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AIRuleGenerator:
    """Gerador de regras ETL usando IA Claude (com aceleração GPU)"""
    
    def __init__(self, api_key: Optional[str] = None, enable_gpu: bool = True):
        """
        Inicializa o gerador de regras IA
        
        Args:
            api_key: Chave da API Claude (se não fornecida, busca em variável de ambiente)
            enable_gpu: Habilitar aceleração GPU para processamento de dados
        """
        self.api_key = api_key or os.getenv('CLAUDE_API_KEY')
        
        if not self.api_key:
            logger.warning("Claude API key não encontrada. Usando modo simulado.")
            self.claude_client = None
        else:
            try:
                self.claude_client = anthropic.Anthropic(api_key=self.api_key)
                logger.info("Cliente Claude inicializado com sucesso")
            except Exception as e:
                logger.error(f"Erro ao inicializar Claude: {e}")
                self.claude_client = None
        
        # Configurar aceleração GPU
        self.gpu_enabled = enable_gpu and GPU_AVAILABLE
        self.gpu_processor = None
        
        if self.gpu_enabled:
            try:
                gpu_config = GPUAccelerationConfig(
                    enabled=True,
                    prefer_gpu=True,
                    memory_fraction=0.3,  # Usar memória moderada para geração de regras
                    fallback_to_cpu=True
                )
                gpu_accelerator = GPUAccelerator(gpu_config)
                self.gpu_processor = GPUDataProcessor(gpu_accelerator)
                logger.info("AI Rule Generator com aceleração GPU habilitado")
            except Exception as e:
                logger.warning(f"Falha ao inicializar GPU: {e}")
                self.gpu_enabled = False
        
        # Cache de regras geradas
        self.rule_cache = {}
        
        # Templates de transformações comuns
        self.templates = {
            'padronizacao_texto': '''
def padronizar_texto(df, coluna, tipo_padronizacao='title'):
    """Padroniza texto conforme especificado"""
    if tipo_padronizacao == 'title':
        df[coluna] = df[coluna].str.title()
    elif tipo_padronizacao == 'upper':
        df[coluna] = df[coluna].str.upper()
    elif tipo_padronizacao == 'lower':
        df[coluna] = df[coluna].str.lower()
    return df
            ''',
            'limpeza_dados': '''
def limpar_dados(df, colunas=None):
    """Remove espaços e caracteres inválidos"""
    if colunas is None:
        colunas = df.select_dtypes(include=['object']).columns
    
    for col in colunas:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()
            df[col] = df[col].str.replace(r'\\s+', ' ', regex=True)
    
    return df
            ''',
            'padronizacao_datas': '''
def padronizar_datas(df, coluna, formato_origem=None, formato_destino='%d/%m/%Y'):
    """Padroniza datas para formato brasileiro"""
    import pandas as pd
    from datetime import datetime
    
    # Detectar e converter datas em português
    meses_pt = {
        'janeiro': '01', 'fevereiro': '02', 'março': '03', 'abril': '04',
        'maio': '05', 'junho': '06', 'julho': '07', 'agosto': '08',
        'setembro': '09', 'outubro': '10', 'novembro': '11', 'dezembro': '12'
    }
    
    def converter_data_pt(data_str):
        if pd.isna(data_str):
            return None
            
        data_str = str(data_str).lower()
        
        # Padrão: "02 outubro 1968"
        import re
        match = re.search(r'(\\d{1,2})\\s+(\\w+)\\s+(\\d{4})', data_str)
        if match:
            dia, mes_nome, ano = match.groups()
            if mes_nome in meses_pt:
                return f"{dia.zfill(2)}/{meses_pt[mes_nome]}/{ano}"
        
        # Tentar conversão padrão
        try:
            data_convertida = pd.to_datetime(data_str, errors='coerce')
            if not pd.isna(data_convertida):
                return data_convertida.strftime(formato_destino)
        except:
            pass
        
        return data_str
    
    df[coluna] = df[coluna].apply(converter_data_pt)
    return df
            '''
        }

    def generate_rule_from_description(self, description: str, column_info: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Gera uma regra ETL baseada em descrição em linguagem natural
        
        Args:
            description: Descrição da transformação desejada
            column_info: Informações sobre as colunas do dataset (opcional)
            
        Returns:
            Dict contendo o código gerado e metadados
        """
        logger.info(f"Gerando regra para: {description}")
        
        # Verificar cache
        cache_key = f"{description}_{hash(str(column_info)) if column_info else 'no_cols'}"
        if cache_key in self.rule_cache:
            logger.info("Regra encontrada no cache")
            return self.rule_cache[cache_key]
        
        # Tentar usar Claude API
        if self.claude_client:
            result = self._generate_with_claude(description, column_info)
        else:
            # Fallback para templates/regras predefinidas
            result = self._generate_with_templates(description, column_info)
        
        # Salvar no cache
        self.rule_cache[cache_key] = result
        
        return result

    def _generate_with_claude(self, description: str, column_info: Optional[Dict] = None) -> Dict[str, Any]:
        """Gera regra usando Claude API"""
        
        # Construir contexto
        context = "Dataset pandas DataFrame com as seguintes colunas:\n"
        if column_info:
            for col, info in column_info.items():
                context += f"- {col}: {info.get('dtype', 'object')} - {info.get('sample', 'N/A')}\n"
        else:
            context += "- Estrutura não especificada, assumir DataFrame genérico\n"
        
        prompt = f"""
Você é um especialista em ETL e Python. Crie uma função Python para a seguinte transformação:

REQUISITO: {description}

CONTEXTO DO DATASET:
{context}

INSTRUÇÕES:
1. Crie uma função Python que aceite um DataFrame pandas como parâmetro
2. A função deve aplicar a transformação solicitada
3. Retorne o DataFrame modificado
4. Inclua tratamento de erros básico
5. Use boas práticas de pandas
6. Adicione comentários explicativos
7. A função deve ser segura e não quebrar com dados inesperados

FORMATO DE RESPOSTA:
Retorne APENAS o código Python, começando com 'def' e terminando com 'return df'.
Não inclua imports externos além de pandas (que já está disponível como pd).

EXEMPLO DE FUNÇÃO:
```python
def transformar_dados(df):
    \"\"\"Descrição da transformação\"\"\"
    try:
        # Sua lógica aqui
        df_modificado = df.copy()
        # ... transformações ...
        return df_modificado
    except Exception as e:
        print(f"Erro na transformação: {{e}}")
        return df
```
"""

        try:
            response = self.claude_client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=1500,
                temperature=0.1,
                messages=[{"role": "user", "content": prompt}]
            )
            
            generated_code = response.content[0].text.strip()
            
            # Limpar código (remover markdown se presente)
            generated_code = re.sub(r'^```python\s*', '', generated_code)
            generated_code = re.sub(r'```\s*$', '', generated_code)
            
            # Validar código
            validation_result = self._validate_generated_code(generated_code)
            
            return {
                'code': generated_code,
                'description': description,
                'source': 'claude_ai',
                'validation': validation_result,
                'timestamp': datetime.now().isoformat(),
                'column_info': column_info
            }
            
        except Exception as e:
            logger.error(f"Erro ao gerar com Claude: {e}")
            return self._generate_with_templates(description, column_info)

    def _generate_with_templates(self, description: str, column_info: Optional[Dict] = None) -> Dict[str, Any]:
        """Gera regra usando templates predefinidos"""
        
        description_lower = description.lower()
        
        # Mapear descrição para template
        if any(word in description_lower for word in ['padronizar', 'maiúscula', 'minúscula', 'title']):
            code = self.templates['padronizacao_texto']
            template_used = 'padronizacao_texto'
        elif any(word in description_lower for word in ['data', 'data', 'brasileiro', 'dd/mm/yyyy']):
            code = self.templates['padronizacao_datas']
            template_used = 'padronizacao_datas'
        elif any(word in description_lower for word in ['limpar', 'espaços', 'caracteres']):
            code = self.templates['limpeza_dados']
            template_used = 'limpeza_dados'
        else:
            # Template genérico
            code = f'''
def transformacao_customizada(df):
    """
    Transformação para: {description}
    
    ATENÇÃO: Esta é uma função template que precisa ser personalizada.
    Substitua o comentário abaixo pela lógica específica.
    """
    df_modificado = df.copy()
    
    # TODO: Implementar lógica específica para: {description}
    # Exemplo de estrutura:
    # for col in df_modificado.columns:
    #     df_modificado[col] = df_modificado[col].apply(lambda x: x)  # sua lógica aqui
    
    return df_modificado
'''
            template_used = 'generico'
        
        validation_result = self._validate_generated_code(code)
        
        return {
            'code': code,
            'description': description,
            'source': 'template',
            'template_used': template_used,
            'validation': validation_result,
            'timestamp': datetime.now().isoformat(),
            'column_info': column_info
        }

    def _validate_generated_code(self, code: str) -> Dict[str, Any]:
        """Valida o código gerado"""
        
        validation = {
            'is_valid': False,
            'syntax_ok': False,
            'has_function': False,
            'function_name': None,
            'errors': []
        }
        
        try:
            # Verificar sintaxe
            ast.parse(code)
            validation['syntax_ok'] = True
            
            # Verificar se tem função
            tree = ast.parse(code)
            functions = [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
            
            if functions:
                validation['has_function'] = True
                validation['function_name'] = functions[0]
            else:
                validation['errors'].append("Código não contém função definida")
            
            # Verificar se função aceita DataFrame
            if 'def ' in code and '(df' in code:
                validation['accepts_dataframe'] = True
            else:
                validation['errors'].append("Função não aceita DataFrame como parâmetro")
            
            # Verificar se retorna DataFrame
            if 'return' in code:
                validation['returns_data'] = True
            else:
                validation['errors'].append("Função não retorna dados")
            
            validation['is_valid'] = (validation['syntax_ok'] and 
                                    validation['has_function'] and 
                                    len(validation['errors']) == 0)
            
        except SyntaxError as e:
            validation['errors'].append(f"Erro de sintaxe: {e}")
        except Exception as e:
            validation['errors'].append(f"Erro de validação: {e}")
        
        return validation

    def execute_rule(self, rule: Dict[str, Any], df: pd.DataFrame) -> Tuple[bool, pd.DataFrame, str]:
        """
        Executa uma regra gerada no DataFrame (com aceleração GPU quando apropriado)
        
        Args:
            rule: Regra gerada pelo generate_rule_from_description
            df: DataFrame para aplicar a transformação
            
        Returns:
            Tuple: (sucesso, dataframe_resultado, mensagem)
        """
        
        if not rule['validation']['is_valid']:
            return False, df, f"Regra inválida: {', '.join(rule['validation']['errors'])}"
        
        # Para DataFrames grandes, tentar usar GPU
        if self.gpu_enabled and len(df) > 50000:
            try:
                return self._execute_rule_gpu(rule, df)
            except Exception as e:
                logger.warning(f"Fallback para execução CPU: {e}")
        
        # Execução padrão CPU
        return self._execute_rule_cpu(rule, df)
    
    def _execute_rule_cpu(self, rule: Dict[str, Any], df: pd.DataFrame) -> Tuple[bool, pd.DataFrame, str]:
        """Executa regra usando CPU"""
        
        try:
            # Criar um namespace seguro para execução
            namespace = {
                'pd': pd,
                'df': df.copy(),
                'datetime': datetime,
                're': re
            }
            
            # Executar código
            exec(rule['code'], namespace)
            
            # Obter função gerada
            function_name = rule['validation']['function_name']
            if function_name in namespace:
                func = namespace[function_name]
                result_df = func(df.copy())
                
                return True, result_df, f"Transformação '{rule['description']}' aplicada com sucesso (CPU)"
            else:
                return False, df, f"Função {function_name} não encontrada após execução"
                
        except Exception as e:
            logger.error(f"Erro ao executar regra: {e}")
            return False, df, f"Erro na execução: {e}"
    
    def _execute_rule_gpu(self, rule: Dict[str, Any], df: pd.DataFrame) -> Tuple[bool, pd.DataFrame, str]:
        """Executa regra usando GPU para datasets grandes"""
        
        if not self.gpu_processor:
            raise Exception("GPU processor não disponível")
        
        logger.info(f"Executando regra em GPU para dataset com {len(df)} registros")
        
        # Pré-processar dados com GPU para otimizar
        operations = ['fillna']  # Operações básicas de preparação
        df_processed = self.gpu_processor.process_large_dataframe(df, operations)
        
        # Executar a regra no DataFrame pré-processado
        success, result_df, message = self._execute_rule_cpu(rule, df_processed)
        
        if success:
            return True, result_df, f"Transformação '{rule['description']}' aplicada com sucesso (GPU+CPU)"
        else:
            return success, result_df, message

    def save_rule(self, rule: Dict[str, Any], filename: str) -> bool:
        """Salva regra em arquivo para reutilização"""
        
        try:
            rules_dir = Path("generated_rules")
            rules_dir.mkdir(exist_ok=True)
            
            filepath = rules_dir / f"{filename}.json"
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(rule, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Regra salva em: {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao salvar regra: {e}")
            return False

    def load_rule(self, filename: str) -> Optional[Dict[str, Any]]:
        """Carrega regra salva de arquivo"""
        
        try:
            rules_dir = Path("generated_rules")
            filepath = rules_dir / f"{filename}.json"
            
            if not filepath.exists():
                logger.warning(f"Arquivo de regra não encontrado: {filepath}")
                return None
            
            with open(filepath, 'r', encoding='utf-8') as f:
                rule = json.load(f)
            
            logger.info(f"Regra carregada de: {filepath}")
            return rule
            
        except Exception as e:
            logger.error(f"Erro ao carregar regra: {e}")
            return None

    def list_saved_rules(self) -> List[str]:
        """Lista regras salvas disponíveis"""
        
        try:
            rules_dir = Path("generated_rules")
            if not rules_dir.exists():
                return []
            
            rule_files = [f.stem for f in rules_dir.glob("*.json")]
            return sorted(rule_files)
            
        except Exception as e:
            logger.error(f"Erro ao listar regras: {e}")
            return []

    def analyze_dataset_for_suggestions(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analisa dataset e sugere transformações possíveis"""
        
        analysis = {
            'column_info': {},
            'suggested_transformations': [],
            'data_quality_issues': []
        }
        
        for col in df.columns:
            col_info = {
                'dtype': str(df[col].dtype),
                'null_count': df[col].isnull().sum(),
                'unique_count': df[col].nunique(),
                'sample_values': df[col].dropna().head(3).tolist()
            }
            
            # Detectar problemas de qualidade
            if col_info['null_count'] > 0:
                analysis['data_quality_issues'].append(f"Coluna '{col}' tem {col_info['null_count']} valores nulos")
            
            # Sugerir transformações baseadas no tipo e conteúdo
            if df[col].dtype == 'object':
                # Verificar se precisa de padronização de texto
                sample_values = [str(v) for v in col_info['sample_values']]
                if any(v.isupper() for v in sample_values):
                    analysis['suggested_transformations'].append(f"Padronizar texto na coluna '{col}' (contém MAIÚSCULAS)")
                
                # Verificar se é data em português
                if any('janeiro' in str(v).lower() or 'outubro' in str(v).lower() for v in sample_values):
                    analysis['suggested_transformations'].append(f"Converter datas em português na coluna '{col}'")
            
            analysis['column_info'][col] = col_info
        
        return analysis


def demo_ai_rule_generator():
    """Demonstração do gerador de regras IA com aceleração GPU"""
    
    print("🤖 DEMO: Gerador de Regras ETL com IA + GPU")
    print("=" * 55)
    
    # Inicializar gerador com GPU
    generator = AIRuleGenerator(enable_gpu=True)
    
    # Mostrar status GPU
    if generator.gpu_enabled:
        print("🚀 Aceleração GPU habilitada para processamento de dados grandes")
    else:
        print("💻 Usando processamento CPU padrão")
    
    # Criar dados de exemplo (maior para demonstrar GPU)
    print("📊 Criando dataset de exemplo...")
    
    import numpy as np
    
    # Dataset maior para demonstrar benefícios GPU
    n_rows = 100000
    dados_exemplo = pd.DataFrame({
        'nome': [f'USUARIO_{i}' if i % 2 == 0 else f'usuario_{i}' for i in range(n_rows)],
        'data_nascimento': [f'{np.random.randint(1,28):02d} {"OUTUBRO" if i % 3 == 0 else "outubro"} {np.random.randint(1950,2000)}' for i in range(n_rows)],
        'estado_civil': [np.random.choice(['CASADO', 'solteira', 'DIVORCIADO']) for _ in range(n_rows)],
        'email': [f'user{i}@{"TEST.COM" if i % 2 == 0 else "test.com"}' for i in range(n_rows)]
    })
    
    print(f"Dataset criado: {len(dados_exemplo)} registros")
    print("Amostra dos dados:")
    print(dados_exemplo.head(3))
    print()
    
    # Analisar dataset
    print("🔍 Análise do dataset:")
    analysis = generator.analyze_dataset_for_suggestions(dados_exemplo)
    print("Transformações sugeridas:")
    for suggestion in analysis['suggested_transformations']:
        print(f"  - {suggestion}")
    print()
    
    # Testar geração de regras
    test_descriptions = [
        "Padronizar nomes para Title Case",
        "Converter emails para minúsculas",
        "Padronizar datas brasileiras para formato dd/mm/aaaa",
        "Padronizar estado civil (primeira letra maiúscula)"
    ]
    
    for description in test_descriptions:
        print(f"🔄 Processando: {description}")
        
        # Gerar regra
        rule = generator.generate_rule_from_description(description, analysis['column_info'])
        
        print(f"  Fonte: {rule['source']}")
        print(f"  Válida: {rule['validation']['is_valid']}")
        
        if rule['validation']['is_valid']:
            # Executar transformação com medição de tempo
            import time
            start_time = time.time()
            
            success, resultado, message = generator.execute_rule(rule, dados_exemplo)
            
            execution_time = time.time() - start_time
            
            if success:
                print(f"  ✅ {message}")
                print(f"  ⏱️ Tempo de execução: {execution_time:.3f}s")
                # Mostrar resultado apenas da primeira transformação como exemplo
                if description == test_descriptions[0]:
                    print("  📊 Resultado (amostra):")
                    print(resultado[['nome']].head(3))
            else:
                print(f"  ❌ {message}")
        else:
            print(f"  ❌ Erros: {', '.join(rule['validation']['errors'])}")
        
        print()


if __name__ == "__main__":
    demo_ai_rule_generator()