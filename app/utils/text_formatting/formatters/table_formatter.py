"""
Table Formatter

This module provides the TableFormatter class for formatting tables
within text.
"""
import re
import logging
from typing import Dict, Any, Optional, List, Tuple

from app.utils.text_formatting.formatters.base_formatter import BaseFormatter
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

# Create a dedicated logger for table formatting
logger = logging.getLogger("app.utils.text_formatting.formatters.table_formatter")


class TableFormatter(BaseFormatter):
    """
    Formatter for tables within text
    
    This formatter handles:
    - Markdown tables
    - Proper alignment of columns
    - Header row formatting
    - Cell content formatting
    """
    
    def __init__(self):
        """Initialize the table formatter"""
        pass
    
    def can_format(self, text: str) -> bool:
        """
        Check if this formatter can handle the given text
        
        Args:
            text: The text to check
            
        Returns:
            True if the text contains tables, False otherwise
        """
        # Check if the text contains markdown tables
        return bool(re.search(TABLE_PATTERN, text, re.MULTILINE))
    
    def format(self, text: str, **kwargs) -> str:
        """
        Format tables within the given text
        
        Args:
            text: The text containing tables to format
            **kwargs: Additional formatting options
            
        Returns:
            Text with properly formatted tables
        """
        if not text:
            logger.debug("format_tables called with empty text")
            return text
        
        logger.debug(f"format_tables input length: {len(text)}")
        
        # Ensure tables have headers
        text = self._ensure_table_has_header(text)
        
        # Find all table sections
        table_sections = re.findall(TABLE_PATTERN, text, re.MULTILINE)
        
        for table in table_sections:
            # Process each table
            processed_table = self._format_table(table)
            
            # Format table content
            processed_table = self._format_table_content(processed_table)
            
            # Replace the original table with the processed one
            text = text.replace(table, processed_table)
        
        logger.debug(f"format_tables output length: {len(text)}")
        
        return text
    
    def _format_table(self, table: str) -> str:
        """
        Format a single markdown table
        
        Args:
            table: The markdown table to format
            
        Returns:
            Properly formatted markdown table
        """
        # Split the table into rows
        rows = re.findall(TABLE_ROW_PATTERN, table, re.MULTILINE)
        
        if not rows or len(rows) < 2:
            logger.warning("Invalid table format: not enough rows")
            return table
        
        # Extract header row, separator row, and data rows
        header_row = rows[0] if rows else ""
        separator_row = rows[1] if len(rows) > 1 else ""
        data_rows = rows[2:] if len(rows) > 2 else []
        
        # Apply table fixes
        for fix in TABLE_FIXES:
            pattern = fix.get('pattern')
            replacement = fix.get('replacement')
            if pattern and replacement:
                header_row = re.sub(pattern, replacement, header_row)
                separator_row = re.sub(pattern, replacement, separator_row)
                data_rows = [re.sub(pattern, replacement, row) for row in data_rows]
        
        # Parse header cells
        header_cells = re.findall(TABLE_CELL_PATTERN, header_row)
        header_cells = [cell.strip() for cell in header_cells]
        
        # Determine column widths
        column_widths = calculate_column_widths(table)
        
        if not column_widths:
            logger.warning("Failed to calculate column widths")
            return table
        
        # Format header row
        formatted_header = "| " + " | ".join(cell.ljust(column_widths[i]) for i, cell in enumerate(header_cells) if i < len(column_widths)) + " |"
        
        # Determine column alignments from separator row
        alignments = self._determine_alignments(separator_row)
        
        # Format separator row
        formatted_separator = "| "
        for i, width in enumerate(column_widths):
            if i < len(alignments):
                alignment = alignments[i]
                if alignment == "left":
                    formatted_separator += ":".ljust(width, "-") + " | "
                elif alignment == "right":
                    formatted_separator += "".ljust(width - 1, "-") + ":" + " | "
                elif alignment == "center":
                    formatted_separator += ":".ljust(width - 1, "-") + ":" + " | "
                else:
                    formatted_separator += "".ljust(width, "-") + " | "
            else:
                formatted_separator += "".ljust(width, "-") + " | "
        
        formatted_separator = formatted_separator.rstrip()
        
        # Format data rows
        formatted_data_rows = []
        for row in data_rows:
            cells = re.findall(TABLE_CELL_PATTERN, row)
            cells = [cell.strip() for cell in cells]
            
            formatted_row = "| "
            for i, cell in enumerate(cells):
                if i < len(column_widths):
                    width = column_widths[i]
                    if i < len(alignments):
                        alignment = alignments[i]
                        if alignment == "left":
                            formatted_row += cell.ljust(width) + " | "
                        elif alignment == "right":
                            formatted_row += cell.rjust(width) + " | "
                        elif alignment == "center":
                            padding = width - len(cell)
                            left_padding = padding // 2
                            right_padding = padding - left_padding
                            formatted_row += " " * left_padding + cell + " " * right_padding + " | "
                        else:
                            formatted_row += cell.ljust(width) + " | "
                    else:
                        formatted_row += cell.ljust(width) + " | "
                else:
                    formatted_row += cell + " | "
            
            formatted_row = formatted_row.rstrip()
            formatted_data_rows.append(formatted_row)
        
        # Combine all rows
        formatted_table = "\n".join([formatted_header, formatted_separator] + formatted_data_rows)
        
        return formatted_table
    
    def _determine_alignments(self, separator_row: str) -> List[str]:
        """
        Determine column alignments from the separator row
        
        Args:
            separator_row: The separator row of the table
            
        Returns:
            List of alignment strings ("left", "right", "center", "default")
        """
        cells = re.findall(TABLE_CELL_PATTERN, separator_row)
        alignments = []
        
        for cell in cells:
            cell = cell.strip()
            if cell.startswith(':') and cell.endswith(':'):
                alignments.append("center")
            elif cell.startswith(':'):
                alignments.append("left")
            elif cell.endswith(':'):
                alignments.append("right")
            else:
                alignments.append("default")
        
        return alignments
    
    def _detect_table_type(self, table: str) -> str:
        """
        Detect the type of table in the given text
        
        Args:
            table: The table text to analyze
            
        Returns:
            The detected table type ("simple", "complex", or "unknown")
        """
        rows = re.findall(TABLE_ROW_PATTERN, table, re.MULTILINE)
        
        if not rows:
            return "unknown"
        
        # Count rows and columns
        row_count = len(rows)
        column_count = len(re.findall(TABLE_CELL_PATTERN, rows[0])) if rows else 0
        
        # Check against table type rules
        for table_type, rule in TABLE_TYPE_RULES.items():
            min_rows = rule.get("min_rows", 0)
            min_columns = rule.get("min_columns", 0)
            
            if row_count >= min_rows and column_count >= min_columns:
                return table_type
        
        return "unknown"
    
    def _format_table_content(self, table: str) -> str:
        """
        Format the content of table cells
        
        Args:
            table: The table text
            
        Returns:
            Table with properly formatted cell content
        """
        # Apply content formatting rules
        for rule in TABLE_CONTENT_RULES:
            pattern = rule.get('pattern')
            replacement = rule.get('replacement')
            flags = rule.get('flags', 0)
            if pattern and replacement:
                table = re.sub(pattern, replacement, table, flags=flags)
        
        return table
    
    def _ensure_table_has_header(self, text: str) -> str:
        """
        Ensure the table has a proper header row
        
        Args:
            text: The text containing tables
            
        Returns:
            Text with tables that have proper header rows
        """
        # Apply header rules
        for rule in TABLE_HEADER_RULES:
            pattern = rule.get('pattern')
            replacement = rule.get('replacement')
            flags = rule.get('flags', 0)
            if pattern and replacement:
                text = re.sub(pattern, replacement, text, flags=flags)
        
        return text