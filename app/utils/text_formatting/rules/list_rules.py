"""
List Formatting Rules

This module defines rules for formatting lists within text.
"""
import re

# Pattern to match unordered lists
UNORDERED_LIST_PATTERN = r'(?:^|\n)[ \t]*[-*+][ \t]+.+(?:\n|$)'

# Pattern to match ordered lists
ORDERED_LIST_PATTERN = r'(?:^|\n)[ \t]*\d+\.[ \t]+.+(?:\n|$)'

# List item fixes
LIST_ITEM_FIXES = [
    # Ensure proper spacing after list markers
    {"pattern": r'^([ \t]*[-*+])(\S)', "replacement": r'\1 \2', "flags": re.MULTILINE},
    {"pattern": r'^([ \t]*\d+\.)(\S)', "replacement": r'\1 \2', "flags": re.MULTILINE},
    
    # Fix inconsistent bullet points (standardize on -)
    {"pattern": r'^[ \t]*[*+][ \t]+', "replacement": r'- ', "flags": re.MULTILINE},
    
    # Fix extra spaces after bullet points
    {"pattern": r'^([ \t]*[-*+])[ \t]{2,}', "replacement": r'\1 ', "flags": re.MULTILINE},
    {"pattern": r'^([ \t]*\d+\.)[ \t]{2,}', "replacement": r'\1 ', "flags": re.MULTILINE},
    
    # Fix nested list indentation
    {"pattern": r'^([ \t]+)([-*+])', "replacement": r'  \2', "flags": re.MULTILINE},
]

# Nested list detection
NESTED_LIST_PATTERN = r'(?:^|\n)[ \t]+[-*+][ \t]+.+(?:\n|$)'

# List continuation pattern (for multi-line list items)
LIST_CONTINUATION_PATTERN = r'(?:^|\n)[ \t]+(?![-*+]|\d+\.)[ \t]*\S+.+(?:\n|$)'

# Rules for detecting list types
LIST_TYPE_RULES = {
    "unordered": {
        "pattern": UNORDERED_LIST_PATTERN,
        "marker_pattern": r'^[ \t]*[-*+][ \t]+',
        "standard_marker": "- ",
    },
    "ordered": {
        "pattern": ORDERED_LIST_PATTERN,
        "marker_pattern": r'^[ \t]*\d+\.[ \t]+',
        "standard_marker": "1. ",  # Will be replaced with the correct number
    },
    "nested": {
        "pattern": NESTED_LIST_PATTERN,
        "indentation": 2,  # Standard indentation for nested lists
    },
}

# Rules for list item content formatting
LIST_CONTENT_RULES = [
    # Fix capitalization at the beginning of list items
    {"pattern": r'^([ \t]*[-*+][ \t]+)([a-z])', "replacement": r'\1\2', "flags": re.MULTILINE},
    
    # Fix punctuation at the end of list items
    {"pattern": r'([.,:;!?])$', "replacement": r'\1', "flags": re.MULTILINE},
    
    # Fix spacing after punctuation within list items
    {"pattern": r'([.,:;!?])(\S)', "replacement": r'\1 \2', "flags": re.MULTILINE},
]