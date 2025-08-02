# Quick Start Guide

Get up and running with the ML CI/CD pipeline in just a few minutes!

## 🚀 5-Minute Setup

### Prerequisites
- Python 3.9+
- Docker and Docker Compose
- Git

### Step 1: Clone and Setup

```bash
# Clone the repository
git clone https://github.com/your-username/ml_ci_cd.git
cd ml_ci_cd

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Environment Configuration

```bash
# Copy environment template
cp .env.example .env

# Install pre-commit hooks
pre-commit install

# Run setup script
./setup_env.sh
```

### Step 3: Start Services with Docker

```bash
# Start all services
docker-compose up -d

# Verify services are running
docker-compose ps
```

### Step 4: Access the Applications

- **MLflow UI**: http://localhost:5000
- **Model API**: http://localhost:8080
- **API Documentation**: http://localhost:8080/docs

## 🧪 Quick Test

Run a simple prediction test:

```bash
# Health check
curl http://localhost:8080/health

# Make a prediction
curl -X POST http://localhost:8080/predict \
  -H "Content-Type: application/json" \
  -d '{"instances": [{"input": "Hello, world!"}]}'
```

## 📊 Run Your First Experiment

```bash
# Run model training
make train-model

# View results in MLflow UI
open http://localhost:5000
```

## 🧹 Cleanup

```bash
# Stop all services
docker-compose down

# Clean up artifacts
make clean
```

## ➡️ Next Steps

Now that you have the basic setup running:

1. [Set up Local Development](local-development.md) - Configure your development environment
2. [Understand the Architecture](../architecture/overview.md) - Learn how components work together
3. [Development Workflow](../development/workflow.md) - Learn the development process

## 🆘 Troubleshooting

### Common Issues

**Port already in use:**
```bash
# Check what's using the port
lsof -i :5000
# Kill the process and restart
make start-mlflow
```

**Docker build fails:**
```bash
# Clean Docker cache
docker system prune -a
# Rebuild
docker-compose build --no-cache
```

**Permission denied:**
```bash
# Make scripts executable
chmod +x setup_env.sh
chmod +x scripts/*.sh
```

Need more help? Check the [Troubleshooting Guide](../troubleshooting/common-issues.md).
