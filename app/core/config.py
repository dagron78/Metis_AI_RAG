import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Base directory
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# API settings
API_V1_STR = "/api"
PROJECT_NAME = "Metis RAG"

# Ollama settings
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "gemma3:12b")
DEFAULT_EMBEDDING_MODEL = os.getenv("DEFAULT_EMBEDDING_MODEL", "nomic-embed-text")

# LLM Judge settings
CHUNKING_JUDGE_MODEL = os.getenv("CHUNKING_JUDGE_MODEL", "gemma3:12b")
RETRIEVAL_JUDGE_MODEL = os.getenv("RETRIEVAL_JUDGE_MODEL", "gemma3:12b")
USE_CHUNKING_JUDGE = os.getenv("USE_CHUNKING_JUDGE", "True").lower() == "true"
USE_RETRIEVAL_JUDGE = os.getenv("USE_RETRIEVAL_JUDGE", "True").lower() == "true"

# LangGraph RAG Agent settings
LANGGRAPH_RAG_MODEL = os.getenv("LANGGRAPH_RAG_MODEL", "gemma3:12b")
USE_LANGGRAPH_RAG = os.getenv("USE_LANGGRAPH_RAG", "True").lower() == "true"

# Document settings
UPLOAD_DIR = os.getenv("UPLOAD_DIR", str(BASE_DIR / "uploads"))
CHROMA_DB_DIR = os.getenv("CHROMA_DB_DIR", str(BASE_DIR / "chroma_db"))
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "1500"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "150"))

# Database settings
DATABASE_TYPE = os.getenv("DATABASE_TYPE", "postgresql")
DATABASE_USER = os.getenv("DATABASE_USER", "postgres")
DATABASE_PASSWORD = os.getenv("DATABASE_PASSWORD", "postgres")
DATABASE_HOST = os.getenv("DATABASE_HOST", "localhost")
DATABASE_PORT = os.getenv("DATABASE_PORT", "5432")
DATABASE_NAME = os.getenv("DATABASE_NAME", "metis_rag")
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    f"{DATABASE_TYPE}://{DATABASE_USER}:{DATABASE_PASSWORD}@{DATABASE_HOST}:{DATABASE_PORT}/{DATABASE_NAME}"
)
DATABASE_POOL_SIZE = int(os.getenv("DATABASE_POOL_SIZE", "5"))
DATABASE_MAX_OVERFLOW = int(os.getenv("DATABASE_MAX_OVERFLOW", "10"))

# Security settings
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")

# Make sure upload directory exists
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(CHROMA_DB_DIR, exist_ok=True)