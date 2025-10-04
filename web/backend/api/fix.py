"""
自动修复 API - Agent 自动解决环境问题
"""
from flask import Blueprint, jsonify, request
import subprocess
import platform
import os

fix_bp = Blueprint('fix', __name__)

@fix_bp.route('/docker/install', methods=['POST'])
def install_docker():
    """
    自动安装 Docker
    POST /api/fix/docker/install
    """
    try:
        os_type = platform.system()

        if os_type == 'Darwin':  # macOS
            return install_docker_macos()
        elif os_type == 'Linux':
            return install_docker_linux()
        elif os_type == 'Windows':
            return install_docker_windows()
        else:
            return jsonify({
                'success': False,
                'error': f'不支持的操作系统: {os_type}'
            }), 400

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


def install_docker_macos():
    """在 macOS 上安装 Docker Desktop"""
    try:
        # 检查是否安装了 Homebrew
        brew_check = subprocess.run(
            ['which', 'brew'],
            capture_output=True,
            text=True
        )

        if brew_check.returncode != 0:
            return jsonify({
                'success': False,
                'error': '需要先安装 Homebrew',
                'instructions': [
                    '请手动安装 Homebrew:',
                    '/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"',
                    '或者访问: https://brew.sh'
                ]
            }), 400

        # 使用 Homebrew 安装 Docker Desktop
        # 注意: 这需要用户授权，所以我们返回指令而不是直接安装
        return jsonify({
            'success': True,
            'method': 'manual',
            'instructions': [
                'Docker Desktop 需要手动安装',
                '方式 1 - Homebrew (推荐):',
                '  brew install --cask docker',
                '',
                '方式 2 - 官网下载:',
                '  访问 https://www.docker.com/products/docker-desktop',
                '  下载并安装 Docker Desktop for Mac',
                '',
                '安装完成后:',
                '  1. 打开 Docker Desktop',
                '  2. 等待 Docker 引擎启动',
                '  3. 返回此页面重新检查环境'
            ]
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


def install_docker_linux():
    """在 Linux 上自动安装 Docker"""
    try:
        # 检测 Linux 发行版
        with open('/etc/os-release', 'r') as f:
            os_info = f.read()

        if 'Ubuntu' in os_info or 'Debian' in os_info:
            # Ubuntu/Debian 系统 - 真正执行安装
            try:
                # 实际执行安装命令
                install_script = """
                sudo apt-get update -qq && \
                sudo apt-get install -y -qq docker.io docker-compose-v2 && \
                sudo systemctl start docker && \
                sudo systemctl enable docker && \
                sudo usermod -aG docker $USER
                """

                result = subprocess.run(
                    install_script,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=300  # 5 minutes timeout
                )

                if result.returncode == 0:
                    return jsonify({
                        'success': True,
                        'method': 'auto',
                        'installed': True,
                        'message': 'Docker 已成功安装！请重新登录以使用 docker 命令。',
                        'instructions': [
                            '✓ Docker 安装完成',
                            '⚠️ 请注意：您需要重新登录或运行以下命令：',
                            '  newgrp docker',
                            '然后重新运行环境检查'
                        ]
                    })
                else:
                    return jsonify({
                        'success': False,
                        'error': f'安装失败: {result.stderr}',
                        'instructions': [
                            '自动安装失败，请手动安装:',
                            'curl -fsSL https://get.docker.com -o get-docker.sh',
                            'sudo sh get-docker.sh'
                        ]
                    }), 500

            except subprocess.TimeoutExpired:
                return jsonify({
                    'success': False,
                    'error': '安装超时',
                    'instructions': ['请手动安装 Docker: https://docs.docker.com/engine/install/']
                }), 500

        elif 'Fedora' in os_info or 'CentOS' in os_info or 'Red Hat' in os_info:
            # Red Hat 系列
            install_script = """
            sudo dnf install -y docker docker-compose && \
            sudo systemctl start docker && \
            sudo systemctl enable docker && \
            sudo usermod -aG docker $USER
            """

            result = subprocess.run(
                install_script,
                shell=True,
                capture_output=True,
                text=True,
                timeout=300
            )

            if result.returncode == 0:
                return jsonify({
                    'success': True,
                    'method': 'auto',
                    'installed': True,
                    'message': 'Docker 已成功安装！',
                    'instructions': [
                        '✓ Docker 安装完成',
                        '⚠️ 请重新登录以使用 docker 命令'
                    ]
                })
            else:
                return jsonify({
                    'success': False,
                    'error': f'安装失败: {result.stderr}'
                }), 500

        else:
            return jsonify({
                'success': False,
                'method': 'manual',
                'error': '不支持的 Linux 发行版',
                'instructions': [
                    '请手动安装 Docker:',
                    'https://docs.docker.com/engine/install/'
                ]
            }), 400

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'instructions': [
                '安装过程出错',
                '请手动安装: https://docs.docker.com/engine/install/'
            ]
        }), 500


def install_docker_windows():
    """在 Windows 上安装 Docker Desktop"""
    return jsonify({
        'success': True,
        'method': 'manual',
        'instructions': [
            'Docker Desktop for Windows 需要手动安装',
            '',
            '步骤:',
            '  1. 访问 https://www.docker.com/products/docker-desktop',
            '  2. 下载 Docker Desktop for Windows',
            '  3. 运行安装程序',
            '  4. 启用 WSL 2 (如果提示)',
            '  5. 重启计算机',
            '  6. 打开 Docker Desktop',
            '  7. 返回此页面重新检查环境'
        ]
    })


@fix_bp.route('/check-progress', methods=['GET'])
def check_fix_progress():
    """
    检查修复进度
    GET /api/fix/check-progress?issue=docker
    """
    issue = request.args.get('issue')

    if issue == 'docker':
        # 重新检查 Docker 是否已安装
        try:
            result = subprocess.run(
                ['docker', '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                return jsonify({
                    'success': True,
                    'fixed': True,
                    'message': 'Docker 已成功安装',
                    'version': result.stdout.strip()
                })
            else:
                return jsonify({
                    'success': True,
                    'fixed': False,
                    'message': 'Docker 尚未安装'
                })
        except Exception:
            return jsonify({
                'success': True,
                'fixed': False,
                'message': 'Docker 尚未安装'
            })

    return jsonify({
        'success': False,
        'error': '未知的问题类型'
    }), 400
