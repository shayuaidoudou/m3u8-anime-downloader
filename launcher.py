#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
M3U8高速下载器启动器
处理依赖检查和错误处理
"""

import sys
import subprocess
import importlib.util
from pathlib import Path


def check_python_version():
    """检查Python版本"""
    if sys.version_info < (3, 7):
        print("错误: 需要Python 3.7或更高版本")
        print(f"当前版本: {sys.version}")
        return False
    return True


def check_dependencies():
    """检查依赖包"""
    required_packages = [
        'PySide6',
        'requests', 
        'cryptography',
        'aiohttp'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        if importlib.util.find_spec(package) is None:
            missing_packages.append(package)
    
    if missing_packages:
        print("错误: 缺少以下依赖包:")
        for package in missing_packages:
            print(f"  - {package}")
        print("\n请运行以下命令安装依赖:")
        print("pip install -r requirements.txt")
        return False
    
    return True


def install_dependencies():
    """自动安装依赖"""
    print("正在安装依赖包...")
    try:
        subprocess.check_call([
            sys.executable, '-m', 'pip', 'install', 
            '-r', 'requirements.txt'
        ])
        print("依赖安装完成!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"依赖安装失败: {e}")
        return False


def main():
    """主函数"""
    print("M3U8高速下载器启动器")
    print("=" * 40)
    
    # 检查Python版本
    if not check_python_version():
        input("按回车键退出...")
        return 1
    
    # 检查依赖
    if not check_dependencies():
        print("\n是否自动安装依赖包？(y/n): ", end="")
        choice = input().lower().strip()
        
        if choice == 'y':
            if not install_dependencies():
                input("按回车键退出...")
                return 1
            
            # 重新检查依赖
            if not check_dependencies():
                print("依赖安装后仍然缺少必要包")
                input("按回车键退出...")
                return 1
        else:
            input("按回车键退出...")
            return 1
    
    # 启动主程序
    print("正在启动M3U8高速下载器...")
    try:
        from main import main as app_main
        return app_main()
    except Exception as e:
        print(f"启动失败: {e}")
        import traceback
        traceback.print_exc()
        input("按回车键退出...")
        return 1


if __name__ == "__main__":
    sys.exit(main())
