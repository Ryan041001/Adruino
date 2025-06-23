# -*- coding: utf-8 -*-
"""
配置文件 - 存储系统配置信息
"""

import os

# =============================================================================
# API 配置
# =============================================================================

# DeepSeek API 配置 (用于大语言模型)
DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY')
DEEPSEEK_MODEL = 'deepseek-chat'
DEEPSEEK_BASE_URL = 'https://api.deepseek.com/v1'

# 百度语音API配置 (用于语音识别)
BAIDU_APP_ID = os.getenv('BAIDU_APP_ID')
BAIDU_API_KEY = os.getenv('BAIDU_API_KEY')
BAIDU_SECRET_KEY = os.getenv('BAIDU_SECRET_KEY')

# 科大讯飞语音合成API配置
XUNFEI_APP_ID = os.getenv('XUNFEI_APP_ID')
XUNFEI_API_KEY = os.getenv('XUNFEI_API_KEY')
XUNFEI_API_SECRET = os.getenv('XUNFEI_API_SECRET')

# 检查环境变量是否设置
_required_env_vars = [
    'DEEPSEEK_API_KEY',
    'BAIDU_APP_ID',
    'BAIDU_API_KEY',
    'BAIDU_SECRET_KEY',
    'XUNFEI_APP_ID',
    'XUNFEI_API_KEY',
    'XUNFEI_API_SECRET'
]

for var in _required_env_vars:
    if not globals().get(var):
        raise ValueError(f"错误：环境变量 {var} 未设置。请在 .env 文件中或直接在系统中设置。")

# =============================================================================
# GUI配置
# =============================================================================

# 主窗口配置 - 适配树莓派3B小屏幕(320*480)
GUI_CONFIG = {
    'WINDOW_WIDTH': 480,
    'WINDOW_HEIGHT': 320,
    'WINDOW_TITLE': '语音备忘录',
    'FONT_SIZE': 10,
    'LARGE_FONT_SIZE': 12
}

# 按钮配置
BUTTON_CONFIG = {
    'RECORD_BUTTON_TEXT': '开始录音',
    'STOP_BUTTON_TEXT': '停止录音',
    'CLEAR_BUTTON_TEXT': '清除提醒'
}

# 音频配置
AUDIO_CONFIG = {
    'SAMPLE_RATE': 16000,
    'CHUNK_SIZE': 1024,
    'CHANNELS': 1,
    'FORMAT': 'int16',
    'RECORD_TIMEOUT': 5,  # 录音超时时间(秒)
    'PHRASE_TIMEOUT': 1   # 短语超时时间(秒)
}

# =============================================================================
# Web服务配置
# =============================================================================

WEB_CONFIG = {
    'HOST': '0.0.0.0',
    'PORT': 5000,
    'DEBUG': False
}

# =============================================================================
# 语音合成配置
# =============================================================================

TTS_CONFIG = {
    'ENGINE': 'xunfei',   # 使用科大讯飞语音合成
    'LANGUAGE': 'zh',
    'SPEED': 50,          # 语速 (0-100)
    'PITCH': 50,          # 音调 (0-100)
    'VOLUME': 50,         # 音量 (0-100)
    'VOICE': 'xiaoyan'    # 发音人 (xiaoyan-小燕, aisjiuxu-爱思久, aisxping-爱思萍等)
}

# =============================================================================
# 系统配置
# =============================================================================

# 日志配置
LOG_CONFIG = {
    'LEVEL': 'INFO',
    'FORMAT': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'FILE': 'logs/system.log'
}

# 提醒配置
REMINDER_CONFIG = {
    'MAX_REMINDERS': 20,   # 最大提醒数量 - 支持更多同时运行的提醒
    'DEFAULT_SNOOZE': 5,   # 默认延迟时间(分钟)
    'SOUND_FILE': 'assets/alarm.wav',  # 提醒音效文件
    'CONCURRENT_REMINDERS': True,  # 启用多个提醒同时运行
    'UPDATE_INTERVAL': 1,  # 倒计时更新间隔(秒)
    'URGENT_THRESHOLD': 300,  # 紧急提醒阈值(秒) - 5分钟内的提醒会高亮显示
    'CRITICAL_THRESHOLD': 60  # 关键提醒阈值(秒) - 1分钟内的提醒会特别标记
}

# 显示配置
DISPLAY_CONFIG = {
    'FONT_SIZE': 12,
    'SCROLL_SPEED': 2,     # 滚动速度
    'UPDATE_INTERVAL': 1   # 更新间隔(秒)
}

# =============================================================================
# 文件路径配置
# =============================================================================

PATHS = {
    'ASSETS': 'assets/',
    'LOGS': 'logs/',
    'TEMP': 'temp/',
    'AUDIO_TEMP': 'temp/audio/'
}

# 确保目录存在
for path in PATHS.values():
    os.makedirs(path, exist_ok=True)