from elasticsearch import Elasticsearch
from typing import List, Dict, Any, Optional
import logging
from ..core.config import settings

logger = logging.getLogger(__name__)


class ElasticsearchService:
    def __init__(self):
        """Initialize Elasticsearch client."""
        auth = None
        if settings.elasticsearch_username and settings.elasticsearch_password:
            auth = (settings.elasticsearch_username, settings.elasticsearch_password)
        
        self.client = Elasticsearch(
            hosts=[settings.elasticsearch_url],
            basic_auth=auth,
            verify_certs=False,
            ssl_show_warn=False
        )
        self.index_name = settings.elasticsearch_index

    async def create_index(self) -> bool:
        """Create the documents index with proper mapping."""
        mapping = {
            "mappings": {
                "properties": {
                    "title": {
                        "type": "text",
                        "analyzer": "standard"
                    },
                    "content": {
                        "type": "text",
                        "analyzer": "standard"
                    },
                    "chunk": {
                        "type": "text",
                        "analyzer": "standard"
                    },
                    "url": {
                        "type": "keyword"
                    },
                    "metadata": {
                        "type": "object",
                        "enabled": True
                    },
                    "vector": {
                        "type": "dense_vector",
                        "dims": settings.embedding_dimensions,
                        "index": True,
                        "similarity": "cosine"
                    },
                    "created_at": {
                        "type": "date"
                    }
                }
            },
            "settings": {
                "number_of_shards": 1,
                "number_of_replicas": 0
            }
        }

        try:
            if not self.client.indices.exists(index=self.index_name):
                self.client.indices.create(index=self.index_name, body=mapping)
                logger.info(f"Created index: {self.index_name}")
            return True
        except Exception as e:
            logger.error(f"Error creating index: {e}")
            return False

    async def index_document(self, doc_id: str, document: Dict[str, Any]) -> bool:
        """Index a single document."""
        try:
            self.client.index(
                index=self.index_name,
                id=doc_id,
                body=document
            )
            return True
        except Exception as e:
            logger.error(f"Error indexing document {doc_id}: {e}")
            return False

    async def bulk_index_documents(self, documents: List[Dict[str, Any]]) -> bool:
        """Bulk index multiple documents."""
        try:
            actions = []
            for doc in documents:
                action = {
                    "_index": self.index_name,
                    "_id": doc.get("id"),
                    "_source": doc
                }
                actions.append(action)
            
            from elasticsearch.helpers import bulk
            bulk(self.client, actions)
            logger.info(f"Bulk indexed {len(documents)} documents")
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
        if top_k is None:
            top_k = settings.rag_top_k

        search_body = {
            "knn": {
                "field": "vector",
                "query_vector": query_vector,
                "k": top_k,
                "num_candidates": top_k * 10
            },
            "_source": {
                "excludes": ["vector"]  # Exclude vector from results to save bandwidth
            }
        }

        # Add text-based query if provided
        if query_text:
            search_body["query"] = {
                "bool": {
                    "should": [
                        {
                            "multi_match": {
                                "query": query_text,
                                "fields": ["title^2", "content", "chunk"],
                                "type": "best_fields"
                            }
                        }
                    ]
                }
            }

        try:
            response = self.client.search(
                index=self.index_name,
                body=search_body
            )
            
            results = []
            for hit in response["hits"]["hits"]:
                result = {
                    "id": hit["_id"],
                    "score": hit["_score"],
                    "title": hit["_source"].get("title", ""),
                    "content": hit["_source"].get("content", ""),
                    "chunk": hit["_source"].get("chunk", ""),
                    "url": hit["_source"].get("url"),
                    "metadata": hit["_source"].get("metadata", {})
                }
                results.append(result)
            
            return results
        except Exception as e:
            logger.error(f"Error performing semantic search: {e}")
            return []

    async def keyword_search(self, query: str, top_k: int = None) -> List[Dict[str, Any]]:
        """Perform keyword-based search."""
        if top_k is None:
            top_k = settings.rag_top_k

        search_body = {
            "query": {
                "multi_match": {
                    "query": query,
                    "fields": ["title^3", "content^2", "chunk"],
                    "type": "best_fields"
                }
            },
            "size": top_k,
            "_source": {
                "excludes": ["vector"]
            }
        }

        try:
            response = self.client.search(
                index=self.index_name,
                body=search_body
            )
            
            results = []
            for hit in response["hits"]["hits"]:
                result = {
                    "id": hit["_id"],
                    "score": hit["_score"],
                    "title": hit["_source"].get("title", ""),
                    "content": hit["_source"].get("content", ""),
                    "chunk": hit["_source"].get("chunk", ""),
                    "url": hit["_source"].get("url"),
                    "metadata": hit["_source"].get("metadata", {})
                }
                results.append(result)
            
            return results
        except Exception as e:
            logger.error(f"Error performing keyword search: {e}")
            return []

    async def delete_index(self) -> bool:
        """Delete the index."""
        try:
            if self.client.indices.exists(index=self.index_name):
                self.client.indices.delete(index=self.index_name)
                logger.info(f"Deleted index: {self.index_name}")
            return True
        except Exception as e:
            logger.error(f"Error deleting index: {e}")
            return False

    async def get_index_stats(self) -> Dict[str, Any]:
        """Get index statistics."""
        try:
            if not self.client.indices.exists(index=self.index_name):
                return {"exists": False}
            
            stats = self.client.indices.stats(index=self.index_name)
            count = self.client.count(index=self.index_name)
            
            return {
                "exists": True,
                "document_count": count["count"],
                "size_in_bytes": stats["indices"][self.index_name]["total"]["store"]["size_in_bytes"],
                "shards": stats["indices"][self.index_name]["total"]["shards"]
            }
        except Exception as e:
            logger.error(f"Error getting index stats: {e}")
            return {"exists": False, "error": str(e)}
