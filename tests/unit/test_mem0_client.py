"""
Unit tests for Mem0 client
"""
import pytest
from unittest.mock import patch, MagicMock
from app.rag.mem0_client import get_mem0_client, store_message, get_conversation_history

@pytest.fixture
def mock_mem0_client():
    """
    Mock Mem0 client
    """
    with patch("app.rag.mem0_client.EnhancedMem0Client") as mock_client:
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance
        yield mock_instance

@pytest.fixture
def mock_settings():
    """
    Mock settings
    """
    with patch("app.rag.mem0_client.SETTINGS") as mock_settings:
        mock_settings.use_mem0 = True
        mock_settings.mem0_endpoint = "http://localhost:8050"
        mock_settings.mem0_api_key = "test_key"
        yield mock_settings

def test_get_mem0_client(mock_mem0_client, mock_settings):
    """
    Test get_mem0_client
    """
    # Reset singleton
    import app.rag.mem0_client
    app.rag.mem0_client._mem0_client = None
    
    # Mock MEM0_AVAILABLE
    with patch("app.rag.mem0_client.MEM0_AVAILABLE", True):
        client = get_mem0_client()
        assert client is not None
        assert client == mock_mem0_client

def test_store_message(mock_mem0_client, mock_settings):
    """
    Test store_message
    """
    # Reset singleton
    import app.rag.mem0_client
    app.rag.mem0_client._mem0_client = None
    
    # Mock MEM0_AVAILABLE and get_or_create_human
    with patch("app.rag.mem0_client.MEM0_AVAILABLE", True):
        with patch("app.rag.mem0_client.get_or_create_human", return_value=True):
            result = store_message("user123", "user", "Hello")
            assert result is True
            mock_mem0_client.append_message.assert_called_once()

def test_get_conversation_history(mock_mem0_client, mock_settings):
    """
    Test get_conversation_history
    """
    # Reset singleton
    import app.rag.mem0_client
    app.rag.mem0_client._mem0_client = None
    
    # Mock MEM0_AVAILABLE
    with patch("app.rag.mem0_client.MEM0_AVAILABLE", True):
        mock_mem0_client.get_recall_memory.return_value = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there"}
        ]
        
        history = get_conversation_history("user123")
        assert len(history) == 2
        assert history[0]["role"] == "user"
        assert history[1]["role"] == "assistant"
        mock_mem0_client.get_recall_memory.assert_called_once()