# MLflow Experiment Tracking and Model Registry Guide

This guide explains how to use MLflow for experiment tracking, model comparison, and model registry in our ML pipeline.

## Table of Contents

1. [Setup](#setup)
2. [Running MLflow Server](#running-mlflow-server)
3. [Training with MLflow Tracking](#training-with-mlflow-tracking)
4. [Comparing Experiments and Runs](#comparing-experiments-and-runs)
5. [Model Registry](#model-registry)
6. [Production Deployment](#production-deployment)
7. [MLflow PyFunc Models](#mlflow-pyfunc-models)
8. [Best Practices](#best-practices)

## Setup

### Local Development Setup

1. **Initialize MLflow directories and configuration:**
   ```bash
   python mlflow_server.py --setup-only
   ```

   This creates:
   - `mlflow/` directory with subdirectories for artifacts and database
   - `config/.env.mlflow` with local development settings
   - `config/.env.mlflow.prod` template for production

2. **Set environment variables:**
   ```bash
   # For local development
   export MLFLOW_TRACKING_URI=http://localhost:5000
   
   # Or source the config file
   source config/.env.mlflow
   ```

### Production Setup

1. **Configure PostgreSQL backend:**
   ```bash
   # Set environment variables for production
   export MLFLOW_TRACKING_URI=http://your-mlflow-server:5000
   export MLFLOW_BACKEND_STORE_URI=postgresql://user:password@host:port/dbname
   export MLFLOW_DEFAULT_ARTIFACT_ROOT=s3://your-mlflow-bucket/artifacts
   ```

2. **AWS RDS Setup for Production:**
   ```sql
   -- Create database for MLflow
   CREATE DATABASE mlflow_db;
   
   -- Create user for MLflow
   CREATE USER mlflow_user WITH ENCRYPTED PASSWORD 'your_password';
   GRANT ALL PRIVILEGES ON DATABASE mlflow_db TO mlflow_user;
   ```

## Running MLflow Server

### Local Development

```bash
# Start MLflow server with SQLite backend
python mlflow_server.py

# Or with custom settings
python mlflow_server.py --host 0.0.0.0 --port 5000
```

### Production

```bash
# Start MLflow server with PostgreSQL backend
mlflow server \
  --host 0.0.0.0 \
  --port 5000 \
  --backend-store-uri postgresql://user:password@host:port/dbname \
  --default-artifact-root s3://your-mlflow-bucket/artifacts \
  --serve-artifacts
```

## Training with MLflow Tracking

### Basic Training

```bash
# Set MLflow tracking URI
export MLFLOW_TRACKING_URI=http://localhost:5000

# Run training with MLflow tracking
python src/training/train.py --config src/training/config.yaml
```

### Training with Custom Experiment

```bash
# Run with custom experiment name and parameters
python src/training/train.py \
  --config src/training/config.yaml \
  --overrides \
    mlflow.experiment_name=codet5_lora_experiment \
    mlflow.run_name=run_v1.0 \
    training.learning_rate=1e-4 \
    peft.r=32
```

### CI/CD Training

The CI pipeline automatically:
- Sets up MLflow tracking
- Runs training tests with MLflow logging
- Stores artifacts and metrics

```yaml
# In .github/workflows/ci.yml
- name: Set up MLflow tracking
  run: |
    python mlflow_server.py --setup-only
    echo "MLFLOW_TRACKING_URI=file://$(pwd)/mlflow" >> $GITHUB_ENV
```

## Comparing Experiments and Runs

### Using MLflow UI

1. **Start MLflow UI:**
   ```bash
   mlflow ui --host 0.0.0.0 --port 5000
   ```

2. **Navigate to experiments:**
   - Go to http://localhost:5000
   - Select experiment from the dropdown
   - Compare runs by selecting multiple runs and clicking "Compare"

### Programmatic Comparison

```python
import mlflow
from mlflow.tracking import MlflowClient

# Initialize client
client = MlflowClient()

# Get experiment by name
experiment = client.get_experiment_by_name("code_model_fine_tuning")

# Get all runs for experiment
runs = client.search_runs(
    experiment_ids=[experiment.experiment_id],
    order_by=["metrics.test_eval_loss ASC"]  # Order by best performance
)

# Compare top 5 runs
for run in runs[:5]:
    print(f"Run ID: {run.info.run_id}")
    print(f"Test Loss: {run.data.metrics.get('test_eval_loss', 'N/A')}")
    print(f"Learning Rate: {run.data.params.get('learning_rate', 'N/A')}")
    print(f"LoRA r: {run.data.params.get('lora_r', 'N/A')}")
    print("-" * 40)
```

### Key Metrics to Compare

- **Training Loss**: `train_loss`
- **Test Metrics**: `test_eval_loss`, `test_eval_exact_match`
- **Training Parameters**: `learning_rate`, `batch_size`, `lora_r`
- **Model Parameters**: `model_name`, `use_peft`
- **Training Time**: Duration of training runs

## Model Registry

### Registering Models

Models are automatically registered during training if `mlflow.log_model: true` in config:

```python
# Two models are registered:
# 1. PyTorch model: {experiment_name}_pytorch_model
# 2. PyFunc model: {experiment_name}_model (recommended for serving)
```

### Manual Model Registration

```python
import mlflow

# Register a model from a run
model_uri = f"runs:/{run_id}/pyfunc_model"
mlflow.register_model(
    model_uri=model_uri,
    name="code_generation_model"
)
```

### Model Versioning and Stages

```python
from mlflow.tracking import MlflowClient

client = MlflowClient()

# Get model versions
model_name = "code_model_fine_tuning_model"
model_versions = client.search_model_versions(f"name='{model_name}'")

# Promote best model to staging
best_version = model_versions[0]  # Assume sorted by performance
client.transition_model_version_stage(
    name=model_name,
    version=best_version.version,
    stage="Staging"
)

# After validation, promote to production
client.transition_model_version_stage(
    name=model_name,
    version=best_version.version,
    stage="Production"
)
```

### Model Comparison and Selection

```python
# Compare model versions
for version in model_versions:
    run = client.get_run(version.run_id)
    print(f"Version {version.version} (Stage: {version.current_stage}):")
    print(f"  Test Loss: {run.data.metrics.get('test_eval_loss', 'N/A')}")
    print(f"  Exact Match: {run.data.metrics.get('test_eval_exact_match', 'N/A')}")
    print(f"  Learning Rate: {run.data.params.get('learning_rate', 'N/A')}")
```

## Production Deployment

### Loading Models for Serving

```python
import mlflow.pyfunc

# Load latest production model
model_uri = "models:/code_model_fine_tuning_model/Production"
model = mlflow.pyfunc.load_model(model_uri)

# Make predictions
predictions = model.predict(["def fibonacci(n):", "// Calculate factorial"])
```

### Model Serving with MLflow

```bash
# Serve model via REST API
mlflow models serve \
  --model-uri models:/code_model_fine_tuning_model/Production \
  --host 0.0.0.0 \
  --port 8080
```

### Docker Deployment

```bash
# Build Docker image for model serving
mlflow models build-docker \
  --model-uri models:/code_model_fine_tuning_model/Production \
  --name code-generation-model

# Run Docker container
docker run -p 8080:8080 code-generation-model
```

## MLflow PyFunc Models

### Benefits of PyFunc Format

- **Framework Agnostic**: Works with any ML framework
- **Easy Serving**: Simple REST API deployment
- **Custom Logic**: Add preprocessing/postprocessing
- **Dependency Management**: Automated environment handling

### Testing PyFunc Models

```python
from src.serving.mlflow_model import test_pyfunc_model

# Test model with sample inputs
test_inputs = [
    "def fibonacci(n):",
    "// Function to calculate factorial",
    "def quicksort(arr):"
]

model_uri = "models:/code_model_fine_tuning_model/1"
test_pyfunc_model(model_uri, test_inputs)
```

### Custom Prediction Parameters

```python
# Use custom generation parameters
predictions = model.predict(
    ["def fibonacci(n):"],
    params={
        "max_new_tokens": 128,
        "num_beams": 2,
        "do_sample": True,
        "temperature": 0.7
    }
)
```

## Best Practices

### Experiment Organization

1. **Use Descriptive Experiment Names**:
   - `codet5_baseline`
   - `codet5_lora_r16`
   - `codet5_full_finetune`

2. **Consistent Run Naming**:
   - Include key parameters: `lr1e-4_bs8_r16`
   - Include date/version: `v1.0_20240101`

3. **Tag Runs Appropriately**:
   ```python
   mlflow.set_tag("model_type", "code_generation")
   mlflow.set_tag("experiment_phase", "hyperparameter_tuning")
   ```

### Parameter Tracking

1. **Log All Relevant Parameters**:
   - Model architecture details
   - Training hyperparameters
   - Data preprocessing settings
   - Hardware configuration

2. **Use Nested Parameters**:
   ```python
   mlflow.log_params({
       "model.name": config.model.name,
       "training.learning_rate": config.training.learning_rate,
       "peft.r": config.peft.r
   })
   ```

### Metrics and Artifacts

1. **Track Key Metrics**:
   - Training/validation loss
   - Task-specific metrics (BLEU, exact match)
   - Training time and resource usage

2. **Save Important Artifacts**:
   - Model checkpoints
   - Generated examples
   - Training logs
   - Configuration files

### Model Registry Usage

1. **Stage Transitions**:
   - `None` → `Staging`: After initial validation
   - `Staging` → `Production`: After thorough testing
   - `Production` → `Archived`: When superseded

2. **Model Descriptions**:
   ```python
   client.update_model_version(
       name=model_name,
       version=version,
       description="CodeT5 with LoRA (r=16), trained on CodeSearchNet. Best performing model on exact match metric."
   )
   ```

3. **Model Aliases** (MLflow 2.0+):
   ```python
   client.set_registered_model_alias(
       name=model_name,
       alias="champion",
       version=best_version
   )
   ```

### Production Monitoring

1. **Monitor Model Performance**:
   - Track prediction latency
   - Monitor prediction quality
   - Set up alerts for anomalies

2. **A/B Testing**:
   ```python
   # Load different model versions for comparison
   model_a = mlflow.pyfunc.load_model("models:/model_name/1")
   model_b = mlflow.pyfunc.load_model("models:/model_name/2")
   ```

### Cleanup and Maintenance

1. **Regular Cleanup**:
   ```python
   # Delete old experiments
   client.delete_experiment(experiment_id)
   
   # Archive old model versions
   client.transition_model_version_stage(
       name=model_name,
       version=old_version,
       stage="Archived"
   )
   ```

2. **Backup Important Runs**:
   - Export successful experiments
   - Store configuration files
   - Backup production models

## Troubleshooting

### Common Issues

1. **Connection Problems**:
   ```bash
   # Check MLflow server status
   curl http://localhost:5000/health
   
   # Verify environment variables
   echo $MLFLOW_TRACKING_URI
   ```

2. **Model Loading Errors**:
   ```python
   # Check model registry
   client.search_model_versions("name='model_name'")
   
   # Verify model artifacts
   mlflow.artifacts.list_artifacts("runs/{run_id}")
   ```

3. **PyFunc Model Issues**:
   ```python
   # Test model loading
   from src.serving.mlflow_model import load_pyfunc_model
   model = load_pyfunc_model("models:/model_name/1")
   ```

### Getting Help

- Check MLflow logs: `mlflow server --help`
- Review MLflow documentation: https://mlflow.org/docs/
- Check our training logs for detailed error messages

This guide provides a comprehensive overview of using MLflow in our ML pipeline. For specific issues or advanced use cases, refer to the MLflow documentation or reach out to the ML team.
