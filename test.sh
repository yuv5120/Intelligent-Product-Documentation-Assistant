#!/bin/bash

# Quick test script to verify the RAG system is working

echo "🧪 Testing RAG System..."
echo ""

# Activate virtual environment
source venv/bin/activate

# Run pytest
echo "Running tests..."
python -m pytest tests/ -v --tb=short

echo ""
echo "✅ Tests complete!"
