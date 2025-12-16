# WealthAI 策略规范（Strategy Spec）

## 概述
- 本目录定义面向策略实现者的公共接口规范（Proto3），用于在策略与策略管理系统之间进行标准化交互。
- 设计目标：无状态、可测试、跨语言、可扩展；易于在不同运行环境（回测、仿真、真实交易）复用。
- 适用范围：量化策略的执行接口、账户/订单/行情数据结构、触发机制与错误反馈。

## 设计原则
- 无状态策略：策略不保存内部状态，每次 `Exec` 为纯函数式调用，由入参决定行为。
- 风控内部化：风控逻辑在策略内部闭环，对外仅通过订单事件体现。
- 时间统一：所有时间字段使用 Unix 毫秒时间戳。
- 明确触发：支持行情、风控、订单状态三类触发，触发详情通过 `TriggerDetail` 描述。

## OpenSpec 规范文档

本项目采用 [OpenSpec](https://github.com/Fission-AI/OpenSpec) 方式进行需求与开发迭代管理。

- **[OpenSpec 主规格文档](./PRD/openspec.md)**：所有规格文档的索引和入口
- **[开发范式文档](./PRD/开发范式文档.md)**：OpenSpec 交互入口与规范约定

### 核心模块规格文档

- [策略执行引擎规范](./openspec/specs/strategy-engine/spec.md) - 服务接口、触发机制、执行流程、引擎架构
- [策略开发规范](./openspec/specs/strategy-development/spec.md) - 生命周期函数、Context 对象、wealthdata 兼容层、Python 策略开发
- [账户与持仓规范](./openspec/specs/account/spec.md) - 账户类型、余额、持仓、风控指标
- [订单管理规范](./openspec/specs/order/spec.md) - 订单类型、状态流转、操作事件
- [行情数据规范](./openspec/specs/market-data/spec.md) - K线数据、技术指标、多分辨率支持
- [Python SDK 规范](./openspec/specs/python-sdk/spec.md) - TradingRule、佣金费率查询接口
- [示例文档](./PRD/spec_example.md) - OpenSpec 结构示例参考

## 文件结构
- `strategy_spec.proto`：服务接口与核心消息（`Exec/Health`、触发类型、执行响应）
- `account.proto`：账户与持仓结构（含风控指标）
- `order.proto`：订单结构（类型、状态、价格字段、手续费等）
- `market_data.proto`：行情结构（Bar 与技术指标）
- `review.md`：规范评审与改进建议
- `python_sdk.md`：策略侧 Python SDK 方法手册（TradingRule、佣金费率）
- `PRD/`：OpenSpec 规范文档目录

## 服务接口（StrategySpec）
- `Health(Empty) -> HealthResponse`：返回策略健康状态（`HEALTHY/DEGRADED/UNHEALTHY`）
- `Exec(ExecRequest) -> ExecResponse`：执行策略决策，返回订单操作事件
- 并发与幂等约定：
  - 同一账户的同一策略由系统保证串行执行
  - 系统对同一触发事件的重复执行进行去重；`ExecRequest.exec_id` 作为执行幂等 ID

## 触发机制
- 触发类型（`TriggerType`）：
  - `MARKET_DATA_TRIGGER_TYPE`：行情触发
  - `RISK_MANAGE_TRIGGER_TYPE`：风控触发（如补充保证金、强平预警）
  - `ORDER_STATUS_TRIGGER_TYPE`：订单状态变更触发
- 触发详情（`TriggerDetail`）：
  - 行情触发：`MarketDataTriggerDetail.server_ts`
  - 风控触发：`RiskManageTriggerDetail.risk_event_type/remark`

## 请求与响应
- `ExecRequest` 核心字段：
  - `max_timeout`：最大超时秒数
  - `trigger_type/trigger_detail`：触发类型与详情
  - `market_data_context[]`：行情上下文（支持多分辨率）
  - `account`：账户信息（含风控指标）
  - `incomplete_orders/completed_orders`：订单集合
  - `exchange`：交易所名称（用于佣金计算等）
  - `exec_id`：执行幂等 ID
  - `strategy_param`：透传策略参数
- `ExecResponse` 执行反馈：
  - `order_op_event[]`：订单操作事件（创建/撤单/修改）
  - `status`：`SUCCESS/PARTIAL_SUCCESS/FAILED`
  - `error_message`：错误信息（失败时）
  - `warnings[]`：警告信息（非致命问题）

## 数据模型要点
- 订单（`Order`）：
  - 类型：市价/限价/止损市价/止损限价
  - 价格字段：`limit_price`、`stop_price`（不再使用语义混乱的通用 `price`）
  - 执行信息：`avg_fill_price`、`commission`、`cancel_reason` 等
  - 幂等：`unique_id` 为订单幂等 ID（系统维度说明见交易系统规范）
- 账户（`Account`）：
  - 余额与持仓：`balances`、`positions`
  - 风控指标：`total_net_value`、`available_margin`、`margin_ratio`、`risk_level`、`leverage`
- 行情（`MarketDataContext`）：
  - `symbol`、`timeframe`、`bars[]`（OHLCV）
  - `indicators[]`：技术指标（MA/EMA，或扩展结构）

## 生成代码（Proto 编译）
- 依赖：`protoc` 与对应语言的插件
- Go（示例）：
  - 安装：`go install google.golang.org/protobuf/cmd/protoc-gen-go@latest`
  - 命令：`protoc --go_out=. --go_opt=paths=source_relative *.proto`
- Python（示例）：
  - 安装：`pip install protobuf grpcio-tools`
  - 命令：`python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. *.proto`

## Python SDK（策略侧）
- TradingRule 与 佣金费率通过本地查询接口获取，详见 `python_sdk.md`
  - `get_trading_rule(broker, symbol)`：本地开销，返回品种的下单与精度限制
  - `get_commission_rates(broker, symbol)`：本地开销，返回 Maker/Taker 手续费率

## JoinQuant 兼容性

WealthAI 策略框架提供完整的 JoinQuant 兼容层，支持平滑迁移：

- **数据查询 API**：`get_price()`, `get_bars()`, `get_all_securities()`, `get_trade_days()`, `get_index_stocks()`, `get_index_weights()`, `get_fundamentals()`, `get_industry()`, `get_trades()`
- **兼容功能**：全局变量（`g`）、日志模块（`log`）、定时运行（`run_daily`）、下单函数（`order_value`, `order_target`）、配置函数（`set_benchmark`, `set_option`, `set_order_cost`）
- **市场类型支持**：股票市场（A股、美股、港股）和加密货币市场（7x24 交易）

**迁移步骤**：
1. 将 `import jqdata` 改为 `import wealthdata`
2. 将股票代码改为交易对格式（如 `'000001.XSHE'` → `'BTCUSDT'`）
3. 其他代码基本无需修改

详细迁移指南请参考：[JoinQuant 迁移指南](./PRD/JoinQuant迁移指南.md)

## 版本与兼容
- 语义化版本管理：变更遵循 `MAJOR.MINOR.PATCH`
- 兼容性：
  - 添加字段：默认向后兼容（保留已有字段与语义）
  - 删除/重命名字段：视为破坏性变更，需升级主版本并提供迁移建议

## 贡献与反馈
- 欢迎通过 Issue/PR 提交改进建议或扩展（指标、订单字段、错误模型等）
- 请遵循现有风格与注释规范：所有标识符与字段保留中文注释（`INVALID_XXX` 占位除外）

