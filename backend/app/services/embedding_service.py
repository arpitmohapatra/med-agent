import openai
from typing import List, Dict, Any
import logging
from ..core.config import settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    def __init__(self):
        """Initialize the embedding service."""
        self.model = settings.embedding_model
        self.dimensions = settings.embedding_dimensions
        
        # Configure OpenAI client based on provider
        if settings.azure_openai_endpoint and settings.azure_openai_api_key:
            # Azure OpenAI configuration
            openai.api_type = "azure"
            openai.api_base = settings.azure_openai_endpoint
            openai.api_key = settings.azure_openai_api_key
            openai.api_version = settings.azure_openai_api_version
            self.client = openai
            self.deployment_name = settings.azure_openai_embedding_deployment
        else:
            # OpenAI configuration
            openai.api_key = settings.openai_api_key
            if settings.openai_organization:
                openai.organization = settings.openai_organization
            self.client = openai
            self.deployment_name = None

    async def get_embedding(self, text: str) -> List[float]:
        """Get embedding for a single text."""
        try:
            # Clean and prepare text
            text = text.replace("\n", " ").strip()
            if not text:
                logger.warning("Empty text provided for embedding")
                return [0.0] * self.dimensions

            # Get embedding based on provider
            if settings.azure_openai_endpoint and settings.azure_openai_api_key:
                # Azure OpenAI
                from openai import AzureOpenAI
                client = AzureOpenAI(
                    api_key=settings.azure_openai_api_key,
                    api_version=settings.azure_openai_api_version,
                    azure_endpoint=settings.azure_openai_endpoint
                )
                response = client.embeddings.create(
                    input=text,
                    model=settings.azure_openai_embedding_deployment
                )
            else:
                # OpenAI
                from openai import OpenAI
                client = OpenAI(api_key=settings.openai_api_key)
                response = client.embeddings.create(
                    input=text,
                    model=self.model
                )
            
            embedding = response.data[0].embedding
            
            # Validate embedding dimensions
            if len(embedding) != self.dimensions:
                logger.warning(
                    f"Embedding dimension mismatch: expected {self.dimensions}, "
                    f"got {len(embedding)}"
                )
            
            return embedding
            
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            # Return zero vector as fallback
            return [0.0] * self.dimensions

    async def get_embeddings_batch(self, texts: List[str], batch_size: int = 100) -> List[List[float]]:
        """Get embeddings for multiple texts in batches."""
        all_embeddings = []
        
        try:
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i + batch_size]
                
                # Clean texts
                cleaned_batch = [text.replace("\n", " ").strip() for text in batch]
                
                # Get embeddings for batch
                if self.deployment_name:  # Azure
                    response = await self.client.Embedding.acreate(
                        input=cleaned_batch,
                        engine=self.deployment_name
                    )
                else:  # OpenAI
                    response = await self.client.Embedding.acreate(
                        input=cleaned_batch,
                        model=self.model
                    )
                
                # Extract embeddings
                batch_embeddings = [item['embedding'] for item in response['data']]
                all_embeddings.extend(batch_embeddings)
                
                logger.info(f"Generated embeddings for batch {i//batch_size + 1}")
        
        except Exception as e:
            logger.error(f"Error generating batch embeddings: {e}")
            # Return zero vectors as fallback
            all_embeddings = [[0.0] * self.dimensions for _ in texts]
        
        return all_embeddings

    def chunk_text(self, text: str, chunk_size: int = None, overlap: int = None) -> List[str]:
        """Split text into chunks with overlap."""
        if chunk_size is None:
            chunk_size = settings.chunk_size
        if overlap is None:
            overlap = settings.chunk_overlap
            
        if not text or len(text.strip()) == 0:
            return []
        
        # Simple word-based chunking
        words = text.split()
        if len(words) <= chunk_size:
            return [text]
        
        chunks = []
        for i in range(0, len(words), chunk_size - overlap):
            chunk_words = words[i:i + chunk_size]
            chunk = " ".join(chunk_words)
            chunks.append(chunk)
            
            # Stop if we've reached the end
            if i + chunk_size >= len(words):
                break
        
        return chunks

    async def embed_document(self, document: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Process a document by chunking and embedding.
        Returns a list of embedded chunks.
        """
        try:
            # Extract text content
            content = document.get("content", "")
            title = document.get("title", "")
            
            # Combine title and content for chunking
            full_text = f"{title}\n\n{content}" if title else content
            
            # Create chunks
            chunks = self.chunk_text(full_text)
            if not chunks:
                logger.warning("No chunks created from document")
                return []
            
            # Get embeddings for all chunks
            embeddings = await self.get_embeddings_batch(chunks)
            
            # Create embedded chunk documents
            embedded_chunks = []
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                chunk_doc = {
                    "id": f"{document.get('id', 'unknown')}_{i}",
                    "title": title,
                    "content": content,
                    "chunk": chunk,
                    "vector": embedding,
                    "url": document.get("url"),
                    "metadata": {
                        **document.get("metadata", {}),
                        "chunk_index": i,
                        "total_chunks": len(chunks),
                        "chunk_size": len(chunk.split())
                    },
                    "created_at": document.get("created_at")
                }
                embedded_chunks.append(chunk_doc)
            
            logger.info(f"Created {len(embedded_chunks)} embedded chunks from document")
            return embedded_chunks
            
        except Exception as e:
            logger.error(f"Error embedding document: {e}")
            return []
