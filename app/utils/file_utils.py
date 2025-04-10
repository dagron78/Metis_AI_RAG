import os
import logging
import shutil
from pathlib import Path
from typing import List, Optional, Set
from fastapi import UploadFile

from app.core.config import UPLOAD_DIR

logger = logging.getLogger("app.utils.file_utils")

# Set of allowed file extensions with max size in MB
ALLOWED_EXTENSIONS = {
    ".pdf": 20,    # 20MB max for PDFs
    ".txt": 10,    # 10MB max for text files
    ".csv": 15,    # 15MB max for CSV files
    ".md": 10,     # 10MB max for markdown files
    ".docx": 20,   # 20MB max for Word documents
    ".doc": 20,    # 20MB max for older Word documents
    ".rtf": 15,    # 15MB max for rich text files
    ".html": 10,   # 10MB max for HTML files
    ".json": 10,   # 10MB max for JSON files
    ".xml": 10     # 10MB max for XML files
}

# Default max file size in bytes (10MB)
DEFAULT_MAX_FILE_SIZE = 10 * 1024 * 1024

async def validate_file(file: UploadFile) -> tuple[bool, str]:
    """
    Enhanced file validation with detailed error messages
    Returns a tuple of (is_valid, error_message)
    """
    # Get file extension
    _, ext = os.path.splitext(file.filename.lower())
    
    # Check if extension is allowed
    if ext not in ALLOWED_EXTENSIONS:
        error_msg = f"File type {ext} is not allowed. Supported types: {', '.join(ALLOWED_EXTENSIONS)}"
        logger.warning(error_msg)
        return False, error_msg
    
    # Get max file size for this extension
    max_file_size = ALLOWED_EXTENSIONS.get(ext, DEFAULT_MAX_FILE_SIZE) * 1024 * 1024
    
    # Check file size - FastAPI's UploadFile doesn't have tell/seek methods
    # so we need to use file.file which is a SpooledTemporaryFile
    try:
        # Read the file content into memory for validation
        content = await file.read()
        file_size = len(content)
        
        # Reset the file pointer for subsequent reads
        await file.seek(0)
        
        if file_size > max_file_size:
            error_msg = f"File exceeds maximum size of {max_file_size/(1024*1024):.1f}MB"
            logger.warning(error_msg)
            return False, error_msg
            
        # Basic content validation for specific file types
        if ext == ".pdf" and file_size >= 5:
            # Check PDF header
            if content[:5] != b"%PDF-":
                error_msg = "Invalid PDF file format"
                logger.warning(error_msg)
                return False, error_msg
                
    except Exception as e:
        error_msg = f"Error validating file: {str(e)}"
        logger.error(error_msg)
        return False, error_msg
    
    return True, ""

async def save_upload_file(file: UploadFile, document_id: str) -> str:
    """
    Save an uploaded file to the upload directory
    """
    try:
        # Create directory for the document
        document_dir = os.path.join(UPLOAD_DIR, document_id)
        os.makedirs(document_dir, exist_ok=True)
        
        # Define file path
        file_path = os.path.join(document_dir, file.filename)
        
        # Save file
        with open(file_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
        
        logger.info(f"File saved to {file_path}")
        return file_path
    except Exception as e:
        logger.error(f"Error saving uploaded file: {str(e)}")
        raise
    finally:
        # Make sure to close the file
        await file.close()

def delete_document_files(document_id: str) -> None:
    """
    Delete document files
    """
    try:
        # Get document directory
        document_dir = os.path.join(UPLOAD_DIR, document_id)
        
        # Check if directory exists
        if os.path.exists(document_dir):
            # Delete directory and all its contents
            shutil.rmtree(document_dir)
            logger.info(f"Deleted document files for {document_id}")
        else:
            logger.warning(f"Document directory for {document_id} does not exist")
    except Exception as e:
        logger.error(f"Error deleting document files: {str(e)}")
        raise