# Text Formatting Architecture

## Overview

The text formatting system in Metis RAG is designed to handle various types of text formatting, including code blocks, lists, tables, and general markdown. The system follows a modular approach with clear separation of concerns between formatters and rules.

## Architecture

```
app/utils/text_formatting/
├── __init__.py                 # Exports all formatters
├── monitor.py                  # Performance tracking and analytics
├── formatters/
│   ├── __init__.py             # Exports formatter classes
│   ├── base_formatter.py       # Abstract base class with common interfaces
│   ├── code_formatter.py       # Handles code block formatting
│   ├── list_formatter.py       # Handles list formatting
│   ├── table_formatter.py      # Handles table formatting
│   └── markdown_formatter.py   # Handles general markdown formatting
└── rules/
    ├── __init__.py             # Exports rules
    ├── code_rules.py           # Rules for code formatting
    ├── list_rules.py           # Rules for list formatting
    ├── table_rules.py          # Rules for table formatting
    └── markdown_rules.py       # Rules for markdown formatting
```

## Components

### Monitor

The `TextFormattingMonitor` class in `monitor.py` tracks formatting events, providing statistics and insights into the performance of different formatting approaches. It records success, error, and fallback events, and can generate reports on formatting performance.

### Formatters

Formatters are responsible for applying formatting rules to text. Each formatter implements the `BaseFormatter` interface, which defines methods for checking if a formatter can handle a given text and for formatting the text.

- **BaseFormatter**: Abstract base class that defines the common interface for all formatters.
- **CodeFormatter**: Handles code block formatting, including language detection, proper indentation, and syntax highlighting.
- **ListFormatter**: Handles ordered and unordered lists, ensuring proper indentation and consistent formatting.
- **TableFormatter**: Handles markdown tables, ensuring proper alignment and formatting of cells.
- **MarkdownFormatter**: Handles general markdown formatting, including headings, emphasis, links, and images.

### Rules

Rules define patterns and replacements for different types of formatting. They are used by the formatters to identify and format specific elements in the text.

- **CodeRules**: Defines patterns for identifying code blocks and rules for formatting them.
- **ListRules**: Defines patterns for identifying lists and rules for formatting them.
- **TableRules**: Defines patterns for identifying tables and rules for formatting them.
- **MarkdownRules**: Defines patterns for identifying markdown elements and rules for formatting them.

## Usage

The text formatting system can be used in two ways:

1. **Direct Usage**: Import and use the formatters directly:

```python
from app.utils.text_formatting import CodeFormatter, ListFormatter

code_formatter = CodeFormatter()
formatted_text = code_formatter.format(text)
```

2. **Monitor Usage**: Use the monitor to track formatting events:

```python
from app.utils.text_formatting.monitor import get_monitor, FormattingApproach, FormattingEvent

monitor = get_monitor()
monitor.record_event(
    approach=FormattingApproach.RULE_BASED,
    event=FormattingEvent.SUCCESS,
    details={"content_type": "code"}
)
```

## Integration

The text formatting system is integrated with the RAG engine to format responses from the LLM. The `rag_generation.py` module uses the formatters to process responses before returning them to the user.