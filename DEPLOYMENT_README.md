# Gemma-4-31B Deployment on RunPod Serverless

Complete guide to deploying Google's **Gemma-4-31B-it** model on RunPod Serverless with vLLM.

## 📋 Quick Start

### 1. Check Available Configurations

```bash
python deploy_to_runpod.py --list-configs
```

This shows all available GPU configurations (A100, H100, RTX 4090, etc.) with specs.

### 2. Generate Deployment Files

```bash
# For A100 80GB with INT4 (recommended)
python deploy_to_runpod.py --config a100_80gb_int4 --output-dir ./deployment

# For H100 with full precision (best quality)
python deploy_to_runpod.py --config h100_80gb_bf16 --output-dir ./deployment

# For dual A100 40GB with tensor parallelism (production)
python deploy_to_runpod.py --config a100_40gb_tp2_int4 --output-dir ./deployment
```

This generates:
- `Dockerfile` - Container configuration
- `.env.runpod` - Environment variables
- `runpod_config.json` - RunPod template configuration

### 3. Build and Push Docker Image

```bash
cd deployment

# Build
docker build -t gemma4-runpod:latest .

# Tag for your registry
docker tag gemma4-runpod:latest your-username/gemma4-runpod:latest

# Push to DockerHub
docker push your-username/gemma4-runpod:latest
```

### 4. Create RunPod Serverless Endpoint

1. Go to: https://www.runpod.io/console/serverless
2. Click **Create New Endpoint**
3. Create a new template with:
   - Container Image: `your-username/gemma4-runpod:latest`
   - Environment Variables (from `.env.runpod`):
     - `MODEL_NAME=google/gemma-4-31b-it`
     - `QUANTIZATION=int4` (or `None` for full precision)
     - `TENSOR_PARALLEL_SIZE=1` (or `2` for dual GPU)
     - `HF_TOKEN=your_hugging_face_token`
     - `GPU_MEMORY_UTILIZATION=0.90`

4. Deploy with your chosen GPU type

### 5. Test the Endpoint

```bash
python test_endpoint.py --endpoint-id YOUR_ENDPOINT_ID

# Test with custom prompt
python test_endpoint.py --endpoint-id YOUR_ENDPOINT_ID \
  --prompt "What is quantum computing?" \
  --max-tokens 512

# Run benchmark
python test_endpoint.py --endpoint-id YOUR_ENDPOINT_ID --benchmark 10
```

---

## 🏗️ Architecture Overview

### File Structure

```
/Users/shubhammohape/Documents/RunPod/
├── handler.py                    # Main serverless handler
├── requirements.txt              # Python dependencies
├── configs.yaml                  # GPU configurations
├── deploy_to_runpod.py          # Deployment script
├── test_endpoint.py             # Testing script
├── .env                         # Local environment (RUNPOD_API_KEY, HF_TOKEN)
├── Dockerfile                   # (generated)
├── .env.runpod                  # (generated)
└── runpod_config.json          # (generated)
```

### Handler Flow

```
HTTP Request → handler.py
    ↓
vLLMEngine (async) ← Initialized once on first request
    ↓
vLLM AsyncLLMEngine
    ↓
Model Loading (google/gemma-4-31b-it)
    ↓
Quantization (int4/int8/bf16)
    ↓
Text Generation
    ↓
JSON Response
```

---

## 💻 Configuration Options

### Quantization Methods

| Method | Quality | VRAM | Throughput | Notes |
|--------|---------|------|-----------|-------|
| BF16 | 99.2% MMLU | 72-87GB | 50-200 tok/s | Full precision, highest quality |
| INT8 | 98.5% MMLU | 40-52GB | 100-150 tok/s | Balanced, less common |
| INT4 (AWQ) | 97.1% MMLU | 25-32GB | 150-350 tok/s | **RECOMMENDED** - best cost/performance |
| INT4 (GGUF) | 97.1% MMLU | 24-30GB | 7-8 tok/s | Budget option, slow on GPUs |

### GPU Options

#### Single GPU Deployments

| GPU | VRAM | Cost/hr | BF16 | INT4 | Recommended For |
|-----|------|---------|------|------|-----------------|
| H100 SXM | 80GB | $2.69 | ✓ | ✓ Best | Max performance |
| A100 80GB | 80GB | $1.29 | ✓ | ✓ Best | **Best value** |
| A100 40GB | 40GB | $0.80 | ✗ | ✓ | Budget + TP |
| L40S | 48GB | $0.19-0.55 | ✗ | ✗ (slow) | Not viable |
| RTX 4090 | 24GB | $0.34 | ✗ | ✗ (slow) | Testing only |

#### Multi-GPU Deployments

| Setup | Cost/hr | Throughput | Use Case |
|-------|---------|-----------|----------|
| Dual A100 40GB (TP=2) | $1.60 | 150-250 tok/s | Production medium |
| Dual H100 (TP=2) | $5.38 | 500-800 tok/s | Production large |

---

## 🔧 Handler Configuration

The `handler.py` accepts these environment variables:

```bash
# Model
MODEL_NAME=google/gemma-4-31b-it

# Quantization: "int4", "int8", or "None" (default: "int4")
QUANTIZATION=int4

# Multi-GPU
TENSOR_PARALLEL_SIZE=1              # 1 for single GPU, 2+ for multi-GPU

# Memory
GPU_MEMORY_UTILIZATION=0.90         # 0.85-0.95 range
MAX_MODEL_LEN=32768                 # Max context tokens (32K-262K)
MAX_NUM_SEQS=64                     # Max concurrent sequences

# Hugging Face
HF_TOKEN=hf_xxxxxxxxxxxxxxxxxxxxx
```

### Recommended Environment Configs

#### A100 80GB + INT4 (Balanced)
```bash
QUANTIZATION=int4
GPU_MEMORY_UTILIZATION=0.85
MAX_NUM_SEQS=128
MAX_TOKENS_PER_BATCH=32768
```

#### H100 + BF16 (Quality)
```bash
QUANTIZATION=None
GPU_MEMORY_UTILIZATION=0.92
MAX_NUM_SEQS=64
MAX_TOKENS_PER_BATCH=16384
```

#### Dual A100 40GB + INT4 + TP (Production)
```bash
QUANTIZATION=int4
TENSOR_PARALLEL_SIZE=2
GPU_MEMORY_UTILIZATION=0.85
MAX_NUM_SEQS=256
MAX_TOKENS_PER_BATCH=65536
```

---

## 📝 Request Format

### HTTP Request

```bash
curl -X POST https://api.runpod.io/v1/{ENDPOINT_ID}/run \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "prompt": "What is artificial intelligence?",
      "max_tokens": 256,
      "temperature": 0.7,
      "top_p": 0.9,
      "top_k": 50,
      "repetition_penalty": 1.0
    }
  }'
```

### Response

```json
{
  "status": "success",
  "prompt": "What is artificial intelligence?",
  "generated_text": "Artificial intelligence (AI) is...",
  "finish_reason": "length",
  "usage": {
    "prompt_tokens": 8,
    "completion_tokens": 256
  }
}
```

### Parameters

| Parameter | Type | Default | Notes |
|-----------|------|---------|-------|
| prompt | string | required | Input text to generate from |
| max_tokens | int | 1024 | Max generation length |
| temperature | float | 0.7 | 0.0-1.0, higher = more random |
| top_p | float | 0.9 | Nucleus sampling threshold |
| top_k | int | 50 | Top-K sampling |
| repetition_penalty | float | 1.0 | Penalize token repetition |

---

## 🧪 Testing

### Single Request

```bash
python test_endpoint.py --endpoint-id YOUR_ENDPOINT_ID \
  --prompt "What is AI?" \
  --max-tokens 512 \
  --temperature 0.8
```

### Benchmark (5 requests)

```bash
python test_endpoint.py --endpoint-id YOUR_ENDPOINT_ID --benchmark 5
```

Output:
```
BENCHMARK SUMMARY
================================================
Total Requests: 5
Average Time: 8.3s
Min Time: 6.2s
Max Time: 12.1s
```

### Expected Performance

| Configuration | First Request | Avg Gen Speed |
|---------------|---------------|---------------|
| A100 80GB INT4 | 12-18s | 80-120 tok/s |
| H100 BF16 | 10-15s | 120-200 tok/s |
| Dual A100 TP | 20-30s | 150-250 tok/s |

---

## 🐛 Troubleshooting

### CUDA Out of Memory (OOM)

**Error:** `RuntimeError: NVML_SUCCESS == r INTERNAL ASSERT FAILED`

**Solution:**
1. Reduce `GPU_MEMORY_UTILIZATION` from 0.90 to 0.80
2. Reduce `MAX_MODEL_LEN` from 32768 to 8192
3. Reduce `MAX_NUM_SEQS` from 128 to 64
4. Use INT4 quantization instead of BF16

```bash
GPU_MEMORY_UTILIZATION=0.80
MAX_MODEL_LEN=8192
QUANTIZATION=int4
```

### Model Download Fails

**Error:** `Model not found on Hugging Face`

**Solution:** Set valid `HF_TOKEN`
```bash
# Get token from: https://huggingface.co/settings/tokens
docker run ... -e HF_TOKEN=hf_xxxxxxxxxxxxx ...
```

### Slow Response Time

**Error:** First request takes >30s

**Solution:** Pre-download model in Dockerfile (uncomment in generated Dockerfile)
```dockerfile
RUN python3 -c "from transformers import AutoTokenizer; \
    AutoTokenizer.from_pretrained('google/gemma-4-31b-it')"
```

### Worker Initialization Failed

**Error:** `WorkerProc initialization failed`

**Solution:** Set environment variable
```bash
VLLM_WORKER_MULTIPROC_METHOD=spawn
```

### Tensor Parallelism Hangs

**Error:** Endpoint freezes with `TENSOR_PARALLEL_SIZE=2`

**Solution:**
```bash
export CUDA_LAUNCH_BLOCKING=1
export VLLM_WORKER_MULTIPROC_METHOD=spawn
```

---

## 📊 Cost Analysis

### Monthly Costs (Rough Estimates)

| Configuration | Cost/Hour | 24/7 | 8h/day | 2h/day |
|---------------|-----------|------|--------|--------|
| A100 80GB INT4 | $1.29 | $926 | $309 | $77 |
| A100 40GB TP=2 | $1.60 | $1,152 | $384 | $96 |
| H100 INT4 | $2.69 | $1,933 | $644 | $161 |
| RTX 4090 INT4 | $0.34 | $245 | $82 | $20 |

**Note:** RTX 4090 throughput is too slow for production.

---

## 🚀 Production Deployment Checklist

- [ ] Set `HF_TOKEN` environment variable
- [ ] Set `QUANTIZATION` based on GPU (int4 for 40GB, any for 80GB+)
- [ ] Set `GPU_MEMORY_UTILIZATION` to 0.85-0.90
- [ ] Set `MAX_MODEL_LEN` to 32768 or less
- [ ] Configure scaling: min=1, max=3 workers
- [ ] Enable cold-start optimization
- [ ] Set request timeout to 300s
- [ ] Set up health check endpoint
- [ ] Test with benchmark (10+ requests)
- [ ] Monitor logs for errors

---

## 📚 Resources

- **RunPod Docs:** https://docs.runpod.io/
- **vLLM Docs:** https://docs.vllm.ai/
- **Gemma Model:** https://huggingface.co/google/gemma-4-31b-it
- **Quantization Guide:** https://huggingface.co/docs/bitsandbytes/

---

## 📝 License

This deployment guide is provided as-is. Follow RunPod and Hugging Face terms of service.

---

**Questions or Issues?**
- RunPod Discord: https://discord.gg/runpod
- vLLM Issues: https://github.com/vllm-project/vllm/issues
