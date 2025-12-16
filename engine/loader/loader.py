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
        
        # Load module
        module_name = f"strategy_{self.strategy_path.stem}"
        spec = importlib.util.spec_from_file_location(
            module_name,
            self.strategy_path
        )
        
        if spec is None or spec.loader is None:
            raise ImportError(f"Cannot load strategy file: {self.strategy_path}")
        
        self._module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self._module)
        
        # Inject JoinQuant compatibility objects
        self._inject_compatibility_objects()
        
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
    
    def _inject_compatibility_objects(self):
        """
        Inject JoinQuant compatibility objects into strategy module namespace.
        
        This includes:
        - `g`: Global variable object for strategy state
        - `log`: Logging module
        - `run_daily`: Scheduled function registration
        - `order_value`, `order_target`: Order functions
        - `set_benchmark`, `set_option`, `set_order_cost`: Config functions
        """
        if self._module is None:
            return
        
        # Import compatibility modules
        from engine.compat.g import create_g_object
        from engine.compat.log import create_log_object
        from engine.compat.scheduler import create_run_daily_function
        from engine.compat.order import create_order_functions
        from engine.compat.config import create_config_functions
        
        # Inject g object
        self._module.g = create_g_object()
        
        # Inject log object
        self._module.log = create_log_object()
        
        # Inject run_daily function
        self._module.run_daily = create_run_daily_function(self._module)
        
        # Inject order functions
        order_funcs = create_order_functions()
        self._module.order_value = order_funcs['order_value']
        self._module.order_target = order_funcs['order_target']
        
        # Inject config functions
        config_funcs = create_config_functions(self._module)
        self._module.set_benchmark = config_funcs['set_benchmark']
        self._module.set_option = config_funcs['set_option']
        self._module.set_order_cost = config_funcs['set_order_cost']

