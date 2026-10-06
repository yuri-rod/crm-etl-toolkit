# CRM ETL System - Google Cloud Deployment Script (PowerShell)
# Deploy to any Google Cloud project (excluding "gestor de reservaS")

Write-Host "==========================================" -ForegroundColor Blue
Write-Host "    CRM ETL System - Cloud Deployment    " -ForegroundColor Blue  
Write-Host "==========================================" -ForegroundColor Blue
Write-Host

# Check if gcloud is installed
$gcloudVersion = & gcloud version 2>$null
if (-not $gcloudVersion) {
    Write-Host "ERROR: gcloud CLI is not installed" -ForegroundColor Red
    Write-Host "Please install Google Cloud CLI: https://cloud.google.com/sdk/docs/install"
    exit 1
}

# Get current project
$currentProject = & gcloud config get-value project 2>$null
if (-not $currentProject -or $currentProject -eq "UNSET") {
    Write-Host "ERROR: No Google Cloud project is configured" -ForegroundColor Red
    Write-Host "Please run: gcloud config set project YOUR_PROJECT_ID"
    exit 1
}

# Check if project is the restricted one
if ($currentProject -eq "gestor de reservaS") {
    Write-Host "ERROR: Cannot deploy to 'gestor de reservaS' project" -ForegroundColor Red
    Write-Host "Please switch to a different project:"
    Write-Host "gcloud config set project YOUR_OTHER_PROJECT_ID"
    exit 1
}

Write-Host "✅ Current project: $currentProject" -ForegroundColor Green
Write-Host

# Confirm deployment
$confirmation = Read-Host "Deploy CRM ETL System to project '$currentProject'? (y/N)"
if ($confirmation -ne 'y' -and $confirmation -ne 'Y') {
    Write-Host "Deployment cancelled" -ForegroundColor Yellow
    exit 0
}

Write-Host "🚀 Starting deployment..." -ForegroundColor Blue
Write-Host

# Enable required APIs
Write-Host "📋 Enabling required Google Cloud APIs..." -ForegroundColor Yellow
& gcloud services enable cloudbuild.googleapis.com
& gcloud services enable run.googleapis.com  
& gcloud services enable containerregistry.googleapis.com
Write-Host "✅ APIs enabled" -ForegroundColor Green
Write-Host

# Build and deploy using Cloud Build
Write-Host "🏗️  Building and deploying with Cloud Build..." -ForegroundColor Yellow
& gcloud builds submit --config=backend/cloudbuild.yaml --substitutions=_PROJECT_ID=$currentProject .

if ($LASTEXITCODE -eq 0) {
    Write-Host
    Write-Host "🎉 Deployment successful!" -ForegroundColor Green
    Write-Host
    
    # Get service URL
    $serviceUrl = & gcloud run services describe crm-etl-api --region=us-central1 --format='value(status.url)' 2>$null
    
    if ($serviceUrl) {
        Write-Host "🔗 Your CRM ETL API is available at:" -ForegroundColor Blue
        Write-Host "   $serviceUrl" -ForegroundColor Green
        Write-Host
        Write-Host "📚 API Documentation:" -ForegroundColor Blue  
        Write-Host "   $serviceUrl/docs" -ForegroundColor Green
        Write-Host
        Write-Host "🔍 Health Check:" -ForegroundColor Blue
        Write-Host "   $serviceUrl/health" -ForegroundColor Green
    }
    
    Write-Host
    Write-Host "📝 Next steps:" -ForegroundColor Yellow
    Write-Host "1. Configure environment variables if needed:"
    Write-Host "   gcloud run services update crm-etl-api --region=us-central1 --set-env-vars KEY=VALUE"
    Write-Host
    Write-Host "2. Set up authentication if required:"
    Write-Host "   gcloud run services update crm-etl-api --region=us-central1 --remove-flags allow-unauthenticated"
    Write-Host
    Write-Host "3. Monitor your service:"
    Write-Host "   gcloud run services logs read crm-etl-api --region=us-central1"
    
} else {
    Write-Host "❌ Deployment failed" -ForegroundColor Red
    Write-Host "Check the build logs above for details"
    exit 1
}