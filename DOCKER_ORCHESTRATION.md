# Docker Orchestration for ML Pipeline

This document describes the complete Docker Compose orchestration setup for the ML CI/CD pipeline with MLflow, monitoring, and serving capabilities.

## 🏗️ Architecture Overview

The orchestration includes the following services:

### Core Services
- **MLflow**: Experiment tracking and model registry
- **PostgreSQL**: Optional backend database for MLflow (instead of SQLite)
- **Training Container**: On-demand model training
- **Serving Container**: Model serving API
- **Nginx**: Reverse proxy for load balancing and SSL termination

### Monitoring Stack
- **Prometheus**: Metrics collection and storage
- **Grafana**: Metrics visualization and dashboards
- **Node Exporter**: System metrics collection

## 🚀 Quick Start

### 1. Development Environment
Start the full development environment with monitoring:

```bash
make dev
```

This starts:
- MLflow tracking server (http://localhost:5000)
- Prometheus (http://localhost:9090)
- Grafana (http://localhost:3000) - admin/admin

### 2. Training Pipeline
Run the training pipeline in containers:

```bash
make train
```

### 3. Model Serving
Start model serving with nginx proxy:

```bash
make serve
```

This starts:
- MLflow UI via nginx (http://localhost:80)
- Model API via nginx (http://localhost:8080)
- Health checks at (http://localhost/health)

## 📦 Available Profiles

The Docker Compose setup uses profiles to start different combinations of services:

### `dev` Profile
Basic development environment:
```bash
docker-compose --profile dev up -d
```
**Services**: mlflow, prometheus, grafana, node-exporter

### `postgres` Profile  
Development with PostgreSQL backend:
```bash
docker-compose --profile dev --profile postgres up -d
```
**Services**: postgres, mlflow (with postgres backend), monitoring stack

### `train` Profile
Training pipeline:
```bash
docker-compose --profile train up
```
**Services**: train container (runs once and exits)

### `serve` Profile
Production serving:
```bash
docker-compose --profile serve up -d
```
**Services**: mlflow, serve, nginx (reverse proxy)

### `monitoring` Profile
Monitoring stack only:
```bash
docker-compose --profile monitoring up -d
```
**Services**: prometheus, grafana, node-exporter

### `full` Profile
All services:
```bash
docker-compose --profile full up -d
```
**Services**: All services including postgres, full monitoring, serving with nginx

## 🎯 Makefile Targets

### Main Orchestration Commands
- `make dev` - Start development environment (MLflow + monitoring)
- `make dev-postgres` - Start dev environment with PostgreSQL backend
- `make dev-full` - Start full environment with all services
- `make train` - Run training pipeline in containers
- `make serve` - Start model serving with nginx proxy
- `make monitoring` - Start monitoring stack only

### Management Commands
- `make down` - Stop all services
- `make down-volumes` - Stop all services and remove volumes
- `make status` - Show service status
- `make logs` - Show logs from all services
- `make logs-mlflow` - Show MLflow-specific logs
- `make logs-serve` - Show serving-specific logs

## 🔧 Configuration

### Environment Variables

The `.env` file contains all configuration:

```bash
# MLflow Configuration
MLFLOW_BACKEND_STORE_URI=sqlite:///mlflow.db
MLFLOW_DEFAULT_ARTIFACT_ROOT=/app/artifacts
USE_POSTGRES=false

# PostgreSQL Configuration
POSTGRES_DB=mlflow
POSTGRES_USER=mlflow
POSTGRES_PASSWORD=mlflow_password

# Training Configuration
EXPERIMENT_NAME=code_model_training
MODEL_NAME=code_model_fine_tuning_model

# Serving Configuration
MODEL_URI=models:/code_model_fine_tuning_model/latest

# Grafana Configuration
GRAFANA_USER=admin
GRAFANA_PASSWORD=admin
```

### Using PostgreSQL Backend

To use PostgreSQL instead of SQLite:

```bash
# Set in .env file
USE_POSTGRES=true

# Start with postgres profile
make dev-postgres
```

## 🌐 Service Endpoints

### Development Environment (`make dev`)
- **MLflow UI**: http://localhost:5000
- **Prometheus**: http://localhost:9090  
- **Grafana**: http://localhost:3000 (admin/admin)

### Serving Environment (`make serve`)
- **MLflow UI**: http://localhost:80 (via nginx)
- **Model API**: http://localhost:8080 (via nginx)
- **Health Check**: http://localhost/health
- **API Health**: http://localhost:8080/health

### Database Access (when using PostgreSQL)
- **PostgreSQL**: localhost:5432
- **Database**: mlflow
- **User**: mlflow / mlflow_password

## 📊 Monitoring & Metrics

### Prometheus Metrics
Prometheus scrapes metrics from:
- Model serving API (`/metrics` endpoint)
- Node exporter (system metrics)
- Prometheus itself

### Grafana Dashboards
Pre-configured dashboards include:
- **ML Pipeline Monitoring**: API requests, system resources, container status
- **System Metrics**: CPU, memory, disk usage
- **Application Metrics**: Model serving performance

### Custom Metrics
Add custom metrics to your serving application by exposing them at `/metrics` endpoint in Prometheus format.

## 🔐 Security Features

### Nginx Configuration
- Rate limiting on API endpoints
- Security headers (X-Frame-Options, X-XSS-Protection, etc.)
- Gzip compression
- Health check endpoints

### Network Security
- All services communicate via isolated Docker network
- External access only through designated ports
- Internal service discovery via container names

## 🗂️ Data Persistence

### Docker Volumes
- `postgres_data`: PostgreSQL database files
- `mlflow_data`: MLflow tracking data (when using SQLite)
- `mlflow_artifacts`: MLflow artifact storage
- `model_artifacts`: Trained model files
- `prometheus_data`: Prometheus metrics storage
- `grafana_data`: Grafana dashboards and configuration

### Volume Management
```bash
# Stop services and remove volumes (WARNING: deletes all data)
make down-volumes

# Backup volumes (example for MLflow data)
docker run --rm -v ml_ci_cd_mlflow_data:/data -v $(pwd):/backup alpine tar czf /backup/mlflow_backup.tar.gz -C /data .
```

## 🚀 Production Deployment

### Environment Variables for Production
```bash
# Use PostgreSQL for production
USE_POSTGRES=true
MLFLOW_BACKEND_STORE_URI=postgresql://user:password@host:port/dbname
MLFLOW_DEFAULT_ARTIFACT_ROOT=s3://your-bucket/artifacts

# Secure Grafana credentials
GRAFANA_USER=your_admin_user
GRAFANA_PASSWORD=secure_password
```

### Scaling Considerations
- Use external PostgreSQL/MySQL for MLflow backend
- Use S3/GCS for artifact storage
- Scale serving containers with load balancer
- Monitor resource usage and set appropriate limits

## 🔍 Troubleshooting

### Common Issues

**Services not starting:**
```bash
# Check service status
make status

# View logs
make logs

# Restart specific service
docker-compose -f docker-compose.yaml restart mlflow
```

**PostgreSQL connection issues:**
```bash
# Check PostgreSQL logs
docker-compose -f docker-compose.yaml logs postgres

# Verify PostgreSQL is ready
docker-compose -f docker-compose.yaml exec postgres pg_isready -U mlflow
```

**Training container fails:**
```bash
# Check training logs
docker-compose -f docker-compose.yaml logs train

# Run training interactively for debugging
docker-compose -f docker-compose.yaml run --rm train bash
```

### Health Checks
All services include health checks. Check status:
```bash
# Overall service health
docker-compose -f docker-compose.yaml ps

# Individual service health
curl http://localhost:5000/health  # MLflow
curl http://localhost/health       # Nginx
curl http://localhost:8080/health  # Serving API
```

## 🔄 Development Workflow

### Typical Development Session
```bash
# 1. Start development environment
make dev

# 2. Run training
make train

# 3. Check results in MLFlow
open http://localhost:5000

# 4. Start serving
make serve

# 5. Test API
curl -X POST http://localhost:8080/invocations \
  -H 'Content-Type: application/json' \
  -d '{"inputs": ["your test data"]}'

# 6. Monitor with Grafana
open http://localhost:3000

# 7. Stop everything
make down
```

### Continuous Integration
For CI/CD pipelines:
```bash
# Build images
make docker-build

# Run tests in containers
make test-docker

# Deploy to staging/production
make serve
```

This orchestration setup provides a complete MLOps environment with proper monitoring, scalability, and production-ready features. 
