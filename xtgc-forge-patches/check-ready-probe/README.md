# check-ready-probe · vendor 上游漂移探测（方案 E 第 2 步）

> **来源**：R02 方案 E 第 2 步落地（与 VERSION.md 配套使用）
> **依赖**：vendor/<skill>/VERSION.md × 5（来自 `../vendor-version/`）
> **零侵入**：不修改 `check-ready.sh`，作为独立 add-on 运行

---

## 📂 文件清单

```
xtgc-forge-patches/check-ready-probe/
├── README.md                       ← 本文件
├── vendor-freshness-check.sh       ← 主脚本（bash）
└── （可选）check-ready.sh.patch    ← 待你决定是否要 apply 到 check-ready.sh
```

---

## 🚀 快速使用（已通过实测）

### 1. 默认模式（**离线，仅检查 VERSION.md 健康度**）

```bash
bash vendor-freshness-check.sh
```

**实测输出**（2026-08-26）：

```
✅ bilingual-paper-reader  | age=0d / refresh=90d | criticality=core
✅ literature-matrix-builder | age=0d / refresh=60d | criticality=core
✅ research-method-selector | age=0d / refresh=60d | criticality=core
✅ causal-inference-architect | age=0d / refresh=30d | criticality=core
✅ academic-humanizer      | age=0d / refresh=30d | criticality=core
```

### 2. 探测模式（**联网，对比上游 commit**）

```bash
bash vendor-freshness-check.sh --probe
```

**实测输出**（2026-08-26，**已探测到真实漂移**）：

```
🔄 bilingual-paper-reader   | upstream=97ec77d vs vendored=6356e27  **DRIFT**
🔄 literature-matrix-builder | upstream=97ec77d vs vendored=6356e27  **DRIFT**
🔄 research-method-selector | upstream=97ec77d vs vendored=6356e27  **DRIFT**
🔄 causal-inference-architect | upstream=97ec77d vs vendored=6356e27  **DRIFT**
🔄 academic-humanizer        | upstream=94b88b2 vs vendored=6356e27  **DRIFT**
```

### 3. JSON 模式（CI 友好）

```bash
bash vendor-freshness-check.sh --probe --json | jq '.[] | select(.drift_status=="upstream_moved")'
```

### 4. 强制离线（即使带 `--probe` 也不联网）

```bash
XTGC_OFFLINE=1 bash vendor-freshness-check.sh --probe
```

---

## 🔧 设计原则（与 R02 方案 E 一致）

| 原则 | 实现 | 为什么 |
|---|---|---|
| **默认离线** | `PROBE=0` 默认；不带 `--probe` 不联网 | 零侵入用户工作流 |
| **失败静默** | curl/git 失败只 INFO，不 WARN | 避免网络抖动时的噪音告警 |
| **可独立运行** | 不 apply 到 check-ready.sh | 维护者逐 PR 控制节奏 |
| **路径自探测** | `XTGC_ROOT` envvar → 同级 → 上跳 1 级 → 上跳 2 级 → fallback SCRIPT_DIR | 在 xtgc-forge-clone/ 或 patches/ 下都能跑 |
| **JSON 可机读** | `--json` 输出结构化数组 | 接 GH Actions / CI |
| **不泄露密钥** | 纯 git ls-remote，零 token | 公开仓库探测无需认证 |

---

## 📋 输出字段（人读 + JSON 共用）

| 字段 | 含义 | 来源 |
|---|---|---|
| `skill` | vendor 子 skill 名 | 硬编码 5 个 |
| `vendored_commit` | xtgc-forge 当前 vendor 的 git commit | 读 VERSION.md |
| `last_verified` | VERSION.md 上次核验日期 | 读 VERSION.md |
| `age_days` | 距 last_verified 的天数 | 系统当前日期 - last_verified |
| `refresh_days` | 建议刷新间隔（核心 30d / 周边 60-90d） | 读 VERSION.md |
| `criticality` | `core` / `optional` | 读 VERSION.md |
| `drift_status` | `upstream_moved` / `upstream_match` / `local_fresh` / `missing_version_md` / `upstream_unfetchable` | 综合判断 |
| `upstream_commit` | 上游最新 commit（probe 模式填充）| `git ls-remote` |
| `fetch_status` | `ok` / `offline` / `network_error` / `repo_not_found` | curl/git 返回值 |

---

## 🔌 与 check-ready.sh 的集成（**可选，未启用**）

如果你想把探测自动接入现有的 `check-ready.sh`，可以手动追加一段（**不推荐**——保持独立 add-on 更安全）：

```bash
# 在 check-ready.sh 的"全部就绪" echo 之前追加：
if [ -f "$SCRIPT_DIR/xtgc-forge-patches/check-ready-probe/vendor-freshness-check.sh" ]; then
    echo ""
    echo "[vendor 上游漂移探测（可选）]"
    bash "$SCRIPT_DIR/xtgc-forge-patches/check-ready-probe/vendor-freshness-check.sh"
fi
```

**为什么默认不集成**：
1. `check-ready.sh` 的核心承诺是"就绪检查"，加漂移探测会**改变语义**
2. 联网是副作用，应保持 opt-in
3. 独立 add-on 更易升级（脚本可独立 PR）

---

## ⚠️ 实测发现的真实漂移（2026-08-26）

| skill | upstream | vendored | 差距 | 风险评估 |
|---|---|---|---|---|
| bilingual-paper-reader | 97ec77d | 6356e27 | Nero1688 mono-repo 已演进 | 低（脚本自写，仅 SKILL.md 漂移）|
| literature-matrix-builder | 97ec77d | 6356e27 | 同上 | 中（CrossRef API 约定可能变）|
| research-method-selector | 97ec77d | 6356e27 | 同上 | 低（方法论稳定）|
| causal-inference-architect | 97ec77d | 6356e27 | 同上 | **高**（识别策略家族会更新）|
| academic-humanizer | 94b88b2 | 6356e27 | jefeerzhang fork 母库演进 | **中-高**（fork 维护成本真实存在）|

**建议**：先把 5 个 VERSION.md 提交（**v0.3.21**），再决定是否针对每个 skill 跟进 sync。**不建议全量 auto-sync**——causal-inference-architect 与 academic-humanizer 需人工 review。

---

## 🛠️ 故障排查

| 现象 | 原因 | 修复 |
|---|---|---|
| `VERSION.md 不存在` | 未 cp 进 vendor/ | 见 `../README.md` 第 2 步 |
| `upstream_unfetchable` | 仓库 404 或改名 | 核对 VERSION.md 中 `upstream_repo` |
| `network_error` | 离线 | 重新联网或用 `XTGC_OFFLINE=1` |
| `command 'git' not found` | Windows 无 git | 装 git for windows |
| 探测超时 | 上游仓库大 | 用 `XTGC_OFFLINE=1` 或超时前 ctrl-c |

—— END ——