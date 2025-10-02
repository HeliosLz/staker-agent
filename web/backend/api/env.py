"""
环境检测 API
"""
from flask import Blueprint, jsonify
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from core.env_checker import EnvChecker

env_bp = Blueprint('env', __name__)

@env_bp.route('/check', methods=['GET'])
def check_environment():
    """
    检查系统环境
    GET /api/env/check
    """
    try:
        checker = EnvChecker()

        # 执行所有检查
        os_info = checker.check_os()
        python_info = checker.check_python()
        docker_info = checker.check_docker()
        disk_info = checker.check_disk_space()
        network_info = checker.check_network()

        # 汇总结果
        results = {
            'os': {
                'name': os_info.get('name', 'Unknown'),
                'version': os_info.get('version', 'Unknown'),
                'status': os_info.get('status', 'unknown'),
                'message': os_info.get('message', '')
            },
            'python': {
                'version': python_info.get('version', 'Unknown'),
                'status': python_info.get('status', 'unknown'),
                'message': python_info.get('message', '')
            },
            'docker': {
                'installed': docker_info.get('status') == 'success',
                'version': docker_info.get('version', ''),
                'status': docker_info.get('status', 'unknown'),
                'message': docker_info.get('message', '')
            },
            'disk': {
                'available_gb': disk_info.get('available_gb', 0),
                'status': disk_info.get('status', 'unknown'),
                'message': disk_info.get('message', '')
            },
            'network': {
                'connected': network_info.get('status') == 'success',
                'status': network_info.get('status', 'unknown'),
                'message': network_info.get('message', '')
            }
        }

        # 判断整体状态
        all_checks_passed = all([
            os_info.get('status') == 'success',
            python_info.get('status') == 'success',
            docker_info.get('status') == 'success',
            disk_info.get('status') == 'success',
            network_info.get('status') == 'success'
        ])

        return jsonify({
            'success': True,
            'data': results,
            'all_passed': all_checks_passed
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
