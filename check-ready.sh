#!/bin/bash
# 选题工坊 · 完整实测就绪检查脚本 (v0.3.17 · vendor-first + 版本对账)
# 用法:
#   bash check-ready.sh [PDF目录]        # 检查全部
#   PDF目录缺省时只检查环境与依赖,不检查文献

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILLS_DIR="${CLAUDE_SKILLS_DIR:-$HOME/.claude/skills}"
VENDOR_DIR="$SCRIPT_DIR/vendor"

# 从 SKILL.md 动态读取版本,避免横幅与仓库版本漂移(曾硬编码 v0.2.9 滞后)
SELF_VERSION="$(grep "^version:" "$SCRIPT_DIR/SKILL.md" 2>/dev/null | head -1 | tr -d '"' | awk '{print $2}')"
[ -n "$SELF_VERSION" ] || SELF_VERSION="unknown"

# 从 vendor 子目录的 SKILL.md frontmatter 读取版本(若存在)
# Nero1688 4 个子 skill 的 SKILL.md 不带 version:,学术润色器 academic-humanizer 带 version: 0.3.3
_read_version() {
    local f="$1"
    [ -f "$f" ] || return 1
    local v
    v="$(grep -E '^version:\s*' "$f" 2>/dev/null | head -1 | sed -E 's/^version:\s*["]?([^"]+)["]?.*/\1/' | tr -d '[:space:]')"
    if [ -n "$v" ]; then
        echo "$v"
        return 0
    fi
    return 1
}

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

# 2. 检查 5 个内置子 skill(vendor/ 优先,external fallback + 版本对账)
echo ""
echo "[2/6] 检查 5 个内置子 skill(优先看仓库 vendor/;$SKILLS_DIR 仅作外部覆盖 + 版本对账)..."

EXPECTED_SKILLS=("bilingual-paper-reader" "literature-matrix-builder" "research-method-selector" "causal-inference-architect" "academic-humanizer")

MISSING=()
DOUBLE_SOURCE_WARN=()
VERSION_MISMATCH_WARN=()

for skill in "${EXPECTED_SKILLS[@]}"; do
    VENDOR_PRESENT=0
    EXTERNAL_PRESENT=0

    if [ -d "$VENDOR_DIR/$skill" ]; then
        VENDOR_PRESENT=1
        echo "  ✅ $skill 已就位(来自 vendor/)"
    fi

    if [ -d "$SKILLS_DIR/$skill" ]; then
        EXTERNAL_PRESENT=1
        echo "  ✅ $skill 已就位(来自 $SKILLS_DIR)"
    fi

    if [ $VENDOR_PRESENT -eq 0 ] && [ $EXTERNAL_PRESENT -eq 0 ]; then
        echo "  ⚠️  $skill 未就位(vendor 与 $SKILLS_DIR 均缺)"
        MISSING+=("$skill")
    fi

    # 版本对账:两边都存在时,对比 SKILL.md frontmatter version:
    if [ $VENDOR_PRESENT -eq 1 ] && [ $EXTERNAL_PRESENT -eq 1 ]; then
        DOUBLE_SOURCE_WARN+=("$skill")
        VENDOR_VER=$(_read_version "$VENDOR_DIR/$skill/SKILL.md" 2>/dev/null || true)
        EXTERNAL_VER=$(_read_version "$SKILLS_DIR/$skill/SKILL.md" 2>/dev/null || true)

        if [ -z "$VENDOR_VER" ] && [ -z "$EXTERNAL_VER" ]; then
            echo "     ⚠️  双来源均存在,但两边 SKILL.md 都缺 version: 字段(无法自动对账),请手动 diff"
        elif [ -z "$VENDOR_VER" ]; then
            echo "     ⚠️  双来源:vendor 缺 version:,外部 $EXTERNAL_VER —— 升级 vendor 子目录的 SKILL.md 才能对账"
        elif [ -z "$EXTERNAL_VER" ]; then
            echo "     ⚠️  双来源:外部缺 version:,vendor $VENDOR_VER —— 外部可能装了旧版/未带版本号,可能错位"
            VERSION_MISMATCH_WARN+=("$skill (vendor=$VENDOR_VER, external=<无>)")
        elif [ "$VENDOR_VER" != "$EXTERNAL_VER" ]; then
            echo "     ⚠️  版本不一致:vendor $VENDOR_VER vs 外部 $EXTERNAL_VER —— SKILL.md 引用的 vendor/<name>/ 路径可能与 $SKILLS_DIR 下运行版本不一致"
            VERSION_MISMATCH_WARN+=("$skill (vendor=$VENDOR_VER, external=$EXTERNAL_VER)")
        else
            echo "     ✅ 版本对账一致:$VENDOR_VER = $EXTERNAL_VER"
        fi
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

if [ ${#DOUBLE_SOURCE_WARN[@]} -gt 0 ]; then
    echo ""
    echo "  ⚠️  ${#DOUBLE_SOURCE_WARN[@]} 个子 skill 同时存在于 vendor/ 和 $SKILLS_DIR/"
    echo "     SKILL.md 引用走仓库 vendor/ 路径,Claude Code 默认按 $SKILLS_DIR > 当前目录优先级加载"
    echo "     若本机是旧版同名 skill,可能加载到旧版而非本仓库版本,导致子步骤行为不一致"
    echo "     建议处理(任选其一):"
    echo "       A. 升级本机子 skill 到与 vendor 同版(如 npx skills update Nero1688/claude-academic-skills)"
    echo "       B. 临时改名/移走 $SKILLS_DIR/<skill> 强制 Claude Code 加载仓库 vendor 副本"
    echo "       C. 确认本机版本 >= vendor 版本,接受外部覆盖(检查上面对账结果是否一致)"
fi

# 3. 检查选题工坊自身 + 法务 / 文档完整性 + 跨文件版本一致性
echo ""
echo "[3/6] 检查选题工坊自身 + 法务完整性 + 跨文件版本一致性 ..."
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

# 跨文件版本对账:SKILL.md / README.md / CHANGELOG.md 顶部
echo ""
echo "  🔎 跨文件版本对账(防 SKILL.md/README/CHANGELOG 头部漂移)..."

README_VER=$(grep -oE "Version-v0\.[0-9]+\.[0-9]+" "$SCRIPT_DIR/README.md" 2>/dev/null | head -1 | sed -E 's/Version-v//')
CHANGELOG_VER=$(grep -oE "v0\.[0-9]+\.[0-9]+" "$SCRIPT_DIR/CHANGELOG.md" 2>/dev/null | head -1 | sed -E 's/v//')

INCONSISTENT=0
if [ -n "$README_VER" ] && [ "$README_VER" != "$SELF_VERSION" ]; then
    echo "     ⚠️  README badge 版本 v$README_VER ≠ SKILL.md frontmatter version $SELF_VERSION"
    INCONSISTENT=1
elif [ -n "$README_VER" ]; then
    echo "     ✅ README badge v$README_VER = SKILL.md $SELF_VERSION"
fi

if [ -n "$CHANGELOG_VER" ] && [ "$CHANGELOG_VER" != "$SELF_VERSION" ]; then
    echo "     ⚠️  CHANGELOG.md 顶部版本 v$CHANGELOG_VER ≠ SKILL.md frontmatter version $SELF_VERSION"
    INCONSISTENT=1
elif [ -n "$CHANGELOG_VER" ]; then
    echo "     ✅ CHANGELOG.md 顶部 v$CHANGELOG_VER = SKILL.md $SELF_VERSION"
fi

if [ -z "$README_VER" ]; then
    echo "     ⚠️  README.md 未找到 Version badge"
fi
if [ -z "$CHANGELOG_VER" ]; then
    echo "     ⚠️  CHANGELOG.md 顶部未找到 v0.x.x 版本号"
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
