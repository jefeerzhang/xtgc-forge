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
# XTGC_ROOT 优先级：环境变量 > 同级目录的 xtgc-forge-clone > 上跳 1 级 > 上跳 2 级
if [ -n "${XTGC_ROOT:-}" ] && [ -d "${XTGC_ROOT}/vendor" ]; then
    : # 用环境变量
elif [ -d "${SCRIPT_DIR}/../xtgc-forge-clone/vendor" ]; then
    XTGC_ROOT="$(cd "${SCRIPT_DIR}/../xtgc-forge-clone" && pwd)"
elif [ -d "${SCRIPT_DIR}/../../xtgc-forge-clone/vendor" ]; then
    XTGC_ROOT="$(cd "${SCRIPT_DIR}/../../xtgc-forge-clone" && pwd)"
else
    XTGC_ROOT="$SCRIPT_DIR"
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

SKILLS=("bilingual-paper-reader" "literature-matrix-builder" "research-method-selector" "causal-inference-architect" "academic-humanizer")

# 收集结果
results_json="["
first=1
results_human=""

for skill in "${SKILLS[@]}"; do
    version_file="$VENDOR_DIR/$skill/VERSION.md"
    if [ ! -f "$version_file" ]; then
        results_human+="  ⚠️  $skill: VERSION.md 不存在(请先 cp xtgc-forge-patches/vendor-version/$skill-VERSION.md vendor/$skill/VERSION.md)
"
        [ $first -eq 0 ] && results_json+=","
        results_json+="{\"skill\":\"$skill\",\"status\":\"missing_version_md\"}"
        first=0
        continue
    fi

    vendored_commit=$(grep -oE '`vendored_commit`\s*\|\s*`[^`]+`' "$version_file" | head -1 | sed -E 's/.*`([^`]+)`$/\1/')
    vendored_from=$(grep -oE '`vendored_from`\s*\|\s*`[^`]+`' "$version_file" | head -1 | sed -E 's/.*`([^`]+)`$/\1/')
    last_verified=$(grep -oE '`last_verified`\s*\|\s*`[^`]+`' "$version_file" | head -1 | sed -E 's/.*`([^`]+)`$/\1/')
    refresh_days=$(grep -oE '`refresh_cadence_days`\s*\|\s*`[^`]+`' "$version_file" | head -1 | sed -E 's/.*`([^`]+)`$/\1/')
    criticality=$(grep -oE '`criticality`\s*\|\s*`[^`]+`' "$version_file" | head -1 | sed -E 's/.*`([^`]+)`$/\1/')

    # 计算 age
    today=$(date -u +%s)
    verified_ts=$(date -d "$last_verified" -u +%s 2>/dev/null || echo 0)
    age_days=$(( (today - verified_ts) / 86400 ))
    refresh_days=${refresh_days:-90}

    drift_status="ok"
    upstream_commit=""
    fetch_status=""

    if [ $PROBE -eq 1 ] && [ $PROBE_FORCE_OFFLINE -eq 0 ]; then
        # 探测上游（用 git ls-remote 拿 HEAD commit）
        if command -v git >/dev/null 2>&1; then
            upstream_commit=$(git ls-remote https://github.com/AIScientists-Dev/academic-humanizer HEAD 2>/dev/null | awk '{print $1}' | head -c 7)
            # Nero1688 仓库是 mono-repo，没有子目录 HEAD；只能探测仓库级 commit
            if [ "$skill" != "academic-humanizer" ]; then
                upstream_commit=$(git ls-remote https://github.com/Nero1688/claude-academic-skills HEAD 2>/dev/null | awk '{print $1}' | head -c 7)
            fi
            if [ -n "$upstream_commit" ]; then
                fetch_status="ok"
                if [ "$upstream_commit" != "$vendored_commit" ]; then
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
    [ "$drift_status" = "missing_version_md" ] && status_icon="❌"

    results_human+="$status_icon $skill"
    results_human+=" | age=${age_days}d / refresh=${refresh_days}d"
    results_human+=" | criticality=$criticality"
    [ -n "$upstream_commit" ] && results_human+=" | upstream=$upstream_commit vs vendored=$vendored_commit"
    [ "$drift_status" = "upstream_moved" ] && results_human+=" **DRIFT**"
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
