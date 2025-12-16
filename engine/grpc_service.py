"""
gRPC service implementation for StrategySpec.

This module provides a gRPC service that wraps the strategy execution engine.
"""

from typing import Dict, Any
import logging

# Note: In real implementation, these would be generated from .proto files
# For now, we'll use type hints and assume the proto types exist

logger = logging.getLogger(__name__)


class StrategySpecService:
    """
    gRPC service implementation for StrategySpec.
    
    Wraps StrategyExecutionEngine to provide gRPC interface.
    """
    
    def __init__(self, strategy_path: str):
        """
        Initialize service.
        
        Args:
            strategy_path: Path to Python strategy file
        """
        from .engine import StrategyExecutionEngine
        self.engine = StrategyExecutionEngine(strategy_path)
        self.engine.load_strategy()
    
    def Health(self, request: Any) -> Dict[str, Any]:
        """
        Health check endpoint.
        
        Args:
            request: Empty request (google.protobuf.Empty)
        
        Returns:
            HealthResponse with status and message
        """
        try:
            # Check if strategy is loaded
            if not self.engine._loaded:
                return {
                    "status": 2,  # UNHEALTHY
                    "message": "Strategy not loaded",
                    "details": [],
                }
            
            return {
                "status": 0,  # HEALTHY
                "message": "Strategy service is healthy",
                "details": [],
            }
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "status": 2,  # UNHEALTHY
                "message": f"Health check failed: {str(e)}",
                "details": [str(e)],
            }
    
    def Exec(self, request: Any) -> Dict[str, Any]:
        """
        Execute strategy.
        
        Args:
            request: ExecRequest with trigger and context data
        
        Returns:
            ExecResponse with order operations and status
        """
        try:
            # Convert proto request to dictionary
            exec_request = self._proto_to_dict(request)
            
            # Execute strategy
            response = self.engine.execute(exec_request)
            
            return response
        
        except Exception as e:
            logger.error(f"Strategy execution failed: {e}", exc_info=True)
            return {
                "order_op_event": [],
                "status": 2,  # FAILED
                "error_message": str(e),
                "warnings": [],
            }
    
    def _proto_to_dict(self, proto_request: Any) -> Dict[str, Any]:
        """
        Convert proto ExecRequest to dictionary.
        
        In real implementation, this would properly parse the proto message.
        For now, we assume the proto object has attributes matching the spec.
        """
        # This is a simplified conversion
        # In real implementation, you would use proto's SerializeToString/ParseFromString
        # or use a proto-to-dict library
        
        return {
            "max_timeout": getattr(proto_request, "max_timeout", 30),
            "trigger_type": getattr(proto_request, "trigger_type", 0),
            "trigger_detail": self._proto_message_to_dict(
                getattr(proto_request, "trigger_detail", None)
            ),
            "market_data_context": [
                self._proto_message_to_dict(ctx)
                for ctx in getattr(proto_request, "market_data_context", [])
            ],
            "account": self._proto_message_to_dict(
                getattr(proto_request, "account", None)
            ),
            "incomplete_orders": [
                self._proto_message_to_dict(order)
                for order in getattr(proto_request, "incomplete_orders", [])
            ],
            "completed_orders": [
                self._proto_message_to_dict(order)
                for order in getattr(proto_request, "completed_orders", [])
            ],
            "exchange": getattr(proto_request, "exchange", ""),
            "exec_id": getattr(proto_request, "exec_id", ""),
            "strategy_param": dict(getattr(proto_request, "strategy_param", {})),
        }
    
    def _proto_message_to_dict(self, proto_msg: Any) -> Dict[str, Any]:
        """
        Convert proto message to dictionary.
        
        In real implementation, use proper proto serialization.
        """
        if proto_msg is None:
            return {}
        
        # Simplified: assume proto message has __dict__ or can be converted
        # In real implementation, use MessageToDict from google.protobuf.json_format
        try:
            return {
                key: getattr(proto_msg, key)
                for key in dir(proto_msg)
                if not key.startswith("_") and not callable(getattr(proto_msg, key))
            }
        except Exception:
            return {}

