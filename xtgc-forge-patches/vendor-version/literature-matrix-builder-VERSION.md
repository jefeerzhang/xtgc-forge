# VERSION · vendor/literature-matrix-builder

> ⚠️ 本文件由 R02 方案 E MVP 自动生成（2026-08-26）。
> 维护者请在引入/刷新时更新带 🔄 的字段。

## 必填字段

| 字段 | 值 |
|---|---|
| `vendored_name` | `literature-matrix-builder` |
| `vendored_path` | `vendor/literature-matrix-builder/` |
| `upstream_repo` | `https://github.com/Nero1688/claude-academic-skills` |
| `upstream_branch` | `main` |
| `upstream_skill_path` | `skills/literature-matrix-builder/`（待维护者核实精确路径）|
| 🔄 `vendored_commit` | `6356e27` |
| 🔄 `vendored_from` | `unknown`（建议补 `literature-matrix-builder@2026-08-13`）|
| `vendored_license` | `MIT` |
| 🔄 `last_verified` | `2026-08-26` |
| `local_patches` | 无 |

## 可选字段

| 字段 | 值 |
|---|---|
| `verify_cmd` | `git -C vendor/literature-matrix-builder rev-parse HEAD` |
| `refresh_cadence_days` | `60`（矩阵 schema 可能因 Q1 期刊新规范而变）|
| `criticality` | `core`（xtgc-forge Step 2a 文献要点卡主路径）|

## 维护约定（本 skill 特有）

- ATTRIBUTION.md 声明：**零代码借用**（litmatrix.py 全自写 + 直接 requests 调 CrossRef）
- **CrossRef 风险**：上游若改了 API 调用约定或加 polite-pool 策略，需同步
- 输出 Excel schema 字段（理论视角/方法/IV/DV/中介调节等）若上游变动，xtgc-forge 的 Step 2b 矩阵合并规则可能需同步更新

## 给 check-ready.sh --probe 的判定提示

| 探测结果 | 建议 |
|---|---|
| 上游 Excel 字段定义改了 | 同步更新 `references/litmatrix-schema.md` |
| 上游 CrossRef 调用改了 | 测试本地 CrossRef 抓取仍工作 |
| 上游引入新的依赖（如 habanero）| **不引入** —— 本 skill 哲学就是零外部依赖 |

—— END ——