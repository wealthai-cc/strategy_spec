"""
Market time utilities for handling timezone and trading hours.

Provides functions to convert UTC time to market local time and
determine if current time matches trading schedule.
"""

from datetime import datetime, time
from typing import Optional, Dict, Tuple, Any
try:
    import pytz
    PYTZ_AVAILABLE = True
except ImportError:
    PYTZ_AVAILABLE = False
    # Fallback: use UTC if pytz not available
    pytz = None

from .market_type import MarketType


# Market timezone mappings
MARKET_TIMEZONES: Dict[str, str] = {
    'A_STOCK': 'Asia/Shanghai',
    'US_STOCK': 'America/New_York',
    'HK_STOCK': 'Asia/Hong_Kong',
    'CRYPTO': 'UTC',
}

# Market trading hours (local time)
MARKET_TRADING_HOURS: Dict[str, Dict[str, Tuple[int, int]]] = {
    'A_STOCK': {
        'open': (9, 30),      # 9:30
        'close': (15, 0),     # 15:00
        'before_open': (9, 25),  # 9:25
        'after_close': (15, 5),  # 15:05
    },
    'US_STOCK': {
        'open': (9, 30),      # 9:30 ET
        'close': (16, 0),     # 16:00 ET
        'before_open': (9, 25),  # 9:25 ET
        'after_close': (16, 5),  # 16:05 ET
    },
    'HK_STOCK': {
        'open': (9, 30),      # 9:30 HKT
        'close': (16, 0),     # 16:00 HKT
        'before_open': (9, 25),  # 9:25 HKT
        'after_close': (16, 5),  # 16:05 HKT
    },
    'CRYPTO': {
        'open': (0, 0),       # 00:00 UTC (logical time)
        'close': (23, 59),    # 23:59 UTC (logical time)
        'before_open': (0, 0),   # 00:00 UTC
        'after_close': (23, 59),  # 23:59 UTC
    },
}


def get_market_timezone(market_type: MarketType) -> Optional[Any]:
    """
    Get timezone object for market type.
    
    Args:
        market_type: Market type enum
    
    Returns:
        Timezone object or None if pytz not available
    """
    if not PYTZ_AVAILABLE:
        return None
    
    tz_name = MARKET_TIMEZONES.get(market_type.value, 'UTC')
    try:
        return pytz.timezone(tz_name)
    except Exception:
        return pytz.UTC


def get_market_local_time(utc_time: datetime, market_type: MarketType) -> datetime:
    """
    Convert UTC time to market local time.
    
    Args:
        utc_time: UTC datetime
        market_type: Market type
    
    Returns:
        Local datetime (or UTC if pytz not available)
    """
    tz = get_market_timezone(market_type)
    if tz is None:
        return utc_time
    
    # Assume input is UTC if not timezone-aware
    if utc_time.tzinfo is None:
        utc_time = pytz.UTC.localize(utc_time)
    
    return utc_time.astimezone(tz)


def get_market_time_point(
    current_utc_time: datetime,
    market_type: MarketType,
    time_point: str
) -> Optional[datetime]:
    """
    Get market time point for a given time (e.g., 'before_open', 'open').
    
    Args:
        current_utc_time: Current UTC time
        market_type: Market type
        time_point: Time point ('before_open', 'open', 'after_close')
    
    Returns:
        Market time point datetime or None
    """
    market_hours = MARKET_TRADING_HOURS.get(market_type.value, {})
    if time_point not in market_hours:
        return None
    
    hour, minute = market_hours[time_point]
    
    # Convert to market local time
    local_time = get_market_local_time(current_utc_time, market_type)
    
    # Create time point at today's date
    time_point_dt = local_time.replace(hour=hour, minute=minute, second=0, microsecond=0)
    
    return time_point_dt


def is_time_match(
    current_utc_time: datetime,
    market_type: MarketType,
    time_point: str,
    tolerance_minutes: int = 30
) -> bool:
    """
    Check if current time matches a market time point.
    
    Args:
        current_utc_time: Current UTC time
        market_type: Market type
        time_point: Time point to match ('before_open', 'open', 'after_close')
        tolerance_minutes: Tolerance in minutes for matching
    
    Returns:
        True if time matches, False otherwise
    """
    target_time = get_market_time_point(current_utc_time, market_type, time_point)
    if target_time is None:
        return False
    
    # Convert current time to market local time
    current_local = get_market_local_time(current_utc_time, market_type)
    
    # Check if within tolerance
    time_diff = abs((current_local - target_time).total_seconds() / 60)
    return time_diff <= tolerance_minutes

