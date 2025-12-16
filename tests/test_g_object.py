"""
Unit tests for global variable (g) object.
"""

import pytest
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
    test_file = Path('/tmp/test_strategy_g.py')
    test_file.write_text(test_strategy_content)
    
    try:
        loader = StrategyLoader(str(test_file))
        functions = loader.load()
        
        # Check that g object exists in module
        assert hasattr(loader._module, 'g')
        assert loader._module.g is not None
        
        # Call initialize to set g values
        class MockContext:
            pass
        
        context = MockContext()
        functions['initialize'](context)
        
        # Verify g values were set
        assert loader._module.g.security == 'BTCUSDT'
        assert loader._module.g.ma_period == 20
        
    finally:
        # Clean up
        if test_file.exists():
            test_file.unlink()

