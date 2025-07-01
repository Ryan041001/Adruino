# -*- coding: utf-8 -*-
"""
科大讯飞语音合成模块
"""

import websocket
import datetime
import hashlib
import base64
import hmac
import json
from urllib.parse import urlencode
import time
import ssl
from wsgiref.handlers import format_date_time
from datetime import datetime
from time import mktime
import _thread as thread
import logging
import tempfile
import os

STATUS_FIRST_FRAME = 0  # 第一帧的标识
STATUS_CONTINUE_FRAME = 1  # 中间帧标识
STATUS_LAST_FRAME = 2  # 最后一帧的标识

class XunfeiTTS:
    def __init__(self, app_id, api_key, api_secret):
        self.app_id = app_id
        self.api_key = api_key
        self.api_secret = api_secret
        self.logger = logging.getLogger(__name__)
        self.audio_data = b''
        self.synthesis_complete = False
        
    def create_url(self):
        """生成WebSocket连接URL"""
        url = 'wss://tts-api.xfyun.cn/v2/tts'
        # 生成RFC1123格式的时间戳
        now = datetime.now()
        date = format_date_time(mktime(now.timetuple()))

        # 拼接字符串
        signature_origin = "host: " + "tts-api.xfyun.cn" + "\n"
        signature_origin += "date: " + date + "\n"
        signature_origin += "GET " + "/v2/tts " + "HTTP/1.1"
        
        # 进行hmac-sha256进行加密
        signature_sha = hmac.new(self.api_secret.encode('utf-8'), 
                               signature_origin.encode('utf-8'),
                               digestmod=hashlib.sha256).digest()
        signature_sha = base64.b64encode(signature_sha).decode(encoding='utf-8')

        authorization_origin = f'api_key="{self.api_key}", algorithm="hmac-sha256", headers="host date request-line", signature="{signature_sha}"'
        authorization = base64.b64encode(authorization_origin.encode('utf-8')).decode(encoding='utf-8')
        
        # 将请求的鉴权参数组合为字典
        v = {
            "authorization": authorization,
            "date": date,
            "host": "tts-api.xfyun.cn"
        }
        # 拼接鉴权参数，生成url
        url = url + '?' + urlencode(v)
        return url

    def on_message(self, ws, message):
        """收到websocket消息的处理"""
        try:
            message = json.loads(message)
            code = message["code"]
            sid = message["sid"]
            audio = message.get("data", {}).get("audio", "")
            status = message.get("data", {}).get("status", 0)
            
            self.logger.debug(f"收到消息: code={code}, sid={sid}, status={status}, audio_length={len(audio) if audio else 0}")
            
            if code != 0:
                errMsg = message["message"]
                self.logger.error(f"科大讯飞TTS错误: {code}, {errMsg}")
                self.synthesis_complete = True
                ws.close()
                return
                
            if audio:
                try:
                    audio_data = base64.b64decode(audio)
                    self.audio_data += audio_data
                    self.logger.debug(f"累积音频数据: {len(self.audio_data)} bytes")
                except Exception as decode_error:
                    self.logger.error(f"音频数据解码失败: {decode_error}")
                    self.synthesis_complete = True
                    ws.close()
                    return
            else:
                self.logger.debug("收到空音频数据")
                
            if status == 2:
                # 合成完成
                self.logger.info(f"语音合成完成，总音频数据: {len(self.audio_data)} bytes")
                self.synthesis_complete = True
                ws.close()
                
        except Exception as e:
            self.logger.error(f"处理消息时出错: {e}")
            ws.close()

    def on_error(self, ws, error):
        """连接错误"""
        self.logger.error(f"WebSocket错误: {error}")
        self.synthesis_complete = True

    def on_close(self, ws, close_status_code, close_msg):
        """连接关闭"""
        self.logger.info("WebSocket连接已关闭")
        self.synthesis_complete = True

    def on_open(self, ws):
        """连接建立后发送数据"""
        def run(*args):
            d = {
                "common": {"app_id": self.app_id},
                "business": self.business_args,
                "data": self.data_args
            }
            d = json.dumps(d)
            ws.send(d)
            
        thread.start_new_thread(run, ())

    def synthesis(self, text, voice='xiaoyan', speed=50, pitch=50, volume=50):
        """语音合成"""
        try:
            self.logger.info(f"开始语音合成: {text}")
            self.audio_data = b''
            self.synthesis_complete = False
            
            # 业务参数
            self.business_args = {
                "aue": "lame",  # 音频编码格式
                "sfl": 1,       # 是否流式返回
                "auf": "audio/L16;rate=16000",  # 音频采样率
                "vcn": voice,   # 发音人
                "speed": speed, # 语速
                "pitch": pitch, # 音调
                "volume": volume, # 音量
                "tte": "utf8"   # 文本编码格式
            }
            
            # 数据参数
            self.data_args = {
                "status": 2,
                "text": str(base64.b64encode(text.encode('utf-8')), "UTF8")
            }
            
            # 创建WebSocket连接
            ws_url = self.create_url()
            self.logger.debug(f"WebSocket URL: {ws_url[:100]}...")
            
            ws = websocket.WebSocketApp(ws_url, 
                                      on_message=self.on_message, 
                                      on_error=self.on_error, 
                                      on_close=self.on_close)
            ws.on_open = self.on_open
            
            # 使用线程运行WebSocket连接
            import threading
            ws_thread = threading.Thread(target=lambda: ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE}))
            ws_thread.daemon = True
            ws_thread.start()
            
            # 等待合成完成
            timeout = 30  # 30秒超时
            start_time = time.time()
            while not self.synthesis_complete and (time.time() - start_time) < timeout:
                time.sleep(0.1)
                
            # 确保WebSocket连接关闭
            try:
                ws.close()
            except:
                pass
                
            elapsed_time = time.time() - start_time
            self.logger.info(f"语音合成耗时: {elapsed_time:.2f}秒")
                
            if not self.synthesis_complete:
                raise Exception(f"语音合成超时 ({elapsed_time:.2f}秒)")
                
            if not self.audio_data:
                raise Exception("未获取到音频数据")
                
            self.logger.info(f"语音合成成功，音频数据大小: {len(self.audio_data)} bytes")
                
            # 保存音频到临时文件
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
            temp_file.write(self.audio_data)
            temp_file.close()
            
            self.logger.info(f"音频文件保存到: {temp_file.name}")
            return temp_file.name
            
        except Exception as e:
            self.logger.error(f"科大讯飞语音合成失败: {e}")
            return None