#!/usr/bin/env python3
"""
Data Drift Detection Lambda Function

This function compares current input embeddings with the training set to detect data drift.
It runs nightly as a scheduled Lambda function and sends alerts when drift is detected.
"""

import json
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List, Tuple

import boto3
import numpy as np
from scipy import stats
from sklearn.metrics.pairwise import cosine_similarity

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS services
s3_client = boto3.client('s3')
sns_client = boto3.client('sns')

# Configuration from environment variables
S3_BUCKET = os.environ['S3_BUCKET']
TRAINING_SET_S3_KEY = os.environ['TRAINING_SET_S3_KEY']
SNS_TOPIC_ARN = os.environ['SNS_TOPIC_ARN']
ENVIRONMENT = os.environ['ENVIRONMENT']

# Drift detection thresholds
DRIFT_THRESHOLD_KS = 0.05  # Kolmogorov-Smirnov test p-value threshold
DRIFT_THRESHOLD_COSINE = 0.1  # Cosine similarity threshold
DRIFT_THRESHOLD_MEAN_SHIFT = 0.2  # Mean shift threshold


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Main Lambda handler for data drift detection.
    
    Args:
        event: Lambda event data
        context: Lambda context
        
    Returns:
        Response with drift detection results
    """
    try:
        logger.info("Starting data drift detection")
        
        # Load training set embeddings
        training_embeddings = load_training_embeddings()
        logger.info(f"Loaded {len(training_embeddings)} training embeddings")
        
        # Load recent production embeddings (last 24 hours)
        recent_embeddings = load_recent_embeddings()
        logger.info(f"Loaded {len(recent_embeddings)} recent embeddings")
        
        if len(recent_embeddings) == 0:
            logger.warning("No recent embeddings found, skipping drift detection")
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'status': 'skipped',
                    'reason': 'No recent embeddings found'
                })
            }
        
        # Perform drift detection
        drift_results = detect_drift(training_embeddings, recent_embeddings)
        
        # Check if drift is detected
        drift_detected = (
            drift_results['ks_test_p_value'] < DRIFT_THRESHOLD_KS or
            drift_results['cosine_similarity_change'] > DRIFT_THRESHOLD_COSINE or
            drift_results['mean_shift_magnitude'] > DRIFT_THRESHOLD_MEAN_SHIFT
        )
        
        # Send alert if drift is detected
        if drift_detected:
            send_drift_alert(drift_results)
        
        # Store results
        store_drift_results(drift_results)
        
        logger.info(f"Data drift detection completed. Drift detected: {drift_detected}")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'status': 'completed',
                'drift_detected': drift_detected,
                'results': drift_results
            })
        }
        
    except Exception as e:
        logger.error(f"Error in data drift detection: {e}")
        
        # Send error alert
        send_error_alert(str(e))
        
        return {
            'statusCode': 500,
            'body': json.dumps({
                'status': 'error',
                'message': str(e)
            })
        }


def load_training_embeddings() -> np.ndarray:
    """Load training set embeddings from S3."""
    try:
        response = s3_client.get_object(Bucket=S3_BUCKET, Key=TRAINING_SET_S3_KEY)
        training_data = json.loads(response['Body'].read())
        return np.array(training_data['embeddings'])
    except Exception as e:
        logger.error(f"Error loading training embeddings: {e}")
        raise


def load_recent_embeddings() -> np.ndarray:
    """Load recent embeddings from the last 24 hours."""
    try:
        # Calculate date range for last 24 hours
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=1)
        
        # List objects in the embeddings folder for the date range
        prefix = f"production_embeddings/{start_date.strftime('%Y/%m/%d')}"
        
        response = s3_client.list_objects_v2(
            Bucket=S3_BUCKET,
            Prefix=prefix
        )
        
        embeddings = []
        
        # Load embeddings from each file
        for obj in response.get('Contents', []):
            obj_response = s3_client.get_object(Bucket=S3_BUCKET, Key=obj['Key'])
            data = json.loads(obj_response['Body'].read())
            embeddings.extend(data.get('embeddings', []))
        
        return np.array(embeddings) if embeddings else np.array([])
    
    except Exception as e:
        logger.error(f"Error loading recent embeddings: {e}")
        raise


def detect_drift(training_embeddings: np.ndarray, recent_embeddings: np.ndarray) -> Dict[str, Any]:
    """
    Detect data drift between training and recent embeddings.
    
    Args:
        training_embeddings: Training set embeddings
        recent_embeddings: Recent production embeddings
        
    Returns:
        Dictionary with drift detection results
    """
    results = {
        'timestamp': datetime.utcnow().isoformat(),
        'training_samples': len(training_embeddings),
        'recent_samples': len(recent_embeddings)
    }
    
    # Statistical tests on embedding dimensions
    ks_p_values = []
    for dim in range(min(training_embeddings.shape[1], recent_embeddings.shape[1])):
        ks_stat, p_value = stats.ks_2samp(
            training_embeddings[:, dim],
            recent_embeddings[:, dim]
        )
        ks_p_values.append(p_value)
    
    results['ks_test_p_value'] = min(ks_p_values)
    results['ks_test_mean_p_value'] = np.mean(ks_p_values)
    
    # Cosine similarity comparison
    training_centroid = np.mean(training_embeddings, axis=0)
    recent_centroid = np.mean(recent_embeddings, axis=0)
    
    # Reshape for cosine similarity calculation
    cosine_sim = cosine_similarity(
        training_centroid.reshape(1, -1),
        recent_centroid.reshape(1, -1)
    )[0, 0]
    
    results['cosine_similarity'] = float(cosine_sim)
    results['cosine_similarity_change'] = float(1 - cosine_sim)
    
    # Mean shift magnitude
    mean_shift = np.linalg.norm(training_centroid - recent_centroid)
    results['mean_shift_magnitude'] = float(mean_shift)
    
    # Distribution comparison metrics
    training_std = np.std(training_embeddings, axis=0)
    recent_std = np.std(recent_embeddings, axis=0)
    std_ratio = np.mean(recent_std / (training_std + 1e-8))
    
    results['std_deviation_ratio'] = float(std_ratio)
    
    return results


def send_drift_alert(drift_results: Dict[str, Any]) -> None:
    """Send drift detection alert via SNS."""
    try:
        message = {
            "alert_type": "data_drift_detected",
            "environment": ENVIRONMENT,
            "timestamp": drift_results['timestamp'],
            "summary": {
                "ks_test_p_value": drift_results['ks_test_p_value'],
                "cosine_similarity_change": drift_results['cosine_similarity_change'],
                "mean_shift_magnitude": drift_results['mean_shift_magnitude']
            },
            "recommendations": [
                "Review recent input data for anomalies",
                "Consider retraining the model if drift persists",
                "Check data preprocessing pipeline for changes"
            ]
        }
        
        sns_client.publish(
            TopicArn=SNS_TOPIC_ARN,
            Subject=f"[{ENVIRONMENT.upper()}] Data Drift Detected - ML Pipeline",
            Message=json.dumps(message, indent=2)
        )
        
        logger.info("Drift alert sent successfully")
        
    except Exception as e:
        logger.error(f"Error sending drift alert: {e}")


def send_error_alert(error_message: str) -> None:
    """Send error alert via SNS."""
    try:
        message = {
            "alert_type": "drift_detection_error",
            "environment": ENVIRONMENT,
            "timestamp": datetime.utcnow().isoformat(),
            "error": error_message
        }
        
        sns_client.publish(
            TopicArn=SNS_TOPIC_ARN,
            Subject=f"[{ENVIRONMENT.upper()}] Data Drift Detection Error - ML Pipeline",
            Message=json.dumps(message, indent=2)
        )
        
        logger.info("Error alert sent successfully")
        
    except Exception as e:
        logger.error(f"Error sending error alert: {e}")


def store_drift_results(drift_results: Dict[str, Any]) -> None:
    """Store drift detection results in S3 for historical tracking."""
    try:
        timestamp = datetime.utcnow()
        key = f"drift_results/{timestamp.strftime('%Y/%m/%d')}/{timestamp.strftime('%H%M%S')}_drift_results.json"
        
        s3_client.put_object(
            Bucket=S3_BUCKET,
            Key=key,
            Body=json.dumps(drift_results, indent=2),
            ContentType='application/json'
        )
        
        logger.info(f"Drift results stored at s3://{S3_BUCKET}/{key}")
        
    except Exception as e:
        logger.error(f"Error storing drift results: {e}")


if __name__ == "__main__":
    # For local testing
    test_event = {}
    test_context = None
    result = lambda_handler(test_event, test_context)
    print(json.dumps(result, indent=2))
