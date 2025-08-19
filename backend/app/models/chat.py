from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from enum import Enum


class ChatMode(str, Enum):
    ASK = "ask"
    RAG = "rag"
    AGENT = "agent"


class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str
    timestamp: Optional[str] = None


class ChatRequest(BaseModel):
    message: str
    mode: ChatMode
    conversation_history: List[ChatMessage] = []
    provider: Optional[str] = "openai"  # "openai" or "azure"
    model: Optional[str] = None
    stream: bool = True


class ChatResponse(BaseModel):
    response: str
    mode: ChatMode
    sources: Optional[List[Dict[str, Any]]] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    metadata: Optional[Dict[str, Any]] = None


class RAGDocument(BaseModel):
    title: str
    content: str
    metadata: Dict[str, Any]
    score: float
    url: Optional[str] = None


class RAGResponse(BaseModel):
    documents: List[RAGDocument]
    query: str
    total_hits: int
