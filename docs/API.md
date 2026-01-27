# API Documentation

## Base URL

```
http://localhost:8000
```

## Authentication

Currently, no authentication is required. For production use, implement API key authentication.

## Endpoints

### 1. Root Endpoint

**GET** `/`

Get basic API information.

**Response:**
```json
{
  "message": "Intelligent Product Documentation Assistant API",
  "docs": "/docs",
  "health": "/health"
}
```

---

### 2. Health Check

**GET** `/health`

Check service health and get statistics.

**Response:**
```json
{
  "status": "healthy",
  "model_type": "openai",
  "total_documents": 150
}
```

---

### 3. Upload Document

**POST** `/upload`

Upload and index a document.

**Request:**
- Content-Type: `multipart/form-data`
- Body: File upload

**Supported Formats:**
- PDF (`.pdf`)
- HTML (`.html`, `.htm`)
- Markdown (`.md`, `.markdown`)
- Word (`.docx`)
- Text (`.txt`)

**Example:**
```bash
curl -X POST "http://localhost:8000/upload" \
  -F "file=@/path/to/document.pdf"
```

**Response:**
```json
{
  "message": "Document uploaded and indexed successfully",
  "filename": "document.pdf",
  "chunks_created": 25,
  "total_documents": 175
}
```

**Error Responses:**
- `400`: Unsupported file format or empty document
- `500`: Server error during processing

---

### 4. Query Documents

**POST** `/query`

Ask a question and get an AI-generated answer with sources.

**Request Body:**
```json
{
  "query": "How do I reset my device?",
  "session_id": "user123",
  "top_k": 20,
  "top_n": 5
}
```

**Parameters:**
- `query` (required): The question to ask
- `session_id` (optional): Session ID for conversation tracking (default: "default")
- `top_k` (optional): Number of initial candidates (default: from config)
- `top_n` (optional): Number of documents after reranking (default: from config)

**Response:**
```json
{
  "answer": "To reset your device to factory settings: 1) Go to Settings > System > Advanced...",
  "sources": [
    "[1] user_manual.pdf (section 12)",
    "[2] faq.md (section 3)"
  ],
  "context_used": 2,
  "session_id": "user123"
}
```

**Error Responses:**
- `400`: No documents in database or invalid request
- `500`: Server error during query processing

---

### 5. Clear Database

**DELETE** `/clear`

Remove all documents from the vector database.

⚠️ **Warning:** This action cannot be undone!

**Example:**
```bash
curl -X DELETE "http://localhost:8000/clear"
```

**Response:**
```json
{
  "message": "Database cleared successfully",
  "documents_removed": 175
}
```

---

### 6. List Sessions

**GET** `/sessions`

Get list of active conversation sessions.

**Response:**
```json
{
  "active_sessions": ["user123", "user456", "default"],
  "total_sessions": 3
}
```

---

### 7. Clear Session

**DELETE** `/sessions/{session_id}`

Clear conversation history for a specific session.

**Example:**
```bash
curl -X DELETE "http://localhost:8000/sessions/user123"
```

**Response:**
```json
{
  "message": "Session user123 cleared"
}
```

---

## Usage Examples

### Python

```python
import requests

# Upload document
with open("manual.pdf", "rb") as f:
    response = requests.post(
        "http://localhost:8000/upload",
        files={"file": f}
    )
    print(response.json())

# Query
response = requests.post(
    "http://localhost:8000/query",
    json={
        "query": "What is the warranty period?",
        "session_id": "python_client"
    }
)
print(response.json()["answer"])
```

### JavaScript (Node.js)

```javascript
const FormData = require('form-data');
const fs = require('fs');
const axios = require('axios');

// Upload document
const form = new FormData();
form.append('file', fs.createReadStream('manual.pdf'));

axios.post('http://localhost:8000/upload', form, {
  headers: form.getHeaders()
})
.then(response => console.log(response.data));

// Query
axios.post('http://localhost:8000/query', {
  query: 'What is the warranty period?',
  session_id: 'js_client'
})
.then(response => console.log(response.data.answer));
```

### cURL

```bash
# Upload
curl -X POST "http://localhost:8000/upload" \
  -F "file=@manual.pdf"

# Query
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "What is the warranty period?", "session_id": "curl_client"}'

# Health check
curl "http://localhost:8000/health"

# Clear database
curl -X DELETE "http://localhost:8000/clear"
```

---

## Interactive Documentation

Visit `http://localhost:8000/docs` for interactive Swagger UI documentation where you can:
- Test all endpoints directly in the browser
- See detailed request/response schemas
- Download OpenAPI specification

Alternative documentation available at `http://localhost:8000/redoc`.

---

## Rate Limiting

Currently, no rate limiting is implemented. For production use, consider adding:
- Request rate limiting per IP/session
- File size limits for uploads
- Query complexity limits

---

## Best Practices

1. **Session Management**: Use unique session IDs for different users
2. **Error Handling**: Always check response status codes
3. **File Validation**: Validate file types before uploading
4. **Query Optimization**: Use specific questions for better results
5. **Batch Operations**: Upload multiple documents separately for better tracking

---

## WebSocket Support (Future)

Real-time query streaming is planned for future releases:
```javascript
// Future feature
const ws = new WebSocket('ws://localhost:8000/ws/query');
ws.send(JSON.stringify({query: "How do I..."}));
ws.onmessage = (event) => {
  console.log('Streaming response:', event.data);
};
```
