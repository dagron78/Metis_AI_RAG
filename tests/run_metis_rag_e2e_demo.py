#!/usr/bin/env python3
"""
Runner script for the Metis RAG End-to-End Demo Test.
This script:
1. Creates necessary directories
2. Generates PDF file from text
3. Runs the end-to-end demo test
"""

import os
import sys
import subprocess
import time

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

def run_demo_test():
    """Run the end-to-end demo test"""
    try:
        print("\n" + "="*80)
        print("Running Metis RAG End-to-End Demo Test")
        print("="*80 + "\n")
        
        # Check if the test script exists
        if not os.path.exists("tests/test_metis_rag_e2e_demo.py"):
            print("✗ Error: test_metis_rag_e2e_demo.py not found!")
            sys.exit(1)
        
        # Run the test
        start_time = time.time()
        result = subprocess.run(
            [sys.executable, "tests/test_metis_rag_e2e_demo.py"], 
            check=False
        )
        end_time = time.time()
        
        # Print summary
        print("\n" + "="*80)
        print(f"Test execution completed in {end_time - start_time:.2f} seconds")
        if result.returncode == 0:
            print("✓ Demo test completed successfully!")
        else:
            print(f"✗ Demo test failed with exit code {result.returncode}")
        print("="*80 + "\n")
        
        # Move result files to results directory
        result_files = [
            "test_e2e_demo_upload_results.json",
            "test_e2e_demo_query_results.json",
            "test_e2e_demo_comprehensive_report.json"
        ]
        
        for file in result_files:
            if os.path.exists(file):
                # Create destination path
                dest_path = os.path.join("test_results", file)
                
                # Copy file to destination
                with open(file, 'r') as src_file:
                    content = src_file.read()
                
                with open(dest_path, 'w') as dest_file:
                    dest_file.write(content)
                
                print(f"✓ Copied {file} to test_results directory")
                
                # Remove original file
                os.remove(file)
        
        return result.returncode
        
    except Exception as e:
        print(f"✗ Error running demo test: {e}")
        return 1

def main():
    """Main function to run the test"""
    print("\nMetis RAG End-to-End Demo Test Runner\n")
    
    # Check requirements
    check_requirements()
    
    # Create directories
    create_directories()
    
    # Generate PDF
    generate_pdf()
    
    # Run demo test
    return run_demo_test()

if __name__ == "__main__":
    sys.exit(main())