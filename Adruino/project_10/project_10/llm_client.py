#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
大语言模型客户端模块

包含DeepSeek客户端实现
"""

import json
import requests
from enum import Enum
from PyQt5.QtCore import QObject, pyqtSignal

from config import DEEPSEEK_API_KEY


class LLMType(Enum):
    """大语言模型类型"""
    DEEPSEEK = "DeepSeek"  # DeepSeek


class LLMClient(QObject):
    """大语言模型客户端基类"""
    
    # 定义信号
    response_received = pyqtSignal(str)  # 响应接收信号，参数为响应文本
    response_error = pyqtSignal(str)     # 响应错误信号，参数为错误信息
    response_chunk = pyqtSignal(str)     # 流式响应块信号，参数为响应块文本
    
    def __init__(self, parent=None):
        super().__init__(parent)
    
    def query(self, text, stream=True):
        """查询大语言模型
        
        Args:
            text: 查询文本
            stream: 是否使用流式响应
            
        Returns:
            str: 响应文本
        """
        raise NotImplementedError("子类必须实现此方法")


class DeepSeekClient(LLMClient):
    """DeepSeek客户端"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.api_key = DEEPSEEK_API_KEY
    
    def query(self, text, stream=True):
        """查询DeepSeek
        
        Args:
            text: 查询文本
            stream: 是否使用流式响应
            
        Returns:
            str: 响应文本
        """
        # 检查API密钥是否已设置
        if not self.api_key:
            error_msg = "DeepSeek API密钥未设置，请在config.py中设置"
            self.response_error.emit(error_msg)
            return None
        
        # 构建请求URL
        url = "https://api.deepseek.com/v1/chat/completions"
        
        # 构建请求体
        payload = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "user", "content": text}
            ],
            "stream": stream,
            "temperature": 0.7,
            "top_p": 0.9
        }
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        try:
            if stream:
                # 流式响应
                full_response = ""
                response = requests.post(url, headers=headers, json=payload, stream=True)
                
                for line in response.iter_lines():
                    if line:
                        line = line.decode('utf-8')
                        if line.startswith("data: "):
                            data = line[6:]  # 去掉 "data: " 前缀
                            if data == "[DONE]":
                                break
                            
                            try:
                                result = json.loads(data)
                                if "choices" in result and result["choices"]:
                                    delta = result["choices"][0].get("delta", {})
                                    content = delta.get("content", "")
                                    if content:
                                        full_response += content
                                        self.response_chunk.emit(content)
                            except json.JSONDecodeError:
                                pass
                
                self.response_received.emit(full_response)
                return full_response
            else:
                # 非流式响应
                response = requests.post(url, headers=headers, json=payload)
                result = response.json()
                
                if "choices" in result and result["choices"]:
                    content = result["choices"][0].get("message", {}).get("content", "")
                    self.response_received.emit(content)
                    return content
                else:
                    error_msg = f"查询失败: {result.get('error', {}).get('message', '未知错误')}"
                    self.response_error.emit(error_msg)
                    return None
                    
        except Exception as e:
            error_msg = f"查询异常: {str(e)}"
            self.response_error.emit(error_msg)
            return None


class LLMFactory:
    """大语言模型工厂"""
    
    @staticmethod
    def create_client(llm_type, parent=None):
        """创建大语言模型客户端
        
        Args:
            llm_type: 大语言模型类型
            parent: 父对象
            
        Returns:
            LLMClient: 大语言模型客户端
        """
        if llm_type == LLMType.DEEPSEEK:
            return DeepSeekClient(parent)
        else:
            raise ValueError(f"不支持的大语言模型类型: {llm_type}")


if __name__ == "__main__":
    # 简单测试
    import sys
    from PyQt5.QtCore import QCoreApplication
    
    app = QCoreApplication(sys.argv)
    
    def on_response(text):
        print(f"\n完整响应: {text}")
        app.quit()
    
    def on_error(error_msg):
        print(f"错误: {error_msg}")
        app.quit()
    
    def on_chunk(chunk):
        print(chunk, end="", flush=True)
    
    # 创建客户端
    client = LLMFactory.create_client(LLMType.DEEPSEEK)
    client.response_received.connect(on_response)
    client.response_error.connect(on_error)
    client.response_chunk.connect(on_chunk)
    
    # 测试查询
    print("正在查询，请稍候...")
    client.query("介绍一下人工智能的发展历史")
    
    sys.exit(app.exec_())