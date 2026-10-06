#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Detector de Schema Drift Inteligente
CRM ETL

Sistema que detecta automaticamente mudanças na estrutura dos dados (schema drift)
e sugere adaptações necessárias nas pipelines ETL.
"""

import os
import json
import logging
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, asdict
from pathlib import Path
import pandas as pd
import numpy as np

# Importar acelerador GPU
try:
    from gpu_accelerator import GPUAccelerator, GPUAccelerationConfig, GPUDataProcessor
    GPU_AVAILABLE = True
except ImportError:
    GPU_AVAILABLE = False
    logging.info("GPU Accelerator não disponível para Schema Drift Detection")

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class ColumnSchema:
    """Esquema de uma coluna"""
    name: str
    dtype: str
    nullable: bool
    unique_count: int
    sample_values: List[Any]
    min_value: Optional[Any] = None
    max_value: Optional[Any] = None
    avg_length: Optional[float] = None
    pattern: Optional[str] = None

@dataclass
class DatasetSchema:
    """Esquema completo de um dataset"""
    source_name: str
    timestamp: datetime
    total_columns: int
    total_rows: int
    columns: Dict[str, ColumnSchema]
    schema_hash: str
    data_quality_score: float

@dataclass
class SchemaChange:
    """Representação de uma mudança de schema"""
    change_type: str  # added, removed, modified, type_changed
    column_name: str
    old_value: Optional[Any]
    new_value: Optional[Any]
    impact_level: str  # low, medium, high, critical
    description: str
    suggested_action: str
    auto_fixable: bool

@dataclass
class DriftReport:
    """Relatório de drift de schema"""
    source_name: str
    timestamp: datetime
    previous_schema: DatasetSchema
    current_schema: DatasetSchema
    changes: List[SchemaChange]
    drift_score: float
    is_breaking: bool
    recommended_actions: List[str]

class SchemaAnalyzer:
    """Analisador de esquema de dados (com aceleração GPU)"""
    
    def __init__(self, enable_gpu: bool = True):
        """
        Inicializa analisador com suporte opcional a GPU
        
        Args:
            enable_gpu: Habilitar aceleração GPU para datasets grandes
        """
        self.gpu_enabled = enable_gpu and GPU_AVAILABLE
        self.gpu_processor = None
        
        if self.gpu_enabled:
            try:
                gpu_config = GPUAccelerationConfig(
                    enabled=True,
                    prefer_gpu=True,
                    memory_fraction=0.4,  # Usar mais memória para análise de schema
                    fallback_to_cpu=True
                )
                gpu_accelerator = GPUAccelerator(gpu_config)
                self.gpu_processor = GPUDataProcessor(gpu_accelerator)
                logger.info("Schema Analyzer com aceleração GPU habilitado")
            except Exception as e:
                logger.warning(f"Falha ao inicializar GPU para schema analysis: {e}")
                self.gpu_enabled = False
    
    def analyze_dataframe(self, df: pd.DataFrame, source_name: str) -> DatasetSchema:
        """Analisa DataFrame e extrai esquema"""
        
        # Para datasets grandes, usar GPU se disponível
        if self.gpu_enabled and len(df) > 100000:
            logger.info(f"Analisando schema de dataset grande ({len(df)} registros) com GPU")
            df_processed = self._preprocess_large_dataset(df)
        else:
            df_processed = df
        
        columns = {}
        
        for col in df_processed.columns:
            col_data = df_processed[col]
            
            # Análise básica
            dtype = str(col_data.dtype)
            nullable = col_data.isnull().any()
            unique_count = col_data.nunique()
            sample_values = col_data.dropna().head(5).tolist()
            
            # Análise específica por tipo
            min_value = None
            max_value = None
            avg_length = None
            pattern = None
            
            if pd.api.types.is_numeric_dtype(col_data):
                min_value = col_data.min() if not col_data.empty else None
                max_value = col_data.max() if not col_data.empty else None
            elif pd.api.types.is_string_dtype(col_data) or dtype == 'object':
                if not col_data.empty:
                    lengths = col_data.astype(str).str.len()
                    avg_length = lengths.mean()
                    pattern = self._detect_pattern(col_data.dropna().head(20))
            
            columns[col] = ColumnSchema(
                name=col,
                dtype=dtype,
                nullable=nullable,
                unique_count=unique_count,
                sample_values=sample_values,
                min_value=min_value,
                max_value=max_value,
                avg_length=avg_length,
                pattern=pattern
            )
        
        # Calcular hash do schema
        schema_str = json.dumps({
            col: {
                'dtype': schema.dtype,
                'nullable': schema.nullable
            }
            for col, schema in columns.items()
        }, sort_keys=True)
        
        schema_hash = hashlib.md5(schema_str.encode()).hexdigest()
        
        # Calcular score de qualidade
        data_quality_score = self._calculate_data_quality_score(df, columns)
        
        return DatasetSchema(
            source_name=source_name,
            timestamp=datetime.now(),
            total_columns=len(df.columns),
            total_rows=len(df),
            columns=columns,
            schema_hash=schema_hash,
            data_quality_score=data_quality_score
        )
    
    def _preprocess_large_dataset(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Pré-processa dataset grande usando GPU para otimizar análise de schema
        
        Args:
            df: DataFrame original
            
        Returns:
            DataFrame otimizado para análise
        """
        
        if not self.gpu_processor:
            return df
        
        try:
            # Usar GPU para operações de preparação
            operations = ['fillna', 'deduplicate']  # Operações que ajudam na análise
            
            # Amostragem para análise de schema (para datasets muito grandes)
            if len(df) > 1000000:  # 1M+ registros
                logger.info("Usando amostragem estratificada para dataset muito grande")
                # Pegar amostra representativa
                sample_size = min(500000, len(df))
                df_sample = df.sample(n=sample_size, random_state=42)
            else:
                df_sample = df
            
            # Processar com GPU
            df_processed = self.gpu_processor.process_large_dataframe(df_sample, operations)
            
            logger.info(f"Dataset pré-processado com GPU: {len(df_processed)} registros")
            return df_processed
            
        except Exception as e:
            logger.warning(f"Erro no pré-processamento GPU: {e}")
            return df
    
    def _detect_pattern(self, series: pd.Series) -> Optional[str]:
        """Detecta padrões comuns em dados textuais"""
        
        if series.empty:
            return None
        
        sample_values = series.head(10).tolist()
        
        # Padrões comuns
        patterns = {
            'email': r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
            'phone': r'^\+?[\d\s\-\(\)]{10,}$',
            'cpf': r'^\d{3}\.\d{3}\.\d{3}-\d{2}$|^\d{11}$',
            'cnpj': r'^\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}$|^\d{14}$',
            'cep': r'^\d{5}-?\d{3}$',
            'date_br': r'^\d{1,2}/\d{1,2}/\d{4}$',
            'numeric': r'^\d+$',
            'decimal': r'^\d+[.,]\d+$'
        }
        
        import re
        
        for pattern_name, pattern_regex in patterns.items():
            matches = sum(1 for val in sample_values if re.match(pattern_regex, str(val)))
            if matches / len(sample_values) > 0.7:  # 70% dos valores seguem o padrão
                return pattern_name
        
        return None
    
    def _calculate_data_quality_score(self, df: pd.DataFrame, columns: Dict[str, ColumnSchema]) -> float:
        """Calcula score de qualidade dos dados"""
        
        if df.empty:
            return 0.0
        
        quality_factors = []
        
        # Fator 1: Completude (% de valores não nulos)
        completeness = 1 - (df.isnull().sum().sum() / (len(df) * len(df.columns)))
        quality_factors.append(completeness)
        
        # Fator 2: Consistência de tipos
        type_consistency = 1.0  # Assumir que pandas já fez a conversão correta
        quality_factors.append(type_consistency)
        
        # Fator 3: Unicidade (para colunas que parecem ser IDs)
        uniqueness_scores = []
        for col, schema in columns.items():
            if 'id' in col.lower() or schema.unique_count == len(df):
                uniqueness = schema.unique_count / len(df) if len(df) > 0 else 1.0
                uniqueness_scores.append(uniqueness)
        
        if uniqueness_scores:
            avg_uniqueness = np.mean(uniqueness_scores)
            quality_factors.append(avg_uniqueness)
        
        # Fator 4: Conformidade com padrões
        pattern_conformity_scores = []
        for col, schema in columns.items():
            if schema.pattern:
                # Se detectou um padrão, assume boa conformidade
                pattern_conformity_scores.append(0.9)
        
        if pattern_conformity_scores:
            avg_pattern_conformity = np.mean(pattern_conformity_scores)
            quality_factors.append(avg_pattern_conformity)
        
        return np.mean(quality_factors)

class SchemaDriftDetector:
    """Detector principal de schema drift (com aceleração GPU)"""
    
    def __init__(self, storage_path: str = "schema_history", enable_gpu: bool = True):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(exist_ok=True)
        self.analyzer = SchemaAnalyzer(enable_gpu=enable_gpu)
    
    def detect_drift(self, df: pd.DataFrame, source_name: str) -> Optional[DriftReport]:
        """Detecta drift comparando com schema anterior"""
        
        # Analisar schema atual
        current_schema = self.analyzer.analyze_dataframe(df, source_name)
        
        # Buscar schema anterior
        previous_schema = self._load_latest_schema(source_name)
        
        if not previous_schema:
            # Primeira execução - salvar schema base
            self._save_schema(current_schema)
            logger.info(f"Schema base salvo para {source_name}")
            return None
        
        # Comparar schemas
        changes = self._compare_schemas(previous_schema, current_schema)
        
        if not changes:
            # Nenhuma mudança detectada
            return None
        
        # Calcular score de drift
        drift_score = self._calculate_drift_score(changes)
        
        # Verificar se é breaking change
        is_breaking = any(change.impact_level in ['high', 'critical'] for change in changes)
        
        # Gerar recomendações
        recommended_actions = self._generate_recommendations(changes)
        
        # Criar relatório
        drift_report = DriftReport(
            source_name=source_name,
            timestamp=datetime.now(),
            previous_schema=previous_schema,
            current_schema=current_schema,
            changes=changes,
            drift_score=drift_score,
            is_breaking=is_breaking,
            recommended_actions=recommended_actions
        )
        
        # Salvar novo schema
        self._save_schema(current_schema)
        
        # Salvar relatório de drift
        self._save_drift_report(drift_report)
        
        return drift_report
    
    def _compare_schemas(self, old_schema: DatasetSchema, new_schema: DatasetSchema) -> List[SchemaChange]:
        """Compara dois schemas e identifica mudanças"""
        
        changes = []
        
        old_columns = set(old_schema.columns.keys())
        new_columns = set(new_schema.columns.keys())
        
        # Colunas removidas
        removed_columns = old_columns - new_columns
        for col in removed_columns:
            changes.append(SchemaChange(
                change_type="removed",
                column_name=col,
                old_value=old_schema.columns[col].dtype,
                new_value=None,
                impact_level="high",
                description=f"Coluna '{col}' foi removida",
                suggested_action=f"Verificar se '{col}' ainda é necessária ou foi renomeada",
                auto_fixable=False
            ))
        
        # Colunas adicionadas
        added_columns = new_columns - old_columns
        for col in added_columns:
            impact = "medium" if new_schema.columns[col].nullable else "high"
            changes.append(SchemaChange(
                change_type="added",
                column_name=col,
                old_value=None,
                new_value=new_schema.columns[col].dtype,
                impact_level=impact,
                description=f"Nova coluna '{col}' adicionada",
                suggested_action=f"Atualizar pipeline para processar coluna '{col}'",
                auto_fixable=True
            ))
        
        # Colunas modificadas
        common_columns = old_columns & new_columns
        for col in common_columns:
            old_col = old_schema.columns[col]
            new_col = new_schema.columns[col]
            
            # Mudança de tipo
            if old_col.dtype != new_col.dtype:
                impact = self._assess_type_change_impact(old_col.dtype, new_col.dtype)
                changes.append(SchemaChange(
                    change_type="type_changed",
                    column_name=col,
                    old_value=old_col.dtype,
                    new_value=new_col.dtype,
                    impact_level=impact,
                    description=f"Tipo da coluna '{col}' mudou de {old_col.dtype} para {new_col.dtype}",
                    suggested_action=f"Atualizar transformações para tipo {new_col.dtype}",
                    auto_fixable=self._is_type_change_auto_fixable(old_col.dtype, new_col.dtype)
                ))
            
            # Mudança de nulabilidade
            if old_col.nullable != new_col.nullable:
                if new_col.nullable and not old_col.nullable:
                    # Coluna passou a aceitar nulos - baixo impacto
                    changes.append(SchemaChange(
                        change_type="modified",
                        column_name=col,
                        old_value=f"nullable={old_col.nullable}",
                        new_value=f"nullable={new_col.nullable}",
                        impact_level="low",
                        description=f"Coluna '{col}' agora aceita valores nulos",
                        suggested_action="Adicionar validação para valores nulos se necessário",
                        auto_fixable=True
                    ))
                else:
                    # Coluna não aceita mais nulos - alto impacto
                    changes.append(SchemaChange(
                        change_type="modified",
                        column_name=col,
                        old_value=f"nullable={old_col.nullable}",
                        new_value=f"nullable={new_col.nullable}",
                        impact_level="high",
                        description=f"Coluna '{col}' não aceita mais valores nulos",
                        suggested_action="Implementar lógica para tratar valores nulos",
                        auto_fixable=False
                    ))
            
            # Mudança significativa na quantidade de valores únicos
            if old_col.unique_count > 0 and new_col.unique_count > 0:
                ratio = new_col.unique_count / old_col.unique_count
                if ratio < 0.5 or ratio > 2.0:  # Mudança de mais de 50%
                    changes.append(SchemaChange(
                        change_type="modified",
                        column_name=col,
                        old_value=old_col.unique_count,
                        new_value=new_col.unique_count,
                        impact_level="medium",
                        description=f"Cardinalidade da coluna '{col}' mudou significativamente",
                        suggested_action="Verificar se mudança na cardinalidade afeta transformações",
                        auto_fixable=True
                    ))
        
        return changes
    
    def _assess_type_change_impact(self, old_type: str, new_type: str) -> str:
        """Avalia o impacto de uma mudança de tipo"""
        
        # Mapeamento de compatibilidade de tipos
        compatible_changes = [
            ('int', 'float'),
            ('int32', 'int64'),
            ('float32', 'float64'),
            ('object', 'string')
        ]
        
        breaking_changes = [
            ('float', 'int'),
            ('object', 'datetime64'),
            ('string', 'int'),
            ('string', 'float')
        ]
        
        change_pair = (old_type.lower(), new_type.lower())
        
        if any(old in old_type.lower() and new in new_type.lower() for old, new in compatible_changes):
            return "low"
        elif any(old in old_type.lower() and new in new_type.lower() for old, new in breaking_changes):
            return "critical"
        else:
            return "medium"
    
    def _is_type_change_auto_fixable(self, old_type: str, new_type: str) -> bool:
        """Verifica se mudança de tipo pode ser corrigida automaticamente"""
        
        auto_fixable_changes = [
            ('int', 'float'),
            ('int32', 'int64'),
            ('float32', 'float64'),
            ('object', 'string')
        ]
        
        return any(old in old_type.lower() and new in new_type.lower() for old, new in auto_fixable_changes)
    
    def _calculate_drift_score(self, changes: List[SchemaChange]) -> float:
        """Calcula score de drift (0-1, onde 1 é máximo drift)"""
        
        if not changes:
            return 0.0
        
        impact_weights = {
            'low': 0.1,
            'medium': 0.3,
            'high': 0.7,
            'critical': 1.0
        }
        
        total_impact = sum(impact_weights.get(change.impact_level, 0.5) for change in changes)
        max_possible_impact = len(changes) * 1.0
        
        return min(total_impact / max_possible_impact, 1.0) if max_possible_impact > 0 else 0.0
    
    def _generate_recommendations(self, changes: List[SchemaChange]) -> List[str]:
        """Gera recomendações baseadas nas mudanças"""
        
        recommendations = []
        
        # Agrupar mudanças por tipo
        by_type = {}
        for change in changes:
            if change.change_type not in by_type:
                by_type[change.change_type] = []
            by_type[change.change_type].append(change)
        
        # Recomendações específicas por tipo
        if 'removed' in by_type:
            removed_count = len(by_type['removed'])
            recommendations.append(f"Investigar remoção de {removed_count} coluna(s) - pode quebrar pipeline")
        
        if 'added' in by_type:
            added_count = len(by_type['added'])
            auto_fixable = sum(1 for c in by_type['added'] if c.auto_fixable)
            recommendations.append(f"Atualizar pipeline para {added_count} nova(s) coluna(s)")
            if auto_fixable > 0:
                recommendations.append(f"{auto_fixable} mudança(s) podem ser corrigidas automaticamente")
        
        if 'type_changed' in by_type:
            type_changes = len(by_type['type_changed'])
            critical_changes = sum(1 for c in by_type['type_changed'] if c.impact_level == 'critical')
            recommendations.append(f"Revisar {type_changes} mudança(s) de tipo")
            if critical_changes > 0:
                recommendations.append(f"ATENÇÃO: {critical_changes} mudança(s) crítica(s) de tipo detectada(s)")
        
        # Recomendações gerais
        high_impact_changes = sum(1 for c in changes if c.impact_level in ['high', 'critical'])
        if high_impact_changes > 0:
            recommendations.append("Testar pipeline com novos dados antes de produção")
            recommendations.append("Considerar implementar versionamento de schema")
        
        auto_fixable_changes = sum(1 for c in changes if c.auto_fixable)
        if auto_fixable_changes > 0:
            recommendations.append(f"Aplicar correções automáticas para {auto_fixable_changes} mudança(s)")
        
        return recommendations
    
    def _save_schema(self, schema: DatasetSchema):
        """Salva schema em arquivo"""
        
        filename = f"{schema.source_name}_{schema.timestamp.strftime('%Y%m%d_%H%M%S')}.json"
        filepath = self.storage_path / filename
        
        # Converter para dict serializable
        schema_dict = asdict(schema)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(schema_dict, f, indent=2, ensure_ascii=False, default=str)
        
        logger.info(f"Schema salvo: {filepath}")
    
    def _load_latest_schema(self, source_name: str) -> Optional[DatasetSchema]:
        """Carrega o schema mais recente para uma fonte"""
        
        # Buscar arquivos de schema para a fonte
        pattern = f"{source_name}_*.json"
        schema_files = list(self.storage_path.glob(pattern))
        
        if not schema_files:
            return None
        
        # Ordenar por timestamp (mais recente primeiro)
        schema_files.sort(reverse=True)
        latest_file = schema_files[0]
        
        try:
            with open(latest_file, 'r', encoding='utf-8') as f:
                schema_dict = json.load(f)
            
            # Converter de volta para objetos
            columns = {}
            for col_name, col_data in schema_dict['columns'].items():
                columns[col_name] = ColumnSchema(**col_data)
            
            schema_dict['columns'] = columns
            schema_dict['timestamp'] = datetime.fromisoformat(schema_dict['timestamp'])
            
            return DatasetSchema(**schema_dict)
            
        except Exception as e:
            logger.error(f"Erro ao carregar schema de {latest_file}: {e}")
            return None
    
    def _save_drift_report(self, report: DriftReport):
        """Salva relatório de drift"""
        
        reports_dir = self.storage_path / "drift_reports"
        reports_dir.mkdir(exist_ok=True)
        
        filename = f"drift_{report.source_name}_{report.timestamp.strftime('%Y%m%d_%H%M%S')}.json"
        filepath = reports_dir / filename
        
        # Converter para dict serializable
        report_dict = asdict(report)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report_dict, f, indent=2, ensure_ascii=False, default=str)
        
        logger.info(f"Relatório de drift salvo: {filepath}")
    
    def get_drift_history(self, source_name: str, days: int = 30) -> List[DriftReport]:
        """Obtém histórico de drift reports"""
        
        reports_dir = self.storage_path / "drift_reports"
        if not reports_dir.exists():
            return []
        
        # Buscar reports da fonte
        pattern = f"drift_{source_name}_*.json"
        report_files = list(reports_dir.glob(pattern))
        
        # Filtrar por data
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_reports = []
        
        for report_file in report_files:
            try:
                with open(report_file, 'r', encoding='utf-8') as f:
                    report_dict = json.load(f)
                
                report_timestamp = datetime.fromisoformat(report_dict['timestamp'])
                if report_timestamp >= cutoff_date:
                    # Reconstruir objetos (versão simplificada para histórico)
                    recent_reports.append(report_dict)
                    
            except Exception as e:
                logger.error(f"Erro ao ler report {report_file}: {e}")
        
        return sorted(recent_reports, key=lambda x: x['timestamp'], reverse=True)


def demo_schema_drift_detection():
    """Demonstração do detector de schema drift (com aceleração GPU)"""
    
    print("🔍 DEMO: Detector de Schema Drift com GPU")
    print("=" * 55)
    
    # Inicializar detector com GPU
    detector = SchemaDriftDetector("demo_schema_history", enable_gpu=True)
    
    # Mostrar status GPU
    if detector.analyzer.gpu_enabled:
        print("🚀 Aceleração GPU habilitada para análise de schema")
    else:
        print("💻 Usando processamento CPU padrão")
    
    print("📊 Criando dataset inicial...")
    
    # Dataset inicial
    df_inicial = pd.DataFrame({
        'id': [1, 2, 3, 4, 5],
        'nome': ['João Silva', 'Maria Santos', 'Pedro Costa', 'Ana Lima', 'Carlos Souza'],
        'email': ['joao@test.com', 'maria@test.com', 'pedro@test.com', 'ana@test.com', 'carlos@test.com'],
        'idade': [25, 30, 35, 28, 42],
        'salario': [5000.0, 6000.0, 7500.0, 5500.0, 8000.0],
        'ativo': [True, True, False, True, True]
    })
    
    print("Dataset inicial:")
    print(df_inicial.dtypes)
    print()
    
    # Primeira execução (criar baseline)
    drift_report = detector.detect_drift(df_inicial, "funcionarios")
    print(f"Primeira execução: {drift_report}")
    print()
    
    # Simular passagem de tempo
    import time
    time.sleep(1)
    
    print("📊 Simulando mudanças no dataset...")
    
    # Dataset com mudanças
    df_modificado = pd.DataFrame({
        'id': [1, 2, 3, 4, 5, 6],  # Nova linha
        'nome': ['João Silva', 'Maria Santos', 'Pedro Costa', 'Ana Lima', 'Carlos Souza', 'Lucia Ferreira'],
        'email': ['joao@test.com', 'maria@test.com', 'pedro@test.com', 'ana@test.com', 'carlos@test.com', 'lucia@test.com'],
        'idade': ['25', '30', '35', '28', '42', '29'],  # Mudou de int para string!
        'salario': [5000.0, 6000.0, 7500.0, 5500.0, 8000.0, 5800.0],
        'ativo': [True, True, False, True, True, True],
        'departamento': ['TI', 'RH', 'TI', 'Vendas', 'TI', 'RH']  # Nova coluna!
        # Coluna 'salario' continua igual
        # Note que não removemos nenhuma coluna, mas mudamos o tipo de 'idade'
    })
    
    print("Dataset modificado:")
    print(df_modificado.dtypes)
    print()
    
    # Segunda execução (detectar drift)
    drift_report = detector.detect_drift(df_modificado, "funcionarios")
    
    if drift_report:
        print("🚨 SCHEMA DRIFT DETECTADO!")
        print(f"Score de drift: {drift_report.drift_score:.2f}")
        print(f"É breaking change: {drift_report.is_breaking}")
        print()
        
        print("📋 Mudanças detectadas:")
        for i, change in enumerate(drift_report.changes, 1):
            print(f"{i}. {change.change_type.upper()}: {change.description}")
            print(f"   Impacto: {change.impact_level}")
            print(f"   Ação sugerida: {change.suggested_action}")
            print(f"   Auto-corrigível: {change.auto_fixable}")
            print()
        
        print("💡 Recomendações:")
        for i, rec in enumerate(drift_report.recommended_actions, 1):
            print(f"{i}. {rec}")
        
    else:
        print("✅ Nenhum drift detectado")
    
    print()
    
    # Simular dataset com problemas críticos
    print("📊 Simulando mudanças críticas...")
    
    df_critico = pd.DataFrame({
        'id': [1, 2, 3],
        'nome_completo': ['João Silva', 'Maria Santos', 'Pedro Costa'],  # 'nome' foi renomeado!
        'email': ['joao@test.com', 'maria@test.com', 'pedro@test.com'],
        # 'idade' foi removida!
        'salario_bruto': [5000.0, 6000.0, 7500.0],  # 'salario' foi renomeado!
        # 'ativo' foi removido!
        'departamento': ['TI', 'RH', 'TI'],
        'data_admissao': ['2023-01-15', '2022-06-10', '2021-03-20']  # Nova coluna
    })
    
    time.sleep(1)
    drift_report = detector.detect_drift(df_critico, "funcionarios")
    
    if drift_report:
        print("🚨 MUDANÇAS CRÍTICAS DETECTADAS!")
        print(f"Score de drift: {drift_report.drift_score:.2f}")
        print(f"É breaking change: {drift_report.is_breaking}")
        print()
        
        critical_changes = [c for c in drift_report.changes if c.impact_level == 'critical']
        high_changes = [c for c in drift_report.changes if c.impact_level == 'high']
        
        if critical_changes:
            print("💥 Mudanças CRÍTICAS:")
            for change in critical_changes:
                print(f"  - {change.description}")
        
        if high_changes:
            print("⚠️ Mudanças de ALTO IMPACTO:")
            for change in high_changes:
                print(f"  - {change.description}")
    
    # Mostrar histórico
    print("\n📈 Histórico de drift:")
    history = detector.get_drift_history("funcionarios", days=1)
    for i, report in enumerate(history, 1):
        print(f"{i}. {report['timestamp']}: {len(report['changes'])} mudanças, score: {report['drift_score']:.2f}")
    
    print("\n✅ Demo concluída!")


if __name__ == "__main__":
    demo_schema_drift_detection()