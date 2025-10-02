"""
Staker Agent - Flask Backend API Server
提供 REST API 和 WebSocket 服务
"""
import os
import sys
from flask import Flask, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO

# 添加项目根目录到路径,以便导入 core 模块
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# 创建 Flask 应用
app = Flask(__name__)
app.config['SECRET_KEY'] = 'staker-agent-secret-key'

# 配置 CORS
CORS(app, resources={
    r"/api/*": {
        "origins": ["http://localhost:5173", "http://localhost:3000"],
        "methods": ["GET", "POST", "PUT", "DELETE"],
        "allow_headers": ["Content-Type"]
    }
})

# 配置 SocketIO
socketio = SocketIO(
    app,
    cors_allowed_origins=["http://localhost:5173", "http://localhost:3000"]
)

# 导入 API 路由
from api.env import env_bp
from api.config import config_bp
from api.deploy import deploy_bp
from api.status import status_bp

# 注册蓝图
app.register_blueprint(env_bp, url_prefix='/api/env')
app.register_blueprint(config_bp, url_prefix='/api/config')
app.register_blueprint(deploy_bp, url_prefix='/api/deploy')
app.register_blueprint(status_bp, url_prefix='/api/status')

# 导入 WebSocket 事件处理
from websocket import init_socketio

# 初始化 WebSocket
init_socketio(socketio)

# 健康检查
@app.route('/api/health')
def health():
    """API 健康检查"""
    return jsonify({
        'status': 'healthy',
        'message': 'Staker Agent API is running'
    })

# 根路径
@app.route('/')
def index():
    """根路径"""
    return jsonify({
        'name': 'Staker Agent API',
        'version': '0.1.0',
        'endpoints': {
            'health': '/api/health',
            'env_check': '/api/env/check',
            'config_generate': '/api/config/generate',
            'deploy_start': '/api/deploy/start',
            'status': '/api/status'
        }
    })

if __name__ == '__main__':
    print("🚀 Starting Staker Agent API Server...")
    print("📍 URL: http://localhost:5001")
    print("🔌 WebSocket enabled")

    # 使用 socketio 运行（开发模式）
    socketio.run(
        app,
        host='0.0.0.0',
        port=5001,
        debug=True,
        allow_unsafe_werkzeug=True
    )
