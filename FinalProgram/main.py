#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
适老化语音备忘录系统 - 主程序

功能:
1. 语音识别和自然语言理解
2. 定时提醒管理
3. OLED显示屏控制
4. Web消息接收
5. 硬件按钮控制
"""

import os
import sys
import time
import logging
import signal
import threading
from datetime import datetime
from typing import Optional
from dotenv import load_dotenv
from PyQt5.QtCore import QTimer

# 加载 .env 文件中的环境变量
load_dotenv()

# 添加src目录到路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.voice_assistant import VoiceAssistant
from src.reminder import ReminderManager
from src.gui_controller import GUIController
from src.web_server import WebServer
from src.gui_button_controller import GUIButtonController, ButtonEvent, ButtonFunction
from config import LOG_CONFIG, PATHS

class VoiceReminderSystem:
    """语音提醒系统主类"""
    
    def __init__(self, gui_mode: bool = True):
        self.gui_mode = gui_mode
        self.running = False
        
        # 设置日志
        self._setup_logging()
        self.logger = logging.getLogger(__name__)
        
        # 初始化组件
        self.voice_assistant: Optional[VoiceAssistant] = None
        self.reminder_manager: Optional[ReminderManager] = None
        self.gui_controller: Optional[GUIController] = None
        self.web_server: Optional[WebServer] = None
        self.button_controller: Optional[GUIButtonController] = None
        
        # 系统状态
        self.current_state = "idle"  # idle, listening, processing, reminder_active
        self.state_lock = threading.Lock()
        
        self.logger.info("语音提醒系统初始化开始")
        
        try:
            self._initialize_components()
            self.logger.info("语音提醒系统初始化完成")
        except Exception as e:
            self.logger.error(f"系统初始化失败: {e}")
            raise
    
    def _setup_logging(self):
        """设置日志系统"""
        # 确保日志目录存在
        os.makedirs(os.path.dirname(LOG_CONFIG['FILE']), exist_ok=True)
        
        # 配置日志
        logging.basicConfig(
            level=getattr(logging, LOG_CONFIG['LEVEL']),
            format=LOG_CONFIG['FORMAT'],
            handlers=[
                logging.FileHandler(LOG_CONFIG['FILE'], encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )
    
    def _initialize_components(self):
        """初始化所有组件"""
        try:
            # 1. 初始化GUI控制器
            self.gui_controller = GUIController()
            self.gui_controller.show_welcome_screen()
            
            # 2. 初始化语音助手
            self.voice_assistant = VoiceAssistant()
            
            # 3. 初始化提醒管理器
            self.reminder_manager = ReminderManager(
                voice_callback=self._voice_callback,
                display_callback=self._display_callback
            )
            
            # 4. 初始化Web服务器
            self.web_server = WebServer(message_callback=self._message_callback)
            
            # 5. 初始化GUI按钮控制器
            self.button_controller = GUIButtonController(
                button_callback=self._button_callback
            )
            
            # 6. 设置GUI回调函数
            self.gui_controller.set_callbacks(
                record_callback=self._start_voice_recording,
                clear_callback=self._clear_all_reminders
            )
            
            self.logger.info("所有组件初始化完成")
            
        except Exception as e:
            self.logger.error(f"组件初始化失败: {e}")
            raise
    
    def _voice_callback(self, message: str):
        """语音播报回调"""
        try:
            self.logger.info(f"语音播报: {message}")
            if self.voice_assistant:
                self.voice_assistant.speak(message)
        except Exception as e:
            self.logger.error(f"语音播报失败: {e}")
    
    def _reset_to_ready_state(self):
        """重置系统到就绪状态，确保可以继续录音"""
        try:
            # 确保在主线程中更新GUI
            if self.gui_controller and hasattr(self.gui_controller, 'main_window'):
                if self.gui_controller.main_window:
                    # 使用Qt的信号槽机制确保线程安全
                    QTimer.singleShot(0, lambda: self.gui_controller.show_welcome_screen())
                    self.logger.info("系统状态已重置，可以继续添加新提醒")
        except Exception as e:
            self.logger.error(f"重置状态失败: {e}")
    
    def _display_callback(self):
        """显示更新回调"""
        try:
            if not self.gui_controller or not self.reminder_manager:
                return
            
            # 获取当前提醒
            current_reminder = self.reminder_manager.get_current_reminder()
            
            if current_reminder:
                # 显示提醒信息
                reminder_data = {
                    'task': current_reminder.task,
                    'time_remaining': current_reminder.format_time_remaining(),
                    'scheduled_time': current_reminder.scheduled_time.strftime('%H:%M')
                }
                self.gui_controller.show_reminder_screen(reminder_data)
                
                # 更新提醒列表
                all_reminders = self.reminder_manager.get_all_reminders()
                self.gui_controller.update_reminder_list(all_reminders)
            else:
                # 显示欢迎界面
                self.gui_controller.show_welcome_screen()
                
        except Exception as e:
            self.logger.error(f"显示更新失败: {e}")
    
    def _restore_normal_display(self):
        """恢复正常显示状态"""
        try:
            if self.gui_controller and hasattr(self.gui_controller, 'main_window'):
                if self.gui_controller.main_window:
                    # 使用Qt的信号槽机制确保线程安全
                    QTimer.singleShot(0, lambda: self.gui_controller.main_window.status_label.setText("系统就绪"))
                    
                    # 延迟调用显示更新，避免竞态条件
                    QTimer.singleShot(100, self._display_callback)
                    
                    self.logger.info("GUI状态已恢复正常")
        except Exception as e:
            self.logger.error(f"恢复正常显示失败: {e}")
    
    def _message_callback(self, message: str, sender: str):
        """Web消息回调 - 增强处理子女消息中的提醒项目"""
        try:
            self.logger.info(f"收到来自 {sender} 的消息: {message}")
            
            # 使用语音助手处理子女消息，识别是否包含提醒项目
            if self.voice_assistant:
                result = self.voice_assistant.process_child_message(message, sender)
                
                if result and result['type'] == 'reminder':
                    # 消息中包含提醒项目，添加到提醒管理器
                    reminder_data = result['data']
                    reminder_id = self.reminder_manager.add_reminder(
                        task=reminder_data['task'],
                        scheduled_time=reminder_data['time'],
                        original_text=reminder_data['original_text']
                    )
                    
                    if reminder_id:
                        self.logger.info(f"从{sender}消息中成功添加提醒: {reminder_id}")
                        if self.gui_controller:
                            self.gui_controller.add_log_message(f"从{sender}消息中添加提醒: {reminder_data['task']}")
                            # 显示提醒确认界面
                            self.gui_controller.show_message_screen(
                                f"已添加提醒：{reminder_data['task']}", 
                                f"来自{sender}"
                            )
                    else:
                        self.logger.error(f"添加来自{sender}的提醒失败")
                        if self.gui_controller:
                            self.gui_controller.add_log_message(f"添加来自{sender}的提醒失败")
                
                elif result and result['type'] == 'message':
                    # 普通消息，已经通过语音播报了
                    if self.gui_controller:
                        self.gui_controller.show_message_screen(message, sender)
                        self.gui_controller.add_log_message(f"收到{sender}消息: {message}")
                
                else:
                    # 处理失败，使用原有逻辑
                    announcement = f"您有来自{sender}的新消息：{message}"
                    self._voice_callback(announcement)
                    if self.gui_controller:
                        self.gui_controller.show_message_screen(message, sender)
            
            else:
                # 语音助手未初始化，使用原有逻辑
                announcement = f"您有来自{sender}的新消息：{message}"
                self._voice_callback(announcement)
                if self.gui_controller:
                    self.gui_controller.show_message_screen(message, sender)
            
            # 5秒后恢复正常显示
            if self.gui_controller:
                threading.Timer(5.0, self._restore_normal_display).start()
                
        except Exception as e:
            self.logger.error(f"消息处理失败: {e}")
            # 发生错误时使用原有逻辑
            try:
                    announcement = f"您有来自{sender}的新消息：{message}"
                    self._voice_callback(announcement)
                    if self.gui_controller:
                        self.gui_controller.show_message_screen(message, sender)
                        threading.Timer(5.0, self._restore_normal_display).start()
            except Exception as fallback_error:
                self.logger.error(f"消息处理降级方案也失败: {fallback_error}")
    
    def _button_callback(self, button_name: str, event: ButtonEvent):
        """按钮事件回调"""
        try:
            self.logger.info(f"按钮事件: {button_name} - {event.value}")
            
            if event == ButtonEvent.PRESSED:
                self._handle_button_press(button_name)
            elif event == ButtonEvent.LONG_PRESS:
                self._handle_button_long_press(button_name)
                
        except Exception as e:
            self.logger.error(f"按钮事件处理失败: {e}")
    
    def _handle_button_press(self, button_name: str):
        """处理按钮短按事件"""
        self.logger.info(f"按钮短按: {button_name}")
        
        try:
            if button_name == "RECORD":
                # 录音按钮：开始录音
                if self.current_state == "idle":
                    self._start_voice_recording()
                elif self.current_state == "reminder_active":
                    self._confirm_reminder()
                    
            elif button_name == "STOP":
                # 停止按钮：停止当前操作
                if self.current_state in ["listening", "processing"]:
                    self._stop_current_operation()
                else:
                    self._cancel_current_operation()
                
            elif button_name == "CLEAR":
                # 清除按钮：清除所有提醒
                self._clear_all_reminders()
                    
        except Exception as e:
            self.logger.error(f"处理按钮事件失败: {e}")
    
    def _handle_button_long_press(self, button_name: str):
        """处理按钮长按"""
        with self.state_lock:
            if button_name == "RECORD":
                # 长按录音按钮：开始连续语音识别模式
                self._start_continuous_listening()
                
            elif button_name == "STOP":
                # 长按停止按钮：系统关机
                self._initiate_shutdown()
                
            elif button_name == "CLEAR":
                # 长按清除按钮：清除所有提醒
                self._clear_all_reminders()
    
    def _start_voice_recording(self):
        """开始语音录制"""
        try:
            self.current_state = "listening"
            
            if self.gui_controller:
                self.gui_controller.show_listening_screen()
                self.gui_controller.add_log_message("开始录音...")
            
            # 在新线程中处理语音
            threading.Thread(target=self._process_voice_command, daemon=True).start()
            
        except Exception as e:
            self.logger.error(f"开始语音录制失败: {e}")
            self.current_state = "idle"
            if self.gui_controller:
                self.gui_controller.show_welcome_screen()
                self.gui_controller.add_log_message(f"录音失败: {e}")
    
    def _process_voice_command(self):
        """处理语音命令"""
        with self.state_lock:  # 添加状态锁保护
            try:
                self.current_state = "processing"
                
                if self.gui_controller:
                    self.gui_controller.show_processing_screen()
                    self.gui_controller.add_log_message("正在处理语音...")
                
                if not self.voice_assistant:
                    raise Exception("语音助手未初始化")
                
                # 处理语音命令
                result = self.voice_assistant.process_voice_command()
                
                if result and result['type'] == 'reminder':
                    # 添加提醒
                    reminder_data = result['data']
                    reminder_id = self.reminder_manager.add_reminder(
                        task=reminder_data['task'],
                        scheduled_time=reminder_data['time'],
                        original_text=reminder_data['original_text']
                    )
                    
                    if reminder_id:
                        self.logger.info(f"提醒添加成功: {reminder_id}")
                        if self.gui_controller:
                            self.gui_controller.add_log_message(f"提醒添加成功: {reminder_data['task']}")
                    else:
                        self._voice_callback("抱歉，添加提醒失败。")
                        if self.gui_controller:
                            self.gui_controller.add_log_message("提醒添加失败")
                
                elif result and result['type'] == 'chat':
                    # 普通对话
                    self.logger.info(f"对话内容: {result['data']['message']}")
                    if self.gui_controller:
                        self.gui_controller.add_log_message(f"对话: {result['data']['message']}")
                
            except Exception as e:
                self.logger.error(f"语音命令处理失败: {e}")
                try:
                    if self.voice_assistant:
                        self.voice_assistant.speak("抱歉，处理您的请求时出现了问题。")
                except Exception as voice_error:
                    self.logger.error(f"语音播报失败: {voice_error}")
                
                if self.gui_controller:
                    self.gui_controller.add_log_message(f"处理失败: {e}")
            
            finally:
                # 安全地重置状态
                try:
                    self.current_state = "idle"
                    self._reset_to_ready_state()
                    # 延迟调用显示更新，避免竞态条件
                    threading.Timer(0.1, self._display_callback).start()
                except Exception as reset_error:
                    self.logger.error(f"状态重置失败: {reset_error}")
    
    def _stop_current_operation(self):
        """停止当前操作"""
        self.current_state = "idle"
        self._voice_callback("操作已停止")
        self._display_callback()
    
    def _cancel_current_operation(self):
        """取消当前操作"""
        self.current_state = "idle"
        self._voice_callback("操作已取消")
        self._display_callback()
    
    def _confirm_reminder(self):
        """确认提醒"""
        # 这里可以添加确认提醒的逻辑
        self._voice_callback("提醒已确认")
        self.current_state = "idle"
        self._display_callback()
    
    def _start_continuous_listening(self):
        """开始连续监听模式"""
        self._voice_callback("进入连续监听模式")
        # 这里可以实现连续监听逻辑
    
    def _clear_all_reminders(self):
        """清除所有提醒"""
        try:
            if self.reminder_manager:
                cleared_count = len(self.reminder_manager.get_active_reminders())
                self.reminder_manager.clear_all_reminders()
                
                message = f"已清除 {cleared_count} 个提醒"
                self.logger.info(message)
                self._voice_callback(message)
                
                if self.gui_controller:
                    self.gui_controller.add_log_message(message)
                    self.gui_controller.update_reminder_list([])
                    
        except Exception as e:
            self.logger.error(f"清除提醒失败: {e}")
            if self.gui_controller:
                self.gui_controller.add_log_message(f"清除提醒失败: {e}")
    
    def _show_system_menu(self):
        """显示系统菜单"""
        try:
            if self.reminder_manager:
                active_reminders = self.reminder_manager.get_active_reminders()
                reminder_count = len(active_reminders)
                
                menu_info = f"系统状态: {self.current_state}\n活动提醒: {reminder_count}个"
                
                if self.gui_controller:
                    self.gui_controller.add_log_message(menu_info)
                    self.gui_controller.update_reminder_list(active_reminders)
                
                # 语音播报系统状态
                voice_message = f"当前有{reminder_count}个活动提醒"
                if reminder_count > 0:
                    next_reminder = min(active_reminders, key=lambda r: r.scheduled_time)
                    time_str = next_reminder.scheduled_time.strftime("%H:%M")
                    voice_message += f"，下一个提醒在{time_str}"
                
                self._voice_callback(voice_message)
                
        except Exception as e:
            self.logger.error(f"显示系统菜单失败: {e}")
            if self.gui_controller:
                self.gui_controller.add_log_message(f"显示系统菜单失败: {e}")
    
    def _initiate_shutdown(self):
        """启动关机流程"""
        self._voice_callback("系统即将关闭")
        self.logger.info("用户请求关机")
        threading.Timer(2.0, self.shutdown).start()
    
    def start(self):
        """启动系统"""
        try:
            self.running = True
            
            # 启动Web服务器
            if self.web_server:
                self.web_server.start()
            
            # 显示GUI界面
            if self.gui_controller:
                self.gui_controller.show()
                self.gui_controller.add_log_message("系统启动完成")
            
            self.logger.info("系统启动完成")
            
            # 延迟播放语音，确保GUI完全显示后再播放
            def delayed_voice_announcement():
                try:
                    # 等待2秒确保GUI完全渲染
                    import time
                    time.sleep(2)
                    self._voice_callback("语音助手已启用")
                except Exception as e:
                    self.logger.error(f"延迟语音播放失败: {e}")
            
            # 在新线程中播放语音，避免阻塞GUI
            threading.Thread(target=delayed_voice_announcement, daemon=True).start()
            
            # 启动GUI主循环
            if self.gui_controller:
                return self.gui_controller.run()
            
        except Exception as e:
            self.logger.error(f"系统启动失败: {e}")
            raise
    
    def _main_loop(self):
        """主循环"""
        try:
            while self.running:
                # 定期更新显示
                self._display_callback()
                
                # 检查系统状态
                if self.reminder_manager:
                    status = self.reminder_manager.get_status_summary()
                    if status['current_reminder']:
                        self.current_state = "reminder_active"
                    elif self.current_state == "reminder_active":
                        self.current_state = "idle"
                
                time.sleep(1)  # 1秒更新间隔
                
        except KeyboardInterrupt:
            self.logger.info("收到中断信号，正在关闭系统...")
        except Exception as e:
            self.logger.error(f"主循环异常: {e}")
        finally:
            self.shutdown()
    
    def shutdown(self):
        """关闭系统"""
        with self.state_lock:  # 添加状态锁保护
            try:
                self.running = False
                self.logger.info("正在关闭系统...")
                
                # 按顺序关闭各个组件，避免资源竞争
                components_to_shutdown = [
                    ("button_controller", self.button_controller, "cleanup"),
                    ("web_server", self.web_server, "stop"),
                    ("reminder_manager", self.reminder_manager, "shutdown"),
                ]
                
                for name, component, method_name in components_to_shutdown:
                    if component:
                        try:
                            method = getattr(component, method_name)
                            method()
                            self.logger.info(f"{name} 已关闭")
                        except Exception as e:
                            self.logger.warning(f"{name} 关闭失败: {e}")
                
                # 清理语音助手资源
                if self.voice_assistant:
                    try:
                        self.voice_assistant.cleanup_resources()
                        self.logger.info("语音助手资源已清理")
                    except Exception as e:
                        self.logger.warning(f"语音助手资源清理失败: {e}")
                
                # 确保GUI在主线程中关闭
                if self.gui_controller and hasattr(self.gui_controller, 'app'):
                    try:
                        QTimer.singleShot(0, lambda: self.gui_controller.app.quit())
                    except Exception as e:
                        self.logger.warning(f"GUI关闭失败: {e}")
                
                self.logger.info("系统已关闭")
                
            except Exception as e:
                self.logger.error(f"系统关闭失败: {e}")

def signal_handler(signum, frame):
    """信号处理器"""
    print("\n收到退出信号，正在关闭系统...")
    sys.exit(0)

def main():
    """主函数"""
    # 设置信号处理
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # 检查命令行参数
    gui_mode = '--gui' in sys.argv or len(sys.argv) == 1  # 默认使用GUI模式
    
    if gui_mode:
        print("运行在GUI模式下")
    
    try:
        # 创建并启动系统
        system = VoiceReminderSystem(gui_mode=gui_mode)
        exit_code = system.start()
        sys.exit(exit_code or 0)
        
    except KeyboardInterrupt:
        print("\n用户中断，正在退出...")
    except Exception as e:
        print(f"系统错误: {e}")
        logging.error(f"系统错误: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()