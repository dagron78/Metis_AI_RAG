"""
Unit tests for DocumentAnalysisService
"""
import pytest
import uuid
from unittest.mock import MagicMock, patch

from app.models.document import Document
from app.rag.document_analysis_service import DocumentAnalysisService

@pytest.fixture
def mock_llm_provider():
    """Mock LLM provider"""
    provider = MagicMock()
    
    async def mock_generate(**kwargs):
        return {"response": """
        {
            "strategy": "recursive",
            "parameters": {
                "chunk_size": 1500,
                "chunk_overlap": 150
            },
            "justification": "Test justification"
        }
        """}
    
    provider.generate = mock_generate
    return provider

@pytest.fixture
def document_analysis_service(mock_llm_provider):
    """Document analysis service with mock LLM provider"""
    return DocumentAnalysisService(llm_provider=mock_llm_provider)

@pytest.fixture
def sample_document():
    """Sample document for testing"""
    return Document(
        id=str(uuid.uuid4()),
        filename="test_document.txt",
        content="This is a test document with some content for testing the document analysis service.",
        metadata={"file_type": "txt"}
    )

@pytest.mark.asyncio
async def test_analyze_document(document_analysis_service, sample_document):
    """Test analyzing a document"""
    # Analyze document
    result = await document_analysis_service.analyze_document(sample_document)
    
    # Check result
    assert result is not None
    assert "strategy" in result
    assert result["strategy"] == "recursive"
    assert "parameters" in result
    assert "chunk_size" in result["parameters"]
    assert result["parameters"]["chunk_size"] == 1500
    assert "chunk_overlap" in result["parameters"]
    assert result["parameters"]["chunk_overlap"] == 150
    assert "justification" in result
    assert result["justification"] == "Test justification"

@pytest.mark.asyncio
async def test_rule_based_strategy(document_analysis_service, sample_document):
    """Test rule-based strategy when LLM is not available"""
    # Remove LLM provider
    document_analysis_service.llm_provider = None
    
    # Analyze document
    result = await document_analysis_service.analyze_document(sample_document)
    
    # Check result
    assert result is not None
    assert "strategy" in result
    assert "parameters" in result
    assert "chunk_size" in result["parameters"]
    assert "chunk_overlap" in result["parameters"]
    assert "justification" in result

@pytest.mark.asyncio
async def test_analyze_document_batch(document_analysis_service, sample_document):
    """Test analyzing a batch of documents"""
    # Create batch of documents
    documents = [sample_document, sample_document]
    
    # Analyze batch
    result = await document_analysis_service.analyze_document_batch(documents)
    
    # Check result
    assert result is not None
    assert "strategy" in result
    assert result["strategy"] == "recursive"
    assert "parameters" in result
    assert "chunk_size" in result["parameters"]
    assert result["parameters"]["chunk_size"] == 1500
    assert "chunk_overlap" in result["parameters"]
    assert result["parameters"]["chunk_overlap"] == 150
    assert "justification" in result
    assert result["justification"] == "Test justification"

@pytest.mark.asyncio
async def test_extract_sample_content(document_analysis_service, sample_document, monkeypatch):
    """Test extracting sample content from a document"""
    # Mock file operations
    def mock_open(*args, **kwargs):
        return MagicMock(__enter__=MagicMock(return_value=MagicMock(read=MagicMock(return_value=sample_document.content))))
    
    def mock_path_exists(*args, **kwargs):
        return True
    
    def mock_path_getsize(*args, **kwargs):
        return len(sample_document.content)
    
    monkeypatch.setattr("builtins.open", mock_open)
    monkeypatch.setattr("os.path.exists", mock_path_exists)
    monkeypatch.setattr("os.path.getsize", mock_path_getsize)
    
    # Extract sample content
    content = await document_analysis_service._extract_sample_content(sample_document)
    
    # Check content
    assert content is not None
    assert len(content) > 0