"""
Cryptocurrency industry/category configuration.

Defines trading pair categories for crypto assets.
This module provides static configuration data for industry-related APIs.
"""

# Trading pair categories: mapping from trading pair symbol to category
TRADING_PAIR_CATEGORIES = {
    # Layer 1 Blockchains
    'BTCUSDT': 'Layer1',
    'ETHUSDT': 'Layer1',
    'SOLUSDT': 'Layer1',
    'ADAUSDT': 'Layer1',
    'AVAXUSDT': 'Layer1',
    'DOTUSDT': 'Layer1',
    'ATOMUSDT': 'Layer1',
    'NEARUSDT': 'Layer1',
    
    # Layer 2 Solutions
    'MATICUSDT': 'Layer2',
    'ARBUSDT': 'Layer2',
    'OPUSDT': 'Layer2',
    'IMXUSDT': 'Layer2',
    'LRCUSDT': 'Layer2',
    
    # DeFi
    'UNIUSDT': 'DeFi',
    'AAVEUSDT': 'DeFi',
    'LINKUSDT': 'DeFi',
    'SUSHIUSDT': 'DeFi',
    'CRVUSDT': 'DeFi',
    'MKRUSDT': 'DeFi',
    'COMPUSDT': 'DeFi',
    
    # Exchange Tokens
    'BNBUSDT': 'Exchange',
    'FTTUSDT': 'Exchange',
    'HTUSDT': 'Exchange',
    'OKBUSDT': 'Exchange',
    
    # Meme Coins
    'DOGEUSDT': 'Meme',
    'SHIBUSDT': 'Meme',
    
    # Stablecoins (for reference, though they're not typically traded)
    'USDCUSDT': 'Stablecoin',
    'USDPUSDT': 'Stablecoin',
    
    # Gaming/Metaverse
    'AXSUSDT': 'Gaming',
    'SANDUSDT': 'Gaming',
    'MANAUSDT': 'Gaming',
    
    # Storage
    'FILUSDT': 'Storage',
    'ARUSDT': 'Storage',
}


def get_trading_pair_category(symbol: str) -> str:
    """
    Get category for a trading pair.
    
    Args:
        symbol: Trading pair symbol (e.g., 'BTCUSDT')
    
    Returns:
        Category string (e.g., 'Layer1', 'DeFi', 'Layer2'), or empty string if not found
    """
    return TRADING_PAIR_CATEGORIES.get(symbol, '')

