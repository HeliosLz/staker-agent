# Staker Agent

以太坊验证者一站式部署与管理工具。通过 CLI 或 Web UI，在几分钟内完成从环境检查到节点上线的全流程。

## 特性

- **一键部署** — Web UI 单次点击，后端自动编排 6 步流程（环境检查 → 安装 eth-docker → 生成配置 → 生成密钥 → 部署 → 验证）
- **实时进度** — Socket.IO 推送每步状态，前端 Stepper 实时展示
- **本地 + 远程** — 本地 Docker Compose 直接部署，或通过 SSH + Ansible 部署到远程服务器
- **多网络** — Mainnet、Holesky、Sepolia
- **多客户端** — Lighthouse (Rust)、Prysm (Go)、Teku (Java)、Nimbus (Nim)，执行层统一使用 Geth
- **Lido CSM** — 内置 Lido Community Staking Module 集成，自动填充 withdrawal vault 地址
- **CLI + Web** — 命令行和 Web 界面双入口，共享 `core/` 业务逻辑

## 架构

```
┌──────────┐   ┌──────────────────┐
│  CLI     │   │  Flask API       │
│ (Click)  │   │ + Socket.IO      │
└────┬─────┘   └──────┬───────────┘
     │                │
     │    ┌───────────┴───────────┐
     │    │  staker_backend/      │
     │    │  routes → services    │
     │    │  → repositories      │
     │    └───────────┬───────────┘
     │                │
     └────────┬───────┘
              ▼
        ┌──────────┐
        │  core/*  │
        └────┬─────┘
     ┌───────┼───────┐
     ▼       ▼       ▼
  Docker  SSH/Ansible FileSystem
```

## 快速开始

### 环境要求

- Python 3.10+
- Docker & Docker Compose
- Node.js 18+（Web UI 开发）

### 安装

```bash
git clone https://github.com/HeliosLz/staker-agent.git
cd staker-agent

# Python 依赖
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pip install -r web/backend/requirements.txt

# 前端依赖
cd web/frontend && npm install && cd ../..
```

### 方式一：CLI 部署

```bash
# 1. 检查环境
python3 cli.py init

# 2. 安装 Docker + eth-docker
python3 cli.py setup

# 3. 配置节点
python3 cli.py configure --network holesky --client lighthouse

# 4. 生成验证者密钥
python3 cli.py keys generate --count 1 --network holesky

# 5. 部署节点
python3 cli.py deploy

# 6. 查看状态
python3 cli.py status
```

### 方式二：Web UI 部署

```bash
# 启动后端 (端口 5001)
python3 web/backend/app.py

# 启动前端 (另一个终端, 端口 5173)
cd web/frontend && npm run dev
```

打开 http://localhost:5173/setup，按向导完成 5 步配置后点击"开始部署"。

### 方式三：远程部署

```bash
# 预检远程主机
python3 cli.py remote-preflight user@your-server.com --ssh-key ~/.ssh/id_rsa

# 远程部署
python3 cli.py deploy \
  --host user@your-server.com \
  --ssh-key ~/.ssh/id_rsa \
  --network holesky \
  --client lighthouse
```

## CLI 命令参考

| 命令 | 说明 | 关键选项 |
|------|------|----------|
| `init` | 环境检查 | — |
| `setup` | 安装 Docker + eth-docker | `--skip-docker` |
| `configure` | 配置网络与客户端 | `--network`, `--client`, `--fee-recipient`, `--withdrawal-address`, `-i` |
| `keys generate` | 生成验证者密钥 | `--count`, `--network`, `--withdrawal-address` |
| `keys list` | 查看已有密钥 | — |
| `keys import` | 导入密钥 | `--keys-path` |
| `deploy` | 部署节点（本地或远程） | `--host`, `--user`, `--port`, `--ssh-key`, `--network`, `--client` |
| `status` | 查看节点状态 | `--detailed` |
| `logs` | 查看日志 | `--service`, `-f` |
| `start` / `stop` | 启动 / 停止节点 | — |
| `validate` | 验证配置文件 | — |
| `remote-preflight` | 远程主机预检 | `--user`, `--port`, `--ssh-key` |

## Web API 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/env/check` | 环境检查 |
| GET | `/api/config/networks` | 可用网络列表 |
| GET | `/api/config/clients` | 可用客户端列表 |
| POST | `/api/config/generate` | 生成 .env 配置 |
| POST | `/api/deploy/full` | 一键全流程部署（通过 Socket.IO 推送进度） |
| POST | `/api/deploy/start` | 启动部署 |
| POST | `/api/deploy/keys/generate` | 生成验证者密钥 |
| GET | `/api/status` | 节点状态 |
| GET | `/api/jobs/:id` | 查询后台任务状态 |

**Socket.IO 事件：** `pipeline_progress`（逐步进度）、`pipeline_complete`（部署完成）

## 项目结构

```
staker-agent/
├── cli.py                  # CLI 入口
├── commands/               # CLI 子命令
├── core/                   # 共享业务逻辑
│   ├── config/             #   配置生成与验证
│   ├── deploy/             #   部署编排
│   ├── docker/             #   Docker / eth-docker 管理
│   ├── keys/               #   验证者密钥管理
│   ├── node/               #   节点状态监控
│   ├── remote/             #   SSH 客户端 / Ansible / 远程部署
│   └── system/             #   系统环境检查
├── config/                 # 网络配置 (networks.yaml)
├── ansible/                # Ansible playbooks & roles
├── web/
│   ├── backend/            # Flask + Socket.IO 后端
│   │   ├── app.py          #   应用入口
│   │   └── staker_backend/ #   路由 / 服务 / Schema / 仓库
│   └── frontend/           # React + Vite + Tailwind 前端
│       └── src/
│           ├── pages/      #   Landing / SetupWizard / Dashboard / Terminal
│           ├── components/ #   Setup 步骤组件
│           ├── hooks/      #   usePipelineProgress
│           └── services/   #   API 客户端 / Socket.IO
└── tests/                  # 测试
```

## 系统要求

|  | 测试网 (Holesky / Sepolia) | 主网 (Mainnet) |
|--|---------------------------|----------------|
| 存储 | 100 GB+ | 2 TB+ SSD |
| 内存 | 8 GB+ | 16 GB+ |
| CPU | 2 核+ | 4 核+ |

## 使用场景

### Holesky 测试网（入门推荐）

```bash
python3 cli.py configure --network holesky --client lighthouse
python3 cli.py keys generate --count 1 --network holesky
python3 cli.py deploy
```

### Lido CSM 社区质押

```bash
python3 cli.py configure --network holesky --client lighthouse \
  --withdrawal-address 0x...
python3 cli.py keys generate --count 1 --network holesky \
  --withdrawal-address 0x...
python3 cli.py deploy
```

### 主网部署（需要 32 ETH）

```bash
python3 cli.py configure --network mainnet --client lighthouse \
  --fee-recipient 0x... --withdrawal-address 0x...
python3 cli.py keys generate --count 1 --network mainnet \
  --withdrawal-address 0x...
python3 cli.py deploy
```

## 安全提示

- 妥善保管助记词（24 个单词），这是恢复密钥的唯一方式
- 备份 keystore 文件和密码
- 提款地址一旦设置无法更改
- 主网部署前务必在测试网验证
- 不要将 `.env`、密钥文件或 keystore 提交到版本控制

## 相关资源

- [eth-docker 文档](https://ethdocker.com)
- [Ethereum Launchpad](https://launchpad.ethereum.org)
- [Lido CSM](https://csm.lido.fi)
- [EthStaker 社区](https://discord.gg/ethstaker)

## 贡献

欢迎提交 Issue 和 Pull Request。请遵循 [Conventional Commits](https://www.conventionalcommits.org/) 规范（`feat:`, `fix:`, `chore:`）。

## License

Apache License 2.0
