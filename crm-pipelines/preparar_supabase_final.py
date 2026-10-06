#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
Preparação de Dados para Supabase
Versão: 1.0
Data: 04/09/2025
Descrição: Script de preparação e modelagem de dados para migração ao Supabase
'''

import json
import pandas as pd
from datetime import datetime
from pathlib import Path

class PreparadorSupabase:
    '''Prepara dados para importação no Supabase'''
    
    def __init__(self):
        self.timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
    def criar_schema_supabase(self):
        '''Cria script SQL com schema do banco de dados para Supabase'''
        
        schema_sql = '''-- Schema do Banco de Dados CRM
-- Data de Criação: ''' + datetime.now().strftime('%d/%m/%Y') + '''

-- Tabela principal de empresas
CREATE TABLE IF NOT EXISTS empresas (
    id SERIAL PRIMARY KEY,
    codigo_empresa VARCHAR(50) UNIQUE,
    nome_empresa VARCHAR(255) NOT NULL,
    site VARCHAR(255),
    cidade VARCHAR(100),
    estado VARCHAR(50),
    estagio_operacional VARCHAR(100),
    modelo_negocio VARCHAR(100),
    setor_mercado VARCHAR(100),
    estagio_investimento VARCHAR(100),
    data_cadastro TIMESTAMP DEFAULT NOW(),
    data_atualizacao TIMESTAMP DEFAULT NOW()
);

-- Tabela de contatos
CREATE TABLE IF NOT EXISTS contatos (
    id SERIAL PRIMARY KEY,
    empresa_id INTEGER REFERENCES empresas(id) ON DELETE CASCADE,
    nome_contato VARCHAR(255),
    email VARCHAR(255),
    telefone VARCHAR(50),
    cargo VARCHAR(100),
    principal BOOLEAN DEFAULT FALSE,
    data_cadastro TIMESTAMP DEFAULT NOW()
);

-- Tabela de avaliações financeiras
CREATE TABLE IF NOT EXISTS avaliacoes_financeiras (
    id SERIAL PRIMARY KEY,
    empresa_id INTEGER REFERENCES empresas(id) ON DELETE CASCADE,
    codigo_avaliacao VARCHAR(50) UNIQUE,
    valor_avaliacao DECIMAL(15,2),
    receita_recorrente_mensal DECIMAL(15,2),
    receita_ultimos_12_meses DECIMAL(15,2),
    interesse_captacao VARCHAR(100),
    tipo_avaliacao VARCHAR(100),
    data_avaliacao DATE,
    taxas_crescimento TEXT,
    investimentos_planejados DECIMAL(15,2),
    divida_atual DECIMAL(15,2),
    receita_atual DECIMAL(15,2),
    mrr_atual DECIMAL(15,2),
    lucro_atual DECIMAL(15,2),
    taxa_crescimento_atual DECIMAL(5,2),
    prazo_fornecedores INTEGER,
    prazo_clientes INTEGER,
    data_cadastro TIMESTAMP DEFAULT NOW()
);

-- Tabela de pagamentos
CREATE TABLE IF NOT EXISTS pagamentos (
    id SERIAL PRIMARY KEY,
    empresa_id INTEGER REFERENCES empresas(id) ON DELETE CASCADE,
    valor DECIMAL(15,2) NOT NULL,
    status_pagamento VARCHAR(50),
    tipo_servico VARCHAR(100),
    data_pagamento DATE,
    referencia_externa VARCHAR(100),
    data_cadastro TIMESTAMP DEFAULT NOW()
);

-- Tabela de análises
CREATE TABLE IF NOT EXISTS analises (
    id SERIAL PRIMARY KEY,
    empresa_id INTEGER REFERENCES empresas(id) ON DELETE SET NULL,
    codigo_analise VARCHAR(50) UNIQUE,
    tipo_analise VARCHAR(50),
    nome_usuario VARCHAR(255),
    id_planilha VARCHAR(100),
    consentimento BOOLEAN DEFAULT FALSE,
    perguntas JSONB,
    resultados JSONB,
    data_analise TIMESTAMP,
    data_cadastro TIMESTAMP DEFAULT NOW()
);

-- Tabela de métricas agregadas
CREATE TABLE IF NOT EXISTS metricas_agregadas (
    id SERIAL PRIMARY KEY,
    tipo_metrica VARCHAR(50) NOT NULL,
    periodo VARCHAR(20),
    total_avaliacoes INTEGER,
    avaliacao_media DECIMAL(15,2),
    receita_media DECIMAL(15,2),
    total_avaliacoes_pagas INTEGER,
    valor_total_pago DECIMAL(15,2),
    dados_adicionais JSONB,
    data_calculo TIMESTAMP DEFAULT NOW()
);

-- Tabela de links de pagamento
CREATE TABLE IF NOT EXISTS links_pagamento (
    id SERIAL PRIMARY KEY,
    empresa_id INTEGER REFERENCES empresas(id) ON DELETE SET NULL,
    codigo_link VARCHAR(50) UNIQUE,
    url_pagamento VARCHAR(500),
    valor DECIMAL(15,2),
    status VARCHAR(50),
    data_criacao TIMESTAMP,
    data_expiracao TIMESTAMP,
    data_cadastro TIMESTAMP DEFAULT NOW()
);

-- Índices para otimização
CREATE INDEX idx_empresas_nome ON empresas(nome_empresa);
CREATE INDEX idx_empresas_setor ON empresas(setor_mercado);
CREATE INDEX idx_contatos_email ON contatos(email);
CREATE INDEX idx_avaliacoes_data ON avaliacoes_financeiras(data_avaliacao);
CREATE INDEX idx_pagamentos_status ON pagamentos(status_pagamento);
CREATE INDEX idx_pagamentos_data ON pagamentos(data_pagamento);

-- Views para relatórios
CREATE OR REPLACE VIEW vw_resumo_empresas AS
SELECT 
    e.id,
    e.codigo_empresa,
    e.nome_empresa,
    e.setor_mercado,
    e.estagio_operacional,
    COUNT(DISTINCT c.id) as total_contatos,
    COUNT(DISTINCT af.id) as total_avaliacoes,
    MAX(af.valor_avaliacao) as ultima_avaliacao,
    MAX(af.data_avaliacao) as data_ultima_avaliacao,
    SUM(p.valor) as total_pago
FROM empresas e
LEFT JOIN contatos c ON e.id = c.empresa_id
LEFT JOIN avaliacoes_financeiras af ON e.id = af.empresa_id
LEFT JOIN pagamentos p ON e.id = p.empresa_id
GROUP BY e.id, e.codigo_empresa, e.nome_empresa, e.setor_mercado, e.estagio_operacional;

-- Políticas de segurança RLS
ALTER TABLE empresas ENABLE ROW LEVEL SECURITY;
ALTER TABLE contatos ENABLE ROW LEVEL SECURITY;
ALTER TABLE avaliacoes_financeiras ENABLE ROW LEVEL SECURITY;
ALTER TABLE pagamentos ENABLE ROW LEVEL SECURITY;'''
        
        # Salvar schema SQL
        with open(f'schema_supabase_{self.timestamp}.sql', 'w', encoding='utf-8') as f:
            f.write(schema_sql)
        
        print(f'✓ Schema SQL criado: schema_supabase_{self.timestamp}.sql')
        return schema_sql
    
    def criar_script_migracao(self):
        '''Cria guia de migração de dados'''
        
        migration_script = f'''Guia de Migração para Supabase
==============================

Data: {datetime.now().strftime('%d/%m/%Y')}

## 1. PREPARAÇÃO DO AMBIENTE SUPABASE

### 1.1 Criar Projeto no Supabase
- Acesse: https://supabase.com
- Crie novo projeto
- Anote as credenciais

### 1.2 Executar Schema SQL
- Acesse SQL Editor no painel Supabase
- Cole o conteúdo de: schema_supabase_{self.timestamp}.sql
- Execute o script

## 2. IMPORTAÇÃO DE DADOS

### 2.1 Via Interface Web
- Acesse Table Editor no Supabase
- Para cada tabela:
  1. Clique em "Import"
  2. Selecione o arquivo CSV correspondente
  3. Mapeie as colunas
  4. Confirme importação

## 3. ORDEM DE IMPORTAÇÃO

IMPORTANTE: Respeitar esta ordem devido às chaves estrangeiras

1. empresas
2. contatos
3. avaliacoes_financeiras
4. pagamentos
5. analises
6. metricas_agregadas
7. links_pagamento

## 4. VALIDAÇÃO DOS DADOS

### Queries de Validação:

-- Verificar total de registros
SELECT 
    'empresas' as tabela, COUNT(*) as total FROM empresas
UNION ALL
SELECT 'contatos', COUNT(*) FROM contatos
UNION ALL
SELECT 'avaliacoes_financeiras', COUNT(*) FROM avaliacoes_financeiras
UNION ALL
SELECT 'pagamentos', COUNT(*) FROM pagamentos;

## 5. MONITORAMENTO

- Configurar alertas
- Ativar logs detalhados
- Revisar semanalmente

## CONTATOS DE SUPORTE

Documentação: https://supabase.com/docs'''
        
        with open(f'guia_migracao_supabase_{self.timestamp}.md', 'w', encoding='utf-8') as f:
            f.write(migration_script)
        
        print(f'✓ Guia de migração criado: guia_migracao_supabase_{self.timestamp}.md')
        return migration_script
    
    def preparar_csvs_para_importacao(self):
        '''Prepara arquivos CSV otimizados para importação direta'''
        
        print('\nPreparando arquivos CSV para importação...')
        
        # Carregar dados existentes
        excel_principal = 'CRM_Data_Complete_ETL_20250827_080246.xlsx'
        excel_novo = 'Dados_CRM_Completo_20250903_214328.xlsx'
        
        # Preparar CSV de empresas (dados únicos)
        df_companies = pd.read_excel(excel_principal, sheet_name='Companies')
        df_empresas = df_companies[['company_id', 'company_name', 'website', 'city', 'state',
                                   'operational_stage', 'business_model', 'market_sector', 
                                   'investment_stage']].drop_duplicates()
        df_empresas.columns = ['codigo_empresa', 'nome_empresa', 'site', 'cidade', 'estado',
                              'estagio_operacional', 'modelo_negocio', 'setor_mercado', 
                              'estagio_investimento']
        df_empresas.to_csv(f'empresas_supabase_{self.timestamp}.csv', index=False, encoding='utf-8')
        print(f'  ✓ empresas_supabase_{self.timestamp}.csv - {len(df_empresas)} registros')
        
        # Preparar CSV de contatos
        df_contacts = pd.read_excel(excel_principal, sheet_name='Contacts')
        df_contatos = df_contacts[['company_id', 'contact_name', 'email', 'phone']].dropna(subset=['contact_name'])
        df_contatos.columns = ['codigo_empresa', 'nome_contato', 'email', 'telefone']
        df_contatos.to_csv(f'contatos_supabase_{self.timestamp}.csv', index=False, encoding='utf-8')
        print(f'  ✓ contatos_supabase_{self.timestamp}.csv - {len(df_contatos)} registros')
        
        # Preparar CSV de pagamentos
        df_payments = pd.read_excel(excel_principal, sheet_name='Payments')
        df_pagamentos = df_payments[['company_id', 'payment_amount', 'payment_status', 'service_type', 'payment_date']]
        df_pagamentos.columns = ['codigo_empresa', 'valor', 'status_pagamento', 'tipo_servico', 'data_pagamento']
        df_pagamentos.to_csv(f'pagamentos_supabase_{self.timestamp}.csv', index=False, encoding='utf-8')
        print(f'  ✓ pagamentos_supabase_{self.timestamp}.csv - {len(df_pagamentos)} registros')
        
        # Preparar CSV de avaliações detalhadas
        df_avaliacoes = pd.read_excel(excel_novo, sheet_name='avaliacoes_detalhadas')
        df_avaliacoes.to_csv(f'avaliacoes_supabase_{self.timestamp}.csv', index=False, encoding='utf-8')
        print(f'  ✓ avaliacoes_supabase_{self.timestamp}.csv - {len(df_avaliacoes)} registros')
        
        # Preparar CSV de análises GPT
        df_analises = pd.read_excel(excel_novo, sheet_name='analises_gpt')
        df_analises.to_csv(f'analises_gpt_supabase_{self.timestamp}.csv', index=False, encoding='utf-8')
        print(f'  ✓ analises_gpt_supabase_{self.timestamp}.csv - {len(df_analises)} registros')
        
        # Preparar CSV de métricas
        df_metricas_sense = pd.read_excel(excel_novo, sheet_name='metricas_sense')
        df_metricas_sense.to_csv(f'metricas_sense_supabase_{self.timestamp}.csv', index=False, encoding='utf-8')
        print(f'  ✓ metricas_sense_supabase_{self.timestamp}.csv - {len(df_metricas_sense)} registros')
        
        df_metricas_crm = pd.read_excel(excel_novo, sheet_name='metricas_crm')
        df_metricas_crm.to_csv(f'metricas_crm_supabase_{self.timestamp}.csv', index=False, encoding='utf-8')
        print(f'  ✓ metricas_crm_supabase_{self.timestamp}.csv - {len(df_metricas_crm)} registros')
        
        # Preparar CSV de links de pagamento
        df_links = pd.read_excel(excel_novo, sheet_name='links_pagamento')
        df_links.to_csv(f'links_pagamento_supabase_{self.timestamp}.csv', index=False, encoding='utf-8')
        print(f'  ✓ links_pagamento_supabase_{self.timestamp}.csv - {len(df_links)} registros')
        
        print('\n✓ Todos os arquivos CSV preparados para importação')

# Executar preparação
if __name__ == '__main__':
    print('\n=== PREPARAÇÃO PARA SUPABASE ===\n')
    
    preparador = PreparadorSupabase()
    
    # Criar schema SQL
    preparador.criar_schema_supabase()
    
    # Criar guia de migração
    preparador.criar_script_migracao()
    
    # Preparar CSVs
    preparador.preparar_csvs_para_importacao()
    
    print(f'\n✓ Preparação completa! Arquivos gerados:')
    print(f'  1. schema_supabase_{preparador.timestamp}.sql - Schema do banco de dados')
    print(f'  2. guia_migracao_supabase_{preparador.timestamp}.md - Guia passo a passo')
    print(f'  3. *_supabase_{preparador.timestamp}.csv - Arquivos CSV prontos para importação')
    print('\nPróximos passos:')
    print('  1. Criar projeto no Supabase')
    print('  2. Executar o schema SQL')
    print('  3. Importar os arquivos CSV na ordem correta')
    print('\n✓ Sistema pronto para migração ao Supabase!')
