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

# Ensure CUDA compatibility
RUN ldconfig /usr/local/cuda-12.1/compat/

# Ensure pip is updated and install core dependencies
RUN --mount=type=cache,target=/root/.cache/pip \
    python3.10 -m pip install --upgrade pip setuptools wheel && \
    python3.10 -m pip install --no-cache-dir \
    torch==2.4.0 \
    torchaudio==2.4.0

# Install FlashInfer with specific CUDA and PyTorch versions
RUN python3.10 -m pip install flashinfer -i https://flashinfer.ai/whl/cu121/torch2.3

# Set working directory
WORKDIR /app

# Copy application files
COPY . /app

# Install dependencies from requirements.txt
COPY requirements.txt /app/requirements.txt
RUN --mount=type=cache,target=/root/.cache/pip \
    python3.10 -m pip install --no-cache-dir -r requirements.txt

# Use a direct command rather than entrypoint
CMD ["python3.10", "-u", "handler.py"]