"""
Structured output models for text and code formatting
"""
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, HttpUrl


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


class TableCell(BaseModel):
    """
    Represents a cell in a table
    """
    content: str = Field(description="The content of the cell")
    is_header: bool = Field(
        default=False,
        description="Whether this cell is a header cell"
    )
    colspan: int = Field(
        default=1,
        description="Number of columns this cell spans"
    )
    rowspan: int = Field(
        default=1,
        description="Number of rows this cell spans"
    )
    align: str = Field(
        default="left",
        description="Text alignment in the cell (left, center, right)"
    )


class TableRow(BaseModel):
    """
    Represents a row in a table
    """
    cells: List[TableCell] = Field(description="The cells in this row")
    is_header_row: bool = Field(
        default=False,
        description="Whether this is a header row"
    )


class Table(BaseModel):
    """
    Represents a table with rows and cells
    """
    rows: List[TableRow] = Field(description="The rows in the table")
    caption: Optional[str] = Field(
        default=None,
        description="Optional caption for the table"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional metadata about the table"
    )


class Image(BaseModel):
    """
    Represents an image with a URL and optional caption
    """
    url: str = Field(description="URL or data URI of the image")
    alt_text: str = Field(description="Alternative text for the image")
    caption: Optional[str] = Field(
        default=None,
        description="Optional caption for the image"
    )
    width: Optional[str] = Field(
        default=None,
        description="Optional width of the image (e.g., '100px', '50%')"
    )
    height: Optional[str] = Field(
        default=None,
        description="Optional height of the image (e.g., '100px', '50%')"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional metadata about the image"
    )


class MathBlock(BaseModel):
    """
    Represents a mathematical expression using LaTeX syntax
    """
    latex: str = Field(description="LaTeX representation of the mathematical expression")
    display_mode: bool = Field(
        default=True,
        description="Whether to display as a block (true) or inline (false)"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional metadata about the math block"
    )


class FormattedResponse(BaseModel):
    """
    Structured response format that properly handles various content types
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
    tables: List[Table] = Field(
        default=[],
        description="List of tables to be inserted into the text. "
                   "Reference them in the text using {TABLE_0}, {TABLE_1}, etc."
    )
    images: List[Image] = Field(
        default=[],
        description="List of images to be inserted into the text. "
                   "Reference them in the text using {IMAGE_0}, {IMAGE_1}, etc."
    )
    math_blocks: List[MathBlock] = Field(
        default=[],
        description="List of math blocks to be inserted into the text. "
                   "Reference them in the text using {MATH_0}, {MATH_1}, etc."
    )
    preserve_paragraphs: bool = Field(
        default=True,
        description="Whether to preserve paragraph structure in the text"
    )
    theme: Optional[str] = Field(
        default=None,
        description="Optional theme for styling the response (e.g., 'light', 'dark')"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional metadata about the response"
    )