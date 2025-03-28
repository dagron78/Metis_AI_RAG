import re
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger("app.utils.text_utils")

def extract_citations(text: str) -> List[int]:
    """
    Extract citation numbers from text
    
    Example:
    "According to [1] and also mentioned in [3], the study shows..."
    Returns: [1, 3]
    """
    try:
        # Find all citations in the format [number]
        citations = re.findall(r'\[(\d+)\]', text)
        
        # Convert to integers and remove duplicates
        citation_numbers = list(set(int(c) for c in citations))
        
        # Sort by number
        citation_numbers.sort()
        
        return citation_numbers
    except Exception as e:
        logger.error(f"Error extracting citations: {str(e)}")
        return []

def truncate_text(text: str, max_length: int = 100) -> str:
    """
    Truncate text to a maximum length
    """
    if len(text) <= max_length:
        return text
    return text[:max_length] + "..."

def clean_text(text: str) -> str:
    """
    Clean text by removing extra whitespace, etc.
    """
    # Remove multiple newlines
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # Remove multiple spaces
    text = re.sub(r' {2,}', ' ', text)
    
    # Trim whitespace
    text = text.strip()
    
    return text