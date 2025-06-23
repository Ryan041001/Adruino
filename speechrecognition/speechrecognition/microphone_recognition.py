'''
从麦克风实时识别语音

这个脚本展示了如何使用SpeechRecognition库从麦克风获取音频并实时识别语音。
'''

import speech_recognition as sr
import time

def recognize_speech_from_mic(recognizer, microphone, language="zh-CN"):
    """
    从麦克风录制音频并识别语音
    
    参数:
        recognizer: Recognizer对象
        microphone: Microphone对象
        language: 识别语言 (默认为中文)
    
    返回: 包含以下键的字典:
        "success": 布尔值，表示操作是否成功
        "error":   None或错误信息字符串
        "transcription": None或识别的文本字符串
    """
    # 检查参数类型
    if not isinstance(recognizer, sr.Recognizer):
        raise TypeError("'recognizer' 必须是 'Recognizer' 实例")

    if not isinstance(microphone, sr.Microphone):
        raise TypeError("'microphone' 必须是 'Microphone' 实例")

    # 设置响应对象
    response = {
        "success": True,
        "error": None,
        "transcription": None
    }

    # 调整麦克风灵敏度以应对环境噪音
    with microphone as source:
        print("调整麦克风以适应环境噪音...")
        recognizer.adjust_for_ambient_noise(source, duration=1)
        print("请说话...")
        
        try:
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=5)
        except sr.WaitTimeoutError:
            response["success"] = False
            response["error"] = "听取超时 - 未检测到语音"
            return response

    # 尝试识别语音
    try:
        response["transcription"] = recognizer.recognize_google(audio, language=language)
    except sr.RequestError:
        # API不可用或无网络连接
        response["success"] = False
        response["error"] = "API不可用或网络连接问题"
    except sr.UnknownValueError:
        # 语音不清晰或无法识别
        response["success"] = False
        response["error"] = "无法识别语音"

    return response

def main():
    # 创建Recognizer和Microphone实例
    recognizer = sr.Recognizer()
    microphone = sr.Microphone()
    
    print("麦克风实时语音识别示例")
    print("按Ctrl+C退出程序\n")
    
    try:
        while True:
            print("\n准备识别...")
            result = recognize_speech_from_mic(recognizer, microphone)
            
            if result["success"]:
                print(f"识别结果: {result['transcription']}")
            else:
                print(f"错误: {result['error']}")
            
            time.sleep(1)  # 短暂暂停，避免CPU使用率过高
    except KeyboardInterrupt:
        print("\n程序已退出")

if __name__ == "__main__":
    main()


