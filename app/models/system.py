from typing import List, Dict, Optional, Any, Union
from pydantic import BaseModel, Field


class SystemStats(BaseModel):
    """System statistics model"""
    documents_count: int
    total_chunks: int
    vector_store_size: Optional[int] = None
    available_models: List[str]
    
    # Cache statistics
    cache_enabled: Optional[bool] = False
    cache_size: Optional[int] = None
    cache_max_size: Optional[int] = None
    cache_hits: Optional[int] = None
    cache_misses: Optional[int] = None
    cache_hit_ratio: Optional[float] = None
    cache_ttl_seconds: Optional[int] = None
    cache_persist: Optional[bool] = None

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


class AgentSettings(BaseModel):
    """RAG Agent settings model"""
    use_mem0: bool = True
    use_chunking_judge: bool = True
    use_retrieval_judge: bool = True
    use_langgraph_rag: bool = True
    use_enhanced_langgraph_rag: bool = True
    
    # Sensitivity settings (0-100 scale, where higher means more sensitive/aggressive)
    mem0_sensitivity: int = Field(default=50, ge=0, le=100)
    chunking_judge_sensitivity: int = Field(default=50, ge=0, le=100)
    retrieval_judge_sensitivity: int = Field(default=50, ge=0, le=100)
    langgraph_rag_sensitivity: int = Field(default=50, ge=0, le=100)
    
    class Config:
        arbitrary_types_allowed = True


class AgentSettingsUpdate(BaseModel):
    """Model for updating agent settings"""
    use_mem0: Optional[bool] = None
    use_chunking_judge: Optional[bool] = None
    use_retrieval_judge: Optional[bool] = None
    use_langgraph_rag: Optional[bool] = None
    use_enhanced_langgraph_rag: Optional[bool] = None
    
    # Sensitivity settings
    mem0_sensitivity: Optional[int] = Field(default=None, ge=0, le=100)
    chunking_judge_sensitivity: Optional[int] = Field(default=None, ge=0, le=100)
    retrieval_judge_sensitivity: Optional[int] = Field(default=None, ge=0, le=100)
    langgraph_rag_sensitivity: Optional[int] = Field(default=None, ge=0, le=100)


class HealthCheck(BaseModel):
    """Health check model"""
    status: str
    ollama_status: str
    vector_db_status: str
    api_version: str
    server_start_time: Optional[str] = "unknown"
    
    class Config:
        arbitrary_types_allowed = True