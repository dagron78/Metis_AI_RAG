"""
Structured output models for text and code formatting
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class CodeBlock(BaseModel):
    """
    Represents a code block with language and content
    """
    language: str = Field(description="Programming language of the code block")
    code: str = Field(description="The actual code content")
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional metadata about the code block, such as filename, line numbers, etc."
    )


class TextBlock(BaseModel):
    """
    Represents a block of text with formatting information
    """
    content: str = Field(description="The text content")
    format_type: str = Field(
        default="paragraph",
        description="The type of text block (paragraph, heading, list, etc.)"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional metadata about the text block"
    )


class FormattedResponse(BaseModel):
    """
    Structured response format that properly handles text and code blocks
    """
    text: str = Field(description="The main text content of the response")
    code_blocks: List[CodeBlock] = Field(
        default=[],
        description="List of code blocks to be inserted into the text. "
                   "Reference them in the text using {CODE_BLOCK_0}, {CODE_BLOCK_1}, etc."
    )
    text_blocks: Optional[List[TextBlock]] = Field(
        default=None,
        description="Optional list of text blocks for more structured formatting. "
                   "If provided, these will be used instead of the 'text' field."
    )
    preserve_paragraphs: bool = Field(
        default=True,
        description="Whether to preserve paragraph structure in the text"
    )