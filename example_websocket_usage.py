#!/usr/bin/env python3
"""
示例：WebSocket 行情接入使用方式

这个示例展示了如何在策略管理系统中配置和使用 WebSocket 行情接入。
"""

# ============================================================================
# 1. 系统级配置（策略管理系统）
# ============================================================================

def setup_websocket_for_strategy(symbols, resolutions):
    """
    为策略设置 WebSocket 连接。
    
    这个函数应该在策略管理系统启动策略时调用。
    """
    from engine.python_sdk.websocket_manager import get_websocket_manager
    
    # 获取管理器
    manager = get_websocket_manager()
    
    # 配置订阅
    manager.configure(
        symbols=symbols,
        resolutions=resolutions,
        # 可选：自定义端点
        # endpoint="wss://ws.wealthai.cc:18000/market_data",
        # csrf_token="your_token",
        # market_type="binance-testnet",
    )
    
    # 启动 WebSocket 连接
    try:
        manager.start()
        print(f"WebSocket started for symbols: {symbols}, resolutions: {resolutions}")
        return True
    except Exception as e:
        print(f"Failed to start WebSocket: {e}")
        return False


def check_websocket_status():
    """检查 WebSocket 连接状态。"""
    from engine.python_sdk.websocket_manager import get_websocket_manager
    
    manager = get_websocket_manager()
    status = manager.get_status()
    
    print(f"WebSocket Status:")
    print(f"  State: {status['state']}")
    print(f"  Symbols: {status['symbols']}")
    print(f"  Resolutions: {status['resolutions']}")
    if status['last_error']:
        print(f"  Last Error: {status['last_error']}")
    
    return status


# ============================================================================
# 2. 策略使用（策略代码无需修改）
# ============================================================================

def example_strategy_with_websocket(context, bar):
    """
    示例策略：使用 WebSocket 实时数据
    
    注意：策略代码完全不需要改变，WebSocket 数据会自动提供。
    """
    from wealthdata import get_price
    import pandas as pd
    
    # 获取价格数据
    # 这会自动从 WebSocket 缓存（如果可用）或 Context 获取数据
    df = get_price('BTCUSDT', count=20, frequency='1h')
    
    # 计算移动平均
    ma5 = df['close'].rolling(5).mean().iloc[-1]
    ma20 = df['close'].rolling(20).mean().iloc[-1]
    
    current_price = df['close'].iloc[-1]
    
    # 策略逻辑
    if ma5 > ma20 and current_price > ma5:
        # 买入信号
        print(f"Buy signal: price={current_price}, MA5={ma5}, MA20={ma20}")
        # context.buy('BTCUSDT', 0.1)  # 示例：买入
    elif ma5 < ma20 and current_price < ma5:
        # 卖出信号
        print(f"Sell signal: price={current_price}, MA5={ma5}, MA20={ma20}")
        # context.sell('BTCUSDT', 0.1)  # 示例：卖出


# ============================================================================
# 3. 环境变量配置方式
# ============================================================================

def setup_via_environment_variables():
    """
    通过环境变量配置 WebSocket（可选）。
    
    设置以下环境变量：
    export WEBSOCKET_ENDPOINT="wss://ws.wealthai.cc:18000/market_data"
    export WEBSOCKET_CSRF_TOKEN="your_token"
    export WEBSOCKET_MARKET_TYPE="binance-testnet"
    export WEBSOCKET_SYMBOLS="BTCUSDT,ETHUSDT"
    export WEBSOCKET_RESOLUTIONS="1m,5m,1h"
    """
    from engine.python_sdk.websocket_manager import get_websocket_manager
    
    manager = get_websocket_manager()
    
    # 从环境变量加载配置
    config = manager.load_config_from_env()
    print(f"Loaded config from environment: {config}")
    
    # 如果环境变量中有配置，自动启动
    if config.get('symbols') and config.get('resolutions'):
        manager.start()


# ============================================================================
# 4. 完整示例
# ============================================================================

def main():
    """完整使用示例。"""
    print("=" * 60)
    print("WebSocket 行情接入使用示例")
    print("=" * 60)
    print()
    
    # 1. 系统启动时配置 WebSocket
    print("1. 配置 WebSocket 连接...")
    success = setup_websocket_for_strategy(
        symbols=["BTCUSDT", "ETHUSDT"],
        resolutions=["1m", "5m", "1h"]
    )
    
    if not success:
        print("WebSocket 启动失败，策略将使用 Context 数据（回测模式）")
        return
    
    # 2. 检查状态
    print("\n2. 检查 WebSocket 状态...")
    status = check_websocket_status()
    
    # 3. 策略执行（模拟）
    print("\n3. 策略执行示例...")
    print("策略代码无需修改，自动使用 WebSocket 数据（如果可用）")
    print("或回退到 Context 数据（回测模式）")
    
    # 注意：实际策略执行由策略引擎管理
    # 这里只是展示数据获取方式
    from engine.python_sdk.websocket_cache import get_websocket_cache
    cache = get_websocket_cache()
    cached_symbols = cache.get_cached_symbols()
    print(f"当前缓存的数据: {cached_symbols}")
    
    print("\n" + "=" * 60)
    print("示例完成")
    print("=" * 60)


if __name__ == "__main__":
    main()

