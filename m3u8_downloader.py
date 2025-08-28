#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
M3U8 高速下载器核心模块
支持多线程、异步下载和AES解密
"""

import os
import re
import requests
import asyncio
import aiohttp
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urljoin, urlparse, urlsplit, urlunsplit
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import threading
from typing import List, Optional, Callable, Dict, Any
import time


class AESDecryptor:
    """AES解密处理器"""
    
    def __init__(self, custom_headers: Dict[str, str] = None):
        self.key_cache: Dict[str, bytes] = {}
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36'
        }
        if custom_headers:
            self.headers.update(custom_headers)
    
    def get_key(self, key_uri: str, headers: Dict[str, str] = None) -> bytes:
        """获取AES密钥"""
        if key_uri in self.key_cache:
            return self.key_cache[key_uri]
        
        try:
            # 优先使用传入的headers，否则使用实例的headers
            request_headers = headers or self.headers
            print(f"[DEBUG] 获取密钥: {key_uri}")
            print(f"[DEBUG] 密钥请求头: {request_headers}")
            
            response = requests.get(key_uri, headers=request_headers, timeout=10)
            response.raise_for_status()
            key = response.content
            self.key_cache[key_uri] = key
            print(f"[DEBUG] 密钥获取成功，长度: {len(key)} 字节")
            return key
        except Exception as e:
            print(f"[ERROR] 获取AES密钥失败: {e}")
            raise Exception(f"获取AES密钥失败: {e}")
    
    def decrypt_segment(self, encrypted_data: bytes, key: bytes, iv: bytes = None) -> bytes:
        """解密TS片段"""
        if iv is None:
            iv = b'\x00' * 16
        
        cipher = Cipher(
            algorithms.AES(key),
            modes.CBC(iv),
            backend=default_backend()
        )
        decryptor = cipher.decryptor()
        decrypted_data = decryptor.update(encrypted_data) + decryptor.finalize()
        
        # 移除PKCS7填充
        padding_length = decrypted_data[-1]
        if padding_length <= 16:
            decrypted_data = decrypted_data[:-padding_length]
        
        return decrypted_data


class M3U8Parser:
    """M3U8播放列表解析器"""
    
    def __init__(self, custom_headers: Dict[str, str] = None):
        self.base_url = ""
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36',
            'Accept': '*/*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
        }
        # 如果提供了自定义请求头，则合并
        if custom_headers:
            self.headers.update(custom_headers)
            print(f"[DEBUG] 使用自定义请求头: {custom_headers}")
    
    def parse_m3u8(self, url: str) -> Dict[str, Any]:
        """解析M3U8文件"""
        try:
            print(f"[DEBUG] 请求M3U8文件: {url}")
            print(f"[DEBUG] 请求头: {self.headers}")
            
            response = requests.get(url, headers=self.headers, timeout=15)
            print(f"[DEBUG] 响应状态码: {response.status_code}")
            print(f"[DEBUG] 响应头: {dict(response.headers)}")
            
            response.raise_for_status()
            content = response.text
            print(f"[DEBUG] 内容长度: {len(content)} 字符")
            print(f"[DEBUG] 内容预览: {content[:500]}")
            
            if not content.strip():
                raise Exception("M3U8文件内容为空")
            
            if not content.startswith('#EXTM3U'):
                print(f"[WARNING] M3U8文件没有标准开头，内容可能不是有效的M3U8格式")
            
            # 更准确的基础URL处理
            parsed_url = urlparse(url)
            if parsed_url.path.endswith('.m3u8'):
                # 移除文件名，保留目录路径
                path_parts = parsed_url.path.rsplit('/', 1)
                base_path = path_parts[0] + '/' if len(path_parts) > 1 else '/'
                self.base_url = f"{parsed_url.scheme}://{parsed_url.netloc}{base_path}"
            else:
                self.base_url = url if url.endswith('/') else url + '/'
            print(f"[DEBUG] 基础URL: {self.base_url}")
            
            # 解析播放列表信息
            playlist_info = {
                'segments': [],
                'encryption': None,
                'total_duration': 0,
                'base_url': self.base_url
            }
            
            lines = content.strip().split('\n')
            print(f"[DEBUG] M3U8文件行数: {len(lines)}")
            
            current_segment = {}
            encryption_info = None
            
            # 检查是否是主播放列表（master playlist）
            is_master_playlist = any('#EXT-X-STREAM-INF' in line for line in lines)
            if is_master_playlist:
                print("[DEBUG] 检测到主播放列表，查找子播放列表...")
                # 找到第一个子播放列表URL
                for i, line in enumerate(lines):
                    if line.startswith('#EXT-X-STREAM-INF'):
                        if i + 1 < len(lines):
                            next_line = lines[i + 1].strip()
                            if next_line and not next_line.startswith('#'):
                                sub_m3u8_url = urljoin(self.base_url, next_line)
                                print(f"[DEBUG] 找到子播放列表: {sub_m3u8_url}")
                                # 递归解析子播放列表
                                return self.parse_m3u8(sub_m3u8_url)
                
                raise Exception("主播放列表中未找到有效的子播放列表")
            
            for line_num, line in enumerate(lines):
                line = line.strip()
                
                if line.startswith('#EXT-X-KEY:'):
                    # 解析加密信息
                    encryption_info = self._parse_key_line(line)
                    playlist_info['encryption'] = encryption_info
                    print(f"[DEBUG] 找到加密信息: {encryption_info}")
                
                elif line.startswith('#EXTINF:'):
                    # 解析段信息
                    duration_match = re.search(r'#EXTINF:([\d.]+)', line)
                    if duration_match:
                        duration = float(duration_match.group(1))
                        current_segment = {'duration': duration}
                        playlist_info['total_duration'] += duration
                
                elif line and not line.startswith('#'):
                    # TS文件URL
                    if current_segment:
                        segment_url = urljoin(self.base_url, line)
                        current_segment['url'] = segment_url
                        current_segment['index'] = len(playlist_info['segments'])
                        if encryption_info:
                            current_segment['encryption'] = encryption_info.copy()
                        
                        playlist_info['segments'].append(current_segment)
                        print(f"[DEBUG] 添加片段 {current_segment['index']}: {segment_url}")
                        current_segment = {}
                    else:
                        # 没有对应的EXTINF，可能是直接的TS文件
                        segment_url = urljoin(self.base_url, line)
                        segment_info = {
                            'url': segment_url,
                            'index': len(playlist_info['segments']),
                            'duration': 10.0  # 默认时长
                        }
                        if encryption_info:
                            segment_info['encryption'] = encryption_info.copy()
                        
                        playlist_info['segments'].append(segment_info)
                        print(f"[DEBUG] 添加片段(无EXTINF) {segment_info['index']}: {segment_url}")
            
            print(f"[DEBUG] 解析完成: {len(playlist_info['segments'])} 个片段, 总时长: {playlist_info['total_duration']:.1f}秒")
            
            if len(playlist_info['segments']) == 0:
                raise Exception("未找到任何视频片段，可能不是有效的M3U8文件")
            
            return playlist_info
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"网络请求失败: {e}")
        except Exception as e:
            print(f"[ERROR] M3U8解析异常: {str(e)}")
            import traceback
            print(f"[ERROR] 详细错误: {traceback.format_exc()}")
            raise Exception(f"解析M3U8失败: {e}")
    
    def _parse_key_line(self, line: str) -> Dict[str, str]:
        """解析KEY行"""
        key_info = {}
        
        # 解析METHOD
        method_match = re.search(r'METHOD=([^,\s]+)', line)
        if method_match:
            key_info['method'] = method_match.group(1)
        
        # 解析URI
        uri_match = re.search(r'URI="([^"]+)"', line)
        if uri_match:
            key_uri = uri_match.group(1)
            key_info['uri'] = urljoin(self.base_url, key_uri)
        
        # 解析IV
        iv_match = re.search(r'IV=0x([0-9a-fA-F]+)', line)
        if iv_match:
            key_info['iv'] = bytes.fromhex(iv_match.group(1))
        
        return key_info


class ProgressCallback:
    """进度回调处理器"""
    
    def __init__(self, callback: Callable = None):
        self.callback = callback
        self.total_segments = 0
        self.completed_segments = 0
        self.failed_segments = 0
        self.start_time = time.time()
        self._lock = threading.Lock()
    
    def set_total(self, total: int):
        """设置总段数"""
        self.total_segments = total
    
    def update_progress(self, success: bool = True):
        """更新进度"""
        with self._lock:
            if success:
                self.completed_segments += 1
            else:
                self.failed_segments += 1
            
            if self.callback:
                progress_data = {
                    'completed': self.completed_segments,
                    'failed': self.failed_segments,
                    'total': self.total_segments,
                    'progress': (self.completed_segments + self.failed_segments) / self.total_segments * 100 if self.total_segments > 0 else 0,
                    'speed': self.completed_segments / (time.time() - self.start_time + 1),
                    'eta': (self.total_segments - self.completed_segments - self.failed_segments) / (self.completed_segments / (time.time() - self.start_time + 1)) if self.completed_segments > 0 else 0
                }
                self.callback(progress_data)


class M3U8Downloader:
    """M3U8高速下载器"""
    
    def __init__(self, max_workers: int = 10, max_retries: int = 3, custom_headers: Dict[str, str] = None):
        self.max_workers = max_workers
        self.max_retries = max_retries
        self.custom_headers = custom_headers or {}
        
        self.parser = M3U8Parser(custom_headers)
        self.decryptor = AESDecryptor(custom_headers)
        self.session = requests.Session()
        
        # 设置默认请求头
        default_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36',
            'Accept': '*/*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
        }
        
        # 合并自定义请求头
        if custom_headers:
            default_headers.update(custom_headers)
            print(f"[DEBUG] 下载器使用自定义请求头: {custom_headers}")
        
        self.session.headers.update(default_headers)
        self._stop_flag = threading.Event()
    
    def download(self, m3u8_url: str, output_path: str, progress_callback: Callable = None) -> bool:
        """下载M3U8视频"""
        try:
            # 重置停止标志
            self._stop_flag.clear()
            
            # 解析M3U8
            if progress_callback:
                progress_callback({'status': 'parsing', 'message': '正在解析M3U8文件...'})
            
            print(f"[DEBUG] 开始解析M3U8: {m3u8_url}")
            playlist_info = self.parser.parse_m3u8(m3u8_url)
            segments = playlist_info['segments']
            print(f"[DEBUG] 解析完成，找到 {len(segments)} 个片段")
            
            if not segments:
                raise Exception("未找到视频片段，请检查M3U8链接是否正确")
            
            # 检查加密信息
            encryption = playlist_info.get('encryption')
            if encryption:
                print(f"[DEBUG] 检测到加密: {encryption}")
                if progress_callback:
                    progress_callback({'status': 'parsing', 'message': f'检测到{encryption["method"]}加密，正在准备解密...'})
            
            # 创建输出目录
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            temp_dir = output_path + '_temp'
            os.makedirs(temp_dir, exist_ok=True)
            print(f"[DEBUG] 临时目录: {temp_dir}")
            
            # 设置进度回调
            progress = ProgressCallback(progress_callback)
            progress.set_total(len(segments))
            
            if progress_callback:
                progress_callback({'status': 'downloading', 'message': f'开始下载 {len(segments)} 个片段...'})
            
            # 多线程下载片段
            downloaded_files = self._download_segments(segments, temp_dir, encryption, progress)
            print(f"[DEBUG] 下载完成，成功下载 {len([f for f in downloaded_files if f])} 个片段")
            
            if self._stop_flag.is_set():
                print("[DEBUG] 下载被用户停止")
                return False
            
            # 检查下载结果
            successful_downloads = [f for f in downloaded_files if f]
            if len(successful_downloads) == 0:
                raise Exception("所有片段下载都失败了，请检查网络连接和链接有效性")
            elif len(successful_downloads) < len(segments) * 0.8:  # 如果超过20%的片段失败
                print(f"[WARNING] 只有 {len(successful_downloads)}/{len(segments)} 个片段下载成功")
                if progress_callback:
                    progress_callback({'status': 'warning', 'message': f'警告: 只下载了 {len(successful_downloads)}/{len(segments)} 个片段'})
            
            # 合并片段
            if progress_callback:
                progress_callback({'status': 'merging', 'message': '正在合并视频片段...'})
            
            self._merge_segments(successful_downloads, output_path)
            print(f"[DEBUG] 视频合并完成: {output_path}")
            
            # 清理临时文件
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)
            
            if progress_callback:
                progress_callback({'status': 'completed', 'message': '下载完成！'})
            
            return True
            
        except Exception as e:
            print(f"[ERROR] 下载失败: {str(e)}")
            import traceback
            print(f"[ERROR] 详细错误: {traceback.format_exc()}")
            if progress_callback:
                progress_callback({'status': 'error', 'message': f'下载失败: {str(e)}'})
            return False
    
    def _download_segments(self, segments: List[Dict], temp_dir: str, encryption: Dict = None, progress: ProgressCallback = None) -> List[str]:
        """多线程下载片段"""
        downloaded_files = [''] * len(segments)
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # 提交所有下载任务
            future_to_index = {}
            for i, segment in enumerate(segments):
                if self._stop_flag.is_set():
                    break
                future = executor.submit(self._download_segment, segment, temp_dir, encryption)
                future_to_index[future] = i
            
            # 处理下载结果
            for future in as_completed(future_to_index):
                if self._stop_flag.is_set():
                    break
                    
                index = future_to_index[future]
                try:
                    file_path = future.result()
                    if file_path:
                        downloaded_files[index] = file_path
                        if progress:
                            progress.update_progress(True)
                    else:
                        if progress:
                            progress.update_progress(False)
                except Exception as e:
                    if progress:
                        progress.update_progress(False)
        
        return [f for f in downloaded_files if f]
    
    def _download_segment(self, segment: Dict, temp_dir: str, encryption: Dict = None) -> Optional[str]:
        """下载单个片段"""
        url = segment['url']
        index = segment['index']
        file_path = os.path.join(temp_dir, f'segment_{index:06d}.ts')
        
        for attempt in range(self.max_retries):
            if self._stop_flag.is_set():
                return None
                
            try:
                if attempt == 0:
                    print(f"[DEBUG] 开始下载片段 {index}: {url}")
                
                response = self.session.get(url, timeout=30)
                response.raise_for_status()
                
                data = response.content
                print(f"[DEBUG] 片段 {index} 下载完成，大小: {len(data)} 字节")
                
                if len(data) == 0:
                    raise Exception("片段数据为空")
                
                # AES解密处理
                if encryption and encryption.get('method') == 'AES-128':
                    print(f"[DEBUG] 对片段 {index} 进行AES解密")
                    try:
                        # 传递session的headers给解密器
                        key = self.decryptor.get_key(encryption['uri'], dict(self.session.headers))
                        iv = encryption.get('iv', bytes.fromhex(f'{index:032x}'))
                        data = self.decryptor.decrypt_segment(data, key, iv)
                        print(f"[DEBUG] 片段 {index} 解密成功，解密后大小: {len(data)} 字节")
                    except Exception as decrypt_error:
                        print(f"[ERROR] 片段 {index} 解密失败: {decrypt_error}")
                        raise decrypt_error
                
                # 写入文件
                with open(file_path, 'wb') as f:
                    f.write(data)
                
                print(f"[DEBUG] 片段 {index} 保存成功: {file_path}")
                return file_path
                
            except Exception as e:
                print(f"[ERROR] 下载片段 {index} 失败 (尝试 {attempt + 1}/{self.max_retries}): {e}")
                if attempt == self.max_retries - 1:
                    print(f"[ERROR] 片段 {index} 最终下载失败: {e}")
                    return None
                
                # 等待后重试
                wait_time = min(2 ** attempt, 10)  # 指数退避，最多等10秒
                print(f"[DEBUG] 等待 {wait_time} 秒后重试...")
                time.sleep(wait_time)
        
        return None
    
    def _merge_segments(self, segment_files: List[str], output_path: str):
        """合并视频片段"""
        with open(output_path, 'wb') as output_file:
            for segment_file in sorted(segment_files):
                if os.path.exists(segment_file):
                    with open(segment_file, 'rb') as f:
                        output_file.write(f.read())
    
    def stop_download(self):
        """停止下载"""
        self._stop_flag.set()


if __name__ == "__main__":
    # 测试代码
    def progress_callback(data):
        if 'progress' in data:
            print(f"进度: {data['progress']:.1f}% ({data['completed']}/{data['total']})")
        elif 'message' in data:
            print(data['message'])
    
    downloader = M3U8Downloader(max_workers=16)
    # 这里需要真实的m3u8 URL进行测试
    # success = downloader.download("your_m3u8_url_here", "output_video.mp4", progress_callback)
