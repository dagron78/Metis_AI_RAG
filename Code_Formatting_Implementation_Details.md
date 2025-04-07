# Metis RAG Text Formatting: Fallback Mechanisms

## Overview

This document outlines the fallback mechanisms that will be implemented as part of our text formatting solution. These fallbacks ensure that even if the primary approach fails, users will still receive properly formatted text and code blocks.

## Layered Fallback Strategy

We will implement a multi-layered fallback strategy that provides multiple safety nets:

### Layer 1: Structured Output (Primary Approach)
- Use Ollama's structured output feature with JSON schema
- Define Pydantic models for text and code blocks
- Pass schema to model via format parameter
- Process structured response for display

### Layer 2: Backend Text Processing (First Fallback)
- If structured output fails or is unavailable:
  - Apply robust text processing in the backend
  - Use enhanced regex patterns to fix common formatting issues
  - Implement language detection for code blocks
  - Normalize text while preserving paragraph structure

### Layer 3: Frontend Markdown Parsing (Second Fallback)
- If backend processing is insufficient:
  - Configure marked.js to handle various text formats
  - Implement preprocessing for code blocks
  - Add custom renderers for different content types
  - Apply sanitization for security

### Layer 4: CSS-based Formatting (Last Resort)
- If all else fails:
  - Use CSS to improve the visual display of unformatted text
  - Apply styling to distinguish paragraphs
  - Use monospace fonts and background colors for code-like content
  - Ensure readability even with minimal formatting

## Implementation Details

### 1. Structured Output Implementation

```python
# Define Pydantic models
class CodeBlock(BaseModel):
    language: str
    code: str

class FormattedResponse(BaseModel):
    text: str
    code_blocks: List[CodeBlock] = []

# Use in RAG engine
if self._is_code_related_query(query):
    # Set the format parameter for structured output
    model_parameters["format"] = FormattedResponse.model_json_schema()
    
    # Add fallback flag to track if structured output was used
    model_parameters["_using_structured_output"] = True
```

### 2. Fallback Detection

```python
# In response processing
try:
    # Attempt to parse as structured output
    if "_using_structured_output" in model_parameters:
        structured_data = json.loads(response_text)
        formatted_response = FormattedResponse.model_validate(structured_data)
        # Process structured response...
        return processed_text
except (json.JSONDecodeError, ValidationError) as e:
    logger.warning(f"Structured output parsing failed: {str(e)}")
    # Fall back to standard text processing
    return self.process_standard_response(response_text)
```

### 3. Enhanced Text Processing Fallback

```python
def process_standard_response(self, response_text):
    """Fallback processing for when structured output fails"""
    # Apply text normalization
    normalized_text = normalize_text(response_text)
    
    # Format code blocks with paragraph preservation
    formatted_text = format_code_blocks(normalized_text, preserve_paragraphs=True)
    
    # Add metadata to indicate fallback was used
    self._last_response_used_fallback = True
    
    return formatted_text
```

#### Improved Code Block Formatting (April 7, 2025)

We've enhanced the `format_code_blocks` function to better preserve paragraph structure:

```python
def format_code_blocks(text, preserve_paragraphs=True):
    """
    Properly format code blocks in text, handling various edge cases from LLM output.
    
    Args:
        text: The input text containing code blocks
        preserve_paragraphs: Whether to preserve the original paragraph structure
        
    Returns:
        Text with properly formatted code blocks
    """
    # Process code blocks...
    
    if preserve_paragraphs and paragraphs_before != paragraphs_after:
        # A more robust approach: preserve the original paragraph structure
        try:
            # First, identify code blocks in the original text
            original_code_blocks = re.findall(r'```[\w\-+#]*\s*.*?```', text, re.DOTALL)
            
            # Then, identify code blocks in the processed text
            processed_code_blocks = re.findall(r'```[\w\-+#]*\s*.*?```', processed_text, re.DOTALL)
            
            # If we have the same number of code blocks, we can map them directly
            if len(original_code_blocks) == len(processed_code_blocks):
                # Replace each original code block with its processed version
                result_text = text
                for i, (orig_block, proc_block) in enumerate(zip(original_code_blocks, processed_code_blocks)):
                    result_text = result_text.replace(orig_block, proc_block)
                
                # Use the result text instead of the processed text
                processed_text = result_text
        except Exception as e:
            logger.error(f"Error preserving paragraph structure: {str(e)}")
    
    return processed_text
```

### 4. Frontend Fallback Configuration

```javascript
// In markdown-parser.js
// Configure marked.js with fallback options
console.log("CONFIGURING MARKED.JS OPTIONS");

// Log the current breaks setting and its impact
console.log("MARKED.JS BREAKS OPTION EXPLANATION:");
console.log("- When breaks=true: Single newlines (\\n) are converted to <br> tags");
console.log("- When breaks=false: Single newlines are ignored, double newlines (\\n\\n) create new paragraphs");
console.log("- If Ollama uses single newlines for line breaks, breaks=true is better");
console.log("- If Ollama uses double newlines for paragraphs, breaks=false might be better");

// Current setting: breaks=false (Updated April 7, 2025)
const useBreaks = false;
console.log("CURRENT SETTING: breaks=" + useBreaks);

marked.setOptions({
    highlight: function(code, lang) {
        // Use the provided language tag or fallback to plaintext
        const language = lang && hljs.getLanguage(lang) ? lang : 'plaintext';
        console.log("HIGHLIGHTING CODE WITH LANGUAGE:", language);
        
        try {
            return hljs.highlight(code, { language, ignoreIllegals: true }).value;
        } catch (e) {
            console.error('Error highlighting code:', e);
            const temp = document.createElement('div');
            temp.textContent = code;
            return temp.innerHTML; // Basic escaping
        }
    },
    breaks: useBreaks, // Only create paragraphs on double newlines (Updated April 7, 2025)
    gfm: true,    // Enable GitHub Flavored Markdown
    // Add fallback renderer
    renderer: {
        ...new marked.Renderer(),
        paragraph: function(text) {
            // Enhanced paragraph handling for better fallback formatting
            console.log("RENDERING PARAGRAPH:", text.substring(0, 50) + "...");
            return `<p class="enhanced-paragraph">${text}</p>`;
        },
        // Other renderer overrides...
    }
});

// Detect if backend processing failed to format properly
function detectFormattingIssues(text) {
    // Check for common indicators of formatting problems
    const hasUnformattedCodeBlocks = text.includes("```") && !text.includes("```\n");
    const hasLongUnbrokenParagraphs = /[.!?] [A-Z]/.test(text) && !text.includes("\n\n");
    
    return hasUnformattedCodeBlocks || hasLongUnbrokenParagraphs;
}

// Apply additional frontend formatting if needed
function applyFrontendFormatting(text) {
    if (detectFormattingIssues(text)) {
        console.log("Applying frontend formatting fallback");
        // Apply additional formatting rules
        return enhancedFormatting(text);
    }
    return text;
}
```

### 5. CSS Fallback Styling

```css
/* In styles.css */
/* Fallback styling for unformatted text */
.message-content {
    /* Ensure paragraphs have proper spacing even without <p> tags */
    white-space: pre-wrap;
    line-height: 1.6;
}

/* Add visual separation between sentences if paragraphs aren't properly formatted */
.message-content.needs-formatting {
    text-align: justify;
}

/* Improve readability of unformatted code */
.message-content pre:not(.hljs) {
    background-color: #f5f5f5;
    border: 1px solid #ddd;
    border-radius: 4px;
    padding: 10px;
    font-family: monospace;
    overflow-x: auto;
}
```

## Fallback Detection and Metrics

We will implement a system to detect when fallbacks are being used and collect metrics to help improve the primary approach:

```python
# In the API layer
@router.post("/query", response_model=ChatResponse)
async def query_chat(query: ChatQuery, ...):
    # Process query...
    
    # Check if fallback was used
    if hasattr(rag_engine, "_last_response_used_fallback") and rag_engine._last_response_used_fallback:
        # Add to response metadata
        response_metadata["used_fallback"] = True
        
        # Log for analytics
        logger.info(f"Fallback formatting used for query: {query.message[:50]}...")
        
        # Record in analytics
        await analytics_repository.log_fallback_use(
            query_id=query_id,
            fallback_type="text_formatting",
            original_query=query.message
        )
    
    return ChatResponse(...)
```

## Testing Fallback Mechanisms

We will create comprehensive tests to ensure our fallback mechanisms work correctly:

1. **Unit Tests**:
   - Test each fallback layer independently
   - Verify correct detection of formatting issues
   - Ensure proper handoff between layers

2. **Integration Tests**:
   - Test the full pipeline with forced fallbacks
   - Verify end-to-end formatting with various input types
   - Ensure consistent user experience regardless of which layer handles formatting

3. **Chaos Testing**:
   - Deliberately introduce formatting issues to trigger fallbacks
   - Simulate failures in each layer to verify fallback behavior
   - Test with malformed responses from the LLM

## Monitoring and Improvement

We will implement monitoring to track fallback usage and continuously improve the system:

1. **Fallback Usage Dashboard**:
   - Track frequency of fallback activation
   - Identify common patterns that trigger fallbacks
   - Monitor performance impact of fallbacks
   - Track paragraph structure preservation issues (Added April 7, 2025)

2. **Continuous Improvement**:
   - Analyze fallback patterns to improve primary approach
   - Update structured output schema based on common failures
   - Enhance regex patterns based on real-world usage
   - Improve code block mapping logic to handle edge cases (Added April 7, 2025)
   - Consider using marked.js extensions like marked-cjk-breaks (Added April 7, 2025)

3. **A/B Testing**:
   - Test improvements to reduce fallback frequency
   - Compare user experience with different fallback configurations
   - Optimize for both reliability and performance
   - Test marked.js with breaks: true vs. breaks: false (Added April 7, 2025)
   - Compare paragraph preservation approaches (Added April 7, 2025)

## Conclusion

By implementing this comprehensive fallback strategy, we ensure that users will receive properly formatted text and code blocks even if the primary approach fails. This multi-layered approach provides robustness and reliability while allowing us to use advanced features like structured output when available.

The fallback mechanisms are designed to be transparent to the user, providing a consistent experience regardless of which layer handles the formatting. This approach balances innovation with reliability, allowing us to push the boundaries of text formatting while maintaining a high-quality user experience.

### Recent Improvements (April 7, 2025)

Our recent work has significantly improved the text formatting capabilities of the system:

1. We've enhanced the backend processing to better preserve paragraph structure when formatting code blocks.
2. We've updated the frontend configuration to better match Ollama's output format.
3. We've added comprehensive logging throughout the pipeline to help diagnose and fix issues.
4. We've created testing tools to verify the effectiveness of our changes.

These improvements have addressed many of the issues with paragraph structure preservation and code block formatting, but there is still work to be done. We will continue to monitor the system and make further improvements as needed.