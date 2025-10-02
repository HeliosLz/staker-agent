#!/bin/bash
# Staker Agent - 自动化测试脚本

set -e

echo "🧪 Staker Agent - Automated Testing"
echo "===================================="
echo ""

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 测试计数
TOTAL=0
PASSED=0
FAILED=0

# 测试函数
run_test() {
    local test_name=$1
    local command=$2
    local expected=$3

    TOTAL=$((TOTAL + 1))
    echo -n "Testing: $test_name ... "

    if output=$(eval "$command" 2>&1); then
        if [[ -z "$expected" ]] || echo "$output" | grep -q "$expected"; then
            echo -e "${GREEN}✅ PASSED${NC}"
            PASSED=$((PASSED + 1))
            return 0
        else
            echo -e "${RED}❌ FAILED${NC}"
            echo "  Expected: $expected"
            echo "  Got: $output"
            FAILED=$((FAILED + 1))
            return 1
        fi
    else
        echo -e "${RED}❌ FAILED (command failed)${NC}"
        FAILED=$((FAILED + 1))
        return 1
    fi
}

# 切换到项目目录
cd ~/staker-agent

echo "📋 Test Suite 1: Basic Commands"
echo "--------------------------------"

run_test "CLI help" "python3 cli.py --help" "Staker Agent"
run_test "CLI version" "python3 cli.py --version" "0.1.0"
run_test "Init command" "python3 cli.py init" "Environment Status"
run_test "Validate command" "python3 cli.py validate" "Validating Configuration"
run_test "Status command" "python3 cli.py status" "Staker Agent - Status"
run_test "Keys list" "python3 cli.py keys list" "Validator Keys"

echo ""
echo "📋 Test Suite 2: Configuration Generation"
echo "----------------------------------------"

run_test "Configure Holesky" "python3 cli.py configure --network holesky --client lighthouse" "Configuration completed"
run_test "Verify NETWORK" "grep 'NETWORK=holesky' ~/eth-docker/.env" "NETWORK=holesky"
run_test "Verify COMPOSE_FILE" "grep 'lighthouse.yml:geth.yml' ~/eth-docker/.env" "lighthouse.yml:geth.yml"
run_test "Verify Checkpoint Sync" "grep 'checkpoint-sync.holesky' ~/eth-docker/.env" "checkpoint-sync.holesky"

echo ""
echo "📋 Test Suite 3: Multi-Network Support"
echo "-------------------------------------"

run_test "Configure Mainnet" "python3 cli.py configure --network mainnet --client prysm" "MAINNET WARNINGS"
run_test "Configure Hoodi" "python3 cli.py configure --network hoodi --client teku" "Lido CSM"
run_test "Verify Lido Fee Recipient" "grep 'FEE_RECIPIENT=0xE73a3602b99f1f913e72F8bdcBC235e206794Ac8' ~/eth-docker/.env" "FEE_RECIPIENT"

echo ""
echo "📋 Test Suite 4: Error Handling"
echo "------------------------------"

run_test "Invalid network" "python3 cli.py configure --network invalid 2>&1 || true" "not one of"
run_test "Keys without Docker" "echo 'n' | python3 cli.py keys generate --count 1 2>&1 || true" "Docker is not"

echo ""
echo "📋 Test Suite 5: Disk Detection Fix"
echo "----------------------------------"

# 检查磁盘空间是否显示为非零值
disk_output=$(python3 cli.py init 2>&1 | grep "Disk Space")
if echo "$disk_output" | grep -q "0GB available"; then
    echo -e "Disk detection ... ${RED}❌ FAILED (still showing 0GB)${NC}"
    FAILED=$((FAILED + 1))
else
    echo -e "Disk detection ... ${GREEN}✅ PASSED (showing actual space)${NC}"
    PASSED=$((PASSED + 1))
fi
TOTAL=$((TOTAL + 1))

echo ""
echo "===================================="
echo "📊 Test Results"
echo "===================================="
echo "Total Tests:  $TOTAL"
echo -e "Passed:       ${GREEN}$PASSED${NC}"
echo -e "Failed:       ${RED}$FAILED${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}🎉 All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}❌ Some tests failed${NC}"
    exit 1
fi
