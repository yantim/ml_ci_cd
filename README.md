# ML CI/CD Pipeline Project

This project demonstrates a complete ML CI/CD pipeline with modern tools and practices.

## Project Structure

```
ml_ci_cd/
├── data/                   # Data storage and management
├── src/                    # Source code
│   ├── training/          # Model training code
│   ├── serving/           # Model serving code
│   └── utils/             # Utility functions
├── infra/                 # Infrastructure as code
├── tests/                 # Test suite
├── docker/                # Docker configurations
└── .github/workflows/     # CI/CD workflows
```

## Tech Stack

- **ML Framework**: PyTorch, Transformers
- **Experiment Tracking**: MLflow
- **Data Versioning**: DVC
- **Model Serving**: FastAPI, Uvicorn
- **Cloud**: AWS (boto3)
- **Code Quality**: Black, isort, pre-commit
- **Testing**: pytest
- **Infrastructure**: Terraform

## Getting Started

1. Install dependencies:
   ```bash
   poetry install
   ```

2. Set up pre-commit hooks:
   ```bash
   poetry run pre-commit install
   ```

3. Run tests:
   ```bash
   poetry run pytest
   ```

## Development

This project uses Poetry for dependency management and includes:
- Automated code formatting with Black
- Import sorting with isort  
- Pre-commit hooks for code quality
- Comprehensive test suite

## Infrastructure

The `infra/` directory contains Terraform configurations for cloud deployment.

## CI/CD

GitHub Actions workflows handle:
- Code quality checks
- Testing
- Model training
- Deployment
