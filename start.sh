#!/bin/bash

# Startup script for the RAG system

echo "🚀 Starting Intelligent Product Documentation Assistant..."

# Activate virtual environment
source venv/bin/activate

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  No .env file found. Creating from template..."
    cp .env.example .env
    echo "✅ Created .env file. Please edit it to add your OpenAI API key if needed."
fi

# Start the server
echo "🌐 Starting FastAPI server on http://localhost:8000"
echo "📚 API Documentation: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

python -m uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
