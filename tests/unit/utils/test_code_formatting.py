"""
Test script for code formatting functionality in Metis RAG.

This script tests the code formatting functionality in the text_processor.py file,
particularly the format_code_blocks function which handles code blocks in markdown text.
"""
import sys
import os
import unittest
import re

# Add the app directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.utils.text_processor import format_code_blocks

class TestCodeFormatting(unittest.TestCase):
    """Test cases for code formatting functionality."""

    def test_basic_code_block(self):
        """Test basic code block formatting."""
        input_text = """
Here's a simple Python function:

```python
def hello_world():
    print("Hello, world!")
```
"""
        formatted_text = format_code_blocks(input_text)
        self.assertIn("```python", formatted_text)
        self.assertIn("def hello_world():", formatted_text)
        self.assertIn('print("Hello, world!")', formatted_text)

    def test_missing_language_tag(self):
        """Test handling of code blocks with missing language tag."""
        input_text = """
Here's some Python code:

```
def hello():
    print("Hello")
```
"""
        formatted_text = format_code_blocks(input_text)
        self.assertIn("```python", formatted_text)
        self.assertIn("def hello():", formatted_text)

    def test_no_newline_after_backticks(self):
        """Test handling of code blocks with no newline after backticks."""
        input_text = """
Here's some Python code:

```pythonimport math
def sqrt(x):
    return math.sqrt(x)
```
"""
        formatted_text = format_code_blocks(input_text)
        # Check that the code block is properly formatted with Python language tag
        self.assertIn("```python", formatted_text)
        # Check that the import statement is included
        self.assertIn("import math", formatted_text)

    def test_concatenated_language_tags(self):
        """Test handling of concatenated language tags."""
        input_text = """
Here's some HTML code:

```pythonhtml
<div class="container">
    <h1>Hello, world!</h1>
</div>
```
"""
        formatted_text = format_code_blocks(input_text)
        self.assertIn("```html", formatted_text)
        self.assertNotIn("```pythonhtml", formatted_text)
        self.assertIn('<div class="container">', formatted_text)

    def test_function_names_with_spaces(self):
        """Test fixing of function names with spaces."""
        input_text = """
Here's a Python function with spaces in the name:

```python
def calculate _ square _ root(n):
    return math . sqrt(n)
```
"""
        formatted_text = format_code_blocks(input_text)
        self.assertIn("calculate_square_root", formatted_text)
        self.assertIn("math.sqrt", formatted_text)
        self.assertNotIn("calculate _ square _ root", formatted_text)
        self.assertNotIn("math . sqrt", formatted_text)

    def test_method_calls_with_spaces(self):
        """Test fixing of method calls with spaces."""
        input_text = """
Here's a Python method call with spaces:

```python
result = obj . calculate_result ( param1, param2 )
data . append(item)
```
"""
        formatted_text = format_code_blocks(input_text)
        self.assertIn("result = obj.calculate_result(param1, param2)", formatted_text)
        self.assertIn("data.append(item)", formatted_text)
        self.assertNotIn("obj . calculate_result", formatted_text)

    def test_abbreviations_with_spaces(self):
        """Test fixing of abbreviations with spaces."""
        input_text = """
Here's a Python function with abbreviations:

```python
# This function calculates the average of a list of numbers
# e. g. , [1, 2, 3] would return 2.0
def calculate_average(numbers):
    # i. e. , sum divided by count
    return sum(numbers) / len(numbers)
```
"""
        formatted_text = format_code_blocks(input_text)
        self.assertIn("e.g.,", formatted_text)
        self.assertIn("i.e.,", formatted_text)
        self.assertNotIn("e. g. ,", formatted_text)
        self.assertNotIn("i. e. ,", formatted_text)

    def test_language_inference(self):
        """Test language inference for code blocks without language tags."""
        # Test Python inference
        python_text = """
```
import math
def sqrt(x):
    return math.sqrt(x)
```
"""
        formatted_python = format_code_blocks(python_text)
        self.assertIn("```python", formatted_python)

        # Test JavaScript inference
        js_text = """
```
function calculateTotal(items) {
    let total = 0;
    for (const item of items) {
        total += item;
    }
    return total;
}
```
"""
        formatted_js = format_code_blocks(js_text)
        self.assertIn("```javascript", formatted_js)

        # Test HTML inference
        html_text = """
```
<div class="container">
    <h1>Hello, world!</h1>
    <p>This is a paragraph.</p>
</div>
```
"""
        formatted_html = format_code_blocks(html_text)
        self.assertIn("```html", formatted_html)

        # Test CSS inference
        css_text = """
```
.container {
    width: 100%;
    max-width: 1200px;
    margin: 0 auto;
}
```
"""
        formatted_css = format_code_blocks(css_text)
        self.assertIn("```css", formatted_css)

    def test_duplicate_language_tags(self):
        """Test handling of duplicate language tags."""
        input_text = """
Here's some Python code:

```python python
def hello():
    print("Hello")
```
"""
        formatted_text = format_code_blocks(input_text)
        self.assertIn("```python", formatted_text)
        self.assertNotIn("```python python", formatted_text)
        self.assertIn("def hello():", formatted_text)
    
    def test_no_newline_after_language_tag_extended(self):
        """Test handling of code blocks with no newline after language tag for various languages."""
        # Test JavaScript
        js_text = """
Here's some JavaScript code:

```javascriptconst x = 1;
console.log(x);
```
"""
        formatted_js = format_code_blocks(js_text)
        # Check that the code block contains the JavaScript code
        self.assertIn("```javascript", formatted_js)
        self.assertIn("const x = 1;", formatted_js)
        
        # Test HTML
        html_text = """
Here's some HTML code:

```html<div>Hello</div>
<p>World</p>
```
"""
        formatted_html = format_code_blocks(html_text)
        # Check that the code block contains the HTML code
        self.assertIn("```html", formatted_html)
        self.assertIn("<div>Hello</div>", formatted_html)
        
        # Test CSS
        css_text = """
Here's some CSS code:

```css.container {
    width: 100%;
}
```
"""
        formatted_css = format_code_blocks(css_text)
        # Check that the code block contains the CSS code
        self.assertIn("```css", formatted_css)
        self.assertIn(".container {", formatted_css)
    
    def test_complex_concatenated_language_tags(self):
        """Test handling of complex concatenated language tags."""
        input_text = """
Here's some code with concatenated tags:

```pythoncss
.python-class {
    color: green;
}
```

```javascripthtml
<div onclick="alert('Hello')">Click me</div>
```
"""
        formatted_text = format_code_blocks(input_text)
        self.assertIn("```css", formatted_text)
        self.assertIn("```html", formatted_text)
        self.assertNotIn("```pythoncss", formatted_text)
        self.assertNotIn("```javascripthtml", formatted_text)

if __name__ == "__main__":
    unittest.main()