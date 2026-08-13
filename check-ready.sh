#!/bin/bash
# 选题工坊 · 完整实测就绪检查脚本 (v0.3.14 · vendor-first)
# 用法:
#   bash check-ready.sh [PDF目录]        # 检查全部
#   PDF目录缺省时只检查环境与依赖,不检查文献

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILLS_DIR="${CLAUDE_SKILLS_DIR:-$HOME/.claude/skills}"
VENDOR_DIR="$SCRIPT_DIR/vendor"

# 版本从 SKILL.md 动态读取,避免横幅与仓库版本漂移(曾硬编码 v0.2.9 滞后)
SELF_VERSION="$(grep "^version:" "$SCRIPT_DIR/SKILL.md" 2>/dev/null | head -1 | tr -d '"' | awk '{print $2}')"
[ -n "$SELF_VERSION" ] || SELF_VERSION="unknown"

echo "================================================"
echo "  选题工坊 ${SELF_VERSION} · 完整实测就绪检查"
echo "================================================"
echo ""

# 1. 检查 Claude Code 是否能用
echo "[1/6] 检查 Claude Code ..."
if command -v claude &> /dev/null; then
    CLAUDE_PATH=$(which claude)
    echo "  ✅ Claude Code 已装在 $CLAUDE_PATH"
else
    echo "  ❌ Claude Code 未安装或不在 PATH"
    echo "     安装:https://code.claude.com/docs/en/skills"
    exit 1
fi

# 2. 检查 4 个内置子 skill(vendor/ 优先,external fallback)
echo ""
echo "[2/6] 检查 4 个内置子 skill(优先看仓库 vendor/;$SKILLS_DIR 仅作外部覆盖)..."

EXPECTED_SKILLS=("bilingual-paper-reader" "literature-matrix-builder" "research-method-selector" "causal-inference-architect" "academic-humanizer")

MISSING=()
for skill in "${EXPECTED_SKILLS[@]}"; do
    if [ -d "$VENDOR_DIR/$skill" ]; then
        echo "  ✅ $skill 已就位(来自 vendor/)"
    elif [ -d "$SKILLS_DIR/$skill" ]; then
        echo "  ✅ $skill 已就位(来自 $SKILLS_DIR)"
    else
        echo "  ⚠️  $skill 未就位(vendor 与 $SKILLS_DIR 均缺)"
        MISSING+=("$skill")
    fi
done

if [ ${#MISSING[@]} -gt 0 ]; then
    echo ""
    echo "  ⚠️  缺失 ${#MISSING[@]} 个子 skill —— 主路径不阻塞,默认走自写兜底"
    echo "     修复方法(任选其一):"
    echo ""
    echo "  方法 A · 重新跑 vendor 拷贝:"
    echo "     git clone --depth 1 https://github.com/Nero1688/claude-academic-skills.git /tmp/cas"
    for skill in "${MISSING[@]}"; do
        echo "     cp -r /tmp/cas/skills/$skill \"$VENDOR_DIR/\""
    done
    echo ""
    echo "  方法 B · 装到 \$CLAUDE_SKILLS_DIR(高级用户):"
    echo "     export CLAUDE_SKILLS_DIR=/your/path"
    echo "     npx skills add Nero1688/claude-academic-skills"
fi

# 3. 检查选题工坊自身 + 法务 / 文档完整性
echo ""
echo "[3/6] 检查选题工坊本体 + 法务完整性 ..."
if [ -f "$SCRIPT_DIR/SKILL.md" ]; then
    echo "  ✅ SKILL.md 存在($SCRIPT_DIR)"
    echo "  当前版本:$SELF_VERSION"
else
    echo "  ❌ SKILL.md 不存在(期望在 $SCRIPT_DIR)"
    exit 1
fi

if [ -f "$SCRIPT_DIR/NOTICE.md" ]; then
    echo "  ✅ NOTICE.md 存在(上游版权 + 传递依赖汇总)"
else
    echo "  ⚠️  NOTICE.md 缺失(MIT §(c) 合规要求)"
fi

if [ -f "$VENDOR_DIR/LICENSE" ]; then
    echo "  ✅ vendor/LICENSE 存在(Nero1688 MIT)"
else
    echo "  ⚠️  vendor/LICENSE 缺失"
fi

# 4. vendored 脚本的 Python 依赖检查(仅警告,不阻塞)
echo ""
echo "[4/6] 检查 vendored 脚本的 Python 依赖 ..."
PY_DEPS_OK=true
for pkg in pypdf requests openpyxl; do
    if python3 -c "import importlib; importlib.import_module('$pkg')" 2>/dev/null; then
        echo "  ✅ $pkg 可导入"
    else
        echo "  ⚠️  $pkg 未装(纯 prose 流程不依赖;调 vendor/literature-matrix-builder/scripts/litmatrix.py 时需要)"
        PY_DEPS_OK=false
    fi
done
if [ "$PY_DEPS_OK" = false ]; then
    echo ""
    echo "  安装一行:pip install pypdf requests openpyxl"
fi

# 5. 检查用户文献目录(可选;传参才检查)
echo ""
echo "[5/6] 检查文献 PDF ..."
PDF_DIR="${1:-}"

if [ -z "$PDF_DIR" ]; then
    echo "  ⏭️  未传 PDF 目录,跳过文献检查"
    echo "     完整检查:bash check-ready.sh <你的PDF目录>"
else
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
fi

# 6. 检查 academic-humanizer(v0.3.15 起内置,Step 6 去 AI 味润色)
echo ""
echo "[6/6] 检查 academic-humanizer(jefeerzhang fork,Step 6 去 AI 味润色)..."
if [ -d "$VENDOR_DIR/academic-humanizer" ]; then
    echo "  ✅ academic-humanizer 已就位(来自 vendor/)"
elif [ -d "$SKILLS_DIR/academic-humanizer" ]; then
    echo "  ✅ academic-humanizer 已就位(来自 $SKILLS_DIR)"
else
    echo "  ⚠️  academic-humanizer 未就位 —— Step 6 退到 references/deai-checklist.md 兜底润色"
    echo "     修复(任选其一):"
    echo "       A:确认 vendor/academic-humanizer/ 未被误删"
    echo "       B:export CLAUDE_SKILLS_DIR=/your/path;放入 academic-humanizer 目录"
fi

echo ""
echo "================================================"
echo "  ✅ 全部就绪!可以跑实测。"
echo "================================================"
echo ""
echo "下一步:在 Claude Code 里输入 /选题工坊,然后对 Claude 说:"
if [ -n "$PDF_DIR" ]; then
    echo "  跑全部。文献目录:$PDF_DIR;模糊领域:<你的研究方向>"
else
    echo "  跑全部。模糊领域:<你的研究方向>"
fi
echo ""