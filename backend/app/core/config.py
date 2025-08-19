from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # JWT Configuration
    jwt_secret_key: str = "your-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    
    # OpenAI Configuration
    openai_api_key: Optional[str] = None
    openai_organization: Optional[str] = None
    
    # Azure OpenAI Configuration
    azure_openai_endpoint: Optional[str] = None
    azure_openai_api_key: Optional[str] = None
    azure_openai_api_version: str = "2023-12-01-preview"
    azure_openai_deployment_name: str = "gpt-4"
    azure_openai_embedding_deployment: str = "text-embedding-3-small"
    
    # Elasticsearch Configuration
    elasticsearch_url: str = "http://localhost:9200"
    elasticsearch_index: str = "medquery_documents"
    elasticsearch_username: Optional[str] = None
    elasticsearch_password: Optional[str] = None
    
    # Application Configuration
    app_name: str = "MedQuery"
    debug: bool = False
    cors_origins: list = ["http://localhost:3000"]
    
    # Embedding Configuration
    embedding_model: str = "text-embedding-3-small"
    embedding_dimensions: int = 1536
    chunk_size: int = 220
    chunk_overlap: int = 40
    
    # RAG Configuration
    rag_top_k: int = 3
    max_tokens: int = 1000
    temperature: float = 0.1
    
    class Config:
        env_file = ".env"


settings = Settings()
