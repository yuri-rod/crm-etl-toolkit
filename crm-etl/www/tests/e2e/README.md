# 🧪 Testes End-to-End - Sistema ETL Inteligente

Este diretório contém os testes end-to-end (E2E) para o Sistema ETL Inteligente da CRM Tools, implementados usando Playwright.

## 📋 Visão Geral

Os testes E2E verificam o funcionamento completo da aplicação, simulando interações reais do usuário:

- ✅ **Upload de arquivos** (CSV, Excel)
- ✅ **Configuração de pipeline**
- ✅ **Execução completa do ETL**
- ✅ **Verificação de resultados**
- ✅ **Download de arquivos processados**
- ✅ **Interface responsiva** (Desktop, Tablet, Mobile)

## 🚀 Execução Rápida

```bash
# Instalar dependências
pip install -r requirements.txt

# Instalar browsers
python run_tests.py --install-browsers

# Executar testes smoke (básicos)
python run_tests.py --suite smoke --browser chromium

# Executar com interface gráfica (para debug)
python run_tests.py --suite smoke --browser chromium --headed
```

## 📁 Estrutura dos Arquivos

```
tests/e2e/
├── requirements.txt           # Dependências Python
├── pytest.ini               # Configuração do pytest
├── conftest.py              # Fixtures e configuração
├── run_tests.py             # Script principal para executar testes
├── README.md                # Esta documentação
├── playwright.config.py     # Configurações do Playwright
├── pages/                   # Page Objects
│   ├── __init__.py
│   ├── base_page.py        # Classe base para pages
│   └── etl_page.py         # Page object da interface ETL
├── test_smoke.py            # Testes básicos (críticos)
├── test_full_pipeline.py    # Testes completos da pipeline
└── test_responsive.py       # Testes de design responsivo
```

## 🎯 Suites de Testes

### 🟢 Smoke Tests (`test_smoke.py`)
Testes básicos e rápidos que verificam funcionalidades críticas:
- Carregamento da página principal
- Interface de upload disponível
- Painel de configuração acessível
- Dashboard ao vivo funcional
- Layout responsivo básico

**Tempo:** ~5-10 minutos  
**Quando executar:** A cada commit, antes de deploy

### 🟡 Regression Tests (`test_full_pipeline.py`)
Testes completos que executam workflows end-to-end:
- Workflow completo de treinamento (CSV e Excel)
- Workflow completo de predição
- Diferentes configurações de pipeline
- Indicação de progresso
- Sistema de notificações
- Dashboard ao vivo durante execução

**Tempo:** ~20-45 minutos  
**Quando executar:** Antes de releases, diariamente

### 🟣 Mobile Tests (`test_responsive.py`)
Testes específicos para dispositivos móveis e tablets:
- Layout mobile e tablet
- Interface de upload em mobile
- Configurações em dispositivos pequenos
- Dashboard responsivo
- Testes cross-device

**Tempo:** ~15-25 minutos  
**Quando executar:** Antes de releases, quando houver mudanças de UI

## 🛠 Executando os Testes

### Usando o Script Python (Recomendado)

```bash
# Testes básicos
python run_tests.py --suite smoke --browser chromium

# Todos os testes em todos os browsers
python run_tests.py --suite all --browser all

# Testes com interface gráfica (debug)
python run_tests.py --suite smoke --browser chromium --headed

# Arquivo específico
python run_tests.py test_smoke.py --browser firefox

# Sem iniciar servidor (se já estiver rodando)
python run_tests.py --suite smoke --no-server

# Abrir relatórios após execução
python run_tests.py --suite smoke --open-reports
```

### Usando Pytest Diretamente

```bash
# Navegar para diretório de testes
cd tests/e2e

# Executar testes específicos
pytest test_smoke.py --browser=chromium --headed=false -v

# Com relatórios HTML
pytest test_smoke.py --browser=chromium --html=../../reports/smoke-report.html --self-contained-html

# Apenas testes móveis
pytest test_responsive.py -m mobile --browser=chromium

# Executar em paralelo (se instalado pytest-xdist)
pytest test_smoke.py -n 2 --browser=chromium
```

### Variáveis de Ambiente

```bash
# URL do servidor (padrão: http://localhost:8000)
export BASE_URL=http://localhost:3000

# Executar sem interface gráfica
export HEADLESS=true

# Timeout personalizado (em ms)
export TIMEOUT=60000

# Velocidade de execução (para debug)
export SLOW_MO=100
```

## 📊 Relatórios e Resultados

### Relatórios HTML
Os testes geram relatórios HTML detalhados em `reports/`:
- Resultado de cada teste
- Screenshots de falhas
- Logs detalhados
- Métricas de execução

### Screenshots
Capturas de tela são salvas automaticamente em `screenshots/`:
- Falhas de teste
- Pontos específicos do fluxo
- Diferentes resoluções (responsivo)

### Artefatos
- **Vídeos:** Gravações da execução (apenas em falhas)
- **Traces:** Rastreamento detalhado da execução
- **Logs:** Saídas do console da aplicação

## 🔧 Configuração Avançada

### Configurações do Playwright

Editar `playwright.config.py`:

```python
# Configurações por ambiente
ENVIRONMENTS = {
    'local': {
        'base_url': 'http://localhost:8000',
        'headless': False,
    },
    'staging': {
        'base_url': 'https://staging.example.com',
        'headless': True,
    }
}
```

### Configurações do Pytest

Editar `pytest.ini`:

```ini
[pytest]
# Adicionar marcadores customizados
markers =
    critical: Critical functionality tests
    integration: Integration tests
    
# Opções de execução
addopts = 
    --strict-markers
    --tb=short
```

### Fixtures Customizadas

Adicionar em `conftest.py`:

```python
@pytest.fixture
def custom_context(browser):
    context = browser.new_context(
        viewport={"width": 1366, "height": 768},
        locale="pt-BR"
    )
    yield context
    context.close()
```

## 🚀 Integração CI/CD

### GitHub Actions

O arquivo `.github/workflows/e2e-tests.yml` configura execução automática:

- **Push/PR:** Testes smoke em múltiplos browsers
- **Diário:** Suite completa de testes
- **Manual:** Execução sob demanda

### Comandos CI

```bash
# Execução headless
HEADLESS=true python run_tests.py --suite smoke --browser chromium

# Com artefatos
python run_tests.py --suite all --browser chromium --open-reports
```

## 🐛 Debug e Troubleshooting

### Debug Local

```bash
# Executar com interface gráfica
python run_tests.py --suite smoke --headed

# Executar teste específico com debug
pytest test_smoke.py::TestSmokeSuite::test_homepage_loads --browser=chromium --headed=true -v -s

# Usar breakpoints
pytest test_smoke.py --browser=chromium --headed=true --pdb
```

### Problemas Comuns

#### Servidor não inicia
```bash
# Verificar se porta está livre
netstat -an | grep :8000

# Iniciar servidor manualmente
python backend/api_server.py --port 8001

# Usar servidor externo
python run_tests.py --base-url http://localhost:8001 --no-server
```

#### Browsers não instalados
```bash
# Instalar todos os browsers
python run_tests.py --install-browsers

# Instalar browser específico
playwright install chromium --with-deps
```

#### Timeouts
```bash
# Aumentar timeout
export TIMEOUT=60000

# Ou no código
etl_page.wait_for_pipeline_completion(timeout=180000)
```

#### Falhas em mobile
```bash
# Executar apenas testes mobile
pytest test_responsive.py -m mobile --browser=chromium -v

# Debug com screenshot
pytest test_responsive.py::TestMobileResponsive::test_mobile_layout_loads --browser=chromium --headed=true
```

## 📈 Métricas e KPIs

### Cobertura de Testes
- ✅ Upload de arquivos: CSV, Excel
- ✅ Configurações: Treinamento, Predição
- ✅ Pipeline completa: Início ao fim
- ✅ Interface: Desktop, Tablet, Mobile
- ✅ Downloads: Resultados processados

### Targets de Performance
- **Smoke Tests:** < 10 minutos
- **Regression Tests:** < 45 minutos
- **Mobile Tests:** < 25 minutos
- **Full Suite:** < 60 minutos

### Reliability
- **Target:** 95% de sucesso em execuções CI
- **Retry:** Testes flaky têm retry automático
- **Alertas:** Notificação em falhas consecutivas

## 🤝 Contribuindo

### Adicionando Novos Testes

1. **Smoke Test:** Para funcionalidades críticas
   ```python
   def test_critical_feature(self, etl_page: ETLPage):
       etl_page.load_page()
       # Teste rápido da funcionalidade
   ```

2. **Regression Test:** Para fluxos completos
   ```python  
   def test_complete_workflow(self, etl_page: ETLPage, sample_csv_file: str):
       # Teste completo end-to-end
   ```

3. **Mobile Test:** Para responsividade
   ```python
   @pytest.mark.mobile
   def test_mobile_feature(self, mobile_context: BrowserContext):
       # Teste específico para mobile
   ```

### Page Objects

Criar novos page objects em `pages/`:

```python
class NewFeaturePage(BasePage):
    SELECTORS = {
        'feature_button': '#feature-btn',
        'result_area': '.results'
    }
    
    def use_feature(self):
        self.click_element(self.SELECTORS['feature_button'])
        # Implementar funcionalidade
```

### Boas Práticas

- ✅ **Nomes descritivos:** `test_upload_csv_file_training_mode`
- ✅ **Documentação:** Docstrings explicando o que o teste faz
- ✅ **Assertions claras:** Mensagens de erro úteis
- ✅ **Cleanup:** Usar fixtures para setup/teardown
- ✅ **Marcadores:** `@pytest.mark.smoke` para categorização
- ✅ **Page Objects:** Reutilizar elementos comuns

## 📞 Suporte

### Logs e Debug
- **Console logs:** Capturados automaticamente
- **Screenshots:** Salvos em falhas
- **Traces:** Disponíveis para debugging

### Contato
- **Equipe:** CRM ETL
- **Projeto:** Sistema ETL Inteligente
- **Documentação:** [docs.crm.com.br](https://docs.crm.com.br)

---

**CRM Tools - Sistema ETL Inteligente**  
*Desenvolvido com ❤️ pela CRM ETL*
