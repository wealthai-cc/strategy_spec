# 导入函数库
# 添加项目根目录到 Python 路径（用于直接运行测试）
import sys
import os
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from wealthdata import *

# 类型提示：这些函数在运行时由引擎自动注入，不需要导入
# 导入 strategy 模块可以让编辑器识别这些函数
try:
    from strategy import g, log, run_daily, order_value, order_target, set_benchmark, set_option, set_order_cost, OrderCost
except ImportError:
    # 运行时这些函数会被注入，这里只是为了让编辑器不报错
    pass

# 初始化函数，设定基准等等
def initialize(context):
    # 设定 BTC 作为基准
    set_benchmark('BTCUSDT')
    # 开启动态复权模式(真实价格)
    set_option('use_real_price', True)
    # 输出内容到日志 log.info()
    log.info('初始函数开始运行且全局只运行一次')
    
    ### 加密货币相关设定 ###
    # 加密货币交易手续费：买入时 0.1%，卖出时 0.1%（Binance Spot 标准费率）
    set_order_cost(OrderCost(open_commission=0.001, close_commission=0.001, min_commission=0), type='crypto')
    
    ## 运行函数（reference_security为运行时间的参考标的）
      # 开盘前运行（加密货币24小时交易，这里设置为每天UTC 00:00）
    run_daily(before_market_open, time='before_open', reference_security='BTCUSDT')
      # 开盘时运行（设置为每天UTC 00:00）
    run_daily(market_open, time='open', reference_security='BTCUSDT')
      # 收盘后运行（设置为每天UTC 23:59）
    run_daily(after_market_close, time='after_close', reference_security='BTCUSDT')

## 开盘前运行函数
def before_market_open(context):
    # 输出运行时间
    log.info('函数运行时间(before_market_open)：'+str(context.current_dt.time()))
    
    # 要操作的加密货币交易对
    g.security = 'BTCUSDT'

## 开盘时运行函数
def market_open(context):
    log.info('函数运行时间(market_open):'+str(context.current_dt.time()))
    security = g.security
    # 获取加密货币的收盘价
    close_data = get_bars(security, count=5, unit='1h', fields=['close'])
    # 取得过去五小时的平均价格
    MA5 = close_data['close'].mean()
    # 取得上一时间点价格
    current_price = close_data['close'][-1]
    # 取得当前的现金（USDT）
    cash = context.portfolio.available_cash
    
    # 如果上一时间点价格高出五小时平均价1%, 则全仓买入
    if (current_price > 1.01*MA5) and (cash > 0):
        # 记录这次买入
        log.info("价格高于均价 1%%, 买入 %s" % (security))
        print("当前可用资金为{0}, position_value为{1}".format(cash, context.portfolio.positions_value))
        # 用所有 cash 买入加密货币
        order_value(security, cash)
    # 如果上一时间点价格低于五小时平均价, 则空仓卖出
    elif current_price < MA5 and context.portfolio.positions[security].closeable_amount > 0:
        # 记录这次卖出
        log.info("价格低于均价, 卖出 %s" % (security))
        # 卖出所有加密货币,使这个交易对的最终持有量为0
        order_target(security, 0)

## 收盘后运行函数
def after_market_close(context):
    log.info(str('函数运行时间(after_market_close):'+str(context.current_dt.time())))
    #得到当天所有成交记录
    trades = get_trades()
    for _trade in trades.values():
        log.info('成交记录：'+str(_trade))
    log.info('一天结束')
    log.info('##############################################################')

