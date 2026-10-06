#!/usr/bin/env python3

# -*- coding: utf-8 -*-

"""

=================================================

--- CRM Tools - Plano PRO ---

=================================================



Serviço de qualificação de leads por regras configuráveis.

Sistema completo para CRM com automação e alertas.



Empresa: CRM ETL

Versão: 1.0

"""



from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks

from fastapi.responses import HTMLResponse, FileResponse, JSONResponse

from fastapi.staticfiles import StaticFiles

import pandas as pd

import numpy as np

import json

import logging

from datetime import datetime, timedelta

from pathlib import Path

from typing import Dict, List, Optional, Any

import asyncio

from dataclasses import dataclass, asdict

from enum import Enum

# Email functionality

import smtplib

from email.mime.text import MIMEText

from email.mime.multipart import MIMEMultipart

import requests

from io import BytesIO



# Configurar logging

logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)



# Criar app FastAPI

app = FastAPI(

    title="CRM Tools - Plano PRO",

    description="Qualificação de leads por regras configuráveis com integração CRM",

    version="1.0.0"

)



# Diretórios

DATA_DIR = Path("data")

CONFIG_DIR = Path("config")

OUTPUT_DIR = Path("output")

STATIC_DIR = Path("static")



# Criar diretórios

for dir_path in [DATA_DIR, CONFIG_DIR, OUTPUT_DIR, STATIC_DIR]:

    dir_path.mkdir(exist_ok=True)



# Servir arquivos estáticos

app.mount("/static", StaticFiles(directory="static"), name="static")



class LeadStatus(Enum):

    FRIO = "frio"

    MORNO = "morno"

    QUENTE = "quente"

    QUALIFICADO = "qualificado"

    CONVERTIDO = "convertido"



@dataclass

class ScoringRule:

    """Regra de pontuação"""

    name: str

    field: str

    condition: str

    value: Any

    points: int

    weight: float = 1.0

    active: bool = True



@dataclass

class Lead:

    """Dados do lead"""

    id: str

    nome: str

    email: str

    telefone: str = ""

    empresa: str = ""

    cargo: str = ""

    segmento: str = ""

    regiao: str = ""

    valor_estimado: float = 0.0

    data_cadastro: datetime = None

    fonte: str = ""

    status: LeadStatus = LeadStatus.FRIO

    score: float = 0.0

    tags: List[str] = None

    historico: List[Dict] = None

    

    def __post_init__(self):

        if self.data_cadastro is None:

            self.data_cadastro = datetime.now()

        if self.tags is None:

            self.tags = []

        if self.historico is None:

            self.historico = []



class LeadScoringEngine:

    """Engine de pontuação de leads"""

    

    def __init__(self):

        self.rules: List[ScoringRule] = []

        self.leads: Dict[str, Lead] = {}

        self.load_default_rules()

    

    def load_default_rules(self):

        """Carrega regras padrão"""

        default_rules = [

            ScoringRule("Valor Alto", "valor_estimado", ">", 5000, 50, 2.0),

            ScoringRule("Email Empresarial", "email", "contains", "@empresa.com", 30, 1.5),

            ScoringRule("Cargo Decisor", "cargo", "in", ["CEO", "CTO", "Diretor", "Gerente"], 40, 1.8),

            ScoringRule("Segmento Premium", "segmento", "in", ["Tecnologia", "Saúde", "Finanças"], 35, 1.5),

            ScoringRule("Região SP", "regiao", "contains", "São Paulo", 20, 1.0),

            ScoringRule("Lead Recente", "data_cadastro", "days_ago", 7, 25, 1.2),

            ScoringRule("Fonte Qualificada", "fonte", "in", ["Indicação", "Site", "LinkedIn"], 15, 1.0),

        ]

        self.rules = default_rules

    

    def add_rule(self, rule: ScoringRule):

        """Adiciona regra customizada"""

        self.rules.append(rule)

        logger.info(f"Regra adicionada: {rule.name}")

    

    def calculate_score(self, lead: Lead) -> float:

        """Calcula score do lead"""

        total_score = 0.0

        

        for rule in self.rules:

            if not rule.active:

                continue

                

            field_value = getattr(lead, rule.field, None)

            if field_value is None:

                continue

            

            points = 0

            

            # Avaliar condição

            if rule.condition == ">":

                if isinstance(field_value, (int, float)) and field_value > rule.value:

                    points = rule.points

                    

            elif rule.condition == "<":

                if isinstance(field_value, (int, float)) and field_value < rule.value:

                    points = rule.points

                    

            elif rule.condition == "==":

                if field_value == rule.value:

                    points = rule.points

                    

            elif rule.condition == "contains":

                if isinstance(field_value, str) and rule.value.lower() in field_value.lower():

                    points = rule.points

                    

            elif rule.condition == "in":

                if isinstance(rule.value, list) and any(v.lower() in str(field_value).lower() for v in rule.value):

                    points = rule.points

                    

            elif rule.condition == "days_ago":

                if isinstance(field_value, datetime):

                    days_diff = (datetime.now() - field_value).days

                    if days_diff <= rule.value:

                        points = rule.points * (rule.value - days_diff) / rule.value

            

            # Aplicar peso e somar

            weighted_points = points * rule.weight

            total_score += weighted_points

            

            # Log da aplicação da regra

            if points > 0:

                logger.debug(f"Lead {lead.id}: Regra '{rule.name}' aplicada - {weighted_points} pontos")

        

        return round(total_score, 2)

    

    def classify_lead(self, score: float) -> LeadStatus:

        """Classifica lead baseado no score"""

        if score >= 100:

            return LeadStatus.QUALIFICADO

        elif score >= 70:

            return LeadStatus.QUENTE

        elif score >= 40:

            return LeadStatus.MORNO

        else:

            return LeadStatus.FRIO

    

    def process_lead(self, lead_data: Dict) -> Lead:

        """Processa e pontua um lead"""

        # Criar lead

        lead = Lead(**lead_data)

        

        # Calcular score

        lead.score = self.calculate_score(lead)

        

        # Classificar

        lead.status = self.classify_lead(lead.score)

        

        # Adicionar histórico

        lead.historico.append({

            'timestamp': datetime.now().isoformat(),

            'action': 'scoring',

            'score': lead.score,

            'status': lead.status.value

        })

        

        # Salvar

        self.leads[lead.id] = lead

        

        return lead

    

    def get_qualified_leads(self) -> List[Lead]:

        """Retorna leads qualificados"""

        return [lead for lead in self.leads.values() 

                if lead.status in [LeadStatus.QUENTE, LeadStatus.QUALIFICADO]]

    

    def get_stats(self) -> Dict:

        """Retorna estatísticas"""

        if not self.leads:

            return {"total": 0}

            

        leads = list(self.leads.values())

        status_counts = {}

        

        for status in LeadStatus:

            status_counts[status.value] = len([l for l in leads if l.status == status])

        

        return {

            "total": len(leads),

            "status_distribution": status_counts,

            "avg_score": round(sum(l.score for l in leads) / len(leads), 2),

            "qualified_percentage": round((status_counts.get('qualificado', 0) + status_counts.get('quente', 0)) / len(leads) * 100, 2)

        }



class NotificationService:

    """Serviço de notificações"""

    

    def __init__(self):

        self.email_config = {}

        self.webhook_urls = []

    

    async def send_email_alert(self, lead: Lead, message: str):

        """Envia alerta por email"""

        try:

            # Simulação - em produção configurar SMTP real

            logger.info(f"EMAIL ALERT: Lead {lead.nome} ({lead.email}) - {message}")

            

            # Aqui iria a implementação real do SMTP

            return True

            

        except Exception as e:

            logger.error(f"Erro ao enviar email: {e}")

            return False

    

    async def send_webhook(self, data: Dict):

        """Envia webhook para integração"""

        for url in self.webhook_urls:

            try:

                response = requests.post(url, json=data, timeout=10)

                logger.info(f"Webhook enviado para {url}: {response.status_code}")

            except Exception as e:

                logger.error(f"Erro ao enviar webhook para {url}: {e}")



# Instâncias globais

scoring_engine = LeadScoringEngine()

notification_service = NotificationService()



@app.get("/", response_class=HTMLResponse)

async def root():

    """Interface principal do CRM Tools - Plano PRO"""

    return """
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ETL Tools - Plano PRO</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/xlsx/0.18.5/xlsx.full.min.js"></script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%);
            min-height: 100vh;
            display: flex;
            flex-direction: column;
        }
        .header {
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            color: white;
            padding: 2rem 0;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }
        .header-content {
            max-width: 1400px;
            margin: 0 auto;
            padding: 0 2rem;
        }
        .container {
            flex: 1;
            max-width: 1400px;
            margin: 2rem auto;
            padding: 0 2rem;
            width: 100%;
        }
        .tabs {
            display: flex;
            gap: 1rem;
            margin-bottom: 2rem;
            border-bottom: 2px solid #e0e0e0;
        }
        .tab {
            padding: 1rem 2rem;
            background: none;
            border: none;
            color: #666;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            position: relative;
        }
        .tab.active {
            color: #f5576c;
        }
        .tab.active::after {
            content: '';
            position: absolute;
            bottom: -2px;
            left: 0;
            right: 0;
            height: 2px;
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        }
        .card {
            background: white;
            border-radius: 12px;
            padding: 2rem;
            margin-bottom: 2rem;
            box-shadow: 0 4px 20px rgba(0,0,0,0.08);
        }
        .validation-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 1.5rem;
            margin-top: 1.5rem;
        }
        .validation-item {
            padding: 1.5rem;
            border-radius: 8px;
            background: #f8f9fa;
            border-left: 4px solid #f5576c;
        }
        .validation-item.success {
            border-left-color: #28a745;
        }
        .validation-item.warning {
            border-left-color: #ffc107;
        }
        .enrichment-options {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
            margin-top: 1rem;
        }
        .enrichment-card {
            padding: 1rem;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.3s ease;
            text-align: center;
        }
        .enrichment-card:hover {
            border-color: #f5576c;
            background: #fff5f7;
        }
        .enrichment-card.selected {
            border-color: #f5576c;
            background: linear-gradient(135deg, #f093fb20 0%, #f5576c20 100%);
        }
        .quality-score {
            display: flex;
            align-items: center;
            gap: 1rem;
            padding: 1rem;
            background: linear-gradient(135deg, #f093fb20 0%, #f5576c20 100%);
            border-radius: 8px;
            margin-top: 1rem;
        }
        .score-bar {
            flex: 1;
            height: 20px;
            background: #e0e0e0;
            border-radius: 10px;
            overflow: hidden;
        }
        .score-fill {
            height: 100%;
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            transition: width 0.5s ease;
        }
        .btn {
            padding: 0.75rem 1.5rem;
            border: none;
            border-radius: 6px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            display: inline-block;
            margin: 0.5rem;
        }
        .btn-primary {
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            color: white;
        }
        .btn-primary:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(245, 87, 108, 0.4);
        }
        .stats-container {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
            margin-top: 1rem;
        }
        .stat-box {
            background: white;
            padding: 1.5rem;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
            text-align: center;
        }
        .stat-value {
            font-size: 2rem;
            font-weight: bold;
            color: #f5576c;
        }
        .footer {
            background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%);
            color: white;
            padding: 2rem 0;
            margin-top: auto;
        }
    </style>
</head>
<body>
    <div class="header">
        <div class="header-content">
            <h1>ETL Tools - Plano PRO</h1>
            <p>Processamento avançado com validação e enriquecimento de dados</p>
        </div>
    </div>
    
    <div class="container">
        <div class="tabs">
            <button class="tab active" onclick="switchTab('upload')">📤 Upload</button>
            <button class="tab" onclick="switchTab('validation')">✔️ Validação</button>
            <button class="tab" onclick="switchTab('enrichment')">🔄 Enriquecimento</button>
            <button class="tab" onclick="switchTab('segmentation')">📊 Segmentação</button>
            <button class="tab" onclick="switchTab('export')">💾 Exportação</button>
        </div>
        
        <div id="upload-tab" class="tab-content">
            <div class="card">
                <h2>Upload de Dados Avançado</h2>
                <div style="border: 2px dashed #e0e0e0; border-radius: 8px; padding: 3rem; text-align: center;">
                    <p>Arraste múltiplos arquivos ou pastas</p>
                    <p style="color: #666; margin-top: 0.5rem;">CSV, Excel, JSON, XML, Parquet</p>
                    <button class="btn btn-primary" style="margin-top: 1rem;">Selecionar Arquivos</button>
                </div>
            </div>
        </div>
        
        <div id="validation-tab" class="tab-content" style="display: none;">
            <div class="card">
                <h2>Validação de Dados</h2>
                <div class="validation-grid">
                    <div class="validation-item success">
                        <h3>✅ Formato de Email</h3>
                        <p>1,234 emails válidos</p>
                        <p style="color: #28a745;">100% validados</p>
                    </div>
                    <div class="validation-item warning">
                        <h3>⚠️ Telefones</h3>
                        <p>892 telefones verificados</p>
                        <p style="color: #ffc107;">23 necessitam revisão</p>
                    </div>
                    <div class="validation-item success">
                        <h3>✅ CPF/CNPJ</h3>
                        <p>Todos os documentos válidos</p>
                        <p style="color: #28a745;">100% conformidade</p>
                    </div>
                    <div class="validation-item">
                        <h3>📍 Endereços</h3>
                        <p>567 endereços completos</p>
                        <p>89 parcialmente completos</p>
                    </div>
                </div>
                <div class="quality-score">
                    <span>Score de Qualidade:</span>
                    <div class="score-bar">
                        <div class="score-fill" style="width: 87%;"></div>
                    </div>
                    <span style="font-weight: bold; color: #f5576c;">87%</span>
                </div>
            </div>
        </div>
        
        <div id="enrichment-tab" class="tab-content" style="display: none;">
            <div class="card">
                <h2>Enriquecimento de Dados</h2>
                <div class="enrichment-options">
                    <div class="enrichment-card selected">
                        <h3>🏢 Dados Empresariais</h3>
                        <p>CNAE, Porte, Faturamento</p>
                    </div>
                    <div class="enrichment-card">
                        <h3>📱 Redes Sociais</h3>
                        <p>LinkedIn, Facebook, Instagram</p>
                    </div>
                    <div class="enrichment-card">
                        <h3>📊 Score de Crédito</h3>
                        <p>Análise de risco e crédito</p>
                    </div>
                    <div class="enrichment-card">
                        <h3>🌍 Geolocalização</h3>
                        <p>Coordenadas e região</p>
                    </div>
                </div>
                <button class="btn btn-primary" style="margin-top: 2rem;">Iniciar Enriquecimento</button>
            </div>
        </div>
        
        <div id="segmentation-tab" class="tab-content" style="display: none;">
            <div class="card">
                <h2>Segmentação Inteligente</h2>
                <div class="stats-container">
                    <div class="stat-box">
                        <div class="stat-value">A</div>
                        <p>234 Leads Premium</p>
                    </div>
                    <div class="stat-box">
                        <div class="stat-value">B</div>
                        <p>567 Leads Qualificados</p>
                    </div>
                    <div class="stat-box">
                        <div class="stat-value">C</div>
                        <p>432 Leads Potenciais</p>
                    </div>
                </div>
            </div>
        </div>
        
        <div id="export-tab" class="tab-content" style="display: none;">
            <div class="card">
                <h2>Exportação de Dados</h2>
                <p>Escolha o formato de exportação:</p>
                <div style="display: flex; gap: 1rem; margin-top: 1rem;">
                    <button class="btn btn-primary">📊 Excel</button>
                    <button class="btn btn-primary">📄 CSV</button>
                    <button class="btn btn-primary">🔗 API</button>
                    <button class="btn btn-primary">💾 Database</button>
                </div>
            </div>
        </div>
    </div>
    
    <div class="footer">
        <div class="footer-content">
            <p>&copy; 2024 ETL Tools Pro. Todos os direitos reservados.</p>
        </div>
    </div>
    
    <script>
        function switchTab(tabName) {
            // Hide all tabs
            document.querySelectorAll('.tab-content').forEach(tab => {
                tab.style.display = 'none';
            });
            
            // Remove active class from all tabs
            document.querySelectorAll('.tab').forEach(tab => {
                tab.classList.remove('active');
            });
            
            // Show selected tab
            const selectedTab = document.getElementById(tabName + '-tab');
            if (selectedTab) {
                selectedTab.style.display = 'block';
            }
            
            // Add active class to clicked tab
            event.target.classList.add('active');
        }
        
        // Enrichment card selection
        document.querySelectorAll('.enrichment-card').forEach(card => {
            card.addEventListener('click', () => {
                card.classList.toggle('selected');
            });
        });
    </script>
</body>
"""



@app.get("/api/stats")

async def get_stats():

    """Retorna estatísticas dos leads"""

    return scoring_engine.get_stats()



@app.get("/api/rules") 

async def get_rules():

    """Retorna regras de pontuação"""

    return [asdict(rule) for rule in scoring_engine.rules]



@app.post("/api/process-leads")

async def process_leads_api(

    file: UploadFile = File(...),

    auto_score: bool = Form(True),

    send_alerts: bool = Form(True)

):

    """Processa leads do arquivo"""

    

    try:

        # Ler arquivo

        content = await file.read()

        

        if file.filename.endswith('.csv'):

            df = pd.read_csv(BytesIO(content))

        elif file.filename.endswith(('.xlsx', '.xls')):

            df = pd.read_excel(BytesIO(content))

        else:

            raise HTTPException(status_code=400, detail="Formato não suportado")

        

        processed_count = 0

        qualified_count = 0

        

        # Processar cada lead

        for _, row in df.iterrows():

            try:

                # Mapear colunas (flexível)

                lead_data = {

                    'id': str(len(scoring_engine.leads) + processed_count + 1),

                    'nome': str(row.get('nome', row.get('name', ''))),

                    'email': str(row.get('email', '')),

                    'telefone': str(row.get('telefone', row.get('phone', ''))),

                    'empresa': str(row.get('empresa', row.get('company', ''))),

                    'cargo': str(row.get('cargo', row.get('position', ''))),

                    'segmento': str(row.get('segmento', row.get('segment', ''))),

                    'regiao': str(row.get('regiao', row.get('region', ''))),

                    'valor_estimado': float(row.get('valor_estimado', row.get('estimated_value', 0))),

                    'fonte': str(row.get('fonte', row.get('source', 'Import')))

                }

                

                # Processar lead

                if auto_score:

                    lead = scoring_engine.process_lead(lead_data)

                    

                    # Verificar se qualificado para alertas

                    if send_alerts and lead.status in [LeadStatus.QUENTE, LeadStatus.QUALIFICADO]:

                        qualified_count += 1

                        # Enviar alerta em background

                        asyncio.create_task(

                            notification_service.send_email_alert(

                                lead, 

                                f"Novo lead qualificado: {lead.nome} com score {lead.score}"

                            )

                        )

                

                processed_count += 1

                

            except Exception as e:

                logger.warning(f"Erro ao processar lead da linha {processed_count}: {e}")

                continue

        

        return {

            "processed": processed_count,

            "qualified": qualified_count,

            "total_leads": len(scoring_engine.leads)

        }

        

    except Exception as e:

        logger.error(f"Erro no processamento: {e}")

        raise HTTPException(status_code=500, detail=str(e))



@app.get("/api/leads")

async def get_leads(status: Optional[str] = None, limit: int = 50):

    """Retorna lista de leads"""

    

    leads = list(scoring_engine.leads.values())

    

    # Filtrar por status se especificado

    if status and status != "all":

        leads = [lead for lead in leads if lead.status.value == status]

    

    # Ordenar por score

    leads.sort(key=lambda x: x.score, reverse=True)

    

    # Limitar resultados

    leads = leads[:limit]

    

    # Converter para dict para serialização

    return [asdict(lead) for lead in leads]



@app.get("/health")

async def health_check():

    """Health check"""

    return {

        "status": "healthy", 

        "service": "CRM Tools - Plano PRO",

        "version": "1.0.0",

        "leads_count": len(scoring_engine.leads),

        "rules_count": len(scoring_engine.rules),

        "timestamp": datetime.now().isoformat()

    }



if __name__ == "__main__":

    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8002)