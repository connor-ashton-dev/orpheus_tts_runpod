FROM nvidia/cuda:12.1.0-base-ubuntu22.04

# Install Python and other dependencies
RUN apt-get update && apt-get install -y \
    git \
    wget \
    software-properties-common \
    && add-apt-repository ppa:deadsnakes/ppa \
    && apt-get update \
    && apt-get install -y \
    python3.10 \
    python3.10-dev \
    python3.10-venv \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

# Ensure pip is updated
RUN python3.10 -m pip install --upgrade pip setuptools wheel

# Set up working directory
WORKDIR /app

# Install PyTorch and core dependencies first
RUN python3.10 -m pip install --no-cache-dir \
    torch==2.4.0 \
    torchaudio==2.4.0 \
    numpy>=1.21.0 \
    scipy>=1.7.0

# Install transformers and related packages
RUN python3.10 -m pip install --no-cache-dir \
    tokenizers==0.21.0 \
    transformers==4.49.0 \
    huggingface_hub==0.28.1 \
    safetensors>=0.3.0

# Install utility packages
RUN python3.10 -m pip install --no-cache-dir \
    einops \
    tqdm>=4.65.0 \
    runpod>=1.0.0

# Install vllm first (specific version to avoid bugs)
RUN python3.10 -m pip install --no-cache-dir vllm==0.7.3

# Finally install orpheus-speech
RUN python3.10 -m pip install --no-cache-dir orpheus-speech

# Copy our handler and other files
COPY handler.py /app/
COPY requirements.txt /app/

# Command to run the application
CMD ["python3.10", "-u", "/app/handler.py"] 