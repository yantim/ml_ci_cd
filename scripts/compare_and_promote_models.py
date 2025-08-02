#!/usr/bin/env python3
"""
MLflow Model Comparison and Promotion Script

This script helps compare different model runs and promote the best
performing model to different stages in the model registry.
"""

import argparse
import logging
import os
from typing import Dict, List, Optional

import mlflow
import pandas as pd
from mlflow.tracking import MlflowClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ModelComparator:
    """Compare and promote MLflow models"""
    
    def __init__(self, tracking_uri: Optional[str] = None):
        if tracking_uri:
            mlflow.set_tracking_uri(tracking_uri)
        
        self.client = MlflowClient()
        
    def compare_experiment_runs(
        self,
        experiment_name: str,
        metric_name: str = "test_eval_loss",
        top_k: int = 5,
        ascending: bool = True
    ) -> pd.DataFrame:
        """
        Compare runs within an experiment
        
        Args:
            experiment_name: Name of the experiment
            metric_name: Metric to sort by
            top_k: Number of top runs to return
            ascending: Sort order (True for ascending, False for descending)
            
        Returns:
            DataFrame with run comparison
        """
        logger.info(f"Comparing runs in experiment: {experiment_name}")
        
        # Get experiment
        try:
            experiment = self.client.get_experiment_by_name(experiment_name)
            if experiment is None:
                raise ValueError(f"Experiment '{experiment_name}' not found")
        except Exception as e:
            logger.error(f"Error getting experiment: {e}")
            return pd.DataFrame()
        
        # Search runs
        sort_order = "ASC" if ascending else "DESC"
        runs = self.client.search_runs(
            experiment_ids=[experiment.experiment_id],
            order_by=[f"metrics.{metric_name} {sort_order}"],
            max_results=top_k
        )
        
        if not runs:
            logger.warning(f"No runs found in experiment '{experiment_name}'")
            return pd.DataFrame()
        
        # Create comparison DataFrame
        comparison_data = []
        for run in runs:
            run_data = {
                "run_id": run.info.run_id,
                "run_name": run.data.tags.get("mlflow.runName", "N/A"),
                "status": run.info.status,
                "start_time": run.info.start_time,
                "duration_minutes": (run.info.end_time - run.info.start_time) / (1000 * 60) if run.info.end_time else None,
            }
            
            # Add metrics
            for metric, value in run.data.metrics.items():
                run_data[f"metric_{metric}"] = value
            
            # Add key parameters
            key_params = ["model_name", "learning_rate", "batch_size", "use_peft", "lora_r"]
            for param in key_params:
                run_data[f"param_{param}"] = run.data.params.get(param, "N/A")
            
            comparison_data.append(run_data)
        
        df = pd.DataFrame(comparison_data)
        logger.info(f"Found {len(df)} runs for comparison")
        
        return df
    
    def compare_model_versions(self, model_name: str) -> pd.DataFrame:
        """
        Compare different versions of a registered model
        
        Args:
            model_name: Name of the registered model
            
        Returns:
            DataFrame with model version comparison
        """
        logger.info(f"Comparing versions of model: {model_name}")
        
        try:
            model_versions = self.client.search_model_versions(f"name='{model_name}'")
        except Exception as e:
            logger.error(f"Error getting model versions: {e}")
            return pd.DataFrame()
        
        if not model_versions:
            logger.warning(f"No versions found for model '{model_name}'")
            return pd.DataFrame()
        
        # Create comparison DataFrame
        comparison_data = []
        for version in model_versions:
            try:
                run = self.client.get_run(version.run_id)
                
                version_data = {
                    "version": version.version,
                    "stage": version.current_stage,
                    "run_id": version.run_id,
                    "creation_timestamp": version.creation_timestamp,
                    "description": version.description or "N/A",
                }
                
                # Add metrics from the run
                for metric, value in run.data.metrics.items():
                    version_data[f"metric_{metric}"] = value
                
                # Add key parameters
                key_params = ["model_name", "learning_rate", "batch_size", "use_peft", "lora_r"]
                for param in key_params:
                    version_data[f"param_{param}"] = run.data.params.get(param, "N/A")
                
                comparison_data.append(version_data)
                
            except Exception as e:
                logger.warning(f"Error getting run data for version {version.version}: {e}")
                continue
        
        df = pd.DataFrame(comparison_data)
        logger.info(f"Found {len(df)} model versions for comparison")
        
        return df
    
    def promote_model(
        self,
        model_name: str,
        version: str,
        stage: str,
        description: Optional[str] = None
    ) -> bool:
        """
        Promote a model version to a specific stage
        
        Args:
            model_name: Name of the registered model
            version: Version to promote
            stage: Target stage (Staging, Production, Archived)
            description: Optional description for the promotion
            
        Returns:
            Success status
        """
        logger.info(f"Promoting model {model_name} version {version} to {stage}")
        
        try:
            # Transition model stage
            self.client.transition_model_version_stage(
                name=model_name,
                version=version,
                stage=stage
            )
            
            # Update description if provided
            if description:
                self.client.update_model_version(
                    name=model_name,
                    version=version,
                    description=description
                )
            
            logger.info(f"Successfully promoted model {model_name} version {version} to {stage}")
            return True
            
        except Exception as e:
            logger.error(f"Error promoting model: {e}")
            return False
    
    def find_best_model(
        self,
        experiment_name: str,
        metric_name: str = "test_eval_loss",
        minimize: bool = True
    ) -> Optional[str]:
        """
        Find the best performing model run in an experiment
        
        Args:
            experiment_name: Name of the experiment
            metric_name: Metric to optimize
            minimize: Whether to minimize the metric (True) or maximize (False)
            
        Returns:
            Run ID of the best model, or None if not found
        """
        logger.info(f"Finding best model in experiment: {experiment_name}")
        
        df = self.compare_experiment_runs(
            experiment_name=experiment_name,
            metric_name=metric_name,
            top_k=1,
            ascending=minimize
        )
        
        if df.empty:
            logger.warning("No runs found")
            return None
        
        best_run_id = df.iloc[0]["run_id"]
        best_metric_value = df.iloc[0][f"metric_{metric_name}"]
        
        logger.info(f"Best run: {best_run_id} with {metric_name}={best_metric_value}")
        return best_run_id
    
    def auto_promote_best_model(
        self,
        experiment_name: str,
        model_name: str,
        metric_name: str = "test_eval_loss",
        minimize: bool = True,
        target_stage: str = "Staging"
    ) -> bool:
        """
        Automatically find and promote the best model
        
        Args:
            experiment_name: Name of the experiment
            model_name: Name of the registered model
            metric_name: Metric to optimize
            minimize: Whether to minimize the metric
            target_stage: Stage to promote to
            
        Returns:
            Success status
        """
        logger.info(f"Auto-promoting best model from experiment: {experiment_name}")
        
        # Find best run
        best_run_id = self.find_best_model(
            experiment_name=experiment_name,
            metric_name=metric_name,
            minimize=minimize
        )
        
        if not best_run_id:
            logger.error("No best run found")
            return False
        
        # Find model version associated with this run
        try:
            model_versions = self.client.search_model_versions(f"name='{model_name}'")
            target_version = None
            
            for version in model_versions:
                if version.run_id == best_run_id:
                    target_version = version.version
                    break
            
            if not target_version:
                logger.error(f"No model version found for run {best_run_id}")
                return False
            
            # Get run details for description
            run = self.client.get_run(best_run_id)
            metric_value = run.data.metrics.get(metric_name, "N/A")
            
            description = f"Auto-promoted best model with {metric_name}={metric_value}"
            
            # Promote model
            return self.promote_model(
                model_name=model_name,
                version=target_version,
                stage=target_stage,
                description=description
            )
            
        except Exception as e:
            logger.error(f"Error in auto-promotion: {e}")
            return False


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Compare and promote MLflow models")
    parser.add_argument("--tracking-uri", help="MLflow tracking URI")
    parser.add_argument("--experiment-name", required=True, help="Experiment name")
    parser.add_argument("--model-name", help="Registered model name")
    parser.add_argument("--metric", default="test_eval_loss", help="Metric to compare")
    parser.add_argument("--top-k", type=int, default=5, help="Number of top runs to show")
    parser.add_argument("--minimize", action="store_true", help="Minimize metric (default: True for loss)")
    parser.add_argument("--maximize", action="store_true", help="Maximize metric")
    parser.add_argument(
        "--action", 
        choices=["compare", "promote", "auto-promote"], 
        default="compare",
        help="Action to perform"
    )
    parser.add_argument("--version", help="Model version to promote")
    parser.add_argument("--stage", choices=["Staging", "Production", "Archived"], help="Target stage")
    parser.add_argument("--description", help="Description for promotion")
    
    args = parser.parse_args()
    
    # Set up tracking URI
    if args.tracking_uri:
        os.environ["MLFLOW_TRACKING_URI"] = args.tracking_uri
    
    # Initialize comparator
    comparator = ModelComparator(args.tracking_uri)
    
    # Determine minimize/maximize
    minimize = not args.maximize if args.maximize else True
    
    if args.action == "compare":
        # Compare experiment runs
        logger.info("Comparing experiment runs...")
        df = comparator.compare_experiment_runs(
            experiment_name=args.experiment_name,
            metric_name=args.metric,
            top_k=args.top_k,
            ascending=minimize
        )
        
        if not df.empty:
            print("\n=== Top Runs Comparison ===")
            print(df.to_string(index=False))
            
            # Also compare model versions if model name provided
            if args.model_name:
                print("\n=== Model Versions Comparison ===")
                model_df = comparator.compare_model_versions(args.model_name)
                if not model_df.empty:
                    print(model_df.to_string(index=False))
        
    elif args.action == "promote":
        # Promote specific model version
        if not all([args.model_name, args.version, args.stage]):
            parser.error("--model-name, --version, and --stage are required for promotion")
        
        success = comparator.promote_model(
            model_name=args.model_name,
            version=args.version,
            stage=args.stage,
            description=args.description
        )
        
        if success:
            print(f"✅ Successfully promoted {args.model_name} v{args.version} to {args.stage}")
        else:
            print(f"❌ Failed to promote {args.model_name} v{args.version}")
    
    elif args.action == "auto-promote":
        # Auto-promote best model
        if not all([args.model_name, args.stage]):
            parser.error("--model-name and --stage are required for auto-promotion")
        
        success = comparator.auto_promote_best_model(
            experiment_name=args.experiment_name,
            model_name=args.model_name,
            metric_name=args.metric,
            minimize=minimize,
            target_stage=args.stage
        )
        
        if success:
            print(f"✅ Successfully auto-promoted best model to {args.stage}")
        else:
            print("❌ Failed to auto-promote model")


if __name__ == "__main__":
    main()
