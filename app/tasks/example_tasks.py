"""
Example task handlers for the Background Task System
"""
import time
import asyncio
import logging
import random
from typing import Dict, Any

from app.tasks.task_models import Task, TaskStatus
from app.tasks.task_manager import TaskManager

# Initialize logger
logger = logging.getLogger("app.tasks.example_tasks")

async def document_processing_handler(task: Task) -> Dict[str, Any]:
    """
    Example handler for document processing tasks
    
    Args:
        task: Task to execute
        
    Returns:
        Task result
    """
    logger.info(f"Processing document task {task.id}")
    
    # Get document ID from task parameters
    document_id = task.params.get("document_id")
    if not document_id:
        raise ValueError("Missing document_id parameter")
    
    # Simulate document processing
    total_steps = 5
    for step in range(1, total_steps + 1):
        # Update progress
        progress = (step / total_steps) * 100
        task.update_progress(progress)
        
        # Simulate processing step
        logger.info(f"Document {document_id} processing step {step}/{total_steps}")
        await asyncio.sleep(1)  # Simulate work
    
    # Return result
    return {
        "document_id": document_id,
        "status": "processed",
        "chunks": random.randint(5, 20),
        "processing_time_ms": random.randint(1000, 5000)
    }

async def vector_store_update_handler(task: Task) -> Dict[str, Any]:
    """
    Example handler for vector store update tasks
    
    Args:
        task: Task to execute
        
    Returns:
        Task result
    """
    logger.info(f"Updating vector store task {task.id}")
    
    # Get document IDs from task parameters
    document_ids = task.params.get("document_ids", [])
    if not document_ids:
        raise ValueError("Missing document_ids parameter")
    
    # Simulate vector store update
    total_documents = len(document_ids)
    for i, doc_id in enumerate(document_ids):
        # Update progress
        progress = ((i + 1) / total_documents) * 100
        task.update_progress(progress)
        
        # Simulate update step
        logger.info(f"Updating vector store for document {doc_id} ({i+1}/{total_documents})")
        await asyncio.sleep(0.5)  # Simulate work
    
    # Return result
    return {
        "document_count": total_documents,
        "vectors_added": random.randint(total_documents * 5, total_documents * 20),
        "update_time_ms": random.randint(500, 2000) * total_documents
    }

async def report_generation_handler(task: Task) -> Dict[str, Any]:
    """
    Example handler for report generation tasks
    
    Args:
        task: Task to execute
        
    Returns:
        Task result
    """
    logger.info(f"Generating report task {task.id}")
    
    # Get report parameters
    report_type = task.params.get("report_type", "summary")
    document_ids = task.params.get("document_ids", [])
    
    if not document_ids:
        raise ValueError("Missing document_ids parameter")
    
    # Simulate report generation
    logger.info(f"Generating {report_type} report for {len(document_ids)} documents")
    
    # Simulate work with random duration based on report type and document count
    duration = 0
    if report_type == "summary":
        duration = 2 + (0.2 * len(document_ids))
    elif report_type == "detailed":
        duration = 5 + (0.5 * len(document_ids))
    elif report_type == "comprehensive":
        duration = 10 + (1.0 * len(document_ids))
    
    # Update progress periodically
    total_steps = int(duration)
    for step in range(1, total_steps + 1):
        # Update progress
        progress = (step / total_steps) * 100
        task.update_progress(progress)
        
        # Simulate processing step
        logger.info(f"Report generation step {step}/{total_steps}")
        await asyncio.sleep(1)  # Simulate work
    
    # Return result
    return {
        "report_type": report_type,
        "document_count": len(document_ids),
        "page_count": random.randint(1, 5 + len(document_ids)),
        "generation_time_ms": int(duration * 1000)
    }

async def system_maintenance_handler(task: Task) -> Dict[str, Any]:
    """
    Example handler for system maintenance tasks
    
    Args:
        task: Task to execute
        
    Returns:
        Task result
    """
    logger.info(f"Performing system maintenance task {task.id}")
    
    # Get maintenance parameters
    maintenance_type = task.params.get("maintenance_type", "cleanup")
    
    # Simulate maintenance
    logger.info(f"Performing {maintenance_type} maintenance")
    
    # Different maintenance types
    if maintenance_type == "cleanup":
        # Simulate cleanup
        logger.info("Cleaning up old data")
        await asyncio.sleep(2)
        result = {
            "files_removed": random.randint(10, 100),
            "space_freed_mb": random.randint(50, 500)
        }
    elif maintenance_type == "optimization":
        # Simulate optimization
        logger.info("Optimizing database")
        await asyncio.sleep(5)
        result = {
            "tables_optimized": random.randint(5, 20),
            "indexes_rebuilt": random.randint(10, 30)
        }
    elif maintenance_type == "backup":
        # Simulate backup
        logger.info("Creating backup")
        await asyncio.sleep(10)
        result = {
            "backup_size_mb": random.randint(100, 1000),
            "backup_location": f"/backups/metis_rag_{int(time.time())}.bak"
        }
    else:
        raise ValueError(f"Unknown maintenance type: {maintenance_type}")
    
    # Return result with common fields
    result.update({
        "maintenance_type": maintenance_type,
        "execution_time_ms": random.randint(1000, 10000)
    })
    
    return result

def register_example_handlers(task_manager: TaskManager) -> None:
    """
    Register example task handlers with the task manager
    
    Args:
        task_manager: Task manager instance
    """
    task_manager.register_task_handler("document_processing", document_processing_handler)
    task_manager.register_task_handler("vector_store_update", vector_store_update_handler)
    task_manager.register_task_handler("report_generation", report_generation_handler)
    task_manager.register_task_handler("system_maintenance", system_maintenance_handler)
    
    logger.info("Registered example task handlers")