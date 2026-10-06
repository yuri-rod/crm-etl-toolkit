#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
Sistema de Processamento de Dados CRM
Versão: 2.0
Data: 04/09/2025
Descrição: Pipeline completo de processamento de dados para migração ao Supabase
'''

import json
import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path
import re
from typing import Dict, List, Any, Optional
import warnings
warnings.filterwarnings('ignore')

class ProcessadorDadosCRM:
    '''Processador principal para transformação de dados CRM'''
    
    def __init__(self):
        self.diretorio_dados = Path('.')
        self.mapeamento_campos = self._criar_mapeamento_campos()
        self.dados_processados = {}
        self.metricas_qualidade = {}
        
    def _criar_mapeamento_campos(self) -> Dict[str, str]:
        '''Mapeamento de campos em inglês para português brasileiro'''
        return {
            # Campos de Empresa
            'id': 'codigo_empresa',
            'ID': 'codigo_empresa',
            'company_id': 'codigo_empresa',
            'company_name': 'nome_empresa',
            'Nome da Startup': 'nome_empresa',
            'website': 'site',
            'Site': 'site',
            'location': 'cidade_estado',
            'Cidade/Estado': 'cidade_estado',
            'operational_stage': 'estagio_operacional',
            'Estágio Operacional': 'estagio_operacional',
            'business_model': 'modelo_negocio',
            'Modelo de Negócio': 'modelo_negocio',
            'market_sector': 'setor_mercado',
            'Mercado': 'setor_mercado',
            'investment_stage': 'estagio_investimento',
            'Estágio de Investimento': 'estagio_investimento',
            
            # Campos de Contato
            'contact_name': 'nome_contato',
            'Nome do Respondente': 'nome_contato',
            'email': 'email',
            'Email': 'email',
            'phone': 'telefone',
            'Telefone': 'telefone',
            'name': 'nome',
            
            # Campos Financeiros
            'valuation_amount': 'valor_avaliacao',
            'Valuation': 'valor_avaliacao',
            'monthly_recurring_revenue': 'receita_recorrente_mensal',
            'MRR': 'receita_recorrente_mensal',
            'last_twelve_months_revenue': 'receita_ultimos_12_meses',
            'LTM': 'receita_ultimos_12_meses',
            'fundraising_interest': 'interesse_captacao',
            'Captação': 'interesse_captacao',
            'valuation_type': 'tipo_avaliacao',
            'Tipo de Valuation': 'tipo_avaliacao',
            'valuation_date': 'data_avaliacao',
            'Data de Valuation': 'data_avaliacao',
            
            # Campos de Pagamento
            'payment_status': 'status_pagamento',
            'paid': 'pago',
            'payment_amount': 'valor_pagamento',
            'amount': 'valor',
            'service_type': 'tipo_servico',
            'type': 'tipo',
            'payment_date': 'data_pagamento',
            'date': 'data',
            
            # Campos de Data/Sistema
            'created_date': 'data_criacao',
            'createdAt': 'criado_em',
            'updatedAt': 'atualizado_em',
            'consent_given': 'consentimento',
            'consent': 'consentimento',
            'questions_asked': 'perguntas_feitas',
            'questions': 'perguntas',
            
            # Campos de Métricas
            'total_valuations': 'total_avaliacoes',
            'totalValuations': 'total_avaliacoes',
            'average_valuation': 'avaliacao_media',
            'averageValuation': 'avaliacao_media',
            'average_revenue': 'receita_media',
            'averageRevenue': 'receita_media',
            'total_paid_valuations': 'total_avaliacoes_pagas',
            'totalPaidValuations': 'total_avaliacoes_pagas',
            'total_paid_value': 'valor_total_pago',
            'totalPaidValue': 'valor_total_pago',
            
            # Campos Financeiros Detalhados
            'financials.growthRates': 'taxas_crescimento',
            'financials.currentPlannedInvestments': 'investimentos_planejados',
            'financials.currentDebt': 'divida_atual',
            'financials.timeframes.suppliers': 'prazo_fornecedores',
            'financials.timeframes.customers': 'prazo_clientes',
            'financials.currentRevenue': 'receita_atual',
            'financials.currentMRR': 'mrr_atual',
            'financials.currentProfit': 'lucro_atual',
            'financials.currentGrowthRate': 'taxa_crescimento_atual',
            
            # Campos de Análise
            'spreadsheetId': 'id_planilha',
            'timestamp': 'data_hora',
            'project': 'projeto',
            'collections': 'colecoes'
        }
    
    def carregar_dados_nao_processados(self) -> Dict[str, pd.DataFrame]:
        '''Carrega todos os dados que não foram processados anteriormente'''
        dados = {}
        
        # Carregar dados de valuation detalhados
        print('Carregando dados de avaliação detalhada...')
        valuation_files = list(self.diretorio_dados.glob('valuation-*.json'))
        if valuation_files:
            latest = sorted(valuation_files)[-1]
            with open(latest, 'r', encoding='utf-8') as f:
                data = json.load(f)
                dados['avaliacoes_detalhadas'] = self._processar_avaliacoes(data)
                print(f'  ✓ {len(data)} avaliações carregadas')
        
        # Carregar dados do GPT
        print('Carregando dados de análise GPT...')
        gpt_files = list(self.diretorio_dados.glob('opoderdoequitygpt-*.json'))
        if gpt_files:
            latest = sorted(gpt_files)[-1]
            with open(latest, 'r', encoding='utf-8') as f:
                data = json.load(f)
                dados['analises_gpt'] = self._processar_gpt(data)
                print(f'  ✓ {len(data)} análises GPT carregadas')
        
        # Carregar métricas SENSE
        print('Carregando métricas SENSE...')
        sense_files = list(self.diretorio_dados.glob('senseMetrics-*.json'))
        if sense_files:
            latest = sorted(sense_files)[-1]
            with open(latest, 'r', encoding='utf-8') as f:
                data = json.load(f)
                dados['metricas_sense'] = self._processar_metricas(data, 'sense')
                print(f'  ✓ Métricas SENSE carregadas')
        
        # Carregar métricas CRM
        print('Carregando métricas CRM...')
        crm_files = list(self.diretorio_dados.glob('crmMetrics-*.json'))
        if crm_files:
            latest = sorted(crm_files)[-1]
            with open(latest, 'r', encoding='utf-8') as f:
                data = json.load(f)
                dados['metricas_crm'] = self._processar_metricas(data, 'crm')
                print(f'  ✓ Métricas CRM carregadas')
        
        # Carregar links de pagamento
        print('Carregando links de pagamento...')
        payment_links_files = list(self.diretorio_dados.glob('paymentLinks-*.json'))
        if payment_links_files:
            latest = sorted(payment_links_files)[-1]
            with open(latest, 'r', encoding='utf-8') as f:
                data = json.load(f)
                dados['links_pagamento'] = self._processar_links_pagamento(data)
                print(f'  ✓ {len(data)} links de pagamento carregados')
        
        # Carregar exploração de banco
        print('Carregando dados de exploração do banco...')
        db_files = list(self.diretorio_dados.glob('db-exploration-*.json'))
        for db_file in db_files:
            with open(db_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                file_key = f'exploracao_db_{db_file.stem.split("-")[-1]}'
                dados[file_key] = self._processar_exploracao_db(data)
                print(f'  ✓ Exploração DB carregada de {db_file.name}')
        
        return dados
    
    def _processar_avaliacoes(self, data: List[Dict]) -> pd.DataFrame:
        '''Processa dados de avaliações detalhadas'''
        records = []
        for item in data:
            record = {'codigo_avaliacao': item.get('id')}
            
            # Processar campos financeiros
            if 'financials' in item and isinstance(item['financials'], dict):
                fin = item['financials']
                record.update({
                    'taxas_crescimento': str(fin.get('growthRates', '')),
                    'investimentos_planejados': fin.get('currentPlannedInvestments'),
                    'divida_atual': fin.get('currentDebt'),
                    'receita_atual': fin.get('currentRevenue'),
                    'mrr_atual': fin.get('currentMRR'),
                    'lucro_atual': fin.get('currentProfit'),
                    'taxa_crescimento_atual': fin.get('currentGrowthRate')
                })
                
                # Prazos
                if 'timeframes' in fin:
                    record['prazo_fornecedores'] = fin['timeframes'].get('suppliers')
                    record['prazo_clientes'] = fin['timeframes'].get('customers')
            
            # Outros campos
            for key, value in item.items():
                if key != 'financials' and key != 'id':
                    campo_pt = self.mapeamento_campos.get(key, key)
                    record[campo_pt] = value
            
            records.append(record)
        
        return pd.DataFrame(records)
    
    def _processar_gpt(self, data: List[Dict]) -> pd.DataFrame:
        '''Processa dados de análises GPT'''
        records = []
        for item in data:
            record = {
                'codigo_analise': item.get('id'),
                'data_criacao': self._converter_data(item.get('createdAt')),
                'nome_usuario': item.get('name'),
                'id_planilha': item.get('spreadsheetId'),
                'consentimento': item.get('consent'),
                'perguntas': json.dumps(item.get('questions', []), ensure_ascii=False)
            }
            records.append(record)
        
        return pd.DataFrame(records)
    
    def _processar_metricas(self, data: Any, tipo: str) -> pd.DataFrame:
        '''Processa dados de métricas'''
        if isinstance(data, list):
            records = []
            for item in data:
                record = {'tipo_metrica': tipo}
                for key, value in item.items():
                    campo_pt = self.mapeamento_campos.get(key, key)
                    record[campo_pt] = value
                records.append(record)
            return pd.DataFrame(records)
        else:
            # Objeto único
            record = {'tipo_metrica': tipo}
            for key, value in data.items():
                campo_pt = self.mapeamento_campos.get(key, key)
                record[campo_pt] = value
            return pd.DataFrame([record])
    
    def _processar_links_pagamento(self, data: List[Dict]) -> pd.DataFrame:
        '''Processa dados de links de pagamento'''
        records = []
        for item in data:
            record = {
                'codigo_link': item.get('id'),
                'url_pagamento': item.get('url'),
                'status': item.get('status'),
                'valor': item.get('amount'),
                'data_criacao': self._converter_data(item.get('createdAt'))
            }
            records.append(record)
        
        return pd.DataFrame(records)
    
    def _processar_exploracao_db(self, data: Dict) -> pd.DataFrame:
        '''Processa dados de exploração do banco'''
        record = {
            'data_exploracao': self._converter_data(data.get('timestamp')),
            'projeto': data.get('project'),
            'colecoes': json.dumps(data.get('collections', []), ensure_ascii=False)
        }
        
        # Processar estatísticas das coleções
        if 'collections' in data and isinstance(data['collections'], list):
            stats = {
                'total_colecoes': len(data['collections']),
                'nomes_colecoes': ', '.join([c.get('name', '') for c in data['collections'] if 'name' in c])
            }
            record.update(stats)
        
        return pd.DataFrame([record])
    
    def _converter_data(self, data_str: Any) -> Optional[str]:
        '''Converte data para formato brasileiro DD/MM/AAAA HH:MM:SS'''
        if not data_str:
            return None
        
        try:
            if isinstance(data_str, (int, float)):
                # Timestamp Unix
                dt = datetime.fromtimestamp(data_str / 1000 if data_str > 10000000000 else data_str)
            elif isinstance(data_str, str):
                # ISO format
                if 'T' in data_str:
                    dt = datetime.fromisoformat(data_str.replace('Z', '+00:00'))
                else:
                    return data_str  # Já está em formato brasileiro
            else:
                return str(data_str)
            
            return dt.strftime('%d/%m/%Y %H:%M:%S')
        except:
            return str(data_str)
    
    def salvar_dados_processados(self, dados: Dict[str, pd.DataFrame]):
        '''Salva todos os dados processados em formato Excel e JSON'''
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Salvar Excel com todas as abas
        excel_file = f'Dados_CRM_Completo_{timestamp}.xlsx'
        with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
            for nome_aba, df in dados.items():
                if not df.empty:
                    # Limitar nome da aba a 31 caracteres (limite do Excel)
                    nome_aba_curto = nome_aba[:31]
                    df.to_excel(writer, sheet_name=nome_aba_curto, index=False)
                    print(f'  ✓ Aba "{nome_aba_curto}" salva com {len(df)} registros')
        
        print(f'\\n✓ Arquivo Excel salvo: {excel_file}')
        
        # Salvar cada dataset como JSON
        for nome, df in dados.items():
            if not df.empty:
                json_file = f'{nome}_{timestamp}.json'
                df.to_json(json_file, orient='records', force_ascii=False, indent=2, date_format='iso')
                print(f'  ✓ JSON salvo: {json_file}')
        
        return excel_file

# Executar processamento
if __name__ == '__main__':
    print('\\n=== PROCESSAMENTO COMPLETO DE DADOS CRM ===\\n')
    
    processador = ProcessadorDadosCRM()
    
    # Carregar e processar dados
    dados = processador.carregar_dados_nao_processados()
    
    # Salvar dados processados
    if dados:
        arquivo_final = processador.salvar_dados_processados(dados)
        print(f'\\n✓ Processamento concluído com sucesso!')
        print(f'✓ Arquivo principal: {arquivo_final}')
    else:
        print('✗ Nenhum dado novo para processar')
