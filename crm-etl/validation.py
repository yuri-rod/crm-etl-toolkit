"""
Módulo de Validação Expandido
==============================
Integra validações brasileiras e genéricas para o pipeline ETL.
Adaptado para o contexto brasileiro com validações específicas.
"""

import re
import pandas as pd
from typing import Any, Dict, List, Optional, Tuple, Callable
from datetime import datetime
import numpy as np
from abc import ABC, abstractmethod
import sys
import os

# Adiciona o diretório pai ao path para importar validacao_brasileira
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from validacao_brasileira import (
    validar_cpf, validar_cnpj, validar_telefone_brasileiro,
    validar_cep, validar_email, validar_documento_por_tipo,
    formatar_cpf, formatar_cnpj, formatar_telefone, formatar_cep,
    extrair_estado_de_cidade_estado
)


class BaseValidator(ABC):
    """Classe base abstrata para validadores."""
    
    @abstractmethod
    def validate(self, value: Any) -> bool:
        """Valida um valor."""
        pass
    
    @abstractmethod
    def get_error_message(self, value: Any) -> str:
        """Retorna mensagem de erro para valor inválido."""
        pass


class CPFValidator(BaseValidator):
    """Validador de CPF brasileiro."""
    
    def validate(self, value: Any) -> bool:
        if pd.isna(value) or value == '':
            return False
        return validar_cpf(str(value))
    
    def get_error_message(self, value: Any) -> str:
        return f"CPF inválido: {value}"


class CNPJValidator(BaseValidator):
    """Validador de CNPJ brasileiro."""
    
    def validate(self, value: Any) -> bool:
        if pd.isna(value) or value == '':
            return False
        return validar_cnpj(str(value))
    
    def get_error_message(self, value: Any) -> str:
        return f"CNPJ inválido: {value}"


class EmailValidator(BaseValidator):
    """Validador de email."""
    
    def validate(self, value: Any) -> bool:
        if pd.isna(value) or value == '':
            return False
        return validar_email(str(value))
    
    def get_error_message(self, value: Any) -> str:
        return f"Email inválido: {value}"


class TelefoneValidator(BaseValidator):
    """Validador de telefone brasileiro."""
    
    def validate(self, value: Any) -> bool:
        if pd.isna(value) or value == '':
            return False
        return validar_telefone_brasileiro(str(value))
    
    def get_error_message(self, value: Any) -> str:
        return f"Telefone inválido: {value}"


class CEPValidator(BaseValidator):
    """Validador de CEP brasileiro."""
    
    def validate(self, value: Any) -> bool:
        if pd.isna(value) or value == '':
            return False
        return validar_cep(str(value))
    
    def get_error_message(self, value: Any) -> str:
        return f"CEP inválido: {value}"


class DateValidator(BaseValidator):
    """Validador de datas."""
    
    def __init__(self, format: str = "%d/%m/%Y"):
        self.format = format
    
    def validate(self, value: Any) -> bool:
        if pd.isna(value) or value == '':
            return False
        
        try:
            if isinstance(value, str):
                datetime.strptime(value, self.format)
            elif isinstance(value, (pd.Timestamp, datetime)):
                return True
            else:
                return False
            return True
        except:
            return False
    
    def get_error_message(self, value: Any) -> str:
        return f"Data inválida: {value} (formato esperado: {self.format})"


class RangeValidator(BaseValidator):
    """Validador de faixa numérica."""
    
    def __init__(self, min_value: Optional[float] = None, max_value: Optional[float] = None):
        self.min_value = min_value
        self.max_value = max_value
    
    def validate(self, value: Any) -> bool:
        if pd.isna(value):
            return False
        
        try:
            num_value = float(value)
            if self.min_value is not None and num_value < self.min_value:
                return False
            if self.max_value is not None and num_value > self.max_value:
                return False
            return True
        except:
            return False
    
    def get_error_message(self, value: Any) -> str:
        return f"Valor fora da faixa permitida: {value} (min: {self.min_value}, max: {self.max_value})"


class ValidationEngine:
    """Motor de validação principal."""
    
    def __init__(self):
        self.validators = {
            'cpf_brasileiro': CPFValidator(),
            'cnpj_brasileiro': CNPJValidator(),
            'email': EmailValidator(),
            'telefone_brasileiro': TelefoneValidator(),
            'cep_brasileiro': CEPValidator(),
            'date': DateValidator(),
            'date_br': DateValidator("%d/%m/%Y"),
            'date_us': DateValidator("%Y-%m-%d"),
        }
        self.validation_results = []
        
    def add_validator(self, name: str, validator: BaseValidator):
        """Adiciona um validador customizado."""
        self.validators[name] = validator
        
    def validate_field(self, value: Any, validator_name: str) -> Tuple[bool, Optional[str]]:
        """
        Valida um campo usando o validador especificado.
        
        Returns:
            Tuple[bool, Optional[str]]: (é_válido, mensagem_erro)
        """
        if validator_name not in self.validators:
            return False, f"Validador não encontrado: {validator_name}"
        
        validator = self.validators[validator_name]
        is_valid = validator.validate(value)
        error_msg = None if is_valid else validator.get_error_message(value)
        
        return is_valid, error_msg
    
    def validate_dataframe(self, df: pd.DataFrame, validations: List[Dict[str, Any]]) -> pd.DataFrame:
        """
        Valida um DataFrame completo baseado nas regras de validação.
        
        Args:
            df: DataFrame para validar
            validations: Lista de regras de validação
            
        Returns:
            DataFrame com colunas adicionais de validação
        """
        df_validated = df.copy()
        self.validation_results = []
        
        for validation in validations:
            field = validation['field']
            validator_name = validation['validator']
            required = validation.get('required', False)
            
            if field not in df_validated.columns:
                self.validation_results.append({
                    'field': field,
                    'status': 'missing',
                    'errors': 0,
                    'total': len(df_validated)
                })
                continue
            
            # Cria coluna de validação
            validation_col = f"{field}_valid"
            error_col = f"{field}_error"
            
            df_validated[validation_col] = True
            df_validated[error_col] = ""
            
            errors = 0
            for idx, value in df_validated[field].items():
                if pd.isna(value) or value == '':
                    if required:
                        df_validated.at[idx, validation_col] = False
                        df_validated.at[idx, error_col] = "Campo obrigatório vazio"
                        errors += 1
                else:
                    is_valid, error_msg = self.validate_field(value, validator_name)
                    df_validated.at[idx, validation_col] = is_valid
                    if not is_valid:
                        df_validated.at[idx, error_col] = error_msg
                        errors += 1
            
            self.validation_results.append({
                'field': field,
                'validator': validator_name,
                'status': 'validated',
                'errors': errors,
                'total': len(df_validated),
                'error_rate': errors / len(df_validated) if len(df_validated) > 0 else 0
            })
        
        return df_validated
    
    def get_validation_summary(self) -> Dict[str, Any]:
        """Retorna um resumo das validações realizadas."""
        total_errors = sum(r['errors'] for r in self.validation_results)
        total_validations = sum(r['total'] for r in self.validation_results)
        
        return {
            'total_fields_validated': len(self.validation_results),
            'total_errors': total_errors,
            'total_validations': total_validations,
            'overall_error_rate': total_errors / total_validations if total_validations > 0 else 0,
            'field_details': self.validation_results
        }


class DataQualityChecker:
    """Verificador de qualidade de dados."""
    
    def __init__(self):
        self.quality_metrics = {}
        
    def check_duplicates(self, df: pd.DataFrame, key_fields: List[str]) -> Dict[str, Any]:
        """Verifica duplicatas no DataFrame."""
        duplicates = df.duplicated(subset=key_fields, keep=False)
        duplicate_count = duplicates.sum()
        
        duplicate_details = []
        if duplicate_count > 0:
            for keys in df[duplicates][key_fields].drop_duplicates().values:
                mask = True
                for i, field in enumerate(key_fields):
                    mask = mask & (df[field] == keys[i])
                count = mask.sum()
                duplicate_details.append({
                    'keys': dict(zip(key_fields, keys)),
                    'count': int(count)
                })
        
        return {
            'has_duplicates': duplicate_count > 0,
            'duplicate_count': int(duplicate_count),
            'duplicate_percentage': duplicate_count / len(df) * 100 if len(df) > 0 else 0,
            'details': duplicate_details[:10]  # Limita a 10 exemplos
        }
    
    def check_completeness(self, df: pd.DataFrame, required_fields: List[str]) -> Dict[str, Any]:
        """Verifica completude dos dados."""
        completeness = {}
        
        for field in required_fields:
            if field in df.columns:
                non_null = df[field].notna() & (df[field] != '')
                completeness[field] = {
                    'complete_count': int(non_null.sum()),
                    'missing_count': int((~non_null).sum()),
                    'completeness_rate': float(non_null.sum() / len(df) * 100) if len(df) > 0 else 0
                }
        
        overall_completeness = np.mean([v['completeness_rate'] for v in completeness.values()])
        
        return {
            'overall_completeness': float(overall_completeness),
            'field_completeness': completeness
        }
    
    def check_consistency(self, df: pd.DataFrame, rules: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Verifica consistência dos dados baseado em regras."""
        consistency_results = []
        
        for rule in rules:
            fields = rule['fields']
            rule_type = rule['rule']
            
            if rule_type == 'not_both_present':
                # Verifica se ambos os campos não estão preenchidos ao mesmo tempo
                mask = True
                for field in fields:
                    if field in df.columns:
                        mask = mask & df[field].notna() & (df[field] != '')
                
                violations = mask.sum()
                consistency_results.append({
                    'rule': rule_type,
                    'fields': fields,
                    'violations': int(violations),
                    'violation_rate': float(violations / len(df) * 100) if len(df) > 0 else 0
                })
        
        return {
            'total_violations': sum(r['violations'] for r in consistency_results),
            'rules_checked': len(consistency_results),
            'details': consistency_results
        }
    
    def generate_quality_report(self, df: pd.DataFrame, config: Dict[str, Any]) -> Dict[str, Any]:
        """Gera relatório completo de qualidade de dados."""
        report = {
            'timestamp': datetime.now().isoformat(),
            'total_records': len(df),
            'total_columns': len(df.columns),
            'checks': {}
        }
        
        # Verifica duplicatas
        if 'duplicate_detection' in [c['type'] for c in config.get('checks', [])]:
            check = next(c for c in config['checks'] if c['type'] == 'duplicate_detection')
            report['checks']['duplicates'] = self.check_duplicates(df, check['key_fields'])
        
        # Verifica completude
        if 'completeness_check' in [c['type'] for c in config.get('checks', [])]:
            check = next(c for c in config['checks'] if c['type'] == 'completeness_check')
            report['checks']['completeness'] = self.check_completeness(df, check['required_fields'])
        
        # Verifica consistência
        if 'consistency_check' in [c['type'] for c in config.get('checks', [])]:
            check = next(c for c in config['checks'] if c['type'] == 'consistency_check')
            report['checks']['consistency'] = self.check_consistency(df, check['rules'])
        
        # Calcula score geral de qualidade
        quality_scores = []
        
        if 'duplicates' in report['checks']:
            dup_score = 100 - report['checks']['duplicates']['duplicate_percentage']
            quality_scores.append(dup_score)
        
        if 'completeness' in report['checks']:
            quality_scores.append(report['checks']['completeness']['overall_completeness'])
        
        if 'consistency' in report['checks']:
            violations = report['checks']['consistency']['total_violations']
            cons_score = 100 - (violations / len(df) * 100) if len(df) > 0 else 100
            quality_scores.append(cons_score)
        
        report['overall_quality_score'] = float(np.mean(quality_scores)) if quality_scores else 0
        
        return report


# Funções auxiliares para normalização de texto
def remove_extra_spaces(text: str) -> str:
    """Remove espaços extras."""
    if pd.isna(text):
        return text
    return ' '.join(str(text).split())


def capitalize_names(text: str) -> str:
    """Capitaliza nomes próprios corretamente."""
    if pd.isna(text):
        return text
    
    prepositions = ['de', 'da', 'do', 'das', 'dos', 'e']
    words = str(text).lower().split()
    result = []
    
    for i, word in enumerate(words):
        if i == 0 or word not in prepositions:
            result.append(word.capitalize())
        else:
            result.append(word)
    
    return ' '.join(result)


def remove_special_chars(text: str) -> str:
    """Remove caracteres especiais mantendo acentos."""
    if pd.isna(text):
        return text
    
    # Mantém letras, números, espaços e acentos comuns
    return re.sub(r'[^a-zA-ZÀ-ÿ0-9\s]', '', str(text))


def capitalize_words(text: str) -> str:
    """Capitaliza todas as palavras."""
    if pd.isna(text):
        return text
    return str(text).title()


# Exemplo de uso
if __name__ == "__main__":
    # Teste do motor de validação
    engine = ValidationEngine()
    
    # Dados de teste
    test_data = pd.DataFrame({
        'cpf': ['111.444.777-35', '123.456.789-00', None],
        'email': ['teste@email.com', 'invalido@', 'outro@teste.com'],
        'telefone': ['11987654321', '1133334444', '999']
    })
    
    # Regras de validação
    validations = [
        {'field': 'cpf', 'validator': 'cpf_brasileiro', 'required': True},
        {'field': 'email', 'validator': 'email', 'required': True},
        {'field': 'telefone', 'validator': 'telefone_brasileiro', 'required': False}
    ]
    
    # Valida dados
    validated_df = engine.validate_dataframe(test_data, validations)
    summary = engine.get_validation_summary()
    
    print("Resumo da Validação:")
    print(f"Total de erros: {summary['total_errors']}")
    print(f"Taxa de erro geral: {summary['overall_error_rate']:.2%}")
    
    # Teste do verificador de qualidade
    checker = DataQualityChecker()
    quality_config = {
        'checks': [
            {'type': 'duplicate_detection', 'key_fields': ['cpf']},
            {'type': 'completeness_check', 'required_fields': ['cpf', 'email']},
            {'type': 'consistency_check', 'rules': []}
        ]
    }
    
    quality_report = checker.generate_quality_report(validated_df, quality_config)
    print(f"\nScore de Qualidade Geral: {quality_report['overall_quality_score']:.2f}%")
