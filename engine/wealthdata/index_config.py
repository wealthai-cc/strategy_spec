"""
Cryptocurrency index configuration.

Defines index compositions and weights for crypto indices.
This module provides static configuration data for index-related APIs.
"""

# Index compositions: mapping from index symbol to list of trading pair symbols
INDEX_COMPOSITIONS = {
    'BTC_INDEX': ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT', 'ADAUSDT'],
    'ETH_INDEX': ['ETHUSDT', 'BTCUSDT', 'BNBUSDT', 'SOLUSDT', 'MATICUSDT'],
    'DEFI_INDEX': ['ETHUSDT', 'UNIUSDT', 'AAVEUSDT', 'LINKUSDT', 'SUSHIUSDT'],
    'LAYER1_INDEX': ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'ADAUSDT', 'AVAXUSDT'],
    'LAYER2_INDEX': ['ETHUSDT', 'MATICUSDT', 'ARBUSDT', 'OPUSDT', 'IMXUSDT'],
}

# Index weights: mapping from index symbol to dict of {symbol: weight}
# Weights should sum to approximately 1.0
INDEX_WEIGHTS = {
    'BTC_INDEX': {
        'BTCUSDT': 0.50,
        'ETHUSDT': 0.25,
        'BNBUSDT': 0.10,
        'SOLUSDT': 0.10,
        'ADAUSDT': 0.05,
    },
    'ETH_INDEX': {
        'ETHUSDT': 0.60,
        'BTCUSDT': 0.20,
        'BNBUSDT': 0.10,
        'SOLUSDT': 0.05,
        'MATICUSDT': 0.05,
    },
    'DEFI_INDEX': {
        'ETHUSDT': 0.40,
        'UNIUSDT': 0.20,
        'AAVEUSDT': 0.15,
        'LINKUSDT': 0.15,
        'SUSHIUSDT': 0.10,
    },
    'LAYER1_INDEX': {
        'BTCUSDT': 0.35,
        'ETHUSDT': 0.35,
        'SOLUSDT': 0.15,
        'ADAUSDT': 0.10,
        'AVAXUSDT': 0.05,
    },
    'LAYER2_INDEX': {
        'ETHUSDT': 0.40,
        'MATICUSDT': 0.25,
        'ARBUSDT': 0.15,
        'OPUSDT': 0.12,
        'IMXUSDT': 0.08,
    },
}


def get_index_composition(index_symbol: str) -> list:
    """
    Get index composition (list of trading pair symbols).
    
    Args:
        index_symbol: Index identifier (e.g., 'BTC_INDEX')
    
    Returns:
        List of trading pair symbols, or empty list if index not found
    """
    return INDEX_COMPOSITIONS.get(index_symbol, [])


def get_index_weight_dict(index_symbol: str) -> dict:
    """
    Get index weights as a dictionary.
    
    Args:
        index_symbol: Index identifier (e.g., 'BTC_INDEX')
    
    Returns:
        Dictionary mapping trading pair symbols to weights, or empty dict if not found
    """
    return INDEX_WEIGHTS.get(index_symbol, {})

