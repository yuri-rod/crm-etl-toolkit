#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EXEMPLO DE USO DOS DADOS FINAIS
==============================

Exemplos práticos de como usar os dados processados
pelo script processador_dados_unificado.py

"""

import pandas as pd
import numpy as np
from pathlib import Path
import json
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime

class AnalisadorDadosFinais:
    """
    Classe para demonstrar análises com os dados finais processados.
    """
    
    def __init__(self, caminho_csv=None):
        if caminho_csv is None:
            # Procurar o arquivo mais recente
            diretorio = Path(r"data")
            arquivos_dataset = list(diretorio.glob("dataset_consolidado_final_*.csv"))
            if not arquivos_dataset:
                raise FileNotFoundError("Nenhum dataset final encontrado. Execute primeiro o processador_dados_unificado.py")
            self.caminho_csv = max(arquivos_dataset, key=lambda f: f.stat().st_mtime)
        else:
            self.caminho_csv = Path(caminho_csv)
        
        print(f"📊 Carregando dados de: {self.caminho_csv.name}")
        self.df = pd.read_csv(self.caminho_csv, encoding='utf-8')
        print(f"✓ Carregados {len(self.df):,} registros com {len(self.df.columns)} colunas")
        
        # Carregar metadados se disponível
        caminho_metadados = self.caminho_csv.with_suffix('.metadados.json')
        if caminho_metadados.exists():
            with open(caminho_metadados, 'r', encoding='utf-8') as f:
                self.metadados = json.load(f)
            print(f"✓ Metadados carregados")
        else:
            self.metadados = None
    
    def visao_geral_dados(self):
        """Fornece visão geral dos dados."""
        print("\n" + "=" * 60)
        print("📋 VISÃO GERAL DOS DADOS")
        print("=" * 60)
        
        print(f"\n📊 Informações básicas:")
        print(f"  • Total de registros: {len(self.df):,}")
        print(f"  • Total de colunas: {len(self.df.columns)}")
        print(f"  • Período dos dados: {self.obter_periodo_dados()}")
        print(f"  • Arquivos de origem: {self.df['arquivo_origem'].nunique() if 'arquivo_origem' in self.df.columns else 'N/A'}")
        
        print(f"\n🎯 Principais campos:")
        campos_principais = ['nome_completo', 'email', 'empresa_nome', 'segmento_atuacao', 'cpf']
        for campo in campos_principais:
            if campo in self.df.columns:
                completude = (self.df[campo].notna().sum() / len(self.df)) * 100
                valores_unicos = self.df[campo].nunique()
                print(f"  • {campo}: {completude:.1f}% completo, {valores_unicos:,} valores únicos")
        
        print(f"\n📈 Distribuição por arquivo de origem:")
        if 'arquivo_origem' in self.df.columns:
            dist_origem = self.df['arquivo_origem'].value_counts()
            for origem, count in dist_origem.head().items():
                print(f"  • {origem}: {count:,} registros ({count/len(self.df)*100:.1f}%)")
    
    def obter_periodo_dados(self):
        """Obtém o período coberto pelos dados."""
        if 'submit_date' in self.df.columns:
            try:
                datas = pd.to_datetime(self.df['submit_date'], errors='coerce')
                data_min = datas.min().strftime('%Y-%m-%d') if not pd.isna(datas.min()) else 'N/A'
                data_max = datas.max().strftime('%Y-%m-%d') if not pd.isna(datas.max()) else 'N/A'
                return f"{data_min} a {data_max}"
            except:
                return "Data não disponível"
        return "Campo de data não encontrado"
    
    def analisar_segmentos_empresa(self):
        """Analisa os segmentos de atuação das empresas."""
        print("\n" + "=" * 60)
        print("🏢 ANÁLISE DE SEGMENTOS EMPRESARIAIS")
        print("=" * 60)
        
        if 'segmento_atuacao' not in self.df.columns:
            print("❌ Campo 'segmento_atuacao' não encontrado")
            return
        
        # Top 10 segmentos
        segmentos = self.df['segmento_atuacao'].dropna().value_counts().head(10)
        
        print(f"\n📊 Top 10 segmentos de atuação:")
        for i, (segmento, count) in enumerate(segmentos.items(), 1):
            percentual = (count / len(self.df)) * 100
            print(f"  {i:2d}. {segmento}: {count:,} empresas ({percentual:.1f}%)")
        
        # Segmentos únicos
        total_segmentos = self.df['segmento_atuacao'].nunique()
        print(f"\n📈 Total de segmentos únicos: {total_segmentos}")
        
        return segmentos
    
    def analisar_dados_demograficos(self):
        """Analisa dados demográficos dos participantes."""
        print("\n" + "=" * 60)
        print("👥 ANÁLISE DEMOGRÁFICA")
        print("=" * 60)
        
        # Análise de estado civil
        if 'estado_civil' in self.df.columns:
            estados_civis = self.df['estado_civil'].dropna().value_counts()
            print(f"\n💑 Distribuição por estado civil:")
            for estado, count in estados_civis.items():
                percentual = (count / len(self.df)) * 100
                print(f"  • {estado}: {count:,} pessoas ({percentual:.1f}%)")
        
        # Análise de faixa etária (se data de nascimento disponível)
        if 'data_nascimento' in self.df.columns:
            self.analisar_faixa_etaria()
        
        # Análise geográfica
        if 'cidade_estado' in self.df.columns:
            self.analisar_distribuicao_geografica()
    
    def analisar_faixa_etaria(self):
        """Analisa a distribuição de faixa etária."""
        try:
            # Converter datas de nascimento
            datas_nasc = pd.to_datetime(self.df['data_nascimento'], errors='coerce')
            idades = ((datetime.now() - datas_nasc).dt.days / 365.25).round().astype('Int64')
            
            # Criar faixas etárias
            bins = [0, 25, 35, 45, 55, 65, 100]
            labels = ['Até 25', '26-35', '36-45', '46-55', '56-65', '65+']
            faixas_etarias = pd.cut(idades, bins=bins, labels=labels, right=False)
            
            print(f"\n🎂 Distribuição por faixa etária:")
            dist_faixas = faixas_etarias.value_counts().sort_index()
            for faixa, count in dist_faixas.items():
                percentual = (count / len(self.df)) * 100
                print(f"  • {faixa} anos: {count:,} pessoas ({percentual:.1f}%)")
            
            # Estatísticas básicas
            idade_media = idades.mean()
            idade_mediana = idades.median()
            if not pd.isna(idade_media):
                print(f"\n📊 Estatísticas de idade:")
                print(f"  • Idade média: {idade_media:.1f} anos")
                print(f"  • Idade mediana: {idade_mediana:.1f} anos")
                print(f"  • Idade mínima: {idades.min()} anos")
                print(f"  • Idade máxima: {idades.max()} anos")
        
        except Exception as e:
            print(f"  ⚠️ Erro na análise de idade: {str(e)}")
    
    def analisar_distribuicao_geografica(self):
        """Analisa a distribuição geográfica."""
        try:
            # Extrair estados
            cidades_estados = self.df['cidade_estado'].dropna()
            estados = cidades_estados.str.extract(r'([A-Z]{2})$')[0]  # Últimas 2 letras maiúsculas
            
            if not estados.empty:
                print(f"\n🗺️ Distribuição por estado (top 10):")
                dist_estados = estados.value_counts().head(10)
                for estado, count in dist_estados.items():
                    percentual = (count / len(self.df)) * 100
                    print(f"  • {estado}: {count:,} participantes ({percentual:.1f}%)")
        
        except Exception as e:
            print(f"  ⚠️ Erro na análise geográfica: {str(e)}")
    
    def analisar_qualidade_dados(self):
        """Analisa a qualidade dos dados."""
        print("\n" + "=" * 60)
        print("🔍 ANÁLISE DE QUALIDADE DOS DADOS")
        print("=" * 60)
        
        # Campos obrigatórios
        campos_criticos = ['nome_completo', 'email', 'cpf']
        
        print(f"\n🎯 Completude de campos críticos:")
        for campo in campos_criticos:
            if campo in self.df.columns:
                completude = (self.df[campo].notna().sum() / len(self.df)) * 100
                status = "✅" if completude >= 95 else "⚠️" if completude >= 80 else "❌"
                print(f"  {status} {campo}: {completude:.1f}% completo")
        
        # Duplicatas potenciais
        if 'cpf' in self.df.columns:
            cpfs_duplicados = self.df['cpf'].duplicated().sum()
            print(f"\n🔍 CPFs duplicados: {cpfs_duplicados}")
        
        if 'email' in self.df.columns:
            emails_duplicados = self.df['email'].duplicated().sum()
            print(f"🔍 Emails duplicados: {emails_duplicados}")
        
        # Resumo geral de completude
        print(f"\n📊 Resumo de completude por coluna:")
        completude_geral = (self.df.notna().sum() / len(self.df) * 100).sort_values(ascending=False)
        for coluna, completude in completude_geral.head(10).items():
            status = "✅" if completude >= 90 else "⚠️" if completude >= 70 else "❌"
            print(f"  {status} {coluna}: {completude:.1f}%")
    
    def gerar_relatorio_completo(self, salvar_arquivo=True):
        """Gera relatório completo de análise."""
        print("\n" + "=" * 80)
        print("📋 RELATÓRIO COMPLETO DE ANÁLISE DOS DADOS")
        print("=" * 80)
        
        # Executar todas as análises
        self.visao_geral_dados()
        self.analisar_segmentos_empresa()
        self.analisar_dados_demograficos()
        self.analisar_qualidade_dados()
        
        if salvar_arquivo:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            caminho_relatorio = self.caminho_csv.parent / f"relatorio_analise_{timestamp}.txt"
            
            # Aqui você poderia salvar o relatório em arquivo
            print(f"\n💾 Relatório completo disponível para exportação")
            print(f"📁 Local sugerido: {caminho_relatorio.name}")
    
    def exemplo_consultas_uteis(self):
        """Mostra exemplos de consultas úteis nos dados."""
        print("\n" + "=" * 60)
        print("🔧 EXEMPLOS DE CONSULTAS ÚTEIS")
        print("=" * 60)
        
        print(f"\n💡 1. Participantes de segmento específico:")
        if 'segmento_atuacao' in self.df.columns:
            exemplo = self.df[self.df['segmento_atuacao'].str.contains('Tecnologia', case=False, na=False)]
            print(f"   df[df['segmento_atuacao'].str.contains('Tecnologia', case=False, na=False)]")
            print(f"   Resultado: {len(exemplo)} registros encontrados")
        
        print(f"\n💡 2. Participantes por estado:")
        if 'cidade_estado' in self.df.columns:
            print(f"   df[df['cidade_estado'].str.contains('SP', na=False)]")
            exemplo_sp = self.df[self.df['cidade_estado'].str.contains('SP', na=False)]
            print(f"   Resultado: {len(exemplo_sp)} participantes de SP")
        
        print(f"\n💡 3. Dados de qualidade (sem emails vazios):")
        if 'email' in self.df.columns:
            exemplo_emails = self.df[self.df['email'].notna() & (self.df['email'] != '')]
            print(f"   df[df['email'].notna() & (df['email'] != '')]")
            print(f"   Resultado: {len(exemplo_emails)} registros com email válido")
        
        print(f"\n💡 4. Empresas com CNPJ informado:")
        if 'cnpj' in self.df.columns:
            exemplo_cnpj = self.df[self.df['cnpj'].notna() & (self.df['cnpj'] != '')]
            print(f"   df[df['cnpj'].notna() & (df['cnpj'] != '')]")
            print(f"   Resultado: {len(exemplo_cnpj)} empresas com CNPJ")

def main():
    """Função principal para demonstrar o uso dos dados."""
    try:
        # Carregar e analisar dados
        analisador = AnalisadorDadosFinais()
        
        # Gerar relatório completo
        analisador.gerar_relatorio_completo()
        
        # Mostrar exemplos de consultas
        analisador.exemplo_consultas_uteis()
        
        print(f"\n✨ Análise concluída! Use este script como base para suas próprias análises.")
        
        return analisador.df
        
    except FileNotFoundError as e:
        print(f"❌ Erro: {str(e)}")
        print(f"\n💡 Dica: Execute primeiro o script 'processador_dados_unificado.py'")
        return None
    except Exception as e:
        print(f"❌ Erro inesperado: {str(e)}")
        return None

if __name__ == "__main__":
    print("\n🔍 Iniciando análise dos dados finais...")
    dados = main()
    
    if dados is not None:
        print(f"\n🎉 Análise finalizada! DataFrame carregado com {len(dados):,} registros.")
        print(f"\n📚 Para usar os dados em seus próprios scripts:")
        print(f"   import pandas as pd")
        print(f"   df = pd.read_csv('seu_arquivo_dataset_consolidado_final.csv', encoding='utf-8')")

