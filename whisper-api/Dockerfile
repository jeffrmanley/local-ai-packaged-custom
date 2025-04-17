# Use NVIDIA CUDA base image with Python 3.11
FROM nvidia/cuda:12.1.0-cudnn8-devel-ubuntu22.04

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3.11 \
    python3.11-dev \
    python3-pip \
    gcc \
    ffmpeg \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set Python 3.11 as the default
RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1
RUN update-alternatives --install /usr/bin/python python /usr/bin/python3.11 1

# Upgrade pip
RUN python3.11 -m pip install --upgrade pip

WORKDIR /app

# Install base Python packages (using default PyPI index)
RUN python3.11 -m pip install --no-cache-dir \
    fastapi \
    uvicorn \
    python-multipart \
    git+https://github.com/openai/whisper.git

# Install PyTorch with CUDA support (add PyTorch index as extra)
RUN python3.11 -m pip install --no-cache-dir \
    torch torchvision torchaudio \
    --extra-index-url https://download.pytorch.org/whl/cu121

COPY . .

EXPOSE 5000

CMD ["python3.11", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5000"]