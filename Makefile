-include .env

DOCKER_USER ?= yang517
IMAGE_NAME   = yoto-downloader
TAG          ?= latest

# NAS deployment — set these in .env (never committed to git)
NAS_USER        ?= admin
NAS_IP          ?= 192.168.1.1
NAS_DIR         ?= /volume1/docker/yoto_downloader
NAS_COMPOSE_CMD ?= sudo /usr/local/bin/docker-compose

.PHONY: dev dev-down dev-logs test smoke build push deploy help

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

# ---------------------------------------------------------------------------
# NAS deployment
# ---------------------------------------------------------------------------

deploy: ## Pull latest image and restart on NAS (set NAS_USER/NAS_IP/NAS_DIR in .env)
	ssh $(NAS_USER)@$(NAS_IP) "cd $(NAS_DIR) && $(NAS_COMPOSE_CMD) pull && $(NAS_COMPOSE_CMD) up -d"

