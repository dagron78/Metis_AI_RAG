#!/usr/bin/env python3
"""
Script to create sample PDF and DOC files for testing Metis_RAG.
This script creates binary files that simulate PDF and DOC formats.
"""

import os
import random
import base64

def create_sample_pdf():
    """Create a sample PDF file with some binary content."""
    # This is a minimal valid PDF structure
    pdf_content = b'''%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /Resources << /Font << /F1 4 0 R >> >> /MediaBox [0 0 612 792] /Contents 5 0 R >>
endobj
4 0 obj
<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>
endobj
5 0 obj
<< /Length 68 >>
stream
BT
/F1 24 Tf
100 700 Td
(Metis RAG Performance Benchmarks) Tj
ET
endstream
endobj
xref
0 6
0000000000 65535 f
0000000010 00000 n
0000000059 00000 n
0000000118 00000 n
0000000251 00000 n
0000000319 00000 n
trailer
<< /Size 6 /Root 1 0 R >>
startxref
439
%%EOF'''
    
    # Add more content to make it at least 1000 bytes
    additional_content = b'\n'
    for i in range(50):
        line = f"Line {i}: This is sample content for testing Metis RAG with PDF files. " * 5
        additional_content += line.encode('utf-8') + b'\n'
    
    pdf_content += additional_content
    
    with open('data/test_docs/performance_benchmarks.pdf', 'wb') as f:
        f.write(pdf_content)
    
    print(f"Created sample PDF file: performance_benchmarks.pdf ({len(pdf_content)} bytes)")

def create_sample_doc():
    """Create a sample DOC file with some binary content."""
    # This is a simplified binary structure that looks like a DOC file
    doc_header = b'\xD0\xCF\x11\xE0\xA1\xB1\x1A\xE1\x00\x00\x00\x00\x00\x00\x00\x00'
    doc_header += b'\x00\x00\x00\x00\x00\x00\x00\x00\x3E\x00\x03\x00\xFE\xFF\x09\x00'
    
    # Add document content
    doc_content = b"Metis RAG Implementation Guide\r\n\r\n"
    
    # Add more content to make it at least 1000 bytes
    for i in range(50):
        line = f"Section {i}: This document provides implementation guidance for Metis RAG systems. " * 5
        doc_content += line.encode('utf-8') + b'\r\n'
    
    # Combine header and content
    doc_data = doc_header + doc_content
    
    with open('data/test_docs/implementation_guide.doc', 'wb') as f:
        f.write(doc_data)
    
    print(f"Created sample DOC file: implementation_guide.doc ({len(doc_data)} bytes)")

if __name__ == "__main__":
    create_sample_pdf()
    create_sample_doc()
    print("Sample files created successfully!")