"""
Unit tests for global variable (g) object.
"""

import pytest
import tempfile
from types import SimpleNamespace
from typing import Any
from engine.compat.g import create_g_object
from engine.loader import StrategyLoader
from pathlib import Path


def test_create_g_object():
    """Test creating a g object."""
    g = create_g_object()
    assert g is not None
    
    # Test storing values
    g.security = 'BTCUSDT'
    assert g.security == 'BTCUSDT'
    
    g.ma_period = 20
    assert g.ma_period == 20


def test_g_object_isolation():
    """Test that different g objects are isolated."""
    g1 = create_g_object()
    g2 = create_g_object()
    
    g1.value = 'value1'
    g2.value = 'value2'
    
    assert g1.value == 'value1'
    assert g2.value == 'value2'
    assert g1.value != g2.value


def test_g_object_injection():
    """Test that g object is injected into strategy module."""
    # Create a simple test strategy file
    test_strategy_content = '''
def initialize(context):
    g.security = 'BTCUSDT'
    g.ma_period = 20

def handle_bar(context, bar):
    pass
'''
    
    # Write test strategy to temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as temp_file:
        temp_file.write(test_strategy_content)
        test_file = Path(temp_file.name)
    
    try:
        loader = StrategyLoader(str(test_file))
        functions = loader.load()
        
        # Check that g object exists in module
        assert loader._module is not None, "Module should be loaded after calling load()"
        assert hasattr(loader._module, 'g'), "Module should have g object injected"
        assert loader._module.g is not None, "g object should not be None"
        
        # Call initialize to set g values
        class MockContext:
            pass
        
        context = MockContext()
        
        # Verify initialize function exists and is callable
        initialize_func = functions.get('initialize')
        assert initialize_func is not None, "initialize function should be loaded"
        assert callable(initialize_func), "initialize should be callable"
        
        # Call initialize function
        initialize_func(context)
        
        # Verify g values were set
        # We already verified loader._module is not None above
        module = loader._module
        g_obj: SimpleNamespace = module.g
        assert g_obj.security == 'BTCUSDT'
        assert g_obj.ma_period == 20
        
    finally:
        # Clean up
        if test_file.exists():
            test_file.unlink()

