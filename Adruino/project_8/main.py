#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# 忽略PyQt5的弃用警告
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

import sys
import os
import time
import math
import requests
import ntplib
from datetime import datetime, timedelta
import threading

from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QGridLayout, QFrame)
from PyQt5.QtGui import (QPixmap, QPainter, QColor, QPen, QBrush, QFont, 
                         QPainterPath, QPolygon, QFontMetrics)
from PyQt5.QtCore import (Qt, QTimer, QRect, QPoint, QSize, 
                          pyqtSignal, QDateTime, QThread)

import config

# Directory for weather icons
ICONS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icons")

# Weather condition mapping to icon filenames
WEATHER_ICONS = {
    "晴": "sunny.png",
    "多云": "cloudy.png",
    "阴": "overcast.png",
    "雨": "rain.png",
    "雪": "snow.png",
    "雾": "fog.png",
    "霾": "haze.png",
    "default": "unknown.png"
}

class TimeSync(QThread):
    """Thread for synchronizing system time with NTP server"""
    time_updated = pyqtSignal(datetime)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ntp_client = ntplib.NTPClient()
        self.running = True
        self._sleep_event = threading.Event()
        
    def run(self):
        while self.running:
            try:
                # 尝试使用主NTP服务器
                try:
                    response = self.ntp_client.request(config.NTP_SERVER_PRIMARY, timeout=config.NTP_TIMEOUT)
                    ntp_time = datetime.fromtimestamp(response.tx_time)
                    self.time_updated.emit(ntp_time)
                    print(f"成功从主NTP服务器({config.NTP_SERVER_PRIMARY})同步时间")
                except Exception as e:
                    print(f"主NTP服务器同步失败: {e}，尝试备用服务器")
                    # 如果主服务器失败，尝试备用服务器
                    response = self.ntp_client.request(config.NTP_SERVER_BACKUP, timeout=config.NTP_TIMEOUT)
                    ntp_time = datetime.fromtimestamp(response.tx_time)
                    self.time_updated.emit(ntp_time)
                    print(f"成功从备用NTP服务器({config.NTP_SERVER_BACKUP})同步时间")
            except Exception as e:
                print(f"NTP同步错误: {e}")
            
            # 使用事件而不是简单的sleep，这样可以响应停止请求
            # 如果事件被设置（由stop()方法触发）或者超时，则退出等待
            if self._sleep_event.wait(timeout=min(config.TIME_SYNC_INTERVAL, 5)):
                # 如果事件被设置，说明收到停止信号
                break
    
    def stop(self):
        """Stop the thread by setting the event and the running flag"""
        self.running = False
        self._sleep_event.set()  # 设置事件，触发线程退出等待


class WeatherUpdater(QThread):
    """Thread for updating weather information"""
    weather_updated = pyqtSignal(list)
    life_index_updated = pyqtSignal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.running = True
        self.retry_count = 0
        self._sleep_event = threading.Event()
        
    def run(self):
        while self.running:
            try:
                # 获取天气预报数据
                weather_data = self.fetch_weather_forecast()
                if weather_data:
                    self.weather_updated.emit(weather_data)
                    self.retry_count = 0  # 重置重试计数
                
                # 获取生活指数数据
                life_data = self.fetch_life_index()
                if life_data:
                    self.life_index_updated.emit(life_data)
                    
            except Exception as e:
                print(f"天气更新错误: {e}")
                self.retry_count += 1
                
                # 如果重试次数超过最大值，等待下一个更新周期
                if self.retry_count >= config.MAX_RETRY_COUNT:
                    print(f"重试次数超过最大值({config.MAX_RETRY_COUNT})，等待下一个更新周期")
                    self.retry_count = 0
                    
                    # 使用事件进行等待，可以响应停止请求
                    if self._sleep_event.wait(timeout=min(config.UPDATE_INTERVAL, 30)):
                        # 如果事件被设置，说明收到停止信号
                        break
                    continue
                
                # 重试前等待
                if self._sleep_event.wait(timeout=config.RETRY_DELAY):
                    # 如果事件被设置，说明收到停止信号
                    break
                continue
            
            # 使用事件进行等待，可以响应停止请求
            # 每5秒检查一次是否收到停止信号
            interval_remaining = config.UPDATE_INTERVAL
            while interval_remaining > 0 and self.running:
                wait_time = min(interval_remaining, 5)  # 最多等待5秒
                if self._sleep_event.wait(timeout=wait_time):
                    # 如果事件被设置，说明收到停止信号
                    break
                interval_remaining -= wait_time
    
    def fetch_weather_forecast(self):
        """Fetch weather forecast data from Seniverse API"""
        params = {
            'key': config.WEATHER_API_KEY,
            'location': config.WEATHER_LOCATION,
            'language': config.WEATHER_LANGUAGE,
            'unit': config.WEATHER_UNIT,
            'start': 0,
            'days': 3
        }
        
        try:
            response = requests.get(config.WEATHER_API_URL, params=params)
            if response.status_code == 200:
                data = response.json()
                return data['results'][0]['daily']
            else:
                print(f"天气预报API错误: {response.status_code}")
                return None
        except Exception as e:
            print(f"获取天气预报错误: {e}")
            return None
    

    
    def fetch_life_index(self):
        """Fetch life index data from Seniverse API"""
        params = {
            'key': config.WEATHER_API_KEY,
            'location': config.WEATHER_LOCATION,
            'language': config.WEATHER_LANGUAGE
        }
        
        try:
            response = requests.get(config.WEATHER_LIFE_API_URL, params=params)
            if response.status_code == 200:
                data = response.json()
                return data['results'][0]['suggestion']
            else:
                print(f"生活指数API错误: {response.status_code}")
                return None
        except Exception as e:
            print(f"获取生活指数错误: {e}")
            return None
    
    def stop(self):
        """Stop the thread by setting the event and the running flag"""
        self.running = False
        self._sleep_event.set()  # 设置事件，触发线程退出等待


class AnalogClock(QWidget):
    """Widget for displaying an analog clock"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(config.CLOCK_SIZE, config.CLOCK_SIZE)
        self.hour = 0
        self.minute = 0
        self.second = 0
        
        # Update the clock every second
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update)
        self.timer.start(1000)
    
    def set_time(self, hour, minute, second):
        """Set the current time for the clock"""
        self.hour = hour
        self.minute = minute
        self.second = second
        self.update()
    
    def paintEvent(self, event):
        """Draw the analog clock"""
        side = min(self.width(), self.height())
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.translate(self.width() / 2, self.height() / 2)
        painter.scale(side / 200.0, side / 200.0)
        
        # Draw the clock face
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor(255, 255, 255)))
        painter.drawEllipse(QRect(-90, -90, 180, 180))
        
        # Draw the clock border
        painter.setPen(QPen(QColor(0, 0, 0), 2))
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(QRect(-90, -90, 180, 180))
        
        # Draw hour markers
        painter.setPen(QPen(QColor(0, 0, 0), 2))
        for i in range(12):
            painter.save()
            painter.rotate(30.0 * i)
            painter.drawLine(80, 0, 90, 0)
            painter.restore()
        
        # Draw minute markers
        painter.setPen(QPen(QColor(0, 0, 0), 1))
        for i in range(60):
            if i % 5 != 0:  # Skip hour markers
                painter.save()
                painter.rotate(6.0 * i)
                painter.drawLine(85, 0, 90, 0)
                painter.restore()
        
        # Draw hour numbers
        font = QFont()
        font.setPointSize(10)
        painter.setFont(font)
        painter.setPen(QPen(QColor(0, 0, 0)))
        
        for i in range(1, 13):
            angle = i * 30
            rad = math.radians(angle - 90)  # -90 to start at 12 o'clock
            x = 70 * math.cos(rad)
            y = 70 * math.sin(rad)
            
            # Center the text
            text = str(i)
            fm = QFontMetrics(font)
            text_width = fm.width(text)
            text_height = fm.height()
            
            painter.drawText(int(x - text_width/2), int(y + text_height/3), text)
        
        # Calculate angles for hour, minute, and second hands
        hour_angle = (self.hour % 12 + self.minute / 60.0) * 30.0
        minute_angle = (self.minute + self.second / 60.0) * 6.0
        second_angle = self.second * 6.0
        
        # Draw hour hand
        painter.save()
        painter.rotate(hour_angle)
        painter.setPen(QPen(QColor(0, 0, 0), 4))
        painter.drawLine(0, 0, 0, -40)
        painter.restore()
        
        # Draw minute hand
        painter.save()
        painter.rotate(minute_angle)
        painter.setPen(QPen(QColor(0, 0, 0), 2))
        painter.drawLine(0, 0, 0, -60)
        painter.restore()
        
        # Draw second hand
        painter.save()
        painter.rotate(second_angle)
        painter.setPen(QPen(QColor(255, 0, 0), 1))
        painter.drawLine(0, 0, 0, -70)
        painter.restore()
        
        # Draw the center point
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor(255, 0, 0)))
        painter.drawEllipse(QRect(-4, -4, 8, 8))


class WeatherWidget(QWidget):
    """Widget for displaying weather information"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the weather widget UI"""
        layout = QVBoxLayout(self)
        
        # 标题
        title_label = QLabel("天气预报")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet(f"font-size: 18px; font-weight: bold; font-family: {config.FONT_FAMILY}; color: {config.THEME_COLOR};")
        layout.addWidget(title_label)
        
        # 天气预报网格
        weather_frame = QFrame()
        weather_frame.setFrameShape(QFrame.StyledPanel)
        weather_frame.setStyleSheet("background-color: rgba(255, 255, 255, 0.7); border-radius: 10px;")
        weather_layout = QVBoxLayout(weather_frame)
        
        self.weather_grid = QGridLayout()
        
        # 创建3天的天气显示组件
        self.day_labels = []
        self.icon_labels = []
        self.temp_labels = []
        self.cond_labels = []
        
        # 列标题
        headers = ["日期", "天气", "温度", "状况"]
        for i, header in enumerate(headers):
            label = QLabel(header)
            label.setAlignment(Qt.AlignCenter)
            label.setStyleSheet(f"font-weight: bold; font-family: {config.FONT_FAMILY};")
            self.weather_grid.addWidget(label, 0, i)
        
        # 创建3天天气的占位符
        for i in range(3):
            # 日期标签
            day_label = QLabel("--")
            day_label.setAlignment(Qt.AlignCenter)
            day_label.setStyleSheet(f"font-family: {config.FONT_FAMILY};")
            self.day_labels.append(day_label)
            self.weather_grid.addWidget(day_label, i+1, 0)
            
            # 天气图标
            icon_label = QLabel()
            icon_label.setAlignment(Qt.AlignCenter)
            icon_label.setFixedSize(50, 50)
            self.icon_labels.append(icon_label)
            self.weather_grid.addWidget(icon_label, i+1, 1)
            
            # 温度
            temp_label = QLabel("--°C")
            temp_label.setAlignment(Qt.AlignCenter)
            temp_label.setStyleSheet(f"font-family: {config.FONT_FAMILY};")
            self.temp_labels.append(temp_label)
            self.weather_grid.addWidget(temp_label, i+1, 2)
            
            # 天气状况
            cond_label = QLabel("--")
            cond_label.setAlignment(Qt.AlignCenter)
            cond_label.setStyleSheet(f"font-family: {config.FONT_FAMILY};")
            self.cond_labels.append(cond_label)
            self.weather_grid.addWidget(cond_label, i+1, 3)
        
        weather_layout.addLayout(self.weather_grid)
        layout.addWidget(weather_frame)
        
        # 生活指数信息
        info_frame = QFrame()
        info_frame.setFrameShape(QFrame.StyledPanel)
        info_frame.setStyleSheet("background-color: rgba(255, 255, 255, 0.7); border-radius: 10px;")
        info_layout = QVBoxLayout(info_frame)
        
        # 生活指数信息
        life_title = QLabel("生活指数")
        life_title.setAlignment(Qt.AlignCenter)
        life_title.setStyleSheet(f"font-weight: bold; font-family: {config.FONT_FAMILY}; color: {config.THEME_COLOR};")
        info_layout.addWidget(life_title)
        
        life_grid = QGridLayout()
        
        # 生活指数项目
        self.life_index_labels = {}
        life_indices = [
            ("comfort", "舒适度"), 
            ("dressing", "穿衣"), 
            ("uv", "紫外线"), 
            ("sport", "运动")
        ]
        
        for i, (index_key, index_name) in enumerate(life_indices):
            row, col = divmod(i, 2)
            label = QLabel(f"{index_name}: --")
            label.setAlignment(Qt.AlignCenter)
            label.setStyleSheet(f"font-family: {config.FONT_FAMILY};")
            self.life_index_labels[index_key] = label
            life_grid.addWidget(label, row, col)
        
        info_layout.addLayout(life_grid)
        layout.addWidget(info_frame)
        
        # 数据更新时间
        self.update_time_label = QLabel("数据更新时间: --")
        self.update_time_label.setAlignment(Qt.AlignCenter)
        self.update_time_label.setStyleSheet(f"font-size: 12px; font-family: {config.FONT_FAMILY}; color: gray;")
        layout.addWidget(self.update_time_label)
        
        self.setLayout(layout)
    
    def update_weather(self, weather_data):
        """Update the weather display with new data"""
        if not weather_data or len(weather_data) < 3:
            return
        
        for i, day_data in enumerate(weather_data[:3]):
            # 更新日期
            date = datetime.strptime(day_data['date'], '%Y-%m-%d')
            day_str = f"{date.month}月{date.day}日"
            self.day_labels[i].setText(day_str)
            
            # 更新图标
            condition = day_data['text_day']
            icon_file = WEATHER_ICONS.get(condition, WEATHER_ICONS['default'])
            icon_path = os.path.join(ICONS_DIR, icon_file)
            
            if os.path.exists(icon_path):
                pixmap = QPixmap(icon_path)
                self.icon_labels[i].setPixmap(pixmap.scaled(40, 40, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            
            # 更新温度
            temp_range = f"{day_data['low']}°C ~ {day_data['high']}°C"
            self.temp_labels[i].setText(temp_range)
            
            # 更新天气状况
            self.cond_labels[i].setText(condition)
        
        # 更新数据更新时间
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.update_time_label.setText(f"数据更新时间: {current_time}")
    

    
    def update_life_index(self, life_data):
        """Update the life index display with new data"""
        if not life_data:
            return
        
        # 更新生活指数
        for index_key, label in self.life_index_labels.items():
            if index_key in life_data:
                brief = life_data[index_key]['brief']
                label.setText(f"{label.text().split(':')[0]}: {brief}")
                
                # 设置工具提示显示详细信息
                if 'details' in life_data[index_key]:
                    label.setToolTip(life_data[index_key]['details'])



class DigitalClock(QLabel):
    """Widget for displaying a digital clock"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet("font-size: 24px; font-weight: bold;")
        
        # Update the clock every second
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_time)
        self.timer.start(1000)
        
        self.update_time()
    
    def update_time(self):
        """Update the displayed time"""
        current_time = QDateTime.currentDateTime()
        time_str = current_time.toString("yyyy年MM月dd日 hh:mm:ss")
        weekday = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"][current_time.date().dayOfWeek() - 1]
        display_text = f"{time_str} {weekday}"
        self.setText(display_text)


class MainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("家庭时钟和气象服务")
        self.setMinimumSize(config.WINDOW_WIDTH, config.WINDOW_HEIGHT)
        
        # 设置应用程序风格
        if config.DARK_MODE:
            self.setStyleSheet("background-color: #303030; color: white;")
        
        self.setup_ui()
        self.init_threads()
        
        # 如果图标目录不存在，创建它
        if not os.path.exists(ICONS_DIR):
            os.makedirs(ICONS_DIR)
    
    def setup_ui(self):
        """Set up the main UI"""
        central_widget = QWidget()
        main_layout = QHBoxLayout(central_widget)
        
        # 左侧面板 - 时钟
        left_panel = QFrame()
        left_panel.setFrameShape(QFrame.StyledPanel)
        left_panel.setStyleSheet("background-color: rgba(255, 255, 255, 0.7); border-radius: 10px;")
        left_layout = QVBoxLayout(left_panel)
        
        # 数字时钟
        clock_title = QLabel("当前时间")
        clock_title.setAlignment(Qt.AlignCenter)
        clock_title.setStyleSheet(f"font-size: 18px; font-weight: bold; font-family: {config.FONT_FAMILY}; color: {config.THEME_COLOR};")
        left_layout.addWidget(clock_title)
        
        self.digital_clock = DigitalClock()
        left_layout.addWidget(self.digital_clock)
        
        # 模拟时钟
        self.analog_clock = AnalogClock()
        left_layout.addWidget(self.analog_clock, 1)  # 拉伸填充空间
        
        # 时间同步状态
        self.time_sync_label = QLabel("时间同步状态: 未同步")
        self.time_sync_label.setAlignment(Qt.AlignCenter)
        self.time_sync_label.setStyleSheet(f"font-size: 12px; font-family: {config.FONT_FAMILY}; color: gray;")
        left_layout.addWidget(self.time_sync_label)
        
        # 右侧面板 - 天气
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        # 天气组件
        self.weather_widget = WeatherWidget()
        right_layout.addWidget(self.weather_widget)
        
        # 状态信息
        self.status_frame = QFrame()
        self.status_frame.setFrameShape(QFrame.StyledPanel)
        self.status_frame.setStyleSheet("background-color: rgba(255, 255, 255, 0.7); border-radius: 10px;")
        status_layout = QVBoxLayout(self.status_frame)
        
        status_title = QLabel("系统状态")
        status_title.setAlignment(Qt.AlignCenter)
        status_title.setStyleSheet(f"font-weight: bold; font-family: {config.FONT_FAMILY}; color: {config.THEME_COLOR};")
        status_layout.addWidget(status_title)
        
        self.status_label = QLabel("正在获取数据...")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet(f"font-family: {config.FONT_FAMILY};")
        status_layout.addWidget(self.status_label)
        
        right_layout.addWidget(self.status_frame)
        
        # 设置布局
        right_panel.setLayout(right_layout)
        
        # 将面板添加到主布局
        main_layout.addWidget(left_panel, 1)  # 左侧面板占据1份空间
        
        # 添加分隔线
        separator = QFrame()
        separator.setFrameShape(QFrame.VLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet(f"color: {config.THEME_COLOR};")
        main_layout.addWidget(separator)
        
        main_layout.addWidget(right_panel, 2)  # 右侧面板占据2份空间
        
        self.setCentralWidget(central_widget)
        
        # 设置定时器更新模拟时钟
        self.clock_timer = QTimer(self)
        self.clock_timer.timeout.connect(self.update_analog_clock)
        self.clock_timer.start(1000)
    
    def init_threads(self):
        """Initialize background threads for time sync and weather updates"""
        # 时间同步线程
        self.time_sync = TimeSync(self)
        self.time_sync.time_updated.connect(self.on_time_updated)
        self.time_sync.start()
        
        # 天气更新线程
        self.weather_updater = WeatherUpdater(self)
        self.weather_updater.weather_updated.connect(self.on_weather_updated)
        self.weather_updater.life_index_updated.connect(self.on_life_index_updated)
        self.weather_updater.start()
    
    def update_analog_clock(self):
        """Update the analog clock with current time"""
        current_time = QDateTime.currentDateTime().time()
        self.analog_clock.set_time(current_time.hour(), current_time.minute(), current_time.second())
    
    def on_time_updated(self, ntp_time):
        """Handle NTP time update"""
        self.time_sync_label.setText(f"时间同步状态: 已同步 ({ntp_time.strftime('%Y-%m-%d %H:%M:%S')})")
        self.status_label.setText(f"时间已从阿里云NTP服务器同步")
        
        # 在真实应用中，您将在此处设置系统时间
        # 这需要在Linux/Raspberry Pi上的root权限
        # 对于演示，我们只更新显示
    
    def on_weather_updated(self, weather_data):
        """Handle weather forecast data update"""
        self.weather_widget.update_weather(weather_data)
        self.status_label.setText(f"天气预报数据已更新")
    

    
    def on_life_index_updated(self, life_data):
        """Handle life index data update"""
        self.weather_widget.update_life_index(life_data)
        self.status_label.setText(f"生活指数数据已更新")
    
    def closeEvent(self, event):
        """Handle application close event"""
        # 显示关闭状态
        self.status_label.setText("正在关闭应用程序...")
        QApplication.processEvents()  # 确保UI更新
        
        # 停止后台线程
        try:
            # 设置超时，避免无限等待
            self.time_sync.stop()
            self.weather_updater.stop()
            
            # 使用带超时的等待
            if not self.time_sync.wait(3000):  # 等待最多3秒
                print("时间同步线程未能在超时时间内结束")
                
            if not self.weather_updater.wait(3000):  # 等待最多3秒
                print("天气更新线程未能在超时时间内结束")
                
        except Exception as e:
            print(f"关闭线程时出错: {e}")
        
        # 强制接受关闭事件
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Set application style
    app.setStyle("Fusion")
    
    # Create and show the main window
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec_())
