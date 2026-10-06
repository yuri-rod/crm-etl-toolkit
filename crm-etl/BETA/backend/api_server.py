#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=================================================
--- API Server para Sistema ETL Inteligente ---
=================================================

Servidor FastAPI que conecta a interface web com o backend ETL inteligente.
Fornece endpoints para execução de pipelines, geração de regras IA e monitoramento.

Desenvolvido para CRM ETL
"""

import os
import sys
import json
import asyncio
import logging
import tempfile
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
import pandas as pd
import numpy as np
from concurrent.futures import ThreadPoolExecutor

# FastAPI e dependências
try:
    from fastapi import FastAPI, HTTPException, UploadFile, File, Form, BackgroundTasks
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import JSONResponse, FileResponse
    from fastapi.staticfiles import StaticFiles
    from pydantic import BaseModel
    import uvicorn
    HAS_FASTAPI = True
except ImportError:
    print("❌ FastAPI não instalado. Execute: pip install fastapi uvicorn python-multipart")
    HAS_FASTAPI = False
    sys.exit(1)

# Importar nossos módulos
from unificado import UnifiedCRMPipeline
from ai_rule_generator import AIRuleGenerator
from simple_inference import CRMLeadPredictor

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

class AIRuleRequest(BaseModel):
    requirement: str
    data_context: Optional[Dict] = None

class PipelineStatus(BaseModel):
    status: str
    progress: float
    message: str
    details: Optional[Dict] = None

# Estado global da aplicação
app_state = {
    'pipelines': {},  # Armazena status de pipelines em execução
    'rule_generator': None,
    'statistics': {
        'total_pipelines_executed': 0,
        'total_records_processed': 0,
        'total_ai_rules_generated': 0
    }
}

# Criar aplicação FastAPI
app = FastAPI(
    title="CRM ETL API | CRM ETL",
    description="API para Sistema ETL Inteligente com IA Generativa",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, especificar origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Montar arquivos estáticos
static_path = Path(__file__).parent.parent / "www"
if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

# Inicialização da aplicação
@app.on_event("startup")
async def startup_event():
    """Inicialização dos componentes"""
    logger.info("🚀 CRM - Inicializando API ETL Inteligente...")
    
    # Inicializar gerador de regras IA
    try:
        app_state['rule_generator'] = AIRuleGenerator()
        logger.info("✅ Gerador de regras IA inicializado")
    except Exception as e:
        logger.warning(f"⚠️ Gerador IA não disponível: {e}")
    
    logger.info("✅ CRM ETL API pronto para uso!")

# Endpoint raiz - serve a interface web
@app.get("/")
async def read_root():
    """Serve a página principal"""
    index_path = static_path / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    else:
        return JSONResponse({
            "message": "CRM ETL API | CRM ETL",
            "version": "1.0.0",
            "status": "operational",
            "endpoints": ["/docs", "/pipeline/execute", "/ai/generate-rule"]
        })

# Endpoint para executar pipeline
@app.post("/pipeline/execute")
async def execute_pipeline(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    mode: str = Form(...),
    target_column: str = Form("qualidade_lead"),
    model_dir: str = Form("./production_models/"),
    enable_enrichment: bool = Form(False),
    output_filename: str = Form("predictions_output.csv")
):
    """
    Executa pipeline ETL em background
    """
    
    pipeline_id = f"pipeline_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    logger.info(f"🚀 CRM - Iniciando pipeline {pipeline_id}")
    logger.info(f"   Modo: {mode}")
    logger.info(f"   Arquivo: {file.filename}")
    logger.info(f"   Enriquecimento: {enable_enrichment}")
    
    # Salvar arquivo temporário
    temp_dir = Path(tempfile.gettempdir()) / "crm_etl"
    temp_dir.mkdir(exist_ok=True)
    
    input_file_path = temp_dir / f"{pipeline_id}_{file.filename}"
    
    try:
        # Salvar arquivo upload
        with open(input_file_path, "wb") as buffer:
            content = await file.read()
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
            run_pipeline_background,
            pipeline_id,
            str(input_file_path),
            mode,
            target_column,
            model_dir,
            enable_enrichment,
            output_filename
        )
        
        return JSONResponse({
            "pipeline_id": pipeline_id,
            "status": "iniciada",
            "message": "Pipeline iniciada com sucesso. Use /pipeline/status/{pipeline_id} para acompanhar o progresso."
        })
        
    except Exception as e:
        logger.error(f"❌ Erro ao iniciar pipeline: {e}")
        logger.error(traceback.format_exc())
        
        return JSONResponse(
            status_code=500,
            content={
                "error": f"Erro ao iniciar pipeline: {str(e)}",
                "pipeline_id": pipeline_id
            }
        )

async def run_pipeline_background(
    pipeline_id: str,
    input_file: str,
    mode: str,
    target_column: str,
    model_dir: str,
    enable_enrichment: bool,
    output_filename: str
):
    """
    Executa pipeline em background thread
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
        # Atualizar status: carregando dados
        update_status('carregando', 10.0, 'CRM - Carregando dados do arquivo...')
        
        # Criar pipeline
        pipeline = UnifiedCRMPipeline(
            model_dir=model_dir,
            enable_api_calls=enable_enrichment
        )
        
        # Executar ETL
        update_status('processando', 30.0, 'CRM - Executando pipeline de ETL...')
        df = pipeline.run_etl(input_file)
        
        # Estatísticas dos dados
        data_stats = {
            'total_records': len(df),
            'total_columns': len(df.columns),
            'memory_usage_mb': df.memory_usage(deep=True).sum() / 1024 / 1024,
            'null_counts': df.isnull().sum().to_dict()
        }
        
        update_status('executando', 60.0, f'CRM - Dados processados: {len(df)} registros', data_stats)
        
        # Preparar diretório de saída
        output_dir = Path(tempfile.gettempdir()) / "crm_etl" / "output"
        output_dir.mkdir(exist_ok=True)
        output_file = output_dir / f"{pipeline_id}_{output_filename}"
        
        if mode == 'train':
            # Modo treinamento
            update_status('treinando', 80.0, 'CRM - Treinando modelo de Machine Learning...')
            
            pipeline.train_model(df, target_column=target_column)
            
            # Salvar dados processados
            df.to_csv(output_file, index=False, sep=';', encoding='utf-8-sig')
            
            training_details = {
                'model_type': 'RandomForestClassifier',
                'target_column': target_column,
                'features_used': len(df.columns) - 1,
                'records_trained': len(df)
            }
            
            update_status('concluida', 100.0, 'CRM - Treinamento concluído com sucesso!', {
                'output_file': str(output_file),
                'training_details': training_details,
                'data_overview': data_stats
            })
            
        elif mode == 'batch-predict':
            # Modo predição
            update_status('predizendo', 80.0, 'CRM - Realizando predições...')
            
            results_df = pipeline.batch_predict(df)
            
            # Salvar resultados
            results_df.to_csv(output_file, index=False, sep=';', encoding='utf-8-sig')
            
            # Estatísticas das predições
            if 'qualidade_predita' in results_df.columns:
                prediction_summary = results_df['qualidade_predita'].value_counts().to_dict()
            else:
                prediction_summary = {}
            
            prediction_details = {
                'total_predictions': len(results_df),
                'prediction_summary': prediction_summary,
                'confidence_stats': {
                    'mean_confidence': float(results_df.get('confianca_predicao', pd.Series([0])).mean()),
                    'high_confidence_count': int((results_df.get('confianca_predicao', pd.Series([0])) > 0.8).sum())
                } if 'confianca_predicao' in results_df.columns else {}
            }
            
            update_status('concluida', 100.0, 'CRM - Predições concluídas com sucesso!', {
                'output_file': str(output_file),
                'prediction_details': prediction_details,
                'data_overview': data_stats
            })
        
        # Atualizar estatísticas globais
        app_state['statistics']['total_pipelines_executed'] += 1
        app_state['statistics']['total_records_processed'] += len(df)
        
        logger.info(f"✅ Pipeline {pipeline_id} concluída com sucesso")
        
    except Exception as e:
        logger.error(f"❌ Erro na pipeline {pipeline_id}: {e}")
        logger.error(traceback.format_exc())
        
        update_status('erro', 0.0, f'CRM - Erro na execução: {str(e)}', {
            'error_type': type(e).__name__,
            'error_details': str(e)
        })

# Endpoint para status da pipeline
@app.get("/pipeline/status/{pipeline_id}")
async def get_pipeline_status(pipeline_id: str):
    """
    Obtém status de uma pipeline em execução
    """
    
    if pipeline_id not in app_state['pipelines']:
        raise HTTPException(status_code=404, detail="Pipeline não encontrada")
    
    return JSONResponse(app_state['pipelines'][pipeline_id])

# Endpoint para listar pipelines
@app.get("/pipeline/list")
async def list_pipelines():
    """
    Lista todas as pipelines executadas
    """
    
    return JSONResponse({
        'pipelines': app_state['pipelines'],
        'statistics': app_state['statistics']
    })

# Endpoint para gerar regras com IA
@app.post("/ai/generate-rule")
async def generate_ai_rule(request: AIRuleRequest):
    """
    Gera regra de transformação ETL usando IA
    """
    
    if not app_state['rule_generator']:
        raise HTTPException(
            status_code=503, 
            detail="Gerador de regras IA não disponível. Verifique configuração de API keys."
        )
    
    try:
        logger.info(f"🤖 CRM - Gerando regra IA: {request.requirement}")
        
        # Gerar regra
        rule_result = app_state['rule_generator'].generate_transformation_rule(
            requirement=request.requirement,
            data_context=request.data_context
        )
        
        # Atualizar estatísticas
        app_state['statistics']['total_ai_rules_generated'] += 1
        
        return JSONResponse({
            'success': True,
            'rule_result': rule_result,
            'message': 'CRM - Regra gerada com sucesso!'
        })
        
    except Exception as e:
        logger.error(f"❌ Erro ao gerar regra IA: {e}")
        
        return JSONResponse(
            status_code=500,
            content={
                'success': False,
                'error': str(e),
                'message': 'CRM - Erro ao gerar regra com IA'
            }
        )

# Endpoint para download de arquivos
@app.get("/download/{pipeline_id}")
async def download_result(pipeline_id: str):
    """
    Download do arquivo resultado de uma pipeline
    """
    
    if pipeline_id not in app_state['pipelines']:
        raise HTTPException(status_code=404, detail="Pipeline não encontrada")
    
    pipeline_data = app_state['pipelines'][pipeline_id]
    
    if pipeline_data['status'] != 'concluida':
        raise HTTPException(status_code=400, detail="Pipeline ainda não concluída")
    
    if 'details' not in pipeline_data or 'output_file' not in pipeline_data['details']:
        raise HTTPException(status_code=404, detail="Arquivo de resultado não encontrado")
    
    output_file = Path(pipeline_data['details']['output_file'])
    
    if not output_file.exists():
        raise HTTPException(status_code=404, detail="Arquivo não existe")
    
    return FileResponse(
        path=str(output_file),
        media_type='application/octet-stream',
        filename=f"crm_result_{pipeline_id}.csv"
    )

# Endpoint para estatísticas do sistema
@app.get("/stats")
async def get_system_stats():
    """
    Obtém estatísticas do sistema
    """
    
    return JSONResponse({
        'system_stats': app_state['statistics'],
        'active_pipelines': len([p for p in app_state['pipelines'].values() if p['status'] in ['iniciando', 'carregando', 'processando', 'executando', 'treinando', 'predizendo']]),
        'total_pipelines': len(app_state['pipelines']),
        'ai_available': app_state['rule_generator'] is not None,
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

# Endpoint para limpar cache
@app.delete("/admin/cleanup")
async def cleanup_system():
    """
    Limpa pipelines antigas e arquivos temporários
    """
    
    try:
        # Limpar pipelines antigas (mais de 1 dia)
        current_time = datetime.now()
        old_pipelines = []
        
        for pipeline_id, pipeline_data in list(app_state['pipelines'].items()):
            if pipeline_data.get('start_time'):
                start_time = datetime.fromisoformat(pipeline_data['start_time'])
                if (current_time - start_time).days > 1:
                    old_pipelines.append(pipeline_id)
        
        for pipeline_id in old_pipelines:
            del app_state['pipelines'][pipeline_id]
        
        # Limpar arquivos temporários
        temp_dir = Path(tempfile.gettempdir()) / "crm_etl"
        cleaned_files = 0
        if temp_dir.exists():
            for file_path in temp_dir.rglob("*"):
                if file_path.is_file():
                    try:
                        file_path.unlink()
                        cleaned_files += 1
                    except:
                        pass
        
        return JSONResponse({
            'success': True,
            'cleaned_pipelines': len(old_pipelines),
            'cleaned_files': cleaned_files,
            'message': 'CRM - Limpeza concluída com sucesso'
        })
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                'success': False,
                'error': str(e)
            }
        )

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