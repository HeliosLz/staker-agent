"""
WebSocket 事件处理 - 实时进度追踪
"""
from flask_socketio import emit
import threading
import time

def init_socketio(socketio):
    """初始化 WebSocket 事件处理器"""

    @socketio.on('connect')
    def handle_connect():
        """客户端连接"""
        print('🔌 Client connected')
        emit('connected', {'message': 'Connected to Staker Agent'})

    @socketio.on('disconnect')
    def handle_disconnect():
        """客户端断开"""
        print('🔌 Client disconnected')

    @socketio.on('start_deployment')
    def handle_deployment(data):
        """处理部署请求，实时推送进度"""
        print(f'🚀 Starting deployment with data: {data}')

        def run_deployment():
            steps = [
                {'step': 1, 'name': '环境检查', 'message': '正在检查系统环境...', 'progress': 0},
                {'step': 2, 'name': '安装依赖', 'message': '正在安装必要的依赖包...', 'progress': 20},
                {'step': 3, 'name': '生成配置', 'message': '正在生成节点配置文件...', 'progress': 40},
                {'step': 4, 'name': '生成密钥', 'message': '正在生成验证者密钥...', 'progress': 60},
                {'step': 5, 'name': '启动容器', 'message': '正在启动 Docker 容器...', 'progress': 80},
                {'step': 6, 'name': '完成', 'message': '部署完成！', 'progress': 100},
            ]

            for step in steps:
                time.sleep(2)  # 模拟耗时操作
                socketio.emit('deployment_progress', {
                    'step': step['step'],
                    'name': step['name'],
                    'message': step['message'],
                    'progress': step['progress'],
                    'status': 'running' if step['progress'] < 100 else 'completed'
                })

            socketio.emit('deployment_complete', {
                'success': True,
                'message': '验证节点部署成功！'
            })

        # 在后台线程中运行部署
        thread = threading.Thread(target=run_deployment)
        thread.daemon = True
        thread.start()

        return {'status': 'started'}

    @socketio.on('start_docker_install')
    def handle_docker_install(data):
        """处理 Docker 安装，实时推送进度"""
        print(f'🐋 Starting Docker installation: {data}')

        def run_install():
            steps = [
                {'message': '正在检测操作系统...', 'progress': 10},
                {'message': '正在下载 Docker 安装包...', 'progress': 30},
                {'message': '正在安装 Docker...', 'progress': 60},
                {'message': '正在配置 Docker 服务...', 'progress': 80},
                {'message': 'Docker 安装完成！', 'progress': 100},
            ]

            for step in steps:
                time.sleep(1.5)
                socketio.emit('docker_install_progress', {
                    'message': step['message'],
                    'progress': step['progress'],
                    'status': 'running' if step['progress'] < 100 else 'completed'
                })

            socketio.emit('docker_install_complete', {
                'success': True,
                'message': 'Docker 安装成功！请重新检查环境。'
            })

        thread = threading.Thread(target=run_install)
        thread.daemon = True
        thread.start()

        return {'status': 'started'}

    return socketio
