# CRM ETL System - Google Cloud Deployment Instructions

## Prerequisites

1. **Google Cloud CLI installed**
   ```bash
   # Install from: https://cloud.google.com/sdk/docs/install
   gcloud --version
   ```

2. **Authenticated with Google Cloud**
   ```bash
   gcloud auth login
   gcloud auth configure-docker
   ```

3. **Set target project** (NOT "gestor de reservaS")
   ```bash
   gcloud config set project YOUR_PROJECT_ID
   ```

## Quick Deployment

### Option 1: Linux/Mac
```bash
chmod +x deploy.sh
./deploy.sh
```

### Option 2: Windows PowerShell
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
./deploy.ps1
```

### Option 3: Manual Deployment
```bash
# Enable APIs
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com

# Deploy
gcloud builds submit --config=backend/cloudbuild.yaml .
```

## What Gets Deployed

- **Service Name**: `crm-etl-api`
- **Region**: `us-central1`
- **Platform**: Cloud Run (fully managed)
- **Resources**: 2 CPU cores, 2GB RAM
- **Access**: Public (unauthenticated)
- **Auto-scaling**: 0-10 instances

## Post-Deployment Configuration

### 1. Environment Variables (Optional)
```bash
gcloud run services update crm-etl-api \
  --region=us-central1 \
  --set-env-vars ANTHROPIC_API_KEY=your_key,OPENAI_API_KEY=your_key
```

### 2. Enable Authentication (Optional)
```bash
gcloud run services update crm-etl-api \
  --region=us-central1 \
  --remove-flags allow-unauthenticated
```

### 3. Custom Domain (Optional)
```bash
gcloud run domain-mappings create \
  --service crm-etl-api \
  --domain your-domain.com \
  --region us-central1
```

## Service Endpoints

After deployment, your service will be available at:
- **Main API**: `https://crm-etl-api-[hash]-uc.a.run.app`
- **API Docs**: `https://crm-etl-api-[hash]-uc.a.run.app/docs`
- **Health Check**: `https://crm-etl-api-[hash]-uc.a.run.app/health`

## Key Features Deployed

### API Endpoints
- `POST /process-data` - Process ETL data
- `POST /generate-rules` - Generate AI rules
- `POST /predict-leads` - ML lead prediction
- `GET /health` - Health check
- `GET /docs` - API documentation

### Integrated Components
- **Unified ETL Pipeline** - AI-powered data processing
- **AI Rule Generator** - Claude/OpenAI integration
- **ML Lead Predictor** - CRM lead scoring
- **Data Extractors** - Multiple format support
- **Monitoring** - Built-in health checks

## Monitoring & Logs

```bash
# View logs
gcloud run services logs read crm-etl-api --region=us-central1

# Monitor metrics
gcloud run services list --region=us-central1

# Service details
gcloud run services describe crm-etl-api --region=us-central1
```

## Troubleshooting

### Common Issues

1. **Build fails with "No such file"**
   - Ensure you're running from the project root directory
   - Check file paths in Dockerfile

2. **Service fails to start**
   - Check service logs: `gcloud run services logs read crm-etl-api --region=us-central1`
   - Verify Python dependencies in requirements-prod.txt

3. **Import errors**
   - Missing dependencies in requirements-prod.txt
   - Python path issues - check PYTHONPATH environment variable

4. **Permission errors**
   - Ensure service account has necessary permissions
   - Check Cloud Build service account roles

### Health Check
Test your deployment:
```bash
curl https://YOUR_SERVICE_URL/health
```

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2025-01-09T...",
  "version": "1.0.0",
  "service": "crm-etl-api"
}
```

## Cost Optimization

- **Pay-per-use**: Only charged when processing requests
- **Auto-scaling**: Scales to zero when idle
- **Resource limits**: Configured for optimal cost/performance
- **Monitoring**: Track usage and costs in Cloud Console

## Security Best Practices

1. **API Keys**: Use environment variables, not hardcoded values
2. **Authentication**: Enable if needed for production
3. **HTTPS**: Enforced by default on Cloud Run
4. **Network**: VPC connector if accessing private resources
5. **IAM**: Principle of least privilege for service accounts

## Support

For deployment issues:
1. Check the logs first
2. Verify prerequisites are met  
3. Ensure correct project is selected
4. Contact: tech@crm.com.br