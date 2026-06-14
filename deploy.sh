#!/bin/bash
# RunPod Gemma-4-31B Deployment Script

set -e

echo "========================================"
echo "🚀 RunPod Gemma-4-31B Deployment"
echo "========================================"
echo ""

# Load environment
source .env

if [ -z "$RUNPOD_API_KEY" ]; then
    echo "❌ ERROR: RUNPOD_API_KEY not found in .env"
    exit 1
fi

if [ -z "$HF_TOKEN" ]; then
    echo "❌ ERROR: HF_TOKEN not found in .env"
    exit 1
fi

echo "✅ Credentials loaded"
echo ""

# Step 1: Get available GPUs
echo "📋 Checking available GPUs..."

curl -s -X POST "https://api.runpod.io/graphql" \
  -H "Content-Type: application/json" \
  -H "api_key: $RUNPOD_API_KEY" \
  -d '{
    "query": "{ podFindAndDeployOnDemand { id gpuType maxBidPrice } }"
  }' | jq '.' > /tmp/gpus.json

echo "Available GPUs:"
cat /tmp/gpus.json | jq '.data.podFindAndDeployOnDemand[0:5] | .[] | {gpuType, maxBidPrice}'

echo ""
echo "========================================"
echo "✅ MANUAL SETUP REQUIRED"
echo "========================================"
echo ""
echo "Please go to: https://www.runpod.io/console/serverless"
echo ""
echo "Create New Endpoint with these settings:"
echo ""
echo "TEMPLATE SETTINGS:"
echo "  Name: Gemma-4-31B"
echo "  Image: runpod/vllm:latest"
echo "  Container Disk: 50 GB"
echo "  Volume: 50 GB"
echo ""
echo "ENVIRONMENT VARIABLES:"
echo "  MODEL_NAME=google/gemma-4-31b-it"
echo "  QUANTIZATION=int4"
echo "  TENSOR_PARALLEL_SIZE=1"
echo "  MAX_MODEL_LEN=32768"
echo "  GPU_MEMORY_UTILIZATION=0.90"
echo "  VLLM_WORKER_MULTIPROC_METHOD=spawn"
echo "  HF_TOKEN=$HF_TOKEN"
echo ""
echo "DEPLOYMENT:"
echo "  GPU Type: A100 80GB"
echo "  Min Workers: 1"
echo "  Max Workers: 3"
echo ""
echo "After deployment, save your Endpoint ID and run:"
echo "  python test_endpoint.py --endpoint-id YOUR_ENDPOINT_ID"
echo ""
echo "========================================"
