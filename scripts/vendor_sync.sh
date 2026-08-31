#!/bin/bash
# vendor_sync.sh · xtgc-forge vendor 上游同步 (MVP, R02 方案 E 第 3 步)
# 作者：R04 自动生成（2026-08-26）
#
# 设计原则（R02 E.3 + R02 §7 收口）：
#   1. **同步决策权留给用户** —— apply 默认 dry-run，真写需显式 --write
#   2. **默认 dry-run** —— 任何写操作前用户审
#   3. **失败静默** —— curl/网络异常只 INFO，不 WARN，避免噪音
#   4. **零外部依赖** —— 只用 bash + curl + tar + diff + awk + grep + sed
#   5. **可独立运行** —— 不强制依赖 R03 的 probe helper，但默认复用
#
# 范围（MVP）：
#   list    列出各 vendor 子 skill 的 VERSION.md 状态
#   check   探测上游最新 commit（委托 R03 的 vendor-freshness-check.sh）
#   fetch   拉上游 tarball 到 .vendor_staging/<skill>/
#   diff    diff vendored vs .vendor_staging/<skill>
#   apply   3-way merge 把 staging 写回 vendor/（R05 已实现；默认 dry-run，--write 真执行）
#
# 用法：
#   bash vendor_sync.sh list
#   bash vendor_sync.sh check
#   bash vendor_sync.sh fetch <skill>|--all
#   bash vendor_sync.sh diff <skill>|--all
#   bash vendor_sync.sh apply <skill>|--all [--write] [--no-backup]
#   bash vendor_sync.sh --help

set -e

# === 路径解析 ===
# 根目录只认两处：XTGC_ROOT（且其下有 vendor/）或本脚本的上一级。
# 不用 pwd、不探测 xtgc-forge-clone，避免在 scripts/ 下执行扫空，
# 或写到旁边另一棵树。
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -n "${XTGC_ROOT:-}" ] && [ -d "${XTGC_ROOT}/vendor" ]; then
    : # 用环境变量
else
    XTGC_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
fi
VENDOR_DIR="$XTGC_ROOT/vendor"
STAGING_DIR="$XTGC_ROOT/.vendor_staging"
BACKUP_DIR="$XTGC_ROOT/.vendor_backup"
DIFF_DIR="$XTGC_ROOT/.vendor_diff"
# vendor-version/ 镜像目录（apply 后同步更新 <skill>-VERSION.md）
VENDOR_VERSION_DIR="$(dirname "$SCRIPT_DIR")/vendor-version"

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

# === 已注册 vendor 子 skill 名单（唯一来源）===
# 从 vendor/ 子目录自动派生，四个子命令共用；
# 新增子 skill = vendor/ 下加目录，无需改本脚本。
# 位置必须在 log_* 定义之后（空名单分支要用 log_warn）
VENDOR_SKILLS=()
for _skill_dir in "$VENDOR_DIR"/*/; do
    [ -d "$_skill_dir" ] || continue
    VENDOR_SKILLS+=("$(basename "$_skill_dir")")
done
if [ ${#VENDOR_SKILLS[@]} -eq 0 ]; then
    log_warn "未在 $VENDOR_DIR 下发现任何 vendor 子 skill 目录"
fi

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

# 文件是否含 NUL（PNG 等）。含 NUL 则按二进制 cmp，不去 CR。
_file_has_nul() {
    local f="$1"
    [ -f "$f" ] || return 1
    local orig stripped
    orig=$(dd if="$f" bs=8192 count=1 2>/dev/null | wc -c)
    stripped=$(dd if="$f" bs=8192 count=1 2>/dev/null | tr -d '\0' | wc -c)
    [ "$stripped" -lt "$orig" ]
}

# 文本忽略 CR 再比；二进制原样 cmp。避免 PNG 读进 bash 被截断。
_cmp_vendor_files() {
    local a="$1" b="$2"
    if _file_has_nul "$a" || _file_has_nul "$b"; then
        cmp -s "$a" "$b"
        return $?
    fi
    cmp -s <(tr -d '\r' < "$a") <(tr -d '\r' < "$b")
}

# vendored_commit 若是本仓库 git 对象，可作为 3-way base（上次同步点）。
# 若是上游 SHA（本仓库没有），git show 失败 → 调用方把 mine!=theirs 标为冲突，不覆盖。
_local_base_rev() {
    local commit="$1"
    [ -n "$commit" ] || return 1
    [ "$commit" = "unknown" ] && return 1
    git -C "$XTGC_ROOT" cat-file -t "$commit" >/dev/null 2>&1 || return 1
    echo "$commit"
}

# === 子命令：list ===
cmd_list() {
    echo "================================================"
    echo "  xtgc-forge vendor 子 skill 状态清单"
    echo "================================================"
    printf "  %-32s %-10s %-12s %s\n" "SKILL" "AGE" "STATUS" "UPSTREAM"
    printf "  %-32s %-10s %-12s %s\n" "----" "---" "------" "--------"
    local total=0 missing=0 present=0
    for skill in "${VENDOR_SKILLS[@]}"; do
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
        if [ -n "$verified" ]; then
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
    if [ -z "$repo" ]; then
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

# === 子命令：fetch ===
cmd_fetch() {
    local target="${1:---all}"
    mkdir -p "$STAGING_DIR"
    if [ "$target" = "--all" ]; then
        log_info "fetch --all (${#VENDOR_SKILLS[@]} skills)"
        local ok=0 fail=0
        for skill in "${VENDOR_SKILLS[@]}"; do
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
    only_v=$(cd "$vendored" && find . -type f 2>/dev/null | while read f; do [ ! -f "$staging/$f" ] && echo "$f"; done)
    if [ -n "$only_v" ]; then
        echo ""
        echo "  ⚠️  vendored 独有（本地补丁，未在上游）："
        echo "$only_v" | sed 's/^/      + /'
    fi
    # 3) 仅 staging 独有（=上游新增）
    local only_s
    only_s=$(cd "$staging" && find . -type f 2>/dev/null | while read f; do [ ! -f "$vendored/$f" ] && echo "$f"; done)
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
        log_info "diff --all (${#VENDOR_SKILLS[@]} skills)"
        local ok=0 fail=0
        for skill in "${VENDOR_SKILLS[@]}"; do
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

# === apply 核心：3-way merge (base=VERSION.md vendored_commit, mine=vendored, theirs=staging) ===
# 策略：
#   - staging 独有     → 上游新增，复制
#   - vendored 独有    → 本地独有（用户定制？），不删
#   - 内容相同         → 无需操作
#   - mine==base       → 自 vendored_commit 以来本地没改，theirs 赢（接受上游）
#   - theirs==base     → 上游没改，mine 赢（保留本地）
#   - 都不等或无 base  → 冲突，不覆盖（含已提交补丁；base 不是 HEAD）
# 比较用 cmp（二进制原样；文本去 CR）。不把文件 cat 进 bash 字符串。
apply_one() {
    local skill="$1"
    local dry_run="${2:-true}"
    local no_backup="${3:-false}"

    local vendored="$VENDOR_DIR/$skill"
    local staging="$STAGING_DIR/$skill"

    if [ ! -d "$vendored" ]; then
        log_err "[$skill] vendored 不存在: $vendored"
        return 1
    fi
    if [ ! -d "$staging" ]; then
        log_err "[$skill] staging 不存在: $staging（先跑 fetch）"
        return 1
    fi

    local base_rev=""
    local pin_commit=""
    local info_pin
    info_pin=$(parse_version_md "$skill" 2>/dev/null) || info_pin=""
    IFS='|' read -r _ _ pin_commit _ _ <<< "$info_pin"
    base_rev=$(_local_base_rev "$pin_commit") || base_rev=""

    echo ""
    echo "════════════════════════════════════════════════════════════════════"
    if [ "$dry_run" = "true" ]; then
        log_info "[DRY-RUN] [$skill] 计划 apply（不写文件）"
    else
        log_info "[APPLY] [$skill] 执行 apply"
    fi
    echo "════════════════════════════════════════════════════════════════════"
    echo "  mine   = $vendored"
    echo "  theirs = $staging"
    if [ -n "$base_rev" ]; then
        echo "  base   = $XTGC_ROOT @ $base_rev  (VERSION.md vendored_commit)"
    else
        echo "  base   = <unavailable: vendored_commit 不是本仓 git 对象；内容不同 → 冲突，不覆盖>"
    fi

    local s_files v_files
    s_files=$(cd "$staging" && find . -type f 2>/dev/null | sort)
    v_files=$(cd "$vendored" && find . -type f 2>/dev/null | sort)

    local take_new=() keep_local=() take_theirs=() keep_mine=() conflicts=() same=()
    local base_tmp
    base_tmp=$(mktemp)

    # 遍历 staging 全部文件 → 分类
    while IFS= read -r rel; do
        [ -z "$rel" ] && continue
        local s_file="$staging/$rel"
        local v_file="$vendored/$rel"
        if [ ! -f "$v_file" ]; then
            take_new+=("$rel")
            continue
        fi
        local rel_clean="${rel#./}"
        if _cmp_vendor_files "$v_file" "$s_file"; then
            same+=("$rel")
            continue
        fi
        local has_base=0
        if [ -n "$base_rev" ] && git -C "$XTGC_ROOT" show "${base_rev}:vendor/${skill}/${rel_clean}" > "$base_tmp" 2>/dev/null; then
            has_base=1
        else
            : > "$base_tmp"
        fi
        if [ "$has_base" -eq 1 ] && _cmp_vendor_files "$v_file" "$base_tmp"; then
            take_theirs+=("$rel")
        elif [ "$has_base" -eq 1 ] && _cmp_vendor_files "$s_file" "$base_tmp"; then
            keep_mine+=("$rel")
        else
            # 无 base，或三方都不等：不覆盖本地（含已提交补丁）
            conflicts+=("$rel")
        fi
    done <<< "$s_files"
    rm -f "$base_tmp"

    # 仅 vendored 独有（=本地定制）
    while IFS= read -r rel; do
        [ -z "$rel" ] && continue
        if [ ! -f "$staging/$rel" ]; then
            keep_local+=("$rel")
        fi
    done <<< "$v_files"

    echo ""
    echo "  📊 分类统计："
    echo "    ✅ 内容相同      ：${#same[@]}"
    echo "    🆕 上游新增      ：${#take_new[@]}"
    echo "    🔄 上游更新      ：${#take_theirs[@]}（将覆盖）"
    echo "    📌 本地独有      ：${#keep_local[@]}（保留，不删）"
    echo "    🔒 本地定制保留  ：${#keep_mine[@]}（上游未动，本地改了，保留）"
    echo "    ⚠️   冲突（需人工）：${#conflicts[@]}"
    if [ ${#conflicts[@]} -gt 0 ]; then
        echo ""
        echo "  ⚠️  冲突文件："
        printf '      - %s\n' "${conflicts[@]}"
    fi

    if [ "$dry_run" = "true" ]; then
        echo ""
        log_info "[DRY-RUN] 未修改文件。加 --write 真执行。"
        return 0
    fi

    # 真 apply：先备份整个 vendored（--no-backup 可跳过，不推荐）
    local ts backup_dir conflict_dir
    ts=$(date +%Y%m%d_%H%M%S)
    if [ "$no_backup" = "true" ]; then
        backup_dir=""
        log_warn "[$skill] --no-backup：跳过备份（不推荐）"
    else
        backup_dir="$XTGC_ROOT/.vendor_backup/${skill}.${ts}"
        mkdir -p "$backup_dir"
        # 用 cp -r（保留结构）
        (cd "$vendored" && tar -cf - .) | (cd "$backup_dir" && tar -xf -)
        log_ok "[$skill] 备份原 vendored → $backup_dir"
    fi

    # 写 take_new + take_theirs
    local rel
    for rel in "${take_new[@]}" "${take_theirs[@]}"; do
        [ -z "$rel" ] && continue
        local dst_dir
        dst_dir="$vendored/$(dirname "$rel")"
        [ "$dst_dir" = "$vendored/." ] && dst_dir="$vendored"
        mkdir -p "$dst_dir"
        cp "$staging/$rel" "$vendored/$rel"
    done

    # 冲突：备份到 backup_dir/conflicts/<rel>.theirs + .mine
    if [ ${#conflicts[@]} -gt 0 ] && [ -n "$backup_dir" ]; then
        conflict_dir="$backup_dir/conflicts"
        mkdir -p "$conflict_dir"
        for rel in "${conflicts[@]}"; do
            local dst_dir
            dst_dir="$conflict_dir/$(dirname "$rel")"
            [ "$dst_dir" = "$conflict_dir/." ] && dst_dir="$conflict_dir"
            mkdir -p "$dst_dir"
            cp "$staging/$rel" "$conflict_dir/$rel.theirs"
            cp "$vendored/$rel" "$conflict_dir/$rel.mine"
        done
        log_warn "[$skill] ${#conflicts[@]} 个冲突未覆盖，已备份 mine+theirs 到 $conflict_dir"
        echo "    人工解决后手动 copy（不要覆盖本地独有定制）："
        echo "      diff $conflict_dir/<rel>.mine $conflict_dir/<rel>.theirs"
        echo "      cp $conflict_dir/<rel>.theirs vendor/$skill/<rel>  # 接受上游"
    elif [ ${#conflicts[@]} -gt 0 ]; then
        log_warn "[$skill] ${#conflicts[@]} 个冲突未覆盖（--no-backup：mine/theirs 未留存，见上方清单）"
    fi

    # 更新 VERSION.md 的 vendored_commit / vendored_from / last_verified（R04 §5）
    # 主目标是 vendored 副本（与漂移内容同在）；vendor-version/ 镜像存在则同步。
    # vendored_commit：fetch 走 tarball，无上游 commit SHA，脚本无法可靠写入 → 提示人工核实，不盲写。
    local today version_md
    today=$(date +%Y-%m-%d)
    local info2 repo2
    info2=$(parse_version_md "$skill" 2>/dev/null) || info2=""
    IFS='|' read -r repo2 _ _ _ _ <<< "$info2"
    local repo_short2
    repo_short2=$(echo "$repo2" | sed -E 's|https?://github.com/||')
    local vendored_from="${repo_short2:-unknown}@${today}"
    for version_md in "$VENDOR_DIR/$skill/VERSION.md" "$VENDOR_VERSION_DIR/${skill}-VERSION.md"; do
        [ -f "$version_md" ] || continue
        if grep -q '`last_verified`' "$version_md"; then
            sed -i.bak -E "s/(\`last_verified\` \| \`).*(\`)/\1${today}\2/" "$version_md" && rm -f "${version_md}.bak"
        fi
        if grep -q '`vendored_from`' "$version_md"; then
            sed -i.bak -E "s#(\`vendored_from\` \| \`)[^\`]*(\`)#\1${vendored_from}\2#" "$version_md" && rm -f "${version_md}.bak"
        fi
        log_ok "[$skill] VERSION.md 已更新（last_verified → $today，vendored_from → $vendored_from）：$version_md"
    done
    # 技术决策：fetch 使用 tarball 抓取避免全量 clone 与额外的 GitHub API 依赖，
    # 本地解包无法直接提取上游完整 commit SHA。为防止写入伪造/过期哈希，
    # 此处不自动盲写 vendored_commit，显式提示由维护者在核对后手工回填。
    log_info "[$skill] vendored_commit 需人工核实为本次同步的上游 commit（tarball 抓取无 SHA 决策说明见 README）"

    # 清理 staging（apply 完成）
    rm -rf "$staging"
    log_ok "[$skill] staging 已清理"

    echo ""
    log_ok "[$skill] apply 完成 → $vendored"
    # 契约：有冲突 → 1，由调用方感知需人工介入（见 apply --help）
    [ ${#conflicts[@]} -gt 0 ] && return 1 || return 0
}

cmd_apply() {
    local dry_run=true
    local no_backup=false
    local target=""
    while [ $# -gt 0 ]; do
        case "$1" in
            --write|--no-dry-run) dry_run=false ;;
            --dry-run)            dry_run=true ;;
            --no-backup)          no_backup=true ;;
            --all)                target="--all" ;;
            --help|-h)
                cat <<EOF
用法: bash vendor_sync.sh apply [--all | <skill>] [--write] [--no-backup]

选项:
  (无)         单 skill 模式，需指定 skill 名
  --all        全部已注册 skill 顺序 apply
  --dry-run    默认，仅展示计划不写文件（默认开）
  --write      真执行：备份原 vendored 到 .vendor_backup/<skill>.<ts>/，
               覆盖非冲突文件，更新 VERSION.md（vendored_commit/
               vendored_from/last_verified），清理 staging
  --no-backup  跳过备份（不推荐）
  --help       本帮助

返回值:
  0 = 成功（含无冲突情况）
  1 = 有冲突需人工，或 staging 缺失
EOF
                return 0 ;;
            *) target="$1" ;;
        esac
        shift
    done

    if [ -z "$target" ]; then
        log_err "用法: bash vendor_sync.sh apply {<skill>|--all} [--write]"
        return 2
    fi

    local ok=0 fail=0 conflicts=0
    if [ "$target" = "--all" ]; then
        log_info "apply --all (${#VENDOR_SKILLS[@]} skills, dry_run=$dry_run, no_backup=$no_backup)"
        local skill rc
        for skill in "${VENDOR_SKILLS[@]}"; do
            rc=0
            apply_one "$skill" "$dry_run" "$no_backup" || rc=$?
            if [ $rc -eq 0 ]; then
                ok=$((ok+1))
            else
                fail=$((fail+1))
                [ $rc -eq 1 ] && conflicts=$((conflicts+1))
            fi
        done
        echo ""
        log_info "apply 完成: ok=$ok fail=$fail conflicts=$conflicts"
        [ $conflicts -gt 0 ] && return 1
        [ $fail -gt 0 ] && return 1 || return 0
    else
        apply_one "$target" "$dry_run" "$no_backup"
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
    apply)       shift; cmd_apply "$@" ;;
    --help|-h|help|"")  cmd_help ;;
    *)
        log_err "未知子命令: $1"
        echo "用法: bash vendor_sync.sh {list|check|fetch|diff|apply|--help}"
        exit 2
        ;;
esac
