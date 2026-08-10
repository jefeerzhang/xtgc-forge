#!/bin/bash
# 选题工坊 · 完整实测就绪检查脚本
# 用法:
#   bash check-ready.sh [PDF目录]        # 检查全部
#   PDF目录缺省时只检查环境与依赖,不检查文献

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILLS_DIR="${CLAUDE_SKILLS_DIR:-$HOME/.claude/skills}"

echo "================================================"
echo "  选题工坊 v0.2.9 · 完整实测就绪检查"
echo "================================================"
echo ""

# 1. 检查 Claude Code 是否能用
echo "[1/4] 检查 Claude Code ..."
if command -v claude &> /dev/null; then
    CLAUDE_PATH=$(which claude)
    echo "  ✅ Claude Code 已装在 $CLAUDE_PATH"
else
    echo "  ❌ Claude Code 未安装或不在 PATH"
    echo "     安装:https://code.claude.com/docs/en/skills"
    exit 1
fi

# 2. 检查 Nero1688 子 skill 是否装
echo ""
echo "[2/4] 检查 Nero1688 4 个核心子 skill(目录:$SKILLS_DIR)..."
EXPECTED_SKILLS=("bilingual-paper-reader" "literature-matrix-builder" "research-method-selector" "causal-inference-architect")

MISSING=()
for skill in "${EXPECTED_SKILLS[@]}"; do
    if [ -d "$SKILLS_DIR/$skill" ]; then
        echo "  ✅ $skill 已装"
    else
        echo "  ❌ $skill 未装"
        MISSING+=("$skill")
    fi
done

if [ ${#MISSING[@]} -gt 0 ]; then
    echo ""
    echo "  ⚠️  缺失 ${#MISSING[@]} 个子 skill,补装方法(任选其一):"
    echo ""
    echo "  方法 A · 从上游仓库拷贝:"
    echo "     git clone --depth 1 https://github.com/Nero1688/claude-academic-skills.git /tmp/cas"
    for skill in "${MISSING[@]}"; do
        echo "     cp -r /tmp/cas/skills/$skill \"$SKILLS_DIR/\""
    done
    echo ""
    echo "  方法 B · 用 npx skills(若上游已注册):"
    echo "     npx skills add Nero1688/claude-academic-skills"
    exit 1
fi

# 3. 检查选题工坊自身(按脚本所在目录定位,不写死路径)
echo ""
echo "[3/4] 检查选题工坊 SKILL.md ..."
if [ -f "$SCRIPT_DIR/SKILL.md" ]; then
    echo "  ✅ SKILL.md 存在($SCRIPT_DIR)"
    VERSION=$(grep "^version:" "$SCRIPT_DIR/SKILL.md" | head -1 | tr -d '"' | awk '{print $2}')
    echo "  当前版本:$VERSION"
else
    echo "  ❌ SKILL.md 不存在(期望在 $SCRIPT_DIR)"
    exit 1
fi

# 4. 检查用户文献目录(可选;传参才检查)
echo ""
echo "[4/4] 检查文献 PDF ..."
PDF_DIR="${1:-}"

if [ -z "$PDF_DIR" ]; then
    echo "  ⏭️  未传 PDF 目录,跳过文献检查"
    echo "     完整检查:bash check-ready.sh <你的PDF目录>"
    echo ""
    echo "================================================"
    echo "  ✅ 环境与依赖就绪!"
    echo "================================================"
    exit 0
fi

if [ ! -d "$PDF_DIR" ]; then
    echo "  ⚠️  文献目录 $PDF_DIR 不存在"
    echo "     建议建一个:mkdir -p \"$PDF_DIR\""
    echo "     然后把你研究领域的 PDF 放进去"
    exit 1
fi

PDF_COUNT=$(find "$PDF_DIR" -maxdepth 2 -iname "*.pdf" 2>/dev/null | wc -l)
if [ "$PDF_COUNT" -eq 0 ]; then
    echo "  ❌ $PDF_DIR 下没有找到 PDF"
    echo "     至少放 5 篇 PDF 进去(建议 8-15 篇)"
    exit 1
fi

echo "  ✅ $PDF_DIR 下有 $PDF_COUNT 个 PDF"
echo ""
echo "================================================"
echo "  ✅ 全部就绪!可以跑实测。"
echo "================================================"
echo ""
echo "下一步:在 Claude Code 里输入 /选题工坊,然后对 Claude 说:"
echo "  跑全部。文献目录:$PDF_DIR;模糊领域:<你的研究方向>"
echo ""
