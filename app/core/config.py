import os
from pathlib import Path
from dotenv import load_dotenv
from types import SimpleNamespace

# Load environment variables from .env file
load_dotenv()

print(f"DATABASE_URL from environment: {os.getenv('DATABASE_URL')}")  # Debug print

# Base directory
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# API settings
API_V1_STR = "/api"
PROJECT_NAME = "Metis RAG"

# Ollama settings
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "gemma3:4b")
DEFAULT_EMBEDDING_MODEL = os.getenv("DEFAULT_EMBEDDING_MODEL", "nomic-embed-text")

# LLM Judge settings
CHUNKING_JUDGE_MODEL = os.getenv("CHUNKING_JUDGE_MODEL", "gemma3:4b")
RETRIEVAL_JUDGE_MODEL = os.getenv("RETRIEVAL_JUDGE_MODEL", "gemma3:4b")
USE_CHUNKING_JUDGE = os.getenv("USE_CHUNKING_JUDGE", "True").lower() == "true"
USE_RETRIEVAL_JUDGE = os.getenv("USE_RETRIEVAL_JUDGE", "True").lower() == "true"

# LangGraph RAG Agent settings
LANGGRAPH_RAG_MODEL = os.getenv("LANGGRAPH_RAG_MODEL", "gemma3:4b")
USE_LANGGRAPH_RAG = os.getenv("USE_LANGGRAPH_RAG", "True").lower() == "true"
USE_ENHANCED_LANGGRAPH_RAG = os.getenv("USE_ENHANCED_LANGGRAPH_RAG", "True").lower() == "true"

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

# Handle SQLite URLs differently
if DATABASE_TYPE.startswith("sqlite"):
    DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite+aiosqlite:///./test.db")
elif DATABASE_TYPE == "postgresql":
    # Always use asyncpg for PostgreSQL
    db_url = os.getenv("DATABASE_URL")
    if db_url and "+asyncpg" not in db_url and db_url.startswith("postgresql"):
        # Replace the URL with one that includes asyncpg and credentials
        if "localhost" in db_url and "@" not in db_url:
            # URL is missing credentials, add them
            DATABASE_URL = f"postgresql+asyncpg://{DATABASE_USER}:{DATABASE_PASSWORD}@{DATABASE_HOST}:{DATABASE_PORT}/{DATABASE_NAME}"
            print(f"Modified DATABASE_URL to include asyncpg and credentials: {DATABASE_URL}")
        else:
            # Just add asyncpg
            DATABASE_URL = db_url.replace("postgresql", "postgresql+asyncpg", 1)
            print(f"Modified DATABASE_URL to include asyncpg: {DATABASE_URL}")
    else:
        DATABASE_URL = os.getenv(
            "DATABASE_URL",
            f"postgresql+asyncpg://{DATABASE_USER}:{DATABASE_PASSWORD}@{DATABASE_HOST}:{DATABASE_PORT}/{DATABASE_NAME}"
        )
else:
    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        f"{DATABASE_TYPE}://{DATABASE_USER}:{DATABASE_PASSWORD}@{DATABASE_HOST}:{DATABASE_PORT}/{DATABASE_NAME}"
    )

print(f"DATABASE_URL after default construction: {DATABASE_URL}")  # Debug print
DATABASE_POOL_SIZE = int(os.getenv("DATABASE_POOL_SIZE", "5"))
DATABASE_MAX_OVERFLOW = int(os.getenv("DATABASE_MAX_OVERFLOW", "10"))

# Security settings
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))  # Default to 24 hours instead of 30 minutes
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
TOKEN_URL = f"{API_V1_STR}/auth/token"
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
RATE_LIMITING_ENABLED = os.getenv("RATE_LIMITING_ENABLED", "True").lower() == "true"
JWT_AUDIENCE = os.getenv("JWT_AUDIENCE", "metis-rag-api")
JWT_ISSUER = os.getenv("JWT_ISSUER", "metis-rag")

# Email settings
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_SENDER = os.getenv("SMTP_SENDER", "noreply@metisrag.com")
SMTP_USE_TLS = os.getenv("SMTP_USE_TLS", "True").lower() == "true"
EMAIL_ENABLED = os.getenv("EMAIL_ENABLED", "False").lower() == "true"
BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")

# Mem0 settings
MEM0_ENDPOINT = os.getenv("MEM0_ENDPOINT", "http://localhost:8050")
MEM0_API_KEY = os.getenv("MEM0_API_KEY", None)
USE_MEM0 = os.getenv("USE_MEM0", "True").lower() == "true"

# Make sure upload directory exists
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(CHROMA_DB_DIR, exist_ok=True)

# Create a settings object for easy access
SETTINGS = SimpleNamespace(
    version="0.1.0",
    api_v1_str=API_V1_STR,
    project_name=PROJECT_NAME,
    
    # Ollama settings
    ollama_base_url=OLLAMA_BASE_URL,
    default_model=DEFAULT_MODEL,
    default_embedding_model=DEFAULT_EMBEDDING_MODEL,
    
    # LLM Judge settings
    chunking_judge_model=CHUNKING_JUDGE_MODEL,
    retrieval_judge_model=RETRIEVAL_JUDGE_MODEL,
    use_chunking_judge=USE_CHUNKING_JUDGE,
    use_retrieval_judge=USE_RETRIEVAL_JUDGE,
    
    # LangGraph RAG Agent settings
    langgraph_rag_model=LANGGRAPH_RAG_MODEL,
    use_langgraph_rag=USE_LANGGRAPH_RAG,
    use_enhanced_langgraph_rag=USE_ENHANCED_LANGGRAPH_RAG,
    
    # Document settings
    upload_dir=UPLOAD_DIR,
    chroma_db_dir=CHROMA_DB_DIR,
    chunk_size=CHUNK_SIZE,
    chunk_overlap=CHUNK_OVERLAP,
    
    # Database settings
    database_type=DATABASE_TYPE,
    database_user=DATABASE_USER,
    database_password=DATABASE_PASSWORD,
    database_host=DATABASE_HOST,
    database_port=DATABASE_PORT,
    database_name=DATABASE_NAME,
    database_url=DATABASE_URL,
    database_pool_size=DATABASE_POOL_SIZE,
    database_max_overflow=DATABASE_MAX_OVERFLOW,
    
    # Security settings
    cors_origins=CORS_ORIGINS,
    secret_key=SECRET_KEY,
    algorithm=ALGORITHM,
    access_token_expire_minutes=ACCESS_TOKEN_EXPIRE_MINUTES,
    refresh_token_expire_days=REFRESH_TOKEN_EXPIRE_DAYS,
    token_url=TOKEN_URL,
    redis_url=REDIS_URL,
    rate_limiting_enabled=RATE_LIMITING_ENABLED,
    jwt_audience=JWT_AUDIENCE,
    jwt_issuer=JWT_ISSUER,
    
    # Email settings
    smtp_server=SMTP_SERVER,
    smtp_port=SMTP_PORT,
    smtp_username=SMTP_USERNAME,
    smtp_password=SMTP_PASSWORD,
    smtp_sender=SMTP_SENDER,
    smtp_tls=SMTP_USE_TLS,
    email_enabled=EMAIL_ENABLED,
    email_sender=SMTP_SENDER,
    base_url=BASE_URL,
    api_base_url=BASE_URL,  # Use the same base URL for API endpoints
    
    # Mem0 settings
    mem0_endpoint=MEM0_ENDPOINT,
    mem0_api_key=MEM0_API_KEY,
    use_mem0=USE_MEM0
)

print(f"Final DATABASE_URL in settings: {SETTINGS.database_url}")  # Debug print