# Ollama Output Debugging Guide

This guide explains how to compare the raw output from the Ollama API call with the final processed output that your FastAPI backend sends to the frontend.

## Overview

The system has been enhanced with debugging capabilities to help you understand the transformations that happen to text as it flows through the backend:

1. **Raw Ollama Output**: The unmodified text string received directly from the Ollama LLM call
2. **Processed Backend Output**: The text after backend processing (normalization, code block formatting)
3. **Final API Response**: The text actually sent to the frontend

## Methods to Check the Logs

### Method 1: Using the Debug Scripts

We've created two scripts to help you easily check and compare the outputs:

#### Step 1: Enable Debug Logging

Run the script to enable DEBUG level logging for the relevant modules:

```bash
python scripts/enable_debug_logging.py
```

This will:
- Set the logging level to DEBUG for the relevant modules
- Configure logging to output to both console and a file (`logs/ollama_debug.log`)
- Print instructions on how to check the logs

#### Step 2: Run the Test Script

Run the script to make test requests and compare the outputs:

```bash
python scripts/check_ollama_debug_logs.py
```

This will:
- Make requests to the chat API with `debug_raw=true`
- Display the raw and processed outputs for comparison
- Save the outputs to files for easier comparison

### Method 2: Manual Checking

If you prefer to check the logs manually:

#### Step 1: Enable Debug Logging

Add the following to your `.env` file or environment variables:

```
LOG_LEVEL=DEBUG
```

#### Step 2: Make Requests with Debug Mode

When making requests to the chat API, add the `debug_raw=true` query parameter:

```
http://localhost:8000/api/query?debug_raw=true
```

Or if using curl:

```bash
curl -X POST "http://localhost:8000/api/query?debug_raw=true" \
  -H "Content-Type: application/json" \
  -d '{"message":"Write a Python function to calculate factorial","use_rag":true,"stream":false}'
```

#### Step 3: Check the Logs

The logs will contain entries with:

- `RAW OLLAMA OUTPUT (Query ID: <id>)`: The raw text from Ollama
- `PROCESSED BACKEND OUTPUT (Query ID: <id>)`: The text after backend processing
- `FINAL API RESPONSE TEXT (Query ID: <id>)`: The text sent to the frontend

Look for these entries with the same Query ID to compare the different stages.

### Method 3: Frontend Comparison

If you want to see the comparison in the frontend:

1. Make requests with `debug_raw=true`
2. The response will include both the processed text (in the `message` field) and the raw text (in the `raw_ollama_output` field)
3. You can display both versions in the UI for direct visual comparison

## Log File Locations

- Main log file: `logs/ollama_debug.log`
- Test script output: `ollama_debug_comparison.log`
- Raw output files: `raw_output_<timestamp>.txt`
- Processed output files: `processed_output_<timestamp>.txt`

## What to Look For

When comparing the outputs, pay attention to:

1. **Code Block Formatting**: How code blocks are formatted, including language tags, indentation, and syntax
2. **Paragraph Structure**: How paragraphs are preserved or modified
3. **Text Normalization**: Changes to spacing, punctuation, and other text formatting
4. **Content Differences**: Any actual content that might be added, removed, or modified

## Troubleshooting

If you don't see the debug logs:

1. Make sure the logging level is set to DEBUG
2. Check that you're looking at the correct log file
3. Verify that the modules you're interested in are configured for DEBUG logging
4. Ensure that your request includes `debug_raw=true` to get the raw output in the response

If the raw output is not included in the response:

1. Verify that you're including `debug_raw=true` in your request
2. Check that the ChatResponse model has been updated to include the `raw_ollama_output` field
3. Ensure that the RAG engine is capturing and returning the raw output