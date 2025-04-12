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
    
    # Check file size
    try:
        # The UploadFile object doesn't have async versions of tell() and seek()
        # We need to access the underlying file object
        file_obj = file.file
        
        # Save current position
        current_position = file_obj.tell()
        
        # Move to end to get size
        file_obj.seek(0, 2)  # Seek to end
        file_size = file_obj.tell()
        
        # Reset position
        file_obj.seek(current_position)
        
        if file_size > max_file_size:
            error_msg = f"File exceeds maximum size of {max_file_size/(1024*1024):.1f}MB"
            logger.warning(error_msg)
            return False, error_msg
            
        # Basic content validation for specific file types
        if ext == ".pdf":
            # Save current position
            current_position = file_obj.tell()
            
            # Check PDF header
            file_obj.seek(0)
            header = file_obj.read(5)
            
            # Reset position
            file_obj.seek(current_position)
            
            if header != b"%PDF-":
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

def delete_document_files(path: str) -> None:
    """
    Delete document files
    
    Args:
        path: Either a document ID or a full file path
    """
    try:
        # Check if path is a full file path or just a document ID
        if os.path.isabs(path):
            # It's a full file path
            if os.path.exists(path):
                # Delete the file
                os.remove(path)
                logger.info(f"Deleted document file at {path}")
                
                # Check if the parent directory is empty and is under UPLOAD_DIR
                parent_dir = os.path.dirname(path)
                if parent_dir.startswith(UPLOAD_DIR) and os.path.exists(parent_dir) and not os.listdir(parent_dir):
                    # Remove empty directory
                    os.rmdir(parent_dir)
                    logger.info(f"Removed empty directory {parent_dir}")
            else:
                logger.warning(f"Document file at {path} does not exist")
        else:
            # It's a document ID
            document_dir = os.path.join(UPLOAD_DIR, path)
            
            # Check if directory exists
            if os.path.exists(document_dir):
                # Delete directory and all its contents
                shutil.rmtree(document_dir)
                logger.info(f"Deleted document files for {path}")
            else:
                logger.warning(f"Document directory for {path} does not exist")
    except Exception as e:
        logger.error(f"Error deleting document files: {str(e)}")
        raise