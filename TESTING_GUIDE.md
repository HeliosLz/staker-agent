# 🧪 Staker Agent - 测试指南

## 快速测试（5分钟）

### 前置准备

```bash
cd ~/staker-agent
pip install -r requirements.txt
```

---

## 📋 测试清单

### 1️⃣ 基础功能测试（2分钟）

```bash
# 测试帮助信息
python3 cli.py --help

# 测试版本
python3 cli.py --version

# 测试环境检测
python3 cli.py init
```

**预期结果：**
- ✅ 显示所有可用命令
- ✅ 显示 v0.1.0
- ✅ 显示完整的环境检查表，包括正确的磁盘空间

---

### 2️⃣ 配置测试（1分钟）

```bash
# 测试配置生成（Holesky 测试网）
python3 cli.py configure --network holesky --client lighthouse

# 验证生成的配置
cat ~/eth-docker/.env | head -20

# 验证配置
python3 cli.py validate
```

**预期结果：**
- ✅ 生成 ~/eth-docker/.env 文件
- ✅ NETWORK=holesky
- ✅ COMPOSE_FILE=lighthouse.yml:geth.yml:deposit-cli.yml
- ✅ CHECKPOINT_SYNC_URL 正确

**验证要点：**
```bash
# 检查关键配置
grep "NETWORK=holesky" ~/eth-docker/.env
grep "COMPOSE_FILE=lighthouse.yml:geth.yml:deposit-cli.yml" ~/eth-docker/.env
grep "CHECKPOINT_SYNC_URL=https://checkpoint-sync.holesky.ethpandaops.io" ~/eth-docker/.env
```

---

### 3️⃣ 多网络测试（2分钟）

```bash
# 测试主网配置（会显示警告）
python3 cli.py configure --network mainnet --client prysm

# 测试 Lido CSM 配置
python3 cli.py configure --network hoodi --client teku

# 验证 Lido CSM 特殊配置
grep "FEE_RECIPIENT=0xE73a3602b99f1f913e72F8bdcBC235e206794Ac8" ~/eth-docker/.env
```

**预期结果：**
- ✅ Mainnet: 显示 "2TB+ 存储" 警告
- ✅ Hoodi: 自动设置 Lido fee recipient
- ✅ 显示 Lido CSM 说明

---

### 4️⃣ 密钥管理测试（1分钟）

```bash
# 测试密钥列表
python3 cli.py keys list

# 测试密钥生成帮助
python3 cli.py keys --help

# 测试密钥生成（会提示需要 Docker）
echo "n" | python3 cli.py keys generate --count 1 --network holesky
```

**预期结果：**
- ✅ 显示密钥目录位置
- ✅ 显示完整的参数说明
- ✅ 友好提示 "Docker is not installed"

---

### 5️⃣ 状态监控测试（1分钟）

```bash
# 测试状态查看
python3 cli.py status

# 测试详细状态
python3 cli.py status --detailed

# 测试日志帮助
python3 cli.py logs --help
```

**预期结果：**
- ✅ 显示当前网络和客户端配置
- ✅ 提示 "No containers running"
- ✅ 给出下一步建议

---

### 6️⃣ 错误处理测试（1分钟）

```bash
# 测试无效网络
python3 cli.py configure --network invalid 2>&1

# 测试无效客户端
python3 cli.py configure --client invalid 2>&1

# 测试未配置的部署
rm ~/eth-docker/.env
python3 cli.py deploy
```

**预期结果：**
- ✅ Click 提示有效选项
- ✅ 清晰的错误信息
- ✅ deploy 前置检查失败并提示

---

## 🎯 完整流程测试（10分钟）

### 场景：部署 Holesky 测试网节点

```bash
# 步骤 1: 环境检查
python3 cli.py init
# ✅ 检查所有环境要求

# 步骤 2: 安装 eth-docker（跳过 Docker）
python3 cli.py setup --skip-docker
# ✅ 克隆 eth-docker 仓库

# 步骤 3: 配置节点
python3 cli.py configure --network holesky --client lighthouse
# ✅ 生成配置文件

# 步骤 4: 验证配置
python3 cli.py validate
# ✅ 检查配置完整性

# 步骤 5: 查看配置
cat ~/eth-docker/.env | grep -E "^(NETWORK|COMPOSE_FILE|CHECKPOINT)" | head -5
# ✅ 验证配置正确

# 步骤 6: 查看状态
python3 cli.py status
# ✅ 显示当前配置
```

---

## 🧩 进阶测试

### 测试所有网络和客户端组合

```bash
# 创建测试脚本
cat > test_all_configs.sh << 'EOF'
#!/bin/bash
cd ~/staker-agent

networks=("holesky" "mainnet" "hoodi" "sepolia")
clients=("lighthouse" "prysm" "teku" "nimbus")

echo "Testing all network and client combinations..."
echo ""

for network in "${networks[@]}"; do
    for client in "${clients[@]}"; do
        echo "=== Testing $network + $client ==="
        python3 cli.py configure --network $network --client $client 2>&1 | grep -E "(Network|Client|✅)" | head -3

        # 验证配置
        if grep -q "NETWORK=$network" ~/eth-docker/.env && grep -q "$client.yml" ~/eth-docker/.env; then
            echo "✅ Configuration verified"
        else
            echo "❌ Configuration failed"
        fi
        echo ""
    done
done
EOF

chmod +x test_all_configs.sh
./test_all_configs.sh
```

**预期结果：**
- ✅ 16 个组合全部生成成功
- ✅ 每个配置都能通过验证

---

## 🔬 特定功能测试

### 测试 Lido CSM 配置

```bash
# 配置 Hoodi 网络
python3 cli.py configure --network hoodi --client lighthouse

# 验证 Lido 特定配置
echo "Checking Lido CSM configuration..."
grep "FEE_RECIPIENT" ~/eth-docker/.env
grep "hoodi.lido.fi" ~/eth-docker/.env

# 应该看到：
# FEE_RECIPIENT=0xE73a3602b99f1f913e72F8bdcBC235e206794Ac8
# CHECKPOINT_SYNC_URL=https://checkpoint-sync.hoodi.lido.fi
```

### 测试磁盘检测修复

```bash
# 运行 init 并检查磁盘空间
python3 cli.py init 2>&1 | grep "Disk Space"

# 应该看到实际的磁盘空间，例如：
# Disk Space     │ Disk Space (209GB available) │ ✅
# 而不是：
# Disk Space     │ Disk Space (0GB available)   │ ⚠️
```

### 测试配置验证

```bash
# 正常配置
python3 cli.py configure --network holesky --client lighthouse
python3 cli.py validate
# ✅ 应该通过验证

# 删除配置文件
mv ~/eth-docker/.env ~/eth-docker/.env.backup
python3 cli.py validate
# ❌ 应该提示配置文件不存在

# 恢复配置
mv ~/eth-docker/.env.backup ~/eth-docker/.env
```

---

## 🐛 边界情况测试

### 测试命令参数

```bash
# 测试帮助信息
python3 cli.py configure --help
python3 cli.py keys --help
python3 cli.py deploy --help

# 测试无效参数
python3 cli.py configure --network invalid_network
python3 cli.py configure --client invalid_client
python3 cli.py keys generate --count -1
```

### 测试文件权限

```bash
# 测试目录不存在的情况
rm -rf ~/eth-docker
python3 cli.py status
# 应该提示 eth-docker 不存在

# 重新安装
python3 cli.py setup --skip-docker
```

---

## 📊 验证清单

完成测试后，请检查：

### 基础功能 ✅
- [ ] `--help` 显示所有命令
- [ ] `--version` 显示版本号
- [ ] `init` 检查所有环境
- [ ] 磁盘空间显示正确（不是 0GB）

### 配置生成 ✅
- [ ] 生成的 .env 文件存在
- [ ] NETWORK 设置正确
- [ ] COMPOSE_FILE 格式正确（yml:yml:yml）
- [ ] CHECKPOINT_SYNC_URL 正确

### 网络支持 ✅
- [ ] Mainnet - 显示 2TB 警告
- [ ] Holesky - 正常配置
- [ ] Hoodi - Lido CSM fee recipient
- [ ] Sepolia - 正常配置

### 客户端支持 ✅
- [ ] Lighthouse - 配置正确
- [ ] Prysm - 配置正确
- [ ] Teku - 配置正确
- [ ] Nimbus - 配置正确

### 错误处理 ✅
- [ ] 无效参数被拒绝
- [ ] 缺少 Docker 提示友好
- [ ] 未配置时给出建议
- [ ] 所有错误都有解决方案

---

## 🚀 如果你有 Docker

如果你已经安装了 Docker，可以测试完整部署流程：

```bash
# 1. 启动 Docker Desktop (macOS)
open -a Docker

# 等待 Docker 启动完成，然后：

# 2. 重新检查环境
python3 cli.py init
# 应该看到 Docker 和 Docker Compose 都是 ✅

# 3. 配置节点
python3 cli.py configure --network holesky --client lighthouse

# 4. 验证配置
python3 cli.py validate

# 5. 生成密钥（交互式）
python3 cli.py keys generate --count 1 --network holesky
# 按提示操作：
# - 选择语言
# - 创建助记词
# - 设置密码
# - 确认助记词

# 6. 查看生成的密钥
python3 cli.py keys list

# 7. 部署节点（会拉取 Docker 镜像，需要时间）
python3 cli.py deploy

# 8. 查看状态
python3 cli.py status

# 9. 查看日志
python3 cli.py logs

# 10. 停止节点
python3 cli.py stop
```

---

## 📝 报告问题

如果发现问题，请记录：

1. **命令**: 你执行的命令
2. **预期**: 应该发生什么
3. **实际**: 实际发生了什么
4. **错误信息**: 完整的错误输出
5. **环境**: OS 版本、Python 版本

---

## ✅ 快速验证（30秒）

如果时间有限，运行这个快速测试：

```bash
cd ~/staker-agent

# 一键测试核心功能
python3 cli.py init && \
python3 cli.py configure --network holesky --client lighthouse && \
python3 cli.py validate && \
python3 cli.py status && \
echo "✅ All basic tests passed!"
```

如果看到 "✅ All basic tests passed!"，说明核心功能正常！

---

## 🎯 测试成功标准

测试通过的标志：
- ✅ 所有命令都能运行（不崩溃）
- ✅ 配置文件正确生成
- ✅ 磁盘空间显示正确数值
- ✅ 错误提示清晰友好
- ✅ Lido CSM 自动配置 fee recipient

祝测试顺利！🚀
