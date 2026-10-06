#!/bin/bash

# CRM ETL System - Google Cloud Deployment Script
# Deploy to any Google Cloud project (excluding "gestor de reservaS")

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}===========================================${NC}"
echo -e "${BLUE}    CRM ETL System - Cloud Deployment    ${NC}"
echo -e "${BLUE}===========================================${NC}"
echo

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}ERROR: gcloud CLI is not installed${NC}"
    echo "Please install Google Cloud CLI: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Get current project
CURRENT_PROJECT=$(gcloud config get-value project 2>/dev/null || echo "")

if [[ -z "$CURRENT_PROJECT" ]]; then
    echo -e "${RED}ERROR: No Google Cloud project is configured${NC}"
    echo "Please run: gcloud config set project YOUR_PROJECT_ID"
    exit 1
fi

# Check if project is the restricted one
if [[ "$CURRENT_PROJECT" == "gestor de reservaS" ]]; then
    echo -e "${RED}ERROR: Cannot deploy to 'gestor de reservaS' project${NC}"
    echo "Please switch to a different project:"
    echo "gcloud config set project YOUR_OTHER_PROJECT_ID"
    exit 1
fi

echo -e "${GREEN}✅ Current project: ${CURRENT_PROJECT}${NC}"
echo

# Confirm deployment
read -p "Deploy CRM ETL System to project '${CURRENT_PROJECT}'? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}Deployment cancelled${NC}"
    exit 0
fi

echo -e "${BLUE}🚀 Starting deployment...${NC}"
echo

# Enable required APIs
echo -e "${YELLOW}📋 Enabling required Google Cloud APIs...${NC}"
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com
echo -e "${GREEN}✅ APIs enabled${NC}"
echo

# Build and deploy using Cloud Build
echo -e "${YELLOW}🏗️  Building and deploying with Cloud Build...${NC}"
gcloud builds submit \
    --config=backend/cloudbuild.yaml \
    --substitutions=_PROJECT_ID=${CURRENT_PROJECT} \
    .

if [[ $? -eq 0 ]]; then
    echo
    echo -e "${GREEN}🎉 Deployment successful!${NC}"
    echo
    
    # Get service URL
    SERVICE_URL=$(gcloud run services describe crm-etl-api --region=us-central1 --format='value(status.url)' 2>/dev/null || echo "")
    
    if [[ -n "$SERVICE_URL" ]]; then
        echo -e "${BLUE}🔗 Your CRM ETL API is available at:${NC}"
        echo -e "${GREEN}   ${SERVICE_URL}${NC}"
        echo
        echo -e "${BLUE}📚 API Documentation:${NC}"
        echo -e "${GREEN}   ${SERVICE_URL}/docs${NC}"
        echo
        echo -e "${BLUE}🔍 Health Check:${NC}"
        echo -e "${GREEN}   ${SERVICE_URL}/health${NC}"
    fi
    
    echo
    echo -e "${YELLOW}📝 Next steps:${NC}"
    echo "1. Configure environment variables if needed:"
    echo "   gcloud run services update crm-etl-api --region=us-central1 --set-env-vars KEY=VALUE"
    echo
    echo "2. Set up authentication if required:"
    echo "   gcloud run services update crm-etl-api --region=us-central1 --remove-flags allow-unauthenticated"
    echo
    echo "3. Monitor your service:"
    echo "   gcloud run services logs read crm-etl-api --region=us-central1"
    
else
    echo -e "${RED}❌ Deployment failed${NC}"
    echo "Check the build logs above for details"
    exit 1
fi