#!/usr/bin/env python3
"""
Quick demo script to test the RAG system.
Uploads sample documents and runs test queries.
"""

import requests
import time
from pathlib import Path

BASE_URL = "http://localhost:8000"

def check_health():
    """Check if server is running."""
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            print("✅ Server is healthy")
            print(f"   {response.json()}")
            return True
    except requests.exceptions.ConnectionError:
        print("❌ Server is not running. Start it with: ./start.sh")
        return False

def upload_sample_docs():
    """Upload sample documentation."""
    print("\n📤 Uploading sample documents...")
    
    sample_files = [
        "sample_docs/product_manual.md",
        "sample_docs/faq.md"
    ]
    
    for file_path in sample_files:
        path = Path(file_path)
        if not path.exists():
            print(f"   ⚠️  File not found: {file_path}")
            continue
        
        with open(path, "rb") as f:
            files = {"file": (path.name, f, "text/markdown")}
            response = requests.post(f"{BASE_URL}/upload", files=files)
            
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ {path.name}: {data['chunks_created']} chunks")
            else:
                print(f"   ❌ Failed to upload {path.name}")

def run_test_queries():
    """Run test queries."""
    print("\n🔍 Running test queries...\n")
    
    queries = [
        "What is the warranty period?",
        "How do I reset my device?",
        "What connectivity options are available?",
        "How long does the battery last?"
    ]
    
    for query in queries:
        print(f"Q: {query}")
        
        response = requests.post(
            f"{BASE_URL}/query",
            json={"query": query, "session_id": "demo"}
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"A: {data['answer'][:200]}...")
            print(f"   Sources: {', '.join(data['sources'][:2])}")
        else:
            print(f"   ❌ Query failed: {response.status_code}")
        
        print()
        time.sleep(1)

def main():
    """Run the demo."""
    print("🤖 RAG System Demo\n")
    print("=" * 60)
    
    if not check_health():
        return
    
    upload_sample_docs()
    run_test_queries()
    
    print("=" * 60)
    print("\n✨ Demo complete!")
    print("\n📚 Try the interactive API docs at: http://localhost:8000/docs")

if __name__ == "__main__":
    main()
