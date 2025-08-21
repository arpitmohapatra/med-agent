from fastapi import APIRouter, HTTPException, status, Depends, UploadFile, File
from typing import List, Dict, Any, Optional
import json
import logging
from ..models.user import User
from ..models.chat import RAGResponse, RAGDocument
from ..services.auth import get_current_user
from ..services.embedding_service import EmbeddingService
# from ..services.elasticsearch_service import ElasticsearchService
from ..services.chromadb_service import ChromaDBService

router = APIRouter(prefix="/api/rag", tags=["rag"])
logger = logging.getLogger(__name__)

# Initialize services
embedding_service = EmbeddingService()
# es_service = ElasticsearchService()
chroma_service = ChromaDBService()


@router.post("/index")
async def index_documents(
    documents: List[Dict[str, Any]] = None,
    file: UploadFile = File(None),
    current_user: User = Depends(get_current_user)
):
    """Index documents into Elasticsearch."""
    try:
        # Ensure index exists
        await chroma_service.create_index()
        
        docs_to_process = []
        
        if file:
            # Handle file upload
            if file.content_type not in ["application/json", "text/csv"]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Only JSON and CSV files are supported"
                )
            
            content = await file.read()
            
            if file.content_type == "application/json":
                data = json.loads(content.decode())
                if isinstance(data, list):
                    docs_to_process = data
                else:
                    docs_to_process = [data]
            
            elif file.content_type == "text/csv":
                import pandas as pd
                from io import StringIO
                
                df = pd.read_csv(StringIO(content.decode()))
                docs_to_process = df.to_dict('records')
        
        elif documents:
            docs_to_process = documents
        
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Either documents or file must be provided"
            )
        
        if not docs_to_process:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No documents to process"
            )
        
        # Process and embed documents
        all_embedded_chunks = []
        for i, doc in enumerate(docs_to_process):
            # Ensure document has required fields
            if "id" not in doc:
                doc["id"] = f"doc_{i}"
            if "created_at" not in doc:
                from datetime import datetime
                doc["created_at"] = datetime.utcnow().isoformat()
            
            # Embed document
            embedded_chunks = await embedding_service.embed_document(doc)
            all_embedded_chunks.extend(embedded_chunks)
        
        # Index embedded chunks
        success = await chroma_service.bulk_index_documents(all_embedded_chunks)
        
        if success:
            return {
                "message": "Documents indexed successfully",
                "total_documents": len(docs_to_process),
                "total_chunks": len(all_embedded_chunks)
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to index documents"
            )
            
    except Exception as e:
        logger.error(f"Error indexing documents: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Indexing error: {str(e)}"
        )


@router.get("/search")
async def search_documents(
    query: str,
    top_k: int = 3,
    search_type: str = "semantic",
    current_user: User = Depends(get_current_user)
) -> RAGResponse:
    """Search documents using semantic or keyword search."""
    try:
        if search_type == "semantic":
            # Get query embedding
            query_embedding = await embedding_service.get_embedding(query)
            
            # Perform semantic search
            results = await chroma_service.semantic_search(
                query_vector=query_embedding,
                query_text=query,
                top_k=top_k
            )
        elif search_type == "keyword":
            # Perform keyword search
            results = await chroma_service.keyword_search(
                query=query,
                top_k=top_k
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="search_type must be 'semantic' or 'keyword'"
            )
        
        # Format results
        documents = []
        for result in results:
            doc = RAGDocument(
                title=result["title"],
                content=result["chunk"],
                metadata=result["metadata"],
                score=result["score"],
                url=result.get("url")
            )
            documents.append(doc)
        
        return RAGResponse(
            documents=documents,
            query=query,
            total_hits=len(documents)
        )
        
    except Exception as e:
        logger.error(f"Error searching documents: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search error: {str(e)}"
        )


@router.get("/stats")
async def get_index_stats(current_user: User = Depends(get_current_user)):
    """Get Elasticsearch index statistics."""
    try:
        stats = await chroma_service.get_index_stats()
        return stats
    except Exception as e:
        logger.error(f"Error getting index stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Stats error: {str(e)}"
        )


@router.delete("/index")
async def delete_index(current_user: User = Depends(get_current_user)):
    """Delete the entire index."""
    try:
        success = await chroma_service.delete_index()
        if success:
            return {"message": "Index deleted successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete index"
            )
    except Exception as e:
        logger.error(f"Error deleting index: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Delete error: {str(e)}"
        )


@router.post("/reindex")
async def reindex_documents(current_user: User = Depends(get_current_user)):
    """Recreate the index with fresh mapping."""
    try:
        # Delete existing index
        await es_service.delete_index()
        
        # Create new index
        success = await es_service.create_index()
        
        if success:
            return {"message": "Index recreated successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to recreate index"
            )
    except Exception as e:
        logger.error(f"Error reindexing: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Reindex error: {str(e)}"
        )
