# Tasks: 增强 JoinQuant 兼容性

## 1. 市场类型识别和基础兼容功能

### 1.1 市场类型识别机制
- [x] 创建 `engine/compat/market_type.py` 模块，实现市场类型识别函数
- [x] 实现 `is_stock_market()` 和 `is_crypto_market()` 函数
- [x] 实现 `detect_market_type()` 函数，支持显式配置和格式识别
- [x] 支持识别 A股（.XSHE/.XSHG）、美股（.US）、港股（.HK）、加密货币（交易对格式）
- [x] 实现边界情况处理（格式不规范、显式指定、回退机制）
- [x] 编写单元测试验证市场类型识别逻辑和边界情况

### 1.2 全局变量（g）支持
- [x] 在 `engine/loader/loader.py` 中实现 `g` 对象注入逻辑
- [x] 创建 `engine/compat/g.py` 模块，提供全局变量对象
- [x] 在策略加载时注入 `g` 对象到策略模块命名空间
- [x] 编写单元测试验证 `g` 对象功能

### 1.3 日志模块（log）实现
- [x] 创建 `engine/compat/log.py` 模块，实现 `Log` 类
- [x] 支持 `info()`, `warn()`, `error()`, `debug()` 方法
- [x] 支持 `set_level()` 方法（简化实现）
- [x] 在策略加载时注入 `log` 对象到策略模块命名空间
- [x] 编写单元测试验证日志功能

### 1.4 Context 属性扩展
- [x] 修改 `engine/context/context.py`，添加 `current_dt` 属性（从 `current_bar.close_time` 计算）
- [x] 修改 `engine/context/context.py` 中的 `Portfolio` 类：
  - [x] 添加 `available_cash` 属性（从 `account` 计算）
  - [x] 添加 `positions_value` 属性（计算持仓市值）
  - [x] 实现字典式 `positions` 访问（维护 `positions_list` 和 `positions_dict`）
- [x] 编写单元测试验证新属性

### 1.5 下单函数扩展
- [x] 创建 `engine/compat/order.py` 模块，实现 `order_value()` 函数
- [x] 实现 `order_target()` 函数
- [x] 根据市场类型调整数量单位（股票市场按"股"计算为整数，加密货币按数量计算）
- [x] 在策略加载时注入这些函数到策略模块命名空间
- [x] 编写单元测试验证下单函数和市场类型适配

## 2. 定时运行机制实现

### 2.1 run_daily 函数注册
- [x] 创建 `engine/compat/scheduler.py` 模块，实现 `run_daily()` 函数
- [x] 实现定时函数注册逻辑（存储函数、时间、参考标的）
- [x] 在策略加载时注入 `run_daily` 函数到策略模块命名空间
- [x] 编写单元测试验证注册逻辑

### 2.2 引擎集成定时调用
- [x] 修改 `engine/lifecycle/lifecycle.py`，添加定时函数调用逻辑
- [x] 在 `before_trading` 中检查并调用注册的定时函数
- [x] 实现时区处理模块（使用 `pytz` 库）
- [x] 实现市场交易时间配置（A股、美股、港股、加密货币）
- [x] 实现时间匹配逻辑，根据市场类型调整：
  - [x] 股票市场：匹配实际开盘时间（A股 9:30，美股/港股根据时区），只在交易日触发
  - [x] 加密货币市场：匹配逻辑时间点（如 00:00），每天都会触发
- [x] 实现交易日判断逻辑（股票市场排除节假日）
- [x] 编写单元测试验证定时调用、时区处理和市场类型适配

## 3. 成交记录和参数兼容

### 3.1 get_trades 实现
- [x] 在 `engine/wealthdata/wealthdata.py` 中添加 `get_trades()` 函数
- [x] 从 `context._completed_orders` 提取成交记录
- [x] 转换为 JoinQuant 格式的字典
- [x] 编写单元测试验证成交记录格式

### 3.2 get_trade_days 市场类型适配
- [x] 创建 `engine/compat/trade_calendar.py` 模块，实现交易日历管理器
- [x] 实现交易日历数据加载（支持配置文件和默认数据）
- [x] 实现 `is_trade_day()` 和 `get_trade_days()` 方法
- [x] 修改 `engine/wealthdata/wealthdata.py` 中的 `get_trade_days()` 函数，集成交易日历
- [x] 根据市场类型返回不同的交易日列表：
  - [x] 股票市场：返回实际交易日（排除周末和节假日）
  - [x] 加密货币市场：返回所有日期（每天都是交易日）
- [x] 创建默认交易日历配置文件（包含常见节假日）
- [x] 编写单元测试验证交易日逻辑和节假日处理

### 3.3 get_bars 参数兼容
- [x] 修改 `engine/wealthdata/wealthdata.py` 中的 `get_bars()`，支持 `unit` 参数
- [x] `unit` 参数作为 `frequency` 的别名
- [x] 编写单元测试验证参数兼容性

### 3.4 简化 API 实现
- [x] 创建 `engine/compat/config.py` 模块
- [x] 实现 `set_benchmark()`（仅记录，不影响执行）
- [x] 实现 `set_option()`（仅记录，不影响执行）
- [x] 实现 `set_order_cost()`（仅记录，不影响执行）
- [x] 在策略加载时注入这些函数到策略模块命名空间

## 4. 测试和文档

### 4.1 策略迁移测试
- [x] 使用 `double_mean.py` 作为股票市场测试用例
- [x] 创建加密货币市场的策略测试用例（`double_mean_migrated.py`）
- [x] 修改策略代码以适配框架（最小修改）
- [x] 验证策略能够正常运行（分别测试股票和加密货币市场）
- [x] 验证市场类型识别和差异化处理逻辑
- [x] 记录迁移过程中遇到的问题和解决方案

### 4.2 单元测试
- [x] 为所有新增功能编写单元测试
- [x] 测试覆盖率 > 80%（67 个测试用例全部通过）
- [x] 验证边界情况和错误处理

### 4.3 集成测试
- [x] 创建完整的策略测试用例（`test_double_mean_migration.py`）
- [x] 验证定时运行、下单、持仓管理等功能的集成
- [x] 验证与现有功能的兼容性

### 4.4 文档更新
- [x] 更新 `PRD/JoinQuant迁移指南.md`，添加新 API 说明
- [x] 更新 `openspec/specs/strategy-development/spec.md`，添加新 API 文档
- [x] 创建 `double_mean_migrated.py` 迁移示例
- [x] 创建 `PRD/JoinQuant迁移指南-完整API列表.md` 完整 API 文档
- [x] 更新 README.md，添加 JoinQuant 兼容性说明

## 5. 代码审查和优化

### 5.1 代码审查
- [ ] 代码风格检查
- [ ] 性能影响评估
- [ ] 安全性检查

### 5.2 优化（如需要）
- [ ] 性能优化（如持仓字典的更新策略）
- [ ] 代码重构（如提取公共逻辑）
- [ ] 错误处理改进

