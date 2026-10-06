#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=================================================
--- API Server para Sistema ETL Inteligente ---
=================================================

Servidor FastAPI que conecta a interface web com o backend ETL inteligente.
Fornece endpoints para execução de pipelines e download de resultados.

Desenvolvido para CRM ETL
"""

import os
import sys
import json
import asyncio
import logging
import tempfile
import traceback
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
import pandas as pd
import numpy as np
from concurrent.futures import ThreadPoolExecutor
import time

# FastAPI e dependências
try:
    from fastapi import FastAPI, HTTPException, UploadFile, File, Form, BackgroundTasks, status
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import JSONResponse, FileResponse, StreamingResponse
    from fastapi.staticfiles import StaticFiles
    from pydantic import BaseModel
    import uvicorn
    HAS_FASTAPI = True
except ImportError:
    print("❌ FastAPI não instalado. Execute: pip install fastapi uvicorn python-multipart")
    HAS_FASTAPI = False
    sys.exit(1)

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Modelos Pydantic para API
class PipelineRequest(BaseModel):
    mode: str  # 'train' ou 'batch-predict'
    target_column: str = 'qualidade_lead'
    model_dir: str = './production_models/'
    enable_enrichment: bool = False
    output_filename: str = "predictions_output.csv"

class PipelineStatus(BaseModel):
    status: str
    progress: float
    message: str
    details: Optional[Dict] = None

class PipelineResponse(BaseModel):
    pipeline_id: str
    status: str
    message: str

# Estado global da aplicação
app_state = {
    'pipelines': {},  # Armazena status de pipelines em execução
    'statistics': {
        'total_pipelines_executed': 0,
        'total_records_processed': 0,
        'total_files_processed': 0
    }
}

# Criar aplicação FastAPI
app = FastAPI(
    title="CRM ETL API | CRM ETL",
    description="API para Sistema ETL Inteligente com processamento de dados",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, especificar origins específicos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Montar arquivos estáticos (para servir o frontend)
# Mount the static folder for dev/prod parity with App Engine handlers
static_path = Path(__file__).parent.parent / "static"
if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

# Criar diretórios necessários
def setup_directories():
    """Configura diretórios necessários para o sistema"""
    directories = [
        "production_models",
        "logs",
        "data/input",
        "data/output",
        "temp"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)

# Inicialização da aplicação
@app.on_event("startup")
async def startup_event():
    """Inicialização dos componentes"""
    logger.info("🚀 CRM - Inicializando API ETL Inteligente...")
    setup_directories()
    logger.info("✅ CRM ETL API pronto para uso!")

# Endpoint raiz - serve a interface web
@app.get("/")
async def read_root():
    """Serve a página principal"""
    index_path = static_path / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path), media_type="text/html")
    else:
        return JSONResponse({
            "message": "CRM ETL API | CRM ETL",
            "version": "1.0.0",
            "status": "operational",
            "endpoints": ["/docs", "/etl/run", "/etl/status", "/etl/download"]
        })

# Função para simular processamento ETL
async def process_etl_pipeline(
    pipeline_id: str,
    input_file: Path,
    mode: str,
    target_column: str,
    model_dir: str,
    enable_enrichment: bool,
    output_filename: str
):
    """
    Processa pipeline ETL em background
    """
    
    def update_status(status: str, progress: float, message: str, details: Optional[Dict] = None):
        app_state['pipelines'][pipeline_id].update({
            'status': status,
            'progress': progress,
            'message': message,
            'last_update': datetime.now().isoformat()
        })
        if details:
            app_state['pipelines'][pipeline_id]['details'] = details

    try:
        # Etapa 1: Carregando dados
        update_status('carregando', 10.0, 'CRM - Carregando dados do arquivo...')
        await asyncio.sleep(1)
        
        # Simular carregamento do arquivo
        if input_file.suffix.lower() == '.csv':
            df = pd.read_csv(input_file)
        elif input_file.suffix.lower() in ['.xlsx', '.xls']:
            df = pd.read_excel(input_file)
        else:
            raise ValueError(f"Formato de arquivo não suportado: {input_file.suffix}")
        
        logger.info(f"Arquivo carregado: {len(df)} registros, {len(df.columns)} colunas")

        # Etapa 2: Limpeza e validação
        update_status('processando', 30.0, 'CRM - Limpando e validando dados...')
        await asyncio.sleep(2)
        
        # Simular limpeza de dados
        initial_records = len(df)
        df = df.dropna(thresh=len(df.columns) * 0.5)  # Remove linhas com muitos valores nulos
        cleaned_records = len(df)
        
        # Etapa 3: Feature Engineering
        update_status('executando', 50.0, 'CRM - Criando features...')
        await asyncio.sleep(2)
        
        # Simular criação de features
        features_created = []
        if 'email' in df.columns:
            df['email_domain'] = df['email'].str.split('@').str[1] if 'email' in df.columns else None
            features_created.append('email_domain')
        
        if 'telefone' in df.columns:
            df['tem_telefone'] = df['telefone'].notna().astype(int)
            features_created.append('tem_telefone')
        
        # Etapa 4: Processamento do modelo
        update_status('treinando' if mode == 'train' else 'predizendo', 70.0, 
                     'CRM - Processando modelo de ML...')
        await asyncio.sleep(3)
        
        # Preparar diretório de saída
        output_dir = Path("data/output")
        output_dir.mkdir(exist_ok=True)
        output_file = output_dir / f"{pipeline_id}_{output_filename}"
        
        if mode == 'train':
            # Modo treinamento
            if target_column not in df.columns:
                # Criar coluna alvo simulada se não existir
                df[target_column] = np.random.choice(['Alto', 'Médio', 'Baixo'], len(df), p=[0.3, 0.5, 0.2])
            
            # Simular treinamento
            accuracy = round(np.random.uniform(0.75, 0.95), 3)
            
            # Salvar dados processados
            df.to_csv(output_file, index=False, sep=';', encoding='utf-8-sig')
            
            training_details = {
                'model_type': 'RandomForestClassifier',
                'target_column': target_column,
                'features_used': len(features_created),
                'records_trained': len(df),
                'accuracy': accuracy
            }
            
            details = {
                'output_file': str(output_file),
                'training_details': training_details,
                'data_overview': {
                    'initial_records': initial_records,
                    'cleaned_records': cleaned_records,
                    'features_created': features_created
                }
            }
            
        elif mode == 'batch-predict':
            # Modo predição
            # Simular predições
            predictions = np.random.choice(['Alto', 'Médio', 'Baixo'], len(df), p=[0.3, 0.5, 0.2])
            confidence = np.random.uniform(0.6, 0.99, len(df))
            
            df['qualidade_predita'] = predictions
            df['confianca_predicao'] = confidence
            
            # Salvar resultados
            df.to_csv(output_file, index=False, sep=';', encoding='utf-8-sig')
            
            # Estatísticas das predições
            prediction_summary = pd.Series(predictions).value_counts().to_dict()
            
            prediction_details = {
                'total_predictions': len(df),
                'prediction_summary': prediction_summary,
                'confidence_stats': {
                    'mean_confidence': float(confidence.mean()),
                    'high_confidence_count': int((confidence > 0.8).sum())
                }
            }
            
            details = {
                'output_file': str(output_file),
                'prediction_details': prediction_details,
                'data_overview': {
                    'initial_records': initial_records,
                    'cleaned_records': cleaned_records,
                    'features_created': features_created
                }
            }
        
        # Etapa 5: Finalização
        update_status('concluida', 100.0, 'CRM - Processamento concluído com sucesso!', details)
        
        # Atualizar estatísticas globais
        app_state['statistics']['total_pipelines_executed'] += 1
        app_state['statistics']['total_records_processed'] += len(df)
        app_state['statistics']['total_files_processed'] += 1
        
        logger.info(f"✅ Pipeline {pipeline_id} concluída com sucesso")
        
    except Exception as e:
        logger.error(f"❌ Erro na pipeline {pipeline_id}: {e}")
        logger.error(traceback.format_exc())
        
        update_status('erro', 0.0, f'CRM - Erro na execução: {str(e)}', {
            'error_type': type(e).__name__,
            'error_details': str(e)
        })

# Endpoint principal: POST /etl/run
@app.post("/etl/run", response_model=PipelineResponse)
async def run_etl_pipeline(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    mode: str = Form(...),
    target_column: str = Form("qualidade_lead"),
    model_dir: str = Form("./production_models/"),
    enable_enrichment: bool = Form(False),
    output_filename: str = Form("predictions_output.csv")
):
    """
    Endpoint principal para executar pipeline ETL
    """
    
    # Validar parâmetros
    if mode not in ['train', 'batch-predict']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Modo deve ser 'train' ou 'batch-predict'"
        )
    
    # Verificar tipo de arquivo
    if not file.filename.lower().endswith(('.csv', '.xlsx', '.xls')):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Formato de arquivo não suportado. Use CSV, XLSX ou XLS."
        )
    
    pipeline_id = str(uuid.uuid4())[:8]
    
    logger.info(f"🚀 CRM - Iniciando pipeline {pipeline_id}")
    logger.info(f"   Modo: {mode}")
    logger.info(f"   Arquivo: {file.filename}")
    logger.info(f"   Enriquecimento: {enable_enrichment}")
    
    # Salvar arquivo temporário
    temp_dir = Path("temp")
    temp_dir.mkdir(exist_ok=True)
    
    input_file_path = temp_dir / f"{pipeline_id}_{file.filename}"
    
    try:
        # Salvar arquivo upload
        content = await file.read()
        with open(input_file_path, "wb") as buffer:
            buffer.write(content)
        
        # Inicializar status
        app_state['pipelines'][pipeline_id] = {
            'status': 'iniciando',
            'progress': 0.0,
            'message': 'Pipeline iniciada...',
            'start_time': datetime.now().isoformat(),
            'file_info': {
                'name': file.filename,
                'size': len(content)
            }
        }
        
        # Executar em background
        background_tasks.add_task(
            process_etl_pipeline,
            pipeline_id,
            input_file_path,
            mode,
            target_column,
            model_dir,
            enable_enrichment,
            output_filename
        )
        
        return PipelineResponse(
            pipeline_id=pipeline_id,
            status="iniciada",
            message="Pipeline iniciada com sucesso. Use /etl/status/{pipeline_id} para acompanhar o progresso."
        )
        
    except Exception as e:
        logger.error(f"❌ Erro ao iniciar pipeline: {e}")
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao iniciar pipeline: {str(e)}"
        )

# Endpoint para acompanhar status da pipeline
@app.get("/etl/status/{pipeline_id}", response_model=PipelineStatus)
async def get_pipeline_status(pipeline_id: str):
    """
    Obtém status de uma pipeline em execução
    """
    
    if pipeline_id not in app_state['pipelines']:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Pipeline não encontrada"
        )
    
    pipeline_data = app_state['pipelines'][pipeline_id]
    
    return PipelineStatus(
        status=pipeline_data['status'],
        progress=pipeline_data['progress'],
        message=pipeline_data['message'],
        details=pipeline_data.get('details')
    )

# Endpoint para download de resultados
@app.get("/etl/download/{pipeline_id}")
async def download_result(pipeline_id: str):
    """
    Download do arquivo resultado de uma pipeline
    """
    
    if pipeline_id not in app_state['pipelines']:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Pipeline não encontrada"
        )
    
    pipeline_data = app_state['pipelines'][pipeline_id]
    
    if pipeline_data['status'] != 'concluida':
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Pipeline ainda não concluída"
        )
    
    if 'details' not in pipeline_data or 'output_file' not in pipeline_data['details']:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Arquivo de resultado não encontrado"
        )
    
    output_file = Path(pipeline_data['details']['output_file'])
    
    if not output_file.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Arquivo não existe"
        )
    
    return FileResponse(
        path=str(output_file),
        media_type='application/octet-stream',
        filename=f"crm_result_{pipeline_id}.csv"
    )

# Endpoint para listar pipelines
@app.get("/etl/pipelines")
async def list_pipelines():
    """
    Lista todas as pipelines executadas
    """
    
    return JSONResponse({
        'pipelines': app_state['pipelines'],
        'statistics': app_state['statistics']
    })

# Endpoint para estatísticas do sistema
@app.get("/etl/stats")
async def get_system_stats():
    """
    Obtém estatísticas do sistema
    """
    
    return JSONResponse({
        'system_stats': app_state['statistics'],
        'active_pipelines': len([p for p in app_state['pipelines'].values() 
                                if p['status'] in ['iniciando', 'carregando', 'processando', 'executando', 'treinando', 'predizendo']]),
        'total_pipelines': len(app_state['pipelines']),
        'uptime': datetime.now().isoformat()
    })

# Endpoint para health check
@app.get("/health")
async def health_check():
    """
    Health check do sistema
    """
    
    return JSONResponse({
        'status': 'healthy',
        'service': 'CRM ETL API',
        'version': '1.0.0',
        'timestamp': datetime.now().isoformat()
    })

# Função para executar o servidor
def run_server(host: str = "127.0.0.1", port: int = 8000, reload: bool = False):
    """
    Executa o servidor FastAPI
    """
    
    print("🚀 CRM ETL - ETL API Server")
    print("=" * 50)
    print(f"📡 Servidor: http://{host}:{port}")
    print(f"📚 Documentação: http://{host}:{port}/docs")
    print(f"🔄 Auto-reload: {reload}")
    print("=" * 50)
    
    uvicorn.run(
        "api_server:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="CRM ETL API Server")
    parser.add_argument("--host", default="127.0.0.1", help="Host do servidor")
    parser.add_argument("--port", type=int, default=8000, help="Porta do servidor")
    parser.add_argument("--reload", action="store_true", help="Auto-reload durante desenvolvimento")
    
    args = parser.parse_args()
    
    run_server(host=args.host, port=args.port, reload=args.reload)
