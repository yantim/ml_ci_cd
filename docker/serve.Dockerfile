# Stage 1: Builder stage for minimal runtime dependencies
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

# Install only minimal runtime dependencies (serving dependencies)
RUN poetry install --only=main --no-dev && \
    # Remove unnecessary packages for serving
    poetry run pip uninstall -y dvc && \
    rm -rf $POETRY_CACHE_DIR

# Stage 2: Runtime serving image
FROM python:3.10-slim as runtime

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/.venv/bin:$PATH"

# Install minimal runtime system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd --create-home --shell /bin/bash app
USER app
WORKDIR /home/app

# Copy virtual environment from builder stage
COPY --from=builder --chown=app:app /app/.venv /.venv

# Copy only serving source code
COPY --chown=app:app src/serving/ ./src/serving/
COPY --chown=app:app src/__init__.py ./src/__init__.py

# Create directories for models (can be mounted as volumes)
USER root
RUN mkdir -p /app/models /app/artifacts && \
    chown -R app:app /app/models /app/artifacts
USER app

# Set default environment variables
ENV MODEL_URI=models:/code_model_fine_tuning_model/latest \
    MLFLOW_TRACKING_URI=http://host.docker.internal:5000 \
    MODEL_PATH=/app/models \
    ARTIFACTS_PATH=/app/artifacts

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Default command to run uvicorn
CMD ["uvicorn", "src.serving.main:app", "--host", "0.0.0.0", "--port", "8000"]
