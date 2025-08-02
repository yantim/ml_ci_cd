#!/bin/bash
set -e

echo "Starting training pipeline..."

# Set default values if not provided
EXPERIMENT_NAME=${EXPERIMENT_NAME:-"code_model_training"}
MODEL_NAME=${MODEL_NAME:-"code_model_fine_tuning_model"}
TRACKING_URI=${TRACKING_URI:-"http://host.docker.internal:5000"}

# Set MLflow tracking URI
export MLFLOW_TRACKING_URI=$TRACKING_URI

echo "MLflow Tracking URI: $MLFLOW_TRACKING_URI"
echo "Experiment Name: $EXPERIMENT_NAME"
echo "Model Name: $MODEL_NAME"

# Run the training pipeline
python -m src.training.train \
    --experiment-name "$EXPERIMENT_NAME" \
    --model-name "$MODEL_NAME" \
    "$@"

echo "Training completed successfully!"
