# System Prompt Testing for Metis RAG

This directory contains scripts for testing different system prompts for the Metis RAG system.

## Overview

The `test_system_prompts.py` script allows you to compare the behavior of different system prompts by running the same set of queries against both the original complex prompt and the simplified prompt.

## Features

- Tests both individual queries and multi-turn conversations
- Runs predefined test scenarios to evaluate specific issues:
  - Empty Vector Store Test
  - Non-existent Document Test
  - User Information Test
  - Citation Test
- Generates detailed HTML reports with side-by-side comparisons
- Saves all results in JSON format for further analysis

## Usage

```bash
# Run all tests
python scripts/test_system_prompts.py

# Run only test queries
python scripts/test_system_prompts.py --test-queries

# Run only test scenarios
python scripts/test_system_prompts.py --test-scenarios

# Specify a custom output directory
python scripts/test_system_prompts.py --output-dir custom_results
```

## Test Queries

The script includes the following test queries based on the example chat:

1. "hello"
2. "where is Paris in comparison to Madrid"
3. "distance and direction"
4. "how can I get there from the US?"
5. "I will be leaving from Washington DC"

## Test Scenarios

The script includes the following test scenarios:

1. **Empty Vector Store Test**: Tests how the system handles queries when no documents exist
2. **Non-existent Document Test**: Tests how the system handles queries about specific documents that don't exist
3. **User Information Test**: Tests if the system remembers user information across the conversation
4. **Citation Test**: Tests how the system uses citations when documents are available

## Results

The script generates the following output:

1. JSON files with detailed test results
2. HTML reports with side-by-side comparisons of responses
3. Console output with test progress

Results are saved in the `test_results` directory by default, with a timestamp to distinguish different test runs.

## Customization

You can customize the script by:

1. Modifying the `TEST_QUERIES` list to add your own test queries
2. Adding new test scenarios to the `TEST_SCENARIOS` list
3. Implementing custom setup functions in the `setup_scenario` method

## Issues to Look For

When analyzing the results, pay attention to:

1. **Document Hallucination**: Does the system claim to have documents it doesn't have?
2. **Memory Loss**: Does the system remember user information across the conversation?
3. **Content Fabrication**: Does the system generate text instead of admitting it doesn't have information?
4. **Citation Misuse**: Does the system use citation markers correctly?
5. **Empty Results Handling**: Does the system clearly communicate when no documents are found?
6. **Response Repetition**: Does the system repeat previous responses or greetings?

## Example Issues from Sample Chat

The sample chat with the simplified prompt showed several issues:

1. **Greeting Repetition**: The system repeated "Hello there! How can I help you today? [1]" in multiple responses
2. **Citation Misuse**: The system used citation markers [1] even when it didn't seem to have actual documents
3. **Unclear Sourcing**: The system provided information without clearly indicating if it was from retrieved documents or general knowledge