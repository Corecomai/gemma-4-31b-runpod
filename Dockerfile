FROM nvidia/cuda:12.1.1-runtime-ubuntu22.04

WORKDIR /src

# Install Python and dependencies
RUN apt-get update && apt-get install -y \
    python3.10 \
    python3-pip \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy handler code
COPY handler.py .

# Set environment variables for vLLM optimization
ENV VLLM_WORKER_MULTIPROC_METHOD=spawn
ENV CUDA_LAUNCH_BLOCKING=1
ENV OMP_NUM_THREADS=1

# Configuration for A100 80GB INT4 (recommended)
ENV MODEL_NAME=google/gemma-4-31b-it
ENV QUANTIZATION=int4
ENV TENSOR_PARALLEL_SIZE=1
ENV MAX_MODEL_LEN=32768
ENV GPU_MEMORY_UTILIZATION=0.90
ENV MAX_NUM_SEQS=64
ENV MAX_TOKENS_PER_BATCH=32768

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python3 -c "import sys; sys.exit(0)" || exit 1

# Run handler
CMD ["python3", "-c", "import asyncio; from handler import handler; asyncio.run(handler({'prompt': 'test'}))"]
