'''
处理噪音和调整识别灵敏度

这个脚本展示了如何使用SpeechRecognition库处理环境噪音和调整识别灵敏度。
'''

import speech_recognition as sr
import time

def main():
    # 创建Recognizer和Microphone实例
    recognizer = sr.Recognizer()
    microphone = sr.Microphone()
    
    print("噪音处理和灵敏度调整示例")
    print("按Ctrl+C退出程序\n")
    
    # 展示不同的能量阈值
    print("能量阈值说明:")
    print("- 较低的能量阈值会使识别器更敏感，可能会错误地将背景噪音识别为语音")
    print("- 较高的能量阈值需要更大的音量才能触发识别，但可能会错过轻声说话")
    print("- 默认值通常在300-3000之间，取决于麦克风和环境")
    print("- adjust_for_ambient_noise()方法会自动设置适合当前环境的阈值\n")
    
    # 展示不同的暂停阈值
    print("暂停阈值说明:")
    print("- 暂停阈值决定了多长时间的静音被视为语音结束")
    print("- 较低的值会使识别器在短暂停顿后就结束录音")
    print("- 较高的值允许说话者在句子之间有更长的停顿")
    print("- 默认值为0.8秒\n")
    
    try:
        # 1. 自动调整环境噪音
        print("\n1. 自动调整环境噪音")
        print("保持安静，正在测量环境噪音...")
        with microphone as source:
            # 调整麦克风以适应环境噪音，持续2秒
            recognizer.adjust_for_ambient_noise(source, duration=2)
            current_threshold = recognizer.energy_threshold
            print(f"自动设置的能量阈值: {current_threshold}")
            
            print("请说话...")
            try:
                audio = recognizer.listen(source, timeout=5, phrase_time_limit=5)
                text = recognizer.recognize_google(audio, language="zh-CN")
                print(f"识别结果: {text}")
            except sr.WaitTimeoutError:
                print("超时 - 未检测到语音")
            except sr.UnknownValueError:
                print("无法识别语音")
            except sr.RequestError as e:
                print(f"请求错误: {e}")
        
        time.sleep(1)
        
        # 2. 手动设置低能量阈值（更敏感）
        print("\n2. 手动设置低能量阈值（更敏感）")
        low_threshold = max(50, current_threshold / 4)  # 不要设置太低
        recognizer.energy_threshold = low_threshold
        print(f"低能量阈值: {low_threshold}")
        
        with microphone as source:
            print("请轻声说话...")
            try:
                audio = recognizer.listen(source, timeout=5, phrase_time_limit=5)
                text = recognizer.recognize_google(audio, language="zh-CN")
                print(f"识别结果: {text}")
            except sr.WaitTimeoutError:
                print("超时 - 未检测到语音")
            except sr.UnknownValueError:
                print("无法识别语音")
            except sr.RequestError as e:
                print(f"请求错误: {e}")
        
        time.sleep(1)
        
        # 3. 手动设置高能量阈值（不太敏感）
        print("\n3. 手动设置高能量阈值（不太敏感）")
        high_threshold = current_threshold * 2
        recognizer.energy_threshold = high_threshold
        print(f"高能量阈值: {high_threshold}")
        
        with microphone as source:
            print("请大声说话...")
            try:
                audio = recognizer.listen(source, timeout=5, phrase_time_limit=5)
                text = recognizer.recognize_google(audio, language="zh-CN")
                print(f"识别结果: {text}")
            except sr.WaitTimeoutError:
                print("超时 - 未检测到语音")
            except sr.UnknownValueError:
                print("无法识别语音")
            except sr.RequestError as e:
                print(f"请求错误: {e}")
        
        time.sleep(1)
        
        # 4. 调整暂停阈值（短暂停顿）
        print("\n4. 调整暂停阈值（短暂停顿）")
        recognizer.energy_threshold = current_threshold  # 恢复正常能量阈值
        recognizer.pause_threshold = 0.3  # 短暂停顿
        print(f"短暂停顿阈值: 0.3秒")
        
        with microphone as source:
            print("请说一句话，中间有短暂停顿...")
            try:
                audio = recognizer.listen(source, timeout=5, phrase_time_limit=8)
                text = recognizer.recognize_google(audio, language="zh-CN")
                print(f"识别结果: {text}")
            except sr.WaitTimeoutError:
                print("超时 - 未检测到语音")
            except sr.UnknownValueError:
                print("无法识别语音")
            except sr.RequestError as e:
                print(f"请求错误: {e}")
        
        time.sleep(1)
        
        # 5. 调整暂停阈值（长暂停顿）
        print("\n5. 调整暂停阈值（长暂停顿）")
        recognizer.pause_threshold = 2.0  # 长暂停顿
        print(f"长暂停顿阈值: 2.0秒")
        
        with microphone as source:
            print("请说一句话，中间有较长停顿...")
            try:
                audio = recognizer.listen(source, timeout=10, phrase_time_limit=15)
                text = recognizer.recognize_google(audio, language="zh-CN")
                print(f"识别结果: {text}")
            except sr.WaitTimeoutError:
                print("超时 - 未检测到语音")
            except sr.UnknownValueError:
                print("无法识别语音")
            except sr.RequestError as e:
                print(f"请求错误: {e}")
        
        # 总结
        print("\n噪音处理和灵敏度调整总结:")
        print("1. 使用 adjust_for_ambient_noise() 自动调整环境噪音")
        print("2. 通过设置 energy_threshold 调整麦克风灵敏度")
        print("3. 通过设置 pause_threshold 调整语音暂停识别")
        print("4. 对于嘈杂环境，增加能量阈值并使用更长的调整持续时间")
        print("5. 对于安静环境，可以使用较低的能量阈值")
        
    except KeyboardInterrupt:
        print("\n程序已退出")

if __name__ == "__main__":
    main()