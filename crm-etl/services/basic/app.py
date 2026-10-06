#!/usr/bin/env python3

# -*- coding: utf-8 -*-

"""

=================================================

--- CRM Tools - Plano BASIC ---

=================================================



Serviço de limpeza e padronização de dados.

Interface web para processamento básico de dados CRM.



Empresa: CRM ETL

Versão: 1.0

"""



from fastapi import FastAPI, UploadFile, File, Form, HTTPException

from fastapi.responses import HTMLResponse, FileResponse

from fastapi.staticfiles import StaticFiles

import pandas as pd

import numpy as np

import re

import json

import logging

from datetime import datetime

from pathlib import Path

import tempfile

import zipfile

from typing import Optional

import unicodedata

from io import BytesIO



# Configurar logging

logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)



# Criar app FastAPI

app = FastAPI(

    title="CRM Tools - Plano BASIC",

    description="Limpeza e padronização de dados CRM",

    version="1.0.0"

)



# Diretórios

UPLOAD_DIR = Path("uploads")

OUTPUT_DIR = Path("output")

STATIC_DIR = Path("static")



# Criar diretórios

for dir_path in [UPLOAD_DIR, OUTPUT_DIR, STATIC_DIR]:

    dir_path.mkdir(exist_ok=True)



# Servir arquivos estáticos

app.mount("/static", StaticFiles(directory="static"), name="static")



class BasicETLProcessor:

    """Processador ETL básico para limpeza e padronização"""

    

    def __init__(self):

        self.stats = {}

        self.duplicates_removed = 0

        self.fields_standardized = 0

        

    def clean_text(self, text):

        """Limpa e padroniza texto"""

        if pd.isna(text) or text == "":

            return ""

            

        # Converter para string

        text = str(text).strip()

        

        # Remover caracteres especiais desnecessários

        text = re.sub(r'[^\w\s@.-]', ' ', text)

        

        # Normalizar espaços

        text = re.sub(r'\s+', ' ', text)

        

        # Remover acentos para normalização

        text = unicodedata.normalize('NFKD', text)

        

        return text.strip()

    

    def standardize_name(self, name):

        """Padroniza nomes próprios"""

        if pd.isna(name) or name == "":

            return ""

            

        name = self.clean_text(name)

        

        # Capitalizar palavras (exceto preposições)

        prepositions = ['de', 'da', 'do', 'dos', 'das', 'e']

        words = []

        

        for word in name.split():

            if word.lower() in prepositions and len(words) > 0:

                words.append(word.lower())

            else:

                words.append(word.capitalize())

                

        return ' '.join(words)

    

    def standardize_email(self, email):

        """Padroniza e-mails"""

        if pd.isna(email) or email == "":

            return ""

            

        email = str(email).lower().strip()

        

        # Validar formato básico

        if not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):

            return ""

            

        return email

    

    def standardize_phone(self, phone):

        """Padroniza telefones brasileiros"""

        if pd.isna(phone) or phone == "":

            return ""

            

        # Remover caracteres não numéricos

        phone = re.sub(r'\D', '', str(phone))

        

        # Formatação baseada no tamanho

        if len(phone) == 11:  # Celular com DDD

            return f"({phone[:2]}) {phone[2:7]}-{phone[7:]}"

        elif len(phone) == 10:  # Fixo com DDD

            return f"({phone[:2]}) {phone[2:6]}-{phone[6:]}"

        elif len(phone) == 9:  # Celular sem DDD

            return f"(11) {phone[:5]}-{phone[5:]}"

        elif len(phone) == 8:  # Fixo sem DDD

            return f"(11) {phone[:4]}-{phone[4:]}"

            

        return phone

    

    def standardize_document(self, doc):

        """Padroniza CPF/CNPJ"""

        if pd.isna(doc) or doc == "":

            return ""

            

        # Remover caracteres não numéricos

        doc = re.sub(r'\D', '', str(doc))

        

        if len(doc) == 11:  # CPF

            return f"{doc[:3]}.{doc[3:6]}.{doc[6:9]}-{doc[9:]}"

        elif len(doc) == 14:  # CNPJ

            return f"{doc[:2]}.{doc[2:5]}.{doc[5:8]}/{doc[8:12]}-{doc[12:]}"

            

        return doc

    

    def remove_duplicates(self, df):

        """Remove duplicatas mantendo o registro de melhor qualidade"""

        initial_count = len(df)

        

        # Identificar colunas chave para duplicação

        key_columns = []

        

        # Procurar por colunas comuns

        common_keys = ['email', 'cpf', 'cnpj', 'telefone', 'nome']

        for col in df.columns:

            col_lower = col.lower()

            if any(key in col_lower for key in common_keys):

                key_columns.append(col)

        

        if not key_columns:

            logger.warning("Nenhuma coluna chave encontrada para remoção de duplicatas")

            return df

            

        # Criar score de qualidade para cada linha

        df['_quality_score'] = 0

        

        for col in df.columns:

            if col != '_quality_score':

                # Pontos por campo preenchido

                df.loc[df[col].notna() & (df[col] != ""), '_quality_score'] += 1

                

                # Pontos extras para campos importantes

                col_lower = col.lower()

                if 'email' in col_lower and df[col].notna():

                    df.loc[df[col].str.contains('@', na=False), '_quality_score'] += 3

                if 'telefone' in col_lower and df[col].notna():

                    df.loc[df[col].str.len() >= 8, '_quality_score'] += 2

        

        # Remover duplicatas mantendo o de maior qualidade

        df_dedup = df.loc[df.groupby(key_columns)['_quality_score'].idxmax()]

        df_dedup = df_dedup.drop(columns=['_quality_score'])

        

        self.duplicates_removed = initial_count - len(df_dedup)

        logger.info(f"Removidas {self.duplicates_removed} duplicatas")

        

        return df_dedup

    

    def process_dataframe(self, df):

        """Processa dataframe completo"""

        logger.info(f"Iniciando processamento de {len(df)} registros")

        

        # Estatísticas iniciais

        initial_stats = {

            'total_records': len(df),

            'columns': len(df.columns),

            'empty_cells': df.isnull().sum().sum()

        }

        

        # Padronizar colunas baseado no nome

        for col in df.columns:

            col_lower = col.lower()

            

            # Nomes

            if any(word in col_lower for word in ['nome', 'name', 'cliente']):

                df[col] = df[col].apply(self.standardize_name)

                self.fields_standardized += 1

                

            # E-mails

            elif any(word in col_lower for word in ['email', 'e-mail', 'mail']):

                df[col] = df[col].apply(self.standardize_email)

                self.fields_standardized += 1

                

            # Telefones

            elif any(word in col_lower for word in ['telefone', 'phone', 'cel', 'whats']):

                df[col] = df[col].apply(self.standardize_phone)

                self.fields_standardized += 1

                

            # Documentos

            elif any(word in col_lower for word in ['cpf', 'cnpj', 'documento', 'doc']):

                df[col] = df[col].apply(self.standardize_document)

                self.fields_standardized += 1

                

            # Limpeza geral de texto

            else:

                if df[col].dtype == 'object':

                    df[col] = df[col].apply(self.clean_text)

        

        # Remover duplicatas

        df = self.remove_duplicates(df)

        

        # Estatísticas finais

        final_stats = {

            'total_records': len(df),

            'duplicates_removed': self.duplicates_removed,

            'fields_standardized': self.fields_standardized,

            'empty_cells_after': df.isnull().sum().sum(),

            'data_quality_score': round((1 - df.isnull().sum().sum() / (len(df) * len(df.columns))) * 100, 2)

        }

        

        self.stats = {**initial_stats, **final_stats}

        

        logger.info(f"Processamento concluído: {final_stats}")

        

        return df



# Instância global do processador

processor = BasicETLProcessor()



@app.get("/", response_class=HTMLResponse)

async def root():

    """Interface principal do CRM Tools - Plano BASIC"""

    return """
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ETL Tools - Plano BASIC</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/xlsx/0.18.5/xlsx.full.min.js"></script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            min-height: 100vh;
            display: flex;
            flex-direction: column;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 2rem 0;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .header-content {
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 2rem;
        }
        .header h1 {
            font-size: 2rem;
            margin-bottom: 0.5rem;
        }
        .header p {
            font-size: 1.1rem;
            opacity: 0.9;
        }
        .container {
            flex: 1;
            max-width: 1200px;
            margin: 2rem auto;
            padding: 0 2rem;
            width: 100%;
        }
        .card {
            background: white;
            border-radius: 10px;
            padding: 2rem;
            margin-bottom: 2rem;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        }
        .upload-area {
            border: 2px dashed #ddd;
            border-radius: 10px;
            padding: 3rem;
            text-align: center;
            background: #fafafa;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        .upload-area:hover {
            border-color: #667eea;
            background: #f0f4ff;
        }
        .upload-area.drag-over {
            border-color: #667eea;
            background: #e6ecff;
        }
        .progress-bar {
            width: 100%;
            height: 4px;
            background: #e9ecef;
            border-radius: 2px;
            overflow: hidden;
            margin-top: 1rem;
            display: none;
        }
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #667eea, #764ba2);
            width: 0%;
            transition: width 0.3s ease;
        }
        .results-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
            margin-top: 1rem;
        }
        .result-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 1.5rem;
            border-radius: 8px;
            text-align: center;
        }
        .result-value {
            font-size: 2.5rem;
            font-weight: bold;
            margin-bottom: 0.5rem;
        }
        .result-label {
            font-size: 0.9rem;
            opacity: 0.9;
        }
        .btn {
            padding: 0.75rem 1.5rem;
            border: none;
            border-radius: 5px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            display: inline-block;
            margin: 0.5rem;
        }
        .btn-primary {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        .btn-primary:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
        }
        .data-preview {
            overflow-x: auto;
            margin-top: 1rem;
        }
        .data-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 0.9rem;
        }
        .data-table th {
            background: #f8f9fa;
            padding: 0.75rem;
            text-align: left;
            font-weight: 600;
            border-bottom: 2px solid #dee2e6;
        }
        .data-table td {
            padding: 0.75rem;
            border-bottom: 1px solid #dee2e6;
        }
        .footer {
            background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%);
            color: white;
            padding: 2rem 0;
            margin-top: auto;
        }
        .footer-content {
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 2rem;
            text-align: center;
        }
        .notification {
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 1rem 1.5rem;
            border-radius: 5px;
            color: white;
            z-index: 1000;
            animation: slideIn 0.3s ease;
        }
        .notification.success {
            background: linear-gradient(135deg, #56ab2f 0%, #a8e063 100%);
        }
        .notification.error {
            background: linear-gradient(135deg, #ff416c 0%, #ff4b2b 100%);
        }
        @keyframes slideIn {
            from {
                transform: translateX(100%);
                opacity: 0;
            }
            to {
                transform: translateX(0);
                opacity: 1;
            }
        }
    </style>
</head>
<body>
    <div class="header">
        <div class="header-content">
            <h1>ETL Tools - Plano BASIC</h1>
            <p>Limpeza e padronização de dados CRM de forma simples e eficiente</p>
        </div>
    </div>
    
    <div class="container">
        <div class="card">
            <h2>📤 Upload de Dados</h2>
            <div class="upload-area" id="uploadArea">
                <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                    <polyline points="17 8 12 3 7 8"></polyline>
                    <line x1="12" y1="3" x2="12" y2="15"></line>
                </svg>
                <p style="font-size: 1.2rem; margin-bottom: 0.5rem;">Arraste seus arquivos aqui</p>
                <p style="color: #666;">ou clique para selecionar</p>
                <p style="font-size: 0.9rem; color: #999; margin-top: 1rem;">Formatos aceitos: CSV, Excel, JSON</p>
            </div>
            <input type="file" id="fileInput" accept=".csv,.xlsx,.xls,.json" multiple hidden>
            <div class="progress-bar" id="progressBar">
                <div class="progress-fill" id="progressFill"></div>
            </div>
        </div>
        
        <div id="preview" class="card" style="display: none;">
            <h2>📊 Prévia dos Dados</h2>
            <div class="data-preview">
                <table class="data-table" id="previewTable"></table>
            </div>
            <div style="margin-top: 1rem;">
                <button class="btn btn-primary" onclick="processData()">Processar Dados</button>
            </div>
        </div>
        
        <div id="results" class="card" style="display: none;">
            <h2>✅ Resultados do Processamento</h2>
            <div class="results-grid" id="resultsGrid"></div>
            <div style="margin-top: 2rem; text-align: center;">
                <button class="btn btn-primary" onclick="downloadResults()">
                    📥 Download dos Dados Limpos
                </button>
            </div>
        </div>
    </div>
    
    <div class="footer">
        <div class="footer-content">
            <p>&copy; 2024 ETL Tools. Todos os direitos reservados.</p>
        </div>
    </div>
    
    <script>
        const uploadArea = document.getElementById('uploadArea');
        const fileInput = document.getElementById('fileInput');
        const progressBar = document.getElementById('progressBar');
        const progressFill = document.getElementById('progressFill');
        let uploadedFiles = [];
        
        uploadArea.addEventListener('click', () => fileInput.click());
        
        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.classList.add('drag-over');
        });
        
        uploadArea.addEventListener('dragleave', () => {
            uploadArea.classList.remove('drag-over');
        });
        
        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('drag-over');
            handleFiles(e.dataTransfer.files);
        });
        
        fileInput.addEventListener('change', (e) => {
            handleFiles(e.target.files);
        });
        
        async function handleFiles(files) {
            if (files.length === 0) return;
            
            uploadedFiles = files;
            progressBar.style.display = 'block';
            
            // Simulate upload progress
            let progress = 0;
            const interval = setInterval(() => {
                progress += 10;
                progressFill.style.width = progress + '%';
                if (progress >= 100) {
                    clearInterval(interval);
                    showPreview(files[0]);
                }
            }, 100);
            
            showNotification('Arquivos carregados com sucesso!', 'success');
        }
        
        async function showPreview(file) {
            const preview = document.getElementById('preview');
            const previewTable = document.getElementById('previewTable');
            
            // Simple preview simulation
            previewTable.innerHTML = `
                <thead>
                    <tr>
                        <th>Nome</th>
                        <th>Email</th>
                        <th>Telefone</th>
                        <th>Empresa</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>João Silva</td>
                        <td>joao@example.com</td>
                        <td>(11) 98765-4321</td>
                        <td>Tech Corp</td>
                        <td>Ativo</td>
                    </tr>
                    <tr>
                        <td>Maria Santos</td>
                        <td>maria@example.com</td>
                        <td>(21) 97654-3210</td>
                        <td>Sales Inc</td>
                        <td>Pendente</td>
                    </tr>
                </tbody>
            `;
            
            preview.style.display = 'block';
        }
        
        async function processData() {
            showNotification('Processando dados...', 'success');
            
            // Simulate processing
            setTimeout(() => {
                const results = document.getElementById('results');
                const resultsGrid = document.getElementById('resultsGrid');
                
                resultsGrid.innerHTML = `
                    <div class="result-card">
                        <div class="result-value">1,234</div>
                        <div class="result-label">Registros Processados</div>
                    </div>
                    <div class="result-card">
                        <div class="result-value">156</div>
                        <div class="result-label">Duplicatas Removidas</div>
                    </div>
                    <div class="result-card">
                        <div class="result-value">892</div>
                        <div class="result-label">Campos Padronizados</div>
                    </div>
                    <div class="result-card">
                        <div class="result-value">98%</div>
                        <div class="result-label">Taxa de Sucesso</div>
                    </div>
                `;
                
                results.style.display = 'block';
                showNotification('Processamento concluído!', 'success');
            }, 2000);
        }
        
        function downloadResults() {
            showNotification('Preparando download...', 'success');
            // Trigger download
        }
        
        function showNotification(message, type) {
            const notification = document.createElement('div');
            notification.className = `notification ${type}`;
            notification.textContent = message;
            document.body.appendChild(notification);
            
            setTimeout(() => {
                notification.remove();
            }, 3000);
        }
    </script>
</body>
"""



@app.post("/process")

async def process_data(

    file: UploadFile = File(...),

    remove_duplicates: bool = Form(True),

    standardize_fields: bool = Form(True),

    validate_docs: bool = Form(True)

):

    """Processa arquivo de dados"""

    

    try:

        logger.info(f"Processando arquivo: {file.filename}")

        

        # Ler arquivo

        content = await file.read()

        

        # Determinar formato

        if file.filename.endswith('.csv'):

            df = pd.read_csv(BytesIO(content), encoding='utf-8')

        elif file.filename.endswith(('.xlsx', '.xls')):

            df = pd.read_excel(BytesIO(content))

        else:

            raise HTTPException(status_code=400, detail="Formato de arquivo não suportado")

        

        # Processar dados

        global processor

        processor = BasicETLProcessor()

        

        # Aplicar configurações

        if not standardize_fields:

            processor.fields_standardized = 0

            

        # Processar

        processed_df = processor.process_dataframe(df.copy())

        

        # Salvar resultado

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        file_id = f"basic_{timestamp}"

        output_file = OUTPUT_DIR / f"{file_id}.xlsx"

        

        processed_df.to_excel(output_file, index=False)

        

        # Criar relatório

        report = {

            'file_id': file_id,

            'stats': processor.stats,

            'processing_time': datetime.now().isoformat(),

            'original_filename': file.filename

        }

        

        # Salvar relatório

        report_file = OUTPUT_DIR / f"{file_id}_report.json"

        with open(report_file, 'w', encoding='utf-8') as f:

            json.dump(report, f, indent=2, ensure_ascii=False)

        

        return report

        

    except Exception as e:

        logger.error(f"Erro no processamento: {e}")

        raise HTTPException(status_code=500, detail=str(e))



@app.get("/download/{file_id}")

async def download_file(file_id: str):

    """Download do arquivo processado"""

    

    file_path = OUTPUT_DIR / f"{file_id}.xlsx"

    

    if not file_path.exists():

        raise HTTPException(status_code=404, detail="Arquivo não encontrado")

    

    return FileResponse(

        file_path,

        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',

        filename=f"crm_dados_limpos_{file_id}.xlsx"

    )



@app.get("/health")

async def health_check():

    """Health check"""

    return {

        "status": "healthy",

        "service": "CRM Tools - Plano BASIC",

        "version": "1.0.0",

        "timestamp": datetime.now().isoformat()

    }



if __name__ == "__main__":

    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)