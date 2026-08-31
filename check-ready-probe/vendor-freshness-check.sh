#!/bin/bash
# vendor-freshness-check.sh · xtgc-forge vendor 上游漂移探测（方案 E 第 2 步）
# 作者：R02/R03 自动生成（2026-08-26）  ·  不修改 check-ready.sh 即可独立使用
#
# 设计原则（与方案 E 一致）：
#   1. **默认离线** —— 不带 --probe 不联网
#   2. **失败静默** —— curl/网络异常只 INFO，不 WARN，避免噪音
#   3. **可独立运行** —— 不用 apply 到 check-ready.sh，单独调
#
# 用法：
#   bash vendor-freshness-check.sh                    # 默认模式：仅读 VERSION.md → 报告 age，不联网
#   bash vendor-freshness-check.sh --probe            # 探测上游 commit，给出 drift 警告
#   bash vendor-freshness-check.sh --probe --json     # 机器读 JSON 输出（CI 友好）
#   XTGC_OFFLINE=1 bash vendor-freshness-check.sh --probe  # 强制离线（--probe 但仍跳过网络）

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# XTGC_ROOT：环境变量（且其下有 vendor/）> 本脚本上一级（仓库根）
# 不探测 xtgc-forge-clone，避免写到旁边另一棵树。
if [ -n "${XTGC_ROOT:-}" ] && [ -d "${XTGC_ROOT}/vendor" ]; then
    : # 用环境变量
else
    XTGC_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
fi
VENDOR_DIR="$XTGC_ROOT/vendor"

PROBE=0
JSON_OUT=0
[ "${XTGC_OFFLINE:-0}" = "1" ] && PROBE_FORCE_OFFLINE=1 || PROBE_FORCE_OFFLINE=0
for arg in "$@"; do
    case "$arg" in
        --probe) PROBE=1 ;;
        --json)  JSON_OUT=1 ;;
        --help|-h)
            # 打印头部注释（直到第一个非注释非空行）
            awk '/^[^#]/ && NR>1 && !/^$/{exit} {print}' "$0" | sed 's/^# \?//' | sed '/^$/d' | head -n 25
            exit 0
            ;;
        *) echo "未知参数:$arg（用 --help 看用法）" >&2; exit 2 ;;
    esac
done

# 已注册 vendor 子 skill：从 vendor/ 子目录派生（与 vendor_sync.sh 同一来源）
SKILLS=()
for _skill_dir in "$VENDOR_DIR"/*/; do
    [ -d "$_skill_dir" ] || continue
    SKILLS+=("$(basename "$_skill_dir")")
done

# 两个 SHA 是否同一提交（短针是长针前缀，且至少 7 位）
_sha_match() {
    local a="${1,,}" b="${2,,}"
    [ -z "$a" ] || [ -z "$b" ] && return 1
    [ "$a" = "$b" ] && return 0
    [ ${#a} -ge 7 ] && [ ${#b} -ge 7 ] || return 1
    case "$b" in "$a"*) return 0 ;; esac
    case "$a" in "$b"*) return 0 ;; esac
    return 1
}

# 收集结果
results_json="["
first=1
results_human=""

for skill in "${SKILLS[@]}"; do
    version_file="$VENDOR_DIR/$skill/VERSION.md"
    if [ ! -f "$version_file" ]; then
        results_human+="  ⚠️  $skill: VERSION.md 不存在(请参考现有 vendor 子目录中的 VERSION.md 补充)
"
        [ $first -eq 0 ] && results_json+=","
        results_json+="{\"skill\":\"$skill\",\"status\":\"missing_version_md\"}"
        first=0
        continue
    fi

    vendored_commit=$(grep -oE '`vendored_commit`\s*\|\s*`[^`]+`' "$version_file" | head -1 | sed -E 's/.*`([^`]+)`$/\1/')
    last_verified=$(grep -oE '`last_verified`\s*\|\s*`[^`]+`' "$version_file" | head -1 | sed -E 's/.*`([^`]+)`$/\1/')
    refresh_days=$(grep -oE '`refresh_cadence_days`\s*\|\s*`[^`]+`' "$version_file" | head -1 | sed -E 's/.*`([^`]+)`$/\1/')
    criticality=$(grep -oE '`criticality`\s*\|\s*`[^`]+`' "$version_file" | head -1 | sed -E 's/.*`([^`]+)`$/\1/')
    upstream_repo=$(grep -oE '`upstream_repo`\s*\|\s*`[^`]+`' "$version_file" | head -1 | sed -E 's/.*`([^`]+)`$/\1/')

    # 计算 age
    today=$(date -u +%s)
    verified_ts=$(date -d "$last_verified" -u +%s 2>/dev/null || echo 0)
    age_days=$(( (today - verified_ts) / 86400 ))
    refresh_days=${refresh_days:-90}

    drift_status="ok"
    upstream_commit=""
    fetch_status=""

    if [ $PROBE -eq 1 ] && [ $PROBE_FORCE_OFFLINE -eq 0 ]; then
        # vendored_commit 若是本仓库 git 对象，那是本地同步标记，不能拿去对上游 HEAD
        if [ -n "$vendored_commit" ] && git -C "$XTGC_ROOT" cat-file -t "$vendored_commit" >/dev/null 2>&1 \
            && git -C "$XTGC_ROOT" cat-file -e "${vendored_commit}:vendor/${skill}" >/dev/null 2>&1; then
            drift_status="local_pin"
            fetch_status="skipped_local_pin"
        elif [ -z "$upstream_repo" ]; then
            drift_status="pin_invalid"
            fetch_status="missing_upstream_repo"
        elif command -v git >/dev/null 2>&1; then
            local_repo="$upstream_repo"
            # 去掉可能的 .git 后缀
            local_repo="${local_repo%.git}"
            upstream_commit=$(git ls-remote "$local_repo" HEAD 2>/dev/null | awk '{print $1}' | head -1)
            if [ -n "$upstream_commit" ]; then
                fetch_status="ok"
                if ! _sha_match "$upstream_commit" "$vendored_commit"; then
                    drift_status="upstream_moved"
                fi
            else
                fetch_status="network_fail"
            fi
        else
            fetch_status="git_missing"
        fi
    fi

    # 报告（人类）
    status_icon="✅"
    [ $age_days -gt $refresh_days ] && status_icon="⚠️ "
    [ "$drift_status" = "upstream_moved" ] && status_icon="🔄"
    [ "$drift_status" = "local_pin" ] && status_icon="📌"
    [ "$drift_status" = "pin_invalid" ] && status_icon="⚠️ "
    [ "$drift_status" = "missing_version_md" ] && status_icon="❌"

    results_human+="$status_icon $skill"
    results_human+=" | age=${age_days}d / refresh=${refresh_days}d"
    results_human+=" | criticality=$criticality"
    [ -n "$upstream_commit" ] && results_human+=" | upstream=$upstream_commit vs vendored=$vendored_commit"
    [ "$drift_status" = "upstream_moved" ] && results_human+=" **DRIFT**"
    [ "$drift_status" = "local_pin" ] && results_human+=" (vendored_commit 是本仓同步点，未与上游 HEAD 比 SHA)"
    [ "$drift_status" = "pin_invalid" ] && results_human+=" (缺少 upstream_repo)"
    [ -n "$fetch_status" ] && [ "$fetch_status" != "ok" ] && results_human+=" (probe=$fetch_status)"
    results_human+="
"

    # JSON
    [ $first -eq 0 ] && results_json+=","
    results_json+="{\"skill\":\"$skill\",\"vendored_commit\":\"$vendored_commit\",\"last_verified\":\"$last_verified\",\"age_days\":$age_days,\"refresh_days\":$refresh_days,\"criticality\":\"$criticality\",\"drift_status\":\"$drift_status\",\"upstream_commit\":\"$upstream_commit\",\"fetch_status\":\"$fetch_status\"}"
    first=0
done
results_json+="]"

# 输出
echo "================================================"
if [ $PROBE -eq 1 ]; then
    echo "  vendor 上游漂移探测 (--probe 模式) · xtgc-forge"
else
    echo "  vendor VERSION.md 健康度 (本地模式,未联网) · xtgc-forge"
fi
echo "================================================"
echo ""
if [ $PROBE -eq 0 ]; then
    echo "提示:用 --probe 联网探测上游 commit"
    echo ""
fi
echo "$results_human"
echo "================================================"

if [ $JSON_OUT -eq 1 ]; then
    echo "$results_json"
fi
