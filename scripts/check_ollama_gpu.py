#!/usr/bin/env python3
"""
Script to check if Ollama is using the GPU.
"""
import os
import sys
import json
import requests
import subprocess
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Import project settings
from app.core.config import SETTINGS

def check_ollama_running():
    """Check if Ollama is running."""
    try:
        response = requests.get(SETTINGS.ollama_base_url + "/api/tags", timeout=5)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False

def get_ollama_models():
    """Get list of models from Ollama."""
    try:
        response = requests.get(SETTINGS.ollama_base_url + "/api/tags", timeout=5)
        if response.status_code == 200:
            return response.json().get("models", [])
        return []
    except requests.exceptions.RequestException:
        return []

def check_nvidia_gpu():
    """Check if NVIDIA GPU is available."""
    try:
        result = subprocess.run(["nvidia-smi"], capture_output=True, text=True)
        return result.returncode == 0
    except FileNotFoundError:
        return False

def check_cuda_available():
    """Check if CUDA is available."""
    try:
        import torch
        return torch.cuda.is_available()
    except ImportError:
        print("PyTorch not installed, can't check CUDA availability")
        return False
    except Exception as e:
        print(f"Error checking CUDA: {e}")
        return False

def check_ollama_gpu_usage():
    """Check if Ollama is using GPU."""
    # First check if we can run a simple inference
    try:
        payload = {
            "model": "llama2:latest",  # Use a model we know exists
            "prompt": "Hello, are you using GPU?",
            "stream": False,
            "gpu": True
        }
        
        print(f"Testing model: llama2:latest")
        print(f"GPU flag enabled: {SETTINGS.ollama_use_gpu}")
        print(f"CUDA devices: {SETTINGS.cuda_visible_devices}")
        
        response = requests.post(
            f"{SETTINGS.ollama_base_url}/api/generate",
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            print("Successfully ran inference with GPU flag enabled")
            return True
        else:
            print(f"Failed to run inference: {response.text}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"Error running inference: {e}")
        return False

def main():
    """Main function."""
    print("=== Ollama GPU Check ===")
    
    # Check if Ollama is running
    if not check_ollama_running():
        print("❌ Ollama is not running. Please start Ollama first.")
        return
    
    print("✅ Ollama is running")
    
    # Check available models
    models = get_ollama_models()
    if models:
        print(f"📋 Available models: {', '.join(m['name'] for m in models)}")
    else:
        print("❌ No models found in Ollama")
    
    # Check if NVIDIA GPU is available
    if check_nvidia_gpu():
        print("✅ NVIDIA GPU detected")
    else:
        print("❌ NVIDIA GPU not detected or nvidia-smi not installed")
    
    # Check if CUDA is available
    if check_cuda_available():
        print("✅ CUDA is available")
    else:
        print("❌ CUDA is not available")
    
    # Check Ollama GPU usage
    print("\nTesting Ollama GPU usage...")
    if check_ollama_gpu_usage():
        print("✅ Ollama appears to be using the GPU")
    else:
        print("❌ Ollama may not be using the GPU")
    
    print("\nTo ensure Ollama uses the GPU:")
    print("1. Make sure you have NVIDIA drivers installed")
    print("2. Make sure CUDA is installed")
    print("3. Set OLLAMA_USE_GPU=true in your .env file")
    print("4. Set CUDA_VISIBLE_DEVICES=0 in your .env file")
    print("5. Restart Ollama and your application")

if __name__ == "__main__":
    main()