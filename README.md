# 🌸 M3U8萌动下载器 ✨

> 💖 一个超可爱的二次元风格M3U8视频下载工具 (´∀`)

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![PySide6](https://img.shields.io/badge/PySide6-6.0+-green.svg)](https://wiki.qt.io/Qt_for_Python)
[![License](https://img.shields.io/badge/License-MIT-pink.svg)](LICENSE)
[![GitHub](https://img.shields.io/badge/GitHub-@shayuaidoudou-purple.svg)](https://github.com/shayuaidoudou/m3u8-anime-downloader)

## 🌟 特色功能

<table>
<tr>
<td width="50%">

### 🎨 界面设计
- 💖 **二次元萌系风格** - 独特的粉紫配色方案
- ✨ **现代化组件** - 圆角设计、渐变背景、阴影效果
- 🌙 **流畅动画** - 悬停效果、加载动画、状态转换
- 📱 **响应式布局** - 适配不同屏幕尺寸

</td>
<td width="50%">

### 🚀 核心功能
- ⚡ **多线程下载** - 1-32线程并发，速度飞快
- 🔐 **AES解密支持** - 自动处理加密视频流
- 🛡️ **智能反PA** - 内置多种网站适配模板
- 📊 **实时监控** - 进度条、速度显示、状态追踪

</td>
</tr>
<tr>
<td width="50%">

### 🛠️ 高级特性
- 🔧 **自定义请求头** - 灵活配置各种网站参数
- 📋 **任务管理** - 批量下载、任务队列、状态管理
- 💾 **智能命名** - 自动提取标题、避免文件冲突
- 🎯 **错误处理** - 友好提示、自动重试、日志记录

</td>
<td width="50%">

### 💕 用户体验
- 🎀 **可爱提示** - 萌萌的成功/错误消息
- 🌸 **一键启动** - 自动检查依赖、一键安装
- 📚 **详细文档** - 完整的使用指南和故障排除
- 🎵 **贴心设计** - 状态栏提示、工具提示、快捷操作

</td>
</tr>
</table>

## 📸 界面预览

![image-20250828215408502](https://cdn.jsdelivr.net/gh/shayuaidoudou/Pictures@master/image-20250828215408502.png)

![image-20250828215418634](https://cdn.jsdelivr.net/gh/shayuaidoudou/Pictures@master/image-20250828215418634.png)

![image-20250828215424829](https://cdn.jsdelivr.net/gh/shayuaidoudou/Pictures@master/image-20250828215424829.png)

*🌸 萌萌哒的主界面 - 二次元风格设计*

</div>

### ✨ 界面特色

- 🎨 **粉紫渐变配色** - 梦幻的二次元色彩
- 💫 **流畅动画效果** - 现代化的视觉体验  
- 🌟 **可爱图标设计** - 每个功能都有萌萌的表情
- 📱 **响应式布局** - 自适应不同屏幕尺寸

## 🚀 快速开始

### 环境要求

- Python 3.8 或更高版本
- Windows / macOS / Linux

### 安装依赖

```bash
git clone https://github.com/shayuaidoudou/m3u8-anime-downloader.git
cd m3u8-anime-downloader
pip install -r requirements.txt
```

### 运行程序

```bash
# 直接运行主程序
python main.py

# 或使用启动器（自动检查依赖）
python launcher.py
```

### 批处理运行（Windows）

```bash
# 双击运行
run.bat
```

## 💝 使用指南

### 基本使用

1. **输入M3U8链接** 🎵 - 在"视频链接"输入框中粘贴M3U8视频链接
2. **选择保存位置** 💝 - 点击"浏览"按钮选择视频保存路径
3. **设置下载参数** 🌟 - 调整线程数（建议15-30）
4. **开始下载** 🚀 - 点击"添加萌萌任务"开始下载

### 高级功能

#### 🛡️ 反爬虫设置
- **通用反PA** - 适用于大多数网站
- **移动端模拟** - 模拟手机浏览器访问
- **自定义请求头** - 手动配置请求头

#### 🎀 任务管理
- **实时进度** - 查看下载进度和速度
- **状态监控** - 萌萌的状态图标和消息
- **批量下载** - 支持同时下载多个任务

## 🔧 高级配置

### 自定义请求头示例

```json
{
    "referer": "https://example.com/",
    "origin": "https://example.com",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}
```

### 配置文件

可以编辑 `config.py` 文件来自定义默认设置：

```python
DEFAULT_CONFIG = {
    'max_workers': 16,          # 默认线程数
    'max_retries': 3,           # 重试次数
    'timeout': 30,              # 超时时间
    'window_width': 1200,       # 窗口宽度
    'window_height': 900,       # 窗口高度
}
```

## 📚 文档

- [📖 快速使用指南](快速使用指南.md)
- [🔧 故障排除指南](故障排除指南.md)
- [📋 使用说明](使用说明.md)

## 🤝 贡献指南

我们欢迎所有形式的贡献！无论是Bug报告、功能建议还是代码贡献都非常appreciated ✨

### 🐛 报告Bug
- 使用GitHub Issues报告bug
- 请提供详细的复现步骤
- 包含你的系统环境信息

### ✨ 建议功能
- 在Issues中描述你的想法
- 解释为什么这个功能会有用
- 欢迎提供设计方案

### 💻 代码贡献
1. 🍴 Fork 本仓库
2. 🌿 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 💝 提交你的更改 (`git commit -m '✨ Add some AmazingFeature'`)
4. 📤 推送到分支 (`git push origin feature/AmazingFeature`)
5. 🎯 创建 Pull Request

### 📝 提交规范
```
✨ feat: 新功能
🐛 fix: Bug修复
📚 docs: 文档更新
🎨 style: 代码格式
♻️ refactor: 重构
⚡ perf: 性能优化
🧪 test: 测试相关
```

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 💕 致谢

- 感谢所有贡献者的支持 ✨
- 特别感谢二次元文化的灵感来源 🌸
- Made with ❤️ for anime fans

## 🔗 相关链接

- [项目GitHub](https://github.com/shayuaidoudou/m3u8-anime-downloader)
- [作者博客](https://blog.csdn.net/m0_73641772?type=blog)
- [问题反馈](https://github.com/shayuaidoudou/m3u8-anime-downloader/issues)

---

> 💫 如果这个项目对你有帮助，请给个 ⭐ Star 支持一下吧！ (´∀`) ✨
