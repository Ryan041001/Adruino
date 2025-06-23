'''
多语言支持示例

这个脚本展示了如何使用SpeechRecognition库识别不同语言的语音。
'''

import speech_recognition as sr

def recognize_with_language(recognizer, audio_data, language):
    """
    使用指定语言识别音频
    
    参数:
        recognizer: Recognizer对象
        audio_data: 要识别的音频数据
        language: 语言代码
    
    返回:
        识别结果或错误信息
    """
    try:
        return recognizer.recognize_google(audio_data, language=language)
    except sr.UnknownValueError:
        return "无法识别语音"
    except sr.RequestError as e:
        return f"请求错误: {e}"

def main():
    # 创建Recognizer和Microphone实例
    recognizer = sr.Recognizer()
    microphone = sr.Microphone()
    
    print("多语言语音识别示例")
    
    # 支持的语言列表（部分）
    languages = {
        "中文（简体）": "zh-CN",
        "中文（繁体/粤语）": "zh-TW",
        "英语（美国）": "en-US",
        "英语（英国）": "en-GB",
        "日语": "ja",
        "韩语": "ko",
        "法语": "fr",
        "德语": "de",
        "西班牙语": "es",
        "俄语": "ru",
        "意大利语": "it",
        "葡萄牙语": "pt",
        "阿拉伯语": "ar",
        "印地语": "hi"
    }
    
    print("\n支持的语言:")
    for i, (name, code) in enumerate(languages.items(), 1):
        print(f"{i}. {name} ({code})")
    
    # 录制音频
    print("\n请选择录音方式:")
    print("1. 从麦克风录制")
    print("2. 从音频文件加载")
    
    choice = input("请选择 (1/2): ")
    
    if choice == "1":
        # 从麦克风录制
        with microphone as source:
            print("\n调整麦克风以适应环境噪音...")
            recognizer.adjust_for_ambient_noise(source, duration=1)
            print("请说话...")
            try:
                audio_data = recognizer.listen(source, timeout=5, phrase_time_limit=5)
                print("录音完成!")
            except sr.WaitTimeoutError:
                print("超时 - 未检测到语音")
                return
    elif choice == "2":
        # 从文件加载
        file_path = input("\n请输入音频文件路径: ")
        try:
            with sr.AudioFile(file_path) as source:
                audio_data = recognizer.record(source)
                print("音频加载完成!")
        except Exception as e:
            print(f"错误: {e}")
            return
    else:
        print("无效的选择")
        return
    
    # 使用不同语言识别
    print("\n使用不同语言识别结果:")
    print("-" * 50)
    
    for name, code in languages.items():
        result = recognize_with_language(recognizer, audio_data, code)
        print(f"{name} ({code}): {result}")
    
    print("-" * 50)
    
    # 自定义语言识别
    print("\n自定义语言识别:")
    custom_lang = input("请输入语言代码 (如 zh-CN, en-US): ")
    if custom_lang:
        result = recognize_with_language(recognizer, audio_data, custom_lang)
        print(f"识别结果 ({custom_lang}): {result}")
    
    print("\n语言代码格式说明:")
    print("1. 语言代码通常是两个小写字母 (ISO 639-1)")
    print("2. 对于特定地区的语言，添加连字符和地区代码 (ISO 3166-1)")
    print("3. 例如: 'en' 表示英语, 'en-US' 表示美国英语, 'en-GB' 表示英国英语")
    print("4. 完整的语言代码列表可在Google Cloud Speech-to-Text文档中找到")

if __name__ == "__main__":
    main()