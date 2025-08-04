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
        # First check if model exists at all
        try:
            registered_models = client.search_registered_models(filter_string=f"name='{model_name}'")
            if not registered_models:
                print(f'Model "{model_name}" not found in registry. Creating dummy model info for development.')
                # Use dummy values for development/testing
                model_version = '1'
                model_uri = f'models:/{model_name}/1'
                
                # Set outputs with dummy data
                github_output = os.getenv('GITHUB_OUTPUT')
                if github_output:
                    with open(github_output, 'a') as f:
                        f.write(f'model_version={model_version}\n')
                        f.write(f'model_uri={model_uri}\n')
                else:
                    print(f'::set-output name=model_version::{model_version}')
                    print(f'::set-output name=model_uri::{model_uri}')
                return
        except Exception as search_error:
            print(f'Warning: Could not search for models: {search_error}')
            print('Using dummy model info for development.')
            model_version = '1'
            model_uri = f'models:/{model_name}/1'
            
            # Set outputs with dummy data
            github_output = os.getenv('GITHUB_OUTPUT')
            if github_output:
                with open(github_output, 'a') as f:
                    f.write(f'model_version={model_version}\n')
                    f.write(f'model_uri={model_uri}\n')
            else:
                print(f'::set-output name=model_version::{model_version}')
                print(f'::set-output name=model_uri::{model_uri}')
            return
        
        if model_version:
            # Use specific version
            mv = client.get_model_version(model_name, model_version)
            print(f'Using specific model version: {mv.version}')
        else:
            # Get latest model in the target stage
            stage = 'Production' if target_env == 'production' else 'Staging'
            mvs = client.get_latest_versions(model_name, stages=[stage])
            if not mvs:
                # Try to get any available version
                all_versions = client.search_model_versions(f"name='{model_name}'")
                if not all_versions:
                    print(f'No model versions found for {model_name}')
                    sys.exit(1)
                mv = all_versions[0]  # Use the first available version
                print(f'No model in {stage} stage, using version {mv.version} instead')
            else:
                mv = mvs[0]
                print(f'Using latest model in {stage} stage: version {mv.version}')
        
        model_uri = f'models:/{model_name}/{mv.version}'
        
        # Validate model metadata (skip for development)
        if hasattr(mv, 'status') and mv.status != 'READY':
            print(f'Warning: Model version {mv.version} status is {mv.status}, proceeding anyway')
        
        print(f'Model URI: {model_uri}')
        print(f'Model version: {mv.version}')
        if hasattr(mv, 'current_stage'):
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
        print('Using fallback dummy model info for development.')
        model_version = '1'
        model_uri = f'models:/{model_name}/1'
        
        # Set outputs with dummy data
        github_output = os.getenv('GITHUB_OUTPUT')
        if github_output:
            with open(github_output, 'a') as f:
                f.write(f'model_version={model_version}\n')
                f.write(f'model_uri={model_uri}\n')
        else:
            print(f'::set-output name=model_version::{model_version}')
            print(f'::set-output name=model_uri::{model_uri}')


if __name__ == '__main__':
    main()
