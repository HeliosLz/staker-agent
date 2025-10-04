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

        # 执行所有检查，使用 try-except 保护每个检查
        checks_to_run = [
            ('os', checker.check_os),
            ('python', checker.check_python),
            ('docker', checker.check_docker),
            ('disk_space', checker.check_disk_space),
            ('network', checker.check_network)
        ]

        failed_checks = []
        for check_name, check_func in checks_to_run:
            try:
                check_func()
            except Exception as e:
                failed_checks.append(f'{check_name}: {str(e)}')
                # 添加失败的检查结果
                checker.checks[check_name] = {
                    'name': check_name,
                    'supported': False,
                    'status': '❌',
                    'error': str(e)
                }

        # 从 checker.checks 获取结果
        checks = checker.checks

        # 汇总结果
        results = {
            'os': {
                'name': checks.get('os', {}).get('name', 'Unknown'),
                'supported': checks.get('os', {}).get('supported', False),
                'status': checks.get('os', {}).get('status', '❌'),
                'error': checks.get('os', {}).get('error')
            },
            'python': {
                'name': checks.get('python', {}).get('name', 'Unknown'),
                'supported': checks.get('python', {}).get('supported', False),
                'status': checks.get('python', {}).get('status', '❌'),
                'error': checks.get('python', {}).get('error')
            },
            'docker': {
                'name': checks.get('docker', {}).get('name', 'Docker'),
                'supported': checks.get('docker', {}).get('supported', False),
                'status': checks.get('docker', {}).get('status', '❌'),
                'error': checks.get('docker', {}).get('error')
            },
            'disk': {
                'name': checks.get('disk_space', {}).get('name', 'Disk Space'),
                'supported': checks.get('disk_space', {}).get('supported', False),
                'status': checks.get('disk_space', {}).get('status', '❌'),
                'error': checks.get('disk_space', {}).get('error')
            },
            'network': {
                'name': checks.get('network', {}).get('name', 'Network'),
                'supported': checks.get('network', {}).get('supported', False),
                'status': checks.get('network', {}).get('status', '❌'),
                'error': checks.get('network', {}).get('error')
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

        response = {
            'success': True,
            'data': results,
            'all_passed': all_checks_passed
        }

        # 如果有检查失败，添加警告信息
        if failed_checks:
            response['warnings'] = failed_checks

        return jsonify(response)

    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f'❌ Environment check error: {error_details}')

        return jsonify({
            'success': False,
            'error': '环境检查失败',
            'details': str(e),
            'message': '无法完成环境检查，请确保所有必要的系统工具已安装'
        }), 500
