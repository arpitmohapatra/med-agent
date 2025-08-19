# MedQuery MVP

A professional multi-mode LLM agent application for medical knowledge queries, built with FastAPI, React, and Elasticsearch.

## 🏥 Features

### Core Capabilities
- **Ask Mode**: General medical knowledge chat with AI
- **RAG Mode**: Query against 250k medicines dataset with source citations
- **Agent Mode**: AI agent with tool access via Model Context Protocol (MCP)

### Technical Features
- **JWT Authentication**: Secure user management
- **Streaming Responses**: Real-time chat experience
- **Vector Search**: Semantic search with Elasticsearch
- **Professional UI**: Clean React frontend with Tailwind CSS
- **Multi-Provider**: Support for OpenAI and Azure OpenAI
- **Docker Ready**: Complete containerization support

## 🚀 Quick Start

### Option 1: Automated Setup (Recommended)
```bash
# Clone and setup everything automatically
./quick-start.sh
```

### Option 2: Manual Setup
```bash
# Install dependencies
make setup

# Start Elasticsearch (Docker)
docker-compose up -d elasticsearch

# Start development servers
make start-dev

# Or start individually
make start-backend  # Terminal 1
make start-frontend # Terminal 2
```

### Option 3: Docker Compose
```bash
# Start full stack with Docker
make docker-full

# Or just Elasticsearch
make docker-dev
```

## 📋 Prerequisites

- **Python 3.8+** for backend
- **Node.js 16+** for frontend  
- **Elasticsearch 8.x** for vector storage
- **OpenAI API Key** or **Azure OpenAI** credentials

## 🔧 Configuration

1. **Copy environment template:**
   ```bash
   cp backend/env.example backend/.env
   ```

2. **Update configuration:**
   ```bash
   # Required: Add your API keys
   OPENAI_API_KEY=your-openai-key
   
   # Or for Azure OpenAI
   AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
   AZURE_OPENAI_API_KEY=your-azure-key
   
   # Optional: Customize other settings
   ELASTICSEARCH_URL=http://localhost:9200
   JWT_SECRET_KEY=your-secret-key
   ```

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   React Frontend │    │  FastAPI Backend │    │  Elasticsearch  │
│                 │    │                 │    │                 │
│ • Chat UI       │───▶│ • Authentication │───▶│ • Vector Store  │
│ • Mode Switching│    │ • Chat API      │    │ • Full-text     │
│ • Source Cards  │    │ • RAG Pipeline  │    │ • Search        │
│ • Settings      │    │ • MCP Integration│    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │   OpenAI API    │
                       │                 │
                       │ • GPT-4         │
                       │ • Embeddings    │
                       │ • Function Call │
                       └─────────────────┘
```

## 📊 Data Pipeline

1. **Medicine Dataset**: 248k medicines with comprehensive metadata
2. **Rich Information**: Names, uses, side effects, substitutes, drug classes
3. **Text Processing**: Extract and structure medicine information
4. **Embeddings**: Generate vectors with text-embedding-3-small
5. **Indexing**: Store in Elasticsearch with full metadata
6. **Retrieval**: Semantic search for relevant context

### Ingest Data
```bash
# Quick test with 1000 records
make ingest-dataset-test

# Full dataset (248k records - takes ~30 minutes)
make ingest-dataset

# Sample data (for development)
make ingest-sample

# Custom CSV file
cd backend && python scripts/ingest_medicine_dataset.py --csv path/to/your.csv
```

### Dataset Structure
Your `medicine_dataset.csv` contains:
- **Basic Info**: ID, name, chemical/therapeutic classes
- **Medical Uses**: Up to 5 different use cases
- **Side Effects**: Up to 42 documented side effects  
- **Substitutes**: Up to 5 alternative medicines
- **Safety**: Habit forming warnings
- **Classification**: Action class, therapeutic class

## 🧪 Evaluation

Run the evaluation suite to test RAG performance:

```bash
# Full evaluation
cd backend && python scripts/evaluate.py

# Single query test
cd backend && python scripts/evaluate.py --query "What are the side effects of Paracetamol?"
```

**Success Criteria:**
- ✅ Success Rate ≥ 90%
- ✅ Quality Score ≥ 0.7
- ✅ Top-3 relevant results
- ✅ Medical disclaimer present

## 🛡️ Guardrails & Safety

- **Medical Disclaimer**: All responses include "Not medical advice" warning
- **Source Citations**: RAG mode shows explicit source references
- **No Hallucinations**: Responses based only on retrieved context
- **Fallback Handling**: Clear messages when insufficient data available

## 🔌 API Endpoints

### Authentication
- `POST /auth/register` - User registration
- `POST /auth/login` - User login  
- `GET /auth/me` - Current user info

### Chat
- `POST /api/chat` - Multi-mode chat with streaming

### RAG
- `POST /api/rag/index` - Index documents
- `GET /api/rag/search` - Search documents
- `GET /api/rag/stats` - Index statistics

### MCP (Model Context Protocol)
- `POST /api/mcp/register` - Register MCP server
- `GET /api/mcp/servers` - List servers
- `GET /api/mcp/tools` - Available tools

## 🧑‍💻 Development

### Available Commands
```bash
make help          # Show all commands
make setup         # Complete project setup
make start-dev     # Start development servers
make test          # Run tests
make lint          # Run linters
make format        # Format code
make clean         # Clean build artifacts
```

### Demo Credentials
- **Username**: `demo`
- **Password**: `password123`

### Project Structure
```
med-agent/
├── backend/           # FastAPI application
│   ├── app/          # Main application code
│   ├── scripts/      # Data processing scripts
│   └── requirements.txt
├── frontend/         # React application
│   ├── src/         # Source code
│   ├── public/      # Static assets
│   └── package.json
├── docker-compose.yml # Docker services
├── Makefile          # Development commands
└── quick-start.sh    # Automated setup
```

## 🐳 Docker Deployment

### Development
```bash
# Start Elasticsearch only
docker-compose up elasticsearch

# With Kibana for ES management
docker-compose --profile kibana up
```

### Production
```bash
# Full stack deployment
docker-compose --profile full-stack up --build

# Scale services
docker-compose --profile full-stack up --scale backend=3
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. Submit a pull request

## 📚 Documentation

- **API Documentation**: http://localhost:8000/docs (when running)
- **Frontend Storybook**: `cd frontend && npm run storybook`
- **Architecture Decisions**: `/docs/adr/`

## 🐛 Troubleshooting

### Common Issues

**Elasticsearch Connection Failed**
```bash
# Check if Elasticsearch is running
curl http://localhost:9200

# Start with Docker
docker-compose up -d elasticsearch
```

**OpenAI API Errors**
```bash
# Verify API key is set
echo $OPENAI_API_KEY

# Check rate limits and billing
```

**Frontend Won't Start**
```bash
# Clear node modules and reinstall
cd frontend && rm -rf node_modules && npm install
```

### Logs
```bash
# Backend logs
cd backend && tail -f app.log

# Frontend logs
cd frontend && npm start

# Docker logs
docker-compose logs -f
```

## 📈 Roadmap

### MVP ✅
- [x] Multi-mode chat (Ask/RAG/Agent)
- [x] JWT authentication
- [x] Elasticsearch integration
- [x] Medicine dataset RAG
- [x] React frontend
- [x] Docker support

### Future Enhancements
- [ ] Role-based access control
- [ ] Conversation history
- [ ] Advanced MCP tools
- [ ] Fine-tuned medical models
- [ ] Multi-language support
- [ ] Mobile app

## 📄 License

MIT License - see LICENSE file for details.

## 🏥 Disclaimer

This application is for educational and research purposes only. It is not intended to provide medical advice, diagnosis, or treatment. Always consult with qualified healthcare professionals for medical decisions.
