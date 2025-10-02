"""
配置生成 API
"""
from flask import Blueprint, jsonify, request
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from core.config_generator import ConfigGenerator

config_bp = Blueprint('config', __name__)

@config_bp.route('/generate', methods=['POST'])
def generate_config():
    """
    生成节点配置
    POST /api/config/generate
    Body: {
        "network": "holesky",
        "client": "lighthouse",
        "fee_recipient": "0x...",  # 可选
        "checkpoint_url": "https://..."  # 可选
    }
    """
    try:
        data = request.get_json()

        # 验证必需参数
        network = data.get('network')
        client = data.get('client')

        if not network or not client:
            return jsonify({
                'success': False,
                'error': 'Missing required parameters: network and client'
            }), 400

        # 验证网络
        valid_networks = ['mainnet', 'holesky', 'hoodi', 'sepolia']
        if network not in valid_networks:
            return jsonify({
                'success': False,
                'error': f'Invalid network. Must be one of: {", ".join(valid_networks)}'
            }), 400

        # 验证客户端
        valid_clients = ['lighthouse', 'prysm', 'teku', 'nimbus']
        if client not in valid_clients:
            return jsonify({
                'success': False,
                'error': f'Invalid client. Must be one of: {", ".join(valid_clients)}'
            }), 400

        # 创建配置生成器
        generator = ConfigGenerator(network, client)

        # 设置可选参数
        if 'fee_recipient' in data:
            generator.set_fee_recipient(data['fee_recipient'])

        if 'checkpoint_url' in data:
            generator.set_checkpoint_sync(data['checkpoint_url'])

        # 生成配置
        config_path = generator.generate()

        # 读取生成的配置
        with open(config_path, 'r') as f:
            config_content = f.read()

        return jsonify({
            'success': True,
            'data': {
                'network': network,
                'client': client,
                'config_path': config_path,
                'config_content': config_content
            }
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@config_bp.route('/networks', methods=['GET'])
def get_networks():
    """
    获取支持的网络列表
    GET /api/config/networks
    """
    networks = [
        {
            'id': 'mainnet',
            'name': 'Mainnet',
            'description': 'Ethereum Mainnet - 真实 ETH',
            'recommended': False
        },
        {
            'id': 'holesky',
            'name': 'Holesky',
            'description': 'Holesky Testnet - 推荐测试网',
            'recommended': True
        },
        {
            'id': 'hoodi',
            'name': 'Hoodi (Lido CSM)',
            'description': 'Lido CSM Testnet - Lido 专用',
            'recommended': False
        },
        {
            'id': 'sepolia',
            'name': 'Sepolia',
            'description': 'Sepolia Testnet - 测试网',
            'recommended': False
        }
    ]

    return jsonify({
        'success': True,
        'data': networks
    })

@config_bp.route('/clients', methods=['GET'])
def get_clients():
    """
    获取支持的客户端列表
    GET /api/config/clients
    """
    clients = [
        {
            'id': 'lighthouse',
            'name': 'Lighthouse',
            'language': 'Rust',
            'description': '性能优秀,资源占用低',
            'recommended': True
        },
        {
            'id': 'prysm',
            'name': 'Prysm',
            'language': 'Go',
            'description': '功能丰富,社区活跃',
            'recommended': False
        },
        {
            'id': 'teku',
            'name': 'Teku',
            'language': 'Java',
            'description': '企业级,稳定可靠',
            'recommended': False
        },
        {
            'id': 'nimbus',
            'name': 'Nimbus',
            'language': 'Nim',
            'description': '轻量级,适合低配置',
            'recommended': False
        }
    ]

    return jsonify({
        'success': True,
        'data': clients
    })
