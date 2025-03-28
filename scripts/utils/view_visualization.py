#!/usr/bin/env python3
"""
Simple script to open the Metis_RAG visualization in a browser.
"""
import os
import webbrowser
import sys
from pathlib import Path

def main():
    """Open the Metis_RAG visualization in a browser."""
    # Get the directory of this script
    script_dir = Path(os.path.dirname(os.path.abspath(__file__)))
    
    # Path to the HTML file
    html_path = script_dir / "metis_rag_visualization.html"
    
    if not html_path.exists():
        print(f"Error: Could not find {html_path}")
        sys.exit(1)
    
    # Convert to URL format
    url = f"file://{html_path.absolute()}"
    
    print(f"Opening Metis_RAG visualization in browser...")
    webbrowser.open(url)
    print(f"If the browser doesn't open automatically, you can open this file manually:")
    print(f"{html_path.absolute()}")

if __name__ == "__main__":
    main()