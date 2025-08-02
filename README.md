# ML CI/CD Pipeline Project

[![CI](https://github.com/yantim/ml_ci_cd/workflows/CI/badge.svg)](https://github.com/yantim/ml_ci_cd/actions)
[![Deploy](https://github.com/yantim/ml_ci_cd/workflows/Deploy/badge.svg)](https://github.com/yantim/ml_ci_cd/actions)
[![codecov](https://codecov.io/gh/yantim/ml_ci_cd/branch/main/graph/badge.svg)](https://codecov.io/gh/yantim/ml_ci_cd)

A comprehensive end-to-end MLOps pipeline demonstrating modern machine learning practices with PyTorch, MLflow, Docker, and AWS deployment. This project showcases a complete ML CI/CD workflow from data preparation to production deployment.

## 🏗️ Architecture Overview

```mermaid
graph TB
    subgraph "Data Layer"
        D1[Raw Data]
        D2[DVC - Data Versioning]
        D3[Processed Data]
    end
    
    subgraph "Development"
        DEV1[Local Development]
        DEV2[Pre-commit Hooks]
        DEV3[Code Quality Gates]
    end
    
    subgraph "Training Pipeline"
        T1[Model Training]
        T2[MLflow Tracking]
        T3[Model Registry]
        T4[Model Validation]
    end
    
    subgraph "CI/CD Pipeline"
        CI1[GitHub Actions]
        CI2[Quality Checks]
        CI3[Testing]
        CI4[Model Training]
        CI5[Deployment]
    end
    
    subgraph "Infrastructure"
        I1[Terraform]
        I2[AWS ECS]
        I3[AWS RDS - PostgreSQL]
        I4[AWS S3]
        I5[AWS Lambda]
    end
    
    subgraph "Production"
        P1[Model Serving - FastAPI]
        P2[Load Balancer]
        P3[Monitoring]
        P4[Logging]
    end
    
    D1 --> D2
    D2 --> D3
    D3 --> T1
    
    DEV1 --> DEV2
    DEV2 --> DEV3
    DEV3 --> CI1
    
    T1 --> T2
    T2 --> T3
    T3 --> T4
    
    CI1 --> CI2
    CI2 --> CI3
    CI3 --> CI4
    CI4 --> CI5
    
    I1 --> I2
    I1 --> I3
    I1 --> I4
    I1 --> I5
    
    CI5 --> P1
    P1 --> P2
    P2 --> P3
    P3 --> P4
    
    T2 --> I3
    T2 --> I4
    P1 --> I2
```

## 📁 Project Structure

```
ml_ci_cd/
├── 📊 data/                     # Data storage and management
│   ├── raw/                    # Raw data files
│   ├── processed/              # Processed datasets
│   └── external/               # External data sources
├── 🧠 src/                      # Source code
│   ├── training/               # Model training pipeline
│   │   ├── train.py           # Main training script
│   │   └── deploy_model.py    # Model deployment utilities
│   ├── serving/                # Model serving components
│   │   ├── app.py             # FastAPI application
│   │   ├── main.py            # Entry point
│   │   └── mlflow_model.py    # MLflow model wrapper
│   └── utils/                  # Utility functions
│       └── data_preparation.py # Data preprocessing
├── 🏗️ infra/                   # Infrastructure as Code (Terraform)
│   ├── modules/               # Terraform modules
│   ├── main.tf               # Main infrastructure config
│   ├── variables.tf          # Variable definitions
│   └── outputs.tf            # Output values
├── 🐳 docker/                   # Docker configurations
│   ├── training/              # Training container
│   ├── serving/               # Serving container
│   └── mlflow/                # MLflow server container
├── 🧪 tests/                    # Test suite
│   ├── unit/                  # Unit tests
│   ├── integration/           # Integration tests
│   └── e2e/                   # End-to-end tests
├── 🔄 .github/workflows/        # CI/CD workflows
│   ├── ci.yml                 # Continuous Integration
│   ├── train.yml              # Model training workflow
│   └── deploy.yml             # Deployment workflow
├── 📚 docs/                     # Documentation (MkDocs)
├── 🧾 config/                   # Configuration files
└── 📋 Makefile                  # Development commands
```

## 🛠️ Tech Stack

### Core ML Stack
- **🔥 ML Framework**: PyTorch, Transformers (Hugging Face)
- **📊 Experiment Tracking**: MLflow (with PostgreSQL backend)
- **📦 Data Versioning**: DVC (Data Version Control)
- **🚀 Model Serving**: FastAPI, Uvicorn

### Infrastructure & DevOps
- **☁️ Cloud Platform**: AWS (ECS, RDS, S3, Lambda)
- **🏗️ Infrastructure**: Terraform
- **🐳 Containerization**: Docker, Docker Compose
- **🔄 CI/CD**: GitHub Actions

### Code Quality & Testing
- **🧹 Code Formatting**: Black, isort, Ruff
- **🔍 Static Analysis**: mypy, bandit
- **✅ Testing**: pytest, coverage
- **🪝 Pre-commit**: Automated quality checks

### Monitoring & Observability
- **📈 Metrics**: MLflow metrics tracking
- **📝 Logging**: Structured logging with Python logging
- **🔍 Monitoring**: AWS CloudWatch

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- Docker and Docker Compose
- Git
- AWS CLI (for cloud deployment)
- Terraform (for infrastructure deployment)

### Local Development Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yantim/ml_ci_cd.git
   cd ml_ci_cd
   ```

2. **Set up Python environment**:
   ```bash
   # Create virtual environment
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   
   # Install dependencies
   pip install -r requirements.txt
   # or with poetry:
   poetry install
   ```

3. **Environment configuration**:
   ```bash
   # Copy environment template
   cp .env.example .env
   
   # Edit .env with your configurations
   # Set up AWS credentials, MLflow settings, etc.
   ```

4. **Set up development tools**:
   ```bash
   # Install pre-commit hooks
   pre-commit install
   
   # Run setup script
   ./setup_env.sh
   ```

5. **Initialize data and MLflow**:
   ```bash
   # Setup MLflow directories and configuration
   make setup-mlflow
   
   # Initialize DVC (if using data versioning)
   dvc init
   ```

### 🧪 Running the Pipeline Locally

#### Option 1: Using Make Commands (Recommended)

```bash
# Start MLflow server (in separate terminal)
make start-mlflow

# Run complete pipeline
make run-pipeline

# Or step by step:
make prepare-data        # Data preparation
make train-model         # Model training
make evaluate-model      # Model evaluation
make serve-model         # Start model serving
```

#### Option 2: Using Docker Compose

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

#### Option 3: Manual Steps

```bash
# 1. Start MLflow server
python mlflow_server.py

# 2. In another terminal, run training
python src/training/train.py

# 3. Start model serving
python src/serving/main.py
```

### 🧭 Development Workflow

1. **Create a new feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes and run quality checks**:
   ```bash
   # Format code
   make format
   
   # Run linting
   make lint
   
   # Run tests
   make test
   
   # Run all quality gates
   make quality-gates
   ```

3. **Commit and push**:
   ```bash
   git add .
   git commit -m "feat: your feature description"
   git push origin feature/your-feature-name
   ```

4. **Create Pull Request** - CI/CD will automatically run tests and quality checks

### 🔍 Testing Your Changes

```bash
# Run all tests
make test

# Run specific test categories
make test-unit           # Unit tests only
make test-integration    # Integration tests only
make test-e2e           # End-to-end tests only

# Run tests with coverage
make test-coverage

# Run performance tests
make test-performance
```

## MLflow Experiment Tracking

This project uses MLflow for experiment tracking and model registry:

### Local Development

```bash
# Setup MLflow
make setup-mlflow

# Start MLflow server
make start-mlflow

# Run training with tracking
make train-model

# Compare model runs
make compare-models

# Promote best model to staging
make promote-model
```

### Production Setup

For production, MLflow uses:
- **Backend Store**: PostgreSQL on AWS RDS
- **Artifact Store**: AWS S3
- **Tracking Server**: MLflow server on AWS EC2/ECS

See `MLFLOW_GUIDE.md` for detailed setup and usage instructions.

## Development

This project includes:
- Automated code formatting with Black
- Import sorting with isort  
- Pre-commit hooks for code quality
- Comprehensive test suite
- MLflow experiment tracking
- Model versioning and registry

## Infrastructure

The `infra/` directory contains Terraform configurations for cloud deployment.

## Available Commands

Use the Makefile for common operations:

```bash
make help              # Show all available commands
make setup-mlflow      # Setup MLflow directories and config
make start-mlflow      # Start MLflow tracking server
make train-model       # Run model training with MLflow
make compare-models    # Compare experiment runs
make promote-model     # Promote best model to staging
make serve-model       # Start model serving
make clean             # Clean up artifacts
```

## CI/CD

GitHub Actions workflows handle:
- Code quality checks
- Testing
- MLflow experiment setup
- Model training with tracking
- Automated model promotion
- Deployment

## Model Serving

Models are saved in MLflow PyFunc format for easy serving:

```bash
# Serve model via MLflow
make serve-model

# Or directly
mlflow models serve \
  --model-uri models:/code_model_fine_tuning_model/Production \
  --host 0.0.0.0 --port 8080
```

## ☁️ Cloud Deployment

### AWS Deployment with Terraform

1. **Configure AWS credentials**:
   ```bash
   aws configure
   # or set environment variables:
   export AWS_ACCESS_KEY_ID=your_access_key
   export AWS_SECRET_ACCESS_KEY=your_secret_key
   export AWS_DEFAULT_REGION=us-west-2
   ```

2. **Deploy infrastructure**:
   ```bash
   cd infra
   
   # Initialize Terraform
   terraform init
   
   # Plan deployment
   terraform plan
   
   # Apply infrastructure
   terraform apply
   ```

3. **Deploy application**:
   ```bash
   # Build and push Docker images
   make build-images
   make push-images
   
   # Deploy to AWS ECS
   make deploy-aws
   ```

### Manual Deployment Steps

1. **Create AWS resources**:
   - ECS Cluster for container orchestration
   - RDS PostgreSQL for MLflow backend
   - S3 bucket for MLflow artifacts
   - ECR repositories for Docker images
   - Application Load Balancer

2. **Configure MLflow for production**:
   ```bash
   # Set production MLflow environment variables
   export MLFLOW_BACKEND_STORE_URI=postgresql://user:pass@rds-endpoint:5432/mlflow
   export MLFLOW_DEFAULT_ARTIFACT_ROOT=s3://your-mlflow-bucket/artifacts
   ```

## 💻 API Usage

### Model Inference API

Once the model serving is running, you can make predictions:

```bash
# Health check
curl http://localhost:8080/health

# Model prediction
curl -X POST http://localhost:8080/predict \
  -H "Content-Type: application/json" \
  -d '{
    "instances": [
      {"input": "your input text here"}
    ]
  }'
```

### Python Client Example

```python
import requests
import json

# Model serving endpoint
url = "http://localhost:8080/predict"

# Prepare your data
data = {
    "instances": [
        {"input": "example input text"},
        {"input": "another example"}
    ]
}

# Make prediction request
response = requests.post(url, json=data)
if response.status_code == 200:
    predictions = response.json()
    print(f"Predictions: {predictions}")
else:
    print(f"Error: {response.status_code} - {response.text}")
```

### MLflow Model Registry API

```python
import mlflow
from mlflow.tracking import MlflowClient

# Initialize MLflow client
client = MlflowClient()

# Get latest model version
latest_version = client.get_latest_versions(
    "your_model_name", 
    stages=["Production"]
)[0]

# Load model for inference
model = mlflow.pyfunc.load_model(
    model_uri=f"models:/{latest_version.name}/{latest_version.version}"
)

# Make predictions
result = model.predict(your_input_data)
```

## 🔧 Troubleshooting

### Common Issues

#### MLflow Server Won't Start
```bash
# Check if port is already in use
lsof -i :5000

# Kill existing processes
kill -9 $(lsof -ti:5000)

# Restart MLflow server
make start-mlflow
```

#### Docker Build Issues
```bash
# Clean Docker cache
docker system prune -a

# Rebuild images
make build-images
```

#### AWS Deployment Issues
```bash
# Check AWS credentials
aws sts get-caller-identity

# Verify Terraform state
cd infra && terraform show

# Check ECS service status
aws ecs describe-services --cluster your-cluster --services your-service
```

#### Model Training Failures
```bash
# Check MLflow experiment logs
mlflow ui
# Navigate to failed run and check logs

# Check disk space
df -h

# Clear old artifacts
make clean
```

### Performance Optimization

- **Training**: Use GPU-enabled instances, adjust batch sizes
- **Serving**: Enable model caching, use multiple workers
- **Infrastructure**: Configure auto-scaling, optimize instance types

### Monitoring and Logging

```bash
# View application logs
docker-compose logs -f serving

# Check MLflow server logs
docker-compose logs -f mlflow

# Monitor resource usage
docker stats
```

## 📈 Performance Metrics

### Key Metrics Tracked

- **Training Metrics**: Loss, accuracy, F1-score, training time
- **Inference Metrics**: Latency, throughput, error rate
- **Infrastructure Metrics**: CPU/Memory usage, request count
- **Business Metrics**: Model drift, prediction distribution

### Monitoring Dashboard

Access MLflow UI at `http://localhost:5000` to view:
- Experiment comparisons
- Model performance over time
- Hyperparameter optimization results
- Model registry and deployment status

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests and quality checks (`make quality-gates`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

### Development Guidelines

- Follow PEP 8 style guidelines
- Write tests for new functionality
- Update documentation for any changes
- Ensure all quality gates pass
- Use conventional commit messages

## 📚 Documentation

### Core Documentation
- [`docs/`](docs/) - Complete documentation with MkDocs
- [`MLFLOW_GUIDE.md`](MLFLOW_GUIDE.md) - MLflow setup and usage
- [`TRAINING_PIPELINE.md`](TRAINING_PIPELINE.md) - Training pipeline details
- [`TESTING.md`](TESTING.md) - Testing strategies and setup
- [`PRODUCTION_DEPLOYMENT.md`](PRODUCTION_DEPLOYMENT.md) - Production deployment guide

### Additional Resources
- [`DATA_SETUP_SUMMARY.md`](DATA_SETUP_SUMMARY.md) - Data preparation guide
- [`DOCKER_ORCHESTRATION.md`](DOCKER_ORCHESTRATION.md) - Docker setup and usage
- Architecture Decision Records (ADRs) in [`docs/adr/`](docs/adr/)

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📞 Support

For questions and support:
- Create an issue in the repository
- Check existing documentation in `docs/`
- Review troubleshooting section above

---

**Built with ❤️ by the MLOps Team**
