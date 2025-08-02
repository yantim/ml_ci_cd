#!/usr/bin/env python3
"""
FastAPI app entry point for serving.
Re-exports the app from main.py for uvicorn.
"""

from .main import app

__all__ = ["app"]
