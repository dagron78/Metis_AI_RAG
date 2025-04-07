# Text Formatting Implementation Plan

## Executive Summary

This document outlines the implementation plan for addressing the fundamental text formatting issues in the Metis RAG system. The issues affect both regular text (paragraphs not being properly formatted) and code blocks (inconsistent formatting and language detection). The plan follows a phased approach, starting with investigation and diagnosis, followed by short-term fixes, medium-term architectural improvements, and long-term redesign considerations.

## Current Status (April 7, 2025)

### Investigation and Diagnosis Phase (Completed)

- [x] **Implement Logging Throughout the Text Processing Pipeline**
  - [x] Added detailed logging in text_processor.py for normalize_text and format_code_blocks functions
  - [x] Added logging in rag_generation.py for process_complete_response method
  - [x] Enhanced frontend logging in markdown-parser.js and chat.js
  - [x] Created test scripts to analyze text formatting issues

- [x] **Create Testing Tools**
  - [x] Developed test_text_formatting.py to analyze text structure preservation
  - [x] Created test_marked_config.html to experiment with marked.js configurations
  - [x] Added test cases for various text formatting scenarios

### Short-term Fixes (Implemented)

- [x] **Fix Backend Text Processing**
  - [x] Modified format_code_blocks() to preserve original paragraph structure
  - [x] Implemented a more robust approach to handle code blocks by mapping them to their original positions
  - [x] Fixed issues with current_paragraph reference in the code

- [x] **Optimize Markdown Parser Configuration**
  - [x] Updated marked.js configuration to use breaks: false
  - [x] This ensures only double newlines create new paragraphs, matching Ollama's output format

### Key Findings

1. **Paragraph Structure Issues**:
   - The text processing pipeline was not consistently preserving paragraph structure
   - Code block formatting was adding extra newlines, changing the paragraph count
   - The issue was most pronounced in text containing code blocks

2. **Code Block Handling**:
   - Problematic code blocks (with concatenated language tags) were not being processed correctly
   - The format_code_blocks function was adding extra newlines around code blocks
   - This was causing the paragraph count to increase

3. **Frontend Rendering**:
   - The marked.js configuration (breaks: true) was converting single newlines to <br> tags
   - This didn't match how Ollama formats paragraphs (using double newlines)
   - We've updated the configuration to breaks: false to better preserve paragraph structure

## Implementation Plan

### Phase 1: Short-term Fixes (1-2 weeks)

- [ ] **Run Diagnostic Tests**
  - [ ] Execute test_text_formatting.py to identify specific issues
  - [ ] Use test_marked_config.html to find optimal marked.js configuration
  - [ ] Analyze logs to pinpoint where paragraph structure is being lost

- [ ] **Optimize Markdown Parser Configuration**
  - [ ] Experiment with breaks: true/false setting based on test results
  - [ ] Update marked.js configuration in production code
  - [ ] Test with various text formats to ensure proper rendering

- [ ] **Enhance Backend Text Processing**
  - [ ] Modify normalize_text() to better preserve paragraph structure
  - [ ] Ensure newlines are consistently handled
  - [ ] Add specific handling for paragraph breaks

- [ ] **Implement Fallback Mechanisms**
  - [ ] Create layered fallback strategy for text formatting
  - [ ] Implement structured output as primary approach
  - [ ] Add backend text processing as first fallback
  - [ ] Configure frontend markdown parsing as second fallback
  - [ ] Use CSS-based formatting as last resort

### Phase 2: Medium-term Architectural Improvements (2-3 weeks)

- [ ] **Refactor Text Processing Pipeline**
  - [ ] Create a unified text processing module
  - [ ] Implement consistent newline handling throughout the pipeline
  - [ ] Add robust error handling and logging

- [ ] **Enhance System Prompts**
  - [ ] Update system prompts to explicitly instruct the LLM on proper text formatting
  - [ ] Add examples of correctly formatted paragraphs and code blocks
  - [ ] Test with various query types

- [ ] **Implement Text Format Verification**
  - [ ] Add a verification step to ensure proper formatting before rendering
  - [ ] Create a format correction mechanism for common issues
  - [ ] Test with various edge cases

- [ ] **Create Comprehensive Testing Framework**
  - [ ] Develop unit tests for text processing functions
  - [ ] Create integration tests for the full text processing pipeline
  - [ ] Implement automated testing for various content types

### Phase 3: Long-term Redesign (3-4 weeks)

- [ ] **Evaluate Alternative Markdown Parsers**
  - [ ] Research alternatives to marked.js
  - [ ] Compare performance and feature sets
  - [ ] Test with Ollama's output format

- [ ] **Consider Custom Text Processing Pipeline**
  - [ ] Design a custom pipeline specifically for LLM output
  - [ ] Implement specialized handling for different content types
  - [ ] Optimize for performance and reliability

- [ ] **Implement Structured Output Format**
  - [ ] Research Ollama's structured output feature
  - [ ] Design a schema for text and code content
  - [ ] Implement frontend rendering for structured output

- [ ] **Enhance User Experience**
  - [ ] Add user preferences for text display
  - [ ] Implement theme support for code highlighting
  - [ ] Add accessibility features for text content

## Testing Plan

### Unit Tests

- [ ] **Text Processing Functions**
  - [ ] Test normalize_text() with various paragraph structures
  - [ ] Test format_code_blocks() with different code formats
  - [ ] Test markdown parsing with different configurations
  - [ ] Test HTML sanitization with potentially malicious inputs
  - [ ] Test each fallback layer independently

### Integration Tests

- [ ] **End-to-End Flow**
  - [ ] Test the full flow from RAG response to rendered output
  - [ ] Verify paragraph structure is preserved throughout the pipeline
  - [ ] Test with various content types (text, code, lists, tables)
  - [ ] Test streaming vs. non-streaming behavior
  - [ ] Test the full pipeline with forced fallbacks

### Visual Regression Tests

- [ ] **UI Consistency**
  - [ ] Create baseline screenshots of properly formatted responses
  - [ ] Compare with new implementations to ensure visual consistency
  - [ ] Test across different browsers and screen sizes
  - [ ] Verify accessibility standards are met

### Chaos Testing

- [ ] **Edge Cases**
  - [ ] Deliberately introduce formatting issues to trigger fallbacks
  - [ ] Simulate failures in each layer to verify fallback behavior
  - [ ] Test with malformed responses from the LLM

## Monitoring and Improvement

- [ ] **Fallback Usage Dashboard**
  - [ ] Track frequency of fallback activation
  - [ ] Identify common patterns that trigger fallbacks
  - [ ] Monitor performance impact of fallbacks

- [ ] **Continuous Improvement**
  - [ ] Analyze fallback patterns to improve primary approach
  - [ ] Update structured output schema based on common failures
  - [ ] Enhance regex patterns based on real-world usage

- [ ] **A/B Testing**
  - [ ] Test improvements to reduce fallback frequency
  - [ ] Compare user experience with different fallback configurations
  - [ ] Optimize for both reliability and performance

## Conclusion

This implementation plan provides a comprehensive approach to addressing the fundamental text formatting issues in the Metis RAG system. By systematically analyzing the entire text processing pipeline, implementing targeted fixes, and adopting industry best practices, we can significantly improve the readability and consistency of both regular text and code blocks in chat responses.

The plan emphasizes a phased approach, starting with investigation and diagnosis to identify the root causes, followed by short-term fixes to address immediate issues, medium-term architectural improvements for more robust handling, and long-term redesign considerations for optimal performance and user experience.