from fastapi import APIRouter, HTTPException, status, Depends
from typing import List, Dict, Any
import logging
from ..models.user import User
from ..models.mcp import MCPServer, MCPServerCreate, MCPToolCall, MCPToolResponse
from ..services.auth import get_current_user
from ..services.mcp_service import MCPService

router = APIRouter(prefix="/api/mcp", tags=["mcp"])
logger = logging.getLogger(__name__)

# Initialize MCP service
mcp_service = MCPService()


@router.post("/register", response_model=MCPServer)
async def register_server(
    server_data: MCPServerCreate,
    current_user: User = Depends(get_current_user)
):
    """Register a new MCP server."""
    try:
        server = mcp_service.register_server(server_data.dict())
        
        # Try to discover tools
        await mcp_service.discover_tools(server.id)
        
        return server
    except Exception as e:
        logger.error(f"Error registering MCP server: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration error: {str(e)}"
        )


@router.get("/servers", response_model=List[MCPServer])
async def list_servers(current_user: User = Depends(get_current_user)):
    """List all registered MCP servers."""
    try:
        return mcp_service.get_servers()
    except Exception as e:
        logger.error(f"Error listing MCP servers: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"List error: {str(e)}"
        )


@router.get("/servers/active", response_model=List[MCPServer])
async def list_active_servers(current_user: User = Depends(get_current_user)):
    """List active MCP servers."""
    try:
        return mcp_service.get_active_servers()
    except Exception as e:
        logger.error(f"Error listing active MCP servers: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"List error: {str(e)}"
        )


@router.get("/tools")
async def list_tools(current_user: User = Depends(get_current_user)):
    """List all available tools from active servers."""
    try:
        tools = await mcp_service.get_available_tools()
        return {"tools": tools}
    except Exception as e:
        logger.error(f"Error listing tools: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Tools error: {str(e)}"
        )


@router.post("/tools/discover/{server_id}")
async def discover_tools(
    server_id: str,
    current_user: User = Depends(get_current_user)
):
    """Discover available tools for a specific server."""
    try:
        tools = await mcp_service.discover_tools(server_id)
        return {
            "server_id": server_id,
            "tools": tools,
            "count": len(tools)
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error discovering tools: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Discovery error: {str(e)}"
        )


@router.post("/tools/call", response_model=MCPToolResponse)
async def call_tool(
    tool_call: MCPToolCall,
    current_user: User = Depends(get_current_user)
):
    """Execute a tool call on an MCP server."""
    try:
        response = await mcp_service.call_tool(tool_call)
        return response
    except Exception as e:
        logger.error(f"Error calling tool: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Tool call error: {str(e)}"
        )


@router.post("/proxy")
async def proxy_tool_call(
    function_name: str,
    arguments: Dict[str, Any],
    current_user: User = Depends(get_current_user)
):
    """Proxy a function call through appropriate MCP server."""
    try:
        result = await mcp_service.execute_function_call(function_name, arguments)
        return result
    except Exception as e:
        logger.error(f"Error proxying tool call: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Proxy error: {str(e)}"
        )


@router.delete("/servers/{server_id}")
async def remove_server(
    server_id: str,
    current_user: User = Depends(get_current_user)
):
    """Remove an MCP server."""
    try:
        success = mcp_service.remove_server(server_id)
        if success:
            return {"message": "Server removed successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Server not found"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing server: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Remove error: {str(e)}"
        )


@router.patch("/servers/{server_id}/deactivate")
async def deactivate_server(
    server_id: str,
    current_user: User = Depends(get_current_user)
):
    """Deactivate an MCP server."""
    try:
        success = mcp_service.deactivate_server(server_id)
        if success:
            return {"message": "Server deactivated successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Server not found"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deactivating server: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Deactivate error: {str(e)}"
        )


@router.patch("/servers/{server_id}/activate")
async def activate_server(
    server_id: str,
    current_user: User = Depends(get_current_user)
):
    """Activate an MCP server."""
    try:
        if server_id in mcp_service.servers:
            mcp_service.servers[server_id].is_active = True
            return {"message": "Server activated successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Server not found"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error activating server: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Activate error: {str(e)}"
        )
