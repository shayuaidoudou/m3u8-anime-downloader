# 🎨 资源文件夹

## 📁 文件说明

### 🖼️ 图标文件
- **`favicon.ico`** - 应用程序图标
  - 用途：GUI窗口图标、任务栏图标
  - 格式：ICO (推荐) 或 PNG
  - 尺寸：建议 32x32, 64x64, 128x128 多尺寸
  - 显示位置：
    - 🪟 窗口标题栏左上角
    - 📋 任务栏应用图标
    - 🖥️ Alt+Tab 切换窗口时的图标

## 💡 使用说明

### 🔧 技术实现
```python
# 在 MainWindow.setup_ui() 中设置窗口图标
icon_path = os.path.join(os.path.dirname(__file__), "assets", "favicon.ico")
if os.path.exists(icon_path):
    self.setWindowIcon(QIcon(icon_path))

# 在 main() 函数中设置应用图标
app.setWindowIcon(QIcon(icon_path))
```

### 📋 图标要求
- **格式支持**: ICO, PNG, JPG, SVG
- **推荐格式**: ICO（支持多尺寸）
- **文件大小**: 建议小于 100KB
- **透明背景**: 推荐使用透明背景

### 🎯 替换图标
如果要更换图标：
1. 将新图标文件保存为 `favicon.ico`
2. 确保文件格式正确
3. 重启应用即可看到新图标

---

> 💫 个性化图标让您的应用更有辨识度！ (´∀`) ✨
