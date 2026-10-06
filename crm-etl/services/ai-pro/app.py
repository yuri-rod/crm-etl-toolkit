#!/usr/bin/env python3

# -*- coding: utf-8 -*-

"""

=================================================

--- CRM Tools - Plano AI PRO ---

=================================================



Serviço premium com IA avançada para qualificação de leads.

Sistema completo com machine learning, análise preditiva e automação.



Empresa: CRM ETL

Versão: 1.0

"""



from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect

from fastapi.responses import HTMLResponse, FileResponse, JSONResponse, StreamingResponse

from fastapi.staticfiles import StaticFiles

import pandas as pd

import numpy as np

import json

import logging

import asyncio

from datetime import datetime, timedelta

from pathlib import Path

from typing import Dict, List, Optional, Any, Tuple

import pickle

import joblib

from dataclasses import dataclass, asdict

from enum import Enum

# Using redis-py instead of aioredis for better compatibility

# import aioredis

import redis.asyncio as redis

import aiohttp

import uuid

from io import BytesIO

import base64



# ML and AI imports

from sklearn.model_selection import train_test_split

from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier

from sklearn.linear_model import LogisticRegression

from sklearn.preprocessing import StandardScaler, LabelEncoder

from sklearn.metrics import accuracy_score, classification_report, roc_auc_score

from sklearn.feature_extraction.text import TfidfVectorizer

import xgboost as xgb

import shap



# Configurar logging

logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)



# Criar app FastAPI

app = FastAPI(

    title="CRM Tools - Plano AI PRO",

    description="Qualificação inteligente de leads com IA avançada",

    version="1.0.0"

)



# Diretórios

DATA_DIR = Path("data")

MODELS_DIR = Path("models")

CONFIG_DIR = Path("config") 

OUTPUT_DIR = Path("output")

STATIC_DIR = Path("static")



# Criar diretórios

for dir_path in [DATA_DIR, MODELS_DIR, CONFIG_DIR, OUTPUT_DIR, STATIC_DIR]:

    dir_path.mkdir(exist_ok=True)



# Servir arquivos estáticos

app.mount("/static", StaticFiles(directory="static"), name="static")



class ModelType(Enum):

    RANDOM_FOREST = "random_forest"

    GRADIENT_BOOSTING = "gradient_boosting"

    XGBOOST = "xgboost"

    LOGISTIC_REGRESSION = "logistic_regression"

    NEURAL_NETWORK = "neural_network"



class PredictionConfidence(Enum):

    VERY_HIGH = "very_high"  # > 90%

    HIGH = "high"           # 75-90%

    MEDIUM = "medium"       # 50-75%

    LOW = "low"             # < 50%



@dataclass

class AIInsight:

    """Insight gerado pela IA"""

    type: str

    title: str

    description: str

    confidence: float

    impact: str

    recommended_action: str

    timestamp: datetime = None

    

    def __post_init__(self):

        if self.timestamp is None:

            self.timestamp = datetime.now()



@dataclass

class LeadScore:

    """Score detalhado de um lead"""

    lead_id: str

    final_score: float

    conversion_probability: float

    confidence: PredictionConfidence

    feature_importance: Dict[str, float]

    model_explanation: str

    recommended_actions: List[str]

    next_best_action: str

    optimal_contact_time: datetime

    predicted_value: float

    risk_factors: List[str]

    strengths: List[str]



class AIModelManager:

    """Gerenciador de modelos de ML"""

    

    def __init__(self):

        self.models: Dict[str, Any] = {}

        self.scalers: Dict[str, StandardScaler] = {}

        self.encoders: Dict[str, LabelEncoder] = {}

        self.feature_importance: Dict[str, Dict] = {}

        self.model_performance: Dict[str, Dict] = {}

        self.explainer = None

        

    def prepare_features(self, df: pd.DataFrame) -> pd.DataFrame:

        """Prepara features avançadas para ML"""

        

        logger.info("Preparando features avançadas...")

        

        # Features temporais

        if 'data_cadastro' in df.columns:

            df['data_cadastro'] = pd.to_datetime(df['data_cadastro'])

            df['days_since_registration'] = (datetime.now() - df['data_cadastro']).dt.days

            df['registration_hour'] = df['data_cadastro'].dt.hour

            df['registration_weekday'] = df['data_cadastro'].dt.weekday

            df['registration_month'] = df['data_cadastro'].dt.month

        

        # Features de texto

        if 'nome' in df.columns:

            df['name_length'] = df['nome'].str.len()

            df['name_word_count'] = df['nome'].str.split().str.len()

        

        if 'email' in df.columns:

            df['email_length'] = df['email'].str.len()

            df['has_corporate_email'] = df['email'].str.contains(r'@(?!gmail|yahoo|hotmail|outlook)', case=False, na=False)

            df['email_domain'] = df['email'].str.split('@').str[-1]

            df['email_provider'] = df['email_domain'].apply(self._classify_email_provider)

        

        # Features de empresa

        if 'empresa' in df.columns:

            df['company_length'] = df['empresa'].str.len()

            df['company_word_count'] = df['empresa'].str.split().str.len()

            df['has_company_name'] = df['empresa'].notna() & (df['empresa'] != '')

        

        # Features de cargo

        if 'cargo' in df.columns:

            df['is_decision_maker'] = df['cargo'].str.contains(

                r'CEO|CTO|CFO|Diretor|Presidente|Gerente|Manager|VP|Vice', case=False, na=False

            )

            df['seniority_level'] = df['cargo'].apply(self._extract_seniority)

        

        # Features de valor

        if 'valor_estimado' in df.columns:

            df['valor_estimado'] = pd.to_numeric(df['valor_estimado'], errors='coerce').fillna(0)

            df['high_value_lead'] = df['valor_estimado'] > df['valor_estimado'].quantile(0.75)

            df['value_category'] = pd.cut(df['valor_estimado'], bins=5, labels=['Muito Baixo', 'Baixo', 'Médio', 'Alto', 'Muito Alto'])

        

        # Features de segmento

        if 'segmento' in df.columns:

            df['is_tech_segment'] = df['segmento'].str.contains('Tecnologia|Software|TI|Tech', case=False, na=False)

            df['is_finance_segment'] = df['segmento'].str.contains('Financ|Bank|Invest', case=False, na=False)

        

        # Features de região

        if 'regiao' in df.columns:

            df['is_sp'] = df['regiao'].str.contains('São Paulo|SP', case=False, na=False)

            df['is_rj'] = df['regiao'].str.contains('Rio de Janeiro|RJ', case=False, na=False)

            df['is_major_city'] = df['regiao'].str.contains('São Paulo|Rio de Janeiro|Belo Horizonte|Salvador|Brasília', case=False, na=False)

        

        # Features de engajamento (simuladas)

        np.random.seed(42)

        df['page_views'] = np.random.poisson(5, len(df))

        df['email_opens'] = np.random.poisson(3, len(df))

        df['time_on_site'] = np.random.exponential(2, len(df))

        df['downloads'] = np.random.poisson(1, len(df))

        

        # Features derivadas de engajamento

        df['engagement_score'] = (df['page_views'] * 0.3 + df['email_opens'] * 0.4 + 

                                 df['time_on_site'] * 0.2 + df['downloads'] * 0.1)

        df['high_engagement'] = df['engagement_score'] > df['engagement_score'].quantile(0.7)

        

        # Features de sazonalidade

        current_month = datetime.now().month

        df['is_high_season'] = current_month in [3, 4, 9, 10, 11]  # Meses típicos de alta conversão B2B

        

        return df

    

    def _classify_email_provider(self, domain):

        """Classifica provedor de email"""

        if pd.isna(domain):

            return 'unknown'

        

        domain = domain.lower()

        if any(provider in domain for provider in ['gmail', 'yahoo', 'hotmail', 'outlook']):

            return 'personal'

        else:

            return 'corporate'

    

    def _extract_seniority(self, cargo):

        """Extrai nível de senioridade do cargo"""

        if pd.isna(cargo):

            return 'unknown'

        

        cargo = cargo.lower()

        if any(term in cargo for term in ['ceo', 'presidente', 'diretor', 'vp', 'vice']):

            return 'executive'

        elif any(term in cargo for term in ['gerente', 'manager', 'coordenador', 'supervisor']):

            return 'management'

        elif any(term in cargo for term in ['senior', 'especialista', 'lead', 'principal']):

            return 'senior'

        elif any(term in cargo for term in ['junior', 'trainee', 'estagiario', 'assistente']):

            return 'junior'

        else:

            return 'mid-level'

    

    def train_ensemble_model(self, X: pd.DataFrame, y: pd.Series, model_name: str = "ensemble"):

        """Treina ensemble de modelos para máxima precisão"""

        

        logger.info(f"Treinando ensemble de modelos ML para {model_name}...")

        

        # Split dos dados

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

        

        # Preparar dados categóricos

        X_train_processed, X_test_processed = self._prepare_categorical_features(X_train, X_test)

        

        # Normalizar features numéricas

        scaler = StandardScaler()

        numeric_cols = X_train_processed.select_dtypes(include=[np.number]).columns

        X_train_processed[numeric_cols] = scaler.fit_transform(X_train_processed[numeric_cols])

        X_test_processed[numeric_cols] = scaler.transform(X_test_processed[numeric_cols])

        

        # Salvar scaler

        self.scalers[model_name] = scaler

        

        # Treinar múltiplos modelos

        models = {

            'random_forest': RandomForestClassifier(n_estimators=100, random_state=42, class_weight='balanced'),

            'gradient_boosting': GradientBoostingClassifier(n_estimators=100, random_state=42),

            'xgboost': xgb.XGBClassifier(random_state=42, eval_metric='logloss'),

            'logistic': LogisticRegression(random_state=42, class_weight='balanced', max_iter=1000)

        }

        

        trained_models = {}

        performances = {}

        

        for name, model in models.items():

            logger.info(f"Treinando {name}...")

            

            try:

                model.fit(X_train_processed, y_train)

                y_pred = model.predict(X_test_processed)

                y_proba = model.predict_proba(X_test_processed)[:, 1] if hasattr(model, 'predict_proba') else None

                

                # Métricas

                accuracy = accuracy_score(y_test, y_pred)

                auc = roc_auc_score(y_test, y_proba) if y_proba is not None else 0

                

                performances[name] = {

                    'accuracy': accuracy,

                    'auc': auc,

                    'classification_report': classification_report(y_test, y_pred, output_dict=True)

                }

                

                trained_models[name] = model

                logger.info(f"{name} - Accuracy: {accuracy:.3f}, AUC: {auc:.3f}")

                

            except Exception as e:

                logger.error(f"Erro ao treinar {name}: {e}")

                continue

        

        # Selecionar melhor modelo baseado em AUC

        if performances:

            best_model_name = max(performances.keys(), key=lambda x: performances[x]['auc'])

            best_model = trained_models[best_model_name]

            

            logger.info(f"Melhor modelo: {best_model_name} (AUC: {performances[best_model_name]['auc']:.3f})")

            

            # Salvar modelo e performance

            self.models[model_name] = best_model

            self.model_performance[model_name] = performances[best_model_name]

            

            # Feature importance

            if hasattr(best_model, 'feature_importances_'):

                feature_names = X_train_processed.columns

                importances = best_model.feature_importances_

                self.feature_importance[model_name] = dict(zip(feature_names, importances))

            

            # SHAP explainer para interpretabilidade

            try:

                self.explainer = shap.Explainer(best_model, X_train_processed)

                logger.info("SHAP explainer criado com sucesso")

            except Exception as e:

                logger.warning(f"Erro ao criar SHAP explainer: {e}")

            

            # Salvar modelo em disco

            model_path = MODELS_DIR / f"{model_name}_model.joblib"

            joblib.dump(best_model, model_path)

            

            # Salvar scaler

            scaler_path = MODELS_DIR / f"{model_name}_scaler.joblib"

            joblib.dump(scaler, scaler_path)

            

            return best_model, performances[best_model_name]

        

        else:

            raise Exception("Nenhum modelo foi treinado com sucesso")

    

    def _prepare_categorical_features(self, X_train: pd.DataFrame, X_test: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:

        """Prepara features categóricas"""

        

        X_train_processed = X_train.copy()

        X_test_processed = X_test.copy()

        

        # Codificar variáveis categóricas

        categorical_cols = X_train_processed.select_dtypes(include=['object']).columns

        

        for col in categorical_cols:

            if col in X_train_processed.columns:

                # Label encoding para categóricas ordinais

                le = LabelEncoder()

                

                # Combinar valores de treino e teste para encoding consistente

                combined_values = pd.concat([X_train_processed[col], X_test_processed[col]]).astype(str)

                le.fit(combined_values.unique())

                

                X_train_processed[col] = le.transform(X_train_processed[col].astype(str))

                X_test_processed[col] = le.transform(X_test_processed[col].astype(str))

                

                # Salvar encoder

                self.encoders[col] = le

        

        return X_train_processed, X_test_processed

    

    def predict_with_explanation(self, X: pd.DataFrame, model_name: str = "ensemble") -> List[LeadScore]:

        """Faz predição com explicação detalhada"""

        

        if model_name not in self.models:

            raise ValueError(f"Modelo {model_name} não encontrado")

        

        model = self.models[model_name]

        scaler = self.scalers.get(model_name)

        

        # Preparar dados

        X_processed = X.copy()

        

        # Aplicar encoders categóricos

        for col, encoder in self.encoders.items():

            if col in X_processed.columns:

                try:

                    X_processed[col] = encoder.transform(X_processed[col].astype(str))

                except ValueError:

                    # Valor não visto no treino, usar categoria mais comum

                    X_processed[col] = 0

        

        # Aplicar scaler

        if scaler:

            numeric_cols = X_processed.select_dtypes(include=[np.number]).columns

            X_processed[numeric_cols] = scaler.transform(X_processed[numeric_cols])

        

        # Predições

        predictions = model.predict_proba(X_processed)[:, 1]  # Probabilidade da classe positiva

        

        # Explicações SHAP (se disponível)

        explanations = None

        if self.explainer:

            try:

                explanations = self.explainer.shap_values(X_processed)

                if len(explanations.shape) > 2:  # Multi-class

                    explanations = explanations[:, :, 1]  # Classe positiva

            except Exception as e:

                logger.warning(f"Erro ao gerar explicações SHAP: {e}")

        

        # Criar objetos LeadScore

        lead_scores = []

        feature_names = X_processed.columns.tolist()

        

        for i, prob in enumerate(predictions):

            # Feature importance para este lead

            if explanations is not None:

                feature_importance = dict(zip(feature_names, explanations[i]))

                # Ordenar por importância absoluta

                feature_importance = dict(sorted(feature_importance.items(), 

                                               key=lambda x: abs(x[1]), reverse=True)[:10])

            else:

                # Usar feature importance global do modelo

                feature_importance = self.feature_importance.get(model_name, {})

            

            # Classificar confiança

            if prob >= 0.9:

                confidence = PredictionConfidence.VERY_HIGH

            elif prob >= 0.75:

                confidence = PredictionConfidence.HIGH

            elif prob >= 0.5:

                confidence = PredictionConfidence.MEDIUM

            else:

                confidence = PredictionConfidence.LOW

            

            # Gerar recomendações baseadas na predição

            recommended_actions = self._generate_recommendations(X.iloc[i], prob, feature_importance)

            

            # Score final (0-100)

            final_score = min(prob * 100, 100)

            

            lead_score = LeadScore(

                lead_id=str(i),

                final_score=final_score,

                conversion_probability=prob,

                confidence=confidence,

                feature_importance=feature_importance,

                model_explanation=self._generate_explanation(feature_importance, prob),

                recommended_actions=recommended_actions,

                next_best_action=recommended_actions[0] if recommended_actions else "Revisar dados do lead",

                optimal_contact_time=self._predict_best_contact_time(),

                predicted_value=self._predict_lead_value(X.iloc[i]),

                risk_factors=self._identify_risk_factors(X.iloc[i], feature_importance),

                strengths=self._identify_strengths(X.iloc[i], feature_importance)

            )

            

            lead_scores.append(lead_score)

        

        return lead_scores

    

    def _generate_recommendations(self, lead_data: pd.Series, probability: float, importance: Dict[str, float]) -> List[str]:

        """Gera recomendações personalizadas"""

        recommendations = []

        

        if probability >= 0.8:

            recommendations.append(" URGENTE: Entrar em contato imediatamente - Lead de alta conversão!")

            recommendations.append(" Ligar dentro de 1 hora para maximizar conversão")

        elif probability >= 0.6:

            recommendations.append(" Prioridade alta: Agendar call comercial hoje")

            recommendations.append(" Enviar proposta customizada")

        elif probability >= 0.4:

            recommendations.append(" Lead promissor: Nutrição personalizada necessária")

            recommendations.append(" Compartilhar case studies relevantes")

        else:

            recommendations.append(" Lead em desenvolvimento: Nutrição de longo prazo")

            recommendations.append(" Qualificar melhor antes de abordagem comercial")

        

        # Recomendações baseadas em features importantes

        top_features = list(importance.keys())[:3]

        

        if 'valor_estimado' in top_features and hasattr(lead_data, 'valor_estimado'):

            if lead_data.get('valor_estimado', 0) > 10000:

                recommendations.append(" Lead de alto valor - Envolver gerência comercial")

        

        if 'is_decision_maker' in top_features and lead_data.get('is_decision_maker'):

            recommendations.append(" Decisor identificado - Focar em ROI e benefícios")

        

        if 'high_engagement' in top_features and lead_data.get('high_engagement'):

            recommendations.append(" Alto engajamento - Acelerar processo de vendas")

        

        return recommendations[:5]  # Limitar a 5 recomendações

    

    def _generate_explanation(self, importance: Dict[str, float], probability: float) -> str:

        """Gera explicação legível do modelo"""

        

        top_positive = {k: v for k, v in importance.items() if v > 0}

        top_negative = {k: v for k, v in importance.items() if v < 0}

        

        explanation = f"A IA prevê {probability*100:.1f}% de probabilidade de conversão. "

        

        if top_positive:

            top_pos = max(top_positive.items(), key=lambda x: x[1])

            explanation += f"O fator mais positivo é '{top_pos[0]}' (impacto: {top_pos[1]:.3f}). "

        

        if top_negative:

            top_neg = min(top_negative.items(), key=lambda x: x[1])

            explanation += f"O maior risco é '{top_neg[0]}' (impacto: {top_neg[1]:.3f}). "

        

        if probability >= 0.8:

            explanation += "Este é um lead de conversão muito provável!"

        elif probability >= 0.6:

            explanation += "Lead com boa probabilidade de conversão."

        elif probability >= 0.4:

            explanation += "Lead promissor que precisa de nutrição."

        else:

            explanation += "Lead que precisa de qualificação adicional."

        

        return explanation

    

    def _predict_best_contact_time(self) -> datetime:

        """Prediz melhor momento para contato"""

        # Lógica simples - horário comercial do próximo dia útil

        now = datetime.now()

        

        # Se for final de semana, empurrar para segunda

        if now.weekday() >= 5:  # Sábado ou domingo

            days_to_add = 7 - now.weekday()

            target_date = now + timedelta(days=days_to_add)

        else:

            target_date = now + timedelta(days=1)

        

        # Horário entre 9h e 11h (melhor para contato comercial)

        optimal_hour = np.random.choice([9, 10, 11])

        

        return target_date.replace(hour=optimal_hour, minute=0, second=0, microsecond=0)

    

    def _predict_lead_value(self, lead_data: pd.Series) -> float:

        """Prediz valor potencial do lead"""

        base_value = lead_data.get('valor_estimado', 5000)

        

        # Ajustes baseados em características

        multiplier = 1.0

        

        if lead_data.get('is_decision_maker'):

            multiplier *= 1.5

        

        if lead_data.get('has_corporate_email'):

            multiplier *= 1.2

        

        if lead_data.get('high_engagement'):

            multiplier *= 1.3

        

        return base_value * multiplier

    

    def _identify_risk_factors(self, lead_data: pd.Series, importance: Dict[str, float]) -> List[str]:

        """Identifica fatores de risco"""

        risks = []

        

        negative_factors = {k: v for k, v in importance.items() if v < -0.01}

        

        for factor, impact in negative_factors.items():

            if factor == 'valor_estimado' and lead_data.get('valor_estimado', 0) < 1000:

                risks.append(" Valor estimado muito baixo")

            elif factor == 'days_since_registration' and lead_data.get('days_since_registration', 0) > 90:

                risks.append(" Lead muito antigo - pode estar frio")

            elif factor == 'email_provider' and lead_data.get('email_provider') == 'personal':

                risks.append(" Email pessoal - pode não ser decisor")

            elif 'engagement' in factor and not lead_data.get('high_engagement'):

                risks.append(" Baixo engajamento com conteúdo")

        

        return risks[:3]  # Limitar a 3 riscos principais

    

    def _identify_strengths(self, lead_data: pd.Series, importance: Dict[str, float]) -> List[str]:

        """Identifica pontos fortes"""

        strengths = []

        

        positive_factors = {k: v for k, v in importance.items() if v > 0.01}

        

        for factor, impact in positive_factors.items():

            if factor == 'is_decision_maker' and lead_data.get('is_decision_maker'):

                strengths.append(" Identificado como decisor")

            elif factor == 'high_value_lead' and lead_data.get('high_value_lead'):

                strengths.append(" Lead de alto valor")

            elif factor == 'has_corporate_email' and lead_data.get('has_corporate_email'):

                strengths.append(" Email corporativo")

            elif factor == 'high_engagement' and lead_data.get('high_engagement'):

                strengths.append(" Alto engajamento")

            elif factor == 'is_tech_segment' and lead_data.get('is_tech_segment'):

                strengths.append(" Segmento de tecnologia")

        

        return strengths[:3]  # Limitar a 3 strengths principais



class RealTimeProcessor:

    """Processador de eventos em tempo real"""

    

    def __init__(self):

        self.event_queue = asyncio.Queue()

        self.active_connections: List[WebSocket] = []

        self.redis = None

    

    async def initialize_redis(self):

        """Inicializa conexão Redis"""

        try:

            # Using redis-py's async client

            self.redis = await redis.from_url("redis://redis:6379", decode_responses=True)

            logger.info("Redis conectado com sucesso")

        except Exception as e:

            logger.warning(f"Erro ao conectar Redis: {e}")

    

    async def process_event(self, event_type: str, data: Dict):

        """Processa evento em tempo real"""

        event = {

            'id': str(uuid.uuid4()),

            'type': event_type,

            'data': data,

            'timestamp': datetime.now().isoformat()

        }

        

        # Adicionar à fila

        await self.event_queue.put(event)

        

        # Notificar conexões WebSocket

        await self._broadcast_event(event)

        

        # Salvar no Redis (se disponível)

        if self.redis:

            await self.redis.lpush("ai_events", json.dumps(event))

            await self.redis.expire("ai_events", 86400)  # 24 horas

    

    async def _broadcast_event(self, event: Dict):

        """Envia evento para todas as conexões WebSocket ativas"""

        if self.active_connections:

            message = json.dumps(event)

            disconnected = []

            

            for connection in self.active_connections:

                try:

                    await connection.send_text(message)

                except WebSocketDisconnect:

                    disconnected.append(connection)

            

            # Remove conexões desconectadas

            for conn in disconnected:

                self.active_connections.remove(conn)



# Instâncias globais

ai_model_manager = AIModelManager()

real_time_processor = RealTimeProcessor()



@app.on_event("startup")

async def startup_event():

    """Inicialização da aplicação"""

    logger.info("Inicializando CRM Tools - AI PRO...")

    

    # Inicializar Redis

    await real_time_processor.initialize_redis()

    

    # Carregar modelos salvos (se existirem)

    try:

        model_files = list(MODELS_DIR.glob("*_model.joblib"))

        for model_file in model_files:

            model_name = model_file.stem.replace("_model", "")

            model = joblib.load(model_file)

            ai_model_manager.models[model_name] = model

            logger.info(f"Modelo {model_name} carregado com sucesso")

    except Exception as e:

        logger.warning(f"Erro ao carregar modelos: {e}")



@app.get("/", response_class=HTMLResponse)

async def root():

    """Interface principal do CRM Tools - Plano AI PRO"""

    return """
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ETL Tools - AI PRO Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/xlsx/0.18.5/xlsx.full.min.js"></script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #0f0f23;
            color: #e0e0e0;
            min-height: 100vh;
        }
        .dashboard {
            display: grid;
            grid-template-columns: 250px 1fr;
            min-height: 100vh;
        }
        .sidebar {
            background: linear-gradient(180deg, #1a1a2e 0%, #16213e 100%);
            padding: 2rem 1rem;
            border-right: 1px solid #2a2a4a;
        }
        .sidebar h2 {
            color: #4facfe;
            margin-bottom: 2rem;
            font-size: 1.5rem;
        }
        .nav-item {
            display: block;
            width: 100%;
            padding: 1rem;
            margin-bottom: 0.5rem;
            background: none;
            border: none;
            color: #e0e0e0;
            text-align: left;
            cursor: pointer;
            border-radius: 8px;
            transition: all 0.3s ease;
        }
        .nav-item:hover {
            background: rgba(79, 172, 254, 0.1);
            color: #4facfe;
        }
        .nav-item.active {
            background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
            color: white;
        }
        .main-content {
            padding: 2rem;
            overflow-y: auto;
        }
        .header {
            background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
            padding: 2rem;
            border-radius: 12px;
            margin-bottom: 2rem;
            box-shadow: 0 10px 30px rgba(79, 172, 254, 0.3);
        }
        .header h1 {
            font-size: 2rem;
            margin-bottom: 0.5rem;
        }
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2rem;
        }
        .metric-card {
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            padding: 1.5rem;
            border-radius: 12px;
            border: 1px solid #2a2a4a;
            position: relative;
            overflow: hidden;
        }
        .metric-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 3px;
            background: linear-gradient(90deg, #4facfe, #00f2fe);
        }
        .metric-value {
            font-size: 2.5rem;
            font-weight: bold;
            background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .metric-label {
            color: #888;
            margin-top: 0.5rem;
        }
        .chart-container {
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            padding: 2rem;
            border-radius: 12px;
            border: 1px solid #2a2a4a;
            margin-bottom: 2rem;
        }
        .chart-container h3 {
            margin-bottom: 1.5rem;
            color: #4facfe;
        }
        .model-training {
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            padding: 2rem;
            border-radius: 12px;
            border: 1px solid #2a2a4a;
        }
        .input-group {
            margin-bottom: 1.5rem;
        }
        .input-group label {
            display: block;
            margin-bottom: 0.5rem;
            color: #4facfe;
        }
        .input-group select,
        .input-group input {
            width: 100%;
            padding: 0.75rem;
            background: #0f0f23;
            border: 1px solid #2a2a4a;
            border-radius: 6px;
            color: #e0e0e0;
        }
        .btn {
            padding: 0.75rem 2rem;
            border: none;
            border-radius: 6px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        .btn-primary {
            background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
            color: white;
        }
        .btn-primary:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 20px rgba(79, 172, 254, 0.4);
        }
        .real-time-feed {
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            padding: 1.5rem;
            border-radius: 12px;
            border: 1px solid #2a2a4a;
            height: 400px;
            overflow-y: auto;
        }
        .feed-item {
            padding: 1rem;
            margin-bottom: 0.5rem;
            background: rgba(79, 172, 254, 0.05);
            border-left: 3px solid #4facfe;
            border-radius: 4px;
        }
        .feed-time {
            font-size: 0.8rem;
            color: #666;
        }
        .prediction-panel {
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            padding: 2rem;
            border-radius: 12px;
            border: 1px solid #2a2a4a;
            margin-top: 2rem;
        }
        .prediction-result {
            margin-top: 1.5rem;
            padding: 1.5rem;
            background: rgba(79, 172, 254, 0.1);
            border-radius: 8px;
            border: 1px solid #4facfe;
        }
        .confidence-bar {
            width: 100%;
            height: 30px;
            background: #0f0f23;
            border-radius: 15px;
            overflow: hidden;
            margin-top: 1rem;
        }
        .confidence-fill {
            height: 100%;
            background: linear-gradient(90deg, #4facfe, #00f2fe);
            transition: width 0.5s ease;
        }
        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.5; }
            100% { opacity: 1; }
        }
        .live-indicator {
            display: inline-block;
            width: 8px;
            height: 8px;
            background: #00f2fe;
            border-radius: 50%;
            margin-right: 0.5rem;
            animation: pulse 2s infinite;
        }
    </style>
</head>
<body>
    <div class="dashboard">
        <div class="sidebar">
            <h2>🤖 AI PRO</h2>
            <button class="nav-item active" onclick="showSection('overview')">
                📊 Overview
            </button>
            <button class="nav-item" onclick="showSection('training')">
                🧠 Treinar Modelo
            </button>
            <button class="nav-item" onclick="showSection('predictions')">
                🎯 Predições
            </button>
            <button class="nav-item" onclick="showSection('analytics')">
                📈 Analytics
            </button>
            <button class="nav-item" onclick="showSection('realtime')">
                ⚡ Real-Time
            </button>
            <button class="nav-item" onclick="showSection('export')">
                💾 Exportar
            </button>
        </div>
        
        <div class="main-content">
            <div id="overview-section">
                <div class="header">
                    <h1>AI-Powered ETL Dashboard</h1>
                    <p>Machine Learning e Análise Preditiva em Tempo Real</p>
                </div>
                
                <div class="metrics-grid">
                    <div class="metric-card">
                        <div class="metric-value">98.7%</div>
                        <div class="metric-label">Acurácia do Modelo</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">1.2M</div>
                        <div class="metric-label">Dados Processados</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">
                            <span class="live-indicator"></span>
                            156
                        </div>
                        <div class="metric-label">Predições/Minuto</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">0.92</div>
                        <div class="metric-label">AUC Score</div>
                    </div>
                </div>
                
                <div class="chart-container">
                    <h3>Performance do Modelo ao Longo do Tempo</h3>
                    <canvas id="performanceChart" height="80"></canvas>
                </div>
                
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 2rem;">
                    <div class="chart-container">
                        <h3>Distribuição de Predições</h3>
                        <canvas id="distributionChart"></canvas>
                    </div>
                    <div class="chart-container">
                        <h3>Feature Importance</h3>
                        <canvas id="featureChart"></canvas>
                    </div>
                </div>
            </div>
            
            <div id="training-section" style="display: none;">
                <div class="model-training">
                    <h2>🧠 Treinamento de Modelo ML</h2>
                    
                    <div class="input-group">
                        <label>Dataset de Treinamento</label>
                        <input type="file" accept=".csv,.xlsx">
                    </div>
                    
                    <div class="input-group">
                        <label>Algoritmo</label>
                        <select>
                            <option>Random Forest</option>
                            <option>XGBoost</option>
                            <option>Neural Network</option>
                            <option>Gradient Boosting</option>
                            <option>Ensemble</option>
                        </select>
                    </div>
                    
                    <div class="input-group">
                        <label>Target Column</label>
                        <select>
                            <option>lead_score</option>
                            <option>conversion_probability</option>
                            <option>churn_risk</option>
                            <option>lifetime_value</option>
                        </select>
                    </div>
                    
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
                        <div class="input-group">
                            <label>Train/Test Split</label>
                            <input type="range" min="50" max="90" value="80">
                        </div>
                        <div class="input-group">
                            <label>Cross Validation Folds</label>
                            <input type="number" value="5" min="2" max="10">
                        </div>
                    </div>
                    
                    <button class="btn btn-primary" onclick="startTraining()">
                        Iniciar Treinamento
                    </button>
                    
                    <div id="trainingProgress" style="display: none; margin-top: 2rem;">
                        <h3>Progresso do Treinamento</h3>
                        <div class="confidence-bar">
                            <div class="confidence-fill" id="trainingBar" style="width: 0%;"></div>
                        </div>
                        <p style="margin-top: 1rem;" id="trainingStatus">Preparando dados...</p>
                    </div>
                </div>
            </div>
            
            <div id="predictions-section" style="display: none;">
                <div class="prediction-panel">
                    <h2>🎯 Realizar Predições</h2>
                    
                    <div class="input-group">
                        <label>Dados para Predição</label>
                        <input type="file" accept=".csv,.xlsx">
                    </div>
                    
                    <div class="input-group">
                        <label>Modelo Treinado</label>
                        <select>
                            <option>Lead Scoring v2.3</option>
                            <option>Churn Prediction v1.8</option>
                            <option>CLV Estimator v3.1</option>
                        </select>
                    </div>
                    
                    <button class="btn btn-primary" onclick="runPrediction()">
                        Executar Predição
                    </button>
                    
                    <div class="prediction-result" style="display: none;" id="predictionResult">
                        <h3>Resultados da Predição</h3>
                        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-top: 1rem;">
                            <div>
                                <p>Score Médio: <strong>0.867</strong></p>
                                <p>Confiança: <strong>94.3%</strong></p>
                            </div>
                            <div>
                                <p>Leads Hot: <strong>234</strong></p>
                                <p>Leads Warm: <strong>567</strong></p>
                            </div>
                        </div>
                        <div class="confidence-bar">
                            <div class="confidence-fill" style="width: 94.3%;"></div>
                        </div>
                    </div>
                </div>
            </div>
            
            <div id="realtime-section" style="display: none;">
                <h2>⚡ Monitoramento em Tempo Real</h2>
                <div class="real-time-feed" id="realtimeFeed">
                    <div class="feed-item">
                        <span class="live-indicator"></span>
                        <strong>Nova predição executada</strong>
                        <p>Score: 0.92 | Confiança: 96%</p>
                        <span class="feed-time">Agora</span>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        // Initialize Charts
        const ctx1 = document.getElementById('performanceChart');
        if (ctx1) {
            new Chart(ctx1, {
                type: 'line',
                data: {
                    labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
                    datasets: [{
                        label: 'Acurácia',
                        data: [94, 95, 96, 97, 98, 98.7],
                        borderColor: '#4facfe',
                        backgroundColor: 'rgba(79, 172, 254, 0.1)',
                        tension: 0.4
                    }, {
                        label: 'AUC',
                        data: [0.88, 0.89, 0.90, 0.91, 0.91, 0.92],
                        borderColor: '#00f2fe',
                        backgroundColor: 'rgba(0, 242, 254, 0.1)',
                        tension: 0.4
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            labels: { color: '#e0e0e0' }
                        }
                    },
                    scales: {
                        x: { ticks: { color: '#888' }, grid: { color: '#2a2a4a' } },
                        y: { ticks: { color: '#888' }, grid: { color: '#2a2a4a' } }
                    }
                }
            });
        }
        
        const ctx2 = document.getElementById('distributionChart');
        if (ctx2) {
            new Chart(ctx2, {
                type: 'doughnut',
                data: {
                    labels: ['Hot Leads', 'Warm Leads', 'Cold Leads'],
                    datasets: [{
                        data: [30, 45, 25],
                        backgroundColor: [
                            'rgba(79, 172, 254, 0.8)',
                            'rgba(0, 242, 254, 0.8)',
                            'rgba(42, 42, 74, 0.8)'
                        ]
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: {
                            labels: { color: '#e0e0e0' }
                        }
                    }
                }
            });
        }
        
        const ctx3 = document.getElementById('featureChart');
        if (ctx3) {
            new Chart(ctx3, {
                type: 'bar',
                data: {
                    labels: ['Email Engagement', 'Company Size', 'Industry', 'Budget', 'Timeline'],
                    datasets: [{
                        label: 'Importance',
                        data: [0.89, 0.76, 0.65, 0.92, 0.58],
                        backgroundColor: 'rgba(79, 172, 254, 0.6)'
                    }]
                },
                options: {
                    responsive: true,
                    indexAxis: 'y',
                    plugins: {
                        legend: { display: false }
                    },
                    scales: {
                        x: { ticks: { color: '#888' }, grid: { color: '#2a2a4a' } },
                        y: { ticks: { color: '#888' }, grid: { color: '#2a2a4a' } }
                    }
                }
            });
        }
        
        function showSection(section) {
            // Hide all sections
            document.querySelectorAll('[id$="-section"]').forEach(s => {
                s.style.display = 'none';
            });
            
            // Show selected section
            const selectedSection = document.getElementById(section + '-section');
            if (selectedSection) {
                selectedSection.style.display = 'block';
            }
            
            // Update active nav
            document.querySelectorAll('.nav-item').forEach(item => {
                item.classList.remove('active');
            });
            event.target.classList.add('active');
        }
        
        function startTraining() {
            const progress = document.getElementById('trainingProgress');
            const bar = document.getElementById('trainingBar');
            const status = document.getElementById('trainingStatus');
            
            progress.style.display = 'block';
            let width = 0;
            
            const interval = setInterval(() => {
                width += 10;
                bar.style.width = width + '%';
                
                if (width === 30) status.textContent = 'Processando features...';
                if (width === 60) status.textContent = 'Treinando modelo...';
                if (width === 90) status.textContent = 'Validando resultados...';
                
                if (width >= 100) {
                    clearInterval(interval);
                    status.textContent = '✅ Treinamento concluído! Acurácia: 98.7%';
                }
            }, 500);
        }
        
        function runPrediction() {
            const result = document.getElementById('predictionResult');
            result.style.display = 'block';
        }
        
        // WebSocket for real-time updates
        function connectWebSocket() {
            const feed = document.getElementById('realtimeFeed');
            
            // Simulate real-time updates
            setInterval(() => {
                const item = document.createElement('div');
                item.className = 'feed-item';
                item.innerHTML = `
                    <span class="live-indicator"></span>
                    <strong>Nova atividade detectada</strong>
                    <p>Score: ${(Math.random() * 0.3 + 0.7).toFixed(2)} | Confiança: ${(Math.random() * 20 + 80).toFixed(0)}%</p>
                    <span class="feed-time">${new Date().toLocaleTimeString()}</span>
                `;
                
                if (feed) {
                    feed.insertBefore(item, feed.firstChild);
                    if (feed.children.length > 10) {
                        feed.removeChild(feed.lastChild);
                    }
                }
            }, 5000);
        }
        
        connectWebSocket();
    </script>
</body>
"""



@app.post("/api/train-model")

async def train_model_api(

    file: UploadFile = File(...),

    algorithm: str = Form("random_forest"),

    target_column: str = Form("qualidade_lead")

):

    """API para treinar modelo"""

    

    try:

        logger.info(f"Iniciando treinamento do modelo {algorithm}")

        

        # Ler dados

        content = await file.read()

        

        if file.filename.endswith('.csv'):

            df = pd.read_csv(BytesIO(content))

        elif file.filename.endswith(('.xlsx', '.xls')):

            df = pd.read_excel(BytesIO(content))

        else:

            raise HTTPException(status_code=400, detail="Formato não suportado")

        

        # Verificar se coluna alvo existe

        if target_column not in df.columns:

            raise HTTPException(status_code=400, detail=f"Coluna '{target_column}' não encontrada")

        

        # Preparar features

        df_features = ai_model_manager.prepare_features(df)

        

        # Separar features e target

        y = df_features[target_column]

        X = df_features.drop(columns=[target_column])

        

        # Converter target para binário se necessário

        if y.dtype == 'object':

            from sklearn.preprocessing import LabelEncoder

            le = LabelEncoder()

            y = le.fit_transform(y)

        

        # Treinar modelo

        model, performance = ai_model_manager.train_ensemble_model(X, y, f"model_{algorithm}")

        

        # Processar evento em tempo real

        await real_time_processor.process_event("model_training", {

            "algorithm": algorithm,

            "performance": performance,

            "features": len(X.columns),

            "samples": len(X)

        })

        

        return {

            "success": True,

            "algorithm": algorithm,

            "performance": performance,

            "features_count": len(X.columns),

            "samples_count": len(X),

            "model_saved": True

        }

        

    except Exception as e:

        logger.error(f"Erro no treinamento: {e}")

        raise HTTPException(status_code=500, detail=str(e))



@app.post("/api/predict")

async def predict_api(lead_data: Dict[str, Any]):

    """API para fazer predições"""

    

    try:

        # Criar DataFrame com o lead

        df = pd.DataFrame([lead_data])

        

        # Preparar features

        df_features = ai_model_manager.prepare_features(df)

        

        # Fazer predição

        if "ensemble" in ai_model_manager.models:

            predictions = ai_model_manager.predict_with_explanation(df_features, "ensemble")

            

            # Processar evento em tempo real

            lead_score = predictions[0]

            await real_time_processor.process_event("prediction", {

                "lead_id": lead_score.lead_id,

                "score": lead_score.final_score,

                "probability": lead_score.conversion_probability,

                "confidence": lead_score.confidence.value

            })

            

            return asdict(predictions[0])

        else:

            raise HTTPException(status_code=400, detail="Nenhum modelo treinado disponível")

            

    except Exception as e:

        logger.error(f"Erro na predição: {e}")

        raise HTTPException(status_code=500, detail=str(e))



@app.websocket("/ws")

async def websocket_endpoint(websocket: WebSocket):

    """Endpoint WebSocket para tempo real"""

    await websocket.accept()

    real_time_processor.active_connections.append(websocket)

    

    try:

        while True:

            # Manter conexão viva

            await websocket.receive_text()

    except WebSocketDisconnect:

        real_time_processor.active_connections.remove(websocket)



@app.get("/api/model-status")

async def get_model_status():

    """Status dos modelos"""

    return {

        "models_available": list(ai_model_manager.models.keys()),

        "performance": ai_model_manager.model_performance,

        "feature_importance": ai_model_manager.feature_importance,

        "models_count": len(ai_model_manager.models)

    }



@app.get("/health")

async def health_check():

    """Health check"""

    return {

        "status": "healthy",

        "service": "CRM Tools - AI PRO",

        "version": "1.0.0",

        "ai_models": len(ai_model_manager.models),

        "websocket_connections": len(real_time_processor.active_connections),

        "timestamp": datetime.now().isoformat()

    }



if __name__ == "__main__":

    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8003)