"""
WebSocket 模块初始化
"""
from .logs import init_socketio as _init_logs_socketio
from .agent import init_agent_socketio as _init_agent_socketio
from .monitor import init_monitor_socketio as _init_monitor_socketio


def init_socketio(socketio):
    """Initialize all WebSocket event handlers."""
    _init_logs_socketio(socketio)
    _init_agent_socketio(socketio)
    _init_monitor_socketio(socketio)
