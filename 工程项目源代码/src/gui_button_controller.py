# -*- coding: utf-8 -*-
"""
GUI按钮控制器模块 - 替代硬件按钮的GUI按钮控制
"""

import logging
from typing import Callable, Optional
from enum import Enum

class ButtonEvent(Enum):
    """按钮事件类型"""
    PRESSED = "pressed"
    RELEASED = "released"
    LONG_PRESS = "long_press"

class ButtonFunction(Enum):
    """按钮功能类型"""
    RECORD = "record"      # 录音功能
    STOP = "stop"          # 停止功能
    CLEAR = "clear"        # 清除功能

class GUIButtonController:
    """GUI按钮控制器类 - 管理GUI按钮事件"""
    
    def __init__(self, button_callback: Optional[Callable] = None):
        self.logger = logging.getLogger(__name__)
        self.button_callback = button_callback
        
        # 按钮状态
        self.button_states = {
            'RECORD': False,
            'STOP': False,
            'CLEAR': False
        }
        
        self.logger.info("GUI按钮控制器初始化完成")
    
    def handle_record_button(self):
        """处理录音按钮点击"""
        self.logger.info("录音按钮被点击")
        if self.button_callback:
            self.button_callback("RECORD", ButtonEvent.PRESSED)
    
    def handle_stop_button(self):
        """处理停止按钮点击"""
        self.logger.info("停止按钮被点击")
        if self.button_callback:
            self.button_callback("STOP", ButtonEvent.PRESSED)
    
    def handle_clear_button(self):
        """处理清除按钮点击"""
        self.logger.info("清除按钮被点击")
        if self.button_callback:
            self.button_callback("CLEAR", ButtonEvent.PRESSED)
    
    def set_button_callback(self, callback: Callable):
        """设置按钮回调函数"""
        self.button_callback = callback
    
    def get_button_state(self, button_name: str) -> bool:
        """获取按钮状态"""
        return self.button_states.get(button_name, False)
    
    def set_button_state(self, button_name: str, state: bool):
        """设置按钮状态"""
        if button_name in self.button_states:
            self.button_states[button_name] = state
            self.logger.debug(f"按钮 {button_name} 状态设置为: {state}")
    
    def cleanup(self):
        """清理资源"""
        self.logger.info("GUI按钮控制器清理完成")
        # GUI按钮控制器不需要特殊的清理操作
        pass