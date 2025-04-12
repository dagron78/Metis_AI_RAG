#!/bin/bash
# Script to check GPU utilization

echo "Checking GPU utilization..."
nvidia-smi --query-gpu=timestamp,name,utilization.gpu,utilization.memory,memory.used,memory.total,temperature.gpu,power.draw --format=csv

echo ""
echo "Running a test query to measure GPU utilization..."
echo "This will take a few seconds..."

# Run a test query and measure GPU utilization before, during, and after
nvidia-smi --query-gpu=utilization.gpu --format=csv -l 1 > gpu_util_before.txt &
NVIDIA_PID=$!
sleep 2
kill $NVIDIA_PID

# Run the query
curl -s -X POST http://localhost:11434/api/generate -d '{"model": "llama2:latest", "prompt": "Explain quantum computing in detail", "stream": false, "gpu": true}' > /dev/null &
CURL_PID=$!

# Measure GPU utilization during query
nvidia-smi --query-gpu=utilization.gpu --format=csv -l 1 > gpu_util_during.txt &
NVIDIA_PID=$!
sleep 5
kill $NVIDIA_PID

# Wait for query to complete
wait $CURL_PID

# Measure GPU utilization after query
nvidia-smi --query-gpu=utilization.gpu --format=csv -l 1 > gpu_util_after.txt &
NVIDIA_PID=$!
sleep 2
kill $NVIDIA_PID

echo ""
echo "GPU Utilization Results:"
echo "Before query: $(tail -n 1 gpu_util_before.txt)"
echo "During query: $(tail -n 1 gpu_util_during.txt)"
echo "After query: $(tail -n 1 gpu_util_after.txt)"

# Clean up temporary files
rm gpu_util_before.txt gpu_util_during.txt gpu_util_after.txt

echo ""
echo "Current GPU Status:"
nvidia-smi