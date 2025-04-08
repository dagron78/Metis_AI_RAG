from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime
import uuid


class Citation(BaseModel):
    """Citation for a message"""
    document_id: str
    chunk_id: str
    relevance_score: float
    excerpt: str

    class Config:
        arbitrary_types_allowed = True


class Message(BaseModel):
    """Chat message"""
    content: str
    role: str = "user"  # "user" or "assistant"
    citations: Optional[List[Citation]] = None
    timestamp: datetime = Field(default_factory=datetime.now)

    class Config:
        arbitrary_types_allowed = True


class Conversation(BaseModel):
    """Chat conversation"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: Optional[str] = None
    messages: List[Message] = []
    metadata: Dict[str, Any] = {}
    created: datetime = Field(default_factory=datetime.now)
    updated: datetime = Field(default_factory=datetime.now)
    
    def add_message(self, message: Message) -> None:
        """Add a message to the conversation"""
        self.messages.append(message)
        self.updated = datetime.now()

    class Config:
        arbitrary_types_allowed = True


class ChatQuery(BaseModel):
    """Chat query model"""
    message: str
    conversation_id: Optional[str] = None
    user_id: Optional[str] = None
    model: Optional[str] = None
    use_rag: bool = True
    stream: bool = True
    model_parameters: Dict[str, Any] = {}
    metadata_filters: Optional[Dict[str, Any]] = None

    class Config:
        arbitrary_types_allowed = True


class ChatResponse(BaseModel):
    """Chat response model"""
    message: str
    conversation_id: Optional[str] = None
    citations: Optional[List[Citation]] = None
    execution_trace: Optional[List[Dict[str, Any]]] = None
    warnings: Optional[List[str]] = None
    raw_ollama_output: Optional[str] = None

    class Config:
        arbitrary_types_allowed = True