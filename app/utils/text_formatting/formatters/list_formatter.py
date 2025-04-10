"""
List Formatter

This module provides the ListFormatter class for formatting lists
within text.
"""
import re
import logging
from typing import Dict, Any, Optional, List as ListType

from app.utils.text_formatting.formatters.base_formatter import BaseFormatter
from app.utils.text_formatting.rules.list_rules import (
    UNORDERED_LIST_PATTERN,
    ORDERED_LIST_PATTERN,
    LIST_ITEM_FIXES,
    NESTED_LIST_PATTERN,
    LIST_CONTINUATION_PATTERN,
    LIST_TYPE_RULES,
    LIST_CONTENT_RULES
)

# Create a dedicated logger for list formatting
logger = logging.getLogger("app.utils.text_formatting.formatters.list_formatter")


class ListFormatter(BaseFormatter):
    """
    Formatter for lists within text
    
    This formatter handles:
    - Unordered lists (bullet points)
    - Ordered lists (numbered items)
    - Nested lists
    - Consistent indentation and spacing
    """
    
    def __init__(self):
        """Initialize the list formatter"""
        pass
    
    def can_format(self, text: str) -> bool:
        """
        Check if this formatter can handle the given text
        
        Args:
            text: The text to check
            
        Returns:
            True if the text contains lists, False otherwise
        """
        # Check if the text contains unordered or ordered lists
        return bool(re.search(UNORDERED_LIST_PATTERN, text, re.MULTILINE)) or \
               bool(re.search(ORDERED_LIST_PATTERN, text, re.MULTILINE))
    
    def format(self, text: str, **kwargs) -> str:
        """
        Format lists within the given text
        
        Args:
            text: The text containing lists to format
            **kwargs: Additional formatting options
            
        Returns:
            Text with properly formatted lists
        """
        if not text:
            logger.debug("format_lists called with empty text")
            return text
        
        logger.debug(f"format_lists input length: {len(text)}")
        
        # Format unordered lists
        text = self._format_unordered_lists(text)
        
        # Format ordered lists
        text = self._format_ordered_lists(text)
        
        # Format nested lists
        text = self._format_nested_lists(text)
        
        # Format list content
        text = self._format_list_content(text)
        
        # Handle list continuations
        text = self._handle_list_continuations(text)
        
        logger.debug(f"format_lists output length: {len(text)}")
        
        return text
    
    def _format_unordered_lists(self, text: str) -> str:
        """
        Format unordered lists (bullet points)
        
        Args:
            text: The text containing unordered lists
            
        Returns:
            Text with properly formatted unordered lists
        """
        # Find all unordered list sections
        list_sections = re.findall(r'(?:^|\n\n)((?:[ \t]*[-*+][ \t]+.+(?:\n|$))+)', text, re.MULTILINE)
        
        for section in list_sections:
            # Process each list section
            processed_section = section
            
            # Apply list item fixes
            for fix in LIST_ITEM_FIXES:
                pattern = fix.get('pattern')
                replacement = fix.get('replacement')
                flags = fix.get('flags', 0)
                if pattern and replacement:
                    processed_section = re.sub(pattern, replacement, processed_section, flags=flags)
            
            # Ensure consistent bullet point style (use - for all items)
            processed_section = re.sub(r'^[ \t]*[*+][ \t]+', '- ', processed_section, flags=re.MULTILINE)
            
            # Ensure proper spacing after bullet points
            processed_section = re.sub(r'^([ \t]*-[ \t]*)(\S)', r'\1 \2', processed_section, flags=re.MULTILINE)
            
            # Replace the original section with the processed one
            text = text.replace(section, processed_section)
        
        return text
    
    def _format_ordered_lists(self, text: str) -> str:
        """
        Format ordered lists (numbered items)
        
        Args:
            text: The text containing ordered lists
            
        Returns:
            Text with properly formatted ordered lists
        """
        # Find all ordered list sections
        list_sections = re.findall(r'(?:^|\n\n)((?:[ \t]*\d+\.[ \t]+.+(?:\n|$))+)', text, re.MULTILINE)
        
        for section in list_sections:
            # Process each list section
            processed_section = section
            
            # Apply list item fixes
            for fix in LIST_ITEM_FIXES:
                pattern = fix.get('pattern')
                replacement = fix.get('replacement')
                flags = fix.get('flags', 0)
                if pattern and replacement:
                    processed_section = re.sub(pattern, replacement, processed_section, flags=flags)
            
            # Ensure proper numbering sequence
            lines = processed_section.split('\n')
            numbered_lines = []
            number = 1
            
            for line in lines:
                if re.match(r'[ \t]*\d+\.[ \t]+', line):
                    # Replace the number with the correct sequence number
                    numbered_line = re.sub(r'[ \t]*\d+\.[ \t]+', f"{number}. ", line)
                    numbered_lines.append(numbered_line)
                    number += 1
                else:
                    numbered_lines.append(line)
            
            processed_section = '\n'.join(numbered_lines)
            
            # Ensure proper spacing after numbers
            processed_section = re.sub(r'^([ \t]*\d+\.[ \t]*)(\S)', r'\1 \2', processed_section, flags=re.MULTILINE)
            
            # Replace the original section with the processed one
            text = text.replace(section, processed_section)
        
        return text
    
    def _format_nested_lists(self, text: str) -> str:
        """
        Format nested lists
        
        Args:
            text: The text containing nested lists
            
        Returns:
            Text with properly formatted nested lists
        """
        # Find all nested list sections
        nested_list_sections = re.findall(NESTED_LIST_PATTERN, text, re.MULTILINE)
        
        for section in nested_list_sections:
            # Process each nested list section
            processed_section = section
            
            # Apply list item fixes
            for fix in LIST_ITEM_FIXES:
                pattern = fix.get('pattern')
                replacement = fix.get('replacement')
                flags = fix.get('flags', 0)
                if pattern and replacement:
                    processed_section = re.sub(pattern, replacement, processed_section, flags=flags)
            
            # Ensure consistent indentation for nested lists
            indentation = LIST_TYPE_RULES["nested"]["indentation"]
            processed_section = re.sub(r'^([ \t]+)([-*+])', r' ' * indentation + r'\2', processed_section, flags=re.MULTILINE)
            
            # Replace the original section with the processed one
            text = text.replace(section, processed_section)
        
        return text
    
    def _format_list_content(self, text: str) -> str:
        """
        Format the content of list items
        
        Args:
            text: The text containing list items
            
        Returns:
            Text with properly formatted list item content
        """
        # Apply content formatting rules
        for rule in LIST_CONTENT_RULES:
            pattern = rule.get('pattern')
            replacement = rule.get('replacement')
            flags = rule.get('flags', 0)
            if pattern and replacement:
                text = re.sub(pattern, replacement, text, flags=flags)
        
        return text
    
    def _handle_list_continuations(self, text: str) -> str:
        """
        Handle multi-line list items (continuations)
        
        Args:
            text: The text containing list continuations
            
        Returns:
            Text with properly formatted list continuations
        """
        # Find all list continuation sections
        continuation_sections = re.findall(LIST_CONTINUATION_PATTERN, text, re.MULTILINE)
        
        for section in continuation_sections:
            # Process each continuation section
            processed_section = section
            
            # Ensure proper indentation for list continuations
            processed_section = re.sub(r'^([ \t]+)(?![-*+]|\d+\.)(.*?)$', r'    \2', processed_section, flags=re.MULTILINE)
            
            # Replace the original section with the processed one
            text = text.replace(section, processed_section)
        
        return text
    
    def _detect_list_type(self, text: str) -> str:
        """
        Detect the type of list in the given text
        
        Args:
            text: The text to analyze
            
        Returns:
            The detected list type ("unordered", "ordered", "nested", or "none")
        """
        for list_type, rule in LIST_TYPE_RULES.items():
            pattern = rule.get("pattern")
            if pattern and re.search(pattern, text, re.MULTILINE):
                return list_type
        
        return "none"