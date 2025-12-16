#!/usr/bin/env python3
"""
验证测试结构重组是否成功
"""

import os
import sys
from pathlib import Path

def verify_test_structure():
    """验证测试文件结构"""
    print("🔍 验证 WealthAI SDK 测试结构...")
    
    # 项目根目录
    project_root = Path(__file__).parent
    tests_dir = project_root / "tests"
    wealthaisdk_tests_dir = tests_dir / "wealthaisdk"
    
    print(f"📁 项目根目录: {project_root}")
    print(f"📁 测试目录: {tests_dir}")
    print(f"📁 WealthAI SDK 测试目录: {wealthaisdk_tests_dir}")
    
    # 检查目录结构
    expected_files = [
        "__init__.py",
        "README.md", 
        "test_suite.py",
        "test_trading.py",
        "test_data_utils.py",
        "test_config.py",
        "test_exceptions.py"
    ]
    
    print("\n📋 检查测试文件:")
    all_files_exist = True
    
    for file_name in expected_files:
        file_path = wealthaisdk_tests_dir / file_name
        if file_path.exists():
            file_size = file_path.stat().st_size
            print(f"  ✅ {file_name} ({file_size} bytes)")
        else:
            print(f"  ❌ {file_name} - 文件不存在")
            all_files_exist = False
    
    # 检查原测试文件是否已删除
    old_test_file = tests_dir / "test_wealthai_sdk.py"
    if old_test_file.exists():
        print(f"  ⚠️  原测试文件仍存在: {old_test_file}")
        all_files_exist = False
    else:
        print(f"  ✅ 原测试文件已成功移除")
    
    # 尝试导入测试模块
    print("\n🔧 测试模块导入:")
    try:
        sys.path.insert(0, str(project_root))
        
        # 测试导入各个模块
        test_modules = [
            "tests.wealthaisdk.test_trading",
            "tests.wealthaisdk.test_data_utils", 
            "tests.wealthaisdk.test_config",
            "tests.wealthaisdk.test_exceptions"
        ]
        
        for module_name in test_modules:
            try:
                __import__(module_name)
                print(f"  ✅ {module_name}")
            except ImportError as e:
                print(f"  ❌ {module_name} - 导入失败: {e}")
                all_files_exist = False
    
    except Exception as e:
        print(f"  ❌ 模块导入测试失败: {e}")
        all_files_exist = False
    
    # 检查 WealthAI SDK 本身是否可用
    print("\n🚀 测试 WealthAI SDK 可用性:")
    try:
        from wealthai_sdk import get_trading_rule, get_commission_rates, bars_to_dataframe
        print("  ✅ WealthAI SDK 核心模块导入成功")
        
        from wealthai_sdk.exceptions import NotFoundError, ParseError
        print("  ✅ WealthAI SDK 异常模块导入成功")
        
    except ImportError as e:
        print(f"  ❌ WealthAI SDK 导入失败: {e}")
        all_files_exist = False
    
    # 总结
    print("\n" + "="*50)
    if all_files_exist:
        print("🎉 测试结构重组成功！")
        print("\n📚 使用方法:")
        print("  # 运行所有 WealthAI SDK 测试")
        print("  python tests/wealthaisdk/test_suite.py")
        print("")
        print("  # 运行单个测试模块")
        print("  python -m unittest tests.wealthaisdk.test_trading -v")
        print("")
        print("  # 使用 pytest 运行")
        print("  python -m pytest tests/wealthaisdk/ -v")
        return True
    else:
        print("❌ 测试结构重组存在问题，请检查上述错误")
        return False

if __name__ == "__main__":
    success = verify_test_structure()
    sys.exit(0 if success else 1)