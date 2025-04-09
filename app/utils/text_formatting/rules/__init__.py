"""
Text Formatting Rules Package

This package contains rules for different types of text formatting.
"""

from app.utils.text_formatting.rules.code_rules import (
    CODE_BLOCK_PATTERN,
    LANGUAGE_FIXES,
    METHOD_CALL_FIXES,
    VARIABLE_NAME_FIXES,
    LANGUAGE_INFERENCE_PATTERNS
)

from app.utils.text_formatting.rules.list_rules import (
    UNORDERED_LIST_PATTERN,
    ORDERED_LIST_PATTERN,
    LIST_ITEM_FIXES,
    NESTED_LIST_PATTERN,
    LIST_CONTINUATION_PATTERN,
    LIST_TYPE_RULES,
    LIST_CONTENT_RULES
)

from app.utils.text_formatting.rules.table_rules import (
    TABLE_PATTERN,
    TABLE_ROW_PATTERN,
    TABLE_CELL_PATTERN,
    TABLE_FIXES,
    TABLE_HEADER_RULES,
    TABLE_ALIGNMENT_RULES,
    TABLE_TYPE_RULES,
    TABLE_CONTENT_RULES,
    calculate_column_widths
)

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

__all__ = [
    # Code rules
    'CODE_BLOCK_PATTERN',
    'LANGUAGE_FIXES',
    'METHOD_CALL_FIXES',
    'VARIABLE_NAME_FIXES',
    'LANGUAGE_INFERENCE_PATTERNS',
    
    # List rules
    'UNORDERED_LIST_PATTERN',
    'ORDERED_LIST_PATTERN',
    'LIST_ITEM_FIXES',
    'NESTED_LIST_PATTERN',
    'LIST_CONTINUATION_PATTERN',
    'LIST_TYPE_RULES',
    'LIST_CONTENT_RULES',
    
    # Table rules
    'TABLE_PATTERN',
    'TABLE_ROW_PATTERN',
    'TABLE_CELL_PATTERN',
    'TABLE_FIXES',
    'TABLE_HEADER_RULES',
    'TABLE_ALIGNMENT_RULES',
    'TABLE_TYPE_RULES',
    'TABLE_CONTENT_RULES',
    'calculate_column_widths',
    
    # Markdown rules
    'PARAGRAPH_RULES',
    'HEADING_RULES',
    'EMPHASIS_RULES',
    'LINK_RULES',
    'IMAGE_RULES',
    'BLOCKQUOTE_RULES',
    'HORIZONTAL_RULE_RULES',
    'INLINE_CODE_RULES',
    'MARKDOWN_ELEMENT_PATTERNS'
]