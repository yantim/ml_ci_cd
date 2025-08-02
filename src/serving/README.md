# Code Generation Model API

FastAPI application for serving ML models with MLflow integration, providing code generation, review, and documentation capabilities.

## Features

- **Code Generation** (`/predict`): Generate code completions
- **Code Review** (`/review`): Get AI-powered code review suggestions
- **Docstring Generation** (`/doc`): Generate documentation for functions
- **Health Monitoring** (`/health`): Service health status
- **Metrics** (`/metrics`): Prometheus metrics for monitoring
- **Authentication**: API key-based security for production endpoints

## Environment Variables

### Model Configuration
- `MODEL_NAME`: MLflow model name (default: `code_model_fine_tuning_model`)
- `MODEL_STAGE`: MLflow model stage (default: `Production`)
- `LOCAL_MODEL_PATH`: Path to local model (optional)
- `MODEL_URI`: Fallback model URI (default: `models:/code_model_fine_tuning_model/latest`)

### Authentication
- `API_KEY`: API key for authentication (optional, disables auth if not set)

### Monitoring
- `ENABLE_METRICS`: Enable Prometheus metrics (default: enabled)

## API Endpoints

### Public Endpoints

#### GET `/`
Root endpoint with API information.

#### GET `/health`
Health check endpoint.
```json
{
  "status": "healthy",
  "model_loaded": true
}
```

#### POST `/predict`
Generate code completions.
```json
{
  "input": ["def fibonacci(n):"],
  "parameters": {
    "max_new_tokens": 256,
    "num_beams": 4
  }
}
```

### Authenticated Endpoints

#### POST `/review`
Get code review suggestions (requires API key).
```json
{
  "code": ["def fibonacci(n): return n if n <= 1 else fibonacci(n-1) + fibonacci(n-2)"],
  "language": "python",
  "review_type": "general",
  "parameters": {
    "max_new_tokens": 200
  }
}
```

Response:
```json
{
  "reviews": ["Consider adding type hints and memoization for better performance"],
  "severity": ["medium"],
  "status": "success"
}
```

#### POST `/doc`
Generate docstrings for functions (requires API key).
```json
{
  "functions": ["def fibonacci(n: int) -> int:"],
  "style": "google",
  "include_examples": true,
  "parameters": {
    "max_new_tokens": 300
  }
}
```

Response:
```json
{
  "docstrings": ["\"\"\"Calculate the nth Fibonacci number.\n\nArgs:\n    n: The position in the Fibonacci sequence.\n\nReturns:\n    The nth Fibonacci number.\n\nExample:\n    >>> fibonacci(5)\n    5\n\"\"\""],
  "status": "success"
}
```

### Monitoring

#### GET `/metrics`
Prometheus metrics endpoint.

## Authentication

For production use, set the `API_KEY` environment variable. Authenticated endpoints require the API key in the Authorization header:

```bash
curl -X POST "http://localhost:8000/review" \
  -H "Authorization: Bearer your-api-key" \
  -H "Content-Type: application/json" \
  -d '{"code": ["def test(): pass"]}'
```

## Running the Application

### Development
```bash
cd src/serving
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Production
```bash
cd src/serving
export API_KEY="your-secure-api-key"
export MODEL_STAGE="Production"
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Docker
```bash
docker build -t ml-api .
docker run -p 8000:8000 -e API_KEY="your-key" ml-api
```

## Model Loading Strategy

The application tries to load models in this order:
1. `models:/MODEL_NAME/Production` (if MODEL_NAME is set)
2. `models:/MODEL_NAME/latest` (fallback)
3. `LOCAL_MODEL_PATH` (if specified)
4. `MODEL_URI` (environment fallback)

## Monitoring and Metrics

The application exposes Prometheus metrics at `/metrics` including:
- Request count and latency
- Active requests
- HTTP status codes
- Custom model inference metrics

Access metrics with:
```bash
curl http://localhost:8000/metrics
```

## Testing

Run the test suite:
```bash
pytest tests/test_api.py -v
```

## API Documentation

Once running, access the interactive API documentation at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
