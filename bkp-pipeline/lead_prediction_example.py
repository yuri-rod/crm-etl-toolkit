#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Exemplo de Uso do Sistema para Análise de Novos Leads
Demonstra como usar os modelos treinados para analisar leads individualmente
"""

import pandas as pd
import numpy as np
import joblib
from advanced_ml_analytics import AdvancedMLAnalytics
import json
from datetime import datetime

class LeadPredictor:
    """
    Classe para fazer predições em novos leads usando modelos treinados
    """
    
    def __init__(self, models_dir='./ml_models/'):
        self.models_dir = models_dir
        self.analytics = None
        self.models_loaded = False
        
    def load_trained_models(self):
        """
        Carrega modelos já treinados
        """
        try:
            print("📎 Carregando modelos treinados...")
            
            # Carrega cada modelo
            model_files = [
                'lead_scoring_model.pkl',
                'conversion_probability_model.pkl',
                'roi_analysis_model.pkl',
                'churn_prediction_model.pkl',
                'segmentation_model.pkl',
                'funnel_analysis_model.pkl'
            ]
            
            self.models = {}
            for model_file in model_files:
                model_path = f"{self.models_dir}{model_file}"
                try:
                    model_name = model_file.replace('_model.pkl', '')
                    self.models[model_name] = joblib.load(model_path)
                    print(f"✅ {model_name} carregado")
                except FileNotFoundError:
                    print(f"⚠️ {model_file} não encontrado")
            
            self.models_loaded = len(self.models) > 0
            return self.models_loaded
            
        except Exception as e:
            print(f"❌ Erro ao carregar modelos: {e}")
            return False
    
    def prepare_lead_data(self, lead_data):
        """
        Prepara dados de um novo lead para análise
        """
        if isinstance(lead_data, dict):
            df = pd.DataFrame([lead_data])
        else:
            df = lead_data.copy()
        
        # Aplica as mesmas transformações do treinamento
        df['nome_length'] = df['nome'].astype(str).str.len()
        df['empresa_cargo_length'] = df['empresa_cargo'].astype(str).str.len()
        df['segmento_length'] = df['segmento'].astype(str).str.len()
        
        df['has_linkedin'] = df['linkedin'].astype(str).str.contains('linkedin', case=False, na=False).astype(int)
        df['has_cnpj'] = (df['cnpj'].astype(str).str.len() > 10).astype(int)
        df['has_whatsapp'] = df['whatsapp'].astype(str).str.contains(r'\+55|55', na=False).astype(int)
        df['has_email'] = df['email'].astype(str).str.contains('@', na=False).astype(int)
        
        df['estado'] = df['cidade_estado'].astype(str).str.extract(r'([A-Z]{2})$')
        df['estado'] = df['estado'].fillna('OUTROS')
        
        # Categoriza segmento
        def categorize_segment(segment):
            segment = str(segment).lower()
            if any(word in segment for word in ['tech', 'tecnologia', 'software', 'digital']):
                return 'TECNOLOGIA'
            elif any(word in segment for word in ['constru', 'engenharia', 'obra']):
                return 'CONSTRUCAO'
            elif any(word in segment for word in ['educa', 'ensino', 'escola']):
                return 'EDUCACAO'
            elif any(word in segment for word in ['saude', 'medic', 'hospital']):
                return 'SAUDE'
            elif any(word in segment for word in ['financ', 'invest', 'banco']):
                return 'FINANCAS'
            elif any(word in segment for word in ['comercio', 'venda', 'varejo']):
                return 'COMERCIO'
            else:
                return 'OUTROS'
        
        df['segmento_categoria'] = df['segmento'].apply(categorize_segment)
        
        # Features temporais
        try:
            df['aniversario_mes'] = pd.to_datetime(df['aniversario'], errors='coerce').dt.month
            df['aniversario_mes'] = df['aniversario_mes'].fillna(0).astype(int)
        except:
            df['aniversario_mes'] = 0
        
        # Score de qualidade
        df['data_quality_score'] = (
            df['has_email'] + 
            df['has_whatsapp'] + 
            df['has_linkedin'] + 
            (df['nome_length'] > 5).astype(int) +
            (df['segmento_length'] > 3).astype(int)
        )
        
        # Valor do segmento
        segment_values = {
            'TECNOLOGIA': 1.5, 'FINANCAS': 1.3, 'SAUDE': 1.2,
            'EDUCACAO': 1.0, 'CONSTRUCAO': 0.9, 'COMERCIO': 0.8, 'OUTROS': 0.7
        }
        df['segment_value_multiplier'] = df['segmento_categoria'].map(segment_values).fillna(0.7)
        
        # Encoding simples (usando valores padrão para novos dados)
        df['estado_civil_encoded'] = 0
        df['estado_encoded'] = 0
        df['segmento_categoria_encoded'] = {
            'TECNOLOGIA': 0, 'FINANCAS': 1, 'SAUDE': 2, 'EDUCACAO': 3,
            'CONSTRUCAO': 4, 'COMERCIO': 5, 'OUTROS': 6
        }.get(df['segmento_categoria'].iloc[0], 6)
        
        return df
    
    def analyze_single_lead(self, lead_data):
        """
        Analisa um único lead e retorna todas as predições
        """
        if not self.models_loaded:
            if not self.load_trained_models():
                return None
        
        # Prepara dados
        df = self.prepare_lead_data(lead_data)
        
        results = {
            'lead_info': {
                'nome': df['nome'].iloc[0],
                'empresa_cargo': df['empresa_cargo'].iloc[0],
                'segmento': df['segmento'].iloc[0],
                'email': df['email'].iloc[0]
            },
            'analysis_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # 1. Lead Scoring
        if 'lead_scoring' in self.models:
            try:
                model_data = self.models['lead_scoring']
                features = model_data['features']
                
                X = df[features].fillna(0)
                X_scaled = model_data['scaler'].transform(X)
                
                quality_pred = model_data['classifier'].predict(X)[0]
                quality_proba = model_data['classifier'].predict_proba(X)[0, 1]
                lead_score = model_data['regressor'].predict(X_scaled)[0]
                
                results['lead_scoring'] = {
                    'score': round(np.clip(lead_score, 0, 100), 1),
                    'quality': 'Alta' if quality_pred == 1 else 'Baixa',
                    'probability': round(quality_proba, 3),
                    'recommendation': 'Priorizar contato' if lead_score > 70 else 'Qualificar mais' if lead_score > 40 else 'Baixa prioridade'
                }
            except Exception as e:
                results['lead_scoring'] = {'error': str(e)}
        
        # 2. Probabilidade de Conversão
        if 'conversion_probability' in self.models:
            try:
                model_data = self.models['conversion_probability']
                features = model_data['features']
                
                X = df[features].fillna(0)
                
                # Random Forest prediction
                rf_pred = model_data['random_forest'].predict(X)[0]
                
                # Gradient Boosting prediction
                gb_proba = model_data['gradient_boosting'].predict_proba(X)[0, 1]
                
                avg_conversion = (rf_pred + gb_proba) / 2
                
                results['conversion_probability'] = {
                    'probability': round(avg_conversion, 3),
                    'rf_prediction': round(rf_pred, 3),
                    'gb_prediction': round(gb_proba, 3),
                    'category': 'Alto' if avg_conversion > 0.7 else 'Médio' if avg_conversion > 0.4 else 'Baixo'
                }
            except Exception as e:
                results['conversion_probability'] = {'error': str(e)}
        
        # 3. Análise de ROI
        if 'roi_analysis' in self.models:
            try:
                model_data = self.models['roi_analysis']
                features = model_data['features']
                
                # Adiciona conversion_probability se não existir
                if 'conversion_probability' not in df.columns:
                    df['conversion_probability'] = 0.5  # Valor padrão
                
                X = df[features].fillna(0)
                predicted_roi = model_data['model'].predict(X)[0]
                
                # Calcula opportunity score
                opportunity_score = predicted_roi * df['conversion_probability'].iloc[0]
                
                results['roi_analysis'] = {
                    'predicted_roi': round(predicted_roi, 0),
                    'opportunity_score': round(opportunity_score, 0),
                    'roi_category': 'Alto' if predicted_roi > 2000 else 'Médio' if predicted_roi > 1000 else 'Baixo'
                }
            except Exception as e:
                results['roi_analysis'] = {'error': str(e)}
        
        # 4. Risco de Churn
        if 'churn_prediction' in self.models:
            try:
                model_data = self.models['churn_prediction']
                features = model_data['features']
                
                # Adiciona features sintéticas necessárias
                if 'days_since_contact' not in df.columns:
                    df['days_since_contact'] = 0  # Novo lead
                if 'conversion_probability' not in df.columns:
                    df['conversion_probability'] = 0.5
                
                X = df[features].fillna(0)
                churn_proba = model_data['model'].predict_proba(X)[0, 1]
                
                # Gera recomendações
                recommendations = []
                if churn_proba > 0.7:
                    recommendations.extend(["Contato urgente", "Oferecer incentivos"])
                elif churn_proba > 0.5:
                    recommendations.extend(["Aumentar frequência de contato", "Personalizar abordagem"])
                else:
                    recommendations.append("Manter acompanhamento regular")
                
                if df['data_quality_score'].iloc[0] < 3:
                    recommendations.append("Atualizar dados de contato")
                
                results['churn_prediction'] = {
                    'risk_score': round(churn_proba, 3),
                    'risk_level': 'Alto' if churn_proba > 0.7 else 'Médio' if churn_proba > 0.5 else 'Baixo',
                    'recommendations': recommendations
                }
            except Exception as e:
                results['churn_prediction'] = {'error': str(e)}
        
        # 5. Segmentação/Persona
        if 'segmentation' in self.models:
            try:
                model_data = self.models['segmentation']
                features = model_data['features']
                
                # Adiciona features necessárias
                if 'conversion_probability' not in df.columns:
                    df['conversion_probability'] = 0.5
                if 'potential_roi' not in df.columns:
                    df['potential_roi'] = 1500  # Valor médio
                
                X = df[features].fillna(0)
                X_scaled = model_data['scaler'].transform(X)
                
                cluster_id = model_data['kmeans'].predict(X_scaled)[0]
                persona = model_data['persona_mapping'].get(cluster_id, 'Indefinido')
                
                results['segmentation'] = {
                    'persona': persona,
                    'cluster_id': int(cluster_id),
                    'description': {
                        'Empreendedor_Tech': 'Alta tecnologia, inovação, crescimento acelerado',
                        'Gestor_Tradicional': 'Setores tradicionais, crescimento estável',
                        'Startup_Founder': 'Empresas nascentes, alta necessidade de capital',
                        'CRM_Consolidado': 'Empresas estabelecidas, faturamento consistente',
                        'Freelancer_Pro': 'Profissionais autônomos, alta qualificação'
                    }.get(persona, 'Perfil indefinido')
                }
            except Exception as e:
                results['segmentation'] = {'error': str(e)}
        
        # Resumo executivo
        results['executive_summary'] = self._generate_executive_summary(results)
        
        return results
    
    def _generate_executive_summary(self, results):
        """
        Gera resumo executivo da análise
        """
        summary = {
            'priority_level': 'Média',
            'key_insights': [],
            'recommended_actions': [],
            'overall_score': 50
        }
        
        # Calcula score geral
        scores = []
        
        if 'lead_scoring' in results and 'score' in results['lead_scoring']:
            scores.append(results['lead_scoring']['score'])
        
        if 'conversion_probability' in results and 'probability' in results['conversion_probability']:
            scores.append(results['conversion_probability']['probability'] * 100)
        
        if 'roi_analysis' in results and 'predicted_roi' in results['roi_analysis']:
            roi_score = min(100, (results['roi_analysis']['predicted_roi'] / 30))  # Normaliza
            scores.append(roi_score)
        
        if scores:
            summary['overall_score'] = round(np.mean(scores), 1)
        
        # Determina prioridade
        if summary['overall_score'] > 75:
            summary['priority_level'] = 'Alta'
        elif summary['overall_score'] > 50:
            summary['priority_level'] = 'Média'
        else:
            summary['priority_level'] = 'Baixa'
        
        # Insights principais
        if 'lead_scoring' in results and results['lead_scoring'].get('score', 0) > 70:
            summary['key_insights'].append('Lead de alta qualidade identificado')
        
        if 'conversion_probability' in results and results['conversion_probability'].get('probability', 0) > 0.7:
            summary['key_insights'].append('Alta probabilidade de conversão')
        
        if 'roi_analysis' in results and results['roi_analysis'].get('predicted_roi', 0) > 2000:
            summary['key_insights'].append('Alto potencial de ROI')
        
        if 'churn_prediction' in results and results['churn_prediction'].get('risk_score', 0) > 0.7:
            summary['key_insights'].append('Risco elevado de churn - ação urgente')
        
        # Ações recomendadas
        if summary['priority_level'] == 'Alta':
            summary['recommended_actions'].extend([
                'Contato imediato',
                'Enviar proposta personalizada',
                'Agendar reunião comercial'
            ])
        elif summary['priority_level'] == 'Média':
            summary['recommended_actions'].extend([
                'Agendar contato em 24-48h',
                'Enviar material informativo',
                'Qualificar necessidades'
            ])
        else:
            summary['recommended_actions'].extend([
                'Incluir em nurturing',
                'Monitorar engagement',
                'Qualificar dados'
            ])
        
        return summary

def create_sample_leads():
    """
    Cria alguns leads de exemplo para demonstração
    """
    sample_leads = [
        {
            'nome': 'João Silva',
            'empresa_cargo': 'TechCorp - CTO',
            'segmento': 'Tecnologia',
            'linkedin': 'linkedin.com/in/joaosilva',
            'cnpj': '12345678000199',
            'whatsapp': '+5511999999999',
            'email': 'joao.silva@techcorp.com',
            'cidade_estado': 'São Paulo - SP',
            'estado_civil': 'Casado',
            'aniversario': '15/03/1985'
        },
        {
            'nome': 'Maria Santos',
            'empresa_cargo': 'Educação Online - Diretora',
            'segmento': 'Educação',
            'linkedin': '',
            'cnpj': '98765432000188',
            'whatsapp': '11987654321',
            'email': 'maria.santos@educacao.com.br',
            'cidade_estado': 'Rio de Janeiro - RJ',
            'estado_civil': 'Solteira',
            'aniversario': '22/07/1990'
        },
        {
            'nome': 'Carlos Oliveira',
            'empresa_cargo': 'Consultoria',
            'segmento': 'Consultoria',
            'linkedin': 'linkedin.com/in/carlosoliveira',
            'cnpj': '',
            'whatsapp': '',
            'email': 'carlos@consultoria.com',
            'cidade_estado': 'Belo Horizonte - MG',
            'estado_civil': 'Casado',
            'aniversario': '10/12/1978'
        }
    ]
    
    return sample_leads

def main():
    """
    Função principal de demonstração
    """
    print("🔎 DEMONSTRAÇÃO - ANÁLISE DE NOVOS LEADS")
    print("=" * 60)
    
    # Inicializa o preditor
    predictor = LeadPredictor()
    
    # Carrega modelos
    if not predictor.load_trained_models():
        print("❌ Não foi possível carregar os modelos.")
        print("   Execute primeiro o script de treinamento (demo_advanced_analytics.py)")
        return False
    
    # Obtém leads de exemplo
    sample_leads = create_sample_leads()
    
    print(f"\n📈 Analisando {len(sample_leads)} leads de exemplo...")
    print("=" * 60)
    
    # Analisa cada lead
    for i, lead_data in enumerate(sample_leads, 1):
        print(f"\n👤 LEAD {i}: {lead_data['nome']}")
        print("-" * 40)
        
        # Faz a análise
        analysis = predictor.analyze_single_lead(lead_data)
        
        if analysis:
            # Mostra resumo executivo
            summary = analysis['executive_summary']
            print(f"Score Geral: {summary['overall_score']}/100")
            print(f"Prioridade: {summary['priority_level']}")
            
            # Detalhes por modelo
            if 'lead_scoring' in analysis:
                ls = analysis['lead_scoring']
                if 'score' in ls:
                    print(f"Lead Score: {ls['score']}/100 ({ls['quality']})")
            
            if 'conversion_probability' in analysis:
                cp = analysis['conversion_probability']
                if 'probability' in cp:
                    print(f"Prob. Conversão: {cp['probability']} ({cp['category']})")
            
            if 'roi_analysis' in analysis:
                roi = analysis['roi_analysis']
                if 'predicted_roi' in roi:
                    print(f"ROI Predito: R$ {roi['predicted_roi']} ({roi['roi_category']})")
            
            if 'churn_prediction' in analysis:
                churn = analysis['churn_prediction']
                if 'risk_score' in churn:
                    print(f"Risco Churn: {churn['risk_score']} ({churn['risk_level']})")
            
            if 'segmentation' in analysis:
                seg = analysis['segmentation']
                if 'persona' in seg:
                    print(f"Persona: {seg['persona']}")
            
            # Ações recomendadas
            print("\nAções Recomendadas:")
            for action in summary['recommended_actions']:
                print(f"  • {action}")
        
        else:
            print("❌ Erro na análise")
    
    print(f"\n✅ Análise de {len(sample_leads)} leads concluída!")
    return True

if __name__ == "__main__":
    success = main()
    if success:
        print("\n✨ Sistema de predição funcionando perfeitamente!")
    else:
        print("\n❌ Falha na demonstração.")

