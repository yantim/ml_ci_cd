# Stage 1: Build dependencies and install packages
FROM python:3.10-slim as builder

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies needed for building
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install poetry==2.1.3

# Configure Poetry
ENV POETRY_NO_INTERACTION=1 \
    POETRY_VENV_IN_PROJECT=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

# Set working directory
WORKDIR /app

# Copy dependency files
COPY poetry.lock pyproject.toml ./

# Install dependencies (production + training)
RUN poetry install --only=main && rm -rf $POETRY_CACHE_DIR

# Stage 2: Runtime image
FROM python:3.10-slim as runtime

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/.venv/bin:$PATH"

# Install minimal runtime dependencies
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd --create-home --shell /bin/bash app
USER app
WORKDIR /home/app

# Copy virtual environment from builder stage
COPY --from=builder --chown=app:app /app/.venv /.venv

# Copy source code
COPY --chown=app:app src/ ./src/
COPY --chown=app:app config/ ./config/
COPY --chown=app:app scripts/train.sh ./scripts/train.sh

# Make sure the training script is executable
USER root
RUN chmod +x ./scripts/train.sh
USER app

# Set default environment variables
ENV MLFLOW_TRACKING_URI=http://host.docker.internal:5000 \
    EXPERIMENT_NAME=code_model_training \
    MODEL_NAME=code_model_fine_tuning_model

# Default entrypoint
ENTRYPOINT ["./scripts/train.sh"]
