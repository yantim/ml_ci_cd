# Multi-stage Docker build for ML model serving
FROM python:3.10-slim as base

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install poetry

# Copy poetry files
COPY pyproject.toml poetry.lock ./

# Configure poetry to not create virtual environment
RUN poetry config virtualenvs.create false

# Install dependencies
RUN poetry install --no-dev

# Copy source code
COPY src/ ./src/

# Expose port for FastAPI
EXPOSE 8000

# Run the application
CMD ["uvicorn", "src.serving.main:app", "--host", "0.0.0.0", "--port", "8000"]
