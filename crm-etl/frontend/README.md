# CRM Tools - Sistema ETL Inteligente

## 🚀 Ready for GCP Hosting

This is the static frontend for the CRM Tools ETL system, prepared for Google Cloud Platform hosting. The application provides a user-friendly interface for data processing and analysis.

### Features

- ✅ **Static Frontend**: Netlify-compatible static site
- ✅ **Responsive Design**: Works on all devices  
- ✅ **File Upload**: Support for CSV and Excel files
- ✅ **Real-time Progress**: Visual feedback during processing
- ✅ **CRM Branding**: Professional CRM ETL design
- ✅ **Simulated Processing**: Demo functionality without backend dependencies

### Demo Functionality

The frontend currently runs in **demo mode** with simulated data processing. It includes:

- File upload interface
- Configuration options
- Progress tracking
- Results visualization
- Export capabilities

### Technology Stack

- **HTML5**: Semantic markup
- **CSS3**: Modern styling with custom properties
- **Vanilla JavaScript**: No framework dependencies
- **XLSX.js**: Client-side Excel file processing

### Deployment

This site is prepared for Google Cloud Platform hosting:

1. **GCP Static Hosting**: Configured with `.gcloudignore`
2. **No build process** required (static files only)
3. **Backend URL placeholder**: Ready to connect to GCP backend
4. **Static assets optimized** for cloud storage
5. **Ready for App Engine** or **Cloud Storage** deployment

### Next Steps for Full Functionality

To connect this frontend to a working backend:

1. Deploy the Python backend (`BETA/backend/`) to Google Cloud Platform:
   - **App Engine**: Serverless Python runtime
   - **Cloud Run**: Containerized deployment
   - **Compute Engine**: Virtual machine deployment

2. Replace `{BACKEND_URL}` in the `BASE` constant with your GCP backend URL

3. Configure CORS settings in the backend to allow requests from your GCP frontend domain

---

**Powered by CRM ETL**  
*Transforming data into intelligent insights*