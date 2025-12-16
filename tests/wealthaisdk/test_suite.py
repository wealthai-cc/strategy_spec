"""
WealthAI SDK 完整测试套件

运行所有 WealthAI SDK 相关的测试
"""

import unittest
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# 导入所有测试模块
from tests.wealthaisdk.test_trading import TestTradingFunctions
from tests.wealthaisdk.test_data_utils import TestDataUtils
from tests.wealthaisdk.test_config import TestConfig
from tests.wealthaisdk.test_exceptions import TestExceptions


def create_test_suite():
    """创建完整的测试套件"""
    suite = unittest.TestSuite()
    loader = unittest.TestLoader()
    
    # 添加交易功能测试
    suite.addTest(loader.loadTestsFromTestCase(TestTradingFunctions))
    
    # 添加数据工具测试
    suite.addTest(loader.loadTestsFromTestCase(TestDataUtils))
    
    # 添加配置管理测试
    suite.addTest(loader.loadTestsFromTestCase(TestConfig))
    
    # 添加异常处理测试
    suite.addTest(loader.loadTestsFromTestCase(TestExceptions))
    
    return suite


def run_all_tests():
    """运行所有测试"""
    print("=" * 60)
    print("WealthAI SDK 测试套件")
    print("=" * 60)
    
    # 创建测试套件
    suite = create_test_suite()
    
    # 运行测试
    runner = unittest.TextTestRunner(
        verbosity=2,
        descriptions=True,
        failfast=False
    )
    
    result = runner.run(suite)
    
    # 输出测试结果摘要
    print("\n" + "=" * 60)
    print("测试结果摘要")
    print("=" * 60)
    print(f"总测试数: {result.testsRun}")
    print(f"成功: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"失败: {len(result.failures)}")
    print(f"错误: {len(result.errors)}")
    
    if result.failures:
        print("\n失败的测试:")
        for test, traceback in result.failures:
            print(f"  - {test}")
    
    if result.errors:
        print("\n错误的测试:")
        for test, traceback in result.errors:
            print(f"  - {test}")
    
    # 返回是否所有测试都通过
    return len(result.failures) == 0 and len(result.errors) == 0


if __name__ == '__main__':
    """直接运行此文件时执行所有测试"""
    success = run_all_tests()
    
    if success:
        print("\n🎉 所有测试通过！")
        sys.exit(0)
    else:
        print("\n❌ 部分测试失败，请检查上述错误信息")
        sys.exit(1)