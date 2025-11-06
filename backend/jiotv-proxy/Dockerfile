FROM python:3.10-slim

LABEL maintainer="JioTV Proxy Service"
LABEL description="FastAPI-based proxy for JioTV streaming"

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    git \
    && rm -rf /var/lib/apt/lists/*

# Clone JioTV-Proxy repository
RUN git clone https://github.com/henry-richard7/JioTV-Proxy.git /app

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health', timeout=5)"

# Run the application
CMD ["python", "main.py"]
