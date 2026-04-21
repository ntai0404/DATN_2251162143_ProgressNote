FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for PyMuPDF
RUN apt-get update && apt-get install -y \
    libmupdf-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (layer cache optimization)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install playwright && playwright install chromium --with-deps

# Copy source code
COPY collector_agent/ ./collector_agent/
COPY search-agent/ ./search-agent/
COPY mq_worker.py .

# Default: run the batch harvester
CMD ["python", "collector_agent/batch_collector.py"]
