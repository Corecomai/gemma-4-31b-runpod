"""
RunPod Serverless Handler for Gemma-4-31B-it
Optimized for vLLM v2.22.4 with quantization support
"""

import os
import json
import logging
from typing import Dict, Any, Optional
import asyncio
from datetime import datetime

from vllm import AsyncLLMEngine
from vllm.engine.arg_utils import AsyncEngineArgs
from vllm.sampling_params import SamplingParams

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class vLLMEngine:
    """Wrapper for vLLM AsyncLLMEngine with optimized configuration"""

    def __init__(self):
        """Initialize the vLLM engine with optimal settings for Gemma-4-31B"""

        self.model = os.getenv('MODEL_NAME', 'google/gemma-4-31b-it')
        self.quantization = os.getenv('QUANTIZATION', 'None')  # None for BF16, or: awq, gptq, fp8, bitsandbytes
        self.tensor_parallel_size = int(os.getenv('TENSOR_PARALLEL_SIZE', '1'))
        self.max_model_len = int(os.getenv('MAX_MODEL_LEN', '40000'))
        self.gpu_memory_utilization = float(os.getenv('GPU_MEMORY_UTILIZATION', '0.85'))
        self.max_num_seqs = int(os.getenv('MAX_NUM_SEQS', '64'))

        logger.info(f"Engine config: {self.get_config()}")

        self.engine_args = AsyncEngineArgs(
            model=self.model,
            quantization=self.quantization if self.quantization != 'None' else None,
            dtype='auto',
            tensor_parallel_size=self.tensor_parallel_size,
            max_model_len=self.max_model_len,
            gpu_memory_utilization=self.gpu_memory_utilization,
            max_num_seqs=self.max_num_seqs,
            trust_remote_code=True,
            enforce_eager=False,
            # Optimizations
            enable_prefix_caching=True,
            enable_chunked_prefill=False,  # Gemma-4 doesn't support this well
            # Distributed settings
            pipeline_parallel_size=1,
            disable_custom_all_reduce=False,
        )

        self.llm = None
        self._initialize_engine()

    def _initialize_engine(self):
        """Initialize AsyncLLMEngine"""
        try:
            self.llm = AsyncLLMEngine.from_engine_args(self.engine_args)
            logger.info("vLLM engine initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize vLLM engine: {e}", exc_info=True)
            raise

    def get_config(self) -> Dict[str, Any]:
        """Get current engine configuration"""
        return {
            'model': self.model,
            'quantization': self.quantization,
            'tensor_parallel_size': self.tensor_parallel_size,
            'max_model_len': self.max_model_len,
            'gpu_memory_utilization': self.gpu_memory_utilization,
            'max_num_seqs': self.max_num_seqs,
        }

    async def generate(
        self,
        prompt: str,
        max_tokens: int = 1024,
        temperature: float = 0.7,
        top_p: float = 0.9,
        top_k: int = 50,
        repetition_penalty: float = 1.0,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate text using vLLM"""

        if not self.llm:
            raise RuntimeError("vLLM engine not initialized")

        # Cap max_tokens to model's max_model_len
        max_tokens = min(max_tokens, self.max_model_len - len(prompt.split()))

        sampling_params = SamplingParams(
            temperature=temperature,
            top_p=top_p,
            top_k=top_k,
            max_tokens=max_tokens,
            repetition_penalty=repetition_penalty,
        )

        try:
            # Generate with async engine
            request_id = f"{datetime.now().timestamp()}"
            outputs = await self.llm.generate(
                prompt,
                sampling_params,
                request_id=request_id
            )

            # Extract generated text
            generated_text = outputs.outputs[0].text if outputs.outputs else ""

            return {
                'status': 'success',
                'prompt': prompt,
                'generated_text': generated_text,
                'finish_reason': outputs.outputs[0].finish_reason if outputs.outputs else None,
                'usage': {
                    'prompt_tokens': len(outputs.prompt_token_ids),
                    'completion_tokens': len(outputs.outputs[0].token_ids) if outputs.outputs else 0,
                }
            }
        except Exception as e:
            logger.error(f"Generation failed: {e}", exc_info=True)
            return {
                'status': 'error',
                'error': str(e),
            }


# Global engine instance
vllm_engine = None


async def handler(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    RunPod Serverless handler function

    Input format:
    {
        "prompt": "string",
        "max_tokens": 1024,
        "temperature": 0.7,
        "top_p": 0.9,
        "top_k": 50,
        "repetition_penalty": 1.0
    }
    """
    global vllm_engine

    # Initialize engine on first request
    if vllm_engine is None:
        logger.info("Initializing vLLM engine on first request...")
        vllm_engine = vLLMEngine()

    try:
        # Extract parameters from event
        prompt = event.get('prompt')
        if not prompt:
            return {
                'status': 'error',
                'error': 'Missing "prompt" in input'
            }

        # Generation parameters
        max_tokens = event.get('max_tokens', 1024)
        temperature = event.get('temperature', 0.7)
        top_p = event.get('top_p', 0.9)
        top_k = event.get('top_k', 50)
        repetition_penalty = event.get('repetition_penalty', 1.0)

        # Generate
        result = await vllm_engine.generate(
            prompt=prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
            top_k=top_k,
            repetition_penalty=repetition_penalty,
        )

        return result

    except Exception as e:
        logger.error(f"Handler error: {e}", exc_info=True)
        return {
            'status': 'error',
            'error': str(e),
        }


# For local testing
if __name__ == "__main__":
    async def test():
        result = await handler({
            "prompt": "What is artificial intelligence?",
            "max_tokens": 256,
            "temperature": 0.7,
        })
        print(json.dumps(result, indent=2))

    asyncio.run(test())
