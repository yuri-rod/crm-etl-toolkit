#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=================================================
--- Gerador de Regras ETL com IA Generativa ---
=================================================

Sistema avançado que utiliza modelos de linguagem (Claude, OpenAI) para gerar 
automaticamente regras de transformação ETL baseadas em linguagem natural.

Desenvolvido para CRM ETL
Autor: Sistema ETL Inteligente
Data: 2025
"""

import os
import re
import json
import logging
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from pathlib import Path

# Bibliotecas de IA
try:
    import anthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False

try:
    import openai
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AIRuleGenerator:
    """
    Gerador inteligente de regras ETL usando IA generativa
    """
    
    def __init__(self, 
                 claude_api_key: Optional[str] = None,
                 openai_api_key: Optional[str] = None,
                 preferred_model: str = "claude"):
        """
        Inicializa o gerador de regras com IA
        
        Args:
            claude_api_key: Chave da API Anthropic Claude
            openai_api_key: Chave da API OpenAI
            preferred_model: Modelo preferido ('claude' ou 'openai')
        """
        
        self.claude_client = None
        self.openai_client = None
        self.preferred_model = preferred_model
        
        # Configurar Claude
        if claude_api_key or os.getenv("ANTHROPIC_API_KEY"):
            if HAS_ANTHROPIC:
                self.claude_client = anthropic.Anthropic(
                    api_key=claude_api_key or os.getenv("ANTHROPIC_API_KEY")
                )
                logger.info("✅ Claude API configurado com sucesso")
            else:
                logger.warning("❌ Biblioteca 'anthropic' não instalada")
        
        # Configurar OpenAI
        if openai_api_key or os.getenv("OPENAI_API_KEY"):
            if HAS_OPENAI:
                openai.api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
                self.openai_client = openai
                logger.info("✅ OpenAI API configurado com sucesso")
            else:
                logger.warning("❌ Biblioteca 'openai' não instalada")
        
        # Cache de regras
        self.rule_cache = {}
        self.execution_history = []
        
        # Validador de código
        self.code_validator = PythonCodeValidator()
    
    def generate_transformation_rule(self, 
                                   requirement: str, 
                                   data_context: Optional[Dict] = None,
                                   save_to_cache: bool = True) -> Dict[str, Any]:
        """
        Gera uma regra de transformação ETL baseada em linguagem natural
        
        Args:
            requirement: Descrição em português da transformação desejada
            data_context: Contexto sobre os dados (colunas, tipos, exemplos)
            save_to_cache: Se deve salvar no cache para reutilização
            
        Returns:
            Dict com código Python, validação e metadados
        """
        
        logger.info(f"🤖 Gerando regra para: {requirement}")
        
        # Verificar cache primeiro
        cache_key = self._generate_cache_key(requirement, data_context)
        if cache_key in self.rule_cache:
            logger.info("📋 Regra encontrada no cache")
            return self.rule_cache[cache_key]
        
        # Construir prompt contextualizado
        prompt = self._build_transformation_prompt(requirement, data_context)
        
        # Gerar código usando IA
        ai_response = self._call_ai_api(prompt)
        
        if not ai_response:
            raise Exception("Erro ao gerar regra com IA")
        
        # Processar e validar resposta
        rule_result = self._process_ai_response(ai_response, requirement)
        
        # Salvar no cache se solicitado
        if save_to_cache:
            self.rule_cache[cache_key] = rule_result
        
        # Adicionar ao histórico
        self.execution_history.append({
            'timestamp': datetime.now().isoformat(),
            'requirement': requirement,
            'success': rule_result['validation']['is_valid'],
            'execution_time': rule_result['metadata']['generation_time']
        })
        
        return rule_result
    
    def _build_transformation_prompt(self, requirement: str, data_context: Optional[Dict] = None) -> str:
        """Constrói prompt otimizado para geração de regras ETL"""
        
        base_prompt = f"""
Você é um especialista em ETL e Data Engineering da CRM ETL.

TAREFA: Criar uma função Python para transformação de dados baseada neste requisito:
"{requirement}"

CONTEXTO DOS DADOS:
"""
        
        if data_context:
            if 'columns' in data_context:
                base_prompt += f"- Colunas disponíveis: {data_context['columns']}\n"
            if 'dtypes' in data_context:
                base_prompt += f"- Tipos de dados: {data_context['dtypes']}\n"
            if 'sample_data' in data_context:
                base_prompt += f"- Exemplo dos dados:\n{data_context['sample_data']}\n"
        
        base_prompt += """
REQUISITOS TÉCNICOS:
1. Usar pandas DataFrame como entrada e saída
2. Incluir tratamento de erros e validações
3. Adicionar logs informativos
4. Comentários em português
5. Seguir padrões CRM de codificação
6. Retornar sempre um DataFrame válido

FORMATO DE RESPOSTA:
```python
def transform_data(df: pd.DataFrame) -> pd.DataFrame:
    \"\"\"
    [Descrição da transformação em português]
    
    Args:
        df: DataFrame de entrada
        
    Returns:
        DataFrame transformado
    \"\"\"
    import pandas as pd
    import numpy as np
    import logging
    
    logger = logging.getLogger(__name__)
    logger.info("CRM - Iniciando transformação: [descrição]")
    
    try:
        # Validação de entrada
        if df.empty:
            raise ValueError("DataFrame de entrada está vazio")
        
        # Sua transformação aqui
        df_transformed = df.copy()
        
        # [Código da transformação]
        
        logger.info(f"CRM - Transformação concluída. Registros: {len(df_transformed)}")
        return df_transformed
        
    except Exception as e:
        logger.error(f"CRM - Erro na transformação: {e}")
        raise
```

IMPORTANTE: Responda APENAS com o código Python, sem explicações adicionais.
"""
        
        return base_prompt
    
    def _call_ai_api(self, prompt: str) -> Optional[str]:
        """Chama a API de IA preferida para geração do código"""
        
        try:
            if self.preferred_model == "claude" and self.claude_client:
                return self._call_claude_api(prompt)
            elif self.preferred_model == "openai" and self.openai_client:
                return self._call_openai_api(prompt)
            else:
                # Fallback para qualquer API disponível
                if self.claude_client:
                    return self._call_claude_api(prompt)
                elif self.openai_client:
                    return self._call_openai_api(prompt)
                else:
                    logger.error("❌ Nenhuma API de IA configurada")
                    return None
                    
        except Exception as e:
            logger.error(f"❌ Erro ao chamar API de IA: {e}")
            return None
    
    def _call_claude_api(self, prompt: str) -> str:
        """Chama a API do Claude"""
        try:
            response = self.claude_client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=2000,
                temperature=0.3,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            return response.content[0].text
        except Exception as e:
            logger.error(f"Erro na API Claude: {e}")
            raise
    
    def _call_openai_api(self, prompt: str) -> str:
        """Chama a API do OpenAI"""
        try:
            response = self.openai_client.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": "Você é um especialista em ETL da CRM ETL."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=2000,
                temperature=0.3
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Erro na API OpenAI: {e}")
            raise
    
    def _process_ai_response(self, ai_response: str, requirement: str) -> Dict[str, Any]:
        """Processa e valida a resposta da IA"""
        
        generation_start = datetime.now()
        
        # Extrair código Python da resposta
        python_code = self._extract_python_code(ai_response)
        
        if not python_code:
            raise ValueError("Não foi possível extrair código Python válido da resposta da IA")
        
        # Validar código
        validation_result = self.code_validator.validate_code(python_code)
        
        # Executar teste se o código for válido
        test_result = None
        if validation_result['is_valid']:
            test_result = self._test_generated_code(python_code)
        
        generation_time = (datetime.now() - generation_start).total_seconds()
        
        return {
            'requirement': requirement,
            'generated_code': python_code,
            'raw_ai_response': ai_response,
            'validation': validation_result,
            'test_result': test_result,
            'metadata': {
                'generation_time': generation_time,
                'model_used': self.preferred_model,
                'timestamp': datetime.now().isoformat(),
                'code_lines': len(python_code.split('\n'))
            }
        }
    
    def _extract_python_code(self, response: str) -> Optional[str]:
        """Extrai código Python da resposta da IA"""
        
        # Procurar por blocos de código Python
        python_blocks = re.findall(r'```python\s*(.*?)\s*```', response, re.DOTALL)
        
        if python_blocks:
            return python_blocks[0].strip()
        
        # Fallback: procurar por 'def transform_data'
        if 'def transform_data' in response:
            # Extrair a partir da definição da função
            start_idx = response.find('def transform_data')
            if start_idx != -1:
                return response[start_idx:].strip()
        
        return None
    
    def _test_generated_code(self, code: str) -> Dict[str, Any]:
        """Testa o código gerado com dados de exemplo"""
        
        try:
            # Criar DataFrame de teste
            test_df = pd.DataFrame({
                'nome': ['João Silva', 'Maria Santos', 'Pedro Oliveira'],
                'email': ['joao@email.com', 'maria@teste.com', 'pedro@exemplo.com'],
                'idade': [25, 30, 35],
                'cidade': ['São Paulo', 'Rio de Janeiro', 'Belo Horizonte'],
                'data_cadastro': ['2024-01-15', '2024-02-10', '2024-03-05']
            })
            
            # Executar código em namespace seguro
            namespace = {
                'pd': pd,
                'np': np,
                'logging': logging
            }
            
            exec(code, namespace)
            
            # Executar função
            if 'transform_data' in namespace:
                result_df = namespace['transform_data'](test_df.copy())
                
                return {
                    'success': True,
                    'input_shape': test_df.shape,
                    'output_shape': result_df.shape,
                    'columns_added': list(set(result_df.columns) - set(test_df.columns)),
                    'columns_removed': list(set(test_df.columns) - set(result_df.columns)),
                    'execution_time': 'success'
                }
            else:
                return {
                    'success': False,
                    'error': 'Função transform_data não encontrada'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _generate_cache_key(self, requirement: str, data_context: Optional[Dict] = None) -> str:
        """Gera chave para cache baseada no requisito e contexto"""
        
        key_components = [requirement.lower().strip()]
        
        if data_context:
            if 'columns' in data_context:
                key_components.append(str(sorted(data_context['columns'])))
        
        return hash(tuple(key_components))
    
    def execute_rule(self, rule_result: Dict[str, Any], df: pd.DataFrame) -> pd.DataFrame:
        """
        Executa uma regra gerada anteriormente em um DataFrame
        
        Args:
            rule_result: Resultado da função generate_transformation_rule
            df: DataFrame para aplicar a transformação
            
        Returns:
            DataFrame transformado
        """
        
        if not rule_result['validation']['is_valid']:
            raise ValueError("Regra não é válida e não pode ser executada")
        
        try:
            # Preparar namespace de execução
            namespace = {
                'pd': pd,
                'np': np,
                'logging': logging
            }
            
            # Executar código
            exec(rule_result['generated_code'], namespace)
            
            # Aplicar transformação
            if 'transform_data' in namespace:
                return namespace['transform_data'](df)
            else:
                raise ValueError("Função transform_data não encontrada no código gerado")
                
        except Exception as e:
            logger.error(f"❌ Erro ao executar regra: {e}")
            raise
    
    def save_rule_library(self, file_path: str = "ai_rules_library.json"):
        """Salva biblioteca de regras para reutilização"""
        
        library = {
            'metadata': {
                'created_at': datetime.now().isoformat(),
                'total_rules': len(self.rule_cache),
                'execution_history': self.execution_history[-10:]  # Últimas 10 execuções
            },
            'rules': {}
        }
        
        for cache_key, rule_data in self.rule_cache.items():
            rule_id = f"rule_{len(library['rules']) + 1}"
            library['rules'][rule_id] = {
                'requirement': rule_data['requirement'],
                'code': rule_data['generated_code'],
                'validation': rule_data['validation'],
                'metadata': rule_data['metadata']
            }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(library, f, indent=2, ensure_ascii=False)
        
        logger.info(f"📚 Biblioteca de regras salva em: {file_path}")
    
    def load_rule_library(self, file_path: str = "ai_rules_library.json"):
        """Carrega biblioteca de regras salva"""
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                library = json.load(f)
            
            # Recriar cache
            self.rule_cache = {}
            for rule_id, rule_data in library.get('rules', {}).items():
                cache_key = self._generate_cache_key(rule_data['requirement'])
                self.rule_cache[cache_key] = rule_data
            
            logger.info(f"📚 Biblioteca carregada: {len(self.rule_cache)} regras")
            
        except FileNotFoundError:
            logger.warning(f"❌ Arquivo não encontrado: {file_path}")
        except Exception as e:
            logger.error(f"❌ Erro ao carregar biblioteca: {e}")


class PythonCodeValidator:
    """Validador de código Python para segurança"""
    
    FORBIDDEN_IMPORTS = [
        'os', 'sys', 'subprocess', 'eval', 'exec', 'open', 'file',
        'input', '__import__', 'globals', 'locals', 'vars'
    ]
    
    ALLOWED_IMPORTS = [
        'pandas', 'numpy', 'logging', 'datetime', 're', 'json', 'math'
    ]
    
    def validate_code(self, code: str) -> Dict[str, Any]:
        """Valida código Python gerado"""
        
        validation_result = {
            'is_valid': True,
            'errors': [],
            'warnings': [],
            'security_score': 100
        }
        
        try:
            # Verificar sintaxe
            compile(code, '<string>', 'exec')
            
        except SyntaxError as e:
            validation_result['is_valid'] = False
            validation_result['errors'].append(f"Erro de sintaxe: {e}")
            return validation_result
        
        # Verificar imports proibidos
        for forbidden in self.FORBIDDEN_IMPORTS:
            if forbidden in code:
                validation_result['is_valid'] = False
                validation_result['errors'].append(f"Import proibido detectado: {forbidden}")
                validation_result['security_score'] -= 20
        
        # Verificar se tem função principal
        if 'def transform_data' not in code:
            validation_result['warnings'].append("Função 'transform_data' não encontrada")
            validation_result['security_score'] -= 10
        
        # Verificar tratamento de erros
        if 'try:' not in code or 'except' not in code:
            validation_result['warnings'].append("Código sem tratamento de erros adequado")
            validation_result['security_score'] -= 5
        
        return validation_result


# Função de conveniência para uso rápido
def generate_etl_rule(requirement: str, 
                     data_context: Optional[Dict] = None,
                     claude_api_key: Optional[str] = None,
                     openai_api_key: Optional[str] = None) -> Dict[str, Any]:
    """
    Função de conveniência para gerar rapidamente uma regra ETL
    
    Args:
        requirement: Descrição da transformação em português
        data_context: Contexto dos dados (opcional)
        claude_api_key: Chave API Claude (opcional)
        openai_api_key: Chave API OpenAI (opcional)
        
    Returns:
        Resultado da geração da regra
    """
    
    generator = AIRuleGenerator(
        claude_api_key=claude_api_key,
        openai_api_key=openai_api_key
    )
    
    return generator.generate_transformation_rule(requirement, data_context)


# Exemplo de uso
if __name__ == "__main__":
    # Configurar logging
    logging.basicConfig(level=logging.INFO)
    
    # Criar gerador
    generator = AIRuleGenerator()
    
    # Exemplo de uso
    requirement = "Filtrar registros com valor maior que 1000 e criar coluna de categoria baseada no valor"
    
    data_context = {
        'columns': ['nome', 'email', 'valor', 'data_cadastro'],
        'dtypes': {'valor': 'float64'},
        'sample_data': "valor: [500, 1500, 2000, 800]"
    }
    
    try:
        result = generator.generate_transformation_rule(requirement, data_context)
        
        print("🎯 CRM - Regra ETL Gerada com Sucesso!")
        print(f"✅ Válida: {result['validation']['is_valid']}")
        print(f"⏱️ Tempo: {result['metadata']['generation_time']:.2f}s")
        print(f"📝 Linhas: {result['metadata']['code_lines']}")
        print("\n📋 Código Gerado:")
        print("-" * 50)
        print(result['generated_code'])
        
    except Exception as e:
        print(f"❌ Erro: {e}")