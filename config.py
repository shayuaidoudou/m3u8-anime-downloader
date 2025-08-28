#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
M3U8下载器配置文件
"""

# 默认配置
DEFAULT_CONFIG = {
    # 下载设置
    'max_workers': 16,              # 默认线程数
    'max_retries': 3,               # 最大重试次数
    'timeout': 30,                  # 请求超时时间（秒）
    'chunk_size': 8192,             # 下载块大小
    
    # UI设置
    'window_width': 1200,           # 窗口默认宽度
    'window_height': 900,           # 窗口默认高度
    'theme': 'modern',              # 界面主题
    
    # 网络设置
    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'headers': {
        'Accept': '*/*',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
    },
    
    # 文件设置
    'temp_dir_suffix': '_temp',     # 临时目录后缀
    'segment_name_format': 'segment_{index:06d}.ts',  # 片段文件命名格式
    
    # 高级设置
    'enable_proxy': False,          # 是否启用代理
    'proxy_url': '',               # 代理地址
    'enable_logging': True,        # 是否启用日志
    'log_level': 'INFO',           # 日志级别
}

# 支持的视频格式
SUPPORTED_FORMATS = [
    '.mp4', '.ts', '.m4v', '.mkv', '.avi', '.mov'
]

# 错误消息
ERROR_MESSAGES = {
    'invalid_url': '无效的M3U8链接',
    'network_error': '网络连接错误',
    'parse_error': '解析M3U8文件失败',
    'download_error': '下载失败',
    'decrypt_error': 'AES解密失败',
    'file_error': '文件操作失败',
}

# 状态消息
STATUS_MESSAGES = {
    'ready': '准备就绪',
    'parsing': '正在解析M3U8文件...',
    'downloading': '正在下载...',
    'merging': '正在合并视频片段...',
    'completed': '下载完成！',
    'failed': '下载失败',
    'stopped': '已停止',
}
