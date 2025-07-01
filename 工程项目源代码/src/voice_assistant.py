# -*- coding: utf-8 -*-
"""
语音助手模块 - 处理语音识别、自然语言理解和语音合成
"""

from aip import AipSpeech
import openai
import pygame
import io
import json
import re
import logging
import pyaudio
import wave
import tempfile
import os
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple

from config import (DEEPSEEK_API_KEY, DEEPSEEK_MODEL, DEEPSEEK_BASE_URL,
                   BAIDU_APP_ID, BAIDU_API_KEY, BAIDU_SECRET_KEY,
                   XUNFEI_APP_ID, XUNFEI_API_KEY, XUNFEI_API_SECRET,
                   TTS_CONFIG, AUDIO_CONFIG)
from src.xunfei_tts import XunfeiTTS

class VoiceAssistant:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # 初始化百度语音识别
        self.aip_speech = None
        self._init_baidu_speech()
        
        # 初始化科大讯飞语音合成
        self.xunfei_tts = XunfeiTTS(XUNFEI_APP_ID, XUNFEI_API_KEY, XUNFEI_API_SECRET)
        
        # 初始化音频录制
        self.audio = pyaudio.PyAudio()
        
        # 初始化pygame用于音频播放
        pygame.mixer.init()
        
        # 初始化DeepSeek客户端
        self.openai_client = openai.OpenAI(
            api_key=DEEPSEEK_API_KEY,
            base_url=DEEPSEEK_BASE_URL
        )
        
        # 移除jieba初始化，使用优化的LLM语义识别
        
        self.logger.info("语音助手初始化完成")
    
    def _init_baidu_speech(self):
        """初始化百度语音识别客户端"""
        try:
            self.aip_speech = AipSpeech(BAIDU_APP_ID, BAIDU_API_KEY, BAIDU_SECRET_KEY)
            self.logger.info("百度语音识别客户端初始化成功")
        except Exception as e:
            self.logger.error(f"百度语音识别客户端初始化失败: {e}")
    
    # 移除jieba相关方法，使用优化的LLM语义识别
    
    def _record_audio(self, duration: int = 5) -> Optional[str]:
        """录制音频并保存为临时文件"""
        try:
            # 音频参数
            chunk = AUDIO_CONFIG['CHUNK_SIZE']
            format = pyaudio.paInt16
            channels = AUDIO_CONFIG['CHANNELS']
            rate = AUDIO_CONFIG['SAMPLE_RATE']
            
            # 开始录音
            stream = self.audio.open(
                format=format,
                channels=channels,
                rate=rate,
                input=True,
                frames_per_buffer=chunk
            )
            
            self.logger.info("开始录音...")
            frames = []
            
            for _ in range(0, int(rate / chunk * duration)):
                data = stream.read(chunk)
                frames.append(data)
            
            stream.stop_stream()
            stream.close()
            
            # 保存为临时文件
            temp_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
            wf = wave.open(temp_file.name, 'wb')
            wf.setnchannels(channels)
            wf.setsampwidth(self.audio.get_sample_size(format))
            wf.setframerate(rate)
            wf.writeframes(b''.join(frames))
            wf.close()
            
            self.logger.info("录音完成")
            return temp_file.name
            
        except Exception as e:
            self.logger.error(f"录音失败: {e}")
            return None
    
    def listen_for_speech(self, timeout: int = 5) -> Optional[str]:
        """监听语音输入并转换为文本 - 增强错误处理和重试机制"""
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                # 录制音频
                audio_file = self._record_audio(timeout)
                if not audio_file:
                    return None
                
                # 读取音频文件
                with open(audio_file, 'rb') as f:
                    audio_data = f.read()
                
                # 检查音频文件大小
                if len(audio_data) < 1000:  # 音频文件太小
                    self.logger.warning(f"音频文件过小 ({len(audio_data)} bytes)，可能录音失败")
                    os.unlink(audio_file)
                    if attempt == max_retries - 1:
                        return None
                    continue
                
                # 使用百度语音识别
                self.logger.info(f"正在识别语音... (尝试 {attempt + 1})")
                
                # 重新初始化百度语音客户端（解决access_token问题）
                if attempt > 0:
                    self.logger.info("重新初始化百度语音客户端")
                    self._init_baidu_speech()
                
                result = self.aip_speech.asr(audio_data, 'wav', AUDIO_CONFIG['SAMPLE_RATE'], {
                    'dev_pid': 1537,  # 中文普通话
                    'cuid': 'voice_assistant_' + str(int(datetime.now().timestamp())),  # 添加唯一标识
                })
                
                # 清理临时文件
                os.unlink(audio_file)
                
                # 详细的结果处理
                self.logger.info(f"百度API响应: {result}")
                
                if isinstance(result, dict):
                    if result.get('err_no') == 0 and 'result' in result and result['result']:
                        text = result['result'][0]
                        self.logger.info(f"识别结果: {text}")
                        return text
                    elif result.get('err_no') == 3301:  # access_token错误
                        self.logger.warning(f"access_token错误，尝试重新初始化 (尝试 {attempt + 1})")
                        if attempt < max_retries - 1:
                            continue
                    elif result.get('err_no') == 3300:  # 输入参数不正确
                        self.logger.error(f"输入参数错误: {result.get('err_msg')}")
                        return None
                    else:
                        self.logger.warning(f"语音识别失败 (尝试 {attempt + 1}): err_no={result.get('err_no')}, err_msg={result.get('err_msg', '未知错误')}")
                        if attempt == max_retries - 1:
                            return None
                        continue
                else:
                    self.logger.error(f"百度API返回格式异常: {type(result)} - {result}")
                    if attempt == max_retries - 1:
                        return None
                    continue
                    
            except KeyError as e:
                self.logger.error(f"语音识别KeyError (尝试 {attempt + 1}): {e}")
                if 'access_token' in str(e):
                    self.logger.info("检测到access_token问题，尝试重新初始化")
                    if attempt < max_retries - 1:
                        continue
                if attempt == max_retries - 1:
                    return None
            except Exception as e:
                self.logger.error(f"语音识别异常 (尝试 {attempt + 1}): {e}")
                if attempt == max_retries - 1:
                    return None
                continue
        
        self.logger.error("语音识别多次重试后仍然失败")
        return None
    
    def speak(self, text: str):
        """语音播报文本 - 播放完成后自动删除音频文件"""
        audio_file = None
        try:
            self.logger.info(f"语音播报: {text}")
            
            # 使用科大讯飞语音合成
            audio_file = self.xunfei_tts.synthesis(
                text,
                voice=TTS_CONFIG['VOICE'],
                speed=TTS_CONFIG['SPEED'],
                pitch=TTS_CONFIG['PITCH'],
                volume=TTS_CONFIG['VOLUME']
            )
            
            if audio_file and os.path.exists(audio_file):
                # 检查文件大小，确保音频文件有效
                file_size = os.path.getsize(audio_file)
                if file_size < 1000:  # 音频文件太小，可能无效
                    self.logger.warning(f"音频文件过小 ({file_size} bytes)，可能合成失败")
                    raise Exception(f"音频文件过小: {file_size} bytes")
                
                self.logger.info(f"开始播放音频文件: {audio_file} (大小: {file_size} bytes)")
                
                # 播放音频文件
                try:
                    pygame.mixer.music.load(audio_file)
                    pygame.mixer.music.play()
                    
                    # 等待播放完成
                    while pygame.mixer.music.get_busy():
                        pygame.time.wait(100)
                        
                    self.logger.info("音频播放完成")
                except pygame.error as pe:
                    self.logger.error(f"pygame播放错误: {pe}")
                    raise Exception(f"音频播放失败: {pe}")
                
            else:
                error_msg = "科大讯飞语音合成失败" if not audio_file else f"音频文件不存在: {audio_file}"
                self.logger.error(error_msg)
                raise Exception(error_msg)
                
        except Exception as e:
            self.logger.error(f"语音播报失败: {e}")
            # 可以在这里添加备用TTS方案
            # self._fallback_tts(text)
        finally:
            # 确保音频文件被删除（带重试机制）
            if audio_file and os.path.exists(audio_file):
                import time
                max_retries = 3
                for attempt in range(max_retries):
                    try:
                        # 确保pygame释放文件句柄
                        try:
                            pygame.mixer.music.stop()
                            pygame.mixer.music.unload()
                        except:
                            pass  # 忽略pygame清理错误
                        time.sleep(0.1)  # 短暂等待
                        
                        os.unlink(audio_file)
                        self.logger.info(f"已删除临时音频文件: {audio_file}")
                        break
                    except Exception as e:
                        if attempt == max_retries - 1:
                            self.logger.warning(f"删除临时音频文件失败 (尝试 {attempt + 1}): {e}")
                        else:
                            time.sleep(0.2)  # 等待后重试
    
    def parse_intent(self, text: str) -> Optional[Dict]:
        """解析提醒意图和时间 - 使用增强可靠性的LLM语义识别"""
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                # 构建增强可靠性的LLM提示词
                prompt = f"""
                你是一个专业的语音助手，专门为老年人解析提醒需求。请仔细分析以下内容，这可能是语音输入，也可能是子女发送的文字消息。
                
                **核心任务：**
                1. 准确判断是否为设置提醒的指令（关键词：提醒、记得、别忘、到时候、叫、通知、告诉等）
                2. 精确提取时间信息和任务内容
                3. 充分考虑老年人的表达习惯、口语化特点以及子女关怀的表达方式
                4. 识别子女发送的关怀消息中的提醒内容（如："妈妈记得明天吃药"、"爸爸别忘了下午去医院"等）
                5. 确保输出格式严格符合JSON规范
                
                **时间解析规则（严格执行）：**
                - 相对时间："一小时后"=1小时，"两小时后"=2小时，"半小时后"=30分钟
                - 分钟单位："十分钟后"=10分钟，"二十分钟后"=20分钟
                - 具体时间点：需要返回特殊格式来标识具体时间，必须准确解析小时和分钟
                  * "明天下午3点" -> time_value=15, time_unit="明天具体时间", hour=15, minute=0
                  * "明天17点" -> time_value=17, time_unit="明天具体时间", hour=17, minute=0
                  * "明天晚上7点" -> time_value=19, time_unit="明天具体时间", hour=19, minute=0
                  * "明天晚上7点半" -> time_value=19, time_unit="明天具体时间", hour=19, minute=30
                  * "今天晚上10:30" -> time_value=22, time_unit="今天具体时间", hour=22, minute=30
                  * "今天晚上10点30分" -> time_value=22, time_unit="今天具体时间", hour=22, minute=30
                  * "后天上午9点" -> time_value=9, time_unit="后天具体时间", hour=9, minute=0
                  * "今天晚上8点" -> time_value=20, time_unit="今天具体时间", hour=20, minute=0
                  * "明天早上" -> time_value=8, time_unit="明天具体时间", hour=8, minute=0
                  * "明天晚上" -> time_value=19, time_unit="明天具体时间", hour=19, minute=0
                - 相对天数（无具体时间）："明天"=1天，"后天"=2天（仅当没有具体时间点时使用）
                
                **质量控制要求：**
                - time_value必须是正整数或0.5（半小时情况）
                - time_unit必须是"分钟"、"小时"、"天"、"今天具体时间"、"明天具体时间"、"后天具体时间"之一
                - task必须去除所有时间相关词汇，保留核心任务内容
                - confidence必须基于识别确定性给出0.7-1.0的评分
                
                **输出格式（严格JSON）：**
                如果是设置提醒（具体时间点）：
                {{
                    "intent": "set_reminder",
                    "task": "核心任务内容",
                    "time_value": 小时数(0-23),
                    "time_unit": "今天具体时间|明天具体时间|后天具体时间",
                    "hour": 小时数(0-23),
                    "minute": 分钟数(0-59),
                    "confidence": 置信度数字
                }}
                
                如果是设置提醒（相对时间）：
                {{
                    "intent": "set_reminder",
                    "task": "核心任务内容",
                    "time_value": 数字,
                    "time_unit": "分钟|小时|天",
                    "confidence": 置信度数字
                }}
                
                如果不是设置提醒：
                {{
                    "intent": "other",
                    "message": "用户原始内容",
                    "confidence": 0.9
                }}
                
                **用户语音内容：**"{text}"
                
                请严格按照JSON格式返回，不要添加任何解释文字。
                """
                
                response = self.openai_client.chat.completions.create(
                    model=DEEPSEEK_MODEL,
                    messages=[
                        {"role": "system", "content": "你是一个高精度的语音助手，专门解析老年人的提醒需求。必须严格按照JSON格式输出。"},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=300,
                    temperature=0.05,  # 降低随机性，提高一致性
                    top_p=0.9
                )
                
                result_text = response.choices[0].message.content.strip()
                self.logger.info(f"LLM解析结果 (尝试 {attempt + 1}): {result_text}")
                
                # 清理可能的格式问题
                result_text = self._clean_json_response(result_text)
                
                # 解析JSON
                result = json.loads(result_text)
                
                # 验证结果完整性和合理性
                if self._validate_parse_result(result, text):
                    self.logger.info(f"LLM语义识别成功: {result}")
                    return result
                else:
                    self.logger.warning(f"解析结果验证失败，尝试重试 (尝试 {attempt + 1})")
                    continue
                    
            except json.JSONDecodeError as e:
                self.logger.error(f"JSON解析失败 (尝试 {attempt + 1}): {e}, 原始响应: {result_text if 'result_text' in locals() else 'N/A'}")
                if attempt == max_retries - 1:
                    return self._fallback_parse(text)
                continue
            except Exception as e:
                self.logger.error(f"意图解析失败 (尝试 {attempt + 1}): {e}")
                if attempt == max_retries - 1:
                    return self._fallback_parse(text)
                continue
        
        # 所有重试都失败，返回降级解析结果
        return self._fallback_parse(text)
    
    def _clean_json_response(self, response_text: str) -> str:
        """清理LLM响应中的格式问题"""
        # 移除可能的markdown代码块标记
        response_text = response_text.replace('```json', '').replace('```', '')
        # 移除前后空白字符
        response_text = response_text.strip()
        # 确保只保留JSON部分
        if '{' in response_text and '}' in response_text:
            start = response_text.find('{')
            end = response_text.rfind('}') + 1
            response_text = response_text[start:end]
        return response_text
    
    def _validate_parse_result(self, result: Dict, original_text: str) -> bool:
        """验证解析结果的完整性和合理性"""
        try:
            # 检查必需字段
            if 'intent' not in result or 'confidence' not in result:
                return False
            
            # 检查置信度范围
            confidence = result.get('confidence', 0)
            if not isinstance(confidence, (int, float)) or confidence < 0.7 or confidence > 1.0:
                return False
            
            # 如果是设置提醒，检查必需字段
            if result['intent'] == 'set_reminder':
                required_fields = ['task', 'time_value', 'time_unit']
                for field in required_fields:
                    if field not in result:
                        return False
                
                # 验证时间值
                time_value = result.get('time_value')
                if not isinstance(time_value, (int, float)) or time_value < 0:
                    return False
                
                # 验证时间单位
                time_unit = result.get('time_unit')
                valid_time_units = ['分钟', '小时', '天', '今天具体时间', '明天具体时间', '后天具体时间']
                if time_unit not in valid_time_units:
                    return False
                
                # 对于具体时间，验证hour和minute字段
                if '具体时间' in time_unit:
                    hour = result.get('hour')
                    if hour is None or not isinstance(hour, int) or hour < 0 or hour > 23:
                        return False
                    
                    minute = result.get('minute', 0)  # 默认为0分钟
                    if not isinstance(minute, int) or minute < 0 or minute > 59:
                        return False
                
                # 验证任务内容
                task = result.get('task', '').strip()
                if not task or len(task) < 1:
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"结果验证异常: {e}")
            return False
    
    def _fallback_parse(self, text: str) -> Optional[Dict]:
        """降级解析方案 - 基于关键词的简单解析"""
        try:
            self.logger.info("启用降级解析方案")
            
            # 检查是否包含提醒关键词（包括子女关怀表达）
            reminder_keywords = ['提醒', '记得', '别忘', '到时候', '时间到', '叫我', '通知我', '叫', '通知', '告诉']
            # 子女关怀表达模式
            care_patterns = ['妈妈记得', '爸爸记得', '妈妈别忘', '爸爸别忘', '妈妈要', '爸爸要', '记得要', '别忘了']
            
            is_reminder = any(keyword in text for keyword in reminder_keywords) or any(pattern in text for pattern in care_patterns)
            
            if not is_reminder:
                return {
                    'intent': 'other',
                    'message': text,
                    'confidence': 0.8
                }
            
            # 简单的时间和任务提取
            import re
            
            time_value = 30  # 默认30分钟
            time_unit = '分钟'
            hour = None
            minute = None
            
            # 优先检查具体时间点（包含分钟）
            specific_time_patterns = [
                (r'明天.*?(\d+):(\d+)', 'tomorrow_hour_minute'),  # 明天17:30
                (r'明天.*?(\d+)点(\d+)分', 'tomorrow_hour_minute'),  # 明天17点30分
                (r'明天.*?(\d+)点半', 'tomorrow_hour_half'),  # 明天17点半
                (r'明天.*?(\d+)点', 'tomorrow_hour'),  # 明天17点
                (r'明天.*?([上下])午.*?(\d+):(\d+)', 'tomorrow_specific_minute'),  # 明天下午3:30
                (r'明天.*?([上下])午.*?(\d+)点(\d+)分', 'tomorrow_specific_minute'),  # 明天下午3点30分
                (r'明天.*?([上下])午.*?(\d+)点半', 'tomorrow_specific_half'),  # 明天下午3点半
                (r'明天.*?([上下])午.*?(\d+)点', 'tomorrow_specific'),
                (r'明天.*?(早上|晚上)', 'tomorrow_period'),
                (r'后天.*?(\d+):(\d+)', 'day_after_tomorrow_hour_minute'),  # 后天17:30
                (r'后天.*?(\d+)点(\d+)分', 'day_after_tomorrow_hour_minute'),  # 后天17点30分
                (r'后天.*?(\d+)点半', 'day_after_tomorrow_hour_half'),  # 后天17点半
                (r'后天.*?(\d+)点', 'day_after_tomorrow_hour'),  # 后天17点
                (r'后天.*?([上下])午.*?(\d+):(\d+)', 'day_after_tomorrow_specific_minute'),
                (r'后天.*?([上下])午.*?(\d+)点(\d+)分', 'day_after_tomorrow_specific_minute'),
                (r'后天.*?([上下])午.*?(\d+)点半', 'day_after_tomorrow_specific_half'),
                (r'后天.*?([上下])午.*?(\d+)点', 'day_after_tomorrow_specific'),
                (r'今天.*?(\d+):(\d+)', 'today_hour_minute'),  # 今天17:30
                (r'今天.*?(\d+)点(\d+)分', 'today_hour_minute'),  # 今天17点30分
                (r'今天.*?(\d+)点半', 'today_hour_half'),  # 今天17点半
                (r'今天.*?(\d+)点', 'today_hour'),  # 今天17点
                (r'今天.*?([上下])午.*?(\d+):(\d+)', 'today_specific_minute'),
                (r'今天.*?([上下])午.*?(\d+)点(\d+)分', 'today_specific_minute'),
                (r'今天.*?([上下])午.*?(\d+)点半', 'today_specific_half'),
                (r'今天.*?([上下])午.*?(\d+)点', 'today_specific'),
                (r'今天.*?(晚上|早上)', 'today_period')
            ]
            
            found_specific = False
            for pattern, time_type in specific_time_patterns:
                match = re.search(pattern, text)
                if match:
                    found_specific = True
                    
                    if 'hour_minute' in time_type:  # 处理带分钟的时间（如"17:30"或"17点30分"）
                        hour_num = int(match.group(1))
                        minute_num = int(match.group(2))
                        hour = hour_num if 0 <= hour_num <= 23 else 12
                        minute = minute_num if 0 <= minute_num <= 59 else 0
                        
                        if 'tomorrow' in time_type:
                            time_unit = '明天具体时间'
                        elif 'day_after_tomorrow' in time_type:
                            time_unit = '后天具体时间'
                        elif 'today' in time_type:
                            time_unit = '今天具体时间'
                        time_value = hour
                        
                    elif 'hour_half' in time_type:  # 处理"点半"时间（如"17点半"）
                        hour_num = int(match.group(1))
                        hour = hour_num if 0 <= hour_num <= 23 else 12
                        minute = 30
                        
                        if 'tomorrow' in time_type:
                            time_unit = '明天具体时间'
                        elif 'day_after_tomorrow' in time_type:
                            time_unit = '后天具体时间'
                        elif 'today' in time_type:
                            time_unit = '今天具体时间'
                        time_value = hour
                        
                    elif 'specific_minute' in time_type:  # 处理上午/下午带分钟时间
                        period = match.group(1)
                        hour_num = int(match.group(2))
                        minute_num = int(match.group(3))
                        
                        # 转换为24小时制
                        if period == '下' and hour_num != 12:
                            hour = hour_num + 12
                        elif period == '上' and hour_num == 12:
                            hour = 0
                        else:
                            hour = hour_num
                        minute = minute_num if 0 <= minute_num <= 59 else 0
                            
                        if 'tomorrow' in time_type:
                            time_unit = '明天具体时间'
                        elif 'day_after_tomorrow' in time_type:
                            time_unit = '后天具体时间'
                        elif 'today' in time_type:
                            time_unit = '今天具体时间'
                        time_value = hour
                        
                    elif 'specific_half' in time_type:  # 处理上午/下午"点半"时间
                        period = match.group(1)
                        hour_num = int(match.group(2))
                        
                        # 转换为24小时制
                        if period == '下' and hour_num != 12:
                            hour = hour_num + 12
                        elif period == '上' and hour_num == 12:
                            hour = 0
                        else:
                            hour = hour_num
                        minute = 30
                            
                        if 'tomorrow' in time_type:
                            time_unit = '明天具体时间'
                        elif 'day_after_tomorrow' in time_type:
                            time_unit = '后天具体时间'
                        elif 'today' in time_type:
                            time_unit = '今天具体时间'
                        time_value = hour
                        
                    elif 'hour' in time_type and 'hour_' not in time_type:  # 处理24小时制时间（如"明天17点"）
                        hour_num = int(match.group(1))
                        hour = hour_num if 0 <= hour_num <= 23 else 12  # 验证小时范围
                        minute = 0
                        
                        if 'tomorrow' in time_type:
                            time_unit = '明天具体时间'
                        elif 'day_after_tomorrow' in time_type:
                            time_unit = '后天具体时间'
                        elif 'today' in time_type:
                            time_unit = '今天具体时间'
                        time_value = hour
                        
                    elif 'specific' in time_type and 'specific_' not in time_type:  # 处理上午/下午时间
                        period = match.group(1) if len(match.groups()) >= 1 else ''
                        hour_num = int(match.group(2)) if len(match.groups()) >= 2 else 12
                        
                        # 转换为24小时制
                        if period == '下' and hour_num != 12:
                            hour = hour_num + 12
                        elif period == '上' and hour_num == 12:
                            hour = 0
                        else:
                            hour = hour_num
                        minute = 0
                            
                        if 'tomorrow' in time_type:
                            time_unit = '明天具体时间'
                        elif 'day_after_tomorrow' in time_type:
                            time_unit = '后天具体时间'
                        elif 'today' in time_type:
                            time_unit = '今天具体时间'
                        time_value = hour
                        
                    elif 'period' in time_type:  # 处理早上/晚上时间段
                        period = match.group(1)
                        if period == '早上':
                            hour = 8
                        elif period == '晚上':
                            hour = 19
                        minute = 0
                        
                        if 'tomorrow' in time_type:
                            time_unit = '明天具体时间'
                        elif 'today' in time_type:
                            time_unit = '今天具体时间'
                        time_value = hour
                    break
            
            # 如果没有找到具体时间，使用相对时间模式
            if not found_specific:
                relative_time_patterns = [
                    (r'(\d+)分钟', 'minutes'),
                    (r'(\d+)小时', 'hours'),
                    (r'(\d+)天', 'days'),
                    (r'明天', 'tomorrow'),
                    (r'后天', 'day_after_tomorrow')
                ]
                
                for pattern, time_type in relative_time_patterns:
                    match = re.search(pattern, text)
                    if match:
                        if time_type == 'minutes':
                            time_value = int(match.group(1))
                            time_unit = '分钟'
                        elif time_type == 'hours':
                            time_value = int(match.group(1))
                            time_unit = '小时'
                        elif time_type == 'days':
                            time_value = int(match.group(1))
                            time_unit = '天'
                        elif time_type == 'tomorrow':
                            time_value = 1
                            time_unit = '天'
                        elif time_type == 'day_after_tomorrow':
                            time_value = 2
                            time_unit = '天'
                        break
            
            # 提取任务内容
            task = self._extract_task_from_text(text)
            
            result = {
                'intent': 'set_reminder',
                'task': task,
                'time_value': time_value,
                'time_unit': time_unit,
                'confidence': 0.75  # 降级方案的置信度较低
            }
            
            # 如果是具体时间，添加hour和minute字段
            if hour is not None:
                result['hour'] = hour
            if minute is not None:
                result['minute'] = minute
                
            return result
            
        except Exception as e:
            self.logger.error(f"降级解析失败: {e}")
            return None
    
    def _extract_task_from_text(self, text: str) -> str:
        """从文本中提取任务描述 - 使用优化的文本处理，支持子女关怀消息"""
        try:
            # 过滤掉时间相关的词汇和提醒关键词
            filter_words = ['提醒', '我', '记得', '别忘', '到时候', '时间到', '明天', '后天', '今天', 
                          '上午', '下午', '中午', '晚上', '早上', '傍晚', '点', '分钟', '小时', '天',
                          '一', '二', '三', '四', '五', '六', '七', '八', '九', '十', '半',
                          '后', '前', '钟', '个', '的', '了', '要', '去', '来', '叫', '通知', '告诉']
            
            # 子女关怀表达的过滤词汇
            care_filter_words = ['妈妈', '爸爸', '爷爷', '奶奶', '您', '你']
            
            # 移除过滤词汇
            result_text = text
            for filter_word in filter_words + care_filter_words:
                result_text = result_text.replace(filter_word, '')
            
            # 清理空格和标点
            result_text = result_text.strip().replace(' ', '')
            
            # 如果结果为空或太短，尝试更智能的提取
            if not result_text or len(result_text) < 2:
                # 尝试提取核心动作词汇
                import re
                action_patterns = [
                    r'(吃药|服药|用药)',
                    r'(看医生|去医院|体检|检查)',
                    r'(买菜|购物|买)',
                    r'(做饭|煮饭|烧饭)',
                    r'(锻炼|运动|散步)',
                    r'(喝水|补水)',
                    r'(休息|睡觉)',
                    r'(洗澡|洗头)',
                    r'(打电话|联系)',
                    r'([\u4e00-\u9fa5]{2,})'  # 匹配2个以上的中文字符
                ]
                
                for pattern in action_patterns:
                    match = re.search(pattern, text)
                    if match:
                        result_text = match.group(1)
                        break
                
                # 如果还是没有找到，返回默认值
                if not result_text or len(result_text) < 2:
                    return "重要事项"
            
            return result_text
                
        except Exception as e:
            self.logger.error(f"任务提取失败: {e}")
            return "重要事项"
    
    def calculate_reminder_time(self, time_value: int, time_unit: str, hour: int = None, minute: int = None) -> datetime:
        """计算提醒时间 - 支持具体时间点和相对时间"""
        now = datetime.now()
        
        # 处理具体时间点
        if "具体时间" in time_unit:
            target_hour = hour if hour is not None else time_value
            target_minute = minute if minute is not None else 0
            
            if "今天具体时间" in time_unit:
                # 智能匹配最近的时间点
                target_time = self._find_nearest_time(now, target_hour, target_minute)
                return target_time
                
            elif "明天具体时间" in time_unit:
                # 明天的具体时间
                target_time = now.replace(hour=target_hour, minute=target_minute, second=0, microsecond=0)
                return target_time + timedelta(days=1)
                
            elif "后天具体时间" in time_unit:
                # 后天的具体时间
                target_time = now.replace(hour=target_hour, minute=target_minute, second=0, microsecond=0)
                return target_time + timedelta(days=2)
        
        # 处理相对时间（原有逻辑）
        if time_unit in ['分钟', '分']:
            return now + timedelta(minutes=time_value)
        elif time_unit in ['小时', '时']:
            return now + timedelta(hours=time_value)
        elif time_unit in ['天', '日']:
            return now + timedelta(days=time_value)
        else:
            # 默认按分钟处理
            return now + timedelta(minutes=time_value)
    
    def _find_nearest_time(self, now: datetime, target_hour: int, target_minute: int = 0) -> datetime:
        """智能匹配最近的时间点
        
        规则：
        - 如果目标时间是12小时制（1-12点），智能选择上午或下午
        - 如果目标时间是24小时制（13-23点），直接使用
        - 选择离当前时间最近的那个时间点
        """
        # 如果是24小时制时间（13-23点），直接使用
        if target_hour >= 13:
            target_time = now.replace(hour=target_hour, minute=target_minute, second=0, microsecond=0)
            # 如果时间已过，设置为明天同一时间
            if target_time <= now:
                target_time += timedelta(days=1)
            return target_time
        
        # 12小时制时间（1-12点），需要智能选择上午或下午
        if target_hour == 12:
            # 12点特殊处理：12点是中午，0点是午夜
            am_time = now.replace(hour=0, minute=target_minute, second=0, microsecond=0)  # 午夜12点
            pm_time = now.replace(hour=12, minute=target_minute, second=0, microsecond=0)  # 中午12点
        else:
            # 1-11点：上午和下午两个选择
            am_time = now.replace(hour=target_hour, minute=target_minute, second=0, microsecond=0)
            pm_time = now.replace(hour=target_hour + 12, minute=target_minute, second=0, microsecond=0)
        
        # 如果上午时间已过，移到明天
        if am_time <= now:
            am_time += timedelta(days=1)
        
        # 如果下午时间已过，移到明天
        if pm_time <= now:
            pm_time += timedelta(days=1)
        
        # 选择离当前时间最近的那个
        am_diff = (am_time - now).total_seconds()
        pm_diff = (pm_time - now).total_seconds()
        
        if am_diff <= pm_diff:
            return am_time
        else:
            return pm_time
    
    def format_confirmation(self, task: str, reminder_time: datetime) -> str:
        """格式化确认消息"""
        now = datetime.now()
        
        # 判断是今天、明天还是后天
        if reminder_time.date() == now.date():
            day_str = "今天"
        elif reminder_time.date() == (now + timedelta(days=1)).date():
            day_str = "明天"
        elif reminder_time.date() == (now + timedelta(days=2)).date():
            day_str = "后天"
        else:
            day_str = reminder_time.strftime("%m月%d日")
        
        time_str = reminder_time.strftime("%H:%M")
        return f"好的，我会在{day_str}{time_str}提醒您{task}。"
    
    def process_voice_command(self) -> Optional[Dict]:
        """处理完整的语音命令流程"""
        # 1. 监听语音
        text = self.listen_for_speech()
        if not text:
            return None

        # 2. 解析意图
        intent_result = self.parse_intent(text)
        if not intent_result:
            self.speak("抱歉，我没有理解您的意思，请再说一遍。")
            return None

        # 3. 处理不同意图
        if intent_result['intent'] == 'set_reminder':
            try:
                # 计算提醒时间
                reminder_time = self.calculate_reminder_time(
                    intent_result['time_value'],
                    intent_result['time_unit'],
                    intent_result.get('hour'),  # 传递具体小时数
                    intent_result.get('minute')  # 传递具体分钟数
                )
                
                # 构建提醒信息
                reminder_info = {
                    'task': intent_result['task'],
                    'time': reminder_time,
                    'original_text': text
                }
                
                # 语音确认
                confirmation = self.format_confirmation(
                    intent_result['task'], 
                    reminder_time
                )
                self.speak(confirmation)
                
                return {
                    'type': 'reminder',
                    'data': reminder_info
                }
                
            except Exception as e:
                self.logger.error(f"处理提醒设置失败: {e}")
                self.speak("抱歉，设置提醒时出现了问题。")
                return None
        
        else:
            # 其他类型的对话
            self.speak("我主要负责帮您设置提醒，请告诉我需要提醒什么事情。")
            return {
                'type': 'chat',
                'data': {'message': intent_result.get('message', text)}
            }
    
    def process_child_message(self, message: str, sender: str = "子女") -> Optional[Dict]:
        """处理子女发送的消息，识别是否包含时间提醒项目"""
        try:
            self.logger.info(f"处理来自{sender}的消息: {message}")
            
            # 解析消息中的提醒意图
            intent_result = self.parse_intent(message)
            
            if intent_result and intent_result['intent'] == 'set_reminder':
                # 消息中包含提醒项目
                try:
                    # 计算提醒时间
                    reminder_time = self.calculate_reminder_time(
                        intent_result['time_value'],
                        intent_result['time_unit'],
                        intent_result.get('hour'),
                        intent_result.get('minute')
                    )
                    
                    # 构建提醒信息
                    reminder_info = {
                        'task': intent_result['task'],
                        'time': reminder_time,
                        'original_text': message,
                        'sender': sender
                    }
                    
                    # 语音确认并重复一遍
                    confirmation = self.format_confirmation(
                        intent_result['task'], 
                        reminder_time
                    )
                    repeat_message = f"收到{sender}的提醒消息：{intent_result['task']}。{confirmation}"
                    self.speak(repeat_message)
                    
                    self.logger.info(f"从{sender}消息中成功提取提醒: {intent_result['task']}")
                    
                    return {
                        'type': 'reminder',
                        'data': reminder_info,
                        'source': 'child_message'
                    }
                    
                except Exception as e:
                    self.logger.error(f"处理{sender}消息中的提醒失败: {e}")
                    error_message = f"收到{sender}的消息，但设置提醒时出现了问题。"
                    self.speak(error_message)
                    return None
            else:
                # 普通消息，没有提醒内容
                normal_message = f"收到{sender}的消息：{message}"
                self.speak(normal_message)
                
                return {
                    'type': 'message',
                    'data': {
                        'message': message,
                        'sender': sender,
                        'processed_message': normal_message
                    },
                    'source': 'child_message'
                }
                
        except Exception as e:
            self.logger.error(f"处理{sender}消息失败: {e}")
            return None

if __name__ == "__main__":
    # 测试代码
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    logging.basicConfig(level=logging.INFO)
    
    assistant = VoiceAssistant()
    print("语音助手已启动，请说话...")
    
    result = assistant.process_voice_command()
    if result:
        print(f"处理结果: {result}")