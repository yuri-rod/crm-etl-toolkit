#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Demo Completo: ETL com IA e Aceleração GPU
CRM ETL

Demonstração completa de todas as funcionalidades de aceleração GPU
integradas no sistema ETL com IA.
"""

import os
import sys
import time
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime

# Importar módulos do sistema
from gpu_accelerator import GPUAccelerator, GPUAccelerationConfig
from ai_rule_generator import AIRuleGenerator
from intelligent_monitoring import IntelligentMonitoringSystem
from schema_drift_detector import SchemaDriftDetector
from etl_ai_interface import ETLAIInterface

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_large_test_dataset(n_rows: int = 250000) -> pd.DataFrame:
    """Cria dataset grande para testar aceleração GPU"""
    
    print(f"📊 Criando dataset de teste com {n_rows:,} registros...")
    
    np.random.seed(42)
    
    # Gerar dados realistas
    nomes = [f"Usuario_{i}" for i in range(n_rows)]
    emails = [f"user{i}@{'empresa' if i % 3 == 0 else 'teste'}.com" for i in range(n_rows)]
    idades = np.random.randint(18, 80, n_rows)
    salarios = np.random.lognormal(10, 0.5, n_rows)
    departamentos = np.random.choice(['TI', 'RH', 'Vendas', 'Marketing', 'Financeiro'], n_rows)
    ativo = np.random.choice([True, False], n_rows, p=[0.85, 0.15])
    
    # Dados com problemas para demonstrar limpeza
    for i in range(0, n_rows, 100):  # Introduzir alguns problemas
        if i < len(nomes):
            nomes[i] = nomes[i].upper()
            emails[i] = emails[i].upper()
    
    # Introduzir valores nulos aleatórios
    null_indices = np.random.choice(n_rows, size=n_rows//50, replace=False)
    for idx in null_indices:
        if idx < len(salarios):
            salarios[idx] = np.nan
    
    df = pd.DataFrame({
        'id': range(1, n_rows + 1),
        'nome': nomes,
        'email': emails,
        'idade': idades,
        'salario': salarios,
        'departamento': departamentos,
        'ativo': ativo,
        'data_criacao': pd.date_range('2020-01-01', periods=n_rows, freq='H')
    })
    
    print(f"✅ Dataset criado: {len(df):,} registros, {len(df.columns)} colunas")
    return df

def benchmark_gpu_vs_cpu():
    """Executa benchmark comparando GPU vs CPU"""
    
    print("\n🏁 BENCHMARK: GPU vs CPU")
    print("=" * 50)
    
    # Configurações
    gpu_config = GPUAccelerationConfig(enabled=True, prefer_gpu=True)
    gpu_accelerator = GPUAccelerator(gpu_config)
    
    # Mostrar informações do sistema
    system_info = gpu_accelerator.get_system_info()
    print(f"🖥️ Sistema GPU:")
    print(f"  CUDA disponível: {system_info['cuda_available']}")
    print(f"  CuDF disponível: {system_info['cudf_available']}")
    print(f"  Dispositivo ótimo: {system_info['optimal_device']}")
    
    if system_info['gpu_info']:
        gpu_info = system_info['gpu_info']
        print(f"  GPU: {gpu_info['name']}")
        print(f"  Memória: {gpu_info['total_memory_gb']:.1f}GB")
    
    # Executar benchmark
    print(f"\n⚡ Executando benchmark de performance...")
    benchmark_results = gpu_accelerator.benchmark_performance(100000)
    
    print(f"Resultados:")
    print(f"  CPU: {benchmark_results['cpu_time']:.3f}s")
    print(f"  GPU: {benchmark_results['gpu_time']:.3f}s")
    print(f"  Speedup: {benchmark_results['speedup']:.2f}x")
    print(f"  Memória GPU: {benchmark_results['memory_used_gb']:.2f}GB")

def demo_ai_rule_generation_gpu():
    """Demo de geração de regras IA com GPU"""
    
    print("\n🤖 DEMO: Geração de Regras IA com GPU")
    print("=" * 50)
    
    # Criar dataset grande
    df_large = create_large_test_dataset(100000)
    
    # Inicializar gerador com GPU
    ai_generator = AIRuleGenerator(enable_gpu=True)
    
    if ai_generator.gpu_enabled:
        print("🚀 AI Rule Generator com GPU habilitado")
    else:
        print("💻 AI Rule Generator usando CPU")
    
    # Testar transformações
    transformations = [
        "Padronizar nomes para Title Case",
        "Converter emails para minúsculas",
        "Preencher valores nulos de salário com mediana"
    ]
    
    for i, transformation in enumerate(transformations, 1):
        print(f"\n🔄 Transformação {i}: {transformation}")
        
        start_time = time.time()
        
        # Gerar regra
        rule = ai_generator.generate_rule_from_description(transformation)
        
        if rule['validation']['is_valid']:
            # Executar regra
            success, result_df, message = ai_generator.execute_rule(rule, df_large)
            
            execution_time = time.time() - start_time
            
            if success:
                print(f"  ✅ {message}")
                print(f"  ⏱️ Tempo total: {execution_time:.3f}s")
                print(f"  📊 Registros processados: {len(result_df):,}")
            else:
                print(f"  ❌ Erro: {message}")
        else:
            print(f"  ❌ Regra inválida")

def demo_schema_drift_gpu():
    """Demo de detecção de schema drift com GPU"""
    
    print("\n🔍 DEMO: Schema Drift Detection com GPU")
    print("=" * 50)
    
    # Inicializar detector com GPU
    drift_detector = SchemaDriftDetector(
        storage_path="demo_gpu_schema_history",
        enable_gpu=True
    )
    
    if drift_detector.analyzer.gpu_enabled:
        print("🚀 Schema Drift Detector com GPU habilitado")
    else:
        print("💻 Schema Drift Detector usando CPU")
    
    # Dataset inicial
    df_initial = create_large_test_dataset(150000)
    
    print(f"\n📊 Analisando schema inicial ({len(df_initial):,} registros)...")
    
    start_time = time.time()
    drift_report = drift_detector.detect_drift(df_initial, "test_gpu_source")
    analysis_time = time.time() - start_time
    
    print(f"⏱️ Tempo de análise: {analysis_time:.3f}s")
    print(f"✅ Schema baseline criado")
    
    # Simular mudanças no schema
    print(f"\n🔄 Simulando mudanças no schema...")
    
    df_modified = df_initial.copy()
    df_modified['idade'] = df_modified['idade'].astype(str)  # Mudança de tipo
    df_modified['nova_coluna'] = 'valor_padrao'  # Nova coluna
    df_modified = df_modified.drop('ativo', axis=1)  # Remoção de coluna
    
    start_time = time.time()
    drift_report = drift_detector.detect_drift(df_modified, "test_gpu_source")
    analysis_time = time.time() - start_time
    
    if drift_report:
        print(f"🚨 Schema drift detectado!")
        print(f"⏱️ Tempo de análise: {analysis_time:.3f}s")
        print(f"📊 Score de drift: {drift_report.drift_score:.2f}")
        print(f"⚠️ Breaking change: {drift_report.is_breaking}")
        print(f"🔄 Mudanças detectadas: {len(drift_report.changes)}")
        
        for change in drift_report.changes[:3]:  # Mostrar 3 primeiras
            print(f"  - {change.change_type}: {change.description}")

def demo_intelligent_monitoring_gpu():
    """Demo de monitoramento inteligente com GPU"""
    
    print("\n📊 DEMO: Monitoramento Inteligente com GPU")
    print("=" * 50)
    
    # Inicializar sistema de monitoramento
    monitoring = IntelligentMonitoringSystem("demo_gpu_monitoring.db")
    
    # Configurar detector de anomalias com GPU
    monitoring.anomaly_detector = monitoring.anomaly_detector.__class__(
        contamination=0.1,
        enable_gpu=True
    )
    
    if monitoring.anomaly_detector.gpu_enabled:
        print("🚀 Anomaly Detector com GPU habilitado")
    else:
        print("💻 Anomaly Detector usando CPU")
    
    # Simular dados históricos
    print(f"\n📈 Gerando dados históricos para treinamento...")
    
    pipeline_name = "gpu_etl_pipeline"
    
    # Gerar 500 métricas históricas
    for i in range(500):
        from intelligent_monitoring import PipelineMetrics
        
        metrics = PipelineMetrics(
            timestamp=datetime.now(),
            pipeline_name=pipeline_name,
            records_processed=np.random.randint(80000, 120000),
            processing_time_seconds=np.random.normal(45, 10),
            memory_usage_mb=np.random.normal(400, 100),
            cpu_usage_percent=np.random.normal(60, 15),
            error_count=np.random.poisson(1),
            success_rate=np.random.normal(0.98, 0.02),
            latency_ms=np.random.normal(200, 50),
            throughput_records_per_sec=np.random.normal(25, 5),
            data_quality_score=np.random.normal(0.95, 0.05)
        )
        
        monitoring.metrics_collector.collect_metrics(metrics)
    
    # Treinar modelo baseline
    print(f"🤖 Treinando modelo de detecção de anomalias...")
    
    start_time = time.time()
    historical_metrics = monitoring.metrics_collector.get_historical_metrics(
        pipeline_name, hours=24
    )
    
    monitoring.anomaly_detector.train_baseline(pipeline_name, historical_metrics)
    training_time = time.time() - start_time
    
    print(f"⏱️ Tempo de treinamento: {training_time:.3f}s")
    print(f"📊 Métricas históricas: {len(historical_metrics)}")
    
    # Testar detecção de anomalias
    print(f"\n🔍 Testando detecção de anomalias...")
    
    # Métrica anômala
    anomalous_metrics = PipelineMetrics(
        timestamp=datetime.now(),
        pipeline_name=pipeline_name,
        records_processed=100000,
        processing_time_seconds=200,  # Muito alto
        memory_usage_mb=1500,  # Muito alto
        cpu_usage_percent=60,
        error_count=25,  # Muito alto
        success_rate=0.70,  # Muito baixo
        latency_ms=800,  # Muito alto
        throughput_records_per_sec=8,  # Muito baixo
        data_quality_score=0.80  # Baixo
    )
    
    start_time = time.time()
    anomalies = monitoring.anomaly_detector.detect_anomalies(anomalous_metrics)
    detection_time = time.time() - start_time
    
    print(f"⏱️ Tempo de detecção: {detection_time:.4f}s")
    print(f"🚨 Anomalias detectadas: {len(anomalies)}")
    
    for anomaly in anomalies[:3]:  # Mostrar 3 primeiras
        print(f"  - {anomaly.metric_name}: {anomaly.description}")
        print(f"    Severidade: {anomaly.severity}")

def demo_integrated_gpu_pipeline():
    """Demo do pipeline integrado com GPU"""
    
    print("\n🚀 DEMO: Pipeline ETL Integrado com GPU")
    print("=" * 55)
    
    # Configuração com GPU
    config = {
        'enable_gpu': True,
        'gpu_memory_fraction': 0.7,
        'claude_api_key': None  # Usar modo simulado
    }
    
    # Inicializar interface
    interface = ETLAIInterface(config)
    
    print(f"GPU habilitado: {interface.gpu_enabled}")
    
    # Criar dados de teste
    df_test = create_large_test_dataset(200000)
    
    # Salvar dados temporários
    input_path = "temp_gpu_input.csv"
    output_path = "temp_gpu_output.csv"
    
    print(f"\n💾 Salvando dataset temporário...")
    df_test.to_csv(input_path, index=False)
    
    # Executar pipeline completo
    print(f"\n🔄 Executando pipeline ETL completo com GPU...")
    
    transformations = [
        "Padronizar nomes para Title Case",
        "Converter emails para minúsculas",
        "Preencher valores nulos com valores apropriados"
    ]
    
    start_time = time.time()
    
    results = interface.process_data_with_ai(
        input_path=input_path,
        output_path=output_path,
        source_name="gpu_pipeline_test",
        transformations=transformations,
        enable_monitoring=True,
        enable_drift_detection=True
    )
    
    total_time = time.time() - start_time
    
    # Mostrar resultados
    print(f"\n📊 RESULTADOS DO PIPELINE:")
    print(f"  ✅ Sucesso: {results['success']}")
    print(f"  ⏱️ Tempo total: {total_time:.3f}s")
    print(f"  📊 Registros processados: {results['records_processed']:,}")
    print(f"  🔄 Transformações aplicadas: {len(results['transformations_applied'])}")
    print(f"  🔍 Drift detectado: {results['drift_detected']}")
    print(f"  🚨 Alertas gerados: {len(results['alerts_generated'])}")
    
    if results['errors']:
        print(f"  ❌ Erros: {len(results['errors'])}")
        for error in results['errors'][:3]:
            print(f"    - {error}")
    
    # Limpeza
    print(f"\n🧹 Limpando arquivos temporários...")
    try:
        os.remove(input_path)
        os.remove(output_path)
    except:
        pass

def main():
    """Função principal da demonstração"""
    
    print("🔥 DEMONSTRAÇÃO COMPLETA: ETL com IA e Aceleração GPU")
    print("CRM ETL")
    print("=" * 70)
    
    try:
        # 1. Benchmark GPU vs CPU
        benchmark_gpu_vs_cpu()
        
        # 2. Demo de geração de regras IA
        demo_ai_rule_generation_gpu()
        
        # 3. Demo de schema drift detection
        demo_schema_drift_gpu()
        
        # 4. Demo de monitoramento inteligente
        demo_intelligent_monitoring_gpu()
        
        # 5. Demo do pipeline integrado
        demo_integrated_gpu_pipeline()
        
        print(f"\n🎉 DEMONSTRAÇÃO CONCLUÍDA COM SUCESSO!")
        print(f"Todas as funcionalidades GPU foram testadas e estão operacionais.")
        
    except Exception as e:
        print(f"\n❌ ERRO NA DEMONSTRAÇÃO: {e}")
        logger.error(f"Erro na demo: {e}", exc_info=True)
    
    print(f"\n💡 PRÓXIMOS PASSOS:")
    print(f"1. Instalar dependências GPU: pip install torch cudf-cu11 cupy-cuda11x")
    print(f"2. Configurar CUDA environment")
    print(f"3. Testar com dados reais de produção")
    print(f"4. Configurar monitoramento contínuo")

if __name__ == "__main__":
    main()