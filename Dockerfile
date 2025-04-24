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

# Install the specific dependencies required
RUN python3.10 -m pip install --no-cache-dir \
    torch==2.4.0 \
    torchaudio==2.4.0 \
    tokenizers==0.21.0 \
    transformers==4.49.0 \
    huggingface_hub==0.28.1 \
    einops \
    runpod>=1.0.0 \
    numpy>=1.21.0 \
    scipy>=1.7.0 \
    tqdm>=4.65.0 \
    safetensors>=0.3.0 \
    torchtune==0.4.0

# Clone the CSM streaming repository and set up the module structure
RUN git clone https://github.com/davidbrowne17/csm-streaming.git /app/csm && \
    mkdir -p /app/csm_streaming && \
    cp /app/csm/generator.py /app/csm_streaming/ && \
    cp /app/csm/models.py /app/csm_streaming/ && \
    cp /app/csm/config.py /app/csm_streaming/ && \
    touch /app/csm_streaming/__init__.py && \
    rm -rf /app/csm

# Copy our handler and other files
COPY handler.py /app/
COPY requirements.txt /app/

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV CUDA_VISIBLE_DEVICES=0
ENV PYTHONPATH=/app:$PYTHONPATH

# Command to run the application
CMD ["python3.10", "-u", "/app/handler.py"] 