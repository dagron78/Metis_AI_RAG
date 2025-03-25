"""
API endpoints for document processing jobs
"""
import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field

from app.db.dependencies import get_db, get_document_repository, get_document_processor
from app.db.repositories.document_repository import DocumentRepository
from app.rag.document_processor import DocumentProcessor
from app.rag.processing_job import DocumentProcessingService, ProcessingJob

# Initialize router
router = APIRouter()

# Initialize logger
logger = logging.getLogger("app.api.processing")

# Initialize document processor and processing service
document_processor = get_document_processor()
processing_service = DocumentProcessingService(document_processor=document_processor)

# Document repository will be set in the startup event

# Pydantic models for request/response
class ProcessingJobRequest(BaseModel):
    """Request model for creating a processing job"""
    document_ids: List[str] = Field(..., description="List of document IDs to process")
    strategy: Optional[str] = Field(None, description="Processing strategy")

class ProcessingJobResponse(BaseModel):
    """Response model for processing job"""
    id: str = Field(..., description="Job ID")
    document_ids: List[str] = Field(..., description="List of document IDs")
    strategy: Optional[str] = Field(None, description="Processing strategy")
    status: str = Field(..., description="Job status")
    created_at: str = Field(..., description="Creation timestamp")
    completed_at: Optional[str] = Field(None, description="Completion timestamp")
    document_count: int = Field(..., description="Total number of documents")
    processed_count: int = Field(..., description="Number of processed documents")
    progress_percentage: float = Field(..., description="Progress percentage")
    error_message: Optional[str] = Field(None, description="Error message if failed")

class ProcessingJobListResponse(BaseModel):
    """Response model for listing processing jobs"""
    jobs: List[ProcessingJobResponse] = Field(..., description="List of jobs")
    total: int = Field(..., description="Total number of jobs")

# Startup event
@router.on_event("startup")
async def startup_event():
    """Start the processing service on startup"""
    # Get document repository
    from app.db.dependencies import get_document_repository
    from app.db.session import AsyncSessionLocal
    
    # Create a session
    db = AsyncSessionLocal()
    try:
        # Get document repository
        document_repo = await get_document_repository(db)
        
        # Set document repository for processing service
        processing_service.set_document_repository(document_repo)
        logger.info("Document repository set for processing service")
        
        # Start processing service
        await processing_service.start()
        logger.info("Processing service started")
    except Exception as e:
        logger.error(f"Error starting processing service: {str(e)}")
    finally:
        await db.close()

# Shutdown event
@router.on_event("shutdown")
async def shutdown_event():
    """Stop the processing service on shutdown"""
    await processing_service.stop()
    logger.info("Processing service stopped")

@router.post("/jobs", response_model=ProcessingJobResponse, tags=["processing"])
async def create_processing_job(
    job_request: ProcessingJobRequest,
    document_repo: DocumentRepository = Depends(get_document_repository)
) -> Dict[str, Any]:
    """
    Create a new document processing job
    
    Args:
        job_request: Job request
        document_repo: Document repository
        
    Returns:
        Created job
    """
    try:
        # Validate document IDs
        for document_id in job_request.document_ids:
            document = document_repo.get_document_with_chunks(document_id)
            if not document:
                raise HTTPException(status_code=404, detail=f"Document {document_id} not found")
            
            # Update document status to pending processing
            document_repo.update_processing_status(document_id, "pending", job_request.strategy)
        
        # Create job
        job = await processing_service.create_job(
            document_ids=job_request.document_ids,
            strategy=job_request.strategy
        )
        
        logger.info(f"Created processing job {job.id} for {len(job_request.document_ids)} documents")
        
        # Return job
        return job.to_dict()
    except Exception as e:
        logger.error(f"Error creating processing job: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/jobs", response_model=ProcessingJobListResponse, tags=["processing"])
async def list_processing_jobs(
    status: Optional[str] = None
) -> Dict[str, Any]:
    """
    List processing jobs
    
    Args:
        status: Filter by status
        
    Returns:
        List of jobs
    """
    try:
        jobs = await processing_service.list_jobs(status=status)
        return {
            "jobs": [job.to_dict() for job in jobs],
            "total": len(jobs)
        }
    except Exception as e:
        logger.error(f"Error listing processing jobs: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/jobs/{job_id}", response_model=ProcessingJobResponse, tags=["processing"])
async def get_processing_job(
    job_id: str
) -> Dict[str, Any]:
    """
    Get a processing job by ID
    
    Args:
        job_id: Job ID
        
    Returns:
        Job
    """
    try:
        job = await processing_service.get_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
        return job.to_dict()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting processing job {job_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/jobs/{job_id}/cancel", response_model=ProcessingJobResponse, tags=["processing"])
async def cancel_processing_job(
    job_id: str
) -> Dict[str, Any]:
    """
    Cancel a processing job
    
    Args:
        job_id: Job ID
        
    Returns:
        Cancelled job
    """
    try:
        success = await processing_service.cancel_job(job_id)
        if not success:
            raise HTTPException(status_code=400, detail=f"Cannot cancel job {job_id}")
        
        job = await processing_service.get_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
        
        logger.info(f"Cancelled processing job {job_id}")
        
        return job.to_dict()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling processing job {job_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))