FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements-prod.txt .

# Install system dependencies
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Install dependencies
RUN pip install --no-cache-dir -r requirements-prod.txt

# Copy backend application
COPY backend/ /app/
COPY ferramenta_etl_ai_unificada.py /app/
COPY processador_dados_unificado.py /app/
COPY extractors/ /app/extractors/
COPY utils/ /app/utils/

# Copy frontend files
COPY index.html /app/static/
COPY frontend/ /app/static/frontend/
COPY www/ /app/static/www/

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD curl -f http://localhost:8080/health || exit 1

# Run the application
CMD ["uvicorn", "api_server:app", "--host", "0.0.0.0", "--port", "8080"]
