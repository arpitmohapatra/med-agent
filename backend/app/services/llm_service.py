import openai
from typing import List, Dict, Any, AsyncGenerator, Optional
import json
import logging
from ..core.config import settings
from ..models.chat import ChatMessage, ChatMode

logger = logging.getLogger(__name__)


class LLMService:
    def __init__(self):
        """Initialize the LLM service."""
        # Configure OpenAI client based on provider
        if settings.azure_openai_endpoint and settings.azure_openai_api_key:
            # Azure OpenAI configuration
            from openai import AzureOpenAI
            self.client = AzureOpenAI(
                api_key=settings.azure_openai_api_key,
                api_version=settings.azure_openai_api_version,
                azure_endpoint=settings.azure_openai_endpoint
            )
            self.deployment_name = settings.azure_openai_deployment_name
            self.provider = "azure"
        else:
            # OpenAI configuration
            from openai import OpenAI
            self.client = OpenAI(
                api_key=settings.openai_api_key,
                organization=settings.openai_organization
            )
            self.deployment_name = "gpt-4"
            self.provider = "openai"

    def get_system_prompt(self, mode: ChatMode, context: Optional[str] = None) -> str:
        """Get system prompt based on chat mode."""
        base_disclaimer = "\n\nIMPORTANT: This is not medical advice. Always consult with qualified healthcare professionals for medical decisions."
        
        if mode == ChatMode.ASK:
            return f"""You are MedQuery, a helpful AI assistant for medical research and education. 
You can answer general questions about medicine, healthcare, and medical concepts.
Provide accurate, well-researched information while being clear about limitations.{base_disclaimer}"""
        
        elif mode == ChatMode.RAG:
            context_text = context or "No relevant context found."
            return f"""You are MedQuery, a medical knowledge assistant. Answer the user's question based ONLY on the provided context.

CONTEXT:
{context_text}

INSTRUCTIONS:
- Answer only based on the provided context
- If the context doesn't contain enough information, say "Insufficient data in the provided context. Try rephrasing your question."
- Always cite specific information from the context
- Do not hallucinate or make up information not in the context
- Be precise and factual{base_disclaimer}"""
        
        elif mode == ChatMode.AGENT:
            return f"""You are MedQuery, an AI agent capable of using various tools to help with medical research and information gathering.

You have access to tools for:
- Web browsing and research
- File system operations
- Code execution
- Calendar management
- PubMed database queries
- Knowledge graph queries

Use these tools strategically to provide comprehensive and accurate information.
Explain your reasoning and the steps you're taking.{base_disclaimer}"""
        
        return f"You are MedQuery, a medical AI assistant.{base_disclaimer}"

    async def generate_response(
        self,
        messages: List[ChatMessage],
        mode: ChatMode,
        context: Optional[str] = None,
        stream: bool = True,
        model: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        """Generate streaming response from LLM."""
        try:
            # Prepare messages for API
            api_messages = []
            
            # Add system prompt
            system_prompt = self.get_system_prompt(mode, context)
            api_messages.append({"role": "system", "content": system_prompt})
            
            # Add conversation history
            for msg in messages:
                api_messages.append({
                    "role": msg.role,
                    "content": msg.content
                })
            
            # Determine model to use
            if not model:
                model = self.deployment_name
            
            # Generate response
            if stream:
                if self.provider == "azure":
                    response = self.client.chat.completions.create(
                        model=model,
                        messages=api_messages,
                        temperature=settings.temperature,
                        max_tokens=settings.max_tokens,
                        stream=True
                    )
                else:
                    response = self.client.chat.completions.create(
                        model=model,
                        messages=api_messages,
                        temperature=settings.temperature,
                        max_tokens=settings.max_tokens,
                        stream=True
                    )
                
                # Stream response
                for chunk in response:
                    if chunk.choices and chunk.choices[0].delta.content:
                        yield chunk.choices[0].delta.content
            
            else:
                # Non-streaming response
                if self.provider == "azure":
                    response = self.client.chat.completions.create(
                        model=model,
                        messages=api_messages,
                        temperature=settings.temperature,
                        max_tokens=settings.max_tokens
                    )
                else:
                    response = self.client.chat.completions.create(
                        model=model,
                        messages=api_messages,
                        temperature=settings.temperature,
                        max_tokens=settings.max_tokens
                    )
                
                yield response.choices[0].message.content
                
        except Exception as e:
            logger.error(f"Error generating LLM response: {e}")
            yield f"Error generating response: {str(e)}"

    async def generate_response_with_tools(
        self,
        messages: List[ChatMessage],
        tools: List[Dict[str, Any]],
        model: Optional[str] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Generate response with tool calling capability."""
        try:
            # Prepare messages for API
            api_messages = []
            
            # Add system prompt for agent mode
            system_prompt = self.get_system_prompt(ChatMode.AGENT)
            api_messages.append({"role": "system", "content": system_prompt})
            
            # Add conversation history
            for msg in messages:
                api_messages.append({
                    "role": msg.role,
                    "content": msg.content
                })
            
            # Determine model to use
            if not model:
                model = self.deployment_name
            
            # Generate response with tools
            if self.provider == "azure":
                response = await self.client.ChatCompletion.acreate(
                    engine=model,
                    messages=api_messages,
                    tools=tools,
                    tool_choice="auto",
                    temperature=settings.temperature,
                    max_tokens=settings.max_tokens,
                    stream=True
                )
            else:
                response = await self.client.ChatCompletion.acreate(
                    model=model,
                    messages=api_messages,
                    tools=tools,
                    tool_choice="auto",
                    temperature=settings.temperature,
                    max_tokens=settings.max_tokens,
                    stream=True
                )
            
            # Stream response and tool calls
            async for chunk in response:
                if chunk.choices:
                    choice = chunk.choices[0]
                    
                    # Text content
                    if choice.delta.get("content"):
                        yield {
                            "type": "content",
                            "data": choice.delta["content"]
                        }
                    
                    # Tool calls
                    if choice.delta.get("tool_calls"):
                        yield {
                            "type": "tool_calls",
                            "data": choice.delta["tool_calls"]
                        }
                        
        except Exception as e:
            logger.error(f"Error generating response with tools: {e}")
            yield {
                "type": "error",
                "data": f"Error generating response: {str(e)}"
            }

    def format_rag_context(self, documents: List[Dict[str, Any]]) -> str:
        """Format retrieved documents into context string."""
        if not documents:
            return "No relevant documents found."
        
        context_parts = []
        for i, doc in enumerate(documents, 1):
            title = doc.get("title", "Unknown")
            content = doc.get("chunk", doc.get("content", ""))
            metadata = doc.get("metadata", {})
            
            # Extract key metadata
            uses = metadata.get("uses", "")
            side_effects = metadata.get("side_effects", "")
            substitutes = metadata.get("substitutes", "")
            
            context_part = f"Document {i}: {title}\n"
            if content:
                context_part += f"Content: {content}\n"
            if uses:
                context_part += f"Uses: {uses}\n"
            if side_effects:
                context_part += f"Side Effects: {side_effects}\n"
            if substitutes:
                context_part += f"Substitutes: {substitutes}\n"
            
            context_parts.append(context_part)
        
        return "\n---\n".join(context_parts)
