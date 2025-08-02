#!/usr/bin/env python3
"""
Model Deployment Script for HuggingFace Hub and AWS S3
"""

import argparse
import json
import logging
import os
import shutil
import tempfile
import tarfile
import pandas as pd
from typing import Dict, Optional

import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from huggingface_hub import HfApi, create_repo, upload_folder
from omegaconf import DictConfig, OmegaConf
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ModelDeployer:
    """Deploy fine-tuned models to HuggingFace Hub and AWS S3"""
    
    def __init__(self, config: DictConfig):
        self.config = config
        self.hf_api = HfApi()
        
    def deploy_to_huggingface_hub(self, model_path: str) -> bool:
        """Deploy model to HuggingFace Hub"""
        if not self.config.registry.huggingface.repo_id:
            logger.warning("HuggingFace repo_id not specified, skipping HF Hub deployment")
            return False
            
        logger.info(f"Deploying model to HuggingFace Hub: {self.config.registry.huggingface.repo_id}")
        
        try:
            # Get HF token from environment or config
            token = os.getenv("HF_TOKEN") or self.config.registry.huggingface.token
            if not token:
                logger.error("HuggingFace token not found. Set HF_TOKEN environment variable or provide in config")
                return False
            
            # Create repository if it doesn't exist
            try:
                create_repo(
                    repo_id=self.config.registry.huggingface.repo_id,
                    private=self.config.registry.huggingface.private,
                    token=token,
                    exist_ok=True,
                )
                logger.info(f"Repository {self.config.registry.huggingface.repo_id} created/verified")
            except Exception as e:
                logger.error(f"Failed to create repository: {e}")
                return False
            
            # Create model card
            model_card_content = self._create_model_card(model_path)
            model_card_path = os.path.join(model_path, "README.md")
            with open(model_card_path, 'w') as f:
                f.write(model_card_content)
            
            # Upload model to HuggingFace Hub
            upload_folder(
                folder_path=model_path,
                repo_id=self.config.registry.huggingface.repo_id,
                token=token,
                commit_message=f"Upload fine-tuned model - {self.config.model.name}",
            )
            
            logger.info(f"Model successfully deployed to HuggingFace Hub: https://huggingface.co/{self.config.registry.huggingface.repo_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to deploy to HuggingFace Hub: {e}")
            return False
    
    def deploy_to_s3(self, model_path: str) -> bool:
        """Deploy model to AWS S3"""
        if not self.config.registry.s3.bucket:
            logger.warning("S3 bucket not specified, skipping S3 deployment")
            return False
            
        logger.info(f"Deploying model to S3: s3://{self.config.registry.s3.bucket}/{self.config.registry.s3.key_prefix}")
        
        try:
            # Initialize S3 client
            s3_client = boto3.client('s3', region_name=self.config.registry.s3.region)
            
            # Create archive of model directory
            with tempfile.NamedTemporaryFile(suffix='.tar.gz', delete=False) as tmp_file:
                archive_path = tmp_file.name
                
            # Create tar archive
            import tarfile
            with tarfile.open(archive_path, 'w:gz') as tar:
                tar.add(model_path, arcname=os.path.basename(model_path))
            
            # Generate S3 key
            model_name = os.path.basename(model_path)
            s3_key = f"{self.config.registry.s3.key_prefix}/{model_name}.tar.gz"
            
            # Upload to S3
            s3_client.upload_file(
                archive_path,
                self.config.registry.s3.bucket,
                s3_key
            )
            
            # Clean up temporary file
            os.unlink(archive_path)
            
            logger.info(f"Model successfully deployed to S3: s3://{self.config.registry.s3.bucket}/{s3_key}")
            
            # Upload model metadata
            metadata = self._create_model_metadata(model_path)
            metadata_key = f"{self.config.registry.s3.key_prefix}/{model_name}_metadata.json"
            
            s3_client.put_object(
                Bucket=self.config.registry.s3.bucket,
                Key=metadata_key,
                Body=json.dumps(metadata, indent=2),
                ContentType='application/json'
            )
            
            logger.info(f"Model metadata uploaded to S3: s3://{self.config.registry.s3.bucket}/{metadata_key}")
            return True
            
        except NoCredentialsError:
            logger.error("AWS credentials not found. Configure AWS credentials.")
            return False
        except ClientError as e:
            logger.error(f"AWS S3 error: {e}")
            return False
        except Exception as e:
            logger.error(f"Failed to deploy to S3: {e}")
            return False
    
    def _create_model_card(self, model_path: str) -> str:
        """Create model card for HuggingFace Hub"""
        
        # Load training metrics if available
        metrics_path = os.path.join(model_path, "metrics.json")
        metrics_info = ""
        if os.path.exists(metrics_path):
            with open(metrics_path, 'r') as f:
                metrics = json.load(f)
                metrics_info = f"""
## Training Results

- **Training Loss**: {metrics.get('train_results', {}).get('training_loss', 'N/A')}
- **Test Loss**: {metrics.get('test_results', {}).get('eval_loss', 'N/A')}
- **Test Exact Match**: {metrics.get('test_results', {}).get('eval_exact_match', 'N/A')}
"""
        
        model_card = f"""
---
license: apache-2.0
base_model: {self.config.model.name}
tags:
- code
- fine-tuned
- {self.config.model.name.split('/')[-1]}
language:
- code
datasets:
- custom
pipeline_tag: text2text-generation
---

# Fine-tuned Code Model

This model is a fine-tuned version of [{self.config.model.name}](https://huggingface.co/{self.config.model.name}) on a custom code dataset.

## Model Details

- **Base Model**: {self.config.model.name}
- **Fine-tuning Method**: {'LoRA/PEFT' if self.config.peft.use_peft else 'Full Fine-tuning'}
- **Task**: Code generation and understanding

{metrics_info}

## Training Configuration

- **Learning Rate**: {self.config.training.learning_rate}
- **Batch Size**: {self.config.training.per_device_train_batch_size}
- **Epochs**: {self.config.training.num_train_epochs}
- **Max Length**: {self.config.data.max_length}

{'## LoRA Configuration' if self.config.peft.use_peft else ''}

{f'''- **LoRA Rank (r)**: {self.config.peft.r}
- **LoRA Alpha**: {self.config.peft.lora_alpha}
- **LoRA Dropout**: {self.config.peft.lora_dropout}
- **Target Modules**: {', '.join(self.config.peft.target_modules)}''' if self.config.peft.use_peft else ''}

## Intended Use

This model is intended for research and educational purposes in code generation and understanding tasks.

## Training Data

The model was fine-tuned on a custom dataset containing code samples and their corresponding documentation/comments.
"""
        
        return model_card
    
    def _create_model_metadata(self, model_path: str) -> Dict:
        """Create model metadata for S3"""
        
        # Load training metrics if available
        metrics_path = os.path.join(model_path, "metrics.json")
        metrics = {}
        if os.path.exists(metrics_path):
            with open(metrics_path, 'r') as f:
                metrics = json.load(f)
        
        from datetime import datetime
        metadata = {
            "model_info": {
                "base_model": self.config.model.name,
                "fine_tuning_method": "LoRA/PEFT" if self.config.peft.use_peft else "Full Fine-tuning",
                "task_type": "text2text-generation",
            },
            "training_config": {
                "learning_rate": self.config.training.learning_rate,
                "batch_size": self.config.training.per_device_train_batch_size,
                "num_epochs": self.config.training.num_train_epochs,
                "max_length": self.config.data.max_length,
            },
            "peft_config": {
                "use_peft": self.config.peft.use_peft,
                "r": self.config.peft.r if self.config.peft.use_peft else None,
                "lora_alpha": self.config.peft.lora_alpha if self.config.peft.use_peft else None,
                "lora_dropout": self.config.peft.lora_dropout if self.config.peft.use_peft else None,
                "target_modules": self.config.peft.target_modules if self.config.peft.use_peft else None,
            },
            "metrics": metrics,
            "deployment_info": {
                "deployment_date": str(datetime.now()),
                "s3_bucket": self.config.registry.s3.bucket,
                "s3_key_prefix": self.config.registry.s3.key_prefix,
            }
        }
        
        return metadata
    
    def deploy_model(self, model_path: str) -> Dict[str, bool]:
        """Deploy model to all configured registries"""
        logger.info(f"Starting model deployment from: {model_path}")
        
        if not os.path.exists(model_path):
            raise ValueError(f"Model path does not exist: {model_path}")
        
        results = {
            "huggingface_hub": False,
            "s3": False,
        }
        
        # Deploy to HuggingFace Hub
        if self.config.registry.huggingface.repo_id:
            results["huggingface_hub"] = self.deploy_to_huggingface_hub(model_path)
        
        # Deploy to S3
        if self.config.registry.s3.bucket:
            results["s3"] = self.deploy_to_s3(model_path)
        
        # Summary
        successful_deployments = sum(results.values())
        total_deployments = len([k for k, v in results.items() if k in ['huggingface_hub', 's3'] and 
                               (getattr(self.config.registry.huggingface, 'repo_id', None) or 
                                getattr(self.config.registry.s3, 'bucket', None))])
        
        logger.info(f"Deployment completed: {successful_deployments}/{total_deployments} successful")
        
        return results


def load_config(config_path: str, overrides: Optional[list] = None) -> DictConfig:
    """Load configuration from YAML file with optional CLI overrides"""
    config = OmegaConf.load(config_path)
    
    if overrides:
        override_config = OmegaConf.from_dotlist(overrides)
        config = OmegaConf.merge(config, override_config)
    
    return config


def main():
    """Main deployment function"""
    parser = argparse.ArgumentParser(description="Deploy fine-tuned model to registries")
    parser.add_argument(
        "--config",
        type=str,
        default="src/training/config.yaml",
        help="Path to configuration file",
    )
    parser.add_argument(
        "--model-path",
        type=str,
        required=True,
        help="Path to the fine-tuned model directory",
    )
    parser.add_argument(
        "--overrides",
        nargs="*",
        help="Configuration overrides in key=value format",
    )
    
    args = parser.parse_args()
    
    # Load configuration
    config = load_config(args.config, args.overrides)
    
    # Initialize deployer
    deployer = ModelDeployer(config)
    
    # Deploy model
    results = deployer.deploy_model(args.model_path)
    
    # Print results
    print("\n=== Deployment Results ===")
    for registry, success in results.items():
        status = "✅ Success" if success else "❌ Failed"
        print(f"{registry}: {status}")
    
    return results


if __name__ == "__main__":
    main()
