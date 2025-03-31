#!/usr/bin/env python3
"""
Runner script for the Metis RAG End-to-End test.
This script:
1. Creates necessary directories
2. Generates PDF file from text
3. Runs the end-to-end test suite
"""

import os
import sys
import subprocess
import importlib.util
import time
import shutil

def check_requirements():
    """Check if required packages are installed"""
    try:
        import reportlab
        print("✓ ReportLab is installed")
    except ImportError:
        print("✗ ReportLab is not installed. Installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "reportlab"])
        print("✓ ReportLab installed successfully")

def create_directories():
    """Create necessary directories"""
    directories = [
        "data/test_docs",
        "tests/utils",
        "test_e2e_chroma",
        "test_results"
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"✓ Directory created/verified: {directory}")

def generate_pdf():
    """Generate PDF from the text file"""
    if not os.path.exists("data/test_docs/smart_home_technical_specs.txt"):
        print("✗ Error: smart_home_technical_specs.txt not found!")
        print("  Please ensure you have created all test documents first.")
        sys.exit(1)
    
    try:
        print("Generating PDF from text file...")
        if os.path.exists("tests/utils/create_test_pdf.py"):
            # Run the script directly
            subprocess.run(
                [sys.executable, "tests/utils/create_test_pdf.py"],
                check=True
            )
            
            # Verify the PDF was created
            if os.path.exists("data/test_docs/smart_home_technical_specs.pdf"):
                print("✓ PDF file created successfully")
            else:
                print("✗ PDF file was not created")
                sys.exit(1)
        else:
            print("✗ Error: create_test_pdf.py not found!")
            sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"✗ Error generating PDF: {e}")
        sys.exit(1)

def run_e2e_test():
    """Run the end-to-end test"""
    try:
        print("\n" + "="*80)
        print("Running Metis RAG End-to-End Test")
        print("="*80 + "\n")
        
        # Check if the test script exists
        if not os.path.exists("tests/test_metis_rag_e2e.py"):
            print("✗ Error: test_metis_rag_e2e.py not found!")
            sys.exit(1)
        
        # Run the test
        start_time = time.time()
        result = subprocess.run(
            ["pytest", "-xvs", "tests/test_metis_rag_e2e.py"], 
            check=False
        )
        end_time = time.time()
        
        # Print summary
        print("\n" + "="*80)
        print(f"Test execution completed in {end_time - start_time:.2f} seconds")
        if result.returncode == 0:
            print("✓ All tests passed successfully!")
        else:
            print(f"✗ Tests failed with exit code {result.returncode}")
        print("="*80 + "\n")
        
        # Move result files to results directory
        result_files = [
            "test_e2e_upload_results.json",
            "test_e2e_single_doc_results.json",
            "test_e2e_multi_doc_results.json",
            "test_e2e_complex_results.json",
            "test_e2e_citation_results.json",
            "test_e2e_performance_results.json",
            "test_e2e_comprehensive_report.json"
        ]
        
        for file in result_files:
            if os.path.exists(file):
                shutil.move(file, os.path.join("test_results", file))
                print(f"✓ Moved {file} to test_results directory")
        
        return result.returncode
        
    except Exception as e:
        print(f"✗ Error running tests: {e}")
        return 1
def create_test_user():
    """Create test user for authentication"""
    print("Creating test user for authentication...")
    try:
        # Run the script to create a test user
        result = subprocess.run(
            [sys.executable, "scripts/create_test_user.py"],
            check=False
        )
        
        if result.returncode == 0:
            print("✓ Test user created/verified successfully")
        else:
            print(f"✗ Error creating test user (exit code {result.returncode})")
            print("  Tests may fail if authentication is required.")
    except Exception as e:
        print(f"✗ Error running create_test_user.py: {e}")
        print("  Tests may fail if authentication is required.")

def initialize_chroma_db():
    """Initialize ChromaDB for testing"""
    print("Initializing ChromaDB for testing...")
    try:
        # Run the script to initialize ChromaDB
        result = subprocess.run(
            [sys.executable, "scripts/initialize_test_chroma.py"],
            check=False
        )
        
        if result.returncode == 0:
            print("✓ ChromaDB initialized successfully")
            return True
        else:
            print(f"✗ Error initializing ChromaDB (exit code {result.returncode})")
            print("  Tests may fail if ChromaDB is not properly initialized.")
            return False
    except Exception as e:
        print(f"✗ Error running initialize_test_chroma.py: {e}")
        print("  Tests may fail if ChromaDB is not properly initialized.")
        return False

def main():
    """Main function to run the test"""
    print("\nMetis RAG End-to-End Test Runner\n")
    
    # Check requirements
    check_requirements()
    
    # Create directories
    create_directories()
    
    # Generate PDF
    generate_pdf()
    
    # Create test user
    create_test_user()
    
    # Initialize ChromaDB
    initialize_chroma_db()
    
    # Run tests
    return run_e2e_test()
    return run_e2e_test()

if __name__ == "__main__":
    sys.exit(main())