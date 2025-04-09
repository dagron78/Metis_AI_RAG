"""
Table Formatting Rules

This module defines rules for formatting tables within text.
"""
import re

# Pattern to match markdown tables
TABLE_PATTERN = r'(?:^|\n)(\|.+\|\n\|[-:| ]+\|\n(?:\|.+\|\n)+)'

# Pattern to match table rows
TABLE_ROW_PATTERN = r'^\|.+\|$'

# Pattern to match table cells
TABLE_CELL_PATTERN = r'\|(.*?)(?=\|)'

# Table fixes
TABLE_FIXES = [
    # Fix missing spaces in table cells
    {"pattern": r'\|(\S)', "replacement": r'| \1'},
    {"pattern": r'(\S)\|', "replacement": r'\1 |'},
    
    # Fix alignment markers in separator row
    {"pattern": r'\|[ ]*:?-+:?[ ]*\|', "replacement": r'| --- |'},
    
    # Fix empty cells
    {"pattern": r'\|\s*\|', "replacement": r'|  |'},
]

# Table header rules
TABLE_HEADER_RULES = [
    # Ensure header row has proper formatting
    {"pattern": r'^(\|.+\|)\n(?!\|[-:| ]+\|)', "replacement": r'\1\n| --- | --- |\n', "flags": re.MULTILINE},
    
    # Fix header separator row
    {"pattern": r'^(\|.+\|)\n\|([ ]*[^-:| ]+.+)\|', "replacement": r'\1\n| --- | --- |\n|\2|', "flags": re.MULTILINE},
]

# Table alignment rules
TABLE_ALIGNMENT_RULES = {
    "left": {
        "pattern": r'^\|[ ]*:?-+[ ]*\|',
        "replacement": r'| :--- |',
    },
    "center": {
        "pattern": r'^\|[ ]*:-+:[ ]*\|',
        "replacement": r'| :---: |',
    },
    "right": {
        "pattern": r'^\|[ ]*-+:[ ]*\|',
        "replacement": r'| ---: |',
    },
}

# Rules for detecting table types
TABLE_TYPE_RULES = {
    "simple": {
        "pattern": r'(?:^|\n)(\|.+\|\n\|[-:| ]+\|\n(?:\|.+\|\n)+)',
        "min_rows": 3,  # Header + separator + at least one data row
        "min_columns": 2,
    },
    "complex": {
        "pattern": r'(?:^|\n)(\|.+\|\n\|[-:| ]+\|\n(?:\|.+\|\n){3,})',
        "min_rows": 5,  # Header + separator + at least three data rows
        "min_columns": 3,
    },
}

# Rules for table content formatting
TABLE_CONTENT_RULES = [
    # Fix capitalization in header cells
    {"pattern": r'\|([ ]*[a-z])', "replacement": r'|\1', "flags": re.MULTILINE},
    
    # Fix punctuation in cells
    {"pattern": r'([.,:;!?])\|', "replacement": r'\1 |', "flags": re.MULTILINE},
    
    # Fix spacing after punctuation within cells
    {"pattern": r'\|([ ]*)([^|]+?)([.,:;!?])([^ |])', "replacement": r'|\1\2\3 \4', "flags": re.MULTILINE},
]

# Function to calculate column widths for a table
def calculate_column_widths(table_text):
    """
    Calculate the optimal column widths for a markdown table
    
    Args:
        table_text: The markdown table text
        
    Returns:
        List of column widths
    """
    rows = re.findall(TABLE_ROW_PATTERN, table_text, re.MULTILINE)
    if not rows:
        return []
    
    # Extract cells from each row
    all_cells = []
    for row in rows:
        cells = re.findall(TABLE_CELL_PATTERN, row)
        all_cells.append([cell.strip() for cell in cells])
    
    # Calculate maximum width for each column
    num_columns = max(len(row) for row in all_cells)
    column_widths = [0] * num_columns
    
    for row in all_cells:
        for i, cell in enumerate(row):
            if i < num_columns:
                column_widths[i] = max(column_widths[i], len(cell))
    
    return column_widths