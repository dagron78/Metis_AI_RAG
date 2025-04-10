"""
File handler utility for file operations
"""
import os
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional, Union

class FileHandler:
    """
    File handler utility class for file operations
    
    This is a mock/stub implementation for testing purposes.
    """
    
    @staticmethod
    def save_file(file_path: str, content: Union[str, bytes]) -> bool:
        """
        Save content to a file
        
        Args:
            file_path: Path to save the file
            content: Content to save
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # Determine mode based on content type
            mode = 'wb' if isinstance(content, bytes) else 'w'
            
            # Write content to file
            with open(file_path, mode) as f:
                f.write(content)
                
            return True
        except Exception as e:
            print(f"Error saving file: {str(e)}")
            return False
    
    @staticmethod
    def read_file(file_path: str, binary: bool = False) -> Optional[Union[str, bytes]]:
        """
        Read content from a file
        
        Args:
            file_path: Path to the file
            binary: Whether to read in binary mode
            
        Returns:
            str or bytes: File content, or None if error
        """
        try:
            mode = 'rb' if binary else 'r'
            with open(file_path, mode) as f:
                return f.read()
        except Exception as e:
            print(f"Error reading file: {str(e)}")
            return None
    
    @staticmethod
    def delete_file(file_path: str) -> bool:
        """
        Delete a file
        
        Args:
            file_path: Path to the file
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
            return True
        except Exception as e:
            print(f"Error deleting file: {str(e)}")
            return False
    
    @staticmethod
    def file_exists(file_path: str) -> bool:
        """
        Check if a file exists
        
        Args:
            file_path: Path to the file
            
        Returns:
            bool: True if exists, False otherwise
        """
        return os.path.exists(file_path) and os.path.isfile(file_path)
    
    @staticmethod
    def get_file_info(file_path: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a file
        
        Args:
            file_path: Path to the file
            
        Returns:
            dict: File information, or None if error
        """
        try:
            if not os.path.exists(file_path):
                return None
                
            stat = os.stat(file_path)
            path = Path(file_path)
            
            return {
                "name": path.name,
                "path": str(path),
                "size": stat.st_size,
                "created": stat.st_ctime,
                "modified": stat.st_mtime,
                "extension": path.suffix,
            }
        except Exception as e:
            print(f"Error getting file info: {str(e)}")
            return None
    
    @staticmethod
    def create_directory(dir_path: str) -> bool:
        """
        Create a directory
        
        Args:
            dir_path: Path to the directory
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            os.makedirs(dir_path, exist_ok=True)
            return True
        except Exception as e:
            print(f"Error creating directory: {str(e)}")
            return False
    
    @staticmethod
    def list_directory(dir_path: str) -> List[str]:
        """
        List contents of a directory
        
        Args:
            dir_path: Path to the directory
            
        Returns:
            list: List of file and directory names
        """
        try:
            if not os.path.exists(dir_path) or not os.path.isdir(dir_path):
                return []
                
            return os.listdir(dir_path)
        except Exception as e:
            print(f"Error listing directory: {str(e)}")
            return []