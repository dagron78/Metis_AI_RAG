#!/bin/bash
# Script to optimize Ollama GPU usage

echo "Optimizing Ollama GPU configuration..."

# Create Ollama config directory if it doesn't exist
mkdir -p ~/.ollama

# Create or update the Ollama config file with more aggressive GPU settings
echo "# Ollama GPU optimization settings" > ~/.ollama/config
echo "GPU_LAYERS=99" >> ~/.ollama/config
echo "GPU_MEMORY=4096" >> ~/.ollama/config  # Allocate 4GB of GPU memory

# Set environment variables for GPU
export CUDA_VISIBLE_DEVICES=0

echo "Configuration updated. Restarting Ollama..."

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
    echo "Ollama is now running with optimized GPU settings."
    
    echo "Running a test query to warm up the GPU..."
    curl -s -X POST http://localhost:11434/api/generate -d '{"model": "llama2:latest", "prompt": "Hello, GPU!", "stream": false, "gpu": true}' > /dev/null
    
    echo "Checking GPU utilization..."
    nvidia-smi
    
    echo "Done! Ollama should now be using GPU acceleration more efficiently."
    echo "To verify, run: watch -n 1 nvidia-smi"
    echo "You should see higher GPU utilization when running queries."
else
    echo "Failed to start Ollama. Please check the logs."
fi