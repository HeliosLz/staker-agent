# 🛰️ Staker Agent

一个 AI 驱动的以太坊验证者部署和管理工具。让任何人都能在几分钟内部署和管理以太坊验证节点。

## ✨ 特性

- ✅ **本地部署优先** - 支持在自己的电脑上运行（降低成本）
- ✅ **自动环境检测** - 检测 OS、Docker、磁盘空间等
- ✅ **智能配置** - 自动生成 eth-docker 配置
- ✅ **多网络支持** - Mainnet、Holesky、Hoodi (Lido CSM)、Sepolia
- ✅ **多客户端支持** - Lighthouse、Prysm、Teku、Nimbus
- ✅ **密钥管理** - 安全生成和管理验证者密钥
- ✅ **美观的 CLI** - 彩色输出、表格展示、清晰提示

## 🚀 快速开始

### 安装依赖

```bash
pip install -r requirements.txt
```

### 完整流程（5 分钟部署测试网节点）

```bash
# 1. 检查环境
python3 cli.py init

# 2. 安装 eth-docker
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

详细使用指南请查看 [USAGE.md](USAGE.md)

## 🧪 测试

### 快速测试（30秒）

```bash
cd ~/staker-agent
./test.sh
```

自动化测试脚本会验证所有核心功能。

### 手动测试

详细测试步骤请查看 [TESTING_GUIDE.md](TESTING_GUIDE.md)

```bash
# 基础功能测试
python3 cli.py init
python3 cli.py configure --network holesky --client lighthouse
python3 cli.py validate
python3 cli.py status
```

**测试结果：** 16/16 测试通过 ✅

## 📋 命令列表

| 命令 | 说明 | 状态 |
|------|------|------|
| `init` | 检查环境 | ✅ 完成 |
| `validate` | 验证配置 | ✅ 完成 |
| `setup` | 安装 Docker + eth-docker | ✅ 完成 |
| `configure` | 配置网络和客户端 | ✅ 完成 |
| `keys` | 管理验证者密钥 | ✅ 完成 |
| `deploy` | 部署节点 | ✅ 完成 |
| `status` | 查看节点状态 | ✅ 完成 |
| `logs` | 查看日志 | ✅ 完成 |
| `start/stop` | 启动/停止节点 | ✅ 完成 |

## 🎯 支持的配置

### 网络
- **mainnet** - 以太坊主网
- **holesky** - Holesky 测试网（推荐测试）
- **hoodi** - Lido CSM 测试网
- **sepolia** - Sepolia 测试网

### 客户端
- **Lighthouse** - Rust 实现，推荐
- **Prysm** - Go 实现
- **Teku** - Java 实现
- **Nimbus** - Nim 实现

所有客户端都使用 Geth 作为执行层客户端。

## 💡 使用场景

### 1. Holesky 测试网（新手）
```bash
python3 cli.py configure --network holesky --client lighthouse
python3 cli.py keys generate --count 1 --network holesky
python3 cli.py deploy
```

### 2. Lido CSM（社区质押）
```bash
python3 cli.py configure --network hoodi --client lighthouse
python3 cli.py keys generate --count 1 --network hoodi --withdrawal-address 0x...
python3 cli.py deploy
```

### 3. 主网部署（需要 32 ETH）
```bash
python3 cli.py configure --network mainnet --client lighthouse
python3 cli.py keys generate --count 1 --network mainnet --withdrawal-address 0x...
python3 cli.py deploy
```

## 📊 系统要求

### 测试网（Holesky / Hoodi）
- 存储: 100GB+
- 内存: 8GB+
- CPU: 2核+

### 主网（Mainnet）
- 存储: 2TB+ SSD
- 内存: 16GB+
- CPU: 4核+

## 🛠️ 开发状态

**当前版本**: v0.1.0 (MVP)

**完成度**: 100% ✅

- ✅ 环境检测
- ✅ 配置验证
- ✅ 依赖安装
- ✅ 配置生成
- ✅ 密钥管理
- ✅ 节点部署
- ✅ 状态监控
- ✅ 日志查看

查看详细完成报告：[MVP_COMPLETE.md](MVP_COMPLETE.md)

## 🔒 安全提示

- ⚠️ 妥善保管助记词（24个单词）
- ⚠️ 备份 keystore 文件和密码
- ⚠️ 提款地址一旦设置无法更改
- ⚠️ 主网部署前务必在测试网测试

## 📚 相关资源

- [eth-docker 文档](https://ethdocker.com)
- [Ethereum Launchpad](https://launchpad.ethereum.org)
- [Lido CSM](https://csm.lido.fi)
- [EthStaker 社区](https://discord.gg/ethstaker)

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 License

Apache License v2

