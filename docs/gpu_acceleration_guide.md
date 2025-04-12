# GPU Acceleration Guide for Metis RAG

This guide provides step-by-step instructions for enabling GPU acceleration in Metis RAG with Ollama.

## Prerequisites

- NVIDIA GPU (recommended)
- CUDA-compatible GPU drivers
- CUDA toolkit installed

## Step 1: Install NVIDIA Drivers

### For Ubuntu/Debian:

```bash
# Update package list
sudo apt update

# Install nvidia-driver package
sudo apt install nvidia-driver-535  # Use the latest version available

# Reboot your system
sudo reboot
```

### For other distributions:

Download and install the appropriate drivers from the [NVIDIA Driver Downloads](https://www.nvidia.com/Download/index.aspx) page.

## Step 2: Install CUDA Toolkit

### For Ubuntu/Debian:

```bash
# Download CUDA installer
wget https://developer.download.nvidia.com/compute/cuda/12.3.0/local_installers/cuda_12.3.0_545.23.06_linux.run

# Make it executable
chmod +x cuda_12.3.0_545.23.06_linux.run

# Run the installer
sudo ./cuda_12.3.0_545.23.06_linux.run
```

Follow the on-screen instructions to complete the installation.

### For other distributions:

Download and install the CUDA Toolkit from the [NVIDIA CUDA Downloads](https://developer.nvidia.com/cuda-downloads) page.

## Step 3: Verify GPU Installation

```bash
# Check if NVIDIA drivers are installed
nvidia-smi

# Check CUDA installation
nvcc --version
```

You should see output showing your GPU and CUDA version.

## Step 4: Configure Ollama for GPU

### Update Ollama (if needed)

Make sure you have the latest version of Ollama that supports GPU acceleration:

```bash
# For Linux
curl -fsSL https://ollama.com/install.sh | sh
```

### Configure Ollama to use GPU

Create or edit the Ollama configuration file:

```bash
# Create Ollama config directory if it doesn't exist
mkdir -p ~/.ollama

# Create or edit the config file
nano ~/.ollama/config
```

Add the following configuration:

```
GPU_LAYERS=99
```

Save and close the file.

## Step 5: Configure Metis RAG

Update your `.env` file with the following settings:

```
OLLAMA_USE_GPU=true
CUDA_VISIBLE_DEVICES=0
```

If you have multiple GPUs, you can specify which one to use by changing the `CUDA_VISIBLE_DEVICES` value.

## Step 6: Restart Services

```bash
# Restart Ollama
sudo systemctl restart ollama

# Or if you're running Ollama manually
killall ollama
ollama serve
```

## Step 7: Verify GPU Usage

Run the GPU check script:

```bash
python scripts/check_ollama_gpu.py
```

You should see confirmation that Ollama is using the GPU.

## Troubleshooting

### Common Issues:

1. **"CUDA is not available" error**:
   - Make sure CUDA toolkit is properly installed
   - Check if your GPU is CUDA-compatible
   - Verify that the correct NVIDIA drivers are installed

2. **"Failed to run inference" error**:
   - Check if Ollama is running
   - Verify that the model specified exists in Ollama
   - Try pulling the model again: `ollama pull llama2:latest`

3. **High CPU usage despite GPU configuration**:
   - Check if Ollama is actually using the GPU with `nvidia-smi`
   - Make sure the `GPU_LAYERS` setting is correct in Ollama config
   - Some models may not fully utilize GPU acceleration

### Checking GPU Utilization:

Monitor GPU usage while running inference:

```bash
watch -n 1 nvidia-smi
```

You should see GPU utilization increase when running queries through Metis RAG.

## Additional Resources

- [Ollama GPU Documentation](https://github.com/ollama/ollama/blob/main/docs/gpu.md)
- [NVIDIA CUDA Documentation](https://docs.nvidia.com/cuda/)
- [NVIDIA Driver Documentation](https://docs.nvidia.com/drive/drive-os-5.1.6.1L/drive-os/DRIVE_OS_Linux_SDK_Development_Guide/baggage/nvidia_driver_documentation.html)