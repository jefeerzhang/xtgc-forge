# xtgc-forge vendor 漂移治理 · Patch 集（方案 E MVP）

> **来源**：R02 报告（`autonomous_reports/R2_R02 · xtgc-forge vendor 漂移治理方案头脑风暴.md`）方案 E 的最小可行版落地
> **目标仓库**：`https://github.com/jefeerzhang/xtgc-forge`（本地 clone 在 `xtgc-forge-clone/`）
> **本目录原则**：所有 patch 都**不直接污染** xtgc-forge-clone，由你审过后手动 apply

---

## 📂 目录结构

```
xtgc-forge-patches/
├── README.md                       ← 本文件
├── VERSION-TEMPLATE.md             ← 通用 schema（5 子 skill 复用）
├── vendor-version/                 ← 5 个 vendor 子 skill 的 VERSION.md
│   ├── bilingual-paper-reader-VERSION.md
│   ├── literature-matrix-builder-VERSION.md
│   ├── causal-inference-architect-VERSION.md
│   ├── research-method-selector-VERSION.md
│   └── academic-humanizer-VERSION.md
└── check-ready-probe/
    ├── check-ready.sh.diff         ← 给 check-ready.sh 加 --probe flag 的 patch
    └── README.md                   ← 怎么 apply diff
```

---

## 🚀 Apply 步骤（建议顺序）

### Step 1 — VERSION.md × 5（半天工作量，零风险）

```bash
# 每个 vendor 子目录放一份
cp vendor-version/bilingual-paper-reader-VERSION.md    xtgc-forge-clone/vendor/bilingual-paper-reader/VERSION.md
cp vendor-version/literature-matrix-builder-VERSION.md xtgc-forge-clone/vendor/literature-matrix-builder/VERSION.md
cp vendor-version/causal-inference-architect-VERSION.md xtgc-forge-clone/vendor/causal-inference-architect/VERSION.md
cp vendor-version/research-method-selector-VERSION.md xtgc-forge-clone/vendor/research-method-selector/VERSION.md
cp vendor-version/academic-humanizer-VERSION.md        xtgc-forge-clone/vendor/academic-humanizer/VERSION.md
```

### Step 2 — check-ready.sh --probe patch（半天工作量）

详见 `check-ready-probe/README.md`。**默认不联网**（需显式 `--probe` 才探测上游）。

### Step 3 — 提交 & 发版

```bash
cd xtgc-forge-clone
git add vendor/*/VERSION.md
git diff --staged --check    # 1 个 100 字节检查点（custom hook 可选）
git commit -m "feat(vendor): 给 5 子 skill 各加 VERSION.md + check-ready.sh --probe (v0.3.21)"
```

CHANGELOG 草稿（你润色）：

```markdown
## v0.3.21 (2026-XX-XX)

### Added
- **vendor 漂移可观测性 (R02 方案 E MVP)**
  - 5 个 vendor 子 skill 各加 `VERSION.md`（upstream + vendored_commit + last_checked + local_patches）
  - `check-ready.sh --probe` 新增 flag（默认不联网；探测到上游有更新 → WARN）

### Notes
- 不破坏现有 vendor-first 探测优先级
- 不强制联网；用户选择探测 → 知道有更新 → 选择是否升级
```

---

## ⚠️ 我没做的事（明确边界）

1. **没改任何 xtgc-forge-clone/ 下的文件** —— 100% 在 patches/ 里
2. **没替你 git commit / push** —— 由你审过后执行
3. **没写 vendor_sync.sh** —— R02 方案 E 的第 3 步（工程量 3 天），下次再干
4. **没做 4 维 schema 升级（→ vendored_at + upstream_version 联动）** —— 留待 R04

---

## 📊 产出 vs 风险

| 产出 | 风险 | 验证手段 |
|---|---|---|
| 5 份 VERSION.md | 0（纯文本）| `cat vendor/*/VERSION.md` 可见 |
| check-ready.sh --probe | 低（curl 失败静默） | `bash check-ready.sh --probe` 看 WARN 是否合理 |
| `--probe` 默认不联网 | 0 | 不带 flag 时行为不变 |

—— END —