"""
CRM Branded HTML Template Generator for ETL Services
"""

def get_crm_html_template(service_name, service_title, service_description, main_content):
    """
    Generate CRM branded HTML template for ETL services
    
    Args:
        service_name: Name of the service (basic, pro, ai-pro)
        service_title: Title to display in header
        service_description: Description to display in header
        main_content: Main HTML content of the page
    """
    
    return f"""
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{service_title} | CRM Tools</title>
    <link rel="stylesheet" href="/static/crm-branding.css">
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Poppins', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background-color: var(--light-gray);
            color: var(--text-dark);
            line-height: 1.6;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
        }}

        .main-container {{
            flex: 1;
            max-width: 1400px;
            margin: 0 auto;
            padding: 2rem;
            width: 100%;
        }}

        /* Override existing styles to use CRM colors */
        .header {{
            background: var(--crm-dark-blue) !important;
        }}

        .footer {{
            background: var(--crm-dark-blue) !important;
            margin-top: auto;
        }}

        h1, h2, h3 {{
            color: var(--crm-dark-blue);
        }}

        .btn {{
            padding: 0.7rem 1.5rem;
            border: none;
            border-radius: 8px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            text-decoration: none;
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            font-size: 0.9rem;
        }}

        .btn:hover {{
            transform: translateY(-2px);
            box-shadow: var(--shadow-lg);
        }}

        /* Service-specific accent colors */
        .service-basic .btn-primary {{
            background: var(--gradient-primary);
        }}

        .service-pro .btn-primary {{
            background: var(--gradient-secondary);
        }}

        .service-ai-pro .btn-primary {{
            background: var(--gradient-accent);
        }}

        /* Dashboard sections */
        .dashboard-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 2rem;
            margin-bottom: 2rem;
        }}

        /* Stats cards */
        .stat-card {{
            background: white;
            border-radius: 12px;
            padding: 1.5rem;
            box-shadow: var(--shadow-md);
            border-left: 4px solid var(--crm-teal);
            transition: all 0.3s ease;
        }}

        .stat-card:hover {{
            transform: translateY(-2px);
            box-shadow: var(--shadow-lg);
        }}

        .stat-number {{
            font-size: 2rem;
            font-weight: 700;
            color: var(--crm-teal);
            margin-bottom: 0.5rem;
        }}

        .stat-label {{
            font-size: 0.9rem;
            color: var(--text-gray);
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}

        /* Forms with CRM styling */
        input[type="file"] {{
            display: none;
        }}

        select.form-control {{
            appearance: none;
            background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath fill='%23334155' d='M6 9L2 5h8z'/%3E%3C/svg%3E");
            background-repeat: no-repeat;
            background-position: right 1rem center;
            padding-right: 2.5rem;
        }}

        /* Loading spinner */
        .spinner {{
            border: 3px solid var(--border-gray);
            border-top: 3px solid var(--crm-teal);
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 2rem auto;
        }}

        @keyframes spin {{
            0% {{ transform: rotate(0deg); }}
            100% {{ transform: rotate(360deg); }}
        }}

        /* Responsive design */
        @media (max-width: 768px) {{
            .main-container {{
                padding: 1rem;
            }}

            .dashboard-grid {{
                grid-template-columns: 1fr;
            }}
        }}
    </style>
</head>
<body class="service-{service_name}">
    <!-- CRM Branded Header -->
    <header class="crm-header">
        <div class="crm-header-content">
            <div class="crm-logo-section">
                <img src="/static/crm-logo.png" alt="CRM Tools Logo" class="crm-logo">
                <div class="crm-title-section">
                    <h1>{service_title}</h1>
                    <p>{service_description}</p>
                </div>
            </div>
        </div>
    </header>

    <!-- Main Content -->
    <main class="main-container">
        {main_content}
    </main>

    <!-- CRM Branded Footer -->
    <footer class="crm-footer">
        <div class="crm-footer-content">
            <img src="/static/crm-footer.png" alt="Powered by CRM ETL" class="crm-footer-logo">
            <p class="crm-footer-text">
                © 2025 CRM ETL. Todos os direitos reservados.<br>
                Transformando dados em decisões inteligentes.
            </p>
        </div>
    </footer>

    <script>
        // Add CRM branding animations
        document.addEventListener('DOMContentLoaded', function() {{
            // Add fade-in animation to main content
            const mainContainer = document.querySelector('.main-container');
            mainContainer.style.opacity = '0';
            mainContainer.style.transform = 'translateY(20px)';
            
            setTimeout(() => {{
                mainContainer.style.transition = 'all 0.5s ease';
                mainContainer.style.opacity = '1';
                mainContainer.style.transform = 'translateY(0)';
            }}, 100);

            // Add hover effects to cards
            const cards = document.querySelectorAll('.card, .stat-card');
            cards.forEach(card => {{
                card.addEventListener('mouseenter', function() {{
                    this.style.borderColor = 'var(--crm-teal)';
                }});
                card.addEventListener('mouseleave', function() {{
                    this.style.borderColor = 'var(--border-gray)';
                }});
            }});
        }});
    </script>
</body>
</html>
"""

def wrap_in_crm_template(service_name, service_title, service_description, content_html):
    """Helper function to wrap content in CRM template"""
    return get_crm_html_template(service_name, service_title, service_description, content_html)
