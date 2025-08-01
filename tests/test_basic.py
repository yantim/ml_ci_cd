"""Basic tests to verify project setup."""

import pytest


def test_project_structure():
    """Test that the basic project structure is in place."""
    import os
    
    # Check that main directories exist
    assert os.path.exists("src")
    assert os.path.exists("src/training")
    assert os.path.exists("src/serving")
    assert os.path.exists("src/utils")
    assert os.path.exists("tests")
    assert os.path.exists("data")
    assert os.path.exists("infra")
    assert os.path.exists("docker")
    assert os.path.exists(".github/workflows")


def test_imports():
    """Test that basic imports work."""
    import src
    import src.training
    import src.serving
    import src.utils
    
    # Should not raise any errors
    assert True


def test_basic_math():
    """Basic test to ensure pytest is working."""
    assert 2 + 2 == 4
    assert 10 / 2 == 5.0
