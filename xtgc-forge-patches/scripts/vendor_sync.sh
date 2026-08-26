#!/bin/bash
# vendor_sync.sh · xtgc-forge vendor 上游同步 (MVP, R02 方案 E 第 3 步)
# 作者：R04 自动生成（2026-08-26）
#
# 设计原则（R02 E.3 + R02 §7 收口）：
#   1. **永远不自动 apply** —— 把同步决策权留给用户
#   2. **默认 dry-run** —— 任何写操作前用户审
#   3. **失败静默** —— curl/网络异常只 INFO，不 WARN，避免噪音
#   4. **零外部依赖** —— 只用 bash + curl + tar + diff + awk + grep + sed
#   5. **可独立运行** —— 不强制依赖 R03 的 probe helper，但默认复用
#
# 范围（MVP）：
#   list    列出 5 个 vendor 子 skill 的 VERSION.md 状态
#   check   探测上游最新 commit（委托 R03 的 vendor-freshness-check.sh）
#   fetch   拉上游 tarball 到 .vendor_staging/<skill>/
#   diff    diff vendored vs .vendor_staging/<skill>
#   apply   **不在 MVP 范围** —— R05 单独做（3-way merge 风险）
#
# 用法：
#   bash vendor_sync.sh list
#   bash vendor_sync.sh check
#   bash vendor_sync.sh fetch <skill>|--all
#   bash vendor_sync.sh diff <skill>|--all
#   bash vendor_sync.sh --help

set -e

# === 路径解析（与 R03 一致）===
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -n "${XTGC_ROOT:-}" ] && [ -d "${XTGC_ROOT}/vendor" ]; then
    : # 用环境变量
elif [ -d "${SCRIPT_DIR}/../xtgc-forge-clone/vendor" ]; then
    XTGC_ROOT="$(cd "${SCRIPT_DIR}/../xtgc-forge-clone" && pwd)"
elif [ -d "${SCRIPT_DIR}/../../xtgc-forge-clone/vendor" ]; then
    XTGC_ROOT="$(cd "${SCRIPT_DIR}/../../xtgc-forge-clone" && pwd)"
else
    XTGC_ROOT="${XTGC_ROOT:-$(pwd)}"
fi
VENDOR_DIR="$XTGC_ROOT/vendor"
STAGING_DIR="$XTGC_ROOT/.vendor_staging"
BACKUP_DIR="$XTGC_ROOT/.vendor_backup"
DIFF_DIR="$XTGC_ROOT/.vendor_diff"

# R03 的 probe helper 路径（默认复用 check）
PROBE_HELPER="${PROBE_HELPER:-$(dirname "$SCRIPT_DIR")/check-ready-probe/vendor-freshness-check.sh}"

# 颜色（Windows Terminal 也支持 ANSI）
if [ -t 1 ]; then
    RED='\033[0;31m'; GRN='\033[0;32m'; YLW='\033[1;33m'; CYN='\033[0;36m'; NC='\033[0m'
else
    RED=''; GRN=''; YLW=''; CYN=''; NC=''
fi

log_info() { printf "${CYN}ℹ${NC}  %s\n" "$*"; }
log_ok()   { printf "${GRN}✅${NC}  %s\n" "$*"; }
log_warn() { printf "${YLW}⚠${NC}  %s\n" "$*"; }
log_err()  { printf "${RED}❌${NC}  %s\n" "$*" >&2; }

# === VERSION.md 解析（提取 4 个字段）===
parse_version_md() {
    local skill="$1"
    local f="$VENDOR_DIR/$skill/VERSION.md"
    if [ ! -f "$f" ]; then
        echo "MISSING"
        return 1
    fi
    local repo path commit verified branch
    repo=$(grep -oE '`upstream_repo`\s*\|\s*`[^`]+`' "$f" | head -1 | sed -E 's/.*`([^`]+)`$/\1/')
    path=$(grep -oE '`upstream_skill_path`\s*\|\s*`[^`]+`' "$f" | head -1 | sed -E 's/.*`([^`]+)`$/\1/')
    commit=$(grep -oE '`vendored_commit`\s*\|\s*`[^`]+`' "$f" | head -1 | sed -E 's/.*`([^`]+)`$/\1/')
    verified=$(grep -oE '`last_verified`\s*\|\s*`[^`]+`' "$f" | head -1 | sed -E 's/.*`([^`]+)`$/\1/')
    branch=$(grep -oE '`upstream_branch`\s*\|\s*`[^`]+`' "$f" | head -1 | sed -E 's/.*`([^`]+)`$/\1/')
    echo "${repo}|${path}|${commit}|${verified}|${branch}"
}

# === 子命令：list ===
cmd_list() {
    echo "================================================"
    echo "  xtgc-forge vendor 子 skill 状态清单"
    echo "================================================"
    printf "  %-32s %-10s %-12s %s\n" "SKILL" "AGE" "STATUS" "UPSTREAM"
    printf "  %-32s %-10s %-12s %s\n" "----" "---" "------" "--------"
    local total=0 missing=0 present=0
    for skill in bilingual-paper-reader literature-matrix-builder causal-inference-architect research-method-selector academic-humanizer; do
        total=$((total+1))
        local info age_str status_str upstream_short
        info=$(parse_version_md "$skill" 2>/dev/null) || true
        if [ "$info" = "MISSING" ]; then
            printf "  %-32s %-10s %-12s %s\n" "$skill" "-" "❌ NO VERSION.md" "-"
            missing=$((missing+1))
            continue
        fi
        present=$((present+1))
        IFS='|' read -r repo path commit verified <<< "$info"
        upstream_short=$(echo "$repo" | sed 's|https://github.com/||' | cut -c1-40)
        # 计算 age
        if [ -n "$verified" ] && [ "$verified" != "" ]; then
            local today_epoch verified_epoch days
            today_epoch=$(date +%s 2>/dev/null || echo 0)
            verified_epoch=$(date -d "$verified" +%s 2>/dev/null || echo 0)
            if [ "$today_epoch" -gt 0 ] && [ "$verified_epoch" -gt 0 ]; then
                days=$(( (today_epoch - verified_epoch) / 86400 ))
                age_str="${days}d"
            else
                age_str="?"
            fi
        else
            age_str="?"
        fi
        # 简化状态（详细状态由 check 命令做）
        status_str="📋 logged"
        printf "  %-32s %-10s %-12s %s\n" "$skill" "$age_str" "$status_str" "$upstream_short"
    done
    echo ""
    echo "  total=$total present=$present missing_version_md=$missing"
    echo "  详细漂移探测: bash vendor_sync.sh check"
    echo "  同步上游 fetch: bash vendor_sync.sh fetch --all"
    echo "================================================"
}

# === 子命令：check（委托 R03 probe helper）===
cmd_check() {
    if [ ! -f "$PROBE_HELPER" ]; then
        log_err "probe helper 不存在: $PROBE_HELPER"
        log_info "请设置 PROBE_HELPER 环境变量指向 vendor-freshness-check.sh"
        return 1
    fi
    log_info "委托 R03 probe helper: $PROBE_HELPER --probe"
    bash "$PROBE_HELPER" --probe "$@"
}

# === fetch 核心：从 codeload 拉 tarball + 提取子树 ===
fetch_one() {
    local skill="$1"
    local info repo path commit branch
    info=$(parse_version_md "$skill" 2>/dev/null) || { log_err "$skill: VERSION.md 不存在"; return 1; }
    IFS='|' read -r repo path commit verified branch <<< "$info"
    if [ -z "$repo" ] || [ "$repo" = "" ]; then
        log_err "$skill: upstream_repo 为空（VERSION.md 未填）"
        return 1
    fi
    # branch 默认 main（VERSION.md 未填时兜底）
    [ -z "$branch" ] && branch="main"
    # repo 形如 https://github.com/owner/repo → owner/repo
    local repo_short
    repo_short=$(echo "$repo" | sed -E 's|https?://github.com/||')
    local url="https://codeload.github.com/${repo_short}/tar.gz/refs/heads/${branch}"
    local tmp_tar
    tmp_tar="$(mktemp -t vendor_sync_XXXXXX.tar.gz)"
    log_info "[$skill] GET $url"
    if ! curl -fsSL --max-time 45 "$url" -o "$tmp_tar" 2>/dev/null; then
        log_err "[$skill] 下载失败：$url（网络/分支名/权限？）"
        rm -f "$tmp_tar"
        return 1
    fi
    local size
    size=$(stat -c%s "$tmp_tar" 2>/dev/null || stat -f%z "$tmp_tar" 2>/dev/null || echo 0)
    if [ "$size" -lt 200 ]; then
        log_err "[$skill] tarball 太小（${size}B），可能 404 或空仓库"
        rm -f "$tmp_tar"
        return 1
    fi
    # 找 tarball 顶层目录名（codeload 命名约定：<repo>-<branch>/）
    local topdir
    topdir=$(tar -tzf "$tmp_tar" 2>/dev/null | head -1 | cut -d'/' -f1)
    if [ -z "$topdir" ]; then
        log_err "[$skill] tarball 解压失败"
        rm -f "$tmp_tar"
        return 1
    fi
    local skill_staging="$STAGING_DIR/$skill"
    rm -rf "$skill_staging"
    mkdir -p "$skill_staging"
    # 路径分支：
    #   path = "." 或 ""  → 取 tarball 顶层根
    #   path = "skills/<s>" → 取 ${topdir}/skills/<s>/
    if [ -z "$path" ] || [ "$path" = "." ]; then
        log_info "[$skill] 提取根: $topdir/ → $skill_staging/"
        tar -xzf "$tmp_tar" -C "$skill_staging" --strip-components=1 "$topdir" 2>/dev/null
    else
        log_info "[$skill] 提取子树: ${topdir}/${path}/ → $skill_staging/"
        tar -xzf "$tmp_tar" -C "$skill_staging" --strip-components=2 "${topdir}/${path}" 2>/dev/null
        # Nero1688 等 mono-repo 经常嵌套：path=skills/<s>/，但内部还有 <s>/ 子层
        # 自动检测并上提：若 staging 下只有 1 个名为 <skill> 的子目录，且其下有 SKILL.md/ATTRIBUTION.md
        if [ ! -f "$skill_staging/SKILL.md" ] && [ ! -f "$skill_staging/ATTRIBUTION.md" ] && [ -d "$skill_staging/$skill" ]; then
            log_info "[$skill] 检测到嵌套子目录 '$skill'，自动上提"
            shopt -s dotglob 2>/dev/null
            mv "$skill_staging/$skill"/* "$skill_staging"/ 2>/dev/null
            shopt -u dotglob 2>/dev/null
            rmdir "$skill_staging/$skill" 2>/dev/null
        fi
    fi
    rm -f "$tmp_tar"
    # 验证提取成功（至少有 SKILL.md 或 ATTRIBUTION.md）
    if [ -f "$skill_staging/SKILL.md" ] || [ -f "$skill_staging/ATTRIBUTION.md" ]; then
        local extracted_files
        extracted_files=$(find "$skill_staging" -type f | wc -l)
        log_ok "[$skill] fetch OK → $skill_staging/ (${extracted_files} files)"
        return 0
    else
        log_err "[$skill] 提取后未发现 SKILL.md/ATTRIBUTION.md，路径 '${path}' 可能不对"
        return 1
    fi
}

cmd_fetch_stub() { log_warn "fetch 尚未实现（R04 MVP 范围）"; return 1; }

# === 子命令：fetch ===
cmd_fetch() {
    local target="${1:---all}"
    mkdir -p "$STAGING_DIR"
    if [ "$target" = "--all" ]; then
        log_info "fetch --all (5 skills)"
        local ok=0 fail=0
        for skill in bilingual-paper-reader literature-matrix-builder causal-inference-architect research-method-selector academic-humanizer; do
            if fetch_one "$skill"; then
                ok=$((ok+1))
            else
                fail=$((fail+1))
            fi
        done
        echo ""
        log_info "fetch 完成: ok=$ok fail=$fail"
        [ $fail -gt 0 ] && return 1 || return 0
    else
        fetch_one "$target"
    fi
}

# === diff 核心：递归 diff vendored vs staging（纯 stdout，不写文件）===
diff_one() {
    local skill="$1"
    local vendored="$VENDOR_DIR/$skill"
    local staging="$STAGING_DIR/$skill"
    if [ ! -d "$vendored" ]; then
        log_err "[$skill] vendored 目录不存在: $vendored"
        return 1
    fi
    if [ ! -d "$staging" ]; then
        log_err "[$skill] staging 目录不存在: $staging（先跑 fetch）"
        return 1
    fi
    echo ""
    echo "════════════════════════════════════════════════════════════════════"
    log_info "[$skill] diff: $staging/ ← $vendored/"
    echo "────────────────────────────────────────────────────────────────────"
    # 1) 文件集统计
    local v_files s_files
    v_files=$(cd "$vendored" && find . -type f | wc -l)
    s_files=$(cd "$staging" && find . -type f | wc -l)
    echo "  文件数：vendored=$v_files  staging=$s_files"
    # 2) 仅 vendored 独有（=本地补丁/本地注释）
    local only_v
    only_v=$(cd "$staging" && find . -type f 2>/dev/null | while read f; do [ ! -f "$vendored/$f" ] && echo "$f"; done)
    if [ -n "$only_v" ]; then
        echo ""
        echo "  ⚠️  vendored 独有（本地补丁，未在上游）："
        echo "$only_v" | sed 's/^/      + /'
    fi
    # 3) 仅 staging 独有（=上游新增）
    local only_s
    only_s=$(cd "$vendored" && find . -type f 2>/dev/null | while read f; do [ ! -f "$staging/$f" ] && echo "$f"; done)
    if [ -n "$only_s" ]; then
        echo ""
        echo "  🆕 staging 独有（上游新增，vendored 缺）："
        echo "$only_s" | sed 's/^/      + /'
    fi
    # 4) 共同文件但内容不同 → diff -ru
    local common_diff=()
    while IFS= read -r f; do
        if [ -f "$staging/$f" ] && ! cmp -s "$vendored/$f" "$staging/$f" 2>/dev/null; then
            common_diff+=("$f")
        fi
    done < <(cd "$vendored" && find . -type f)
    if [ ${#common_diff[@]} -gt 0 ]; then
        echo ""
        echo "  🔄 内容差异文件（${#common_diff[@]} 个）："
        for f in "${common_diff[@]}"; do
            local vs ss
            vs=$(wc -c < "$vendored/$f" 2>/dev/null || echo 0)
            ss=$(wc -c < "$staging/$f" 2>/dev/null || echo 0)
            echo "      ~ $f  (vendored=${vs}B → staging=${ss}B)"
        done
        echo ""
        echo "  ── 详细 diff（unified format）──"
        diff -ru "$vendored" "$staging" 2>/dev/null | head -n 200 | sed 's/^/      /'
        local total_diff_lines
        total_diff_lines=$(diff -ru "$vendored" "$staging" 2>/dev/null | wc -l)
        if [ "$total_diff_lines" -gt 200 ]; then
            echo "      ... (还有 $((total_diff_lines - 200)) 行未显示，用 'diff -ru $vendored $staging' 完整看)"
        fi
    fi
    # 5) 无差异
    if [ -z "$only_v" ] && [ -z "$only_s" ] && [ ${#common_diff[@]} -eq 0 ]; then
        echo "  ✅ vendored 与 staging 完全一致"
    fi
    echo "════════════════════════════════════════════════════════════════════"
}

cmd_diff() {
    local target="${1:---all}"
    if [ ! -d "$STAGING_DIR" ] || [ -z "$(ls -A "$STAGING_DIR" 2>/dev/null)" ]; then
        log_err "staging 目录为空或不存在：先跑 'bash vendor_sync.sh fetch --all'"
        return 1
    fi
    if [ "$target" = "--all" ]; then
        log_info "diff --all (5 skills)"
        local ok=0 fail=0
        for skill in bilingual-paper-reader literature-matrix-builder causal-inference-architect research-method-selector academic-humanizer; do
            if diff_one "$skill"; then
                ok=$((ok+1))
            else
                fail=$((fail+1))
            fi
        done
        echo ""
        log_info "diff 完成: ok=$ok fail=$fail"
        [ $fail -gt 0 ] && return 1 || return 0
    else
        diff_one "$target"
    fi
}

# === 子命令：help ===
cmd_help() {
    # 打印头部注释
    awk '/^[^#]/ && NR>1 && !/^$/{exit} {print}' "$0" | sed 's/^# \?//' | sed '/^$/d' | head -n 50
}

# === 入口 ===
case "${1:-help}" in
    list)        cmd_list ;;
    check)       shift; cmd_check "$@" ;;
    fetch)       shift; cmd_fetch "$@" ;;
    diff)        shift; cmd_diff "$@" ;;
    apply)       log_warn "apply 不在 R04 MVP 范围（R05 单独做）"; exit 1 ;;
    --help|-h|help|"")  cmd_help ;;
    *)
        log_err "未知子命令: $1"
        echo "用法: bash vendor_sync.sh {list|check|fetch|diff|apply|--help}"
        exit 2
        ;;
esac
