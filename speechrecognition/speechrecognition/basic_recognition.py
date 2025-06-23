'''
基本的语音识别示例

这个脚本展示了使用SpeechRecognition库的基本用法。
'''

import speech_recognition as sr

def main():
    # 创建一个Recognizer对象
    recognizer = sr.Recognizer()
    
    # 打印可用的识别方法
    print("可用的识别方法:")
    print("- recognize_google: Google Web Speech API (免费，需要网络连接)")
    print("- recognize_google_cloud: Google Cloud Speech API (付费，需要API密钥)")
    print("- recognize_bing: Microsoft Bing Speech (付费，需要API密钥)")
    print("- recognize_sphinx: CMU Sphinx (离线)")
    print("- recognize_wit: Wit.ai (免费，需要API密钥)")
    print("- recognize_azure: Microsoft Azure Speech (付费，需要API密钥)")
    print("- recognize_houndify: Houndify (付费，需要API密钥)")
    print("- recognize_ibm: IBM Speech to Text (付费，需要API密钥)")
    print("- recognize_amazon: Amazon Transcribe (付费，需要API密钥)")
    
    print("\n这个示例将使用Google Web Speech API (无需API密钥)")
    
    # 从文件加载音频
    print("\n从文件加载音频示例:")
    try:
        with sr.AudioFile("example.wav") as source:  # 请确保example.wav文件存在
            print("加载音频文件...")
            # 获取音频数据
            audio_data = recognizer.record(source)
            
            # 使用Google Web Speech API识别语音
            print("识别中...")
            text = recognizer.recognize_google(audio_data, language="zh-CN")
            print(f"识别结果: {text}")
    except FileNotFoundError:
        print("错误: 找不到音频文件 'example.wav'")
        print("请创建一个音频文件或使用 microphone_recognition.py 从麦克风录制")
    except sr.UnknownValueError:
        print("Google Speech Recognition 无法理解音频")
    except sr.RequestError as e:
        print(f"无法从Google Speech Recognition服务请求结果; {e}")

    print("\n基本用法说明:")
    print("1. 创建Recognizer对象: recognizer = sr.Recognizer()")
    print("2. 获取音频源 (文件或麦克风)")
    print("3. 从音频源获取音频数据: audio_data = recognizer.record(source)")
    print("4. 使用识别方法识别语音: text = recognizer.recognize_google(audio_data)")

if __name__ == "__main__":
    main()