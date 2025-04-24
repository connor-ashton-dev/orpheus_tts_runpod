# CUDA 12 / Python 3.11 / PyTorch 2.4 – already optimised for RunPod
FROM runpod/pytorch:2.4.0-py3.11-cuda12.4.1-devel-ubuntu22.04

# --- system libs --------------------------------------------------------------
RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y ffmpeg libsndfile1-dev && \
    rm -rf /var/lib/apt/lists/*

# --- python deps --------------------------------------------------------------
# orpheus-speech pulls in torch, transformers, vllm, etc.
RUN pip install --no-cache-dir \
    orpheus-speech==0.1.3 \
    vllm==0.7.3 \
    runpod

# --- copy app -----------------------------------------------------------------
WORKDIR /app
COPY handler.py /app/handler.py

# --- default entrypoint -------------------------------------------------------
CMD ["python", "-u", "handler.py"]