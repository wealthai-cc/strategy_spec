"""
Trading calendar for stock market trade days.

Provides trade day calculation for stock markets (A股, 美股, 港股),
excluding weekends and holidays. Cryptocurrency markets trade 7x24.
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import json
from pathlib import Path


# Default trading calendar data (can be extended with external file)
DEFAULT_CALENDAR = {
    'A_STOCK': {
        'holidays': [
            # 2024 holidays (example)
            '2024-01-01',  # 元旦
            '2024-02-10',  # 春节
            '2024-02-11',
            '2024-02-12',
            '2024-02-13',
            '2024-02-14',
            '2024-02-15',
            '2024-02-16',
            '2024-02-17',
            '2024-04-04',  # 清明节
            '2024-04-05',
            '2024-04-06',
            '2024-05-01',  # 劳动节
            '2024-05-02',
            '2024-05-03',
            '2024-05-04',
            '2024-05-05',
            '2024-06-10',  # 端午节
            '2024-09-15',  # 中秋节
            '2024-09-16',
            '2024-09-17',
            '2024-10-01',  # 国庆节
            '2024-10-02',
            '2024-10-03',
            '2024-10-04',
            '2024-10-05',
            '2024-10-06',
            '2024-10-07',
        ],
        'weekends': [5, 6],  # Saturday, Sunday
    },
    'US_STOCK': {
        'holidays': [
            # 2024 US holidays (example)
            '2024-01-01',  # New Year's Day
            '2024-01-15',  # Martin Luther King Jr. Day
            '2024-02-19',  # Presidents' Day
            '2024-03-29',  # Good Friday
            '2024-05-27',  # Memorial Day
            '2024-06-19',  # Juneteenth
            '2024-07-04',  # Independence Day
            '2024-09-02',  # Labor Day
            '2024-11-28',  # Thanksgiving
            '2024-12-25',  # Christmas
        ],
        'weekends': [5, 6],  # Saturday, Sunday
    },
    'HK_STOCK': {
        'holidays': [
            # 2024 HK holidays (example)
            '2024-01-01',  # New Year's Day
            '2024-02-10',  # Chinese New Year
            '2024-02-11',
            '2024-02-12',
            '2024-02-13',
            '2024-03-29',  # Good Friday
            '2024-04-01',  # Easter Monday
            '2024-04-04',  # Ching Ming Festival
            '2024-05-01',  # Labour Day
            '2024-05-15',  # Buddha's Birthday
            '2024-06-10',  # Dragon Boat Festival
            '2024-07-01',  # Hong Kong SAR Establishment Day
            '2024-09-18',  # Day after Mid-Autumn Festival
            '2024-10-01',  # National Day
            '2024-10-11',  # Chung Yeung Festival
            '2024-12-25',  # Christmas
            '2024-12-26',  # Boxing Day
        ],
        'weekends': [5, 6],  # Saturday, Sunday
    },
}


class TradeCalendar:
    """
    Trading calendar manager for stock markets.
    
    Handles trade day calculation, excluding weekends and holidays.
    Cryptocurrency markets trade 7x24, so every day is a trading day.
    """
    
    def __init__(self, calendar_file: Optional[str] = None):
        """
        Initialize trade calendar.
        
        Args:
            calendar_file: Optional path to calendar JSON file
        """
        self.calendar_file = calendar_file
        self.calendar_data = self._load_calendar()
    
    def _load_calendar(self) -> Dict[str, Dict[str, Any]]:
        """
        Load trading calendar data.
        
        Returns:
            Calendar data dictionary
        """
        if self.calendar_file and Path(self.calendar_file).exists():
            try:
                with open(self.calendar_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                # Fallback to default if file loading fails
                pass
        
        return DEFAULT_CALENDAR.copy()
    
    def is_trade_day(self, date: datetime, market_type: str) -> bool:
        """
        Check if a date is a trading day.
        
        Args:
            date: Date to check
            market_type: Market type (A_STOCK, US_STOCK, HK_STOCK, CRYPTO)
        
        Returns:
            True if trading day, False otherwise
        """
        # Cryptocurrency: every day is a trading day
        if market_type == 'CRYPTO':
            return True
        
        market_cal = self.calendar_data.get(market_type, {})
        
        # Check if weekend
        if date.weekday() in market_cal.get('weekends', [5, 6]):
            return False
        
        # Check if holiday
        date_str = date.strftime('%Y-%m-%d')
        if date_str in market_cal.get('holidays', []):
            return False
        
        return True
    
    def get_trade_days(
        self,
        start_date: datetime,
        end_date: datetime,
        market_type: str
    ) -> List[str]:
        """
        Get list of trading days in date range.
        
        Args:
            start_date: Start date
            end_date: End date
            market_type: Market type
        
        Returns:
            List of date strings (YYYY-MM-DD format)
        """
        if market_type == 'CRYPTO':
            # Cryptocurrency: return all days
            dates = []
            current = start_date
            while current <= end_date:
                dates.append(current.strftime('%Y-%m-%d'))
                current += timedelta(days=1)
            return dates
        
        # Stock market: return only trading days
        dates = []
        current = start_date
        while current <= end_date:
            if self.is_trade_day(current, market_type):
                dates.append(current.strftime('%Y-%m-%d'))
            current += timedelta(days=1)
        return dates


# Global calendar instance
_calendar = TradeCalendar()


def get_calendar() -> TradeCalendar:
    """Get global trade calendar instance."""
    return _calendar



