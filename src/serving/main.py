#!/usr/bin/env python3
"""
FastAPI application for ML model serving.
"""

import asyncio
import logging
import os
from contextlib import asynccontextmanager
from typing import List, Dict, Any, Optional

import mlflow
from fastapi import FastAPI, HTTPException, Depends, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from prometheus_fastapi_instrumentator import Instrumentator
from pydantic import BaseModel, Field

from .mlflow_model import load_pyfunc_model

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Code Generation Model API",
    description="API for serving code generation models with MLflow",
    version="1.0.0"
)

# Initialize Prometheus metrics
instrumentator = Instrumentator(
    should_group_status_codes=False,
    should_ignore_untemplated=True,
    should_respect_env_var=True,
    should_instrument_requests_inprogress=True,
    env_var_name="ENABLE_METRICS",
    inprogress_name="inprogress",
    inprogress_labels=True,
)
instrumentator.instrument(app).expose(app)

# Global model instance
model = None

# Authentication setup
security = HTTPBearer(auto_error=False)
API_KEY = os.getenv("API_KEY")


def get_api_key(credentials: Optional[HTTPAuthorizationCredentials] = Security(security)):
    """Validate API key for authentication"""
    # Skip authentication in development if no API key is set
    if not API_KEY:
        return None
        
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if credentials.credentials != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return credentials.credentials


class PredictionRequest(BaseModel):
    """Request model for predictions"""
    input: List[str] = Field(..., description="List of code prompts to generate completions for")
    parameters: Optional[Dict[str, Any]] = Field(
        default=None, 
        description="Optional generation parameters (max_new_tokens, num_beams, etc.)"
    )


class CodeReviewRequest(BaseModel):
    """Request model for code review"""
    code: List[str] = Field(..., description="List of code snippets to review")
    language: Optional[str] = Field(default="python", description="Programming language")
    review_type: Optional[str] = Field(default="general", description="Type of review (general, security, performance)")
    parameters: Optional[Dict[str, Any]] = Field(default=None, description="Optional generation parameters")


class DocstringRequest(BaseModel):
    """Request model for docstring generation"""
    functions: List[str] = Field(..., description="List of function signatures to generate docstrings for")
    style: Optional[str] = Field(default="google", description="Docstring style (google, numpy, sphinx)")
    include_examples: Optional[bool] = Field(default=True, description="Include usage examples")
    parameters: Optional[Dict[str, Any]] = Field(default=None, description="Optional generation parameters")


class PredictionResponse(BaseModel):
    """Response model for predictions"""
    predictions: List[str] = Field(..., description="Generated code completions")
    status: str = Field(default="success", description="Response status")


class CodeReviewResponse(BaseModel):
    """Response model for code review"""
    reviews: List[str] = Field(..., description="Code review suggestions")
    severity: List[str] = Field(default_factory=list, description="Severity levels for each suggestion")
    status: str = Field(default="success", description="Response status")


class DocstringResponse(BaseModel):
    """Response model for docstring generation"""
    docstrings: List[str] = Field(..., description="Generated docstrings")
    status: str = Field(default="success", description="Response status")


class HealthResponse(BaseModel):
    """Response model for health check"""
    status: str = Field(..., description="Service health status")
    model_loaded: bool = Field(..., description="Whether model is loaded")


@app.on_event("startup")
async def startup_event():
    """Load model on startup"""
    global model
    
    logger.info("Starting up FastAPI application...")
    
    # Try to load the latest "Production" model from MLflow first
    model_name = os.getenv("MODEL_NAME", "code_model_fine_tuning_model")
    model_stage = os.getenv("MODEL_STAGE", "Production")
    local_model_path = os.getenv("LOCAL_MODEL_PATH")
    
    model_uris_to_try = []
    
    # Add Production model URI if model name is specified
    if model_name:
        production_uri = f"models:/{model_name}/{model_stage}"
        model_uris_to_try.append(production_uri)
        
        # Also try latest as fallback
        latest_uri = f"models:/{model_name}/latest"
        model_uris_to_try.append(latest_uri)
    
    # Add local model path if specified
    if local_model_path:
        model_uris_to_try.append(local_model_path)
    
    # Fallback to environment variable or default
    fallback_uri = os.getenv("MODEL_URI", "models:/code_model_fine_tuning_model/latest")
    if fallback_uri not in model_uris_to_try:
        model_uris_to_try.append(fallback_uri)
    
    model = None
    for model_uri in model_uris_to_try:
        try:
            logger.info(f"Attempting to load model from URI: {model_uri}")
            model = load_pyfunc_model(model_uri)
            logger.info(f"Model loaded successfully from: {model_uri}")
            break
        except Exception as e:
            logger.warning(f"Failed to load model from {model_uri}: {e}")
            continue
    
    if model is None:
        logger.error("Failed to load model from any URI. Service will run in degraded mode.")
        # In production, you might want to fail fast here
        # raise Exception("No model could be loaded")


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy" if model is not None else "degraded",
        model_loaded=model is not None
    )


@app.post("/predict", response_model=PredictionResponse)
async def predict(request: PredictionRequest):
    """
    Generate code predictions
    
    Args:
        request: Prediction request containing input prompts and optional parameters
        
    Returns:
        Generated code completions
    """
    if model is None:
        raise HTTPException(
            status_code=503, 
            detail="Model not loaded. Service is not ready."
        )
    
    try:
        logger.info(f"Received prediction request with {len(request.input)} inputs")
        
        # Use async prediction to avoid blocking
        predictions = await async_predict(request.input, request.parameters)
        
        logger.info(f"Generated {len(predictions)} predictions")
        
        return PredictionResponse(predictions=predictions)
        
    except Exception as e:
        logger.error(f"Prediction failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Prediction failed: {str(e)}"
        )


async def async_predict(inputs: List[str], params: Optional[Dict[str, Any]] = None) -> List[str]:
    """Async wrapper for model prediction to avoid blocking"""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, lambda: model.predict(inputs, params=params))


@app.post("/review", response_model=CodeReviewResponse)
async def review_code(request: CodeReviewRequest, api_key: str = Depends(get_api_key)):
    """
    Provide code review suggestions based on input code.
    
    Args:
        request: Code review request with code snippets and review options
        
    Returns:
        Suggestions for code improvement with severity levels
    """
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    try:
        logger.info(f"Review request with {len(request.code)} code snippets")
        
        # Format prompts for code review
        review_prompts = []
        for code_snippet in request.code:
            prompt = f"Review this {request.language or 'code'} code for {request.review_type} issues:\n\n{code_snippet}\n\nProvide specific suggestions for improvement:"
            review_prompts.append(prompt)
        
        # Use async prediction
        reviews = await async_predict(review_prompts, request.parameters)
        
        # Generate mock severity levels (in real implementation, this would be part of model output)
        severity_levels = ["medium" for _ in reviews]  # Placeholder
        
        logger.info(f"Generated {len(reviews)} code reviews")
        
        return CodeReviewResponse(
            reviews=reviews, 
            severity=severity_levels,
            status="success"
        )
        
    except Exception as e:
        logger.error(f"Code review failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Code review failed: {str(e)}"
        )


@app.post("/doc", response_model=DocstringResponse)
async def generate_docstring(request: DocstringRequest, api_key: str = Depends(get_api_key)):
    """
    Generate docstring suggestions for functions.
    
    Args:
        request: Docstring generation request with function signatures and style options
        
    Returns:
        Generated docstrings in the requested style
    """
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    try:
        logger.info(f"Docstring request with {len(request.functions)} functions")
        
        # Format prompts for docstring generation
        docstring_prompts = []
        for function_sig in request.functions:
            examples_text = " with usage examples" if request.include_examples else ""
            prompt = f"Generate a {request.style} style docstring{examples_text} for this function:\n\n{function_sig}\n\nDocstring:"
            docstring_prompts.append(prompt)
        
        # Use async prediction
        docstrings = await async_predict(docstring_prompts, request.parameters)
        
        logger.info(f"Generated {len(docstrings)} docstrings")
        
        return DocstringResponse(
            docstrings=docstrings,
            status="success"
        )
        
    except Exception as e:
        logger.error(f"Docstring generation failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Docstring generation failed: {str(e)}"
        )


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Code Generation Model API",
        "version": "1.0.0",
        "endpoints": {
            "docs": "/docs",
            "health": "/health",
            "metrics": "/metrics",
            "predict": "/predict",
            "review": "/review (requires API key)",
            "doc": "/doc (requires API key)"
        },
        "authentication": "Bearer token required for /review and /doc endpoints" if API_KEY else "No authentication required (development mode)"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
