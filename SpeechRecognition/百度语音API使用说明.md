# 百度语音API使用说明

## 概述

本项目集成了百度语音API，提供语音识别(ASR)和语音合成(TTS)功能。

## 准备工作

### 1. 申请百度AI开放平台账号

1. 访问 [百度AI开放平台](https://ai.baidu.com/)
2. 注册并登录账号
3. 创建应用，选择"语音技术"
4. 获取以下信息：
   - App ID
   - API Key
   - Secret Key

### 2. 配置API密钥

编辑 `baidu_config.json` 文件，填入您的API信息：

```json
{
    "app_id": "您的App ID",
    "api_key": "您的API Key",
    "secret_key": "您的Secret Key"
}
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

## 功能特性

### 语音识别 (ASR)
- 支持中文普通话识别
- 录音时长可配置（默认5秒）
- 支持多种识别模式
- 实时反馈识别结果

## 使用方法

### 运行演示程序

```bash
python baidu_speech_demo.py
```

### 程序功能

1. **语音识别演示**
   - 选择选项 "1"
   - 按回车开始录音
   - 程序会录制5秒音频并进行识别
   - 可选择将识别结果进行语音合成

3. **退出程序**
   - 输入 "quit" 退出

## API参数说明

### 语音识别参数

- `dev_pid`: 识别模型
  - 1537: 普通话(支持简单的英文识别)
  - 1737: 英语
  - 1637: 粤语
  - 1837: 四川话

## 代码示例

### 基本使用

```python
from baidu_speech_demo import BaiduSpeechAPI

# 初始化API
baidu_speech = BaiduSpeechAPI(app_id, api_key, secret_key)

# 语音识别
audio_file = baidu_speech.record_audio(duration=5)
text = baidu_speech.speech_to_text(audio_file)
print(f"识别结果: {text}")
```

### 自定义参数

```python
# 语音识别选项
asr_options = {
    'dev_pid': 1537,  # 普通话识别
    'cuid': 'python_client',
}
```

## 注意事项

1. **网络连接**: 百度语音API需要网络连接
2. **音频格式**: 录音使用WAV格式，16kHz采样率
3. **文件大小**: 语音识别支持的音频文件不超过60秒
4. **API配额**: 注意百度API的调用次数限制
5. **麦克风权限**: 确保程序有麦克风访问权限

## 故障排除

### 常见问题

1. **"配置文件不完整"**
   - 检查 `baidu_config.json` 是否存在
   - 确认API密钥已正确填入

2. **"无法录音"**
   - 检查麦克风是否连接
   - 确认麦克风权限
   - 尝试重启程序

3. **"识别失败"**
   - 检查网络连接
   - 确认API密钥有效
   - 尝试重新录音

4. **"无法播放音频"**
   - 安装pygame库: `pip install pygame`
   - 检查音频设备

### 错误代码

- `3300`: 输入参数不正确
- `3301`: 音频质量过差
- `3302`: 鉴权失败
- `3303`: 语音服务器后端问题
- `3304`: 用户的请求QPS超限
- `3305`: 用户的日pv（日请求量）超限

## 扩展功能

可以基于现有代码扩展以下功能：

1. **批量处理**: 批量处理音频文件
2. **实时识别**: 实现流式语音识别
3. **语音命令**: 添加语音命令识别
4. **多语言支持**: 支持其他语言识别
5. **音频预处理**: 添加降噪、音量调节等功能

## 相关链接

- [百度AI开放平台](https://ai.baidu.com/)
- [百度语音识别API文档](https://ai.baidu.com/ai-doc/SPEECH/Vk38lxily)
- [百度语音合成API文档](https://ai.baidu.com/ai-doc/SPEECH/Tk38y8lzk)
- [Python SDK文档](https://ai.baidu.com/ai-doc/REFERENCE/Ck3dwjhhu)