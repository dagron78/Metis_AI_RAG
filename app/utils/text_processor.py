import re

def normalize_text(text):
    """
    Normalize text for better formatting and readability.
    
    This function fixes common formatting issues:
    - Adds proper spacing around punctuation
    - Replaces straight apostrophes with curly ones
    - Fixes hyphenation in compound words
    - Removes spaces in function/variable names
    
    Args:
        text: The input text to normalize
        
    Returns:
        Normalized text with improved formatting
    """
    if not text:
        return text
        
    # Fix spacing around punctuation
    text = re.sub(r'([.!?,:;])([A-Za-z0-9])', r'\1 \2', text)
    
    # Fix missing spaces after punctuation
    text = re.sub(r'([A-Za-z0-9])([.!?,:;])', r'\1\2 ', text)
    
    # Fix apostrophes
    text = text.replace("'", "'")
    
    # Fix hyphenation in common terms (remove spaces around hyphens)
    text = re.sub(r'(\w+) - (\w+)', r'\1-\2', text)
    text = re.sub(r'(\w+) - (\w+) - (\w+)', r'\1-\2-\3', text)
    
    # Fix function names with spaces
    text = re.sub(r'([a-z]+) _ ([a-z]+)', r'\1_\2', text)
    
    # Fix multiple spaces
    text = re.sub(r' +', ' ', text)
    
    # Fix spacing in code blocks (preserve indentation)
    lines = text.split('\n')
    for i, line in enumerate(lines):
        # Only process non-indented lines or lines that aren't code
        if not line.startswith('    ') and not line.startswith('\t'):
            lines[i] = line
    
    return '\n'.join(lines)

def format_code_blocks(text):
    """
    Properly format code blocks in text.
    
    This function:
    - Ensures proper indentation in code blocks
    - Fixes function and variable names with spaces
    - Maintains consistent formatting
    
    Args:
        text: The input text containing code blocks
        
    Returns:
        Text with properly formatted code blocks
    """
    if not text:
        return text
        
    # Identify code blocks (between triple backticks)
    code_block_pattern = r'```(?:python)?(.*?)```'
    
    def process_code_block(match):
        code = match.group(1)
        
        # Fix function names with spaces
        code = re.sub(r'([a-z]+) _ ([a-z]+)', r'\1_\2', code)
        
        # Fix variable names with spaces
        code = re.sub(r'([a-z]+) _ ([a-z]+)', r'\1_\2', code)
        
        return f'```python{code}```'
    
    # Process all code blocks
    processed_text = re.sub(code_block_pattern, process_code_block, text, flags=re.DOTALL)
    
    return processed_text