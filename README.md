# Intelligent Product Documentation Assistant 🤖📚

A powerful RAG (Retrieval-Augmented Generation) system that answers customer questions about product documentation, user manuals, and FAQs using semantic search and AI.

## ✨ Features

- **Multi-Format Support**: Parse PDF, HTML, Markdown, DOCX, and TXT files
- **Semantic Search**: Find relevant information using sentence transformers
- **Smart Reranking**: Cross-encoder reranking for improved accuracy
- **Source Citations**: Every answer includes source references
- **Conversational Memory**: Handles follow-up questions with context
- **Free Tier Friendly**: Uses ChromaDB (local) and free LLM options
- **REST API**: FastAPI backend with comprehensive endpoints
- **Easy Setup**: Simple installation and configuration

## 🏗️ Architecture

```
User Query → FastAPI → Retriever → ChromaDB (Vector Search)
                ↓                        ↓
            Generator ← Reranker ← Top-K Documents
                ↓
         Answer + Citations
```

**Components:**
- **Document Processing**: Parses and chunks documents intelligently
- **Embeddings**: `sentence-transformers/all-MiniLM-L6-v2` (local, free)
- **Vector Database**: ChromaDB (persistent, local storage)
- **Retrieval**: Semantic search with cross-encoder reranking
- **LLM**: OpenAI GPT-3.5 (free tier) or Ollama (completely local)
- **API**: FastAPI with automatic documentation

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- pip package manager
- (Optional) OpenAI API key for GPT-3.5
- (Optional) Ollama for local LLM

### Installation

1. **Clone or navigate to the project directory**:
```bash

```

2. **Create and activate a virtual environment**:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**:
```bash
pip install -r requirements.txt
```

4. **Configure environment variables**:
```bash
cp .env.example .env
# Edit .env and add your OpenAI API key (optional)
```

### Running the Server

**Start the FastAPI server**:
```bash
python -m uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:
- **API**: http://localhost:8000
- **Interactive Docs**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc

## 📖 Usage

### 1. Upload Documents

Upload your product documentation:

```bash
curl -X POST "http://localhost:8000/upload" \
  -F "file=@sample_docs/product_manual.md"
```

**Response**:
```json
{
  "message": "Document uploaded and indexed successfully",
  "filename": "product_manual.md",
  "chunks_created": 45,
  "total_documents": 45
}
```

### 2. Query the System

Ask questions about your documentation:

```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "How do I reset my device?",
    "session_id": "user123"
  }'
```

**Response**:
```json
{
  "answer": "To reset your device to factory settings: 1) Go to Settings > System > Advanced, 2) Scroll down to 'Factory Reset', 3) Enter your PIN if prompted, 4) Confirm the reset, 5) The device will restart and erase all data. Warning: Factory reset will delete all your data, so back up important information first.",
  "sources": [
    "[1] faq.md (section 3)",
    "[2] product_manual.md (section 8)"
  ],
  "context_used": 2,
  "session_id": "user123"
}
```

### 3. Follow-up Questions

The system maintains conversation context:

```bash
# First question
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "What is the warranty period?", "session_id": "user123"}'

# Follow-up question (uses context)
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "What does it cover?", "session_id": "user123"}'
```

### 4. Health Check

Check system status:

```bash
curl http://localhost:8000/health
```

### 5. Clear Database

Remove all indexed documents:

```bash
curl -X DELETE "http://localhost:8000/clear"
```

## 🔧 Configuration

Edit `.env` file to customize settings:

```env
# LLM Configuration
MODEL_TYPE=openai              # Options: openai, ollama
OPENAI_API_KEY=sk-...         # Your OpenAI API key

# ChromaDB
CHROMA_PERSIST_DIR=./chroma_db

# Embedding Model
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

# Retrieval Parameters
CHUNK_SIZE=512                 # Characters per chunk
CHUNK_OVERLAP=50              # Overlap between chunks
TOP_K_RETRIEVAL=20            # Initial candidates
TOP_N_RERANK=5                # Final results after reranking

# Server
HOST=0.0.0.0
PORT=8000
```

## 🧪 Testing

Run the test suite:

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_rag_pipeline.py -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html
```

## 📁 Project Structure

```
Intelligent-Product-Documentation-Assistant/
├── src/
│   ├── api/                    # FastAPI application
│   │   ├── main.py            # API endpoints
│   │   └── models.py          # Pydantic models
│   ├── document_processor/     # Document parsing
│   │   ├── parser.py          # Multi-format parser
│   │   └── chunker.py         # Text chunking
│   ├── embeddings/            # Embedding generation
│   │   └── embedding_model.py
│   ├── vector_db/             # Vector database
│   │   └── chroma_client.py
│   ├── rag/                   # RAG pipeline
│   │   ├── retriever.py       # Semantic search + reranking
│   │   ├── generator.py       # LLM answer generation
│   │   └── conversation_memory.py
│   ├── utils/                 # Utilities
│   │   └── logger.py
│   └── config.py              # Configuration
├── tests/                     # Test suite
│   ├── test_rag_pipeline.py
│   └── test_api.py
├── sample_docs/               # Sample documentation
│   ├── product_manual.md
│   └── faq.md
├── requirements.txt           # Python dependencies
├── .env.example              # Environment template
└── README.md                 # This file
```

## 🌟 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Root endpoint |
| GET | `/health` | Health check |
| POST | `/upload` | Upload document |
| POST | `/query` | Ask question |
| DELETE | `/clear` | Clear database |
| GET | `/sessions` | List active sessions |
| DELETE | `/sessions/{id}` | Clear session |

Full API documentation available at `/docs` when server is running.

## 🔄 Using Ollama (Local LLM)

For completely free, local operation:

1. **Install Ollama**:
```bash
# macOS
brew install ollama

# Linux
curl https://ollama.ai/install.sh | sh
```

2. **Start Ollama**:
```bash
ollama serve
```

3. **Pull a model**:
```bash
ollama pull llama2
```

4. **Update `.env`**:
```env
MODEL_TYPE=ollama
```

## 💡 Tips for Best Results

1. **Document Quality**: Upload well-structured documentation with clear headings
2. **Chunk Size**: Adjust `CHUNK_SIZE` based on your document structure (default: 512)
3. **Retrieval Tuning**: Increase `TOP_K_RETRIEVAL` for better recall, `TOP_N_RERANK` for precision
4. **Session Management**: Use unique session IDs for different users/conversations
5. **Regular Updates**: Keep your documentation up-to-date by re-uploading modified files

## 🐛 Troubleshooting

### Issue: "No OpenAI API key found"

**Solution**: Set your API key in `.env`:
```env
OPENAI_API_KEY=sk-your-key-here
```

Or use Ollama for local operation.

### Issue: "ChromaDB connection error"

**Solution**: Ensure the persist directory exists and has write permissions:
```bash
mkdir -p chroma_db
chmod 755 chroma_db
```

### Issue: "Model download fails"

**Solution**: Check your internet connection. Models are downloaded on first use:
- Embedding model: ~80MB
- Reranking model: ~120MB

### Issue: "Slow query responses"

**Solutions**:
- Reduce `TOP_K_RETRIEVAL` and `TOP_N_RERANK`
- Use a smaller embedding model
- Enable GPU acceleration (if available)

## 📊 Performance

- **Document Upload**: ~1-2 seconds per document
- **Query Response**: ~2-5 seconds (including LLM generation)
- **Memory Usage**: ~500MB (base) + ~100MB per 1000 documents
- **Storage**: ~1KB per document chunk

## 🤝 Contributing

Contributions are welcome! Areas for improvement:

- [ ] Add support for more document formats (EPUB, RTF)
- [ ] Implement document versioning
- [ ] Add multilingual support
- [ ] Create web UI frontend
- [ ] Add analytics dashboard
- [ ] Implement user authentication

## 📄 License

This project is open source and available under the MIT License.

## 🙏 Acknowledgments

Built with:
- [FastAPI](https://fastapi.tiangolo.com/) - Web framework
- [ChromaDB](https://www.trychroma.com/) - Vector database
- [Sentence Transformers](https://www.sbert.net/) - Embeddings
- [OpenAI](https://openai.com/) - LLM (optional)
- [Ollama](https://ollama.ai/) - Local LLM (optional)

## 📞 Support

For questions or issues:
- Open an issue on GitHub
- Check the `/docs` endpoint for API documentation
- Review sample documents in `sample_docs/`

---

**Made with ❤️ for better customer support**
