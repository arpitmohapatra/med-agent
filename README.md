# MedQuery MVP

A professional multi-mode LLM agent application for medical knowledge queries.

## Features

- **Ask Mode**: General chat with OpenAI/Azure OpenAI
- **RAG Mode**: Query against 250k medicines dataset with Elasticsearch
- **Agent Mode**: Tool use via Model Context Protocol (MCP)
- **JWT Authentication**: Secure user management
- **Professional UI**: Clean React frontend with Tailwind CSS

## Architecture

### Backend (FastAPI)
- JWT authentication
- Provider routing (OpenAI/Azure OpenAI)
- Elasticsearch vector database
- MCP server integration
- RESTful API endpoints

### Frontend (React + TypeScript)
- Modern chat interface
- Mode switching (Ask/RAG/Agent)
- Real-time streaming responses
- Settings management
- Mobile responsive design

### Data Pipeline
- Kaggle medicines dataset ingestion
- Text chunking and embedding
- Elasticsearch indexing
- Evaluation harness

## Quick Start

### Backend Setup
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

### Frontend Setup
```bash
cd frontend
npm install
npm start
```

### Data Ingestion
```bash
cd backend
python scripts/ingest_data.py
```

## API Endpoints

- `POST /auth/register` - User registration
- `POST /auth/login` - User login
- `POST /api/chat` - Multi-mode chat
- `POST /api/rag/index` - Index documents
- `GET /api/rag/search` - Search documents
- `POST /api/mcp/register` - Register MCP server
- `GET /api/mcp/list` - List MCP servers

## Configuration

Set environment variables:
```bash
OPENAI_API_KEY=your_key
AZURE_OPENAI_ENDPOINT=your_endpoint
ELASTICSEARCH_URL=http://localhost:9200
JWT_SECRET_KEY=your_secret
```

## Guardrails

- All medical responses include "Not medical advice" disclaimer
- RAG answers show explicit sources
- No hallucinated citations
- Fallback responses for insufficient data
