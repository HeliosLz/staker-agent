"""
部署管理 API
"""
from flask import Blueprint, jsonify, request
import sys
import os
import subprocess

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from core.deploy_manager import DeployManager
from core.key_manager import KeyManager

deploy_bp = Blueprint('deploy', __name__)

@deploy_bp.route('/start', methods=['POST'])
def start_deployment():
    """
    开始部署节点
    POST /api/deploy/start
    """
    try:
        deployer = DeployManager()

        # 执行部署（跳过交互式确认，Web UI 已确认）
        result = deployer.deploy(skip_confirm=True)

        if result:
            return jsonify({
                'success': True,
                'data': {
                    'message': 'Deployment started successfully'
                }
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Deployment failed'
            }), 500

    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f'❌ Deployment error: {error_details}')

        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@deploy_bp.route('/keys/generate', methods=['POST'])
def generate_keys():
    """
    生成验证者密钥
    POST /api/deploy/keys/generate
    Body: {
        "network": "holesky",
        "count": 1,
        "withdrawal_address": "0x..."
    }
    """
    try:
        data = request.get_json()

        network = data.get('network', 'holesky')
        count = data.get('count', 1)
        withdrawal_address = data.get('withdrawal_address')

        if not withdrawal_address:
            return jsonify({
                'success': False,
                'error': 'Missing withdrawal_address'
            }), 400

        key_manager = KeyManager()

        # 生成密钥
        result = key_manager.generate_keys(
            network=network,
            num_validators=count,
            withdrawal_address=withdrawal_address
        )

        return jsonify({
            'success': result.get('status') == 'success',
            'data': result
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@deploy_bp.route('/keys/import', methods=['POST'])
def import_keys():
    """
    导入验证者密钥
    POST /api/deploy/keys/import
    Body: {
        "keys_path": "/path/to/keys"
    }
    """
    try:
        data = request.get_json()

        keys_path = data.get('keys_path')

        if not keys_path:
            return jsonify({
                'success': False,
                'error': 'Missing keys_path'
            }), 400

        key_manager = KeyManager()

        # 导入密钥
        result = key_manager.import_keys(keys_path)

        return jsonify({
            'success': result.get('status') == 'success',
            'data': result
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@deploy_bp.route('/setup', methods=['POST'])
def setup_dependencies():
    """
    安装依赖 (eth-docker)
    POST /api/deploy/setup
    Body: {
        "skip_docker": false
    }
    """
    try:
        data = request.get_json() or {}
        skip_docker = data.get('skip_docker', False)

        # 克隆 eth-docker
        eth_docker_path = os.path.expanduser('~/eth-docker')

        if not os.path.exists(eth_docker_path):
            result = subprocess.run(
                ['git', 'clone', 'https://github.com/eth-educators/eth-docker.git', eth_docker_path],
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                return jsonify({
                    'success': False,
                    'error': f'Failed to clone eth-docker: {result.stderr}'
                }), 500

        return jsonify({
            'success': True,
            'data': {
                'message': 'Dependencies installed successfully',
                'eth_docker_path': eth_docker_path
            }
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
