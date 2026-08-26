# VERSION · vendor/causal-inference-architect

> ⚠️ 本文件由 R02 方案 E MVP 自动生成（2026-08-26）。
> 维护者请在引入/刷新时更新带 🔄 的字段。

## 必填字段

| 字段 | 值 |
|---|---|
| `vendored_name` | `causal-inference-architect` |
| `vendored_path` | `vendor/causal-inference-architect/` |
| `upstream_repo` | `https://github.com/Nero1688/claude-academic-skills` |
| `upstream_branch` | `main` |
| `upstream_skill_path` | `skills/causal-inference-architect/`（待维护者核实精确路径）|
| 🔄 `vendored_commit` | `6356e27` |
| 🔄 `vendored_from` | `unknown`（建议补 `causal-inference-architect@2026-08-13`）|
| `vendored_license` | `MIT` |
| 🔄 `last_verified` | `2026-08-26` |
| `local_patches` | 无 |

## 可选字段

| 字段 | 值 |
|---|---|
| `verify_cmd` | `git -C vendor/causal-inference-architect rev-parse HEAD` |
| `refresh_cadence_days` | `30`（顶刊识别策略演进快；TWFE 偏误文献持续更新）|
| `criticality` | `core`（xtgc-forge Step 4 识别策略书 + Step 3b 攻击矩阵主路径）|

## 维护约定（本 skill 特有）

- SKILL.md description 提到：TWFE / Goodman-Bacon / Callaway & Sant'Anna / Sun & Abraham / Rambachan & Roth —— 都是**快速演进的顶刊方法论**
- ⚠️ 本 skill 是 xtgc-forge 卖点"反黑箱 + Gap 判定"的命脉；**漂移风险最高**
- 上游加新识别策略（如最新 2026 Q3 的 panel-IV 混合）必须合并 → xtgc-forge 的攻击矩阵 + 检验策略会过时

## 给 check-ready.sh --probe 的判定提示

| 探测结果 | 建议 |
|---|---|
| 上游新增识别策略家族 | **高优合并** —— xtgc-forge 卖点会过时 |
| 上游改现有 estimator 的 R 代码包名 | 同步更新 `references/` 里的 R 语法示例 |
| 上游弃用某个 estimator | 检查 xtgc-forge 金样例里是否引用；若是 → 改金样例 |

## xtgc-forge 特定引用追踪

本 skill 的内容被 xtgc-forge 在以下 Step 引用：
- Step 3b：候选主题的"识别可行性"评分
- Step 4：识别策略书（核心交付）
- Step 6（复跑决策）：攻击矩阵的检验项

任何上游更新**必须**复核这三处的对齐。

—— END ——