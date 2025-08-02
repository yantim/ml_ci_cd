# Model Fine-tuning Pipeline

This document describes the implemented model fine-tuning pipeline with HuggingFace Trainer, LoRA/PEFT, and MLflow integration.

## ✅ Implementation Summary

### Step 3: Model fine-tuning pipeline (PyTorch/Transformers) - COMPLETED

The following components have been successfully implemented:

#### 🎯 Core Features
- **HuggingFace Trainer wrapper** in `src/training/train.py` for CodeT5/CodeBERT
- **LoRA/PEFT integration** for memory-efficient fine-tuning
- **YAML/CLI configuration** support via Hydra/OmegaConf
- **MLflow tracking** with experiment logging, metrics, and artifacts
- **Model deployment** script for HuggingFace Hub & AWS S3

#### 📁 Files Created
- `src/training/train.py` - Main training script with MLflow integration
- `src/training/deploy_model.py` - Model deployment to HF Hub and S3
- `src/training/config.yaml` - Training configuration file
- `setup_env.sh` - Environment setup script
- Updated `requirements.txt` with all necessary dependencies

#### 🧪 Testing Results
- ✅ Training pipeline runs successfully
- ✅ Model fine-tuning completes with metrics generation
- ✅ MLflow experiment tracking works
- ✅ Model artifacts saved correctly
- ✅ Deployment script functional
- ✅ Basic tests pass

## 🚀 Usage

### 1. Environment Setup
```bash
./setup_env.sh
source venv/bin/activate
```

### 2. Training a Model
```bash
# Basic training with default config
python src/training/train.py --config src/training/config.yaml

# Training with custom parameters
python src/training/train.py --config src/training/config.yaml \
  --overrides \
  training.num_train_epochs=3 \
  training.per_device_train_batch_size=8 \
  peft.use_peft=true \
  model.name=Salesforce/codet5-base
```

### 3. Deploying a Model
```bash
# Deploy to configured registries
python src/training/deploy_model.py \
  --model-path models/fine_tuned \
  --config src/training/config.yaml \
  --overrides \
  registry.huggingface.repo_id=your-username/your-model-name \
  registry.s3.bucket=your-s3-bucket
```

### 4. Running Tests
```bash
python -m pytest tests/ -v
```

## 📊 Training Pipeline Features

### Model Support
- **CodeT5**: `Salesforce/codet5-base`, `Salesforce/codet5-small`
- **CodeBERT**: `microsoft/codebert-base`
- **T5**: `t5-small`, `t5-base` (for testing)

### Memory Optimization
- **LoRA/PEFT**: Low-rank adaptation for efficient fine-tuning
- **Gradient Checkpointing**: Reduce memory usage during training
- **Mixed Precision**: FP16 training support (when GPU available)

### MLflow Integration
- **Experiment Tracking**: Automatic experiment and run management
- **Parameter Logging**: All training hyperparameters logged
- **Metrics Logging**: Training loss, evaluation metrics, custom metrics
- **Artifact Logging**: Model files, metrics JSON, generated examples
- **Model Registry**: Optional model registration in MLflow

### Configuration Management
- **YAML Configuration**: Structured config file with all parameters
- **CLI Overrides**: Runtime parameter modification via command line
- **Hydra Integration**: Advanced configuration management

### Model Deployment
- **HuggingFace Hub**: Automatic model card generation and upload
- **AWS S3**: Model archiving with metadata
- **Model Registry**: Multi-platform model management

## 📈 Outputs

### Training Artifacts
- `models/fine_tuned/model.safetensors` - Fine-tuned model weights
- `models/fine_tuned/config.json` - Model configuration
- `models/fine_tuned/tokenizer.json` - Tokenizer files
- `models/fine_tuned/metrics.json` - Training and evaluation metrics
- `models/fine_tuned/examples.json` - Generated examples
- `models/fine_tuned/trainer_state.json` - Training state

### MLflow Tracking
- `mlruns/` - MLflow experiment tracking database
- Logged parameters, metrics, and artifacts for each run
- Model artifacts and evaluation results

## ⚙️ Configuration Options

### Key Configuration Sections
- `model`: Model selection and caching options
- `data`: Dataset paths and preprocessing parameters  
- `peft`: LoRA/PEFT configuration
- `training`: Training hyperparameters and strategies
- `generation`: Text generation parameters
- `mlflow`: Experiment tracking configuration
- `registry`: Model deployment settings

### Sample Configuration
```yaml
model:
  name: "Salesforce/codet5-base"
  cache_dir: "./models/cache"

peft:
  use_peft: true
  r: 16
  lora_alpha: 32
  lora_dropout: 0.1

training:
  num_train_epochs: 3
  per_device_train_batch_size: 4
  learning_rate: 5e-4
  fp16: true
  gradient_checkpointing: true
```

## 🔄 CI/CD Integration

The pipeline is designed to integrate with existing CI/CD workflows:
- Environment setup via `setup_env.sh`
- Containerizable with Docker
- DVC pipeline integration ready
- GitHub Actions compatible

## 📋 Next Steps

To complete the full ML pipeline, consider implementing:
1. Advanced evaluation metrics (BLEU, CodeBLEU, etc.)
2. Automated hyperparameter tuning
3. Multi-GPU training support
4. Production serving endpoints
5. Model monitoring and drift detection
