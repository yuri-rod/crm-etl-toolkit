"""
Sistema Avançado de Analytics e Machine Learning - CRM The New Education
Motor de análise preditiva, ROI tracking e insights automatizados
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, mean_absolute_error
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
import json
from datetime import datetime, timedelta
import warnings
import logging
from typing import Dict, List, Tuple, Optional, Any
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats

warnings.filterwarnings('ignore')
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CRMAnalyticsEngine:
    """
    Motor de analytics avançado para CRM do CRM
    Inclui ML, tracking de ROI, segmentação automática e compliance LGPD
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = self._get_default_config()
        if config:
            self.config.update(config)
        
        self.models = {}
        self.scalers = {}
        self.encoders = {}
        self.insights = []
        
    def _get_default_config(self) -> Dict:
        return {
            'enable_ml': True,
            'enable_roi_tracking': True,
            'enable_automated_research': True,
            'enable_predictive_analytics': True,
            'lgpd_compliant': True,
            'confidence_threshold': 0.7,
            'roi_calculation_method': 'ltv',  # ltv, cohort, direct
            'clustering_algorithm': 'kmeans',
            'n_clusters': 5
        }
    
    def analyze_complete_dataset(self, data_path: str) -> Dict[str, Any]:
        """
        Análise completa do dataset com ML, insights e recomendações
        """
        logger.info("Iniciando análise completa do dataset")
        
        # Carregar dados
        with open(data_path, 'r', encoding='utf-8') as f:
            data_json = json.load(f)
        
        df = pd.DataFrame(data_json['data'])
        
        results = {
            'timestamp': datetime.now().isoformat(),
            'data_quality': data_json['metadata']['data_quality_score'],
            'total_records': len(df),
            'ml_models': {},
            'roi_analysis': {},
            'segmentation': {},
            'insights': [],
            'recommendations': [],
            'compliance_status': {}
        }
        
        # 1. Análise de qualidade e preparação
        df = self._prepare_data_for_ml(df)
        
        # 2. Modelos de Machine Learning
        if self.config['enable_ml']:
            results['ml_models'] = self._build_ml_models(df)
        
        # 3. ROI Tracking
        if self.config['enable_roi_tracking']:
            results['roi_analysis'] = self._calculate_roi_metrics(df)
        
        # 4. Segmentação automática
        results['segmentation'] = self._perform_segmentation(df)
        
        # 5. Análise preditiva
        if self.config['enable_predictive_analytics']:
            results['predictions'] = self._generate_predictions(df)
        
        # 6. Insights automatizados
        results['insights'] = self._generate_automated_insights(df)
        
        # 7. Recomendações estratégicas
        results['recommendations'] = self._generate_strategic_recommendations(results)
        
        # 8. Compliance LGPD
        if self.config['lgpd_compliant']:
            results['compliance_status'] = self._check_lgpd_compliance(df)
        
        return results
    
    def _prepare_data_for_ml(self, df: pd.DataFrame) -> pd.DataFrame:
        """Prepara dados para machine learning"""
        # Converter datas string para datetime
        date_columns = ['data_inscricao', 'data_nascimento', 'data_processamento']
        for col in date_columns:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')
        
        # Feature engineering
        if 'data_inscricao' in df.columns:
            df['dias_desde_inscricao'] = (datetime.now() - df['data_inscricao']).dt.days
            df['mes_inscricao'] = df['data_inscricao'].dt.month
            df['dia_semana_inscricao'] = df['data_inscricao'].dt.dayofweek
        
        # Criar features compostas
        if 'nivel_cargo' in df.columns and 'faturamento_score' in df.columns:
            df['potencial_score'] = df['nivel_cargo'].map({
                'C-Level': 5, 'Diretoria': 4, 'Gerência': 3, 
                'Coordenação': 2, 'Especialista': 1, 'Operacional': 0
            }).fillna(0) * df['faturamento_score']
        
        return df
    
    def _build_ml_models(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Constrói e treina modelos de ML"""
        ml_results = {}
        
        # 1. Modelo de Propensão à Conversão
        logger.info("Treinando modelo de propensão à conversão")
        conversion_model = self._train_conversion_model(df)
        if conversion_model:
            ml_results['conversion_propensity'] = conversion_model
        
        # 2. Modelo de Lifetime Value (LTV)
        logger.info("Treinando modelo de LTV")
        ltv_model = self._train_ltv_model(df)
        if ltv_model:
            ml_results['lifetime_value'] = ltv_model
        
        # 3. Modelo de Churn Risk
        logger.info("Treinando modelo de risco de churn")
        churn_model = self._train_churn_model(df)
        if churn_model:
            ml_results['churn_risk'] = churn_model
        
        # 4. Modelo de Next Best Action
        logger.info("Treinando modelo de próxima melhor ação")
        nba_model = self._train_next_best_action_model(df)
        if nba_model:
            ml_results['next_best_action'] = nba_model
        
        return ml_results
    
    def _train_conversion_model(self, df: pd.DataFrame) -> Optional[Dict]:
        """Treina modelo de propensão à conversão"""
        # Features para conversão
        feature_cols = [
            'engagement_score', 'faturamento_score', 'dias_desde_inscricao',
            'email_valido', 'cpf_valido', 'idade'
        ]
        
        # Verificar disponibilidade de features
        available_features = [col for col in feature_cols if col in df.columns]
        
        if len(available_features) < 3:
            logger.warning("Features insuficientes para modelo de conversão")
            return None
        
        # Criar target sintético (exemplo - em produção usar dados reais)
        df['converted'] = (
            (df.get('engagement_score', 0) > 60) & 
            (df.get('faturamento_score', 0) >= 3)
        ).astype(int)
        
        # Preparar dados
        X = df[available_features].fillna(0)
        y = df['converted']
        
        # Dividir dados
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        # Escalar features
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        
        # Treinar modelo
        model = RandomForestClassifier(
            n_estimators=100,
            max_depth=5,
            random_state=42,
            class_weight='balanced'
        )
        model.fit(X_train_scaled, y_train)
        
        # Avaliar modelo
        y_pred = model.predict(X_test_scaled)
        accuracy = accuracy_score(y_test, y_pred)
        precision, recall, f1, _ = precision_recall_fscore_support(
            y_test, y_pred, average='binary'
        )
        
        # Feature importance
        feature_importance = pd.DataFrame({
            'feature': available_features,
            'importance': model.feature_importances_
        }).sort_values('importance', ascending=False)
        
        # Salvar modelo e scaler
        self.models['conversion'] = model
        self.scalers['conversion'] = scaler
        
        return {
            'accuracy': float(accuracy),
            'precision': float(precision),
            'recall': float(recall),
            'f1_score': float(f1),
            'feature_importance': feature_importance.to_dict('records'),
            'conversion_rate': float(y.mean()),
            'model_type': 'RandomForestClassifier'
        }
    
    def _train_ltv_model(self, df: pd.DataFrame) -> Optional[Dict]:
        """Treina modelo de Lifetime Value"""
        # Features para LTV
        feature_cols = [
            'faturamento_score', 'nivel_cargo', 'engagement_score',
            'dias_desde_inscricao', 'idade'
        ]
        
        available_features = []
        for col in feature_cols:
            if col in df.columns:
                if df[col].dtype == 'object':
                    # Encoding para variáveis categóricas
                    le = LabelEncoder()
                    df[f'{col}_encoded'] = le.fit_transform(df[col].fillna('unknown'))
                    available_features.append(f'{col}_encoded')
                    self.encoders[col] = le
                else:
                    available_features.append(col)
        
        if len(available_features) < 3:
            return None
        
        # Criar LTV sintético (em produção usar dados reais de faturamento)
        df['ltv'] = (
            df.get('faturamento_score', 1) * 10000 * 
            np.random.uniform(0.8, 1.2, len(df)) *
            (1 + df.get('engagement_score', 50) / 100)
        )
        
        X = df[available_features].fillna(0)
        y = df['ltv']
        
        # Dividir e escalar
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        
        # Treinar modelo
        model = RandomForestRegressor(
            n_estimators=100,
            max_depth=5,
            random_state=42
        )
        model.fit(X_train_scaled, y_train)
        
        # Avaliar
        y_pred = model.predict(X_test_scaled)
        mae = mean_absolute_error(y_test, y_pred)
        mape = np.mean(np.abs((y_test - y_pred) / y_test)) * 100
        
        # Salvar modelo
        self.models['ltv'] = model
        self.scalers['ltv'] = scaler
        
        return {
            'mae': float(mae),
            'mape': float(mape),
            'avg_ltv': float(y.mean()),
            'ltv_distribution': {
                'min': float(y.min()),
                'q1': float(y.quantile(0.25)),
                'median': float(y.median()),
                'q3': float(y.quantile(0.75)),
                'max': float(y.max())
            },
            'model_type': 'RandomForestRegressor'
        }
    
    def _train_churn_model(self, df: pd.DataFrame) -> Optional[Dict]:
        """Treina modelo de risco de churn"""
        # Para churn, precisamos de dados históricos
        # Aqui simulamos com base em engagement
        
        if 'engagement_score' not in df.columns:
            return None
        
        # Simular churn baseado em baixo engajamento e tempo
        df['churn_risk'] = (
            (df['engagement_score'] < 30) | 
            (df.get('dias_desde_inscricao', 0) > 180)
        ).astype(int)
        
        # Features
        feature_cols = ['engagement_score', 'dias_desde_inscricao', 'email_valido']
        available_features = [col for col in feature_cols if col in df.columns]
        
        X = df[available_features].fillna(0)
        y = df['churn_risk']
        
        # Treinar modelo similar ao de conversão
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        model = RandomForestClassifier(n_estimators=50, random_state=42)
        model.fit(X_train, y_train)
        
        accuracy = accuracy_score(y_test, model.predict(X_test))
        
        self.models['churn'] = model
        
        return {
            'accuracy': float(accuracy),
            'churn_rate': float(y.mean()),
            'high_risk_count': int((y == 1).sum()),
            'risk_factors': available_features
        }
    
    def _train_next_best_action_model(self, df: pd.DataFrame) -> Optional[Dict]:
        """Treina modelo para próxima melhor ação"""
        # Definir ações possíveis baseadas no perfil
        actions = {
            'email_nurturing': lambda x: x.get('engagement_score', 0) < 40,
            'sales_call': lambda x: x.get('faturamento_score', 0) >= 3 and x.get('engagement_score', 0) > 60,
            'webinar_invite': lambda x: 40 <= x.get('engagement_score', 0) <= 60,
            'vip_program': lambda x: x.get('potencial_score', 0) > 15,
            'reactivation': lambda x: x.get('dias_desde_inscricao', 0) > 90
        }
        
        # Calcular melhor ação para cada lead
        nba_recommendations = []
        
        for idx, row in df.iterrows():
            row_dict = row.to_dict()
            best_action = None
            best_score = 0
            
            for action, condition in actions.items():
                if condition(row_dict):
                    # Score baseado em potencial e adequação
                    score = row_dict.get('potencial_score', 1) * np.random.uniform(0.7, 1.0)
                    if score > best_score:
                        best_score = score
                        best_action = action
            
            if best_action:
                nba_recommendations.append({
                    'id': row_dict.get('id_unico', idx),
                    'action': best_action,
                    'score': best_score,
                    'nome': row_dict.get('nome_completo', 'Unknown'),
                    'empresa': row_dict.get('empresa', 'Unknown')
                })
        
        # Top recomendações
        top_recommendations = sorted(
            nba_recommendations, 
            key=lambda x: x['score'], 
            reverse=True
        )[:20]
        
        return {
            'total_recommendations': len(nba_recommendations),
            'action_distribution': pd.DataFrame(nba_recommendations)['action'].value_counts().to_dict(),
            'top_recommendations': top_recommendations
        }
    
    def _calculate_roi_metrics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calcula métricas de ROI"""
        roi_metrics = {
            'method': self.config['roi_calculation_method'],
            'metrics': {},
            'cohort_analysis': {},
            'investment_return': {}
        }
        
        # 1. Customer Acquisition Cost (CAC) simulado
        total_leads = len(df)
        marketing_investment = 50000  # Exemplo fixo
        cac = marketing_investment / total_leads if total_leads > 0 else 0
        
        roi_metrics['metrics']['cac'] = float(cac)
        
        # 2. Lifetime Value médio
        if 'ltv' in df.columns:
            avg_ltv = df['ltv'].mean()
            roi_metrics['metrics']['avg_ltv'] = float(avg_ltv)
            roi_metrics['metrics']['ltv_cac_ratio'] = float(avg_ltv / cac) if cac > 0 else 0
        
        # 3. Análise por cohort (mês de inscrição)
        if 'data_inscricao' in df.columns:
            df['cohort_month'] = df['data_inscricao'].dt.to_period('M')
            
            cohort_metrics = []
            for cohort in df['cohort_month'].unique():
                if pd.notna(cohort):
                    cohort_data = df[df['cohort_month'] == cohort]
                    cohort_metrics.append({
                        'cohort': str(cohort),
                        'size': len(cohort_data),
                        'avg_engagement': float(cohort_data.get('engagement_score', 0).mean()),
                        'conversion_rate': float(cohort_data.get('converted', 0).mean()) if 'converted' in cohort_data.columns else 0
                    })
            
            roi_metrics['cohort_analysis'] = sorted(
                cohort_metrics, 
                key=lambda x: x['cohort'], 
                reverse=True
            )[:6]  # Últimos 6 meses
        
        # 4. ROI projetado
        if 'converted' in df.columns and 'ltv' in df.columns:
            converted_count = df['converted'].sum()
            total_revenue = df[df['converted'] == 1]['ltv'].sum() if converted_count > 0 else 0
            roi = ((total_revenue - marketing_investment) / marketing_investment) * 100
            
            roi_metrics['investment_return'] = {
                'total_investment': float(marketing_investment),
                'projected_revenue': float(total_revenue),
                'roi_percentage': float(roi),
                'payback_period_months': float(marketing_investment / (total_revenue / 12)) if total_revenue > 0 else None
            }
        
        return roi_metrics
    
    def _perform_segmentation(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Realiza segmentação automática dos leads"""
        segmentation_results = {
            'algorithm': self.config['clustering_algorithm'],
            'segments': [],
            'distribution': {},
            'characteristics': {}
        }
        
        # Features para clustering
        feature_cols = ['engagement_score', 'faturamento_score', 'idade', 'dias_desde_inscricao']
        available_features = [col for col in feature_cols if col in df.columns]
        
        if len(available_features) < 2:
            logger.warning("Features insuficientes para segmentação")
            return segmentation_results
        
        # Preparar dados
        X = df[available_features].fillna(0)
        
        # Normalizar
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        # Clustering
        kmeans = KMeans(
            n_clusters=self.config['n_clusters'], 
            random_state=42,
            n_init=10
        )
        clusters = kmeans.fit_predict(X_scaled)
        
        df['segment'] = clusters
        
        # Analisar cada segmento
        for segment_id in range(self.config['n_clusters']):
            segment_data = df[df['segment'] == segment_id]
            
            segment_profile = {
                'segment_id': int(segment_id),
                'size': len(segment_data),
                'percentage': float(len(segment_data) / len(df) * 100),
                'characteristics': {}
            }
            
            # Características do segmento
            for feature in available_features:
                segment_profile['characteristics'][feature] = {
                    'mean': float(segment_data[feature].mean()),
                    'std': float(segment_data[feature].std())
                }
            
            # Nome descritivo do segmento
            segment_profile['name'] = self._name_segment(segment_profile['characteristics'])
            
            # Empresas exemplo
            if 'empresa' in segment_data.columns:
                segment_profile['example_companies'] = segment_data['empresa'].dropna().head(5).tolist()
            
            segmentation_results['segments'].append(segment_profile)
        
        # Distribuição
        segmentation_results['distribution'] = df['segment'].value_counts().to_dict()
        
        return segmentation_results
    
    def _name_segment(self, characteristics: Dict) -> str:
        """Gera nome descritivo para o segmento"""
        engagement = characteristics.get('engagement_score', {}).get('mean', 0)
        revenue = characteristics.get('faturamento_score', {}).get('mean', 0)
        
        if engagement > 70 and revenue >= 4:
            return "Premium Engajados"
        elif engagement > 70 and revenue < 4:
            return "Entusiastas Emergentes"
        elif engagement < 30 and revenue >= 4:
            return "Grandes Dormentes"
        elif engagement < 30 and revenue < 4:
            return "Exploratórios"
        else:
            return "Potencial Médio"
    
    def _generate_predictions(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Gera predições usando os modelos treinados"""
        predictions = {
            'conversion_predictions': [],
            'ltv_predictions': [],
            'churn_predictions': [],
            'summary': {}
        }
        
        # Predições de conversão
        if 'conversion' in self.models:
            model = self.models['conversion']
            scaler = self.scalers['conversion']
            
            feature_cols = ['engagement_score', 'faturamento_score', 'dias_desde_inscricao',
                          'email_valido', 'cpf_valido', 'idade']
            available_features = [col for col in feature_cols if col in df.columns]
            
            X = df[available_features].fillna(0)
            X_scaled = scaler.transform(X)
            
            # Probabilidades de conversão
            conv_probs = model.predict_proba(X_scaled)[:, 1]
            
            # Top 10 leads mais prováveis de converter
            top_indices = np.argsort(conv_probs)[-10:][::-1]
            
            for idx in top_indices:
                predictions['conversion_predictions'].append({
                    'nome': df.iloc[idx].get('nome_completo', 'Unknown'),
                    'empresa': df.iloc[idx].get('empresa', 'Unknown'),
                    'probability': float(conv_probs[idx]),
                    'engagement_score': float(df.iloc[idx].get('engagement_score', 0))
                })
        
        # Estatísticas resumidas
        if len(conv_probs) > 0:
            predictions['summary']['conversion'] = {
                'high_probability_count': int((conv_probs > 0.7).sum()),
                'medium_probability_count': int(((conv_probs > 0.3) & (conv_probs <= 0.7)).sum()),
                'low_probability_count': int((conv_probs <= 0.3).sum()),
                'avg_probability': float(conv_probs.mean())
            }
        
        return predictions
    
    def _generate_automated_insights(self, df: pd.DataFrame) -> List[Dict]:
        """Gera insights automatizados dos dados"""
        insights = []
        
        # 1. Insight sobre qualidade dos dados
        if 'email_valido' in df.columns:
            invalid_email_pct = (1 - df['email_valido'].mean()) * 100
            if invalid_email_pct > 10:
                insights.append({
                    'type': 'data_quality',
                    'severity': 'high' if invalid_email_pct > 20 else 'medium',
                    'insight': f"{invalid_email_pct:.1f}% dos emails são inválidos",
                    'impact': "Redução na efetividade de campanhas de email",
                    'recommendation': "Implementar verificação de email em tempo real no formulário"
                })
        
        # 2. Insight sobre engajamento
        if 'engagement_score' in df.columns:
            low_engagement_pct = (df['engagement_score'] < 30).mean() * 100
            if low_engagement_pct > 40:
                insights.append({
                    'type': 'engagement',
                    'severity': 'high',
                    'insight': f"{low_engagement_pct:.1f}% dos leads têm baixo engajamento",
                    'impact': "Baixa taxa de conversão esperada",
                    'recommendation': "Criar programa de nutrição segmentado por perfil"
                })
        
        # 3. Insight sobre potencial de receita
        if 'faturamento_score' in df.columns:
            high_value_pct = (df['faturamento_score'] >= 4).mean() * 100
            insights.append({
                'type': 'revenue_opportunity',
                'severity': 'info',
                'insight': f"{high_value_pct:.1f}% dos leads são de empresas de grande porte",
                'impact': "Alto potencial de receita por cliente",
                'recommendation': "Desenvolver abordagem personalizada para contas enterprise"
            })
        
        # 4. Insight sobre sazonalidade
        if 'mes_inscricao' in df.columns:
            monthly_dist = df['mes_inscricao'].value_counts()
            peak_month = monthly_dist.idxmax()
            insights.append({
                'type': 'seasonality',
                'severity': 'info',
                'insight': f"Pico de inscrições no mês {peak_month}",
                'impact': "Oportunidade para planejamento de campanhas",
                'recommendation': "Aumentar investimento em marketing nos meses anteriores ao pico"
            })
        
        # 5. Insight sobre segmentos
        if 'segmento' in df.columns:
            top_segment = df['segmento'].value_counts().index[0]
            segment_concentration = df['segmento'].value_counts().iloc[0] / len(df) * 100
            if segment_concentration > 30:
                insights.append({
                    'type': 'market_concentration',
                    'severity': 'medium',
                    'insight': f"{segment_concentration:.1f}% dos leads são do segmento {top_segment}",
                    'impact': "Alta dependência de um único segmento",
                    'recommendation': "Diversificar estratégia para outros segmentos"
                })
        
        return insights
    
    def _generate_strategic_recommendations(self, results: Dict) -> List[Dict]:
        """Gera recomendações estratégicas baseadas em toda análise"""
        recommendations = []
        
        # 1. Baseado em ROI
        if 'roi_analysis' in results and 'investment_return' in results['roi_analysis']:
            roi_pct = results['roi_analysis']['investment_return'].get('roi_percentage', 0)
            if roi_pct < 100:
                recommendations.append({
                    'priority': 'high',
                    'category': 'roi_optimization',
                    'recommendation': "Otimizar funil de conversão",
                    'expected_impact': "Aumento de 20-30% no ROI",
                    'actions': [
                        "Implementar lead scoring baseado em ML",
                        "Criar jornadas personalizadas por segmento",
                        "Automatizar follow-up de leads quentes"
                    ]
                })
        
        # 2. Baseado em segmentação
        if 'segmentation' in results and 'segments' in results['segmentation']:
            for segment in results['segmentation']['segments']:
                if segment['name'] == "Premium Engajados" and segment['percentage'] < 20:
                    recommendations.append({
                        'priority': 'high',
                        'category': 'growth',
                        'recommendation': f"Expandir segmento {segment['name']}",
                        'expected_impact': "Aumento de 40% em receita",
                        'actions': [
                            "Criar programa VIP exclusivo",
                            "Desenvolver conteúdo premium",
                            "Implementar account-based marketing"
                        ]
                    })
        
        # 3. Baseado em ML predictions
        if 'predictions' in results and 'summary' in results['predictions']:
            conv_summary = results['predictions']['summary'].get('conversion', {})
            if conv_summary.get('high_probability_count', 0) > 10:
                recommendations.append({
                    'priority': 'immediate',
                    'category': 'sales',
                    'recommendation': "Ação imediata em leads de alta probabilidade",
                    'expected_impact': f"Conversão de {conv_summary['high_probability_count']} leads",
                    'actions': [
                        "Contato direto do time de vendas em 48h",
                        "Oferta personalizada baseada no perfil",
                        "Demo exclusiva do programa"
                    ]
                })
        
        # 4. Baseado em insights
        data_quality_issues = [i for i in results.get('insights', []) if i['type'] == 'data_quality']
        if data_quality_issues:
            recommendations.append({
                'priority': 'medium',
                'category': 'operations',
                'recommendation': "Melhorar qualidade dos dados",
                'expected_impact': "Aumento de 15% em eficiência operacional",
                'actions': [
                    "Implementar validação em tempo real",
                    "Criar processo de enriquecimento de dados",
                    "Treinar equipe em boas práticas de CRM"
                ]
            })
        
        return recommendations
    
    def _check_lgpd_compliance(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Verifica compliance com LGPD"""
        compliance_status = {
            'compliant': True,
            'issues': [],
            'recommendations': [],
            'metrics': {}
        }
        
        # 1. Verificar consentimento
        if 'lgpd_consentimento_dado' in df.columns:
            consent_rate = df['lgpd_consentimento_dado'].mean() * 100
            compliance_status['metrics']['consent_rate'] = float(consent_rate)
            
            if consent_rate < 100:
                compliance_status['compliant'] = False
                compliance_status['issues'].append({
                    'issue': 'Consentimento incompleto',
                    'severity': 'high',
                    'affected_records': int(df[~df['lgpd_consentimento_dado']].shape[0])
                })
                compliance_status['recommendations'].append(
                    "Implementar campanha de re-consentimento para bases antigas"
                )
        
        # 2. Verificar anonimização
        sensitive_fields = ['cpf', 'rg', 'data_nascimento']
        exposed_fields = [f for f in sensitive_fields if f in df.columns and not f'{f}_anonimizado' in df.columns]
        
        if exposed_fields:
            compliance_status['issues'].append({
                'issue': 'Dados sensíveis não anonimizados',
                'severity': 'medium',
                'fields': exposed_fields
            })
            compliance_status['recommendations'].append(
                "Implementar anonimização automática para dados sensíveis em análises"
            )
        
        # 3. Verificar retenção de dados
        if 'data_inscricao' in df.columns:
            old_data = df[df['data_inscricao'] < datetime.now() - timedelta(days=730)]  # 2 anos
            if len(old_data) > 0:
                compliance_status['issues'].append({
                    'issue': 'Dados antigos sem revisão',
                    'severity': 'low',
                    'affected_records': len(old_data)
                })
                compliance_status['recommendations'].append(
                    "Implementar política de retenção e revisão periódica"
                )
        
        return compliance_status
    
    def generate_executive_report(self, results: Dict) -> str:
        """Gera relatório executivo em formato Markdown"""
        report = f"""# Relatório Executivo - Analytics CRM CRM
## Data: {datetime.now().strftime('%d/%m/%Y')}

### Resumo Executivo

- **Total de Registros Analisados**: {results['total_records']:,}
- **Qualidade dos Dados**: {results['data_quality']}%
- **ROI Projetado**: {results.get('roi_analysis', {}).get('investment_return', {}).get('roi_percentage', 0):.1f}%

### Principais Insights

"""
        # Top 3 insights
        for insight in results.get('insights', [])[:3]:
            report += f"- **{insight['type'].replace('_', ' ').title()}**: {insight['insight']}\n"
            report += f"  - Impacto: {insight['impact']}\n"
            report += f"  - Recomendação: {insight['recommendation']}\n\n"
        
        report += "\n### Recomendações Estratégicas\n\n"
        
        # Recomendações por prioridade
        high_priority = [r for r in results.get('recommendations', []) if r['priority'] == 'high']
        immediate = [r for r in results.get('recommendations', []) if r['priority'] == 'immediate']
        
        if immediate:
            report += "#### Ação Imediata Necessária\n"
            for rec in immediate:
                report += f"- **{rec['recommendation']}**\n"
                report += f"  - Impacto Esperado: {rec['expected_impact']}\n"
                report += f"  - Ações: {', '.join(rec['actions'][:2])}\n\n"
        
        if high_priority:
            report += "#### Alta Prioridade\n"
            for rec in high_priority:
                report += f"- **{rec['recommendation']}**\n"
                report += f"  - Categoria: {rec['category']}\n"
                report += f"  - Impacto: {rec['expected_impact']}\n\n"
        
        # Segmentação
        if 'segmentation' in results:
            report += "\n### Análise de Segmentação\n\n"
            for segment in results['segmentation']['segments'][:3]:
                report += f"- **{segment['name']}**: {segment['size']} leads ({segment['percentage']:.1f}%)\n"
        
        # Compliance
        if 'compliance_status' in results:
            report += f"\n### Status de Compliance LGPD\n\n"
            report += f"- **Status**: {'✅ Conforme' if results['compliance_status']['compliant'] else '⚠️ Atenção Necessária'}\n"
            if results['compliance_status']['issues']:
                report += f"- **Issues Identificadas**: {len(results['compliance_status']['issues'])}\n"
        
        return report


# Sistema de pesquisa automatizada
class AutomatedResearchEngine:
    """Motor de pesquisa automatizada para enriquecimento de dados"""
    
    def __init__(self):
        self.research_queue = []
        self.results_cache = {}
        
    def enrich_company_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Enriquece dados de empresas com informações públicas"""
        enriched_df = df.copy()
        
        # Simular enriquecimento (em produção, usar APIs reais)
        if 'empresa' in enriched_df.columns:
            enriched_df['setor_economico'] = enriched_df['empresa'].apply(
                lambda x: self._classify_sector(x) if pd.notna(x) else None
            )
            
            enriched_df['porte_estimado'] = enriched_df.apply(
                lambda row: self._estimate_company_size(row), axis=1
            )
            
            enriched_df['score_credito_estimado'] = np.random.randint(300, 850, len(enriched_df))
        
        return enriched_df
    
    def _classify_sector(self, company_name: str) -> str:
        """Classifica setor econômico baseado no nome"""
        company_lower = company_name.lower()
        
        sectors = {
            'tecnologia': ['tech', 'software', 'sistemas', 'digital', 'it'],
            'saúde': ['saude', 'health', 'clinica', 'hospital', 'medical'],
            'educação': ['edu', 'escola', 'ensino', 'training'],
            'varejo': ['store', 'loja', 'comercio', 'shop'],
            'serviços': ['consultoria', 'services', 'solutions'],
            'indústria': ['industria', 'factory', 'manufatura']
        }
        
        for sector, keywords in sectors.items():
            if any(kw in company_lower for kw in keywords):
                return sector
        
        return 'outros'
    
    def _estimate_company_size(self, row: pd.Series) -> str:
        """Estima porte da empresa baseado em indicadores"""
        score = 0
        
        if row.get('faturamento_score', 0) >= 4:
            score += 3
        elif row.get('faturamento_score', 0) >= 3:
            score += 2
        else:
            score += 1
            
        if row.get('nivel_cargo') in ['C-Level', 'Diretoria']:
            score += 1
            
        if score >= 4:
            return 'grande'
        elif score >= 2:
            return 'média'
        else:
            return 'pequena'


# Função principal de demonstração
def run_complete_analysis(data_file: str = 'crm_crm_centralizado.json'):
    """Executa análise completa do CRM"""
    
    # Configuração
    config = {
        'enable_ml': True,
        'enable_roi_tracking': True,
        'enable_predictive_analytics': True,
        'lgpd_compliant': True
    }
    
    # Inicializar engines
    analytics = CRMAnalyticsEngine(config)
    research = AutomatedResearchEngine()
    
    # Executar análise
    logger.info("Iniciando análise completa do CRM do CRM")
    results = analytics.analyze_complete_dataset(data_file)
    
    # Gerar relatório executivo
    executive_report = analytics.generate_executive_report(results)
    
    # Salvar resultados
    with open('crm_analytics_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    with open('crm_executive_report.md', 'w', encoding='utf-8') as f:
        f.write(executive_report)
    
    # Log resumo
    logger.info("=" * 50)
    logger.info("ANÁLISE COMPLETA FINALIZADA")
    logger.info(f"Total de modelos ML treinados: {len(results.get('ml_models', {}))}")
    logger.info(f"Total de insights gerados: {len(results.get('insights', []))}")
    logger.info(f"Total de recomendações: {len(results.get('recommendations', []))}")
    logger.info(f"ROI Projetado: {results.get('roi_analysis', {}).get('investment_return', {}).get('roi_percentage', 0):.1f}%")
    logger.info("=" * 50)
    
    return results


if __name__ == "__main__":
    # Executar análise
    results = run_complete_analysis()