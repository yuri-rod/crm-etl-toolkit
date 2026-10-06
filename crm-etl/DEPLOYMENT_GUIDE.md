# 🚀 CRM Tools - Deployment Guide

## Overview

This project consists of two main parts:

1. **Frontend (Static)** - Ready for Netlify deployment (`netlify-deploy/`)
2. **Backend (Server)** - Requires server hosting (`BETA/backend/`)

## 📱 Frontend Deployment (Netlify)

### ✅ Ready to Deploy

The `netlify-deploy/` folder contains everything needed for Netlify:

```
netlify-deploy/
├── index.html                 # Main application
├── crm-logo.svg              # Logo file  
├── *.png                     # Brand images
├── _redirects                # SPA redirect rules
├── netlify.toml              # Netlify configuration
└── README.md                 # Documentation
```

### Deployment Steps

1. **Connect to Netlify:**
   - Go to [netlify.com](https://netlify.com)
   - Click "Add new site" → "Import an existing project"
   - Connect your Git repository

2. **Configure Build Settings:**
   - Build command: `echo 'Static site - no build required'`
   - Publish directory: `netlify-deploy`
   - No environment variables needed

3. **Deploy:**
   - Netlify will automatically deploy
   - Your site will be available at `https://your-site-name.netlify.app`

### Current Functionality

The frontend currently runs in **demo mode** with:
- ✅ File upload interface
- ✅ Simulated data processing
- ✅ Progress tracking
- ✅ Results visualization
- ✅ Professional CRM branding

## 🖥️ Backend Deployment (Optional)

### Backend Components (`BETA/backend/`)

- `api_server.py` - FastAPI REST API
- `unificado.py` - Main ETL pipeline
- `ai_rule_generator.py` - AI-powered rule generation
- `simple_inference.py` - ML prediction system

### Recommended Platforms

1. **Railway** (Recommended)
   - Easy Python deployment
   - Automatic HTTPS
   - Good free tier

2. **Render**
   - Simple setup
   - Automatic deployments
   - Free tier available

3. **Heroku**
   - Established platform
   - Many integrations
   - Paid tiers only now

### Backend Requirements

```bash
# Core dependencies
pip install fastapi uvicorn pandas numpy scikit-learn

# Optional AI features
pip install anthropic openai transformers
```

### Environment Variables

```bash
ANTHROPIC_API_KEY=your_claude_key
OPENAI_API_KEY=your_openai_key
```

## 🔗 Connecting Frontend to Backend

Once your backend is deployed:

1. **Update API endpoints** in `netlify-deploy/index.html`:
   ```javascript
   // Replace this line:
   await simulateProcessing();
   
   // With actual API calls:
   const response = await fetch('https://your-backend.railway.app/api/process', {
       method: 'POST',
       headers: {'Content-Type': 'application/json'},
       body: JSON.stringify(formData)
   });
   ```

2. **Configure CORS** in your backend to allow requests from your Netlify domain

## 🗂️ Files Removed for Deployment

The following were removed/excluded for clean deployment:

### Unnecessary Files
- ✅ `temp_qualificadora.html` - Temporary demo file
- ✅ `*.pyc` files - Python cache files  
- ✅ `__pycache__/` directories - Python cache
- ✅ Large documentation files - Kept only essential docs
- ✅ Test files - Kept in main project, not in deployment

### What Was Kept
- ✅ Essential frontend files (`index.html`, images, etc.)
- ✅ Netlify configuration files
- ✅ Brand assets (logos, images)
- ✅ Documentation (README.md, this guide)

## ⚡ Quick Start

### For Static Demo (Netlify Only)
1. Upload `netlify-deploy/` folder to Netlify
2. Done! Your demo is live

### For Full Functionality
1. Deploy frontend to Netlify (as above)
2. Deploy `BETA/backend/` to Railway/Render
3. Update frontend API endpoints
4. Configure environment variables

## 🔧 Development vs Production

### Development
- Run full project locally with Python backend
- Use `python BETA/backend/api_server.py`
- Frontend connects to `localhost:8000`

### Production
- Frontend on Netlify (static)
- Backend on Railway/Render (server)
- Frontend connects to backend API URL

## 📊 Project Structure Summary

```
TODOSETL/
├── netlify-deploy/           # ✅ Ready for Netlify
│   ├── index.html
│   ├── *.png, *.svg
│   ├── _redirects
│   └── netlify.toml
├── BETA/backend/            # 🖥️ Server deployment needed
│   ├── api_server.py
│   ├── unificado.py
│   └── ai_rule_generator.py
├── ETL-main/                # 📚 Core ETL system
├── documentation/           # 📖 Project docs
└── DEPLOYMENT_GUIDE.md      # 📋 This file
```

---

**🎯 Result**: Professional, deployment-ready ETL system with modern architecture!

**Powered by CRM ETL**