"""
Environment check API - Thin wrapper around SystemChecker
No business logic, just API translation.
"""
from flask import Blueprint, jsonify
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from core.system_checker import SystemChecker

env_bp = Blueprint('env', __name__)


@env_bp.route('/check', methods=['GET'])
def check_environment():
    """
    Check system environment.
    Uses SystemChecker - single source of truth.
    """
    try:
        # Get all check results
        results = SystemChecker.run_all_checks()

        # Convert to API format
        data = {
            'os': results['os'].to_dict(),
            'python': results['python'].to_dict(),
            'docker': results['docker'].to_dict(),
            'disk': results['disk_space'].to_dict(),
            'network': results['network'].to_dict()
        }

        # Check if all critical requirements passed
        all_passed = all([
            results['os'].passed,
            results['python'].passed,
            results['docker'].passed,
            results['network'].passed
        ])

        return jsonify({
            'success': True,
            'data': data,
            'all_passed': all_passed
        })

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
