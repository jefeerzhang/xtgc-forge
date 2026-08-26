# VERSION · vendor/bilingual-paper-reader

> ⚠️ 本文件由 R02 方案 E MVP 自动生成（2026-08-26）。
> 维护者请在引入/刷新时更新带 🔄 的字段。

## 必填字段

| 字段 | 值 |
|---|---|
| `vendored_name` | `bilingual-paper-reader` |
| `vendored_path` | `vendor/bilingual-paper-reader/` |
| `upstream_repo` | `https://github.com/Nero1688/claude-academic-skills` |
| `upstream_branch` | `main` |
| `upstream_skill_path` | `skills/bilingual-paper-reader/`（mono-repo，待维护者核实精确路径）|
| 🔄 `vendored_commit` | `6356e27`（xtgc-forge: feat(vendor): 自带 5 个子 skill）|
| 🔄 `vendored_from` | `unknown`（上游无显式 tag；建议补 `bilingual-paper-reader@2026-08-13`）|
| `vendored_license` | `MIT`（见 `vendor/LICENSE` + 仓库根 `NOTICE.md`）|
| 🔄 `last_verified` | `2026-08-26`（本 VERSION.md 创建日；下次核验请更新）|
| `local_patches` | 无（diff vs 上游为空；xtgc-forge 没改 skill 内容） |

## 可选字段

| 字段 | 值 |
|---|---|
| `verify_cmd` | `git -C vendor/bilingual-paper-reader rev-parse HEAD`（仅本地；上游 commit 比对需 `git ls-remote https://github.com/Nero1688/claude-academic-skills`）|
| `refresh_cadence_days` | `90`（纯文本阅读 skill，破坏性变更风险低）|
| `criticality` | `core`（xtgc-forge 用户文献读入主路径之一）|

## 维护约定（本 skill 特有）

- ATTRIBUTION.md 已声明：**零代码借用**（reader.html / pdf_to_paper.py 全自写）；上游只供方法论参考 → 因此本地与上游 SKILL.md 内容可能高度相似但**不要求逐字一致**
- scripts/reader.html 是纯前端离线组件，与 SKILL.md 协议无关，可独立升级

## 给 check-ready.sh --probe 的判定提示

| 探测结果 | 建议 |
|---|---|
| 上游 SKILL.md description 变了 | 看是否与 xtgc-forge 文献读入流程冲突；通常不冲突 |
| 上游新增脚本 | 检查许可证与 NOTICE.md 一致性后并入 |
| 上游删除现有脚本 | **不要自动删** —— xtgc-forge 可能依赖 |

—— END ——