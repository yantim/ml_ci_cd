# ADR 002: Containerization Strategy

**Date**: 2024-01-01  
**Status**: Accepted  
**Deciders**: DevOps Team, ML Engineering Team  

## Context

Our ML CI/CD pipeline requires consistent, reproducible environments across development, testing, and production. We need to containerize:

- Model training workloads
- Model serving applications
- MLflow tracking server
- Data processing pipelines
- Development environments

Key requirements:
- Consistent environments across all stages
- Efficient resource utilization
- Fast build and deployment times
- Security and compliance
- Multi-architecture support (x86/ARM)

Options considered:
- **Docker** with Docker Compose for local development
- **Podman** as Docker alternative
- **Virtual machines** for isolation
- **Conda environments** only

## Decision

We will use **Docker as our primary containerization technology** with the following strategy:

1. **Multi-stage Docker builds** to optimize image sizes
2. **Docker Compose** for local development orchestration
3. **Separate containers** for each service (training, serving, MLflow)
4. **Base images** optimized for ML workloads
5. **AWS ECS Fargate** for production container orchestration

### Container Architecture

```
ml_ci_cd/
├── docker/
│   ├── base/              # Base images with common dependencies
│   ├── training/          # Training container
│   ├── serving/           # Model serving container
│   └── mlflow/            # MLflow server container
└── docker-compose.yml     # Local development orchestration
```

### Implementation Details

**Base Image Strategy:**
- Use `python:3.9-slim` as base for smaller image size
- Create custom base image with common ML dependencies
- Use multi-stage builds to separate build and runtime dependencies

**Training Container:**
- Include PyTorch, Transformers, MLflow client
- Mount data volumes for input/output
- Support GPU acceleration with CUDA base images

**Serving Container:**
- Lightweight runtime with FastAPI and MLflow
- Health checks and graceful shutdown
- Support for model hot-swapping

**MLflow Container:**
- PostgreSQL client for backend store
- S3 client for artifact store
- Web UI and REST API

## Consequences

### Positive
- ✅ **Consistency**: Identical environments across all stages
- ✅ **Isolation**: Services run in isolated environments
- ✅ **Scalability**: Easy horizontal scaling with container orchestration
- ✅ **Version Control**: Infrastructure as code with Dockerfiles
- ✅ **CI/CD Integration**: Seamless integration with GitHub Actions
- ✅ **Resource Efficiency**: Optimal resource allocation per service

### Negative
- ❌ **Complexity**: Additional layer of complexity for debugging
- ❌ **Build Time**: Initial builds can be slow for ML dependencies
- ❌ **Storage Overhead**: Multiple images consume disk space
- ❌ **Learning Curve**: Team needs Docker expertise

### Mitigation Strategies

**Build Optimization:**
```dockerfile
# Use multi-stage builds
FROM python:3.9-slim as builder
RUN pip install --user torch transformers

FROM python:3.9-slim as runtime
COPY --from=builder /root/.local /root/.local
```

**Development Efficiency:**
- Use Docker layer caching in CI/CD
- Create development containers with hot-reload
- Implement health checks for all services

**Security Measures:**
- Use non-root users in containers
- Regularly update base images
- Scan images for vulnerabilities
- Use secrets management for sensitive data

## Docker Compose Configuration

```yaml
version: '3.8'

services:
  mlflow:
    build: ./docker/mlflow
    ports:
      - "5000:5000"
    environment:
      - MLFLOW_BACKEND_STORE_URI=sqlite:///mlflow.db
    volumes:
      - mlflow_data:/mlflow
      
  training:
    build: ./docker/training
    depends_on:
      - mlflow
    volumes:
      - ./data:/data
      - ./models:/models
      
  serving:
    build: ./docker/serving
    ports:
      - "8080:8080"
    depends_on:
      - mlflow
    environment:
      - MLFLOW_TRACKING_URI=http://mlflow:5000

volumes:
  mlflow_data:
```

## Production Deployment

For production on AWS ECS:

- Use ECR for private image registry
- Implement rolling deployments with health checks
- Use Fargate for serverless container execution
- Configure auto-scaling based on metrics
- Implement proper logging and monitoring

## Related Decisions
- [ADR 001: Choice of Machine Learning Framework](001-framework-choice.md)
- [ADR 003: CI/CD Tooling](003-cicd-tooling.md)
- [ADR 004: Cloud Provider Selection](004-cloud-provider.md)

## References
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [AWS ECS Documentation](https://docs.aws.amazon.com/ecs/)
- [Multi-stage Docker Builds](https://docs.docker.com/develop/dev-best-practices/#use-multi-stage-builds)
