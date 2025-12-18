"""
Pytest configuration and fixtures.
"""

import pytest
import sys
from pathlib import Path

# Add engine to path
engine_path = Path(__file__).parent.parent
sys.path.insert(0, str(engine_path))



