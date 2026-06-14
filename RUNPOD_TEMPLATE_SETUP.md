# 🚀 Create RunPod Template - Step by Step

## Option 1: Create Template from GitHub (Recommended)

### Step 1: Go to Templates
**URL:** https://www.runpod.io/console/templates

Click: **+ New Template**

### Step 2: Choose GitHub Source

Look for options:
- [ ] Deploy from GitHub
- [ ] GitHub Repository

**Select:** Deploy from GitHub

### Step 3: Authorize & Select Repository

1. Click: **Connect GitHub** (if not already connected)
2. Authorize RunPod to access your GitHub
3. **Search for:** `Corecomai/gemma-4-31b-runpod`
4. **Click:** Select it

### Step 4: Configure Basic Settings

Fill in these fields:

```
Template Name:           Gemma-4-31B-GitHub
Description:            Google Gemma-4-31B LLM with vLLM on RunPod
GitHub Branch:          main
Dockerfile Path:        ./Dockerfile
Container Disk (GB):    50
Min Volume (GB):        10
Volume (GB):            50
```

### Step 5: Add Environment Variables

Click: **+ Add Variable** for each of these:

#### Variable 1
```
Key:   MODEL_NAME
Value: google/gemma-4-31b-it
```

#### Variable 2
```
Key:   QUANTIZATION
Value: int4
```

#### Variable 3
```
Key:   TENSOR_PARALLEL_SIZE
Value: 1
```

#### Variable 4
```
Key:   MAX_MODEL_LEN
Value: 32768
```

#### Variable 5
```
Key:   GPU_MEMORY_UTILIZATION
Value: 0.90
```

#### Variable 6
```
Key:   MAX_NUM_SEQS
Value: 64
```

#### Variable 7
```
Key:   VLLM_WORKER_MULTIPROC_METHOD
Value: spawn
```

#### Variable 8
```
Key:   CUDA_LAUNCH_BLOCKING
Value: 1
```

#### Variable 9
```
Key:   HF_TOKEN
Value: your_hugging_face_token_here
```

### Step 6: Save Template

Click: **Save Template**

You should see:
```
✅ Template created successfully
Template ID: template_xxxxx
```

---

## Option 2: Create Template from Docker Image

If GitHub option isn't available:

### Step 1: Go to Templates
**URL:** https://www.runpod.io/console/templates

Click: **+ New Template**

### Step 2: Choose Docker Source

Select: **Docker Image** or **Use Docker Registry**

### Step 3: Enter Docker Image

```
Docker Image: runpod/vllm:latest
```

### Step 4: Configure

Same as Option 1, Steps 4-6

---

## Option 3: Manual Template (Copy-Paste Ready)

If you need to fill fields manually, here's all the info:

### Basic Configuration
```
Name:                   Gemma-4-31B
Description:            Gemma 4 31B LLM with vLLM inference
Container Image:        runpod/vllm:latest
                        OR github.com/Corecomai/gemma-4-31b-runpod
Container Disk:         50 GB
Volume:                 50 GB
```

### Environment Variables (Copy-paste as needed)
```
MODEL_NAME=google/gemma-4-31b-it
QUANTIZATION=int4
TENSOR_PARALLEL_SIZE=1
MAX_MODEL_LEN=32768
GPU_MEMORY_UTILIZATION=0.90
MAX_NUM_SEQS=64
VLLM_WORKER_MULTIPROC_METHOD=spawn
CUDA_LAUNCH_BLOCKING=1
HF_TOKEN=your_hugging_face_token_here
```

---

## ✅ Verify Template Created

Once saved, you should see:
- Template name: **Gemma-4-31B-GitHub** (or your chosen name)
- Status: **Ready to Deploy**
- Environment Variables: **9 variables configured**

---

## 🚀 Deploy from Template

1. Go to: https://www.runpod.io/console/serverless
2. Click: **+ Create New Endpoint**
3. Select: **Gemma-4-31B-GitHub** template
4. Choose GPU: **A100 80GB**
5. Set Workers:
   - Min: 1
   - Max: 3
6. Click: **Deploy**

---

## ⏳ Monitor Deployment

Status will show:
- `INITIALIZING` → Building container from GitHub
- `BUILDING` → Running Docker build
- `RUNNING` → Ready to use!

This takes **5-15 minutes**

---

## 🧪 Test Endpoint

Once running, copy your **Endpoint ID** and run:

```bash
python test_endpoint.py --endpoint-id YOUR_ENDPOINT_ID
```

---

## 📝 Notes

- **If Docker option not working:** Use `runpod/vllm:latest` as image
- **If GitHub not available:** Use Docker image method above
- **Template will auto-build** from GitHub on each deployment
- **You can update template** anytime by editing it in console

---

**Follow these steps and let me know which method works for you!** 🚀
