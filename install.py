#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
M3U8萌动下载器 - 一键安装脚本
自动安装依赖并启动程序
"""

import sys
import subprocess
import importlib.util
import os
from pathlib import Path

def print_banner():
    """打印欢迎横幅"""
    banner = """
    🌸✨🌸✨🌸✨🌸✨🌸✨🌸✨🌸✨🌸✨🌸✨🌸
    ✨                                           ✨
    🌸    🌸 M3U8萌动下载器 一键安装 ✨           🌸  
    ✨                                           ✨
    🌸    💖 可爱又强大的二次元视频下载工具     🌸
    ✨                                           ✨
    🌸    🔗 GitHub: @shayuaidoudou              🌸
    ✨                                           ✨
    🌸✨🌸✨🌸✨🌸✨🌸✨🌸✨🌸✨🌸✨🌸✨🌸
    """
    print(banner)

def check_python_version():
    """检查Python版本"""
    if sys.version_info < (3, 7):
        print("❌ 错误: 需要Python 3.7或更高版本")
        print(f"   当前版本: {sys.version}")
        input("按回车键退出...")
        return False
    else:
        print(f"✅ Python版本检查通过: {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
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
        else:
            print(f"✅ {package} 已安装")
    
    if missing_packages:
        print(f"\n🔍 发现缺少以下依赖包:")
        for package in missing_packages:
            print(f"   ❌ {package}")
        return missing_packages
    else:
        print("\n🎉 所有依赖包都已安装！")
    
    return []

def install_dependencies():
    """安装依赖包"""
    print("\n🚀 开始安装依赖包...")
    try:
        # 先升级pip
        print("📦 正在升级pip...")
        subprocess.check_call([
            sys.executable, '-m', 'pip', 'install', '--upgrade', 'pip'
        ], stdout=subprocess.DEVNULL)
        
        # 安装依赖
        print("💫 正在安装项目依赖...")
        subprocess.check_call([
            sys.executable, '-m', 'pip', 'install', 
            '-r', 'requirements.txt'
        ])
        print("✅ 依赖安装完成!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 依赖安装失败: {e}")
        return False

def launch_app():
    """启动应用"""
    print("\n🌸 正在启动M3U8萌动下载器...")
    try:
        # 检查main.py是否存在
        if not Path("main.py").exists():
            print("❌ 找不到main.py文件，请确认文件完整性")
            return False
        
        # 启动主程序
        from main import main as app_main
        app_main()
        return True
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print_banner()
    
    # 检查Python版本
    if not check_python_version():
        return 1
    
    # 检查依赖
    missing = check_dependencies()
    
    if missing:
        print("\n🤔 是否自动安装缺少的依赖包？")
        choice = input("请输入 y/n (默认: y): ").lower().strip()
        
        if choice == 'n':
            print("📝 请手动执行以下命令安装依赖:")
            print("   pip install -r requirements.txt")
            input("按回车键退出...")
            return 1
        
        if not install_dependencies():
            print("💔 安装失败，请检查网络连接或手动安装")
            input("按回车键退出...")
            return 1
        
        # 重新检查依赖
        missing = check_dependencies()
        if missing:
            print("❌ 安装后仍然缺少必要包，请检查安装过程")
            input("按回车键退出...")
            return 1
    
    # 启动应用
    print("\n🎀 所有准备工作完成，即将启动萌萌的下载器...")
    input("按回车键继续...")
    
    if not launch_app():
        input("按回车键退出...")
        return 1
    
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n👋 再见啦~ (´∀`)")
        sys.exit(0)
    except Exception as e:
        print(f"\n💔 意外错误: {e}")
        input("按回车键退出...")
        sys.exit(1)
