#!/usr/bin/env python


"""
智能语音交互系统

基于PyQt5的智能语音交互系统，通过树莓派与PyQt GUI界面结合大语言模型LLM和语音合成API，
实现用户指令输入→智能问答→语音播报的完整流程。

功能：
1. 通过按钮或文本框输入用户指令
2. 通过第三方LLM平台(文心一言或DeepSeek)获取回答
3. 通过第三方语音合成API(科大讯飞)将回答转为语音播报
4. 支持麦克风语音输入和音频文件输入
5. 支持语音播放控制和进度显示


"""

import os
import sys
import threading
import time
from enum import Enum



from PyQt5.QtCore import Qt, QSize, QTimer, pyqtSlot
from PyQt5.QtGui import QIcon, QFont, QTextCursor, QPixmap
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QTextEdit, QLineEdit, QComboBox,
    QSlider, QProgressBar, QFileDialog, QMessageBox, QGroupBox,
    QSplitter, QFrame, QToolButton, QSizePolicy
)

from audio_player import AudioPlayer
from config import (
    PRESET_QUESTIONS, WINDOW_TITLE, WINDOW_WIDTH, WINDOW_HEIGHT,
    DEFAULT_VOICE, DEFAULT_SPEED, DEFAULT_VOLUME, DEFAULT_PITCH
)
from llm_client import LLMFactory, LLMType
from speech_recognizer import SpeechRecognizer
from tts_client import TTSClient


class VoiceAssistant(QMainWindow):
    """智能语音交互系统主窗口"""
    
    def __init__(self):
        super().__init__()
        
        # 初始化组件
        self.llm_client = None
        self.tts_client = TTSClient(self)
        self.speech_recognizer = SpeechRecognizer(self)
        self.audio_player = AudioPlayer(self)
        
        # 设置默认LLM类型
        self.current_llm_type = LLMType.DEEPSEEK
        self.llm_client = LLMFactory.create_client(self.current_llm_type, self)
        
        # 连接信号
        self._connect_signals()
        
        # 初始化UI
        self._init_ui()
        
        # 状态变量
        self.is_processing = False
        self.last_audio_file = None


    def _connect_signals(self):
        """连接信号"""
        # LLM客户端信号
        if self.llm_client:
            self.llm_client.response_received.connect(self._on_llm_response)
            self.llm_client.response_error.connect(self._on_llm_error)
            self.llm_client.response_chunk.connect(self._on_llm_chunk)
        
        # TTS客户端信号
        self.tts_client.tts_finished.connect(self._on_tts_finished)
        self.tts_client.tts_error.connect(self._on_tts_error)
        self.tts_client.tts_progress.connect(self._on_tts_progress)
        
        # 语音识别信号
        self.speech_recognizer.recognition_result.connect(self._on_recognition_result)
        self.speech_recognizer.recognition_error.connect(self._on_recognition_error)
        self.speech_recognizer.recording_started.connect(self._on_recording_started)
        self.speech_recognizer.recording_stopped.connect(self._on_recording_stopped)
        
        # 音频播放信号
        self.audio_player.playback_started.connect(self._on_playback_started)
        self.audio_player.playback_stopped.connect(self._on_playback_stopped)
        self.audio_player.playback_error.connect(self._on_playback_error)
        self.audio_player.playback_position.connect(self._on_playback_position)
        self.audio_player.playback_duration.connect(self._on_playback_duration)


    def _init_ui(self):
        """初始化UI"""
        # 设置窗口属性
        self.setWindowTitle(WINDOW_TITLE)
        self.setMinimumSize(WINDOW_WIDTH, WINDOW_HEIGHT)
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # 创建上下分割器
        splitter = QSplitter(Qt.Vertical)
        main_layout.addWidget(splitter)
        
        # 创建上部分（输入区域和预设问题）
        top_widget = QWidget()
        top_layout = QVBoxLayout(top_widget)
        top_layout.setContentsMargins(0, 0, 0, 0)
        splitter.addWidget(top_widget)
        
        # 创建输入区域
        input_group = QGroupBox("输入区域")
        input_layout = QVBoxLayout(input_group)
        
        # 文本输入框和发送按钮
        input_text_layout = QHBoxLayout()
        self.input_text = QLineEdit()
        self.input_text.setPlaceholderText("请输入问题或指令...")
        self.input_text.returnPressed.connect(self._on_send_clicked)
        input_text_layout.addWidget(self.input_text)
        
        self.send_button = QPushButton("发送")
        self.send_button.clicked.connect(self._on_send_clicked)
        input_text_layout.addWidget(self.send_button)
        
        input_layout.addLayout(input_text_layout)
        
        # 语音输入按钮
        voice_input_layout = QHBoxLayout()
        
        self.voice_input_button = QPushButton("语音输入")
        self.voice_input_button.clicked.connect(self._on_voice_input_clicked)
        voice_input_layout.addWidget(self.voice_input_button)
        
        self.file_input_button = QPushButton("从文件输入")
        self.file_input_button.clicked.connect(self._on_file_input_clicked)
        voice_input_layout.addWidget(self.file_input_button)
        
        voice_input_layout.addStretch()
        
        input_layout.addLayout(voice_input_layout)
        
        top_layout.addWidget(input_group)


        # 创建预设问题区域
        preset_group = QGroupBox("预设问题")
        preset_layout = QVBoxLayout(preset_group)
        
        preset_buttons_layout = QHBoxLayout()
        for question in PRESET_QUESTIONS:
            button = QPushButton(question)
            button.clicked.connect(lambda checked, q=question: self._on_preset_clicked(q))
            preset_buttons_layout.addWidget(button)
        
        preset_layout.addLayout(preset_buttons_layout)
        top_layout.addWidget(preset_group)


        # 创建设置区域
        settings_group = QGroupBox("设置")
        settings_layout = QHBoxLayout(settings_group)
        
        # LLM选择
        llm_layout = QVBoxLayout()
        llm_layout.addWidget(QLabel("大语言模型:"))
        self.llm_combo = QComboBox()
        self.llm_combo.addItem(LLMType.DEEPSEEK.value)
        self.llm_combo.currentTextChanged.connect(self._on_llm_changed)
        llm_layout.addWidget(self.llm_combo)
        settings_layout.addLayout(llm_layout)
        
        # 语音合成设置
        tts_layout = QVBoxLayout()
        tts_layout.addWidget(QLabel("发音人:"))
        self.voice_combo = QComboBox()
        self.voice_combo.addItem("小燕 - xiaoyan", "xiaoyan")
        self.voice_combo.addItem("小宇 - xiaoyu", "xiaoyu")
        self.voice_combo.addItem("小梅 - xiaomei", "xiaomei")
        self.voice_combo.addItem("小云 - xiaoyun", "xiaoyun")
        self.voice_combo.addItem("小艾 - xiaoai", "xiaoai")
        self.voice_combo.setCurrentText("小燕 - xiaoyan")
        tts_layout.addWidget(self.voice_combo)
        settings_layout.addLayout(tts_layout)
        
        # 语速设置
        speed_layout = QVBoxLayout()
        speed_layout.addWidget(QLabel("语速:"))
        self.speed_slider = QSlider(Qt.Horizontal)
        self.speed_slider.setRange(0, 100)
        self.speed_slider.setValue(DEFAULT_SPEED)
        self.speed_slider.setTickPosition(QSlider.TicksBelow)
        self.speed_slider.setTickInterval(10)
        speed_layout.addWidget(self.speed_slider)
        settings_layout.addLayout(speed_layout)
        
        # 音量设置
        volume_layout = QVBoxLayout()
        volume_layout.addWidget(QLabel("音量:"))
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(DEFAULT_VOLUME)
        self.volume_slider.setTickPosition(QSlider.TicksBelow)
        self.volume_slider.setTickInterval(10)
        volume_layout.addWidget(self.volume_slider)
        settings_layout.addLayout(volume_layout)
        
        top_layout.addWidget(settings_group)


        # 创建下部分（响应区域和播放控制）
        bottom_widget = QWidget()
        bottom_layout = QVBoxLayout(bottom_widget)
        bottom_layout.setContentsMargins(0, 0, 0, 0)
        splitter.addWidget(bottom_widget)
        
        # 创建响应区域
        response_group = QGroupBox("响应区域")
        response_layout = QVBoxLayout(response_group)
        
        self.response_text = QTextEdit()
        self.response_text.setReadOnly(True)
        response_layout.addWidget(self.response_text)
        
        bottom_layout.addWidget(response_group)
        
        # 创建播放控制区域
        playback_group = QGroupBox("播放控制")
        playback_layout = QVBoxLayout(playback_group)
        
        # 播放控制按钮
        playback_buttons_layout = QHBoxLayout()
        
        self.play_button = QPushButton("播放")
        self.play_button.clicked.connect(self._on_play_clicked)
        self.play_button.setEnabled(False)
        playback_buttons_layout.addWidget(self.play_button)
        
        self.pause_button = QPushButton("暂停")
        self.pause_button.clicked.connect(self._on_pause_clicked)
        self.pause_button.setEnabled(False)
        playback_buttons_layout.addWidget(self.pause_button)
        
        self.stop_button = QPushButton("停止")
        self.stop_button.clicked.connect(self._on_stop_clicked)
        self.stop_button.setEnabled(False)
        playback_buttons_layout.addWidget(self.stop_button)
        
        playback_layout.addLayout(playback_buttons_layout)
        
        # 播放进度条
        self.playback_progress = QProgressBar()
        self.playback_progress.setRange(0, 100)
        self.playback_progress.setValue(0)
        playback_layout.addWidget(self.playback_progress)
        
        # 播放时间标签
        playback_time_layout = QHBoxLayout()
        self.current_time_label = QLabel("00:00")
        playback_time_layout.addWidget(self.current_time_label)
        playback_time_layout.addStretch()
        self.total_time_label = QLabel("00:00")
        playback_time_layout.addWidget(self.total_time_label)
        playback_layout.addLayout(playback_time_layout)
        
        bottom_layout.addWidget(playback_group)
        
        # 创建状态栏
        self.statusBar().showMessage("就绪")
        
        # 设置分割器比例
        splitter.setSizes([int(WINDOW_HEIGHT * 0.4), int(WINDOW_HEIGHT * 0.6)])


    def _on_send_clicked(self):
        """发送按钮点击事件"""
        # 获取输入文本
        text = self.input_text.text().strip()
        if not text:
            QMessageBox.warning(self, "提示", "请输入问题或指令")
            return
        
        # 禁用发送按钮，防止重复发送
        self.send_button.setEnabled(False)
        self.is_processing = True
        
        # 显示用户输入
        self.response_text.append(f"<b>用户:</b> {text}")
        self.response_text.append("")
        self.response_text.append(f"<b>助手:</b> ")
        
        # 清空输入框
        self.input_text.clear()
        
        # 更新状态栏
        self.statusBar().showMessage("正在处理...")
        
        # 在新线程中查询LLM，避免阻塞UI
        threading.Thread(
            target=self._query_llm,
            args=(text,),
            daemon=True
        ).start()
    
    def _on_preset_clicked(self, question):
        """预设问题按钮点击事件"""
        self.input_text.setText(question)
        self._on_send_clicked()
    
    def _on_voice_input_clicked(self):
        """语音输入按钮点击事件"""
        # 禁用按钮，防止重复点击
        self.voice_input_button.setEnabled(False)
        
        # 更新状态栏
        self.statusBar().showMessage("正在录音，请说话...")
        
        # 开始录音
        self.speech_recognizer.recognize_from_microphone(duration=5)
    
    def _on_file_input_clicked(self):
        """文件输入按钮点击事件"""
        # 打开文件对话框
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择音频文件", "", "音频文件 (*.wav *.mp3 *.flac);;所有文件 (*)"
        )
        
        if file_path:
            # 更新状态栏
            self.statusBar().showMessage(f"正在识别文件: {os.path.basename(file_path)}...")
            
            # 开始识别
            self.speech_recognizer.recognize_from_file(file_path)
    
    def _on_llm_changed(self, text):
        """LLM类型改变事件"""
        # 设置LLM类型为DeepSeek
        self.current_llm_type = LLMType.DEEPSEEK
        
        # 创建新的LLM客户端
        if self.llm_client:
            # 断开旧的信号连接
            self.llm_client.response_received.disconnect(self._on_llm_response)
            self.llm_client.response_error.disconnect(self._on_llm_error)
            self.llm_client.response_chunk.disconnect(self._on_llm_chunk)
        
        # 创建新的客户端
        self.llm_client = LLMFactory.create_client(self.current_llm_type, self)
        
        # 连接新的信号
        self.llm_client.response_received.connect(self._on_llm_response)
        self.llm_client.response_error.connect(self._on_llm_error)
        self.llm_client.response_chunk.connect(self._on_llm_chunk)
        
        # 更新状态栏
        self.statusBar().showMessage(f"已切换到 {text}")
    
    def _on_play_clicked(self):
        """播放按钮点击事件"""
        if self.last_audio_file and os.path.exists(self.last_audio_file):
            if self.audio_player.is_playing():
                # 如果正在播放，则恢复播放
                self.audio_player.resume()
            else:
                # 否则开始播放
                self.audio_player.play(self.last_audio_file)
    
    def _on_pause_clicked(self):
        """暂停按钮点击事件"""
        if self.audio_player.is_playing():
            self.audio_player.pause()
    
    def _on_stop_clicked(self):
        """停止按钮点击事件"""
        self.audio_player.stop()


    def _query_llm(self, text):
        """查询LLM
        
        Args:
            text: 查询文本
        """
        if self.llm_client:
            self.llm_client.query(text)
    
    def _on_llm_response(self, response):
        """LLM响应事件
        
        Args:
            response: 响应文本
        """
        # 在新线程中合成语音，避免阻塞UI
        threading.Thread(
            target=self._synthesize_speech,
            args=(response,),
            daemon=True
        ).start()
    
    def _on_llm_error(self, error_msg):
        """LLM错误事件
        
        Args:
            error_msg: 错误信息
        """
        # 更新UI
        self.response_text.append(f"<span style='color:red;'>{error_msg}</span>")
        self.response_text.append("")
        
        # 更新状态栏
        self.statusBar().showMessage("处理失败")
        
        # 启用发送按钮
        self.send_button.setEnabled(True)
        self.is_processing = False
    
    def _on_llm_chunk(self, chunk):
        """LLM流式响应块事件
        
        Args:
            chunk: 响应块文本
        """
        # 更新UI
        cursor = self.response_text.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.insertText(chunk)
        self.response_text.setTextCursor(cursor)
        self.response_text.ensureCursorVisible()
    
    def _synthesize_speech(self, text):
        """合成语音
        
        Args:
            text: 要合成的文本
        """
        # 获取语音合成参数
        voice = self.voice_combo.currentData()
        speed = self.speed_slider.value()  # 整数值
        volume = self.volume_slider.value()  # 整数值
        
        # 使用整数类型的语速和音量参数
        # 合成语音
        try:
            self.tts_client.synthesize(text, voice, speed, volume)
        except Exception as e:
            error_msg = f"语音合成异常: {str(e)}"
            self.statusBar().showMessage(error_msg)
            print(f"语音合成异常详情: {str(e)}")
            print(f"参数类型: voice={type(voice)}, speed={type(speed)}, volume={type(volume)}")
            self._on_tts_error(error_msg)
    
    def _on_tts_finished(self, file_path):
        """语音合成完成事件
        
        Args:
            file_path: 音频文件路径
        """
        # 保存音频文件路径
        self.last_audio_file = file_path
        
        # 更新UI
        self.play_button.setEnabled(True)
        
        # 更新状态栏
        self.statusBar().showMessage("处理完成")
        
        # 启用发送按钮
        self.send_button.setEnabled(True)
        self.is_processing = False
        
        # 自动播放
        self.audio_player.play(file_path)
    
    def _on_tts_error(self, error_msg):
        """语音合成错误事件
        
        Args:
            error_msg: 错误信息
        """
        # 更新UI
        self.response_text.append(f"<span style='color:red;'>{error_msg}</span>")
        self.response_text.append("")
        
        # 更新状态栏
        self.statusBar().showMessage("语音合成失败")
        
        # 启用发送按钮
        self.send_button.setEnabled(True)
        self.is_processing = False
    
    def _on_tts_progress(self, progress):
        """语音合成进度事件
        
        Args:
            progress: 进度百分比
        """
        # 更新状态栏
        self.statusBar().showMessage(f"正在合成语音: {progress}%")
    
    def _on_recognition_result(self, text):
        """语音识别结果事件
        
        Args:
            text: 识别文本
        """
        # 更新UI
        self.input_text.setText(text)
        
        # 更新状态栏
        self.statusBar().showMessage("语音识别完成")
        
        # 启用语音输入按钮
        self.voice_input_button.setEnabled(True)
        
        # 自动发送
        self._on_send_clicked()
    
    def _on_recognition_error(self, error_msg):
        """语音识别错误事件
        
        Args:
            error_msg: 错误信息
        """
        # 更新UI
        QMessageBox.warning(self, "语音识别错误", error_msg)
        
        # 更新状态栏
        self.statusBar().showMessage("语音识别失败")
        
        # 启用语音输入按钮
        self.voice_input_button.setEnabled(True)
    
    def _on_recording_started(self):
        """录音开始事件"""
        # 更新状态栏
        self.statusBar().showMessage("正在录音，请说话...")
    
    def _on_recording_stopped(self):
        """录音结束事件"""
        # 更新状态栏
        self.statusBar().showMessage("录音结束，正在识别...")
    
    def _on_playback_started(self):
        """播放开始事件"""
        # 更新UI
        self.play_button.setEnabled(True)
        self.pause_button.setEnabled(True)
        self.stop_button.setEnabled(True)
        
        # 更新状态栏
        self.statusBar().showMessage("正在播放...")
    
    def _on_playback_stopped(self):
        """播放结束事件"""
        # 更新UI
        self.play_button.setEnabled(True)
        self.pause_button.setEnabled(False)
        self.stop_button.setEnabled(False)
        self.playback_progress.setValue(0)
        self.current_time_label.setText("00:00")
        
        # 更新状态栏
        self.statusBar().showMessage("播放结束")
    
    def _on_playback_error(self, error_msg):
        """播放错误事件
        
        Args:
            error_msg: 错误信息
        """
        # 更新UI
        QMessageBox.warning(self, "播放错误", error_msg)
        
        # 更新状态栏
        self.statusBar().showMessage("播放失败")
    
    def _on_playback_position(self, position):
        """播放位置事件
        
        Args:
            position: 播放位置，单位为毫秒
        """
        # 更新进度条
        duration = self.audio_player.get_duration()
        if duration > 0:
            progress = int(position / duration * 100)
            self.playback_progress.setValue(progress)
        
        # 更新时间标签
        minutes = position // 60000
        seconds = (position % 60000) // 1000
        self.current_time_label.setText(f"{minutes:02d}:{seconds:02d}")
    
    def _on_playback_duration(self, duration):
        """播放时长事件
        
        Args:
            duration: 播放时长，单位为毫秒
        """
        # 更新时间标签
        minutes = duration // 60000
        seconds = (duration % 60000) // 1000
        self.total_time_label.setText(f"{minutes:02d}:{seconds:02d}")
    
    def closeEvent(self, event):
        """窗口关闭事件
        
        Args:
            event: 事件对象
        """
        # 停止播放
        self.audio_player.stop()
        
        # 接受关闭事件
        event.accept()


if __name__ == "__main__":
    # 创建应用
    app = QApplication(sys.argv)
    
    # 设置应用样式
    app.setStyle("Fusion")
    
    # 创建窗口
    window = VoiceAssistant()
    window.show()
    
    # 运行应用
    sys.exit(app.exec_())