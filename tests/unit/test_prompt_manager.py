"""
Tests for the PromptManager class
"""
import pytest
from app.rag.prompt_manager import PromptManager

class TestPromptManager:
    """Test cases for the PromptManager class"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.prompt_manager = PromptManager()
    
    def test_initialization(self):
        """Test that the PromptManager initializes correctly"""
        assert self.prompt_manager is not None
        assert self.prompt_manager.templates is not None
        assert "with_documents" in self.prompt_manager.templates
        assert "no_documents" in self.prompt_manager.templates
        assert "low_relevance" in self.prompt_manager.templates
        assert "error" in self.prompt_manager.templates
    
    def test_create_prompt_with_documents(self):
        """Test creating a prompt when documents are available"""
        query = "What is the capital of France?"
        context = "[1] Source: geography.txt, Tags: ['geography', 'europe'], Folder: /\n\nParis is the capital of France."
        
        system_prompt, user_prompt = self.prompt_manager.create_prompt(
            query=query,
            retrieval_state="success",
            context=context
        )
        
        # Check system prompt
        assert "ALWAYS prioritize information from the provided documents" in system_prompt
        assert "Use citations [1] ONLY when referring to specific documents" in system_prompt
        
        # Check user prompt
        assert "Context:" in user_prompt
        assert "Paris is the capital of France" in user_prompt
        assert "User question: What is the capital of France?" in user_prompt
        assert "ALWAYS reference your sources with the number in square brackets" in user_prompt
    
    def test_create_prompt_no_documents(self):
        """Test creating a prompt when no documents are available"""
        query = "What is the capital of France?"
        
        system_prompt, user_prompt = self.prompt_manager.create_prompt(
            query=query,
            retrieval_state="no_documents",
            context=""
        )
        
        # Check system prompt
        assert "Be honest about limitations when no relevant documents are available" in system_prompt
        assert "DO NOT use citations [1] as there are no documents to cite" in system_prompt
        
        # Check user prompt
        assert "Context:" not in user_prompt
        assert "User question: What is the capital of France?" in user_prompt
        assert "No relevant documents were found for this query" in user_prompt
        assert "DO NOT use citations [1] as there are no documents to cite" in user_prompt
    
    def test_create_prompt_low_relevance(self):
        """Test creating a prompt when documents have low relevance"""
        query = "What is the capital of France?"
        context = "[1] Source: history.txt, Tags: ['history', 'europe'], Folder: /\n\nFrance has a rich history dating back to the Roman Empire."
        
        system_prompt, user_prompt = self.prompt_manager.create_prompt(
            query=query,
            retrieval_state="low_relevance",
            context=context
        )
        
        # Check system prompt
        assert "Be honest when available documents have low relevance to the query" in system_prompt
        
        # Check user prompt
        assert "Context (Low Relevance):" in user_prompt
        assert "France has a rich history" in user_prompt
        assert "The retrieved documents have low relevance to this query" in user_prompt
    
    def test_create_prompt_with_conversation_history(self):
        """Test creating a prompt with conversation history"""
        query = "What is its population?"
        context = "[1] Source: geography.txt, Tags: ['geography', 'europe'], Folder: /\n\nParis has a population of approximately 2.2 million people."
        conversation_history = [
            {"role": "user", "content": "Tell me about Paris."},
            {"role": "assistant", "content": "Paris is the capital of France and is known for the Eiffel Tower."}
        ]
        
        system_prompt, user_prompt = self.prompt_manager.create_prompt(
            query=query,
            retrieval_state="success",
            context=context,
            conversation_history=conversation_history
        )
        
        # Check that conversation history is included
        assert "Previous conversation:" in user_prompt
        assert "User: Tell me about Paris." in user_prompt
        assert "Assistant: Paris is the capital of France and is known for the Eiffel Tower." in user_prompt
    
    def test_get_retrieval_state(self):
        """Test determining retrieval state from search results"""
        # Test with no results
        assert self.prompt_manager.get_retrieval_state([]) == "no_documents"
        
        # Test with results below threshold
        low_relevance_results = [
            {"chunk_id": "1", "distance": 0.7, "content": "Some content"}
        ]
        assert self.prompt_manager.get_retrieval_state(low_relevance_results) == "low_relevance"
        
        # Test with relevant results
        relevant_results = [
            {"chunk_id": "1", "distance": 0.3, "content": "Some relevant content"}
        ]
        assert self.prompt_manager.get_retrieval_state(relevant_results) == "success"