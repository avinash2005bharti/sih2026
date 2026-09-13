# Sovereign AI Services - FastAPI Backend

Production-ready Python AI Services for the Sovereign On-Premise Agentic AI Workbench.

## Quick Start

### Prerequisites
- Python 3.10+
- Ollama running on `http://localhost:11434`
  - qwen3:4b (chat/reasoning)
  - qwen2.5-coder:3b (coding)
  - qwen2.5vl:3b (vision)
  - nomic-embed-text:latest (embeddings)

### Installation
```bash
cd AI-SERVICES
pip install -r requirements.txt
```

### Run
```bash
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Visit `http://localhost:8000/docs` for interactive API documentation.

## Architecture

### Phase 1: Chat & Model Routing ✅
- `/health` - Service health
- `/api/models` - List models
- `/api/chat` - Chat responses
- `/api/chat/stream` - Streaming responses

### Phase 2: Vision & RAG ✅
- `/api/vision/*` - Image analysis, OCR, classification
- `/api/documents` - Document indexing
- `/api/documents/search` - RAG search
- `/api/documents/rag-status` - RAG system status

### Phase 3: Agents ✅
- `BaseAgent` - Base agent class
- `DocumentAgent` - Document analysis
- `MaintenanceAgent` - Maintenance analysis
- `SafetyAgent` - Safety analysis
- `ComplianceAgent` - Compliance checking
- `RiskAgent` - Risk assessment
- `ReportingAgent` - Report generation

## Configuration

Edit `.env` for configuration:
```ini
# Ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_CHAT_MODEL=qwen3:4b
OLLAMA_CODE_MODEL=qwen2.5-coder:3b
OLLAMA_VISION_MODEL=qwen2.5vl:3b
OLLAMA_EMBED_MODEL=nomic-embed-text:latest

# Qdrant (Vector DB for RAG)
QDRANT_URL=http://localhost:6333
QDRANT_COLLECTION=sovereign_documents
QDRANT_VECTOR_SIZE=768

# Service
HOST=0.0.0.0
PORT=8000
LOG_LEVEL=INFO
```

## Test Endpoints

### Health Check
```bash
curl http://localhost:8000/health
```

### Chat
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"Hello!","model":"auto","task_type":"chat"}'
```

### List Models
```bash
curl http://localhost:8000/api/models
```

### Document Search (RAG)
```bash
curl -X POST http://localhost:8000/api/documents/search \
  -H "Content-Type: application/json" \
  -d '{"query":"your search here","top_k":5}'
```

### Image Analysis
```bash
curl -X POST http://localhost:8000/api/vision/analyze \
  -H "Content-Type: application/json" \
  -d '{"image":"<base64-image>","prompt":"What is in this image?"}'
```

## Integration with Node.js

The FastAPI service is designed to be called from the Node.js backend:

```javascript
// Example: Chat endpoint
const response = await fetch('http://localhost:8000/api/chat', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    message: "Write Python code",
    model: "auto",
    task_type: "coding"
  })
});
const data = await response.json();
```

## Docker Deployment

Services are Docker-ready. Use docker-compose:
```yaml
services:
  ai-service:
    build: ./AI-SERVICES
    ports:
      - "8000:8000"
    environment:
      OLLAMA_BASE_URL: http://ollama:11434
      QDRANT_URL: http://qdrant:6333
    depends_on:
      - ollama
      - qdrant
```

## Key Features

✅ **Sovereign AI** - Local LLM inference via Ollama  
✅ **Zero External APIs** - No cloud dependencies  
✅ **Intelligent Routing** - Auto-selects best model  
✅ **Token Streaming** - Real-time response streaming  
✅ **Vision Support** - Image analysis with qwen2.5vl  
✅ **RAG Pipeline** - Document search with embeddings  
✅ **Agent Framework** - Extensible specialized agents  
✅ **Production Ready** - Type hints, async, error handling  

## File Structure

```
AI-SERVICES/
├── main.py                 # FastAPI app entry
├── requirements.txt        # Python dependencies
├── .env                    # Configuration
│
├── api/
│   └── routes/
│       ├── health.py       # Health endpoint
│       ├── chat.py         # Chat endpoints
│       ├── models.py       # Model listing
│       ├── documents.py    # RAG endpoints
│       └── vision.py       # Vision endpoints
│
├── core/
│   ├── config.py           # Settings
│   └── logging.py          # Logger setup
│
├── llm/
│   ├── ollama_client.py    # Ollama HTTP client
│   ├── model_registry.py   # Model configuration
│   └── model_router.py     # Intelligent routing
│
├── rag/
│   ├── embeddings.py       # Embeddings service
│   ├── qdrant_client.py    # Vector DB client
│   └── retriever.py        # RAG pipeline
│
├── multimodal/
│   └── vision.py           # Vision service
│
└── agents/
    ├── base_agent.py       # Base agent class
    └── document_agent.py   # Specialized agents
```

## Limitations & Next Steps

### Current
- ✅ Chat with model routing
- ✅ Streaming responses
- ✅ Vision/multimodal
- ✅ RAG with Qdrant
- ✅ Agent framework

### Future (Phase 4+)
- LangGraph workflow orchestration
- Tool execution framework
- Valkey background tasks
- Neo4j knowledge graphs
- Mem0AI memory system

## Support

- Check service health: `GET /health`
- View API docs: `http://localhost:8000/docs`
- Check logs in terminal output
- Verify Ollama running: `http://localhost:11434/api/tags`
- Verify Qdrant running: `http://localhost:6333/health` (optional)

---

**See `IMPLEMENTATION_SUMMARY.md` for detailed technical documentation.**
