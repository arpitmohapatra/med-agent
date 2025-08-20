MedQuery – MVP Architecture

Overview

MedQuery is a multi-mode LLM application with three modes: Ask | RAG | Agent.
It uses a FastAPI backend with JWT authentication, a React (TypeScript + Tailwind) frontend, and Elasticsearch as a vector database.
The system integrates with OpenAI / Azure OpenAI providers and MCP servers for tool-augmented reasoning.

⸻

High-Level Architecture

```mermaid
flowchart LR
 subgraph Client["React TypeScript Tailwind"]
        UI["Mode Switch Ask RAG Agent"]
        Chat["Chat Window"]
        Cards["RAG Top-3 Cards"]
        Settings["Settings Page: Providers, ES, MCP"]
        AuthUI["Login / Register"]
  end
 subgraph Provider["Provider Abstraction"]
        LLMClient["OpenAI Azure OpenAI adapter"]
        EmbedClient["Embeddings text-embedding-3-small"]
  end
 subgraph API["FastAPI Backend (JWT protected)"]
        AuthAPI[/"Auth: /auth/register, /auth/login"/]
        ChatAPI[/"Chat: /api/chat"/]
        RAGIndex[/"RAG Index: /api/rag/index"/]
        RAGSearch[/"RAG Search: /api/rag/search"/]
        MCPList[/"MCP List: /api/mcp/list"/]
        MCPReg[/"MCP Register: /api/mcp/register"/]
        MCPProxy[/"MCP Proxy: /api/mcp/proxy"/]
        Provider
  end
 subgraph Data["Data Layer"]
        ES["Elasticsearch Index"]
        Kaggle["Kaggle CSV 250k Medicines"]
  end
 subgraph MCP["MCP Ecosystem (via Proxy)"]
        Web["Web-browse"]
        FS["Filesystem"]
        Code["Code exec"]
        Calendar["Calendar"]
        PubMed["PubMed API"]
        Neo4j["Neo4j Connector"]
        MarkLogic["MarkLogic Connector"]
  end
    Client -- JWT --> API
    API <-- Auth --> Client
    ChatAPI -- Ask --> LLMClient
    ChatAPI -- RAG: search --> RAGSearch
    ChatAPI -- RAG: answer --> LLMClient
    ChatAPI -- Agent: tool calls --> MCPProxy
    MCPProxy --> Web & FS & Code & Calendar & PubMed & Neo4j & MarkLogic
    RAGIndex --> ES & Kaggle
    RAGSearch <--- ES
```

⸻

Flows

Ask Mode
``` mermaid
sequenceDiagram
  autonumber
  participant U as User
  participant FE as React UI
  participant BE as FastAPI /api/chat
  participant LLM as Provider LLM (OpenAI/Azure)

  U->>FE: Type question (Ask mode)
  FE->>BE: POST /api/chat {mode:"ask", messages[], JWT}
  BE->>LLM: chat.completions(messages)
  LLM-->>BE: assistant message
  BE-->>FE: {answer}
  FE-->>U: Render answer (no RAG cards)
```
RAG Mode
```mermaid
sequenceDiagram
  autonumber
  participant U as User
  participant FE as React UI
  participant BE as FastAPI /api/chat
  participant ES as Elasticsearch
  participant EMB as Embedding API
  participant LLM as Provider LLM

  U->>FE: Query (RAG mode)
  FE->>BE: POST /api/chat {mode:"rag", messages[], JWT}
  BE->>EMB: Embed(query)
  EMB-->>BE: query_vector[1536]
  BE->>ES: knn search k=3
  ES-->>BE: top-3 chunks (+meta)
  BE->>LLM: chat.completions(system+CONTEXT+messages)
  LLM-->>BE: grounded answer
  BE-->>FE: {answer, sources: top3}
  FE-->>U: Show answer + 3 UI cards
```
Agent Mode
``` mermaid
sequenceDiagram
  autonumber
  participant U as User
  participant FE as React UI
  participant BE as FastAPI /api/chat
  participant LLM as Provider LLM (with tools)
  participant MCP as /api/mcp/proxy
  participant TOOL as MCP Tool (e.g., PubMed)

  U->>FE: Task requiring tool (Agent)
  FE->>BE: POST /api/chat {mode:"agent", messages[], JWT}
  BE->>LLM: chat.completions(messages, tools=[mcp_call])
  LLM-->>BE: tool_call(name=mcp_call, args={server,tool,args})
  BE->>MCP: POST /api/mcp/proxy {server,tool,args}
  MCP->>TOOL: invoke tool
  TOOL-->>MCP: tool result
  MCP-->>BE: result payload
  BE->>LLM: provide tool result
  LLM-->>BE: final assistant message
  BE-->>FE: {answer, trace}
  FE-->>U: Show answer + trace
```

⸻

Data Ingestion
```mermaid
flowchart TB
  A[Kaggle CSV 250k Medicines] --> B[ETL Loader pandas]
  B --> C[Normalize fields:\nname, composition, uses,\nside_effects, substitutes,\nmanufacturer, dosage, url]
  C --> D[Concatenate -> text]
  D --> E[Chunk ~220 words\n40 overlap]
  E --> F[Embed each chunk text-embedding-3-small]
  F --> G[Build docs:\n title, chunk, url, meta, vector]
  G --> H[Bulk index to ES\nindex: med_medicines]
```

⸻

API Surface
```mermaid
classDiagram
  class AuthAPI {
    +POST /auth/register
    +POST /auth/login
    -bcrypt, JWT(HS256)
  }
  class ChatAPI {
    +POST /api/chat(mode)
    -route Ask|RAG|Agent
  }
  class RAGAPI {
    +POST /api/rag/index
    +GET  /api/rag/search?q&k
    -knn(vector, k=3)
  }
  class MCPAPI {
    +POST /api/mcp/register
    +GET  /api/mcp/list
    +POST /api/mcp/proxy
  }
  class Provider {
    +chat(messages, tools?)
    +embed(text)
    -OpenAI/Azure routing
  }
  class ESIndex {
    <<Elasticsearch>>
    +med_medicines
    +dense_vector(1536)
  }

  ChatAPI --> Provider : Ask & RAG chat
  RAGAPI --> ESIndex : search/index
  ChatAPI --> MCPAPI : Agent tool calls
  AuthAPI <.. ChatAPI : JWT required
  AuthAPI <.. RAGAPI : JWT required
  AuthAPI <.. MCPAPI : JWT required
```

⸻

Frontend Components
```mermaid
flowchart LR
  App[App.tsx] --> Login[LoginForm]
  App --> Shell[Main Shell]
  Shell --> Mode[ModeSwitch]
  Shell --> Chat[ChatWindow]
  Shell --> Right[Right Panel]
  Right --> Settings[SettingsWidget]
  Right --> Cards[RagCards Top 3]
  Settings --> Prov[ProviderConfig]
  Settings --> ESConf[ES Config]
  Settings --> MCP[MCP Servers Table]
```

⸻

Auth & Config Flow
```mermaid
sequenceDiagram
  autonumber
  participant U as User
  participant FE as React UI
  participant AUTH as /auth/*
  participant BE as Protected APIs

  U->>FE: Register/Login
  FE->>AUTH: POST /auth/login {email,pw}
  AUTH-->>FE: {JWT token}
  FE->>BE: Authorization: Bearer <JWT>
  BE-->>FE: Authorized responses
```

⸻

Data Model
```mermaid
erDiagram
  DOC {
    string id PK
    string title
    text   chunk
    string url
    json   meta
    vector[1536] vector
  }
```

⸻

Deployment Topology
```mermaid
flowchart TB
  subgraph Browser
    React[React SPA]
  end

  subgraph Server["FastAPI App Server"]
    Uvicorn[Uvicorn/Gunicorn]
    AppSvc[FastAPI App + Modules]
  end

  subgraph LLMProviders["LLM Providers"]
    OpenAI[(OpenAI API)]
    Azure[(Azure OpenAI)]
  end

  subgraph Search["Search Tier"]
    ES[(Elasticsearch)]
    Kibana[Kibana:::dim]
  end

  subgraph MCPNet["MCP Network"]
    MCPProxy[/MCP Proxy/]
    MCP1[Web-browse]
    MCP2[Filesystem]
    MCP3[Code]
    MCP4[Calendar]
    MCP5[PubMed]
    MCP6[Neo4j]
    MCP7[MarkLogic]
  end

  React -->|HTTPS| Uvicorn
  Uvicorn --> AppSvc
  AppSvc --> ES
  AppSvc --> MCPProxy
  AppSvc --> OpenAI
  AppSvc --> Azure
  MCPProxy --> MCP1 & MCP2 & MCP3 & MCP4 & MCP5 & MCP6 & MCP7
  Kibana:::dim --- ES

  classDef dim fill:#EEE,stroke:#BBB,color:#777;
```

⸻

Error & Fallback Handling
```mermaid
flowchart TD
  Q[User query RAG] --> EMB[Embed query]
  EMB -->|ok| SRCH[ES kNN search]
  EMB -->|error| F1[Return 503: embedding failed]
  SRCH -->|0 hits| F2[Answer: Insufficient data\nSuggest rephrasing]
  SRCH -->|>=1 hit| CTX[Construct CONTEXT]
  CTX --> LLM[Chat completion]
  LLM -->|ok| OUT[Answer + Sources Top 3]
  LLM -->|error| F3[Return 502: LLM call failed]
```