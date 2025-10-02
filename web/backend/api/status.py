"""
节点状态 API
"""
from flask import Blueprint, jsonify, request
import sys
import os
import subprocess

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from core.status_monitor import StatusMonitor

status_bp = Blueprint('status', __name__)

@status_bp.route('/', methods=['GET'])
def get_status():
    """
    获取节点状态
    GET /api/status
    """
    try:
        monitor = StatusMonitor()
        status = monitor.get_status()

        return jsonify({
            'success': True,
            'data': status
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@status_bp.route('/logs', methods=['GET'])
def get_logs():
    """
    获取节点日志
    GET /api/status/logs?service=consensus&lines=100
    """
    try:
        service = request.args.get('service', 'consensus')
        lines = request.args.get('lines', '100')

        eth_docker_path = os.path.expanduser('~/eth-docker')

        # 获取日志
        result = subprocess.run(
            ['docker', 'compose', 'logs', '--tail', lines, service],
            cwd=eth_docker_path,
            capture_output=True,
            text=True
        )

        return jsonify({
            'success': True,
            'data': {
                'service': service,
                'logs': result.stdout
            }
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@status_bp.route('/start', methods=['POST'])
def start_node():
    """
    启动节点
    POST /api/status/start
    """
    try:
        eth_docker_path = os.path.expanduser('~/eth-docker')

        result = subprocess.run(
            ['docker', 'compose', 'up', '-d'],
            cwd=eth_docker_path,
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            return jsonify({
                'success': False,
                'error': result.stderr
            }), 500

        return jsonify({
            'success': True,
            'data': {
                'message': 'Node started successfully'
            }
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@status_bp.route('/stop', methods=['POST'])
def stop_node():
    """
    停止节点
    POST /api/status/stop
    """
    try:
        eth_docker_path = os.path.expanduser('~/eth-docker')

        result = subprocess.run(
            ['docker', 'compose', 'down'],
            cwd=eth_docker_path,
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            return jsonify({
                'success': False,
                'error': result.stderr
            }), 500

        return jsonify({
            'success': True,
            'data': {
                'message': 'Node stopped successfully'
            }
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@status_bp.route('/restart', methods=['POST'])
def restart_node():
    """
    重启节点
    POST /api/status/restart
    """
    try:
        eth_docker_path = os.path.expanduser('~/eth-docker')

        result = subprocess.run(
            ['docker', 'compose', 'restart'],
            cwd=eth_docker_path,
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            return jsonify({
                'success': False,
                'error': result.stderr
            }), 500

        return jsonify({
            'success': True,
            'data': {
                'message': 'Node restarted successfully'
            }
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
