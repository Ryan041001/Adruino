#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
智能语音交互系统配置文件

存储API密钥和其他配置信息
"""



# DeepSeek API配置
DEEPSEEK_API_KEY = "sk-5057828224a04601ac2855887cc6b884"  # 填写实际的API Key

# 科大讯飞API配置
XFYUN_APP_ID = "5bcccdfd"  # 填写实际的APPID
XFYUN_API_KEY = "15842e8af66b701b55e948d19e312793"  # 填写实际的APIKey
XFYUN_API_SECRET = "MzBhNmQ1NDg3Y2JhMWEwNmY4OWU5ZTU0"  # 填写实际的APISecret

# 百度语音识别API配置
BAIDU_APP_ID = "119073268"  # 填写实际的APP ID（当前为测试值）
BAIDU_API_KEY = "F4gOVwNnhziOBHyydSCm4MwR"  # 填写实际的API Key（当前为测试值）
BAIDU_SECRET_KEY = "NpftMIkT6oczhEruxwER2pawnXbQh2O8"  # 填写实际的Secret Key（当前为测试值）

# 语音合成配置
DEFAULT_VOICE = "xiaoyan"  # 默认发音人
DEFAULT_SPEED = 50  # 默认语速
DEFAULT_VOLUME = 77  # 默认音量
DEFAULT_PITCH = 50  # 默认音高

# 语音识别配置
SPEECH_RECOGNITION_LANGUAGE = "zh-CN"  # 语音识别语言

# 预设问题
PRESET_QUESTIONS = [
    "杭州今日天气", 
    "推荐一些旅游景点", 
    "介绍一下人工智能的发展",
    "如何保持健康的生活方式",
    "中国的传统节日有哪些"
]

# 界面配置
WINDOW_TITLE = "智能语音交互系统"
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600