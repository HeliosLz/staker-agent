"""
WebSocket 日志流处理
"""
from flask_socketio import emit, join_room, leave_room
import subprocess
import threading
import time

from staker_backend.auth import authenticate_socketio

def init_socketio(socketio):
    """初始化 WebSocket 事件处理"""

    @socketio.on('connect')
    def handle_connect(auth=None):
        """客户端连接 — 要求 Bearer token 验证"""
        if not authenticate_socketio(auth):
            return False
        emit('connected', {'message': 'Connected to Staker Agent'})

    @socketio.on('disconnect')
    def handle_disconnect():
        """客户端断开"""
        print(f'Client disconnected')

    @socketio.on('subscribe_logs')
    def handle_subscribe_logs(data):
        """订阅日志流"""
        from flask import current_app
        service = data.get('service', 'consensus')
        room = f'logs_{service}'
        eth_docker_path = current_app.config["ETH_DOCKER_PATH"]

        join_room(room)

        thread = threading.Thread(
            target=stream_logs,
            args=(socketio, service, room, eth_docker_path)
        )
        thread.daemon = True
        thread.start()

        emit('subscribed', {'service': service})

    @socketio.on('unsubscribe_logs')
    def handle_unsubscribe_logs(data):
        """取消订阅日志流"""
        service = data.get('service', 'consensus')
        room = f'logs_{service}'

        leave_room(room)
        print(f'Client unsubscribed from {service} logs')

        emit('unsubscribed', {'service': service})

def stream_logs(socketio, service, room, eth_docker_path):
    """流式输出日志"""
    try:
        # 使用 docker compose logs -f 实时跟踪日志
        process = subprocess.Popen(
            ['docker', 'compose', 'logs', '-f', '--tail', '50', service],
            cwd=eth_docker_path,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )

        for line in process.stdout:
            socketio.emit('log_line', {
                'service': service,
                'line': line.strip()
            }, room=room)

            time.sleep(0.01)  # 避免过快

    except Exception as e:
        socketio.emit('log_error', {
            'service': service,
            'error': str(e)
        }, room=room)

# 导出初始化函数
__all__ = ['init_socketio']
