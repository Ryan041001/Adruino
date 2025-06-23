'''
语音转文本应用

这个脚本实现了一个简单的语音转文本应用，支持从麦克风或音频文件输入，
并将识别结果保存到文本文件。
'''

import speech_recognition as sr
import os
import time
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading

class SpeechToTextApp:
    def __init__(self, root):
        self.root = root
        self.root.title("语音转文本应用")
        self.root.geometry("600x500")
        self.root.resizable(True, True)
        
        # 设置样式
        self.style = ttk.Style()
        self.style.configure("TButton", font=("Arial", 10))
        self.style.configure("TLabel", font=("Arial", 10))
        
        # 创建Recognizer实例
        self.recognizer = sr.Recognizer()
        
        # 设置默认参数
        self.language = "zh-CN"
        self.is_recording = False
        self.recording_thread = None
        
        # 创建界面
        self.create_widgets()
    
    def create_widgets(self):
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 顶部控制区域
        control_frame = ttk.LabelFrame(main_frame, text="控制面板", padding="10")
        control_frame.pack(fill=tk.X, pady=5)
        
        # 输入源选择
        source_frame = ttk.Frame(control_frame)
        source_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(source_frame, text="输入源:").pack(side=tk.LEFT, padx=5)
        
        self.source_var = tk.StringVar(value="microphone")
        ttk.Radiobutton(source_frame, text="麦克风", variable=self.source_var, 
                       value="microphone").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(source_frame, text="音频文件", variable=self.source_var, 
                       value="file").pack(side=tk.LEFT, padx=5)
        
        # 文件选择区域
        file_frame = ttk.Frame(control_frame)
        file_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(file_frame, text="音频文件:").pack(side=tk.LEFT, padx=5)
        self.file_var = tk.StringVar()
        ttk.Entry(file_frame, textvariable=self.file_var, width=40).pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        ttk.Button(file_frame, text="浏览...", command=self.browse_file).pack(side=tk.LEFT, padx=5)
        
        # 语言选择区域
        lang_frame = ttk.Frame(control_frame)
        lang_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(lang_frame, text="语言:").pack(side=tk.LEFT, padx=5)
        
        self.languages = {
            "中文（简体）": "zh-CN",
            "中文（繁体/粤语）": "zh-TW",
            "英语（美国）": "en-US",
            "英语（英国）": "en-GB",
            "日语": "ja",
            "韩语": "ko",
            "法语": "fr",
            "德语": "de",
            "西班牙语": "es",
            "俄语": "ru"
        }
        
        self.lang_var = tk.StringVar(value="中文（简体）")
        lang_combo = ttk.Combobox(lang_frame, textvariable=self.lang_var, 
                                values=list(self.languages.keys()), state="readonly", width=15)
        lang_combo.pack(side=tk.LEFT, padx=5)
        lang_combo.bind("<<ComboboxSelected>>", self.on_language_change)
        
        # 操作按钮区域
        button_frame = ttk.Frame(control_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        self.record_button = ttk.Button(button_frame, text="开始录音", command=self.toggle_recording)
        self.record_button.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(button_frame, text="从文件识别", command=self.recognize_from_file).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="清空结果", command=self.clear_results).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="保存结果", command=self.save_results).pack(side=tk.LEFT, padx=5)
        
        # 状态栏
        self.status_var = tk.StringVar(value="就绪")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # 结果区域
        result_frame = ttk.LabelFrame(main_frame, text="识别结果", padding="10")
        result_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # 创建文本框和滚动条
        self.result_text = tk.Text(result_frame, wrap=tk.WORD, width=60, height=15)
        scrollbar = ttk.Scrollbar(result_frame, orient="vertical", command=self.result_text.yview)
        self.result_text.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.result_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    
    def on_language_change(self, event):
        self.language = self.languages[self.lang_var.get()]
        self.status_var.set(f"语言已更改为: {self.lang_var.get()} ({self.language})")
    
    def browse_file(self):
        filetypes = [
            ("音频文件", "*.wav *.aiff *.aif *.flac"),
            ("WAV文件", "*.wav"),
            ("AIFF文件", "*.aiff *.aif"),
            ("FLAC文件", "*.flac"),
            ("所有文件", "*.*")
        ]
        filename = filedialog.askopenfilename(title="选择音频文件", filetypes=filetypes)
        if filename:
            self.file_var.set(filename)
            self.status_var.set(f"已选择文件: {os.path.basename(filename)}")
    
    def toggle_recording(self):
        if self.is_recording:
            # 停止录音
            self.is_recording = False
            self.record_button.configure(text="开始录音")
            self.status_var.set("录音已停止")
        else:
            # 开始录音
            self.is_recording = True
            self.record_button.configure(text="停止录音")
            self.status_var.set("正在录音...")
            
            # 在新线程中开始录音
            self.recording_thread = threading.Thread(target=self.record_from_mic)
            self.recording_thread.daemon = True
            self.recording_thread.start()
    
    def record_from_mic(self):
        try:
            # 创建麦克风实例
            microphone = sr.Microphone()
            
            with microphone as source:
                # 调整麦克风以适应环境噪音
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
                self.root.after(0, lambda: self.status_var.set("正在监听...请说话"))
                
                while self.is_recording:
                    try:
                        audio = self.recognizer.listen(source, timeout=None, phrase_time_limit=10)
                        self.root.after(0, lambda: self.status_var.set("正在识别..."))
                        
                        try:
                            text = self.recognizer.recognize_google(audio, language=self.language)
                            # 在主线程中更新UI
                            self.root.after(0, lambda t=text: self.append_result(t))
                        except sr.UnknownValueError:
                            self.root.after(0, lambda: self.status_var.set("无法识别语音"))
                        except sr.RequestError as e:
                            self.root.after(0, lambda e=e: self.status_var.set(f"请求错误: {e}"))
                        
                        # 短暂暂停，避免CPU使用率过高
                        time.sleep(0.1)
                    
                    except Exception as e:
                        self.root.after(0, lambda e=e: self.status_var.set(f"录音错误: {e}"))
                        break
        
        except Exception as e:
            self.root.after(0, lambda e=e: self.status_var.set(f"麦克风错误: {e}"))
            self.is_recording = False
            self.root.after(0, lambda: self.record_button.configure(text="开始录音"))
    
    def recognize_from_file(self):
        file_path = self.file_var.get()
        if not file_path:
            messagebox.showwarning("警告", "请先选择音频文件")
            return
        
        if not os.path.isfile(file_path):
            messagebox.showerror("错误", f"文件不存在: {file_path}")
            return
        
        # 检查文件扩展名
        file_ext = os.path.splitext(file_path)[1].lower()
        supported_formats = [".wav", ".aiff", ".aif", ".flac"]
        
        if file_ext not in supported_formats:
            messagebox.showerror("错误", f"不支持的文件格式: {file_ext}\n支持的格式: {', '.join(supported_formats)}")
            return
        
        self.status_var.set(f"正在处理文件: {os.path.basename(file_path)}...")
        
        # 在新线程中处理文件
        threading.Thread(target=self.process_audio_file, args=(file_path,), daemon=True).start()
    
    def process_audio_file(self, file_path):
        try:
            with sr.AudioFile(file_path) as source:
                # 获取音频数据
                audio_data = self.recognizer.record(source)
            
            self.root.after(0, lambda: self.status_var.set("正在识别..."))
            
            try:
                text = self.recognizer.recognize_google(audio_data, language=self.language)
                self.root.after(0, lambda t=text: self.append_result(t))
                self.root.after(0, lambda: self.status_var.set("识别完成"))
            except sr.UnknownValueError:
                self.root.after(0, lambda: self.status_var.set("无法识别语音"))
            except sr.RequestError as e:
                self.root.after(0, lambda e=e: self.status_var.set(f"请求错误: {e}"))
        
        except Exception as e:
            self.root.after(0, lambda e=e: self.status_var.set(f"处理文件时出错: {e}"))
    
    def append_result(self, text):
        # 获取当前时间
        current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        
        # 在文本框末尾添加时间戳和识别结果
        self.result_text.insert(tk.END, f"[{current_time}] {text}\n\n")
        self.result_text.see(tk.END)  # 滚动到底部
    
    def clear_results(self):
        self.result_text.delete(1.0, tk.END)
        self.status_var.set("结果已清空")
    
    def save_results(self):
        if not self.result_text.get(1.0, tk.END).strip():
            messagebox.showwarning("警告", "没有可保存的结果")
            return
        
        # 打开保存对话框
        file_path = filedialog.asksaveasfilename(
            title="保存识别结果",
            defaultextension=".txt",
            filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")]
        )
        
        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(self.result_text.get(1.0, tk.END))
                self.status_var.set(f"结果已保存到: {file_path}")
            except Exception as e:
                messagebox.showerror("保存错误", f"保存文件时出错: {e}")

def main():
    root = tk.Tk()
    app = SpeechToTextApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()