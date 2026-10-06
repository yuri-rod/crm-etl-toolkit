#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Acelerador GPU para ETL e IA Workflows
CRM ETL

Sistema de aceleração GPU que suporta múltiplas bibliotecas:
- CUDA/PyTorch para machine learning
- CuPy para computação científica
- CuDF para processamento de DataFrames
- Rapids para ETL acelerado
"""

import os
import sys
import logging
import warnings
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass
import numpy as np
import pandas as pd
from pathlib import Path

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Suprimir warnings de compatibilidade
warnings.filterwarnings('ignore', category=UserWarning)

@dataclass
class GPUInfo:
    """Informações sobre GPU disponível"""
    name: str
    total_memory_gb: float
    available_memory_gb: float
    cuda_version: str
    compute_capability: str
    is_available: bool

@dataclass
class GPUAccelerationConfig:
    """Configuração de aceleração GPU"""
    enabled: bool = True
    prefer_gpu: bool = True
    memory_fraction: float = 0.8
    fallback_to_cpu: bool = True
    batch_size_multiplier: float = 2.0
    precision: str = "float32"  # float32, float16, mixed

class GPUAccelerator:
    """Gerenciador principal de aceleração GPU"""
    
    def __init__(self, config: Optional[GPUAccelerationConfig] = None):
        """
        Inicializa o acelerador GPU
        
        Args:
            config: Configuração de aceleração
        """
        self.config = config or GPUAccelerationConfig()
        
        # Status das bibliotecas GPU
        self.cuda_available = False
        self.pytorch_available = False
        self.cupy_available = False
        self.cudf_available = False
        self.rapids_available = False
        
        # Informações da GPU
        self.gpu_info = None
        
        # Detecção automática de recursos
        self._detect_gpu_capabilities()
        
        logger.info(f"GPU Accelerator iniciado - CUDA: {self.cuda_available}, PyTorch: {self.pytorch_available}")
    
    def _detect_gpu_capabilities(self):
        """Detecta capacidades GPU disponíveis"""
        
        if not self.config.enabled:
            logger.info("Aceleração GPU desabilitada por configuração")
            return
        
        # Verificar CUDA
        try:
            import torch
            if torch.cuda.is_available():
                self.cuda_available = True
                self.pytorch_available = True
                
                # Obter informações da GPU
                device = torch.cuda.current_device()
                gpu_name = torch.cuda.get_device_name(device)
                total_memory = torch.cuda.get_device_properties(device).total_memory / (1024**3)
                
                # Limpar cache para obter memória disponível
                torch.cuda.empty_cache()
                available_memory = (torch.cuda.get_device_properties(device).total_memory - 
                                  torch.cuda.memory_allocated()) / (1024**3)
                
                self.gpu_info = GPUInfo(
                    name=gpu_name,
                    total_memory_gb=total_memory,
                    available_memory_gb=available_memory,
                    cuda_version=torch.version.cuda,
                    compute_capability=f"{torch.cuda.get_device_capability()[0]}.{torch.cuda.get_device_capability()[1]}",
                    is_available=True
                )
                
                logger.info(f"GPU detectada: {gpu_name} ({total_memory:.1f}GB)")
            else:
                logger.warning("CUDA não disponível")
                
        except ImportError:
            logger.warning("PyTorch não instalado")
        except Exception as e:
            logger.error(f"Erro ao detectar CUDA: {e}")
        
        # Verificar CuPy
        try:
            import cupy as cp
            # Teste básico
            test_array = cp.array([1, 2, 3])
            self.cupy_available = True
            logger.info("CuPy disponível para computação científica")
        except ImportError:
            logger.info("CuPy não instalado (opcional)")
        except Exception as e:
            logger.warning(f"CuPy não funcional: {e}")
        
        # Verificar CuDF/Rapids
        try:
            import cudf
            # Teste básico
            test_df = cudf.DataFrame({'a': [1, 2, 3]})
            self.cudf_available = True
            self.rapids_available = True
            logger.info("CuDF/Rapids disponível para DataFrames acelerados")
        except ImportError:
            logger.info("CuDF/Rapids não instalado (opcional)")
        except Exception as e:
            logger.warning(f"CuDF não funcional: {e}")
    
    def get_optimal_device(self) -> str:
        """
        Retorna o dispositivo ótimo para computação
        
        Returns:
            'cuda' se GPU disponível, 'cpu' caso contrário
        """
        if self.config.prefer_gpu and self.cuda_available:
            return 'cuda'
        return 'cpu'
    
    def get_optimal_batch_size(self, base_batch_size: int) -> int:
        """
        Calcula batch size otimizado para GPU
        
        Args:
            base_batch_size: Batch size base para CPU
            
        Returns:
            Batch size otimizado
        """
        if not self.cuda_available:
            return base_batch_size
        
        # Aumentar batch size com base na memória GPU disponível
        if self.gpu_info and self.gpu_info.available_memory_gb > 4:
            multiplier = min(self.config.batch_size_multiplier, 
                           self.gpu_info.available_memory_gb / 4)
            return int(base_batch_size * multiplier)
        
        return base_batch_size
    
    def setup_memory_management(self):
        """Configura gerenciamento de memória GPU"""
        
        if not self.cuda_available:
            return
        
        try:
            import torch
            
            # Configurar fração de memória
            if self.config.memory_fraction < 1.0:
                torch.cuda.set_per_process_memory_fraction(self.config.memory_fraction)
            
            # Habilitar cache de memória
            torch.backends.cudnn.benchmark = True
            
            logger.info(f"Memória GPU configurada: {self.config.memory_fraction*100:.0f}% da capacidade")
            
        except Exception as e:
            logger.warning(f"Erro ao configurar memória GPU: {e}")
    
    def optimize_dataframe_operations(self, df: pd.DataFrame, operation: str = "general") -> Union[pd.DataFrame, Any]:
        """
        Otimiza operações de DataFrame usando GPU quando possível
        
        Args:
            df: DataFrame pandas
            operation: Tipo de operação ('general', 'groupby', 'join', 'transform')
            
        Returns:
            DataFrame otimizado (pode ser CuDF ou pandas)
        """
        
        if not self.cudf_available or len(df) < 10000:  # GPU só vale a pena para datasets grandes
            return df
        
        try:
            import cudf
            
            # Converter para CuDF
            logger.info(f"Convertendo DataFrame para CuDF ({len(df)} registros)")
            cudf_df = cudf.from_pandas(df)
            
            return cudf_df
            
        except Exception as e:
            logger.warning(f"Fallback para pandas: {e}")
            return df
    
    def accelerate_machine_learning(self, 
                                  X: np.ndarray, 
                                  y: Optional[np.ndarray] = None,
                                  model_type: str = "sklearn") -> Tuple[Any, Any, str]:
        """
        Acelera operações de machine learning usando GPU
        
        Args:
            X: Features
            y: Target (opcional)
            model_type: Tipo de modelo ('sklearn', 'lightgbm', 'xgboost')
            
        Returns:
            Tuple: (X_gpu, y_gpu, device_used)
        """
        
        if not self.cuda_available:
            return X, y, "cpu"
        
        try:
            import torch
            
            # Converter para tensors GPU
            device = torch.device('cuda')
            X_tensor = torch.from_numpy(X.astype(np.float32)).to(device)
            
            y_tensor = None
            if y is not None:
                y_tensor = torch.from_numpy(y.astype(np.float32)).to(device)
            
            logger.info(f"Dados movidos para GPU: {X.shape}")
            return X_tensor, y_tensor, "cuda"
            
        except Exception as e:
            logger.warning(f"Fallback para CPU no ML: {e}")
            return X, y, "cpu"
    
    def create_gpu_pipeline(self, operations: List[str]) -> Dict[str, Any]:
        """
        Cria pipeline otimizado para GPU
        
        Args:
            operations: Lista de operações ('preprocess', 'train', 'predict')
            
        Returns:
            Configuração de pipeline GPU
        """
        
        pipeline_config = {
            'device': self.get_optimal_device(),
            'batch_size_multiplier': self.config.batch_size_multiplier,
            'precision': self.config.precision,
            'memory_efficient': True,
            'operations': {}
        }
        
        for op in operations:
            if op == 'preprocess':
                pipeline_config['operations'][op] = {
                    'use_cudf': self.cudf_available,
                    'use_cupy': self.cupy_available,
                    'parallel_workers': self._get_optimal_workers()
                }
            elif op == 'train':
                pipeline_config['operations'][op] = {
                    'device': self.get_optimal_device(),
                    'mixed_precision': self.config.precision == "mixed",
                    'batch_size': self.get_optimal_batch_size(512)
                }
            elif op == 'predict':
                pipeline_config['operations'][op] = {
                    'device': self.get_optimal_device(),
                    'batch_inference': True,
                    'optimize_for_inference': True
                }
        
        return pipeline_config
    
    def _get_optimal_workers(self) -> int:
        """Calcula número ótimo de workers"""
        
        if self.cuda_available:
            # Com GPU, menos workers CPU são necessários
            return min(4, os.cpu_count() // 2)
        else:
            # Sem GPU, usar mais workers CPU
            return min(8, os.cpu_count())
    
    def benchmark_performance(self, test_size: int = 100000) -> Dict[str, float]:
        """
        Faz benchmark de performance GPU vs CPU
        
        Args:
            test_size: Tamanho do dataset de teste
            
        Returns:
            Resultados do benchmark
        """
        
        results = {
            'cpu_time': 0.0,
            'gpu_time': 0.0,
            'speedup': 1.0,
            'memory_used_gb': 0.0
        }
        
        # Criar dados de teste
        X = np.random.randn(test_size, 100).astype(np.float32)
        
        import time
        
        # Benchmark CPU
        start_time = time.time()
        # Operação simples: multiplicação de matriz
        result_cpu = np.dot(X, X.T)
        cpu_time = time.time() - start_time
        results['cpu_time'] = cpu_time
        
        # Benchmark GPU (se disponível)
        if self.cuda_available:
            try:
                import torch
                
                device = torch.device('cuda')
                X_gpu = torch.from_numpy(X).to(device)
                
                # Warm-up
                _ = torch.mm(X_gpu, X_gpu.T)
                torch.cuda.synchronize()
                
                start_time = time.time()
                result_gpu = torch.mm(X_gpu, X_gpu.T)
                torch.cuda.synchronize()
                gpu_time = time.time() - start_time
                
                results['gpu_time'] = gpu_time
                results['speedup'] = cpu_time / gpu_time if gpu_time > 0 else 1.0
                results['memory_used_gb'] = torch.cuda.memory_allocated() / (1024**3)
                
            except Exception as e:
                logger.error(f"Erro no benchmark GPU: {e}")
        
        logger.info(f"Benchmark: CPU {cpu_time:.3f}s, GPU {results['gpu_time']:.3f}s, Speedup: {results['speedup']:.2f}x")
        
        return results
    
    def install_gpu_dependencies(self) -> Dict[str, bool]:
        """
        Instala dependências GPU automaticamente
        
        Returns:
            Status da instalação de cada biblioteca
        """
        
        installation_status = {}
        
        # Lista de pacotes para instalar
        gpu_packages = {
            'torch': 'torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118',
            'cupy': 'cupy-cuda11x',
            'cudf': 'cudf-cu11 --extra-index-url=https://pypi.nvidia.com',
            'rapids': 'rapids-cudf-cu11 --extra-index-url=https://pypi.nvidia.com'
        }
        
        import subprocess
        
        for package, install_cmd in gpu_packages.items():
            try:
                logger.info(f"Instalando {package}...")
                
                # Executar instalação
                result = subprocess.run(
                    f"pip install {install_cmd}",
                    shell=True,
                    capture_output=True,
                    text=True
                )
                
                if result.returncode == 0:
                    installation_status[package] = True
                    logger.info(f"✅ {package} instalado com sucesso")
                else:
                    installation_status[package] = False
                    logger.error(f"❌ Erro ao instalar {package}: {result.stderr}")
                    
            except Exception as e:
                installation_status[package] = False
                logger.error(f"❌ Exceção ao instalar {package}: {e}")
        
        return installation_status
    
    def get_system_info(self) -> Dict[str, Any]:
        """Retorna informações completas do sistema GPU"""
        
        system_info = {
            'gpu_accelerator_enabled': self.config.enabled,
            'cuda_available': self.cuda_available,
            'pytorch_available': self.pytorch_available,
            'cupy_available': self.cupy_available,
            'cudf_available': self.cudf_available,
            'rapids_available': self.rapids_available,
            'optimal_device': self.get_optimal_device(),
            'gpu_info': self.gpu_info.__dict__ if self.gpu_info else None,
            'config': self.config.__dict__
        }
        
        # Adicionar informações do sistema
        try:
            import torch
            if self.cuda_available:
                system_info['cuda_version'] = torch.version.cuda
                system_info['gpu_count'] = torch.cuda.device_count()
                system_info['current_gpu'] = torch.cuda.current_device()
        except:
            pass
        
        return system_info


# Classes específicas para diferentes tipos de aceleração

class GPUDataProcessor:
    """Processador de dados acelerado por GPU"""
    
    def __init__(self, accelerator: GPUAccelerator):
        self.accelerator = accelerator
    
    def process_large_dataframe(self, df: pd.DataFrame, operations: List[str]) -> pd.DataFrame:
        """
        Processa DataFrame grande usando GPU
        
        Args:
            df: DataFrame para processar
            operations: Lista de operações ('groupby', 'merge', 'transform')
            
        Returns:
            DataFrame processado
        """
        
        if not self.accelerator.cudf_available or len(df) < 50000:
            return self._process_with_pandas(df, operations)
        
        try:
            import cudf
            
            logger.info(f"Processando {len(df)} registros com CuDF")
            
            # Converter para CuDF
            cudf_df = cudf.from_pandas(df)
            
            # Aplicar operações
            for operation in operations:
                if operation == 'deduplicate':
                    cudf_df = cudf_df.drop_duplicates()
                elif operation == 'sort':
                    if len(cudf_df.columns) > 0:
                        cudf_df = cudf_df.sort_values(cudf_df.columns[0])
                elif operation == 'fillna':
                    cudf_df = cudf_df.fillna(0)
                elif operation == 'normalize':
                    numeric_cols = cudf_df.select_dtypes(include=[float, int]).columns
                    for col in numeric_cols:
                        cudf_df[col] = (cudf_df[col] - cudf_df[col].mean()) / cudf_df[col].std()
            
            # Converter de volta para pandas
            result_df = cudf_df.to_pandas()
            logger.info("Processamento CuDF concluído")
            
            return result_df
            
        except Exception as e:
            logger.warning(f"Fallback para pandas: {e}")
            return self._process_with_pandas(df, operations)
    
    def _process_with_pandas(self, df: pd.DataFrame, operations: List[str]) -> pd.DataFrame:
        """Processamento fallback com pandas"""
        
        logger.info(f"Processando {len(df)} registros com pandas")
        
        for operation in operations:
            if operation == 'deduplicate':
                df = df.drop_duplicates()
            elif operation == 'sort':
                if len(df.columns) > 0:
                    df = df.sort_values(df.columns[0])
            elif operation == 'fillna':
                df = df.fillna(0)
            elif operation == 'normalize':
                numeric_cols = df.select_dtypes(include=[float, int]).columns
                for col in numeric_cols:
                    df[col] = (df[col] - df[col].mean()) / df[col].std()
        
        return df

class GPUMLAccelerator:
    """Acelerador de machine learning para GPU"""
    
    def __init__(self, accelerator: GPUAccelerator):
        self.accelerator = accelerator
    
    def train_model_gpu(self, X: np.ndarray, y: np.ndarray, model_type: str = "random_forest") -> Any:
        """
        Treina modelo usando GPU quando possível
        
        Args:
            X: Features
            y: Target
            model_type: Tipo de modelo
            
        Returns:
            Modelo treinado
        """
        
        if not self.accelerator.cuda_available:
            return self._train_cpu_fallback(X, y, model_type)
        
        try:
            if model_type == "neural_network":
                return self._train_neural_network_gpu(X, y)
            elif model_type == "random_forest":
                return self._train_random_forest_gpu(X, y)
            else:
                return self._train_cpu_fallback(X, y, model_type)
                
        except Exception as e:
            logger.warning(f"Erro no treinamento GPU: {e}")
            return self._train_cpu_fallback(X, y, model_type)
    
    def _train_neural_network_gpu(self, X: np.ndarray, y: np.ndarray) -> Any:
        """Treina rede neural simples em GPU"""
        
        import torch
        import torch.nn as nn
        import torch.optim as optim
        
        device = torch.device('cuda')
        
        # Converter dados
        X_tensor = torch.from_numpy(X.astype(np.float32)).to(device)
        y_tensor = torch.from_numpy(y.astype(np.float32)).to(device)
        
        # Definir modelo simples
        class SimpleNN(nn.Module):
            def __init__(self, input_size, hidden_size=64):
                super(SimpleNN, self).__init__()
                self.fc1 = nn.Linear(input_size, hidden_size)
                self.fc2 = nn.Linear(hidden_size, hidden_size)
                self.fc3 = nn.Linear(hidden_size, 1)
                self.relu = nn.ReLU()
                self.dropout = nn.Dropout(0.2)
            
            def forward(self, x):
                x = self.relu(self.fc1(x))
                x = self.dropout(x)
                x = self.relu(self.fc2(x))
                x = self.dropout(x)
                x = self.fc3(x)
                return x
        
        model = SimpleNN(X.shape[1]).to(device)
        criterion = nn.MSELoss()
        optimizer = optim.Adam(model.parameters(), lr=0.001)
        
        # Treinamento
        model.train()
        batch_size = self.accelerator.get_optimal_batch_size(128)
        
        for epoch in range(50):  # Treinamento rápido
            for i in range(0, len(X_tensor), batch_size):
                batch_X = X_tensor[i:i+batch_size]
                batch_y = y_tensor[i:i+batch_size].unsqueeze(1)
                
                optimizer.zero_grad()
                outputs = model(batch_X)
                loss = criterion(outputs, batch_y)
                loss.backward()
                optimizer.step()
        
        logger.info("Rede neural treinada em GPU")
        return model
    
    def _train_random_forest_gpu(self, X: np.ndarray, y: np.ndarray) -> Any:
        """Treina Random Forest usando GPU (cuML se disponível)"""
        
        try:
            # Tentar usar cuML (Rapids ML)
            from cuml.ensemble import RandomForestRegressor as cuRandomForest
            import cudf
            
            # Converter para CuDF
            X_cudf = cudf.DataFrame(X)
            y_cudf = cudf.Series(y)
            
            # Treinar modelo
            model = cuRandomForest(
                n_estimators=100,
                max_depth=10,
                random_state=42
            )
            
            model.fit(X_cudf, y_cudf)
            logger.info("Random Forest treinado com cuML (GPU)")
            
            return model
            
        except ImportError:
            logger.info("cuML não disponível, usando scikit-learn")
            return self._train_cpu_fallback(X, y, "random_forest")
    
    def _train_cpu_fallback(self, X: np.ndarray, y: np.ndarray, model_type: str) -> Any:
        """Fallback para treinamento em CPU"""
        
        from sklearn.ensemble import RandomForestRegressor
        from sklearn.linear_model import LinearRegression
        
        if model_type == "random_forest":
            model = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
        else:
            model = LinearRegression()
        
        model.fit(X, y)
        logger.info(f"Modelo {model_type} treinado em CPU")
        
        return model


def demo_gpu_acceleration():
    """Demonstração do sistema de aceleração GPU"""
    
    print("🔥 DEMO: Aceleração GPU para ETL e IA")
    print("=" * 50)
    
    # Inicializar acelerador
    config = GPUAccelerationConfig(
        enabled=True,
        prefer_gpu=True,
        memory_fraction=0.7,
        batch_size_multiplier=2.0
    )
    
    accelerator = GPUAccelerator(config)
    
    # Mostrar informações do sistema
    print("🖥️ Informações do sistema:")
    system_info = accelerator.get_system_info()
    for key, value in system_info.items():
        if key != 'gpu_info':
            print(f"  {key}: {value}")
    
    if system_info['gpu_info']:
        print(f"\n🚀 GPU Detectada:")
        gpu_info = system_info['gpu_info']
        print(f"  Nome: {gpu_info['name']}")
        print(f"  Memória: {gpu_info['total_memory_gb']:.1f}GB")
        print(f"  CUDA: {gpu_info['cuda_version']}")
    
    # Benchmark de performance
    print(f"\n⚡ Benchmark de performance:")
    benchmark_results = accelerator.benchmark_performance(50000)
    print(f"  CPU: {benchmark_results['cpu_time']:.3f}s")
    print(f"  GPU: {benchmark_results['gpu_time']:.3f}s")
    print(f"  Speedup: {benchmark_results['speedup']:.2f}x")
    
    # Demo de processamento de dados
    print(f"\n📊 Demo: Processamento de dados acelerado")
    
    # Criar dataset de teste
    test_data = pd.DataFrame({
        'id': range(100000),
        'value': np.random.randn(100000),
        'category': np.random.choice(['A', 'B', 'C'], 100000),
        'score': np.random.uniform(0, 100, 100000)
    })
    
    print(f"Dataset de teste: {len(test_data)} registros")
    
    # Processamento acelerado
    processor = GPUDataProcessor(accelerator)
    
    import time
    start_time = time.time()
    
    processed_data = processor.process_large_dataframe(
        test_data, 
        ['deduplicate', 'sort', 'normalize']
    )
    
    processing_time = time.time() - start_time
    
    print(f"Processamento concluído em {processing_time:.3f}s")
    print(f"Registros finais: {len(processed_data)}")
    
    # Demo de machine learning acelerado
    print(f"\n🤖 Demo: Machine Learning acelerado")
    
    # Dados para ML
    X = np.random.randn(10000, 20).astype(np.float32)
    y = np.random.randn(10000).astype(np.float32)
    
    ml_accelerator = GPUMLAccelerator(accelerator)
    
    start_time = time.time()
    model = ml_accelerator.train_model_gpu(X, y, "neural_network")
    training_time = time.time() - start_time
    
    print(f"Modelo treinado em {training_time:.3f}s")
    
    # Pipeline GPU
    print(f"\n🔧 Pipeline GPU otimizado:")
    pipeline_config = accelerator.create_gpu_pipeline(['preprocess', 'train', 'predict'])
    
    print(f"  Dispositivo: {pipeline_config['device']}")
    print(f"  Batch size multiplicador: {pipeline_config['batch_size_multiplier']}")
    print(f"  Operações configuradas: {len(pipeline_config['operations'])}")
    
    print(f"\n✅ Demo concluída!")


if __name__ == "__main__":
    demo_gpu_acceleration()