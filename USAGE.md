# 🛰️ Staker Agent - 使用指南

## 快速开始

### 1️⃣ 初始化环境检查

```bash
cd ~/staker-agent
python3 cli.py init
```

检查你的系统是否满足运行要求：
- ✅ 操作系统（macOS / Linux / Windows）
- ✅ Python 版本
- ✅ Docker 安装状态
- ✅ 磁盘空间
- ✅ 网络连接

### 2️⃣ 安装依赖

```bash
python3 cli.py setup
```

自动安装：
- Docker Desktop（macOS/Windows）
- eth-docker（所有平台）

**跳过 Docker 安装：**
```bash
python3 cli.py setup --skip-docker
```

### 3️⃣ 配置节点

```bash
# 基本用法
python3 cli.py configure --network holesky --client lighthouse

# 所有选项
python3 cli.py configure \
  --network holesky \
  --client lighthouse \
  --fee-recipient 0x... \
  --withdrawal-address 0x...

# 交互式配置
python3 cli.py configure -i
```

**支持的网络：**
- `mainnet` - 以太坊主网
- `holesky` - Holesky 测试网（推荐测试）
- `hoodi` - Lido CSM 测试网
- `sepolia` - Sepolia 测试网

**支持的客户端：**
- `lighthouse` - Lighthouse（推荐）
- `prysm` - Prysm
- `teku` - Teku
- `nimbus` - Nimbus

### 4️⃣ 生成 Validator 密钥

```bash
# 生成 1 个验证者密钥
python3 cli.py keys generate --count 1 --network holesky

# 生成多个密钥
python3 cli.py keys generate --count 3 --network holesky

# 指定提款地址
python3 cli.py keys generate \
  --count 1 \
  --network holesky \
  --withdrawal-address 0x...

# 查看已生成的密钥
python3 cli.py keys list

# 导入已有密钥
python3 cli.py keys import --keys-path /path/to/keys
```

**⚠️ 重要提示：**
- 妥善保管助记词（24个单词）
- 记住 keystore 密码
- 备份所有密钥文件
- 提款地址一旦设置无法更改

### 5️⃣ 部署节点

```bash
python3 cli.py deploy
```

### 6️⃣ 监控状态

```bash
# 查看节点状态
python3 cli.py status

# 查看详细状态
python3 cli.py status --detailed

# 查看日志
python3 cli.py logs

# 查看特定服务日志
python3 cli.py logs --service execution
python3 cli.py logs --service consensus
python3 cli.py logs --service validator

# 实时查看日志
python3 cli.py logs -f
```

### 7️⃣ 节点管理

```bash
# 停止节点
python3 cli.py stop

# 启动节点
python3 cli.py start
```

## 完整示例

### 场景 1: Holesky 测试网部署

```bash
# 步骤 1: 检查环境
python3 cli.py init

# 步骤 2: 安装
python3 cli.py setup

# 步骤 3: 配置
python3 cli.py configure --network holesky --client lighthouse

# 步骤 4: 生成密钥
python3 cli.py keys generate --count 1 --network holesky

# 步骤 5: 上传 deposit_data.json 到测试网 Launchpad
# https://holesky.launchpad.ethereum.org

# 步骤 6: 部署节点
python3 cli.py deploy

# 步骤 7: 查看状态
python3 cli.py status
```

### 场景 2: Lido CSM 部署（Hoodi 网络）

```bash
# 配置 Hoodi 网络
python3 cli.py configure --network hoodi --client lighthouse

# 生成密钥（CSM 需要特定的提款地址）
python3 cli.py keys generate \
  --count 1 \
  --network hoodi \
  --withdrawal-address 0xYourAddress

# 上传 deposit_data.json 到 Lido CSM
# https://csm.testnet.fi

# 部署节点
python3 cli.py deploy
```

### 场景 3: 主网部署（生产环境）

```bash
# ⚠️ 警告：主网需要真实 32 ETH

# 配置主网
python3 cli.py configure --network mainnet --client lighthouse

# 生成密钥（推荐设置提款地址）
python3 cli.py keys generate \
  --count 1 \
  --network mainnet \
  --withdrawal-address 0xYourSafeAddress

# 上传 deposit_data.json 到主网 Launchpad
# https://launchpad.ethereum.org

# 等待存款确认后部署
python3 cli.py deploy
```

## 配置文件位置

- **eth-docker**: `~/eth-docker/`
- **配置文件**: `~/eth-docker/.env`
- **密钥文件**: `~/eth-docker/.eth/validator_keys/`
- **验证者数据**: `~/eth-docker/.eth/validators/`

## 硬件要求

### Holesky / Hoodi 测试网
- **存储**: 100GB+
- **内存**: 8GB+
- **CPU**: 2核+
- **网络**: 稳定的宽带连接

### Mainnet 主网
- **存储**: 2TB+ SSD
- **内存**: 16GB+
- **CPU**: 4核+
- **网络**: 稳定的宽带连接（最好不限流量）

## 常见问题

### Docker 未运行

```bash
# macOS: 启动 Docker Desktop
open -a Docker

# Linux: 启动 Docker 服务
sudo systemctl start docker
```

### 磁盘空间不足

```bash
# 查看磁盘使用情况
df -h

# 清理 Docker
docker system prune -a
```

### 节点同步慢

- 确保使用了 Checkpoint Sync（默认启用）
- 检查网络连接速度
- 考虑使用更快的 SSD

### 密钥丢失

⚠️ **没有备份就无法恢复！**
- 确保保存了助记词（24个单词）
- 备份 keystore 文件
- 记住 keystore 密码

## 安全建议

1. **助记词安全**
   - 写在纸上，存放在安全的地方
   - 不要截图或保存在电脑上
   - 不要通过网络传输
   - 考虑使用金属板刻录

2. **密码管理**
   - 使用强密码
   - 使用密码管理器
   - 不要重复使用密码

3. **服务器安全**
   - 启用防火墙
   - 定期更新系统
   - 使用 SSH 密钥认证
   - 禁用 root 登录

4. **备份策略**
   - 定期备份密钥文件
   - 多地点存储备份
   - 测试恢复流程

## 获取帮助

```bash
# 查看命令帮助
python3 cli.py --help
python3 cli.py <command> --help

# 示例
python3 cli.py configure --help
python3 cli.py keys --help
```

## 链接

- **Ethereum Launchpad**: https://launchpad.ethereum.org
- **Holesky Launchpad**: https://holesky.launchpad.ethereum.org
- **Lido CSM**: https://csm.lido.fi
- **eth-docker 文档**: https://ethdocker.com
- **EthStaker 社区**: https://discord.gg/ethstaker

## License

Apache License v2
