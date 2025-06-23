#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
音频播放器模块

使用PyQt5的QMediaPlayer实现音频播放功能
"""

import os

from PyQt5.QtCore import QObject, pyqtSignal, QUrl
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent


class AudioPlayer(QObject):
    """音频播放器"""
    
    # 定义信号
    playback_started = pyqtSignal()       # 播放开始信号
    playback_stopped = pyqtSignal()       # 播放结束信号
    playback_error = pyqtSignal(str)      # 播放错误信号，参数为错误信息
    playback_position = pyqtSignal(int)   # 播放位置信号，参数为位置（毫秒）
    playback_duration = pyqtSignal(int)   # 播放时长信号，参数为时长（毫秒）
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.player = QMediaPlayer(parent)
        self.current_file = None
        
        # 连接信号
        self.player.stateChanged.connect(self._on_state_changed)
        self.player.positionChanged.connect(self._on_position_changed)
        self.player.durationChanged.connect(self._on_duration_changed)
        self.player.error.connect(self._on_error)
    
    def play(self, file_path=None):
        """播放音频文件
        
        Args:
            file_path: 音频文件路径，如果为None则播放当前文件
            
        Returns:
            bool: 是否成功开始播放
        """
        if file_path:
            # 检查文件是否存在
            if not os.path.exists(file_path):
                self.playback_error.emit(f"文件不存在: {file_path}")
                return False
            
            # 设置媒体内容
            self.current_file = file_path
            url = QUrl.fromLocalFile(file_path)
            media_content = QMediaContent(url)
            self.player.setMedia(media_content)
        
        # 开始播放
        self.player.play()
        return True
    
    def pause(self):
        """暂停播放"""
        self.player.pause()
    
    def resume(self):
        """恢复播放"""
        self.player.play()
    
    def stop(self):
        """停止播放"""
        self.player.stop()
    
    def set_volume(self, volume):
        """设置音量
        
        Args:
            volume: 音量值，范围为0-100
        """
        self.player.setVolume(volume)
    
    def get_volume(self):
        """获取音量
        
        Returns:
            int: 音量值，范围为0-100
        """
        return self.player.volume()
    
    def set_position(self, position):
        """设置播放位置
        
        Args:
            position: 播放位置，单位为毫秒
        """
        self.player.setPosition(position)
    
    def get_position(self):
        """获取播放位置
        
        Returns:
            int: 播放位置，单位为毫秒
        """
        return self.player.position()
    
    def get_duration(self):
        """获取音频时长
        
        Returns:
            int: 音频时长，单位为毫秒
        """
        return self.player.duration()
    
    def is_playing(self):
        """是否正在播放
        
        Returns:
            bool: 是否正在播放
        """
        return self.player.state() == QMediaPlayer.PlayingState
    
    def _on_state_changed(self, state):
        """播放状态改变事件
        
        Args:
            state: 播放状态
        """
        if state == QMediaPlayer.PlayingState:
            self.playback_started.emit()
        elif state == QMediaPlayer.StoppedState:
            self.playback_stopped.emit()
    
    def _on_position_changed(self, position):
        """播放位置改变事件
        
        Args:
            position: 播放位置，单位为毫秒
        """
        self.playback_position.emit(position)
    
    def _on_duration_changed(self, duration):
        """播放时长改变事件
        
        Args:
            duration: 播放时长，单位为毫秒
        """
        self.playback_duration.emit(duration)
    
    def _on_error(self, error):
        """播放错误事件
        
        Args:
            error: 错误代码
        """
        error_msg = "未知错误"
        if error == QMediaPlayer.ResourceError:
            error_msg = "资源错误，无法加载媒体"
        elif error == QMediaPlayer.FormatError:
            error_msg = "格式错误，不支持的媒体格式"
        elif error == QMediaPlayer.NetworkError:
            error_msg = "网络错误，无法加载媒体"
        elif error == QMediaPlayer.AccessDeniedError:
            error_msg = "访问被拒绝，无法访问媒体"
        elif error == QMediaPlayer.ServiceMissingError:
            error_msg = "服务缺失，尝试使用系统默认播放器"
            # 尝试使用系统默认播放器作为备用方案
            self._try_system_player()
            return
        
        self.playback_error.emit(f"播放错误: {error_msg}")
    
    def _try_system_player(self):
        """尝试使用系统默认播放器播放音频文件"""
        if self.current_file and os.path.exists(self.current_file):
            try:
                import subprocess
                import platform
                
                system = platform.system()
                if system == "Windows":
                    # Windows系统使用start命令
                    subprocess.Popen(["start", "", self.current_file], shell=True)
                elif system == "Darwin":  # macOS
                    subprocess.Popen(["open", self.current_file])
                elif system == "Linux":
                    subprocess.Popen(["xdg-open", self.current_file])
                
                # 发送播放开始信号
                self.playback_started.emit()
                # 模拟播放完成（因为无法监控外部播放器状态）
                import threading
                def delayed_finish():
                    import time
                    time.sleep(2)  # 等待2秒后发送完成信号
                    self.playback_stopped.emit()
                
                threading.Thread(target=delayed_finish, daemon=True).start()
                
            except Exception as e:
                self.playback_error.emit(f"系统播放器启动失败: {str(e)}")


if __name__ == "__main__":
    # 简单测试
    import sys
    import time
    from PyQt5.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    
    def on_started():
        print("播放开始")
    
    def on_stopped():
        print("播放结束")
        app.quit()
    
    def on_error(error_msg):
        print(f"错误: {error_msg}")
        app.quit()
    
    def on_position(position):
        print(f"\r播放位置: {position/1000:.1f}秒", end="")
    
    def on_duration(duration):
        print(f"音频时长: {duration/1000:.1f}秒")
    
    player = AudioPlayer()
    player.playback_started.connect(on_started)
    player.playback_stopped.connect(on_stopped)
    player.playback_error.connect(on_error)
    player.playback_position.connect(on_position)
    player.playback_duration.connect(on_duration)
    
    # 测试播放
    # 请替换为实际存在的音频文件路径
    test_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "audio", "test.mp3")
    if os.path.exists(test_file):
        player.play(test_file)
        # 等待播放完成
        app.exec_()
    else:
        print(f"测试文件不存在: {test_file}")
        print("请先运行tts_client.py生成测试音频文件")