#!/usr/bin/env python3
"""
Utility script to create a PDF file from the technical specifications text file.
This is needed because the Metis RAG system supports PDF files, and we need to
test all supported file formats in our end-to-end test.

Requirements:
pip install reportlab
"""

import os
import sys
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib import colors

def create_pdf_from_text(txt_file, pdf_file):
    """
    Create a PDF file from a text file, preserving formatting as much as possible.
    
    Args:
        txt_file: Path to the input text file
        pdf_file: Path to the output PDF file
    """
    print(f"Creating PDF from {txt_file}...")
    
    # Read the text file
    with open(txt_file, 'r') as f:
        content = f.read()
    
    # Split into lines and process
    lines = content.split('\n')
    
    # Create styles
    styles = getSampleStyleSheet()
    
    # Create a custom bullet point style
    bullet_style = styles['Normal'].clone('BulletPoint')
    bullet_style.leftIndent = 20
    bullet_style.spaceBefore = 2
    bullet_style.spaceAfter = 2
    
    # Create the PDF document
    doc = SimpleDocTemplate(
        pdf_file,
        pagesize=letter,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=72
    )
    
    # Container for document elements
    elements = []
    
    # Process line by line
    current_line_type = None
    for line in lines:
        # Skip empty lines
        if not line.strip():
            elements.append(Spacer(1, 6))
            continue
        
        # Process heading levels
        if line.startswith('# '):
            elements.append(Paragraph(line[2:], styles['Heading1']))
        elif line.startswith('## '):
            elements.append(Paragraph(line[3:], styles['Heading2']))
        elif line.startswith('### '):
            elements.append(Paragraph(line[4:], styles['Heading3']))
        # Process bullet points
        elif line.strip().startswith('- '):
            bullet_text = "• " + line.strip()[2:]
            elements.append(Paragraph(bullet_text, bullet_style))
        # Regular text
        else:
            elements.append(Paragraph(line, styles['Normal']))
    
    # Build the PDF
    doc.build(elements)
    
    print(f"PDF created successfully: {pdf_file}")

if __name__ == "__main__":
    # Ensure the utils directory exists
    os.makedirs("tests/utils", exist_ok=True)
    
    # Ensure the data/test_docs directory exists
    os.makedirs("data/test_docs", exist_ok=True)
    
    # Path to the input text file and output PDF file
    txt_file = "data/test_docs/smart_home_technical_specs.txt"
    pdf_file = "data/test_docs/smart_home_technical_specs.pdf"
    
    if not os.path.exists(txt_file):
        print(f"Error: Input file not found: {txt_file}")
        sys.exit(1)
    
    create_pdf_from_text(txt_file, pdf_file)