#!/usr/bin/env python3
"""
Test script for RunPod Gemma-4-31B endpoint

Usage:
    python test_endpoint.py --endpoint-id YOUR_ENDPOINT_ID
    python test_endpoint.py --endpoint-id YOUR_ENDPOINT_ID --prompt "Your prompt here"
"""

import os
import sys
import json
import argparse
import time
import requests
from typing import Dict, Any, Optional

from dotenv import load_dotenv

load_dotenv()


class RunPodTester:
    """Test RunPod serverless endpoint"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.runpod.io/v1"

    def test_endpoint(
        self,
        endpoint_id: str,
        prompt: str,
        max_tokens: int = 256,
        temperature: float = 0.7,
        top_p: float = 0.9,
        top_k: int = 50,
        repetition_penalty: float = 1.0,
        timeout: int = 300,
    ) -> Dict[str, Any]:
        """Test the endpoint with a prompt"""

        url = f"{self.base_url}/{endpoint_id}/run"

        payload = {
            "input": {
                "prompt": prompt,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "top_p": top_p,
                "top_k": top_k,
                "repetition_penalty": repetition_penalty,
            }
        }

        headers = {
            "Content-Type": "application/json",
        }

        print(f"\n{'='*70}")
        print("TEST REQUEST")
        print(f"{'='*70}")
        print(f"Endpoint: {endpoint_id}")
        print(f"Prompt: {prompt[:100]}..." if len(prompt) > 100 else f"Prompt: {prompt}")
        print(f"Max Tokens: {max_tokens}")
        print(f"Temperature: {temperature}")
        print(f"\nSending request...")

        try:
            # Send request
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()

            if "id" not in data:
                print(f"ERROR: No job ID in response")
                print(json.dumps(data, indent=2))
                return data

            job_id = data["id"]
            print(f"✓ Job submitted. ID: {job_id}")
            print(f"Waiting for results (timeout: {timeout}s)...")

            # Poll for results
            status_url = f"{self.base_url}/{endpoint_id}/status/{job_id}"
            start_time = time.time()
            poll_count = 0

            while time.time() - start_time < timeout:
                poll_count += 1
                status_response = requests.get(status_url, headers=headers)
                status_data = status_response.json()

                if status_data.get("status") == "COMPLETED":
                    print(f"✓ Completed in {poll_count} polls ({time.time() - start_time:.1f}s)")
                    return self._format_result(status_data)

                elif status_data.get("status") == "FAILED":
                    print(f"✗ Request failed")
                    return self._format_result(status_data)

                time.sleep(2)

            print(f"✗ Request timeout after {timeout}s")
            return {"status": "TIMEOUT"}

        except requests.exceptions.RequestException as e:
            print(f"✗ Request error: {e}")
            return {"status": "ERROR", "error": str(e)}

    def _format_result(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Format and display results"""

        print(f"\n{'='*70}")
        print("TEST RESULT")
        print(f"{'='*70}")

        status = data.get("status")
        print(f"Status: {status}")

        if status == "COMPLETED":
            output = data.get("output", {})

            if isinstance(output, dict):
                print(f"Generated Text:")
                print("-" * 70)
                print(output.get("generated_text", ""))
                print("-" * 70)

                if "usage" in output:
                    usage = output["usage"]
                    print(f"\nUsage:")
                    print(f"  Prompt Tokens: {usage.get('prompt_tokens', 'N/A')}")
                    print(f"  Completion Tokens: {usage.get('completion_tokens', 'N/A')}")
                    total = usage.get('prompt_tokens', 0) + usage.get('completion_tokens', 0)
                    print(f"  Total Tokens: {total}")

                if "finish_reason" in output:
                    print(f"  Finish Reason: {output['finish_reason']}")
            else:
                print(f"Output: {output}")

        elif status == "FAILED":
            print(f"Error: {data.get('error', 'Unknown error')}")
            if "traceback" in data:
                print(f"\nTraceback:")
                print(data["traceback"])

        print()
        return data

    def run_benchmark(self, endpoint_id: str, num_requests: int = 5) -> Dict[str, Any]:
        """Run benchmark tests"""

        prompts = [
            "What is artificial intelligence?",
            "Explain quantum computing in simple terms.",
            "Write a Python function to calculate fibonacci numbers.",
            "What are the main causes of climate change?",
            "How does photosynthesis work?",
        ]

        print(f"\n{'='*70}")
        print(f"RUNNING BENCHMARK ({num_requests} requests)")
        print(f"{'='*70}\n")

        results = []
        times = []

        for i, prompt in enumerate(prompts[:num_requests]):
            print(f"[{i+1}/{num_requests}] Testing: {prompt[:60]}...")

            start = time.time()
            result = self.test_endpoint(endpoint_id, prompt, max_tokens=128)
            elapsed = time.time() - start

            times.append(elapsed)
            results.append(result)

            print(f"Time: {elapsed:.1f}s\n")

        # Summary
        print(f"{'='*70}")
        print("BENCHMARK SUMMARY")
        print(f"{'='*70}")
        print(f"Total Requests: {len(times)}")
        print(f"Average Time: {sum(times)/len(times):.1f}s")
        print(f"Min Time: {min(times):.1f}s")
        print(f"Max Time: {max(times):.1f}s")

        return {
            "total_requests": len(times),
            "average_time": sum(times) / len(times),
            "min_time": min(times),
            "max_time": max(times),
            "times": times,
        }


def main():
    parser = argparse.ArgumentParser(
        description="Test RunPod Gemma-4-31B endpoint",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Test with default prompt
  python test_endpoint.py --endpoint-id YOUR_ENDPOINT_ID

  # Test with custom prompt
  python test_endpoint.py --endpoint-id YOUR_ENDPOINT_ID --prompt "Your prompt"

  # Run benchmark
  python test_endpoint.py --endpoint-id YOUR_ENDPOINT_ID --benchmark 5

  # Custom generation params
  python test_endpoint.py --endpoint-id YOUR_ENDPOINT_ID \\
    --prompt "Hello" --max-tokens 512 --temperature 0.8
        """
    )

    parser.add_argument(
        '--endpoint-id',
        type=str,
        required=True,
        help='RunPod endpoint ID'
    )
    parser.add_argument(
        '--prompt',
        type=str,
        default='What is artificial intelligence? Explain it in 2-3 sentences.',
        help='Prompt to test (default: AI explanation)'
    )
    parser.add_argument(
        '--max-tokens',
        type=int,
        default=256,
        help='Maximum tokens to generate (default: 256)'
    )
    parser.add_argument(
        '--temperature',
        type=float,
        default=0.7,
        help='Sampling temperature (default: 0.7)'
    )
    parser.add_argument(
        '--top-p',
        type=float,
        default=0.9,
        help='Top-p (nucleus) sampling (default: 0.9)'
    )
    parser.add_argument(
        '--top-k',
        type=int,
        default=50,
        help='Top-k sampling (default: 50)'
    )
    parser.add_argument(
        '--benchmark',
        type=int,
        nargs='?',
        const=5,
        help='Run benchmark with N requests (default: 5)'
    )
    parser.add_argument(
        '--timeout',
        type=int,
        default=300,
        help='Request timeout in seconds (default: 300)'
    )

    args = parser.parse_args()

    api_key = os.getenv('RUNPOD_API_KEY')
    if not api_key:
        print("ERROR: RUNPOD_API_KEY environment variable not set")
        sys.exit(1)

    tester = RunPodTester(api_key)

    if args.benchmark:
        # Run benchmark
        tester.run_benchmark(args.endpoint_id, args.benchmark)
    else:
        # Single test
        tester.test_endpoint(
            args.endpoint_id,
            args.prompt,
            max_tokens=args.max_tokens,
            temperature=args.temperature,
            top_p=args.top_p,
            top_k=args.top_k,
            timeout=args.timeout,
        )


if __name__ == "__main__":
    main()
