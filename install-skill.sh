#!/bin/bash

# MemoryBridge Skill 一键安装脚本
# 用法：bash install-skill.sh

set -e

echo "🚀 MemoryBridge Skill 一键安装"
echo "================================"
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查 Python
echo "📋 检查环境..."
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ 错误：未找到 Python3${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Python3: $(python3 --version)${NC}"

# 检查 pip
if ! command -v pip3 &> /dev/null; then
    echo -e "${RED}❌ 错误：未找到 pip3${NC}"
    exit 1
fi
echo -e "${GREEN}✅ pip3: $(pip3 --version | head -n1)${NC}"

# 检查 OpenClaw 工作区
WORKSPACE="$HOME/.openclaw/workspace"
if [ ! -d "$WORKSPACE" ]; then
    echo -e "${RED}❌ 错误：未找到 OpenClaw 工作区 $WORKSPACE${NC}"
    exit 1
fi
echo -e "${GREEN}✅ OpenClaw 工作区：$WORKSPACE${NC}"
echo ""

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
SKILL_DIR="$SCRIPT_DIR/skills/memorybridge"

if [ ! -d "$SKILL_DIR" ]; then
    echo -e "${RED}❌ 错误：未找到 Skill 目录 $SKILL_DIR${NC}"
    exit 1
fi

# 1. 安装 Python 包
echo "📦 步骤 1/4: 安装 MemoryBridge Python 包..."
cd "$SCRIPT_DIR"
pip3 install -e . --break-system-packages -q
echo -e "${GREEN}✅ Python 包安装完成${NC}"
echo ""

# 2. 创建 Skill 目录
echo "📁 步骤 2/4: 创建 Skill 目录..."
TARGET_SKILL_DIR="$WORKSPACE/skills/memorybridge"
mkdir -p "$TARGET_SKILL_DIR"
echo -e "${GREEN}✅ 创建目录：$TARGET_SKILL_DIR${NC}"
echo ""

# 3. 复制 Skill 文件
echo "📋 步骤 3/4: 复制 Skill 文件..."
cp "$SKILL_DIR/SKILL.md" "$TARGET_SKILL_DIR/SKILL.md"
cp "$SKILL_DIR/tools.py" "$TARGET_SKILL_DIR/tools.py"
echo -e "${GREEN}✅ 文件复制完成${NC}"
echo "   - $TARGET_SKILL_DIR/SKILL.md"
echo "   - $TARGET_SKILL_DIR/tools.py"
echo ""

# 4. 配置 openclaw.json
echo "⚙️  步骤 4/4: 配置 openclaw.json..."
CONFIG_FILE="$WORKSPACE/../openclaw.json"

if [ ! -f "$CONFIG_FILE" ]; then
    echo -e "${YELLOW}⚠️  配置文件不存在：$CONFIG_FILE${NC}"
    echo "请手动编辑 openclaw.json，添加以下配置："
    echo ""
    echo '```json'
    echo '{'
    echo '  "skills": {'
    echo '    "entries": {'
    echo '      "memorybridge": {'
    echo '        "enabled": true'
    echo '      }'
    echo '    }'
    echo '  }'
    echo '}'
    echo '```'
    echo ""
else
    # 检查是否已配置
    if grep -q "memorybridge" "$CONFIG_FILE"; then
        echo -e "${GREEN}✅ memorybridge 已配置${NC}"
    else
        echo -e "${YELLOW}⚠️  需要手动配置 openclaw.json${NC}"
        echo "请添加以下配置到 $CONFIG_FILE 的 skills.entries 部分："
        echo ""
        echo '```json'
        echo '"memorybridge": {'
        echo '  "enabled": true'
        echo '}'
        echo '```'
        echo ""
    fi
fi

# 5. 重启 Gateway
echo ""
echo "🔄 最后一步：重启 OpenClaw Gateway"
echo ""
echo "请运行以下命令："
echo "  ${YELLOW}openclaw gateway restart${NC}"
echo ""

# 完成
echo "================================"
echo -e "${GREEN}✅ 安装完成！${NC}"
echo ""
echo "📖 使用方法："
echo "  在 OpenClaw 中说："
echo "    - 帮我记住 Python 是一种编程语言"
echo "    - 搜索关于 Python 的记忆"
echo "    - 查看所有记忆"
echo ""
echo "📚 更多文档："
echo "  $SCRIPT_DIR/docs/skill-setup.md"
echo ""
echo "🐛 故障排查："
echo "  如果 Skill 未加载，请检查："
echo "    openclaw logs --tail 50 | grep memorybridge"
echo ""
