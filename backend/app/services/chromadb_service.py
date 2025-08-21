import chromadb
from chromadb.config import Settings as ChromaSettings
from typing import List, Dict, Any, Optional
import logging
import uuid
from ..core.config import settings

logger = logging.getLogger(__name__)


class ChromaDBService:
    def __init__(self):
        """Initialize ChromaDB client."""
        try:
            # Use persistent storage for ChromaDB
            self.client = chromadb.PersistentClient(
                path="./chroma_db",
                settings=ChromaSettings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            self.collection_name = settings.elasticsearch_index  # Reuse the same setting name
            self.collection = None
            logger.info("ChromaDB client initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing ChromaDB client: {e}")
            raise

    async def create_index(self) -> bool:
        """Create the documents collection."""
        try:
            # Get or create collection
            try:
                self.collection = self.client.get_collection(
                    name=self.collection_name,
                    embedding_function=None  # We'll provide embeddings explicitly
                )
                logger.info(f"Retrieved existing collection: {self.collection_name}")
            except Exception:
                # Collection doesn't exist, create it
                self.collection = self.client.create_collection(
                    name=self.collection_name,
                    embedding_function=None,  # We'll provide embeddings explicitly
                    metadata={"hnsw:space": "cosine"}  # Use cosine similarity like Elasticsearch
                )
                logger.info(f"Created new collection: {self.collection_name}")
            
            return True
        except Exception as e:
            logger.error(f"Error creating collection: {e}")
            return False

    async def index_document(self, doc_id: str, document: Dict[str, Any]) -> bool:
        """Index a single document."""
        try:
            if not self.collection:
                await self.create_index()
            
            # Extract vector from document
            vector = document.pop('vector', None)
            if not vector:
                logger.error(f"No vector found in document {doc_id}")
                return False
            
            # Prepare metadata (everything except vector)
            metadata = {
                "title": document.get("title", ""),
                "content": document.get("content", ""),
                "chunk": document.get("chunk", ""),
                "url": document.get("url", ""),
                "created_at": document.get("created_at", ""),
            }
            
            # Add any additional metadata
            if "metadata" in document:
                metadata.update(document["metadata"])
            
            # Create document content for full-text search
            document_text = f"{metadata.get('title', '')} {metadata.get('content', '')} {metadata.get('chunk', '')}"
            
            self.collection.add(
                ids=[doc_id],
                embeddings=[vector],
                documents=[document_text],
                metadatas=[metadata]
            )
            
            return True
        except Exception as e:
            logger.error(f"Error indexing document {doc_id}: {e}")
            return False

    async def bulk_index_documents(self, documents: List[Dict[str, Any]]) -> bool:
        """Bulk index multiple documents."""
        try:
            if not self.collection:
                await self.create_index()
            
            ids = []
            embeddings = []
            document_texts = []
            metadatas = []
            
            for doc in documents:
                doc_id = doc.get("id")
                if not doc_id:
                    doc_id = str(uuid.uuid4())
                
                # Extract vector
                vector = doc.pop('vector', None)
                if not vector:
                    logger.warning(f"No vector found in document {doc_id}, skipping")
                    continue
                
                # Prepare metadata
                metadata = {
                    "title": doc.get("title", ""),
                    "content": doc.get("content", ""),
                    "chunk": doc.get("chunk", ""),
                    "url": doc.get("url", ""),
                    "created_at": doc.get("created_at", ""),
                }
                
                # Add any additional metadata
                if "metadata" in doc:
                    metadata.update(doc["metadata"])
                
                # Create document content for full-text search
                document_text = f"{metadata.get('title', '')} {metadata.get('content', '')} {metadata.get('chunk', '')}"
                
                ids.append(doc_id)
                embeddings.append(vector)
                document_texts.append(document_text)
                metadatas.append(metadata)
            
            if ids:
                self.collection.add(
                    ids=ids,
                    embeddings=embeddings,
                    documents=document_texts,
                    metadatas=metadatas
                )
                logger.info(f"Bulk indexed {len(ids)} documents")
            
            return True
        except Exception as e:
            logger.error(f"Error bulk indexing documents: {e}")
            return False

    async def semantic_search(
        self, 
        query_vector: List[float], 
        query_text: str = "",
        top_k: int = None
    ) -> List[Dict[str, Any]]:
        """Perform semantic search using vector similarity."""
        try:
            if not self.collection:
                await self.create_index()
            
            if top_k is None:
                top_k = settings.rag_top_k
            
            # Perform vector search
            results = self.collection.query(
                query_embeddings=[query_vector],
                n_results=top_k,
                include=["documents", "metadatas", "distances"]
            )
            
            # Format results to match Elasticsearch format
            formatted_results = []
            if results['ids'] and len(results['ids']) > 0:
                for i, doc_id in enumerate(results['ids'][0]):
                    # Convert distance to score (ChromaDB uses distance, ES uses score)
                    # For cosine similarity: score = 1 - distance
                    distance = results['distances'][0][i] if results['distances'] else 0
                    score = 1 - distance
                    
                    metadata = results['metadatas'][0][i] if results['metadatas'] else {}
                    
                    result = {
                        "id": doc_id,
                        "score": score,
                        "title": metadata.get("title", ""),
                        "content": metadata.get("content", ""),
                        "chunk": metadata.get("chunk", ""),
                        "url": metadata.get("url"),
                        "metadata": {k: v for k, v in metadata.items() 
                                   if k not in ["title", "content", "chunk", "url", "created_at"]}
                    }
                    formatted_results.append(result)
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error performing semantic search: {e}")
            return []

    async def keyword_search(self, query: str, top_k: int = None) -> List[Dict[str, Any]]:
        """Perform keyword-based search using ChromaDB's where clause."""
        try:
            if not self.collection:
                await self.create_index()
            
            if top_k is None:
                top_k = settings.rag_top_k
            
            # ChromaDB doesn't have built-in keyword search like Elasticsearch
            # We'll use get() with where clause or query with where_document
            # For now, let's use a simple approach with where_document
            results = self.collection.query(
                query_texts=[query],
                n_results=top_k,
                include=["documents", "metadatas", "distances"]
            )
            
            # Format results
            formatted_results = []
            if results['ids'] and len(results['ids']) > 0:
                for i, doc_id in enumerate(results['ids'][0]):
                    distance = results['distances'][0][i] if results['distances'] else 0
                    # For text search, we'll use a simple scoring mechanism
                    score = max(0, 1 - distance)
                    
                    metadata = results['metadatas'][0][i] if results['metadatas'] else {}
                    
                    result = {
                        "id": doc_id,
                        "score": score,
                        "title": metadata.get("title", ""),
                        "content": metadata.get("content", ""),
                        "chunk": metadata.get("chunk", ""),
                        "url": metadata.get("url"),
                        "metadata": {k: v for k, v in metadata.items() 
                                   if k not in ["title", "content", "chunk", "url", "created_at"]}
                    }
                    formatted_results.append(result)
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error performing keyword search: {e}")
            return []

    async def delete_index(self) -> bool:
        """Delete the collection."""
        try:
            if self.collection:
                self.client.delete_collection(name=self.collection_name)
                self.collection = None
                logger.info(f"Deleted collection: {self.collection_name}")
            return True
        except Exception as e:
            logger.error(f"Error deleting collection: {e}")
            return False

    async def get_index_stats(self) -> Dict[str, Any]:
        """Get collection statistics."""
        try:
            if not self.collection:
                # Try to get existing collection
                try:
                    self.collection = self.client.get_collection(name=self.collection_name)
                except Exception:
                    return {"exists": False}
            
            # Get document count
            count = self.collection.count()
            
            return {
                "exists": True,
                "document_count": count,
                "collection_name": self.collection_name
            }
        except Exception as e:
            logger.error(f"Error getting collection stats: {e}")
            return {"exists": False, "error": str(e)}
