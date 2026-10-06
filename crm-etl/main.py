# -*- coding: utf-8 -*-
"""
Ponto de entrada principal para a aplicação CRM Analytics

Este arquivo serve como entry point para o deploy no Google Cloud,
fornecendo uma interface unificada para todas as funcionalidades.

Versão 2.0 - Aplicação Flask com Dash embarcado
"""

import os
import sys
from pathlib import Path

# Adicionar o diretório atual ao path
sys.path.append(str(Path(__file__).parent))

try:
    from config import HOST, PORT, DEBUG
except ImportError:
    # Configurações padrão caso o config.py não esteja disponível
    HOST = '0.0.0.0'
    PORT = int(os.getenv('PORT', 8080))
    DEBUG = os.getenv('FLASK_ENV') != 'production'

def create_app():
    """
    Cria e configura a aplicação principal
    
    Returns:
        Flask app configurada com Dash embarcado
    """
    try:
        # Importar a nova aplicação Flask aprimorada
        from app import create_app as create_enhanced_app
        app = create_enhanced_app()
        return app
    except ImportError as e:
        print(f"Erro ao importar aplicação principal: {e}")
        
        # Fallback para aplicação simples com dashboard
        try:
            from dashboard_interativo import DashboardCRM
            from flask import Flask
            
            app = Flask(__name__)
            app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'fallback-key')
            
            # Criar dashboard básico
            dashboard = DashboardCRM()
            dashboard.app.init_app(app)
            
            @app.route('/')
            def health_check():
                return {
                    'status': 'ok',
                    'message': 'CRM Analytics - Aplicação funcionando (modo básico)',
                    'version': '2.0.0',
                    'dashboard_url': '/dashboard/'
                }
            
            return app
            
        except Exception as fallback_error:
            print(f"Erro no fallback: {fallback_error}")
            
            # Última opção - aplicação mínima
            from flask import Flask, jsonify
            app = Flask(__name__)
            
            @app.route('/')
            def minimal_health_check():
                return jsonify({
                    'status': 'ok',
                    'message': 'CRM Analytics - Modo mínimo',
                    'version': '2.0.0',
                    'note': 'Algumas funcionalidades podem estar limitadas'
                })
            
            @app.route('/health')
            def health():
                return jsonify({'status': 'healthy'})
            
            return app

def main():
    """
    Função principal para executar a aplicação
    """
    print("🚀 Iniciando Sistema CRM CRM v2.0")
    print("📊 Aplicação Flask com Dashboard Dash Embarcado")
    
    app = create_app()
    
    if app:
        print(f"\n✅ Aplicação criada com sucesso")
        print(f"🌐 Host: {HOST}")
        print(f"🔌 Porta: {PORT}")
        print(f"🔧 Debug: {DEBUG}")
        print(f"\n🔗 URLs Disponíveis:")
        print(f"   - Página Principal: http://{HOST}:{PORT}/")
        print(f"   - Dashboard: http://{HOST}:{PORT}/dashboard/")
        print(f"   - Upload: http://{HOST}:{PORT}/upload")
        print(f"   - API Status: http://{HOST}:{PORT}/api/status")
        print(f"\n🔄 Iniciando servidor...\n")
        
        # Executar a aplicação
        try:
            app.run(host=HOST, port=PORT, debug=DEBUG, threaded=True)
        except KeyboardInterrupt:
            print("\n🛑 Aplicação interrompida pelo usuário")
        except Exception as e:
            print(f"❌ Erro ao executar aplicação: {e}")
            sys.exit(1)
    else:
        print("❌ Erro ao criar a aplicação")
        sys.exit(1)

# Flask app instance para deployment (Gunicorn, etc.)
app = create_app()

if __name__ == '__main__':
    main()

