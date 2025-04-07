# Structured Code Output Implementation

## Overview

This document describes the implementation of structured code outputs in the Metis RAG system to solve code formatting issues, particularly with code blocks in chat responses.

## Problem Statement

The system was experiencing issues with code block formatting in chat responses. Specifically, code blocks were being rendered with incorrect closing tags:

```
```python python
def is_prime(n):
    # code here
```python
```

Instead of the correct format:

```
```python
def is_prime(n):
    # code here
```
```

This issue made code examples difficult to read, copy, and use.

## Solution: Structured Outputs

Rather than trying to fix the formatting after the fact with regex and string manipulation, we implemented a more robust solution using Ollama's structured outputs feature. This approach constrains the model's output to a specific format defined by a JSON schema, ensuring code blocks are properly formatted from the beginning.

### Key Components

1. **Structured Output Schema**: A Pydantic model that defines the structure of responses containing code blocks.
2. **System Prompt**: A specialized system prompt that instructs the model to return responses in the structured format.
3. **Response Processing**: Logic to process the structured responses and format them properly for display.

## Implementation Details

### 1. Structured Output Schema

We defined a Pydantic model in `app/models/structured_output.py` that specifies the structure for responses containing code blocks:

```python
class CodeBlock(BaseModel):
    language: str
    code: str

class FormattedResponse(BaseModel):
    text: str
    code_blocks: List[CodeBlock] = []
```

This schema allows the model to return:
- Regular text in the `text` field
- Code blocks in the `code_blocks` array, each with a language and code content
- References to code blocks in the text using placeholders like `{CODE_BLOCK_0}`

### 2. System Prompt

We created a specialized system prompt (`STRUCTURED_CODE_OUTPUT_PROMPT`) that instructs the model to return responses in the structured format:

```python
STRUCTURED_CODE_OUTPUT_PROMPT = """You are a helpful coding assistant...

STRUCTURED OUTPUT FORMAT:
You MUST return your response in the following JSON structure:

{
  "text": "Your explanation text here. Reference code blocks with {CODE_BLOCK_0}, {CODE_BLOCK_1}, etc.",
  "code_blocks": [
    {
      "language": "python",
      "code": "def example():\\n    return 'Hello World'"
    }
  ]
}
"""
```

### 3. Code Detection and Format Application

We modified the RAG engine to:
1. Detect code-related queries using the existing `_is_code_related_query` method
2. Apply the structured output format for code-related queries:

```python
if self._is_code_related_query(query):
    # For code queries, use the structured output system prompt
    system_prompt = self._create_system_prompt(query)
    
    # Set the format parameter for structured output
    model_parameters["format"] = FormattedResponse.model_json_schema()
    
    # Set temperature to 0 for more deterministic output
    model_parameters["temperature"] = 0.0
```

### 4. Response Processing

We enhanced the response processing to handle structured outputs:

```python
def _process_response_text(self, response: Dict[str, Any]) -> str:
    # Get response text
    response_text = response.get("response", "")
    
    # Check if this is a structured output response (JSON)
    try:
        # Try to parse as JSON
        structured_data = json.loads(response_text)
        
        # Validate against our schema
        formatted_response = FormattedResponse.model_validate(structured_data)
        
        # Process the structured response
        main_text = formatted_response.text
        
        # Replace code block placeholders with properly formatted code blocks
        for i, code_block in enumerate(formatted_response.code_blocks):
            placeholder = f"{{CODE_BLOCK_{i}}}"
            formatted_block = f"```{code_block.language}\n{code_block.code}\n```"
            main_text = main_text.replace(placeholder, formatted_block)
        
        return main_text
    except:
        # Fall back to normal processing
        pass
```

### 5. Streaming Support

For streaming responses with structured outputs, we modified the streaming logic to:
1. Detect when structured output is being used
2. Generate a complete response instead of streaming for structured outputs
3. Process the structured response and return it as a single chunk

```python
# For structured outputs, we can't stream the response directly
if is_structured_output:
    # Generate the complete response
    response = await self.ollama_client.generate(
        prompt=prompt,
        model=model,
        system_prompt=system_prompt,
        stream=False,
        parameters=model_parameters or {}
    )
    
    # Process the structured response
    processed_text = self._process_response_text(response)
    
    # Yield the processed text as a single chunk
    yield processed_text
    return
```

## Testing

We created a comprehensive test suite in `tests/test_structured_code_output.py` to verify:
1. The structured output schema works correctly
2. The RAG engine applies the format parameter for code-related queries
3. The response processing correctly handles structured outputs
4. The integration of all components works end-to-end

## Benefits

This implementation provides several benefits:

1. **Robustness**: By constraining the model's output format, we ensure consistent code block formatting.
2. **Maintainability**: The solution is more maintainable than regex-based fixes that try to correct formatting after the fact.
3. **Extensibility**: The structured output approach can be extended to handle other types of structured content.
4. **Improved User Experience**: Users receive properly formatted code blocks that are easier to read and use.

## Limitations and Future Work

1. **Streaming Limitation**: Structured outputs currently don't support true streaming, as the entire response needs to be generated before processing.
2. **Model Support**: This approach requires a model that supports the `format` parameter (Ollama models).
3. **Future Enhancement**: Consider implementing a hybrid approach that allows streaming for non-code parts while ensuring proper code block formatting.