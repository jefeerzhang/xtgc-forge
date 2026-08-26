# <skill-name>-VERSION.md · 模板
<!-- 复制此文件到 vendor/<skill>/VERSION.md，替换尖括号内容。所有字段必填或显式填 "none" -->

| 字段 | 示例值 | 说明 |
|---|---|---|
| `vendored_name` | `bilingual-paper-reader` | vendor 子目录名（与目录名一致） |
| `vendored_path` | `vendor/bilingual-paper-reader/` | vendored 所在路径（相对仓库根） |
| `upstream_repo` | `https://github.com/Nero1688/claude-academic-skills` | 上游仓库 URL |
| `upstream_skill_path` | `skills/bilingual-paper-reader/` | 上游 mono-repo 内子路径（无则填 `.` 表示根） |
| `upstream_branch` | `main` | 上游分支（默认 main，按需填 `dev` / tag 名 / commit SHA） |
| `vendored_commit` | `6356e27` | vendored 当前对应的上游 commit 缩写（7 位） |
| `vendored_from` | `Nero1688/claude-academic-skills@2026-08-26` | vendored 最初从上游何处获得（URL + 日期/commit） |
| `vendored_skill_version` | `0.3.3` 或 `none` | 上游对该 skill 的版本号（无则填 `none`） |
| `vendored_license` | `MIT` | 上游 LICENSE（vendored 必须保留同许可证） |
| `last_verified` | `2026-08-26` | 最后一次人工/vendor_sync.sh check 通过日期 |
| `verify_cmd` | `bash scripts/vendor_sync.sh check <skill>` | 验证漂移的命令 |
| `refresh_cadence_days` | `30` | 建议重新检查上游漂移的天数 |
| `criticality` | `core` / `utility` / `optional` | 该 skill 在 xtgc-forge 中的关键性（影响优先升级） |

<!--
README：
- 本文件由 `vendor_sync.sh` 解析，请勿改字段名（脚本依赖反引号包裹的精确匹配）
- 每次同步上游后，请同时更新 `last_verified`、`vendored_commit`、必要时更新 `vendored_from`
- LICENSE 字段：vendored 必须保留上游 LICENSE 原文（不复制 = 漂移风险）
-->
