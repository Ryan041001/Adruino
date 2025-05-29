#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
百度语音API调用示例
包含语音识别(ASR)和语音合成(TTS)功能

使用前需要:
1. 在百度AI开放平台申请应用: https://ai.baidu.com/
2. 获取API Key和Secret Key
3. 安装依赖: pip install baidu-aip pyaudio
"""

import os
import json
import time
import wave
import pyaudio
from aip import AipSpeech
from typing import Optional, Dict, Any

class BaiduSpeechAPI:
    def __init__(self, app_id: str, api_key: str, secret_key: str):
        """
        初始化百度语音API客户端
        
        Args:
            app_id: 百度应用ID
            api_key: 百度API Key
            secret_key: 百度Secret Key
        """
        self.app_id = app_id
        self.api_key = api_key
        self.secret_key = secret_key
        
        # 初始化百度语音客户端
        self.client = AipSpeech(app_id, api_key, secret_key)
        
        # 音频录制参数
        self.chunk = 1024
        self.format = pyaudio.paInt16
        self.channels = 1
        self.rate = 16000
        self.record_seconds = 5
        
        # 初始化PyAudio
        self.audio = pyaudio.PyAudio()
        
        print("百度语音API初始化完成")
    
    def record_audio(self, duration: int = 5, filename: str = "temp_audio.wav") -> str:
        """
        录制音频文件
        
        Args:
            duration: 录制时长（秒）
            filename: 保存的文件名
            
        Returns:
            录制的音频文件路径
        """
        print(f"开始录音，录制{duration}秒...")
        
        stream = self.audio.open(
            format=self.format,
            channels=self.channels,
            rate=self.rate,
            input=True,
            frames_per_buffer=self.chunk
        )
        
        frames = []
        
        for i in range(0, int(self.rate / self.chunk * duration)):
            data = stream.read(self.chunk)
            frames.append(data)
        
        stream.stop_stream()
        stream.close()
        
        # 保存音频文件
        wf = wave.open(filename, 'wb')
        wf.setnchannels(self.channels)
        wf.setsampwidth(self.audio.get_sample_size(self.format))
        wf.setframerate(self.rate)
        wf.writeframes(b''.join(frames))
        wf.close()
        
        print(f"录音完成，保存为: {filename}")
        return filename
    
    def speech_to_text(self, audio_file: str, options: Dict[str, Any] = None) -> Optional[str]:
        """
        语音识别 - 将音频转换为文字
        
        Args:
            audio_file: 音频文件路径
            options: 识别选项
            
        Returns:
            识别的文字结果
        """
        if options is None:
            options = {
                'dev_pid': 1537,  # 1537表示识别普通话，使用输入法模型
                'cuid': 'python_client',
            }
        
        try:
            # 读取音频文件
            with open(audio_file, 'rb') as fp:
                audio_data = fp.read()
            
            print("正在进行语音识别...")
            
            # 调用百度语音识别API
            result = self.client.asr(
                audio_data, 
                'wav', 
                self.rate, 
                options
            )
            
            if result.get('err_no') == 0:
                text = ''.join(result.get('result', []))
                print(f"识别结果: {text}")
                return text
            else:
                print(f"识别失败: {result.get('err_msg', '未知错误')}")
                return None
                
        except Exception as e:
            print(f"语音识别异常: {e}")
            return None

    
    def play_audio(self, filename: str):
        """
        播放音频文件（简单实现）
        
        Args:
            filename: 音频文件路径
        """
        try:
            import pygame
            pygame.mixer.init()
            pygame.mixer.music.load(filename)
            pygame.mixer.music.play()
            
            # 等待播放完成
            while pygame.mixer.music.get_busy():
                time.sleep(0.1)
                
        except ImportError:
            print("请安装pygame库来播放音频: pip install pygame")
            print(f"音频文件已保存为: {filename}")
        except Exception as e:
            print(f"播放音频失败: {e}")
    
    def interactive_demo(self):
        """
        交互式演示
        """
        print("\n=== 百度语音API交互式演示 ===")
        print("1. 语音识别 - 按回车开始录音")
        print("2. 输入 'quit' 退出程序")
        
        while True:
            print("\n请选择功能:")
            print("1 - 语音识别")
            print("quit - 退出")
            
            choice = input("请输入选择: ").strip()
            
            if choice.lower() == 'quit':
                print("程序退出")
                break
            elif choice == '1':
                self.demo_speech_recognition()
            else:
                print("无效选择，请重新输入")
    
    def demo_speech_recognition(self):
        """
        演示语音识别功能
        """
        print("\n=== 语音识别演示 ===")
        input("按回车键开始录音...")
        
        # 录制音频
        audio_file = self.record_audio(duration=5)
        
        # 进行语音识别
        result = self.speech_to_text(audio_file)
        
        if result:
            print(f"\n识别成功: {result}")

        else:
            print("识别失败")
        
        # 清理临时文件
        if os.path.exists(audio_file):
            os.remove(audio_file)

    
    def __del__(self):
        """
        析构函数，清理资源
        """
        if hasattr(self, 'audio'):
            self.audio.terminate()

def load_config(config_file: str = "baidu_config.json") -> Dict[str, str]:
    """
    从配置文件加载百度API配置
    
    Args:
        config_file: 配置文件路径
        
    Returns:
        配置字典
    """
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        return config
    except FileNotFoundError:
        print(f"配置文件 {config_file} 不存在")
        return create_config_template(config_file)
    except Exception as e:
        print(f"读取配置文件失败: {e}")
        return {}

def create_config_template(config_file: str = "baidu_config.json") -> Dict[str, str]:
    """
    创建配置文件模板
    
    Args:
        config_file: 配置文件路径
        
    Returns:
        空配置字典
    """
    template = {
        "app_id": "your_app_id_here",
        "api_key": "your_api_key_here",
        "secret_key": "your_secret_key_here"
    }
    
    try:
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(template, f, indent=4, ensure_ascii=False)
        print(f"已创建配置文件模板: {config_file}")
        print("请填入您的百度API密钥后重新运行程序")
    except Exception as e:
        print(f"创建配置文件失败: {e}")
    
    return {}

def main():
    """
    主函数
    """
    print("百度语音API调用示例")
    print("=" * 50)
    
    # 加载配置
    config = load_config()
    
    if not all(key in config for key in ['app_id', 'api_key', 'secret_key']):
        print("配置文件不完整，请检查 baidu_config.json")
        return
    
    if any(value.startswith('your_') for value in config.values()):
        print("请先在 baidu_config.json 中填入正确的API密钥")
        return
    
    try:
        # 初始化百度语音API
        baidu_speech = BaiduSpeechAPI(
            config['app_id'],
            config['api_key'],
            config['secret_key']
        )
        
        # 开始交互式演示
        baidu_speech.interactive_demo()
        
    except Exception as e:
        print(f"程序运行异常: {e}")
        print("请检查网络连接和API密钥是否正确")

if __name__ == "__main__":
    main()