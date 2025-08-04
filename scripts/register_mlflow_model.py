#!/usr/bin/env python3
"""
Script to register model in MLflow Model Registry after training.
Used by GitHub Actions training workflow.
"""

import os
import sys
import mlflow
from mlflow.tracking import MlflowClient


def main():
    """Register model in MLflow Model Registry."""
    
    # Get environment variables
    mlflow_uri = os.getenv('MLFLOW_TRACKING_URI')
    model_name = os.getenv('MODEL_NAME', 'code_model_fine_tuning_model')
    experiment_name = os.getenv('MLFLOW_EXPERIMENT_NAME', 'code_model_training')
    
    if not mlflow_uri:
        print("Error: MLFLOW_TRACKING_URI environment variable not set")
        sys.exit(1)
    
    try:
        mlflow.set_tracking_uri(mlflow_uri)
        client = MlflowClient()
        
        # Get the latest run
        experiment = mlflow.get_experiment_by_name(experiment_name)
        if not experiment:
            print(f'Experiment "{experiment_name}" not found')
            sys.exit(1)
        
        runs = mlflow.search_runs(
            experiment.experiment_id, 
            max_results=1, 
            order_by=['start_time DESC']
        )
        
        if runs.empty:
            print('No runs found to register')
            sys.exit(1)
        
        latest_run = runs.iloc[0]
        run_id = latest_run.run_id
        model_uri = f'runs:/{run_id}/model'
        
        # Register the model
        model_version = mlflow.register_model(
            model_uri=model_uri,
            name=model_name,
            tags={
                'commit_sha': os.getenv('GITHUB_SHA'),
                'branch': os.getenv('GITHUB_REF_NAME'),
                'workflow_run_id': os.getenv('GITHUB_RUN_ID'),
                'training_date': os.getenv('GITHUB_EVENT_HEAD_COMMIT_TIMESTAMP')
            }
        )
        print(f'Model registered successfully: {model_version.name} version {model_version.version}')
        
        # Transition to Staging
        client.transition_model_version_stage(
            name=model_name,
            version=model_version.version,
            stage='Staging'
        )
        print(f'Model version {model_version.version} transitioned to Staging')
        
    except Exception as e:
        print(f'Error registering model: {e}')
        sys.exit(1)


if __name__ == '__main__':
    main()
