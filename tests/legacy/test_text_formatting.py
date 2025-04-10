"""
Test script for text formatting in Metis RAG.

This script tests the text formatting pipeline from raw LLM output to final display,
focusing on paragraph structure preservation and code block formatting.
"""
import sys
import os
import logging
import json
import re
from pathlib import Path

# Add the parent directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('text_formatting_test.log')
    ]
)

logger = logging.getLogger("test_text_formatting")

# Import the text processing functions
from app.utils.text_processor import normalize_text, format_code_blocks
from app.rag.rag_generation import GenerationMixin

class TextFormattingTester:
    """Test the text formatting pipeline."""
    
    def __init__(self):
        """Initialize the tester."""
        self.test_cases = []
        self.load_test_cases()
        
    def load_test_cases(self):
        """Load test cases from the test_cases directory."""
        test_cases_dir = Path(__file__).parent / "test_cases" / "text_formatting"
        
        # Create the directory if it doesn't exist
        test_cases_dir.mkdir(parents=True, exist_ok=True)
        
        # If no test cases exist, create some default ones
        if not list(test_cases_dir.glob("*.txt")):
            self.create_default_test_cases(test_cases_dir)
        
        # Load all test cases
        for test_case_file in test_cases_dir.glob("*.txt"):
            with open(test_case_file, "r", encoding="utf-8") as f:
                content = f.read()
                self.test_cases.append({
                    "name": test_case_file.stem,
                    "content": content
                })
        
        logger.info(f"Loaded {len(self.test_cases)} test cases")
    
    def create_default_test_cases(self, directory):
        """Create default test cases for testing."""
        test_cases = [
            {
                "name": "simple_paragraphs",
                "content": """This is a simple test with multiple paragraphs.

This is the second paragraph.

This is the third paragraph with a longer text that spans multiple lines.
It should be treated as a single paragraph despite having a single newline.

This is the fourth paragraph."""
            },
            {
                "name": "code_blocks",
                "content": """Here's a Python code example:

```python
def hello_world():
    print("Hello, world!")
    
hello_world()
```

And here's a JavaScript example:

```javascript
function helloWorld() {
    console.log("Hello, world!");
}

helloWorld();
```"""
            },
            {
                "name": "mixed_content",
                "content": """# Mixed Content Test

This test contains both paragraphs and code blocks.

## Section 1

Here's some text with a list:
- Item 1
- Item 2
- Item 3

## Section 2

```python
# Python code
class TestClass:
    def __init__(self):
        self.value = 42
        
    def get_value(self):
        return self.value
```

And some more text after the code block.

## Section 3

Final paragraph with some **bold** and *italic* text."""
            },
            {
                "name": "problematic_code_blocks",
                "content": """Here are some problematic code blocks:

```pythonimport math
print(math.sqrt(16))
```

```javascriptconst x = 10;
console.log(x);
```

```html<div>Hello</div>```

```css.container {
    width: 100%;
}```"""
            },
            {
                "name": "no_paragraph_breaks",
                "content": """This is a test with no paragraph breaks. It should be a single paragraph. Even though it's quite long, it doesn't have any double newlines. It just keeps going and going without any proper paragraph structure. This is exactly the kind of text we're seeing in some of our responses where paragraph breaks are lost."""
            }
        ]
        
        # Write test cases to files
        for test_case in test_cases:
            file_path = directory / f"{test_case['name']}.txt"
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(test_case["content"])
        
        logger.info(f"Created {len(test_cases)} default test cases")
    
    def analyze_text_structure(self, text):
        """Analyze the structure of the text."""
        result = {
            "length": len(text),
            "paragraphs": text.count("\n\n") + 1,
            "single_newlines": text.count("\n"),
            "double_newlines": text.count("\n\n"),
            "code_blocks": len(re.findall(r"```[\w\-+#]*\s*[\s\S]*?```", text, re.DOTALL)),
        }
        
        # Extract the first few paragraphs
        paragraphs = text.split("\n\n")
        result["first_paragraphs"] = [p[:100] + "..." if len(p) > 100 else p for p in paragraphs[:3]]
        
        return result
    
    def test_normalize_text(self, text):
        """Test the normalize_text function."""
        logger.info("Testing normalize_text function")
        
        # Analyze before normalization
        before = self.analyze_text_structure(text)
        logger.info(f"Before normalization: {json.dumps(before, indent=2)}")
        
        # Apply normalization
        normalized = normalize_text(text)
        
        # Analyze after normalization
        after = self.analyze_text_structure(normalized)
        logger.info(f"After normalization: {json.dumps(after, indent=2)}")
        
        # Check if paragraphs were preserved
        if before["paragraphs"] != after["paragraphs"]:
            logger.warning(f"Paragraph count changed: {before['paragraphs']} -> {after['paragraphs']}")
        
        return normalized
    
    def test_format_code_blocks(self, text):
        """Test the format_code_blocks function."""
        logger.info("Testing format_code_blocks function")
        
        # Analyze before formatting
        before = self.analyze_text_structure(text)
        logger.info(f"Before code block formatting: {json.dumps(before, indent=2)}")
        
        # Apply code block formatting
        formatted = format_code_blocks(text)
        
        # Analyze after formatting
        after = self.analyze_text_structure(formatted)
        logger.info(f"After code block formatting: {json.dumps(after, indent=2)}")
        
        # Check if paragraphs were preserved
        if before["paragraphs"] != after["paragraphs"]:
            logger.warning(f"Paragraph count changed: {before['paragraphs']} -> {after['paragraphs']}")
        
        # Check if code blocks were preserved
        if before["code_blocks"] != after["code_blocks"]:
            logger.warning(f"Code block count changed: {before['code_blocks']} -> {after['code_blocks']}")
        
        return formatted
    
    def test_full_pipeline(self, text):
        """Test the full text processing pipeline."""
        logger.info("Testing full text processing pipeline")
        
        # Analyze raw text
        raw_analysis = self.analyze_text_structure(text)
        logger.info(f"Raw text analysis: {json.dumps(raw_analysis, indent=2)}")
        
        # Step 1: Normalize text
        normalized = self.test_normalize_text(text)
        
        # Step 2: Format code blocks
        formatted = self.test_format_code_blocks(normalized)
        
        # Final analysis
        final_analysis = self.analyze_text_structure(formatted)
        logger.info(f"Final text analysis: {json.dumps(final_analysis, indent=2)}")
        
        # Compare raw and final
        logger.info("Comparison of raw and final text:")
        logger.info(f"  Paragraphs: {raw_analysis['paragraphs']} -> {final_analysis['paragraphs']}")
        logger.info(f"  Code blocks: {raw_analysis['code_blocks']} -> {final_analysis['code_blocks']}")
        
        return formatted
    
    def run_tests(self):
        """Run all tests."""
        logger.info(f"Running tests on {len(self.test_cases)} test cases")
        
        results = []
        
        for i, test_case in enumerate(self.test_cases):
            logger.info(f"Test case {i+1}/{len(self.test_cases)}: {test_case['name']}")
            
            try:
                # Test the full pipeline
                processed_text = self.test_full_pipeline(test_case["content"])
                
                # Store the result
                results.append({
                    "name": test_case["name"],
                    "success": True,
                    "raw_text": test_case["content"],
                    "processed_text": processed_text
                })
                
                logger.info(f"Test case {test_case['name']} completed successfully")
            except Exception as e:
                logger.error(f"Error processing test case {test_case['name']}: {str(e)}")
                results.append({
                    "name": test_case["name"],
                    "success": False,
                    "error": str(e)
                })
        
        # Write results to file
        results_file = Path(__file__).parent / "results" / "text_formatting_results.json"
        results_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(results_file, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"Test results written to {results_file}")
        
        return results

def main():
    """Run the text formatting tests."""
    tester = TextFormattingTester()
    results = tester.run_tests()
    
    # Print summary
    success_count = sum(1 for r in results if r["success"])
    logger.info(f"Test summary: {success_count}/{len(results)} tests passed")

if __name__ == "__main__":
    main()