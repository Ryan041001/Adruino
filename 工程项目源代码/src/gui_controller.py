# -*- coding: utf-8 -*-
"""
Qt5 GUI控制器模块 - 替代OLED显示屏的图形界面
"""

import sys
import logging
from datetime import datetime
from typing import Optional, Callable, Dict, Any
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTextEdit, QListWidget, QListWidgetItem,
    QFrame, QScrollArea, QMessageBox, QSystemTrayIcon, QMenu, QGraphicsDropShadowEffect
)
from PyQt5.QtCore import QTimer, pyqtSignal, QThread, Qt, QSize
from PyQt5.QtGui import QFont, QIcon, QPalette, QColor, QPixmap

from config import GUI_CONFIG, BUTTON_CONFIG

def add_shadow(widget):
    shadow = QGraphicsDropShadowEffect(widget)
    shadow.setBlurRadius(25)
    shadow.setColor(QColor(0, 0, 0, 40))
    shadow.setOffset(2, 4)
    widget.setGraphicsEffect(shadow)

class VoiceReminderGUI(QMainWindow):
    """语音提醒系统主界面"""
    
    # 信号定义
    record_requested = pyqtSignal()
    stop_requested = pyqtSignal()
    clear_reminders_requested = pyqtSignal()
    message_received = pyqtSignal(str)  # 添加一个用于接收消息的信号
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        
        # 回调函数
        self.record_callback: Optional[Callable] = None
        self.stop_callback: Optional[Callable] = None
        self.clear_callback: Optional[Callable] = None
        
        # 当前状态
        self.current_state = "idle"  # idle, listening, processing
        
        # 初始化界面
        self._init_ui()
        self._setup_style()
        self._connect_signals()
        self.message_received.connect(self.message_area.append) # 连接信号到槽
        
        self.logger.info("Qt5 GUI界面初始化完成")
    
    def _init_ui(self):
        """初始化用户界面 - 4:3横屏布局"""
        self.setWindowTitle(GUI_CONFIG['WINDOW_TITLE'])
        # 设置4:3横屏尺寸
        self.setGeometry(100, 100, 1024, 768)
        self.setFixedSize(1024, 768)
        
        # 创建中央窗口部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局 - 垂直布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(15, 15, 15, 15)

        # 创建顶部和底部两个QFrame
        top_frame = QFrame()
        bottom_frame = QFrame()

        # 将两个frame添加到主布局，并设置比例
        main_layout.addWidget(top_frame, 2)  # 比例为2
        main_layout.addWidget(bottom_frame, 1) # 比例为1

        # 在top_frame中创建时间区域
        top_layout = QVBoxLayout(top_frame)
        self._create_top_time_area(top_layout)

        # 在bottom_frame中创建中间内容区域
        bottom_layout = QHBoxLayout(bottom_frame)
        bottom_layout.setSpacing(15)

        # 左侧消息通知区域
        self._create_left_message_area(bottom_layout)

        # 中间按钮区域
        self._create_center_buttons_area(bottom_layout)

        # 右侧提醒信息区域（包含倒计时）
        self._create_right_reminder_area(bottom_layout)
    
    def _create_top_time_area(self, layout):
        """创建顶部时间信息区域"""
        time_frame = QFrame()
        time_frame.setObjectName("timeFrame")
        add_shadow(time_frame)
        # time_frame.setMaximumHeight(180)
        # time_frame.setMinimumHeight(180)
        time_layout = QVBoxLayout(time_frame)
        time_layout.setSpacing(10)
        
        # 系统标题
        title_label = QLabel("🎙️ 适老化语音备忘录系统")
        title_label.setObjectName("titleLabel")
        title_label.setAlignment(Qt.AlignCenter)
        title_font = QFont()
        title_font.setPointSize(24)
        title_font.setBold(True)
        title_label.setFont(title_font)
        
        # 当前时间显示 - 超大时钟
        self.time_label = QLabel()
        self.time_label.setObjectName("timeLabel")
        self.time_label.setAlignment(Qt.AlignCenter)
        time_font = QFont()
        time_font.setPointSize(96)  # 增大字体
        time_font.setBold(True)
        self.time_label.setFont(time_font)
        
        time_layout.addWidget(title_label)
        time_layout.addWidget(self.time_label)
        layout.addWidget(time_frame)
        
        # 定时更新时间
        self.time_timer = QTimer()
        self.time_timer.timeout.connect(self._update_time)
        self.time_timer.start(1000)  # 每秒更新
        self._update_time()
    
    def _create_left_message_area(self, layout):
        """创建左侧消息通知区域"""
        message_frame = QFrame()
        message_frame.setObjectName("messageFrame")
        add_shadow(message_frame)
        message_frame.setFixedWidth(300)
        message_layout = QVBoxLayout(message_frame)
        message_layout.setSpacing(10)
        
        # 消息标题
        message_title = QLabel("💬 消息通知")
        message_title.setObjectName("sectionTitle")
        message_title.setAlignment(Qt.AlignCenter)
        message_title.setFont(QFont('', 16, QFont.Bold))
        
        # 系统状态
        self.status_label = QLabel("系统就绪")
        self.status_label.setObjectName("statusLabel")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setFont(QFont('', 14))
        self.status_label.setWordWrap(True)
        
        # 消息显示区域
        self.message_area = QTextEdit()
        self.message_area.setObjectName("messageArea")
        self.message_area.setFont(QFont('', 12))
        self.message_area.setMaximumHeight(400)
        self.message_area.setReadOnly(True)
        
        message_layout.addWidget(message_title)
        message_layout.addWidget(self.status_label)
        message_layout.addWidget(self.message_area)
        message_layout.addStretch()
        
        layout.addWidget(message_frame)
    
    def _create_center_buttons_area(self, layout):
        """创建中间按钮区域"""
        button_frame = QFrame()
        button_frame.setObjectName("buttonFrame")
        button_frame.setFixedWidth(300)
        button_layout = QVBoxLayout(button_frame)
        button_layout.setSpacing(30)
        
        # 录音按钮 - 大按钮
        self.record_button = QPushButton(f"🎤\n{BUTTON_CONFIG['RECORD_BUTTON_TEXT']}")
        self.record_button.setObjectName("recordButton")
        self.record_button.setMinimumHeight(120)
        self.record_button.setFont(QFont('', 18, QFont.Bold))
        
        # 删除停止按钮，录音可以自动识别暂停
        
        # 清除按钮 - 大按钮
        self.clear_button = QPushButton(f"🗑️\n{BUTTON_CONFIG['CLEAR_BUTTON_TEXT']}")
        self.clear_button.setObjectName("clearButton")
        self.clear_button.setMinimumHeight(120)
        self.clear_button.setFont(QFont('', 18, QFont.Bold))
        
        button_layout.addWidget(self.record_button)
        # 移除停止按钮
        button_layout.addWidget(self.clear_button)
        button_layout.addStretch()
        
        layout.addWidget(button_frame)
    
    def _create_right_reminder_area(self, layout):
        """创建右侧提醒信息区域（包含倒计时）"""
        reminder_frame = QFrame()
        reminder_frame.setObjectName("reminderFrame")
        add_shadow(reminder_frame)
        reminder_frame.setFixedWidth(300)
        reminder_layout = QVBoxLayout(reminder_frame)
        reminder_layout.setSpacing(10)
        
        # 提醒标题
        reminder_title = QLabel("📝 提醒事项")
        reminder_title.setObjectName("sectionTitle")
        reminder_title.setAlignment(Qt.AlignCenter)
        reminder_title.setFont(QFont('', 16, QFont.Bold))
        
        # 倒计时显示
        self.countdown_label = QLabel("--:--")
        self.countdown_label.setObjectName("countdownLabel")
        self.countdown_label.setAlignment(Qt.AlignCenter)
        self.countdown_label.setFont(QFont('', 28, QFont.Bold))
        
        # 当前提醒显示
        self.current_reminder_label = QLabel("暂无提醒")
        self.current_reminder_label.setObjectName("currentReminderLabel")
        self.current_reminder_label.setAlignment(Qt.AlignCenter)
        self.current_reminder_label.setFont(QFont('', 14))
        self.current_reminder_label.setWordWrap(True)
        
        # 提醒列表
        self.reminder_list = QListWidget()
        self.reminder_list.setObjectName("reminderList")
        self.reminder_list.setFont(QFont('', 12))
        self.reminder_list.setMaximumHeight(250)
        
        reminder_layout.addWidget(reminder_title)
        reminder_layout.addWidget(self.countdown_label)
        reminder_layout.addWidget(self.current_reminder_label)
        reminder_layout.addWidget(self.reminder_list)
        reminder_layout.addStretch()
        
        layout.addWidget(reminder_frame)
    

    
    def _setup_style(self):
        """设置界面样式 - 优化版"""
        # 定义一个更柔和、统一的调色板
        PRIMARY_COLOR = "#007BFF"      # 主色调 - 柔和蓝
        PRIMARY_LIGHT = "#409CFF"     # 主色调亮色
        PRIMARY_DARK = "#0056b3"      # 主色调暗色
        
        SUCCESS_COLOR = "#28a745"      # 成功/开始 - 绿色
        SUCCESS_HOVER_COLOR = "#218838"
        
        DANGER_COLOR = "#dc3545"       # 危险/停止 - 红色
        DANGER_HOVER_COLOR = "#c82333"

        WARNING_COLOR = "#ffc107"      # 警告/清除 - 橙色
        WARNING_HOVER_COLOR = "#e0a800"

        BACKGROUND_COLOR = "#F4F6F9"   # 主背景色 - 浅灰
        FRAME_BG_COLOR = "#FFFFFF"     # 卡片背景色 - 白色
        TEXT_COLOR = "#212529"         # 主要文字颜色 - 深灰
        TEXT_SECONDARY_COLOR = "#6c757d" # 次要文字颜色 - 灰色
        
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {BACKGROUND_COLOR};
                font-family: 'Microsoft YaHei', 'SimHei', sans-serif;
            }}

            /* --- 统一卡片样式 --- */
            QFrame {{
                background-color: {FRAME_BG_COLOR};
                border-radius: 12px;
                /* 移除边框，使用阴影代替，但阴影需要用 QGraphicsDropShadowEffect 实现 */
                border: 1px solid #E0E0E0; 
                padding: 15px;
            }}

            /* --- 顶部区域 --- */
            #timeFrame {{
                background-color: {PRIMARY_COLOR};
                border: none;
                padding: 20px;
            }}

            #titleLabel, #timeLabel {{
                color: white;
                background-color: transparent;
                border: none;
                text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.2);
            }}
            
            #titleLabel {{ font-size: 28px; font-weight: bold; }}
            #timeLabel {{ font-size: 32px; font-weight: 500; }}

            /* --- 统一分区标题 --- */
            #sectionTitle {{
                font-size: 18px;
                font-weight: bold;
                color: {PRIMARY_DARK};
                padding: 5px 0;
                margin-bottom: 10px;
                background-color: transparent;
                border: none;
                border-bottom: 2px solid {PRIMARY_LIGHT};
            }}

            /* --- 左侧消息区 --- */
            #statusLabel {{
                color: {TEXT_COLOR};
                font-size: 14px;
                font-weight: 500;
                padding: 12px;
                background-color: #E9F5FE; /* 淡蓝色背景 */
                border-radius: 8px;
                border: 1px solid #BDE0FE;
            }}

            #messageArea {{
                background-color: {BACKGROUND_COLOR};
                border: 1px solid #E0E0E0;
                border-radius: 8px;
                padding: 10px;
                font-size: 13px;
                color: {TEXT_SECONDARY_COLOR};
            }}
            
            /* --- 中间按钮区 --- */
            #buttonFrame {{
                 background-color: transparent; /* 让按钮区的背景透明 */
                 border: none;
            }}

            /* 统一按钮基础样式 */
            QPushButton {{
                color: white;
                border: none;
                border-radius: 10px;
                padding: 15px;
                font-size: 18px;
                font-weight: bold;
                min-height: 100px; /* 适度减小按钮高度，使其更协调 */
            }}
            
            QPushButton:hover {{
                /* 简单的亮度提升效果 */
                opacity: 0.9;
            }}

            QPushButton:pressed {{
                /* 按下时稍微变暗 */
                opacity: 0.8;
            }}

            QPushButton:disabled {{
                background-color: #BDBDBD;
                color: #757575;
            }}

            /* 分别定义按钮颜色 */
            #recordButton {{ background-color: {SUCCESS_COLOR}; }}
            #recordButton:hover {{ background-color: {SUCCESS_HOVER_COLOR}; }}

            #stopButton {{ background-color: {DANGER_COLOR}; }}
            #stopButton:hover {{ background-color: {DANGER_HOVER_COLOR}; }}

            #clearButton {{ background-color: {WARNING_COLOR}; }}
            #clearButton:hover {{ background-color: {WARNING_HOVER_COLOR}; }}


            /* --- 右侧提醒区 --- */
            #countdownLabel {{
                color: {DANGER_COLOR};
                font-size: 36px;
                font-weight: bold;
                background-color: transparent;
                border: none;
                qproperty-alignment: 'AlignCenter';
            }}

            #currentReminderLabel {{
                color: {TEXT_COLOR};
                font-size: 15px;
                padding: 12px;
                background: #FFF9E6; /* 淡黄色背景 */
                border-radius: 8px;
                border: 1px solid {WARNING_COLOR};
                min-height: 70px;
            }}

            #reminderList {{
                border: 1px solid #E0E0E0;
                border-radius: 8px;
                font-size: 14px;
            }}

            #reminderList::item {{
                padding: 10px;
                border-bottom: 1px solid #F0F0F0;
                background-color: transparent;
            }}

            #reminderList::item:hover {{
                background-color: #E9F5FE;
            }}

            #reminderList::item:selected {{
                background-color: {PRIMARY_COLOR};
                color: white;
                font-weight: bold;
                border-radius: 6px;
            }}
        """)
    
    def _connect_signals(self):
        """连接信号和槽"""
        self.record_button.clicked.connect(self._on_record_clicked)
        # 移除停止按钮事件处理
        self.clear_button.clicked.connect(self._on_clear_clicked)
    
    def _update_time(self):
        """更新时间显示"""
        current_time = datetime.now().strftime("%Y年%m月%d日 %H:%M:%S")
        self.time_label.setText(current_time)
    
    def _on_record_clicked(self):
        """录音按钮点击事件"""
        if self.record_callback:
            self.record_callback()
    
    # 移除停止按钮点击事件处理
    
    def _on_clear_clicked(self):
        """清除按钮点击事件"""
        if self.clear_callback:
            self.clear_callback()
    
    def set_callbacks(self, record_callback: Callable, clear_callback: Callable):
        """设置回调函数"""
        self.record_callback = record_callback
        self.clear_callback = clear_callback
    
    def show_welcome_screen(self):
        """显示欢迎界面"""
        self.current_state = "idle"
        self.status_label.setText("系统就绪 - 点击开始录音按钮添加提醒")
        self.record_button.setEnabled(True)
        # 移除停止按钮状态设置
        self.record_button.setText(BUTTON_CONFIG['RECORD_BUTTON_TEXT'])
        self.logger.info("GUI状态重置为欢迎界面，录音按钮已启用")
    
    def show_listening_screen(self):
        """显示录音界面"""
        self.current_state = "listening"
        self.status_label.setText("正在录音... 请说出您的提醒内容")
        self.record_button.setEnabled(False)
        # 移除停止按钮状态设置
    
    def show_processing_screen(self):
        """显示处理界面"""
        self.current_state = "processing"
        self.status_label.setText("正在处理语音... 请稍候")
        self.record_button.setEnabled(False)
        # 移除停止按钮状态设置
    
    def show_reminder_screen(self, reminder_data: Dict[str, Any]):
        """显示提醒界面"""
        self.status_label.setText(f"提醒: {reminder_data['task']}")
        # 可以添加更多提醒相关的显示逻辑
    
    def show_message_screen(self, message: str, sender: str):
        """显示消息界面"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        message_text = f"[{timestamp}] {sender}: {message}\n"
        self.message_received.emit(message_text) # 通过信号发送消息
        
        # 更新状态标签显示最新消息
        self.status_label.setText(f"收到来自{sender}的消息:\n{message}")
        
        # 显示系统托盘通知（如果支持）- 使用非阻塞方式
        self.show_notification_non_blocking(f"来自{sender}的消息", message)
    
    def update_reminder_list(self, reminders: list):
        """更新提醒列表 - 支持多个提醒同时显示倒计时"""
        self.reminder_list.clear()
        
        # 过滤活跃的提醒
        active_reminders = [r for r in reminders if r.is_active and not r.is_completed]
        
        # 更新当前提醒显示
        if active_reminders:
            # 按时间排序，显示最近的提醒
            active_reminders.sort(key=lambda r: r.scheduled_time)
            next_reminder = active_reminders[0]
            
            self.current_reminder_label.setText(
                f"最近提醒:\n{next_reminder.task}\n{next_reminder.scheduled_time.strftime('%H:%M')}"
            )
            
            # 更新主倒计时（显示最近提醒的倒计时）
            time_remaining = next_reminder.format_time_remaining() if hasattr(next_reminder, 'format_time_remaining') else None
            if time_remaining and time_remaining != "已到期":
                self.countdown_label.setText(time_remaining)
            else:
                self.countdown_label.setText("即将到时")
        else:
            self.current_reminder_label.setText("暂无提醒")
            self.countdown_label.setText("--:--")
        
        # 更新提醒列表 - 显示所有活跃提醒的倒计时
        for i, reminder in enumerate(active_reminders):
            # 格式化显示文本，包含倒计时
            time_str = reminder.scheduled_time.strftime('%H:%M')
            task_str = reminder.task
            
            if hasattr(reminder, 'format_time_remaining'):
                time_remaining = reminder.format_time_remaining()
                if time_remaining and time_remaining != "已到期":
                    item_text = f"⏰ {time_str} - {task_str} (剩余: {time_remaining})"
                else:
                    item_text = f"🔔 {time_str} - {task_str} (即将到时!)"
            else:
                item_text = f"⏰ {time_str} - {task_str}"
            
            # 为最近的提醒添加特殊标记
            if i == 0:
                item_text = f"📍 {item_text}"
            
            item = QListWidgetItem(item_text)
            
            # 根据剩余时间设置不同的显示样式
            if hasattr(reminder, 'time_remaining'):
                remaining_seconds = reminder.time_remaining().total_seconds()
                if remaining_seconds <= 60:  # 1分钟内
                    item.setBackground(QColor(255, 235, 235))  # 浅红色背景
                elif remaining_seconds <= 300:  # 5分钟内
                    item.setBackground(QColor(255, 248, 220))  # 浅黄色背景
            
            self.reminder_list.addItem(item)
    
    def show_notification(self, title: str, message: str):
        """显示系统通知"""
        try:
            # 创建消息框作为通知
            msg_box = QMessageBox()
            msg_box.setWindowTitle(title)
            msg_box.setText(message)
            msg_box.setIcon(QMessageBox.Information)
            msg_box.setStandardButtons(QMessageBox.Ok)
            msg_box.show()
            
            # 3秒后自动关闭
            QTimer.singleShot(3000, msg_box.close)
            
        except Exception as e:
            self.logger.error(f"显示通知失败: {e}")
    
    def show_notification_non_blocking(self, title: str, message: str):
        """显示非阻塞系统通知"""
        try:
            # 只在状态标签和消息区域显示，不使用弹窗
            self.logger.info(f"通知: {title} - {message}")
            
            # 可以在这里添加其他非阻塞的通知方式，比如:
            # - 改变窗口标题
            # - 闪烁任务栏图标
            # - 播放提示音等
            
        except Exception as e:
            self.logger.error(f"显示非阻塞通知失败: {e}")
    
    def add_log_message(self, message: str):
        """添加日志消息 - 后进先出（LIFO）顺序"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_text = f"[{timestamp}] {message}"
        # 将新消息插入到顶部
        cursor = self.message_area.textCursor()
        cursor.movePosition(cursor.Start)
        cursor.insertText(log_text + "\n")
        # 保持光标在顶部
        cursor.movePosition(cursor.Start)
        self.message_area.setTextCursor(cursor)
    
    def closeEvent(self, event):
        """窗口关闭事件"""
        reply = QMessageBox.question(
            self, '确认退出', 
            '确定要退出语音提醒系统吗？',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()

class GUIController:
    """GUI控制器类 - 管理Qt5界面"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.app = None
        self.main_window = None
        
        # 初始化Qt应用
        self._init_qt_app()
        
        self.logger.info("GUI控制器初始化完成")
    
    def _init_qt_app(self):
        """初始化Qt应用程序"""
        # 检查是否已有QApplication实例
        if not QApplication.instance():
            self.app = QApplication(sys.argv)
        else:
            self.app = QApplication.instance()
        
        # 设置应用程序属性
        self.app.setApplicationName(GUI_CONFIG['WINDOW_TITLE'])
        self.app.setQuitOnLastWindowClosed(True)
        
        # 创建主窗口
        self.main_window = VoiceReminderGUI()
    
    def set_callbacks(self, record_callback: Callable, clear_callback: Callable):
        """设置回调函数"""
        if self.main_window:
            self.main_window.set_callbacks(record_callback, clear_callback)
    
    def show(self):
        """显示主窗口"""
        if self.main_window:
            self.main_window.show()
    
    def run(self):
        """运行Qt应用程序"""
        if self.app:
            return self.app.exec_()
    
    def show_welcome_screen(self):
        """显示欢迎界面"""
        if self.main_window:
            self.main_window.show_welcome_screen()
    
    def show_listening_screen(self):
        """显示录音界面"""
        if self.main_window:
            self.main_window.show_listening_screen()
    
    def show_processing_screen(self):
        """显示处理界面"""
        if self.main_window:
            self.main_window.show_processing_screen()
    
    def show_reminder_screen(self, reminder_data: Dict[str, Any]):
        """显示提醒界面"""
        if self.main_window:
            self.main_window.show_reminder_screen(reminder_data)
    
    def show_message_screen(self, message: str, sender: str):
        """显示消息界面"""
        if self.main_window:
            self.main_window.show_message_screen(message, sender)
    
    def update_reminder_list(self, reminders: list):
        """更新提醒列表"""
        if self.main_window:
            self.main_window.update_reminder_list(reminders)
    
    def add_log_message(self, message: str):
        """添加日志消息"""
        if self.main_window:
            self.main_window.add_log_message(message)