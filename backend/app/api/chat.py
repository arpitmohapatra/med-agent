from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.responses import StreamingResponse
from typing import List, Dict, Any
import json
import logging
from ..models.chat import ChatRequest, ChatResponse, ChatMode, ChatMessage
from ..models.user import User
from ..services.auth import get_current_user
from ..services.llm_service import LLMService
from ..services.embedding_service import EmbeddingService
from ..services.elasticsearch_service import ElasticsearchService
from ..services.mcp_service import MCPService

router = APIRouter(prefix="/api", tags=["chat"])
logger = logging.getLogger(__name__)

# Initialize services
llm_service = LLMService()
embedding_service = EmbeddingService()
es_service = ElasticsearchService()
mcp_service = MCPService()


@router.post("/chat")
async def chat(
    request: ChatRequest,
    current_user: User = Depends(get_current_user)
):
    """Multi-mode chat endpoint."""
    try:
        # Add user message to history
        user_message = ChatMessage(
            role="user",
            content=request.message
        )
        
        # Combine with existing history
        all_messages = request.conversation_history + [user_message]
        
        if request.mode == ChatMode.ASK:
            return await handle_ask_mode(request, all_messages)
        elif request.mode == ChatMode.RAG:
            return await handle_rag_mode(request, all_messages)
        elif request.mode == ChatMode.AGENT:
            return await handle_agent_mode(request, all_messages)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported chat mode: {request.mode}"
            )
            
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chat error: {str(e)}"
        )


async def handle_ask_mode(request: ChatRequest, messages: List[ChatMessage]):
    """Handle Ask mode - general chat."""
    if request.stream:
        async def generate():
            try:
                async for chunk in llm_service.generate_response(
                    messages=messages,
                    mode=ChatMode.ASK,
                    stream=True,
                    model=request.model
                ):
                    yield f"data: {json.dumps({'content': chunk})}\n\n"
                yield f"data: {json.dumps({'done': True})}\n\n"
            except Exception as e:
                yield f"data: {json.dumps({'error': str(e)})}\n\n"
        
        return StreamingResponse(
            generate(),
            media_type="text/plain",
            headers={"Cache-Control": "no-cache"}
        )
    else:
        # Non-streaming response
        response_text = ""
        async for chunk in llm_service.generate_response(
            messages=messages,
            mode=ChatMode.ASK,
            stream=False,
            model=request.model
        ):
            response_text += chunk
        
        return ChatResponse(
            response=response_text,
            mode=ChatMode.ASK
        )


async def handle_rag_mode(request: ChatRequest, messages: List[ChatMessage]):
    """Handle RAG mode - retrieval augmented generation."""
    try:
        # Get embedding for the query
        query_embedding = await embedding_service.get_embedding(request.message)
        
        # Search for relevant documents
        search_results = await es_service.semantic_search(
            query_vector=query_embedding,
            query_text=request.message
        )
        
        # Format context from search results
        context = llm_service.format_rag_context(search_results)
        
        if request.stream:
            async def generate():
                try:
                    # First send the sources
                    sources_data = []
                    for doc in search_results:
                        source = {
                            "id": doc["id"],
                            "title": doc["title"],
                            "content": doc["chunk"][:200] + "..." if len(doc["chunk"]) > 200 else doc["chunk"],
                            "score": doc["score"],
                            "metadata": doc["metadata"],
                            "url": doc.get("url")
                        }
                        sources_data.append(source)
                    
                    yield f"data: {json.dumps({'sources': sources_data})}\n\n"
                    
                    # Then stream the response
                    async for chunk in llm_service.generate_response(
                        messages=messages,
                        mode=ChatMode.RAG,
                        context=context,
                        stream=True,
                        model=request.model
                    ):
                        yield f"data: {json.dumps({'content': chunk})}\n\n"
                    
                    yield f"data: {json.dumps({'done': True})}\n\n"
                except Exception as e:
                    yield f"data: {json.dumps({'error': str(e)})}\n\n"
            
            return StreamingResponse(
                generate(),
                media_type="text/plain",
                headers={"Cache-Control": "no-cache"}
            )
        else:
            # Non-streaming response
            response_text = ""
            async for chunk in llm_service.generate_response(
                messages=messages,
                mode=ChatMode.RAG,
                context=context,
                stream=False,
                model=request.model
            ):
                response_text += chunk
            
            # Format sources for response
            sources = []
            for doc in search_results:
                source = {
                    "id": doc["id"],
                    "title": doc["title"],
                    "content": doc["chunk"],
                    "score": doc["score"],
                    "metadata": doc["metadata"],
                    "url": doc.get("url")
                }
                sources.append(source)
            
            return ChatResponse(
                response=response_text,
                mode=ChatMode.RAG,
                sources=sources
            )
            
    except Exception as e:
        logger.error(f"Error in RAG mode: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"RAG error: {str(e)}"
        )


async def handle_agent_mode(request: ChatRequest, messages: List[ChatMessage]):
    """Handle Agent mode - tool use via MCP."""
    try:
        # Get available tools
        tool_schemas = mcp_service.create_tool_schemas()
        
        if request.stream:
            async def generate():
                try:
                    action_trace = []
                    
                    async for chunk in llm_service.generate_response_with_tools(
                        messages=messages,
                        tools=tool_schemas,
                        model=request.model
                    ):
                        if chunk["type"] == "content":
                            yield f"data: {json.dumps({'content': chunk['data']})}\n\n"
                        
                        elif chunk["type"] == "tool_calls":
                            # Execute tool calls
                            for tool_call in chunk["data"]:
                                try:
                                    function_name = tool_call["function"]["name"]
                                    arguments = json.loads(tool_call["function"]["arguments"])
                                    
                                    # Execute the function
                                    result = await mcp_service.execute_function_call(
                                        function_name, arguments
                                    )
                                    
                                    # Add to action trace
                                    action = {
                                        "action": function_name,
                                        "parameters": arguments,
                                        "result": result,
                                        "success": result.get("success", False)
                                    }
                                    action_trace.append(action)
                                    
                                    # Send action update
                                    yield f"data: {json.dumps({'action': action})}\n\n"
                                    
                                except Exception as tool_error:
                                    error_action = {
                                        "action": function_name,
                                        "parameters": arguments,
                                        "error": str(tool_error),
                                        "success": False
                                    }
                                    action_trace.append(error_action)
                                    yield f"data: {json.dumps({'action': error_action})}\n\n"
                        
                        elif chunk["type"] == "error":
                            yield f"data: {json.dumps({'error': chunk['data']})}\n\n"
                    
                    # Send final trace
                    yield f"data: {json.dumps({'tool_calls': action_trace, 'done': True})}\n\n"
                    
                except Exception as e:
                    yield f"data: {json.dumps({'error': str(e)})}\n\n"
            
            return StreamingResponse(
                generate(),
                media_type="text/plain",
                headers={"Cache-Control": "no-cache"}
            )
        else:
            # Non-streaming response for agent mode
            response_text = ""
            tool_calls = []
            
            async for chunk in llm_service.generate_response_with_tools(
                messages=messages,
                tools=tool_schemas,
                model=request.model
            ):
                if chunk["type"] == "content":
                    response_text += chunk["data"]
                elif chunk["type"] == "tool_calls":
                    # Process tool calls
                    for tool_call in chunk["data"]:
                        try:
                            function_name = tool_call["function"]["name"]
                            arguments = json.loads(tool_call["function"]["arguments"])
                            
                            result = await mcp_service.execute_function_call(
                                function_name, arguments
                            )
                            
                            tool_calls.append({
                                "action": function_name,
                                "parameters": arguments,
                                "result": result,
                                "success": result.get("success", False)
                            })
                            
                        except Exception as tool_error:
                            tool_calls.append({
                                "action": function_name,
                                "parameters": arguments,
                                "error": str(tool_error),
                                "success": False
                            })
            
            return ChatResponse(
                response=response_text,
                mode=ChatMode.AGENT,
                tool_calls=tool_calls
            )
            
    except Exception as e:
        logger.error(f"Error in Agent mode: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Agent error: {str(e)}"
        )
