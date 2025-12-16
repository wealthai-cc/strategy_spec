## 1. 核心实现
- [ ] 1.1 实现线程局部存储机制（context_local.py）
- [ ] 1.2 创建 jqdata.py 兼容模块
- [ ] 1.3 实现 get_price() API（映射到 context.history()）
- [ ] 1.4 实现 get_bars() API（get_price 的别名）
- [ ] 1.5 实现 DataFrame 转换函数（bars_to_dataframe）
- [ ] 1.6 引擎集成（在执行前设置 Context，执行后清理）

## 2. API 实现
- [ ] 2.1 实现参数兼容性处理（count, end_date, frequency, fields）
- [ ] 2.2 处理不支持的参数（fq, skip_paused）- 接受但忽略
- [ ] 2.3 实现数据范围检查和警告机制
- [ ] 2.4 实现 get_available_data_range() 方法（可选）

## 3. 测试
- [ ] 3.1 单元测试：线程局部存储机制
- [ ] 3.2 单元测试：get_price() API
- [ ] 3.3 单元测试：DataFrame 转换
- [ ] 3.4 集成测试：完整策略执行流程
- [ ] 3.5 测试：并发执行时的 Context 隔离

## 4. 文档
- [ ] 4.1 编写零代码迁移指南
- [ ] 4.2 创建 API 映射文档
- [ ] 4.3 提供迁移示例策略（展示直接复制代码）
- [ ] 4.4 文档化数据范围限制和差异说明

## 5. 扩展（可选）
- [ ] 5.1 实现 get_fundamentals() API（如需要）
- [ ] 5.2 实现其他常用 jqdata API
- [ ] 5.3 提供迁移工具（自动替换 import 语句）

