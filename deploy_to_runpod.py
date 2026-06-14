#!/usr/bin/env python3
"""
RunPod Deployment Script for Gemma-4-31B-it

This script helps you deploy the Gemma-4-31B-it model to RunPod Serverless
with different configurations (int4, int8, bf16) and GPU options.

Usage:
    python deploy_to_runpod.py --config a100_80gb_int4
    python deploy_to_runpod.py --config h100_80gb_bf16 --endpoint-name my-gemma-endpoint
"""

import os
import sys
import json
import argparse
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
import subprocess

try:
    import requests
except ImportError:
    print("ERROR: requests library not installed. Install with: pip install requests")
    sys.exit(1)

from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class RunPodDeployer:
    """Deploy Gemma-4-31B to RunPod Serverless"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.runpod.io/graphql"
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "api_key": api_key,
        })

    def get_available_gpus(self) -> list:
        """Get list of available GPU types on RunPod"""
        query = """
        {
            podFindAndDeployOnDemand {
                id
                gpuType
                maxBidPrice
                minBidPrice
            }
        }
        """
        try:
            response = self.session.post(self.base_url, json={"query": query})
            response.raise_for_status()
            data = response.json()
            if "errors" in data:
                print(f"API Error: {data['errors']}")
                return []
            return data.get("data", {}).get("podFindAndDeployOnDemand", [])
        except Exception as e:
            print(f"Error fetching GPU availability: {e}")
            return []

    def create_dockerfile(self, config: Dict[str, Any], output_path: Path = None) -> str:
        """Generate a Dockerfile for the deployment"""

        if output_path is None:
            output_path = Path("Dockerfile")

        quantization = config.get('quantization', 'None')
        if quantization is None:
            quantization = "None"

        dockerfile_content = f"""FROM nvidia/cuda:12.1.1-runtime-ubuntu22.04

WORKDIR /src

# Install Python and dependencies
RUN apt-get update && apt-get install -y \\
    python3.10 \\
    python3-pip \\
    git \\
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

# Configuration
ENV MODEL_NAME=google/gemma-4-31b-it
ENV QUANTIZATION={quantization}
ENV TENSOR_PARALLEL_SIZE={config.get('tensor_parallel_size', 1)}
ENV MAX_MODEL_LEN={config.get('max_model_len', 32768)}
ENV GPU_MEMORY_UTILIZATION={config.get('gpu_memory_utilization', 0.90)}
ENV MAX_NUM_SEQS={config.get('max_num_seqs', 64)}
ENV HF_TOKEN=${{HF_TOKEN}}

# Pre-download model (optional - uncomment if using Hugging Face token)
# RUN python3 -c "from transformers import AutoTokenizer, AutoModelForCausalLM; \\
#     tokenizer = AutoTokenizer.from_pretrained('google/gemma-4-31b-it'); \\
#     model = AutoModelForCausalLM.from_pretrained('google/gemma-4-31b-it', device_map='auto')"

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \\
    CMD python3 -c "import sys; sys.exit(0)" || exit 1

# Run handler
CMD ["python3", "-c", "import asyncio; from handler import handler; asyncio.run(handler({{'prompt': 'test'}}))"]
"""

        with open(output_path, 'w') as f:
            f.write(dockerfile_content)

        print(f"✓ Dockerfile created at {output_path}")
        return dockerfile_content

    def create_env_file(self, config: Dict[str, Any], hf_token: str = None, output_path: Path = None) -> str:
        """Generate .env file for the deployment"""

        if output_path is None:
            output_path = Path(".env.runpod")

        quantization = config.get('quantization') or 'None'

        env_content = f"""# Gemma-4-31B RunPod Configuration
# {config.get('name', 'Custom Config')}

MODEL_NAME=google/gemma-4-31b-it
QUANTIZATION={quantization}
TENSOR_PARALLEL_SIZE={config.get('tensor_parallel_size', 1)}
MAX_MODEL_LEN={config.get('max_model_len', 32768)}
GPU_MEMORY_UTILIZATION={config.get('gpu_memory_utilization', 0.90)}
MAX_NUM_SEQS={config.get('max_num_seqs', 64)}
MAX_TOKENS_PER_BATCH={config.get('max_tokens_per_batch', 16384)}

# Hugging Face token for model access
HF_TOKEN={hf_token or 'YOUR_HF_TOKEN_HERE'}

# vLLM optimization flags
VLLM_WORKER_MULTIPROC_METHOD=spawn
CUDA_LAUNCH_BLOCKING=1
OMP_NUM_THREADS=1
CUDA_VISIBLE_DEVICES=0
"""

        with open(output_path, 'w') as f:
            f.write(env_content)

        print(f"✓ .env file created at {output_path}")
        return env_content

    def create_runpod_config(self, config: Dict[str, Any], output_path: Path = None) -> str:
        """Generate RunPod template configuration"""

        if output_path is None:
            output_path = Path("runpod_config.json")

        gpu_type = config.get('gpu_type', 'A100')
        gpu_count = config.get('gpu_count', 1)

        runpod_config = {
            "containerDiskInGb": 50,
            "imageName": "your-docker-image:latest",  # Update with your image
            "minVolumeInGb": 0,
            "env": [
                {
                    "key": "MODEL_NAME",
                    "value": "google/gemma-4-31b-it"
                },
                {
                    "key": "QUANTIZATION",
                    "value": config.get('quantization') or 'None'
                },
                {
                    "key": "TENSOR_PARALLEL_SIZE",
                    "value": str(config.get('tensor_parallel_size', 1))
                },
                {
                    "key": "MAX_MODEL_LEN",
                    "value": str(config.get('max_model_len', 32768))
                },
                {
                    "key": "HF_TOKEN",
                    "value": "YOUR_HF_TOKEN"
                }
            ],
            "containerDiskInGb": 50,
            "minDiskInGb": 20,
            "gpuTypes": [gpu_type],
            "minCount": gpu_count,
            "maxCount": gpu_count,
            "supportPublicIp": True,
        }

        with open(output_path, 'w') as f:
            json.dump(runpod_config, f, indent=2)

        print(f"✓ RunPod config created at {output_path}")
        return json.dumps(runpod_config, indent=2)

    def print_deployment_guide(self, config: Dict[str, Any]):
        """Print step-by-step deployment guide"""

        print("\n" + "="*70)
        print(f"DEPLOYMENT GUIDE: {config['name']}")
        print("="*70)

        print(f"""
Configuration Details:
  - GPU Type: {config.get('gpu_type')} (×{config.get('gpu_count', 1)})
  - VRAM Required: {config.get('vram_required')}
  - Quantization: {config.get('quantization') or 'None (Full Precision)'}
  - Max Context Length: {config.get('max_model_len')} tokens
  - Expected Throughput: {config.get('expected_throughput')}
  - Cost per Hour: {config.get('cost_per_hour')}
  - Quality: {config.get('quality')}

DEPLOYMENT STEPS:

1. Build Docker Image:
   docker build -t gemma4-runpod:latest .

2. Push to DockerHub (or your registry):
   docker tag gemma4-runpod:latest your-username/gemma4-runpod:latest
   docker push your-username/gemma4-runpod:latest

3. Create RunPod Template:
   - Go to: https://www.runpod.io/console/templates
   - Create New Template
   - Use the runpod_config.json as reference
   - Set container image to: your-username/gemma4-runpod:latest
   - Set environment variables from .env.runpod

4. Deploy Serverless Endpoint:
   - Go to: https://www.runpod.io/console/serverless
   - Create New Endpoint
   - Select your template
   - Configure: {config.get('gpu_type')} with {config.get('gpu_count')} GPU(s)
   - Set scaling and cold-start preferences

5. Test the Endpoint:
   python test_endpoint.py --endpoint-id YOUR_ENDPOINT_ID

NOTES:
{config.get('notes', 'No additional notes')}

Documentation:
  - RunPod Docs: https://docs.runpod.io/
  - vLLM Docs: https://docs.vllm.ai/
  - Gemma Model: https://huggingface.co/google/gemma-4-31b-it
""")


def load_configs() -> Dict[str, Dict[str, Any]]:
    """Load configurations from YAML file"""
    config_path = Path(__file__).parent / "configs.yaml"

    if not config_path.exists():
        print(f"ERROR: configs.yaml not found at {config_path}")
        sys.exit(1)

    with open(config_path, 'r') as f:
        data = yaml.safe_load(f)

    return data.get('configs', {})


def main():
    parser = argparse.ArgumentParser(
        description="Deploy Gemma-4-31B to RunPod Serverless",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List available configurations
  python deploy_to_runpod.py --list-configs

  # Create deployment files for A100 80GB INT4
  python deploy_to_runpod.py --config a100_80gb_int4 --output-dir ./deployment

  # Create deployment with custom name
  python deploy_to_runpod.py --config h100_80gb_bf16 --endpoint-name my-gemma
        """
    )

    parser.add_argument(
        '--config',
        type=str,
        help='Configuration name (see --list-configs)'
    )
    parser.add_argument(
        '--list-configs',
        action='store_true',
        help='List all available configurations'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default='.',
        help='Output directory for generated files (default: current directory)'
    )
    parser.add_argument(
        '--endpoint-name',
        type=str,
        help='Custom endpoint name'
    )
    parser.add_argument(
        '--hf-token',
        type=str,
        help='Hugging Face token (or set HF_TOKEN env var)'
    )

    args = parser.parse_args()

    configs = load_configs()

    if args.list_configs:
        print("\nAvailable Configurations:")
        print("="*70)
        for config_name, config in configs.items():
            print(f"\n{config_name}:")
            print(f"  Name: {config.get('name')}")
            print(f"  GPU: {config.get('gpu_type')} (×{config.get('gpu_count')})")
            print(f"  VRAM: {config.get('vram_required')}")
            print(f"  Quantization: {config.get('quantization') or 'None'}")
            print(f"  Throughput: {config.get('expected_throughput')}")
            print(f"  Cost: {config.get('cost_per_hour')}/hr")
            print(f"  Quality: {config.get('quality')}")
        return

    if not args.config:
        parser.print_help()
        sys.exit(0)

    if args.config not in configs:
        print(f"ERROR: Configuration '{args.config}' not found")
        print(f"Available: {', '.join(configs.keys())}")
        sys.exit(1)

    config = configs[args.config]
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Get HF token
    hf_token = args.hf_token or os.getenv('HF_TOKEN')
    if not hf_token:
        print("WARNING: HF_TOKEN not set. Model download may fail.")
        print("Set HF_TOKEN environment variable or use --hf-token flag")

    # Generate deployment files
    print(f"\n✓ Generating deployment files for: {config['name']}")

    deployer = RunPodDeployer(os.getenv('RUNPOD_API_KEY', ''))

    # Create files
    deployer.create_dockerfile(config, output_dir / "Dockerfile")
    deployer.create_env_file(config, hf_token, output_dir / ".env.runpod")
    deployer.create_runpod_config(config, output_dir / "runpod_config.json")

    # Print guide
    deployer.print_deployment_guide(config)

    print(f"\n✓ Generated files in: {output_dir}")
    print("Files created:")
    print(f"  - {output_dir}/Dockerfile")
    print(f"  - {output_dir}/.env.runpod")
    print(f"  - {output_dir}/runpod_config.json")


if __name__ == "__main__":
    main()
