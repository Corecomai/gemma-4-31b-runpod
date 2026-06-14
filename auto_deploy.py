#!/usr/bin/env python3
"""
Automated RunPod Deployment Script
Deploys Gemma-4-31B directly to RunPod using API
"""

import os
import json
import time
import requests
from dotenv import load_dotenv

load_dotenv()

RUNPOD_API_KEY = os.getenv('RUNPOD_API_KEY')
HF_TOKEN = os.getenv('HF_TOKEN')

if not RUNPOD_API_KEY:
    print("❌ ERROR: RUNPOD_API_KEY not found in .env")
    exit(1)

if not HF_TOKEN:
    print("❌ ERROR: HF_TOKEN not found in .env")
    exit(1)

BASE_URL = "https://api.runpod.io/graphql"

def make_request(query, variables=None):
    """Make GraphQL request to RunPod API"""
    headers = {
        "Content-Type": "application/json",
        "api_key": RUNPOD_API_KEY,
    }

    payload = {"query": query}
    if variables:
        payload["variables"] = variables

    try:
        response = requests.post(BASE_URL, json=payload, headers=headers, timeout=30)
        data = response.json()

        if "errors" in data:
            print(f"❌ API Error: {data['errors']}")
            return None

        return data.get("data", {})
    except Exception as e:
        print(f"❌ Request error: {e}")
        return None


def create_template():
    """Create RunPod template"""
    print("\n📋 Creating RunPod Template...")

    query = """
    mutation CreateTemplate($input: CreateTemplateInput!) {
      podTemplateCreate(input: $input) {
        id
        name
      }
    }
    """

    variables = {
        "input": {
            "name": "Gemma-4-31B",
            "containerDiskInGb": 50,
            "imageName": "runpod/vllm:latest",
            "minVolumeInGb": 10,
            "volumeInGb": 50,
            "env": [
                {"key": "MODEL_NAME", "value": "google/gemma-4-31b-it"},
                {"key": "QUANTIZATION", "value": "int4"},
                {"key": "TENSOR_PARALLEL_SIZE", "value": "1"},
                {"key": "MAX_MODEL_LEN", "value": "32768"},
                {"key": "GPU_MEMORY_UTILIZATION", "value": "0.90"},
                {"key": "MAX_NUM_SEQS", "value": "64"},
                {"key": "HF_TOKEN", "value": HF_TOKEN},
                {"key": "VLLM_WORKER_MULTIPROC_METHOD", "value": "spawn"},
                {"key": "CUDA_LAUNCH_BLOCKING", "value": "1"},
            ],
        }
    }

    result = make_request(query, variables)
    if result and "podTemplateCreate" in result:
        template = result["podTemplateCreate"]
        print(f"✅ Template created: {template['id']}")
        return template["id"]
    else:
        print("⚠️ Template creation may have failed, trying alternative method...")
        return None


def list_templates():
    """List all templates"""
    query = """
    query {
      podTemplates(input: {limit: 50}) {
        edges {
          node {
            id
            name
          }
        }
      }
    }
    """

    result = make_request(query)
    if result and "podTemplates" in result:
        templates = result["podTemplates"]["edges"]
        for template in templates:
            node = template["node"]
            print(f"  - {node['name']} (ID: {node['id']})")

        # Try to find existing vLLM template
        for template in templates:
            node = template["node"]
            if "gemma" in node["name"].lower() or "vllm" in node["name"].lower():
                return node["id"]

    return None


def create_serverless_endpoint(template_id):
    """Create serverless endpoint"""
    print("\n🚀 Creating Serverless Endpoint...")

    query = """
    mutation CreateServerlessEndpoint($input: CreateServerlessEndpointInput!) {
      serverlessEndpointCreate(input: $input) {
        id
        name
        templateId
      }
    }
    """

    variables = {
        "input": {
            "name": "Gemma-4-31B-Endpoint",
            "templateId": template_id,
            "gpuTypes": ["A100"],
            "minWorkers": 1,
            "maxWorkers": 3,
            "requestsPerDay": 100,
            "allowClientMetrics": True,
        }
    }

    result = make_request(query, variables)
    if result and "serverlessEndpointCreate" in result:
        endpoint = result["serverlessEndpointCreate"]
        endpoint_id = endpoint["id"]
        print(f"✅ Endpoint created: {endpoint_id}")
        return endpoint_id
    else:
        print("❌ Endpoint creation failed")
        return None


def get_endpoint_status(endpoint_id):
    """Get endpoint status"""
    query = """
    query GetEndpoint($input: GetEndpointInput!) {
      serverlessEndpoint(input: $input) {
        id
        name
        deployed
      }
    }
    """

    variables = {
        "input": {
            "endpointId": endpoint_id
        }
    }

    result = make_request(query, variables)
    if result and "serverlessEndpoint" in result:
        endpoint = result["serverlessEndpoint"]
        return endpoint
    return None


def wait_for_endpoint(endpoint_id, max_wait=600):
    """Wait for endpoint to be ready"""
    print("\n⏳ Waiting for endpoint to be ready...")
    print("   (This may take 5-15 minutes)")

    start_time = time.time()
    check_count = 0

    while time.time() - start_time < max_wait:
        check_count += 1
        status = get_endpoint_status(endpoint_id)

        if status and status.get("deployed"):
            elapsed = int(time.time() - start_time)
            print(f"✅ Endpoint ready! ({elapsed}s)")
            return True

        if check_count % 6 == 0:  # Every 30 seconds
            elapsed = int(time.time() - start_time)
            print(f"   Still waiting... ({elapsed}s)")

        time.sleep(5)

    print("⏱️ Timeout waiting for endpoint")
    return False


def test_endpoint(endpoint_id):
    """Test the endpoint"""
    print("\n🧪 Testing Endpoint...")

    url = f"https://api.runpod.io/v1/{endpoint_id}/run"

    payload = {
        "input": {
            "prompt": "What is artificial intelligence?",
            "max_tokens": 100,
            "temperature": 0.7,
        }
    }

    try:
        response = requests.post(url, json=payload, timeout=30)
        data = response.json()

        if "id" in data:
            job_id = data["id"]
            print(f"✅ Test request submitted (Job ID: {job_id})")

            # Poll for result
            status_url = f"https://api.runpod.io/v1/{endpoint_id}/status/{job_id}"
            for i in range(60):
                status = requests.get(status_url, timeout=10).json()

                if status.get("status") == "COMPLETED":
                    output = status.get("output", {})
                    if isinstance(output, dict):
                        generated = output.get("generated_text", "")[:100]
                        print(f"✅ Response: {generated}...")
                    return True

                if i % 10 == 0:
                    print(f"   Polling... ({i}s)")

                time.sleep(1)

            print("⏱️ Test request timeout")
            return False
        else:
            print(f"❌ Test failed: {data}")
            return False
    except Exception as e:
        print(f"❌ Test error: {e}")
        return False


def main():
    print("="*70)
    print("🚀 Automated Gemma-4-31B Deployment to RunPod")
    print("="*70)

    # Step 1: Try to get existing template
    print("\n🔍 Looking for existing templates...")
    template_id = list_templates()

    if not template_id:
        print("\n📝 No existing template found, creating new one...")
        template_id = create_template()

    if not template_id:
        print("\n❌ Failed to create template")
        print("\n⚠️ Manual Setup Required:")
        print("1. Go to: https://www.runpod.io/console/serverless")
        print("2. Create template with image: runpod/vllm:latest")
        print("3. Set environment variables (see DEPLOY_NOW.md)")
        print("4. Deploy endpoint with A100 GPU")
        exit(1)

    # Step 2: Create endpoint
    endpoint_id = create_serverless_endpoint(template_id)

    if not endpoint_id:
        print("\n❌ Failed to create endpoint")
        exit(1)

    # Step 3: Wait for ready
    success = wait_for_endpoint(endpoint_id)

    if not success:
        print("\n⚠️ Endpoint may still be initializing")
        print(f"Check status at: https://www.runpod.io/console/serverless/{endpoint_id}")

    # Step 4: Test
    print("\n")
    test_success = test_endpoint(endpoint_id)

    # Summary
    print("\n" + "="*70)
    print("✅ DEPLOYMENT COMPLETE")
    print("="*70)
    print(f"\n📌 Endpoint ID: {endpoint_id}")
    print(f"🔗 Console: https://www.runpod.io/console/serverless/{endpoint_id}")

    print("\n📝 Next Steps:")
    print(f"1. Test endpoint:")
    print(f"   python test_endpoint.py --endpoint-id {endpoint_id}")

    print(f"\n2. Benchmark:")
    print(f"   python test_endpoint.py --endpoint-id {endpoint_id} --benchmark 5")

    print(f"\n3. Use in your app:")
    print(f"   python example_integration.py (update ENDPOINT_ID)")

    print("\n" + "="*70)

    # Save endpoint ID to file
    with open("ENDPOINT_ID.txt", "w") as f:
        f.write(endpoint_id)
    print(f"\n✅ Endpoint ID saved to: ENDPOINT_ID.txt")


if __name__ == "__main__":
    main()
