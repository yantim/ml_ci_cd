#!/bin/bash

# ML CI/CD Project Environment Setup Script

echo "🔧 Setting up ML CI/CD project environment..."

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3.9 -m venv venv
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "📈 Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📋 Installing dependencies..."
pip install -r requirements.txt

# Install additional dev dependencies
echo "🛠️ Installing development dependencies..."
pip install pytest pytest-cov

echo "✅ Environment setup complete!"
echo ""
echo "To activate the environment, run:"
echo "    source venv/bin/activate"
echo ""
echo "To run training:"
echo "    python src/training/train.py --config src/training/config.yaml"
echo ""
echo "To run tests:"
echo "    python -m pytest tests/ -v"
echo ""
echo "To deploy model:"
echo "    python src/training/deploy_model.py --model-path models/fine_tuned --config src/training/config.yaml"
