# Common Issues and Troubleshooting

This guide covers the most common issues you might encounter when working with the ML CI/CD pipeline and their solutions.

## 🐳 Docker Issues

### Docker Build Failures

**Issue**: Docker build fails with dependency conflicts
```bash
ERROR: Could not find a version that satisfies the requirement torch==2.0.0
```

**Solution**:
```bash
# Clear Docker cache
docker system prune -a

# Rebuild with no cache
docker-compose build --no-cache

# Check if base image is accessible
docker pull python:3.9-slim
```

**Issue**: Permission denied when running Docker commands
```bash
docker: Got permission denied while trying to connect to the Docker daemon socket
```

**Solution**:
```bash
# Add user to docker group (Linux)
sudo usermod -aG docker $USER
newgrp docker

# Or use sudo (temporary fix)
sudo docker-compose up
```

### Container Runtime Issues

**Issue**: Container exits immediately with code 0
```bash
# Check container logs
docker-compose logs service-name

# Run container interactively for debugging
docker run -it --entrypoint /bin/bash image-name
```

**Issue**: Port already in use
```bash
Error: bind: address already in use
```

**Solution**:
```bash
# Find process using the port
lsof -i :5000
# Or on Linux
netstat -tulpn | grep :5000

# Kill the process
kill -9 PID

# Or use different ports in docker-compose.yml
```

## 🔬 MLflow Issues

### Server Won't Start

**Issue**: MLflow server fails to start
```bash
mlflow server --host 0.0.0.0 --port 5000
# Connection refused or port in use
```

**Solution**:
```bash
# Check if port is available
lsof -i :5000

# Kill existing MLflow processes
pkill -f "mlflow server"

# Start with different port
mlflow server --host 0.0.0.0 --port 5001

# Or use the make command
make start-mlflow
```

### Database Connection Issues

**Issue**: Cannot connect to MLflow backend store
```bash
sqlalchemy.exc.OperationalError: (psycopg2.OperationalError) 
connection to server at "localhost" (127.0.0.1), port 5432 failed
```

**Solution**:
```bash
# Check if PostgreSQL is running
docker-compose ps

# Verify database credentials
echo $MLFLOW_BACKEND_STORE_URI

# Reset database
docker-compose down
docker volume rm ml_ci_cd_postgres_data
docker-compose up -d
```

### Artifact Store Issues

**Issue**: Cannot access S3 artifacts
```bash
botocore.exceptions.NoCredentialsError: Unable to locate credentials
```

**Solution**:
```bash
# Check AWS credentials
aws sts get-caller-identity

# Set credentials
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret

# Or use AWS profile
export AWS_PROFILE=your_profile

# Verify S3 access
aws s3 ls s3://your-mlflow-bucket/
```

## 🏋️ Training Issues

### Memory Errors

**Issue**: Out of memory during training
```bash
RuntimeError: CUDA out of memory. Tried to allocate 2.00 GiB
```

**Solution**:
```python
# Reduce batch size
BATCH_SIZE = 8  # Instead of 32

# Enable gradient checkpointing
model.gradient_checkpointing_enable()

# Use mixed precision training
from torch.cuda.amp import autocast, GradScaler
scaler = GradScaler()

# Clear GPU cache
import torch
torch.cuda.empty_cache()
```

### Model Loading Errors

**Issue**: Cannot load pre-trained model
```bash
OSError: Can't load config for 'bert-base-uncased'
```

**Solution**:
```bash
# Check internet connection
curl -I https://huggingface.co

# Use local model cache
export TRANSFORMERS_CACHE=/path/to/cache

# Download model manually
python -c "from transformers import AutoModel; AutoModel.from_pretrained('bert-base-uncased')"
```

### Training Stalls or Crashes

**Issue**: Training process hangs or crashes unexpectedly

**Solution**:
```bash
# Check disk space
df -h

# Monitor memory usage
htop
# Or
nvidia-smi  # For GPU memory

# Check logs
docker-compose logs training

# Reduce complexity
# - Smaller model
# - Less data
# - Lower learning rate
```

## 🚀 Deployment Issues

### ECS Task Failures

**Issue**: ECS tasks fail to start or keep restarting

**Solution**:
```bash
# Check ECS service events
aws ecs describe-services --cluster your-cluster --services your-service

# Check task logs
aws logs tail /ecs/your-service --follow

# Verify task definition
aws ecs describe-task-definition --task-definition your-task:1

# Check security groups and subnets
aws ec2 describe-security-groups --group-ids sg-xxxxx
```

### Load Balancer Health Checks

**Issue**: ALB health checks failing
```bash
# Check target group health
aws elbv2 describe-target-health --target-group-arn arn:aws:elasticloadbalancing:...

# Verify health check endpoint
curl http://your-service:8080/health

# Check security group rules
# Ensure ALB can reach targets on health check port
```

### Database Connection in Production

**Issue**: Cannot connect to RDS from ECS tasks
```bash
# Check RDS security group
aws rds describe-db-instances --db-instance-identifier your-db

# Verify network connectivity
# From ECS task, test connection:
telnet your-rds-endpoint 5432

# Check parameter store values
aws ssm get-parameter --name "/your-app/database/url"
```

## 🧪 Testing Issues

### Test Failures

**Issue**: Tests fail unexpectedly
```bash
# Run tests in verbose mode
pytest -v tests/

# Run specific test
pytest tests/test_model.py::test_training -v

# Check test environment
pytest --collect-only

# Clean test artifacts
make clean-test
```

### Import Errors in Tests

**Issue**: Module not found errors
```bash
ModuleNotFoundError: No module named 'src'
```

**Solution**:
```bash
# Install package in development mode
pip install -e .

# Or add to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"

# Check __init__.py files exist
find src -name "__init__.py"
```

## 🔧 CI/CD Issues

### GitHub Actions Failures

**Issue**: Workflow fails on specific steps

**Solution**:
```bash
# Check workflow logs in GitHub Actions tab
# Look for specific error messages

# Test workflow locally with act
act -j test

# Debug with SSH (add to workflow)
- name: Setup tmate session
  uses: mxschmitt/action-tmate@v3
```

### Secret Management Issues

**Issue**: Cannot access secrets in GitHub Actions

**Solution**:
```yaml
# Verify secret names match exactly
env:
  AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
  
# Check if secrets are set in repository settings
# GitHub repo -> Settings -> Secrets and variables -> Actions
```

## 📊 Performance Issues

### Slow API Response

**Issue**: Model serving API responds slowly

**Solution**:
```bash
# Check container resources
docker stats

# Optimize model loading
# - Use ONNX for faster inference
# - Implement model caching
# - Use smaller models for production

# Scale horizontally
# Increase desired_count in ECS service
```

### High Memory Usage

**Issue**: Memory usage keeps increasing

**Solution**:
```python
# Implement proper cleanup
import gc
import torch

def cleanup():
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

# Monitor memory usage
import psutil
print(f"Memory usage: {psutil.virtual_memory().percent}%")
```

## 🔍 Debugging Tools

### Useful Commands

```bash
# Check all running containers
docker ps -a

# Inspect container configuration
docker inspect container-name

# Execute commands in running container
docker exec -it container-name /bin/bash

# Check logs with timestamps
docker-compose logs -t service-name

# Monitor system resources
htop
iotop
nvidia-smi watch -n 1

# Check network connectivity
curl -v http://service:port/endpoint
telnet hostname port
```

### Environment Debugging

```bash
# Print all environment variables
env | sort

# Check Python path and imports
python -c "import sys; print('\n'.join(sys.path))"

# Verify package versions
pip list
pip show package-name

# Check CUDA availability
python -c "import torch; print(torch.cuda.is_available())"
```

## 🆘 Getting Help

When you encounter issues not covered here:

1. **Check logs first** - Most issues leave traces in logs
2. **Search existing issues** - Check GitHub issues for similar problems
3. **Create minimal reproduction** - Isolate the problem
4. **Provide context** - Include error messages, logs, and environment details

### Log Collection

```bash
# Collect all relevant logs
mkdir debug-logs
docker-compose logs > debug-logs/docker-compose.log
kubectl logs deployment/your-app > debug-logs/k8s.log  # If using K8s
aws logs tail /aws/ecs/your-service > debug-logs/ecs.log  # If using ECS

# System information
uname -a > debug-logs/system.txt
docker version > debug-logs/docker-version.txt
python --version > debug-logs/python-version.txt
```

### Contact Information

- **GitHub Issues**: [Project Issues](https://github.com/your-username/ml_ci_cd/issues)
- **Documentation**: Check other sections in `/docs`
- **Community**: Join discussions in GitHub Discussions

Remember: Most issues have been encountered by someone else before. Take time to search and read error messages carefully!
