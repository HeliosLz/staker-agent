#!/bin/bash

#################################################
# Staker Agent - GCP VM 自动化设置脚本
#
# 用途: 在 GCP VM 上自动安装和配置 Staker Agent
# 使用: curl -fsSL https://raw.githubusercontent.com/HeliosLz/staker-agent/main/scripts/gcp-setup.sh | bash
#################################################

set -e  # 遇到错误立即退出

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 打印函数
print_header() {
    echo -e "\n${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}$1${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_step() {
    echo -e "${CYAN}▶ $1${NC}"
}

# 检测操作系统
detect_os() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        OS=$NAME
        VER=$VERSION_ID
    else
        print_error "无法检测操作系统"
        exit 1
    fi
}

# 检查是否为 root 用户
check_root() {
    if [ "$EUID" -eq 0 ]; then
        print_warning "不建议使用 root 用户运行此脚本"
        print_info "建议使用普通用户，脚本会在需要时提示 sudo"
        read -p "是否继续? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
}

# 主安装流程
main() {
    print_header "🚀 Staker Agent - GCP VM 自动化设置"

    print_info "操作系统: $OS $VER"
    print_info "用户: $(whoami)"
    print_info "主目录: $HOME"
    echo ""

    # 步骤 1: 更新系统
    print_step "步骤 1/6: 更新系统包"
    sudo apt update -qq
    print_success "系统包已更新"

    # 步骤 2: 安装 Python 和 Git
    print_step "步骤 2/6: 安装 Python 3 和 Git"
    if ! command -v python3 &> /dev/null; then
        sudo apt install -y python3 python3-pip git -qq
        print_success "Python 3 和 Git 安装完成"
    else
        print_success "Python 3 已安装 ($(python3 --version))"
    fi

    # 步骤 3: 安装 Docker
    print_step "步骤 3/6: 安装 Docker"
    if ! command -v docker &> /dev/null; then
        print_info "安装 Docker..."
        sudo apt install -y docker.io docker-compose-v2 -qq
        sudo systemctl start docker
        sudo systemctl enable docker
        print_success "Docker 安装完成"
    else
        print_success "Docker 已安装 ($(docker --version))"
    fi

    # 步骤 4: 配置 Docker 权限
    print_step "步骤 4/6: 配置 Docker 用户权限"
    if groups $USER | grep -q '\bdocker\b'; then
        print_success "用户 $USER 已在 docker 组中"
    else
        sudo usermod -aG docker $USER
        print_success "用户 $USER 已添加到 docker 组"
        print_warning "需要重新登录或运行 'newgrp docker' 使权限生效"
    fi

    # 步骤 5: 克隆 Staker Agent
    print_step "步骤 5/6: 克隆 Staker Agent 项目"
    if [ -d "$HOME/staker-agent" ]; then
        print_warning "目录 $HOME/staker-agent 已存在"
        read -p "是否删除并重新克隆? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            rm -rf "$HOME/staker-agent"
            git clone https://github.com/HeliosLz/staker-agent.git "$HOME/staker-agent"
            print_success "项目已克隆"
        else
            print_info "跳过克隆步骤"
        fi
    else
        git clone https://github.com/HeliosLz/staker-agent.git "$HOME/staker-agent"
        print_success "项目已克隆到 $HOME/staker-agent"
    fi

    # 步骤 6: 安装 Python 依赖
    print_step "步骤 6/6: 安装 Python 依赖"
    cd "$HOME/staker-agent"
    pip3 install -q -r requirements.txt
    print_success "Python 依赖已安装"

    # 完成
    print_header "🎉 安装完成!"

    echo -e "${GREEN}所有组件已成功安装:${NC}"
    echo -e "  • Python 3: $(python3 --version)"
    echo -e "  • Docker: $(docker --version)"
    echo -e "  • Docker Compose: $(docker compose version)"
    echo -e "  • Staker Agent: $HOME/staker-agent"
    echo ""

    print_info "下一步操作:"
    echo -e "${YELLOW}1. 刷新用户组权限 (如果首次安装 Docker):${NC}"
    echo -e "   ${CYAN}newgrp docker${NC}"
    echo ""
    echo -e "${YELLOW}2. 运行环境检查:${NC}"
    echo -e "   ${CYAN}cd $HOME/staker-agent${NC}"
    echo -e "   ${CYAN}python3 cli.py check${NC}"
    echo ""
    echo -e "${YELLOW}3. 初始化 Staker Agent:${NC}"
    echo -e "   ${CYAN}python3 cli.py init${NC}"
    echo ""
    echo -e "${YELLOW}4. 配置验证节点:${NC}"
    echo -e "   ${CYAN}python3 cli.py configure${NC}"
    echo ""
    echo -e "${YELLOW}5. 部署节点:${NC}"
    echo -e "   ${CYAN}python3 cli.py deploy${NC}"
    echo ""

    print_info "查看完整文档:"
    echo -e "   ${CYAN}https://github.com/HeliosLz/staker-agent${NC}"
    echo ""

    print_success "安装脚本执行完毕!"
}

# 错误处理
trap 'print_error "安装过程中发生错误"; exit 1' ERR

# 运行主程序
detect_os
check_root
main
