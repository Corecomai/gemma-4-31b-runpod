# 🚀 Quick Start - Deploy Gemma-4-31B to RunPod in 5 Minutes

## Prerequisites

1. **RunPod Account** - https://www.runpod.io/
2. **RunPod API Key** - Get from https://www.runpod.io/console/api
3. **Hugging Face Token** - Get from https://huggingface.co/settings/tokens (for model access)
4. **Docker** - Installed and running
5. **Python 3.9+** - With pip

## Step 1: Set Up Environment

```bash
cd /Users/shubhammohape/Documents/RunPod

# Create .env file with your credentials
cat > .env << 'EOF'
RUNPOD_API_KEY=your_runpod_api_key_here
HF_TOKEN=hf_your_hugging_face_token_here
EOF

# Install dependencies
pip install -r requirements.txt
pip install pyyaml requests python-dotenv
```

## Step 2: Choose Configuration

See what's available:

```bash
python deploy_to_runpod.py --list-configs
```

### Recommended Configs:

| Budget | Performance | Production |
|--------|-----------|-----------|
| **A100 80GB INT4** | **H100 BF16** | **Dual A100 TP=2** |
| $0.90/hr | $2.69/hr | $1.60/hr |
| 80-120 tok/s | 120-200 tok/s | 150-250 tok/s |

## Step 3: Generate Deployment Files

**For most users (recommended):**

```bash
python deploy_to_runpod.py \
  --config a100_80gb_int4 \
  --output-dir ./deployment
```

**For maximum quality:**

```bash
python deploy_to_runpod.py \
  --config h100_80gb_bf16 \
  --output-dir ./deployment
```

**For production (multiple GPUs):**

```bash
python deploy_to_runpod.py \
  --config a100_40gb_tp2_int4 \
  --output-dir ./deployment
```

## Step 4: Build Docker Image

```bash
cd deployment

# Build the image
docker build -t gemma4-runpod:latest .

# Tag for DockerHub
docker tag gemma4-runpod:latest YOUR_DOCKER_USERNAME/gemma4-runpod:latest

# Push to registry
docker push YOUR_DOCKER_USERNAME/gemma4-runpod:latest
```

**Example with Docker username:**

```bash
docker build -t gemma4-runpod:latest .
docker tag gemma4-runpod:latest johndoe/gemma4-runpod:latest
docker push johndoe/gemma4-runpod:latest
```

## Step 5: Create RunPod Endpoint

1. **Open RunPod Console:** https://www.runpod.io/console/serverless

2. **Create New Template:**
   - Click: **+ New Template**
   - Name: `Gemma-4-31B`
   - Container Image: `YOUR_DOCKER_USERNAME/gemma4-runpod:latest`
   - **Container Disk:** 50GB
   - Click: **Save Template**

3. **Add Environment Variables:**
   - Click your template
   - **Environment Variables:**
     - `HF_TOKEN` = your Hugging Face token
     - `QUANTIZATION` = `int4` (or `None` for BF16)
     - `MODEL_NAME` = `google/gemma-4-31b-it`

4. **Create Endpoint:**
   - Click: **+ Deploy**
   - Select your template
   - Choose GPU: `A100` or `H100`
   - Set workers: min=1, max=3
   - Click: **Deploy**

5. **Wait for Ready:**
   - Status will show: `READY` (typically 5-10 min)
   - Copy your **Endpoint ID**

## Step 6: Test the Endpoint

```bash
# Test with default prompt
python test_endpoint.py --endpoint-id YOUR_ENDPOINT_ID

# Test with custom prompt
python test_endpoint.py \
  --endpoint-id YOUR_ENDPOINT_ID \
  --prompt "What is quantum computing?" \
  --max-tokens 512

# Run benchmark (5 requests)
python test_endpoint.py \
  --endpoint-id YOUR_ENDPOINT_ID \
  --benchmark 5
```

### Expected Output:

```
TEST REQUEST
================================================
Endpoint: YOUR_ENDPOINT_ID
Prompt: What is artificial intelligence?
Max Tokens: 256

Sending request...
✓ Job submitted. ID: abc123...
Waiting for results...
✓ Completed in 5 polls (8.2s)

TEST RESULT
================================================
Status: COMPLETED
Generated Text:
---
Artificial intelligence (AI) refers to the intelligence
exhibited by machines or software. It is demonstrated by
machines that imitate cognitive functions that humans
associate with other human minds...
---

Usage:
  Prompt Tokens: 8
  Completion Tokens: 256
  Total Tokens: 264
  Finish Reason: length
```

## Step 7: Use in Your App

### Python Example

```python
import requests
import json

ENDPOINT_ID = "YOUR_ENDPOINT_ID"
API_KEY = "your_runpod_api_key"

def generate_text(prompt, max_tokens=256):
    url = f"https://api.runpod.io/v1/{ENDPOINT_ID}/run"
    
    payload = {
        "input": {
            "prompt": prompt,
            "max_tokens": max_tokens,
            "temperature": 0.7,
            "top_p": 0.9,
        }
    }
    
    response = requests.post(url, json=payload)
    data = response.json()
    
    # Poll for results
    job_id = data["id"]
    status_url = f"https://api.runpod.io/v1/{ENDPOINT_ID}/status/{job_id}"
    
    import time
    while True:
        status = requests.get(status_url).json()
        if status["status"] == "COMPLETED":
            return status["output"]["generated_text"]
        time.sleep(1)

# Use it
result = generate_text("What is AI?")
print(result)
```

### cURL Example

```bash
curl -X POST "https://api.runpod.io/v1/YOUR_ENDPOINT_ID/run" \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "prompt": "What is artificial intelligence?",
      "max_tokens": 256,
      "temperature": 0.7
    }
  }'
```

## Troubleshooting

### "Model not found on Hugging Face"
→ Make sure `HF_TOKEN` is set and valid

### "CUDA out of memory"
→ Reduce `GPU_MEMORY_UTILIZATION` to 0.80 or use INT4 quantization

### "Worker failed to start"
→ Check Docker image was pushed correctly
→ Check `HF_TOKEN` environment variable is set

### "Request timeout"
→ First request can take 20-30s (model loading)
→ Subsequent requests: 5-15s

### Endpoint stuck in "INITIALIZING"
→ Check logs in RunPod console
→ Restart endpoint

## Cost Examples

### Monthly Usage (24/7 running)

| Config | Cost/Month | Throughput |
|--------|-----------|-----------|
| A100 80GB INT4 | ~$930 | 80-120 tok/s |
| H100 BF16 | ~$1,930 | 120-200 tok/s |
| A100 40GB TP=2 | ~$1,150 | 150-250 tok/s |

### Estimated Monthly Cost for 1M Requests

- **500K tokens avg per request**
- **Total: 500M tokens/month**

| Config | Requests/Hour | Hours Needed | Cost |
|--------|--------------|-------------|------|
| A100 INT4 (100 tok/s) | 360 | 2,777h | $3,577 |
| H100 BF16 (160 tok/s) | 576 | 1,736h | $4,670 |
| Dual A100 TP (200 tok/s) | 720 | 1,389h | $2,222 |

## Next Steps

1. ✅ Test endpoint works
2. ✅ Integrate into your application
3. ✅ Monitor costs and performance
4. ✅ Scale workers as needed (min/max in RunPod console)

## Support

- **RunPod Docs:** https://docs.runpod.io/
- **vLLM Issues:** https://github.com/vllm-project/vllm/issues
- **Gemma Model:** https://huggingface.co/google/gemma-4-31b-it

---

**That's it!** You now have Gemma-4-31B running on RunPod. 🎉
