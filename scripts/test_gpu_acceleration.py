#!/usr/bin/env python3
"""
Script to test GPU acceleration in Metis RAG.
"""
import os
import sys
import json
import time
import requests
import subprocess
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

def check_gpu_before():
    """Check GPU utilization before the test."""
    print("Checking GPU utilization before test...")
    try:
        result = subprocess.run(["nvidia-smi", "--query-gpu=utilization.gpu,memory.used", "--format=csv,noheader"],
                               capture_output=True, text=True)
        print(f"GPU utilization before test: {result.stdout.strip()}")
        return result.stdout.strip()
    except Exception as e:
        print(f"Error checking GPU: {e}")
        return "Error"

def check_gpu_after():
    """Check GPU utilization after the test."""
    print("Checking GPU utilization after test...")
    try:
        result = subprocess.run(["nvidia-smi", "--query-gpu=utilization.gpu,memory.used", "--format=csv,noheader"],
                               capture_output=True, text=True)
        print(f"GPU utilization after test: {result.stdout.strip()}")
        return result.stdout.strip()
    except Exception as e:
        print(f"Error checking GPU: {e}")
        return "Error"

def test_ollama_directly():
    """Test Ollama directly."""
    print("\n=== Testing Ollama Directly ===")
    
    # Check GPU before
    gpu_before = check_gpu_before()
    
    # Make request to Ollama
    print("Sending request to Ollama...")
    start_time = time.time()
    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "llama2:latest",
                "prompt": "Write a short story about quantum computing",
                "stream": False,
                "gpu": True
            },
            timeout=60
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response received in {time.time() - start_time:.2f} seconds")
            print(f"Response preview: {data.get('response', '')[:100]}...")
        else:
            print(f"Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Error making request: {e}")
    
    # Check GPU after
    gpu_after = check_gpu_after()
    
    # Compare
    print(f"\nGPU utilization comparison:")
    print(f"Before: {gpu_before}")
    print(f"After: {gpu_after}")

def test_metis_rag():
    """Test Metis RAG application."""
    print("\n=== Testing Metis RAG Application ===")
    
    # Check GPU before
    gpu_before = check_gpu_before()
    
    # Make request to Metis RAG
    print("Sending request to Metis RAG...")
    start_time = time.time()
    try:
        response = requests.post(
            "http://localhost:8000/query",  # This is the endpoint used by the chat interface
            json={
                "query": "Write a short story about quantum computing"
            },
            timeout=60
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response received in {time.time() - start_time:.2f} seconds")
            print(f"Response preview: {data.get('message', '')[:100]}...")
        else:
            print(f"Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Error making request: {e}")
    
    # Check GPU after
    gpu_after = check_gpu_after()
    
    # Compare
    print(f"\nGPU utilization comparison:")
    print(f"Before: {gpu_before}")
    print(f"After: {gpu_after}")

def main():
    """Main function."""
    print("=== GPU Acceleration Test ===")
    
    # Test Ollama directly
    test_ollama_directly()
    
    # Wait a bit for GPU to cool down
    time.sleep(5)
    
    # Test Metis RAG
    test_metis_rag()
    
    print("\nTest completed!")

if __name__ == "__main__":
    main()