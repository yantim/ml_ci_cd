#!/usr/bin/env python3
"""
MLflow PyFunc Model Wrapper for Code Generation Models

This module provides a custom MLflow PyFunc wrapper for HuggingFace
code generation models, enabling easy serving and deployment.
"""

import json
import logging
import os
from typing import Any, Dict, List, Optional, Union

import mlflow
import mlflow.pyfunc
import numpy as np
import pandas as pd
import torch
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
from peft import PeftModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CodeGenerationModel(mlflow.pyfunc.PythonModel):
    """MLflow PyFunc wrapper for code generation models"""
    
    def __init__(self):
        self.model = None
        self.tokenizer = None
        self.generation_config = None
        self.device = None
    
    def load_context(self, context):
        """Load model and tokenizer from MLflow context"""
        logger.info("Loading model from MLflow context...")
        
        # Get device
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        logger.info(f"Using device: {self.device}")
        
        # Load model configuration
        config_path = os.path.join(context.artifacts["model"], "config.json")
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                model_config = json.load(f)
        else:
            model_config = {}
        
        # Load tokenizer
        tokenizer_path = context.artifacts["model"]
        self.tokenizer = AutoTokenizer.from_pretrained(tokenizer_path)
        logger.info("Tokenizer loaded successfully")
        
        # Load model (handle both regular and PEFT models)
        model_path = context.artifacts["model"]
        
        # Check if this is a PEFT model
        peft_config_path = os.path.join(model_path, "adapter_config.json")
        if os.path.exists(peft_config_path):
            # Load PEFT model
            logger.info("Loading PEFT model...")
            with open(peft_config_path, 'r') as f:
                peft_config = json.load(f)
            
            base_model_name = peft_config.get("base_model_name_or_path")
            if base_model_name:
                # Load base model
                base_model = AutoModelForSeq2SeqLM.from_pretrained(
                    base_model_name,
                    torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32
                )
                # Load PEFT adapter
                self.model = PeftModel.from_pretrained(base_model, model_path)
            else:
                # Fallback to loading as regular model
                self.model = AutoModelForSeq2SeqLM.from_pretrained(
                    model_path,
                    torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32
                )
        else:
            # Load regular model
            logger.info("Loading regular model...")
            self.model = AutoModelForSeq2SeqLM.from_pretrained(
                model_path,
                torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32
            )
        
        self.model.to(self.device)
        self.model.eval()
        logger.info("Model loaded successfully")
        
        # Load generation configuration
        generation_config_path = os.path.join(context.artifacts["model"], "generation_config.json")
        if os.path.exists(generation_config_path):
            with open(generation_config_path, 'r') as f:
                self.generation_config = json.load(f)
        else:
            # Default generation config
            self.generation_config = {
                "max_new_tokens": 256,
                "num_beams": 4,
                "do_sample": False,
                "early_stopping": True,
                "pad_token_id": self.tokenizer.pad_token_id or self.tokenizer.eos_token_id
            }
        
        logger.info(f"Generation config: {self.generation_config}")
    
    def predict(self, context, model_input, params: Optional[Dict[str, Any]] = None):
        """
        Generate code predictions
        
        Args:
            context: MLflow context
            model_input: Input data (pandas DataFrame or dict/list)
            params: Optional parameters for generation
            
        Returns:
            List of generated code strings
        """
        # Handle different input formats
        if isinstance(model_input, pd.DataFrame):
            if "input" in model_input.columns:
                inputs = model_input["input"].tolist()
            elif "prompt" in model_input.columns:
                inputs = model_input["prompt"].tolist()
            else:
                # Assume first column is the input
                inputs = model_input.iloc[:, 0].tolist()
        elif isinstance(model_input, dict):
            inputs = model_input.get("input", model_input.get("prompt", model_input.get("instances", [])))
        elif isinstance(model_input, list):
            inputs = model_input
        else:
            raise ValueError(f"Unsupported input format: {type(model_input)}")
        
        # Ensure inputs is a list of strings
        if not isinstance(inputs, list):
            inputs = [inputs]
        
        # Update generation config with params if provided
        generation_config = self.generation_config.copy()
        if params:
            generation_config.update(params)
        
        predictions = []
        
        for input_text in inputs:
            try:
                # Tokenize input
                input_ids = self.tokenizer.encode(
                    input_text,
                    return_tensors="pt",
                    max_length=512,
                    truncation=True,
                    padding=True
                ).to(self.device)
                
                # Generate
                with torch.no_grad():
                    generated_ids = self.model.generate(
                        input_ids,
                        **generation_config
                    )
                
                # Decode generated text
                generated_text = self.tokenizer.decode(
                    generated_ids[0],
                    skip_special_tokens=True
                )
                
                # Remove input text from generated text if it's included
                if generated_text.startswith(input_text):
                    generated_text = generated_text[len(input_text):].strip()
                
                predictions.append(generated_text)
                
            except Exception as e:
                logger.error(f"Error generating prediction for input '{input_text[:50]}...': {e}")
                predictions.append(f"[Error: {str(e)}]")
        
        return predictions


def save_model_as_pyfunc(
    model,
    tokenizer,
    model_path: str,
    mlflow_model_path: str,
    generation_config: Optional[Dict] = None,
    registered_model_name: Optional[str] = None,
    metadata: Optional[Dict] = None
):
    """
    Save a HuggingFace model as MLflow PyFunc
    
    Args:
        model: HuggingFace model
        tokenizer: HuggingFace tokenizer
        model_path: Path where the model is saved
        mlflow_model_path: MLflow model artifact path
        generation_config: Generation configuration
        registered_model_name: Name for model registry
        metadata: Additional metadata
    """
    logger.info(f"Saving model as MLflow PyFunc to {mlflow_model_path}")
    
    # Save generation config
    if generation_config:
        generation_config_path = os.path.join(model_path, "generation_config.json")
        with open(generation_config_path, 'w') as f:
            json.dump(generation_config, f, indent=2)
    
    # Create artifacts dictionary
    artifacts = {"model": model_path}
    
    # Create conda environment
    conda_env = {
        "channels": ["defaults", "conda-forge", "pytorch", "huggingface"],
        "dependencies": [
            "python=3.10",
            "pip",
            {
                "pip": [
                    "mlflow>=2.0.0",
                    "torch>=2.0.0",
                    "transformers>=4.30.0",
                    "peft>=0.5.0",
                    "accelerate>=0.21.0",
                    "pandas>=1.5.0",
                    "numpy>=1.21.0",
                ]
            }
        ]
    }
    
    # Create model signature
    signature = mlflow.models.infer_signature(
        model_input=pd.DataFrame({"input": ["def fibonacci(n):"]}),
        model_output=["def fibonacci(n):\n    if n <= 1:\n        return n\n    return fibonacci(n-1) + fibonacci(n-2)"]
    )
    
    # Additional metadata
    model_metadata = {
        "model_type": "code_generation",
        "framework": "transformers",
        "task": "text2text-generation",
    }
    if metadata:
        model_metadata.update(metadata)
    
    # Save as MLflow PyFunc
    mlflow.pyfunc.save_model(
        path=mlflow_model_path,
        python_model=CodeGenerationModel(),
        artifacts=artifacts,
        conda_env=conda_env,
        signature=signature,
        metadata=model_metadata
    )
    
    logger.info(f"Model saved as MLflow PyFunc at {mlflow_model_path}")
    
    # Register model if requested
    if registered_model_name:
        logger.info(f"Registering model as {registered_model_name}")
        mlflow.register_model(
            model_uri=mlflow_model_path,
            name=registered_model_name
        )
        logger.info(f"Model registered as {registered_model_name}")


def load_pyfunc_model(model_uri: str) -> mlflow.pyfunc.PyFuncModel:
    """Load MLflow PyFunc model for inference"""
    logger.info(f"Loading MLflow PyFunc model from {model_uri}")
    model = mlflow.pyfunc.load_model(model_uri)
    logger.info("Model loaded successfully")
    return model


def test_pyfunc_model(model_uri: str, test_inputs: List[str]):
    """Test MLflow PyFunc model with sample inputs"""
    logger.info("Testing MLflow PyFunc model...")
    
    # Load model
    model = load_pyfunc_model(model_uri)
    
    # Test with different input formats
    test_cases = [
        # DataFrame input
        pd.DataFrame({"input": test_inputs}),
        # Dictionary input
        {"input": test_inputs},
        # List input
        test_inputs,
    ]
    
    for i, test_input in enumerate(test_cases):
        logger.info(f"Testing input format {i + 1}: {type(test_input)}")
        try:
            predictions = model.predict(test_input)
            logger.info(f"Predictions: {predictions}")
        except Exception as e:
            logger.error(f"Error with input format {i + 1}: {e}")
    
    logger.info("PyFunc model testing completed")


if __name__ == "__main__":
    # Example usage
    test_inputs = [
        "def fibonacci(n):",
        "// Function to calculate factorial",
        "def quicksort(arr):",
    ]
    
    # Test the model (replace with actual model URI)
    model_uri = "models:/code_model_fine_tuning_model/1"
    try:
        test_pyfunc_model(model_uri, test_inputs)
    except Exception as e:
        logger.error(f"Testing failed: {e}")
        logger.info("Make sure to train and register a model first")
