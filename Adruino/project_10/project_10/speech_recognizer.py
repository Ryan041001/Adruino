#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
语音识别模块

使用百度语音识别API实现语音输入功能，支持从麦克风录音和从音频文件输入
"""

import os
import tempfile
import threading
import uuid
import wave
import base64
import requests
from datetime import datetime

import pyaudio
from aip import AipSpeech
from PyQt5.QtCore import QObject, pyqtSignal

from config import (
    SPEECH_RECOGNITION_LANGUAGE,
    BAIDU_APP_ID,
    BAIDU_API_KEY,
    BAIDU_SECRET_KEY
)


class SpeechRecognizer(QObject):
    """语音识别器"""
    
    # 定义信号
    recognition_result = pyqtSignal(str)  # 识别结果信号，参数为识别文本
    recognition_error = pyqtSignal(str)   # 识别错误信号，参数为错误信息
    recording_started = pyqtSignal()      # 录音开始信号
    recording_stopped = pyqtSignal()      # 录音结束信号
    recording_level = pyqtSignal(float)   # 录音电平信号，参数为电平值（0.0-1.0）
    
    def __init__(self, parent=None):
        super().__init__(parent)
        # 初始化百度语音识别客户端
        self.client = AipSpeech(BAIDU_APP_ID, BAIDU_API_KEY, BAIDU_SECRET_KEY)
        self.language = SPEECH_RECOGNITION_LANGUAGE
        self.recording = False
        self.recording_thread = None
        self.audio_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "audio")
        
        # 创建音频目录
        if not os.path.exists(self.audio_dir):
            os.makedirs(self.audio_dir)
        
        # 录音参数
        self.format = pyaudio.paInt16  # 16位深度
        self.channels = 1              # 单声道
        self.rate = 16000              # 采样率16kHz
        self.chunk = 1024              # 每次读取的帧数
        self.audio = pyaudio.PyAudio() # 创建PyAudio对象
        
        # 获取access_token
        self._get_access_token()
    
    def recognize_from_microphone(self, duration=5):
        """从麦克风识别语音
        
        Args:
            duration: 录音时长，单位为秒
            
        Returns:
            bool: 是否成功启动录音
        """
        if self.recording:
            self.recognition_error.emit("正在录音中，请等待当前录音完成")
            return False
        
        # 启动录音线程
        self.recording_thread = threading.Thread(
            target=self._record_and_recognize,
            args=(duration,)
        )
        self.recording_thread.daemon = True
        self.recording_thread.start()
        return True
    
    def _record_and_recognize(self, duration):
        """录音并识别
        
        Args:
            duration: 录音时长，单位为秒
        """
        self.recording = True
        self.recording_started.emit()
        
        try:
            # 打开音频流
            stream = self.audio.open(
                format=self.format,
                channels=self.channels,
                rate=self.rate,
                input=True,
                frames_per_buffer=self.chunk
            )
            
            # 录音
            frames = []
            for i in range(0, int(self.rate / self.chunk * duration)):
                if not self.recording:
                    break
                data = stream.read(self.chunk)
                frames.append(data)
                
                # 发送电平信号（简单实现，实际应该计算音频振幅）
                level = min(1.0, sum(abs(int.from_bytes(data[i:i+2], byteorder='little', signed=True)) 
                                for i in range(0, len(data), 2)) / (32767.0 * self.chunk))
                self.recording_level.emit(level)
            
            # 停止录音
            stream.stop_stream()
            stream.close()
            
            # 保存音频文件
            audio_file = os.path.join(self.audio_dir, f"{uuid.uuid4()}.wav")
            with wave.open(audio_file, 'wb') as wf:
                wf.setnchannels(self.channels)
                wf.setsampwidth(self.audio.get_sample_size(self.format))
                wf.setframerate(self.rate)
                wf.writeframes(b''.join(frames))
            
            # 识别
            self._recognize_audio(audio_file)
                
        except Exception as e:
            self.recognition_error.emit(f"录音异常: {str(e)}")
        finally:
            self.recording = False
            self.recording_stopped.emit()
    
    def recognize_from_file(self, file_path):
        """从文件识别语音
        
        Args:
            file_path: 音频文件路径
            
        Returns:
            bool: 是否成功启动识别
        """
        if not os.path.exists(file_path):
            self.recognition_error.emit(f"文件不存在: {file_path}")
            return False
        
        # 启动识别线程
        threading.Thread(
            target=self._recognize_from_file,
            args=(file_path,)
        ).start()
        return True
    
    def _recognize_from_file(self, file_path):
        """从文件识别语音
        
        Args:
            file_path: 音频文件路径
        """
        try:
            # 检查文件格式，如果不是wav格式，需要转换
            if not file_path.lower().endswith('.wav'):
                self.recognition_error.emit(f"目前仅支持WAV格式音频文件")
                return
            
            # 识别
            self._recognize_audio(file_path)
            
        except Exception as e:
            self.recognition_error.emit(f"文件识别异常: {str(e)}")
    
    def _get_access_token(self):
        """获取百度语音识别API的access_token"""
        # 初始化access_token属性，防止获取失败时出现属性不存在的错误
        self.access_token = ""
        
        try:
            # 打印API凭证，用于调试
            print(f"APP_ID: {BAIDU_APP_ID}")
            print(f"API_KEY: {BAIDU_API_KEY}")
            print(f"SECRET_KEY: {BAIDU_SECRET_KEY}")
            
            # 构建获取token的URL
            token_url = f"https://openapi.baidu.com/oauth/2.0/token?grant_type=client_credentials&client_id={BAIDU_API_KEY}&client_secret={BAIDU_SECRET_KEY}"
            print(f"Token URL: {token_url}")
            
            # 发送请求获取token
            response = requests.get(token_url)
            print(f"Response status code: {response.status_code}")
            response_json = response.json()
            print(f"Response JSON: {response_json}")
            
            if 'access_token' in response_json:
                self.access_token = response_json['access_token']
                print(f"获取access_token成功: {self.access_token}")
                return True
            else:
                print(f"获取access_token失败: {response_json}")
                return False
        except Exception as e:
            print(f"获取access_token异常: {str(e)}")
            return False
    
    def _recognize_audio(self, audio_file):
        """识别音频文件
        
        Args:
            audio_file: 音频文件路径
        """
        try:
            # 每次识别前重新获取access_token
            self._get_access_token()
            
            print(f"当前access_token: {self.access_token}")
            
            # 读取音频文件
            with open(audio_file, 'rb') as f:
                audio_data = f.read()
            
            print(f"音频文件大小: {len(audio_data)} 字节")
            
            # 使用百度语音识别API识别
            # 设置识别参数
            dev_pid = 1537  # 普通话(有标点)，使用1536表示普通话(无标点)
            
            # 根据语言设置不同的模型
            if self.language == 'en-US':
                dev_pid = 1737  # 英语模型
            elif self.language == 'zh-HK' or self.language == 'zh-TW':
                dev_pid = 1637  # 粤语模型
            
            print(f"使用的语音识别模型: {dev_pid}")
            
            # 将音频数据进行base64编码
            speech = base64.b64encode(audio_data).decode('utf-8')
            
            # 构建请求数据
            data = {
                'format': 'wav',
                'rate': self.rate,
                'channel': self.channels,
                'cuid': 'python_demo',
                'token': self.access_token,
                'speech': speech,
                'len': len(audio_data),
                'dev_pid': dev_pid
            }
            
            print(f"请求数据: {data}")
            
            # 发送请求
            headers = {'Content-Type': 'application/json'}
            url = 'https://vop.baidu.com/server_api'
            print(f"发送请求到: {url}")
            response = requests.post(url, json=data, headers=headers)
            print(f"响应状态码: {response.status_code}")
            result = response.json()
            print(f"响应结果: {result}")
            
            # 处理识别结果
            if result['err_no'] == 0 and 'result' in result and result['result']:
                text = result['result'][0]
                print(f"识别成功: {text}")
                self.recognition_result.emit(text)
            else:
                error_msg = f"识别失败: {result.get('err_msg', '未知错误')}"
                print(f"识别失败: {error_msg}")
                self.recognition_error.emit(error_msg)
            
        except Exception as e:
            print(f"识别异常: {str(e)}")
            self.recognition_error.emit(f"识别异常: {str(e)}")
    
    def stop_recording(self):
        """停止录音"""
        self.recording = False
    
    def set_language(self, language):
        """设置识别语言
        
        Args:
            language: 语言代码，如zh-CN、en-US等
        """
        self.language = language
        
    def __del__(self):
        """析构函数，释放资源"""
        if hasattr(self, 'audio') and self.audio:
            self.audio.terminate()


if __name__ == "__main__":
    # 简单测试
    import sys
    import time
    from PyQt5.QtCore import QCoreApplication
    
    app = QCoreApplication(sys.argv)
    
    def on_result(text):
        print(f"识别结果: {text}")
        app.quit()
    
    def on_error(error_msg):
        print(f"错误: {error_msg}")
        app.quit()
    
    def on_recording_started():
        print("录音开始...")
    
    def on_recording_stopped():
        print("录音结束")
    
    def on_recording_level(level):
        # 简单的音量显示
        bars = int(level * 20)
        print(f"音量: {'|' * bars}{' ' * (20 - bars)} {level:.2f}")
    
    recognizer = SpeechRecognizer()
    recognizer.recognition_result.connect(on_result)
    recognizer.recognition_error.connect(on_error)
    recognizer.recording_started.connect(on_recording_started)
    recognizer.recording_stopped.connect(on_recording_stopped)
    recognizer.recording_level.connect(on_recording_level)
    
    # 测试麦克风识别
    print("请对着麦克风说话...")
    recognizer.recognize_from_microphone(duration=5)
    
    # 等待识别完成
    time.sleep(7)
    
    sys.exit(app.exec_())