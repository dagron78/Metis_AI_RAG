"""
Query Processor Utility for RAG Engine

This module provides utilities for processing and analyzing queries
in the RAG Engine.
"""
import logging
import re
from typing import Dict, Any, Optional, List, Tuple, Union

logger = logging.getLogger("app.rag.engine.utils.query_processor")

async def process_query(query: str, 
                       user_id: Optional[str] = None, 
                       conversation_id: Optional[str] = None,
                       db = None) -> Tuple[str, Optional[str], Optional[str]]:
    """
    Process a query for memory operations and other transformations
    
    Args:
        query: The user query
        user_id: User ID for memory operations
        conversation_id: Conversation ID for memory operations
        db: Database session
        
    Returns:
        Tuple of (processed_query, memory_response, memory_operation)
    """
    # Initialize return values
    processed_query = query
    memory_response = None
    memory_operation = None
    
    try:
        # Check if this is a memory operation
        if _is_memory_operation(query):
            # Process memory operation
            processed_query, memory_response, memory_operation = await _handle_memory_operation(
                query, user_id, conversation_id, db
            )
            
            logger.info(f"Processed memory operation: {memory_operation}")
            return processed_query, memory_response, memory_operation
        
        # Check if this is a command
        if _is_command(query):
            # Process command
            processed_query, memory_response, memory_operation = _handle_command(query)
            
            logger.info(f"Processed command: {processed_query}")
            return processed_query, memory_response, memory_operation
        
        # Apply standard query preprocessing
        processed_query = _preprocess_query(query)
        
        return processed_query, memory_response, memory_operation
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        # Return original query on error
        return query, None, None

def _is_memory_operation(query: str) -> bool:
    """
    Check if a query is a memory operation
    
    Args:
        query: The user query
        
    Returns:
        True if the query is a memory operation, False otherwise
    """
    # Memory operation patterns
    memory_patterns = [
        r'(?i)^remember\s+that\s+',
        r'(?i)^store\s+this\s+',
        r'(?i)^save\s+this\s+',
        r'(?i)^memorize\s+that\s+',
        r'(?i)^recall\s+',
        r'(?i)^what\s+do\s+you\s+remember\s+about\s+',
        r'(?i)^forget\s+about\s+'
    ]
    
    # Check if any pattern matches
    for pattern in memory_patterns:
        if re.search(pattern, query):
            return True
    
    return False

async def _handle_memory_operation(query: str, 
                                  user_id: Optional[str], 
                                  conversation_id: Optional[str],
                                  db) -> Tuple[str, Optional[str], Optional[str]]:
    """
    Handle a memory operation
    
    Args:
        query: The user query
        user_id: User ID for memory operations
        conversation_id: Conversation ID for memory operations
        db: Database session
        
    Returns:
        Tuple of (processed_query, memory_response, memory_operation)
    """
    # Import memory buffer functions
    from app.rag.memory_buffer import store_memory, recall_memory, forget_memory
    
    # Check for store operation
    store_patterns = [
        r'(?i)^remember\s+that\s+(.+)',
        r'(?i)^store\s+this\s*:?\s*(.+)',
        r'(?i)^save\s+this\s*:?\s*(.+)',
        r'(?i)^memorize\s+that\s+(.+)'
    ]
    
    for pattern in store_patterns:
        match = re.search(pattern, query)
        if match:
            # Extract the content to store
            content = match.group(1).strip()
            
            # Store the memory
            if user_id and conversation_id and db:
                await store_memory(content, user_id, conversation_id, db)
                
                # Return a confirmation message
                memory_response = f"I've stored this information: '{content}'"
                
                # Return the original query without the memory command
                return content, memory_response, "store"
    
    # Check for recall operation
    recall_patterns = [
        r'(?i)^recall\s+(.+)',
        r'(?i)^what\s+do\s+you\s+remember\s+about\s+(.+)'
    ]
    
    for pattern in recall_patterns:
        match = re.search(pattern, query)
        if match:
            # Extract the topic to recall
            topic = match.group(1).strip()
            
            # Recall the memory
            if user_id and conversation_id and db:
                recalled_content = await recall_memory(topic, user_id, conversation_id, db)
                
                if recalled_content:
                    # Return the recalled content
                    memory_response = f"Here's what I remember: {recalled_content}"
                else:
                    # No memory found
                    memory_response = f"I don't have any specific memories about '{topic}'."
                
                # Return the original query without the memory command
                return topic, memory_response, "recall"
    
    # Check for forget operation
    forget_patterns = [
        r'(?i)^forget\s+about\s+(.+)'
    ]
    
    for pattern in forget_patterns:
        match = re.search(pattern, query)
        if match:
            # Extract the topic to forget
            topic = match.group(1).strip()
            
            # Forget the memory
            if user_id and conversation_id and db:
                success = await forget_memory(topic, user_id, conversation_id, db)
                
                if success:
                    # Return a confirmation message
                    memory_response = f"I've forgotten the information about '{topic}'."
                else:
                    # No memory found to forget
                    memory_response = f"I don't have any specific memories about '{topic}' to forget."
                
                # Return a generic query asking for confirmation
                return f"Please confirm you've forgotten about {topic}", memory_response, "forget"
    
    # If we get here, it's a memory operation but we couldn't handle it
    logger.warning(f"Unhandled memory operation: {query}")
    return query, None, None

def _is_command(query: str) -> bool:
    """
    Check if a query is a command
    
    Args:
        query: The user query
        
    Returns:
        True if the query is a command, False otherwise
    """
    # Command patterns
    command_patterns = [
        r'(?i)^/\w+',  # Slash commands like /help
        r'(?i)^![\w-]+',  # Bang commands like !search
        r'(?i)^@[\w-]+'  # At commands like @user
    ]
    
    # Check if any pattern matches
    for pattern in command_patterns:
        if re.search(pattern, query):
            return True
    
    return False

def _handle_command(query: str) -> Tuple[str, Optional[str], Optional[str]]:
    """
    Handle a command
    
    Args:
        query: The user query
        
    Returns:
        Tuple of (processed_query, response, operation)
    """
    # Check for help command
    if re.match(r'(?i)^/help', query):
        response = """
        Available commands:
        /help - Show this help message
        /clear - Clear the conversation
        /save - Save the conversation
        /models - List available models
        """
        return query, response, "help"
    
    # Check for clear command
    if re.match(r'(?i)^/clear', query):
        response = "Conversation cleared."
        return query, response, "clear"
    
    # Check for save command
    if re.match(r'(?i)^/save', query):
        response = "Conversation saved."
        return query, response, "save"
    
    # Check for models command
    if re.match(r'(?i)^/models', query):
        response = "Fetching available models..."
        return query, response, "models"
    
    # If we get here, it's a command but we couldn't handle it
    logger.warning(f"Unhandled command: {query}")
    return query, None, None

def _preprocess_query(query: str) -> str:
    """
    Preprocess a query
    
    Args:
        query: The user query
        
    Returns:
        Preprocessed query
    """
    # Trim whitespace
    processed = query.strip()
    
    # Remove excessive punctuation
    processed = re.sub(r'([.!?]){3,}', r'\1\1\1', processed)
    
    # Remove excessive whitespace
    processed = re.sub(r'\s+', ' ', processed)
    
    # Ensure the query ends with a question mark if it's a question
    question_starters = ['what', 'who', 'where', 'when', 'why', 'how', 'is', 'are', 'can', 'could', 'would', 'should', 'do', 'does', 'did']
    if any(processed.lower().startswith(starter + ' ') for starter in question_starters) and not processed.endswith('?'):
        processed += '?'
    
    return processed

def analyze_query_complexity(query: str) -> Dict[str, Any]:
    """
    Analyze the complexity of a query
    
    Args:
        query: The user query
        
    Returns:
        Dictionary with complexity analysis
    """
    # Initialize analysis
    analysis = {
        "complexity": "simple",
        "word_count": 0,
        "has_multiple_questions": False,
        "requires_reasoning": False,
        "requires_calculation": False,
        "requires_external_knowledge": False,
        "requires_code_generation": False,
        "requires_structured_output": False
    }
    
    # Count words
    words = query.split()
    analysis["word_count"] = len(words)
    
    # Check for multiple questions
    question_marks = query.count('?')
    analysis["has_multiple_questions"] = question_marks > 1
    
    # Check for reasoning indicators
    reasoning_indicators = ['why', 'reason', 'explain', 'analyze', 'compare', 'contrast', 'evaluate', 'assess']
    analysis["requires_reasoning"] = any(indicator in query.lower() for indicator in reasoning_indicators)
    
    # Check for calculation indicators
    calculation_indicators = ['calculate', 'compute', 'solve', 'equation', 'formula', 'math', 'arithmetic']
    analysis["requires_calculation"] = any(indicator in query.lower() for indicator in calculation_indicators)
    
    # Check for external knowledge indicators
    knowledge_indicators = ['current', 'latest', 'recent', 'news', 'today', 'yesterday', 'last week', 'this year']
    analysis["requires_external_knowledge"] = any(indicator in query.lower() for indicator in knowledge_indicators)
    
    # Check for code generation indicators
    code_indicators = ['code', 'function', 'program', 'script', 'algorithm', 'implement']
    analysis["requires_code_generation"] = any(indicator in query.lower() for indicator in code_indicators)
    
    # Check for structured output indicators
    structured_indicators = ['table', 'list', 'format', 'json', 'csv', 'structured']
    analysis["requires_structured_output"] = any(indicator in query.lower() for indicator in structured_indicators)
    
    # Determine overall complexity
    complexity_score = 0
    complexity_score += analysis["word_count"] // 10
    complexity_score += 1 if analysis["has_multiple_questions"] else 0
    complexity_score += 2 if analysis["requires_reasoning"] else 0
    complexity_score += 2 if analysis["requires_calculation"] else 0
    complexity_score += 1 if analysis["requires_external_knowledge"] else 0
    complexity_score += 2 if analysis["requires_code_generation"] else 0
    complexity_score += 1 if analysis["requires_structured_output"] else 0
    
    if complexity_score <= 2:
        analysis["complexity"] = "simple"
    elif complexity_score <= 5:
        analysis["complexity"] = "moderate"
    else:
        analysis["complexity"] = "complex"
    
    return analysis

def extract_keywords(query: str) -> List[str]:
    """
    Extract keywords from a query
    
    Args:
        query: The user query
        
    Returns:
        List of keywords
    """
    # Import nltk for natural language processing
    try:
        import nltk
        from nltk.corpus import stopwords
        from nltk.tokenize import word_tokenize
        
        # Download required nltk resources if not already downloaded
        try:
            nltk.data.find('tokenizers/punkt')
        except LookupError:
            nltk.download('punkt')
        
        try:
            nltk.data.find('corpora/stopwords')
        except LookupError:
            nltk.download('stopwords')
        
        # Tokenize the query
        tokens = word_tokenize(query.lower())
        
        # Remove stopwords
        stop_words = set(stopwords.words('english'))
        keywords = [word for word in tokens if word.isalnum() and word not in stop_words]
        
        return keywords
    except ImportError:
        # Fallback if nltk is not available
        logger.warning("NLTK not available, using simple keyword extraction")
        
        # Simple keyword extraction
        stop_words = {'a', 'an', 'the', 'and', 'or', 'but', 'if', 'because', 'as', 'what', 'which', 'this', 'that', 'these', 'those', 'then', 'just', 'so', 'than', 'such', 'both', 'through', 'about', 'for', 'is', 'of', 'while', 'during', 'to'}
        words = re.findall(r'\b\w+\b', query.lower())
        keywords = [word for word in words if word not in stop_words and len(word) > 2]
        
        return keywords