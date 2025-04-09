"""
Markdown Formatting Rules

This module defines rules for formatting markdown text.
"""
import re

# Paragraph formatting rules
PARAGRAPH_RULES = [
    # Normalize multiple newlines to double newlines
    {"pattern": r'\n{3,}', "replacement": r'\n\n'},
    
    # Ensure proper spacing after headings
    {"pattern": r'^(#+.+)\n([^#\n])', "replacement": r'\1\n\n\2', "flags": re.MULTILINE},
    
    # Ensure proper spacing before headings
    {"pattern": r'([^\n])\n(#+.+)', "replacement": r'\1\n\n\2', "flags": re.MULTILINE},
    
    # Fix spacing around punctuation
    {"pattern": r'([.!?,:;])(?!\s)([A-Za-z0-9])', "replacement": r'\1 \2'},
    {"pattern": r'([A-Za-z0-9])([.!?,:;])(?!\s)', "replacement": r'\1\2 '},
    
    # Fix hyphenation in common terms
    {"pattern": r'(\w+) - (\w+)', "replacement": r'\1-\2'},
    {"pattern": r'(\w+) - (\w+) - (\w+)', "replacement": r'\1-\2-\3'},
    
    # Fix multiple spaces
    {"pattern": r' +', "replacement": r' '},
]

# Heading formatting rules
HEADING_RULES = [
    # Ensure space after heading markers
    {"pattern": r'^(#+)([^ #])', "replacement": r'\1 \2', "flags": re.MULTILINE},
    
    # Fix inconsistent heading levels (ensure proper hierarchy)
    {"pattern": r'^# (.+)', "replacement": r'# \1', "flags": re.MULTILINE},  # Level 1
    {"pattern": r'^## (.+)', "replacement": r'## \1', "flags": re.MULTILINE},  # Level 2
    {"pattern": r'^### (.+)', "replacement": r'### \1', "flags": re.MULTILINE},  # Level 3
    {"pattern": r'^#### (.+)', "replacement": r'#### \1', "flags": re.MULTILINE},  # Level 4
    {"pattern": r'^##### (.+)', "replacement": r'##### \1', "flags": re.MULTILINE},  # Level 5
    {"pattern": r'^###### (.+)', "replacement": r'###### \1', "flags": re.MULTILINE},  # Level 6
    
    # Fix alternative heading syntax (underlined headings)
    {"pattern": r'^(.+)\n={3,}\s*$', "replacement": r'# \1', "flags": re.MULTILINE},  # Level 1
    {"pattern": r'^(.+)\n-{3,}\s*$', "replacement": r'## \1', "flags": re.MULTILINE},  # Level 2
]

# Emphasis formatting rules
EMPHASIS_RULES = [
    # Fix inconsistent emphasis markers (standardize on * for italic and ** for bold)
    {"pattern": r'_([^_\n]+)_', "replacement": r'*\1*'},  # Italic with _
    {"pattern": r'__([^_\n]+)__', "replacement": r'**\1**'},  # Bold with __
    
    # Fix spaces inside emphasis markers
    {"pattern": r'\* ([^*\n]+) \*', "replacement": r'*\1*'},  # Italic
    {"pattern": r'\*\* ([^*\n]+) \*\*', "replacement": r'**\1**'},  # Bold
    
    # Fix emphasis markers without spaces
    {"pattern": r'(\w)\*(\w)', "replacement": r'\1 *\2'},  # Italic
    {"pattern": r'(\w)\*\*(\w)', "replacement": r'\1 **\2'},  # Bold
]

# Link formatting rules
LINK_RULES = [
    # Fix spaces in link text
    {"pattern": r'\[ ([^]]+) \]', "replacement": r'[\1]'},
    
    # Fix spaces in link URLs
    {"pattern": r'\]\( ([^)]+) \)', "replacement": r'](\1)'},
    
    # Fix missing spaces after links
    {"pattern": r'\)\S', "replacement": r') '},
]

# Image formatting rules
IMAGE_RULES = [
    # Fix spaces in image alt text
    {"pattern": r'!\[ ([^]]+) \]', "replacement": r'![\1]'},
    
    # Fix spaces in image URLs
    {"pattern": r'\]\( ([^)]+) \)', "replacement": r'](\1)'},
]

# Blockquote formatting rules
BLOCKQUOTE_RULES = [
    # Ensure space after blockquote marker
    {"pattern": r'^(>)([^ >])', "replacement": r'\1 \2', "flags": re.MULTILINE},
    
    # Fix nested blockquotes
    {"pattern": r'^(>+)([^ >])', "replacement": r'\1 \2', "flags": re.MULTILINE},
    
    # Ensure proper spacing around blockquotes
    {"pattern": r'([^\n])(\n>)', "replacement": r'\1\n\n>', "flags": re.MULTILINE},
    {"pattern": r'^(>.+)\n([^>\n])', "replacement": r'\1\n\n\2', "flags": re.MULTILINE},
]

# Horizontal rule formatting rules
HORIZONTAL_RULE_RULES = [
    # Standardize horizontal rules
    {"pattern": r'^-{3,}\s*$', "replacement": r'---', "flags": re.MULTILINE},
    {"pattern": r'^\*{3,}\s*$', "replacement": r'---', "flags": re.MULTILINE},
    {"pattern": r'^_{3,}\s*$', "replacement": r'---', "flags": re.MULTILINE},
    
    # Ensure proper spacing around horizontal rules
    {"pattern": r'([^\n])\n(---)', "replacement": r'\1\n\n\2', "flags": re.MULTILINE},
    {"pattern": r'^(---)\n([^\n])', "replacement": r'\1\n\n\2', "flags": re.MULTILINE},
]

# Inline code formatting rules
INLINE_CODE_RULES = [
    # Fix spaces inside inline code markers
    {"pattern": r'` ([^`\n]+) `', "replacement": r'`\1`'},
    
    # Fix missing spaces around inline code
    {"pattern": r'(\w)`', "replacement": r'\1 `'},
    {"pattern": r'`(\w)', "replacement": r'`\1'},
]

# Rules for detecting markdown elements
MARKDOWN_ELEMENT_PATTERNS = {
    "heading": r'^#+\s+.+$',
    "list_item": r'^[ \t]*[-*+][ \t]+.+$',
    "ordered_list_item": r'^[ \t]*\d+\.[ \t]+.+$',
    "blockquote": r'^>[ \t].+$',
    "code_block": r'```[\w\-+#]*\s*[\s\S]*?```',
    "inline_code": r'`[^`\n]+`',
    "link": r'\[.+?\]\(.+?\)',
    "image": r'!\[.+?\]\(.+?\)',
    "emphasis": r'\*[^*\n]+\*',
    "strong": r'\*\*[^*\n]+\*\*',
    "horizontal_rule": r'^---$',
    "table_row": r'^\|.+\|$',
}