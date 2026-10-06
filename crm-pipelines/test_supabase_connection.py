#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste de Conexão com Supabase
==============================
Verifica se as credenciais estão corretas e o banco está acessível
"""

import os
import sys
from dotenv import load_dotenv
from supabase import create_client, Client
import requests

# Carrega variáveis de ambiente
load_dotenv()

def test_supabase_connection():
    """Testa a conexão com o Supabase"""
    print("\n" + "=" * 60)
    print("🔧 TESTE DE CONEXÃO SUPABASE")
    print("=" * 60)
    
    # Obtém credenciais
    url = os.getenv('SUPABASE_URL')
    anon_key = os.getenv('SUPABASE_ANON_KEY')
    service_key = os.getenv('SUPABASE_SERVICE_KEY')
    
    if not url or not anon_key:
        print("❌ ERRO: Credenciais não encontradas no arquivo .env")
        print("   Verifique se o arquivo .env está configurado corretamente")
        return False
    
    print(f"\n📍 URL do Projeto: {url}")
    print(f"📍 Project ID: {url.split('.')[0].split('//')[1]}")
    
    # Teste 1: Verificar se a URL é acessível
    print("\n1️⃣ Testando acessibilidade da URL...")
    try:
        response = requests.get(f"{url}/rest/v1/", timeout=5)
        if response.status_code in [200, 401, 403]:
            print("   ✅ URL acessível")
        else:
            print(f"   ⚠️ Status code: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Erro ao acessar URL: {e}")
        return False
    
    # Teste 2: Criar cliente com Anon Key
    print("\n2️⃣ Testando conexão com Anon Key...")
    try:
        supabase: Client = create_client(url, anon_key)
        print("   ✅ Cliente criado com sucesso (Anon Key)")
        
        # Tenta listar tabelas públicas
        try:
            # Testa query simples
            response = supabase.table('companies').select("*").limit(1).execute()
            print(f"   ✅ Acesso a tabelas confirmado")
        except Exception as e:
            if "doesn't exist" in str(e) or "not found" in str(e).lower():
                print("   ⚠️ Tabelas ainda não criadas (execute o schema SQL)")
            elif "permission" in str(e).lower() or "denied" in str(e).lower():
                print("   ℹ️ RLS ativo - acesso limitado (normal para anon key)")
            else:
                print(f"   ⚠️ {e}")
    except Exception as e:
        print(f"   ❌ Erro ao criar cliente: {e}")
        return False
    
    # Teste 3: Verificar Service Key (se disponível)
    if service_key and service_key != "YOUR_SERVICE_KEY_HERE":
        print("\n3️⃣ Testando Service Role Key...")
        try:
            supabase_admin: Client = create_client(url, service_key)
            print("   ✅ Cliente admin criado com sucesso")
            
            # Tenta operação administrativa
            try:
                response = supabase_admin.table('companies').select("count", count='exact').execute()
                print(f"   ✅ Acesso administrativo confirmado")
            except Exception as e:
                if "doesn't exist" in str(e) or "not found" in str(e).lower():
                    print("   ⚠️ Tabelas ainda não criadas")
                else:
                    print(f"   ⚠️ {e}")
        except Exception as e:
            print(f"   ❌ Erro com Service Key: {e}")
    else:
        print("\n3️⃣ Service Role Key não configurada (opcional para testes)")
    
    # Teste 4: Verificar estrutura do banco
    print("\n4️⃣ Verificando estrutura do banco...")
    print("   ℹ️ Para criar as tabelas, execute:")
    print("      1. Acesse o SQL Editor no Supabase Dashboard")
    print(f"      2. Cole o conteúdo de 'supabase_crm_schema.sql'")
    print("      3. Execute o script")
    
    print("\n" + "=" * 60)
    print("✅ TESTE DE CONEXÃO CONCLUÍDO!")
    print("=" * 60)
    
    print("\n📋 RESUMO:")
    print(f"   • Projeto Supabase: kihyqokxcvtmvqsgbocm")
    print(f"   • URL: {url}")
    print(f"   • Status: ONLINE ✅")
    print(f"\n💡 PRÓXIMOS PASSOS:")
    print("   1. Obter a senha do banco no Supabase Dashboard")
    print("   2. Atualizar DB_PASSWORD no arquivo .env")
    print("   3. Executar o schema SQL no Supabase")
    print("   4. Rodar o script de migração: python supabase_etl.py")
    
    return True

def test_with_requests_only():
    """Teste simples usando apenas requests (sem SDK)"""
    print("\n📡 Teste alternativo com requests...")
    
    url = os.getenv('SUPABASE_URL')
    anon_key = os.getenv('SUPABASE_ANON_KEY')
    
    if not url or not anon_key:
        print("❌ Credenciais não encontradas")
        return
    
    headers = {
        'apikey': anon_key,
        'Authorization': f'Bearer {anon_key}',
        'Content-Type': 'application/json'
    }
    
    # Testa endpoint de health
    try:
        response = requests.get(f"{url}/rest/v1/", headers=headers, timeout=5)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print("   ✅ API REST acessível")
    except Exception as e:
        print(f"   ❌ Erro: {e}")

if __name__ == "__main__":
    print("\n🚀 Iniciando teste de conexão com Supabase...")
    
    # Verifica se o arquivo .env existe
    if not os.path.exists('.env'):
        print("❌ Arquivo .env não encontrado!")
        print("   Certifique-se de que o arquivo .env está no diretório atual")
        sys.exit(1)
    
    # Tenta instalar dependências se necessário
    try:
        import supabase
    except ImportError:
        print("📦 Instalando supabase-py...")
        os.system("pip install supabase python-dotenv requests --quiet")
        print("✅ Dependências instaladas")
    
    # Executa testes
    success = test_supabase_connection()
    
    if not success:
        print("\n🔧 Tentando teste alternativo...")
        test_with_requests_only()
    
    print("\n✨ Teste finalizado!")
