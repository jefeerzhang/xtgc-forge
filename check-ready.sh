#!/bin/bash
# 选题工坊 · 完整实测就绪检查脚本
# 用法:bash check-ready.sh [PDF目录]

set -e

echo "================================================"
echo "  选题工坊 v0.2.1 · 完整实测就绪检查"
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
echo "[2/4] 检查 Nero1688 4 个核心子 skill ..."
SKILLS_DIR="$HOME/.claude/skills"
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
    echo "  ⚠️  缺失子 skill,执行以下命令补装:"
    echo "     bash /c/Users/jefeer/Downloads/claude-academic-skills/plugin/scripts/install.sh \\"
    echo "       --skill ${MISSING[*]}"
    exit 1
fi

# 3. 检查选题工坊自身
echo ""
echo "[3/4] 检查选题工坊 SKILL.md ..."
XTGC_DIR="/c/Users/jefeer/Downloads/选题工坊"
if [ -f "$XTGC_DIR/SKILL.md" ]; then
    echo "  ✅ SKILL.md 存在"
    VERSION=$(grep "^version:" "$XTGC_DIR/SKILL.md" | head -1 | tr -d '"' | awk '{print $2}')
    echo "  当前版本:$VERSION"
else
    echo "  ❌ SKILL.md 不存在"
    exit 1
fi

# 4. 检查用户文献目录
echo ""
echo "[4/4] 检查文献 PDF ..."
PDF_DIR="${1:-/c/Users/jefeer/Downloads/我的文献}"

if [ ! -d "$PDF_DIR" ]; then
    echo "  ⚠️  文献目录 $PDF_DIR 不存在"
    echo "     建议建一个:mkdir -p $PDF_DIR"
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
echo "下一步:在 Claude Code 里执行:"
echo "  /选题工坊/跑全部"
echo ""
echo "  然后告诉 Claude:"
echo "  - 文献目录:$PDF_DIR"
echo "  - 模糊领域:<你的研究方向>"
echo ""