import logging
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.dependencies import get_db
from app.db.repositories.document_repository import DocumentRepository

# Create router
router = APIRouter()

# Logger
logger = logging.getLogger("app.api.test")

@router.get("/test-document-repository")
async def test_document_repository(db: AsyncSession = Depends(get_db)):
    """
    Test the document repository
    """
    try:
        # Create a document repository
        document_repository = DocumentRepository(db)
        
        # Create a document
        document = await document_repository.create_document(
            filename="test_document.txt",
            content="This is a test document.",
            metadata={"source": "test"},
            tags=["test", "sample"],
            folder="/"
        )
        
        return {
            "success": True,
            "message": "Document created successfully",
            "document_id": str(document.id)
        }
    except Exception as e:
        logger.error(f"Error testing document repository: {str(e)}")
        return {
            "success": False,
            "message": f"Error testing document repository: {str(e)}"
        }