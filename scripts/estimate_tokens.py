#!/usr/bin/env python3
"""
Script to estimate the number of tokens in a file.
"""

import os
import re
import sys
import math

# Configuration
FILE_PATH = "misc/metis_rag_code_only.txt"

def count_tokens_simple(text):
    """
    Simple token count estimation based on character count.
    This is a rough approximation - actual tokenization depends on the specific tokenizer.
    
    For code, a common approximation is:
    - 1 token ≈ 4 characters (or 0.25 tokens per character)
    """
    return len(text) / 4

def count_tokens_by_words(text):
    """
    Estimate tokens based on word count.
    For English text, a common approximation is:
    - 1 token ≈ 0.75 words
    
    For code, which has more symbols and special characters:
    - 1 token ≈ 0.6 words
    """
    # Split by whitespace and punctuation
    words = re.findall(r'\b\w+\b|[^\w\s]', text)
    return len(words) * 0.6

def count_tokens_by_lines(text):
    """
    Estimate tokens based on line count.
    For code, a common approximation is:
    - 1 line ≈ 8-10 tokens
    """
    lines = text.split('\n')
    return len(lines) * 9  # Using average of 9 tokens per line

def main():
    """Main function."""
    file_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), FILE_PATH)
    
    if not os.path.exists(file_path):
        print(f"Error: File {file_path} does not exist.")
        return 1
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
            # Get file size
            file_size = os.path.getsize(file_path)
            
            # Count characters
            char_count = len(content)
            
            # Count words
            word_count = len(re.findall(r'\b\w+\b', content))
            
            # Count lines
            line_count = content.count('\n') + 1
            
            # Estimate tokens using different methods
            tokens_by_chars = count_tokens_simple(content)
            tokens_by_words = count_tokens_by_words(content)
            tokens_by_lines = count_tokens_by_lines(content)
            
            # Average of the three methods
            avg_tokens = (tokens_by_chars + tokens_by_words + tokens_by_lines) / 3
            
            # Print results
            print(f"File: {FILE_PATH}")
            print(f"Size: {file_size:,} bytes ({file_size / 1024 / 1024:.2f} MB)")
            print(f"Characters: {char_count:,}")
            print(f"Words: {word_count:,}")
            print(f"Lines: {line_count:,}")
            print("\nToken Estimates:")
            print(f"By characters: {tokens_by_chars:,.0f} tokens")
            print(f"By words: {tokens_by_words:,.0f} tokens")
            print(f"By lines: {tokens_by_lines:,.0f} tokens")
            print(f"Average estimate: {avg_tokens:,.0f} tokens")
            
            # Context windows
            print("\nContext Window Estimates:")
            for window_size in [8000, 16000, 32000, 64000, 128000]:
                windows = math.ceil(avg_tokens / window_size)
                print(f"{window_size:,} token context window: {windows} windows needed")
            
    except Exception as e:
        print(f"Error analyzing file: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())