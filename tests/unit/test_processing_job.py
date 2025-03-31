"""
Unit tests for ProcessingJob and WorkerPool
"""
import pytest
import pytest_asyncio
import asyncio
import uuid
from unittest.mock import MagicMock, patch

from app.models.document import Document
from app.rag.processing_job import ProcessingJob, WorkerPool, DocumentProcessingService

@pytest.fixture
def sample_document_ids():
    """Sample document IDs for testing"""
    return [str(uuid.uuid4()) for _ in range(3)]

@pytest.fixture
def processing_job(sample_document_ids):
    """Processing job for testing"""
    return ProcessingJob(document_ids=sample_document_ids)

@pytest_asyncio.fixture
async def worker_pool():
    """Worker pool for testing"""
    pool = WorkerPool(max_workers=2)
    await pool.start()
    yield pool
    await pool.stop()

@pytest.fixture
def mock_document_processor():
    """Mock document processor"""
    processor = MagicMock()
    processor.process_document = MagicMock(return_value=None)
    return processor

@pytest_asyncio.fixture
async def document_processing_service(mock_document_processor):
    """Document processing service for testing"""
    service = DocumentProcessingService(document_processor=mock_document_processor)
    await service.start()
    yield service
    await service.stop()

def test_processing_job_init(processing_job, sample_document_ids):
    """Test ProcessingJob initialization"""
    assert processing_job.id is not None
    assert processing_job.document_ids == sample_document_ids
    assert processing_job.status == "pending"
    assert processing_job.document_count == len(sample_document_ids)
    assert processing_job.processed_count == 0
    assert processing_job.progress_percentage == 0

def test_processing_job_update_progress(processing_job):
    """Test updating job progress"""
    processing_job.update_progress(2)
    assert processing_job.processed_count == 2
    assert processing_job.progress_percentage == (2 / processing_job.document_count) * 100

def test_processing_job_complete(processing_job):
    """Test marking job as completed"""
    processing_job.complete()
    assert processing_job.status == "completed"
    assert processing_job.completed_at is not None
    assert processing_job.processed_count == processing_job.document_count
    assert processing_job.progress_percentage == 100

def test_processing_job_fail(processing_job):
    """Test marking job as failed"""
    error_message = "Test error"
    processing_job.fail(error_message)
    assert processing_job.status == "failed"
    assert processing_job.completed_at is not None
    assert processing_job.error_message == error_message

def test_processing_job_to_dict(processing_job):
    """Test converting job to dictionary"""
    job_dict = processing_job.to_dict()
    assert job_dict["id"] == processing_job.id
    assert job_dict["document_ids"] == processing_job.document_ids
    assert job_dict["status"] == processing_job.status
    assert job_dict["document_count"] == processing_job.document_count
    assert job_dict["processed_count"] == processing_job.processed_count
    assert job_dict["progress_percentage"] == processing_job.progress_percentage

@pytest.mark.asyncio
async def test_worker_pool_start_stop(worker_pool):
    """Test starting and stopping worker pool"""
    assert worker_pool.running is True
    
    await worker_pool.stop()
    assert worker_pool.running is False

@pytest.mark.asyncio
async def test_worker_pool_add_job(worker_pool):
    """Test adding a job to the worker pool"""
    # Create mock job function
    job_executed = False
    
    async def mock_job():
        nonlocal job_executed
        job_executed = True
    
    # Add job to pool
    await worker_pool.add_job(mock_job)
    
    # Wait for job to execute
    await asyncio.sleep(0.1)
    
    # Check if job was executed
    assert job_executed is True

@pytest.mark.asyncio
async def test_document_processing_service_create_job(document_processing_service, sample_document_ids):
    """Test creating a processing job"""
    # Create job
    job = await document_processing_service.create_job(document_ids=sample_document_ids)
    
    # Check job
    assert job.id is not None
    assert job.document_ids == sample_document_ids
    assert job.status == "pending"
    
    # Wait for job to be processed
    await asyncio.sleep(0.1)

@pytest.mark.asyncio
async def test_document_processing_service_get_job(document_processing_service, sample_document_ids):
    """Test getting a job by ID"""
    # Create job
    job = await document_processing_service.create_job(document_ids=sample_document_ids)
    
    # Get job
    retrieved_job = await document_processing_service.get_job(job.id)
    
    # Check job
    assert retrieved_job is not None
    assert retrieved_job.id == job.id

@pytest.mark.asyncio
async def test_document_processing_service_list_jobs(document_processing_service, sample_document_ids):
    """Test listing jobs"""
    # Create jobs
    job1 = await document_processing_service.create_job(document_ids=sample_document_ids)
    job2 = await document_processing_service.create_job(document_ids=sample_document_ids)
    
    # List jobs
    jobs = await document_processing_service.list_jobs()
    
    # Check jobs
    assert len(jobs) == 2
    assert any(job.id == job1.id for job in jobs)
    assert any(job.id == job2.id for job in jobs)

@pytest.mark.asyncio
async def test_document_processing_service_cancel_job(document_processing_service, sample_document_ids):
    """Test cancelling a job"""
    # Create job
    job = await document_processing_service.create_job(document_ids=sample_document_ids)
    
    # Cancel job
    success = await document_processing_service.cancel_job(job.id)
    
    # Check result
    assert success is True
    
    # Get job
    cancelled_job = await document_processing_service.get_job(job.id)
    
    # Check job
    assert cancelled_job is not None
    assert cancelled_job.status == "cancelled"