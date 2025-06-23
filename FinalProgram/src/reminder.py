# -*- coding: utf-8 -*-
"""
提醒管理器模块 - 管理定时提醒任务
"""

import threading
import time
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Callable
from dataclasses import dataclass
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.date import DateTrigger
import uuid

from config import REMINDER_CONFIG

@dataclass
class Reminder:
    """提醒数据类"""
    id: str
    task: str
    scheduled_time: datetime
    created_time: datetime
    is_active: bool = True
    is_completed: bool = False
    original_text: str = ""
    
    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())
    
    def time_remaining(self) -> timedelta:
        """获取剩余时间"""
        if self.is_completed or not self.is_active:
            return timedelta(0)
        return max(self.scheduled_time - datetime.now(), timedelta(0))
    
    def is_due(self) -> bool:
        """检查是否到期"""
        return datetime.now() >= self.scheduled_time and self.is_active and not self.is_completed
    
    def format_time_remaining(self) -> str:
        """格式化剩余时间显示"""
        remaining = self.time_remaining()
        if remaining.total_seconds() <= 0:
            return "已到期"
        
        hours, remainder = divmod(int(remaining.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        
        if hours > 0:
            return f"{hours}小时{minutes}分钟"
        elif minutes > 0:
            return f"{minutes}分钟{seconds}秒"
        else:
            return f"{seconds}秒"

class ReminderManager:
    """提醒管理器"""
    
    def __init__(self, voice_callback: Optional[Callable] = None, display_callback: Optional[Callable] = None):
        self.logger = logging.getLogger(__name__)
        self.reminders: List[Reminder] = []
        self.scheduler = BackgroundScheduler()
        self.voice_callback = voice_callback  # 语音播报回调
        self.display_callback = display_callback  # 显示更新回调
        self.max_reminders = REMINDER_CONFIG['MAX_REMINDERS']
        
        # 启动调度器
        self.scheduler.start()
        
        # 启动监控线程
        self.monitor_thread = threading.Thread(target=self._monitor_reminders, daemon=True)
        self.monitor_thread.start()
        
        self.logger.info("提醒管理器初始化完成")
    
    def add_reminder(self, task: str, scheduled_time: datetime, original_text: str = "") -> str:
        """添加新提醒"""
        try:
            # 检查提醒数量限制
            active_count = len([r for r in self.reminders if r.is_active and not r.is_completed])
            if active_count >= self.max_reminders:
                self.logger.warning(f"提醒数量已达上限({self.max_reminders})")
                return None
            
            # 创建提醒
            reminder = Reminder(
                id=str(uuid.uuid4()),
                task=task,
                scheduled_time=scheduled_time,
                created_time=datetime.now(),
                original_text=original_text
            )
            
            # 添加到列表
            self.reminders.append(reminder)
            
            # 添加到调度器
            self.scheduler.add_job(
                func=self._trigger_reminder,
                trigger=DateTrigger(run_date=scheduled_time),
                args=[reminder.id],
                id=reminder.id,
                name=f"提醒: {task}"
            )
            
            self.logger.info(f"添加提醒成功: {task} at {scheduled_time}")
            
            # 更新显示
            if self.display_callback:
                self.display_callback()
            
            return reminder.id
            
        except Exception as e:
            self.logger.error(f"添加提醒失败: {e}")
            return None
    
    def _trigger_reminder(self, reminder_id: str):
        """触发单个提醒"""
        try:
            reminder = self.get_reminder(reminder_id)
            if not reminder or not reminder.is_active:
                return
            
            self.logger.info(f"触发提醒: {reminder.task}")
            
            # 标记为已完成
            reminder.is_completed = True
            
            # 语音播报
            if self.voice_callback:
                message = f"提醒时间到了！{reminder.task}"
                self.voice_callback(message)
            
            # 更新显示
            if self.display_callback:
                self.display_callback()
            
        except Exception as e:
            self.logger.error(f"触发提醒失败: {e}")
    
    def check_and_trigger_due_reminders(self):
        """检查并触发所有到期的提醒 - 支持多个提醒同时触发"""
        try:
            due_reminders = []
            for reminder in self.reminders:
                if reminder.is_due():
                    due_reminders.append(reminder)
            
            if due_reminders:
                self.logger.info(f"发现 {len(due_reminders)} 个到期提醒")
                
                # 同时处理所有到期的提醒
                for reminder in due_reminders:
                    reminder.is_completed = True
                    self.logger.info(f"触发提醒: {reminder.task}")
                
                # 合并语音播报消息
                if self.voice_callback and due_reminders:
                    if len(due_reminders) == 1:
                        message = f"提醒时间到了！{due_reminders[0].task}"
                    else:
                        tasks = "、".join([r.task for r in due_reminders])
                        message = f"有 {len(due_reminders)} 个提醒时间到了！包括：{tasks}"
                    self.voice_callback(message)
                
                # 更新显示
                if self.display_callback:
                    self.display_callback()
                
                return len(due_reminders)
            
            return 0
            
        except Exception as e:
            self.logger.error(f"检查到期提醒失败: {e}")
            return 0
    
    def get_reminder(self, reminder_id: str) -> Optional[Reminder]:
        """获取指定提醒"""
        for reminder in self.reminders:
            if reminder.id == reminder_id:
                return reminder
        return None
    
    def get_active_reminders(self) -> List[Reminder]:
        """获取所有活跃的提醒"""
        return [r for r in self.reminders if r.is_active and not r.is_completed]
    
    def get_current_reminder(self) -> Optional[Reminder]:
        """获取当前最近的提醒"""
        active_reminders = self.get_active_reminders()
        if not active_reminders:
            return None
        
        # 按时间排序，返回最近的
        active_reminders.sort(key=lambda r: r.scheduled_time)
        return active_reminders[0]
    
    def cancel_reminder(self, reminder_id: str) -> bool:
        """取消提醒"""
        try:
            reminder = self.get_reminder(reminder_id)
            if not reminder:
                return False
            
            # 标记为非活跃
            reminder.is_active = False
            
            # 从调度器中移除
            try:
                self.scheduler.remove_job(reminder_id)
            except:
                pass  # 任务可能已经执行完毕
            
            self.logger.info(f"取消提醒: {reminder.task}")
            
            # 更新显示
            if self.display_callback:
                self.display_callback()
            
            return True
            
        except Exception as e:
            self.logger.error(f"取消提醒失败: {e}")
            return False
    
    def snooze_reminder(self, reminder_id: str, minutes: int = None) -> bool:
        """延迟提醒"""
        try:
            if minutes is None:
                minutes = REMINDER_CONFIG['DEFAULT_SNOOZE']
            
            reminder = self.get_reminder(reminder_id)
            if not reminder:
                return False
            
            # 计算新时间
            new_time = datetime.now() + timedelta(minutes=minutes)
            reminder.scheduled_time = new_time
            reminder.is_completed = False
            
            # 重新添加到调度器
            try:
                self.scheduler.remove_job(reminder_id)
            except:
                pass
            
            self.scheduler.add_job(
                func=self._trigger_reminder,
                trigger=DateTrigger(run_date=new_time),
                args=[reminder.id],
                id=reminder.id,
                name=f"提醒(延迟): {reminder.task}"
            )
            
            self.logger.info(f"延迟提醒 {minutes} 分钟: {reminder.task}")
            
            # 更新显示
            if self.display_callback:
                self.display_callback()
            
            return True
            
        except Exception as e:
            self.logger.error(f"延迟提醒失败: {e}")
            return False
    
    def clear_completed_reminders(self):
        """清理已完成的提醒"""
        try:
            before_count = len(self.reminders)
            self.reminders = [r for r in self.reminders if not r.is_completed or r.is_active]
            after_count = len(self.reminders)
            
            if before_count != after_count:
                self.logger.info(f"清理了 {before_count - after_count} 个已完成的提醒")
                
                # 更新显示
                if self.display_callback:
                    self.display_callback()
                    
        except Exception as e:
            self.logger.error(f"清理提醒失败: {e}")
    
    def clear_all_reminders(self):
        """清除所有提醒"""
        try:
            # 停止所有调度任务
            for reminder in self.reminders:
                try:
                    self.scheduler.remove_job(reminder.id)
                except:
                    pass
            
            # 清空提醒列表
            reminder_count = len(self.reminders)
            self.reminders.clear()
            
            self.logger.info(f"已清除所有提醒，共 {reminder_count} 个")
            
            # 更新显示
            if self.display_callback:
                self.display_callback()
                
            return True
            
        except Exception as e:
            self.logger.error(f"清除所有提醒失败: {e}")
            return False
    
    def _monitor_reminders(self):
        """监控提醒状态的后台线程 - 支持多个提醒实时倒计时更新"""
        while True:
            try:
                # 每分钟清理一次已完成的提醒
                if hasattr(self, '_last_cleanup_time'):
                    if time.time() - self._last_cleanup_time > 60:
                        self.clear_completed_reminders()
                        self._last_cleanup_time = time.time()
                else:
                    self._last_cleanup_time = time.time()
                
                # 检查并触发到期的提醒
                triggered_count = self.check_and_trigger_due_reminders()
                
                # 实时更新显示 - 每秒更新一次以支持多个倒计时
                if self.display_callback:
                    active_reminders = self.get_active_reminders()
                    if active_reminders or triggered_count > 0:
                        # 检查是否有任何提醒需要更新显示
                        needs_update = triggered_count > 0  # 如果有提醒被触发，必须更新
                        
                        if not needs_update:
                            for reminder in active_reminders:
                                remaining = reminder.time_remaining().total_seconds()
                                # 在最后5分钟内更频繁更新，或者整分钟时更新
                                if remaining <= 300 or remaining % 60 < 1:
                                    needs_update = True
                                    break
                        
                        if needs_update:
                            self.display_callback()
                
                time.sleep(1)  # 每秒检查一次，支持实时倒计时更新
                
            except Exception as e:
                self.logger.error(f"监控线程异常: {e}")
                time.sleep(5)
    
    def get_all_reminders(self) -> List[Reminder]:
        """获取所有提醒"""
        return self.reminders.copy()
    
    def get_status_summary(self) -> Dict:
        """获取状态摘要 - 支持多个提醒状态"""
        active_reminders = self.get_active_reminders()
        current = self.get_current_reminder()
        
        # 统计不同状态的提醒
        urgent_reminders = []
        critical_reminders = []
        
        for reminder in active_reminders:
            remaining_seconds = reminder.time_remaining().total_seconds()
            if remaining_seconds <= REMINDER_CONFIG['CRITICAL_THRESHOLD']:
                critical_reminders.append(reminder)
            elif remaining_seconds <= REMINDER_CONFIG['URGENT_THRESHOLD']:
                urgent_reminders.append(reminder)
        
        return {
            'total_reminders': len(self.reminders),
            'active_reminders': len(active_reminders),
            'urgent_reminders': len(urgent_reminders),
            'critical_reminders': len(critical_reminders),
            'current_reminder': {
                'task': current.task if current else None,
                'time_remaining': current.format_time_remaining() if current else None,
                'scheduled_time': current.scheduled_time.strftime('%H:%M') if current else None
            } if current else None,
            'all_active_reminders': [
                {
                    'id': r.id,
                    'task': r.task,
                    'time_remaining': r.format_time_remaining(),
                    'scheduled_time': r.scheduled_time.strftime('%H:%M'),
                    'is_urgent': r.time_remaining().total_seconds() <= REMINDER_CONFIG['URGENT_THRESHOLD'],
                    'is_critical': r.time_remaining().total_seconds() <= REMINDER_CONFIG['CRITICAL_THRESHOLD']
                } for r in active_reminders
            ]
        }
    
    def shutdown(self):
        """关闭管理器"""
        try:
            self.scheduler.shutdown()
            self.logger.info("提醒管理器已关闭")
        except Exception as e:
            self.logger.error(f"关闭提醒管理器失败: {e}")

if __name__ == "__main__":
    # 测试代码
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    logging.basicConfig(level=logging.INFO)
    
    def test_voice_callback(message):
        print(f"[语音播报] {message}")
    
    def test_display_callback():
        print(f"[显示更新] {datetime.now()}")
    
    manager = ReminderManager(test_voice_callback, test_display_callback)
    
    # 添加测试提醒
    test_time = datetime.now() + timedelta(seconds=10)
    reminder_id = manager.add_reminder("测试提醒", test_time, "这是一个测试")
    
    print(f"添加提醒: {reminder_id}")
    print(f"状态摘要: {manager.get_status_summary()}")
    
    # 等待提醒触发
    time.sleep(15)
    
    manager.shutdown()