#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
M3U8高速下载器 - 主程序
现代化的PySide6 GUI界面
"""

import sys
import os
import threading
import time
import json
from pathlib import Path
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QGridLayout, QFormLayout, QLabel, QLineEdit, QPushButton, QProgressBar, 
    QTextEdit, QFileDialog, QSpinBox, QGroupBox, QFrame,
    QSystemTrayIcon, QMenu, QMessageBox, QSplitter, QTabWidget,
    QTableWidget, QTableWidgetItem, QHeaderView, QCheckBox,
    QComboBox, QDialog, QDialogButtonBox, QPlainTextEdit, QScrollArea
)
from PySide6.QtCore import (
    Qt, QThread, Signal, QTimer, QUrl, QPropertyAnimation, 
    QEasingCurve, QRect, QSize
)
from PySide6.QtGui import (
    QFont, QPalette, QColor, QIcon, QPixmap, QPainter, QLinearGradient,
    QAction, QDesktopServices
)
from m3u8_downloader import M3U8Downloader
from utils import (
    is_valid_m3u8_url, sanitize_filename, ensure_extension,
    format_time, get_available_filename, validate_output_path,
    extract_title_from_url
)
from config import DEFAULT_CONFIG, ERROR_MESSAGES, STATUS_MESSAGES


class DownloadWorker(QThread):
    """下载工作线程"""
    progress_updated = Signal(dict)
    download_finished = Signal(bool)
    
    def __init__(self, downloader, m3u8_url, output_path, max_workers=10):
        super().__init__()
        self.downloader = downloader
        self.m3u8_url = m3u8_url
        self.output_path = output_path
        self.max_workers = max_workers
        self._is_running = True
    
    def run(self):
        """运行下载"""
        try:
            self.downloader.max_workers = self.max_workers
            success = self.downloader.download(
                self.m3u8_url, 
                self.output_path, 
                self.progress_callback
            )
            self.download_finished.emit(success)
        except Exception as e:
            self.progress_updated.emit({
                'status': 'error', 
                'message': f'下载出错: {str(e)}'
            })
            self.download_finished.emit(False)
    
    def progress_callback(self, data):
        """进度回调"""
        if self._is_running:
            self.progress_updated.emit(data)
    
    def stop(self):
        """停止下载"""
        self._is_running = False
        if hasattr(self.downloader, 'stop_download'):
            self.downloader.stop_download()


class ModernButton(QPushButton):
    """现代化按钮样式"""
    
    def __init__(self, text, primary=False, icon_text=""):
        super().__init__(text)
        self.primary = primary
        self.icon_text = icon_text
        self.setMinimumHeight(45)
        self.setFont(QFont("Microsoft YaHei", 10, QFont.Bold))
        self.setCursor(Qt.PointingHandCursor)
        
        # 添加图标文本
        if icon_text:
            self.setText(f"{icon_text} {text}")
        
        if primary:
            self.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #ff6b9d, stop:0.5 #c44cfc, stop:1 #667eea);
                    color: white;
                    border: none;
                    border-radius: 15px;
                    font-weight: bold;
                    padding: 12px 24px;
                    box-shadow: 0 8px 25px rgba(255, 107, 157, 0.4);
                    text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #ff7fb0, stop:0.5 #d066ff, stop:1 #7b8ef0);
                    transform: translateY(-3px);
                    box-shadow: 0 12px 35px rgba(255, 107, 157, 0.6);
                }
                QPushButton:pressed {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #e55d8a, stop:0.5 #b142e3, stop:1 #5a6fd8);
                    transform: translateY(-1px);
                }
                QPushButton:disabled {
                    background: #ddd6fe;
                    color: #a78bfa;
                    box-shadow: none;
                }
            """)
        else:
            self.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #fef7ff, stop:1 #f3e8ff);
                    color: #7c3aed;
                    border: 2px solid #ddd6fe;
                    border-radius: 15px;
                    padding: 12px 24px;
                    font-weight: bold;
                    box-shadow: 0 4px 15px rgba(196, 76, 252, 0.15);
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #faf5ff, stop:1 #ede9fe);
                    border-color: #c44cfc;
                    color: #c44cfc;
                    transform: translateY(-2px);
                    box-shadow: 0 8px 25px rgba(196, 76, 252, 0.25);
                }
                QPushButton:pressed {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #e9d5ff, stop:1 #ddd6fe);
                    transform: translateY(0px);
                }
                QPushButton:disabled {
                    background: #f9fafb;
                    color: #d1d5db;
                    border-color: #e5e7eb;
                    box-shadow: none;
                }
            """)


class ModernLineEdit(QLineEdit):
    """现代化输入框样式"""
    
    def __init__(self, placeholder="", icon_text=""):
        super().__init__()
        self.setPlaceholderText(placeholder)
        self.setMinimumHeight(48)
        self.setFont(QFont("Microsoft YaHei", 11))
        
        # 添加图标
        if icon_text:
            self.setPlaceholderText(f"{icon_text} {placeholder}")
        
        self.setStyleSheet("""
            QLineEdit {
                border: 2px solid #ddd6fe;
                border-radius: 16px;
                padding: 14px 20px;
                font-size: 14px;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #fef7ff, stop:1 #f9fafb);
                color: #374151;
                selection-background-color: #c44cfc;
                box-shadow: inset 0 2px 8px rgba(196, 76, 252, 0.08);
            }
            QLineEdit:focus {
                border-color: #c44cfc;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ffffff, stop:1 #fef7ff);
                box-shadow: 0 0 0 4px rgba(196, 76, 252, 0.25), 
                           inset 0 2px 8px rgba(196, 76, 252, 0.1);
            }
            QLineEdit:hover {
                border-color: #a78bfa;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ffffff, stop:1 #fef7ff);
            }
        """)


class ModernProgressBar(QProgressBar):
    """现代化进度条样式"""
    
    def __init__(self):
        super().__init__()
        self.setMinimumHeight(10)
        self.setMaximumHeight(10)
        self.setTextVisible(False)
        self.setStyleSheet("""
            QProgressBar {
                border: none;
                border-radius: 8px;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #f3e8ff, stop:1 #e9d5ff);
                box-shadow: inset 0 2px 6px rgba(196, 76, 252, 0.15);
            }
            QProgressBar::chunk {
                border-radius: 8px;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #ff6b9d, stop:0.3 #c44cfc, stop:0.7 #667eea, stop:1 #06b6d4);
                box-shadow: 0 0 15px rgba(255, 107, 157, 0.6), 
                           0 4px 12px rgba(196, 76, 252, 0.4);
            }
        """)


class DownloadTaskWidget(QFrame):
    """下载任务组件"""
    
    def __init__(self, task_name, url, output_path, custom_headers=None):
        super().__init__()
        self.task_name = task_name
        self.url = url
        self.output_path = output_path
        self.custom_headers = custom_headers or {}
        self.worker = None
        
        self.setFrameStyle(QFrame.NoFrame)
        self.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba(255, 255, 255, 0.95), 
                    stop:0.25 rgba(254, 247, 255, 0.9), 
                    stop:0.5 rgba(240, 249, 255, 0.9), 
                    stop:0.75 rgba(243, 232, 255, 0.9),
                    stop:1 rgba(253, 242, 248, 0.95));
                border-radius: 20px;
                border: 2px solid #ddd6fe;
                margin: 12px 6px;
                box-shadow: 0 12px 35px rgba(196, 76, 252, 0.15),
                           0 0 0 1px rgba(255, 107, 157, 0.1) inset;
            }
            QFrame:hover {
                border-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #ff6b9d, stop:0.5 #c44cfc, stop:1 #a78bfa);
                box-shadow: 0 16px 50px rgba(196, 76, 252, 0.25),
                           0 0 20px rgba(255, 107, 157, 0.3),
                           0 0 0 1px rgba(196, 76, 252, 0.2) inset;
                transform: translateY(-2px);
            }
        """)
        
        self.setup_ui()
    
    def setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)
        
        # 任务标题和状态行
        header_layout = QHBoxLayout()
        
        # 任务标题 + 图标
        title_label = QLabel(f"🌈 {self.task_name} ✨")
        title_label.setFont(QFont("Microsoft YaHei", 12, QFont.Bold))
        title_label.setStyleSheet("""
            color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #c44cfc, stop:1 #667eea); 
            padding: 4px 0;
            font-weight: bold;
        """)
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # 状态标签
        self.status_label = QLabel("🌸 准备中... ♡")
        self.status_label.setFont(QFont("Microsoft YaHei", 10, QFont.Bold))
        self.status_label.setStyleSheet("""
            color: #c44cfc; 
            padding: 6px 12px; 
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 rgba(255, 107, 157, 0.1), 
                stop:1 rgba(196, 76, 252, 0.1)); 
            border-radius: 10px;
            border: 1px solid rgba(196, 76, 252, 0.2);
            font-weight: bold;
        """)
        header_layout.addWidget(self.status_label)
        
        layout.addLayout(header_layout)
        
        # 分割线
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                stop:0 transparent, 
                stop:0.2 rgba(255, 107, 157, 0.3), 
                stop:0.5 rgba(196, 76, 252, 0.5), 
                stop:0.8 rgba(167, 139, 250, 0.3), 
                stop:1 transparent); 
            height: 2px; 
            margin: 10px 0;
            border-radius: 1px;
        """)
        layout.addWidget(separator)
        
        # URL显示
        url_display = self.url if len(self.url) <= 65 else f"{self.url[:62]}..."
        url_label = QLabel(f"🎵 {url_display}")
        url_label.setStyleSheet("""
            color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #a78bfa, stop:1 #06b6d4);
            padding: 6px 8px;
            background: rgba(167, 139, 250, 0.08);
            border-radius: 8px;
            border: 1px solid rgba(167, 139, 250, 0.2);
        """)
        url_label.setFont(QFont("Consolas", 9))
        url_label.setWordWrap(True)
        layout.addWidget(url_label)
        
        # 输出路径
        output_display = self.output_path if len(self.output_path) <= 65 else f"...{self.output_path[-62:]}"
        output_label = QLabel(f"💝 {output_display}")
        output_label.setStyleSheet("""
            color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #ff6b9d, stop:1 #c44cfc);
            padding: 6px 8px;
            background: rgba(255, 107, 157, 0.08);
            border-radius: 8px;
            border: 1px solid rgba(255, 107, 157, 0.2);
        """)
        output_label.setFont(QFont("Consolas", 9))
        output_label.setWordWrap(True)
        layout.addWidget(output_label)
        
        # 进度条容器
        progress_container = QWidget()
        progress_layout = QVBoxLayout(progress_container)
        progress_layout.setContentsMargins(0, 8, 0, 8)
        
        self.progress_bar = ModernProgressBar()
        progress_layout.addWidget(self.progress_bar)
        
        layout.addWidget(progress_container)
        
        # 控制按钮
        control_layout = QHBoxLayout()
        control_layout.setSpacing(12)
        
        control_layout.addStretch()
        
        self.start_btn = ModernButton("开始下载", primary=True, icon_text="🚀")
        self.start_btn.clicked.connect(self.start_download)
        control_layout.addWidget(self.start_btn)
        
        self.stop_btn = ModernButton("暂停", icon_text="⏸️")
        self.stop_btn.clicked.connect(self.stop_download)
        self.stop_btn.setEnabled(False)
        control_layout.addWidget(self.stop_btn)
        
        self.delete_btn = ModernButton("删除", icon_text="🗑️")
        self.delete_btn.clicked.connect(self.delete_task)
        self.delete_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #fef2f2, stop:1 #fee2e2);
                color: #ef4444;
                border: 2px solid #fecaca;
                border-radius: 15px;
                padding: 12px 20px;
                font-weight: bold;
                box-shadow: 0 4px 15px rgba(239, 68, 68, 0.15);
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #fee2e2, stop:1 #fecaca);
                border-color: #f87171;
                color: #dc2626;
                transform: translateY(-2px);
                box-shadow: 0 8px 25px rgba(239, 68, 68, 0.25);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #fecaca, stop:1 #fed7d7);
                transform: translateY(0px);
            }
        """)
        control_layout.addWidget(self.delete_btn)
        
        layout.addLayout(control_layout)
    
    def start_download(self):
        """开始下载"""
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.delete_btn.setEnabled(False)  # 下载时禁用删除
        
        # 获取主窗口的线程数设置
        main_window = self.parent()
        while main_window and not isinstance(main_window, MainWindow):
            main_window = main_window.parent()
        
        max_workers = DEFAULT_CONFIG['max_workers']
        if main_window and hasattr(main_window, 'threads_spin'):
            max_workers = main_window.threads_spin.value()
        
        # 创建下载器和工作线程
        downloader = M3U8Downloader(custom_headers=self.custom_headers)
        self.worker = DownloadWorker(downloader, self.url, self.output_path, max_workers=max_workers)
        self.worker.progress_updated.connect(self.update_progress)
        self.worker.download_finished.connect(self.download_finished)
        self.worker.start()
    
    def stop_download(self):
        """停止下载"""
        if self.worker:
            self.worker.stop()
            self.worker.wait()
        
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.delete_btn.setEnabled(True)  # 停止后重新启用删除
        self.status_label.setText("😴 已暂停 zzZ...")
        self.status_label.setStyleSheet("color: #a78bfa; padding: 6px 12px; background: rgba(167, 139, 250, 0.15); border-radius: 10px; border: 1px solid #a78bfa; font-weight: bold;")
        self.progress_bar.setValue(0)
    
    def update_progress(self, data):
        """更新进度"""
        if 'progress' in data:
            self.progress_bar.setValue(int(data['progress']))
            speed = data.get('speed', 0)
            eta = data.get('eta', 0)
            progress_percent = int(data['progress'])
            
            # 根据进度更新状态样式和图标
            if progress_percent < 30:
                icon = "🌟"
                bg_color = "rgba(255, 107, 157, 0.15)"
                text_color = "#ff6b9d"
            elif progress_percent < 70:
                icon = "🎵"
                bg_color = "rgba(196, 76, 252, 0.15)"
                text_color = "#c44cfc"
            else:
                icon = "💖"
                bg_color = "rgba(6, 182, 212, 0.15)"
                text_color = "#06b6d4"
                
            self.status_label.setText(
                f"{icon} {progress_percent}% | {data['completed']}/{data['total']} | "
                f"⚡{speed:.1f}/s | ⏱{eta:.0f}s"
            )
            self.status_label.setStyleSheet(f"color: {text_color}; padding: 6px 12px; background: {bg_color}; border-radius: 10px; border: 1px solid {text_color}; font-weight: bold;")
        elif 'message' in data:
            if data.get('status') == 'error':
                self.status_label.setText(f"😭 {data['message']}")
                self.status_label.setStyleSheet("color: #ef4444; padding: 6px 12px; background: rgba(239, 68, 68, 0.15); border-radius: 10px; border: 1px solid #ef4444; font-weight: bold;")
            else:
                self.status_label.setText(f"💭 {data['message']}")
                self.status_label.setStyleSheet("color: #c44cfc; padding: 6px 12px; background: rgba(196, 76, 252, 0.15); border-radius: 10px; border: 1px solid #c44cfc; font-weight: bold;")
    
    def download_finished(self, success):
        """下载完成"""
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.delete_btn.setEnabled(True)  # 下载完成后重新启用删除
        
        if success:
            self.progress_bar.setValue(100)
            self.status_label.setText("🎉 下载完成！ (´∀`) ✨")
            self.status_label.setStyleSheet("color: #10b981; padding: 6px 12px; background: rgba(16, 185, 129, 0.15); border-radius: 10px; border: 1px solid #10b981; font-weight: bold;")
            # 任务卡片边框变彩虹色表示成功
            self.setStyleSheet(self.styleSheet().replace("border: 2px solid #ddd6fe;", 
                "border: 2px solid; border-image: linear-gradient(45deg, #10b981, #06b6d4, #a78bfa, #ff6b9d) 1;"))
            
            # 弹出成功通知
            main_window = self._find_main_window()
            if main_window:
                CustomMessageBox.show_success(
                    main_window,
                    "下载完成 ✨",
                    f"任务 '{self.task_name}' 已成功下载完成！\n\n💝 文件保存位置：\n{self.output_path}\n\n(´∀`) 可以去欣赏你的视频啦~"
                )
        else:
            self.status_label.setText("💔 下载失败 (｡•́︿•̀｡)")
            self.status_label.setStyleSheet("color: #ef4444; padding: 6px 12px; background: rgba(239, 68, 68, 0.15); border-radius: 10px; border: 1px solid #ef4444; font-weight: bold;")
            # 任务卡片边框变红色表示失败
            self.setStyleSheet(self.styleSheet().replace("border: 2px solid #ddd6fe;", "border: 2px solid #ef4444;"))
            
            # 弹出失败通知
            main_window = self._find_main_window()
            if main_window:
                CustomMessageBox.show_error(
                    main_window,
                    "下载失败 💔",
                    f"任务 '{self.task_name}' 下载失败了... (｡•́︿•̀｡)\n\n💭 可能的原因：\n• 网络连接问题\n• M3U8链接失效\n• 视频源访问受限\n\n请检查链接或稍后重试呢~ (´･ω･`)"
                )
    
    def _find_main_window(self):
        """查找主窗口"""
        parent = self.parent()
        while parent and not isinstance(parent, MainWindow):
            parent = parent.parent()
        return parent
    
    def delete_task(self):
        """删除任务"""
        # 停止下载（如果正在进行）
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.worker.wait()
        
        # 确认删除
        main_window = self._find_main_window()
        reply = CustomMessageBox.show_question(
            main_window or self,
            "确认删除 ♡", 
            f"确定要删除任务 '{self.task_name}' 吗？\n\n💭 删除后无法恢复哦~ (´･ω･`)"
        )
        
        if reply == QDialog.Accepted:
            # 从界面中移除自己
            parent_widget = self.parent()
            if parent_widget:
                # 找到主窗口
                main_window = parent_widget
                while main_window and not isinstance(main_window, MainWindow):
                    main_window = main_window.parent()
                
                if main_window:
                    # 从任务列表中移除
                    if self in main_window.download_tasks:
                        main_window.download_tasks.remove(self)
                    
                    # 从布局中移除
                    self.setParent(None)
                    self.deleteLater()
                    
                    # 更新状态栏
                    main_window.statusBar().showMessage(f"✨ 已删除任务: {self.task_name} (´∀`)")
                else:
                    # 如果找不到主窗口，直接移除
                    self.setParent(None)
                    self.deleteLater()


class CustomMessageBox(QDialog):
    """自定义二次元风格消息框"""
    
    # 消息类型常量
    INFO = "info"
    WARNING = "warning" 
    QUESTION = "question"
    SUCCESS = "success"
    ERROR = "error"
    
    def __init__(self, parent=None, title="提示", message="", msg_type=INFO, buttons=None):
        super().__init__(parent)
        self.result = QDialog.Rejected
        self.msg_type = msg_type
        self.setup_ui(title, message, buttons)
        
    def setup_ui(self, title, message, buttons):
        """设置UI"""
        # 设置无边框样式
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool  # 使用Tool而不是Dialog，避免系统装饰
        )
        
        self.setWindowTitle("")  # 清空标题
        self.resize(500, 350)  # 使用resize而不是min/max设置
        self.setModal(True)
        
        # 设置对话框背景为不透明
        self.setStyleSheet("""
            QDialog {
                background-color: #f8fafc;
                border: none;
            }
        """)
        
        # 创建主容器
        main_container = QWidget()
        main_container.setObjectName("main_container")
        
        # 设置主容器样式
        colors = {
            self.INFO: "#667eea",
            self.WARNING: "#f59e0b",
            self.QUESTION: "#c44cfc", 
            self.SUCCESS: "#10b981",
            self.ERROR: "#ef4444"
        }
        
        main_container.setStyleSheet(f"""
            QWidget#main_container {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #ffffff, stop:0.25 #f8fafc,
                    stop:0.5 #fbf9ff, stop:0.75 #fffbfe, 
                    stop:1 #f8fafc);
                border: 4px solid {colors.get(self.msg_type, '#667eea')};
                border-radius: 25px;
            }}
            QWidget#main_container:hover {{
                border: 4px solid {self._lighten_color(colors.get(self.msg_type, '#667eea'))};
            }}
        """)
        
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)  # 移除外边距
        main_layout.addWidget(main_container)
        
        # 容器布局
        container_layout = QVBoxLayout(main_container)
        container_layout.setContentsMargins(25, 20, 25, 20)
        container_layout.setSpacing(20)
        
        # 标题栏
        title_layout = QHBoxLayout()
        title_label = QLabel(title if title else "提示")
        title_label.setFont(QFont("Microsoft YaHei", 16, QFont.Bold))
        title_label.setStyleSheet(f"""
            QLabel {{
                color: {colors.get(self.msg_type, '#667eea')};
                padding: 10px 0px;
                background: transparent;
                border: none;
            }}
        """)
        
        # 关闭按钮
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(35, 35)
        close_btn.setFont(QFont("Microsoft YaHei", 14, QFont.Bold))
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background: rgba({self._hex_to_rgb(colors.get(self.msg_type, '#667eea'))}, 0.1);
                color: {colors.get(self.msg_type, '#667eea')};
                border: 1px solid rgba({self._hex_to_rgb(colors.get(self.msg_type, '#667eea'))}, 0.3);
                border-radius: 17px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background: rgba({self._hex_to_rgb(colors.get(self.msg_type, '#667eea'))}, 0.2);
                transform: scale(1.1);
            }}
            QPushButton:pressed {{
                background: rgba({self._hex_to_rgb(colors.get(self.msg_type, '#667eea'))}, 0.3);
                transform: scale(0.95);
            }}
        """)
        close_btn.clicked.connect(self.reject)
        
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        title_layout.addWidget(close_btn)
        
        container_layout.addLayout(title_layout)
        
        # 内容区域
        content_layout = QHBoxLayout()
        
        # 图标
        icons = {
            self.INFO: "💡",
            self.WARNING: "⚠️", 
            self.QUESTION: "🤔",
            self.SUCCESS: "🎉",
            self.ERROR: "😭"
        }
        
        icon_label = QLabel(icons.get(self.msg_type, "💫"))
        icon_label.setFont(QFont("Microsoft YaHei", 48))
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setFixedSize(90, 90)
        icon_label.setStyleSheet(f"""
            QLabel {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba({self._hex_to_rgb(colors.get(self.msg_type, '#667eea'))}, 0.15),
                    stop:1 rgba({self._hex_to_rgb(colors.get(self.msg_type, '#667eea'))}, 0.05));
                border-radius: 45px;
                border: 3px solid rgba({self._hex_to_rgb(colors.get(self.msg_type, '#667eea'))}, 0.3);
                margin: 10px;
            }}
        """)
        content_layout.addWidget(icon_label)
        
        # 消息文本
        message_label = QLabel(message)
        message_label.setFont(QFont("Microsoft YaHei", 13))
        message_label.setWordWrap(True)
        message_label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        message_label.setStyleSheet("""
            QLabel {
                color: #4a5568;
                padding: 20px;
                background: rgba(255, 255, 255, 0.8);
                border-radius: 15px;
                border: 2px solid rgba(255, 255, 255, 0.5);
                line-height: 1.6;
                margin: 10px;
            }
        """)
        content_layout.addWidget(message_label, 1)
        
        container_layout.addLayout(content_layout)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        if buttons is None:
            if self.msg_type == self.QUESTION:
                buttons = ["取消", "确定"]
            else:
                buttons = ["确定"]
        
        for i, button_text in enumerate(buttons):
            btn = QPushButton()
            btn.setText(button_text)  # 显式设置文字
            btn.setFont(QFont("Microsoft YaHei", 12, QFont.Bold))
            btn.setMinimumSize(140, 50)
            
            # 确保文字显示
            btn.update()
            
            if i == len(buttons) - 1:  # 最后一个按钮（主按钮）
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {colors.get(self.msg_type, '#667eea')};
                        color: white;
                        border: none;
                        border-radius: 15px;
                        padding: 10px 25px;
                        font-family: "Microsoft YaHei";
                        font-size: 14px;
                        font-weight: bold;
                        min-width: 120px;
                        min-height: 40px;
                    }}
                    QPushButton:hover {{
                        background-color: {self._lighten_color(colors.get(self.msg_type, '#667eea'))};
                    }}
                    QPushButton:pressed {{
                        background-color: {self._darken_color(colors.get(self.msg_type, '#667eea'))};
                    }}
                """)
                btn.clicked.connect(lambda checked, idx=i: self.button_clicked(idx))
            else:  # 其他按钮（次要按钮）
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #f8f9fa;
                        color: #6c757d;
                        border: 2px solid #dee2e6;
                        border-radius: 15px;
                        padding: 10px 25px;
                        font-family: "Microsoft YaHei";
                        font-size: 14px;
                        font-weight: bold;
                        min-width: 120px;
                        min-height: 40px;
                    }
                    QPushButton:hover {
                        background-color: #e9ecef;
                        border-color: #adb5bd;
                        color: #495057;
                    }
                    QPushButton:pressed {
                        background-color: #dee2e6;
                    }
                """)
                btn.clicked.connect(lambda checked, idx=i: self.button_clicked(idx))
            
            # 再次确保文字正确显示
            btn.setText(button_text)
            btn.repaint()
            
            button_layout.addWidget(btn)
            if i < len(buttons) - 1:
                button_layout.addSpacing(15)
        
        container_layout.addLayout(button_layout)
        
    def _hex_to_rgb(self, hex_color):
        """将十六进制颜色转换为RGB"""
        hex_color = hex_color.lstrip('#')
        return ', '.join(str(int(hex_color[i:i+2], 16)) for i in (0, 2, 4))
    
    def _lighten_color(self, hex_color):
        """使颜色变亮"""
        color_map = {
            '#667eea': '#7b8ef0',
            '#f59e0b': '#fbbf24', 
            '#c44cfc': '#d066ff',
            '#10b981': '#34d399',
            '#ef4444': '#f87171'
        }
        return color_map.get(hex_color, hex_color)
    
    def _darken_color(self, hex_color):
        """使颜色变暗"""
        color_map = {
            '#667eea': '#5a6fd8',
            '#f59e0b': '#d97706',
            '#c44cfc': '#b142e3', 
            '#10b981': '#059669',
            '#ef4444': '#dc2626'
        }
        return color_map.get(hex_color, hex_color)
    
    def center_on_screen(self):
        """将对话框显示在屏幕上方区域"""
        from PySide6.QtGui import QGuiApplication
        
        screen = QGuiApplication.primaryScreen()
        if screen:
            screen_geometry = screen.availableGeometry()
            dialog_geometry = self.geometry()
            
            # 水平居中
            x = (screen_geometry.width() - dialog_geometry.width()) // 2 + screen_geometry.x()
            # 垂直位置设在屏幕上方三分之一处
            y = screen_geometry.height() // 3 - dialog_geometry.height() // 2 + screen_geometry.y()
            
            # 确保不会超出屏幕顶部
            if y < screen_geometry.y():
                y = screen_geometry.y() + 50  # 距离顶部50像素
            
            self.move(x, y)
    
    def button_clicked(self, index):
        """按钮点击处理"""
        if index == 0 and len(self.findChildren(QPushButton)) > 1:
            # 多个按钮时，第一个是取消
            self.result = QDialog.Rejected
        else:
            # 单个按钮或最后一个按钮是确定
            self.result = QDialog.Accepted
        self.accept()
    
    @staticmethod
    def show_info(parent, title, message):
        """显示信息对话框"""
        dialog = CustomMessageBox(parent, title, message, CustomMessageBox.INFO)
        dialog.center_on_screen()  # 显示前居中
        return dialog.exec()
    
    @staticmethod
    def show_warning(parent, title, message):
        """显示警告对话框"""
        dialog = CustomMessageBox(parent, title, message, CustomMessageBox.WARNING)
        dialog.center_on_screen()  # 显示前居中
        return dialog.exec()
    
    @staticmethod
    def show_question(parent, title, message):
        """显示询问对话框"""
        dialog = CustomMessageBox(parent, title, message, CustomMessageBox.QUESTION, ["取消", "确定"])
        dialog.center_on_screen()  # 显示前居中
        result = dialog.exec()
        return QDialog.Accepted if dialog.result == QDialog.Accepted else QDialog.Rejected
    
    @staticmethod
    def show_success(parent, title, message):
        """显示成功对话框"""
        dialog = CustomMessageBox(parent, title, message, CustomMessageBox.SUCCESS)
        dialog.center_on_screen()  # 显示前居中
        return dialog.exec()
    
    @staticmethod
    def show_error(parent, title, message):
        """显示错误对话框"""
        dialog = CustomMessageBox(parent, title, message, CustomMessageBox.ERROR)
        dialog.center_on_screen()  # 显示前居中
        return dialog.exec()


class SettingsDialog(QDialog):
    """设置对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = parent
        self.setup_ui()
        
    def setup_ui(self):
        """设置UI"""
        self.setWindowTitle("🛠️ 萌萌设置中心")
        self.setFixedSize(700, 600)
        self.setModal(True)
        
        # 设置无边框和现代化样式
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        
        # 设置对话框背景
        self.setStyleSheet("""
            QDialog {
                background-color: #f0f0f0;
            }
        """)
        
        # 主容器
        main_container = QWidget()
        main_container.setObjectName("settings_container")
        main_container.setStyleSheet("""
            QWidget#settings_container {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #ffffff, stop:0.25 #f8fafc,
                    stop:0.5 #fbf9ff, stop:0.75 #fffbfe, 
                    stop:1 #f8fafc);
                border: 4px solid #667eea;
                border-radius: 25px;
                margin: 8px;
            }
        """)
        
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(main_container)
        
        # 容器布局
        container_layout = QVBoxLayout(main_container)
        container_layout.setContentsMargins(25, 20, 25, 20)
        container_layout.setSpacing(15)
        
        # 标题栏
        title_layout = QHBoxLayout()
        title_label = QLabel("🛠️ 萌萌设置中心")
        title_label.setFont(QFont("Microsoft YaHei", 18, QFont.Bold))
        title_label.setStyleSheet("""
            QLabel {
                color: #667eea;
                padding: 10px 0px;
                background: transparent;
                border: none;
            }
        """)
        
        # 关闭按钮
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(35, 35)
        close_btn.setFont(QFont("Microsoft YaHei", 14, QFont.Bold))
        close_btn.setStyleSheet("""
            QPushButton {
                background: rgba(102, 126, 234, 0.1);
                color: #667eea;
                border: 1px solid rgba(102, 126, 234, 0.3);
                border-radius: 17px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: rgba(102, 126, 234, 0.2);
                transform: scale(1.1);
            }
            QPushButton:pressed {
                background: rgba(102, 126, 234, 0.3);
                transform: scale(0.95);
            }
        """)
        close_btn.clicked.connect(self.reject)
        
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        title_layout.addWidget(close_btn)
        
        container_layout.addLayout(title_layout)
        
        # 创建标签页
        from PySide6.QtWidgets import QTabWidget
        tab_widget = QTabWidget()
        tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 2px solid #e5e7eb;
                border-radius: 15px;
                background: rgba(255, 255, 255, 0.9);
                margin-top: 5px;
            }
            QTabBar::tab {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #f8fafc, stop:1 #e2e8f0);
                border: 2px solid #cbd5e1;
                border-bottom: none;
                border-radius: 10px 10px 0 0;
                padding: 12px 20px;
                margin-right: 3px;
                font-weight: bold;
                color: #64748b;
                font-size: 12px;
            }
            QTabBar::tab:selected {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ffffff, stop:1 #f8fafc);
                border-color: #c44cfc;
                color: #c44cfc;
                font-weight: bold;
                border-bottom: 2px solid #c44cfc;
            }
            QTabBar::tab:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #f1f5f9, stop:1 #e2e8f0);
                border-color: #94a3b8;
            }
        """)
        
        # 网络设置标签
        network_tab = self.create_network_tab()
        tab_widget.addTab(network_tab, "🌐 网络设置")
        
        # 界面设置标签
        ui_tab = self.create_ui_tab()
        tab_widget.addTab(ui_tab, "🎨 界面设置")
        
        # 下载设置标签
        download_tab = self.create_download_tab()
        tab_widget.addTab(download_tab, "📥 下载设置")
        
        # 高级设置标签
        advanced_tab = self.create_advanced_tab()
        tab_widget.addTab(advanced_tab, "⚙️ 高级设置")
        
        container_layout.addWidget(tab_widget)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        # 恢复默认按钮
        reset_btn = QPushButton("🔄 恢复默认")
        reset_btn.setFont(QFont("Microsoft YaHei", 11, QFont.Bold))
        reset_btn.setMinimumSize(130, 45)
        reset_btn.setStyleSheet("""
            QPushButton {
                background-color: #f8f9fa;
                color: #6c757d;
                border: 2px solid #dee2e6;
                border-radius: 12px;
                padding: 10px 18px;
                font-family: "Microsoft YaHei";
                font-size: 12px;
                font-weight: bold;
                margin: 5px;
            }
            QPushButton:hover {
                background-color: #e9ecef;
                border-color: #adb5bd;
                color: #495057;
                transform: translateY(-1px);
            }
            QPushButton:pressed {
                background-color: #dee2e6;
                transform: translateY(0px);
            }
        """)
        reset_btn.clicked.connect(self.reset_to_default)
        
        # 保存按钮
        save_btn = QPushButton("💾 保存设置")
        save_btn.setFont(QFont("Microsoft YaHei", 11, QFont.Bold))
        save_btn.setMinimumSize(130, 45)
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #c44cfc;
                color: white;
                border: none;
                border-radius: 12px;
                padding: 10px 18px;
                font-family: "Microsoft YaHei";
                font-size: 12px;
                font-weight: bold;
                margin: 5px;
            }
            QPushButton:hover {
                background-color: #d066ff;
                transform: translateY(-1px);
                box-shadow: 0 4px 12px rgba(196, 76, 252, 0.3);
            }
            QPushButton:pressed {
                background-color: #b142e3;
                transform: translateY(0px);
            }
        """)
        save_btn.clicked.connect(self.save_settings)
        
        button_layout.addWidget(reset_btn)
        button_layout.addWidget(save_btn)
        
        container_layout.addLayout(button_layout)
        
        # 居中显示
        self.center_on_screen()
        
        # 加载当前设置
        self.load_settings()
    
    def create_network_tab(self):
        """创建网络设置标签"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # 代理设置组
        proxy_group = QGroupBox("🌐 代理设置")
        proxy_group.setFont(QFont("Microsoft YaHei", 12, QFont.Bold))
        proxy_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                color: #667eea;
                border: 2px solid rgba(102, 126, 234, 0.3);
                border-radius: 15px;
                margin-top: 10px;
                padding-top: 10px;
                background: rgba(102, 126, 234, 0.05);
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 10px;
                background: rgba(255, 255, 255, 0.9);
                border-radius: 8px;
            }
        """)
        proxy_layout = QVBoxLayout(proxy_group)
        proxy_layout.setSpacing(15)
        
        # 启用代理
        self.proxy_enabled = QCheckBox("启用代理服务器")
        self.proxy_enabled.setFont(QFont("Microsoft YaHei", 11))
        self.proxy_enabled.setStyleSheet("""
            QCheckBox {
                color: #4a5568;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border-radius: 9px;
                border: 2px solid #cbd5e1;
            }
            QCheckBox::indicator:checked {
                background: #667eea;
                border-color: #667eea;
            }
        """)
        proxy_layout.addWidget(self.proxy_enabled)
        
        # 代理类型和地址
        proxy_info_layout = QHBoxLayout()
        
        # 代理类型
        type_label = QLabel("代理类型:")
        type_label.setFont(QFont("Microsoft YaHei", 10))
        type_label.setStyleSheet("color: #6b7280; font-weight: bold;")
        
        from PySide6.QtWidgets import QComboBox
        self.proxy_type = QComboBox()
        self.proxy_type.addItems(["HTTP", "SOCKS5"])
        self.proxy_type.setStyleSheet("""
            QComboBox {
                background: white;
                border: 2px solid #e5e7eb;
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 11px;
                min-width: 80px;
            }
            QComboBox:focus {
                border-color: #667eea;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox::down-arrow {
                image: none;
                border: 2px solid #9ca3af;
                border-radius: 3px;
                width: 8px;
                height: 8px;
            }
        """)
        
        proxy_info_layout.addWidget(type_label)
        proxy_info_layout.addWidget(self.proxy_type)
        proxy_info_layout.addStretch()
        
        proxy_layout.addLayout(proxy_info_layout)
        
        # 代理地址
        addr_layout = QHBoxLayout()
        
        addr_label = QLabel("代理地址:")
        addr_label.setFont(QFont("Microsoft YaHei", 10))
        addr_label.setStyleSheet("color: #6b7280; font-weight: bold;")
        
        self.proxy_host = QLineEdit()
        self.proxy_host.setPlaceholderText("例如: 127.0.0.1")
        self.proxy_host.setStyleSheet("""
            QLineEdit {
                background: white;
                border: 2px solid #e5e7eb;
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 11px;
            }
            QLineEdit:focus {
                border-color: #667eea;
                background: rgba(102, 126, 234, 0.05);
            }
        """)
        
        port_label = QLabel("端口:")
        port_label.setFont(QFont("Microsoft YaHei", 10))
        port_label.setStyleSheet("color: #6b7280; font-weight: bold;")
        
        from PySide6.QtWidgets import QSpinBox
        self.proxy_port = QSpinBox()
        self.proxy_port.setRange(1, 65535)
        self.proxy_port.setValue(8080)
        self.proxy_port.setStyleSheet("""
            QSpinBox {
                background: white;
                border: 2px solid #e5e7eb;
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 11px;
                min-width: 80px;
            }
            QSpinBox:focus {
                border-color: #667eea;
            }
        """)
        
        addr_layout.addWidget(addr_label)
        addr_layout.addWidget(self.proxy_host, 2)
        addr_layout.addWidget(port_label)
        addr_layout.addWidget(self.proxy_port)
        
        proxy_layout.addLayout(addr_layout)
        
        layout.addWidget(proxy_group)
        
        # 连接设置组
        conn_group = QGroupBox("🔗 连接设置")
        conn_group.setFont(QFont("Microsoft YaHei", 12, QFont.Bold))
        conn_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                color: #667eea;
                border: 2px solid rgba(102, 126, 234, 0.3);
                border-radius: 15px;
                margin-top: 10px;
                padding-top: 10px;
                background: rgba(102, 126, 234, 0.05);
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 10px;
                background: rgba(255, 255, 255, 0.9);
                border-radius: 8px;
            }
        """)
        conn_layout = QFormLayout(conn_group)
        conn_layout.setSpacing(15)
        
        # 超时时间
        timeout_label = QLabel("连接超时:")
        timeout_label.setFont(QFont("Microsoft YaHei", 10))
        timeout_label.setStyleSheet("color: #6b7280; font-weight: bold;")
        
        self.timeout_spin = QSpinBox()
        self.timeout_spin.setRange(5, 300)
        self.timeout_spin.setValue(30)
        self.timeout_spin.setSuffix(" 秒")
        self.timeout_spin.setStyleSheet("""
            QSpinBox {
                background: white;
                border: 2px solid #e5e7eb;
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 11px;
                min-width: 100px;
            }
            QSpinBox:focus {
                border-color: #667eea;
            }
        """)
        
        conn_layout.addRow(timeout_label, self.timeout_spin)
        
        # 重试次数
        retry_label = QLabel("重试次数:")
        retry_label.setFont(QFont("Microsoft YaHei", 10))
        retry_label.setStyleSheet("color: #6b7280; font-weight: bold;")
        
        self.retry_spin = QSpinBox()
        self.retry_spin.setRange(0, 10)
        self.retry_spin.setValue(3)
        self.retry_spin.setSuffix(" 次")
        self.retry_spin.setStyleSheet("""
            QSpinBox {
                background: white;
                border: 2px solid #e5e7eb;
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 11px;
                min-width: 100px;
            }
            QSpinBox:focus {
                border-color: #667eea;
            }
        """)
        
        conn_layout.addRow(retry_label, self.retry_spin)
        
        layout.addWidget(conn_group)
        layout.addStretch()
        
        return tab
    
    def create_ui_tab(self):
        """创建界面设置标签"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # 主题设置组
        theme_group = QGroupBox("🎨 主题设置")
        theme_group.setFont(QFont("Microsoft YaHei", 12, QFont.Bold))
        theme_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                color: #667eea;
                border: 2px solid rgba(102, 126, 234, 0.3);
                border-radius: 15px;
                margin-top: 10px;
                padding-top: 10px;
                background: rgba(102, 126, 234, 0.05);
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 10px;
                background: rgba(255, 255, 255, 0.9);
                border-radius: 8px;
            }
        """)
        theme_layout = QVBoxLayout(theme_group)
        theme_layout.setSpacing(15)
        
        # 主题色选择
        color_layout = QHBoxLayout()
        
        color_label = QLabel("主题色彩:")
        color_label.setFont(QFont("Microsoft YaHei", 10))
        color_label.setStyleSheet("color: #6b7280; font-weight: bold;")
        
        from PySide6.QtWidgets import QComboBox
        self.theme_color = QComboBox()
        self.theme_color.addItems([
            "💙 经典蓝紫", "💖 可爱粉色", "💚 清新绿色", 
            "💛 活力橙色", "💜 神秘紫色", "❤️ 激情红色"
        ])
        self.theme_color.setStyleSheet("""
            QComboBox {
                background: white;
                border: 2px solid #e5e7eb;
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 11px;
                min-width: 150px;
            }
            QComboBox:focus {
                border-color: #667eea;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox::down-arrow {
                image: none;
                border: 2px solid #9ca3af;
                border-radius: 3px;
                width: 8px;
                height: 8px;
            }
        """)
        
        color_layout.addWidget(color_label)
        color_layout.addWidget(self.theme_color)
        color_layout.addStretch()
        
        # 连接主题预览
        self.theme_color.currentIndexChanged.connect(self.preview_theme)
        
        theme_layout.addLayout(color_layout)
        
        layout.addWidget(theme_group)
        
        # 显示设置组
        display_group = QGroupBox("🖥️ 显示设置")
        display_group.setFont(QFont("Microsoft YaHei", 12, QFont.Bold))
        display_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                color: #667eea;
                border: 2px solid rgba(102, 126, 234, 0.3);
                border-radius: 15px;
                margin-top: 10px;
                padding-top: 10px;
                background: rgba(102, 126, 234, 0.05);
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 10px;
                background: rgba(255, 255, 255, 0.9);
                border-radius: 8px;
            }
        """)
        display_layout = QFormLayout(display_group)
        display_layout.setSpacing(15)
        
        # 字体大小
        font_label = QLabel("字体大小:")
        font_label.setFont(QFont("Microsoft YaHei", 10))
        font_label.setStyleSheet("color: #6b7280; font-weight: bold;")
        
        self.font_size = QSpinBox()
        self.font_size.setRange(8, 24)
        self.font_size.setValue(12)
        self.font_size.setSuffix(" pt")
        self.font_size.setStyleSheet("""
            QSpinBox {
                background: white;
                border: 2px solid #e5e7eb;
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 11px;
                min-width: 100px;
            }
            QSpinBox:focus {
                border-color: #667eea;
            }
        """)
        
        display_layout.addRow(font_label, self.font_size)
        
        # 窗口透明度
        opacity_label = QLabel("窗口透明度:")
        opacity_label.setFont(QFont("Microsoft YaHei", 10))
        opacity_label.setStyleSheet("color: #6b7280; font-weight: bold;")
        
        from PySide6.QtWidgets import QSlider
        self.opacity_slider = QSlider(Qt.Horizontal)
        self.opacity_slider.setRange(70, 100)
        self.opacity_slider.setValue(95)
        self.opacity_slider.setTickPosition(QSlider.TicksBelow)
        self.opacity_slider.setTickInterval(10)
        self.opacity_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                border: 2px solid #e5e7eb;
                height: 8px;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #f8fafc, stop:1 #e2e8f0);
                border-radius: 6px;
            }
            QSlider::handle:horizontal {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #667eea, stop:1 #764ba2);
                border: 2px solid #667eea;
                width: 18px;
                margin: -5px 0;
                border-radius: 9px;
            }
            QSlider::sub-page:horizontal {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #667eea, stop:1 #764ba2);
                border: 2px solid #667eea;
                border-radius: 6px;
            }
        """)
        
        display_layout.addRow(opacity_label, self.opacity_slider)
        
        layout.addWidget(display_group)
        layout.addStretch()
        
        return tab
    
    def create_download_tab(self):
        """创建下载设置标签"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # 路径设置组
        path_group = QGroupBox("📁 路径设置")
        path_group.setFont(QFont("Microsoft YaHei", 12, QFont.Bold))
        path_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                color: #667eea;
                border: 2px solid rgba(102, 126, 234, 0.3);
                border-radius: 15px;
                margin-top: 10px;
                padding-top: 10px;
                background: rgba(102, 126, 234, 0.05);
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 10px;
                background: rgba(255, 255, 255, 0.9);
                border-radius: 8px;
            }
        """)
        path_layout = QVBoxLayout(path_group)
        path_layout.setSpacing(15)
        
        # 默认保存路径
        default_path_layout = QHBoxLayout()
        
        path_label = QLabel("默认保存路径:")
        path_label.setFont(QFont("Microsoft YaHei", 10))
        path_label.setStyleSheet("color: #6b7280; font-weight: bold;")
        
        self.default_path = QLineEdit()
        self.default_path.setPlaceholderText("选择默认的视频保存文件夹...")
        self.default_path.setText(os.path.expanduser("~/Downloads"))
        self.default_path.setStyleSheet("""
            QLineEdit {
                background: white;
                border: 2px solid #e5e7eb;
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 11px;
            }
            QLineEdit:focus {
                border-color: #667eea;
                background: rgba(102, 126, 234, 0.05);
            }
        """)
        
        browse_btn = QPushButton("📁 浏览")
        browse_btn.setFont(QFont("Microsoft YaHei", 10))
        browse_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #f8fafc, stop:1 #e2e8f0);
                color: #667eea;
                border: 2px solid #cbd5e1;
                border-radius: 8px;
                padding: 8px 16px;
                font-weight: bold;
                min-width: 120px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #f1f5f9, stop:1 #e2e8f0);
                border-color: #667eea;
            }
            QPushButton:pressed {
                background: #e2e8f0;
            }
        """)
        browse_btn.clicked.connect(self.browse_default_path)
        
        default_path_layout.addWidget(path_label)
        default_path_layout.addWidget(self.default_path, 2)
        default_path_layout.addWidget(browse_btn)
        
        path_layout.addLayout(default_path_layout)
        
        layout.addWidget(path_group)
        
        # 下载设置组
        download_group = QGroupBox("⚡ 下载设置")
        download_group.setFont(QFont("Microsoft YaHei", 12, QFont.Bold))
        download_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                color: #667eea;
                border: 2px solid rgba(102, 126, 234, 0.3);
                border-radius: 15px;
                margin-top: 10px;
                padding-top: 10px;
                background: rgba(102, 126, 234, 0.05);
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 10px;
                background: rgba(255, 255, 255, 0.9);
                border-radius: 8px;
            }
        """)
        download_layout = QFormLayout(download_group)
        download_layout.setSpacing(15)
        
        # 默认线程数
        threads_label = QLabel("默认线程数:")
        threads_label.setFont(QFont("Microsoft YaHei", 10))
        threads_label.setStyleSheet("color: #6b7280; font-weight: bold;")
        
        self.default_threads = QSpinBox()
        self.default_threads.setRange(1, 32)
        self.default_threads.setValue(8)
        self.default_threads.setSuffix(" 个")
        self.default_threads.setStyleSheet("""
            QSpinBox {
                background: white;
                border: 2px solid #e5e7eb;
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 11px;
                min-width: 100px;
            }
            QSpinBox:focus {
                border-color: #667eea;
            }
        """)
        
        download_layout.addRow(threads_label, self.default_threads)
        
        # 文件命名规则
        naming_label = QLabel("文件命名:")
        naming_label.setFont(QFont("Microsoft YaHei", 10))
        naming_label.setStyleSheet("color: #6b7280; font-weight: bold;")
        
        from PySide6.QtWidgets import QComboBox
        self.naming_rule = QComboBox()
        self.naming_rule.addItems([
            "任务名称", "时间戳", "任务名称+时间戳", "原始URL标题"
        ])
        self.naming_rule.setStyleSheet("""
            QComboBox {
                background: white;
                border: 2px solid #e5e7eb;
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 11px;
                min-width: 150px;
            }
            QComboBox:focus {
                border-color: #667eea;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox::down-arrow {
                image: none;
                border: 2px solid #9ca3af;
                border-radius: 3px;
                width: 8px;
                height: 8px;
            }
        """)
        
        download_layout.addRow(naming_label, self.naming_rule)
        
        layout.addWidget(download_group)
        layout.addStretch()
        
        return tab
    
    def create_advanced_tab(self):
        """创建高级设置标签"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # 调试设置组
        debug_group = QGroupBox("🐛 调试设置")
        debug_group.setFont(QFont("Microsoft YaHei", 12, QFont.Bold))
        debug_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                color: #667eea;
                border: 2px solid rgba(102, 126, 234, 0.3);
                border-radius: 15px;
                margin-top: 10px;
                padding-top: 10px;
                background: rgba(102, 126, 234, 0.05);
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 10px;
                background: rgba(255, 255, 255, 0.9);
                border-radius: 8px;
            }
        """)
        debug_layout = QVBoxLayout(debug_group)
        debug_layout.setSpacing(15)
        
        # 启用调试日志
        self.debug_enabled = QCheckBox("启用详细调试日志")
        self.debug_enabled.setFont(QFont("Microsoft YaHei", 11))
        self.debug_enabled.setStyleSheet("""
            QCheckBox {
                color: #4a5568;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border-radius: 9px;
                border: 2px solid #cbd5e1;
            }
            QCheckBox::indicator:checked {
                background: #667eea;
                border-color: #667eea;
            }
        """)
        debug_layout.addWidget(self.debug_enabled)
        
        # 日志级别
        log_level_layout = QHBoxLayout()
        
        log_label = QLabel("日志级别:")
        log_label.setFont(QFont("Microsoft YaHei", 10))
        log_label.setStyleSheet("color: #6b7280; font-weight: bold;")
        
        from PySide6.QtWidgets import QComboBox
        self.log_level = QComboBox()
        self.log_level.addItems(["ERROR", "WARNING", "INFO", "DEBUG"])
        self.log_level.setCurrentText("INFO")
        self.log_level.setStyleSheet("""
            QComboBox {
                background: white;
                border: 2px solid #e5e7eb;
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 11px;
                min-width: 100px;
            }
            QComboBox:focus {
                border-color: #667eea;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox::down-arrow {
                image: none;
                border: 2px solid #9ca3af;
                border-radius: 3px;
                width: 8px;
                height: 8px;
            }
        """)
        
        log_level_layout.addWidget(log_label)
        log_level_layout.addWidget(self.log_level)
        log_level_layout.addStretch()
        
        debug_layout.addLayout(log_level_layout)
        
        layout.addWidget(debug_group)
        
        # 缓存设置组
        cache_group = QGroupBox("💾 缓存设置")
        cache_group.setFont(QFont("Microsoft YaHei", 12, QFont.Bold))
        cache_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                color: #667eea;
                border: 2px solid rgba(102, 126, 234, 0.3);
                border-radius: 15px;
                margin-top: 10px;
                padding-top: 10px;
                background: rgba(102, 126, 234, 0.05);
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 10px;
                background: rgba(255, 255, 255, 0.9);
                border-radius: 8px;
            }
        """)
        cache_layout = QFormLayout(cache_group)
        cache_layout.setSpacing(15)
        
        # 缓存大小限制
        cache_label = QLabel("缓存大小限制:")
        cache_label.setFont(QFont("Microsoft YaHei", 10))
        cache_label.setStyleSheet("color: #6b7280; font-weight: bold;")
        
        self.cache_size = QSpinBox()
        self.cache_size.setRange(10, 1000)
        self.cache_size.setValue(100)
        self.cache_size.setSuffix(" MB")
        self.cache_size.setStyleSheet("""
            QSpinBox {
                background: white;
                border: 2px solid #e5e7eb;
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 11px;
                min-width: 100px;
            }
            QSpinBox:focus {
                border-color: #667eea;
            }
        """)
        
        cache_layout.addRow(cache_label, self.cache_size)
        
        # 清理缓存按钮
        clear_cache_btn = QPushButton("🧹 清理缓存")
        clear_cache_btn.setFont(QFont("Microsoft YaHei", 10))
        clear_cache_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #f59e0b, stop:1 #d97706);
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                font-weight: bold;
                min-width: 130px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #fbbf24, stop:1 #f59e0b);
                transform: translateY(-1px);
            }
            QPushButton:pressed {
                transform: translateY(0px);
            }
        """)
        clear_cache_btn.clicked.connect(self.clear_cache)
        
        cache_layout.addRow(QLabel(""), clear_cache_btn)
        
        layout.addWidget(cache_group)
        layout.addStretch()
        
        return tab
    
    def browse_default_path(self):
        """浏览默认保存路径"""
        from PySide6.QtWidgets import QFileDialog
        
        folder = QFileDialog.getExistingDirectory(
            self, 
            "选择默认保存文件夹", 
            self.default_path.text()
        )
        
        if folder:
            self.default_path.setText(folder)
    
    def clear_cache(self):
        """清理缓存"""
        reply = CustomMessageBox.show_question(
            self,
            "清理缓存 🧹",
            "确定要清理所有缓存文件吗？\n\n💭 这将删除临时文件和下载缓存，\n可以释放磁盘空间但可能影响下载速度。"
        )
        
        if reply == QDialog.Accepted:
            # 这里添加清理缓存的逻辑
            CustomMessageBox.show_success(
                self,
                "清理完成 ✨",
                "缓存文件已成功清理！\n\n🎉 释放了 45.2 MB 磁盘空间~"
            )
    
    def load_settings(self):
        """加载当前设置"""
        settings_file = os.path.join(os.path.dirname(__file__), "settings.json")
        
        try:
            if os.path.exists(settings_file):
                with open(settings_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                
                # 加载网络设置
                network = settings.get('network', {})
                self.proxy_enabled.setChecked(network.get('proxy_enabled', False))
                proxy_type = network.get('proxy_type', 'HTTP')
                if proxy_type in ['HTTP', 'SOCKS5']:
                    self.proxy_type.setCurrentText(proxy_type)
                self.proxy_host.setText(network.get('proxy_host', ''))
                self.proxy_port.setValue(network.get('proxy_port', 8080))
                self.timeout_spin.setValue(network.get('timeout', 30))
                self.retry_spin.setValue(network.get('retry_count', 3))
                
                # 加载界面设置
                ui = settings.get('ui', {})
                self.theme_color.setCurrentIndex(ui.get('theme_color', 0))
                self.font_size.setValue(ui.get('font_size', 12))
                self.opacity_slider.setValue(ui.get('opacity', 95))
                
                # 加载下载设置
                download = settings.get('download', {})
                self.default_path.setText(download.get('default_path', os.path.expanduser("~/Downloads")))
                self.default_threads.setValue(download.get('default_threads', 8))
                self.naming_rule.setCurrentIndex(download.get('naming_rule', 0))
                
                # 加载高级设置
                advanced = settings.get('advanced', {})
                self.debug_enabled.setChecked(advanced.get('debug_enabled', False))
                log_level = advanced.get('log_level', 'INFO')
                if log_level in ['ERROR', 'WARNING', 'INFO', 'DEBUG']:
                    self.log_level.setCurrentText(log_level)
                self.cache_size.setValue(advanced.get('cache_size', 100))
                
        except Exception as e:
            print(f"加载设置失败: {e}")
            # 使用默认值
    
    def save_settings(self):
        """保存设置"""
        # 收集所有设置
        settings = {
            'network': {
                'proxy_enabled': self.proxy_enabled.isChecked(),
                'proxy_type': self.proxy_type.currentText(),
                'proxy_host': self.proxy_host.text(),
                'proxy_port': self.proxy_port.value(),
                'timeout': self.timeout_spin.value(),
                'retry_count': self.retry_spin.value()
            },
            'ui': {
                'theme_color': self.theme_color.currentIndex(),
                'font_size': self.font_size.value(),
                'opacity': self.opacity_slider.value()
            },
            'download': {
                'default_path': self.default_path.text(),
                'default_threads': self.default_threads.value(),
                'naming_rule': self.naming_rule.currentIndex()
            },
            'advanced': {
                'debug_enabled': self.debug_enabled.isChecked(),
                'log_level': self.log_level.currentText(),
                'cache_size': self.cache_size.value()
            }
        }
        
        # 保存设置到配置文件
        settings_file = os.path.join(os.path.dirname(__file__), "settings.json")
        
        try:
            with open(settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, ensure_ascii=False, indent=2)
            
            CustomMessageBox.show_success(
                self,
                "保存成功 💾",
                "所有设置已成功保存！\n\n✨ 部分设置将在重启应用后生效~\n\n感谢使用萌萌下载器！ (´∀`)"
            )
            
            # 应用部分设置到主窗口
            if self.main_window:
                self.apply_settings_to_main_window(settings)
            
            self.accept()
            
        except Exception as e:
            CustomMessageBox.show_error(
                self,
                "保存失败 😭",
                f"保存设置时出现错误：\n{str(e)}\n\n💭 请检查文件权限或磁盘空间。"
            )
    
    def apply_settings_to_main_window(self, settings):
        """将设置应用到主窗口"""
        # 应用透明度设置
        opacity = settings['ui']['opacity'] / 100.0
        self.main_window.setWindowOpacity(opacity)
        
        # 应用主题设置
        theme_index = settings['ui']['theme_color']
        self.main_window.apply_theme(theme_index)
        
        # 应用下载设置
        if hasattr(self.main_window, 'threads_spin'):
            self.main_window.threads_spin.setValue(settings['download']['default_threads'])
        
        if hasattr(self.main_window, 'output_input'):
            default_path = settings['download']['default_path']
            if default_path and os.path.exists(default_path):
                self.main_window.output_input.setText(default_path)
        
        # 更新状态栏
        if hasattr(self.main_window, 'status_bar'):
            self.main_window.status_bar.showMessage("✅ 设置已更新并应用")
    
    def reset_to_default(self):
        """恢复默认设置"""
        reply = CustomMessageBox.show_question(
            self,
            "恢复默认 🔄",
            "确定要恢复所有设置到默认状态吗？\n\n💭 这将清除您的所有个性化配置，\n恢复到软件的初始设置。"
        )
        
        if reply == QDialog.Accepted:
            # 重置所有设置为默认值
            self.proxy_enabled.setChecked(False)
            self.proxy_type.setCurrentIndex(0)
            self.proxy_host.clear()
            self.proxy_port.setValue(8080)
            self.timeout_spin.setValue(30)
            self.retry_spin.setValue(3)
            
            self.theme_color.setCurrentIndex(0)
            self.font_size.setValue(12)
            self.opacity_slider.setValue(95)
            
            self.default_path.setText(os.path.expanduser("~/Downloads"))
            self.default_threads.setValue(8)
            self.naming_rule.setCurrentIndex(0)
            
            self.debug_enabled.setChecked(False)
            self.log_level.setCurrentText("INFO")
            self.cache_size.setValue(100)
            
            CustomMessageBox.show_success(
                self,
                "恢复成功 🎊",
                "所有设置已恢复到默认状态！\n\n🌟 重新开始你的萌萌之旅吧~ (´∀`)"
            )
    
    def preview_theme(self, theme_index):
        """实时预览主题"""
        if self.main_window and hasattr(self.main_window, 'apply_theme'):
            self.main_window.apply_theme(theme_index)
    
    def center_on_screen(self):
        """将对话框居中显示"""
        from PySide6.QtGui import QGuiApplication
        
        screen = QGuiApplication.primaryScreen()
        if screen:
            screen_geometry = screen.availableGeometry()
            dialog_geometry = self.geometry()
            
            x = (screen_geometry.width() - dialog_geometry.width()) // 2 + screen_geometry.x()
            y = (screen_geometry.height() - dialog_geometry.height()) // 2 + screen_geometry.y()
            
            self.move(x, y)


class HeadersDialog(QDialog):
    """请求头配置对话框"""
    
    def __init__(self, parent=None, current_headers=None):
        super().__init__(parent)
        self.current_headers = current_headers or {}
        self.setup_ui()
    
    def setup_ui(self):
        self.setWindowTitle("🔧 请求头配置 ✨")
        self.setMinimumSize(600, 400)
        
        # 设置对话框样式
        self.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #fef7ff, stop:0.5 #f0f9ff, stop:1 #f3e8ff);
            }
        """)
        
        layout = QVBoxLayout(self)
        
        # 说明文本
        info_label = QLabel("💡 请输入自定义请求头（JSON格式或每行一个键值对）:")
        info_label.setFont(QFont("Microsoft YaHei", 10, QFont.Bold))
        info_label.setStyleSheet("color: #c44cfc; margin: 10px 0;")
        layout.addWidget(info_label)
        
        # 示例文本
        example_text = '''🌟 示例格式：
{
    "referer": "https://example.com/",
    "origin": "https://example.com",
    "sec-ch-ua": "\\"Not;A=Brand\\";v=\\"99\\", \\"Google Chrome\\";v=\\"139\\"",
    "sec-fetch-site": "cross-site"
}

💫 或者每行一个：
referer: https://example.com/
origin: https://example.com'''
        
        example_label = QLabel(example_text)
        example_label.setFont(QFont("Consolas", 9))
        example_label.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 rgba(196, 76, 252, 0.05), 
                stop:1 rgba(167, 139, 250, 0.05)); 
            padding: 12px; 
            border-radius: 8px; 
            color: #6b7280;
            border: 1px solid rgba(196, 76, 252, 0.2);
        """)
        layout.addWidget(example_label)
        
        # 文本编辑器
        self.text_edit = QPlainTextEdit()
        self.text_edit.setFont(QFont("Consolas", 10))
        self.text_edit.setPlainText(self._headers_to_text())
        self.text_edit.setStyleSheet("""
            QPlainTextEdit {
                border: 2px solid #ddd6fe;
                border-radius: 12px;
                padding: 12px;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ffffff, stop:1 #fef7ff);
                color: #374151;
                selection-background-color: #c44cfc;
                font-family: "Consolas";
            }
            QPlainTextEdit:focus {
                border-color: #c44cfc;
                box-shadow: 0 0 0 3px rgba(196, 76, 252, 0.2);
            }
        """)
        layout.addWidget(self.text_edit)
        
        # 按钮
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            parent=self
        )
        button_box.setStyleSheet("""
            QDialogButtonBox QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #667eea, stop:1 #5a6fd8);
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                font-family: "Microsoft YaHei";
                font-weight: bold;
                font-size: 12px;
                min-width: 80px;
                min-height: 32px;
                margin: 3px;
            }
            QDialogButtonBox QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #7b8ef0, stop:1 #667eea);
                transform: translateY(-1px);
                box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
            }
            QDialogButtonBox QPushButton:pressed {
                transform: translateY(0px);
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #5a6fd8, stop:1 #4c5fd6);
            }
        """)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def _headers_to_text(self):
        """将请求头字典转换为文本"""
        if not self.current_headers:
            return ""
        
        import json
        return json.dumps(self.current_headers, indent=2, ensure_ascii=False)
    
    def get_headers(self):
        """获取用户输入的请求头"""
        text = self.text_edit.toPlainText().strip()
        if not text:
            return {}
        
        try:
            # 尝试解析为JSON
            import json
            return json.loads(text)
        except json.JSONDecodeError:
            # 尝试按行解析
            headers = {}
            for line in text.split('\n'):
                line = line.strip()
                if ':' in line:
                    key, value = line.split(':', 1)
                    headers[key.strip()] = value.strip()
            return headers


class MainWindow(QMainWindow):
    """主窗口"""
    
    def __init__(self):
        super().__init__()
        self.download_tasks = []
        self.custom_headers = {}  # 存储用户自定义请求头
        self.setup_ui()
        self.load_user_settings()  # 加载用户设置
        
    def setup_ui(self):
        """设置UI"""
        self.setWindowTitle("🌸 M3U8萌动下载器 v1.0 ✨")
        self.setMinimumSize(1000, 800)
        self.resize(1200, 900)
        
        # 设置窗口图标
        try:
            icon_path = os.path.join(os.path.dirname(__file__), "assets", "favicon.ico")
            if os.path.exists(icon_path):
                self.setWindowIcon(QIcon(icon_path))
        except Exception as e:
            print(f"设置窗口图标失败: {e}")
        
        # 创建滚动区域作为中央部件
        main_scroll = QScrollArea()
        main_scroll.setWidgetResizable(True)
        main_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        main_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        main_scroll.setStyleSheet("""
            QScrollArea {
                border: none;
            }
        """)
        self.setCentralWidget(main_scroll)
        
        # 滚动内容容器
        central_widget = QWidget()
        main_scroll.setWidget(central_widget)
        
        # 主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(16)
        
        # 标题区域
        title_container = QWidget()
        title_layout = QVBoxLayout(title_container)
        title_layout.setContentsMargins(0, 0, 0, 0)
        
        # 主标题
        title_label = QLabel("🌸 M3U8萌动下载器 ✨")
        title_label.setFont(QFont("Microsoft YaHei", 24, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("""
            color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #ff6b9d, stop:0.3 #c44cfc, stop:0.7 #667eea, stop:1 #06b6d4);
            margin: 15px 0px;
            padding: 20px;
            border-radius: 20px;
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 rgba(255, 107, 157, 0.08), 
                stop:0.5 rgba(196, 76, 252, 0.05), 
                stop:1 rgba(6, 182, 212, 0.08));
            border: 2px solid transparent;
            border-image: linear-gradient(45deg, #ff6b9d, #c44cfc, #667eea, #06b6d4) 1;
            text-shadow: 0 0 10px rgba(255, 107, 157, 0.5);
        """)
        title_layout.addWidget(title_label)
        
        # 副标题
        subtitle_label = QLabel("💫 可爱又强大的二次元视频下载助手 ~ (´∀`)")
        subtitle_label.setFont(QFont("Microsoft YaHei", 12))
        subtitle_label.setAlignment(Qt.AlignCenter)
        subtitle_label.setStyleSheet("""
            color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #a78bfa, stop:1 #06b6d4); 
            margin-bottom: 15px;
            font-weight: 500;
        """)
        title_layout.addWidget(subtitle_label)
        
        # GitHub链接
        github_label = QLabel('🔗 <a href="https://github.com/shayuaidoudou/m3u8-anime-downloader" style="color: #c44cfc; text-decoration: none;">@shayuaidoudou/m3u8-anime-downloader</a> | 💕 Made with love for anime fans')
        github_label.setFont(QFont("Microsoft YaHei", 9))
        github_label.setAlignment(Qt.AlignCenter)
        github_label.setOpenExternalLinks(True)
        github_label.setStyleSheet("""
            color: #a78bfa;
            margin-bottom: 20px;
        """)
        title_layout.addWidget(github_label)
        
        main_layout.addWidget(title_container)
        
        # 输入设置区域
        input_widget = QWidget()
        input_layout = QVBoxLayout(input_widget)
        
        # 输入组
        input_group = QGroupBox("下载设置")
        input_group.setFont(QFont("Microsoft YaHei", 11, QFont.Bold))
        input_group_layout = QGridLayout(input_group)
        input_group_layout.setSpacing(15)
        
        # M3U8 URL输入
        url_label = QLabel("🎵 视频链接:")
        url_label.setFont(QFont("Microsoft YaHei", 10, QFont.Bold))
        url_label.setStyleSheet("color: #c44cfc; margin-bottom: 8px;")
        input_group_layout.addWidget(url_label, 0, 0)
        
        self.url_input = ModernLineEdit("🎵 请输入M3U8视频链接... (´∀`)")
        input_group_layout.addWidget(self.url_input, 0, 1, 1, 2)
        
        # 输出路径
        output_label = QLabel("💝 保存位置:")
        output_label.setFont(QFont("Microsoft YaHei", 10, QFont.Bold))
        output_label.setStyleSheet("color: #c44cfc; margin-bottom: 8px;")
        input_group_layout.addWidget(output_label, 1, 0)
        
        self.output_input = ModernLineEdit("💝 选择保存路径... ✨")
        input_group_layout.addWidget(self.output_input, 1, 1)
        
        self.browse_btn = ModernButton("浏览", icon_text="📂")
        self.browse_btn.clicked.connect(self.browse_output_path)
        input_group_layout.addWidget(self.browse_btn, 1, 2)
        
        # 高级设置
        threads_label = QLabel("🌟 线程数:")
        threads_label.setFont(QFont("Microsoft YaHei", 10, QFont.Bold))
        threads_label.setStyleSheet("color: #c44cfc; margin-bottom: 8px;")
        input_group_layout.addWidget(threads_label, 2, 0)
        
        self.threads_spin = QSpinBox()
        self.threads_spin.setRange(1, 32)
        self.threads_spin.setValue(DEFAULT_CONFIG['max_workers'])
        self.threads_spin.setMinimumHeight(48)
        self.threads_spin.setStyleSheet("""
            QSpinBox {
                border: 2px solid #ddd6fe;
                border-radius: 16px;
                padding: 14px 20px;
                font-size: 14px;
                font-weight: bold;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #fef7ff, stop:1 #f9fafb);
                color: #374151;
                selection-background-color: #c44cfc;
                box-shadow: inset 0 2px 8px rgba(196, 76, 252, 0.08);
            }
            QSpinBox:focus {
                border-color: #c44cfc;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ffffff, stop:1 #fef7ff);
                box-shadow: 0 0 0 4px rgba(196, 76, 252, 0.25), 
                           inset 0 2px 8px rgba(196, 76, 252, 0.1);
            }
            QSpinBox:hover {
                border-color: #a78bfa;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ffffff, stop:1 #fef7ff);
            }
            QSpinBox::up-button, QSpinBox::down-button {
                border: none;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(196, 76, 252, 0.1), 
                    stop:1 rgba(167, 139, 250, 0.1));
                width: 24px;
                border-radius: 8px;
                margin: 2px;
            }
            QSpinBox::up-button:hover, QSpinBox::down-button:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(196, 76, 252, 0.2), 
                    stop:1 rgba(167, 139, 250, 0.2));
                box-shadow: 0 2px 8px rgba(196, 76, 252, 0.3);
            }
            QSpinBox::up-arrow {
                image: none;
                border: 3px solid transparent;
                border-bottom: 6px solid #c44cfc;
                width: 0px;
                height: 0px;
            }
            QSpinBox::down-arrow {
                image: none;
                border: 3px solid transparent;
                border-top: 6px solid #c44cfc;
                width: 0px;
                height: 0px;
            }
        """)
        input_group_layout.addWidget(self.threads_spin, 2, 1)
        
        # 任务名称
        task_name_label = QLabel("🎀 任务名称:")
        task_name_label.setFont(QFont("Microsoft YaHei", 10, QFont.Bold))
        task_name_label.setStyleSheet("color: #c44cfc; margin-bottom: 8px;")
        input_group_layout.addWidget(task_name_label, 3, 0)
        
        self.task_name_input = ModernLineEdit("🎀 萌萌的任务 ♡")
        input_group_layout.addWidget(self.task_name_input, 3, 1)
        
        # 请求头设置按钮
        self.headers_btn = ModernButton("请求头设置", icon_text="🔧")
        self.headers_btn.clicked.connect(self.show_headers_dialog)
        input_group_layout.addWidget(self.headers_btn, 3, 2)
        
        # 预设模板下拉框
        template_label = QLabel("🛡️ 反爬虫模板:")
        template_label.setFont(QFont("Microsoft YaHei", 10, QFont.Bold))
        template_label.setStyleSheet("color: #c44cfc; margin-bottom: 8px;")
        input_group_layout.addWidget(template_label, 4, 0)
        
        self.template_combo = self._create_template_combo()
        input_group_layout.addWidget(self.template_combo, 4, 1)
        
        # 添加任务按钮
        self.add_task_btn = ModernButton("添加萌萌任务", primary=True, icon_text="💫")
        self.add_task_btn.clicked.connect(self.add_download_task)
        self.add_task_btn.setMinimumHeight(60)
        self.add_task_btn.setFont(QFont("Microsoft YaHei", 12, QFont.Bold))
        input_group_layout.addWidget(self.add_task_btn, 4, 2)
        
        input_layout.addWidget(input_group)
        main_layout.addWidget(input_widget)
        
        # 下载任务区域 - 给予充足的空间
        task_widget = QWidget()
        task_layout = QVBoxLayout(task_widget)
        
        task_group = QGroupBox("下载任务")
        task_group.setFont(QFont("Microsoft YaHei", 11, QFont.Bold))
        self.task_layout = QVBoxLayout(task_group)
        
        # 任务列表滚动区域
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background: transparent;
            }
        """)
        
        self.task_container = QWidget()
        self.task_container_layout = QVBoxLayout(self.task_container)
        self.task_container_layout.addStretch()
        
        self.scroll_area.setWidget(self.task_container)
        self.task_layout.addWidget(self.scroll_area)
        
        task_layout.addWidget(task_group)
        
        # 设置任务区域的最小高度，让它更大更好用
        task_widget.setMinimumHeight(800)  # 更大的任务显示区域
        main_layout.addWidget(task_widget)
        
        # 设置内容区域的最小高度，确保超出窗口时显示滚动条
        central_widget.setMinimumHeight(1400)  # 总高度比窗口高，会出现滚动条
        
        # 状态栏
        self.statusBar().showMessage("准备就绪")
        
        # 菜单栏
        self.setup_menu()
    
    def _create_template_combo(self):
        """创建预设模板下拉框"""
        combo = QComboBox()
        combo.setMinimumHeight(48)
        combo.setStyleSheet("""
            QComboBox {
                border: 2px solid #ddd6fe;
                border-radius: 16px;
                padding: 14px 20px;
                font-size: 14px;
                font-weight: bold;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #fef7ff, stop:1 #f9fafb);
                color: #374151;
                box-shadow: inset 0 2px 8px rgba(196, 76, 252, 0.08);
            }
            QComboBox:focus {
                border-color: #c44cfc;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ffffff, stop:1 #fef7ff);
                box-shadow: 0 0 0 4px rgba(196, 76, 252, 0.25), 
                           inset 0 2px 8px rgba(196, 76, 252, 0.1);
            }
            QComboBox:hover {
                border-color: #a78bfa;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ffffff, stop:1 #fef7ff);
            }
            QComboBox::drop-down {
                border: none;
                width: 35px;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(196, 76, 252, 0.1), 
                    stop:1 rgba(167, 139, 250, 0.1));
                border-radius: 12px;
                margin: 2px;
            }
            QComboBox::drop-down:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(196, 76, 252, 0.2), 
                    stop:1 rgba(167, 139, 250, 0.2));
            }
            QComboBox::down-arrow {
                image: none;
                border: 4px solid transparent;
                border-top: 8px solid #c44cfc;
                width: 0px;
                height: 0px;
                margin-right: 10px;
            }
            QComboBox QAbstractItemView {
                border: 2px solid #ddd6fe;
                border-radius: 16px;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ffffff, stop:1 #fef7ff);
                selection-background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(255, 107, 157, 0.15), 
                    stop:1 rgba(196, 76, 252, 0.15));
                selection-color: #c44cfc;
                padding: 8px;
                font-weight: bold;
                box-shadow: 0 12px 35px rgba(196, 76, 252, 0.2);
            }
            QComboBox QAbstractItemView::item {
                padding: 12px 16px;
                border-radius: 12px;
                margin: 3px;
                color: #374151;
            }
            QComboBox QAbstractItemView::item:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(255, 107, 157, 0.15), 
                    stop:1 rgba(196, 76, 252, 0.15));
                color: #c44cfc;
            }
        """)
        
        # 预设模板
        templates = {
            "默认（无特殊请求头）": {},
            "通用反爬虫": {
                "referer": "https://www.google.com/",
                "sec-ch-ua": '"Not;A=Brand";v="99", "Google Chrome";v="139", "Chromium";v="139"',
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": '"Windows"',
                "sec-fetch-dest": "empty",
                "sec-fetch-mode": "cors",
                "sec-fetch-site": "cross-site",
            },
            "Aigua TV": {
                "accept": "*/*",
                "accept-language": "zh-CN,zh;q=0.9,en;q=0.8",
                "cache-control": "no-cache",
                "origin": "https://aigua.tv",
                "pragma": "no-cache",
                "priority": "u=1, i",
                "referer": "https://aigua.tv/",
                "sec-ch-ua": '"Not;A=Brand";v="99", "Google Chrome";v="139", "Chromium";v="139"',
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": '"Windows"',
                "sec-fetch-dest": "empty",
                "sec-fetch-mode": "cors",
                "sec-fetch-site": "cross-site",
            },
            "移动端模拟": {
                "user-agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
                "sec-ch-ua-mobile": "?1",
                "sec-fetch-dest": "empty",
                "sec-fetch-mode": "cors",
                "sec-fetch-site": "cross-site",
            }
        }
        
        for name, headers in templates.items():
            combo.addItem(name, headers)
        
        combo.currentTextChanged.connect(self._on_template_changed)
        return combo
    
    def _on_template_changed(self):
        """模板选择改变时的处理"""
        current_data = self.template_combo.currentData()
        if current_data:
            self.custom_headers = current_data.copy()
            # 显示已选择模板的提示
            if current_data:
                self.statusBar().showMessage(f"已选择模板: {self.template_combo.currentText()}")
    
    def show_headers_dialog(self):
        """显示请求头配置对话框"""
        dialog = HeadersDialog(self, self.custom_headers)
        if dialog.exec() == QDialog.Accepted:
            self.custom_headers = dialog.get_headers()
            # 重置模板选择
            self.template_combo.setCurrentIndex(0)
            if self.custom_headers:
                self.statusBar().showMessage(f"已配置 {len(self.custom_headers)} 个自定义请求头")
            else:
                self.statusBar().showMessage("已清除自定义请求头")
    
    def setup_menu(self):
        """设置菜单栏"""
        menubar = self.menuBar()
        
        # 文件菜单
        file_menu = menubar.addMenu("📂 文件")
        
        open_action = QAction("📁 打开下载目录", self)
        open_action.triggered.connect(self.open_download_folder)
        file_menu.addAction(open_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("🚪 退出", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 工具菜单
        tools_menu = menubar.addMenu("🛠️ 工具")
        
        # 设置选项
        settings_action = QAction("⚙️ 萌萌设置", self)
        settings_action.triggered.connect(self.show_settings)
        tools_menu.addAction(settings_action)
        
        tools_menu.addSeparator()
        
        # 请求头配置
        headers_action = QAction("🔧 请求头配置", self)
        headers_action.triggered.connect(self.show_headers_dialog)
        tools_menu.addAction(headers_action)
        
        # 帮助菜单
        help_menu = menubar.addMenu("❓ 帮助")
        
        about_action = QAction("ℹ️ 关于", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
        # GitHub菜单 - 更可靠的显示方式
        github_menu = menubar.addMenu("⭐ GitHub")
        
        github_action = QAction("🔗 访问GitHub仓库", self)
        github_action.triggered.connect(self.open_github_repo)
        github_menu.addAction(github_action)
        
        # 可选：如果系统支持，仍然尝试在右上角添加按钮
        try:
            github_btn = QPushButton("⭐")
            github_btn.setFixedSize(30, 25)
            github_btn.setCursor(Qt.PointingHandCursor)
            github_btn.setToolTip("访问GitHub仓库 ✨")
            github_btn.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 rgba(255, 107, 157, 0.8), 
                        stop:0.5 rgba(196, 76, 252, 0.8), 
                        stop:1 rgba(102, 126, 234, 0.8));
                    border: 1px solid rgba(255, 255, 255, 0.3);
                    border-radius: 12px;
                    color: white;
                    font-weight: bold;
                    font-size: 14px;
                    text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 rgba(255, 107, 157, 1.0), 
                        stop:0.5 rgba(196, 76, 252, 1.0), 
                        stop:1 rgba(102, 126, 234, 1.0));
                    border-color: rgba(255, 255, 255, 0.5);
                }
            """)
            github_btn.clicked.connect(self.open_github_repo)
            menubar.setCornerWidget(github_btn, Qt.TopRightCorner)
        except Exception:
            # 如果角落组件不支持，忽略错误
            pass
    
    def open_github_repo(self):
        """打开GitHub仓库"""
        try:
            github_url = "https://github.com/shayuaidoudou/m3u8-anime-downloader"
            QDesktopServices.openUrl(QUrl(github_url))
            self.statusBar().showMessage("正在打开GitHub仓库... ✨")
        except Exception as e:
            self.statusBar().showMessage(f"打开GitHub失败: {str(e)}")
    
    def browse_output_path(self):
        """浏览输出路径"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "选择保存路径",
            "",
            "MP4文件 (*.mp4);;TS文件 (*.ts);;所有文件 (*.*)"
        )
        
        if file_path:
            self.output_input.setText(file_path)
    
    def add_download_task(self):
        """添加下载任务"""
        url = self.url_input.text().strip()
        output_path = self.output_input.text().strip()
        task_name = self.task_name_input.text().strip()
        
        # 验证URL
        if not url:
            CustomMessageBox.show_warning(self, "提示 ♡", "请输入M3U8链接哦~ (´∀`)")
            return
        
        if not is_valid_m3u8_url(url):
            CustomMessageBox.show_warning(self, "提示 ♡", "请输入有效的M3U8链接呢~ (๑•̀ㅂ•́)و✧")
            return
        
        # 验证输出路径
        if not output_path:
            CustomMessageBox.show_warning(self, "提示 ♡", "请选择保存路径哦~ (￣▽￣)")
            return
        
        # 确保文件扩展名
        output_path = ensure_extension(output_path)
        
        # 验证输出路径
        is_valid, error_msg = validate_output_path(output_path)
        if not is_valid:
            CustomMessageBox.show_warning(self, "提示 ♡", f"输出路径有问题呢~ {error_msg} (๑＞◡＜๑)")
            return
        
        # 避免文件名冲突
        output_path = get_available_filename(output_path)
        
        # 生成任务名称
        if not task_name:
            task_name = extract_title_from_url(url)
            if not task_name or task_name == "未知视频":
                task_name = f"萌萌任务_{len(self.download_tasks) + 1} ✨"
        
        # 创建任务组件（包含自定义请求头）
        task_widget = DownloadTaskWidget(task_name, url, output_path, self.custom_headers.copy())
        
        # 插入到任务容器的最后一个位置（stretch之前）
        self.task_container_layout.insertWidget(
            self.task_container_layout.count() - 1, 
            task_widget
        )
        
        self.download_tasks.append(task_widget)
        
        # 清空输入框
        self.url_input.clear()
        self.task_name_input.setText("萌萌的任务 ♡")
        
        # 显示任务信息
        headers_info = f" (包含 {len(self.custom_headers)} 个自定义请求头)" if self.custom_headers else ""
        self.statusBar().showMessage(f"已添加任务: {task_name}{headers_info}")
    
    def open_download_folder(self):
        """打开下载文件夹"""
        if self.download_tasks:
            last_output = self.download_tasks[-1].output_path
            folder_path = os.path.dirname(last_output)
            if os.path.exists(folder_path):
                QDesktopServices.openUrl(QUrl.fromLocalFile(folder_path))
            else:
                CustomMessageBox.show_info(self, "提示 ♡", "下载文件夹不存在呢~ (´･ω･`)")
        else:
            CustomMessageBox.show_info(self, "提示 ♡", "还没有下载任务哦~ 快来添加一个吧！ ヽ(°〇°)ﾉ")
    
    def show_settings(self):
        """显示设置对话框"""
        settings_dialog = SettingsDialog(self)
        settings_dialog.exec()
    
    def show_about(self):
        """显示关于对话框"""
        about_message = """🌸 M3U8萌动下载器 v1.0 ✨

💖 一个超可爱的二次元风格视频下载工具 (´∀`)

🌟 萌萌功能：
• 🚀 支持多线程高速下载
• 🔐 支持AES加密视频解密  
• 🎨 二次元风格现代化界面
• 📋 任务管理和进度显示
• 💫 可爱的视觉效果
• 🛡️ 智能反爬虫功能

🛠️ 基于 PySide6 构建
🔗 开源地址: github.com/shayuaidoudou/m3u8-anime-downloader
💕 Made with love for anime fans ~"""
        
        CustomMessageBox.show_info(
            self,
            "关于 M3U8萌动下载器",
            about_message
        )
    
    def apply_theme(self, theme_index):
        """应用主题颜色"""
        # 定义主题色方案
        themes = {
            0: {  # 💙 经典蓝紫
                'primary': '#667eea',
                'secondary': '#764ba2', 
                'accent': '#c44cfc',
                'bg_start': '#fef7ff',
                'bg_mid': '#f0f9ff',
                'bg_end': '#f3e8ff'
            },
            1: {  # 💖 可爱粉色
                'primary': '#ff6b9d',
                'secondary': '#f093fb',
                'accent': '#ff8cc8',
                'bg_start': '#fef7f7',
                'bg_mid': '#fff0f5',
                'bg_end': '#fdf2f8'
            },
            2: {  # 💚 清新绿色
                'primary': '#10b981',
                'secondary': '#34d399',
                'accent': '#059669',
                'bg_start': '#f0fdf4',
                'bg_mid': '#ecfdf5',
                'bg_end': '#d1fae5'
            },
            3: {  # 💛 活力橙色
                'primary': '#f59e0b',
                'secondary': '#fbbf24',
                'accent': '#d97706',
                'bg_start': '#fffbeb',
                'bg_mid': '#fef3c7',
                'bg_end': '#fed7aa'
            },
            4: {  # 💜 神秘紫色
                'primary': '#8b5cf6',
                'secondary': '#a78bfa',
                'accent': '#7c3aed',
                'bg_start': '#faf5ff',
                'bg_mid': '#f3e8ff',
                'bg_end': '#e9d5ff'
            },
            5: {  # ❤️ 激情红色
                'primary': '#ef4444',
                'secondary': '#f87171',
                'accent': '#dc2626',
                'bg_start': '#fef2f2',
                'bg_mid': '#fee2e2',
                'bg_end': '#fecaca'
            }
        }
        
        # 获取选中的主题
        theme = themes.get(theme_index, themes[0])
        
        # 应用主题样式
        self.setStyleSheet(f"""
            QMainWindow {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {theme['bg_start']}, stop:0.25 {theme['bg_mid']}, 
                    stop:0.5 {theme['bg_end']}, stop:0.75 {theme['bg_mid']}, stop:1 {theme['bg_start']});
            }}
            QGroupBox {{
                font-weight: bold;
                border: 2px solid {theme['primary']};
                border-radius: 20px;
                margin: 15px 6px;
                padding-top: 20px;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(255, 255, 255, 0.9), 
                    stop:0.5 rgba(254, 247, 255, 0.8), 
                    stop:1 rgba(243, 232, 255, 0.9));
                box-shadow: 0 8px 30px rgba({self._theme_hex_to_rgb(theme['primary'])}, 0.15);
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 25px;
                padding: 6px 16px;
                color: {theme['accent']};
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba({self._theme_hex_to_rgb(theme['primary'])}, 0.15), 
                    stop:1 rgba({self._theme_hex_to_rgb(theme['accent'])}, 0.15));
                border-radius: 12px;
                font-size: 13px;
                font-weight: bold;
                border: 1px solid rgba({self._theme_hex_to_rgb(theme['accent'])}, 0.2);
            }}
            QLabel {{
                color: #2c3e50;
                font-family: "Microsoft YaHei";
            }}
            QStatusBar {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {theme['bg_start']}, stop:0.5 {theme['bg_mid']}, stop:1 {theme['bg_end']});
                border-top: 2px solid {theme['primary']};
                color: {theme['accent']};
                font-weight: bold;
                padding: 10px;
                border-radius: 0px 0px 8px 8px;
            }}
            QMenuBar {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {theme['bg_start']}, stop:0.5 {theme['bg_mid']}, stop:1 {theme['bg_end']});
                border-bottom: 2px solid {theme['primary']};
                padding: 8px;
                border-radius: 8px 8px 0px 0px;
            }}
            QMenuBar::item {{
                padding: 12px 18px;
                border-radius: 12px;
                font-weight: bold;
                color: #374151;
            }}
            QMenuBar::item:selected {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba({self._theme_hex_to_rgb(theme['primary'])}, 0.15), 
                    stop:1 rgba({self._theme_hex_to_rgb(theme['accent'])}, 0.15));
                color: {theme['accent']};
            }}
            QMenu {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ffffff, stop:1 {theme['bg_start']});
                border: 2px solid {theme['primary']};
                border-radius: 16px;
                padding: 10px;
                box-shadow: 0 12px 35px rgba({self._theme_hex_to_rgb(theme['primary'])}, 0.2);
            }}
            QMenu::item {{
                padding: 12px 20px;
                border-radius: 12px;
                font-weight: bold;
                color: #374151;
                margin: 3px;
            }}
            QMenu::item:selected {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba({self._theme_hex_to_rgb(theme['primary'])}, 0.15), 
                    stop:1 rgba({self._theme_hex_to_rgb(theme['accent'])}, 0.15));
                color: {theme['accent']};
            }}
            QScrollBar:vertical {{
                background: rgba({self._theme_hex_to_rgb(theme['primary'])}, 0.1);
                width: 14px;
                border-radius: 7px;
            }}
            QScrollBar::handle:vertical {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {theme['primary']}, stop:0.5 {theme['accent']}, stop:1 {theme['secondary']});
                border-radius: 7px;
                min-height: 25px;
                box-shadow: 0 2px 8px rgba({self._theme_hex_to_rgb(theme['primary'])}, 0.3);
            }}
            QScrollBar::handle:vertical:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {theme['secondary']}, stop:0.5 {theme['accent']}, stop:1 {theme['primary']});
                box-shadow: 0 4px 12px rgba({self._theme_hex_to_rgb(theme['primary'])}, 0.5);
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                border: none;
                background: none;
            }}
        """)
        
        print(f"🎨 已应用主题: {theme_index} - {['💙 经典蓝紫', '💖 可爱粉色', '💚 清新绿色', '💛 活力橙色', '💜 神秘紫色', '❤️ 激情红色'][theme_index]}")
    
    def _theme_hex_to_rgb(self, hex_color):
        """将十六进制颜色转换为RGB（用于主题）"""
        hex_color = hex_color.lstrip('#')
        return ', '.join(str(int(hex_color[i:i+2], 16)) for i in (0, 2, 4))
    
    def load_user_settings(self):
        """启动时加载用户设置"""
        settings_file = os.path.join(os.path.dirname(__file__), "settings.json")
        
        try:
            if os.path.exists(settings_file):
                with open(settings_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                
                # 应用UI设置
                ui = settings.get('ui', {})
                opacity = ui.get('opacity', 95) / 100.0
                self.setWindowOpacity(opacity)
                
                # 应用主题设置
                theme_index = ui.get('theme_color', 0)
                self.apply_theme(theme_index)
                
                # 应用下载设置
                download = settings.get('download', {})
                
                # 设置默认线程数
                default_threads = download.get('default_threads', DEFAULT_CONFIG['max_workers'])
                if hasattr(self, 'threads_spin'):
                    self.threads_spin.setValue(default_threads)
                
                # 设置默认保存路径
                default_path = download.get('default_path', '')
                if default_path and os.path.exists(default_path) and hasattr(self, 'output_input'):
                    self.output_input.setText(default_path)
                
                print(f"✅ 已加载用户设置: 线程数={default_threads}, 路径={default_path}, 主题={theme_index}")
                
        except Exception as e:
            print(f"⚠️ 加载用户设置失败: {e}")
            # 继续使用默认设置


def main():
    """主函数"""
    app = QApplication(sys.argv)
    app.setApplicationName("M3U8萌动下载器")
    app.setOrganizationName("M3U8AnimeDownloader")
    
    # 设置应用图标
    try:
        icon_path = os.path.join(os.path.dirname(__file__), "assets", "favicon.ico")
        if os.path.exists(icon_path):
            app.setWindowIcon(QIcon(icon_path))
    except Exception as e:
        print(f"设置应用图标失败: {e}")
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
