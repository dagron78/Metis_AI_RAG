"""
Code Formatter

This module provides the CodeFormatter class for formatting code blocks
within text.
"""
import re
import logging
from typing import Dict, Any, Optional, List, Match

from app.utils.text_formatting.formatters.base_formatter import BaseFormatter
from app.utils.text_formatting.rules.code_rules import (
    CODE_BLOCK_PATTERN,
    LANGUAGE_FIXES,
    METHOD_CALL_FIXES,
    VARIABLE_NAME_FIXES,
    LANGUAGE_INFERENCE_PATTERNS
)

# Create a dedicated logger for code formatting
logger = logging.getLogger("app.utils.text_formatting.formatters.code_formatter")


class CodeFormatter(BaseFormatter):
    """
    Formatter for code blocks within text
    
    This formatter handles:
    - Proper indentation in code blocks
    - Language tag detection and normalization
    - Fixing function and variable names with spaces
    - Maintaining consistent formatting
    """
    
    def __init__(self):
        """Initialize the code formatter"""
        pass
    
    def can_format(self, text: str) -> bool:
        """
        Check if this formatter can handle the given text
        
        Args:
            text: The text to check
            
        Returns:
            True if the text contains code blocks, False otherwise
        """
        # Check if the text contains code blocks (```...```)
        return bool(re.search(CODE_BLOCK_PATTERN, text, re.DOTALL))
    
    def format(self, text: str, preserve_paragraphs: bool = True, **kwargs) -> str:
        """
        Format code blocks within the given text
        
        Args:
            text: The text containing code blocks to format
            preserve_paragraphs: Whether to preserve paragraph structure
            **kwargs: Additional formatting options
            
        Returns:
            Text with properly formatted code blocks
        """
        return self.format_code_blocks(text, preserve_paragraphs)
    
    def format_code_blocks(self, text: str, preserve_paragraphs: bool = True) -> str:
        """
        Properly format code blocks in text, handling various edge cases from LLM output.
        
        This function:
        - Ensures proper indentation in code blocks
        - Fixes function and variable names with spaces
        - Maintains consistent formatting
        - Preserves language tags for syntax highlighting
        - Handles concatenated language tags (e.g., pythonhtml)
        - Fixes duplicate language tags (e.g., ```python python)
        - Ensures proper newlines after language tags
        - Fixes method calls with spaces
        - Infers language when no tag is provided
        
        Args:
            text: The input text containing code blocks
            preserve_paragraphs: Whether to preserve the original paragraph structure
            
        Returns:
            Text with properly formatted code blocks
        """
        if not text:
            logger.debug("format_code_blocks called with empty text")
            return text
        
        logger.debug(f"format_code_blocks input length: {len(text)}")
        
        # Count code blocks before formatting
        code_blocks_before = len(re.findall(CODE_BLOCK_PATTERN, text, re.DOTALL))
        logger.debug(f"Code blocks before formatting: {code_blocks_before}")
        
        # Log paragraph structure before code block formatting
        paragraphs_before = text.count('\n\n') + 1
        logger.debug(f"Paragraphs before code block formatting: {paragraphs_before}")
        
        # Apply language tag fixes
        for fix in LANGUAGE_FIXES:
            pattern = fix.get('pattern')
            replacement = fix.get('replacement')
            if pattern and replacement:
                text = re.sub(pattern, replacement, text)
        
        # Handle duplicate language tags (e.g., ```python python)
        text = re.sub(r'```(\w+)\s+\1', r'```\1', text)
        
        # First, detect if there are code blocks without language tags
        # Pattern matches triple backticks not followed by a word character
        no_lang_pattern = r'```(?!\w)'
        
        # If we find code blocks without language tags, try to infer the language
        if re.search(no_lang_pattern, text):
            # Extract the content between the backticks to analyze
            code_content = re.search(r'```\s*(.*?)```', text, re.DOTALL)
            if code_content:
                content = code_content.group(1)
                
                # Try to infer the language based on patterns
                inferred_lang = None
                for lang, pattern in LANGUAGE_INFERENCE_PATTERNS.items():
                    if re.search(pattern, content):
                        inferred_lang = lang
                        break
                
                # Apply the inferred language tag
                if inferred_lang:
                    text = text.replace('```\n', f'```{inferred_lang}\n', 1)
                    text = text.replace('```', f'```{inferred_lang}\n', 1)  # Handle case with no newline
                else:
                    # Default to plaintext if we can't infer
                    text = text.replace('```\n', '```plaintext\n', 1)
                    text = text.replace('```', '```plaintext\n', 1)  # Handle case with no newline
        
        # Process all code blocks
        processed_text = re.sub(CODE_BLOCK_PATTERN, self._process_code_block, text, flags=re.DOTALL)
        
        # Count code blocks after formatting
        code_blocks_after = len(re.findall(CODE_BLOCK_PATTERN, processed_text, re.DOTALL))
        logger.debug(f"Code blocks after formatting: {code_blocks_after}")
        
        # Log paragraph structure after code block formatting
        paragraphs_after = processed_text.count('\n\n') + 1
        logger.debug(f"Paragraphs after code block formatting: {paragraphs_after}")
        
        # Check if paragraphs were lost during code block formatting
        if paragraphs_before > paragraphs_after:
            logger.warning(f"Paragraph count decreased during code block formatting: {paragraphs_before} -> {paragraphs_after}")
        
        # Check if code blocks were lost during formatting
        if code_blocks_before > code_blocks_after:
            logger.warning(f"Code block count decreased during formatting: {code_blocks_before} -> {code_blocks_after}")
        
        # Preserve original paragraph structure if requested
        if preserve_paragraphs and paragraphs_before != paragraphs_after:
            logger.info(f"Preserving original paragraph structure (before: {paragraphs_before}, after: {paragraphs_after})")
            
            # Split the original text and processed text into paragraphs
            original_paragraphs = text.split('\n\n')
            processed_paragraphs = processed_text.split('\n\n')
            
            # If we have more paragraphs after processing, we need to merge some
            if paragraphs_after > paragraphs_before:
                logger.debug("Merging extra paragraphs to match original structure")
                
                # A simpler approach: just use the original text and replace the code blocks
                try:
                    # First, identify code blocks in the original text
                    original_code_blocks = re.findall(r'```[\w\-+#]*\s*.*?```', text, re.DOTALL)
                    
                    # Then, identify code blocks in the processed text
                    processed_code_blocks = re.findall(r'```[\w\-+#]*\s*.*?```', processed_text, re.DOTALL)
                    
                    # If we have the same number of code blocks, we can map them directly
                    if len(original_code_blocks) == len(processed_code_blocks):
                        logger.debug(f"Mapping {len(original_code_blocks)} code blocks to their original positions")
                        
                        # Replace each original code block with its processed version
                        result_text = text
                        for i, (orig_block, proc_block) in enumerate(zip(original_code_blocks, processed_code_blocks)):
                            result_text = result_text.replace(orig_block, proc_block)
                        
                        # Use the result text instead of the processed text
                        processed_text = result_text
                    else:
                        # If we have a different number of code blocks, just keep the processed text
                        logger.debug(f"Cannot map code blocks directly: original={len(original_code_blocks)}, processed={len(processed_code_blocks)}")
                        logger.debug("Using processed text as is")
                except Exception as e:
                    logger.error(f"Error preserving paragraph structure: {str(e)}")
                    logger.debug("Using processed text as is")
                
                # Verify the paragraph count
                final_paragraphs = processed_text.count('\n\n') + 1
                logger.debug(f"Final paragraph count after merging: {final_paragraphs}")
        
        logger.debug(f"format_code_blocks output length: {len(processed_text)}")
        logger.debug(f"format_code_blocks output preview: {processed_text[:100]}...")
        
        return processed_text
    
    def _process_code_block(self, match: Match) -> str:
        """
        Process a single code block match
        
        Args:
            match: The regex match object for the code block
            
        Returns:
            Properly formatted code block
        """
        lang = match.group(1).strip()
        code = match.group(2)
        
        logger.debug(f"Processing code block with language tag: '{lang}'")
        logger.debug(f"Code block preview: {code[:50]}...")
        
        # Handle specific concatenated language tags
        original_lang = lang
        if lang == 'pythoncss':
            lang = 'css'
        elif lang == 'javascripthtml':
            lang = 'html'
        elif lang == 'pythonhtml':
            lang = 'html'
        elif lang == 'pythonjs' or lang == 'pythonjavascript':
            lang = 'javascript'
        
        if lang != original_lang:
            logger.debug(f"Fixed concatenated language tag: '{original_lang}' -> '{lang}'")
        # Handle other concatenated language tags
        elif lang:
            # Check for common concatenated language tags
            if lang.startswith('python') and len(lang) > 6:
                if 'html' in lang:
                    lang = 'html'
                elif 'css' in lang:
                    lang = 'css'
                elif 'javascript' in lang or 'js' in lang:
                    lang = 'javascript'
                else:
                    # Handle case where code starts immediately after language tag
                    # e.g., ```pythonimport math
                    code_part = lang[6:]  # Extract the part after 'python'
                    if code_part:
                        code = code_part + ("\n" if not code.startswith("\n") else "") + code
                    lang = 'python'
            elif lang.startswith('javascript') and len(lang) > 10:
                if 'html' in lang:
                    lang = 'html'
                elif 'css' in lang:
                    lang = 'css'
                else:
                    # Handle case where code starts immediately after language tag
                    code_part = lang[10:]  # Extract the part after 'javascript'
                    if code_part:
                        code = code_part + ("\n" if not code.startswith("\n") else "") + code
                    lang = 'javascript'
            elif lang.startswith('js') and len(lang) > 2:
                if 'html' in lang:
                    lang = 'html'
                elif 'css' in lang:
                    lang = 'css'
                else:
                    # Handle case where code starts immediately after language tag
                    code_part = lang[2:]  # Extract the part after 'js'
                    if code_part:
                        code = code_part + ("\n" if not code.startswith("\n") else "") + code
                    lang = 'javascript'
            elif lang.startswith('html') and len(lang) > 4:
                if 'css' in lang:
                    lang = 'css'
                elif 'javascript' in lang or 'js' in lang:
                    lang = 'javascript'
                else:
                    # Handle case where code starts immediately after language tag
                    code_part = lang[4:]  # Extract the part after 'html'
                    if code_part:
                        code = code_part + ("\n" if not code.startswith("\n") else "") + code
                    lang = 'html'
            elif lang.startswith('css') and len(lang) > 3:
                # Handle case where code starts immediately after language tag
                code_part = lang[3:]  # Extract the part after 'css'
                if code_part:
                    code = code_part + ("\n" if not code.startswith("\n") else "") + code
                lang = 'css'
        
        # Ensure code starts with a newline
        if code and not code.startswith('\n'):
            code = '\n' + code
        
        # Ensure code ends with a newline
        if code and not code.endswith('\n'):
            code = code + '\n'
        
        # Apply method call fixes
        for fix in METHOD_CALL_FIXES:
            pattern = fix.get('pattern')
            replacement = fix.get('replacement')
            if pattern and replacement:
                code = re.sub(pattern, replacement, code)
        
        # Apply variable name fixes
        for fix in VARIABLE_NAME_FIXES:
            pattern = fix.get('pattern')
            replacement = fix.get('replacement')
            if pattern and replacement:
                code = re.sub(pattern, replacement, code)
        
        # Return with proper language tag and spacing
        # Ensure there's always a newline after the language tag and before the closing backticks
        if lang:
            # Ensure we're using the correct format for code blocks
            return f'```{lang}{code}```'
        else:
            return f'```{code}```'