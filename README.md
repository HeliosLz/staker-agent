# Staker Agent

以太坊验证节点的自主运维助手。部署、监控、自动修复、Telegram 告警 — 一个 Agent 全搞定。

> **它不只是帮你部署节点，它是一个住在你机器里的值班员。沉默运行、主动干预、被动应答。**

## 特性

### 自主运维（Phase 2）
- **24/7 健康监控** — 后台每 60 秒检查容器状态、同步进度、Peer 连接
- **自动修复** — 容器崩溃时自动重启，连续失败后升级给人
- **Telegram 告警** — 异常主动推送，恢复后发送通知
- **自然语言管理** — 发 Telegram 消息 "节点怎么样？" 即可获得完整报告

### 一键部署（Phase 1）
- **全流程自动化** — 环境检查 → eth-docker → 配置 → 密钥 → 部署，一步到位
- **多入口** — CLI、Web UI、Telegram 对话，共享 `core/` 业务逻辑
- **多网络** — Mainnet、Holesky、Hoodi、Sepolia
- **多客户端** — Lighthouse、Prysm、Teku、Nimbus + Geth
- **Lido CSM** — 内置 Community Staking Module 集成
- **远程部署** — SSH + Ansible 部署到远程服务器

## 架构

双循环 Agent 设计，基于 Harness 构建：

```
┌─────────────────────────────────────────────────┐
│           Tool Registry (core/agent/tools.py)    │
│           所有工具在这里注册，两个循环共享            │
├──────────────────┬──────────────────────────────┤
│ Monitor Loop     │  Chat Loop                   │
│ (后台 daemon)    │  (用户触发)                    │
│                  │                              │
│ 每 60s:          │  用户发消息时:                  │
│  采集健康数据     │   drain monitor 通知到 LLM 上下文│
│  规则引擎决策     │   micro-compact 旧结果         │
│  自动修复/告警    │   LLM 调用工具 → 回复用户       │
│  推送到通知队列 ──┼──▶ LLM 自动看到监控事件         │
├──────────────────┴──────────────────────────────┤
│           Shared State (core/agent/state.py)     │
├─────────────────────────────────────────────────┤
│           Notification Sinks                     │
│           Telegram (httpx) │ WebSocket │ REST    │
└─────────────────────────────────────────────────┘
```

**Monitor Loop** — 确定性规则引擎，不依赖 LLM，24/7 可靠运行。自动重启崩溃容器，超过 N 次失败后升级给人。

**Chat Loop** — LLM 驱动（OpenRouter），支持自然语言交互。每次调用前自动注入 Monitor 事件（s08 模式），压缩旧上下文（s06 模式）。多步操作（如部署）通过 TodoWrite（s03 模式）跟踪进度，防止长对话中丢失步骤。

## 快速开始

### 环境要求

- Python 3.10+
- Docker & Docker Compose
- Node.js 18+（Web UI）

### 安装

```bash
git clone https://github.com/HeliosLz/staker-agent.git
cd staker-agent

# Python
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pip install -r web/backend/requirements.txt

# 前端
cd web/frontend && npm install && cd ../..
```

### 方式一：完整模式（推荐）

Flask API + Telegram Bot + Monitor，一个命令全启动：

```bash
# 设置环境变量
export TELEGRAM_BOT_TOKEN="your-bot-token"
export TELEGRAM_ALERT_CHAT_ID="your-chat-id"     # 告警推送目标
export OPENROUTER_API_KEY="your-api-key"          # LLM 对话（可选）

python3 web/backend/main.py
```

启动后：
- Flask API 运行在 `http://localhost:5001`
- Monitor 后台每 60 秒检查节点健康
- Telegram Bot 接收命令和对话

### 方式二：Web UI 部署

```bash
python3 web/backend/app.py                        # 后端 :5001
cd web/frontend && npm run dev                     # 前端 :5173
```

打开 http://localhost:5173/setup 按向导部署。

### 方式三：CLI 部署

```bash
python3 cli.py init                                # 检查环境
python3 cli.py configure --network holesky --client lighthouse
python3 cli.py keys generate --count 1 --network holesky
python3 cli.py deploy
python3 cli.py status --detailed
```

### 方式四：远程部署

```bash
python3 cli.py deploy \
  --host user@your-server.com \
  --ssh-key ~/.ssh/id_rsa \
  --network holesky --client lighthouse
```

## Telegram 命令

| 命令 | 说明 | 需要 LLM |
|------|------|---------|
| `/status` | 即时节点状态（容器 + 同步） | 否 |
| `/health` | 即时健康报告（评分 + 各项检查） | 否 |
| `/reset` | 清空对话历史 | 否 |
| 自然语言 | "帮我部署一个验证者" / "节点怎么样？" | 是 |

**告警示例：**
```
⚙️ Container Status
执行层容器异常退出
已自动重启，观察中...

✅ RECOVERED: Container Status
执行层已恢复
停机时间: 1m 23s
```

## API 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/env/check` | 环境检查 |
| GET | `/api/config/networks` | 可用网络列表 |
| POST | `/api/config/generate` | 生成节点配置 |
| POST | `/api/deploy/full` | 一键全流程部署 |
| POST | `/api/deploy/keys/generate` | 生成验证者密钥 |
| GET | `/api/status` | 节点状态 |
| GET | `/api/monitor` | 健康报告 |
| GET | `/api/monitor/alerts` | 活跃告警 |
| GET | `/api/monitor/events` | 操作事件日志 |
| POST | `/api/agent/apikey` | 配置 LLM API Key |

**Socket.IO 事件：** `health_update`、`health_alert`、`agent_text_delta`、`agent_tool_start`、`agent_tool_result`

## 项目结构

```
staker-agent/
├── cli.py                     # CLI 入口
├── core/                      # 共享业务逻辑（不依赖 Flask）
│   ├── agent/                 #   自主 Agent 核心
│   │   ├── tools.py           #     统一工具注册表（12 个工具）
│   │   ├── state.py           #     共享状态（告警、操作日志）
│   │   ├── todo.py            #     s03: 多步任务追踪
│   │   ├── monitor.py         #     Monitor Loop（规则引擎）
│   │   ├── notifier.py        #     事件格式化
│   │   └── skills/            #     按需知识包
│   ├── monitor/health.py      #   健康检查函数
│   ├── node/status.py         #   Docker/RPC 数据采集
│   ├── config/                #   网络配置
│   ├── deploy/                #   部署编排
│   ├── docker/                #   Docker/eth-docker 管理
│   ├── keys/                  #   验证者密钥管理
│   └── remote/                #   SSH/Ansible 远程部署
├── web/
│   ├── backend/
│   │   ├── main.py            #   统一入口（Flask + Telegram + Monitor）
│   │   ├── staker_backend/    #   Flask 应用
│   │   │   ├── services/      #     服务层（agent.py = Chat Loop）
│   │   │   ├── routes/        #     REST API
│   │   │   └── repositories/  #     数据访问
│   │   ├── telegram_bot/      #   Telegram Bot
│   │   └── websocket/         #   Socket.IO 事件处理
│   └── frontend/              #   React + Vite + Tailwind
│       └── src/
│           ├── pages/         #     Dashboard / ChatSetup / SetupWizard
│           └── hooks/         #     useAgentChat / useHealthMonitor
└── config/                    # networks.yaml
```
## 配置

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `OPENROUTER_API_KEY` | — | LLM API Key（对话功能需要） |
| `OPENROUTER_MODEL` | `openrouter/free` | LLM 模型 |
| `TELEGRAM_BOT_TOKEN` | — | Telegram Bot Token |
| `TELEGRAM_ALLOWED_CHAT_IDS` | 全部允许 | 访问控制白名单 |
| `TELEGRAM_ALERT_CHAT_ID` | — | 告警推送目标 Chat ID |
| `MONITOR_ENABLED` | `true` | 启用健康监控 |
| `MONITOR_CHECK_INTERVAL` | `60` | 检查间隔（秒） |
| `MONITOR_ALERT_COOLDOWN` | `300` | 重复告警冷却（秒） |
| `MONITOR_MAX_AUTO_ACTIONS` | `3` | 自动重启次数上限 |
| `STAKER_AGENT_ETH_DOCKER_PATH` | `~/eth-docker` | eth-docker 路径 |

## 系统要求

|  | 测试网 (Holesky) | 主网 (Mainnet) |
|--|-----------------|----------------|
| 存储 | 100 GB+ | 2 TB+ SSD |
| 内存 | 8 GB+ | 16 GB+ |
| CPU | 2 核+ | 4 核+ |

## 安全提示

- 妥善保管助记词（24 个单词），这是恢复密钥的唯一方式
- 备份 keystore 文件和密码
- 提款地址一旦设置无法更改
- 主网部署前务必在测试网验证
- 不要将 `.env`、密钥文件或 keystore 提交到版本控制
- 设置 `TELEGRAM_ALLOWED_CHAT_IDS` 限制 Bot 访问权限

## 相关资源

- [eth-docker](https://ethdocker.com)
- [Ethereum Launchpad](https://launchpad.ethereum.org)
- [Lido CSM](https://csm.lido.fi)
- [EthStaker 社区](https://discord.gg/ethstaker)

## License

Apache License 2.0
