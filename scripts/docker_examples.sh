#!/bin/bash
# Example usage of the Docker containerization system

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_header() {
    echo -e "${YELLOW}========================================${NC}"
    echo -e "${YELLOW}$1${NC}"
    echo -e "${YELLOW}========================================${NC}"
}

print_header "Docker Containerization Examples"

# Example 1: Build images with default settings
print_header "Example 1: Default Build"
print_info "Building with default registry (localhost), project (ml-pipeline), and model version (latest)"
./scripts/build_docker.sh
echo ""

# Example 2: Build with custom registry and project
print_header "Example 2: Custom Registry Build"
print_info "Building with custom registry and project name"
./scripts/build_docker.sh "my-registry.com" "my-ml-project" "v1.0.0"
echo ""

# Example 3: Docker Compose usage
print_header "Example 3: Docker Compose Usage"

print_info "Starting MLflow server..."
echo "docker-compose -f docker/docker-compose.yml up -d mlflow-server"

print_info "Running training (with built images):"
echo "export TRAIN_IMAGE=localhost/ml-pipeline/train:$(git rev-parse --short HEAD)-latest"
echo "docker-compose -f docker/docker-compose.yml --profile train up train"

print_info "Running serving (with built images):"
echo "export SERVE_IMAGE=localhost/ml-pipeline/serve:$(git rev-parse --short HEAD)-latest"
echo "docker-compose -f docker/docker-compose.yml --profile serve up -d serve"

print_info "Running development serving (without MLflow):"
echo "docker-compose -f docker/docker-compose.yml --profile dev up -d serve-dev"
echo ""

# Example 4: Direct Docker usage
print_header "Example 4: Direct Docker Usage"

GIT_SHA=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")
MODEL_VERSION="v1.2.3"
REGISTRY="localhost"
PROJECT="ml-pipeline"

TRAIN_IMAGE="$REGISTRY/$PROJECT/train:$GIT_SHA-$MODEL_VERSION"
SERVE_IMAGE="$REGISTRY/$PROJECT/serve:$GIT_SHA-$MODEL_VERSION"

print_info "Running training container directly:"
echo "docker run --rm --name ml-train \\"
echo "  -e MLFLOW_TRACKING_URI=http://host.docker.internal:5000 \\"
echo "  -e EXPERIMENT_NAME=my_experiment \\"
echo "  -e MODEL_NAME=my_model \\"
echo "  -v \$(pwd)/data:/home/app/data:ro \\"
echo "  -v \$(pwd)/config:/home/app/config:ro \\"
echo "  $TRAIN_IMAGE"

print_info "Running serving container directly:"
echo "docker run --rm --name ml-serve \\"
echo "  -p 8000:8000 \\"
echo "  -e MODEL_URI=models:/my_model/latest \\"
echo "  -e MLFLOW_TRACKING_URI=http://host.docker.internal:5000 \\"
echo "  $SERVE_IMAGE"
echo ""

# Example 5: Production deployment patterns
print_header "Example 5: Production Deployment Patterns"

print_info "Production registry example:"
echo "# Build for production registry"
echo "./scripts/build_docker.sh \"prod-registry.company.com\" \"ml-platform\" \"v2.1.0\""
echo ""

print_info "CI/CD pipeline usage:"
echo "# In CI/CD pipeline:"
echo "GIT_SHA=\$(git rev-parse --short HEAD)"
echo "MODEL_VERSION=\${CI_COMMIT_TAG:-latest}"
echo "REGISTRY=\${DOCKER_REGISTRY:-localhost}"
echo "./scripts/build_docker.sh \"\$REGISTRY\" \"ml-pipeline\" \"\$MODEL_VERSION\""
echo ""

print_info "Kubernetes deployment example:"
echo "# Deploy to Kubernetes with specific image versions"
echo "kubectl set image deployment/ml-train \\"
echo "  train=prod-registry.company.com/ml-platform/train:$GIT_SHA-v2.1.0"
echo "kubectl set image deployment/ml-serve \\"
echo "  serve=prod-registry.company.com/ml-platform/serve:$GIT_SHA-v2.1.0"
echo ""

# Example 6: Model version management
print_header "Example 6: Model Version Management"

print_info "Different model versions:"
echo "# Build training image for model v1.0"
echo "./scripts/build_docker.sh localhost ml-pipeline v1.0"
echo ""
echo "# Build training image for model v1.1 (with bug fix)"
echo "./scripts/build_docker.sh localhost ml-pipeline v1.1"
echo ""
echo "# Build training image for experimental model"
echo "./scripts/build_docker.sh localhost ml-pipeline experimental-$(date +%Y%m%d)"
echo ""

print_info "Serving different model versions:"
echo "# Serve model v1.0"
echo "docker run -p 8000:8000 -e MODEL_URI=models:/my_model/1 \\"
echo "  localhost/ml-pipeline/serve:$GIT_SHA-v1.0"
echo ""
echo "# Serve model v1.1"
echo "docker run -p 8001:8000 -e MODEL_URI=models:/my_model/2 \\"
echo "  localhost/ml-pipeline/serve:$GIT_SHA-v1.1"
echo ""

print_success "Docker containerization examples completed!"
print_info "Use these patterns to build and deploy your ML pipeline containers."
