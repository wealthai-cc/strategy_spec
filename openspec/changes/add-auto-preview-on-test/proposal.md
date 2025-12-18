# Change: 策略测试后自动打开可视化预览

## Why

当前策略测试流程存在以下问题：

1. **需要手动操作**：测试完成后需要手动启动 React 模板、打开浏览器、上传文件，步骤繁琐
2. **无法快速预览**：开发者无法立即看到策略测试结果，需要额外的操作步骤
3. **缺少框架验证可视化**：无法直观地看到策略框架是否支持策略运行
4. **缺少策略合理性判断**：无法快速判断策略逻辑是否合理

需要改进：
- 测试策略后自动打开浏览器预览
- 自动加载刚生成的 JSON 数据，无需手动上传
- 在可视化中展示框架支持情况
- 在可视化中展示策略合理性分析

## What Changes

- **ADDED**: 自动预览功能
  - 修改 `test_strategy.py` 在生成 JSON 后自动启动预览
  - 自动启动简单的 HTTP 服务器提供 JSON 文件访问
  - 自动打开浏览器并加载数据
  - 支持 `--no-preview` 参数禁用自动预览

- **ADDED**: 框架支持情况展示
  - 在 React 模板中添加框架验证面板
  - 显示已注入的函数（g、log、run_daily 等）
  - 显示 wealthdata API 可用性
  - 使用颜色标记（绿色=正常，红色=异常）

- **ADDED**: 策略合理性分析展示
  - 在 React 模板中添加策略分析面板
  - 显示策略执行状态（成功/失败）
  - 显示订单生成情况（是否有订单、订单类型）
  - 显示策略逻辑触发情况
  - 显示数据验证结果（价格条件、技术指标等）

- **MODIFIED**: 数据收集器
  - 添加框架验证结果到 JSON 导出
  - 添加策略执行状态信息
  - 添加数据验证结果

- **MODIFIED**: React 模板
  - 支持从本地 HTTP 服务器加载数据
  - 添加框架验证面板组件
  - 添加策略分析面板组件
  - 优化自动加载体验

## Impact

- **Affected specs**: 
  - `strategy-testing` - 修改策略测试可视化规范
- **Affected code**: 
  - 修改 `test_strategy.py`（添加自动预览功能）
  - 修改 `visualization/data_collector.py`（添加框架验证数据收集）
  - 修改 `visualization/data_exporter.py`（导出框架验证信息）
  - 新增 `visualization/react-template/src/components/FrameworkVerification.tsx`
  - 新增 `visualization/react-template/src/components/StrategyAnalysis.tsx`
  - 修改 `visualization/react-template/src/App.tsx`（集成新组件）
- **Affected docs**: 
  - 更新测试工具使用文档
  - 更新 React 模板使用说明

## Design Considerations

### 自动预览实现方式

**方案 1（推荐）**：启动简单的 HTTP 服务器
- 使用 Python `http.server` 模块
- 在项目根目录启动，提供 JSON 文件访问
- 自动打开浏览器并传递 URL 参数
- 优点：简单、无需额外依赖
- 缺点：需要手动停止服务器

**方案 2**：使用 Vite 代理
- 配置 Vite 开发服务器代理到本地文件
- 需要 React 模板始终运行
- 优点：集成度高
- 缺点：需要 React 模板先启动

**选择**：方案 1，更灵活，不依赖 React 模板运行状态

### 框架验证数据

在 JSON 数据中添加 `framework_verification` 字段：
```json
{
  "framework_verification": {
    "g": true,
    "log": true,
    "run_daily": true,
    "order_value": true,
    "order_target": true,
    "wealthdata_api": true,
    "errors": []
  }
}
```

### 策略分析数据

在 JSON 数据中添加 `strategy_analysis` 字段：
```json
{
  "strategy_analysis": {
    "execution_status": "success",
    "has_orders": true,
    "order_count": 1,
    "data_validation": {
      "price_condition_met": true,
      "ma5_calculated": true
    },
    "warnings": []
  }
}
```

### 浏览器打开方式

- 使用 Python `webbrowser` 模块
- 传递 URL 参数：`?data=http://localhost:8000/data.json`
- 支持不同操作系统（macOS、Linux、Windows）

