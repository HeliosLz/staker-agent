# 🛰️ Staker Agent - 用户指南手册

**版本**: v0.1.0
**更新日期**: 2025-10-01
**适用人群**: 想要运行以太坊验证节点的任何人（无需运维经验）

---

## 📖 目录

1. [简介](#简介)
2. [安装与配置](#安装与配置)
3. [快速开始](#快速开始)
4. [命令详解](#命令详解)
5. [使用场景](#使用场景)
6. [常见问题](#常见问题)
7. [故障排除](#故障排除)
8. [安全最佳实践](#安全最佳实践)
9. [附录](#附录)

---

## 🎯 简介

### 什么是 Staker Agent？

Staker Agent 是一个 AI 驱动的以太坊验证节点部署和管理工具，让任何人都能在几分钟内部署和管理验证节点，无需专业的运维知识。

### 核心特性

- ✅ **5 分钟快速部署** - 从零到配置完成
- ✅ **本地部署优先** - 在自己的电脑上运行，降低成本
- ✅ **智能配置** - 自动生成正确的配置文件
- ✅ **多网络支持** - Mainnet、Holesky、Hoodi、Sepolia
- ✅ **美观界面** - 清晰的彩色输出和表格展示
- ✅ **安全提示** - 密钥管理、助记词安全警告

### 为什么选择 Staker Agent？

| 对比项 | 手动部署 | Staker Agent |
|--------|---------|--------------|
| **时间** | 2-4 小时 | 5 分钟 |
| **难度** | 需要 Linux 运维经验 | 零基础可用 |
| **错误率** | 高（配置复杂） | 低（自动验证） |
| **文档** | 分散在多处 | 一站式指南 |
| **成本** | 云服务器 $50-200/月 | 本地部署零成本 |

---

## 💻 安装与配置

### 系统要求

#### 最低配置（测试网）

- **操作系统**: macOS、Linux 或 Windows
- **Python**: 3.10 或更高版本
- **存储空间**: 100GB 以上
- **内存**: 8GB 以上
- **CPU**: 2 核以上
- **网络**: 稳定的宽带连接

#### 推荐配置（主网）

- **操作系统**: Linux (Ubuntu 22.04 或更高)
- **Python**: 3.10 或更高版本
- **存储空间**: 2TB SSD
- **内存**: 16GB 以上
- **CPU**: 4 核以上
- **网络**: 不限流量的宽带连接

### 前置准备

1. **安装 Python**

```bash
# macOS
brew install python3

# Ubuntu/Debian
sudo apt update
sudo apt install python3 python3-pip

# 验证安装
python3 --version  # 应该显示 3.10 或更高
```

2. **安装 Git**

```bash
# macOS
brew install git

# Ubuntu/Debian
sudo apt install git

# 验证安装
git --version
```

### 下载和安装

```bash
# 1. 克隆项目
cd ~
git clone https://github.com/你的用户名/staker-agent.git
cd staker-agent

# 2. 安装 Python 依赖
pip install -r requirements.txt

# 3. 验证安装
python3 cli.py --version
# 应该显示: cli.py, version 0.1.0
```

---

## 🚀 快速开始

### 五分钟部署 Holesky 测试网节点

这是一个完整的示例，展示如何在 5 分钟内部署一个 Holesky 测试网验证节点。

#### 步骤 1: 检查环境（30秒）

```bash
cd ~/staker-agent
python3 cli.py init
```

**预期输出：**
```
✅ OS: macOS/Linux
✅ Python: 3.12.4
✅ Disk Space: 209GB available
✅ Network: Connected
⚠️  Docker: Not installed (可选)
```

**说明：**
- 绿色 ✅ 表示检查通过
- 黄色 ⚠️ 表示警告，但可以继续
- 红色 ❌ 表示必须修复

#### 步骤 2: 安装依赖（1-2分钟）

```bash
python3 cli.py setup --skip-docker
```

**说明：**
- 会自动下载 eth-docker 到 `~/eth-docker`
- 如果你已经安装了 Docker，可以省略 `--skip-docker`

**预期输出：**
```
✅ eth-docker setup complete!

Next steps:
  1. Run python3 cli.py configure
  2. Run python3 cli.py keys generate
```

#### 步骤 3: 配置节点（10秒）

```bash
python3 cli.py configure --network holesky --client lighthouse
```

**参数说明：**
- `--network holesky`: 选择 Holesky 测试网
- `--client lighthouse`: 选择 Lighthouse 客户端

**预期输出：**
```
✅ Configuration completed successfully!

📋 Configuration details:
  • Network: holesky
  • Client: lighthouse + Geth
  • Config file: ~/eth-docker/.env
```

#### 步骤 4: 验证配置（5秒）

```bash
python3 cli.py validate
```

**预期输出：**
```
🔍 Validating Configuration

⚠️  Warnings:
  • No keystore files found (run: python3 cli.py keys generate)
  • No deposit_data.json found

You can proceed, but address the warnings when possible.
```

#### 步骤 5: 生成验证者密钥（2-3分钟）

⚠️ **重要：此步骤需要 Docker 运行！**

```bash
python3 cli.py keys generate --count 1 --network holesky
```

**交互式流程：**
```
1. 选择语言 (English)
2. 输入要生成的验证者数量: 1
3. 创建助记词 (24个单词) - ⚠️ 务必写下来！
4. 设置 keystore 密码 - ⚠️ 务必记住！
5. 确认助记词
```

**生成的文件：**
```
~/eth-docker/.eth/validator_keys/
  ├── deposit_data-*.json     # 上传到 Launchpad
  └── keystore-m_*.json       # 验证者密钥
```

#### 步骤 6: 上传 Deposit Data

1. 访问 Holesky Launchpad: https://holesky.launchpad.ethereum.org
2. 上传 `deposit_data-*.json`
3. 完成存款（测试网可以从 faucet 获取测试币）

#### 步骤 7: 部署节点（30秒-1分钟）

```bash
python3 cli.py deploy
```

**预期输出：**
```
🚀 Starting services...

✅ Services started successfully!

🎉 Deployment Complete!

📊 What's running:
  • Execution Layer (Geth) - Syncing blockchain
  • Consensus Layer - Syncing beacon chain
  • Validator Client - Waiting for keys
```

#### 步骤 8: 查看状态（随时）

```bash
python3 cli.py status
```

**预期输出：**
```
🛰️  Staker Agent - Status

Network: holesky
Client: Lighthouse + Geth

Container Status:
  execution-client    Running    Up 5 minutes
  consensus-client    Running    Up 5 minutes
  validator-client    Running    Up 5 minutes

✅ Node is running
```

---

## 📚 命令详解

### 命令总览

```bash
python3 cli.py [命令] [选项]
```

| 命令 | 用途 | 常用度 |
|------|------|--------|
| `init` | 检查系统环境 | ⭐⭐⭐ |
| `validate` | 验证配置完整性 | ⭐⭐⭐ |
| `setup` | 安装依赖 | ⭐⭐⭐ |
| `configure` | 配置网络和客户端 | ⭐⭐⭐⭐⭐ |
| `keys` | 管理验证者密钥 | ⭐⭐⭐⭐⭐ |
| `deploy` | 部署节点 | ⭐⭐⭐⭐⭐ |
| `status` | 查看节点状态 | ⭐⭐⭐⭐⭐ |
| `logs` | 查看日志 | ⭐⭐⭐⭐ |
| `start` | 启动节点 | ⭐⭐⭐ |
| `stop` | 停止节点 | ⭐⭐⭐ |

---

### init - 环境检查

**用途：** 检查系统环境是否满足运行要求

**语法：**
```bash
python3 cli.py init
```

**检查项目：**
- ✅ 操作系统类型和版本
- ✅ Python 版本（需要 3.10+）
- ✅ Docker 安装状态
- ✅ 可用磁盘空间
- ✅ 网络连接

**示例输出：**
```
Environment Status
┏━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━┓
┃ Component      ┃ Details          ┃ Status     ┃
┡━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━┩
│ OS             │ Darwin 24.6.0    │ ✅         │
│ Python         │ Python 3.12.4    │ ✅         │
│ Docker         │ Docker           │ ❌         │
│ Disk Space     │ 209GB available  │ ✅         │
│ Network        │ Connected        │ ✅         │
└────────────────┴──────────────────┴────────────┘
```

**常见问题：**

Q: Docker 显示未安装怎么办？
A: 运行 `python3 cli.py setup` 会自动安装，或者手动安装 Docker Desktop

Q: 磁盘空间不足怎么办？
A:
- 测试网至少需要 100GB
- 主网至少需要 2TB
- 清理不必要的文件或升级硬盘

---

### validate - 配置验证

**用途：** 验证配置文件的完整性和正确性

**语法：**
```bash
python3 cli.py validate
```

**验证项目：**
- ✅ eth-docker 是否已安装
- ✅ .env 配置文件是否存在
- ✅ 必需字段是否完整
- ✅ 引用的 compose 文件是否存在
- ⚠️ 验证者密钥是否已生成

**示例输出：**
```
🔍 Validating Configuration

✅ All validations passed!
Your setup is ready to deploy.
```

或者：
```
🔍 Validating Configuration

❌ Issues Found:
  • .env configuration file not found

⚠️  Warnings:
  • No keystore files found

Please fix the issues above before deploying.
```

**最佳实践：**
- 在 `deploy` 之前总是运行 `validate`
- 修改配置后重新运行验证
- 根据警告和错误提示逐一修复

---

### setup - 安装依赖

**用途：** 安装 Docker 和 eth-docker

**语法：**
```bash
python3 cli.py setup [选项]
```

**选项：**
- `--skip-docker`: 跳过 Docker 安装（如果已安装）

**示例：**

```bash
# 完整安装（包括 Docker）
python3 cli.py setup

# 跳过 Docker 安装
python3 cli.py setup --skip-docker
```

**安装内容：**
1. **Docker Desktop** (macOS/Windows)
   - 通过 Homebrew (macOS)
   - 手动安装 (Windows)

2. **eth-docker**
   - 克隆到 `~/eth-docker`
   - 设置执行权限
   - 验证安装

**注意事项：**
- macOS 上需要 Homebrew
- Linux 上需要 sudo 权限
- Windows 上需要手动安装 Docker Desktop

---

### configure - 配置节点

**用途：** 生成 eth-docker 配置文件

**语法：**
```bash
python3 cli.py configure [选项]
```

**选项：**

| 选项 | 说明 | 可选值 | 默认值 |
|------|------|--------|--------|
| `--network` | 选择网络 | mainnet, holesky, hoodi, sepolia | holesky |
| `--client` | 选择客户端 | lighthouse, prysm, teku, nimbus | lighthouse |
| `--fee-recipient` | 费用接收地址 | 0x... | - |
| `--withdrawal-address` | 提款地址 | 0x... | - |
| `-i, --interactive` | 交互式配置 | - | false |

**网络说明：**

| 网络 | 用途 | 存储需求 | 同步时间 | 测试币 |
|------|------|----------|----------|--------|
| **mainnet** | 主网（真实 ETH） | 2TB+ | 1-3天 | 需要 32 ETH |
| **holesky** | 测试网（推荐） | 100GB+ | 2-6小时 | [Faucet](https://faucet.holesky.ethpandaops.io) |
| **hoodi** | Lido CSM 测试网 | 100GB+ | 2-6小时 | [Lido Faucet](https://csm.testnet.fi) |
| **sepolia** | 测试网 | 100GB+ | 2-6小时 | [Faucet](https://sepoliafaucet.com) |

**客户端说明：**

| 客户端 | 语言 | 特点 | 推荐度 |
|--------|------|------|--------|
| **Lighthouse** | Rust | 性能好、资源占用低 | ⭐⭐⭐⭐⭐ |
| **Prysm** | Go | 社区大、文档丰富 | ⭐⭐⭐⭐ |
| **Teku** | Java | 企业级、稳定性好 | ⭐⭐⭐⭐ |
| **Nimbus** | Nim | 轻量级、适合低配 | ⭐⭐⭐ |

**示例：**

```bash
# 基础配置
python3 cli.py configure --network holesky --client lighthouse

# 主网配置（指定费用接收地址）
python3 cli.py configure \
  --network mainnet \
  --client lighthouse \
  --fee-recipient 0x1234567890123456789012345678901234567890

# Lido CSM 配置
python3 cli.py configure \
  --network hoodi \
  --client lighthouse \
  --withdrawal-address 0x1234567890123456789012345678901234567890

# 交互式配置
python3 cli.py configure -i
```

**生成的配置文件：**
- 位置: `~/eth-docker/.env`
- 格式: 环境变量键值对
- 包含: 网络、客户端、端口、Checkpoint Sync 等配置

**配置内容示例：**
```bash
COMPOSE_FILE=lighthouse.yml:geth.yml:deposit-cli.yml
NETWORK=holesky
CHECKPOINT_SYNC_URL=https://checkpoint-sync.holesky.ethpandaops.io
```

---

### keys - 密钥管理

**用途：** 生成、导入、查看验证者密钥

**语法：**
```bash
python3 cli.py keys [动作] [选项]
```

**动作：**
- `generate`: 生成新密钥
- `import`: 导入已有密钥
- `list`: 查看密钥列表

**选项：**

| 选项 | 说明 | 默认值 |
|------|------|--------|
| `--count` | 生成密钥数量 | 1 |
| `--network` | 网络名称 | holesky |
| `--withdrawal-address` | 提款地址 (0x...) | - |
| `--keys-path` | 导入密钥路径 | - |

#### 生成密钥

```bash
# 生成 1 个密钥
python3 cli.py keys generate --count 1 --network holesky

# 生成多个密钥
python3 cli.py keys generate --count 3 --network holesky

# 生成密钥并指定提款地址
python3 cli.py keys generate \
  --count 1 \
  --network mainnet \
  --withdrawal-address 0x1234...
```

**交互流程：**

```
1️⃣ 选择语言
   Please choose your language:
   1. English
   > 1

2️⃣ 创建助记词
   Creating your mnemonic...

   ⚠️  CRITICAL: Write down these 24 words!
   ┌────────────────────────────────────┐
   │ 1. word1    7. word7   13. word13 │
   │ 2. word2    8. word8   14. word14 │
   │ ...                                │
   └────────────────────────────────────┘

3️⃣ 设置密码
   Create a password for your keystore:
   > ********
   Repeat password:
   > ********

4️⃣ 确认助记词
   Type your mnemonic to confirm:
   > word1 word2 word3 ...

5️⃣ 生成完成
   ✅ Keys generated successfully!
```

**⚠️ 安全警告：**

| ⚠️ 重要提示 | 说明 |
|------------|------|
| **助记词** | • 24个单词，是恢复密钥的唯一方法<br>• 写在纸上，存放在安全的地方<br>• 永远不要截图、发邮件或保存在电脑上 |
| **密码** | • 用于加密 keystore 文件<br>• 使用强密码<br>• 记在密码管理器或安全的地方 |
| **提款地址** | • 一旦设置无法更改<br>• 必须是你控制的地址<br>• 建议使用硬件钱包地址 |

**生成的文件：**
```
~/eth-docker/.eth/validator_keys/
  ├── deposit_data-1234567890.json    # 上传到 Launchpad
  └── keystore-m_12345_0_0_0.json     # 验证者密钥（加密）
```

#### 查看密钥

```bash
python3 cli.py keys list
```

**输出：**
```
🔑 Validator Keys

Location: ~/eth-docker/.eth/validator_keys

Deposit Data Files:
  • deposit_data-1234567890.json

Keystore Files (1):
  • keystore-m_12345_0_0_0.json
```

#### 导入密钥

```bash
# 导入单个文件
python3 cli.py keys import --keys-path /path/to/keystore.json

# 导入整个目录
python3 cli.py keys import --keys-path /path/to/keys/
```

---

### deploy - 部署节点

**用途：** 启动 Docker 容器，部署验证节点

**语法：**
```bash
python3 cli.py deploy
```

**前置检查：**
- ✅ eth-docker 已安装
- ✅ 配置文件 (.env) 已存在
- ✅ Docker 正在运行

**部署流程：**

```
1️⃣ 检查前置条件
   ✅ All prerequisites met

2️⃣ 显示配置信息
   Network: holesky
   Client: lighthouse + Geth

3️⃣ 拉取 Docker 镜像
   📥 Pulling Docker images...
   (首次运行需要 5-10 分钟)

4️⃣ 启动服务
   🚀 Starting services...
   ✅ Services started successfully!

5️⃣ 显示后续步骤
   📋 Next steps:
   1. Wait for sync
   2. Import validator keys
   3. Monitor status
```

**启动的服务：**

| 服务 | 用途 | 端口 |
|------|------|------|
| **Execution Client (Geth)** | 执行层，处理交易 | 30303 |
| **Consensus Client** | 共识层，处理信标链 | 9000 |
| **Validator Client** | 验证者，提议和证明区块 | - |
| **Prometheus** | 监控指标收集 | 9090 |
| **Grafana** | 监控仪表板 | 3000 |

**⏱️ 同步时间：**

| 网络 | 执行层 | 共识层（有 Checkpoint Sync） |
|------|--------|----------------------------|
| Mainnet | 1-3 天 | 2-8 小时 |
| Holesky | 2-6 小时 | 30 分钟 - 2 小时 |
| Hoodi | 2-6 小时 | 30 分钟 - 2 小时 |
| Sepolia | 2-6 小时 | 30 分钟 - 2 小时 |

**部署后步骤：**

1. **等待同步完成**
   ```bash
   python3 cli.py status
   python3 cli.py logs -f
   ```

2. **导入验证者密钥**
   ```bash
   cp ~/eth-docker/.eth/validator_keys/keystore-*.json \
      ~/eth-docker/.eth/validators/
   ```

3. **重启以加载密钥**
   ```bash
   python3 cli.py stop
   python3 cli.py start
   ```

---

### status - 状态监控

**用途：** 查看节点运行状态

**语法：**
```bash
python3 cli.py status [选项]
```

**选项：**
- `--detailed`: 显示详细状态

**示例：**
```bash
# 基础状态
python3 cli.py status

# 详细状态
python3 cli.py status --detailed
```

**输出示例：**
```
🛰️  Staker Agent - Status

Network: holesky
Client: Lighthouse + Geth

Container Status:
┏━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━┳━━━━━━━━━━┓
┃ Service           ┃ Status      ┃ State    ┃
┡━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━╇━━━━━━━━━━┩
│ execution-client  │ Up 2 hours  │ running  │
│ consensus-client  │ Up 2 hours  │ running  │
│ validator-client  │ Up 2 hours  │ running  │
└───────────────────┴─────────────┴──────────┘

✅ Node is running

Useful commands:
  • View logs: python3 cli.py logs
  • Stop node: python3 cli.py stop
  • Grafana: http://localhost:3000
```

**状态说明：**

| 状态 | 含义 | 操作建议 |
|------|------|----------|
| 🟢 **running** | 正常运行 | 继续监控 |
| 🟡 **restarting** | 重启中 | 查看日志 |
| 🔴 **exited** | 已停止 | 检查错误 |
| ⚪ **created** | 已创建未启动 | 运行 start |

---

### logs - 日志查看

**用途：** 查看容器日志，排查问题

**语法：**
```bash
python3 cli.py logs [选项]
```

**选项：**

| 选项 | 说明 | 可选值 |
|------|------|--------|
| `--service` | 指定服务 | all, execution, consensus, validator |
| `-f, --follow` | 实时跟踪日志 | - |

**示例：**

```bash
# 查看所有日志（最近 50 行）
python3 cli.py logs

# 查看执行层日志
python3 cli.py logs --service execution

# 实时跟踪共识层日志
python3 cli.py logs --service consensus -f

# 实时跟踪验证者日志
python3 cli.py logs --service validator -f
```

**日志类型：**

**执行层（Geth）日志：**
```
INFO [01-01|12:00:00] Imported new chain segment
INFO [01-01|12:00:05] Syncing: chain download
INFO [01-01|12:00:10] Block synchronisation started
```

**共识层（Lighthouse）日志：**
```
INFO Syncing beacon chain
INFO Downloaded 1000 blocks
INFO Checkpoint sync complete
```

**验证者日志：**
```
INFO Successfully published attestation
INFO Validator balance increased
WARN Missed attestation (node not synced)
```

**常见日志含义：**

| 日志 | 含义 | 是否正常 |
|------|------|----------|
| "Syncing" | 正在同步 | ✅ 正常 |
| "Imported new block" | 导入新区块 | ✅ 正常 |
| "Published attestation" | 发布证明 | ✅ 正常 |
| "Missed attestation" | 错过证明 | ⚠️ 检查同步 |
| "Connection refused" | 连接失败 | ❌ 检查配置 |
| "Out of memory" | 内存不足 | ❌ 增加内存 |

---

### start / stop - 节点控制

**用途：** 启动或停止验证节点

**语法：**
```bash
# 启动节点
python3 cli.py start

# 停止节点
python3 cli.py stop
```

**使用场景：**
- 重新加载配置
- 导入新的验证者密钥
- 系统维护
- 更新客户端版本

**注意事项：**
- 停止节点会导致错过证明（主网会有小额罚款）
- 尽量在低活动时段操作
- 停止前确保已备份重要数据

---

## 💼 使用场景

### 场景 1: 新手测试 - Holesky 测试网

**目标：** 在测试网上学习验证节点操作

**步骤：**

```bash
# 1. 环境检查
python3 cli.py init

# 2. 安装
python3 cli.py setup --skip-docker

# 3. 配置
python3 cli.py configure --network holesky --client lighthouse

# 4. 生成密钥
python3 cli.py keys generate --count 1 --network holesky

# 5. 获取测试币
# 访问 https://faucet.holesky.ethpandaops.io
# 输入你的地址，获取 32 ETH

# 6. 上传 deposit_data.json
# 访问 https://holesky.launchpad.ethereum.org
# 上传文件并完成存款

# 7. 部署节点
python3 cli.py deploy

# 8. 监控状态
python3 cli.py status
python3 cli.py logs -f
```

**预期结果：**
- ✅ 节点正常运行
- ✅ 同步完成
- ✅ 验证者开始证明区块

**学习要点：**
- 了解完整流程
- 熟悉各个命令
- 观察日志输出
- 理解同步过程

---

### 场景 2: Lido CSM - 社区质押

**目标：** 参与 Lido 社区质押模块（CSM）

**背景：**
- Lido CSM 允许个人运行验证节点
- 需要的抵押品较少（1-2 ETH 而非 32 ETH）
- 获得 Lido 代币奖励

**步骤：**

```bash
# 1. 配置 Hoodi 网络（CSM 测试网）
python3 cli.py configure --network hoodi --client lighthouse

# 2. 生成密钥（注意提款地址）
python3 cli.py keys generate \
  --count 1 \
  --network hoodi \
  --withdrawal-address 0x你的地址

# 3. 访问 Lido CSM 平台
# https://csm.testnet.fi

# 4. 上传 deposit_data.json
# 完成 bond 抵押

# 5. 部署节点
python3 cli.py deploy

# 6. 验证配置
cat ~/eth-docker/.env | grep FEE_RECIPIENT
# 应该显示: FEE_RECIPIENT=0xE73a3602b99f1f913e72F8bdcBC235e206794Ac8
```

**Lido CSM 特殊配置：**
- ✅ 自动设置 Lido 的 fee recipient
- ✅ 自动配置 Hoodi 网络参数
- ✅ 提供 CSM 相关说明

**注意事项：**
- 提款地址一旦设置不能更改
- 需要满足 Lido 的 bond 要求
- 遵守 Lido 的验证者职责

---

### 场景 3: 主网部署 - 生产环境

**目标：** 在以太坊主网部署验证节点

**前置要求：**
- ✅ 拥有 32 ETH
- ✅ 在测试网上成功运行过
- ✅ 理解验证者职责和风险
- ✅ 准备好硬件（2TB SSD, 16GB RAM）

**步骤：**

```bash
# 1. 配置主网
python3 cli.py configure \
  --network mainnet \
  --client lighthouse \
  --fee-recipient 0x你的地址 \
  --withdrawal-address 0x你的安全地址

# 2. 生成密钥
python3 cli.py keys generate \
  --count 1 \
  --network mainnet \
  --withdrawal-address 0x你的硬件钱包地址

# 3. 备份密钥！
# - 复制 keystore 文件到多个安全位置
# - 写下助记词，存放在不同地方
# - 测试恢复流程

# 4. 访问主网 Launchpad
# https://launchpad.ethereum.org
# 仔细阅读所有警告和说明

# 5. 上传 deposit_data.json
# 使用 32 ETH 完成存款

# 6. 部署节点
python3 cli.py deploy

# 7. 持续监控
python3 cli.py status
python3 cli.py logs -f
```

**⚠️ 主网特别注意：**

| 警告 | 说明 |
|------|------|
| **资金安全** | • 使用硬件钱包作为提款地址<br>• 永远不要分享助记词<br>• 多重备份 |
| **Slashing 风险** | • 不要运行重复的验证者<br>• 不要导入相同密钥到多个节点<br>• 了解 slashing 条件 |
| **运行时间** | • 保持 99%+ 在线率<br>• 计划维护时间<br>• 准备备用方案 |
| **同步时间** | • 执行层：1-3 天<br>• 共识层：2-8 小时<br>• 提前开始同步 |

**生产环境清单：**

- [ ] 硬件符合要求（2TB SSD, 16GB RAM, 稳定网络）
- [ ] 已在测试网成功运行至少 1 周
- [ ] 备份了所有密钥和助记词
- [ ] 设置了监控和告警
- [ ] 理解 slashing 风险
- [ ] 准备了应急预案
- [ ] 加入了 EthStaker Discord 社区

---

### 场景 4: 多验证者部署

**目标：** 运行多个验证者（需要 N × 32 ETH）

**步骤：**

```bash
# 1. 配置网络
python3 cli.py configure --network mainnet --client lighthouse

# 2. 生成多个密钥
python3 cli.py keys generate \
  --count 10 \
  --network mainnet \
  --withdrawal-address 0x你的地址

# 3. 查看生成的密钥
python3 cli.py keys list
# 应该看到 10 个 keystore 文件

# 4. 批量上传到 Launchpad
# 上传 deposit_data.json（包含所有 10 个验证者）

# 5. 部署节点
python3 cli.py deploy

# 6. 导入所有密钥
cp ~/eth-docker/.eth/validator_keys/keystore-*.json \
   ~/eth-docker/.eth/validators/

# 7. 重启加载密钥
python3 cli.py stop && python3 cli.py start

# 8. 验证所有验证者都在运行
python3 cli.py logs --service validator
```

**扩展建议：**
- 为每个验证者设置独立的 fee recipient
- 使用专业的监控工具
- 考虑地理分布（多地点部署）
- 实施自动故障转移

---

## ❓ 常见问题

### 安装和配置

**Q1: 支持哪些操作系统？**

A:
- ✅ macOS (Intel 和 Apple Silicon)
- ✅ Linux (Ubuntu 22.04+, Debian 11+)
- ⚠️ Windows (需要 WSL2)

---

**Q2: Python 版本要求是什么？**

A: Python 3.10 或更高版本

检查版本：
```bash
python3 --version
```

安装 Python:
```bash
# macOS
brew install python3

# Ubuntu
sudo apt install python3 python3-pip
```

---

**Q3: 是否必须安装 Docker？**

A:
- `keys generate` 和 `deploy` 需要 Docker
- 其他命令不需要 Docker

可以先运行 `init`, `configure`, `validate` 测试工具

---

**Q4: eth-docker 安装在哪里？**

A: 默认安装在 `~/eth-docker`

查看：
```bash
ls -la ~/eth-docker
```

---

### 网络和客户端

**Q5: 应该选择哪个网络？**

| 情况 | 推荐网络 |
|------|----------|
| 第一次使用 | Holesky |
| 学习和测试 | Holesky |
| Lido CSM | Hoodi |
| 生产环境 | Mainnet |

---

**Q6: 应该选择哪个客户端？**

A: 推荐 **Lighthouse**
- 性能好
- 资源占用低
- 社区活跃
- 文档完善

其他选择：
- **Prysm**: 如果你喜欢 Go
- **Teku**: 企业级稳定性
- **Nimbus**: 低配置硬件

---

**Q7: 可以切换网络或客户端吗？**

A: 可以，重新运行 configure：

```bash
# 切换网络
python3 cli.py configure --network mainnet --client lighthouse

# 切换客户端
python3 cli.py configure --network holesky --client prysm
```

⚠️ 需要重新同步数据

---

### 密钥管理

**Q8: 助记词丢了怎么办？**

A: **无法恢复！**

助记词是恢复密钥的唯一方法。建议：
- 写在纸上
- 存在多个安全地方
- 考虑使用金属板刻录
- 永远不要数字化保存

---

**Q9: 忘记 keystore 密码怎么办？**

A: 如果有助记词，可以重新生成：
1. 使用原助记词
2. 重新运行 `keys generate`
3. 设置新密码

如果没有助记词：**无法恢复**

---

**Q10: 可以在多台机器上使用同一个密钥吗？**

A: **绝对不可以！**

这会导致 **Slashing**（大额罚款），可能损失：
- 测试网：验证者被禁用
- 主网：损失 1 ETH 或更多

---

**Q11: 提款地址可以更改吗？**

A: **不可以！**

提款地址在生成密钥时设置，永久有效。

建议使用：
- 硬件钱包地址
- 你完全控制的地址
- 安全性高的多签地址

---

### 部署和运行

**Q12: 同步需要多长时间？**

| 网络 | 执行层 | 共识层 |
|------|--------|--------|
| Mainnet | 1-3天 | 2-8小时 |
| Holesky | 2-6小时 | 30分钟-2小时 |

使用 Checkpoint Sync 可以大幅缩短共识层同步时间

---

**Q13: 如何知道同步完成？**

A: 查看日志：

```bash
python3 cli.py logs -f
```

执行层同步完成标志：
```
INFO Imported new chain segment
```

共识层同步完成标志：
```
INFO Synced, slot: 12345678
```

---

**Q14: 节点运行需要多少流量？**

A:
- **下载**: 10-50 GB/天（同步期间）
- **上传**: 5-20 GB/天
- **建议**: 不限流量的网络

---

**Q15: 可以在同一台机器上运行多个网络吗？**

A: 可以，但需要：
- 不同的 eth-docker 目录
- 不同的端口配置
- 足够的资源（内存、存储）

不推荐新手这样做。

---

### 维护和监控

**Q16: 如何查看验证者余额？**

A: 使用区块链浏览器：

- **Mainnet**: https://beaconcha.in
- **Holesky**: https://holesky.beaconcha.in

输入你的验证者公钥或索引

---

**Q17: 如何更新客户端版本？**

A:

```bash
# 1. 停止节点
python3 cli.py stop

# 2. 更新 eth-docker
cd ~/eth-docker
git pull

# 3. 拉取新镜像
docker compose pull

# 4. 启动节点
python3 cli.py start
```

---

**Q18: 节点离线会怎样？**

A:
- **测试网**: 无影响
- **主网**:
  - 错过证明：小额罚款（~0.000001 ETH/天）
  - 长期离线：更多罚款
  - 不会被 Slashing（除非双重签名）

---

**Q19: 如何备份节点？**

A: 需要备份：
- ✅ 助记词（24个单词）
- ✅ keystore 文件
- ✅ keystore 密码
- ✅ 配置文件 (.env)

不需要备份：
- ❌ 区块链数据（可以重新同步）
- ❌ Docker 镜像

---

**Q20: 如何迁移到新机器？**

A:

```bash
# 在新机器上
# 1. 安装 staker-agent
cd ~
git clone https://github.com/你的用户名/staker-agent.git
cd staker-agent
pip install -r requirements.txt

# 2. 安装依赖
python3 cli.py setup

# 3. 恢复配置
# 复制旧机器的 ~/eth-docker/.env

# 4. 导入密钥
python3 cli.py keys import --keys-path /path/to/backup/

# 5. 部署节点
python3 cli.py deploy

# 重要：停止旧机器上的节点！
```

---

## 🔧 故障排除

### 问题诊断流程

```
遇到问题
    │
    ├─→ 1. 查看状态
    │   python3 cli.py status
    │
    ├─→ 2. 查看日志
    │   python3 cli.py logs
    │
    ├─→ 3. 验证配置
    │   python3 cli.py validate
    │
    ├─→ 4. 重启节点
    │   python3 cli.py stop
    │   python3 cli.py start
    │
    └─→ 5. 寻求帮助
        - 查看文档
        - 搜索错误信息
        - EthStaker Discord
```

---

### 常见错误

#### 错误 1: "Docker is not installed"

**症状：**
```
❌ Docker is not installed or not running.
Please install Docker and try again.
```

**解决方案：**

```bash
# macOS
brew install --cask docker
open -a Docker

# Ubuntu
sudo apt update
sudo apt install docker.io docker-compose
sudo systemctl start docker
sudo usermod -aG docker $USER
# 注销并重新登录

# 验证
docker --version
```

---

#### 错误 2: "Configuration file not found"

**症状：**
```
❌ .env configuration file not found
```

**解决方案：**

```bash
# 重新生成配置
python3 cli.py configure --network holesky --client lighthouse

# 验证
ls -la ~/eth-docker/.env
```

---

#### 错误 3: "Container failed to start"

**症状：**
```
Error: container execution-client failed to start
```

**解决方案：**

```bash
# 1. 查看详细日志
python3 cli.py logs --service execution

# 2. 检查端口占用
sudo lsof -i :30303
sudo lsof -i :9000

# 3. 清理并重启
cd ~/eth-docker
docker compose down
docker compose up -d
```

---

#### 错误 4: "Out of disk space"

**症状：**
```
ERROR: No space left on device
```

**解决方案：**

```bash
# 1. 检查磁盘使用
df -h

# 2. 清理 Docker
docker system prune -a

# 3. 清理旧的链数据（如果切换了网络）
rm -rf ~/eth-docker/.eth/execution-data/*
rm -rf ~/eth-docker/.eth/consensus-data/*

# 4. 考虑升级存储
```

---

#### 错误 5: "Checkpoint sync failed"

**症状：**
```
ERROR: Failed to download checkpoint state
```

**解决方案：**

```bash
# 1. 检查网络连接
ping checkpoint-sync.holesky.ethpandaops.io

# 2. 尝试其他 checkpoint sync 服务器
# 编辑 ~/eth-docker/.env
# 修改 CHECKPOINT_SYNC_URL

# 3. 或者禁用 checkpoint sync（会更慢）
# 在 .env 中设置：
CHECKPOINT_SYNC=false
```

---

#### 错误 6: "Missed attestations"

**症状：**
```
WARN: Missed attestation
```

**原因：**
- 节点未同步
- 网络延迟
- 硬件性能不足

**解决方案：**

```bash
# 1. 检查同步状态
python3 cli.py status

# 2. 查看日志
python3 cli.py logs --service consensus -f

# 3. 检查系统资源
htop  # 查看 CPU/内存使用

# 4. 检查网络
ping 8.8.8.8
```

---

### 日志分析

**如何阅读日志：**

```bash
# 实时查看所有日志
python3 cli.py logs -f

# 只看错误
python3 cli.py logs | grep ERROR

# 只看警告
python3 cli.py logs | grep WARN

# 查看特定服务
python3 cli.py logs --service execution
```

**关键日志模式：**

| 日志 | 含义 | 操作 |
|------|------|------|
| `Syncing` | 正在同步 | 等待 |
| `Imported new block` | 正常工作 | 无需操作 |
| `Published attestation` | 验证者正常 | 无需操作 |
| `ERROR: Connection refused` | 连接失败 | 检查配置 |
| `WARN: Missed attestation` | 错过证明 | 检查同步 |
| `Fatal: Out of memory` | 内存不足 | 增加内存 |

---

### 性能优化

**优化同步速度：**

1. **使用 SSD**
   - NVMe > SATA SSD > HDD
   - 执行层对磁盘 I/O 要求高

2. **启用 Checkpoint Sync**
   ```bash
   # 在 .env 中确认：
   CHECKPOINT_SYNC=true
   CHECKPOINT_SYNC_URL=https://...
   ```

3. **增加对等节点数**
   ```bash
   # 在 .env 中添加：
   EL_MAX_PEERS=50
   CL_TARGET_PEERS=80
   ```

**优化资源使用：**

```bash
# 限制内存使用（在 .env 中）
EL_MEMORY_LIMIT=8g
CL_MEMORY_LIMIT=4g

# 限制 CPU
# 在 docker-compose.yml 中添加：
cpus: '2.0'
```

---

### 获取帮助

**社区资源：**

1. **EthStaker Discord**
   - https://discord.gg/ethstaker
   - #software 频道
   - 最活跃的以太坊质押社区

2. **eth-docker 文档**
   - https://ethdocker.com
   - 详细的技术文档

3. **GitHub Issues**
   - https://github.com/eth-educators/eth-docker/issues
   - 搜索已知问题

4. **Reddit**
   - r/ethstaker
   - 社区讨论和经验分享

**提问技巧：**

提供以下信息：
- 操作系统和版本
- 执行的命令
- 完整的错误信息
- 相关日志（最近 50 行）
- 已经尝试的解决方案

---

## 🔒 安全最佳实践

### 密钥安全

#### 助记词（Mnemonic）

**⚠️ 最高优先级！**

✅ **应该做：**
- 写在纸上，使用钢笔
- 存放在防火防水的保险箱
- 制作多个副本，存在不同地点
- 考虑使用金属板刻录（防火防水）
- 使用 BIP39 词汇表验证拼写

❌ **绝对不要：**
- 截图或拍照
- 保存在电脑、手机、云盘
- 通过邮件、聊天软件发送
- 告诉任何人（包括技术支持）
- 输入到任何网站（除了官方工具）

**测试恢复：**
```bash
# 定期测试恢复流程
# 在测试环境中使用助记词恢复密钥
# 确保能够成功恢复
```

---

#### Keystore 文件和密码

**Keystore 文件：**
- 加密的验证者私钥
- 需要密码才能解密
- 应该备份到安全位置

**密码要求：**
- 至少 12 个字符
- 包含大小写字母、数字、符号
- 不要使用字典单词
- 使用密码管理器生成和保存

**备份位置：**
```
推荐的备份方案：
1. 主备份：硬件钱包或离线电脑
2. 副备份：加密的 USB 驱动器
3. 云备份：加密后上传（可选）
```

---

#### 提款地址

**选择提款地址：**
- ✅ 硬件钱包地址
- ✅ 你完全控制的地址
- ✅ 多签钱包（团队使用）
- ❌ 交易所地址
- ❌ 他人的地址

**验证地址：**
```bash
# 生成密钥时仔细检查地址
# 复制粘贴，不要手动输入
# 多次验证前几位和后几位
```

**注意：**
- 提款地址一旦设置无法更改
- 错误的地址可能导致永久损失
- 三次确认再继续

---

### 服务器安全

#### SSH 安全

**如果使用远程服务器：**

```bash
# 1. 使用 SSH 密钥认证
ssh-keygen -t ed25519
ssh-copy-id user@server

# 2. 禁用密码登录
# 编辑 /etc/ssh/sshd_config
PasswordAuthentication no
PermitRootLogin no

# 3. 更改默认端口
Port 2222

# 4. 使用防火墙
sudo ufw allow 2222/tcp
sudo ufw allow 30303/tcp
sudo ufw allow 9000/tcp
sudo ufw enable
```

**定期更新：**
```bash
# Ubuntu
sudo apt update && sudo apt upgrade -y

# 重启（如果需要）
sudo reboot
```

---

#### 网络安全

**防火墙配置：**
```bash
# 允许必要的端口
sudo ufw allow 30303/tcp  # Execution P2P
sudo ufw allow 30303/udp
sudo ufw allow 9000/tcp   # Consensus P2P
sudo ufw allow 9000/udp

# 仅允许本地访问监控
sudo ufw allow from 127.0.0.1 to any port 9090  # Prometheus
sudo ufw allow from 127.0.0.1 to any port 3000  # Grafana

# 启用防火墙
sudo ufw enable
```

**监控可疑活动：**
```bash
# 查看登录尝试
sudo tail -f /var/log/auth.log

# 查看活动连接
sudo netstat -tuln
```

---

#### Docker 安全

**最佳实践：**

```bash
# 1. 定期更新镜像
docker compose pull

# 2. 清理未使用的资源
docker system prune -a

# 3. 限制资源使用
# 在 .env 中设置：
EL_MEMORY_LIMIT=8g
CL_MEMORY_LIMIT=4g

# 4. 使用只读文件系统（高级）
# 在 docker-compose.yml 中添加：
read_only: true
```

---

### 操作安全

#### 防止 Slashing

**Slashing 是什么？**
- 因为验证者行为不当而受到的罚款
- 可能损失 1 ETH 或更多
- 验证者会被强制退出

**主要原因：**
1. **双重签名**：在多个节点上使用相同密钥
2. **环绕投票**：证明冲突的区块

**如何避免：**
- ✅ 只在一台机器上运行每个验证者
- ✅ 迁移前停止旧节点
- ✅ 使用 doppelganger protection
- ✅ 备份时不要导入到运行的节点

**启用 Doppelganger Protection：**
```bash
# 在 .env 中设置：
DOPPELGANGER=true
```

---

#### 监控和告警

**设置监控：**

1. **使用 Grafana**
   ```bash
   # 访问 http://localhost:3000
   # 默认用户名/密码: admin/admin
   ```

2. **监控指标：**
   - 验证者余额
   - 证明成功率
   - 同步状态
   - 系统资源使用

3. **设置告警：**
   - 验证者离线
   - 余额下降
   - 错过证明
   - 磁盘空间不足

**第三方监控：**
- **beaconcha.in**: 免费的验证者监控
  - 设置邮件/电报告警
  - 跟踪性能
  - 查看奖励历史

---

### 备份和恢复

#### 备份清单

**必须备份：**
- ✅ 助记词（24个单词）
- ✅ Keystore 文件
- ✅ Keystore 密码
- ✅ 配置文件 (.env)
- ✅ Withdrawal 地址

**可选备份：**
- 📝 Slashing protection 数据
- 📝 监控配置

**不需要备份：**
- ❌ 区块链数据
- ❌ Docker 镜像

---

#### 备份方案

**3-2-1 备份原则：**
- 3 份副本
- 2 种介质（如纸张+USB）
- 1 份异地保存

**推荐方案：**

```
主备份（在家）：
  - 助记词：防火保险箱
  - Keystore：加密USB驱动器
  - 配置：打印纸张

副备份（异地）：
  - 助记词：银行保险箱
  - Keystore：加密云存储

应急备份：
  - 助记词：可信家人处（密封信封）
```

---

#### 恢复演练

**定期测试恢复：**

```bash
# 1. 在测试环境中
cd ~/staker-agent-test
python3 cli.py keys generate

# 2. 使用备份的助记词恢复

# 3. 验证生成的密钥与原始密钥匹配

# 4. 删除测试环境
rm -rf ~/staker-agent-test
```

**建议频率：**
- 首次备份后：立即测试
- 之后：每 6 个月一次
- 迁移前：必须测试

---

## 📚 附录

### A. 网络参数对照表

| 参数 | Mainnet | Holesky | Hoodi | Sepolia |
|------|---------|---------|-------|---------|
| Network ID | 1 | 17000 | 17001 | 11155111 |
| Deposit Contract | 0x00000000219ab540... | 0x4242424242... | 0x4242424242... | 0x7f02C3E3c98b... |
| Genesis Fork | 0x00000000 | 0x01017000 | 0x10017000 | 0x90000069 |
| Checkpoint Sync | beaconstate.ethstaker.cc | checkpoint-sync.holesky | checkpoint-sync.hoodi.lido.fi | checkpoint-sync.sepolia |
| Block Explorer | etherscan.io | holesky.etherscan.io | - | sepolia.etherscan.io |
| Beacon Explorer | beaconcha.in | holesky.beaconcha.in | - | sepolia.beaconcha.in |
| Faucet | - | faucet.holesky | csm.testnet.fi | sepoliafaucet.com |

---

### B. 硬件推荐配置

#### 预算配置（测试网）

**适用于：** Holesky, Hoodi, Sepolia

| 组件 | 配置 | 价格 |
|------|------|------|
| CPU | Intel i3 / AMD Ryzen 3 | ~$100 |
| 内存 | 8GB DDR4 | ~$30 |
| 存储 | 256GB SSD | ~$30 |
| 网络 | 以太网 | - |
| **总计** | | **~$160** |

**推荐机型：**
- Intel NUC
- 树莓派 4 (8GB)
- 旧笔记本电脑

---

#### 标准配置（主网）

**适用于：** Mainnet（单个验证者）

| 组件 | 配置 | 价格 |
|------|------|------|
| CPU | Intel i5 / AMD Ryzen 5 | ~$200 |
| 内存 | 16GB DDR4 | ~$60 |
| 存储 | 2TB NVMe SSD | ~$150 |
| 网络 | 千兆以太网 | - |
| 电源 | UPS 备用电源 | ~$100 |
| **总计** | | **~$510** |

**推荐机型：**
- Intel NUC Pro
- 自组装 Mini-ITX
- Dell/HP 小型工作站

---

#### 专业配置（多验证者）

**适用于：** Mainnet（10+ 验证者）

| 组件 | 配置 | 价格 |
|------|------|------|
| CPU | Intel i7 / AMD Ryzen 7 | ~$350 |
| 内存 | 32GB DDR4 | ~$120 |
| 存储 | 4TB NVMe SSD | ~$300 |
| 网络 | 双千兆以太网 | ~$50 |
| 电源 | 企业级 UPS | ~$300 |
| **总计** | | **~$1120** |

**推荐机型：**
- 服务器级硬件
- Dell PowerEdge
- HP ProLiant MicroServer

---

### C. 成本对比分析

#### 本地部署 vs 云服务器

**本地部署（Mainnet）：**

| 项目 | 成本 |
|------|------|
| 硬件（一次性） | ~$500 |
| 电费（月） | ~$10 |
| 网络（月） | $0 (已有) |
| **年成本** | **~$620** |
| **5年总成本** | **~$1,100** |

---

**云服务器（Mainnet）：**

| 项目 | 成本 |
|------|------|
| AWS c5.2xlarge | $240/月 |
| 2TB EBS存储 | $200/月 |
| 网络流量 | $50/月 |
| **年成本** | **~$5,880** |
| **5年总成本** | **~$29,400** |

---

**结论：**
- 本地部署 5 年节省 **$28,300**
- 投资回收期：~2 个月
- 更好的去中心化
- 完全的控制权

---

### D. 术语表

| 术语 | 说明 |
|------|------|
| **Validator** | 验证者，质押 32 ETH 的节点 |
| **Attestation** | 证明，验证者对区块的投票 |
| **Proposal** | 提议，验证者提议新区块 |
| **Slashing** | 罚没，因违规而被罚款 |
| **Sync Committee** | 同步委员会，帮助轻客户端同步 |
| **Deposit** | 存款，质押的 32 ETH |
| **Withdrawal** | 提款，取回质押的 ETH |
| **Execution Layer** | 执行层，处理交易（Geth） |
| **Consensus Layer** | 共识层，处理信标链（Lighthouse） |
| **Beacon Chain** | 信标链，以太坊 PoS 链 |
| **Checkpoint Sync** | 检查点同步，快速同步方式 |
| **MEV** | 最大可提取价值 |
| **Fee Recipient** | 费用接收地址 |
| **Withdrawal Address** | 提款地址 |
| **Keystore** | 密钥库，加密的私钥文件 |
| **Mnemonic** | 助记词，24个单词 |
| **Doppelganger** | 重复验证者检测 |

---

### E. 有用的链接

#### 官方资源

- **以太坊官网**: https://ethereum.org
- **Ethereum Launchpad**: https://launchpad.ethereum.org
- **eth-docker**: https://ethdocker.com
- **Lido CSM**: https://csm.lido.fi

#### 社区

- **EthStaker Discord**: https://discord.gg/ethstaker
- **Reddit r/ethstaker**: https://reddit.com/r/ethstaker
- **EthStaker 知识库**: https://docs.ethstaker.cc

#### 工具

- **Beaconcha.in**: https://beaconcha.in（区块浏览器）
- **Etherscan**: https://etherscan.io（交易浏览器）
- **Rated.network**: https://rated.network（性能评分）

#### 测试网 Faucets

- **Holesky**: https://faucet.holesky.ethpandaops.io
- **Sepolia**: https://sepoliafaucet.com
- **Hoodi**: https://csm.testnet.fi

#### 学习资源

- **Ethereum.org Staking**: https://ethereum.org/staking
- **EthStaker 指南**: https://docs.ethstaker.cc/ethstaker-knowledge-base/
- **Vitalik's Blog**: https://vitalik.ca

---

### F. 更新日志

#### v0.1.0 (2025-10-01)

**新功能：**
- ✅ 初始发布
- ✅ 支持 4 个网络（Mainnet, Holesky, Hoodi, Sepolia）
- ✅ 支持 4 个客户端（Lighthouse, Prysm, Teku, Nimbus）
- ✅ 完整的 CLI 工具
- ✅ 自动化配置生成
- ✅ 密钥管理
- ✅ 节点部署和监控

**已知问题：**
- 无

**路线图：**
- v0.2.0: Web UI
- v0.3.0: 自动更新
- v0.4.0: 多节点管理

---

### G. 支持和反馈

**获取帮助：**
- 📧 Email: support@staker-agent.com
- 💬 Discord: https://discord.gg/staker-agent
- 🐛 GitHub Issues: https://github.com/你的用户名/staker-agent/issues

**贡献：**
- 🌟 Star 项目
- 🐛 报告 Bug
- 💡 提出功能建议
- 📝 改进文档
- 💻 提交代码

**许可证：**
- Apache License v2.0

---

## 📄 结语

感谢使用 **Staker Agent**！

这个工具的目标是让每个人都能参与以太坊的去中心化验证，无论技术背景如何。

如果这个工具帮助了你，请：
- ⭐ 给项目一个 Star
- 📢 分享给其他人
- 💬 提供反馈和建议

**Happy Staking! 🚀**

---

*最后更新: 2025-10-01*
*版本: v0.1.0*
*文档版本: 1.0*
