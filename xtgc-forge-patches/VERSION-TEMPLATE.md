# VERSION.md 模板（vendor 子 skill 通用 schema）

> 每个 v0.3.14+ 的 vendor 子 skill 都应有这份文件。
> 设计原则：**可审计、可比对、可机读**。
> 不引诱维护者填写"上游最新版本号"——只填**入库时的事实快照**，探测由脚本负责。

---

## 必填字段（5）

| 字段 | 含义 | 示例 |
|---|---|---|
| `vendored_name` | 本目录名（即 SKILL.md 的 `name`） | `bilingual-paper-reader` |
| `vendored_path` | 相对仓库根的路径 | `vendor/bilingual-paper-reader/` |
| `upstream_repo` | 上游仓库 URL | `https://github.com/Nero1688/claude-academic-skills` |
| `upstream_skill_path` | 上游仓库内对应路径（若 mono-repo） | `skills/bilingual-paper-reader/` |
| `vendored_commit` | 引入本次快照的本地 commit | `6356e27`（xtgc-forge 本仓库）|
| `vendored_from` | 上游当时的 commit/tag/date（手工记）| `bilingual-paper-reader@2026-08-13` 或上游 commit hash |
| `vendored_license` | 上游协议（须 NOTICE.md 一致）| `MIT` |
| `last_verified` | 上次人工核对的日期（YYYY-MM-DD）| `2026-08-26` |
| `local_patches` | 本仓库对其做的偏离（diff 描述）| 列表，可空 |

## 可选字段（3）

| 字段 | 含义 |
|---|---|
| `verify_cmd` | 一行命令验证 vendored_commit 与 upstream 一致（如 `git -C vendor/<x> rev-parse HEAD` 与 upstream 对比） |
| `refresh_cadence_days` | 推荐刷新周期（学术 skill 默认 90；含 breaking-change 风险者默认 30） |
| `criticality` | `core` / `optional` —— core 必须保持新鲜，optional 可滞后 |

## 维护约定

1. **入库时填**：必填字段全部就位才能合入主分支
2. **每次合入上游更新**：必须更新 `vendored_commit` + `vendored_from` + `last_verified`，并改 CHANGELOG
3. **探测脚本依赖**（R02 方案 E 第 2 步）：`check-ready.sh --probe` 读本文件，与 `upstream_repo` 对比 → 出 WARN
4. **不存敏感信息**：本文件 100% 公开，密钥走环境变量

## 与现有文件的协同

- `NOTICE.md`（根）= 版权方声明（已合规，**不动**）
- `LICENSE`（vendor/）= 协议文本（**不动**）
- `VERSION.md`（本模板）= 入库事实快照（**新增**）
- `ATTRIBUTION.md`（个别 skill）= 设计/方法论致谢（**不动**）

—— END ——