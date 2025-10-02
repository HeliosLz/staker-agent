# 🚀 Staker Agent Web UI - 快速开始

## 📋 前置准备

确保已安装:
- Python 3.9+ (`python3 --version`)
- Node.js 18+ (`node --version`)
- npm (`npm --version`)

## ⚡ 一键启动

### 1. 安装后端依赖

```bash
cd /Users/gffive/staker-agent/web/backend
pip3 install -r requirements.txt
```

### 2. 安装前端依赖

```bash
cd /Users/gffive/staker-agent/web/frontend
npm install
```

### 3. 启动服务

```bash
cd /Users/gffive/staker-agent/web
./start.sh
```

## 🌐 访问地址

启动成功后,访问:

- **前端界面**: http://localhost:5173
- **后端 API**: http://localhost:5000

## 📱 页面导航

### 1. 首页 (/)
- 项目介绍
- 功能特性展示
- 点击 "开始部署" 进入安装向导

### 2. 安装向导 (/setup)
按步骤完成节点部署:
1. **环境检查** - 检测系统环境
2. **选择网络** - Mainnet / Holesky / Hoodi / Sepolia
3. **选择客户端** - Lighthouse / Prysm / Teku / Nimbus
4. **密钥生成** - 配置验证者密钥
5. **部署节点** - 一键启动

### 3. 仪表盘 (/dashboard)
实时监控:
- 节点状态 (运行中/已停止)
- 性能指标 (CPU、内存、磁盘)
- 同步进度
- 实时日志
- 节点控制 (启动/停止/重启)

### 4. 终端 (/terminal)
命令行界面:
- 执行 CLI 命令
- 查看实时输出
- 快捷命令按钮

## 🛠️ 手动启动 (开发模式)

如果不使用启动脚本,可以手动启动:

**终端 1 - 后端**:
```bash
cd /Users/gffive/staker-agent/web/backend
python3 app.py
```

**终端 2 - 前端**:
```bash
cd /Users/gffive/staker-agent/web/frontend
npm run dev
```

## 🧪 测试 API

### 健康检查
```bash
curl http://localhost:5000/api/health
```

### 环境检测
```bash
curl http://localhost:5000/api/env/check
```

### 获取网络列表
```bash
curl http://localhost:5000/api/config/networks
```

## ❌ 故障排除

### 后端端口被占用
```bash
# 查找占用 5000 端口的进程
lsof -i :5000
# 杀死进程
kill -9 <PID>
```

### 前端端口被占用
```bash
# 查找占用 5173 端口的进程
lsof -i :5173
# 杀死进程
kill -9 <PID>
```

### CORS 错误
确保后端已配置 CORS,允许来自 `http://localhost:5173` 的请求

### API 404 错误
检查:
1. 后端是否正常运行
2. API 路径是否正确
3. 查看后端终端日志

## 🎨 界面预览

### 首页
![Landing](docs/screenshots/landing.png)

### 安装向导
![Setup](docs/screenshots/setup.png)

### 仪表盘
![Dashboard](docs/screenshots/dashboard.png)

### 终端
![Terminal](docs/screenshots/terminal.png)

## 📚 下一步

1. 阅读完整文档: [web/README.md](README.md)
2. 查看架构设计: [FRONTEND_ARCHITECTURE.md](../FRONTEND_ARCHITECTURE.md)
3. 运行实际部署测试
4. 自定义界面样式

## 🤝 反馈

遇到问题?
- 查看日志输出
- 检查浏览器控制台
- 提交 Issue

---

**祝您使用愉快! 🎉**
