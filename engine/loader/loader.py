"""
Strategy loader for loading and validating Python strategy files.
"""

import importlib.util
import sys
from typing import Dict, Any, Optional, Callable
from pathlib import Path


class StrategyLoader:
    """
    Loads Python strategy files and extracts lifecycle functions.
    """
    
    REQUIRED_FUNCTION = "initialize"
    OPTIONAL_FUNCTIONS = [
        "before_trading",
        "handle_bar",
        "on_order",
        "on_risk_event",
    ]
    
    def __init__(self, strategy_path: str):
        """
        Initialize strategy loader.
        
        Args:
            strategy_path: Path to Python strategy file
        """
        self.strategy_path = Path(strategy_path)
        if not self.strategy_path.exists():
            raise FileNotFoundError(f"Strategy file not found: {strategy_path}")
        
        self._module = None
        self._functions: Dict[str, Optional[Callable]] = {}
    
    def load(self) -> Dict[str, Optional[Callable]]:
        """
        Load strategy file and extract lifecycle functions.
        
        Returns:
            Dictionary mapping function names to callable functions
        
        Raises:
            ValueError: If required function is missing
            ImportError: If strategy file cannot be loaded
        """
        # Add engine directory to path so strategies can import wealthdata
        import sys
        from pathlib import Path
        engine_dir = Path(__file__).parent.parent.parent
        if str(engine_dir) not in sys.path:
            sys.path.insert(0, str(engine_dir))
        
        # Set up wealthdata module BEFORE loading strategy
        # This ensures that when strategy executes `from wealthdata import *`,
        # it gets the correct log and g objects
        self._setup_wealthdata_before_load()
        
        # Load module
        module_name = f"strategy_{self.strategy_path.stem}"
        spec = importlib.util.spec_from_file_location(
            module_name,
            self.strategy_path
        )
        
        if spec is None or spec.loader is None:
            raise ImportError(f"Cannot load strategy file: {self.strategy_path}")
        
        self._module = importlib.util.module_from_spec(spec)
        
        # Set strategy module in thread-local storage BEFORE loading
        # This is critical because initialize() may call run_daily() during module execution
        self._set_strategy_module()
        
        # Now execute the module (this will execute initialize() which may call run_daily())
        spec.loader.exec_module(self._module)
        
        # Update log, g, run_daily, and order functions references in strategy module after import
        # This ensures that even if strategy imported from wealthdata before we set them,
        # the references in the strategy module point to the correct objects
        import wealthdata
        if hasattr(self._module, 'log'):
            self._module.log = wealthdata.log
        if hasattr(self._module, 'g'):
            self._module.g = wealthdata.g
        if hasattr(self._module, 'run_daily'):
            self._module.run_daily = wealthdata.run_daily
        if hasattr(self._module, 'order_value'):
            self._module.order_value = wealthdata.order_value
        if hasattr(self._module, 'order_target'):
            self._module.order_target = wealthdata.order_target
        
        # Extract lifecycle functions
        self._functions = {}
        
        # Check for required function
        if not hasattr(self._module, self.REQUIRED_FUNCTION):
            raise ValueError(
                f"Strategy file must define '{self.REQUIRED_FUNCTION}' function"
            )
        
        # Get required function
        self._functions[self.REQUIRED_FUNCTION] = getattr(
            self._module,
            self.REQUIRED_FUNCTION
        )
        
        # Get optional functions
        for func_name in self.OPTIONAL_FUNCTIONS:
            if hasattr(self._module, func_name):
                self._functions[func_name] = getattr(self._module, func_name)
            else:
                self._functions[func_name] = None
        
        return self._functions
    
    def get_function(self, name: str) -> Optional[Callable]:
        """
        Get a lifecycle function by name.
        
        Args:
            name: Function name
        
        Returns:
            Function callable or None if not found
        """
        return self._functions.get(name)
    
    def has_function(self, name: str) -> bool:
        """
        Check if strategy has a specific function.
        
        Args:
            name: Function name
        
        Returns:
            True if function exists, False otherwise
        """
        return name in self._functions and self._functions[name] is not None
    
    def _setup_wealthdata_before_load(self):
        """
        Set up wealthdata module BEFORE strategy is loaded.
        
        This ensures that when strategy executes `from wealthdata import *`,
        it gets the correct log and g objects.
        """
        import wealthdata
        from types import SimpleNamespace
        import sys
        
        # Create strategy-specific instances and set them in wealthdata module
        # This must be done BEFORE the strategy module is loaded,
        # so that `from wealthdata import *` gets the correct objects
        # Use wealthdata.Log class directly (defined in wealthdata module)
        wealthdata.g = SimpleNamespace()
        wealthdata.log = wealthdata.Log(output_stream=sys.stdout)
    
    def _set_strategy_module(self):
        """
        Set strategy module in thread-local storage.
        
        This is called AFTER the strategy module is loaded,
        so that run_daily, set_benchmark, etc. can access the module.
        """
        if self._module is None:
            return
        
        import wealthdata
        wealthdata._set_strategy_module(self._module)

