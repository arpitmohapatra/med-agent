import httpx
import json
from typing import Dict, Any, List, Optional
import logging
from ..models.mcp import MCPServer, MCPToolCall, MCPToolResponse, MCPAction
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)


class MCPService:
    def __init__(self):
        """Initialize MCP service."""
        self.servers: Dict[str, MCPServer] = {}
        self.client = httpx.AsyncClient(timeout=30.0)

    def register_server(self, server_data: Dict[str, Any]) -> MCPServer:
        """Register a new MCP server."""
        server_id = str(uuid.uuid4())
        server = MCPServer(
            id=server_id,
            name=server_data["name"],
            description=server_data.get("description"),
            base_url=server_data["base_url"],
            api_key=server_data.get("api_key"),
            is_active=True,
            tools=[]
        )
        
        self.servers[server_id] = server
        logger.info(f"Registered MCP server: {server.name}")
        return server

    def get_servers(self) -> List[MCPServer]:
        """Get list of registered servers."""
        return list(self.servers.values())

    def get_active_servers(self) -> List[MCPServer]:
        """Get list of active servers."""
        return [server for server in self.servers.values() if server.is_active]

    async def discover_tools(self, server_id: str) -> List[str]:
        """Discover available tools from an MCP server."""
        if server_id not in self.servers:
            raise ValueError(f"Server {server_id} not found")
        
        server = self.servers[server_id]
        
        try:
            headers = {}
            if server.api_key:
                headers["Authorization"] = f"Bearer {server.api_key}"
            
            # Standard MCP tools discovery endpoint
            response = await self.client.get(
                f"{server.base_url}/tools",
                headers=headers
            )
            response.raise_for_status()
            
            tools_data = response.json()
            tools = [tool["name"] for tool in tools_data.get("tools", [])]
            
            # Update server with discovered tools
            server.tools = tools
            logger.info(f"Discovered {len(tools)} tools for server {server.name}")
            
            return tools
            
        except Exception as e:
            logger.error(f"Error discovering tools for server {server.name}: {e}")
            return []

    async def call_tool(self, tool_call: MCPToolCall) -> MCPToolResponse:
        """Execute a tool call on an MCP server."""
        start_time = datetime.utcnow()
        
        if tool_call.server_id not in self.servers:
            return MCPToolResponse(
                success=False,
                result=None,
                error=f"Server {tool_call.server_id} not found"
            )
        
        server = self.servers[tool_call.server_id]
        if not server.is_active:
            return MCPToolResponse(
                success=False,
                result=None,
                error=f"Server {server.name} is not active"
            )
        
        try:
            headers = {"Content-Type": "application/json"}
            if server.api_key:
                headers["Authorization"] = f"Bearer {server.api_key}"
            
            # Prepare tool call payload
            payload = {
                "tool": tool_call.tool_name,
                "parameters": tool_call.parameters
            }
            
            # Make the tool call
            response = await self.client.post(
                f"{server.base_url}/tools/{tool_call.tool_name}",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            
            result = response.json()
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            return MCPToolResponse(
                success=True,
                result=result,
                execution_time=execution_time
            )
            
        except Exception as e:
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            logger.error(f"Error calling tool {tool_call.tool_name}: {e}")
            
            return MCPToolResponse(
                success=False,
                result=None,
                error=str(e),
                execution_time=execution_time
            )

    async def get_available_tools(self) -> List[Dict[str, Any]]:
        """Get all available tools from active servers."""
        all_tools = []
        
        for server in self.get_active_servers():
            if not server.tools:
                # Try to discover tools if not already done
                await self.discover_tools(server.id)
            
            for tool_name in server.tools:
                tool_info = {
                    "name": tool_name,
                    "server_id": server.id,
                    "server_name": server.name,
                    "description": f"Tool from {server.name}"
                }
                all_tools.append(tool_info)
        
        return all_tools

    def create_tool_schemas(self) -> List[Dict[str, Any]]:
        """Create OpenAI-compatible tool schemas for function calling."""
        schemas = []
        
        # Web browsing tool
        schemas.append({
            "type": "function",
            "function": {
                "name": "web_search",
                "description": "Search the web for information",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The search query"
                        },
                        "num_results": {
                            "type": "integer",
                            "description": "Number of results to return",
                            "default": 5
                        }
                    },
                    "required": ["query"]
                }
            }
        })
        
        # File system operations
        schemas.append({
            "type": "function",
            "function": {
                "name": "read_file",
                "description": "Read contents of a file",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "Path to the file to read"
                        }
                    },
                    "required": ["file_path"]
                }
            }
        })
        
        # PubMed search
        schemas.append({
            "type": "function",
            "function": {
                "name": "pubmed_search",
                "description": "Search PubMed database for medical literature",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The search query for PubMed"
                        },
                        "max_results": {
                            "type": "integer",
                            "description": "Maximum number of results",
                            "default": 10
                        }
                    },
                    "required": ["query"]
                }
            }
        })
        
        return schemas

    async def execute_function_call(self, function_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a function call through appropriate MCP server."""
        try:
            # Map function calls to MCP servers
            function_map = {
                "web_search": "web-browse",
                "read_file": "filesystem", 
                "pubmed_search": "pubmed",
                "neo4j_query": "neo4j",
                "marklogic_query": "marklogic"
            }
            
            # Find appropriate server
            server_type = function_map.get(function_name)
            if not server_type:
                return {
                    "success": False,
                    "error": f"Unknown function: {function_name}"
                }
            
            # Find active server of this type
            target_server = None
            for server in self.get_active_servers():
                if server_type.lower() in server.name.lower():
                    target_server = server
                    break
            
            if not target_server:
                return {
                    "success": False,
                    "error": f"No active server found for {function_name}"
                }
            
            # Create tool call
            tool_call = MCPToolCall(
                tool_name=function_name,
                server_id=target_server.id,
                parameters=arguments
            )
            
            # Execute tool call
            response = await self.call_tool(tool_call)
            
            if response.success:
                return {
                    "success": True,
                    "result": response.result,
                    "execution_time": response.execution_time,
                    "server": target_server.name
                }
            else:
                return {
                    "success": False,
                    "error": response.error,
                    "server": target_server.name
                }
                
        except Exception as e:
            logger.error(f"Error executing function call {function_name}: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def remove_server(self, server_id: str) -> bool:
        """Remove an MCP server."""
        if server_id in self.servers:
            del self.servers[server_id]
            logger.info(f"Removed MCP server: {server_id}")
            return True
        return False

    def deactivate_server(self, server_id: str) -> bool:
        """Deactivate an MCP server."""
        if server_id in self.servers:
            self.servers[server_id].is_active = False
            logger.info(f"Deactivated MCP server: {server_id}")
            return True
        return False
