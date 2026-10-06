#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROCESSADOR DE DADOS UNIFICADO
=============================

Script único para processar todos os arquivos CSV Base JE*.csv,
padronizar, limpar e exportar dados consolidados.

Este é o ÚNICO script necessário para todo o processo.

Autor: Sistema de Processamento de Dados
Data: 2025-06-05
Versão: 1.0.0
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import logging
import json
import warnings
warnings.filterwarnings('ignore')

class ProcessadorDadosUnificado:
    """
    Processador único para consolidação completa de dados.
    Realiza todo o pipeline: carregamento → padronização → limpeza → exportação.
    """
    
    def __init__(self, nivel_log=logging.INFO):
        self.configurar_logging(nivel_log)
        self.mapeamento_colunas = self._criar_mapeamento_colunas()
        self.metadados_processamento = {}
        
    def configurar_logging(self, nivel):
        """Configura sistema de logs em português."""
        logging.basicConfig(
            level=nivel,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('processamento_dados.log', encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def _criar_mapeamento_colunas(self):
        """Cria mapeamento padrão de colunas em português."""
        return {
            # Dados pessoais
            'nome completo': 'nome_completo',
            'nome_completo': 'nome_completo',
            'name': 'nome_completo',
            'cpf': 'cpf',
            'rg': 'rg',
            'estado civil': 'estado_civil',
            'estado_civil': 'estado_civil',
            'nome do crachá': 'nome_cracha',
            'nome_cracha': 'nome_cracha',
            'data de nascimento': 'data_nascimento',
            'data_nascimento': 'data_nascimento',
            'email': 'email',
            'endereço': 'endereco',
            'endereco': 'endereco',
            'cidade/estado': 'cidade_estado',
            'cidade_estado': 'cidade_estado',
            'whatsapp': 'whatsapp',
            
            # Dados empresariais
            'empresa/nome': 'empresa_nome',
            'empresa_nome': 'empresa_nome',
            'segmento de atuação': 'segmento_atuacao',
            'segmento_atuacao': 'segmento_atuacao',
            'linkedin': 'linkedin',
            'cnpj': 'cnpj',
            'emissão de nota fiscal': 'emissao_nota_fiscal',
            'emissao_nota_fiscal': 'emissao_nota_fiscal',
            'cargo atual': 'cargo_atual',
            'cargo_atual': 'cargo_atual',
            'dores da empresa': 'dores_empresa',
            'dores_empresa': 'dores_empresa',
            'faixa de funcionários': 'faixa_funcionarios',
            'faixa_funcionarios': 'faixa_funcionarios',
            'faixa de faturamento': 'faixa_faturamento',
            'faixa_faturamento': 'faixa_faturamento',
            
            # Dados do formulário
            'objetivo de aprendizado': 'objetivo_aprendizado',
            'objetivo_aprendizado': 'objetivo_aprendizado',
            'autorização de imagem': 'autorizacao_imagem',
            'autorizacao_imagem': 'autorizacao_imagem',
            'response type': 'response_type',
            'response_type': 'response_type',
            'start date': 'start_date',
            'start_date': 'start_date',
            'stage date': 'stage_date',
            'stage_date': 'stage_date',
            'submit date': 'submit_date',
            'submit_date': 'submit_date',
            'network id': 'network_id',
            'network_id': 'network_id',
            'tags': 'tags',
            'id sequencial': 'id_sequencial',
            'id_sequencial': 'id_sequencial'
        }
    
    def carregar_arquivos_base_je(self, diretorio=None):
        """Carrega todos os arquivos Base JE*.csv do diretório."""
        if diretorio is None:
            diretorio = Path(r"data")
        else:
            diretorio = Path(diretorio)
        
        # Encontrar arquivos Base JE
        arquivos_je = list(diretorio.glob("Base JE*.csv"))
        
        if not arquivos_je:
            raise FileNotFoundError("Nenhum arquivo Base JE*.csv encontrado no diretório.")
        
        self.logger.info(f"Encontrados {len(arquivos_je)} arquivos Base JE")
        print(f"📁 Carregando {len(arquivos_je)} arquivos Base JE...")
        
        dataframes = {}
        for arquivo in sorted(arquivos_je):
            try:
                # Tentar diferentes codificações
                for encoding in ['utf-8', 'latin-1', 'cp1252']:
                    try:
                        df = pd.read_csv(arquivo, encoding=encoding)
                        break
                    except UnicodeDecodeError:
                        continue
                else:
                    raise ValueError(f"Não foi possível decodificar {arquivo.name}")
                
                # Normalizar nomes das colunas
                df.columns = df.columns.str.lower().str.strip()
                
                # Nome da chave baseado no arquivo
                chave = arquivo.stem.replace(' ', '_')
                dataframes[chave] = df
                
                print(f"  ✓ {arquivo.name}: {len(df)} registros, {len(df.columns)} colunas")
                
            except Exception as e:
                self.logger.warning(f"Erro ao carregar {arquivo.name}: {str(e)}")
                print(f"  ⚠️ Erro em {arquivo.name}: {str(e)}")
        
        print(f"✅ Total: {sum(len(df) for df in dataframes.values())} registros carregados")
        return dataframes
    
    def padronizar_colunas(self, dataframes, verbose=True):
        """Padroniza nomes de colunas usando mapeamento."""
        if verbose:
            print("\n🔧 Padronizando nomes das colunas...")
        
        dataframes_padronizados = {}
        relatorio_mapeamento = {}
        
        for chave, df in dataframes.items():
            df_novo = df.copy()
            colunas_originais = list(df_novo.columns)
            
            # Aplicar mapeamento
            mapeamento_aplicado = {}
            for col in colunas_originais:
                col_limpa = col.lower().strip()
                if col_limpa in self.mapeamento_colunas:
                    nova_col = self.mapeamento_colunas[col_limpa]
                    mapeamento_aplicado[col] = nova_col
                else:
                    # Manter nome original limpo
                    nova_col = col_limpa.replace(' ', '_').replace('/', '_')
                    mapeamento_aplicado[col] = nova_col
            
            # Renomear colunas
            df_novo = df_novo.rename(columns=mapeamento_aplicado)
            
            # Adicionar metadados
            df_novo['arquivo_origem'] = chave
            df_novo['timestamp_processamento'] = datetime.now()
            
            dataframes_padronizados[chave] = df_novo
            
            # Relatório
            colunas_mapeadas = sum(1 for col in colunas_originais 
                                 if col.lower().strip() in self.mapeamento_colunas)
            colunas_nao_mapeadas = len(colunas_originais) - colunas_mapeadas
            
            relatorio_mapeamento[chave] = {
                'colunas_originais': len(colunas_originais),
                'colunas_mapeadas': colunas_mapeadas,
                'colunas_nao_mapeadas': colunas_nao_mapeadas,
                'mapeamento_detalhado': mapeamento_aplicado
            }
            
            if verbose:
                print(f"  ✓ {chave}: {colunas_mapeadas} mapeadas, {colunas_nao_mapeadas} preservadas")
        
        return dataframes_padronizados, relatorio_mapeamento
    
    def limpar_e_formatar_dados(self, df):
        """Aplica limpeza e formatação final aos dados."""
        print("\n🧹 Aplicando limpeza e formatação dos dados...")
        
        df_limpo = df.copy()
        
        # 1. Padronizar datas
        colunas_data = ['data_nascimento', 'start_date', 'stage_date', 'submit_date']
        for col in colunas_data:
            if col in df_limpo.columns:
                df_limpo[col] = pd.to_datetime(df_limpo[col], errors='coerce')
                df_limpo[col] = df_limpo[col].dt.strftime('%Y-%m-%d')
                print(f"  ✓ Datas padronizadas: {col}")
        
        # 2. Limpar campos de texto
        campos_texto = ['nome_completo', 'empresa_nome', 'objetivo_aprendizado', 'dores_empresa']
        for col in campos_texto:
            if col in df_limpo.columns:
                df_limpo[col] = df_limpo[col].astype(str).str.strip()
                df_limpo[col] = df_limpo[col].replace('nan', '')
                print(f"  ✓ Texto limpo: {col}")
        
        # 3. Padronizar telefones
        if 'whatsapp' in df_limpo.columns:
            df_limpo['whatsapp'] = df_limpo['whatsapp'].astype(str).str.replace("'", "")
            df_limpo['whatsapp'] = df_limpo['whatsapp'].replace('nan', '')
            print(f"  ✓ Telefones padronizados")
        
        # 4. Padronizar CPF e CNPJ
        if 'cpf' in df_limpo.columns:
            df_limpo['cpf'] = df_limpo['cpf'].astype(str).str.replace(r'[^0-9]', '', regex=True)
            df_limpo['cpf'] = df_limpo['cpf'].replace('nan', '')
            print(f"  ✓ CPF padronizado")
        
        if 'cnpj' in df_limpo.columns:
            df_limpo['cnpj'] = df_limpo['cnpj'].astype(str).str.replace(r'[^0-9]', '', regex=True)
            df_limpo['cnpj'] = df_limpo['cnpj'].replace('nan', '')
            print(f"  ✓ CNPJ padronizado")
        
        # 5. Padronizar emails
        if 'email' in df_limpo.columns:
            df_limpo['email'] = df_limpo['email'].astype(str).str.lower().str.strip()
            df_limpo['email'] = df_limpo['email'].replace('nan', '')
            print(f"  ✓ Emails padronizados")
        
        # 6. Ordenar por data de submissão
        if 'submit_date' in df_limpo.columns:
            df_limpo = df_limpo.sort_values('submit_date', na_position='last')
            df_limpo = df_limpo.reset_index(drop=True)
            print(f"  ✓ Registros ordenados por data de submissão")
        
        # 7. Remover linhas completamente vazias
        linhas_iniciais = len(df_limpo)
        df_limpo = df_limpo.dropna(how='all')
        linhas_removidas = linhas_iniciais - len(df_limpo)
        if linhas_removidas > 0:
            print(f"  ✓ Removidas {linhas_removidas} linhas vazias")
        
        print(f"\n✅ Dataset final: {len(df_limpo):,} registros, {len(df_limpo.columns)} colunas")
        return df_limpo
    
    def gerar_dicionario_dados(self, df, diretorio_saida=None):
        """Gera dicionário de dados em português."""
        if diretorio_saida is None:
            diretorio_saida = Path(r"data")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        caminho_dict = diretorio_saida / f"dicionario_dados_{timestamp}.csv"
        
        # Descrições em português
        descricoes = {
            'id_sequencial': 'Identificador único sequencial de cada registro',
            'nome_completo': 'Nome completo do participante',
            'cpf': 'Número do CPF (Cadastro de Pessoa Física)',
            'rg': 'Número do RG (Registro Geral)',
            'estado_civil': 'Estado civil',
            'nome_cracha': 'Nome para crachá/identificação',
            'data_nascimento': 'Data de nascimento',
            'email': 'Endereço de email',
            'endereco': 'Endereço residencial',
            'cidade_estado': 'Cidade e estado',
            'whatsapp': 'Número do WhatsApp',
            'empresa_nome': 'Nome da empresa',
            'segmento_atuacao': 'Segmento de atuação da empresa',
            'linkedin': 'Perfil do LinkedIn',
            'cnpj': 'CNPJ da empresa',
            'emissao_nota_fiscal': 'Tipo de emissão de nota fiscal',
            'objetivo_aprendizado': 'Objetivos de aprendizado declarados',
            'autorizacao_imagem': 'Autorização para uso de imagem',
            'response_type': 'Tipo de resposta do formulário',
            'start_date': 'Data de início do preenchimento',
            'stage_date': 'Data de etapa do processo',
            'submit_date': 'Data de submissão do formulário',
            'network_id': 'Identificador de rede',
            'tags': 'Tags associadas',
            'cargo_atual': 'Cargo atual na empresa',
            'dores_empresa': 'Principais dores/desafios da empresa',
            'faixa_funcionarios': 'Faixa de número de funcionários',
            'faixa_faturamento': 'Faixa de faturamento',
            'arquivo_origem': 'Arquivo de origem dos dados',
            'timestamp_processamento': 'Data e hora do processamento'
        }
        
        # Criar dicionário
        dados_dict = []
        for i, col in enumerate(df.columns, 1):
            dados_col = df[col]
            
            dados_dict.append({
                'posicao': i,
                'nome_coluna': col,
                'descricao': descricoes.get(col, 'Campo gerado automaticamente'),
                'tipo_dados': str(dados_col.dtype),
                'total_registros': len(df),
                'valores_nao_nulos': int(dados_col.count()),
                'valores_nulos': int(dados_col.isnull().sum()),
                'taxa_completude': f"{(dados_col.count() / len(df)) * 100:.1f}%",
                'valores_unicos': int(dados_col.nunique()),
                'exemplo_1': str(dados_col.dropna().iloc[0]) if len(dados_col.dropna()) > 0 else '',
                'exemplo_2': str(dados_col.dropna().iloc[1]) if len(dados_col.dropna()) > 1 else '',
                'exemplo_3': str(dados_col.dropna().iloc[2]) if len(dados_col.dropna()) > 2 else ''
            })
        
        # Criar DataFrame e exportar
        dict_df = pd.DataFrame(dados_dict)
        dict_df.to_csv(caminho_dict, index=False, encoding='utf-8')
        
        print(f"✓ Dicionário de dados criado: {caminho_dict.name}")
        return caminho_dict
    
    def exportar_dataset_final(self, df, caminho_saida=None, incluir_metadados=True):
        """Exporta o dataset final com formatação otimizada."""
        if caminho_saida is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            caminho_saida = Path(r"data") / f"dataset_consolidado_final_{timestamp}.csv"
        else:
            caminho_saida = Path(caminho_saida)
        
        print(f"\n💾 Exportando dataset final...")
        
        # Exportar CSV principal
        df.to_csv(
            caminho_saida,
            index=False,
            encoding='utf-8',
            sep=',',
            quoting=1  # Aspas em campos não-numéricos
        )
        
        print(f"✓ Exportados {len(df):,} registros para: {caminho_saida.name}")
        print(f"✓ Tamanho do arquivo: {caminho_saida.stat().st_size / (1024*1024):.2f} MB")
        
        # Gerar metadados se solicitado
        caminho_metadados = None
        metadados = None
        if incluir_metadados:
            metadados = {
                'info_geral': {
                    'total_registros': len(df),
                    'total_colunas': len(df.columns),
                    'data_processamento': datetime.now().isoformat(),
                    'codificacao': 'UTF-8',
                    'separador': ','
                },
                'colunas': {}
            }
            
            for col in df.columns:
                dados_col = df[col]
                metadados['colunas'][col] = {
                    'tipo_dados': str(dados_col.dtype),
                    'valores_nao_nulos': int(dados_col.count()),
                    'valores_nulos': int(dados_col.isnull().sum()),
                    'taxa_completude': round((dados_col.count() / len(df)) * 100, 2),
                    'valores_unicos': int(dados_col.nunique()),
                    'exemplos': dados_col.dropna().head(3).tolist()
                }
            
            caminho_metadados = caminho_saida.with_suffix('.metadados.json')
            with open(caminho_metadados, 'w', encoding='utf-8') as f:
                json.dump(metadados, f, indent=2, ensure_ascii=False, default=str)
            
            print(f"✓ Metadados salvos: {caminho_metadados.name}")
        
        return {
            'caminho_csv': caminho_saida,
            'caminho_metadados': caminho_metadados,
            'total_registros': len(df),
            'total_colunas': len(df.columns),
            'tamanho_mb': round(caminho_saida.stat().st_size / (1024*1024), 2),
            'metadados': metadados
        }
    
    def executar_pipeline_completo(self, diretorio_entrada=None, caminho_saida=None):
        """Executa o pipeline completo de processamento."""
        print("" + "=" * 80)
        print("PROCESSADOR DE DADOS UNIFICADO")
        print("Pipeline completo: Carregamento → Padronização → Limpeza → Exportação")
        print("=" * 80)
        
        timestamp_inicio = datetime.now()
        
        try:
            # Passo 1: Carregar arquivos
            print("\n📂 PASSO 1: Carregando arquivos Base JE")
            print("-" * 50)
            dataframes = self.carregar_arquivos_base_je(diretorio_entrada)
            
            # Passo 2: Padronizar colunas
            print("\n🔧 PASSO 2: Padronizando colunas")
            print("-" * 40)
            dataframes_padronizados, relatorio_mapeamento = self.padronizar_colunas(dataframes)
            
            # Passo 3: Concatenar dados
            print("\n🔗 PASSO 3: Concatenando datasets")
            print("-" * 40)
            df_unificado = pd.concat(dataframes_padronizados.values(), ignore_index=True)
            print(f"✓ Concatenados {len(df_unificado):,} registros de {len(dataframes_padronizados)} arquivos")
            
            # Passo 4: Limpar e formatar
            print("\n🧹 PASSO 4: Limpeza e formatação")
            print("-" * 40)
            df_limpo = self.limpar_e_formatar_dados(df_unificado)
            
            # Passo 5: Exportar resultado final
            print("\n💾 PASSO 5: Exportação final")
            print("-" * 35)
            resultado_exportacao = self.exportar_dataset_final(df_limpo, caminho_saida)
            
            # Passo 6: Gerar dicionário de dados
            print("\n📋 PASSO 6: Gerando dicionário de dados")
            print("-" * 45)
            caminho_dicionario = self.gerar_dicionario_dados(df_limpo)
            resultado_exportacao['caminho_dicionario'] = caminho_dicionario
            
            # Resumo final
            tempo_processamento = datetime.now() - timestamp_inicio
            
            print("\n" + "=" * 80)
            print("✅ PROCESSAMENTO CONCLUÍDO COM SUCESSO!")
            print("=" * 80)
            
            print(f"\n📊 RESUMO DO PROCESSAMENTO:")
            print(f"  • Arquivos processados: {len(dataframes)}")
            print(f"  • Registros finais: {resultado_exportacao['total_registros']:,}")
            print(f"  • Colunas finais: {resultado_exportacao['total_colunas']}")
            print(f"  • Tempo de processamento: {tempo_processamento}")
            print(f"  • Tamanho do arquivo: {resultado_exportacao['tamanho_mb']} MB")
            
            print(f"\n📁 ARQUIVOS GERADOS:")
            print(f"  • Dataset: {resultado_exportacao['caminho_csv'].name}")
            print(f"  • Metadados: {resultado_exportacao['caminho_metadados'].name}")
            print(f"  • Dicionário: {resultado_exportacao['caminho_dicionario'].name}")
            
            print(f"\n🎯 CARACTERÍSTICAS DO ARQUIVO:")
            print(f"  • Codificação: UTF-8")
            print(f"  • Separador: Vírgula (,)")
            print(f"  • Formato de data: AAAA-MM-DD")
            print(f"  • Cabeçalhos: Padronizados em português")
            print(f"  • Campos de texto: Com aspas")
            
            print(f"\n✨ Os dados estão prontos para análise e uso!")
            
            return resultado_exportacao
            
        except Exception as e:
            self.logger.error(f"Falha no processamento: {str(e)}")
            print(f"\n❌ Falha no processamento: {str(e)}")
            raise

def main():
    """Função principal para executar o processamento."""
    processador = ProcessadorDadosUnificado()
    resultado = processador.executar_pipeline_completo()
    return resultado

if __name__ == "__main__":
    print("\n🚀 Iniciando Processador de Dados Unificado...")
    resultado_final = main()
    print(f"\n🎉 Processamento finalizado! Arquivo: {resultado_final['caminho_csv'].name}")

