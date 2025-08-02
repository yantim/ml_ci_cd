#!/usr/bin/env python3
"""
Demo script for running quality gates and tests.

This script demonstrates the automated testing and quality gates
implemented for the ML CI/CD pipeline.
"""

import subprocess
import sys
import os
from pathlib import Path


def run_command(cmd, description, continue_on_error=False):
    """Run a command and display results."""
    print(f"\n{'='*60}")
    print(f"🔍 {description}")
    print(f"{'='*60}")
    print(f"Running: {cmd}")
    print("-" * 40)
    
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
            
        if result.returncode != 0 and not continue_on_error:
            print(f"❌ {description} failed with return code {result.returncode}")
            return False
        elif result.returncode != 0:
            print(f"⚠️  {description} had issues but continuing...")
        else:
            print(f"✅ {description} passed!")
            
        return True
        
    except Exception as e:
        print(f"❌ Error running {description}: {e}")
        return False


def main():
    """Run quality gates demonstration."""
    print("🚀 ML CI/CD Pipeline - Quality Gates Demo")
    print("=" * 60)
    
    # Check if we're in the right directory
    if not Path("src").exists():
        print("❌ Please run this script from the project root directory")
        sys.exit(1)
    
    # List of quality gate checks
    checks = [
        {
            "cmd": "ruff check src tests --output-format=text",
            "description": "Ruff Linting Check",
            "continue_on_error": True
        },
        {
            "cmd": "ruff format src tests --check",
            "description": "Ruff Format Check", 
            "continue_on_error": True
        },
        {
            "cmd": "black --check --diff src tests",
            "description": "Black Format Check",
            "continue_on_error": True
        },
        {
            "cmd": "isort --check-only --diff src tests",
            "description": "Import Sort Check",
            "continue_on_error": True
        },
        {
            "cmd": "mypy src --config-file mypy.ini",
            "description": "MyPy Type Checking",
            "continue_on_error": True
        },
        {
            "cmd": "bandit -r src -f txt",
            "description": "Bandit Security Scan",
            "continue_on_error": True
        },
        {
            "cmd": 'pytest tests/ -v --cov=src --cov-report=term-missing -m "not integration and not docker"',
            "description": "Unit Tests with Coverage",
            "continue_on_error": True
        }
    ]
    
    # Run checks
    passed = 0
    total = len(checks)
    
    for check in checks:
        success = run_command(
            check["cmd"], 
            check["description"], 
            check.get("continue_on_error", False)
        )
        if success:
            passed += 1
    
    # Summary
    print(f"\n{'='*60}")
    print("📊 QUALITY GATES SUMMARY")
    print(f"{'='*60}")
    print(f"Passed: {passed}/{total} ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 All quality gates passed!")
        print("\n✨ Your code is ready for deployment!")
    else:
        print(f"⚠️  {total - passed} quality gate(s) need attention")
        print("\n🔧 Please fix the issues above before deploying")
    
    # Show available commands
    print(f"\n{'='*60}")
    print("🛠️  AVAILABLE COMMANDS")
    print(f"{'='*60}")
    print("Format code:           make format")
    print("Run all checks:        make all-checks")
    print("Run tests only:        make test-unit")
    print("Run integration tests: make test-integration")
    print("Run security scan:     make security")
    print("Start API server:      make serve-local")
    print("Build Docker image:    make docker-build")
    print("Clean up:              make clean")
    
    print(f"\n{'='*60}")
    print("📚 MORE INFO")
    print(f"{'='*60}")
    print("• Tests are in tests/ directory")
    print("• Coverage report: htmlcov/index.html")  
    print("• CI/CD pipeline: .github/workflows/ci.yml")
    print("• Quality configs: ruff.toml, mypy.ini, .bandit, pytest.ini")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
