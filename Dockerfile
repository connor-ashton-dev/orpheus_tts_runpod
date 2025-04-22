# Base Image
FROM nvidia/cuda:12.1.0-base-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive

# Install Python 3.11, pip, git, espeak-ng, and other essentials
RUN apt-get update && apt-get install -y --no-install-recommends \
    software-properties-common \
    git \
    wget \
    espeak-ng \
    && add-apt-repository ppa:deadsnakes/ppa \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
    python3.11 \
    python3.11-dev \
    python3.11-venv \
    python3-pip \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Update pip, setuptools, wheel
RUN python3.11 -m pip install --upgrade pip setuptools wheel

# Install uv
RUN python3.11 -m pip install uv

# Set the working directory
WORKDIR /app

# Copy only the dependency specification first
COPY pyproject.toml ./

# Install dependencies using uv based on pyproject.toml
# This resolves dependencies inside the container environment
# Using --system installs into the main Python environment, not a venv
RUN uv pip install -p python3.11 --system .

# Install Kokoro TTS specific dependencies
RUN python3.11 -m pip install --no-cache-dir kokoro>=0.9.4 soundfile

# Copy the rest of the application code
# Copy application code *after* dependencies are installed for better caching
COPY . .

# Run the application handler
# Use -u for unbuffered output, helpful for logging in containers
CMD ["python3.11", "-u", "rp_handler.py"] 