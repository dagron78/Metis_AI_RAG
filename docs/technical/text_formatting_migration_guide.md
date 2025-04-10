# Text Formatting Migration Guide

This guide helps developers migrate from the original monolithic `text_formatting_monitor.py` to the new modular text formatting system.

## Overview of Changes

The text formatting system has been restructured from a monolithic file into a modular architecture with the following components:

- **Formatters**: Specialized components for different types of formatting
- **Rules**: Patterns and replacements for identifying and formatting specific elements
- **Monitor**: Performance tracking and analytics for formatting operations

## Import Changes

### Before

```python
from app.rag.text_formatting_monitor import get_monitor, FormattingApproach, FormattingEvent
```

### After

```python
from app.utils.text_formatting.monitor import get_monitor, FormattingApproach, FormattingEvent
```

## Using the Monitor

The monitor API remains the same for backward compatibility:

```python
# Get the monitor instance
monitor = get_monitor()

# Record a formatting event
monitor.record_event(
    approach=FormattingApproach.RULE_BASED,
    event=FormattingEvent.SUCCESS,
    details={"content_type": "code"}
)

# Record a structured output success
monitor.record_structured_output_success(
    response_size=len(text),
    content_types=["text", "code"]
)

# Record a structured output error
monitor.record_structured_output_error(
    error_message="Invalid JSON",
    processing_stage="json_parsing"
)

# Record a fallback
monitor.record_fallback(
    from_approach=FormattingApproach.STRUCTURED_OUTPUT,
    to_approach=FormattingApproach.BACKEND_PROCESSING,
    reason="JSON parsing error"
)
```

## Using the Formatters

The new system provides specialized formatters for different types of formatting:

### Code Formatter

```python
from app.utils.text_formatting.formatters.code_formatter import CodeFormatter

code_formatter = CodeFormatter()

# Check if the formatter can handle the text
if code_formatter.can_format(text):
    # Format the text
    formatted_text = code_formatter.format(text)
```

### List Formatter

```python
from app.utils.text_formatting.formatters.list_formatter import ListFormatter

list_formatter = ListFormatter()

# Format lists in the text
formatted_text = list_formatter.format(text)
```

### Table Formatter

```python
from app.utils.text_formatting.formatters.table_formatter import TableFormatter

table_formatter = TableFormatter()

# Format tables in the text
formatted_text = table_formatter.format(text)
```

### Markdown Formatter

```python
from app.utils.text_formatting.formatters.markdown_formatter import MarkdownFormatter

markdown_formatter = MarkdownFormatter()

# Format general markdown in the text
formatted_text = markdown_formatter.format(text)
```

## Using Multiple Formatters

You can chain multiple formatters to handle different types of formatting:

```python
from app.utils.text_formatting.formatters.code_formatter import CodeFormatter
from app.utils.text_formatting.formatters.list_formatter import ListFormatter
from app.utils.text_formatting.formatters.table_formatter import TableFormatter
from app.utils.text_formatting.formatters.markdown_formatter import MarkdownFormatter

# Create formatters
code_formatter = CodeFormatter()
list_formatter = ListFormatter()
table_formatter = TableFormatter()
markdown_formatter = MarkdownFormatter()

# Apply formatters in sequence
formatted_text = text
formatted_text = code_formatter.format(formatted_text)
formatted_text = list_formatter.format(formatted_text)
formatted_text = table_formatter.format(formatted_text)
formatted_text = markdown_formatter.format(formatted_text)
```

## Using the Rules

The rules are used internally by the formatters, but you can also use them directly if needed:

```python
from app.utils.text_formatting.rules.code_rules import CODE_BLOCK_PATTERN

# Use a rule pattern
import re
code_blocks = re.findall(CODE_BLOCK_PATTERN, text, re.DOTALL)
```

## Extending the System

### Creating a Custom Formatter

You can create a custom formatter by extending the `BaseFormatter` class:

```python
from app.utils.text_formatting.formatters.base_formatter import BaseFormatter

class CustomFormatter(BaseFormatter):
    def can_format(self, text: str) -> bool:
        # Check if this formatter can handle the given text
        return "custom" in text.lower()
    
    def format(self, text: str, **kwargs) -> str:
        # Format the text
        return text.replace("custom", "CUSTOM")
```

### Creating Custom Rules

You can create custom rules by defining patterns and replacements:

```python
# Define a custom rule
CUSTOM_RULE = {
    "pattern": r"custom pattern",
    "replacement": "custom replacement",
    "flags": re.IGNORECASE
}

# Apply the rule
formatted_text = re.sub(
    CUSTOM_RULE["pattern"],
    CUSTOM_RULE["replacement"],
    text,
    flags=CUSTOM_RULE.get("flags", 0)
)
```

## Testing

The text formatting system includes comprehensive tests for all formatters and rules. You can run the tests using the following command:

```bash
python -m pytest tests/unit/utils/text_formatting
```

## Troubleshooting

### Common Issues

1. **Formatting not applied**: Make sure you're using the correct formatter for the type of formatting you need.
2. **Unexpected formatting**: Check if multiple formatters are conflicting with each other.
3. **Performance issues**: Use the monitor to track formatting performance and identify bottlenecks.

### Debugging

The text formatting system includes detailed logging to help with debugging:

```python
import logging

# Enable debug logging
logging.getLogger("app.utils.text_formatting").setLevel(logging.DEBUG)

# Use a formatter
formatted_text = code_formatter.format(text)
```

## Need Help?

If you encounter any issues or have questions about the text formatting system, please contact the development team or refer to the [Text Formatting Architecture](text_formatting_architecture.md) documentation.