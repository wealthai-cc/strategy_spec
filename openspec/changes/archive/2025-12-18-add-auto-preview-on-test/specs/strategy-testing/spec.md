## ADDED Requirements

### Requirement: 策略测试后自动打开可视化预览
策略测试工具 SHALL 在测试完成后自动打开浏览器预览，显示策略测试结果、框架验证和策略分析。

#### Scenario: 自动打开预览
- **WHEN** 策略测试完成并生成 JSON 数据文件
- **THEN** 系统自动启动 HTTP 服务器提供 JSON 文件访问
- **AND** 系统自动检测 React 模板是否运行
- **AND** 系统自动打开浏览器并加载数据
- **AND** 浏览器显示完整的可视化报告

#### Scenario: 框架验证可视化
- **WHEN** 数据加载完成
- **THEN** React 模板显示框架验证面板
- **AND** 显示所有框架功能的可用性（g、log、run_daily 等）
- **AND** 使用颜色标记状态（绿色=正常，红色=异常）
- **AND** 显示错误信息（如果有）

#### Scenario: 策略分析可视化
- **WHEN** 数据加载完成
- **THEN** React 模板显示策略分析面板
- **AND** 显示执行状态（成功/失败）
- **AND** 显示订单统计信息
- **AND** 显示数据验证结果
- **AND** 显示警告和错误列表

#### Scenario: 禁用自动预览
- **WHEN** 用户使用 `--no-preview` 参数运行测试
- **THEN** 系统不启动 HTTP 服务器
- **AND** 系统不打开浏览器
- **AND** 仍然生成 JSON 数据文件

#### Scenario: React 模板未运行处理
- **WHEN** React 模板未运行
- **THEN** 系统显示清晰的启动提示
- **AND** 仍然启动 HTTP 服务器
- **AND** 用户可以手动启动 React 模板后访问

## MODIFIED Requirements

### Requirement: 策略测试可视化报告生成
策略测试工具 SHALL 生成可视化报告，展示策略执行结果、K线图表、买卖点标记和统计信息。

#### Scenario: 自动预览集成
- **WHEN** 策略测试完成
- **THEN** 系统生成 JSON 数据文件
- **AND** 系统自动启动预览（除非使用 `--no-preview`）
- **AND** 浏览器自动打开并显示可视化报告

### Requirement: JSON 数据导出格式
策略测试工具 SHALL 支持将测试数据导出为标准化的 JSON 格式。

#### Scenario: 框架验证数据导出
- **WHEN** 导出 JSON 数据
- **THEN** 数据文件包含 `framework_verification` 字段
- **AND** 包含所有框架功能的可用性信息
- **AND** 包含错误信息（如果有）

#### Scenario: 策略分析数据导出
- **WHEN** 导出 JSON 数据
- **THEN** 数据文件包含 `strategy_analysis` 字段
- **AND** 包含执行状态信息
- **AND** 包含订单统计信息
- **AND** 包含数据验证结果
- **AND** 包含警告和错误信息

