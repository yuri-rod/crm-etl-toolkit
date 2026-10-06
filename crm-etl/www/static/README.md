# Static Directory Structure

This directory contains all static assets for the CRM Tools web application.

## Directory Structure

```
static/
├── img/                              # Images and graphics
│   ├── crm-tools-logo-v02.png       # Header logo (placeholder)
│   ├── crm-logo.svg                 # Hero section logo (placeholder)
│   └── 24_02_2025_powered-by-crm-etl-02.png # Footer logo (placeholder)
├── index.html                       # Main HTML file with embedded CSS/JS
└── README.md                        # This file
```

## Changes Made

1. **Created static/ directory structure**
   - Main `static/` directory for all static assets
   - `static/img/` subdirectory for images

2. **Moved index.html to static/**
   - Copied original `index.html` to `static/index.html`
   - All CSS and JavaScript are embedded in the HTML file

3. **Updated image paths in HTML**
   - Changed all image references to use absolute paths starting with `/static/img/`
   - Header logo: `/static/img/crm-tools-logo-v02.png`
   - Hero logo: `/static/img/crm-logo.svg`  
   - Footer logo: `/static/img/24_02_2025_powered-by-crm-etl-02.png`

## Image Files Needed

The following image files are referenced in the HTML but were not found in the original directory structure. You will need to add these files to `static/img/`:

- `crm-tools-logo-v02.png` - Header navigation logo
- `crm-logo.svg` - Hero section logo 
- `24_02_2025_powered-by-crm-etl-02.png` - Footer branding image

## Production URLs

With this structure, all static assets will be served with predictable URLs in production:

- HTML: `/static/index.html`
- Images: `/static/img/[filename]`

The absolute path structure (`/static/...`) ensures that all assets load correctly regardless of the server configuration or deployment environment.
