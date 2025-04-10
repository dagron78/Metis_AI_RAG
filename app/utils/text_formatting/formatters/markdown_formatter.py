"""
Markdown Formatter

This module provides the MarkdownFormatter class for formatting general
markdown text.
"""
import re
import logging
from typing import Dict, Any, Optional, List, Match

from app.utils.text_formatting.formatters.base_formatter import BaseFormatter
from app.utils.text_formatting.rules.markdown_rules import (
    PARAGRAPH_RULES,
    HEADING_RULES,
    EMPHASIS_RULES,
    LINK_RULES,
    IMAGE_RULES,
    BLOCKQUOTE_RULES,
    HORIZONTAL_RULE_RULES,
    INLINE_CODE_RULES,
    MARKDOWN_ELEMENT_PATTERNS
)

# Create a dedicated logger for markdown formatting
logger = logging.getLogger("app.utils.text_formatting.formatters.markdown_formatter")


class MarkdownFormatter(BaseFormatter):
    """
    Formatter for general markdown text
    
    This formatter handles:
    - Paragraph structure
    - Headings
    - Emphasis (bold, italic)
    - Links and images
    - Blockquotes
    - Horizontal rules
    - Inline code
    """
    
    def __init__(self):
        """Initialize the markdown formatter"""
        pass
    
    def can_format(self, text: str) -> bool:
        """
        Check if this formatter can handle the given text
        
        Args:
            text: The text to check
            
        Returns:
            True if the text contains markdown elements, False otherwise
        """
        # Check if the text contains any markdown elements
        for element_type, pattern in MARKDOWN_ELEMENT_PATTERNS.items():
            if re.search(pattern, text, re.MULTILINE):
                return True
        
        # Default to True since most text can be treated as markdown
        return True
    
    def format(self, text: str, **kwargs) -> str:
        """
        Format markdown text
        
        Args:
            text: The text to format
            **kwargs: Additional formatting options
            
        Returns:
            Properly formatted markdown text
        """
        if not text:
            logger.debug("format_markdown called with empty text")
            return text
        
        logger.debug(f"format_markdown input length: {len(text)}")
        
        # Format paragraphs
        text = self._format_paragraphs(text)
        
        # Format headings
        text = self._format_headings(text)
        
        # Format emphasis (bold, italic)
        text = self._format_emphasis(text)
        
        # Format links
        text = self._format_links(text)
        
        # Format images
        text = self._format_images(text)
        
        # Format blockquotes
        text = self._format_blockquotes(text)
        
        # Format horizontal rules
        text = self._format_horizontal_rules(text)
        
        # Format inline code
        text = self._format_inline_code(text)
        
        logger.debug(f"format_markdown output length: {len(text)}")
        
        return text
    
    def _format_paragraphs(self, text: str) -> str:
        """
        Format paragraphs in markdown text
        
        Args:
            text: The text to format
            
        Returns:
            Text with properly formatted paragraphs
        """
        # Apply paragraph formatting rules
        for rule in PARAGRAPH_RULES:
            pattern = rule.get('pattern')
            replacement = rule.get('replacement')
            flags = rule.get('flags', 0)
            if pattern and replacement:
                text = re.sub(pattern, replacement, text, flags=flags)
        
        return text
    
    def _format_headings(self, text: str) -> str:
        """
        Format headings in markdown text
        
        Args:
            text: The text to format
            
        Returns:
            Text with properly formatted headings
        """
        # Apply heading formatting rules
        for rule in HEADING_RULES:
            pattern = rule.get('pattern')
            replacement = rule.get('replacement')
            flags = rule.get('flags', 0)
            if pattern and replacement:
                text = re.sub(pattern, replacement, text, flags=flags)
        
        return text
    
    def _format_emphasis(self, text: str) -> str:
        """
        Format emphasis (bold, italic) in markdown text
        
        Args:
            text: The text to format
            
        Returns:
            Text with properly formatted emphasis
        """
        # Apply emphasis formatting rules
        for rule in EMPHASIS_RULES:
            pattern = rule.get('pattern')
            replacement = rule.get('replacement')
            flags = rule.get('flags', 0)
            if pattern and replacement:
                text = re.sub(pattern, replacement, text, flags=flags)
        
        return text
    
    def _format_links(self, text: str) -> str:
        """
        Format links in markdown text
        
        Args:
            text: The text to format
            
        Returns:
            Text with properly formatted links
        """
        # Apply link formatting rules
        for rule in LINK_RULES:
            pattern = rule.get('pattern')
            replacement = rule.get('replacement')
            flags = rule.get('flags', 0)
            if pattern and replacement:
                text = re.sub(pattern, replacement, text, flags=flags)
        
        return text
    
    def _format_images(self, text: str) -> str:
        """
        Format images in markdown text
        
        Args:
            text: The text to format
            
        Returns:
            Text with properly formatted images
        """
        # Apply image formatting rules
        for rule in IMAGE_RULES:
            pattern = rule.get('pattern')
            replacement = rule.get('replacement')
            flags = rule.get('flags', 0)
            if pattern and replacement:
                text = re.sub(pattern, replacement, text, flags=flags)
        
        return text
    
    def _format_blockquotes(self, text: str) -> str:
        """
        Format blockquotes in markdown text
        
        Args:
            text: The text to format
            
        Returns:
            Text with properly formatted blockquotes
        """
        # Apply blockquote formatting rules
        for rule in BLOCKQUOTE_RULES:
            pattern = rule.get('pattern')
            replacement = rule.get('replacement')
            flags = rule.get('flags', 0)
            if pattern and replacement:
                text = re.sub(pattern, replacement, text, flags=flags)
        
        return text
    
    def _format_horizontal_rules(self, text: str) -> str:
        """
        Format horizontal rules in markdown text
        
        Args:
            text: The text to format
            
        Returns:
            Text with properly formatted horizontal rules
        """
        # Apply horizontal rule formatting rules
        for rule in HORIZONTAL_RULE_RULES:
            pattern = rule.get('pattern')
            replacement = rule.get('replacement')
            flags = rule.get('flags', 0)
            if pattern and replacement:
                text = re.sub(pattern, replacement, text, flags=flags)
        
        return text
    
    def _format_inline_code(self, text: str) -> str:
        """
        Format inline code in markdown text
        
        Args:
            text: The text to format
            
        Returns:
            Text with properly formatted inline code
        """
        # Apply inline code formatting rules
        for rule in INLINE_CODE_RULES:
            pattern = rule.get('pattern')
            replacement = rule.get('replacement')
            flags = rule.get('flags', 0)
            if pattern and replacement:
                text = re.sub(pattern, replacement, text, flags=flags)
        
        return text
    
    def normalize_text(self, text: str) -> str:
        """
        Normalize text for better formatting and readability
        
        This is a convenience method that applies paragraph formatting rules
        
        Args:
            text: The text to normalize
            
        Returns:
            Normalized text
        """
        return self._format_paragraphs(text)
    
    def _detect_markdown_elements(self, text: str) -> Dict[str, int]:
        """
        Detect markdown elements in the given text
        
        Args:
            text: The text to analyze
            
        Returns:
            Dictionary with element types and their counts
        """
        element_counts = {}
        
        for element_type, pattern in MARKDOWN_ELEMENT_PATTERNS.items():
            matches = re.findall(pattern, text, re.MULTILINE)
            element_counts[element_type] = len(matches)
        
        return element_counts