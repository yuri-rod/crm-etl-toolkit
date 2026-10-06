#!/bin/bash
# CRM ETL Test Suite Runner for Unix/Linux/macOS
# Ensures green tests before deployment

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Print header
echo -e "${CYAN}${BOLD}============================================================${NC}"
echo -e "${CYAN}${BOLD}                 CRM ETL TEST SUITE                        ${NC}"
echo -e "${CYAN}${BOLD}                 Testing before deployment                 ${NC}"
echo -e "${CYAN}${BOLD}============================================================${NC}"
echo ""

# Function to print colored output
print_step() {
    echo -e "${BLUE}🔧 $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check Python installation
print_step "Checking Python installation..."
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
    print_success "Python found: python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
    print_success "Python found: python"
else
    print_error "Python not found. Please install Python 3.9+ and add to PATH"
    exit 1
fi

# Check Python version
PYTHON_VERSION=$($PYTHON_CMD -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
print_success "Python version: $PYTHON_VERSION"

# Check dependencies
print_step "Checking test dependencies..."
REQUIRED_PACKAGES=("pytest" "pandas" "numpy")
MISSING_PACKAGES=()

for package in "${REQUIRED_PACKAGES[@]}"; do
    if $PYTHON_CMD -c "import ${package//-/_}" 2>/dev/null; then
        print_success "$package is installed"
    else
        MISSING_PACKAGES+=("$package")
    fi
done

if [ ${#MISSING_PACKAGES[@]} -gt 0 ]; then
    print_warning "Missing packages: ${MISSING_PACKAGES[*]}"
    print_step "Installing basic dependencies..."
    $PYTHON_CMD -m pip install pytest pandas numpy httpx || {
        print_error "Failed to install dependencies"
        exit 1
    }
fi

# Parse command line arguments
SMOKE=false
ETL=false
BACKEND=false
FRONTEND=false
ALL=false
QUICK=false
HELP=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --smoke)
            SMOKE=true
            shift
            ;;
        --etl)
            ETL=true
            shift
            ;;
        --backend)
            BACKEND=true
            shift
            ;;
        --frontend)
            FRONTEND=true
            shift
            ;;
        --all)
            ALL=true
            shift
            ;;
        --quick)
            QUICK=true
            shift
            ;;
        --help|-h)
            HELP=true
            shift
            ;;
        *)
            print_error "Unknown option: $1"
            HELP=true
            shift
            ;;
    esac
done

if [ "$HELP" = true ]; then
    echo -e "${CYAN}Usage: ./run-tests.sh [options]${NC}"
    echo -e "${BOLD}Options:${NC}"
    echo "  --quick     Run quick validation tests"
    echo "  --smoke     Run smoke tests only"
    echo "  --etl       Run ETL pipeline tests only"
    echo "  --backend   Run backend API tests only"
    echo "  --frontend  Run frontend tests only"
    echo "  --all       Run complete test suite"
    echo "  --help,-h   Show this help message"
    echo ""
    echo -e "${CYAN}Examples:${NC}"
    echo "  ./run-tests.sh --quick"
    echo "  ./run-tests.sh --etl"
    echo "  ./run-tests.sh --all"
    exit 0
fi

# Determine which tests to run
TEST_ARGS=("-m" "pytest" "tests/" "-v" "--tb=short")

if [ "$SMOKE" = true ]; then
    echo -e "${YELLOW}🔥 Running smoke tests...${NC}"
    TEST_ARGS=("-m" "pytest" "tests/test_etl_pipeline.py::TestETLPipeline::test_csv_extraction" "tests/test_frontend_links.py::TestFrontendBasic" "-v")
elif [ "$ETL" = true ]; then
    echo -e "${YELLOW}🔄 Running ETL pipeline tests...${NC}"
    TEST_ARGS=("-m" "pytest" "tests/test_etl_pipeline.py" "-v")
elif [ "$BACKEND" = true ]; then
    echo -e "${YELLOW}🌐 Running backend API tests...${NC}"
    TEST_ARGS=("-m" "pytest" "tests/test_backend_endpoints.py" "-v")
elif [ "$FRONTEND" = true ]; then
    echo -e "${YELLOW}🖥️ Running frontend tests...${NC}"
    TEST_ARGS=("-m" "pytest" "tests/test_frontend_links.py::TestFrontendBasic" "-v")
elif [ "$ALL" = true ]; then
    echo -e "${YELLOW}🎯 Running complete test suite...${NC}"
    TEST_ARGS=("-m" "pytest" "tests/" "-v" "--tb=short" "--maxfail=10")
elif [ "$QUICK" = true ]; then
    echo -e "${YELLOW}⚡ Running quick tests...${NC}"
    TEST_ARGS=("-m" "pytest" "tests/test_etl_pipeline.py::TestETLPipeline::test_csv_extraction" "tests/test_etl_pipeline.py::TestETLPipeline::test_complete_etl_pipeline" "-v")
else
    echo -e "${YELLOW}🧪 Running default test suite...${NC}"
    TEST_ARGS=("-m" "pytest" "tests/test_etl_pipeline.py" "tests/test_frontend_links.py::TestFrontendBasic" "-v" "--tb=short")
fi

echo ""
echo -e "${CYAN}Command: $PYTHON_CMD ${TEST_ARGS[*]}${NC}"
echo ""

# Check if backend server is running
print_step "Checking backend server..."
if curl -s --connect-timeout 2 http://localhost:8000 >/dev/null 2>&1; then
    print_success "Backend server is running"
else
    print_warning "Backend server not running - API tests may fail"
    echo -e "${CYAN}Start server with: python BETA/backend/api_server.py${NC}"
fi

# Run the tests
echo ""
echo -e "${GREEN}🚀 Starting tests...${NC}"
echo ""

START_TIME=$(date +%s)

# Execute the test command
set +e  # Don't exit on test failures
$PYTHON_CMD "${TEST_ARGS[@]}"
TEST_EXIT_CODE=$?
set -e

END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

echo ""
echo -e "${CYAN}${BOLD}============================================================${NC}"
echo -e "${CYAN}${BOLD}                      TEST SUMMARY                         ${NC}"
echo -e "${CYAN}${BOLD}============================================================${NC}"

echo -e "⏱️ Total time: ${DURATION} seconds"

if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}${BOLD}🚀 ALL TESTS PASSED - READY FOR DEPLOYMENT${NC}"
    echo ""
    print_success "System is ready for deployment!"
else
    echo -e "${RED}${BOLD}🛑 TESTS FAILED - DO NOT DEPLOY${NC}"
    echo ""
    print_error "Fix failing tests before deployment!"
    print_warning "Run with --all for detailed test results"
fi

echo ""
echo -e "${CYAN}📋 Available test options:${NC}"
echo "  ./run-tests.sh --quick     # Quick validation"
echo "  ./run-tests.sh --etl       # ETL pipeline tests"
echo "  ./run-tests.sh --all       # Complete test suite"
echo ""

exit $TEST_EXIT_CODE
