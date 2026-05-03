FROM python:3.11-slim

WORKDIR /app

# System deps (needed for some ML libraries)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies first (better layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY src/ ./src/
COPY .env.example .env

# Create ChromaDB directory
RUN mkdir -p /app/chroma_db

EXPOSE 8000

# Use exec form so signals are received properly
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
