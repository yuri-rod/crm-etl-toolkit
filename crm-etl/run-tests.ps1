# CRM ETL Test Suite Runner for Windows
# Ensures green tests before deployment

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "                 CRM ETL TEST SUITE                        " -ForegroundColor Cyan  
Write-Host "                 Testing before deployment                 " -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Function to check if a command exists
function Test-Command {
    param($Command)
    try {
        Get-Command $Command -ErrorAction Stop
        return $true
    } catch {
        return $false
    }
}

# Check Python installation
Write-Host "🔧 Checking Python installation..." -ForegroundColor Blue
if (-not (Test-Command "python") -and -not (Test-Command "python3")) {
    Write-Host "❌ Python not found. Please install Python 3.9+ and add to PATH" -ForegroundColor Red
    exit 1
}

$pythonCmd = if (Test-Command "python3") { "python3" } else { "python" }
Write-Host "✅ Python found: $pythonCmd" -ForegroundColor Green

# Check dependencies
Write-Host ""
Write-Host "🔧 Checking test dependencies..." -ForegroundColor Blue

$requiredPackages = @("pytest", "pandas", "numpy")
$missingPackages = @()

foreach ($package in $requiredPackages) {
    try {
        & $pythonCmd -c "import $($package.replace('-', '_'))" 2>$null
        if ($LASTEXITCODE -ne 0) {
            $missingPackages += $package
        } else {
            Write-Host "✅ $package is installed" -ForegroundColor Green
        }
    } catch {
        $missingPackages += $package
    }
}

if ($missingPackages.Count -gt 0) {
    Write-Host "⚠️ Missing packages: $($missingPackages -join ', ')" -ForegroundColor Yellow
    Write-Host "Installing basic dependencies..." -ForegroundColor Blue
    & $pythonCmd -m pip install pytest pandas numpy httpx
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Failed to install dependencies" -ForegroundColor Red
        exit 1
    }
}

# Parse command line arguments
param(
    [switch]$Quick,
    [switch]$Smoke,
    [switch]$ETL,
    [switch]$Backend,
    [switch]$Frontend,
    [switch]$All,
    [switch]$Help
)

if ($Help) {
    Write-Host "Usage: .\run-tests.ps1 [options]" -ForegroundColor Cyan
    Write-Host "Options:" -ForegroundColor White
    Write-Host "  -Quick     Run quick validation tests" -ForegroundColor White
    Write-Host "  -Smoke     Run smoke tests only" -ForegroundColor White
    Write-Host "  -ETL       Run ETL pipeline tests only" -ForegroundColor White
    Write-Host "  -Backend   Run backend API tests only" -ForegroundColor White
    Write-Host "  -Frontend  Run frontend tests only" -ForegroundColor White
    Write-Host "  -All       Run complete test suite" -ForegroundColor White
    Write-Host "  -Help      Show this help message" -ForegroundColor White
    Write-Host ""
    Write-Host "Examples:" -ForegroundColor Cyan
    Write-Host "  .\run-tests.ps1 -Quick" -ForegroundColor White
    Write-Host "  .\run-tests.ps1 -ETL" -ForegroundColor White
    exit 0
}

# Determine which tests to run
$testArgs = @("-m", "pytest", "tests/", "-v", "--tb=short")

if ($Smoke) {
    Write-Host "🔥 Running smoke tests..." -ForegroundColor Yellow
    $testArgs = @("-m", "pytest", "tests/test_etl_pipeline.py::TestETLPipeline::test_csv_extraction", "tests/test_frontend_links.py::TestFrontendBasic", "-v")
} elseif ($ETL) {
    Write-Host "🔄 Running ETL pipeline tests..." -ForegroundColor Yellow
    $testArgs = @("-m", "pytest", "tests/test_etl_pipeline.py", "-v")
} elseif ($Backend) {
    Write-Host "🌐 Running backend API tests..." -ForegroundColor Yellow
    $testArgs = @("-m", "pytest", "tests/test_backend_endpoints.py", "-v")
} elseif ($Frontend) {
    Write-Host "🖥️ Running frontend tests..." -ForegroundColor Yellow
    $testArgs = @("-m", "pytest", "tests/test_frontend_links.py::TestFrontendBasic", "-v")
} elseif ($All) {
    Write-Host "🎯 Running complete test suite..." -ForegroundColor Yellow
    $testArgs = @("-m", "pytest", "tests/", "-v", "--tb=short", "--maxfail=10")
} elseif ($Quick) {
    Write-Host "⚡ Running quick tests..." -ForegroundColor Yellow
    $testArgs = @("-m", "pytest", "tests/test_etl_pipeline.py::TestETLPipeline::test_csv_extraction", "tests/test_etl_pipeline.py::TestETLPipeline::test_complete_etl_pipeline", "-v")
} else {
    Write-Host "🧪 Running default test suite..." -ForegroundColor Yellow
    $testArgs = @("-m", "pytest", "tests/test_etl_pipeline.py", "tests/test_frontend_links.py::TestFrontendBasic", "-v", "--tb=short")
}

Write-Host ""
Write-Host "Command: $pythonCmd $($testArgs -join ' ')" -ForegroundColor Cyan
Write-Host ""

# Check if backend server is running
Write-Host "🔧 Checking backend server..." -ForegroundColor Blue
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000" -TimeoutSec 2 -ErrorAction Stop
    Write-Host "✅ Backend server is running" -ForegroundColor Green
} catch {
    Write-Host "⚠️ Backend server not running - API tests may fail" -ForegroundColor Yellow
    Write-Host "Start server with: python BETA\backend\api_server.py" -ForegroundColor Cyan
}

# Run the tests
Write-Host ""
Write-Host "🚀 Starting tests..." -ForegroundColor Green
Write-Host ""

$startTime = Get-Date

# Execute the test command
try {
    & $pythonCmd @testArgs
    $testExitCode = $LASTEXITCODE
} catch {
    Write-Host "❌ Test execution failed: $($_.Exception.Message)" -ForegroundColor Red
    $testExitCode = 1
}

$endTime = Get-Date
$duration = ($endTime - $startTime).TotalSeconds

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "                      TEST SUMMARY                         " -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

Write-Host "⏱️ Total time: $([math]::Round($duration, 1)) seconds" -ForegroundColor White

if ($testExitCode -eq 0) {
    Write-Host "🚀 ALL TESTS PASSED - READY FOR DEPLOYMENT" -ForegroundColor Green -BackgroundColor Black
    Write-Host ""
    Write-Host "✅ System is ready for deployment!" -ForegroundColor Green
} else {
    Write-Host "🛑 TESTS FAILED - DO NOT DEPLOY" -ForegroundColor Red -BackgroundColor Black
    Write-Host ""
    Write-Host "❌ Fix failing tests before deployment!" -ForegroundColor Red
    Write-Host "Run with -All for detailed test results" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "📋 Available test options:" -ForegroundColor Cyan
Write-Host "  .\run-tests.ps1 -Quick     # Quick validation" -ForegroundColor White
Write-Host "  .\run-tests.ps1 -ETL       # ETL pipeline tests" -ForegroundColor White
Write-Host "  .\run-tests.ps1 -All       # Complete test suite" -ForegroundColor White
Write-Host ""

exit $testExitCode
