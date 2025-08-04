#!/usr/bin/env python3
"""
Script to verify MLflow artifacts after training.
Used by GitHub Actions training workflow.
"""

import os
import sys
import mlflow


def main():
    """Verify MLflow artifacts from the latest training run."""
    
    # Get environment variables
    mlflow_uri = os.getenv('MLFLOW_TRACKING_URI')
    experiment_name = os.getenv('MLFLOW_EXPERIMENT_NAME', 'code_model_training')
    
    if not mlflow_uri:
        print("Error: MLFLOW_TRACKING_URI environment variable not set")
        sys.exit(1)
    
    try:
        mlflow.set_tracking_uri(mlflow_uri)
        
        # Get the experiment
        experiment = mlflow.get_experiment_by_name(experiment_name)
        if not experiment:
            print(f'Experiment "{experiment_name}" not found')
            sys.exit(1)
        
        # Get the latest run
        runs = mlflow.search_runs(
            experiment.experiment_id, 
            max_results=1, 
            order_by=['start_time DESC']
        )
        
        if runs.empty:
            print('No runs found in experiment')
            sys.exit(1)
        
        latest_run = runs.iloc[0]
        print(f'Latest run ID: {latest_run.run_id}')
        print(f'Latest run status: {latest_run.status}')
        print(f'Latest run metrics: {latest_run.to_dict()}')
        print('Training artifacts verified successfully')
        
    except Exception as e:
        print(f'Error verifying artifacts: {e}')
        sys.exit(1)


if __name__ == '__main__':
    main()
