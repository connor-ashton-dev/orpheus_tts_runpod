FROM nvidia/cuda:12.1.0-base-ubuntu22.04

# Install Python and other dependencies
RUN apt-get update && apt-get install -y \
    git \
    wget \
    software-properties-common \
    build-essential \
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

# Install the specific dependencies required
RUN python3.10 -m pip install --no-cache-dir \
    torch==2.4.0 \
    torchaudio==2.4.0

# Install FlashInfer for improved performance
RUN git clone https://github.com/flashinfer-ai/flashinfer.git && \
    cd flashinfer && \
    git checkout v0.0.1 && \
    pip install -e . && \
    cd .. && \
    rm -rf flashinfer

# Set working directory
WORKDIR /app

# Copy application files
COPY . /app

# Install dependencies from requirements.txt
COPY requirements.txt /app/requirements.txt
RUN python3.10 -m pip install --no-cache-dir -r requirements.txt

# Use a direct command rather than entrypoint
CMD ["python3.10", "-u", "handler.py"]