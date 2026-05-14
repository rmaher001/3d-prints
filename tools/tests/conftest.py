"""Shared pytest fixtures for tools/ tests."""
import sys
from pathlib import Path

# Allow tests to import the primitive modules without installing the package
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
