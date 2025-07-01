# -*- coding: utf-8 -*-
"""
Web服务器模块 - 提供Web接口接收家庭消息
"""

import logging
import json
from datetime import datetime
from typing import Optional, Callable
from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import threading

from config import WEB_CONFIG

class WebServer:
    """Web服务器类"""
    
    def __init__(self, message_callback: Optional[Callable] = None):
        self.logger = logging.getLogger(__name__)
        self.app = Flask(__name__)
        CORS(self.app)  # 允许跨域请求
        
        self.message_callback = message_callback
        self.server_thread = None
        self.running = False
        
        # 消息历史
        self.message_history = []
        
        # 设置路由
        self._setup_routes()
        
        self.logger.info("Web服务器初始化完成")
    
    def _setup_routes(self):
        """设置路由"""
        
        @self.app.route('/')
        def index():
            """主页"""
            return render_template_string(self._get_html_template())
        
        @self.app.route('/api/send_message', methods=['POST'])
        def send_message():
            """发送消息API"""
            try:
                data = request.get_json()
                
                if not data or 'message' not in data:
                    return jsonify({
                        'success': False,
                        'error': '消息内容不能为空'
                    }), 400
                
                message = data['message'].strip()
                sender = data.get('sender', '家人').strip()
                
                if not message:
                    return jsonify({
                        'success': False,
                        'error': '消息内容不能为空'
                    }), 400
                
                if len(message) > 200:
                    return jsonify({
                        'success': False,
                        'error': '消息长度不能超过200字符'
                    }), 400
                
                # 记录消息
                message_data = {
                    'message': message,
                    'sender': sender,
                    'timestamp': datetime.now().isoformat(),
                    'id': len(self.message_history) + 1
                }
                
                self.message_history.append(message_data)
                
                # 保持历史记录在合理范围内
                if len(self.message_history) > 50:
                    self.message_history = self.message_history[-50:]
                
                self.logger.info(f"收到消息 - 发送者: {sender}, 内容: {message}")
                
                # 调用回调函数
                if self.message_callback:
                    try:
                        self.message_callback(message, sender)
                    except Exception as e:
                        self.logger.error(f"消息回调处理失败: {e}")
                
                return jsonify({
                    'success': True,
                    'message': '消息发送成功',
                    'data': message_data
                })
                
            except Exception as e:
                self.logger.error(f"发送消息失败: {e}")
                return jsonify({
                    'success': False,
                    'error': '服务器内部错误'
                }), 500
        
        @self.app.route('/api/messages', methods=['GET'])
        def get_messages():
            """获取消息历史"""
            try:
                # 获取最近的消息
                limit = request.args.get('limit', 10, type=int)
                limit = min(limit, 50)  # 最多返回50条
                
                recent_messages = self.message_history[-limit:] if self.message_history else []
                
                return jsonify({
                    'success': True,
                    'data': {
                        'messages': recent_messages,
                        'total': len(self.message_history)
                    }
                })
                
            except Exception as e:
                self.logger.error(f"获取消息历史失败: {e}")
                return jsonify({
                    'success': False,
                    'error': '服务器内部错误'
                }), 500
        
        @self.app.route('/api/status', methods=['GET'])
        def get_status():
            """获取系统状态"""
            try:
                return jsonify({
                    'success': True,
                    'data': {
                        'status': 'running',
                        'timestamp': datetime.now().isoformat(),
                        'message_count': len(self.message_history)
                    }
                })
            except Exception as e:
                self.logger.error(f"获取状态失败: {e}")
                return jsonify({
                    'success': False,
                    'error': '服务器内部错误'
                }), 500
        
        @self.app.errorhandler(404)
        def not_found(error):
            return jsonify({
                'success': False,
                'error': '页面未找到'
            }), 404
        
        @self.app.errorhandler(500)
        def internal_error(error):
            return jsonify({
                'success': False,
                'error': '服务器内部错误'
            }), 500
    
    def _get_html_template(self) -> str:
        """获取HTML模板"""
        return """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>语音助手 - 家庭消息</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Microsoft YaHei', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }
        
        .container {
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            padding: 40px;
            max-width: 500px;
            width: 100%;
        }
        
        .header {
            text-align: center;
            margin-bottom: 30px;
        }
        
        .header h1 {
            color: #333;
            font-size: 28px;
            margin-bottom: 10px;
        }
        
        .header p {
            color: #666;
            font-size: 16px;
        }
        
        .form-group {
            margin-bottom: 20px;
        }
        
        label {
            display: block;
            margin-bottom: 8px;
            color: #333;
            font-weight: 500;
        }
        
        input, textarea {
            width: 100%;
            padding: 12px 16px;
            border: 2px solid #e1e5e9;
            border-radius: 10px;
            font-size: 16px;
            transition: border-color 0.3s;
        }
        
        input:focus, textarea:focus {
            outline: none;
            border-color: #667eea;
        }
        
        textarea {
            resize: vertical;
            min-height: 120px;
        }
        
        .btn {
            width: 100%;
            padding: 15px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 10px;
            font-size: 18px;
            font-weight: 500;
            cursor: pointer;
            transition: transform 0.2s;
        }
        
        .btn:hover {
            transform: translateY(-2px);
        }
        
        .btn:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }
        
        .message {
            padding: 12px 16px;
            border-radius: 8px;
            margin-bottom: 15px;
            font-size: 14px;
        }
        
        .message.success {
            background: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }
        
        .message.error {
            background: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }
        
        .char-count {
            text-align: right;
            font-size: 12px;
            color: #666;
            margin-top: 5px;
        }
        
        .status {
            text-align: center;
            margin-top: 20px;
            padding: 10px;
            background: #f8f9fa;
            border-radius: 8px;
            font-size: 14px;
            color: #666;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🏠 家庭消息</h1>
            <p>向语音助手发送消息</p>
        </div>
        
        <form id="messageForm">
            <div class="form-group">
                <label for="sender">发送者姓名:</label>
                <input type="text" id="sender" name="sender" placeholder="请输入您的姓名" maxlength="20" required>
            </div>
            
            <div class="form-group">
                <label for="message">消息内容:</label>
                <textarea id="message" name="message" placeholder="请输入要发送的消息..." maxlength="200" required></textarea>
                <div class="char-count">
                    <span id="charCount">0</span>/200
                </div>
            </div>
            
            <button type="submit" class="btn" id="sendBtn">
                📤 发送消息
            </button>
        </form>
        
        <div id="messageArea"></div>
        
        <div class="status" id="status">
            系统状态: 正常运行
        </div>
    </div>
    
    <script>
        const form = document.getElementById('messageForm');
        const messageArea = document.getElementById('messageArea');
        const sendBtn = document.getElementById('sendBtn');
        const messageInput = document.getElementById('message');
        const charCount = document.getElementById('charCount');
        const statusDiv = document.getElementById('status');
        
        // 字符计数
        messageInput.addEventListener('input', function() {
            const count = this.value.length;
            charCount.textContent = count;
            
            if (count > 180) {
                charCount.style.color = '#dc3545';
            } else if (count > 150) {
                charCount.style.color = '#ffc107';
            } else {
                charCount.style.color = '#666';
            }
        });
        
        // 表单提交
        form.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const formData = new FormData(form);
            const data = {
                sender: formData.get('sender'),
                message: formData.get('message')
            };
            
            if (!data.message.trim()) {
                showMessage('请输入消息内容', 'error');
                return;
            }
            
            sendBtn.disabled = true;
            sendBtn.textContent = '发送中...';
            
            try {
                const response = await fetch('/api/send_message', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(data)
                });
                
                const result = await response.json();
                
                if (result.success) {
                    showMessage('消息发送成功！', 'success');
                    form.reset();
                    charCount.textContent = '0';
                    charCount.style.color = '#666';
                } else {
                    showMessage(result.error || '发送失败', 'error');
                }
            } catch (error) {
                showMessage('网络错误，请检查连接', 'error');
            } finally {
                sendBtn.disabled = false;
                sendBtn.textContent = '📤 发送消息';
            }
        });
        
        function showMessage(text, type) {
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${type}`;
            messageDiv.textContent = text;
            
            messageArea.innerHTML = '';
            messageArea.appendChild(messageDiv);
            
            setTimeout(() => {
                messageDiv.remove();
            }, 5000);
        }
        
        // 定期检查系统状态
        async function checkStatus() {
            try {
                const response = await fetch('/api/status');
                const result = await response.json();
                
                if (result.success) {
                    statusDiv.textContent = `系统状态: 正常运行 | 消息数: ${result.data.message_count}`;
                    statusDiv.style.color = '#28a745';
                } else {
                    statusDiv.textContent = '系统状态: 异常';
                    statusDiv.style.color = '#dc3545';
                }
            } catch (error) {
                statusDiv.textContent = '系统状态: 连接失败';
                statusDiv.style.color = '#dc3545';
            }
        }
        
        // 每30秒检查一次状态
        setInterval(checkStatus, 30000);
        checkStatus();
    </script>
</body>
</html>
        """
    
    def start(self, host: str = None, port: int = None, debug: bool = False):
        """启动Web服务器"""
        if self.running:
            self.logger.warning("Web服务器已在运行")
            return
        
        host = host or WEB_CONFIG['HOST']
        port = port or WEB_CONFIG['PORT']
        debug = debug or WEB_CONFIG['DEBUG']
        
        def run_server():
            try:
                self.logger.info(f"启动Web服务器: http://{host}:{port}")
                self.app.run(host=host, port=port, debug=debug, use_reloader=False)
            except Exception as e:
                self.logger.error(f"Web服务器启动失败: {e}")
        
        self.running = True
        self.server_thread = threading.Thread(target=run_server, daemon=True)
        self.server_thread.start()
        
        self.logger.info("Web服务器启动完成")
    
    def stop(self):
        """停止Web服务器"""
        self.running = False
        # Flask开发服务器没有优雅关闭的方法，在生产环境中应使用WSGI服务器
        self.logger.info("Web服务器停止")
    
    def get_message_history(self, limit: int = 10) -> list:
        """获取消息历史"""
        return self.message_history[-limit:] if self.message_history else []
    
    def clear_message_history(self):
        """清空消息历史"""
        self.message_history.clear()
        self.logger.info("消息历史已清空")

if __name__ == "__main__":
    # 测试代码
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    logging.basicConfig(level=logging.INFO)
    
    def test_message_callback(message, sender):
        print(f"[消息回调] {sender}: {message}")
    
    server = WebServer(test_message_callback)
    
    try:
        server.start(debug=True)
        print("Web服务器已启动，访问 http://localhost:5000")
        
        # 保持运行
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n正在关闭服务器...")
        server.stop()