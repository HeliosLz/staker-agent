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
        checker.check_os()
        checker.check_python()
        checker.check_docker()
        checker.check_disk_space()
        checker.check_network()

        # 从 checker.checks 获取结果
        checks = checker.checks

        # 汇总结果
        results = {
            'os': {
                'name': checks.get('os', {}).get('name', 'Unknown'),
                'supported': checks.get('os', {}).get('supported', False),
                'status': checks.get('os', {}).get('status', '❌')
            },
            'python': {
                'name': checks.get('python', {}).get('name', 'Unknown'),
                'supported': checks.get('python', {}).get('supported', False),
                'status': checks.get('python', {}).get('status', '❌')
            },
            'docker': {
                'name': checks.get('docker', {}).get('name', 'Docker'),
                'supported': checks.get('docker', {}).get('supported', False),
                'status': checks.get('docker', {}).get('status', '❌')
            },
            'disk': {
                'name': checks.get('disk_space', {}).get('name', 'Disk Space'),
                'supported': checks.get('disk_space', {}).get('supported', False),
                'status': checks.get('disk_space', {}).get('status', '❌')
            },
            'network': {
                'name': checks.get('network', {}).get('name', 'Network'),
                'supported': checks.get('network', {}).get('supported', False),
                'status': checks.get('network', {}).get('status', '❌')
            }
        }

        # 判断整体状态
        all_checks_passed = all([
            checks.get('os', {}).get('supported', False),
            checks.get('python', {}).get('supported', False),
            checks.get('docker', {}).get('supported', False),
            checks.get('disk_space', {}).get('supported', False),
            checks.get('network', {}).get('supported', False)
        ])

        return jsonify({
            'success': True,
            'data': results,
            'all_passed': all_checks_passed
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
