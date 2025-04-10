"""
Unit tests for text_processor.py
"""
import pytest
from app.utils.text_processor import format_code_blocks, normalize_text

def test_format_code_blocks_python():
    """Test format_code_blocks with Python code"""
    # Input text with Python code block
    input_text = """
Here's an example of how you could implement a function in Python to calculate square roots:

```python
import math

def calculate_square_root(n):
    \"""
    Calculate the square root of a given number.
    
    Args:
        n (float): The input number for which the square root needs to be calculated.
        
    Returns:
        float: The square root of the input number.
    \"""
    if not isinstance(n, (int, float)):
        raise ValueError("Input must be a number.")
        
    if n < 0:
        return complex(math.sqrt(-n), math.atan(0))
    else:
        return math.sqrt(n)

# Example usage
print(calculate_square_root(9))  # Output: 3.0
print(calculate_square_root(-16))  # Output: (4+0j)
```

This function uses the built-in `math.sqrt` function to calculate the square root of a given number.
"""
    
    # Format the code blocks
    formatted_text = format_code_blocks(input_text)
    
    # Check that the Python language tag is preserved
    assert "```python" in formatted_text
    
    # Check that the code block is properly formatted
    assert "import math" in formatted_text
    assert "def calculate_square_root(n):" in formatted_text
    assert "raise ValueError" in formatted_text

def test_format_code_blocks_html():
    """Test format_code_blocks with HTML code"""
    # Input text with HTML code block
    input_text = """
Here's an example of a simple HTML button:

```html
<button id="confetti-btn">Confetti Time!</button>
```
"""
    
    # Format the code blocks
    formatted_text = format_code_blocks(input_text)
    
    # Check that the HTML language tag is preserved
    assert "```html" in formatted_text
    
    # Check that the code block is properly formatted
    assert "<button id=" in formatted_text
    assert "Confetti Time!" in formatted_text

def test_format_code_blocks_css():
    """Test format_code_blocks with CSS code"""
    # Input text with CSS code block
    input_text = """
Here's some CSS styling for the button:

```css
#confetti-container {
    position: relative;
}
.confetti {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background-color: #f2c464; /* confetti color */
    opacity: 0.5;
    transform: scale(0);
    transition: all 1s ease-in-out;
}
.confetti.animate {
    transform: scale(1);
    opacity: 1;
}
```
"""
    
    # Format the code blocks
    formatted_text = format_code_blocks(input_text)
    
    # Check that the CSS language tag is preserved
    assert "```css" in formatted_text
    
    # Check that the code block is properly formatted
    assert "#confetti-container" in formatted_text
    assert "position: relative;" in formatted_text
    assert ".confetti.animate" in formatted_text

def test_format_code_blocks_javascript():
    """Test format_code_blocks with JavaScript code"""
    # Input text with JavaScript code block
    input_text = """
Here's the JavaScript code to make the button work:

```javascript
const confettiBtn = document.getElementById('confetti-btn');
const confettiContainer = document.getElementById('confetti-container');

confettiBtn.addEventListener('click', () => {
    const confetti = document.createElement('div');
    confetti.className = 'confetti';
    confettiContainer.appendChild(confetti);
    
    setTimeout(() => {
        confetti.classList.add('animate');
        setTimeout(() => {
            confetti.classList.remove('animate');
            setTimeout(() => {
                confetti.remove();
            }, 1000);
        }, 2000);
    }, 0);
});
```
"""
    
    # Format the code blocks
    formatted_text = format_code_blocks(input_text)
    
    # Check that the JavaScript language tag is preserved
    assert "```javascript" in formatted_text
    
    # Check that the code block is properly formatted
    assert "const confettiBtn" in formatted_text
    assert "addEventListener" in formatted_text
    assert "setTimeout" in formatted_text

def test_format_code_blocks_no_language():
    """Test format_code_blocks with no language tag"""
    # Input text with no language tag
    input_text = """
Here's a code example with no language tag:

```
function hello() {
    console.log("Hello, world!");
}
```
"""
    
    # Format the code blocks
    formatted_text = format_code_blocks(input_text)
    
    # Check that the code block is properly formatted
    assert "function hello()" in formatted_text
    assert "console.log" in formatted_text

def test_format_code_blocks_with_spaces():
    """Test format_code_blocks with spaces in function names"""
    # Input text with spaces in function names
    input_text = """
Here's a code example with spaces in function names:

```python
def calculate _ square _ root(n):
    return math . sqrt(n)
```
"""
    
    # Format the code blocks
    formatted_text = format_code_blocks(input_text)
    
    # Check that spaces in function names are fixed
    assert "calculate_square_root" in formatted_text
    assert "math.sqrt" in formatted_text

def test_normalize_text():
    """Test normalize_text function"""
    # Input text with formatting issues
    input_text = "This is a test.This has no space after period.And this too."
    
    # Normalize the text
    normalized_text = normalize_text(input_text)
    
    # Check that spaces are added after periods
    assert "This is a test. This has no space" in normalized_text
    assert "after period. And this too." in normalized_text