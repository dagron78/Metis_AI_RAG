import os
import logging
from typing import List, Dict, Any, Optional, Literal
from langchain.text_splitter import (
    RecursiveCharacterTextSplitter,
    MarkdownHeaderTextSplitter,
    TokenTextSplitter
)
from langchain.document_loaders import TextLoader, PyPDFLoader, CSVLoader, UnstructuredMarkdownLoader
from langchain.schema import Document as LangchainDocument

from app.core.config import UPLOAD_DIR, CHUNK_SIZE, CHUNK_OVERLAP, USE_CHUNKING_JUDGE
from app.models.document import Document, Chunk
from app.rag.agents.chunking_judge import ChunkingJudge
from app.rag.chunkers.semantic_chunker import SemanticChunker
from app.rag.document_analysis_service import DocumentAnalysisService

logger = logging.getLogger("app.rag.document_processor")

class DocumentProcessor:
    """
    Process documents for RAG with support for multiple chunking strategies
    """
    def __init__(
        self,
        chunk_size: int = CHUNK_SIZE,
        chunk_overlap: int = CHUNK_OVERLAP,
        chunking_strategy: str = "recursive",
        llm_provider = None
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.chunking_strategy = chunking_strategy
        self.loader_map = {
            '.txt': TextLoader,
            '.pdf': PyPDFLoader,
            '.csv': CSVLoader,
            '.md': UnstructuredMarkdownLoader,
        }
        self.llm_provider = llm_provider
        self.document_analysis_service = DocumentAnalysisService(llm_provider=self.llm_provider)
        self.text_splitter = self._get_text_splitter()
    
    def _get_text_splitter(self, file_ext=None):
        """Get the appropriate text splitter based on chunking strategy and file type"""
        logger.info(f"Using chunking strategy: {self.chunking_strategy} for file type: {file_ext}")
        
        # If we have a chunking analysis in document metadata, log it
        if hasattr(self, 'document') and self.document and 'chunking_analysis' in self.document.metadata:
            logger.info(f"Chunking analysis: {self.document.metadata['chunking_analysis']['justification']}")
        
        # Text file handling - use paragraph-based splitting for more natural chunks
        if file_ext == ".txt":
            # Use a larger chunk size for text files to preserve more context
            larger_chunk_size = self.chunk_size * 3  # Increase from 500 to 1500
            logger.info(f"Using paragraph-based splitting for text file with increased chunk size {larger_chunk_size}")
            return RecursiveCharacterTextSplitter(
                chunk_size=larger_chunk_size,
                chunk_overlap=self.chunk_overlap * 2,  # Increase overlap as well
                separators=["\n\n", "\n", ".", " ", ""]
            )
        
        # PDF-specific handling
        if file_ext == ".pdf":
            logger.info(f"Using PDF-specific splitting with chunk size {self.chunk_size}")
            return RecursiveCharacterTextSplitter(
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap,
                separators=["\n\n", "\n", ".", " ", ""]
            )
        
        # Markdown-specific handling
        if file_ext == ".md" and self.chunking_strategy == "markdown":
            logger.info("Using header-based splitting for markdown")
            # First split by headers
            header_splitter = MarkdownHeaderTextSplitter(
                headers_to_split_on=[
                    ("#", "header1"),
                    ("##", "header2"),
                    ("###", "header3"),
                    ("####", "header4"),
                ]
            )
            # Then apply recursive splitting to each section
            return RecursiveCharacterTextSplitter(
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap
            )
        
        # CSV-specific handling
        if file_ext == ".csv":
            logger.info(f"Using larger chunks for CSV with chunk size {self.chunk_size}")
            return RecursiveCharacterTextSplitter(
                chunk_size=self.chunk_size * 2,  # Double chunk size for CSVs
                chunk_overlap=self.chunk_overlap
            )
        
        # Standard strategies
        if self.chunking_strategy == "recursive":
            return RecursiveCharacterTextSplitter(
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap,
                separators=["\n\n", "\n", ".", "!", "?", ",", " ", ""]
            )
        elif self.chunking_strategy == "token":
            return TokenTextSplitter(
                chunk_size=self.chunk_size // 4,  # Adjust for tokens vs characters
                chunk_overlap=self.chunk_overlap // 4
            )
        elif self.chunking_strategy == "markdown":
            return MarkdownHeaderTextSplitter(
                headers_to_split_on=[
                    ("#", "header1"),
                    ("##", "header2"),
                    ("###", "header3"),
                    ("####", "header4"),
                ]
            )
        elif self.chunking_strategy == "semantic":
            logger.info(f"Using semantic chunking with chunk size {self.chunk_size}")
            return SemanticChunker(
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap
            )
        else:
            logger.warning(f"Unknown chunking strategy: {self.chunking_strategy}, falling back to recursive")
            return RecursiveCharacterTextSplitter(
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap,
                separators=["\n\n", "\n", ".", " ", ""]
            )
    
    async def process_document(self, document: Document) -> Document:
        """
        Process a document by splitting it into chunks
        """
        try:
            logger.info(f"Processing document: {document.filename}")
            
            # Get the document path
            file_path = os.path.join(UPLOAD_DIR, document.id, document.filename)
            
            # Get file extension for specialized handling
            _, ext = os.path.splitext(file_path.lower())
            
            # Use Chunking Judge if enabled
            if USE_CHUNKING_JUDGE:
                logger.info(f"Using Chunking Judge to analyze document: {document.filename}")
                chunking_judge = ChunkingJudge()
                analysis_result = await chunking_judge.analyze_document(document)
                
                # Update chunking strategy and parameters
                self.chunking_strategy = analysis_result["strategy"]
                if "parameters" in analysis_result and "chunk_size" in analysis_result["parameters"]:
                    self.chunk_size = analysis_result["parameters"]["chunk_size"]
                if "parameters" in analysis_result and "chunk_overlap" in analysis_result["parameters"]:
                    self.chunk_overlap = analysis_result["parameters"]["chunk_overlap"]
                
                # Store the chunking analysis in document metadata
                document.metadata["chunking_analysis"] = analysis_result
                
                logger.info(f"Chunking Judge recommendation: strategy={self.chunking_strategy}, " +
                           f"chunk_size={self.chunk_size}, chunk_overlap={self.chunk_overlap}")
            else:
                # Use DocumentAnalysisService if Chunking Judge is disabled
                logger.info(f"Chunking Judge disabled, using DocumentAnalysisService for document: {document.filename}")
                analysis_result = await self.document_analysis_service.analyze_document(document)
                
                # Update chunking strategy and parameters
                self.chunking_strategy = analysis_result["strategy"]
                if "parameters" in analysis_result and "chunk_size" in analysis_result["parameters"]:
                    self.chunk_size = analysis_result["parameters"]["chunk_size"]
                if "parameters" in analysis_result and "chunk_overlap" in analysis_result["parameters"]:
                    self.chunk_overlap = analysis_result["parameters"]["chunk_overlap"]
                
                # Store the document analysis in document metadata
                document.metadata["document_analysis"] = analysis_result
                
                logger.info(f"Document analysis recommendation: strategy={self.chunking_strategy}, " +
                           f"chunk_size={self.chunk_size}, chunk_overlap={self.chunk_overlap}")
            
            # Get appropriate text splitter for this file type
            self.text_splitter = self._get_text_splitter(ext)
            
            # Extract text from the document based on file type
            docs = await self._load_document(file_path)
            
            # Split the document into chunks
            chunks = self._split_document(docs)
            
            # Update the document with chunks
            document.chunks = []
            for i, chunk in enumerate(chunks):
                # Start with the chunk's existing metadata
                metadata = dict(chunk.metadata) if chunk.metadata else {}
                
                # Add document metadata
                metadata.update({
                    "document_id": document.id,
                    "index": i,
                    "folder": document.folder
                })
                
                # Handle tags specially - store as string for ChromaDB compatibility
                if document.tags:
                    metadata["tags_list"] = document.tags  # Keep original list for internal use
                    metadata["tags"] = ",".join(document.tags)  # String version for ChromaDB
                else:
                    metadata["tags"] = ""
                    metadata["tags_list"] = []
                
                # Create the chunk with processed metadata
                document.chunks.append(
                    Chunk(
                        content=chunk.page_content,
                        metadata=metadata
                    )
                )
            
            logger.info(f"Document processed into {len(document.chunks)} chunks")
            
            return document
        except Exception as e:
            logger.error(f"Error processing document {document.filename}: {str(e)}")
            raise
    
    async def _load_document(self, file_path: str) -> List[LangchainDocument]:
        """
        Load a document based on its file type with improved error handling
        """
        _, ext = os.path.splitext(file_path.lower())
        
        try:
            if ext == ".pdf":
                try:
                    loader = PyPDFLoader(file_path)
                    return loader.load()
                except Exception as pdf_error:
                    logger.warning(f"Error using PyPDFLoader: {str(pdf_error)}. Falling back to manual loading.")
                    # Try loading as text, but ignore decoding errors
                    with open(file_path, 'rb') as f:
                        content = f.read().decode('utf-8', errors='ignore')
                    return [LangchainDocument(page_content=content, metadata={"source": file_path})]
            elif ext == ".csv":
                loader = CSVLoader(file_path)
                return loader.load()
            elif ext == ".md":
                try:
                    loader = UnstructuredMarkdownLoader(file_path)
                    return loader.load()
                except Exception as md_error:
                    logger.warning(f"Error using UnstructuredMarkdownLoader: {str(md_error)}. Falling back to manual loading.")
                    # Try loading as text, but ignore decoding errors
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    return [LangchainDocument(page_content=content, metadata={"source": file_path})]
            else:
                # Default to text loader for txt and other files
                loader = TextLoader(file_path)
                return loader.load()
        except Exception as e:
            logger.error(f"Error loading document {file_path}: {str(e)}")
            # Create a simple document with file content to avoid complete failure
            try:
                with open(file_path, 'rb') as f:
                    content = f.read().decode('utf-8', errors='ignore')
                return [LangchainDocument(page_content=content, metadata={"source": file_path})]
            except Exception as fallback_error:
                logger.error(f"Failed to load {file_path} even with fallback: {str(fallback_error)}")
                raise
    
    def _split_document(self, docs: List[LangchainDocument]) -> List[LangchainDocument]:
        """
        Split a document into chunks with a limit on total chunks
        """
        try:
            # Split the document using the configured text splitter
            chunks = self.text_splitter.split_documents(docs)
            
            # Log the original number of chunks
            logger.info(f"Document initially split into {len(chunks)} chunks")
            
            # Limit the maximum number of chunks per document to prevent excessive chunking
            MAX_CHUNKS = 30  # Reduced from 50 to 30 to prevent excessive chunking
            
            if len(chunks) > MAX_CHUNKS:
                logger.warning(f"Document produced {len(chunks)} chunks, limiting to {MAX_CHUNKS}")
                
                # Option 1: Simply truncate to the first MAX_CHUNKS
                # return chunks[:MAX_CHUNKS]
                
                # Option 2: Take evenly distributed chunks to maintain coverage of the document
                step = len(chunks) // MAX_CHUNKS
                limited_chunks = [chunks[i] for i in range(0, len(chunks), step)][:MAX_CHUNKS]
                
                # Ensure we have exactly MAX_CHUNKS or fewer
                return limited_chunks[:MAX_CHUNKS]
            
            return chunks
        except Exception as e:
            logger.error(f"Error splitting document: {str(e)}")
            raise
    
    def extract_metadata(self, file_path: str) -> Dict[str, Any]:
        """
        Extract metadata from a document
        """
        try:
            _, ext = os.path.splitext(file_path.lower())
            file_stats = os.stat(file_path)
            
            metadata = {
                "file_size": file_stats.st_size,
                "file_type": ext[1:] if ext else "unknown",
                "created_at": file_stats.st_ctime,
                "modified_at": file_stats.st_mtime
            }
            
            # Add file type-specific metadata extraction here
            if ext == ".pdf":
                try:
                    # Extract PDF-specific metadata if possible
                    import pypdf
                    with open(file_path, 'rb') as f:
                        pdf = pypdf.PdfReader(f)
                        if pdf.metadata:
                            for key, value in pdf.metadata.items():
                                if key and value:
                                    # Clean up the key name
                                    clean_key = key.strip('/').lower()
                                    metadata[clean_key] = str(value)
                except Exception as e:
                    logger.warning(f"Error extracting PDF metadata: {str(e)}")
            
            return metadata
        except Exception as e:
            logger.error(f"Error extracting metadata from {file_path}: {str(e)}")
            return {}