#!/usr/bin/env python3
"""
Simple Flask API wrapper for RunPod Gemma-4-31B endpoint
Allows your website to call the endpoint securely

Usage:
    python api_server.py

Then call:
    curl -X POST http://localhost:5000/api/generate \
      -H "Content-Type: application/json" \
      -d '{"prompt": "What is AI?"}'
"""

import os
import json
import time
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)  # Enable CORS for website calls

# Configuration
RUNPOD_API_KEY = os.getenv("RUNPOD_API_KEY")
RUNPOD_ENDPOINT_ID = os.getenv("RUNPOD_ENDPOINT_ID", "oodajsphk20uyr")
RUNPOD_BASE_URL = f"https://api.runpod.io/v2/{RUNPOD_ENDPOINT_ID}"

if not RUNPOD_API_KEY:
    print("❌ ERROR: RUNPOD_API_KEY not set in .env")
    exit(1)

HEADERS = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {RUNPOD_API_KEY}"
}


@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint"""
    return jsonify({"status": "ok", "endpoint": RUNPOD_ENDPOINT_ID})


@app.route("/api/generate", methods=["POST"])
def generate():
    """
    Generate text using Gemma-4-31B

    Request body:
    {
        "prompt": "Your prompt here",
        "max_tokens": 256,
        "temperature": 0.7,
        "sync": true
    }
    """
    try:
        data = request.json

        if not data or "prompt" not in data:
            return jsonify({"error": "Missing 'prompt' in request"}), 400

        prompt = data["prompt"]
        max_tokens = data.get("max_tokens", 256)
        temperature = data.get("temperature", 0.7)
        top_p = data.get("top_p", 0.9)
        top_k = data.get("top_k", 50)
        sync = data.get("sync", True)

        # Validate inputs
        if not isinstance(prompt, str) or len(prompt) == 0:
            return jsonify({"error": "Prompt must be non-empty string"}), 400

        if not (0 <= temperature <= 2.0):
            return jsonify({"error": "Temperature must be between 0 and 2"}), 400

        # Prepare payload
        payload = {
            "input": {
                "prompt": prompt,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "top_p": top_p,
                "top_k": top_k
            }
        }

        # Choose sync or async
        endpoint = f"{RUNPOD_BASE_URL}/runsync" if sync else f"{RUNPOD_BASE_URL}/run"

        # Call RunPod
        response = requests.post(
            endpoint,
            headers=HEADERS,
            json=payload,
            timeout=600  # 10 minute timeout
        )

        if response.status_code != 200:
            return jsonify({
                "error": f"RunPod API error: {response.status_code}",
                "details": response.text
            }), response.status_code

        result = response.json()

        # If async, return job ID
        if not sync:
            return jsonify({
                "status": "submitted",
                "job_id": result["id"],
                "check_url": f"/api/status/{result['id']}"
            })

        # If sync, return result
        return jsonify({
            "status": "completed",
            "prompt": prompt,
            "output": result.get("output", {}),
            "usage": result.get("usage", {})
        })

    except requests.exceptions.Timeout:
        return jsonify({"error": "Request timeout - model may still be loading"}), 504
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Request error: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"error": f"Internal error: {str(e)}"}), 500


@app.route("/api/status/<job_id>", methods=["GET"])
def get_status(job_id):
    """
    Check status of async job
    """
    try:
        response = requests.get(
            f"{RUNPOD_BASE_URL}/status/{job_id}",
            headers=HEADERS,
            timeout=30
        )

        if response.status_code != 200:
            return jsonify({
                "error": f"RunPod API error: {response.status_code}"
            }), response.status_code

        result = response.json()

        return jsonify({
            "job_id": job_id,
            "status": result.get("status"),
            "output": result.get("output"),
            "error": result.get("error")
        })

    except Exception as e:
        return jsonify({"error": f"Status check error: {str(e)}"}), 500


@app.route("/api/batch", methods=["POST"])
def batch_generate():
    """
    Generate multiple prompts at once

    Request body:
    {
        "prompts": [
            "First prompt",
            "Second prompt"
        ],
        "max_tokens": 256
    }
    """
    try:
        data = request.json

        if not data or "prompts" not in data:
            return jsonify({"error": "Missing 'prompts' in request"}), 400

        prompts = data["prompts"]
        max_tokens = data.get("max_tokens", 256)
        temperature = data.get("temperature", 0.7)

        if not isinstance(prompts, list) or len(prompts) == 0:
            return jsonify({"error": "Prompts must be non-empty list"}), 400

        # Submit all jobs
        jobs = []
        for prompt in prompts:
            payload = {
                "input": {
                    "prompt": prompt,
                    "max_tokens": max_tokens,
                    "temperature": temperature
                }
            }

            response = requests.post(
                f"{RUNPOD_BASE_URL}/run",
                headers=HEADERS,
                json=payload,
                timeout=30
            )

            if response.status_code == 200:
                job = response.json()
                jobs.append({
                    "prompt": prompt,
                    "job_id": job["id"],
                    "status": job["status"]
                })

        return jsonify({
            "status": "submitted",
            "job_count": len(jobs),
            "jobs": jobs
        })

    except Exception as e:
        return jsonify({"error": f"Batch error: {str(e)}"}), 500


@app.route("/api/docs", methods=["GET"])
def docs():
    """API documentation"""
    return jsonify({
        "title": "Gemma-4-31B RunPod API",
        "description": "Web API wrapper for RunPod Gemma-4-31B endpoint",
        "endpoints": {
            "GET /health": "Health check",
            "POST /api/generate": "Generate text (sync or async)",
            "GET /api/status/<job_id>": "Check async job status",
            "POST /api/batch": "Generate multiple prompts",
            "GET /api/docs": "This documentation"
        },
        "example": {
            "prompt": "What is artificial intelligence?",
            "max_tokens": 256,
            "temperature": 0.7
        }
    })


if __name__ == "__main__":
    print("\n" + "="*70)
    print("🚀 Gemma-4-31B RunPod API Server")
    print("="*70)
    print(f"\n📍 Endpoint ID: {RUNPOD_ENDPOINT_ID}")
    print(f"🔑 API Key: {'***' + RUNPOD_API_KEY[-10:]}")
    print("\n📚 Documentation: http://localhost:5000/api/docs")
    print("\n🧪 Test:")
    print("""
    curl -X POST http://localhost:5000/api/generate \\
      -H "Content-Type: application/json" \\
      -d '{"prompt": "What is AI?", "max_tokens": 256}'
    """)
    print("\n" + "="*70 + "\n")

    app.run(host="0.0.0.0", port=5000, debug=False)
