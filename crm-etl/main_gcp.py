#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=================================================
--- Main Entry Point for Google Cloud Deploy ---
=================================================

Main entry point for the CRM ETL system when deployed to Google Cloud.
This file ensures proper initialization and routing for the FastAPI application.
"""

import os
import sys
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

# Import the FastAPI app from backend
try:
    from backend.api_server import app
    print("✅ Successfully imported FastAPI app from backend.api_server")
except ImportError as e:
    print(f"❌ Failed to import FastAPI app: {e}")
    # Fallback: try to import from current directory
    try:
        from api_server import app
        print("✅ Successfully imported FastAPI app from api_server")
    except ImportError as e2:
        print(f"❌ Complete import failure: {e2}")
        sys.exit(1)

# Set environment variables for Google Cloud
os.environ.setdefault('ENVIRONMENT', 'production')
os.environ.setdefault('PORT', '8080')

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get('PORT', 8080))
    print(f"🚀 Starting CRM ETL API server on port {port}")
    uvicorn.run("main_gcp:app", host="0.0.0.0", port=port)