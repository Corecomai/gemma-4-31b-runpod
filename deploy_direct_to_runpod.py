#!/usr/bin/env python3
"""
Direct RunPod Deployment Script - No Local Docker Build Needed

This script deploys Gemma-4-31B directly to RunPod using the official image.
"""

import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

RUNPOD_API_KEY = os.getenv('RUNPOD_API_KEY')
HF_TOKEN = os.getenv('HF_TOKEN')

if not RUNPOD_API_KEY or not HF_TOKEN:
    print("ERROR: Missing credentials in .env")
    print("Need: RUNPOD_API_KEY and HF_TOKEN")
    exit(1)

print("="*70)
print("RunPod Gemma-4-31B Direct Deployment")
print("="*70)

# Step 1: Create Template
print("\nStep 1: Creating RunPod Template...")

template_query = """
mutation {
  podFindAndDeployOnDemand(input: {
    cloudType: ANY
    gpuType: "A100"
    volumeInGb: 50
    containerDiskInGb: 50
    minVolumeInGb: 10
    gpuCount: 1
    volumeMountPath: "/root"
    templateId: "runpod-vllm"
    name: "Gemma-4-31B"
    containerArgsStr: ""
    env: [
      {key: "MODEL_NAME", value: "google/gemma-4-31b-it"}
      {key: "QUANTIZATION", value: "int4"}
      {key: "HF_TOKEN", value: "%s"}
      {key: "MAX_MODEL_LEN", value: "32768"}
      {key: "GPU_MEMORY_UTILIZATION", value: "0.90"}
    ]
  }) {
    id
    name
    desiredStatus
  }
}
""" % HF_TOKEN

headers = {
    "Content-Type": "application/json",
    "api_key": RUNPOD_API_KEY,
}

try:
    response = requests.post(
        "https://api.runpod.io/graphql",
        json={"query": template_query},
        headers=headers,
        timeout=30
    )
    data = response.json()

    if "errors" in data:
        print(f"Error creating pod: {data['errors']}")
        print("\nManual Setup Required:")
        print("1. Go to: https://www.runpod.io/console/serverless")
        print("2. Create New Template with:")
        print("   - Container Image: runpod/vllm:latest")
        print("   - Environment Variables:")
        print(f"     - HF_TOKEN={HF_TOKEN}")
        print("     - MODEL_NAME=google/gemma-4-31b-it")
        print("     - QUANTIZATION=int4")
        print("     - MAX_MODEL_LEN=32768")
        print("     - GPU_MEMORY_UTILIZATION=0.90")
        print("3. Deploy with A100 GPU")
        exit(1)

    pod_data = data.get("data", {}).get("podFindAndDeployOnDemand", {})
    pod_id = pod_data.get("id")

    if pod_id:
        print(f"✓ Pod created: {pod_id}")
        print(f"Status: {pod_data.get('desiredStatus')}")
    else:
        print("Pod creation returned no ID")
        print(json.dumps(data, indent=2))

except Exception as e:
    print(f"Error: {e}")
    print("\nTrying alternative method...")

    # Alternative: Just provide instructions
    print("\n" + "="*70)
    print("MANUAL RUNPOD DEPLOYMENT")
    print("="*70)
    print("""
Follow these steps to deploy on RunPod:

1. Go to: https://www.runpod.io/console/serverless

2. Click: Create New Endpoint

3. Select: Create New Template
   - Name: Gemma-4-31B
   - Container Image: runpod/vllm:latest
   - Container Disk: 50GB
   - Volume: 50GB

4. Add Environment Variables:
   - HF_TOKEN = your_hugging_face_token
   - MODEL_NAME = google/gemma-4-31b-it
   - QUANTIZATION = int4
   - TENSOR_PARALLEL_SIZE = 1
   - MAX_MODEL_LEN = 32768
   - GPU_MEMORY_UTILIZATION = 0.90
   - VLLM_WORKER_MULTIPROC_METHOD = spawn

5. Save Template

6. Deploy:
   - GPU Type: A100 80GB
   - Min Workers: 1
   - Max Workers: 3
   - Click Deploy

7. Wait for status: READY (5-10 minutes)

8. Copy Endpoint ID and test:
   python test_endpoint.py --endpoint-id YOUR_ENDPOINT_ID
""")
