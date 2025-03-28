import os
import uuid
from typing import Dict, Any, Optional, List
from pydantic import BaseModel
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Create FastAPI app
app = FastAPI(title="Metis RAG (Simplified)")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Setup templates
templates = Jinja2Templates(directory="app/templates")

# API prefix
API_V1_STR = "/api"

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """
    Root endpoint that returns the main HTML page
    """
    return templates.TemplateResponse("chat.html", {"request": request})

@app.get("/documents", response_class=HTMLResponse)
async def documents_page(request: Request):
    """
    Documents management page
    """
    return templates.TemplateResponse("documents.html", {"request": request})

@app.get("/system", response_class=HTMLResponse)
async def system_page(request: Request):
    """
    System management page
    """
    return templates.TemplateResponse("system.html", {"request": request})

@app.get("/analytics", response_class=HTMLResponse)
async def analytics_page(request: Request):
    """
    Analytics dashboard page
    """
    return templates.TemplateResponse("analytics.html", {"request": request})

@app.get("/tasks", response_class=HTMLResponse)
async def tasks_page(request: Request):
    """
    Background tasks management page
    """
    return templates.TemplateResponse("tasks.html", {"request": request})

# Pydantic models for API
class ChatQuery(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    model: Optional[str] = None
    use_rag: bool = True
    stream: bool = False
    model_parameters: Optional[Dict[str, Any]] = None
    user_id: Optional[str] = None
    metadata_filters: Optional[Dict[str, Any]] = None

class ChatResponse(BaseModel):
    message: str
    conversation_id: str
    citations: Optional[List[Dict[str, Any]]] = None

# API endpoints
@app.post(f"{API_V1_STR}/chat/query")
async def chat_query(query: ChatQuery):
    """
    Chat query endpoint (mock)
    """
    # Generate a conversation ID if not provided
    conversation_id = query.conversation_id or str(uuid.uuid4())
    
    # Return a mock response
    return ChatResponse(
        message=f"This is a mock response to: {query.message}",
        conversation_id=conversation_id,
        citations=[]
    )

@app.get(f"{API_V1_STR}/documents/list")
async def list_documents():
    """
    List documents endpoint (mock)
    """
    return {"documents": []}

@app.get(f"{API_V1_STR}/documents/tags")
async def get_tags():
    """
    Get tags endpoint (mock)
    """
    return {"tags": []}

@app.get(f"{API_V1_STR}/documents/folders")
async def get_folders():
    """
    Get folders endpoint (mock)
    """
    return {"folders": ["/"]}

@app.get(f"{API_V1_STR}/system/models")
async def get_models():
    """
    Get models endpoint (mock)
    """
    return {"models": [{"name": "gemma3:12b", "description": "Gemma 3 12B model"}]}

@app.get("/health")
async def health_check():
    """
    Health check endpoint
    """
    return {"status": "healthy", "message": "Simplified Metis RAG is running"}

if __name__ == "__main__":
    print("Starting simplified Metis RAG application...")
    uvicorn.run(app, host="127.0.0.1", port=8000)