# GCP 部署测试指南

在 Google Cloud Platform (GCP) 上测试 Staker Agent 的完整步骤。

---

## 📋 前置要求

- GCP 账户（有 $300 免费额度）
- 安装 `gcloud` CLI 工具
- 本地 Git 和 SSH 配置完成

---

## 🚀 快速开始

### 方法 1: Web 控制台（推荐新手）

按照 [Web 控制台步骤](#方法-1-通过-web-控制台) 操作。

### 方法 2: gcloud CLI（推荐开发者）

```bash
# 一键创建并配置 VM
curl -O https://raw.githubusercontent.com/HeliosLz/staker-agent/main/scripts/gcp-setup.sh
chmod +x gcp-setup.sh
./gcp-setup.sh
```

---

## 📝 详细步骤

### 步骤 1: 创建 GCP VM 实例

#### 方法 1: 通过 Web 控制台

1. **登录 GCP Console**
   - 访问: https://console.cloud.google.com
   - 选择或创建项目

2. **创建 VM 实例**
   - 导航: `Compute Engine` → `VM instances` → `CREATE INSTANCE`

3. **配置实例**
   ```
   名称: staker-agent-test
   区域: us-central1 (或离你最近的区域)
   可用区: us-central1-a

   机器配置:
   - 机器系列: N2
   - 机器类型: n2-standard-4
     • 4 vCPU
     • 16 GB 内存

   启动磁盘:
   - 操作系统: Ubuntu
   - 版本: Ubuntu 22.04 LTS
   - 启动磁盘类型: SSD 永久性磁盘
   - 大小: 500 GB

   防火墙:
   ☑️ 允许 HTTP 流量
   ☑️ 允许 HTTPS 流量
   ```

4. **点击 "创建"**

#### 方法 2: 使用 gcloud CLI

```bash
# 设置项目
gcloud config set project YOUR_PROJECT_ID

# 创建 VM 实例
gcloud compute instances create staker-agent-test \
  --zone=us-central1-a \
  --machine-type=n2-standard-4 \
  --image-family=ubuntu-2204-lts \
  --image-project=ubuntu-os-cloud \
  --boot-disk-size=500GB \
  --boot-disk-type=pd-ssd \
  --tags=http-server,https-server

# 配置防火墙规则（如需要）
gcloud compute firewall-rules create allow-staker-agent \
  --allow=tcp:30303,tcp:9000,tcp:3000,tcp:5173,tcp:5001 \
  --source-ranges=0.0.0.0/0 \
  --target-tags=http-server
```

---

### 步骤 2: 连接到 VM

#### 通过 gcloud SSH

```bash
gcloud compute ssh staker-agent-test --zone=us-central1-a
```

#### 通过 Web SSH

在 GCP Console 的 VM 实例页面，点击实例旁边的 "SSH" 按钮。

---

### 步骤 3: 安装依赖

连接到 VM 后，运行以下命令：

```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装 Python 3 和 pip
sudo apt install -y python3 python3-pip git

# 安装 Docker
sudo apt install -y docker.io docker-compose-v2

# 启动 Docker 服务
sudo systemctl start docker
sudo systemctl enable docker

# 将当前用户添加到 docker 组
sudo usermod -aG docker $USER

# 刷新用户组（避免需要重新登录）
newgrp docker

# 验证安装
docker --version
docker compose version
python3 --version
```

**预期输出**:
```
Docker version 24.0.x
Docker Compose version v2.x.x
Python 3.10.x
```

---

### 步骤 4: 克隆项目并安装

```bash
# 克隆 Staker Agent 项目
git clone https://github.com/HeliosLz/staker-agent.git
cd staker-agent

# 安装 Python 依赖
pip3 install -r requirements.txt

# 验证安装
python3 cli.py --help
```

---

### 步骤 5: 运行 Staker Agent

#### 5.1 环境检查

```bash
python3 cli.py check
```

**预期输出**:
```
🔍 Running Environment Checks...

┏━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━┓
┃ Component       ┃ Details                  ┃ Status ┃
┡━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━┩
│ Os              │ Linux 5.15.x             │ ✅     │
│ Python          │ Python 3.10.x            │ ✅     │
│ Docker          │ Docker version 24.0.x    │ ✅     │
│ Docker Daemon   │ Docker Daemon            │ ✅     │
│ Disk Space      │ Disk Space (450GB+)      │ ✅     │
│ Network         │ Internet Connection      │ ✅     │
└─────────────────┴──────────────────────────┴────────┘

✅ All checks passed! Ready to proceed.
```

#### 5.2 初始化

```bash
python3 cli.py init
```

这将克隆 `eth-docker` 到 `~/eth-docker`。

#### 5.3 配置节点

```bash
python3 cli.py configure
```

**交互式配置**:
```
🔧 Staker Agent - Configure Validator Node

1️⃣  Select Network
   1. Mainnet (Production - Real ETH)
   2. Holesky (Testnet - Free test ETH) ← 推荐测试
   3. Sepolia (Testnet - Free test ETH)

Choose network (1-3): 2

2️⃣  Select Consensus Client
   1. Lighthouse (Rust, Fast, Recommended)
   2. Prysm (Go, Popular)
   3. Teku (Java, Enterprise)
   4. Nimbus (Nim, Lightweight)

Choose client (1-4): 1

3️⃣  Select Execution Client
   1. Geth (Go Ethereum, Most popular)

Choose client (1): 1

4️⃣  Monitoring Setup
   Enable Grafana dashboard? (y/n): y

5️⃣  Checkpoint Sync
   Enable checkpoint sync for faster initial sync? (y/n): y
```

#### 5.4 部署节点

```bash
python3 cli.py deploy
```

**预期流程**:
```
🛰️  Staker Agent - Deploy

Checking prerequisites...
✅ All prerequisites met

Deployment Configuration:
  • Network: holesky
  • Client: Lighthouse + Geth
  • Location: /home/username/eth-docker

Services to deploy:
  • Execution Layer (Geth)
  • Consensus Layer (Beacon Node)
  • Validator Client
  • Prometheus (Metrics)
  • Grafana (Dashboard)

Start deployment? [Y/n]: y

📥 Pulling Docker images...
This may take several minutes on first run...

✅ Images pulled successfully

🚀 Starting services...

✅ Services started successfully!

═══════════════════════════════════════════════════════════
🎉 Deployment Complete!
═══════════════════════════════════════════════════════════
```

#### 5.5 检查状态

```bash
python3 cli.py status
```

#### 5.6 查看日志

```bash
# 查看所有服务日志
python3 cli.py logs

# 查看特定服务日志
python3 cli.py logs --service consensus

# 实时跟踪日志
python3 cli.py logs --follow
```

---

### 步骤 6: 访问 Web UI（可选）

如果你想使用 Web UI 界面：

#### 6.1 启动 Web UI

```bash
cd /home/username/staker-agent/web
./start.sh
```

#### 6.2 配置 SSH 隧道

由于 VM 默认不开放 5173 和 5001 端口，需要通过 SSH 隧道访问：

```bash
# 在本地机器上运行（新终端）
gcloud compute ssh staker-agent-test \
  --zone=us-central1-a \
  -- -L 5173:localhost:5173 -L 5001:localhost:5001
```

#### 6.3 访问 Web UI

在本地浏览器打开:
- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:5001

---

## 📊 访问监控面板

### Grafana Dashboard

1. **配置 SSH 隧道**
   ```bash
   # 在本地机器运行
   gcloud compute ssh staker-agent-test \
     --zone=us-central1-a \
     -- -L 3000:localhost:3000
   ```

2. **访问 Grafana**
   - URL: http://localhost:3000
   - 默认用户名: `admin`
   - 默认密码: `admin`（首次登录需修改）

3. **查看仪表盘**
   - 导航到 `Dashboards` → `Ethereum Staking`

---

## 🧪 运行测试

### 测试部署流程

```bash
# 停止服务
python3 cli.py stop

# 重新启动
python3 cli.py start

# 检查状态
python3 cli.py status

# 查看资源使用
docker stats
```

### 测试网络连接

```bash
# 检查执行层同步
docker logs execution -f

# 检查共识层同步
docker logs consensus -f

# 检查验证器状态
docker logs validator -f
```

---

## 💰 成本估算

### 测试网部署（Holesky）

**n2-standard-4 实例 (us-central1)**:
- 计算: ~$0.19/小时 × 24 = ~$4.56/天
- 存储 (500GB SSD): ~$0.17/GB/月 = ~$85/月 ≈ $2.83/天
- 网络: ~$0.50/天（估算）
- **总计**: ~$7.89/天 ≈ $237/月

### 节省成本建议

1. **使用抢占式 VM (Preemptible VM)**
   ```bash
   gcloud compute instances create staker-agent-test \
     --preemptible \
     # ... 其他参数
   ```
   成本降低 60-91%，但实例可能随时被终止（仅适合测试）

2. **使用较小的实例**
   - 测试时可用 `n2-standard-2` (2 vCPU, 8GB)
   - 成本减半

3. **及时停止实例**
   ```bash
   # 停止实例（保留磁盘）
   gcloud compute instances stop staker-agent-test --zone=us-central1-a

   # 启动实例
   gcloud compute instances start staker-agent-test --zone=us-central1-a
   ```

4. **测试完成后删除**
   ```bash
   gcloud compute instances delete staker-agent-test --zone=us-central1-a
   ```

---

## 🔥 防火墙配置

### 必需端口（仅用于 P2P 连接）

```bash
# 执行层 P2P (Geth)
gcloud compute firewall-rules create allow-geth-p2p \
  --allow=tcp:30303,udp:30303 \
  --source-ranges=0.0.0.0/0 \
  --target-tags=http-server

# 共识层 P2P (Lighthouse)
gcloud compute firewall-rules create allow-lighthouse-p2p \
  --allow=tcp:9000,udp:9000 \
  --source-ranges=0.0.0.0/0 \
  --target-tags=http-server
```

### 可选端口（用于远程访问）

```bash
# Grafana (仅在需要远程访问时)
gcloud compute firewall-rules create allow-grafana \
  --allow=tcp:3000 \
  --source-ranges=YOUR_IP_ADDRESS/32 \
  --target-tags=http-server

# Web UI (仅在需要远程访问时)
gcloud compute firewall-rules create allow-web-ui \
  --allow=tcp:5173,tcp:5001 \
  --source-ranges=YOUR_IP_ADDRESS/32 \
  --target-tags=http-server
```

⚠️ **安全建议**: 优先使用 SSH 隧道而非直接开放端口。

---

## 🐛 故障排查

### 问题 1: Docker 权限错误

**错误**:
```
Got permission denied while trying to connect to the Docker daemon socket
```

**解决**:
```bash
sudo usermod -aG docker $USER
newgrp docker
# 或者重新登录 SSH
```

### 问题 2: 磁盘空间不足

**检查磁盘使用**:
```bash
df -h
docker system df
```

**清理 Docker**:
```bash
docker system prune -a
```

### 问题 3: 同步速度慢

**检查同步状态**:
```bash
# 执行层
docker logs execution 2>&1 | grep "Syncing"

# 共识层
docker logs consensus 2>&1 | grep "peers"
```

**解决**:
- 确保启用了 checkpoint sync
- 检查防火墙规则（P2P 端口必须开放）
- 检查网络连接速度

### 问题 4: 服务无法启动

**检查日志**:
```bash
docker compose logs
python3 cli.py logs
```

**重启服务**:
```bash
python3 cli.py stop
python3 cli.py start
```

---

## 📚 相关资源

- **GCP 文档**: https://cloud.google.com/compute/docs
- **eth-docker**: https://eth-docker.net
- **Staker Agent GitHub**: https://github.com/HeliosLz/staker-agent
- **Holesky Testnet**: https://holesky.ethpandaops.io

---

## ✅ 完成检查清单

部署成功后，确认以下内容：

- [ ] VM 实例运行正常
- [ ] Docker 服务运行中
- [ ] 环境检查全部通过
- [ ] eth-docker 已安装
- [ ] 节点配置完成
- [ ] Docker 容器全部运行
- [ ] 执行层开始同步
- [ ] 共识层开始同步
- [ ] P2P 端口连接正常（有 peers）
- [ ] 监控面板可访问（如启用）
- [ ] Web UI 可访问（如启用）

---

## 🎯 下一步

1. **等待同步完成**
   - 测试网通常需要 2-6 小时
   - 使用 `python3 cli.py status` 监控进度

2. **导入验证器密钥**（如有）
   - 参考主文档的密钥管理部分

3. **监控节点健康状况**
   - 定期检查日志
   - 监控资源使用

4. **测试完成后清理**
   ```bash
   # 停止服务
   python3 cli.py stop

   # 删除 VM 实例
   gcloud compute instances delete staker-agent-test --zone=us-central1-a
   ```

---

**祝测试顺利！** 🚀

如有问题，请在 GitHub 提 issue: https://github.com/HeliosLz/staker-agent/issues
