@echo off
chcp 65001 >nul
title 🌸 M3U8萌动下载器 ✨
color 0D

echo.
echo 🌸✨🌸✨🌸✨🌸✨🌸✨🌸✨🌸✨🌸✨🌸✨🌸
echo ✨                                           ✨
echo 🌸    🌸 M3U8萌动下载器 启动中... ✨        🌸  
echo ✨                                           ✨
echo 🌸    💖 可爱又强大的二次元视频下载工具     🌸
echo ✨                                           ✨
echo 🌸    🔗 GitHub: @shayuaidoudou              🌸
echo ✨                                           ✨
echo 🌸✨🌸✨🌸✨🌸✨🌸✨🌸✨🌸✨🌸✨🌸✨🌸
echo.

echo 💫 正在检查依赖和启动程序...

REM 检查Python是否安装
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ 错误: 未找到Python，请先安装Python 3.7或更高版本
    echo 📥 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

REM 使用安装脚本启动
python install.py

if %errorlevel% neq 0 (
    echo.
    echo 💔 程序运行出错，请检查错误信息
    pause
)

echo.
echo 💕 感谢使用M3U8萌动下载器！ (´∀`)
pause