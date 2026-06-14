# 🚀 Your RunPod Endpoint: oodajsphk20uyr

**Console:** https://console.runpod.io/serverless/user/endpoint/oodajsphk20uyr

---

## 📊 Endpoint Status

Go to the console link above to see:
- ✅ Status (RUNNING, INITIALIZING, etc)
- 📊 Worker count
- 📈 Queue length
- 📝 Logs
- 🔧 Settings

---

## 🔗 API Endpoints

### Base URL
```
https://api.runpod.io/v2/oodajsphk20uyr
```

### Operations

**1. Async Execution** (returns immediately)
```
POST https://api.runpod.io/v2/oodajsphk20uyr/run
```

**2. Sync Execution** (waits for result)
```
POST https://api.runpod.io/v2/oodajsphk20uyr/runsync
```

**3. Check Status**
```
GET https://api.runpod.io/v2/oodajsphk20uyr/status/{job_id}
```

**4. Health Check**
```
GET https://api.runpod.io/v2/oodajsphk20uyr/health
```

---

## 📨 Request Format

### Headers
```
Content-Type: application/json
Authorization: Bearer YOUR_RUNPOD_API_KEY
```

### Body
```json
{
  "input": {
    "prompt": "Your prompt here",
    "max_tokens": 256,
    "temperature": 0.7
  }
}
```

---

## 🧪 Test Locally

### Option 1: Using Our Test Script
```bash
cd /Users/shubhammohape/Documents/RunPod
python test_endpoint.py --endpoint-id oodajsphk20uyr
```

### Option 2: Using cURL
```bash
curl -X POST https://api.runpod.io/v2/oodajsphk20uyr/runsync \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_RUNPOD_API_KEY" \
  -d '{
    "input": {
      "prompt": "What is artificial intelligence?"
    }
  }'
```

### Option 3: Using Python
```python
import requests
import os

ENDPOINT_ID = "oodajsphk20uyr"
API_KEY = os.getenv("RUNPOD_API_KEY")

response = requests.post(
    f"https://api.runpod.io/v2/{ENDPOINT_ID}/runsync",
    headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    },
    json={
        "input": {
            "prompt": "What is artificial intelligence?"
        }
    }
)

result = response.json()
print(f"Status: {result['status']}")
print(f"Output: {result.get('output')}")
```

### Option 4: Using JavaScript
```javascript
const ENDPOINT_ID = "oodajsphk20uyr";
const API_KEY = process.env.RUNPOD_API_KEY;

const response = await fetch(
  `https://api.runpod.io/v2/${ENDPOINT_ID}/runsync`,
  {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${API_KEY}`
    },
    body: JSON.stringify({
      input: {
        prompt: "What is artificial intelligence?"
      }
    })
  }
);

const result = await response.json();
console.log("Status:", result.status);
console.log("Output:", result.output);
```

---

## 📋 Parameters

### Inference Parameters
```
prompt              - (required) Input text
max_tokens          - (optional, default: 1024) Max output length
temperature         - (optional, default: 0.7) Randomness (0-1)
top_p              - (optional, default: 0.9) Nucleus sampling
top_k              - (optional, default: 50) Top-K sampling
repetition_penalty - (optional, default: 1.0) Penalize repetition
```

### Advanced Parameters
```
timeout             - Job timeout in seconds
webhook             - URL to POST results when complete
policy              - Execution policy (priority, TTL, etc)
```

---

## 📊 Response Format

### Success Response
```json
{
  "id": "job-12345",
  "status": "COMPLETED",
  "output": {
    "generated_text": "Artificial intelligence refers to..."
  },
  "usage": {
    "prompt_tokens": 8,
    "completion_tokens": 256
  }
}
```

### Async Response (immediate)
```json
{
  "id": "job-12345",
  "status": "IN_QUEUE"
}
```

### Status Check Response
```json
{
  "id": "job-12345",
  "status": "COMPLETED",
  "output": {
    "generated_text": "..."
  },
  "delayTime": 1234,
  "executionTime": 5678
}
```

---

## ⏱️ Job Status Values

| Status | Meaning |
|--------|---------|
| `IN_QUEUE` | Waiting to run |
| `IN_PROGRESS` | Currently executing |
| `COMPLETED` | Finished successfully |
| `FAILED` | Execution failed |
| `CANCELLED` | Job was cancelled |
| `TIMEOUT` | Job exceeded time limit |

---

## 🔄 Polling for Results (Async)

```python
import time
import requests

# Submit async job
response = requests.post(
    "https://api.runpod.io/v2/oodajsphk20uyr/run",
    headers={"Authorization": f"Bearer {API_KEY}"},
    json={"input": {"prompt": "Hello"}}
)

job_id = response.json()["id"]
print(f"Job ID: {job_id}")

# Poll for results
while True:
    status = requests.get(
        f"https://api.runpod.io/v2/oodajsphk20uyr/status/{job_id}",
        headers={"Authorization": f"Bearer {API_KEY}"}
    ).json()
    
    print(f"Status: {status['status']}")
    
    if status["status"] == "COMPLETED":
        print(f"Result: {status['output']}")
        break
    elif status["status"] == "FAILED":
        print(f"Error: {status.get('error')}")
        break
    
    time.sleep(2)  # Wait 2 seconds before checking again
```

---

## 🔐 Security Best Practices

✅ **Do:**
- Keep API key in environment variables
- Use HTTPS (always https://, never http://)
- Rotate API keys regularly
- Use specific scopes if available

❌ **Don't:**
- Commit API key to git
- Share API key in chat/email
- Use in client-side code
- Log full requests with secrets

---

## 📞 Troubleshooting

### "Unauthorized" Error
- Check `RUNPOD_API_KEY` is set
- Verify API key is correct
- Check `Authorization` header format

### "Endpoint not found"
- Verify endpoint ID: `oodajsphk20uyr`
- Check endpoint is deployed (console shows RUNNING)

### Timeout
- Model still loading (first request takes 15-30s)
- Increase timeout parameter
- Check RunPod console for errors

### Job stuck in queue
- Check worker count (increase min workers)
- Check RunPod console for errors

---

## 📊 Monitoring

**Check endpoint health:**
```bash
curl https://api.runpod.io/v2/oodajsphk20uyr/health \
  -H "Authorization: Bearer YOUR_RUNPOD_API_KEY"
```

**View logs:**
Go to: https://console.runpod.io/serverless/user/endpoint/oodajsphk20uyr?tab=logs

---

## 🚀 Quick Reference

| Task | Command |
|------|---------|
| Test | `python test_endpoint.py --endpoint-id oodajsphk20uyr` |
| Sync call | `POST /v2/oodajsphk20uyr/runsync` |
| Async call | `POST /v2/oodajsphk20uyr/run` |
| Check status | `GET /v2/oodajsphk20uyr/status/{job_id}` |
| View console | https://console.runpod.io/serverless/user/endpoint/oodajsphk20uyr |

---

**Your endpoint is ready to use!** 🎉
