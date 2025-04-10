# Structured Output Approach for Text Formatting: Implementation Summary

## Overview

This document summarizes the implementation of the structured output approach for addressing text formatting issues in the Metis RAG system. This approach provides a robust solution for preserving paragraph structure and properly formatting code blocks by using a structured JSON format for LLM responses.

## Key Components

### 1. Pydantic Models

We've defined Pydantic models to represent the structured output format:

```python
class CodeBlock(BaseModel):
    language: str
    code: str

class TextBlock(BaseModel):
    content: str
    format_type: str = "paragraph"  # paragraph, heading, list_item, etc.

class FormattedResponse(BaseModel):
    text: str
    code_blocks: List[CodeBlock] = []
    text_blocks: List[TextBlock] = []
    preserve_paragraphs: bool = True
```

### 2. System Prompt Enhancement

We've updated the system prompt to instruct the LLM to use the structured output format:

```python
STRUCTURED_OUTPUT_SYSTEM_PROMPT = """
You are a helpful assistant that provides responses in a structured JSON format.
Your responses should follow this structure:

{
  "text": "Main text with code block placeholders like {CODE_BLOCK_0}",
  "code_blocks": [
    {
      "language": "python",
      "code": "def hello():\\n    print('Hello, world!')"
    }
  ],
  "text_blocks": [
    {
      "content": "Heading text",
      "format_type": "heading"
    },
    {
      "content": "Paragraph text",
      "format_type": "paragraph"
    }
  ],
  "preserve_paragraphs": true
}

Use {CODE_BLOCK_n} placeholders in the main text to indicate where code blocks should be inserted.
"""
```

### 3. Backend Processing

We've enhanced the RAG generation module to process structured output:

```python
def _process_response_text(self, response):
    response_text = response.get("response", "")
    
    try:
        # Try to parse as JSON
        json_data = json.loads(response_text)
        
        # Validate against our schema
        formatted_response = FormattedResponse.model_validate(json_data)
        
        # Process the structured response
        main_text = formatted_response.text
        
        # Replace code block placeholders
        for i, code_block in enumerate(formatted_response.code_blocks):
            placeholder = f"{{CODE_BLOCK_{i}}}"
            formatted_block = f"```{code_block.language}\n{code_block.code}\n```"
            main_text = main_text.replace(placeholder, formatted_block)
        
        # Process text blocks if present
        if formatted_response.text_blocks:
            # ... process text blocks ...
        
        return main_text
    except Exception as e:
        # Fall back to normal processing
        logger.warning(f"Failed to parse structured output: {str(e)}")
        monitor = get_monitor()
        monitor.record_fallback(
            from_approach=FormattingApproach.STRUCTURED_OUTPUT,
            to_approach=FormattingApproach.BACKEND_PROCESSING,
            reason=f"Error: {str(e)}"
        )
        
        # Apply text normalization to improve formatting
        response_text = self.process_complete_response(response_text)
        
        return response_text
```

### 4. Frontend Rendering

We've updated the frontend to support structured output:

```javascript
function processResponse(text) {
    // Try to parse as JSON first
    try {
        const jsonData = JSON.parse(text);
        
        // Check if it's a structured output
        if (jsonData.text && (jsonData.code_blocks || jsonData.text_blocks)) {
            return renderStructuredOutput(jsonData);
        }
    } catch (e) {
        // Not JSON, process as markdown
        console.log("Not a structured output, processing as markdown");
    }
    
    // Fall back to markdown processing
    return marked.parse(text);
}
```

### 5. Monitoring and Analytics

We've implemented a monitoring system to track the performance of the structured output approach:

```python
class TextFormattingMonitor:
    def __init__(self, log_dir="logs/text_formatting"):
        self.log_dir = log_dir
        self.events = []
        os.makedirs(log_dir, exist_ok=True)
    
    def record_event(self, approach, event, details=None, error_message=None):
        """Record a text formatting event"""
        event_data = {
            "timestamp": datetime.now().isoformat(),
            "approach": approach.value,
            "event": event.value,
        }
        
        if details:
            event_data["details"] = details
        
        if error_message:
            event_data["error_message"] = error_message
        
        self.events.append(event_data)
    
    def record_fallback(self, from_approach, to_approach, reason):
        """Record a fallback from one approach to another"""
        self.record_event(
            approach=from_approach,
            event=FormattingEvent.FALLBACK,
            details={
                "fallback_to": to_approach.value,
                "reason": reason
            }
        )
```

## Layered Fallback Strategy

We've implemented a multi-layered fallback strategy to ensure robustness:

1. **Structured Output (Primary Approach)**
   - Use Ollama's structured output feature with JSON schema
   - Define Pydantic models for text and code blocks
   - Pass schema to model via format parameter
   - Process structured response for display

2. **Backend Text Processing (First Fallback)**
   - If structured output fails or is unavailable:
     - Apply robust text processing in the backend
     - Use enhanced regex patterns to fix common formatting issues
     - Implement language detection for code blocks
     - Normalize text while preserving paragraph structure

3. **Frontend Markdown Parsing (Second Fallback)**
   - If backend processing is insufficient:
     - Configure marked.js to handle various text formats
     - Implement preprocessing for code blocks
     - Add custom renderers for different content types
     - Apply sanitization for security

4. **CSS-based Formatting (Last Resort)**
   - If all else fails:
     - Use CSS to improve the visual display of unformatted text
     - Apply styling to distinguish paragraphs
     - Use monospace fonts and background colors for code-like content
     - Ensure readability even with minimal formatting

## Benefits

1. **Robustness**: By constraining the model's output format, we ensure consistent formatting.
2. **Maintainability**: The solution is more maintainable than regex-based fixes.
3. **Improved User Experience**: Users receive properly formatted content that is easier to read and use.
4. **Extensibility**: The approach can be extended to support more content types in the future.
5. **Monitoring**: The system provides insights into performance and failure cases.

## Future Improvements

1. **Enhance Error Handling**:
   - Improve error handling in the structured output parsing
   - Add more robust fallback mechanisms
   - Implement better logging for debugging

2. **Expand Content Type Support**:
   - Add support for more content types (tables, images, etc.)
   - Enhance the schema for better type safety
   - Improve the placeholder system for non-text content

3. **Optimize Performance**:
   - Profile the text processing pipeline
   - Identify and address performance bottlenecks
   - Optimize JSON parsing and rendering

4. **Improve Frontend Experience**:
   - Add more visual enhancements for different content types
   - Implement theme support for code highlighting
   - Add accessibility features for text content

5. **Monitoring and Analytics**:
   - Implement a dashboard to track fallback usage
   - Analyze patterns to identify common failure cases
   - Use A/B testing to compare different approaches

## Conclusion

The structured output approach has successfully addressed the fundamental text formatting issues in the Metis RAG system. By using a structured JSON format for LLM responses, we can better preserve paragraph structure and properly format code blocks.

The layered fallback strategy ensures that even if the primary approach fails, users will still receive properly formatted text and code blocks. This multi-layered approach provides robustness and reliability while allowing us to use advanced features like structured output when available.