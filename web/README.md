# Staker Agent Web UI

基于 React + Vite + Flask 的以太坊验证节点部署 Web 界面

## 📐 架构

```
web/
├── frontend/          # React 前端
│   ├── src/
│   │   ├── pages/    # 页面组件
│   │   ├── services/ # API 服务
│   │   ├── types/    # TypeScript 类型
│   │   └── lib/      # 工具函数
│   └── package.json
│
└── backend/           # Flask 后端
    ├── app.py        # 主程序
    ├── api/          # REST API
    └── websocket/    # WebSocket 服务
```

## 🚀 快速开始

### 前置要求

- Node.js 18+
- Python 3.9+
- Docker (可选)

### 安装

1. **安装后端依赖**
```bash
cd web/backend
pip install -r requirements.txt
```

2. **安装前端依赖**
```bash
cd web/frontend
npm install
```

### 运行

**方式 1: 使用启动脚本 (推荐)**

```bash
# 从 web 目录运行
chmod +x start.sh
./start.sh
```

**方式 2: 手动启动**

终端 1 - 启动后端:
```bash
cd web/backend
python app.py
```

终端 2 - 启动前端:
```bash
cd web/frontend
npm run dev
```

### 访问

- 前端: http://localhost:5173
- 后端 API: http://localhost:5000
- API 文档: http://localhost:5000

## 🎨 功能特性

### 1. 首页 (Landing)
- 项目介绍
- 核心功能展示
- 支持的网络和客户端

### 2. 安装向导 (Setup Wizard)
5 步部署流程:
- ① 环境检查
- ② 选择网络
- ③ 选择客户端
- ④ 密钥生成
- ⑤ 部署节点

### 3. 仪表盘 (Dashboard)
- 实时节点状态
- 性能指标监控
- 日志查看
- 节点控制(启动/停止/重启)

### 4. 终端 (Terminal)
- 嵌入式终端模拟器
- 快捷命令支持
- 实时命令执行

## 🔌 API 端点

### 环境检测
- `GET /api/env/check` - 检查系统环境

### 配置管理
- `GET /api/config/networks` - 获取网络列表
- `GET /api/config/clients` - 获取客户端列表
- `POST /api/config/generate` - 生成配置

### 部署管理
- `POST /api/deploy/setup` - 安装依赖
- `POST /api/deploy/keys/generate` - 生成密钥
- `POST /api/deploy/start` - 启动部署

### 节点状态
- `GET /api/status` - 获取节点状态
- `GET /api/status/logs` - 获取日志
- `POST /api/status/start` - 启动节点
- `POST /api/status/stop` - 停止节点
- `POST /api/status/restart` - 重启节点

## 🛠️ 技术栈

### 前端
- React 18
- TypeScript
- Vite
- Tailwind CSS
- React Router
- Axios
- Lucide Icons

### 后端
- Flask
- Flask-SocketIO
- Flask-CORS
- Python 3.9+

## 📦 构建生产版本

```bash
cd web/frontend
npm run build
```

构建产物在 `dist/` 目录

## 🐛 故障排除

### 后端启动失败
- 检查 Python 版本: `python --version`
- 检查依赖安装: `pip list`
- 检查端口占用: `lsof -i :5000`

### 前端启动失败
- 检查 Node 版本: `node --version`
- 清除缓存: `npm cache clean --force`
- 重新安装: `rm -rf node_modules && npm install`

### API 连接失败
- 检查后端是否运行
- 检查 CORS 配置
- 查看浏览器控制台错误

## 📝 开发说明

### 添加新页面
1. 在 `src/pages/` 创建组件
2. 在 `App.tsx` 添加路由
3. 在导航中添加链接

### 添加新 API
1. 在 `backend/api/` 创建蓝图
2. 在 `app.py` 注册蓝图
3. 在 `frontend/src/services/api.ts` 添加客户端调用

## 🔐 安全注意事项

- 生产环境需配置 HTTPS
- 更改 Flask SECRET_KEY
- 限制 CORS 允许的域名
- 不要在前端暴露敏感信息

## 📄 License

MIT
