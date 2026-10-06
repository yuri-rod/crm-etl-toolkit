#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dashboard Interativo CRM CRM
Visualizacão interativa completa com segmentos, funil, scores, ROI, churn e ranking

Funcionalidades:
- Painel com segmentos, funil, scores, ROI, risco de churn, ranking dos leads
- Tooltips em português para todos os elementos
- Exportação HTML para compartilhamento offline
- Interface amigável para decisores não técnicos
"""

import dash
from dash import dcc, html, dash_table, Input, Output, State, callback
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import os
from typing import Dict, List, Tuple, Any

# Importar nossos módulos existentes
try:
    from advanced_ml_analytics import AdvancedMLAnalytics
except ImportError:
    print("Aviso: advanced_ml_analytics não encontrado. Usando dados sintéticos.")
    AdvancedMLAnalytics = None

class DashboardCRM:
    """
    Dashboard interativo completo para análise de CRM
    """
    
    def __init__(self, data_path: str = None):
        self.data_path = data_path
        self.df = None
        self.analytics = None
        self.app = dash.Dash(__name__, 
                           external_stylesheets=[
                               'https://codepen.io/chriddyp/pen/bWLwgP.css',
                               'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css'
                           ])
        self.setup_layout()
        self.setup_callbacks()
    
    def load_data(self):
        """
        Carrega e prepara os dados para o dashboard
        """
        if self.data_path and os.path.exists(self.data_path):
            self.df = pd.read_csv(self.data_path)
            if AdvancedMLAnalytics:
                self.analytics = AdvancedMLAnalytics(self.data_path)
                self.analytics.load_data()
                self.analytics.prepare_features()
        else:
            # Gerar dados sintéticos para demonstração
            self.df = self.generate_synthetic_data()
        
        return self.df is not None
    
    def generate_synthetic_data(self) -> pd.DataFrame:
        """
        Gera dados sintéticos para demonstração do dashboard
        """
        np.random.seed(42)
        n_leads = 1000
        
        # Dados básicos
        data = {
            'id': range(1, n_leads + 1),
            'nome': [f'Lead {i}' for i in range(1, n_leads + 1)],
            'email': [f'lead{i}@empresa{np.random.randint(1,100)}.com' for i in range(1, n_leads + 1)],
            'telefone': [f'11{np.random.randint(10000000, 99999999)}' for _ in range(n_leads)],
            'empresa': [f'Empresa {np.random.randint(1, 200)}' for _ in range(n_leads)],
            'segmento': np.random.choice(['Tecnologia', 'Varejo', 'Serviços', 'Indústria', 'Saúde'], n_leads),
            'porte_empresa': np.random.choice(['Micro', 'Pequena', 'Média'], n_leads, p=[0.5, 0.3, 0.2]),
            'origem': np.random.choice(['Website', 'Email Marketing', 'Redes Sociais', 'Indicação', 'Telefone'], n_leads),
            
            # Scores e métricas
            'lead_score': np.random.randint(0, 101, n_leads),
            'probabilidade_conversao': np.random.uniform(0, 1, n_leads),
            'valor_potencial': np.random.exponential(5000, n_leads),
            'risco_churn': np.random.uniform(0, 1, n_leads),
            
            # Status do funil
            'etapa_funil': np.random.choice([
                'Novo Lead', 'Qualificado', 'Oportunidade', 
                'Proposta', 'Negociação', 'Fechado Ganho', 'Fechado Perdido'
            ], n_leads, p=[0.3, 0.25, 0.2, 0.1, 0.08, 0.05, 0.02]),
            
            # Datas
            'data_criacao': pd.date_range(start='2024-01-01', end='2024-12-31', periods=n_leads),
            'ultima_interacao': pd.date_range(start='2024-11-01', end='2024-12-31', periods=n_leads),
            
            # Interações
            'num_interacoes': np.random.poisson(3, n_leads),
            'dias_sem_contato': np.random.exponential(7, n_leads).astype(int),
        }
        
        df = pd.DataFrame(data)
        
        # Calcular ROI estimado
        df['roi_estimado'] = (df['valor_potencial'] * df['probabilidade_conversao']) / 1000
        
        # Definir status convertido
        df['convertido'] = (df['etapa_funil'] == 'Fechado Ganho').astype(int)
        
        return df
    
    def calculate_kpis(self) -> Dict[str, Any]:
        """
        Calcula KPIs principais para o dashboard
        """
        if self.df is None:
            return {}
        
        kpis = {
            'total_leads': len(self.df),
            'leads_convertidos': len(self.df[self.df['convertido'] == 1]),
            'taxa_conversao': len(self.df[self.df['convertido'] == 1]) / len(self.df) * 100,
            'valor_total_pipeline': self.df['valor_potencial'].sum(),
            'score_medio': self.df['lead_score'].mean(),
            'risco_churn_medio': self.df['risco_churn'].mean() * 100,
            'roi_total': self.df['roi_estimado'].sum(),
        }
        
        return kpis
    
    def create_funil_chart(self) -> go.Figure:
        """
        Cria gráfico de funil de vendas
        """
        if self.df is None:
            return go.Figure()
        
        funil_data = self.df['etapa_funil'].value_counts().reindex([
            'Novo Lead', 'Qualificado', 'Oportunidade', 
            'Proposta', 'Negociação', 'Fechado Ganho', 'Fechado Perdido'
        ], fill_value=0)
        
        # Excluir fechado perdido do funil principal
        funil_vendas = funil_data.drop('Fechado Perdido', errors='ignore')
        
        fig = go.Figure(go.Funnel(
            y=funil_vendas.index,
            x=funil_vendas.values,
            textinfo="value+percent initial",
            texttemplate="%{value}<br>(%{percentInitial})",
            hovertemplate="<b>%{y}</b><br>" +
                          "Leads: %{value}<br>" +
                          "% do Total: %{percentInitial}<br>" +
                          "<extra></extra>",
            marker=dict(
                color=["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#17becf"],
                line=dict(color="white", width=2)
            )
        ))
        
        fig.update_layout(
            title={
                'text': '🎯 Funil de Vendas',
                'x': 0.5,
                'font': {'size': 20}
            },
            height=500,
            paper_bgcolor='white',
            plot_bgcolor='white'
        )
        
        return fig
    
    def create_segmentos_chart(self) -> go.Figure:
        """
        Cria gráfico de distribuição por segmentos
        """
        if self.df is None:
            return go.Figure()
        
        segmentos = self.df.groupby('segmento').agg({
            'id': 'count',
            'lead_score': 'mean',
            'valor_potencial': 'sum',
            'convertido': 'sum'
        }).round(2)
        
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=(
                'Volume de Leads por Segmento',
                'Score Médio por Segmento', 
                'Valor Total do Pipeline',
                'Taxa de Conversão por Segmento'
            ),
            specs=[[{"type": "bar"}, {"type": "bar"}],
                   [{"type": "bar"}, {"type": "bar"}]]
        )
        
        # Volume de leads
        fig.add_trace(
            go.Bar(
                x=segmentos.index,
                y=segmentos['id'],
                name='Volume',
                marker_color='#1f77b4',
                hovertemplate="<b>%{x}</b><br>Leads: %{y}<extra></extra>"
            ),
            row=1, col=1
        )
        
        # Score médio
        fig.add_trace(
            go.Bar(
                x=segmentos.index,
                y=segmentos['lead_score'],
                name='Score Médio',
                marker_color='#ff7f0e',
                hovertemplate="<b>%{x}</b><br>Score: %{y:.1f}<extra></extra>"
            ),
            row=1, col=2
        )
        
        # Valor pipeline
        fig.add_trace(
            go.Bar(
                x=segmentos.index,
                y=segmentos['valor_potencial'],
                name='Valor Pipeline',
                marker_color='#2ca02c',
                hovertemplate="<b>%{x}</b><br>Valor: R$ %{y:,.0f}<extra></extra>"
            ),
            row=2, col=1
        )
        
        # Taxa conversão
        taxa_conversao = (segmentos['convertido'] / segmentos['id'] * 100).fillna(0)
        fig.add_trace(
            go.Bar(
                x=segmentos.index,
                y=taxa_conversao,
                name='Taxa Conversão',
                marker_color='#d62728',
                hovertemplate="<b>%{x}</b><br>Taxa: %{y:.1f}%<extra></extra>"
            ),
            row=2, col=2
        )
        
        fig.update_layout(
            title={
                'text': '📊 Análise por Segmentos',
                'x': 0.5,
                'font': {'size': 20}
            },
            height=600,
            showlegend=False,
            paper_bgcolor='white',
            plot_bgcolor='white'
        )
        
        return fig
    
    def create_ranking_leads(self) -> pd.DataFrame:
        """
        Cria ranking dos melhores leads
        """
        if self.df is None:
            return pd.DataFrame()
        
        # Calcular score composto
        df_ranking = self.df.copy()
        df_ranking['score_composto'] = (
            df_ranking['lead_score'] * 0.4 +
            df_ranking['probabilidade_conversao'] * 100 * 0.3 +
            (df_ranking['valor_potencial'] / df_ranking['valor_potencial'].max()) * 100 * 0.2 +
            (1 - df_ranking['risco_churn']) * 100 * 0.1
        ).round(1)
        
        # Top 20 leads
        top_leads = df_ranking.nlargest(20, 'score_composto')[[
            'nome', 'empresa', 'segmento', 'lead_score', 
            'probabilidade_conversao', 'valor_potencial', 'risco_churn', 
            'score_composto', 'etapa_funil'
        ]].copy()
        
        # Formatar valores para exibição
        top_leads['probabilidade_conversao'] = (top_leads['probabilidade_conversao'] * 100).round(1)
        top_leads['valor_potencial'] = top_leads['valor_potencial'].round(0)
        top_leads['risco_churn'] = (top_leads['risco_churn'] * 100).round(1)
        
        return top_leads
    
    def create_roi_analysis(self) -> go.Figure:
        """
        Cria análise de ROI
        """
        if self.df is None:
            return go.Figure()
        
        # ROI por origem
        roi_origem = self.df.groupby('origem').agg({
            'roi_estimado': 'sum',
            'valor_potencial': 'sum',
            'id': 'count',
            'convertido': 'sum'
        }).round(2)
        
        roi_origem['roi_por_lead'] = (roi_origem['roi_estimado'] / roi_origem['id']).round(2)
        roi_origem['taxa_conversao'] = (roi_origem['convertido'] / roi_origem['id'] * 100).round(1)
        
        fig = make_subplots(
            rows=1, cols=2,
            subplot_titles=('ROI Total por Origem', 'ROI por Lead vs Taxa de Conversão'),
            specs=[[{"type": "bar"}, {"type": "scatter"}]]
        )
        
        # ROI total
        fig.add_trace(
            go.Bar(
                x=roi_origem.index,
                y=roi_origem['roi_estimado'],
                name='ROI Total',
                marker_color='#2ca02c',
                hovertemplate="<b>%{x}</b><br>ROI: R$ %{y:,.0f}<extra></extra>"
            ),
            row=1, col=1
        )
        
        # Scatter ROI vs Conversão
        fig.add_trace(
            go.Scatter(
                x=roi_origem['roi_por_lead'],
                y=roi_origem['taxa_conversao'],
                mode='markers+text',
                text=roi_origem.index,
                textposition='top center',
                marker=dict(
                    size=roi_origem['id']/10,
                    color=roi_origem['roi_estimado'],
                    colorscale='Viridis',
                    showscale=True,
                    colorbar=dict(title="ROI Total")
                ),
                name='Origem',
                hovertemplate="<b>%{text}</b><br>" +
                              "ROI por Lead: R$ %{x:.0f}<br>" +
                              "Taxa Conversão: %{y:.1f}%<br>" +
                              "Total Leads: %{marker.size:.0f}<br>" +
                              "<extra></extra>"
            ),
            row=1, col=2
        )
        
        fig.update_layout(
            title={
                'text': '💰 Análise de ROI',
                'x': 0.5,
                'font': {'size': 20}
            },
            height=500,
            paper_bgcolor='white',
            plot_bgcolor='white'
        )
        
        fig.update_xaxes(title_text="Origem", row=1, col=1)
        fig.update_yaxes(title_text="ROI (R$)", row=1, col=1)
        fig.update_xaxes(title_text="ROI por Lead (R$)", row=1, col=2)
        fig.update_yaxes(title_text="Taxa de Conversão (%)", row=1, col=2)
        
        return fig
    
    def create_churn_risk_chart(self) -> go.Figure:
        """
        Cria análise de risco de churn
        """
        if self.df is None:
            return go.Figure()
        
        # Categorizar risco
        df_churn = self.df.copy()
        df_churn['categoria_risco'] = pd.cut(
            df_churn['risco_churn'],
            bins=[0, 0.3, 0.6, 1.0],
            labels=['Baixo Risco', 'Médio Risco', 'Alto Risco']
        )
        
        # Distribuição por risco
        dist_risco = df_churn['categoria_risco'].value_counts()
        
        # Risco por segmento
        risco_segmento = df_churn.groupby('segmento')['risco_churn'].mean().sort_values(ascending=False)
        
        fig = make_subplots(
            rows=1, cols=2,
            subplot_titles=('Distribuição de Risco de Churn', 'Risco Médio por Segmento'),
            specs=[[{"type": "pie"}, {"type": "bar"}]]
        )
        
        # Gráfico de pizza
        colors = ['#2ca02c', '#ff7f0e', '#d62728']
        fig.add_trace(
            go.Pie(
                labels=dist_risco.index,
                values=dist_risco.values,
                marker_colors=colors,
                hovertemplate="<b>%{label}</b><br>" +
                              "Leads: %{value}<br>" +
                              "Percentual: %{percent}<br>" +
                              "<extra></extra>"
            ),
            row=1, col=1
        )
        
        # Gráfico de barras
        fig.add_trace(
            go.Bar(
                x=risco_segmento.index,
                y=risco_segmento.values * 100,
                marker_color='#d62728',
                hovertemplate="<b>%{x}</b><br>Risco Médio: %{y:.1f}%<extra></extra>"
            ),
            row=1, col=2
        )
        
        fig.update_layout(
            title={
                'text': '⚠️ Análise de Risco de Churn',
                'x': 0.5,
                'font': {'size': 20}
            },
            height=500,
            paper_bgcolor='white',
            plot_bgcolor='white',
            showlegend=False
        )
        
        fig.update_yaxes(title_text="Risco Médio (%)", row=1, col=2)
        
        return fig
    
    def setup_layout(self):
        """
        Define o layout do dashboard
        """
        self.app.layout = html.Div([
            # Header
            html.Div([
                html.H1("🚀 Dashboard CRM CRM", 
                        style={'textAlign': 'center', 'color': '#2c3e50', 'marginBottom': '30px'}),
                html.P("Análise Inteligente de Leads e Oportunidades", 
                       style={'textAlign': 'center', 'color': '#7f8c8d', 'fontSize': '18px'})
            ], style={'padding': '20px', 'backgroundColor': '#ecf0f1'}),
            
            # Botões de ação
            html.Div([
                html.Button("🔄 Atualizar Dados", id='btn-refresh', n_clicks=0, 
                          className='button-primary', style={'marginRight': '10px'}),
                html.Button("📥 Exportar HTML", id='btn-export', n_clicks=0, 
                          className='button-secondary'),
                html.Div(id='export-status', style={'marginTop': '10px', 'color': '#27ae60'})
            ], style={'textAlign': 'center', 'padding': '20px'}),
            
            # KPIs principais
            html.Div(id='kpis-container', style={'padding': '20px'}),
            
            # Gráficos principais - Linha 1
            html.Div([
                html.Div([
                    dcc.Graph(id='funil-chart')
                ], className='six columns'),
                
                html.Div([
                    dcc.Graph(id='segmentos-chart')
                ], className='six columns'),
            ], className='row', style={'padding': '20px'}),
            
            # Gráficos principais - Linha 2
            html.Div([
                html.Div([
                    dcc.Graph(id='roi-chart')
                ], className='six columns'),
                
                html.Div([
                    dcc.Graph(id='churn-chart')
                ], className='six columns'),
            ], className='row', style={'padding': '20px'}),
            
            # Ranking de leads
            html.Div([
                html.H3("🏆 Ranking dos Melhores Leads", 
                       style={'textAlign': 'center', 'color': '#2c3e50'}),
                html.Div(id='ranking-table')
            ], style={'padding': '20px'}),
            
            # Call to Actions
            html.Div([
                html.H3("🎯 Ações Recomendadas", 
                       style={'textAlign': 'center', 'color': '#2c3e50'}),
                html.Div(id='cta-container')
            ], style={'padding': '20px', 'backgroundColor': '#f8f9fa'}),
            
            # Dados ocultos para armazenamento
            dcc.Store(id='data-store'),
            
        ], style={'fontFamily': 'Arial, sans-serif'})
    
    def setup_callbacks(self):
        """
        Define os callbacks do dashboard
        """
        
        @self.app.callback(
            [Output('data-store', 'data'),
             Output('kpis-container', 'children'),
             Output('funil-chart', 'figure'),
             Output('segmentos-chart', 'figure'),
             Output('roi-chart', 'figure'),
             Output('churn-chart', 'figure'),
             Output('ranking-table', 'children'),
             Output('cta-container', 'children')],
            [Input('btn-refresh', 'n_clicks')]
        )
        def update_dashboard(n_clicks):
            # Carregar dados
            self.load_data()
            
            if self.df is None:
                return {}, html.Div("Erro ao carregar dados"), {}, {}, {}, {}, html.Div(), html.Div()
            
            # KPIs
            kpis = self.calculate_kpis()
            kpis_layout = self.create_kpis_layout(kpis)
            
            # Gráficos
            funil_fig = self.create_funil_chart()
            segmentos_fig = self.create_segmentos_chart()
            roi_fig = self.create_roi_analysis()
            churn_fig = self.create_churn_risk_chart()
            
            # Ranking
            ranking_df = self.create_ranking_leads()
            ranking_table = self.create_ranking_table(ranking_df)
            
            # CTAs
            cta_layout = self.create_cta_layout()
            
            return (
                self.df.to_dict('records'),
                kpis_layout,
                funil_fig,
                segmentos_fig,
                roi_fig,
                churn_fig,
                ranking_table,
                cta_layout
            )
        
        @self.app.callback(
            Output('export-status', 'children'),
            [Input('btn-export', 'n_clicks')],
            [State('data-store', 'data')]
        )
        def export_html(n_clicks, data):
            if n_clicks > 0 and data:
                try:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"dashboard_crm_{timestamp}.html"
                    
                    # Gerar HTML estático
                    self.export_static_html(filename)
                    
                    return f"✅ Dashboard exportado: {filename}"
                except Exception as e:
                    return f"❌ Erro na exportação: {str(e)}"
            return ""
    
    def create_kpis_layout(self, kpis: Dict[str, Any]) -> html.Div:
        """
        Cria layout dos KPIs principais
        """
        return html.Div([
            html.Div([
                html.Div([
                    html.H4(f"{kpis.get('total_leads', 0):,}", style={'margin': '0', 'color': '#2c3e50'}),
                    html.P("Total de Leads", style={'margin': '5px 0', 'color': '#7f8c8d'}),
                    html.I(className="fas fa-users", style={'fontSize': '30px', 'color': '#3498db'})
                ], className='kpi-card', style=self.get_kpi_style('#3498db')),
            ], className='two columns'),
            
            html.Div([
                html.Div([
                    html.H4(f"{kpis.get('leads_convertidos', 0):,}", style={'margin': '0', 'color': '#2c3e50'}),
                    html.P("Leads Convertidos", style={'margin': '5px 0', 'color': '#7f8c8d'}),
                    html.I(className="fas fa-check-circle", style={'fontSize': '30px', 'color': '#27ae60'})
                ], className='kpi-card', style=self.get_kpi_style('#27ae60')),
            ], className='two columns'),
            
            html.Div([
                html.Div([
                    html.H4(f"{kpis.get('taxa_conversao', 0):.1f}%", style={'margin': '0', 'color': '#2c3e50'}),
                    html.P("Taxa de Conversão", style={'margin': '5px 0', 'color': '#7f8c8d'}),
                    html.I(className="fas fa-percentage", style={'fontSize': '30px', 'color': '#e74c3c'})
                ], className='kpi-card', style=self.get_kpi_style('#e74c3c')),
            ], className='two columns'),
            
            html.Div([
                html.Div([
                    html.H4(f"R$ {kpis.get('valor_total_pipeline', 0):,.0f}", style={'margin': '0', 'color': '#2c3e50'}),
                    html.P("Valor do Pipeline", style={'margin': '5px 0', 'color': '#7f8c8d'}),
                    html.I(className="fas fa-dollar-sign", style={'fontSize': '30px', 'color': '#f39c12'})
                ], className='kpi-card', style=self.get_kpi_style('#f39c12')),
            ], className='two columns'),
            
            html.Div([
                html.Div([
                    html.H4(f"{kpis.get('score_medio', 0):.1f}", style={'margin': '0', 'color': '#2c3e50'}),
                    html.P("Score Médio", style={'margin': '5px 0', 'color': '#7f8c8d'}),
                    html.I(className="fas fa-star", style={'fontSize': '30px', 'color': '#9b59b6'})
                ], className='kpi-card', style=self.get_kpi_style('#9b59b6')),
            ], className='two columns'),
            
            html.Div([
                html.Div([
                    html.H4(f"R$ {kpis.get('roi_total', 0):,.0f}", style={'margin': '0', 'color': '#2c3e50'}),
                    html.P("ROI Total", style={'margin': '5px 0', 'color': '#7f8c8d'}),
                    html.I(className="fas fa-chart-line", style={'fontSize': '30px', 'color': '#1abc9c'})
                ], className='kpi-card', style=self.get_kpi_style('#1abc9c')),
            ], className='two columns'),
            
        ], className='row')
    
    def get_kpi_style(self, border_color: str) -> Dict[str, str]:
        """
        Retorna estilo para cartões KPI
        """
        return {
            'textAlign': 'center',
            'padding': '20px',
            'backgroundColor': 'white',
            'borderRadius': '10px',
            'boxShadow': '0 4px 6px rgba(0, 0, 0, 0.1)',
            'border': f'3px solid {border_color}',
            'margin': '10px'
        }
    
    def create_ranking_table(self, df: pd.DataFrame) -> dash_table.DataTable:
        """
        Cria tabela de ranking dos leads
        """
        if df.empty:
            return html.Div("Nenhum dado disponível")
        
        return dash_table.DataTable(
            data=df.to_dict('records'),
            columns=[
                {'name': 'Nome', 'id': 'nome'},
                {'name': 'Empresa', 'id': 'empresa'},
                {'name': 'Segmento', 'id': 'segmento'},
                {'name': 'Score', 'id': 'lead_score', 'type': 'numeric', 'format': {'specifier': '.0f'}},
                {'name': 'Prob. Conv. (%)', 'id': 'probabilidade_conversao', 'type': 'numeric', 'format': {'specifier': '.1f'}},
                {'name': 'Valor Pot. (R$)', 'id': 'valor_potencial', 'type': 'numeric', 'format': {'specifier': ',.0f'}},
                {'name': 'Risco Churn (%)', 'id': 'risco_churn', 'type': 'numeric', 'format': {'specifier': '.1f'}},
                {'name': 'Score Final', 'id': 'score_composto', 'type': 'numeric', 'format': {'specifier': '.1f'}},
                {'name': 'Etapa', 'id': 'etapa_funil'}
            ],
            style_table={'overflowX': 'auto'},
            style_cell={
                'textAlign': 'left',
                'padding': '10px',
                'fontFamily': 'Arial, sans-serif'
            },
            style_header={
                'backgroundColor': '#3498db',
                'color': 'white',
                'fontWeight': 'bold'
            },
            style_data_conditional=[
                {
                    'if': {'column_id': 'score_composto', 'filter_query': '{score_composto} >= 80'},
                    'backgroundColor': '#d5f4e6',
                    'color': 'black',
                },
                {
                    'if': {'column_id': 'risco_churn', 'filter_query': '{risco_churn} >= 70'},
                    'backgroundColor': '#fadbd8',
                    'color': 'black',
                }
            ],
            sort_action='native',
            filter_action='native',
            page_size=20,
            tooltip_data=[
                {
                    column: {
                        'value': f'**{column}**: {value}\n\nClique para ordenar ou filtrar os dados.',
                        'type': 'markdown'
                    }
                    for column, value in row.items()
                } for row in df.to_dict('records')
            ],
            tooltip_duration=None
        )
    
    def create_cta_layout(self) -> html.Div:
        """
        Cria layout de call-to-actions baseado nos dados
        """
        if self.df is None:
            return html.Div()
        
        # Análise rápida para CTAs
        high_risk_churn = len(self.df[self.df['risco_churn'] > 0.7])
        high_score_leads = len(self.df[self.df['lead_score'] > 80])
        stalled_leads = len(self.df[self.df['dias_sem_contato'] > 14])
        
        ctas = []
        
        if high_risk_churn > 0:
            ctas.append(
                html.Div([
                    html.H4("⚠️ Atenção: Risco de Churn", style={'color': '#e74c3c'}),
                    html.P(f"{high_risk_churn} leads com alto risco de churn precisam de atenção imediata."),
                    html.Button("Ver Leads em Risco", className='button-danger')
                ], className='cta-card')
            )
        
        if high_score_leads > 0:
            ctas.append(
                html.Div([
                    html.H4("🎯 Oportunidade: Leads Quentes", style={'color': '#27ae60'}),
                    html.P(f"{high_score_leads} leads com score alto (>80) prontos para abordagem."),
                    html.Button("Priorizar Contato", className='button-success')
                ], className='cta-card')
            )
        
        if stalled_leads > 0:
            ctas.append(
                html.Div([
                    html.H4("📞 Ação: Reativar Contatos", style={'color': '#f39c12'}),
                    html.P(f"{stalled_leads} leads sem contato há mais de 14 dias."),
                    html.Button("Planejar Follow-up", className='button-warning')
                ], className='cta-card')
            )
        
        if not ctas:
            ctas.append(
                html.Div([
                    html.H4("✅ Parabéns!", style={'color': '#27ae60'}),
                    html.P("Seu pipeline está bem gerenciado. Continue monitorando os indicadores.")
                ], className='cta-card')
            )
        
        return html.Div(ctas, className='row')
    
    def export_static_html(self, filename: str):
        """
        Exporta dashboard como HTML estático
        """
        # Carregar dados se necessário
        if self.df is None:
            self.load_data()
        
        # Criar versão estática
        kpis = self.calculate_kpis()
        
        static_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Dashboard CRM CRM - {datetime.now().strftime('%d/%m/%Y %H:%M')}</title>
            <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
            <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
            <style>
                body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f8f9fa; }}
                .header {{ text-align: center; background-color: #ecf0f1; padding: 20px; margin-bottom: 20px; border-radius: 10px; }}
                .kpi-container {{ display: flex; justify-content: space-around; margin: 20px 0; }}
                .kpi-card {{ background: white; padding: 20px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); text-align: center; min-width: 150px; }}
                .chart-container {{ margin: 20px 0; background: white; padding: 20px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
                .export-info {{ background: #d4edda; padding: 15px; border-radius: 5px; margin: 20px 0; border-left: 4px solid #28a745; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🚀 Dashboard CRM CRM</h1>
                <p>Relatório gerado em {datetime.now().strftime('%d/%m/%Y às %H:%M')}</p>
            </div>
            
            <div class="export-info">
                <strong>📊 Resumo Executivo:</strong><br>
                Total de Leads: {kpis.get('total_leads', 0):,} | 
                Taxa de Conversão: {kpis.get('taxa_conversao', 0):.1f}% | 
                ROI Total: R$ {kpis.get('roi_total', 0):,.0f}
            </div>
            
            <div class="kpi-container">
                <div class="kpi-card">
                    <h3>{kpis.get('total_leads', 0):,}</h3>
                    <p>Total de Leads</p>
                </div>
                <div class="kpi-card">
                    <h3>{kpis.get('leads_convertidos', 0):,}</h3>
                    <p>Leads Convertidos</p>
                </div>
                <div class="kpi-card">
                    <h3>{kpis.get('taxa_conversao', 0):.1f}%</h3>
                    <p>Taxa de Conversão</p>
                </div>
                <div class="kpi-card">
                    <h3>R$ {kpis.get('valor_total_pipeline', 0):,.0f}</h3>
                    <p>Valor Pipeline</p>
                </div>
            </div>
            
            <div class="chart-container">
                <div id="funil-chart"></div>
            </div>
            
            <div class="chart-container">
                <div id="roi-chart"></div>
            </div>
            
            <script>
                // Gráficos seriam renderizados aqui com Plotly.js
                var funilData = {self.create_funil_chart().to_json()};
                Plotly.newPlot('funil-chart', funilData.data, funilData.layout);
                
                var roiData = {self.create_roi_analysis().to_json()};
                Plotly.newPlot('roi-chart', roiData.data, roiData.layout);
            </script>
            
            <div style="text-align: center; margin-top: 40px; color: #7f8c8d;">
                <p>Dashboard gerado automaticamente pelo Sistema CRM CRM</p>
            </div>
        </body>
        </html>
        """
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(static_html)
    
    def run(self, debug=True, port=8050, host='127.0.0.1'):
        """
        Executa o dashboard
        """
        print(f"\n🚀 Iniciando Dashboard CRM CRM...")
        print(f"📊 Acesse: http://{host}:{port}")
        print(f"💡 Recursos disponíveis:")
        print(f"   - Visualização de funil de vendas")
        print(f"   - Análise de segmentos")
        print(f"   - Ranking de leads")
        print(f"   - Análise de ROI")
        print(f"   - Monitoramento de churn")
        print(f"   - Exportação HTML")
        print(f"\n📱 Interface otimizada para decisores não técnicos")
        print(f"🇧🇷 Todos os tooltips e textos em português")
        
        self.app.run_server(debug=debug, port=port, host=host)

# CSS personalizado
app_css = """
.button-primary {
    background-color: #3498db;
    color: white;
    border: none;
    padding: 12px 24px;
    border-radius: 6px;
    cursor: pointer;
    font-size: 14px;
    font-weight: bold;
}

.button-secondary {
    background-color: #95a5a6;
    color: white;
    border: none;
    padding: 12px 24px;
    border-radius: 6px;
    cursor: pointer;
    font-size: 14px;
    font-weight: bold;
}

.button-success {
    background-color: #27ae60;
    color: white;
    border: none;
    padding: 10px 20px;
    border-radius: 4px;
    cursor: pointer;
}

.button-danger {
    background-color: #e74c3c;
    color: white;
    border: none;
    padding: 10px 20px;
    border-radius: 4px;
    cursor: pointer;
}

.button-warning {
    background-color: #f39c12;
    color: white;
    border: none;
    padding: 10px 20px;
    border-radius: 4px;
    cursor: pointer;
}

.cta-card {
    background: white;
    padding: 20px;
    margin: 10px;
    border-radius: 10px;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    border-left: 4px solid #3498db;
}
"""

def main():
    """
    Função principal para executar o dashboard
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Dashboard Interativo CRM CRM')
    parser.add_argument('--data', type=str, help='Caminho para arquivo de dados CSV')
    parser.add_argument('--port', type=int, default=8050, help='Porta do servidor')
    parser.add_argument('--host', type=str, default='127.0.0.1', help='Host do servidor')
    parser.add_argument('--debug', action='store_true', help='Modo debug')
    
    args = parser.parse_args()
    
    # Criar e executar dashboard
    dashboard = DashboardCRM(data_path=args.data)
    dashboard.run(debug=args.debug, port=args.port, host=args.host)

# Configuração para produção (gunicorn)
# Esta variável é necessária para o Google App Engine
server = None

def create_app(data_path=None):
    """
    Factory function para criar a aplicação Dash para produção
    """
    global server
    if server is None:
        dashboard = DashboardCRM(data_path=data_path)
        server = dashboard.app.server
    return server

# Criar instância global para produção
server = create_app()

if __name__ == '__main__':
    main()

