from pydantic import BaseModel
from typing import Dict, Any, List, Optional


class MCPServer(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    base_url: str
    api_key: Optional[str] = None
    is_active: bool = True
    tools: List[str] = []


class MCPServerCreate(BaseModel):
    name: str
    description: Optional[str] = None
    base_url: str
    api_key: Optional[str] = None


class MCPToolCall(BaseModel):
    tool_name: str
    server_id: str
    parameters: Dict[str, Any]


class MCPToolResponse(BaseModel):
    success: bool
    result: Any
    error: Optional[str] = None
    execution_time: Optional[float] = None


class MCPAction(BaseModel):
    action_type: str
    description: str
    parameters: Dict[str, Any]
    result: Any
    timestamp: str
