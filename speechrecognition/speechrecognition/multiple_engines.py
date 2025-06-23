'''
使用多种识别引擎的示例

这个脚本展示了如何使用SpeechRecognition库的不同识别引擎来处理同一段音频。
注意：大多数引擎需要API密钥，请在使用前替换为你自己的密钥。
'''

import speech_recognition as sr
import os

# 替换为你自己的API密钥
API_KEYS = {
    "bing": "YOUR_BING_API_KEY",
    "google_cloud": "YOUR_GOOGLE_CLOUD_API_KEY",
    "wit": "YOUR_WIT_AI_API_KEY",
    "azure": {
        "key": "YOUR_AZURE_API_KEY",
        "region": "YOUR_AZURE_REGION"
    },
    "houndify": {
        "client_id": "YOUR_HOUNDIFY_CLIENT_ID",
        "client_key": "YOUR_HOUNDIFY_CLIENT_KEY"
    },
    "ibm": {
        "username": "YOUR_IBM_USERNAME",
        "password": "YOUR_IBM_PASSWORD"
    },
    "amazon": {
        "access_key_id": "YOUR_AMAZON_ACCESS_KEY_ID",
        "secret_access_key": "YOUR_AMAZON_SECRET_ACCESS_KEY",
        "region": "us-east-1"
    }
}

def recognize_with_all_engines(audio_data, language="zh-CN"):
    """
    使用所有可用的引擎识别音频
    
    参数:
        audio_data: 要识别的音频数据
        language: 识别语言 (默认为中文，但并非所有引擎都支持)
    
    返回:
        包含每个引擎识别结果的字典
    """
    recognizer = sr.Recognizer()
    results = {}
    
    # 1. Google Web Speech API (免费，有使用限制)
    try:
        results["google"] = {
            "success": True,
            "transcription": recognizer.recognize_google(audio_data, language=language),
        }
    except sr.UnknownValueError:
        results["google"] = {"success": False, "error": "无法识别语音"}
    except sr.RequestError as e:
        results["google"] = {"success": False, "error": f"请求错误: {e}"}
    
    # 2. CMU Sphinx (离线，英语识别效果较好)
    try:
        # Sphinx主要支持英语，所以这里不使用language参数
        results["sphinx"] = {
            "success": True,
            "transcription": recognizer.recognize_sphinx(audio_data)
        }
    except sr.UnknownValueError:
        results["sphinx"] = {"success": False, "error": "无法识别语音"}
    except sr.RequestError as e:
        results["sphinx"] = {"success": False, "error": f"Sphinx错误: {e}"}
    
    # 3. Microsoft Bing Speech (需要API密钥)
    if API_KEYS["bing"] != "YOUR_BING_API_KEY":
        try:
            results["bing"] = {
                "success": True,
                "transcription": recognizer.recognize_bing(audio_data, key=API_KEYS["bing"], language=language)
            }
        except sr.UnknownValueError:
            results["bing"] = {"success": False, "error": "无法识别语音"}
        except sr.RequestError as e:
            results["bing"] = {"success": False, "error": f"请求错误: {e}"}
    else:
        results["bing"] = {"success": False, "error": "未提供API密钥"}
    
    # 4. Google Cloud Speech (需要API密钥)
    if API_KEYS["google_cloud"] != "YOUR_GOOGLE_CLOUD_API_KEY":
        try:
            results["google_cloud"] = {
                "success": True,
                "transcription": recognizer.recognize_google_cloud(audio_data, credentials_json=API_KEYS["google_cloud"], language=language)
            }
        except sr.UnknownValueError:
            results["google_cloud"] = {"success": False, "error": "无法识别语音"}
        except sr.RequestError as e:
            results["google_cloud"] = {"success": False, "error": f"请求错误: {e}"}
    else:
        results["google_cloud"] = {"success": False, "error": "未提供API密钥"}
    
    # 5. Wit.ai (需要API密钥)
    if API_KEYS["wit"] != "YOUR_WIT_AI_API_KEY":
        try:
            results["wit"] = {
                "success": True,
                "transcription": recognizer.recognize_wit(audio_data, key=API_KEYS["wit"])
            }
        except sr.UnknownValueError:
            results["wit"] = {"success": False, "error": "无法识别语音"}
        except sr.RequestError as e:
            results["wit"] = {"success": False, "error": f"请求错误: {e}"}
    else:
        results["wit"] = {"success": False, "error": "未提供API密钥"}
    
    # 6. Microsoft Azure (需要API密钥)
    if API_KEYS["azure"]["key"] != "YOUR_AZURE_API_KEY":
        try:
            results["azure"] = {
                "success": True,
                "transcription": recognizer.recognize_azure(audio_data, key=API_KEYS["azure"]["key"], 
                                                         location=API_KEYS["azure"]["region"], language=language)
            }
        except sr.UnknownValueError:
            results["azure"] = {"success": False, "error": "无法识别语音"}
        except sr.RequestError as e:
            results["azure"] = {"success": False, "error": f"请求错误: {e}"}
    else:
        results["azure"] = {"success": False, "error": "未提供API密钥"}
    
    # 7. Houndify (需要API密钥)
    if API_KEYS["houndify"]["client_id"] != "YOUR_HOUNDIFY_CLIENT_ID":
        try:
            results["houndify"] = {
                "success": True,
                "transcription": recognizer.recognize_houndify(audio_data, 
                                                            client_id=API_KEYS["houndify"]["client_id"],
                                                            client_key=API_KEYS["houndify"]["client_key"])
            }
        except sr.UnknownValueError:
            results["houndify"] = {"success": False, "error": "无法识别语音"}
        except sr.RequestError as e:
            results["houndify"] = {"success": False, "error": f"请求错误: {e}"}
    else:
        results["houndify"] = {"success": False, "error": "未提供API密钥"}
    
    # 8. IBM Speech to Text (需要API密钥)
    if API_KEYS["ibm"]["username"] != "YOUR_IBM_USERNAME":
        try:
            results["ibm"] = {
                "success": True,
                "transcription": recognizer.recognize_ibm(audio_data, 
                                                       username=API_KEYS["ibm"]["username"],
                                                       password=API_KEYS["ibm"]["password"],
                                                       language=language)
            }
        except sr.UnknownValueError:
            results["ibm"] = {"success": False, "error": "无法识别语音"}
        except sr.RequestError as e:
            results["ibm"] = {"success": False, "error": f"请求错误: {e}"}
    else:
        results["ibm"] = {"success": False, "error": "未提供API密钥"}
    
    return results

def main():
    print("多引擎语音识别示例")
    print("注意: 大多数引擎需要API密钥，请在脚本中替换为你自己的密钥\n")
    
    # 创建Recognizer实例
    recognizer = sr.Recognizer()
    
    # 选择音频源
    audio_source = input("选择音频源 (1: 麦克风, 2: 音频文件): ")
    
    if audio_source == "1":
        # 从麦克风获取音频
        microphone = sr.Microphone()
        with microphone as source:
            print("\n调整麦克风以适应环境噪音...")
            recognizer.adjust_for_ambient_noise(source, duration=1)
            print("请说话...")
            audio_data = recognizer.listen(source, timeout=5)
    elif audio_source == "2":
        # 从文件获取音频
        file_path = input("请输入音频文件路径: ")
        if not os.path.isfile(file_path):
            print(f"错误: 文件不存在: {file_path}")
            return
        
        try:
            with sr.AudioFile(file_path) as source:
                audio_data = recognizer.record(source)
        except Exception as e:
            print(f"错误: 读取音频文件时出错: {str(e)}")
            return
    else:
        print("无效的选择")
        return
    
    print("\n使用多种引擎识别中...")
    results = recognize_with_all_engines(audio_data)
    
    print("\n识别结果:")
    print("-" * 50)
    for engine, result in results.items():
        if result["success"]:
            print(f"{engine.upper()}: {result['transcription']}")
        else:
            print(f"{engine.upper()}: {result['error']}")
    print("-" * 50)

if __name__ == "__main__":
    main()