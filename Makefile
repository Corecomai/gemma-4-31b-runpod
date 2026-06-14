.PHONY: help install configs generate build push test clean setup

# Default target
help:
	@echo "Gemma-4-31B RunPod Deployment Helper"
	@echo "====================================="
	@echo ""
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@echo "  make setup              - Install dependencies and setup"
	@echo "  make configs            - List all available configurations"
	@echo "  make generate           - Generate deployment files (requires CONFIG=name)"
	@echo "  make build              - Build Docker image (requires CONFIG=name)"
	@echo "  make push               - Push Docker image to registry (requires DOCKER_USERNAME)"
	@echo "  make test               - Test deployed endpoint (requires ENDPOINT_ID)"
	@echo "  make benchmark          - Run benchmark (requires ENDPOINT_ID)"
	@echo "  make clean              - Clean generated files"
	@echo ""
	@echo "Examples:"
	@echo "  make setup"
	@echo "  make configs"
	@echo "  make generate CONFIG=a100_80gb_int4"
	@echo "  make build CONFIG=a100_80gb_int4 DOCKER_USERNAME=myusername"
	@echo "  make test ENDPOINT_ID=abc123xyz"
	@echo ""

# Setup
setup:
	@echo "Setting up environment..."
	pip install -r requirements.txt
	pip install pyyaml requests python-dotenv
	@echo "✓ Setup complete"
	@echo ""
	@echo "Next steps:"
	@echo "  1. Edit .env with your RUNPOD_API_KEY and HF_TOKEN"
	@echo "  2. Run: make configs"
	@echo "  3. Run: make generate CONFIG=a100_80gb_int4"

# List configurations
configs:
	@python deploy_to_runpod.py --list-configs

# Generate deployment files
generate:
	@if [ -z "$(CONFIG)" ]; then \
		echo "ERROR: CONFIG not specified"; \
		echo "Usage: make generate CONFIG=a100_80gb_int4"; \
		echo ""; \
		make configs; \
		exit 1; \
	fi
	@python deploy_to_runpod.py \
		--config $(CONFIG) \
		--output-dir ./deployment_$(CONFIG)
	@echo ""
	@echo "✓ Generated files in: ./deployment_$(CONFIG)/"
	@echo ""
	@echo "Next steps:"
	@echo "  1. cd deployment_$(CONFIG)"
	@echo "  2. docker build -t gemma4-runpod:latest ."
	@echo "  3. docker tag gemma4-runpod:latest DOCKER_USERNAME/gemma4-runpod:latest"
	@echo "  4. docker push DOCKER_USERNAME/gemma4-runpod:latest"

# Build Docker image
build:
	@if [ -z "$(CONFIG)" ]; then \
		echo "ERROR: CONFIG not specified"; \
		echo "Usage: make build CONFIG=a100_80gb_int4"; \
		exit 1; \
	fi
	@if [ ! -d "deployment_$(CONFIG)" ]; then \
		echo "ERROR: deployment_$(CONFIG) not found"; \
		echo "Run: make generate CONFIG=$(CONFIG)"; \
		exit 1; \
	fi
	@echo "Building Docker image..."
	cd deployment_$(CONFIG) && docker build -t gemma4-runpod:latest .
	@echo "✓ Build complete: gemma4-runpod:latest"

# Push Docker image
push:
	@if [ -z "$(CONFIG)" ]; then \
		echo "ERROR: CONFIG not specified"; \
		echo "Usage: make push CONFIG=a100_80gb_int4 DOCKER_USERNAME=myusername"; \
		exit 1; \
	fi
	@if [ -z "$(DOCKER_USERNAME)" ]; then \
		echo "ERROR: DOCKER_USERNAME not specified"; \
		echo "Usage: make push CONFIG=a100_80gb_int4 DOCKER_USERNAME=myusername"; \
		exit 1; \
	fi
	@echo "Pushing Docker image to $(DOCKER_USERNAME)..."
	docker tag gemma4-runpod:latest $(DOCKER_USERNAME)/gemma4-runpod:latest
	docker push $(DOCKER_USERNAME)/gemma4-runpod:latest
	@echo "✓ Pushed: $(DOCKER_USERNAME)/gemma4-runpod:latest"
	@echo ""
	@echo "Next steps:"
	@echo "  1. Go to: https://www.runpod.io/console/serverless"
	@echo "  2. Create new template with image: $(DOCKER_USERNAME)/gemma4-runpod:latest"
	@echo "  3. Deploy endpoint"
	@echo "  4. Run: make test ENDPOINT_ID=YOUR_ENDPOINT_ID"

# Test endpoint
test:
	@if [ -z "$(ENDPOINT_ID)" ]; then \
		echo "ERROR: ENDPOINT_ID not specified"; \
		echo "Usage: make test ENDPOINT_ID=abc123xyz"; \
		exit 1; \
	fi
	@python test_endpoint.py --endpoint-id $(ENDPOINT_ID)

# Benchmark endpoint
benchmark:
	@if [ -z "$(ENDPOINT_ID)" ]; then \
		echo "ERROR: ENDPOINT_ID not specified"; \
		echo "Usage: make benchmark ENDPOINT_ID=abc123xyz"; \
		exit 1; \
	fi
	@if [ -z "$(REQUESTS)" ]; then \
		python test_endpoint.py --endpoint-id $(ENDPOINT_ID) --benchmark 5; \
	else \
		python test_endpoint.py --endpoint-id $(ENDPOINT_ID) --benchmark $(REQUESTS); \
	fi

# Full deployment workflow
deploy: setup generate build push
	@echo ""
	@echo "✓ Deployment files prepared!"
	@echo ""
	@echo "Next steps:"
	@echo "  1. Go to: https://www.runpod.io/console/serverless"
	@echo "  2. Create template with: YOUR_DOCKER_USERNAME/gemma4-runpod:latest"
	@echo "  3. Deploy endpoint"
	@echo "  4. Run: make test ENDPOINT_ID=YOUR_ENDPOINT_ID"

# Clean up generated files
clean:
	@echo "Cleaning up generated files..."
	@rm -rf deployment_*
	@rm -rf *.pyc __pycache__
	@echo "✓ Clean complete"

# Show current status
status:
	@echo "Gemma-4-31B RunPod Deployment Status"
	@echo "====================================="
	@echo ""
	@if [ -f ".env" ]; then \
		echo "✓ .env file exists"; \
		if grep -q "RUNPOD_API_KEY" .env; then \
			echo "✓ RUNPOD_API_KEY is set"; \
		else \
			echo "✗ RUNPOD_API_KEY is NOT set"; \
		fi; \
		if grep -q "HF_TOKEN" .env; then \
			echo "✓ HF_TOKEN is set"; \
		else \
			echo "✗ HF_TOKEN is NOT set"; \
		fi; \
	else \
		echo "✗ .env file not found"; \
	fi
	@echo ""
	@if command -v docker &> /dev/null; then \
		echo "✓ Docker is installed"; \
	else \
		echo "✗ Docker is NOT installed"; \
	fi
	@echo ""
	@if [ -d "deployment_a100_80gb_int4" ]; then \
		echo "✓ Deployment files generated (a100_80gb_int4)"; \
	else \
		echo "  Deployment files not yet generated"; \
	fi

# Quick start guide
quickstart:
	@echo "Gemma-4-31B on RunPod - Quick Start"
	@echo "===================================="
	@echo ""
	@echo "Step 1: Setup"
	@echo "  $$ make setup"
	@echo ""
	@echo "Step 2: List configurations"
	@echo "  $$ make configs"
	@echo ""
	@echo "Step 3: Generate deployment files"
	@echo "  $$ make generate CONFIG=a100_80gb_int4"
	@echo ""
	@echo "Step 4: Build Docker image"
	@echo "  $$ cd deployment_a100_80gb_int4"
	@echo "  $$ docker build -t gemma4-runpod:latest ."
	@echo ""
	@echo "Step 5: Tag and push to registry"
	@echo "  $$ docker tag gemma4-runpod:latest YOUR_USERNAME/gemma4-runpod:latest"
	@echo "  $$ docker push YOUR_USERNAME/gemma4-runpod:latest"
	@echo ""
	@echo "Step 6: Deploy on RunPod"
	@echo "  1. Go to: https://www.runpod.io/console/serverless"
	@echo "  2. Create template with: YOUR_USERNAME/gemma4-runpod:latest"
	@echo "  3. Deploy endpoint"
	@echo ""
	@echo "Step 7: Test the endpoint"
	@echo "  $$ make test ENDPOINT_ID=YOUR_ENDPOINT_ID"
	@echo ""
	@echo "For more info, see QUICKSTART.md"
