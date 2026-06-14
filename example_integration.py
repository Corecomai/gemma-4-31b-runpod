#!/usr/bin/env python3
"""
Example: Integrate Gemma-4-31B RunPod Endpoint into Your Application

Shows how to use the deployed endpoint from a Python application.
"""

import os
import json
import time
import asyncio
import requests
from typing import Optional, Dict, Any
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass
class GenerationConfig:
    """Configuration for text generation"""
    max_tokens: int = 256
    temperature: float = 0.7
    top_p: float = 0.9
    top_k: int = 50
    repetition_penalty: float = 1.0


class GemmaClient:
    """Client for Gemma-4-31B on RunPod"""

    def __init__(self, endpoint_id: str, timeout: int = 300):
        """
        Initialize client

        Args:
            endpoint_id: RunPod endpoint ID
            timeout: Request timeout in seconds
        """
        self.endpoint_id = endpoint_id
        self.base_url = f"https://api.runpod.io/v1/{endpoint_id}"
        self.timeout = timeout

    def generate(
        self,
        prompt: str,
        config: Optional[GenerationConfig] = None,
    ) -> str:
        """
        Generate text synchronously

        Args:
            prompt: Input prompt
            config: Generation configuration

        Returns:
            Generated text
        """
        if config is None:
            config = GenerationConfig()

        # Submit request
        job_id = self._submit_request(prompt, config)
        if not job_id:
            raise RuntimeError("Failed to submit request")

        # Poll for results
        result = self._wait_for_result(job_id)
        if result["status"] != "COMPLETED":
            raise RuntimeError(f"Request failed: {result.get('error', 'Unknown error')}")

        return result["output"]["generated_text"]

    async def generate_async(
        self,
        prompt: str,
        config: Optional[GenerationConfig] = None,
    ) -> str:
        """
        Generate text asynchronously

        Args:
            prompt: Input prompt
            config: Generation configuration

        Returns:
            Generated text
        """
        if config is None:
            config = GenerationConfig()

        # Submit request
        job_id = self._submit_request(prompt, config)
        if not job_id:
            raise RuntimeError("Failed to submit request")

        # Poll for results asynchronously
        result = await self._wait_for_result_async(job_id)
        if result["status"] != "COMPLETED":
            raise RuntimeError(f"Request failed: {result.get('error', 'Unknown error')}")

        return result["output"]["generated_text"]

    def _submit_request(self, prompt: str, config: GenerationConfig) -> Optional[str]:
        """Submit request to endpoint"""
        url = f"{self.base_url}/run"

        payload = {
            "input": {
                "prompt": prompt,
                "max_tokens": config.max_tokens,
                "temperature": config.temperature,
                "top_p": config.top_p,
                "top_k": config.top_k,
                "repetition_penalty": config.repetition_penalty,
            }
        }

        try:
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            data = response.json()
            return data.get("id")
        except Exception as e:
            print(f"Error submitting request: {e}")
            return None

    def _wait_for_result(self, job_id: str) -> Dict[str, Any]:
        """Poll for result synchronously"""
        status_url = f"{self.base_url}/status/{job_id}"
        start_time = time.time()

        while time.time() - start_time < self.timeout:
            try:
                response = requests.get(status_url, timeout=10)
                response.raise_for_status()
                data = response.json()

                if data["status"] in ["COMPLETED", "FAILED"]:
                    return data

                time.sleep(1)
            except Exception as e:
                print(f"Error polling status: {e}")
                time.sleep(1)

        return {"status": "TIMEOUT"}

    async def _wait_for_result_async(self, job_id: str) -> Dict[str, Any]:
        """Poll for result asynchronously"""
        status_url = f"{self.base_url}/status/{job_id}"
        start_time = time.time()

        while time.time() - start_time < self.timeout:
            try:
                response = requests.get(status_url, timeout=10)
                response.raise_for_status()
                data = response.json()

                if data["status"] in ["COMPLETED", "FAILED"]:
                    return data

                await asyncio.sleep(1)
            except Exception as e:
                print(f"Error polling status: {e}")
                await asyncio.sleep(1)

        return {"status": "TIMEOUT"}


# ============================================================================
# EXAMPLE USAGE
# ============================================================================


def example_basic_usage():
    """Basic usage example"""
    print("\n" + "="*70)
    print("EXAMPLE 1: Basic Usage")
    print("="*70)

    # Initialize client
    endpoint_id = os.getenv("RUNPOD_ENDPOINT_ID", "your_endpoint_id")
    client = GemmaClient(endpoint_id)

    # Generate text
    prompt = "What is artificial intelligence?"
    print(f"\nPrompt: {prompt}")
    print("Generating...")

    try:
        result = client.generate(
            prompt,
            GenerationConfig(
                max_tokens=256,
                temperature=0.7,
            )
        )
        print(f"\nResponse:\n{result}")
    except Exception as e:
        print(f"Error: {e}")


def example_custom_config():
    """Example with custom generation config"""
    print("\n" + "="*70)
    print("EXAMPLE 2: Custom Configuration")
    print("="*70)

    endpoint_id = os.getenv("RUNPOD_ENDPOINT_ID", "your_endpoint_id")
    client = GemmaClient(endpoint_id)

    # Custom generation config
    config = GenerationConfig(
        max_tokens=512,
        temperature=0.9,  # More creative
        top_p=0.95,
        top_k=100,
        repetition_penalty=1.1,
    )

    prompt = "Write a short poem about the moon."
    print(f"\nPrompt: {prompt}")
    print("Generating with custom config...")

    try:
        result = client.generate(prompt, config)
        print(f"\nResponse:\n{result}")
    except Exception as e:
        print(f"Error: {e}")


async def example_async_usage():
    """Example using async/await"""
    print("\n" + "="*70)
    print("EXAMPLE 3: Async Usage")
    print("="*70)

    endpoint_id = os.getenv("RUNPOD_ENDPOINT_ID", "your_endpoint_id")
    client = GemmaClient(endpoint_id)

    prompts = [
        "Explain quantum computing in simple terms.",
        "What are the benefits of renewable energy?",
        "How does photosynthesis work?",
    ]

    print(f"\nGenerating {len(prompts)} responses asynchronously...")

    try:
        # Generate all concurrently
        tasks = [
            client.generate_async(prompt, GenerationConfig(max_tokens=200))
            for prompt in prompts
        ]
        results = await asyncio.gather(*tasks)

        for prompt, result in zip(prompts, results):
            print(f"\n{'='*70}")
            print(f"Q: {prompt}")
            print(f"A: {result[:200]}...")
    except Exception as e:
        print(f"Error: {e}")


def example_batch_processing():
    """Example processing batch of inputs"""
    print("\n" + "="*70)
    print("EXAMPLE 4: Batch Processing")
    print("="*70)

    endpoint_id = os.getenv("RUNPOD_ENDPOINT_ID", "your_endpoint_id")
    client = GemmaClient(endpoint_id)

    questions = [
        "What is machine learning?",
        "Explain deep learning.",
        "What is neural networks?",
    ]

    results = []
    for i, question in enumerate(questions, 1):
        print(f"\n[{i}/{len(questions)}] {question}")
        try:
            result = client.generate(
                question,
                GenerationConfig(max_tokens=150)
            )
            results.append({
                "question": question,
                "answer": result,
            })
            print(f"✓ Success")
        except Exception as e:
            print(f"✗ Error: {e}")

    # Save results
    with open("results.json", "w") as f:
        json.dump(results, f, indent=2)
    print(f"\n✓ Saved {len(results)} results to results.json")


def example_error_handling():
    """Example with proper error handling"""
    print("\n" + "="*70)
    print("EXAMPLE 5: Error Handling")
    print("="*70)

    endpoint_id = os.getenv("RUNPOD_ENDPOINT_ID")
    if not endpoint_id:
        print("ERROR: RUNPOD_ENDPOINT_ID not set")
        print("Set it with: export RUNPOD_ENDPOINT_ID=your_endpoint_id")
        return

    client = GemmaClient(endpoint_id, timeout=60)

    prompts = [
        "What is AI?",
        "",  # Empty prompt (will error)
        "Tell me a story.",
    ]

    for prompt in prompts:
        if not prompt:
            print(f"\nSkipping empty prompt")
            continue

        try:
            print(f"\nGenerating: {prompt[:50]}...")
            result = client.generate(
                prompt,
                GenerationConfig(max_tokens=100)
            )
            print(f"✓ Success: {result[:100]}...")
        except RuntimeError as e:
            print(f"✗ Request failed: {e}")
        except Exception as e:
            print(f"✗ Unexpected error: {e}")


def example_streaming_simulation():
    """Example showing how to add streaming-like response"""
    print("\n" + "="*70)
    print("EXAMPLE 6: Streaming Simulation")
    print("="*70)

    endpoint_id = os.getenv("RUNPOD_ENDPOINT_ID", "your_endpoint_id")
    client = GemmaClient(endpoint_id)

    prompt = "Write a haiku about programming."
    print(f"\nPrompt: {prompt}")
    print("Generating")

    try:
        result = client.generate(prompt, GenerationConfig(max_tokens=100))

        # Simulate streaming by printing character by character
        print("\nStreaming response:")
        for char in result:
            print(char, end="", flush=True)
            time.sleep(0.02)  # Simulate network latency
        print()
    except Exception as e:
        print(f"Error: {e}")


# ============================================================================
# MAIN
# ============================================================================


def main():
    """Run examples"""
    print("\n" + "="*70)
    print("Gemma-4-31B RunPod Integration Examples")
    print("="*70)

    # Check if endpoint ID is set
    endpoint_id = os.getenv("RUNPOD_ENDPOINT_ID")
    if not endpoint_id:
        print("\n⚠️  RUNPOD_ENDPOINT_ID not set!")
        print("\nTo run these examples:")
        print("  1. Deploy Gemma-4-31B on RunPod")
        print("  2. Get your endpoint ID from RunPod console")
        print("  3. Set environment variable:")
        print("     export RUNPOD_ENDPOINT_ID=your_endpoint_id")
        print("\n  Then run: python example_integration.py")
        return

    # Run examples (uncomment to run)
    example_basic_usage()
    # example_custom_config()
    # example_batch_processing()
    # example_error_handling()
    # example_streaming_simulation()

    # For async example
    # asyncio.run(example_async_usage())


if __name__ == "__main__":
    main()
