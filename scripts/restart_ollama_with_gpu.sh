#!/bin/bash
# Script to restart Ollama with GPU support

echo "Restarting Ollama with GPU support..."

# Check if Ollama is running
if pgrep -x "ollama" > /dev/null; then
    echo "Stopping Ollama..."
    if command -v systemctl &> /dev/null && systemctl is-active --quiet ollama; then
        # If Ollama is running as a systemd service
        sudo systemctl stop ollama
    else
        # Otherwise kill the process
        killall ollama
    fi
    echo "Ollama stopped."
else
    echo "Ollama is not running."
fi

# Create Ollama config directory if it doesn't exist
mkdir -p ~/.ollama

# Create or update the Ollama config file
echo "Configuring Ollama for GPU..."
echo "GPU_LAYERS=99" > ~/.ollama/config

# Set environment variables for GPU
export CUDA_VISIBLE_DEVICES=0

# Start Ollama
echo "Starting Ollama..."
if command -v systemctl &> /dev/null && systemctl list-unit-files | grep -q ollama.service; then
    # If Ollama is installed as a systemd service
    sudo systemctl start ollama
else
    # Otherwise start it manually
    ollama serve &
    echo "Ollama started in background."
fi

# Wait for Ollama to start
echo "Waiting for Ollama to start..."
sleep 5

# Check if Ollama is running
if pgrep -x "ollama" > /dev/null; then
    echo "Ollama is now running."
    
    # Pull models if needed
    echo "Checking models..."
    if ! ollama list | grep -q "llama2"; then
        echo "Pulling llama2 model..."
        ollama pull llama2:latest
    fi
    
    if ! ollama list | grep -q "nomic-embed-text"; then
        echo "Pulling nomic-embed-text model..."
        ollama pull nomic-embed-text:latest
    fi
    
    echo "Running GPU check..."
    python scripts/check_ollama_gpu.py
    
    echo "Done! Ollama should now be using GPU acceleration."
    echo "To verify, run: watch -n 1 nvidia-smi"
    echo "You should see GPU utilization when running queries."
else
    echo "Failed to start Ollama. Please check the logs."
fi