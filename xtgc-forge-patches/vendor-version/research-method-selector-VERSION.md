# VERSION · vendor/research-method-selector

> ⚠️ 本文件由 R02 方案 E MVP 自动生成（2026-08-26）。
> 维护者请在引入/刷新时更新带 🔄 的字段。

## 必填字段

| 字段 | 值 |
|---|---|
| `vendored_name` | `research-method-selector` |
| `vendored_path` | `vendor/research-method-selector/` |
| `upstream_repo` | `https://github.com/Nero1688/claude-academic-skills` |
| `upstream_branch` | `main` |
| `upstream_skill_path` | `skills/research-method-selector/`（待维护者核实精确路径）|
| 🔄 `vendored_commit` | `6356e27` |
| 🔄 `vendored_from` | `unknown`（建议补 `research-method-selector@2026-08-13`）|
| `vendored_license` | `MIT` |
| 🔄 `last_verified` | `2026-08-26` |
| `local_patches` | 无 |

## 可选字段

| 字段 | 值 |
|---|---|
| `verify_cmd` | `git -C vendor/research-method-selector rev-parse HEAD` |
| `refresh_cadence_days` | `60`（方法论选择框架演进比识别策略慢）|
| `criticality` | `core`（xtgc-forge Step 4 研究过程书主路径之一）|

## 维护约定（本 skill 特有）

- SKILL.md description 提到 Edmondson & McManus (2007) 方法论适配 → 这是**经典理论**，上游不太可能换；但**应用层面**（混合方法新标准、Q1 期刊新接受的研究过程模板）会变
- 内置"小白引导模式"：从兴趣挖掘到代拟题到第一周行动清单 —— 偏 LLM 行为建议，上游可能因模型升级而调整措辞

## 给 check-ready.sh --probe 的判定提示

| 探测结果 | 建议 |
|---|---|
| 上游改方法论决策树（Edmondson/McManus 框架）| 低风险，可自动同步 |
| 上游改触发词清单 | 同步到 xtgc-forge SKILL.md 的 slash 命令解析 |
| 上游新增方法家族（如 2026 新方法学）| 同步到 Step 4 的过程书模板 |

—— END ——