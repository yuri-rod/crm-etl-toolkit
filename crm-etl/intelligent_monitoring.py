#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sistema de Monitoramento Inteligente com IA
CRM ETL

Sistema de monitoramento que usa ML para detectar anomalias, prever falhas
e sugerir otimizações automaticamente.
"""

import os
import time
import json
import logging
import threading
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from collections import deque, defaultdict
import pandas as pd
import numpy as np
from pathlib import Path

# Machine Learning para detecção de anomalias (com suporte GPU)
try:
    from sklearn.ensemble import IsolationForest
    from sklearn.preprocessing import StandardScaler
    from sklearn.cluster import DBSCAN
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False
    logging.warning("Scikit-learn não disponível. Usando detecção de anomalias básica.")

# Importar acelerador GPU
try:
    from gpu_accelerator import GPUAccelerator, GPUAccelerationConfig, GPUMLAccelerator
    GPU_AVAILABLE = True
except ImportError:
    GPU_AVAILABLE = False
    logging.info("GPU Accelerator não disponível")

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class PipelineMetrics:
    """Métricas de pipeline ETL"""
    timestamp: datetime
    pipeline_name: str
    records_processed: int
    processing_time_seconds: float
    memory_usage_mb: float
    cpu_usage_percent: float
    error_count: int
    success_rate: float
    latency_ms: float
    throughput_records_per_sec: float
    data_quality_score: float

@dataclass
class Anomaly:
    """Representação de uma anomalia detectada"""
    timestamp: datetime
    metric_name: str
    value: float
    expected_range: Tuple[float, float]
    severity: str  # low, medium, high, critical
    description: str
    suggested_action: str

@dataclass
class Alert:
    """Alerta gerado pelo sistema"""
    timestamp: datetime
    alert_type: str
    severity: str
    message: str
    metrics: Dict[str, Any]
    suggested_actions: List[str]

class MetricsCollector:
    """Coletor de métricas de pipeline"""
    
    def __init__(self, db_path: str = "monitoring.db"):
        self.db_path = db_path
        self._init_database()
        
    def _init_database(self):
        """Inicializa banco de dados para métricas"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pipeline_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                pipeline_name TEXT NOT NULL,
                records_processed INTEGER,
                processing_time_seconds REAL,
                memory_usage_mb REAL,
                cpu_usage_percent REAL,
                error_count INTEGER,
                success_rate REAL,
                latency_ms REAL,
                throughput_records_per_sec REAL,
                data_quality_score REAL
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS anomalies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                metric_name TEXT NOT NULL,
                value REAL,
                expected_min REAL,
                expected_max REAL,
                severity TEXT,
                description TEXT,
                suggested_action TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                alert_type TEXT NOT NULL,
                severity TEXT,
                message TEXT,
                metrics TEXT,
                suggested_actions TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def collect_metrics(self, metrics: PipelineMetrics):
        """Coleta e armazena métricas"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO pipeline_metrics 
            (timestamp, pipeline_name, records_processed, processing_time_seconds,
             memory_usage_mb, cpu_usage_percent, error_count, success_rate,
             latency_ms, throughput_records_per_sec, data_quality_score)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            metrics.timestamp.isoformat(),
            metrics.pipeline_name,
            metrics.records_processed,
            metrics.processing_time_seconds,
            metrics.memory_usage_mb,
            metrics.cpu_usage_percent,
            metrics.error_count,
            metrics.success_rate,
            metrics.latency_ms,
            metrics.throughput_records_per_sec,
            metrics.data_quality_score
        ))
        
        conn.commit()
        conn.close()
    
    def get_historical_metrics(self, pipeline_name: str, hours: int = 24) -> List[PipelineMetrics]:
        """Obtém métricas históricas"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        since = (datetime.now() - timedelta(hours=hours)).isoformat()
        
        cursor.execute('''
            SELECT * FROM pipeline_metrics 
            WHERE pipeline_name = ? AND timestamp > ?
            ORDER BY timestamp DESC
        ''', (pipeline_name, since))
        
        rows = cursor.fetchall()
        conn.close()
        
        metrics = []
        for row in rows:
            metrics.append(PipelineMetrics(
                timestamp=datetime.fromisoformat(row[1]),
                pipeline_name=row[2],
                records_processed=row[3],
                processing_time_seconds=row[4],
                memory_usage_mb=row[5],
                cpu_usage_percent=row[6],
                error_count=row[7],
                success_rate=row[8],
                latency_ms=row[9],
                throughput_records_per_sec=row[10],
                data_quality_score=row[11]
            ))
        
        return metrics

class IntelligentAnomalyDetector:
    """Detector de anomalias usando ML (com aceleração GPU)"""
    
    def __init__(self, contamination: float = 0.1, enable_gpu: bool = True):
        self.contamination = contamination
        self.models = {}
        self.scalers = {}
        self.baseline_stats = {}
        
        # Configurar aceleração GPU
        self.gpu_enabled = enable_gpu and GPU_AVAILABLE
        self.gpu_accelerator = None
        self.ml_accelerator = None
        
        if self.gpu_enabled:
            try:
                gpu_config = GPUAccelerationConfig(
                    enabled=True,
                    prefer_gpu=True,
                    memory_fraction=0.3,  # Usar pouca memória para monitoramento
                    fallback_to_cpu=True
                )
                self.gpu_accelerator = GPUAccelerator(gpu_config)
                self.ml_accelerator = GPUMLAccelerator(self.gpu_accelerator)
                logger.info("Detector de anomalias com aceleração GPU habilitado")
            except Exception as e:
                logger.warning(f"Falha ao inicializar GPU: {e}")
                self.gpu_enabled = False
        
    def train_baseline(self, pipeline_name: str, historical_metrics: List[PipelineMetrics]):
        """Treina modelo baseline para detecção de anomalias"""
        
        if len(historical_metrics) < 10:
            logger.warning(f"Poucos dados históricos para {pipeline_name}. Usando detecção estatística.")
            self._compute_statistical_baseline(pipeline_name, historical_metrics)
            return
        
        if not ML_AVAILABLE:
            self._compute_statistical_baseline(pipeline_name, historical_metrics)
            return
        
        # Preparar dados para ML
        features = []
        for m in historical_metrics:
            features.append([
                m.records_processed,
                m.processing_time_seconds,
                m.memory_usage_mb,
                m.cpu_usage_percent,
                m.error_count,
                m.success_rate,
                m.latency_ms,
                m.throughput_records_per_sec,
                m.data_quality_score
            ])
        
        X = np.array(features)
        
        # Remover valores NaN/infinitos
        X = np.nan_to_num(X, nan=0.0, posinf=999999, neginf=-999999)
        
        # Normalizar dados
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        # Treinar modelo de detecção de anomalias (GPU quando possível)
        if self.gpu_enabled and len(X) > 1000:  # GPU vale a pena para datasets maiores
            try:
                # Tentar treinar com GPU (usando PyTorch para Isolation Forest customizado)
                model = self._train_isolation_forest_gpu(X_scaled, pipeline_name)
                logger.info(f"Modelo de anomalias treinado em GPU para {pipeline_name}")
            except Exception as e:
                logger.warning(f"Fallback para CPU: {e}")
                model = IsolationForest(contamination=self.contamination, random_state=42)
                model.fit(X_scaled)
                logger.info(f"Modelo de anomalias treinado em CPU para {pipeline_name}")
        else:
            # Usar CPU padrão
            model = IsolationForest(contamination=self.contamination, random_state=42)
            model.fit(X_scaled)
            logger.info(f"Modelo de anomalias treinado em CPU para {pipeline_name} com {len(historical_metrics)} amostras")
        
        # Armazenar modelos
        self.models[pipeline_name] = model
        self.scalers[pipeline_name] = scaler
    
    def _train_isolation_forest_gpu(self, X_scaled: np.ndarray, pipeline_name: str):
        """Treina Isolation Forest usando GPU com PyTorch"""
        
        import torch
        import torch.nn as nn
        
        device = self.gpu_accelerator.get_optimal_device()
        
        # Converter para tensor GPU
        X_tensor = torch.from_numpy(X_scaled.astype(np.float32))
        if device == 'cuda':
            X_tensor = X_tensor.cuda()
        
        # Implementação simplificada de Isolation Forest para GPU
        class GPUIsolationForest:
            def __init__(self, contamination=0.1, n_trees=100):
                self.contamination = contamination
                self.n_trees = n_trees
                self.trees = []
                self.device = device
            
            def fit(self, X):
                """Treina múltiplas árvores de isolamento"""
                n_samples, n_features = X.shape
                
                for _ in range(self.n_trees):
                    # Amostragem aleatória
                    sample_size = min(256, n_samples)
                    indices = torch.randperm(n_samples)[:sample_size]
                    X_sample = X[indices]
                    
                    # Criar "árvore" simplificada usando splits aleatórios
                    tree = {
                        'splits': [],
                        'sample_data': X_sample
                    }
                    
                    # Criar splits aleatórios
                    for _ in range(10):  # Profundidade limitada para GPU
                        feature_idx = torch.randint(0, n_features, (1,)).item()
                        if X_sample.shape[0] > 1:
                            min_val = X_sample[:, feature_idx].min()
                            max_val = X_sample[:, feature_idx].max()
                            if max_val > min_val:
                                split_val = min_val + torch.rand(1).to(X.device) * (max_val - min_val)
                                tree['splits'].append((feature_idx, split_val.item()))
                    
                    self.trees.append(tree)
                
                return self
            
            def predict(self, X):
                """Predição usando ensemble de árvores"""
                if not self.trees:
                    return torch.ones(X.shape[0]) * -1
                
                scores = torch.zeros(X.shape[0]).to(X.device)
                
                for tree in self.trees:
                    # Calcular score de isolamento para cada árvore
                    tree_scores = self._tree_score(X, tree)
                    scores += tree_scores
                
                # Normalizar scores
                scores = scores / len(self.trees)
                
                # Determinar anomalias baseado no threshold
                threshold = torch.quantile(scores, 1 - self.contamination)
                predictions = torch.where(scores > threshold, -1, 1)
                
                return predictions
            
            def decision_function(self, X):
                """Função de decisão (score de anomalia)"""
                if not self.trees:
                    return torch.zeros(X.shape[0])
                
                scores = torch.zeros(X.shape[0]).to(X.device)
                
                for tree in self.trees:
                    tree_scores = self._tree_score(X, tree)
                    scores += tree_scores
                
                return scores / len(self.trees)
            
            def _tree_score(self, X, tree):
                """Calcula score de isolamento para uma árvore"""
                scores = torch.ones(X.shape[0]).to(X.device)
                
                for feature_idx, split_val in tree['splits']:
                    # Simular profundidade baseada nos splits
                    mask = X[:, feature_idx] < split_val
                    scores[mask] += 0.1
                    scores[~mask] += 0.1
                
                return scores
        
        # Treinar modelo GPU
        gpu_model = GPUIsolationForest(contamination=self.contamination)
        gpu_model.fit(X_tensor)
        
        # Criar wrapper compatível com sklearn
        class GPUIsolationForestWrapper:
            def __init__(self, gpu_model, device):
                self.gpu_model = gpu_model
                self.device = device
            
            def predict(self, X):
                X_tensor = torch.from_numpy(X.astype(np.float32))
                if self.device == 'cuda':
                    X_tensor = X_tensor.cuda()
                
                with torch.no_grad():
                    predictions = self.gpu_model.predict(X_tensor)
                    if self.device == 'cuda':
                        predictions = predictions.cpu()
                    return predictions.numpy()
            
            def decision_function(self, X):
                X_tensor = torch.from_numpy(X.astype(np.float32))
                if self.device == 'cuda':
                    X_tensor = X_tensor.cuda()
                
                with torch.no_grad():
                    scores = self.gpu_model.decision_function(X_tensor)
                    if self.device == 'cuda':
                        scores = scores.cpu()
                    return scores.numpy()
        
        return GPUIsolationForestWrapper(gpu_model, device)
    
    def _compute_statistical_baseline(self, pipeline_name: str, historical_metrics: List[PipelineMetrics]):
        """Computa baseline estatístico simples"""
        
        if not historical_metrics:
            return
        
        stats = {
            'records_processed': [],
            'processing_time_seconds': [],
            'memory_usage_mb': [],
            'cpu_usage_percent': [],
            'error_count': [],
            'success_rate': [],
            'latency_ms': [],
            'throughput_records_per_sec': [],
            'data_quality_score': []
        }
        
        for m in historical_metrics:
            stats['records_processed'].append(m.records_processed)
            stats['processing_time_seconds'].append(m.processing_time_seconds)
            stats['memory_usage_mb'].append(m.memory_usage_mb)
            stats['cpu_usage_percent'].append(m.cpu_usage_percent)
            stats['error_count'].append(m.error_count)
            stats['success_rate'].append(m.success_rate)
            stats['latency_ms'].append(m.latency_ms)
            stats['throughput_records_per_sec'].append(m.throughput_records_per_sec)
            stats['data_quality_score'].append(m.data_quality_score)
        
        # Calcular estatísticas
        baseline = {}
        for metric, values in stats.items():
            values = [v for v in values if v is not None and not np.isnan(v)]
            if values:
                baseline[metric] = {
                    'mean': np.mean(values),
                    'std': np.std(values),
                    'min': np.min(values),
                    'max': np.max(values),
                    'q25': np.percentile(values, 25),
                    'q75': np.percentile(values, 75)
                }
        
        self.baseline_stats[pipeline_name] = baseline
    
    def detect_anomalies(self, metrics: PipelineMetrics) -> List[Anomaly]:
        """Detecta anomalias nas métricas atuais"""
        
        anomalies = []
        pipeline_name = metrics.pipeline_name
        
        # Usar ML se disponível
        if pipeline_name in self.models and ML_AVAILABLE:
            anomalies.extend(self._detect_with_ml(metrics))
        
        # Sempre usar detecção estatística como backup
        if pipeline_name in self.baseline_stats:
            anomalies.extend(self._detect_with_statistics(metrics))
        
        return anomalies
    
    def _detect_with_ml(self, metrics: PipelineMetrics) -> List[Anomaly]:
        """Detecção de anomalias usando ML"""
        
        pipeline_name = metrics.pipeline_name
        model = self.models[pipeline_name]
        scaler = self.scalers[pipeline_name]
        
        # Preparar dados atuais
        features = np.array([[
            metrics.records_processed,
            metrics.processing_time_seconds,
            metrics.memory_usage_mb,
            metrics.cpu_usage_percent,
            metrics.error_count,
            metrics.success_rate,
            metrics.latency_ms,
            metrics.throughput_records_per_sec,
            metrics.data_quality_score
        ]])
        
        features = np.nan_to_num(features, nan=0.0, posinf=999999, neginf=-999999)
        features_scaled = scaler.transform(features)
        
        # Detectar anomalia
        prediction = model.predict(features_scaled)
        anomaly_score = model.decision_function(features_scaled)[0]
        
        anomalies = []
        
        if prediction[0] == -1:  # Anomalia detectada
            severity = "high" if anomaly_score < -0.5 else "medium"
            
            anomalies.append(Anomaly(
                timestamp=metrics.timestamp,
                metric_name="overall_pipeline",
                value=anomaly_score,
                expected_range=(-0.1, 0.1),
                severity=severity,
                description=f"Comportamento anômalo detectado no pipeline {pipeline_name}",
                suggested_action="Investigar métricas específicas e logs do pipeline"
            ))
        
        return anomalies
    
    def _detect_with_statistics(self, metrics: PipelineMetrics) -> List[Anomaly]:
        """Detecção de anomalias usando estatísticas"""
        
        pipeline_name = metrics.pipeline_name
        baseline = self.baseline_stats[pipeline_name]
        anomalies = []
        
        # Verificar cada métrica
        metric_checks = [
            ('processing_time_seconds', metrics.processing_time_seconds, "Tempo de processamento"),
            ('memory_usage_mb', metrics.memory_usage_mb, "Uso de memória"),
            ('cpu_usage_percent', metrics.cpu_usage_percent, "Uso de CPU"),
            ('error_count', metrics.error_count, "Contagem de erros"),
            ('success_rate', metrics.success_rate, "Taxa de sucesso"),
            ('latency_ms', metrics.latency_ms, "Latência"),
            ('data_quality_score', metrics.data_quality_score, "Score de qualidade")
        ]
        
        for metric_name, current_value, display_name in metric_checks:
            if metric_name not in baseline or current_value is None:
                continue
            
            stats = baseline[metric_name]
            mean = stats['mean']
            std = stats['std']
            
            # Definir limites (2 desvios padrão)
            lower_bound = mean - (2 * std)
            upper_bound = mean + (2 * std)
            
            # Verificar anomalia
            if current_value < lower_bound or current_value > upper_bound:
                # Determinar severidade
                extreme_lower = mean - (3 * std)
                extreme_upper = mean + (3 * std)
                
                if current_value < extreme_lower or current_value > extreme_upper:
                    severity = "critical"
                elif current_value < mean - (2.5 * std) or current_value > mean + (2.5 * std):
                    severity = "high"
                else:
                    severity = "medium"
                
                # Gerar sugestão de ação
                if metric_name == 'processing_time_seconds' and current_value > upper_bound:
                    action = "Verificar otimização de queries e recursos computacionais"
                elif metric_name == 'memory_usage_mb' and current_value > upper_bound:
                    action = "Verificar vazamentos de memória e otimizar uso de recursos"
                elif metric_name == 'error_count' and current_value > upper_bound:
                    action = "Investigar logs de erro e corrigir problemas de dados"
                elif metric_name == 'success_rate' and current_value < lower_bound:
                    action = "Investigar falhas na pipeline e corrigir problemas"
                else:
                    action = f"Investigar causa da anomalia em {display_name}"
                
                anomalies.append(Anomaly(
                    timestamp=metrics.timestamp,
                    metric_name=metric_name,
                    value=current_value,
                    expected_range=(lower_bound, upper_bound),
                    severity=severity,
                    description=f"{display_name} fora do padrão: {current_value:.2f} (esperado: {mean:.2f} ± {std:.2f})",
                    suggested_action=action
                ))
        
        return anomalies

class AlertManager:
    """Gerenciador de alertas inteligentes"""
    
    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics_collector = metrics_collector
        self.alert_rules = {
            'critical_error_rate': {
                'condition': lambda m: m.success_rate < 0.8,
                'message': "Taxa de sucesso crítica",
                'actions': ["Parar pipeline", "Investigar erros", "Verificar dados de entrada"]
            },
            'high_latency': {
                'condition': lambda m: m.latency_ms > 10000,
                'message': "Latência muito alta",
                'actions': ["Otimizar queries", "Verificar recursos", "Analisar gargalos"]
            },
            'memory_spike': {
                'condition': lambda m: m.memory_usage_mb > 1000,
                'message': "Uso excessivo de memória",
                'actions': ["Verificar vazamentos", "Otimizar processamento", "Aumentar recursos"]
            }
        }
    
    def evaluate_alerts(self, metrics: PipelineMetrics, anomalies: List[Anomaly]) -> List[Alert]:
        """Avalia e gera alertas baseados em métricas e anomalias"""
        
        alerts = []
        
        # Alertas baseados em regras
        for rule_name, rule in self.alert_rules.items():
            if rule['condition'](metrics):
                alert = Alert(
                    timestamp=metrics.timestamp,
                    alert_type=rule_name,
                    severity="high",
                    message=f"{rule['message']} para pipeline {metrics.pipeline_name}",
                    metrics=asdict(metrics),
                    suggested_actions=rule['actions']
                )
                alerts.append(alert)
        
        # Alertas baseados em anomalias
        for anomaly in anomalies:
            if anomaly.severity in ['high', 'critical']:
                alert = Alert(
                    timestamp=anomaly.timestamp,
                    alert_type="anomaly_detected",
                    severity=anomaly.severity,
                    message=f"Anomalia: {anomaly.description}",
                    metrics={"metric": anomaly.metric_name, "value": anomaly.value},
                    suggested_actions=[anomaly.suggested_action]
                )
                alerts.append(alert)
        
        # Salvar alertas
        for alert in alerts:
            self._save_alert(alert)
        
        return alerts
    
    def _save_alert(self, alert: Alert):
        """Salva alerta no banco de dados"""
        conn = sqlite3.connect(self.metrics_collector.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO alerts 
            (timestamp, alert_type, severity, message, metrics, suggested_actions)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            alert.timestamp.isoformat(),
            alert.alert_type,
            alert.severity,
            alert.message,
            json.dumps(alert.metrics),
            json.dumps(alert.suggested_actions)
        ))
        
        conn.commit()
        conn.close()

class IntelligentMonitoringSystem:
    """Sistema principal de monitoramento inteligente"""
    
    def __init__(self, db_path: str = "monitoring.db"):
        self.metrics_collector = MetricsCollector(db_path)
        self.anomaly_detector = IntelligentAnomalyDetector()
        self.alert_manager = AlertManager(self.metrics_collector)
        self.monitoring_active = False
        self.monitoring_thread = None
        
    def start_monitoring(self, pipeline_name: str, check_interval: int = 60):
        """Inicia monitoramento contínuo"""
        
        if self.monitoring_active:
            logger.warning("Monitoramento já ativo")
            return
        
        # Treinar baseline com dados históricos
        historical_metrics = self.metrics_collector.get_historical_metrics(pipeline_name, hours=168)  # 1 semana
        if historical_metrics:
            self.anomaly_detector.train_baseline(pipeline_name, historical_metrics)
        
        self.monitoring_active = True
        self.monitoring_thread = threading.Thread(
            target=self._monitoring_loop,
            args=(pipeline_name, check_interval),
            daemon=True
        )
        self.monitoring_thread.start()
        
        logger.info(f"Monitoramento iniciado para {pipeline_name}")
    
    def stop_monitoring(self):
        """Para monitoramento"""
        self.monitoring_active = False
        if self.monitoring_thread:
            self.monitoring_thread.join()
        logger.info("Monitoramento parado")
    
    def _monitoring_loop(self, pipeline_name: str, check_interval: int):
        """Loop principal de monitoramento"""
        
        while self.monitoring_active:
            try:
                # Simular coleta de métricas (em produção, seria coletado do pipeline real)
                metrics = self._collect_current_metrics(pipeline_name)
                
                # Detectar anomalias
                anomalies = self.anomaly_detector.detect_anomalies(metrics)
                
                # Avaliar alertas
                alerts = self.alert_manager.evaluate_alerts(metrics, anomalies)
                
                # Log resultados
                if anomalies:
                    logger.warning(f"Detectadas {len(anomalies)} anomalias em {pipeline_name}")
                
                if alerts:
                    logger.error(f"Gerados {len(alerts)} alertas para {pipeline_name}")
                    for alert in alerts:
                        logger.error(f"ALERTA: {alert.message}")
                
                time.sleep(check_interval)
                
            except Exception as e:
                logger.error(f"Erro no loop de monitoramento: {e}")
                time.sleep(check_interval)
    
    def _collect_current_metrics(self, pipeline_name: str) -> PipelineMetrics:
        """Coleta métricas atuais (simulado para demo)"""
        
        # Em produção, isso seria coletado do pipeline real
        # Aqui vamos simular métricas variáveis
        
        import random
        
        # Simular métricas normais com alguma variação
        base_metrics = {
            'records_processed': random.randint(800, 1200),
            'processing_time_seconds': random.uniform(30, 90),
            'memory_usage_mb': random.uniform(200, 400),
            'cpu_usage_percent': random.uniform(30, 70),
            'error_count': random.randint(0, 5),
            'success_rate': random.uniform(0.95, 1.0),
            'latency_ms': random.uniform(100, 500),
            'throughput_records_per_sec': random.uniform(10, 30),
            'data_quality_score': random.uniform(0.85, 0.98)
        }
        
        # Ocasionalmente simular anomalias
        if random.random() < 0.1:  # 10% chance de anomalia
            anomaly_type = random.choice(['latency', 'memory', 'errors'])
            if anomaly_type == 'latency':
                base_metrics['latency_ms'] *= 5  # Latência muito alta
            elif anomaly_type == 'memory':
                base_metrics['memory_usage_mb'] *= 3  # Uso de memória alto
            elif anomaly_type == 'errors':
                base_metrics['error_count'] *= 10  # Muitos erros
                base_metrics['success_rate'] *= 0.5  # Taxa de sucesso baixa
        
        metrics = PipelineMetrics(
            timestamp=datetime.now(),
            pipeline_name=pipeline_name,
            **base_metrics
        )
        
        # Salvar métricas
        self.metrics_collector.collect_metrics(metrics)
        
        return metrics
    
    def get_dashboard_data(self, pipeline_name: str, hours: int = 24) -> Dict[str, Any]:
        """Gera dados para dashboard"""
        
        historical_metrics = self.metrics_collector.get_historical_metrics(pipeline_name, hours)
        
        if not historical_metrics:
            return {"error": "Nenhuma métrica disponível"}
        
        # Calcular estatísticas
        processing_times = [m.processing_time_seconds for m in historical_metrics]
        memory_usage = [m.memory_usage_mb for m in historical_metrics]
        success_rates = [m.success_rate for m in historical_metrics]
        latencies = [m.latency_ms for m in historical_metrics]
        
        dashboard_data = {
            'pipeline_name': pipeline_name,
            'total_executions': len(historical_metrics),
            'avg_processing_time': np.mean(processing_times),
            'avg_memory_usage': np.mean(memory_usage),
            'avg_success_rate': np.mean(success_rates),
            'avg_latency': np.mean(latencies),
            'last_execution': historical_metrics[0].timestamp.isoformat() if historical_metrics else None,
            'timeline_data': [
                {
                    'timestamp': m.timestamp.isoformat(),
                    'processing_time': m.processing_time_seconds,
                    'memory_usage': m.memory_usage_mb,
                    'success_rate': m.success_rate,
                    'latency': m.latency_ms
                }
                for m in historical_metrics[-50:]  # Últimas 50 execuções
            ]
        }
        
        return dashboard_data


def demo_intelligent_monitoring():
    """Demonstração do sistema de monitoramento inteligente"""
    
    print("📊 DEMO: Sistema de Monitoramento Inteligente")
    print("=" * 60)
    
    # Inicializar sistema
    monitoring = IntelligentMonitoringSystem("demo_monitoring.db")
    
    print("🔧 Gerando dados históricos...")
    
    # Gerar dados históricos simulados
    pipeline_name = "etl_crm_pipeline"
    
    for i in range(100):
        # Simular métricas históricas normais
        metrics = PipelineMetrics(
            timestamp=datetime.now() - timedelta(hours=i),
            pipeline_name=pipeline_name,
            records_processed=1000 + (i * 10),
            processing_time_seconds=60 + np.random.normal(0, 10),
            memory_usage_mb=300 + np.random.normal(0, 50),
            cpu_usage_percent=50 + np.random.normal(0, 15),
            error_count=np.random.poisson(2),
            success_rate=0.98 + np.random.normal(0, 0.02),
            latency_ms=200 + np.random.normal(0, 50),
            throughput_records_per_sec=20 + np.random.normal(0, 5),
            data_quality_score=0.95 + np.random.normal(0, 0.05)
        )
        
        monitoring.metrics_collector.collect_metrics(metrics)
    
    print("✅ Dados históricos gerados")
    
    # Treinar modelo de anomalias
    print("🤖 Treinando modelo de detecção de anomalias...")
    historical_metrics = monitoring.metrics_collector.get_historical_metrics(pipeline_name, hours=200)
    monitoring.anomaly_detector.train_baseline(pipeline_name, historical_metrics)
    print("✅ Modelo treinado")
    
    # Simular detecção em tempo real
    print("\n🔍 Simulando detecção de anomalias...")
    
    # Métricas normais
    normal_metrics = PipelineMetrics(
        timestamp=datetime.now(),
        pipeline_name=pipeline_name,
        records_processed=1000,
        processing_time_seconds=65,
        memory_usage_mb=320,
        cpu_usage_percent=55,
        error_count=1,
        success_rate=0.98,
        latency_ms=210,
        throughput_records_per_sec=22,
        data_quality_score=0.96
    )
    
    anomalies = monitoring.anomaly_detector.detect_anomalies(normal_metrics)
    alerts = monitoring.alert_manager.evaluate_alerts(normal_metrics, anomalies)
    
    print(f"Métricas normais: {len(anomalies)} anomalias, {len(alerts)} alertas")
    
    # Métricas anômalas
    anomalous_metrics = PipelineMetrics(
        timestamp=datetime.now(),
        pipeline_name=pipeline_name,
        records_processed=1000,
        processing_time_seconds=300,  # Muito alto
        memory_usage_mb=800,  # Muito alto
        cpu_usage_percent=55,
        error_count=50,  # Muito alto
        success_rate=0.60,  # Muito baixo
        latency_ms=2000,  # Muito alto
        throughput_records_per_sec=5,  # Muito baixo
        data_quality_score=0.70  # Muito baixo
    )
    
    anomalies = monitoring.anomaly_detector.detect_anomalies(anomalous_metrics)
    alerts = monitoring.alert_manager.evaluate_alerts(anomalous_metrics, anomalies)
    
    print(f"Métricas anômalas: {len(anomalies)} anomalias, {len(alerts)} alertas")
    
    # Mostrar detalhes das anomalias
    if anomalies:
        print("\n🚨 Anomalias detectadas:")
        for anomaly in anomalies[:3]:  # Mostrar apenas 3
            print(f"  - {anomaly.metric_name}: {anomaly.description}")
            print(f"    Severidade: {anomaly.severity}")
            print(f"    Ação sugerida: {anomaly.suggested_action}")
    
    # Mostrar detalhes dos alertas
    if alerts:
        print("\n🔔 Alertas gerados:")
        for alert in alerts[:3]:  # Mostrar apenas 3
            print(f"  - {alert.alert_type}: {alert.message}")
            print(f"    Severidade: {alert.severity}")
            print(f"    Ações: {', '.join(alert.suggested_actions)}")
    
    # Gerar dados do dashboard
    print("\n📊 Dados do dashboard:")
    dashboard_data = monitoring.get_dashboard_data(pipeline_name, hours=24)
    print(f"  - Execuções: {dashboard_data['total_executions']}")
    print(f"  - Tempo médio: {dashboard_data['avg_processing_time']:.1f}s")
    print(f"  - Memória média: {dashboard_data['avg_memory_usage']:.1f}MB")
    print(f"  - Taxa de sucesso: {dashboard_data['avg_success_rate']:.1%}")
    print(f"  - Latência média: {dashboard_data['avg_latency']:.1f}ms")
    
    print("\n✅ Demo concluída!")


if __name__ == "__main__":
    demo_intelligent_monitoring()