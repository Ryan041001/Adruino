'''
从音频文件识别语音

这个脚本展示了如何使用SpeechRecognition库从音频文件中识别语音。
支持的文件格式包括WAV, AIFF, AIFF-C, FLAC (需要安装原生FLAC编码器)。
'''

import speech_recognition as sr
import os

def recognize_from_file(file_path, language="zh-CN"):
    """
    从音频文件识别语音
    
    参数:
        file_path: 音频文件路径
        language: 识别语言 (默认为中文)
    
    返回: 包含以下键的字典:
        "success": 布尔值，表示操作是否成功
        "error":   None或错误信息字符串
        "transcription": None或识别的文本字符串
    """
    # 创建Recognizer实例
    recognizer = sr.Recognizer()
    
    # 设置响应对象
    response = {
        "success": True,
        "error": None,
        "transcription": None
    }
    
    # 检查文件是否存在
    if not os.path.isfile(file_path):
        response["success"] = False
        response["error"] = f"文件不存在: {file_path}"
        return response
    
    # 检查文件扩展名
    file_ext = os.path.splitext(file_path)[1].lower()
    supported_formats = [".wav", ".aiff", ".aif", ".flac"]
    
    if file_ext not in supported_formats:
        response["success"] = False
        response["error"] = f"不支持的文件格式: {file_ext}. 支持的格式: {', '.join(supported_formats)}"
        return response
    
    # 从文件加载音频
    try:
        with sr.AudioFile(file_path) as source:
            # 获取音频数据
            audio_data = recognizer.record(source)
    except Exception as e:
        response["success"] = False
        response["error"] = f"读取音频文件时出错: {str(e)}"
        return response
    
    # 尝试识别语音
    try:
        response["transcription"] = recognizer.recognize_google(audio_data, language=language)
    except sr.RequestError as e:
        # API不可用或无网络连接
        response["success"] = False
        response["error"] = f"API不可用或网络连接问题: {str(e)}"
    except sr.UnknownValueError:
        # 语音不清晰或无法识别
        response["success"] = False
        response["error"] = "无法识别语音"
    
    return response

def main():
    print("音频文件语音识别示例")
    print("支持的文件格式: WAV, AIFF, AIFF-C, FLAC\n")
    
    # 示例文件路径
    example_files = [
        "example.wav",  # 请确保这些文件存在或修改为实际文件路径
        "speech_sample.flac",
        "recording.aiff",
        "not_exists.wav",
        "unsupported.mp3"
    ]
    
    for file_path in example_files:
        print(f"\n尝试识别文件: {file_path}")
        result = recognize_from_file(file_path)
        
        if result["success"]:
            print(f"识别结果: {result['transcription']}")
        else:
            print(f"错误: {result['error']}")
    
    print("\n自定义文件识别:")
    custom_file = input("请输入音频文件路径 (或按Enter跳过): ")
    if custom_file:
        result = recognize_from_file(custom_file)
        if result["success"]:
            print(f"识别结果: {result['transcription']}")
        else:
            print(f"错误: {result['error']}")

if __name__ == "__main__":
    main()