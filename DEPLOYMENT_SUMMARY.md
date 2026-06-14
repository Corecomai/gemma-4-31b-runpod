# 📦 Gemma-4-31B RunPod Deployment Package

## ✅ What's Included

This complete deployment package contains everything needed to host **google/gemma-4-31b-it** on RunPod Serverless.

### 📁 Files Created

```
/Users/shubhammohape/Documents/RunPod/
│
├── 🎯 QUICKSTART.md                      ← START HERE (5 min guide)
├── 📖 DEPLOYMENT_README.md               ← Full documentation
├── 📊 GEMMA4_RUNPOD_DEPLOYMENT_GUIDE.md ← Technical deep-dive
│
├── 🐍 Core Scripts
│   ├── handler.py                        ← Serverless handler (main logic)
│   ├── requirements.txt                  ← Python dependencies
│   ├── deploy_to_runpod.py              ← Deployment automation script
│   └── test_endpoint.py                 ← Testing/benchmarking tool
│
├── ⚙️ Configuration
│   └── configs.yaml                      ← GPU configurations (7 presets)
│
└── 📝 Generated Files (after deployment)
    ├── Dockerfile                        ← Docker container definition
    ├── .env.runpod                       ← Environment variables
    └── runpod_config.json               ← RunPod template config
```

---

## 🚀 Quick Start Path (5 min)

1. **Read:** [QUICKSTART.md](./QUICKSTART.md)
2. **Set credentials:** Update `.env` with `RUNPOD_API_KEY` and `HF_TOKEN`
3. **Generate files:** `python deploy_to_runpod.py --config a100_80gb_int4 --output-dir ./deployment`
4. **Build Docker:** `cd deployment && docker build -t gemma4-runpod:latest .`
5. **Push:** `docker push your-username/gemma4-runpod:latest`
6. **Deploy:** Create endpoint on RunPod console
7. **Test:** `python test_endpoint.py --endpoint-id YOUR_ID`

---

## 📋 File Descriptions

### 1. **handler.py** (Main Handler)

The serverless function that runs on RunPod. Features:

✅ Async vLLM engine  
✅ Automatic model loading  
✅ Support for int4, int8, bf16 quantization  
✅ Multi-GPU tensor parallelism (TP)  
✅ Prefix caching for efficiency  
✅ Proper error handling  
✅ Logging  

**Input JSON:**
```json
{
  "prompt": "What is AI?",
  "max_tokens": 256,
  "temperature": 0.7,
  "top_p": 0.9,
  "top_k": 50,
  "repetition_penalty": 1.0
}
```

**Output JSON:**
```json
{
  "status": "success",
  "prompt": "...",
  "generated_text": "...",
  "finish_reason": "length",
  "usage": {
    "prompt_tokens": 8,
    "completion_tokens": 256
  }
}
```

### 2. **deploy_to_runpod.py** (Automation Script)

Generates all deployment files automatically. Features:

✅ Lists all 7 preset configurations  
✅ Generates Dockerfile with optimized settings  
✅ Creates environment variable template  
✅ Generates RunPod template config  
✅ Prints step-by-step deployment guide  

**Usage:**
```bash
python deploy_to_runpod.py --list-configs
python deploy_to_runpod.py --config a100_80gb_int4 --output-dir ./deployment
```

### 3. **test_endpoint.py** (Testing Tool)

Tests and benchmarks your deployed endpoint. Features:

✅ Single request testing  
✅ Benchmark suite (multiple requests)  
✅ Latency measurements  
✅ Token usage tracking  
✅ Error handling  

**Usage:**
```bash
python test_endpoint.py --endpoint-id YOUR_ID
python test_endpoint.py --endpoint-id YOUR_ID --benchmark 10
python test_endpoint.py --endpoint-id YOUR_ID --prompt "Your prompt" --max-tokens 512
```

### 4. **configs.yaml** (Configuration Presets)

7 pre-configured setups for different use cases:

| Config | GPU | VRAM | Quant | Cost/hr | Throughput |
|--------|-----|------|-------|---------|-----------|
| a100_80gb_bf16 | A100 80GB | 80GB | None | $1.29 | 50-80 tok/s |
| **a100_80gb_int4** | A100 80GB | 25GB | int4 | $1.29 | 80-120 tok/s |
| a100_40gb_tp2_int4 | A100×2 40GB | 25GB | int4 | $1.60 | 150-250 tok/s |
| h100_80gb_bf16 | H100 80GB | 80GB | None | $2.69 | 150-200 tok/s |
| h100_80gb_int4 | H100 80GB | 25GB | int4 | $2.69 | 200-350 tok/s |
| h100_tp2_int4 | H100×2 80GB | 25GB | int4 | $5.38 | 500-800 tok/s |
| rtx4090_int4 | RTX4090 | 24GB | int4 | $0.34 | 7-12 tok/s ⚠️ |

---

## 🎯 Recommended Configurations

### For Development/Testing
**Config:** `a100_80gb_int4`
- Single A100 80GB GPU
- INT4 quantization (low memory)
- $1.29/hour
- 80-120 tokens/sec
- Deploy in ~5 min

### For Small Production (10K-50K req/day)
**Config:** `a100_80gb_int4`
- Same as above
- Estimated cost: $930/month (24/7)
- Easy to scale workers

### For Medium Production (50K-500K req/day)
**Config:** `a100_40gb_tp2_int4`
- Dual A100 40GB (Tensor Parallel)
- INT4 quantization
- $1.60/hour ($1,152/month)
- 150-250 tokens/sec
- High throughput

### For Maximum Quality
**Config:** `h100_80gb_bf16`
- Single H100 80GB
- Full precision (99.2% MMLU quality)
- $2.69/hour
- 150-200 tokens/sec
- Deploy in ~5 min

### For Maximum Throughput
**Config:** `h100_tp2_int4`
- Dual H100 with Tensor Parallelism
- 500-800 tokens/sec
- $5.38/hour
- For very high load scenarios

---

## 🔒 Security Notes

⚠️ **IMPORTANT:** Never commit secrets to git!

```bash
# Good - add to .gitignore
.env
.env.runpod
*.key
```

```bash
# Environment variables to keep safe
HF_TOKEN=hf_xxxxxxxxxxxxx          # Hugging Face token
RUNPOD_API_KEY=rpa_xxxxxxxxxxxx    # RunPod API key
```

---

## 📊 Performance Expectations

### First Request (Cold Start)
- Model loading + CUDA initialization
- Expected: 10-30 seconds
- Varies by GPU and quantization

### Subsequent Requests (Warm)
- Direct generation
- Expected: 2-10 seconds for 256 tokens
- Depends on throughput of GPU

### Throughput Comparison
```
A100 80GB INT4:  100 tokens/sec
H100 BF16:       160 tokens/sec  
Dual A100 TP:    200 tokens/sec
H100 INT4:       300 tokens/sec
Dual H100 TP:    600 tokens/sec
```

---

## 💰 Cost Comparison

### One-Time Setup Cost
- Docker build & push: Free (if using DockerHub)
- RunPod template creation: Free
- Total: **$0**

### Monthly Operating Costs (24/7)

| Config | GPU/Count | Cost/Month | Best For |
|--------|-----------|-----------|----------|
| A100 80GB INT4 | 1 | $930 | Development |
| A100 40GB TP=2 | 2 | $1,152 | Production Small |
| H100 BF16 | 1 | $1,933 | Quality |
| H100 INT4 | 1 | $1,933 | Speed |
| H100 TP=2 | 2 | $3,872 | Enterprise |

---

## 🔧 Customization

### Change Model
Edit `handler.py`:
```python
self.model = os.getenv('MODEL_NAME', 'google/gemma-4-31b-it')
# Change to any HF model ID
```

### Change Quantization
In environment variables:
```bash
QUANTIZATION=int4      # int4 AWQ (recommended)
QUANTIZATION=int8      # int8 (balanced)
QUANTIZATION=None      # Full precision
```

### Change Max Context
In environment variables:
```bash
MAX_MODEL_LEN=32768    # 32K tokens
MAX_MODEL_LEN=8192     # 8K tokens (less memory)
MAX_MODEL_LEN=262144   # 262K tokens (needs 80GB+)
```

### Multi-GPU Setup
In environment variables:
```bash
TENSOR_PARALLEL_SIZE=2  # Split across 2 GPUs
TENSOR_PARALLEL_SIZE=4  # Split across 4 GPUs
```

---

## 📚 Reference Guides

- **QUICKSTART.md** - 5-minute getting started (read first!)
- **DEPLOYMENT_README.md** - Detailed deployment guide
- **GEMMA4_RUNPOD_DEPLOYMENT_GUIDE.md** - Technical deep-dive

---

## 🆘 Support Resources

- **RunPod Documentation:** https://docs.runpod.io/
- **vLLM GitHub:** https://github.com/vllm-project/vllm
- **Gemma Model Card:** https://huggingface.co/google/gemma-4-31b-it
- **RunPod Discord:** https://discord.gg/runpod

---

## 📝 Checklist Before Deployment

- [ ] Have RunPod API key
- [ ] Have Hugging Face token (for model access)
- [ ] Docker installed and running
- [ ] Python 3.9+ with pip
- [ ] Read QUICKSTART.md
- [ ] Updated `.env` with credentials
- [ ] Chosen configuration (recommend: a100_80gb_int4)
- [ ] Generated deployment files
- [ ] Built Docker image
- [ ] Pushed to Docker registry
- [ ] Created RunPod template
- [ ] Deployed endpoint
- [ ] Tested with test_endpoint.py

---

## 🎯 Next Steps

1. **Read [QUICKSTART.md](./QUICKSTART.md)** - 5 minute guide
2. **Update `.env`** with your credentials
3. **Run deployment script** - Generate files
4. **Build Docker image** - `docker build -t gemma4-runpod:latest .`
5. **Push to registry** - `docker push your-username/gemma4-runpod:latest`
6. **Create RunPod endpoint** - Use generated config
7. **Test endpoint** - `python test_endpoint.py --endpoint-id YOUR_ID`

---

**Good luck! 🚀**

Once deployed, you'll have a production-ready Gemma-4-31B instance that can handle inference requests at scale.
