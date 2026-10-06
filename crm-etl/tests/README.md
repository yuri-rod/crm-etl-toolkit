# CRM ETL Test Suite

Automated local test suite for CRM ETL ETL system with comprehensive testing coverage.

## 🎯 Overview

This test suite provides comprehensive automated testing for the CRM ETL system, including:

- **Backend endpoint smoke tests** using `httpx.AsyncClient`
- **ETL pipeline tests** that load CSV → transform → write JSON
- **Frontend link checks** with `pytest-playwright` (optional)
- **Automated CI/CD workflow** to ensure green tests before deployment

## 📁 Test Structure

```
tests/
├── README.md                     # This documentation
├── requirements-test.txt         # Testing dependencies
├── test_backend_endpoints.py     # Backend API smoke tests
├── test_etl_pipeline.py         # ETL pipeline comprehensive tests
├── test_frontend_links.py       # Frontend functionality tests
└── test_extractors.py           # Existing unit tests
```

## 🚀 Quick Start

### 1. Install Dependencies

```bash
# Basic dependencies
pip install pytest pytest-asyncio httpx pandas numpy

# Full test suite
pip install -r tests/requirements-test.txt

# Optional: Playwright for frontend tests
pip install pytest-playwright
playwright install
```

### 2. Run Tests

```bash
# Run all tests with the test runner
python run_tests.py

# Run specific test categories
python run_tests.py --smoke      # Quick validation
python run_tests.py --etl        # ETL pipeline tests
python run_tests.py --backend    # API endpoint tests
python run_tests.py --frontend   # Frontend tests

# Run with pytest directly
pytest tests/ -v                 # All tests
pytest tests/test_etl_pipeline.py -v  # ETL tests only
```

## 📋 Test Categories

### 🔥 Smoke Tests
Quick validation tests to ensure core functionality:
- Backend server availability
- ETL CSV extraction capability
- Frontend file structure

### 🔄 ETL Pipeline Tests (`test_etl_pipeline.py`)
Comprehensive ETL workflow testing:
- **CSV Extraction**: Load and validate sample customer data
- **Data Transformation**: Apply business logic transformations
- **JSON Output**: Generate structured JSON with metadata
- **Complete Pipeline**: End-to-end CSV → Transform → JSON
- **Error Handling**: Graceful handling of malformed data
- **Data Quality**: Validation rules and checks
- **Performance**: Large dataset processing tests

### 🌐 Backend API Tests (`test_backend_endpoints.py`)
Backend endpoint smoke tests using async HTTP client:
- Root endpoint availability
- Health check endpoints
- API documentation endpoints
- Pipeline execution endpoints
- AI rule generation endpoints
- CORS configuration validation
- File upload handling
- Error response validation

### 🖥️ Frontend Tests (`test_frontend_links.py`)
Frontend functionality and link integrity:
- **Basic Tests** (no Playwright required):
  - HTML file structure validation
  - Asset reference checks
  - CRM branding verification
- **Playwright Tests** (browser automation):
  - Page loading and rendering
  - Navigation link validation
  - Interactive element testing
  - Responsive design checks
  - JavaScript functionality
  - Accessibility basics
  - Performance metrics

## 🛠️ Configuration

### Pytest Configuration (`pytest.ini`)
```ini
[tool:pytest]
testpaths = tests
markers =
    unit: Unit tests for individual components
    integration: Integration tests for component interaction
    smoke: Smoke tests for basic functionality
    playwright: Tests requiring Playwright browser automation
addopts = -v --tb=short --color=yes
```

### Environment Variables
```bash
# Backend server URL (default: http://localhost:8000)
export CRM_BACKEND_URL="http://localhost:8000"

# Test timeout (default: 30 seconds)
export CRM_TEST_TIMEOUT="30"
```

## 🔄 CI/CD Integration

### GitHub Actions Workflow
Automated testing on:
- Push to `main` or `develop` branches
- Pull requests
- Daily scheduled runs

The workflow includes:
1. **Multi-version testing** (Python 3.9, 3.10, 3.11)
2. **Dependency caching** for faster builds
3. **Parallel test execution**
4. **Test report generation**
5. **Security scanning** with bandit
6. **Performance benchmarking**

### Pre-deployment Check
```bash
# Ensure tests pass before deployment
python run_tests.py --quick

# Full validation
python run_tests.py --all
```

## 📊 Test Reporting

### Console Output
The test runner provides colored, detailed console output:
- ✅ Passed tests
- ❌ Failed tests
- ⚠️ Warnings and skipped tests
- 📊 Summary statistics
- 🚀 Deployment readiness status

### JSON Reports
Test results are saved to `test-results.json`:
```json
{
  "timestamp": 1234567890,
  "total_duration": 45.2,
  "results": {
    "etl_pipeline_tests": {
      "exit_code": 0,
      "passed": 8,
      "failed": 0,
      "duration": 12.3
    }
  }
}
```

### HTML Reports (with pytest-html)
```bash
pytest tests/ --html=report.html --self-contained-html
```

## 🧪 Test Data

### Sample CSV Data
Tests use realistic customer data:
```csv
customer_id,name,email,age,city,purchase_value,purchase_date,category,satisfaction_score,is_premium
1,Customer 1,customer1@example.com,25,São Paulo,150.50,2024-03-15,Electronics,4,true
```

### Transformations Applied
- Customer segmentation (Basic, Standard, Premium, VIP)
- Age grouping (Young, Middle-aged, Senior)
- Purchase month extraction
- High-value customer flagging
- Processing timestamps

### JSON Output Structure
```json
{
  "metadata": {
    "source_file": "sample_customers.csv",
    "processing_timestamp": "2024-03-15T10:30:00",
    "total_records": 100,
    "transformation_applied": ["customer_segmentation", "age_grouping"]
  },
  "data": [...],
  "summary_statistics": {
    "age_stats": {"mean": 42.5, "median": 40.0},
    "purchase_value_stats": {"total": 15000.50},
    "category_distribution": {"Electronics": 25, "Clothing": 20}
  }
}
```

## 🚨 Troubleshooting

### Common Issues

#### 1. Backend Server Not Running
```bash
# Error: API tests failing with connection errors
# Solution: Start the backend server
python BETA/backend/api_server.py
```

#### 2. Missing Dependencies
```bash
# Error: ImportError for test dependencies
# Solution: Install test requirements
pip install -r tests/requirements-test.txt
```

#### 3. Playwright Installation
```bash
# Error: Playwright browser not found
# Solution: Install browsers
playwright install chromium
```

#### 4. Test Timeouts
```bash
# Error: Tests timing out
# Solution: Increase timeout in pytest.ini or run with --timeout=60
pytest tests/ --timeout=60
```

### Debug Mode
```bash
# Run tests with verbose output and no capture
pytest tests/ -v -s --tb=long

# Run specific failing test
pytest tests/test_etl_pipeline.py::TestETLPipeline::test_csv_extraction -v -s
```

## 🔧 Development

### Adding New Tests
1. Create test file in `tests/` directory
2. Follow naming convention: `test_*.py`
3. Use appropriate markers: `@pytest.mark.unit`, `@pytest.mark.integration`
4. Add to test runner if needed

### Test Best Practices
- **Isolation**: Each test should be independent
- **Clear naming**: Test names should describe what they validate
- **Fixtures**: Use pytest fixtures for setup/teardown
- **Mocking**: Mock external dependencies
- **Assertions**: Use descriptive assertion messages

### Custom Markers
```python
@pytest.mark.smoke  # Quick validation tests
@pytest.mark.slow   # Long-running tests
@pytest.mark.playwright  # Requires browser automation
@pytest.mark.integration  # Cross-component tests
```

## 📚 References

- [Pytest Documentation](https://docs.pytest.org/)
- [HTTPX Documentation](https://www.python-httpx.org/)
- [Playwright for Python](https://playwright.dev/python/)
- [Pandas Testing](https://pandas.pydata.org/docs/reference/general_functions.html#testing)

## 🤝 Contributing

1. Add tests for new features
2. Ensure all tests pass before committing
3. Update documentation for new test categories
4. Follow existing code style and patterns

## 📝 License

Part of CRM ETL ETL system. All rights reserved.

---

*"Testing is not just about finding bugs; it's about building confidence in our system."*

**CRM ETL** - Powering the future of data processing
