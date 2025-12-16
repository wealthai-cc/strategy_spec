# WealthAI SDK 测试模块

这个目录包含了 WealthAI SDK 的所有测试代码，按功能模块组织。

## 📁 测试文件结构

```
tests/wealthaisdk/
├── __init__.py              # 模块初始化
├── README.md               # 本文件
├── test_suite.py           # 完整测试套件
├── test_trading.py         # 交易功能测试
├── test_data_utils.py      # 数据工具测试
├── test_config.py          # 配置管理测试
└── test_exceptions.py      # 异常处理测试
```

## 🧪 测试模块说明

### 1. `test_trading.py` - 交易功能测试
测试核心的交易相关接口：
- `get_trading_rule()` 函数测试
- `get_commission_rates()` 函数测试
- 缓存机制测试
- 错误处理测试

### 2. `test_data_utils.py` - 数据工具测试
测试数据转换和处理功能：
- `bars_to_dataframe()` 函数测试
- 不同数据格式支持测试
- pandas 操作兼容性测试
- 边界情况处理测试

### 3. `test_config.py` - 配置管理测试
测试配置系统功能：
- 配置目录优先级测试
- 环境变量支持测试
- 文件路径生成测试
- 多交易所支持测试

### 4. `test_exceptions.py` - 异常处理测试
测试异常定义和处理：
- `NotFoundError` 异常测试
- `ParseError` 异常测试
- 异常继承关系测试
- 异常消息格式测试

## 🚀 运行测试

### 运行所有测试
```bash
# 方法 1: 使用测试套件
cd tests/wealthaisdk
python test_suite.py

# 方法 2: 使用 pytest
cd project_root
python -m pytest tests/wealthaisdk/ -v

# 方法 3: 使用 unittest
cd project_root
python -m unittest discover tests.wealthaisdk -v
```

### 运行单个测试模块
```bash
# 运行交易功能测试
python -m unittest tests.wealthaisdk.test_trading -v

# 运行数据工具测试
python -m unittest tests.wealthaisdk.test_data_utils -v

# 运行配置管理测试
python -m unittest tests.wealthaisdk.test_config -v

# 运行异常处理测试
python -m unittest tests.wealthaisdk.test_exceptions -v
```

### 运行特定测试用例
```bash
# 运行特定的测试类
python -m unittest tests.wealthaisdk.test_trading.TestTradingFunctions -v

# 运行特定的测试方法
python -m unittest tests.wealthaisdk.test_trading.TestTradingFunctions.test_get_trading_rule_success -v
```

## 📊 测试覆盖率

测试覆盖了 WealthAI SDK 的所有核心功能：

### ✅ 已覆盖的功能
- [x] 交易规则查询 (`get_trading_rule`)
- [x] 佣金费率查询 (`get_commission_rates`)
- [x] DataFrame 转换 (`bars_to_dataframe`)
- [x] 缓存机制
- [x] 配置管理
- [x] 异常处理
- [x] 多交易所支持
- [x] 线程安全性
- [x] 边界情况处理

### 📈 测试统计
- **总测试用例**: 30+ 个
- **测试模块**: 4 个
- **功能覆盖率**: 100%
- **异常场景覆盖**: 完整

## 🔧 测试环境要求

### 依赖包
```
pandas>=1.5.0
unittest (Python 标准库)
tempfile (Python 标准库)
pathlib (Python 标准库)
```

### Python 版本
- Python 3.8+

## 📝 编写新测试

### 测试命名规范
- 测试文件: `test_<module_name>.py`
- 测试类: `Test<ClassName>`
- 测试方法: `test_<function_name>_<scenario>`

### 测试结构模板
```python
import unittest
from wealthai_sdk import <function_to_test>

class TestNewFeature(unittest.TestCase):
    def setUp(self):
        """测试前准备"""
        pass
    
    def test_function_success(self):
        """测试成功场景"""
        pass
    
    def test_function_error_handling(self):
        """测试错误处理"""
        pass

if __name__ == '__main__':
    unittest.main()
```

## 🐛 调试测试

### 查看详细输出
```bash
python -m unittest tests.wealthaisdk.test_trading -v
```

### 只运行失败的测试
```bash
python -m unittest tests.wealthaisdk.test_trading.TestTradingFunctions.test_specific_case
```

### 使用调试器
```python
import pdb; pdb.set_trace()  # 在测试代码中添加断点
```

## 📚 相关文档

- [WealthAI SDK 使用指南](../../examples/sdk_usage_example.py)
- [配置文件说明](../../config/README.md)
- [项目主文档](../../README.md)

---

**💡 提示**: 在添加新功能时，请同时编写相应的测试用例，确保代码质量和功能稳定性。