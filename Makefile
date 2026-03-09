DOCKER_USER ?= yang517
IMAGE_NAME   = yoto-downloader
TAG          ?= latest

.PHONY: dev dev-down dev-logs test smoke build push help

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'

# ---------------------------------------------------------------------------
# Local dev
# ---------------------------------------------------------------------------

dev: ## Build and start the local dev stack (hot-reload enabled)
	docker compose -f docker-compose.dev.yml up --build -d
	@echo ""
	@echo "  App:  http://localhost:8000"
	@echo "  Docs: http://localhost:8000/docs"
	@echo ""
	@echo "Run 'make dev-logs' to tail logs, 'make smoke' to verify."

dev-down: ## Stop and remove the local dev stack
	docker compose -f docker-compose.dev.yml down

dev-logs: ## Tail logs from the local dev stack
	docker compose -f docker-compose.dev.yml logs -f

# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

test: ## Run unit tests (no Docker required)
	pytest tests/ -m "not smoke" -v

smoke: ## Run smoke tests against the local dev stack (requires 'make dev' first)
	BASE_URL=http://localhost:8000 pytest tests/smoke_test.py -v

# ---------------------------------------------------------------------------
# Build & publish
# ---------------------------------------------------------------------------

build: ## Build the Docker image
	docker build -t $(DOCKER_USER)/$(IMAGE_NAME):$(TAG) ./app

push: build ## Build and push the Docker image to Docker Hub
	docker push $(DOCKER_USER)/$(IMAGE_NAME):$(TAG)
