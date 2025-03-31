"""
Processing Job - Model and service for batch document processing
"""
import uuid
import time
import logging
import asyncio
from datetime import datetime
from typing import List, Dict, Any, Optional, Callable, Awaitable

from app.models.document import Document

logger = logging.getLogger("app.rag.processing_job")

class ProcessingJob:
    """
    Model for document processing jobs
    """
    def __init__(
        self, 
        document_ids: List[str], 
        strategy: Optional[str] = None, 
        status: str = "pending",
        job_id: Optional[str] = None
    ):
        self.id = job_id or str(uuid.uuid4())
        self.document_ids = document_ids
        self.strategy = strategy
        self.status = status
        self.created_at = datetime.now()
        self.completed_at = None
        self.document_count = len(document_ids)
        self.processed_count = 0
        self.metadata = {}
        self.progress_percentage = 0
        self.error_message = None
        
    def update_progress(self, processed_count: int) -> None:
        """
        Update job progress
        
        Args:
            processed_count: Number of documents processed
        """
        self.processed_count = processed_count
        self.progress_percentage = (processed_count / self.document_count) * 100 if self.document_count > 0 else 0
        
    def complete(self) -> None:
        """
        Mark job as completed
        """
        self.status = "completed"
        self.completed_at = datetime.now()
        self.processed_count = self.document_count
        self.progress_percentage = 100
        
    def fail(self, error_message: str) -> None:
        """
        Mark job as failed
        
        Args:
            error_message: Error message
        """
        self.status = "failed"
        self.completed_at = datetime.now()
        self.error_message = error_message
        
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert job to dictionary
        
        Returns:
            Dictionary representation of the job
        """
        return {
            "id": self.id,
            "document_ids": self.document_ids,
            "strategy": self.strategy,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "document_count": self.document_count,
            "processed_count": self.processed_count,
            "metadata": self.metadata,
            "progress_percentage": self.progress_percentage,
            "error_message": self.error_message
        }


class WorkerPool:
    """
    Pool of workers for processing documents in parallel
    """
    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        self.active_workers = 0
        self.queue = asyncio.Queue()
        self.running = False
        self.logger = logging.getLogger("app.rag.worker_pool")
        
    async def start(self) -> None:
        """
        Start the worker pool
        """
        self.running = True
        self.logger.info(f"Starting worker pool with {self.max_workers} workers")
        for i in range(self.max_workers):
            asyncio.create_task(self._worker(i))
        
    async def stop(self) -> None:
        """
        Stop the worker pool
        """
        self.logger.info("Stopping worker pool")
        self.running = False
        # Wait for queue to empty
        if not self.queue.empty():
            self.logger.info(f"Waiting for {self.queue.qsize()} remaining tasks")
            await self.queue.join()
        
    async def add_job(self, job_func: Callable[..., Awaitable[Any]], *args, **kwargs) -> None:
        """
        Add a job to the queue
        
        Args:
            job_func: Async function to execute
            *args, **kwargs: Arguments to pass to the function
        """
        await self.queue.put((job_func, args, kwargs))
        self.logger.info(f"Added job to queue. Queue size: {self.queue.qsize()}")
        
    async def _worker(self, worker_id: int) -> None:
        """
        Worker process that executes jobs from the queue
        
        Args:
            worker_id: Worker ID
        """
        self.logger.info(f"Worker {worker_id} started")
        while self.running:
            try:
                # Get job from queue with timeout
                job_func, args, kwargs = await asyncio.wait_for(
                    self.queue.get(), timeout=1.0
                )
                
                # Execute job
                self.active_workers += 1
                self.logger.info(f"Worker {worker_id} executing job. Active workers: {self.active_workers}")
                try:
                    await job_func(*args, **kwargs)
                except Exception as e:
                    self.logger.error(f"Worker {worker_id} error processing job: {str(e)}")
                finally:
                    self.active_workers -= 1
                    self.queue.task_done()
                    self.logger.info(f"Worker {worker_id} completed job. Active workers: {self.active_workers}")
            except asyncio.TimeoutError:
                # No job available, continue waiting
                pass
            except Exception as e:
                self.logger.error(f"Worker {worker_id} unexpected error: {str(e)}")


class DocumentProcessingService:
    """
    Service for processing documents in batches
    """
    def __init__(self, document_processor, max_workers: int = 4, document_repository=None):
        self.document_processor = document_processor
        self.worker_pool = WorkerPool(max_workers=max_workers)
        self.jobs: Dict[str, ProcessingJob] = {}
        self.logger = logging.getLogger("app.rag.document_processing_service")
        self.document_repository = document_repository
        
    async def start(self) -> None:
        """
        Start the processing service
        """
        await self.worker_pool.start()
        self.logger.info("Document processing service started")
        
    async def stop(self) -> None:
        """
        Stop the processing service
        """
        await self.worker_pool.stop()
        self.logger.info("Document processing service stopped")
        
    def set_document_repository(self, document_repository) -> None:
        """
        Set the document repository
        
        Args:
            document_repository: Document repository
        """
        self.document_repository = document_repository
        
    async def create_job(self, document_ids: List[str], strategy: Optional[str] = None) -> ProcessingJob:
        """
        Create a new processing job
        
        Args:
            document_ids: List of document IDs to process
            strategy: Processing strategy
            
        Returns:
            Created job
        """
        job = ProcessingJob(document_ids=document_ids, strategy=strategy)
        self.jobs[job.id] = job
        self.logger.info(f"Created processing job {job.id} for {len(document_ids)} documents")
        
        # Add job to worker pool
        await self.worker_pool.add_job(self._process_job, job)
        
        return job
    
    async def get_job(self, job_id: str) -> Optional[ProcessingJob]:
        """
        Get a job by ID
        
        Args:
            job_id: Job ID
            
        Returns:
            Job if found, None otherwise
        """
        return self.jobs.get(job_id)
    
    async def list_jobs(self, status: Optional[str] = None) -> List[ProcessingJob]:
        """
        List all jobs
        
        Args:
            status: Filter by status
            
        Returns:
            List of jobs
        """
        if status:
            return [job for job in self.jobs.values() if job.status == status]
        return list(self.jobs.values())
    
    async def cancel_job(self, job_id: str) -> bool:
        """
        Cancel a job
        
        Args:
            job_id: Job ID
            
        Returns:
            True if job was cancelled, False otherwise
        """
        job = self.jobs.get(job_id)
        if job and job.status == "pending":
            job.status = "cancelled"
            job.completed_at = datetime.now()
            self.logger.info(f"Cancelled job {job_id}")
            return True
        return False
    
    async def _process_job(self, job: ProcessingJob) -> None:
        """
        Process a job
        
        Args:
            job: Job to process
        """
        start_time = time.time()
        self.logger.info(f"Processing job {job.id} with {job.document_count} documents")
        
        try:
            job.status = "processing"
            
            # Process each document
            for i, document_id in enumerate(job.document_ids):
                if job.status == "cancelled":
                    self.logger.info(f"Job {job.id} was cancelled, stopping processing")
                    break
                
                try:
                    # Get document
                    document = await self._get_document(document_id)
                    
                    if document:
                        # Set strategy if specified
                        if job.strategy:
                            self.document_processor.chunking_strategy = job.strategy
                        
                        # Process document
                        processed_document = await self.document_processor.process_document(document)
                        
                        # Save document
                        await self._save_document(processed_document)
                    
                    # Update progress
                    job.update_progress(i + 1)
                    
                    self.logger.info(f"Processed document {document_id} ({i+1}/{job.document_count})")
                except Exception as e:
                    self.logger.error(f"Error processing document {document_id}: {str(e)}")
                    # Continue with next document
            
            # Complete job
            if job.status != "cancelled":
                job.complete()
                
            elapsed_time = time.time() - start_time
            self.logger.info(f"Job {job.id} completed in {elapsed_time:.2f}s")
        except Exception as e:
            self.logger.error(f"Error processing job {job.id}: {str(e)}")
            job.fail(str(e))
    
    async def _get_document(self, document_id: str) -> Optional[Document]:
        """
        Get a document by ID
        
        Args:
            document_id: Document ID
            
        Returns:
            Document if found, None otherwise
        """
        if self.document_repository:
            try:
                # Get document from repository
                document = self.document_repository.get_document_with_chunks(document_id)
                if document:
                    self.logger.info(f"Retrieved document {document_id} from repository")
                    return document
                else:
                    self.logger.warning(f"Document {document_id} not found in repository")
            except Exception as e:
                self.logger.error(f"Error retrieving document {document_id} from repository: {str(e)}")
        
        # Fallback to dummy document if repository not available or document not found
        self.logger.warning(f"Using dummy document for {document_id} (repository not available or document not found)")
        return Document(
            id=document_id,
            filename=f"document_{document_id}.txt",
            content="This is a dummy document content for testing purposes."
        )
    
    async def _save_document(self, document: Document) -> None:
        """
        Save a document
        
        Args:
            document: Document to save (Pydantic model)
        """
        if self.document_repository:
            try:
                # Save document to repository
                self.document_repository.save_document_with_chunks(document)
                self.logger.info(f"Saved document {document.id} to repository")
            except Exception as e:
                self.logger.error(f"Error saving document {document.id} to repository: {str(e)}")
        else:
            self.logger.warning(f"Document repository not available, document {document.id} not saved")