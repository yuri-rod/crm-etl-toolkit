#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Instalador Automático de Dependências GPU
CRM ETL

Script para instalar automaticamente todas as dependências necessárias
para aceleração GPU nos workflows ETL e IA.
"""

import os
import sys
import subprocess
import logging
import platform
from typing import List, Dict, Tuple

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class GPUDependencyInstaller:
    """Instalador inteligente de dependências GPU"""
    
    def __init__(self):
        self.system_info = self._detect_system()
        self.cuda_version = self._detect_cuda_version()
        self.installation_log = []
        
    def _detect_system(self) -> Dict[str, str]:
        """Detecta informações do sistema"""
        
        info = {
            'os': platform.system().lower(),
            'architecture': platform.machine().lower(),
            'python_version': f"{sys.version_info.major}.{sys.version_info.minor}"
        }
        
        logger.info(f"Sistema detectado: {info}")
        return info
    
    def _detect_cuda_version(self) -> str:
        """Detecta versão do CUDA instalada"""
        
        try:
            # Tentar detectar CUDA via nvidia-smi
            result = subprocess.run(['nvidia-smi'], capture_output=True, text=True)
            if result.returncode == 0:
                output = result.stdout
                # Extrair versão CUDA do output
                lines = output.split('\n')
                for line in lines:
                    if 'CUDA Version:' in line:
                        cuda_version = line.split('CUDA Version:')[1].strip().split()[0]
                        logger.info(f"CUDA detectado: {cuda_version}")
                        return cuda_version
            
            # Fallback para CUDA 11.8 (mais comum)
            logger.warning("CUDA não detectado automaticamente, usando versão padrão 11.8")
            return "11.8"
            
        except Exception as e:
            logger.warning(f"Erro ao detectar CUDA: {e}")
            return "11.8"
    
    def _get_cuda_suffix(self) -> str:
        """Retorna sufixo CUDA apropriado para pacotes"""
        
        major_version = self.cuda_version.split('.')[0]
        minor_version = self.cuda_version.split('.')[1] if '.' in self.cuda_version else '0'
        
        # Mapear versões CUDA para sufixos de pacotes
        cuda_mappings = {
            '11': {
                '0': 'cu110',
                '1': 'cu111', 
                '2': 'cu112',
                '3': 'cu113',
                '4': 'cu114',
                '5': 'cu115',
                '6': 'cu116',
                '7': 'cu117',
                '8': 'cu118'
            },
            '12': {
                '0': 'cu120',
                '1': 'cu121',
                '2': 'cu122'
            }
        }
        
        if major_version in cuda_mappings and minor_version in cuda_mappings[major_version]:
            return cuda_mappings[major_version][minor_version]
        else:
            # Default para CUDA 11.8
            return 'cu118'
    
    def install_pytorch(self) -> bool:
        """Instala PyTorch com suporte CUDA"""
        
        cuda_suffix = self._get_cuda_suffix()
        
        commands = [
            f"pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/{cuda_suffix}"
        ]
        
        print("🔥 Instalando PyTorch com suporte CUDA...")
        
        for cmd in commands:
            success = self._run_command(cmd, "PyTorch")
            if not success:
                return False
        
        return self._verify_pytorch_installation()
    
    def install_cupy(self) -> bool:
        """Instala CuPy para computação científica GPU"""
        
        cuda_major = self.cuda_version.split('.')[0]
        
        # Mapear versões principais do CUDA
        cupy_packages = {
            '11': 'cupy-cuda11x',
            '12': 'cupy-cuda12x'
        }
        
        package = cupy_packages.get(cuda_major, 'cupy-cuda11x')
        
        commands = [
            f"pip install {package}"
        ]
        
        print("🧮 Instalando CuPy para computação científica...")
        
        for cmd in commands:
            success = self._run_command(cmd, "CuPy")
            if not success:
                return False
        
        return self._verify_cupy_installation()
    
    def install_rapids(self) -> bool:
        """Instala Rapids (CuDF) para DataFrames acelerados"""
        
        cuda_major = self.cuda_version.split('.')[0]
        
        # Rapids é mais restritivo com versões
        rapids_packages = {
            '11': 'cudf-cu11',
            '12': 'cudf-cu12'
        }
        
        package = rapids_packages.get(cuda_major, 'cudf-cu11')
        
        commands = [
            f"pip install {package} --extra-index-url=https://pypi.nvidia.com",
            f"pip install rapids-cuml-cu{cuda_major} --extra-index-url=https://pypi.nvidia.com"
        ]
        
        print("🚀 Instalando Rapids (CuDF/CuML) para DataFrames acelerados...")
        
        success_count = 0
        for cmd in commands:
            if self._run_command(cmd, "Rapids", critical=False):
                success_count += 1
        
        # Rapids é opcional, então success parcial é aceitável
        return success_count > 0
    
    def install_additional_packages(self) -> bool:
        """Instala pacotes adicionais para otimização"""
        
        additional_packages = [
            "numba",  # Compilação JIT
            "scikit-learn",  # ML básico
            "scipy",  # Computação científica
            "psutil",  # Monitor de sistema
            "memory-profiler",  # Profiling de memória
            "nvidia-ml-py3"  # Monitoring NVIDIA
        ]
        
        print("📦 Instalando pacotes adicionais de otimização...")
        
        success_count = 0
        for package in additional_packages:
            cmd = f"pip install {package}"
            if self._run_command(cmd, package, critical=False):
                success_count += 1
        
        return success_count >= len(additional_packages) // 2  # Pelo menos 50%
    
    def _run_command(self, command: str, package_name: str, critical: bool = True) -> bool:
        """Executa comando de instalação"""
        
        logger.info(f"Executando: {command}")
        
        try:
            result = subprocess.run(
                command.split(),
                capture_output=True,
                text=True,
                timeout=600  # 10 minutos timeout
            )
            
            if result.returncode == 0:
                logger.info(f"✅ {package_name} instalado com sucesso")
                self.installation_log.append(f"✅ {package_name}: Sucesso")
                return True
            else:
                error_msg = f"❌ Erro ao instalar {package_name}: {result.stderr}"
                logger.error(error_msg)
                self.installation_log.append(f"❌ {package_name}: {result.stderr[:100]}")
                
                if not critical:
                    logger.warning(f"Continuando sem {package_name} (não crítico)")
                    return False
                
                return False
                
        except subprocess.TimeoutExpired:
            error_msg = f"❌ Timeout ao instalar {package_name}"
            logger.error(error_msg)
            self.installation_log.append(f"❌ {package_name}: Timeout")
            return False
            
        except Exception as e:
            error_msg = f"❌ Exceção ao instalar {package_name}: {e}"
            logger.error(error_msg)
            self.installation_log.append(f"❌ {package_name}: {str(e)[:100]}")
            return False
    
    def _verify_pytorch_installation(self) -> bool:
        """Verifica se PyTorch foi instalado corretamente"""
        
        try:
            import torch
            
            print(f"🔍 Verificando PyTorch...")
            print(f"  Versão: {torch.__version__}")
            print(f"  CUDA disponível: {torch.cuda.is_available()}")
            
            if torch.cuda.is_available():
                print(f"  GPU detectada: {torch.cuda.get_device_name(0)}")
                print(f"  Versão CUDA: {torch.version.cuda}")
                return True
            else:
                logger.warning("PyTorch instalado mas CUDA não disponível")
                return False
                
        except ImportError:
            logger.error("PyTorch não pode ser importado")
            return False
    
    def _verify_cupy_installation(self) -> bool:
        """Verifica se CuPy foi instalado corretamente"""
        
        try:
            import cupy as cp
            
            print(f"🔍 Verificando CuPy...")
            print(f"  Versão: {cp.__version__}")
            
            # Teste básico
            test_array = cp.array([1, 2, 3])
            result = cp.sum(test_array)
            
            print(f"  Teste básico: ✅ Funcional")
            return True
            
        except ImportError:
            logger.warning("CuPy não pode ser importado")
            return False
        except Exception as e:
            logger.warning(f"CuPy instalado mas não funcional: {e}")
            return False
    
    def _verify_rapids_installation(self) -> bool:
        """Verifica se Rapids foi instalado corretamente"""
        
        try:
            import cudf
            
            print(f"🔍 Verificando Rapids (CuDF)...")
            print(f"  Versão CuDF: {cudf.__version__}")
            
            # Teste básico
            test_df = cudf.DataFrame({'a': [1, 2, 3], 'b': [4, 5, 6]})
            result = test_df.sum()
            
            print(f"  Teste básico: ✅ Funcional")
            return True
            
        except ImportError:
            logger.warning("Rapids (CuDF) não pode ser importado")
            return False
        except Exception as e:
            logger.warning(f"Rapids instalado mas não funcional: {e}")
            return False
    
    def run_full_installation(self) -> bool:
        """Executa instalação completa"""
        
        print("🚀 INSTALAÇÃO AUTOMÁTICA DE DEPENDÊNCIAS GPU")
        print("CRM ETL")
        print("=" * 60)
        
        print(f"Sistema: {self.system_info}")
        print(f"CUDA detectado: {self.cuda_version}")
        print(f"Sufixo CUDA: {self._get_cuda_suffix()}")
        print()
        
        results = {}
        
        # 1. Atualizar pip
        print("📦 Atualizando pip...")
        self._run_command("pip install --upgrade pip", "pip")
        
        # 2. Instalar PyTorch
        results['pytorch'] = self.install_pytorch()
        
        # 3. Instalar CuPy
        results['cupy'] = self.install_cupy()
        
        # 4. Instalar Rapids (opcional)
        results['rapids'] = self.install_rapids()
        
        # 5. Instalar pacotes adicionais
        results['additional'] = self.install_additional_packages()
        
        # Resumo final
        print("\n📊 RESUMO DA INSTALAÇÃO")
        print("=" * 40)
        
        for component, success in results.items():
            status = "✅ Instalado" if success else "❌ Falhou"
            print(f"{component.capitalize()}: {status}")
        
        print(f"\nLog detalhado:")
        for entry in self.installation_log:
            print(f"  {entry}")
        
        # Verificação final
        print(f"\n🔍 VERIFICAÇÃO FINAL")
        print("=" * 30)
        
        verification_results = {}
        verification_results['pytorch'] = self._verify_pytorch_installation()
        verification_results['cupy'] = self._verify_cupy_installation()
        verification_results['rapids'] = self._verify_rapids_installation()
        
        success_count = sum(verification_results.values())
        total_critical = 2  # PyTorch e CuPy são críticos
        
        if success_count >= total_critical:
            print(f"\n🎉 INSTALAÇÃO CONCLUÍDA COM SUCESSO!")
            print(f"Componentes funcionais: {success_count}/3")
            return True
        else:
            print(f"\n⚠️ INSTALAÇÃO PARCIALMENTE CONCLUÍDA")
            print(f"Componentes funcionais: {success_count}/3")
            print(f"Sistema funcionará com capacidades reduzidas")
            return False
    
    def create_gpu_config_file(self):
        """Cria arquivo de configuração GPU"""
        
        config = {
            "gpu_acceleration": {
                "enabled": True,
                "prefer_gpu": True,
                "memory_fraction": 0.8,
                "fallback_to_cpu": True,
                "batch_size_multiplier": 2.0,
                "precision": "float32"
            },
            "system_info": {
                "cuda_version": self.cuda_version,
                "cuda_suffix": self._get_cuda_suffix(),
                "os": self.system_info['os'],
                "architecture": self.system_info['architecture']
            },
            "dependencies": {
                "pytorch_installed": self._verify_pytorch_installation(),
                "cupy_installed": self._verify_cupy_installation(),
                "rapids_installed": self._verify_rapids_installation()
            },
            "installation_log": self.installation_log
        }
        
        import json
        config_file = "gpu_config.json"
        
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        print(f"📄 Configuração salva em: {config_file}")


def main():
    """Função principal"""
    
    if len(sys.argv) > 1 and sys.argv[1] == '--check-only':
        # Modo verificação apenas
        installer = GPUDependencyInstaller()
        
        print("🔍 VERIFICAÇÃO DE DEPENDÊNCIAS GPU")
        print("=" * 50)
        
        pytorch_ok = installer._verify_pytorch_installation()
        cupy_ok = installer._verify_cupy_installation()
        rapids_ok = installer._verify_rapids_installation()
        
        print(f"\nStatus:")
        print(f"  PyTorch: {'✅' if pytorch_ok else '❌'}")
        print(f"  CuPy: {'✅' if cupy_ok else '❌'}")
        print(f"  Rapids: {'✅' if rapids_ok else '❌'}")
        
        if pytorch_ok and cupy_ok:
            print(f"\n🎉 Sistema pronto para aceleração GPU!")
        else:
            print(f"\n⚠️ Execute sem --check-only para instalar dependências")
        
        return
    
    # Verificar se está rodando como administrador (recomendado)
    try:
        import ctypes
        is_admin = ctypes.windll.shell32.IsUserAnAdmin()
        if not is_admin:
            print("⚠️ AVISO: Execute como administrador para melhor compatibilidade")
            print("Continuando em 5 segundos...")
            import time
            time.sleep(5)
    except:
        pass
    
    # Executar instalação
    installer = GPUDependencyInstaller()
    success = installer.run_full_installation()
    
    # Criar arquivo de configuração
    installer.create_gpu_config_file()
    
    if success:
        print(f"\n🚀 PRÓXIMOS PASSOS:")
        print(f"1. Reinicie o terminal/IDE")
        print(f"2. Execute: python demo_gpu_etl_completo.py")
        print(f"3. Configure pipelines ETL para usar GPU")
        print(f"4. Monitore performance e uso de memória")
    else:
        print(f"\n🔧 PROBLEMAS NA INSTALAÇÃO:")
        print(f"1. Verifique se CUDA está instalado")
        print(f"2. Atualize drivers NVIDIA")
        print(f"3. Execute como administrador")
        print(f"4. Consulte logs de erro acima")

if __name__ == "__main__":
    main()