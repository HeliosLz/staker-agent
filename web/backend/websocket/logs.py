"""
WebSocket 日志流处理
"""
from __future__ import annotations

from flask import request
from flask_socketio import emit, join_room, leave_room
import subprocess
import threading
import time

from core.security import redact_secrets
from staker_backend.auth import authenticate_socketio

# sid -> (Popen | None, stop_event)
# The stop_event is created BEFORE the thread starts, so _kill_stream can
# always signal cancellation even if Popen hasn't been registered yet.
_active_streams: dict[str, tuple[subprocess.Popen | None, threading.Event]] = {}
_streams_lock = threading.Lock()


def _kill_stream(sid: str) -> None:
    with _streams_lock:
        entry = _active_streams.pop(sid, None)
    if entry is None:
        return
    proc, stop_event = entry
    stop_event.set()
    if proc is not None and proc.poll() is None:
        proc.kill()
        proc.wait(timeout=5)


def init_socketio(socketio):
    """初始化 WebSocket 事件处理"""

    @socketio.on('connect')
    def handle_connect(auth=None):
        if not authenticate_socketio(auth):
            return False
        emit('connected', {'message': 'Connected to Staker Agent'})

    @socketio.on('disconnect')
    def handle_disconnect():
        _kill_stream(request.sid)

    @socketio.on('subscribe_logs')
    def handle_subscribe_logs(data):
        from flask import current_app
        sid = request.sid
        service = data.get('service', 'consensus')
        room = f'logs_{service}'
        eth_docker_path = current_app.config["ETH_DOCKER_PATH"]

        _kill_stream(sid)
        join_room(room)

        stop_event = threading.Event()
        with _streams_lock:
            _active_streams[sid] = (None, stop_event)

        thread = threading.Thread(
            target=stream_logs,
            args=(socketio, sid, service, room, eth_docker_path, stop_event),
            daemon=True,
        )
        thread.start()
        emit('subscribed', {'service': service})

    @socketio.on('unsubscribe_logs')
    def handle_unsubscribe_logs(data):
        sid = request.sid
        service = data.get('service', 'consensus')
        room = f'logs_{service}'

        _kill_stream(sid)
        leave_room(room)
        emit('unsubscribed', {'service': service})


def stream_logs(socketio, sid, service, room, eth_docker_path, stop_event: threading.Event):
    process: subprocess.Popen | None = None
    try:
        if stop_event.is_set():
            return

        process = subprocess.Popen(
            ['docker', 'compose', 'logs', '-f', '--tail', '50', service],
            cwd=eth_docker_path,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )

        with _streams_lock:
            if stop_event.is_set():
                # Cancelled between Popen and registration — kill immediately
                process.kill()
                process.wait(timeout=5)
                return
            _active_streams[sid] = (process, stop_event)

        assert process.stdout is not None
        for line in process.stdout:
            if stop_event.is_set() or process.poll() is not None:
                break
            socketio.emit('log_line', {
                'service': service,
                'line': redact_secrets(line.strip()),
            }, room=room)
            time.sleep(0.01)

    except Exception as e:
        socketio.emit('log_error', {
            'service': service,
            'error': redact_secrets(str(e)),
        }, room=room)
    finally:
        with _streams_lock:
            entry = _active_streams.get(sid)
            if entry is not None and entry[1] is stop_event:
                del _active_streams[sid]
        if process is not None and process.poll() is None:
            process.kill()
            process.wait(timeout=5)


__all__ = ['init_socketio']
