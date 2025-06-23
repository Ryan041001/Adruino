'''
持续监听和识别

这个脚本展示了如何使用SpeechRecognition库实现持续监听和识别功能。
'''

import speech_recognition as sr
import time
import threading

# 全局变量，用于控制监听循环
listening = True

def listen_in_background(recognizer, microphone, callback, language="zh-CN"):
    """
    在后台持续监听麦克风并识别语音
    
    参数:
        recognizer: Recognizer对象
        microphone: Microphone对象
        callback: 回调函数，接收识别结果
        language: 识别语言
    """
    global listening
    
    # 调整麦克风以适应环境噪音
    with microphone as source:
        recognizer.adjust_for_ambient_noise(source, duration=1)
    
    # 开始监听循环
    while listening:
        try:
            with microphone as source:
                print("\n正在监听...")
                audio = recognizer.listen(source, timeout=None, phrase_time_limit=5)
            
            try:
                text = recognizer.recognize_google(audio, language=language)
                callback(text)
            except sr.UnknownValueError:
                print("无法识别语音")
            except sr.RequestError as e:
                print(f"请求错误: {e}")
                # 如果网络问题，短暂暂停避免大量请求
                time.sleep(2)
        
        except Exception as e:
            print(f"监听错误: {e}")
            time.sleep(1)

def process_speech(text):
    """
    处理识别到的语音
    
    参数:
        text: 识别到的文本
    """
    print(f"识别到: {text}")
    
    # 简单的命令处理示例
    text_lower = text.lower()
    
    if "你好" in text_lower or "hello" in text_lower:
        print("回应: 你好！有什么可以帮助你的吗？")
    
    elif "时间" in text_lower or "几点" in text_lower:
        current_time = time.strftime("%H:%M:%S", time.localtime())
        print(f"回应: 现在的时间是 {current_time}")
    
    elif "日期" in text_lower or "几号" in text_lower:
        current_date = time.strftime("%Y年%m月%d日", time.localtime())
        print(f"回应: 今天是 {current_date}")
    
    elif "退出" in text_lower or "停止" in text_lower or "结束" in text_lower or "exit" in text_lower or "stop" in text_lower:
        global listening
        listening = False
        print("回应: 正在退出程序...")
    
    elif "帮助" in text_lower or "help" in text_lower:
        print("回应: 可用命令: 你好, 时间, 日期, 帮助, 退出")
    
    else:
        print("回应: 我听到了你的话，但不确定如何回应。")

def main():
    global listening
    
    print("持续监听和识别示例")
    print("说 '退出' 或 'stop' 结束程序\n")
    
    # 创建Recognizer和Microphone实例
    recognizer = sr.Recognizer()
    microphone = sr.Microphone()
    
    # 设置能量阈值和暂停阈值
    recognizer.energy_threshold = 300  # 可以根据环境调整
    recognizer.dynamic_energy_threshold = True  # 动态调整能量阈值
    recognizer.pause_threshold = 0.8  # 暂停阈值，单位为秒
    
    print("可用命令:")
    print("- '你好' 或 'hello': 打招呼")
    print("- '时间' 或 '几点': 获取当前时间")
    print("- '日期' 或 '几号': 获取当前日期")
    print("- '帮助' 或 'help': 显示帮助信息")
    print("- '退出' 或 'stop': 退出程序")
    
    print("\n初始化麦克风...")
    
    try:
        # 创建并启动监听线程
        listen_thread = threading.Thread(
            target=listen_in_background,
            args=(recognizer, microphone, process_speech)
        )
        listen_thread.daemon = True
        listen_thread.start()
        
        # 主线程等待，直到listening变为False
        while listening:
            time.sleep(0.1)
        
        print("程序已退出")
    
    except KeyboardInterrupt:
        listening = False
        print("\n程序已被用户中断")
    
    except Exception as e:
        listening = False
        print(f"\n发生错误: {e}")

if __name__ == "__main__":
    main()