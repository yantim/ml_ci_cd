#!/usr/bin/env python3
"""
Standalone MLflow Tracking Server with SQLite Backend

This script sets up and runs a standalone MLflow tracking server
using SQLite as the backend database for local development.
"""

import argparse
import logging
import os
import subprocess
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def setup_mlflow_directories(base_dir: str = "./mlflow"):
    """Setup MLflow directories for artifacts and database"""
    base_path = Path(base_dir)
    
    # Create directories
    artifacts_dir = base_path / "artifacts"
    db_dir = base_path / "db"
    
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    db_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Created MLflow directories at {base_path}")
    
    return {
        "artifacts_uri": artifacts_dir.resolve().as_uri(),
        "db_path": (db_dir / "mlflow.db").resolve(),
        "base_path": base_path.resolve()
    }


def create_mlflow_config(config_dir: str = "./config"):
    """Create MLflow configuration files"""
    config_path = Path(config_dir)
    config_path.mkdir(parents=True, exist_ok=True)
    
    # Create .env file for local development
    env_file = config_path / ".env.mlflow"
    env_content = """# MLflow Configuration for Local Development
MLFLOW_TRACKING_URI=http://localhost:5000
MLFLOW_DEFAULT_ARTIFACT_ROOT=file://./mlflow/artifacts
MLFLOW_BACKEND_STORE_URI=sqlite:///./mlflow/db/mlflow.db

# For production - uncomment and configure
# MLFLOW_TRACKING_URI=http://your-mlflow-server:5000
# MLFLOW_BACKEND_STORE_URI=postgresql://user:password@host:port/dbname
# MLFLOW_DEFAULT_ARTIFACT_ROOT=s3://your-mlflow-bucket/artifacts
"""
    
    with open(env_file, 'w') as f:
        f.write(env_content)
    
    logger.info(f"Created MLflow environment config at {env_file}")
    
    # Create production config template
    prod_env_file = config_path / ".env.mlflow.prod"
    prod_content = """# MLflow Configuration for Production
# Copy this file and configure for your production environment

# MLflow tracking server URL
MLFLOW_TRACKING_URI=http://your-mlflow-server:5000

# PostgreSQL backend for production
MLFLOW_BACKEND_STORE_URI=postgresql://username:password@hostname:port/database

# S3 artifact storage for production
MLFLOW_DEFAULT_ARTIFACT_ROOT=s3://your-mlflow-bucket/artifacts

# AWS credentials (if using S3)
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_DEFAULT_REGION=us-east-1

# Database migration settings
MLFLOW_SQLALCHEMY_UPGRADE=true
"""
    
    with open(prod_env_file, 'w') as f:
        f.write(prod_content)
    
    logger.info(f"Created MLflow production config template at {prod_env_file}")
    
    return env_file, prod_env_file


def start_mlflow_server(
    host: str = "localhost",
    port: int = 5000,
    backend_store_uri: str = None,
    default_artifact_root: str = None,
    serve_artifacts: bool = True
):
    """Start MLflow tracking server"""
    
    # Setup directories if not provided
    if not backend_store_uri or not default_artifact_root:
        dirs = setup_mlflow_directories()
        backend_store_uri = backend_store_uri or f"sqlite:///{dirs['db_path']}"
        default_artifact_root = default_artifact_root or dirs['artifacts_uri']
    
    # Build MLflow server command
    cmd = [
        "mlflow", "server",
        "--host", host,
        "--port", str(port),
        "--backend-store-uri", backend_store_uri,
        "--default-artifact-root", default_artifact_root,
    ]
    
    if serve_artifacts:
        cmd.append("--serve-artifacts")
    
    logger.info(f"Starting MLflow server with command: {' '.join(cmd)}")
    logger.info(f"Backend store: {backend_store_uri}")
    logger.info(f"Artifact root: {default_artifact_root}")
    logger.info(f"Server will be available at: http://{host}:{port}")
    
    try:
        # Start the server
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        logger.info("MLflow server stopped by user")
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to start MLflow server: {e}")
        sys.exit(1)


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Start MLflow tracking server")
    parser.add_argument(
        "--host",
        default="localhost",
        help="Host to bind the server to (default: localhost)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=5000,
        help="Port to bind the server to (default: 5000)"
    )
    parser.add_argument(
        "--backend-store-uri",
        help="Backend store URI (default: SQLite in ./mlflow/db/mlflow.db)"
    )
    parser.add_argument(
        "--default-artifact-root",
        help="Default artifact root (default: ./mlflow/artifacts)"
    )
    parser.add_argument(
        "--no-serve-artifacts",
        action="store_true",
        help="Don't serve artifacts (default: serve artifacts)"
    )
    parser.add_argument(
        "--setup-only",
        action="store_true",
        help="Only setup directories and config files, don't start server"
    )
    
    args = parser.parse_args()
    
    # Setup directories and config
    setup_mlflow_directories()
    create_mlflow_config()
    
    if args.setup_only:
        logger.info("Setup completed. Use --setup-only=false to start the server.")
        return
    
    # Start server
    start_mlflow_server(
        host=args.host,
        port=args.port,
        backend_store_uri=args.backend_store_uri,
        default_artifact_root=args.default_artifact_root,
        serve_artifacts=not args.no_serve_artifacts
    )


if __name__ == "__main__":
    main()
