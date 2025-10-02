"""
WebSocket 日志流处理
"""
from flask_socketio import emit, join_room, leave_room
import subprocess
import threading
import time
import os

def init_socketio(socketio):
    """初始化 WebSocket 事件处理"""

    @socketio.on('connect')
    def handle_connect():
        """客户端连接"""
        print(f'Client connected')
        emit('connected', {'message': 'Connected to Staker Agent'})

    @socketio.on('disconnect')
    def handle_disconnect():
        """客户端断开"""
        print(f'Client disconnected')

    @socketio.on('subscribe_logs')
    def handle_subscribe_logs(data):
        """订阅日志流"""
        service = data.get('service', 'consensus')
        room = f'logs_{service}'

        join_room(room)
        print(f'Client subscribed to {service} logs')

        # 启动日志流线程
        thread = threading.Thread(
            target=stream_logs,
            args=(socketio, service, room)
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

def stream_logs(socketio, service, room):
    """流式输出日志"""
    eth_docker_path = os.path.expanduser('~/eth-docker')

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
