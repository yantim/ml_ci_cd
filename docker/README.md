# Docker Containerization

This directory contains multi-stage Docker builds for the ML CI/CD pipeline, including training and serving containers with parameterized image names using Git SHA and model version tags.

## Files Overview

- `train.Dockerfile` - Multi-stage Docker build for ML model training
- `serve.Dockerfile` - Multi-stage Docker build for ML model serving
- `docker-compose.yml` - Orchestration configuration for the complete ML pipeline
- `README.md` - This documentation

## Architecture

### Training Container (`train.Dockerfile`)

**Stage 1: Builder**
- Base: `python:3.10-slim`
- Installs build dependencies and Poetry
- Copies `poetry.lock` and `pyproject.toml`
- Installs production + training dependencies

**Stage 2: Runtime**
- Base: `python:3.10-slim`
- Copies virtual environment from builder stage
- Copies source code and training script
- Entrypoint: `scripts/train.sh`

### Serving Container (`serve.Dockerfile`)

**Stage 1: Builder**
- Base: `python:3.10-slim`
- Installs minimal runtime dependencies
- Optimized for serving (removes unnecessary packages like DVC)

**Stage 2: Runtime**
- Copies only serving code (`src/serving/`)
- Exposes port 8000
- Runs `uvicorn src.serving.app:app`
- Supports MLflow model loading via environment variables
- Health checks included

## Image Naming Convention

Images are tagged with the following pattern:
```
{registry}/{project}/{service}:{git-sha}-{model-version}
```

Examples:
- `localhost/ml-pipeline/train:abc1234-v1.0.0`
- `prod-registry.com/ml-platform/serve:def5678-v2.1.0`
- `localhost/ml-pipeline/train:latest` (for main/master branch)

## Quick Start

### 1. Build Images

```bash
# Build with default settings (localhost/ml-pipeline/latest)
./scripts/build_docker.sh

# Build with custom registry and version
./scripts/build_docker.sh "my-registry.com" "my-project" "v1.0.0"
```

### 2. Run with Docker Compose

```bash
# Start MLflow server
docker-compose -f docker/docker-compose.yml up -d mlflow-server

# Run training
export TRAIN_IMAGE=localhost/ml-pipeline/train:$(git rev-parse --short HEAD)-latest
docker-compose -f docker/docker-compose.yml --profile train up train

# Run serving
export SERVE_IMAGE=localhost/ml-pipeline/serve:$(git rev-parse --short HEAD)-latest
docker-compose -f docker/docker-compose.yml --profile serve up -d serve
```

### 3. Direct Docker Usage

```bash
# Get current Git SHA and set image tags
GIT_SHA=$(git rev-parse --short HEAD)
TRAIN_IMAGE="localhost/ml-pipeline/train:${GIT_SHA}-latest"
SERVE_IMAGE="localhost/ml-pipeline/serve:${GIT_SHA}-latest"

# Run training
docker run --rm \
  -e MLFLOW_TRACKING_URI=http://host.docker.internal:5000 \
  -e EXPERIMENT_NAME=my_experiment \
  -e MODEL_NAME=my_model \
  -v $(pwd)/data:/home/app/data:ro \
  -v $(pwd)/config:/home/app/config:ro \
  $TRAIN_IMAGE

# Run serving
docker run --rm -p 8000:8000 \
  -e MODEL_URI=models:/my_model/latest \
  -e MLFLOW_TRACKING_URI=http://host.docker.internal:5000 \
  $SERVE_IMAGE
```

## Environment Variables

### Training Container

| Variable | Default | Description |
|----------|---------|-------------|
| `MLFLOW_TRACKING_URI` | `http://host.docker.internal:5000` | MLflow tracking server URL |
| `EXPERIMENT_NAME` | `code_model_training` | MLflow experiment name |
| `MODEL_NAME` | `code_model_fine_tuning_model` | Model registration name |

### Serving Container

| Variable | Default | Description |
|----------|---------|-------------|
| `MODEL_URI` | `models:/code_model_fine_tuning_model/latest` | MLflow model URI |
| `MLFLOW_TRACKING_URI` | `http://host.docker.internal:5000` | MLflow tracking server URL |
| `MODEL_PATH` | `/app/models` | Local model storage path |
| `ARTIFACTS_PATH` | `/app/artifacts` | Model artifacts path |

## Volume Mounts

### Training

- `./data:/home/app/data:ro` - Training data (read-only)
- `./config:/home/app/config:ro` - Configuration files (read-only)
- `model_artifacts:/home/app/models` - Model output storage

### Serving

- `model_artifacts:/app/models` - Model storage
- `mlflow_artifacts:/app/artifacts` - MLflow artifacts

## Docker Compose Profiles

- `train` - Training service
- `serve` - Production serving service
- `dev` - Development serving (without MLflow dependency)

## CI/CD Integration

### GitHub Actions Example

```yaml
- name: Build Docker Images
  run: |
    GIT_SHA=$(git rev-parse --short HEAD)
    MODEL_VERSION=${GITHUB_REF_NAME:-latest}
    ./scripts/build_docker.sh "$DOCKER_REGISTRY" "$PROJECT_NAME" "$MODEL_VERSION"
```

### GitLab CI Example

```yaml
build_docker:
  script:
    - GIT_SHA=$(git rev-parse --short HEAD)
    - MODEL_VERSION=${CI_COMMIT_TAG:-latest}
    - ./scripts/build_docker.sh "$CI_REGISTRY" "$CI_PROJECT_NAME" "$MODEL_VERSION"
```

## Production Deployment

### Kubernetes

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ml-serve
spec:
  template:
    spec:
      containers:
      - name: serve
        image: prod-registry.com/ml-platform/serve:abc1234-v1.0.0
        env:
        - name: MODEL_URI
          value: "models:/production_model/1"
        - name: MLFLOW_TRACKING_URI
          value: "http://mlflow-server:5000"
```

### AWS ECS

```json
{
  "family": "ml-serve",
  "containerDefinitions": [
    {
      "name": "serve",
      "image": "123456789.dkr.ecr.us-west-2.amazonaws.com/ml-platform/serve:abc1234-v1.0.0",
      "environment": [
        {
          "name": "MODEL_URI",
          "value": "models:/production_model/1"
        }
      ]
    }
  ]
}
```

## Security Considerations

1. **Non-root user**: Both containers run as non-root user `app`
2. **Read-only mounts**: Data volumes are mounted read-only
3. **Minimal base images**: Using `python:3.10-slim` for smaller attack surface
4. **Health checks**: Built-in health check endpoints
5. **Environment variables**: Secrets should be injected via orchestration platform

## Troubleshooting

### Build Issues

```bash
# Check Docker daemon
docker info

# Clean build cache
docker builder prune

# Build with verbose output
docker build --progress=plain -f docker/train.Dockerfile .
```

### Runtime Issues

```bash
# Check container logs
docker logs ml-train
docker logs ml-serve

# Inspect container
docker exec -it ml-serve bash

# Check health
curl http://localhost:8000/health
```

### MLflow Connection Issues

```bash
# Test MLflow connectivity from container
docker run --rm --network host $SERVE_IMAGE \
  python -c "import mlflow; print(mlflow.get_tracking_uri())"
```

## Examples

See `scripts/docker_examples.sh` for comprehensive usage examples including:
- Default and custom builds
- Docker Compose orchestration
- Direct Docker usage
- Production deployment patterns
- Model version management
