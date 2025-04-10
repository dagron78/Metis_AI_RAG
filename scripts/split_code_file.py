#!/usr/bin/env python3
"""
Script to split the large code file into smaller chunks that fit within
specific token limits for processing with language models.
"""

import os
import re
import sys
import math
from datetime import datetime

# Configuration
INPUT_FILE = "misc/metis_rag_code_only.txt"
OUTPUT_DIR = "misc/code_chunks"
DEFAULT_TOKEN_LIMIT = 32000  # Default token limit per chunk

def estimate_tokens(text):
    """
    Estimate the number of tokens in the text.
    Uses the average of three different estimation methods.
    """
    # By characters (1 token ≈ 4 characters)
    tokens_by_chars = len(text) / 4
    
    # By words (1 token ≈ 0.6 words for code)
    words = re.findall(r'\b\w+\b|[^\w\s]', text)
    tokens_by_words = len(words) * 0.6
    
    # By lines (1 line ≈ 9 tokens for code)
    lines = text.split('\n')
    tokens_by_lines = len(lines) * 9
    
    # Average of the three methods
    return (tokens_by_chars + tokens_by_words + tokens_by_lines) / 3

def split_by_files(content, token_limit):
    """
    Split the content by file boundaries, ensuring each chunk is under the token limit.
    Returns a list of chunks, where each chunk is a list of file contents.
    """
    # Find file boundaries
    file_pattern = r'={80}\nFile: (.+?)\n={80}\n(.*?)(?=\n\n={80}\nFile:|$)'
    file_matches = re.findall(file_pattern, content, re.DOTALL)
    
    chunks = []
    current_chunk = []
    current_chunk_tokens = 0
    
    for file_path, file_content in file_matches:
        # Estimate tokens for this file
        file_text = f"{'=' * 80}\nFile: {file_path}\n{'=' * 80}\n{file_content}\n\n"
        file_tokens = estimate_tokens(file_text)
        
        # If this file alone exceeds the token limit, we need to split it
        if file_tokens > token_limit:
            # If we have content in the current chunk, add it to chunks
            if current_chunk:
                chunks.append(current_chunk)
                current_chunk = []
                current_chunk_tokens = 0
            
            # Split the large file into smaller parts
            lines = file_text.split('\n')
            part_chunk = []
            part_tokens = 0
            part_num = 1
            
            for line in lines:
                line_tokens = estimate_tokens(line + '\n')
                
                if part_tokens + line_tokens > token_limit:
                    # Add header for the part
                    part_header = f"{'=' * 80}\nFile: {file_path} (Part {part_num})\n{'=' * 80}\n"
                    part_chunk.insert(0, part_header)
                    chunks.append(part_chunk)
                    
                    part_chunk = []
                    part_tokens = 0
                    part_num += 1
                
                part_chunk.append(line)
                part_tokens += line_tokens
            
            # Add the last part if it has content
            if part_chunk:
                part_header = f"{'=' * 80}\nFile: {file_path} (Part {part_num})\n{'=' * 80}\n"
                part_chunk.insert(0, part_header)
                chunks.append(part_chunk)
        
        # If adding this file would exceed the token limit, start a new chunk
        elif current_chunk_tokens + file_tokens > token_limit:
            chunks.append(current_chunk)
            current_chunk = [file_text]
            current_chunk_tokens = file_tokens
        
        # Otherwise, add this file to the current chunk
        else:
            current_chunk.append(file_text)
            current_chunk_tokens += file_tokens
    
    # Add the last chunk if it has content
    if current_chunk:
        chunks.append(current_chunk)
    
    return chunks

def write_chunks(chunks, output_dir, token_limit):
    """Write the chunks to files in the output directory."""
    os.makedirs(output_dir, exist_ok=True)
    
    for i, chunk in enumerate(chunks):
        chunk_content = ''.join(chunk)
        output_file = os.path.join(output_dir, f"code_chunk_{i+1}_of_{len(chunks)}.txt")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            # Write header
            f.write(f"Metis RAG Code Chunk {i+1} of {len(chunks)}\n")
            f.write(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Token limit: {token_limit:,}\n")
            f.write(f"Estimated tokens: {estimate_tokens(chunk_content):,.0f}\n\n")
            
            # Write content
            f.write(chunk_content)
        
        print(f"Wrote chunk {i+1} of {len(chunks)} to {output_file}")
        print(f"  Estimated tokens: {estimate_tokens(chunk_content):,.0f}")

def main():
    """Main function."""
    # Parse command line arguments
    token_limit = DEFAULT_TOKEN_LIMIT
    if len(sys.argv) > 1:
        try:
            token_limit = int(sys.argv[1])
        except ValueError:
            print(f"Error: Invalid token limit '{sys.argv[1]}'. Using default {token_limit:,}.")
    
    input_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), INPUT_FILE)
    output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), OUTPUT_DIR)
    
    if not os.path.exists(input_file):
        print(f"Error: Input file {input_file} does not exist.")
        return 1
    
    try:
        print(f"Reading input file: {input_file}")
        with open(input_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        print(f"Splitting content with token limit: {token_limit:,}")
        chunks = split_by_files(content, token_limit)
        
        print(f"Writing {len(chunks)} chunks to {output_dir}")
        write_chunks(chunks, output_dir, token_limit)
        
        print("\nSummary:")
        print(f"Input file size: {os.path.getsize(input_file):,} bytes")
        print(f"Estimated total tokens: {estimate_tokens(content):,.0f}")
        print(f"Split into {len(chunks)} chunks with token limit {token_limit:,}")
        
    except Exception as e:
        print(f"Error processing file: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())