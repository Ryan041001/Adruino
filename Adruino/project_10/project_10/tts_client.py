#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
科大讯飞语音合成API客户端

使用科大讯飞的流式WebAPI实现文本到语音的转换
"""

import base64
import hashlib
import hmac
import json
import os
import time
import uuid
from datetime import datetime
from urllib.parse import urlencode
from wsgiref.handlers import format_date_time

import requests
import websocket
from PyQt5.QtCore import QObject, pyqtSignal

from config import (
    XFYUN_APP_ID,
    XFYUN_API_KEY,
    XFYUN_API_SECRET,
    DEFAULT_VOICE,
    DEFAULT_SPEED,
    DEFAULT_VOLUME,
    DEFAULT_PITCH
)


class TTSClient(QObject):
    """科大讯飞语音合成客户端"""
    
    # 定义信号
    tts_finished = pyqtSignal(str)  # 语音合成完成信号，参数为音频文件路径
    tts_error = pyqtSignal(str)     # 语音合成错误信号，参数为错误信息
    tts_progress = pyqtSignal(int)  # 语音合成进度信号，参数为进度百分比
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.host = "tts-api.xfyun.cn"
        self.path = "/v2/tts"
        self.app_id = XFYUN_APP_ID
        self.api_key = XFYUN_API_KEY
        self.api_secret = XFYUN_API_SECRET
        self.voice = DEFAULT_VOICE
        self.speed = DEFAULT_SPEED
        self.volume = DEFAULT_VOLUME
        self.pitch = DEFAULT_PITCH
        self.output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "audio")
        
        # 创建输出目录
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
    
    def _create_url(self):
        """生成鉴权URL"""
        # 生成RFC1123格式的时间戳
        now = datetime.now()
        date = format_date_time(time.mktime(now.timetuple()))
        
        # 拼接字符串
        signature_origin = f"host: {self.host}\ndate: {date}\nGET {self.path} HTTP/1.1"
        
        # 进行hmac-sha256加密
        signature_sha = hmac.new(
            self.api_secret.encode('utf-8'),
            signature_origin.encode('utf-8'),
            digestmod=hashlib.sha256
        ).digest()
        
        signature_sha_base64 = base64.b64encode(signature_sha).decode()
        authorization_origin = f'api_key="{self.api_key}", algorithm="hmac-sha256", headers="host date request-line", signature="{signature_sha_base64}"'
        
        authorization = base64.b64encode(authorization_origin.encode()).decode()
        
        # 将请求的鉴权参数组合为字典
        v = {
            "authorization": authorization,
            "date": date,
            "host": self.host
        }
        # 拼接鉴权参数，生成url
        url = f'wss://{self.host}{self.path}?{urlencode(v)}'
        return url
    
    def _create_audio_params(self, text):
        """生成语音合成参数"""
        business_params = {
            "aue": "lame",  # 音频编码，lame为MP3格式
            "sfl": 1,       # 是否开启流式返回
            "auf": "audio/L16;rate=16000",  # 音频采样率
            "vcn": str(self.voice),  # 发音人，确保是字符串
            "speed": int(self.speed),  # 语速，确保是整数类型
            "volume": int(self.volume),  # 音量，确保是整数类型
            "pitch": int(self.pitch),  # 音高，确保是整数类型
            "bgs": 0,  # 是否有背景音
            "tte": "utf8"  # 文本编码
        }
        
        data = {
            "common": {
                "app_id": self.app_id
            },
            "business": business_params,
            "data": {
                "text": base64.b64encode(text.encode()).decode(),
                "status": 2  # 2表示完整的text
            }
        }
        return json.dumps(data)
    
    def synthesize(self, text, voice=None, speed=None, volume=None, pitch=None):
        """合成语音
        
        Args:
            text: 要合成的文本
            voice: 发音人，默认为None，使用默认值
            speed: 语速，默认为None，使用默认值
            volume: 音量，默认为None，使用默认值
            pitch: 音高，默认为None，使用默认值
            
        Returns:
            str: 合成的音频文件路径
        """
        # 更新参数
        if voice:
            self.voice = voice
        if speed is not None:
            self.speed = speed
        if volume is not None:
            self.volume = volume
        if pitch is not None:
            self.pitch = pitch
        
        # 生成输出文件名
        output_file = os.path.join(self.output_dir, f"{uuid.uuid4()}.mp3")
        
        # 检查API密钥是否已设置
        if not self.app_id or not self.api_key or not self.api_secret:
            error_msg = "科大讯飞API密钥未设置，请在config.py中设置"
            self.tts_error.emit(error_msg)
            return None
        
        try:
            # 创建WebSocket连接
            ws_url = self._create_url()
            ws = websocket.create_connection(ws_url)
            
            # 发送合成请求
            audio_params = self._create_audio_params(text)
            ws.send(audio_params)
            
            # 接收合成结果
            audio_data = bytearray()
            response_count = 0
            total_frames = 1  # 假设至少有一帧
            
            while True:
                response = ws.recv()
                response_dict = json.loads(response)
                
                # 检查是否有错误
                if response_dict["code"] != 0:
                    error_msg = f"语音合成失败: {response_dict['message']}"
                    self.tts_error.emit(error_msg)
                    return None
                
                # 获取音频数据
                audio_frame = response_dict["data"]["audio"]
                status = response_dict["data"]["status"]
                
                # 解码音频数据并追加
                audio_data.extend(base64.b64decode(audio_frame))
                
                # 更新进度
                response_count += 1
                if "ced" in response_dict["data"] and int(response_dict["data"]["ced"]) > 0:
                    total_frames = int(response_dict["data"]["ced"])
                progress = min(100, int(response_count / total_frames * 100))
                self.tts_progress.emit(progress)
                
                # 判断是否结束
                if status == 2:
                    break
            
            # 关闭WebSocket连接
            ws.close()
            
            # 保存音频文件
            with open(output_file, "wb") as f:
                f.write(audio_data)
            
            # 发送完成信号
            self.tts_finished.emit(output_file)
            return output_file
            
        except Exception as e:
            error_msg = f"语音合成异常: {str(e)}"
            self.tts_error.emit(error_msg)
            return None
    
    def synthesize_http(self, text, voice=None, speed=None, volume=None, pitch=None):
        """使用HTTP接口合成语音（备用方法）
        
        Args:
            text: 要合成的文本
            voice: 发音人，默认为None，使用默认值
            speed: 语速，默认为None，使用默认值
            volume: 音量，默认为None，使用默认值
            pitch: 音高，默认为None，使用默认值
            
        Returns:
            str: 合成的音频文件路径
        """
        # 更新参数
        if voice:
            self.voice = voice
        if speed is not None:
            self.speed = speed
        if volume is not None:
            self.volume = volume
        if pitch is not None:
            self.pitch = pitch
        
        # 生成输出文件名
        output_file = os.path.join(self.output_dir, f"{uuid.uuid4()}.mp3")
        
        # 检查API密钥是否已设置
        if not self.app_id or not self.api_key or not self.api_secret:
            error_msg = "科大讯飞API密钥未设置，请在config.py中设置"
            self.tts_error.emit(error_msg)
            return None
        
        try:
            # 构建请求URL
            url = f"https://{self.host}{self.path}"
            
            # 构建请求头
            now = datetime.now()
            date = format_date_time(time.mktime(now.timetuple()))
            signature_origin = f"host: {self.host}\ndate: {date}\nPOST {self.path} HTTP/1.1"
            signature_sha = hmac.new(
                self.api_secret.encode('utf-8'),
                signature_origin.encode('utf-8'),
                digestmod=hashlib.sha256
            ).digest()
            signature_sha_base64 = base64.b64encode(signature_sha).decode()
            authorization_origin = f'api_key="{self.api_key}", algorithm="hmac-sha256", headers="host date request-line", signature="{signature_sha_base64}"'
            authorization = base64.b64encode(authorization_origin.encode()).decode()
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": authorization,
                "Date": date,
                "Host": self.host
            }
            
            # 构建请求体
            business_params = {
                "aue": "lame",  # 音频编码，lame为MP3格式
                "auf": "audio/L16;rate=16000",  # 音频采样率
                "vcn": self.voice,  # 发音人
                "speed": self.speed,  # 语速
                "volume": self.volume,  # 音量
                "pitch": self.pitch,  # 音高
                "bgs": 0,  # 是否有背景音
                "tte": "utf8"  # 文本编码
            }
            
            data = {
                "common": {
                    "app_id": self.app_id
                },
                "business": business_params,
                "data": {
                    "text": base64.b64encode(text.encode()).decode()
                }
            }
            
            # 发送请求
            self.tts_progress.emit(10)  # 发送请求前
            response = requests.post(url, headers=headers, data=json.dumps(data))
            self.tts_progress.emit(50)  # 请求已发送
            
            # 检查响应
            if response.status_code != 200:
                error_msg = f"HTTP请求失败: {response.status_code} {response.text}"
                self.tts_error.emit(error_msg)
                return None
            
            response_dict = response.json()
            if response_dict["code"] != 0:
                error_msg = f"语音合成失败: {response_dict['message']}"
                self.tts_error.emit(error_msg)
                return None
            
            # 解码音频数据
            audio_data = base64.b64decode(response_dict["data"]["audio"])
            self.tts_progress.emit(80)  # 数据已接收
            
            # 保存音频文件
            with open(output_file, "wb") as f:
                f.write(audio_data)
            
            # 发送完成信号
            self.tts_progress.emit(100)  # 处理完成
            self.tts_finished.emit(output_file)
            return output_file
            
        except Exception as e:
            error_msg = f"语音合成异常: {str(e)}"
            self.tts_error.emit(error_msg)
            return None


if __name__ == "__main__":
    # 简单测试
    import sys
    from PyQt5.QtCore import QCoreApplication
    
    app = QCoreApplication(sys.argv)
    
    def on_finished(file_path):
        print(f"语音合成完成: {file_path}")
        app.quit()
    
    def on_error(error_msg):
        print(f"错误: {error_msg}")
        app.quit()
    
    def on_progress(progress):
        print(f"进度: {progress}%")
    
    client = TTSClient()
    client.tts_finished.connect(on_finished)
    client.tts_error.connect(on_error)
    client.tts_progress.connect(on_progress)
    
    # 测试合成
    client.synthesize("这是一个科大讯飞语音合成的测试。")
    
    sys.exit(app.exec_())