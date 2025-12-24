#!/usr/bin/env python3
"""
React 服务器诊断工具

用于检查 React 服务器启动问题
"""

import sys
import subprocess
import socket
from pathlib import Path

def check_port(port):
    """检查端口是否被占用"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            result = s.connect_ex(('127.0.0.1', port))
            return result == 0
    except:
        return False

def check_npm():
    """检查 npm 是否可用"""
    try:
        result = subprocess.run(['npm', '--version'], capture_output=True, timeout=5)
        return result.returncode == 0
    except:
        return False

def check_node_modules():
    """检查 node_modules 是否存在"""
    react_dir = Path(__file__).parent / "visualization" / "react-template"
    return (react_dir / "node_modules").exists()

def main():
    print("=" * 60)
    print("React 服务器诊断工具")
    print("=" * 60)
    print()
    
    # 检查端口
    port = 5173
    print(f"1. 检查端口 {port}...")
    if check_port(port):
        print(f"   ✅ 端口 {port} 已被占用（可能有服务器在运行）")
        print(f"   💡 尝试访问: http://localhost:{port}")
    else:
        print(f"   ⚠️  端口 {port} 未被占用")
    print()
    
    # 检查 npm
    print("2. 检查 npm...")
    if check_npm():
        result = subprocess.run(['npm', '--version'], capture_output=True, text=True)
        print(f"   ✅ npm 可用 (版本: {result.stdout.strip()})")
    else:
        print(f"   ❌ npm 不可用，请安装 Node.js: https://nodejs.org/")
    print()
    
    # 检查 node_modules
    print("3. 检查依赖...")
    react_dir = Path(__file__).parent / "visualization" / "react-template"
    if check_node_modules():
        print(f"   ✅ node_modules 存在")
    else:
        print(f"   ⚠️  node_modules 不存在")
        print(f"   💡 运行: cd {react_dir} && npm install")
    print()
    
    # 检查 package.json
    print("4. 检查 package.json...")
    package_json = react_dir / "package.json"
    if package_json.exists():
        print(f"   ✅ package.json 存在")
    else:
        print(f"   ❌ package.json 不存在: {package_json}")
    print()
    
    # 建议
    print("=" * 60)
    print("建议操作:")
    print("=" * 60)
    print()
    print("如果端口未被占用，尝试手动启动:")
    print(f"  cd {react_dir}")
    print("  npm run dev")
    print()
    print("如果端口已被占用，直接访问:")
    print("  http://localhost:5173")
    print()

if __name__ == "__main__":
    main()

