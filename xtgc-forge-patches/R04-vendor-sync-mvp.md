# R04 · vendor_sync.sh MVP 交付报告

**任务来源**：R02 方案 E 第 3 步（vendor-first 漂移防御工具）  
**完成时间**：2026-08-26  
**状态**：✅ MVP 完成（4 子命令 + apply 留 R05）

---

## 1. 范围裁剪

按 R02 共识：MVP 只做 **list / check / fetch / diff**，**apply（3-way merge）留 R05**。

| 子命令 | 作用 | R04 状态 |
|---|---|---|
| `list` | 列出已注册 vendor 及其上游元数据 | ✅ |
| `check` | 探针：对比 vendored vs upstream commit，标记 DRIFT | ✅ |
| `fetch` | 拉上游 tarball → `.vendor_staging/`（**不污染 vendor/**） | ✅ |
| `diff` | vendored vs staging 递归 diff（纯 stdout） | ✅ |
| `apply` | 3-way merge 把 staging 写回 vendor/ | ⏭️ R05 单独做 |

---

## 2. 交付物清单（xtgc-forge-patches/）

```
xtgc-forge-patches/
├── README.md                                     # 总览
├── R04-vendor-sync-mvp.md                        # 本报告
├── VERSION-TEMPLATE.md                           # VERSION.md 字段模板（新增 upstream_branch）
├── check-ready-probe/                            # R03 探针（保留，R04 check 子命令复用）
├── scripts/
│   └── vendor_sync.sh                            # 主脚本 285 行
└── vendor-version/
    ├── VERSION-TEMPLATE.md                       # 5 字段外加 upstream_branch 字段
    ├── bilingual-paper-reader-VERSION.md         # +upstream_branch=main
    ├── literature-matrix-builder-VERSION.md      # +upstream_branch=main
    ├── causal-inference-architect-VERSION.md     # +upstream_branch=main
    ├── research-method-selector-VERSION.md       # +upstream_branch=main
    └── academic-humanizer-VERSION.md             # +upstream_branch=main
```

---

## 3. 实测结果（5 skill × 4 子命令）

### 3.1 `fetch --all` → 5/5 OK

```
✅ bilingual-paper-reader      → 8 files  (Nero1688 mono-repo 双层嵌套自动上提)
✅ literature-matrix-builder   → 5 files  (双层嵌套自动上提)
✅ causal-inference-architect  → 3 files  (双层嵌套自动上提)
✅ research-method-selector    → 2 files  (双层嵌套自动上提)
✅ academic-humanizer          → 10 files (根提取)
```

**遇到并修复的 3 个 bug**：

| # | Bug | 现象 | 修复 |
|---|---|---|---|
| 1 | `case fetch)` 调用 stub `cmd_fetch_stub` | `--all` 返回 "尚未实现" | case 分支改 `cmd_fetch` |
| 2 | `parse_version_md` 字段错位（verified 当 branch） | URL 拼成 `/refs/heads/2026-08-26` 全部 404 | 返 5 字段 `repo\|path\|commit\|verified\|branch` |
| 3 | Nero1688 mono-repo 嵌套（`skills/<s>/<s>/SKILL.md`） | 提取后找不到 SKILL.md | 自动检测 `$stg/$skill` 子目录并上提 |

### 3.2 `diff --all` → 5/5 输出差异（**全 DRIFT**）

```
✅ bilingual-paper-reader    | vendored=9 (含 VERSION.md)  staging=8
✅ literature-matrix-builder | 差异输出
✅ causal-inference-architect| 差异输出
✅ research-method-selector  | 差异输出
✅ academic-humanizer        | vendored=6  staging=10
```

**关键发现**：5 个 skill 全部 DRIFT——上游已晚 6 天更新（vendored_commit=6356e27 vs upstream=97ec77d / 94b88b2），**正是 R02 提出 vendor-first 防御漂移的根本动机**。

### 3.3 `check` 兼容（R03 probe 复用）

```
🔄 bilingual-paper-reader    | age=0d / refresh=90d | criticality=core | **DRIFT**
🔄 literature-matrix-builder | age=0d / refresh=60d | criticality=core | **DRIFT**
🔄 research-method-selector  | age=0d / refresh=60d | criticality=core | **DRIFT**
🔄 causal-inference-architect| age=0d / refresh=30d | criticality=core | **DRIFT**
🔄 academic-humanizer        | age=0d / refresh=30d | criticality=core | **DRIFT**
```

R04 `check` 子命令直接复用 R03 `check-ready-probe/vendor-freshness-check.sh`，无破坏性改动。

---

## 4. 关键设计点

1. **不污染 vendor/**：fetch 写到 `.vendor_staging/`，与 vendor 平级，路径硬编码不冲突
2. **嵌套子目录自动上提**：Nero1688 等 mono-repo 经常 `skills/<s>/<s>/`，脚本自动识别并 `mv`
3. **branch 默认 main + VERSION.md 可覆盖**：5 个 skill 全是 main，模板已示范 `upstream_branch` 字段
4. **diff 纯 stdout**：绝无副作用，方便人工 review 决定是否 apply
5. **CRLF 安全**：Python 写入前清 LF（Windows 端口令行 file_write 默认 CRLF 会污染 bash 脚本）

---

## 5. R05 待办（apply 子命令 = 3-way merge）

```
scripts/vendor_sync.sh apply <skill>          # 把 staging 写回 vendor/（默认自动备份至 .vendor_backup/<skill>.<ts>/）
scripts/vendor_sync.sh apply --all
scripts/vendor_sync.sh apply <skill> --no-backup  # 显式跳过备份（非默认选项，不推荐）
```

要点：
- 3-way merge：base=vendored, mine=vendored+本地补丁, theirs=staging
- 默认安全备份策略：任何写操作执行前，默认自动将原 vendored 目录完整备份至 `.vendor_backup/<skill>.<timestamp>/`；仅在显式传入 `--no-backup` 时才跳过备份
- 冲突文件 → stdout 列出，由人工决定
- 更新 VERSION.md 的 `vendored_commit` / `vendored_from` / `last_verified`

---

## 6. 用户下一步

1. 打开 `xtgc-forge-patches/R04-vendor-sync-mvp.md`（本报告）
2. 浏览 `scripts/vendor_sync.sh`（285 行）+ 跑 `bash scripts/vendor_sync.sh --help`
3. 决定是否把 `xtgc-forge-patches/` 目录 commit 进 xtgc-forge-clone（或作为独立 patch 包）
4. 批准 R05 apply 子命令开发

---

**作者**：xtgc-forge R02-R04 流水线  
**关联**：R02（vendor-first 决策）/ R03（check 探针）/ R05（apply = 3-way merge）