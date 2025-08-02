#!/bin/bash
set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Get Git SHA (short version)
GIT_SHA=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")
print_info "Git SHA: $GIT_SHA"

# Get current branch
GIT_BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")
print_info "Git Branch: $GIT_BRANCH"

# Default values
DEFAULT_REGISTRY="localhost"
DEFAULT_PROJECT="ml-pipeline"
DEFAULT_MODEL_VERSION="latest"

# Parse command line arguments
REGISTRY=${1:-$DEFAULT_REGISTRY}
PROJECT=${2:-$DEFAULT_PROJECT}
MODEL_VERSION=${3:-$DEFAULT_MODEL_VERSION}

print_info "Registry: $REGISTRY"
print_info "Project: $PROJECT"
print_info "Model Version: $MODEL_VERSION"

# Generate image tags
TRAIN_IMAGE_TAG="$REGISTRY/$PROJECT/train:$GIT_SHA-$MODEL_VERSION"
SERVE_IMAGE_TAG="$REGISTRY/$PROJECT/serve:$GIT_SHA-$MODEL_VERSION"

# Also create latest tags for main/master branch
if [[ "$GIT_BRANCH" == "main" || "$GIT_BRANCH" == "master" ]]; then
    TRAIN_LATEST_TAG="$REGISTRY/$PROJECT/train:latest"
    SERVE_LATEST_TAG="$REGISTRY/$PROJECT/serve:latest"
fi

print_info "Building Docker images..."
print_info "Training image: $TRAIN_IMAGE_TAG"
print_info "Serving image: $SERVE_IMAGE_TAG"

# Build training image
print_info "Building training image..."
docker build \
    -f docker/train.Dockerfile \
    -t "$TRAIN_IMAGE_TAG" \
    --build-arg GIT_SHA="$GIT_SHA" \
    --build-arg MODEL_VERSION="$MODEL_VERSION" \
    .

if [ $? -eq 0 ]; then
    print_success "Training image built successfully: $TRAIN_IMAGE_TAG"
else
    print_error "Failed to build training image"
    exit 1
fi

# Tag as latest if on main/master branch
if [[ "$GIT_BRANCH" == "main" || "$GIT_BRANCH" == "master" ]]; then
    docker tag "$TRAIN_IMAGE_TAG" "$TRAIN_LATEST_TAG"
    print_success "Tagged training image as latest: $TRAIN_LATEST_TAG"
fi

# Build serving image
print_info "Building serving image..."
docker build \
    -f docker/serve.Dockerfile \
    -t "$SERVE_IMAGE_TAG" \
    --build-arg GIT_SHA="$GIT_SHA" \
    --build-arg MODEL_VERSION="$MODEL_VERSION" \
    .

if [ $? -eq 0 ]; then
    print_success "Serving image built successfully: $SERVE_IMAGE_TAG"
else
    print_error "Failed to build serving image"
    exit 1
fi

# Tag as latest if on main/master branch
if [[ "$GIT_BRANCH" == "main" || "$GIT_BRANCH" == "master" ]]; then
    docker tag "$SERVE_IMAGE_TAG" "$SERVE_LATEST_TAG"
    print_success "Tagged serving image as latest: $SERVE_LATEST_TAG"
fi

print_success "All Docker images built successfully!"
print_info ""
print_info "Built images:"
print_info "  Training: $TRAIN_IMAGE_TAG"
print_info "  Serving:  $SERVE_IMAGE_TAG"

if [[ "$GIT_BRANCH" == "main" || "$GIT_BRANCH" == "master" ]]; then
    print_info "  Training (latest): $TRAIN_LATEST_TAG"
    print_info "  Serving (latest):  $SERVE_LATEST_TAG"
fi

print_info ""
print_info "Usage examples:"
print_info "  Run training: docker run --rm $TRAIN_IMAGE_TAG"
print_info "  Run serving:  docker run --rm -p 8000:8000 $SERVE_IMAGE_TAG"
