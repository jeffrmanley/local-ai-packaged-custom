# Use NVIDIA's CUDA 12.8.0 base image with Ubuntu 22.04
FROM nvidia/cuda:12.8.0-devel-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies: ffmpeg, Python3, and pip
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        ffmpeg \
        python3 \
        python3-pip && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements.txt and install Python dependencies
COPY requirements.txt ./
RUN pip3 install -r requirements.txt

# Copy your server code
COPY server.py ./

EXPOSE 6000

# Override any inherited ENTRYPOINT and run the Flask server
ENTRYPOINT []
CMD ["python3", "server.py"]
