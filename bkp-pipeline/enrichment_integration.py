#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de Integração - Enriquecimento de Leads com CRM Cleaner

Integra o módulo de enriquecimento com o sistema principal do CRM.
"""

import json
import pandas as pd
from pathlib import Path
from datetime import datetime
from lead_enrichment import LeadEnrichment
from crm_crm_cleaner import CRMCleaner
import logging

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnrichedCRMProcessor:
    """Processador integrado que combina limpeza e enriquecimento"""
    
    def __init__(self, enable_api_enrichment: bool = False, 
                 enable_lgpd: bool = True, anonymize_sensitive: bool = False):
        """
        Inicializa o processador integrado
        
        Args:
            enable_api_enrichment: Habilita enriquecimento via APIs externas
            enable_lgpd: Habilita compliance LGPD
            anonymize_sensitive: Habilita anonimização de dados sensíveis
        """
        # Inicializa o limpador CRM
        self.crm_cleaner = CRMCleaner(
            enable_lgpd=enable_lgpd,
            anonymize_sensitive=anonymize_sensitive
        )
        
        # Inicializa o enriquecedor
        self.enricher = LeadEnrichment(
            enable_api_calls=enable_api_enrichment,
            rate_limit_delay=1.0
        )
        
        self.enable_api_enrichment = enable_api_enrichment
        
        logger.info("EnrichedCRMProcessor inicializado")
        logger.info(f"API Enrichment: {enable_api_enrichment}")
        logger.info(f"LGPD: {enable_lgpd}")
        logger.info(f"Anonymization: {anonymize_sensitive}")
    
    def process_single_lead(self, lead_data: dict) -> dict:
        """Processa um único lead com limpeza e enriquecimento"""
        try:
            # 1. Limpeza básica usando o CRM cleaner
            cleaned_lead = self.crm_cleaner.process_single_record(lead_data)
            
            # 2. Enriquecimento usando o módulo especializado
            enriched_lead = self.enricher.enrich_lead(cleaned_lead)
            
            # 3. Adiciona metadados do processamento
            enriched_lead['processing_metadata'] = {
                'processed_at': datetime.now().isoformat(),
                'processing_stages': ['cleaning', 'enrichment'],
                'api_enrichment_enabled': self.enable_api_enrichment,
                'processor_version': '1.0'
            }
            
            return enriched_lead
            
        except Exception as e:
            logger.error(f"Erro ao processar lead {lead_data.get('id', 'unknown')}: {e}")
            return lead_data
    
    def process_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Processa um DataFrame completo"""
        logger.info(f"Processando {len(df)} leads...")
        
        # Converte cada linha para dict, processa e reconstitui
        processed_records = []
        
        for idx, row in df.iterrows():
            lead_dict = row.to_dict()
            processed_lead = self.process_single_lead(lead_dict)
            processed_records.append(processed_lead)
            
            # Log de progresso
            if (idx + 1) % 100 == 0:
                logger.info(f"Processados {idx + 1}/{len(df)} leads")
        
        # Converte de volta para DataFrame
        enriched_df = pd.DataFrame(processed_records)
        
        logger.info(f"Processamento concluído. {len(enriched_df)} leads processados.")
        return enriched_df
    
    def process_file(self, input_file: str, output_file: str = None) -> str:
        """Processa um arquivo de leads"""
        input_path = Path(input_file)
        
        if not input_path.exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {input_file}")
        
        # Lê o arquivo
        if input_path.suffix.lower() == '.csv':
            df = pd.read_csv(input_file)
        elif input_path.suffix.lower() in ['.xlsx', '.xls']:
            df = pd.read_excel(input_file)
        else:
            raise ValueError("Formato de arquivo não suportado. Use CSV ou Excel.")
        
        logger.info(f"Arquivo carregado: {len(df)} registros")
        
        # Processa
        enriched_df = self.process_dataframe(df)
        
        # Define arquivo de saída se não especificado
        if output_file is None:
            output_file = str(input_path.parent / f"{input_path.stem}_enriched{input_path.suffix}")
        
        # Salva resultado
        if output_file.endswith('.csv'):
            enriched_df.to_csv(output_file, index=False, encoding='utf-8-sig')
        else:
            enriched_df.to_excel(output_file, index=False)
        
        logger.info(f"Arquivo processado salvo em: {output_file}")
        return output_file
    
    def get_enrichment_report(self, df: pd.DataFrame) -> dict:
        """Gera relatório do enriquecimento"""
        total_records = len(df)
        
        # Estatísticas de campos enriquecidos
        enriched_fields = {
            'nomes_normalizados': df['nome_normalizado'].notna().sum() if 'nome_normalizado' in df.columns else 0,
            'cargos_normalizados': df['cargo_normalizado'].notna().sum() if 'cargo_normalizado' in df.columns else 0,
            'empresas_normalizadas': df['empresa_normalizada'].notna().sum() if 'empresa_normalizada' in df.columns else 0,
            'segmentos_classificados': df['segmento_classificado'].notna().sum() if 'segmento_classificado' in df.columns else 0,
            'linkedin_validados': df['linkedin_valido'].sum() if 'linkedin_valido' in df.columns else 0,
            'cnpjs_validados': df['cnpj_valido'].sum() if 'cnpj_valido' in df.columns else 0,
            'enderecos_geocodificados': df['latitude'].notna().sum() if 'latitude' in df.columns else 0,
            'lgpd_consent_processed': df['lgpd_consent_status'].notna().sum() if 'lgpd_consent_status' in df.columns else 0
        }
        
        # Distribuição de segmentos
        segment_distribution = {}
        if 'segmento_classificado' in df.columns:
            segment_distribution = df['segmento_classificado'].value_counts().to_dict()
        
        # Estatísticas de APIs (se habilitadas)
        api_stats = self.enricher.get_cache_stats() if self.enable_api_enrichment else {}
        
        return {
            'total_records': total_records,
            'enriched_fields': enriched_fields,
            'enrichment_percentages': {k: round((v/total_records)*100, 2) for k, v in enriched_fields.items()},
            'segment_distribution': segment_distribution,
            'api_cache_stats': api_stats,
            'generated_at': datetime.now().isoformat()
        }


def main():
    """Exemplo de uso do processador integrado"""
    # Dados de exemplo
    sample_leads = [
        {
            'id': 'lead_001',
            'nome_completo': 'maria da silva santos',
            'cargo': 'gerente de marketing',
            'nome_empresa': 'inovacao digital ltda',
            'email': 'maria@inovacao.com.br',
            'telefone': '(11) 99999-8888',
            'cnpj': '12.345.678/0001-90',
            'linkedin': 'https://linkedin.com/in/maria-silva',
            'endereco': 'Rua das Flores, 123, São Paulo, SP',
            'autorizacao_imagem': 'sim',
            'segmento_empresa': 'tecnologia'
        },
        {
            'id': 'lead_002',
            'nome_completo': 'joão pedro oliveira',
            'cargo': 'diretor comercial',
            'nome_empresa': 'saude total sa',
            'email': 'joao@saudetotal.com.br',
            'telefone': '11987654321',
            'cnpj': '98.765.432/0001-10',
            'linkedin': 'linkedin.com/in/joao-oliveira',
            'endereco': 'Av. Paulista, 1000, São Paulo, SP',
            'autorizacao_imagem': 'não',
            'segmento_empresa': 'saúde'
        },
        {
            'id': 'lead_003',
            'nome_completo': 'ana carolina pereira',
            'cargo': 'ceo',
            'nome_empresa': 'escola nova educacao',
            'email': 'ana@escolanova.edu.br',
            'telefone': '+55 11 8765-4321',
            'cnpj': '',
            'linkedin': '',
            'endereco': 'Rua da Educação, 456, Rio de Janeiro, RJ',
            'autorizacao_imagem': 'aceito',
            'segmento_empresa': 'educação'
        }
    ]
    
    # Cria DataFrame de exemplo
    df_sample = pd.DataFrame(sample_leads)
    
    print("=== TESTE DO PROCESSADOR INTEGRADO ===")
    print(f"Processando {len(sample_leads)} leads de exemplo...\n")
    
    # Teste 1: Processamento sem APIs (mais rápido)
    print("1. Processamento SEM APIs externas:")
    processor_basic = EnrichedCRMProcessor(enable_api_enrichment=False)
    enriched_basic = processor_basic.process_dataframe(df_sample.copy())
    
    # Mostra exemplo de um lead processado
    sample_enriched = enriched_basic.iloc[0].to_dict()
    print("\nExemplo de lead enriquecido (sem APIs):")
    for key, value in sample_enriched.items():
        if not key.startswith('enrichment_') and not key.startswith('processing_'):
            print(f"  {key}: {value}")
    
    # Relatório básico
    report_basic = processor_basic.get_enrichment_report(enriched_basic)
    print("\nRelatório de Enriquecimento (Básico):")
    print(f"  Total de registros: {report_basic['total_records']}")
    print(f"  Nomes normalizados: {report_basic['enriched_fields']['nomes_normalizados']}")
    print(f"  Segmentos classificados: {report_basic['enriched_fields']['segmentos_classificados']}")
    print(f"  CNPJs validados: {report_basic['enriched_fields']['cnpjs_validados']}")
    print(f"  LinkedIn validados: {report_basic['enriched_fields']['linkedin_validados']}")
    
    print("\nDistribuição de Segmentos:")
    for segment, count in report_basic['segment_distribution'].items():
        print(f"  {segment}: {count}")
    
    # Teste 2: Processamento COM APIs (mais lento, mais completo)
    print("\n" + "="*50)
    print("2. Processamento COM APIs externas:")
    print("   (Este teste fará chamadas reais para APIs públicas)")
    
    # Pergunta se deve executar o teste com APIs
    test_with_apis = input("\nExecutar teste com APIs? (s/n): ").lower().startswith('s')
    
    if test_with_apis:
        processor_full = EnrichedCRMProcessor(enable_api_enrichment=True)
        enriched_full = processor_full.process_dataframe(df_sample.copy())
        
        # Relatório completo
        report_full = processor_full.get_enrichment_report(enriched_full)
        print("\nRelatório de Enriquecimento (Completo):")
        print(f"  Endereços geocodificados: {report_full['enriched_fields']['enderecos_geocodificados']}")
        print(f"  Cache CNPJ: {report_full['api_cache_stats'].get('cnpj_cache_size', 0)} itens")
        print(f"  Cache Geocoding: {report_full['api_cache_stats'].get('geocoding_cache_size', 0)} itens")
        
        # Salva exemplo em arquivo
        output_file = "leads_enriquecidos_exemplo.csv"
        enriched_full.to_csv(output_file, index=False, encoding='utf-8-sig')
        print(f"\nArquivo de exemplo salvo: {output_file}")
    
    print("\n=== TESTE CONCLUÍDO ===")
    print("\nFuncionalidades implementadas:")
    print("✓ Normalização de nomes, cargos e empresas")
    print("✓ Classificação automática de segmentos")
    print("✓ Validação e formatação de CNPJ")
    print("✓ Validação de URLs do LinkedIn")
    print("✓ Tags de consentimento LGPD")
    print("✓ Geocodificação de endereços (via API)")
    print("✓ Enriquecimento via APIs da Receita Federal")
    print("✓ Cache para otimização de performance")
    print("✓ Relatórios de qualidade dos dados")


if __name__ == "__main__":
    main()

