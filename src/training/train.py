#!/usr/bin/env python3
"""
Code Model Fine-tuning Script with HuggingFace Trainer, LoRA/PEFT, and MLflow Integration
"""

import argparse
import json
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import mlflow
import mlflow.pytorch
import mlflow.pyfunc
import torch
import transformers
from datasets import Dataset
from omegaconf import DictConfig, OmegaConf
from peft import (
    LoraConfig,
    TaskType,
    get_peft_model,
    prepare_model_for_kbit_training,
)
from sklearn.metrics import accuracy_score, f1_score
from transformers import (
    AutoModelForSeq2SeqLM,
    AutoTokenizer,
    DataCollatorForSeq2Seq,
    EarlyStoppingCallback,
    Seq2SeqTrainer,
    Seq2SeqTrainingArguments,
    set_seed,
)

# Import MLflow PyFunc wrapper
try:
    from src.serving.mlflow_model import save_model_as_pyfunc
except ImportError:
    # Fallback for when running from different directory
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
    from src.serving.mlflow_model import save_model_as_pyfunc

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CodeModelTrainer:
    """HuggingFace Trainer wrapper for code model fine-tuning with LoRA/PEFT"""
    
    def __init__(self, config: DictConfig):
        self.config = config
        self.tokenizer = None
        self.model = None
        self.train_dataset = None
        self.val_dataset = None
        self.test_dataset = None
        
        # Set random seed for reproducibility
        set_seed(config.seed)
        
        # Setup logging
        log_level = getattr(logging, config.logging.level.upper())
        logging.basicConfig(
            level=log_level,
            format=config.logging.format,
        )
        
    def load_tokenizer_and_model(self):
        """Load tokenizer and model"""
        logger.info(f"Loading tokenizer and model: {self.config.model.name}")
        
        # Load tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(
            self.config.model.name,
            cache_dir=self.config.model.cache_dir,
            trust_remote_code=self.config.model.trust_remote_code,
        )
        
        # Add special tokens if needed
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
            
        # Load model
        self.model = AutoModelForSeq2SeqLM.from_pretrained(
            self.config.model.name,
            cache_dir=self.config.model.cache_dir,
            trust_remote_code=self.config.model.trust_remote_code,
            torch_dtype=torch.float16 if self.config.training.fp16 else torch.float32,
        )
        
        # Resize token embeddings if needed
        self.model.resize_token_embeddings(len(self.tokenizer))
        
        logger.info(f"Model loaded with {self.model.num_parameters():,} parameters")
        
    def setup_peft(self):
        """Setup LoRA/PEFT configuration"""
        if not self.config.peft.use_peft:
            logger.info("PEFT disabled, using full fine-tuning")
            return
            
        logger.info("Setting up LoRA/PEFT configuration")
        
        # Prepare model for k-bit training if using quantization
        self.model = prepare_model_for_kbit_training(self.model)
        
        # LoRA configuration
        peft_config = LoraConfig(
            r=self.config.peft.r,
            lora_alpha=self.config.peft.lora_alpha,
            lora_dropout=self.config.peft.lora_dropout,
            target_modules=self.config.peft.target_modules,
            bias=self.config.peft.bias,
            task_type=TaskType.SEQ_2_SEQ_LM,
        )
        
        # Apply LoRA to model
        self.model = get_peft_model(self.model, peft_config)
        
        # Print trainable parameters
        trainable_params = sum(p.numel() for p in self.model.parameters() if p.requires_grad)
        all_params = sum(p.numel() for p in self.model.parameters())
        
        logger.info(f"Trainable parameters: {trainable_params:,}")
        logger.info(f"All parameters: {all_params:,}")
        logger.info(f"Trainable percentage: {100 * trainable_params / all_params:.2f}%")
        
    def load_datasets(self):
        """Load and preprocess datasets"""
        logger.info("Loading datasets...")
        
        # Load datasets
        with open(self.config.data.train_path, 'r') as f:
            train_data = json.load(f)
        with open(self.config.data.val_path, 'r') as f:
            val_data = json.load(f)
        with open(self.config.data.test_path, 'r') as f:
            test_data = json.load(f)
            
        logger.info(f"Loaded {len(train_data)} train, {len(val_data)} val, {len(test_data)} test samples")
        
        # Preprocess data function
        def preprocess_function(example):
            # Convert input tokens back to text if needed
            if isinstance(example['input'], list):
                # Join tokens back to text
                input_text = ' '.join(example['input'])
            else:
                input_text = example['input']
                
            if isinstance(example['output'], list):
                if len(example['output']) > 0 and isinstance(example['output'][0], str):
                    # Multiple outputs (like review comments)
                    target_text = ' '.join(example['output'])
                else:
                    # Single output that's tokenized
                    target_text = ' '.join(example['output'])
            else:
                target_text = example['output']
            
            # Tokenize inputs
            model_inputs = self.tokenizer(
                input_text,
                max_length=self.config.data.max_length,
                padding=self.config.data.padding,
                truncation=self.config.data.truncation,
            )
            
            # Tokenize targets
            labels = self.tokenizer(
                target_text,
                max_length=self.config.data.max_length,
                padding=self.config.data.padding,
                truncation=self.config.data.truncation,
            )
            
            model_inputs["labels"] = labels["input_ids"]
            return model_inputs
            
        # Convert to HuggingFace datasets and preprocess
        self.train_dataset = Dataset.from_list(train_data)
        self.val_dataset = Dataset.from_list(val_data)
        self.test_dataset = Dataset.from_list(test_data)
        
        self.train_dataset = self.train_dataset.map(
            preprocess_function,
            batched=False,
            remove_columns=self.train_dataset.column_names,
        )
        
        self.val_dataset = self.val_dataset.map(
            preprocess_function,
            batched=False,
            remove_columns=self.val_dataset.column_names,
        )
        
        self.test_dataset = self.test_dataset.map(
            preprocess_function,
            batched=False,
            remove_columns=self.test_dataset.column_names,
        )
        
        logger.info("Datasets preprocessed successfully")
        
    def compute_metrics(self, eval_pred):
        """Compute metrics for evaluation"""
        predictions, labels = eval_pred
        
        # Convert to torch tensor if needed
        if not isinstance(labels, torch.Tensor):
            labels = torch.tensor(labels)
        if not isinstance(predictions, torch.Tensor):
            predictions = torch.tensor(predictions)
        
        # Decode predictions and labels
        decoded_preds = self.tokenizer.batch_decode(predictions, skip_special_tokens=True)
        
        # Replace -100 in labels as we can't decode them
        labels_cleaned = torch.where(labels != -100, labels, self.tokenizer.pad_token_id)
        decoded_labels = self.tokenizer.batch_decode(labels_cleaned, skip_special_tokens=True)
        
        # Simple metrics (you can add more sophisticated ones)
        # For now, we'll compute BLEU-like score using exact match
        exact_matches = sum(1 for pred, label in zip(decoded_preds, decoded_labels) if pred.strip() == label.strip())
        exact_match_score = exact_matches / len(decoded_preds)
        
        return {
            "exact_match": exact_match_score,
        }
        
    def train(self):
        """Train the model"""
        logger.info("Starting training...")
        
        # Create output directory
        os.makedirs(self.config.training.output_dir, exist_ok=True)
        
        # Training arguments
        training_args = Seq2SeqTrainingArguments(
            output_dir=self.config.training.output_dir,
            num_train_epochs=self.config.training.num_train_epochs,
            per_device_train_batch_size=self.config.training.per_device_train_batch_size,
            per_device_eval_batch_size=self.config.training.per_device_eval_batch_size,
            gradient_accumulation_steps=self.config.training.gradient_accumulation_steps,
            learning_rate=self.config.training.learning_rate,
            weight_decay=self.config.training.weight_decay,
            warmup_steps=self.config.training.warmup_steps,
            logging_steps=self.config.training.logging_steps,
            eval_steps=self.config.training.eval_steps,
            save_steps=self.config.training.save_steps,
            eval_strategy=self.config.training.evaluation_strategy,
            save_strategy=self.config.training.save_strategy,
            load_best_model_at_end=self.config.training.load_best_model_at_end,
            metric_for_best_model=self.config.training.metric_for_best_model,
            greater_is_better=self.config.training.greater_is_better,
            remove_unused_columns=self.config.training.remove_unused_columns,
            dataloader_num_workers=self.config.training.dataloader_num_workers,
            fp16=self.config.training.fp16,
            gradient_checkpointing=self.config.training.gradient_checkpointing,
            save_total_limit=self.config.training.save_total_limit,
            predict_with_generate=True,
            generation_max_length=self.config.generation.max_new_tokens,
            generation_num_beams=self.config.generation.num_beams,
        )
        
        # Data collator
        data_collator = DataCollatorForSeq2Seq(
            tokenizer=self.tokenizer,
            model=self.model,
            padding=True,
        )
        
        # Initialize trainer
        trainer = Seq2SeqTrainer(
            model=self.model,
            args=training_args,
            train_dataset=self.train_dataset,
            eval_dataset=self.val_dataset,
            tokenizer=self.tokenizer,
            data_collator=data_collator,
            compute_metrics=self.compute_metrics,
            callbacks=[EarlyStoppingCallback(early_stopping_patience=3)],
        )
        
        # Train the model
        train_result = trainer.train()
        
        # Save the final model
        trainer.save_model()
        trainer.save_state()
        
        return trainer, train_result
        
    def evaluate_model(self, trainer):
        """Evaluate model on test set"""
        logger.info("Evaluating model on test set...")
        
        # Evaluate on test set
        test_results = trainer.evaluate(eval_dataset=self.test_dataset)
        
        logger.info(f"Test results: {test_results}")
        return test_results
        
    def generate_examples(self, num_examples: int = 5) -> List[Dict]:
        """Generate examples using the fine-tuned model"""
        logger.info(f"Generating {num_examples} examples...")
        
        examples = []
        test_samples = self.test_dataset.select(range(min(num_examples, len(self.test_dataset))))
        
        # Set model to evaluation mode
        self.model.eval()
        
        for i, sample in enumerate(test_samples):
            try:
                # Get input and move to same device as model
                input_ids = torch.tensor(sample['input_ids']).unsqueeze(0)
                if next(self.model.parameters()).device != torch.device('cpu'):
                    input_ids = input_ids.to(next(self.model.parameters()).device)
                
                # Generate
                with torch.no_grad():
                    generated_ids = self.model.generate(
                        input_ids,
                        max_new_tokens=min(self.config.generation.max_new_tokens, 50),
                        num_beams=self.config.generation.num_beams,
                        do_sample=self.config.generation.do_sample,
                        early_stopping=self.config.generation.early_stopping,
                        pad_token_id=self.tokenizer.pad_token_id,
                    )
                
                # Decode
                input_text = self.tokenizer.decode(sample['input_ids'], skip_special_tokens=True)
                generated_text = self.tokenizer.decode(generated_ids[0], skip_special_tokens=True)
                target_text = self.tokenizer.decode(sample['labels'], skip_special_tokens=True)
                
                examples.append({
                    "example_id": i,
                    "input": input_text,
                    "generated": generated_text,
                    "target": target_text,
                })
            except Exception as e:
                logger.warning(f"Failed to generate example {i}: {e}")
                # Add a placeholder example
                examples.append({
                    "example_id": i,
                    "input": self.tokenizer.decode(sample['input_ids'], skip_special_tokens=True),
                    "generated": "[Generation failed]",
                    "target": self.tokenizer.decode(sample['labels'], skip_special_tokens=True),
                })
            
        return examples
        
    def run_training_pipeline(self):
        """Run the complete training pipeline with MLflow tracking"""
        
        # Initialize MLflow
        mlflow.set_tracking_uri(self.config.mlflow.tracking_uri)
        mlflow.set_experiment(self.config.mlflow.experiment_name)
        
        # Start MLflow run
        run_name = self.config.mlflow.run_name or f"code_model_training_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        with mlflow.start_run(run_name=run_name) as run:
            logger.info(f"Started MLflow run: {run.info.run_id}")
            
            # Log configuration
            mlflow.log_params({
                "model_name": self.config.model.name,
                "use_peft": self.config.peft.use_peft,
                "lora_r": self.config.peft.r if self.config.peft.use_peft else None,
                "learning_rate": self.config.training.learning_rate,
                "batch_size": self.config.training.per_device_train_batch_size,
                "num_epochs": self.config.training.num_train_epochs,
                "max_length": self.config.data.max_length,
            })
            
            try:
                # Load tokenizer and model
                self.load_tokenizer_and_model()
                
                # Setup PEFT
                self.setup_peft()
                
                # Load datasets
                self.load_datasets()
                
                # Train model
                trainer, train_result = self.train()
                
                # Log training metrics
                mlflow.log_metrics({
                    "train_loss": train_result.training_loss,
                    "train_steps": train_result.global_step,
                })
                
                # Evaluate model
                test_results = self.evaluate_model(trainer)
                
                # Log evaluation metrics
                mlflow.log_metrics({
                    f"test_{k}": v for k, v in test_results.items()
                    if isinstance(v, (int, float))
                })
                
                # Generate examples
                examples = self.generate_examples()
                
                # Save metrics and examples
                metrics_file = os.path.join(self.config.training.output_dir, "metrics.json")
                examples_file = os.path.join(self.config.training.output_dir, "examples.json")
                
                with open(metrics_file, 'w') as f:
                    json.dump({
                        "train_results": {
                            "training_loss": train_result.training_loss,
                            "global_step": train_result.global_step,
                        },
                        "test_results": test_results,
                    }, f, indent=2)
                    
                with open(examples_file, 'w') as f:
                    json.dump(examples, f, indent=2)
                
                # Log artifacts
                mlflow.log_artifacts(self.config.training.output_dir)
                
                # Log model if enabled
                if self.config.mlflow.log_model:
                    # Save as PyTorch model (traditional)
                    mlflow.pytorch.log_model(
                        self.model,
                        "pytorch_model",
                        registered_model_name=f"{self.config.mlflow.experiment_name}_pytorch_model"
                    )
                    
                    # Save as MLflow PyFunc for easy serving
                    pyfunc_model_path = os.path.join(self.config.training.output_dir, "mlflow_pyfunc")
                    registered_model_name = f"{self.config.mlflow.experiment_name}_model"
                    
                    save_model_as_pyfunc(
                        model=self.model,
                        tokenizer=self.tokenizer,
                        model_path=self.config.training.output_dir,
                        mlflow_model_path=pyfunc_model_path,
                        generation_config={
                            "max_new_tokens": self.config.generation.max_new_tokens,
                            "num_beams": self.config.generation.num_beams,
                            "do_sample": self.config.generation.do_sample,
                            "early_stopping": self.config.generation.early_stopping,
                            "pad_token_id": self.tokenizer.pad_token_id or self.tokenizer.eos_token_id
                        },
                        registered_model_name=registered_model_name,
                        metadata={
                            "base_model": self.config.model.name,
                            "use_peft": self.config.peft.use_peft,
                            "training_loss": train_result.training_loss,
                            "test_results": test_results
                        }
                    )
                    
                    # Log the PyFunc model to MLflow
                    mlflow.pyfunc.log_model(
                        "pyfunc_model",
                        python_model_path=pyfunc_model_path
                    )
                
                logger.info("Training pipeline completed successfully!")
                
                return {
                    "model": self.model,
                    "tokenizer": self.tokenizer,
                    "trainer": trainer,
                    "metrics": test_results,
                    "examples": examples,
                }
                
            except Exception as e:
                logger.error(f"Training failed: {str(e)}")
                mlflow.log_param("status", "failed")
                mlflow.log_param("error", str(e))
                raise


def load_config(config_path: str, overrides: Optional[List[str]] = None) -> DictConfig:
    """Load configuration from YAML file with optional CLI overrides"""
    config = OmegaConf.load(config_path)
    
    if overrides:
        override_config = OmegaConf.from_dotlist(overrides)
        config = OmegaConf.merge(config, override_config)
    
    return config


def main():
    """Main training function"""
    parser = argparse.ArgumentParser(description="Train code model with LoRA/PEFT")
    parser.add_argument(
        "--config",
        type=str,
        default="src/training/config.yaml",
        help="Path to configuration file",
    )
    parser.add_argument(
        "--overrides",
        nargs="*",
        help="Configuration overrides in key=value format",
    )
    
    args = parser.parse_args()
    
    # Load configuration
    config = load_config(args.config, args.overrides)
    
    # Initialize trainer
    trainer = CodeModelTrainer(config)
    
    # Run training pipeline
    results = trainer.run_training_pipeline()
    
    logger.info("Training completed successfully!")
    return results


if __name__ == "__main__":
    main()
