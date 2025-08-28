#!/bin/bash
# M3U8高速下载器启动脚本 (Linux/macOS)

echo "M3U8高速下载器启动中..."
echo

# 检查Python是否安装
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到Python3，请先安装Python 3.7或更高版本"
    echo "Ubuntu/Debian: sudo apt install python3 python3-pip python3-venv"
    echo "CentOS/RHEL: sudo yum install python3 python3-pip"
    echo "macOS: brew install python3"
    read -p "按回车键退出..."
    exit 1
fi

# 检查是否需要创建虚拟环境
if [ ! -d "venv" ]; then
    echo "正在创建虚拟环境..."
    python3 -m venv venv
    source venv/bin/activate
    echo "正在安装依赖包..."
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

# 启动程序
echo "启动M3U8高速下载器..."
python3 debug_launcher.py

# 检查退出状态
if [ $? -ne 0 ]; then
    echo
    echo "程序运行出错，请检查错误信息"
    read -p "按回车键退出..."
fi
