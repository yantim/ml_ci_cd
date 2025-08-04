#!/usr/bin/env python3
"""
Script to get and validate MLflow model from Model Registry.
Used by GitHub Actions deploy workflow.
"""

import os
import sys
import mlflow
from mlflow.tracking import MlflowClient


def main():
    """Get model from MLflow Model Registry and set GitHub Actions outputs."""
    
    # Set MLflow tracking URI
    mlflow_uri = os.getenv('MLFLOW_TRACKING_URI')
    if not mlflow_uri:
        print("Error: MLFLOW_TRACKING_URI environment variable not set")
        sys.exit(1)
    
    mlflow.set_tracking_uri(mlflow_uri)
    client = MlflowClient()
    
    model_name = os.getenv('MODEL_NAME', 'code_model_fine_tuning_model')
    target_env = os.getenv('TARGET_ENVIRONMENT', 'staging')
    model_version = os.getenv('MODEL_VERSION', '')
    
    try:
        if model_version:
            # Use specific version
            mv = client.get_model_version(model_name, model_version)
            print(f'Using specific model version: {mv.version}')
        else:
            # Get latest model in the target stage
            stage = 'Production' if target_env == 'production' else 'Staging'
            mvs = client.get_latest_versions(model_name, stages=[stage])
            if not mvs:
                print(f'No model found in {stage} stage')
                sys.exit(1)
            mv = mvs[0]
            print(f'Using latest model in {stage} stage: version {mv.version}')
        
        model_uri = f'models:/{model_name}/{mv.version}'
        
        # Validate model metadata
        if mv.status != 'READY':
            print(f'Model version {mv.version} is not ready: {mv.status}')
            sys.exit(1)
        
        print(f'Model URI: {model_uri}')
        print(f'Model version: {mv.version}')
        print(f'Model stage: {mv.current_stage}')
        
        # Set outputs for next job (GitHub Actions format)
        # Using newer GITHUB_OUTPUT format
        github_output = os.getenv('GITHUB_OUTPUT')
        if github_output:
            with open(github_output, 'a') as f:
                f.write(f'model_version={mv.version}\n')
                f.write(f'model_uri={model_uri}\n')
        else:
            # Fallback to legacy format for local testing
            print(f'::set-output name=model_version::{mv.version}')
            print(f'::set-output name=model_uri::{model_uri}')
        
    except Exception as e:
        print(f'Error getting model: {e}')
        sys.exit(1)


if __name__ == '__main__':
    main()
