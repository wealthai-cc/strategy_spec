"""
Global variable object for strategy state storage.

Provides a global variable object `g` compatible with JoinQuant's global variable support.
Each strategy file gets its own independent `g` object.
"""

from types import SimpleNamespace


def create_g_object() -> SimpleNamespace:
    """
    Create a new global variable object.
    
    Returns:
        A SimpleNamespace object that can be used to store strategy-level state
    """
    return SimpleNamespace()

