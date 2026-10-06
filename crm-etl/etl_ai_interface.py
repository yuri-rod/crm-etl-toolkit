#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Interface Integrada ETL com IA - Fase 1
CRM ETL

Interface principal que integra todas as funcionalidades da Fase 1:
- IA para geração de regras ETL
- Monitoramento inteligente
- Detecção de schema drift
"""

import os
import sys
import time
import argparse
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
import pandas as pd

# Importar módulos criados
from ai_rule_generator import AIRuleGenerator
from intelligent_monitoring import IntelligentMonitoringSystem, PipelineMetrics
from schema_drift_detector import SchemaDriftDetector

# Importar acelerador GPU
try:
    from gpu_accelerator import GPUAccelerator, GPUAccelerationConfig
    GPU_AVAILABLE = True
except ImportError:
    GPU_AVAILABLE = False
    logging.info("GPU Accelerator não disponível para interface principal")

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ETLAIInterface:
    """Interface principal do ETL com IA (com aceleração GPU)"""
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Inicializa interface ETL com IA
        
        Args:
            config: Configurações opcionais
        """
        self.config = config or {}
        
        # Configurar GPU
        self.gpu_enabled = self.config.get('enable_gpu', True) and GPU_AVAILABLE
        self.gpu_accelerator = None
        
        if self.gpu_enabled:
            try:
                gpu_config = GPUAccelerationConfig(
                    enabled=True,
                    prefer_gpu=True,
                    memory_fraction=self.config.get('gpu_memory_fraction', 0.6),
                    fallback_to_cpu=True
                )
                self.gpu_accelerator = GPUAccelerator(gpu_config)
                logger.info("Interface ETL com aceleração GPU habilitada")
            except Exception as e:
                logger.warning(f"Falha ao inicializar GPU: {e}")
                self.gpu_enabled = False
        
        # Inicializar componentes com suporte GPU
        self.ai_generator = AIRuleGenerator(
            api_key=self.config.get('claude_api_key'),
            enable_gpu=self.gpu_enabled
        )
        
        self.monitoring = IntelligentMonitoringSystem(
            db_path=self.config.get('monitoring_db', 'etl_monitoring.db')
        )
        
        self.drift_detector = SchemaDriftDetector(
            storage_path=self.config.get('schema_storage', 'schema_history'),
            enable_gpu=self.gpu_enabled
        )
        
        logger.info(f"Interface ETL com IA inicializada (GPU: {'Habilitado' if self.gpu_enabled else 'Desabilitado'})")
    
    def process_data_with_ai(self, 
                           input_path: str, 
                           output_path: str,
                           source_name: str,
                           transformations: List[str] = None,
                           enable_monitoring: bool = True,
                           enable_drift_detection: bool = True) -> Dict[str, Any]:
        """
        Processa dados usando IA para transformações e monitoramento
        
        Args:
            input_path: Caminho do arquivo de entrada
            output_path: Caminho do arquivo de saída
            source_name: Nome da fonte de dados
            transformations: Lista de transformações em linguagem natural
            enable_monitoring: Ativar monitoramento inteligente
            enable_drift_detection: Ativar detecção de schema drift
            
        Returns:
            Dict com resultados do processamento
        """
        
        start_time = datetime.now()
        results = {
            'success': False,
            'start_time': start_time.isoformat(),
            'source_name': source_name,
            'transformations_applied': [],
            'drift_detected': False,
            'alerts_generated': [],
            'processing_time_seconds': 0,
            'records_processed': 0,
            'errors': []
        }
        
        try:
            # 1. Carregar dados
            logger.info(f"Carregando dados de {input_path}")
            df = self._load_data(input_path)
            results['records_processed'] = len(df)
            
            # 2. Detecção de Schema Drift (se habilitado)
            if enable_drift_detection:
                logger.info("Verificando schema drift...")
                drift_report = self.drift_detector.detect_drift(df, source_name)
                
                if drift_report:
                    results['drift_detected'] = True
                    results['drift_report'] = {
                        'drift_score': drift_report.drift_score,
                        'is_breaking': drift_report.is_breaking,
                        'changes_count': len(drift_report.changes),
                        'recommendations': drift_report.recommended_actions
                    }
                    
                    logger.warning(f"Schema drift detectado! Score: {drift_report.drift_score:.2f}")
                    
                    # Se for breaking change, parar processamento
                    if drift_report.is_breaking:
                        results['errors'].append("Schema drift crítico detectado - processamento interrompido")
                        return results
            
            # 3. Aplicar transformações com IA
            if transformations:
                logger.info(f"Aplicando {len(transformations)} transformações com IA...")
                
                # Analisar dataset para sugestões
                analysis = self.ai_generator.analyze_dataset_for_suggestions(df)
                
                for i, transformation_desc in enumerate(transformations, 1):
                    logger.info(f"Transformação {i}: {transformation_desc}")
                    
                    # Gerar regra com IA
                    rule = self.ai_generator.generate_rule_from_description(
                        transformation_desc, 
                        analysis['column_info']
                    )
                    
                    if rule['validation']['is_valid']:
                        # Executar transformação
                        success, df, message = self.ai_generator.execute_rule(rule, df)
                        
                        if success:
                            results['transformations_applied'].append({
                                'description': transformation_desc,
                                'source': rule['source'],
                                'success': True,
                                'message': message
                            })
                            logger.info(f"✅ {message}")
                        else:
                            results['transformations_applied'].append({
                                'description': transformation_desc,
                                'success': False,
                                'error': message
                            })
                            results['errors'].append(f"Falha na transformação: {message}")
                            logger.error(f"❌ {message}")
                    else:
                        error_msg = f"Regra inválida para '{transformation_desc}': {', '.join(rule['validation']['errors'])}"
                        results['errors'].append(error_msg)
                        logger.error(f"❌ {error_msg}")
            
            # 4. Salvar dados processados
            logger.info(f"Salvando dados processados em {output_path}")
            self._save_data(df, output_path)
            
            # 5. Coletar métricas de processamento
            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds()
            results['processing_time_seconds'] = processing_time
            
            # 6. Monitoramento inteligente (se habilitado)
            if enable_monitoring:
                logger.info("Coletando métricas para monitoramento...")
                
                metrics = PipelineMetrics(
                    timestamp=end_time,
                    pipeline_name=source_name,
                    records_processed=len(df),
                    processing_time_seconds=processing_time,
                    memory_usage_mb=self._estimate_memory_usage(df),
                    cpu_usage_percent=50.0,  # Estimado
                    error_count=len(results['errors']),
                    success_rate=1.0 if not results['errors'] else 0.8,
                    latency_ms=processing_time * 1000,
                    throughput_records_per_sec=len(df) / processing_time if processing_time > 0 else 0,
                    data_quality_score=0.95  # Estimado
                )
                
                # Detectar anomalias
                anomalies = self.monitoring.anomaly_detector.detect_anomalies(metrics)
                
                # Gerar alertas
                alerts = self.monitoring.alert_manager.evaluate_alerts(metrics, anomalies)
                
                results['monitoring'] = {
                    'metrics_collected': True,
                    'anomalies_detected': len(anomalies),
                    'alerts_generated': len(alerts)
                }
                
                if alerts:
                    results['alerts_generated'] = [
                        {
                            'type': alert.alert_type,
                            'severity': alert.severity,
                            'message': alert.message
                        }
                        for alert in alerts
                    ]
                
                logger.info(f"Monitoramento: {len(anomalies)} anomalias, {len(alerts)} alertas")
            
            results['success'] = True
            results['end_time'] = end_time.isoformat()
            
            logger.info(f"✅ Processamento concluído: {len(df)} registros em {processing_time:.2f}s")
            
        except Exception as e:
            error_msg = f"Erro durante processamento: {e}"
            results['errors'].append(error_msg)
            logger.error(error_msg)
        
        return results
    
    def generate_rule_interactive(self) -> Optional[Dict]:
        """Gerador interativo de regras ETL"""
        
        print("\n🤖 GERADOR INTERATIVO DE REGRAS ETL COM IA")
        print("=" * 60)
        
        # Solicitar descrição
        description = input("\n📝 Descreva a transformação desejada em português:\n> ")
        
        if not description.strip():
            print("❌ Descrição não pode estar vazia")
            return None
        
        print(f"\n🔄 Gerando regra para: '{description}'...")
        
        # Gerar regra
        rule = self.ai_generator.generate_rule_from_description(description)
        
        print(f"\n📊 Resultado:")
        print(f"  Fonte: {rule['source']}")
        print(f"  Válida: {rule['validation']['is_valid']}")
        
        if rule['validation']['is_valid']:
            print(f"  Função: {rule['validation']['function_name']}")
            
            # Mostrar código gerado
            print("\n💻 Código gerado:")
            print("-" * 40)
            print(rule['code'])
            print("-" * 40)
            
            # Perguntar se quer salvar
            save = input("\n💾 Salvar regra? (s/n): ").lower()
            if save == 's':
                filename = input("Nome do arquivo (sem extensão): ")
                if self.ai_generator.save_rule(rule, filename):
                    print(f"✅ Regra salva como '{filename}.json'")
                else:
                    print("❌ Erro ao salvar regra")
            
            return rule
            
        else:
            print("❌ Regra inválida:")
            for error in rule['validation']['errors']:
                print(f"  - {error}")
            return None
    
    def monitor_pipeline_interactive(self):
        """Monitor interativo de pipeline"""
        
        print("\n📊 MONITOR INTERATIVO DE PIPELINE")
        print("=" * 50)
        
        pipeline_name = input("Nome da pipeline para monitorar: ")
        
        if not pipeline_name.strip():
            print("❌ Nome da pipeline não pode estar vazio")
            return
        
        print(f"\n🔄 Iniciando monitoramento de '{pipeline_name}'...")
        print("Pressione Ctrl+C para parar")
        
        try:
            # Iniciar monitoramento
            self.monitoring.start_monitoring(pipeline_name, check_interval=10)
            
            # Loop interativo
            while True:
                print(f"\n📈 Dashboard - {datetime.now().strftime('%H:%M:%S')}")
                
                # Obter dados do dashboard
                dashboard_data = self.monitoring.get_dashboard_data(pipeline_name, hours=1)
                
                if 'error' not in dashboard_data:
                    print(f"  Execuções: {dashboard_data['total_executions']}")
                    print(f"  Tempo médio: {dashboard_data['avg_processing_time']:.1f}s")
                    print(f"  Memória média: {dashboard_data['avg_memory_usage']:.1f}MB")
                    print(f"  Taxa de sucesso: {dashboard_data['avg_success_rate']:.1%}")
                    print(f"  Latência média: {dashboard_data['avg_latency']:.1f}ms")
                else:
                    print("  ⚠️ Ainda coletando dados...")
                
                time.sleep(10)
                
        except KeyboardInterrupt:
            print("\n\n🛑 Parando monitoramento...")
            self.monitoring.stop_monitoring()
            print("✅ Monitoramento parado")
    
    def check_schema_drift_interactive(self):
        """Verificador interativo de schema drift"""
        
        print("\n🔍 VERIFICADOR INTERATIVO DE SCHEMA DRIFT")
        print("=" * 55)
        
        # Solicitar arquivo
        file_path = input("Caminho do arquivo para verificar: ")
        
        if not Path(file_path).exists():
            print("❌ Arquivo não encontrado")
            return
        
        source_name = input("Nome da fonte de dados: ") or "unknown_source"
        
        print(f"\n🔄 Analisando schema de '{file_path}'...")
        
        try:
            # Carregar dados
            df = self._load_data(file_path)
            print(f"📊 Dataset carregado: {len(df)} registros, {len(df.columns)} colunas")
            
            # Detectar drift
            drift_report = self.drift_detector.detect_drift(df, source_name)
            
            if drift_report:
                print("\n🚨 SCHEMA DRIFT DETECTADO!")
                print(f"Score de drift: {drift_report.drift_score:.2f}")
                print(f"Breaking change: {drift_report.is_breaking}")
                print(f"Mudanças: {len(drift_report.changes)}")
                
                # Mostrar mudanças
                print("\n📋 Detalhes das mudanças:")
                for i, change in enumerate(drift_report.changes, 1):
                    print(f"{i}. {change.change_type.upper()}: {change.description}")
                    print(f"   Impacto: {change.impact_level}")
                    print(f"   Ação: {change.suggested_action}")
                
                # Mostrar recomendações
                print("\n💡 Recomendações:")
                for i, rec in enumerate(drift_report.recommended_actions, 1):
                    print(f"{i}. {rec}")
                
            else:
                print("✅ Nenhum schema drift detectado ou primeiro análise")
            
            # Mostrar histórico
            history = self.drift_detector.get_drift_history(source_name, days=7)
            if history:
                print(f"\n📈 Histórico (últimos 7 dias): {len(history)} análises")
                for i, report in enumerate(history[:5], 1):  # Mostrar últimas 5
                    print(f"{i}. {report['timestamp']}: {len(report['changes'])} mudanças")
            
        except Exception as e:
            print(f"❌ Erro ao analisar: {e}")
    
    def _load_data(self, file_path: str) -> pd.DataFrame:
        """Carrega dados de diferentes formatos"""
        
        file_path = Path(file_path)
        
        if file_path.suffix.lower() == '.csv':
            # Tentar detectar separador automaticamente
            with open(file_path, 'r', encoding='utf-8') as f:
                first_line = f.readline()
                separator = ',' if ',' in first_line else ';'
            
            return pd.read_csv(file_path, sep=separator, encoding='utf-8')
            
        elif file_path.suffix.lower() in ['.xlsx', '.xls']:
            return pd.read_excel(file_path)
            
        elif file_path.suffix.lower() == '.json':
            return pd.read_json(file_path)
            
        else:
            raise ValueError(f"Formato de arquivo não suportado: {file_path.suffix}")
    
    def _save_data(self, df: pd.DataFrame, file_path: str):
        """Salva dados em diferentes formatos"""
        
        file_path = Path(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        if file_path.suffix.lower() == '.csv':
            df.to_csv(file_path, index=False, encoding='utf-8')
        elif file_path.suffix.lower() == '.xlsx':
            df.to_excel(file_path, index=False)
        elif file_path.suffix.lower() == '.json':
            df.to_json(file_path, orient='records', indent=2)
        else:
            # Default para CSV
            df.to_csv(file_path.with_suffix('.csv'), index=False, encoding='utf-8')
    
    def _estimate_memory_usage(self, df: pd.DataFrame) -> float:
        """Estima uso de memória do DataFrame em MB"""
        return df.memory_usage(deep=True).sum() / (1024 * 1024)


def main():
    """Função principal da interface"""
    
    parser = argparse.ArgumentParser(description="Interface ETL com IA - CRM")
    parser.add_argument('mode', choices=['process', 'generate', 'monitor', 'drift', 'interactive'], 
                       help='Modo de operação')
    parser.add_argument('--input', '-i', help='Arquivo de entrada')
    parser.add_argument('--output', '-o', help='Arquivo de saída')
    parser.add_argument('--source', '-s', help='Nome da fonte de dados')
    parser.add_argument('--transform', '-t', action='append', help='Transformação em linguagem natural')
    parser.add_argument('--config', '-c', help='Arquivo de configuração JSON')
    parser.add_argument('--no-monitoring', action='store_true', help='Desabilitar monitoramento')
    parser.add_argument('--no-drift', action='store_true', help='Desabilitar detecção de drift')
    
    args = parser.parse_args()
    
    # Carregar configuração se fornecida
    config = {}
    if args.config and Path(args.config).exists():
        import json
        with open(args.config, 'r', encoding='utf-8') as f:
            config = json.load(f)
    
    # Inicializar interface
    interface = ETLAIInterface(config)
    
    if args.mode == 'interactive':
        # Modo interativo
        print("\n🤖 INTERFACE ETL COM IA - CRM ETL")
        print("=" * 60)
        
        while True:
            print("\n📋 Opções disponíveis:")
            print("1. Processar dados com IA")
            print("2. Gerar regra ETL interativa")
            print("3. Monitorar pipeline")
            print("4. Verificar schema drift")
            print("5. Sair")
            
            choice = input("\nEscolha uma opção (1-5): ")
            
            if choice == '1':
                input_path = input("Arquivo de entrada: ")
                output_path = input("Arquivo de saída: ")
                source_name = input("Nome da fonte: ")
                
                transforms = []
                print("\nTransformações (Enter vazio para terminar):")
                while True:
                    transform = input("> ")
                    if not transform.strip():
                        break
                    transforms.append(transform)
                
                results = interface.process_data_with_ai(
                    input_path, output_path, source_name, 
                    transformations=transforms
                )
                
                print(f"\n✅ Processamento {'bem-sucedido' if results['success'] else 'falhou'}")
                if results['errors']:
                    print("Erros:")
                    for error in results['errors']:
                        print(f"  - {error}")
            
            elif choice == '2':
                interface.generate_rule_interactive()
            
            elif choice == '3':
                interface.monitor_pipeline_interactive()
            
            elif choice == '4':
                interface.check_schema_drift_interactive()
            
            elif choice == '5':
                print("👋 Até logo!")
                break
            
            else:
                print("❌ Opção inválida")
    
    elif args.mode == 'process':
        # Modo de processamento de linha de comando
        if not all([args.input, args.output, args.source]):
            print("❌ Modo 'process' requer --input, --output e --source")
            sys.exit(1)
        
        results = interface.process_data_with_ai(
            args.input,
            args.output,
            args.source,
            transformations=args.transform,
            enable_monitoring=not args.no_monitoring,
            enable_drift_detection=not args.no_drift
        )
        
        # Imprimir resultados
        print(f"\n{'✅' if results['success'] else '❌'} Processamento {'concluído' if results['success'] else 'falhou'}")
        print(f"Registros processados: {results['records_processed']}")
        print(f"Tempo: {results['processing_time_seconds']:.2f}s")
        
        if results['transformations_applied']:
            print(f"Transformações aplicadas: {len(results['transformations_applied'])}")
        
        if results['drift_detected']:
            print("⚠️ Schema drift detectado!")
        
        if results['errors']:
            print("Erros:")
            for error in results['errors']:
                print(f"  - {error}")
    
    elif args.mode == 'generate':
        # Modo de geração de regras
        interface.generate_rule_interactive()
    
    elif args.mode == 'monitor':
        # Modo de monitoramento
        if not args.source:
            print("❌ Modo 'monitor' requer --source")
            sys.exit(1)
        interface.monitor_pipeline_interactive()
    
    elif args.mode == 'drift':
        # Modo de verificação de drift
        if not args.input:
            print("❌ Modo 'drift' requer --input")
            sys.exit(1)
        interface.check_schema_drift_interactive()


if __name__ == "__main__":
    main()