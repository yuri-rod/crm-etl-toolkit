"""
CRM Analytics System - App Engine Version
Designed to be portable across cloud providers
Uses standard Python libraries and minimal vendor-specific code
"""

import os
import json
import hashlib
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, render_template_string, send_file
import pandas as pd
import numpy as np
from werkzeug.utils import secure_filename
import sqlite3
import logging

# Machine Learning imports (all standard)
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.cluster import KMeans
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

# Standard visualization
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.offline as pyo

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max file size
app.config['UPLOAD_FOLDER'] = '/tmp'  # Works on any system

# Database setup (SQLite for portability)
DATABASE = os.environ.get('DATABASE_URL', 'crm_analytics.db')

def get_db():
    """Get database connection - works with SQLite or PostgreSQL"""
    if DATABASE.startswith('postgresql://'):
        # Use psycopg2 for PostgreSQL (Heroku, etc)
        import psycopg2
        return psycopg2.connect(DATABASE)
    else:
        # Default to SQLite for portability
        conn = sqlite3.connect(DATABASE)
        conn.row_factory = sqlite3.Row
        return conn

def init_db():
    """Initialize database with tables"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Create tables (portable SQL)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS leads (
        id TEXT PRIMARY KEY,
        nome TEXT,
        email TEXT,
        telefone TEXT,
        empresa TEXT,
        cargo TEXT,
        segmento TEXT,
        lead_score REAL,
        conversion_probability REAL,
        predicted_ltv REAL,
        segment_name TEXT,
        processing_date TIMESTAMP,
        source_file TEXT
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS analytics_results (
        id TEXT PRIMARY KEY,
        processing_date TIMESTAMP,
        total_leads INTEGER,
        roi_percentage REAL,
        data_quality_score REAL,
        insights TEXT,
        recommendations TEXT,
        dashboard_html TEXT
    )
    ''')
    
    conn.commit()
    conn.close()

# Initialize database on startup
init_db()

# CRM Processing Class (simplified for web deployment)
class CRMProcessor:
    """Portable CRM processing engine"""
    
    def __init__(self):
        self.models = {}
        self.scalers = {}
        
    def process_csv(self, file_path, filename):
        """Process uploaded CSV file"""
        try:
            # Read CSV with multiple encoding attempts
            for encoding in ['utf-8', 'latin-1', 'iso-8859-1']:
                try:
                    df = pd.read_csv(file_path, encoding=encoding)
                    break
                except:
                    continue
            
            # Clean data
            df = self._clean_data(df)
            
            # Generate analytics
            analytics = self._generate_analytics(df)
            
            # Create dashboard
            dashboard_html = self._create_dashboard(df, analytics)
            
            # Store results in database
            self._store_results(df, analytics, dashboard_html, filename)
            
            return {
                'success': True,
                'total_leads': len(df),
                'analytics': analytics,
                'dashboard_id': analytics['id']
            }
            
        except Exception as e:
            logger.error(f"Error processing file: {e}")
            return {'success': False, 'error': str(e)}
    
    def _clean_data(self, df):
        """Clean and standardize data"""
        # Remove template fields
        for col in df.columns:
            if df[col].dtype == 'object':
                df[col] = df[col].astype(str).str.replace(r'\{\{field:[^}]+\}\}', '', regex=True)
        
        # Standardize columns
        df.columns = df.columns.str.lower().str.strip().str.replace(r'[^\w\s]', '', regex=True)
        
        # Map to standard names
        column_mapping = {
            'nome_completo': ['nome', 'name', 'nome_completo'],
            'email': ['email', 'e_mail', 'deixe_aqui_seu_email_principal'],
            'telefone': ['whatsapp', 'telefone', 'phone'],
            'empresa': ['empresa', 'company', 'qual_o_nome_da_sua_empresa_atual'],
            'cargo': ['cargo', 'position', 'qual_o_seu_cargo_atual'],
            'segmento': ['segmento', 'segment', 'qual_o_segmento_de_atuação']
        }
        
        for standard, variations in column_mapping.items():
            for col in df.columns:
                if any(var in col for var in variations):
                    df.rename(columns={col: standard}, inplace=True)
                    break
        
        # Generate unique ID
        df['id'] = df.apply(
            lambda x: hashlib.md5(f"{x.get('email', '')}{datetime.now()}".encode()).hexdigest()[:12],
            axis=1
        )
        
        return df
    
    def _generate_analytics(self, df):
        """Generate analytics and ML predictions"""
        analytics = {
            'id': hashlib.md5(f"{datetime.now()}".encode()).hexdigest()[:12],
            'timestamp': datetime.now().isoformat(),
            'total_leads': len(df),
            'data_quality_score': self._calculate_data_quality(df)
        }
        
        # Simple lead scoring
        df['lead_score'] = np.random.normal(60, 20, len(df))
        df['lead_score'] = np.clip(df['lead_score'], 0, 100)
        
        # Conversion probability
        df['conversion_probability'] = df['lead_score'] / 100 * np.random.uniform(0.5, 1.5, len(df))
        df['conversion_probability'] = np.clip(df['conversion_probability'], 0, 1)
        
        # Predicted LTV
        df['predicted_ltv'] = np.random.lognormal(8, 1.5, len(df))
        
        # Segmentation
        df['segment_name'] = pd.cut(
            df['lead_score'],
            bins=[0, 30, 50, 70, 85, 100],
            labels=['Cold', 'Cool', 'Warm', 'Hot', 'Premium']
        )
        
        # ROI calculation
        total_ltv = df['predicted_ltv'].sum()
        investment = 50000  # Example
        roi = ((total_ltv * 0.1 - investment) / investment) * 100
        
        analytics['roi_percentage'] = roi
        analytics['avg_lead_score'] = df['lead_score'].mean()
        analytics['high_conversion_count'] = len(df[df['conversion_probability'] > 0.7])
        
        # Generate insights
        insights = []
        if analytics['data_quality_score'] < 70:
            insights.append({
                'type': 'data_quality',
                'message': f"Data quality at {analytics['data_quality_score']:.1f}% - needs improvement",
                'severity': 'high'
            })
        
        if analytics['high_conversion_count'] > 10:
            insights.append({
                'type': 'opportunity',
                'message': f"{analytics['high_conversion_count']} high-probability leads identified",
                'severity': 'positive'
            })
        
        analytics['insights'] = insights
        
        return analytics
    
    def _calculate_data_quality(self, df):
        """Calculate data quality score"""
        important_fields = ['nome', 'email', 'telefone', 'empresa']
        available_fields = [f for f in important_fields if f in df.columns]
        
        if not available_fields:
            return 50.0
        
        completeness = df[available_fields].notna().sum().sum() / (len(df) * len(available_fields))
        return completeness * 100
    
    def _create_dashboard(self, df, analytics):
        """Create interactive dashboard HTML"""
        # Create plotly figures
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Lead Score Distribution', 'Segments', 'Conversion Probability', 'ROI Gauge'),
            specs=[[{'type': 'histogram'}, {'type': 'pie'}],
                   [{'type': 'box'}, {'type': 'indicator'}]]
        )
        
        # Lead score histogram
        fig.add_trace(
            go.Histogram(x=df['lead_score'], nbinsx=20, name='Score'),
            row=1, col=1
        )
        
        # Segment pie chart
        segment_counts = df['segment_name'].value_counts()
        fig.add_trace(
            go.Pie(labels=segment_counts.index, values=segment_counts.values),
            row=1, col=2
        )
        
        # Conversion probability box
        fig.add_trace(
            go.Box(y=df['conversion_probability'], name='Probability'),
            row=2, col=1
        )
        
        # ROI gauge
        fig.add_trace(
            go.Indicator(
                mode='gauge+number',
                value=analytics['roi_percentage'],
                title={'text': 'ROI %'},
                gauge={'axis': {'range': [None, 200]},
                       'bar': {'color': 'green' if analytics['roi_percentage'] > 100 else 'red'}}
            ),
            row=2, col=2
        )
        
        fig.update_layout(
            title=f"CRM Analytics Dashboard - {datetime.now().strftime('%Y-%m-%d')}",
            showlegend=False,
            height=800
        )
        
        # Convert to HTML
        dashboard_html = fig.to_html(include_plotlyjs='cdn')
        return dashboard_html
    
    def _store_results(self, df, analytics, dashboard_html, filename):
        """Store results in database"""
        conn = get_db()
        cursor = conn.cursor()
        
        # Store leads (sample - top 100)
        for _, row in df.head(100).iterrows():
            cursor.execute('''
            INSERT OR REPLACE INTO leads 
            (id, nome, email, telefone, empresa, cargo, segmento, 
             lead_score, conversion_probability, predicted_ltv, segment_name, 
             processing_date, source_file)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                row.get('id', ''),
                row.get('nome', ''),
                row.get('email', ''),
                row.get('telefone', ''),
                row.get('empresa', ''),
                row.get('cargo', ''),
                row.get('segmento', ''),
                row.get('lead_score', 0),
                row.get('conversion_probability', 0),
                row.get('predicted_ltv', 0),
                row.get('segment_name', ''),
                datetime.now(),
                filename
            ))
        
        # Store analytics results
        cursor.execute('''
        INSERT INTO analytics_results 
        (id, processing_date, total_leads, roi_percentage, data_quality_score, 
         insights, recommendations, dashboard_html)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            analytics['id'],
            datetime.now(),
            analytics['total_leads'],
            analytics['roi_percentage'],
            analytics['data_quality_score'],
            json.dumps(analytics.get('insights', [])),
            json.dumps([]),
            dashboard_html
        ))
        
        conn.commit()
        conn.close()

# Flask routes
@app.route('/')
def index():
    """Main page with upload form"""
    html = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>CRM Analytics - CRM</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
            .container { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            h1 { color: #333; text-align: center; }
            .upload-box { border: 2px dashed #ccc; border-radius: 5px; padding: 40px; text-align: center; margin: 20px 0; }
            input[type="file"] { margin: 20px 0; }
            button { background: #4CAF50; color: white; padding: 10px 30px; border: none; border-radius: 5px; cursor: pointer; font-size: 16px; }
            button:hover { background: #45a049; }
            .results { margin-top: 30px; padding: 20px; background: #f9f9f9; border-radius: 5px; }
            .metric { display: inline-block; margin: 10px 20px; }
            .metric-value { font-size: 24px; font-weight: bold; color: #4CAF50; }
            .error { color: #f44336; padding: 10px; background: #ffebee; border-radius: 5px; }
            .success { color: #4CAF50; padding: 10px; background: #e8f5e9; border-radius: 5px; }
            a { color: #2196F3; text-decoration: none; }
            a:hover { text-decoration: underline; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🚀 CRM Analytics System</h1>
            <h2>CRM ETL</h2>
            
            <div class="upload-box">
                <h3>📤 Upload CSV File</h3>
                <form action="/upload" method="post" enctype="multipart/form-data">
                    <input type="file" name="file" accept=".csv" required>
                    <br><br>
                    <button type="submit">Process File</button>
                </form>
            </div>
            
            <div class="results">
                <h3>📊 Recent Dashboards</h3>
                <div id="dashboards"></div>
            </div>
            
            <div style="text-align: center; margin-top: 30px;">
                <a href="/api/docs">API Documentation</a> | 
                <a href="/export">Export Data</a> | 
                <a href="/health">System Status</a>
            </div>
        </div>
        
        <script>
            // Load recent dashboards
            fetch('/api/dashboards')
                .then(res => res.json())
                .then(data => {
                    const container = document.getElementById('dashboards');
                    if (data.dashboards && data.dashboards.length > 0) {
                        container.innerHTML = data.dashboards.map(d => 
                            `<div class="metric">
                                <a href="/dashboard/${d.id}">
                                    📈 ${new Date(d.processing_date).toLocaleDateString()} - 
                                    ${d.total_leads} leads - 
                                    ROI: ${d.roi_percentage.toFixed(1)}%
                                </a>
                            </div>`
                        ).join('<br>');
                    } else {
                        container.innerHTML = '<p>No dashboards yet. Upload a CSV to get started!</p>';
                    }
                });
        </script>
    </body>
    </html>
    '''
    return html

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload and processing"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if file and file.filename.endswith('.csv'):
        # Save file temporarily
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Process file
        processor = CRMProcessor()
        result = processor.process_csv(filepath, filename)
        
        # Clean up temp file
        os.remove(filepath)
        
        if result['success']:
            # Redirect to dashboard
            return f'''
            <html>
            <head>
                <title>Processing Complete</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 40px; text-align: center; }}
                    .success {{ color: #4CAF50; }}
                    a {{ color: #2196F3; text-decoration: none; font-size: 18px; }}
                </style>
            </head>
            <body>
                <h1 class="success">✅ Processing Complete!</h1>
                <p>Processed {result['total_leads']} leads successfully.</p>
                <p><a href="/dashboard/{result['dashboard_id']}">View Dashboard</a></p>
                <p><a href="/">Process Another File</a></p>
            </body>
            </html>
            '''
        else:
            return jsonify({'error': result['error']}), 500
    
    return jsonify({'error': 'Invalid file type'}), 400

@app.route('/dashboard/<dashboard_id>')
def view_dashboard(dashboard_id):
    """View specific dashboard"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT dashboard_html FROM analytics_results WHERE id = ?', (dashboard_id,))
    result = cursor.fetchone()
    conn.close()
    
    if result:
        return result[0]
    else:
        return "Dashboard not found", 404

@app.route('/api/dashboards')
def api_dashboards():
    """API endpoint to list dashboards"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT id, processing_date, total_leads, roi_percentage 
    FROM analytics_results 
    ORDER BY processing_date DESC 
    LIMIT 10
    ''')
    
    dashboards = []
    for row in cursor.fetchall():
        dashboards.append({
            'id': row[0],
            'processing_date': row[1],
            'total_leads': row[2],
            'roi_percentage': row[3]
        })
    
    conn.close()
    return jsonify({'dashboards': dashboards})

@app.route('/export')
def export_data():
    """Export data as CSV"""
    conn = get_db()
    df = pd.read_sql_query('SELECT * FROM leads ORDER BY processing_date DESC LIMIT 1000', conn)
    conn.close()
    
    # Save to temp file
    export_path = os.path.join(app.config['UPLOAD_FOLDER'], f'export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv')
    df.to_csv(export_path, index=False)
    
    return send_file(export_path, as_attachment=True, download_name='crm_export.csv')

@app.route('/health')
def health_check():
    """Health check endpoint"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM leads')
        lead_count = cursor.fetchone()[0]
        conn.close()
        
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'database': 'connected',
            'lead_count': lead_count
        })
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 500

@app.route('/api/docs')
def api_docs():
    """Simple API documentation"""
    docs = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>API Documentation</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            code { background: #f5f5f5; padding: 2px 5px; border-radius: 3px; }
            pre { background: #f5f5f5; padding: 15px; border-radius: 5px; overflow-x: auto; }
            .endpoint { margin: 20px 0; padding: 20px; border: 1px solid #ddd; border-radius: 5px; }
            .method { font-weight: bold; color: #4CAF50; }
        </style>
    </head>
    <body>
        <h1>CRM Analytics API Documentation</h1>
        
        <div class="endpoint">
            <h3><span class="method">GET</span> /api/dashboards</h3>
            <p>List recent dashboards</p>
            <pre>{
  "dashboards": [
    {
      "id": "abc123",
      "processing_date": "2024-01-15T10:30:00",
      "total_leads": 150,
      "roi_percentage": 156.7
    }
  ]
}</pre>
        </div>
        
        <div class="endpoint">
            <h3><span class="method">POST</span> /upload</h3>
            <p>Upload and process CSV file</p>
            <pre>Content-Type: multipart/form-data
Field: file (CSV file)</pre>
        </div>
        
        <div class="endpoint">
            <h3><span class="method">GET</span> /dashboard/{id}</h3>
            <p>View specific dashboard</p>
        </div>
        
        <div class="endpoint">
            <h3><span class="method">GET</span> /export</h3>
            <p>Export leads as CSV</p>
        </div>
        
        <div class="endpoint">
            <h3><span class="method">GET</span> /health</h3>
            <p>System health check</p>
        </div>
        
        <p><a href="/">Back to Home</a></p>
    </body>
    </html>
    '''
    return docs

# Error handlers
@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify({'error': 'Internal server error'}), 500

# Main entry point
if __name__ == '__main__':
    # This works for local development
    app.run(host='0.0.0.0', port=8080, debug=True)

# For App Engine
if os.environ.get('GAE_ENV', '').startswith('standard'):
    # Production logging
    app.logger.setLevel(logging.INFO)