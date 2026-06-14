# 🚀 Deploy Gemma-4-31B to RunPod NOW (No Local Docker)

**Total time: 5-10 minutes**

## Option 1: Use Official RunPod vLLM Image (Fastest)

### Step 1: Go to RunPod Console
https://www.runpod.io/console/serverless

### Step 2: Create New Endpoint

1. Click: **+ Create New Endpoint**

2. Create Template:
   - **Name:** `Gemma-4-31B`
   - **Container Image:** `runpod/vllm:latest`
   - **Container Disk:** `50 GB`
   - **Volume Size:** `50 GB`

3. Add Environment Variables:
   ```
   MODEL_NAME=google/gemma-4-31b-it
   QUANTIZATION=int4
   TENSOR_PARALLEL_SIZE=1
   MAX_MODEL_LEN=32768
   GPU_MEMORY_UTILIZATION=0.90
   VLLM_WORKER_MULTIPROC_METHOD=spawn
   HF_TOKEN=your_hugging_face_token_here
   ```

4. Click: **Save Template**

### Step 3: Deploy Endpoint

1. Click your template
2. Click: **Deploy**
3. Select GPU: **A100 80GB** (or H100 if available)
4. Set Workers:
   - Min: `1`
   - Max: `3`
5. Click: **Deploy**

### Step 4: Wait for Ready

Status will show: `READY` (5-10 minutes)

Copy your **Endpoint ID** (looks like: `abc123xyz...`)

### Step 5: Test It

```bash
python test_endpoint.py --endpoint-id YOUR_ENDPOINT_ID
```

---

## Option 2: Push Custom Docker Image

If you want to use the optimized Dockerfile we created:

### Step 1: Build & Push Locally

```bash
# Build
docker build -t gemma4-runpod:latest .

# Tag for DockerHub
docker tag gemma4-runpod:latest YOUR_DOCKER_USERNAME/gemma4-runpod:latest

# Push (requires docker login)
docker login
docker push YOUR_DOCKER_USERNAME/gemma4-runpod:latest
```

### Step 2: Create Template on RunPod

1. Go: https://www.runpod.io/console/serverless
2. **+ Create New Template**
3. **Container Image:** `YOUR_DOCKER_USERNAME/gemma4-runpod:latest`
4. Add HF_TOKEN to environment variables
5. Save & Deploy

---

## ✅ Verification

Once deployed, test with:

```bash
python test_endpoint.py --endpoint-id YOUR_ENDPOINT_ID \
  --prompt "What is artificial intelligence?" \
  --max-tokens 256
```

Expected response in ~8-15 seconds (first request slower due to model loading)

---

## 🐛 Troubleshooting

**"Model not found"**
→ Check HF_TOKEN is correct and set in environment

**"Out of memory"**
→ Change QUANTIZATION to int4 (we already did this)

**"Waiting for pod to be ready..."**
→ First deployment takes 10-15 min, be patient

**"Connection timeout"**
→ Check endpoint status is RUNNING in RunPod console

---

## 💡 What's Next?

Once working:
1. Integrate into your app using `example_integration.py`
2. Run benchmarks: `python test_endpoint.py --endpoint-id YOUR_ID --benchmark 10`
3. Scale workers in RunPod console as needed

---

**That's it! You now have Gemma-4-31B running on RunPod.** 🎉
