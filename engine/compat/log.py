"""
Logging module for JoinQuant compatibility.

Provides a simple logging interface compatible with JoinQuant's log module.
"""

import sys
from typing import Optional


class Log:
    """
    Simple logging class compatible with JoinQuant's log interface.
    """
    
    def __init__(self, output_stream=None):
        """
        Initialize log object.
        
        Args:
            output_stream: Output stream for logs (default: sys.stdout)
        """
        self.output_stream = output_stream or sys.stdout
        self._log_levels = {}  # Store log level configuration (simplified)
    
    def info(self, message: str) -> None:
        """
        Log an info message.
        
        Args:
            message: Message to log
        """
        self._log('INFO', message)
    
    def warn(self, message: str) -> None:
        """
        Log a warning message.
        
        Args:
            message: Message to log
        """
        self._log('WARN', message)
    
    def error(self, message: str) -> None:
        """
        Log an error message.
        
        Args:
            message: Message to log
        """
        self._log('ERROR', message)
    
    def debug(self, message: str) -> None:
        """
        Log a debug message.
        
        Args:
            message: Message to log
        """
        self._log('DEBUG', message)
    
    def set_level(self, category: str, level: str) -> None:
        """
        Set log level for a category (simplified implementation).
        
        This method accepts the call for compatibility but may not affect
        output in the simplified implementation.
        
        Args:
            category: Log category (e.g., 'order')
            level: Log level (e.g., 'error')
        """
        self._log_levels[category] = level
        # Simplified implementation: accept but don't filter
    
    def _log(self, level: str, message: str) -> None:
        """
        Internal method to log a message.
        
        Args:
            level: Log level
            message: Message to log
        """
        log_line = f"[{level}] {message}\n"
        self.output_stream.write(log_line)
        self.output_stream.flush()


def create_log_object(output_stream=None) -> Log:
    """
    Create a log object for strategy use.
    
    Args:
        output_stream: Optional output stream (default: sys.stdout)
    
    Returns:
        Log object
    """
    return Log(output_stream=output_stream)

