# Makefile for ML CI/CD Pipeline with MLflow

.PHONY: help setup-mlflow start-mlflow stop-mlflow train-model compare-models promote-model docker-build docker-train docker-serve docker-compose-up docker-compose-down clean dev train serve monitoring infra-init infra-plan infra-apply infra-destroy infra-output docs-build docs-serve docs-deploy

# Default target
help:
	@echo "🚀 ML CI/CD Pipeline - Available Targets"
	@echo ""
	@echo "📦 Docker Compose Orchestration:"
	@echo "  dev              - Start development environment (MLflow + monitoring)"
	@echo "  dev-postgres     - Start dev environment with PostgreSQL backend"
	@echo "  dev-full         - Start full environment with all services"
	@echo "  train            - Run training pipeline in containers"
	@echo "  serve            - Start model serving with nginx proxy"
	@echo "  monitoring       - Start monitoring stack (Prometheus + Grafana)"
	@echo "  down             - Stop all Docker Compose services"
	@echo ""
	@echo "🐳 Docker Build & Run:"
	@echo "  docker-build     - Build Docker images with Git SHA tags"
	@echo "  docker-train     - Run training in Docker container"
	@echo "  docker-serve     - Run serving in Docker container"
	@echo ""
	@echo "🧪 MLflow & Training:"
	@echo "  setup-mlflow     - Setup MLflow directories and configuration"
	@echo "  start-mlflow     - Start MLflow tracking server"
	@echo "  train-model      - Run model training with MLflow tracking"
	@echo "  compare-models   - Compare model runs and versions"
	@echo "  promote-model    - Promote best model to staging"
	@echo "  serve-model      - Start model serving"
	@echo ""
	@echo "🔧 Development:"
	@echo "  install          - Install dependencies"
	@echo "  test             - Run tests"
	@echo "  lint             - Run linting and type checks"
	@echo "  format           - Format code"
	@echo "  clean            - Clean up artifacts and logs"
	@echo ""
	@echo "☁️  Infrastructure (Terraform):"
	@echo "  infra-init       - Initialize Terraform backend"
	@echo "  infra-plan       - Plan infrastructure changes"
	@echo "  infra-apply      - Apply infrastructure changes"
	@echo "  infra-destroy    - Destroy infrastructure"
	@echo "  infra-output     - Show infrastructure outputs"
	@echo ""
	@echo "📚 Documentation:"
	@echo "  docs-build       - Build documentation with MkDocs"
	@echo "  docs-serve       - Serve documentation locally"
	@echo "  docs-deploy      - Deploy documentation to GitHub Pages"
	@echo ""
	@echo "💡 Quick Start: make dev"

# MLflow setup and management
setup-mlflow:
	@echo "Setting up MLflow directories and configuration..."
	python mlflow_server.py --setup-only
	@echo "MLflow setup complete!"
	@echo "To start the server, run: make start-mlflow"

start-mlflow:
	@echo "Starting MLflow tracking server..."
	@echo "Server will be available at http://localhost:5000"
	@echo "Use Ctrl+C to stop the server"
	python mlflow_server.py

stop-mlflow:
	@echo "Stopping MLflow server..."
	pkill -f "mlflow server" || echo "No MLflow server process found"

# Training and model management
train-model:
	@echo "Running model training with MLflow tracking..."
	@export MLFLOW_TRACKING_URI=http://localhost:5000 && \
	python src/training/train.py --config src/training/config.yaml

train-quick:
	@echo "Running quick training for testing..."
	@export MLFLOW_TRACKING_URI=http://localhost:5000 && \
	python src/training/train.py \
		--config src/training/config.yaml \
		--overrides \
			training.num_train_epochs=1 \
			training.per_device_train_batch_size=2 \
			training.eval_steps=10 \
			training.save_steps=20 \
			mlflow.experiment_name=quick_test

compare-models:
	@echo "Comparing model runs..."
	@export MLFLOW_TRACKING_URI=http://localhost:5000 && \
	python scripts/compare_and_promote_models.py \
		--experiment-name code_model_fine_tuning \
		--action compare \
		--top-k 5

promote-model:
	@echo "Auto-promoting best model to staging..."
	@export MLFLOW_TRACKING_URI=http://localhost:5000 && \
	python scripts/compare_and_promote_models.py \
		--experiment-name code_model_fine_tuning \
		--model-name code_model_fine_tuning_model \
		--action auto-promote \
		--stage Staging

serve-model:
	@echo "Starting model serving..."
	@export MLFLOW_TRACKING_URI=http://localhost:5000 && \
	mlflow models serve \
		--model-uri models:/code_model_fine_tuning_model/Staging \
		--host 0.0.0.0 \
		--port 8080 \
		--no-conda

# Development tasks
install:
	@echo "Installing dependencies..."
	pip install -r requirements.txt

# Quality Gates
lint:
	@echo "Running linting checks..."
	@echo "1. Ruff linting..."
	ruff check src tests
	@echo "2. MyPy type checking..."
	mypy src --config-file mypy.ini || true
	@echo "✅ Linting complete"

format:
	@echo "Formatting code..."
	@echo "1. Ruff formatting..."
	ruff format src tests
	@echo "2. Black formatting..."
	black src tests
	@echo "3. isort import sorting..."
	isort src tests
	@echo "✅ Code formatting complete"

format-check:
	@echo "Checking code formatting..."
	@echo "1. Ruff format check..."
	ruff format src tests --check
	@echo "2. Black format check..."
	black --check src tests
	@echo "3. isort check..."
	isort --check-only src tests
	@echo "✅ Format check complete"

security:
	@echo "Running security scans..."
	@echo "1. Bandit security scan..."
	bandit -r src -f txt
	bandit -r src -f json -o bandit-report.json || true
	@echo "✅ Security scan complete"

# Testing with Coverage
test:
	@echo "Running unit tests..."
	pytest tests/ -v -m "not integration and not docker"

test-unit:
	@echo "Running unit tests with coverage (≥80% required)..."
	pytest tests/ -v \
		--cov=src \
		--cov-report=term-missing \
		--cov-report=html:htmlcov \
		--cov-report=xml:coverage.xml \
		--cov-fail-under=80 \
		-m "not integration and not docker"

test-integration:
	@echo "Running integration tests..."
	pytest tests/test_integration.py -v -m "integration and not docker"

test-docker:
	@echo "Running Docker integration tests..."
	pytest tests/test_integration.py -v -m "docker"

coverage:
	@echo "Generating coverage report..."
	pytest tests/ \
		--cov=src \
		--cov-report=term-missing \
		--cov-report=html:htmlcov \
		--cov-report=xml:coverage.xml \
		-m "not integration and not docker"
	@echo "Coverage report generated in htmlcov/index.html"

# Combined quality checks
all-checks: format-check lint security test-unit
	@echo "🎉 All quality gates passed!"

ci-local: clean format-check lint security test-unit test-integration
	@echo "🚀 Local CI simulation complete!"

# Docker Containerization with Multi-stage builds
docker-build:
	@echo "Building Docker images with Git SHA and model version tags..."
	./scripts/build_docker.sh

docker-build-custom:
	@echo "Building Docker images with custom parameters..."
	@echo "Usage: make docker-build-custom REGISTRY=my-registry PROJECT=my-project VERSION=v1.0.0"
	./scripts/build_docker.sh $(REGISTRY) $(PROJECT) $(VERSION)

docker-train:
	@echo "Running training in Docker container..."
	@GIT_SHA=$$(git rev-parse --short HEAD 2>/dev/null || echo "unknown") && \
	docker run --rm --name ml-train \
		-e MLFLOW_TRACKING_URI=http://host.docker.internal:5000 \
		-e EXPERIMENT_NAME=docker_training \
		-e MODEL_NAME=docker_model \
		-v $$(pwd)/data:/home/app/data:ro \
		-v $$(pwd)/config:/home/app/config:ro \
		localhost/ml-pipeline/train:$$GIT_SHA-latest

docker-serve:
	@echo "Running serving in Docker container..."
	@GIT_SHA=$$(git rev-parse --short HEAD 2>/dev/null || echo "unknown") && \
	docker run --rm --name ml-serve \
		-p 8000:8000 \
		-e MODEL_URI=models:/code_model_fine_tuning_model/latest \
		-e MLFLOW_TRACKING_URI=http://host.docker.internal:5000 \
		localhost/ml-pipeline/serve:$$GIT_SHA-latest

# Docker Compose Orchestration Targets
dev:
	@echo "🚀 Starting development environment with MLflow + Prometheus + Grafana..."
	@echo "Building Docker images first..."
	@make docker-build
	@echo "Starting development services..."
	docker-compose --env-file .env -f docker-compose.yaml --profile dev up -d
	@echo "✅ Development environment ready!"
	@echo "🔗 MLflow UI: http://localhost:5000"
	@echo "📊 Prometheus: http://localhost:9090"
	@echo "📈 Grafana: http://localhost:3000 (admin/admin)"

dev-postgres:
	@echo "🚀 Starting development environment with PostgreSQL backend..."
	@make docker-build
	@echo "Setting up PostgreSQL backend..."
	USE_POSTGRES=true docker-compose --env-file .env -f docker-compose.yaml --profile dev --profile postgres up -d
	@echo "✅ Development environment with PostgreSQL ready!"
	@echo "🔗 MLflow UI: http://localhost:5000"
	@echo "🗄️  PostgreSQL: localhost:5432"

dev-full:
	@echo "🚀 Starting full development environment with all services..."
	@make docker-build
	docker-compose --env-file .env -f docker-compose.yaml --profile full up -d
	@echo "✅ Full development environment ready!"

train:
	@echo "🎯 Running training pipeline with Docker Compose..."
	@make docker-build
	@echo "Starting MLflow server..."
	docker-compose --env-file .env -f docker-compose.yaml --profile dev up -d mlflow
	@echo "Running training container..."
	docker-compose --env-file .env -f docker-compose.yaml --profile train up train
	@echo "✅ Training completed!"

serve:
	@echo "🌐 Starting model serving with Docker Compose..."
	@make docker-build
	@echo "Starting backend services..."
	docker-compose --env-file .env -f docker-compose.yaml --profile serve up -d
	@echo "✅ Serving environment ready!"
	@echo "🔗 MLflow UI: http://localhost:80 (via nginx)"
	@echo "🚀 Model API: http://localhost:8080 (via nginx)"
	@echo "📈 Health Check: http://localhost/health"

monitoring:
	@echo "📊 Starting monitoring stack (Prometheus + Grafana)..."
	docker-compose --env-file .env -f docker-compose.yaml --profile monitoring up -d
	@echo "✅ Monitoring stack ready!"
	@echo "📊 Prometheus: http://localhost:9090"
	@echo "📈 Grafana: http://localhost:3000 (admin/admin)"

# Convenience targets
down:
	@echo "🛑 Stopping all Docker Compose services..."
	docker-compose -f docker-compose.yaml down --remove-orphans
	@echo "✅ All services stopped!"

down-volumes:
	@echo "🛑 Stopping all services and removing volumes..."
	docker-compose -f docker-compose.yaml down --volumes --remove-orphans
	@echo "⚠️  All services stopped and volumes removed!"

status:
	@echo "📊 Docker Compose Services Status:"
	docker-compose -f docker-compose.yaml ps

logs:
	@echo "📜 Showing logs from all services..."
	docker-compose -f docker-compose.yaml logs -f

logs-mlflow:
	@echo "📜 Showing MLflow logs..."
	docker-compose -f docker-compose.yaml logs -f mlflow

logs-serve:
	@echo "📜 Showing serving logs..."
	docker-compose -f docker-compose.yaml logs -f serve nginx

docker-examples:
	@echo "Running Docker usage examples..."
	./scripts/docker_examples.sh

# Cleanup
clean:
	@echo "Cleaning up MLflow artifacts..."
	rm -rf mlflow/
	rm -rf mlruns/
	rm -rf models/fine_tuned/
	rm -rf __pycache__/
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -delete
	@echo "Cleanup complete!"

# Environment setup for different stages
setup-local:
	@echo "Setting up local development environment..."
	@make setup-mlflow
	@echo "MLFLOW_TRACKING_URI=http://localhost:5000" > .env
	@echo "Local environment setup complete!"

setup-ci:
	@echo "Setting up CI environment..."
	@export MLFLOW_TRACKING_URI=file://$(PWD)/mlflow && \
	python mlflow_server.py --setup-only
	@echo "CI environment setup complete!"

# Production deployment helpers
deploy-mlflow-prod:
	@echo "Deploying MLflow to production..."
	@echo "Make sure to configure the following environment variables:"
	@echo "  MLFLOW_TRACKING_URI=http://your-mlflow-server:5000"
	@echo "  MLFLOW_BACKEND_STORE_URI=postgresql://user:password@host:port/dbname"
	@echo "  MLFLOW_DEFAULT_ARTIFACT_ROOT=s3://your-mlflow-bucket/artifacts"
	@echo "Then run: mlflow server --host 0.0.0.0 --port 5000 --backend-store-uri \$$MLFLOW_BACKEND_STORE_URI --default-artifact-root \$$MLFLOW_DEFAULT_ARTIFACT_ROOT"

# Help for common workflows
workflow-help:
	@echo ""
	@echo "Common workflows:"
	@echo ""
	@echo "1. First-time setup:"
	@echo "   make install"
	@echo "   make setup-local"
	@echo ""
	@echo "2. Start development:"
	@echo "   make start-mlflow    # In one terminal"
	@echo "   make train-model     # In another terminal"
	@echo ""
	@echo "3. Compare and promote models:"
	@echo "   make compare-models"
	@echo "   make promote-model"
	@echo ""
	@echo "4. Serve model:"
	@echo "   make serve-model"
	@echo ""

# Infrastructure as Code with Terraform
infra-init:
	@echo "🚀 Initializing Terraform backend..."
	@echo "⚠️  Make sure to update backend.tf with your S3 bucket and DynamoDB table names"
	cd infra && terraform init
	@echo "✅ Terraform initialized!"

infra-plan:
	@echo "📋 Planning infrastructure changes..."
	cd infra && terraform plan -var-file="terraform.tfvars"

infra-apply:
	@echo "🚀 Applying infrastructure changes..."
	@echo "⚠️  This will create AWS resources that may incur costs!"
	@read -p "Are you sure you want to continue? [y/N] " confirm && \
	if [ "$$confirm" = "y" ] || [ "$$confirm" = "Y" ]; then \
		cd infra && terraform apply -var-file="terraform.tfvars"; \
	else \
		echo "❌ Infrastructure deployment cancelled"; \
	fi

infra-destroy:
	@echo "💥 Destroying infrastructure..."
	@echo "⚠️  This will permanently delete all AWS resources!"
	@read -p "Are you sure you want to destroy everything? [y/N] " confirm && \
	if [ "$$confirm" = "y" ] || [ "$$confirm" = "Y" ]; then \
		cd infra && terraform destroy -var-file="terraform.tfvars"; \
	else \
		echo "❌ Infrastructure destruction cancelled"; \
	fi

infra-output:
	@echo "📊 Infrastructure outputs:"
	cd infra && terraform output

infra-validate:
	@echo "✅ Validating Terraform configuration..."
	cd infra && terraform validate

infra-fmt:
	@echo "🎨 Formatting Terraform files..."
	cd infra && terraform fmt -recursive
infra-docs:
	@echo "📚 Generating Terraform documentation..."
	@if command -v terraform-docs > /dev/null 2>&1; then \
		terraform-docs markdown table infra > infra/README.md; \
		echo "✅ Documentation generated in infra/README.md"; \
	else \
		echo "⚠️  terraform-docs not installed. Install it with: brew install terraform-docs"; \
	fi

# Documentation with MkDocs
docs-build:
	@echo "📚 Building documentation with MkDocs..."
	@if command -v mkdocs > /dev/null 2>&1; then \
		mkdocs build; \
		echo "✅ Documentation built in site/ directory"; \
	else \
		echo "⚠️  MkDocs not installed. Install it with: pip install mkdocs-material"; \
	fi

docs-serve:
	@echo "🌐 Serving documentation locally..."
	@if command -v mkdocs > /dev/null 2>&1; then \
		echo "📖 Documentation will be available at http://localhost:8000"; \
		echo "Press Ctrl+C to stop the server"; \
		mkdocs serve; \
	else \
		echo "⚠️  MkDocs not installed. Install it with: pip install mkdocs-material"; \
	fi

docs-deploy:
	@echo "🚀 Deploying documentation to GitHub Pages..."
	@if command -v mkdocs > /dev/null 2>&1; then \
		mkdocs gh-deploy --clean; \
		echo "✅ Documentation deployed to GitHub Pages"; \
	else \
		echo "⚠️  MkDocs not installed. Install it with: pip install mkdocs-material"; \
	fi

docs-install:
	@echo "📦 Installing MkDocs and dependencies..."
	pip install mkdocs-material mkdocs-git-revision-date-localized-plugin mkdocs-minify-plugin
	@echo "✅ MkDocs installed successfully"

docs-clean:
	@echo "🧹 Cleaning documentation build artifacts..."
	rm -rf site/
	@echo "✅ Documentation artifacts cleaned"
