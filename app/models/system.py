from typing import List, Dict, Optional, Any
from pydantic import BaseModel


class SystemStats(BaseModel):
    """System statistics model"""
    documents_count: int
    total_chunks: int
    vector_store_size: Optional[int] = None
    available_models: List[str]

    class Config:
        arbitrary_types_allowed = True


class ModelInfo(BaseModel):
    """Model information"""
    name: str
    size: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    description: Optional[str] = None
    modified_at: Optional[str] = None
    
    class Config:
        arbitrary_types_allowed = True
    
    
class HealthCheck(BaseModel):
    """Health check model"""
    status: str
    ollama_status: str
    vector_db_status: str
    api_version: str
    
    class Config:
        arbitrary_types_allowed = True