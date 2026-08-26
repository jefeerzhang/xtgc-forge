# VERSION · vendor/academic-humanizer

> ⚠️ 本文件由 R02 方案 E MVP 自动生成（2026-08-26）。
> ⚠️ 本 skill 是 **jefeerzhang fork**（非 Nero1688），维护责任在主机项目。
> 维护者请在引入/刷新时更新带 🔄 的字段。

## 必填字段

| 字段 | 值 |
|---|---|
| `vendored_name` | `academic-humanizer` |
| `vendored_path` | `vendor/academic-humanizer/` |
| `upstream_repo` | `https://github.com/AIScientists-Dev/academic-humanizer`（fork 之母）|
| `upstream_skill_path` | 仓库根（mono-skill，非 mono-repo）|
| 🔄 `vendored_commit` | `6356e27`（xtgc-forge: feat(vendor): 自带 5 个子 skill, v0.3.15）|
| 🔄 `vendored_from` | `AIScientists-Dev/academic-humanizer@version 0.3.3`（来自 vendored SKILL.md `version` 字段）|
| 🔄 `vendored_skill_version` | `0.3.3`（SKILL.md 头部声明）|
| `vendored_license` | `MIT`（见 `vendor/academic-humanizer/LICENSE` + `NOTICE.md`）|
| 🔄 `last_verified` | `2026-08-26` |
| `local_patches` | 见下方 |

### local_patches（jefeerzhang 相对 fork 之母的偏离）

1. **中文社科特化**（v0.3.15 增量）：
   - 新增 `references/rules-zh.md`（14.4 KB，去 AI 味规则中文特化）
   - 新增 `examples/before-after-zh-academic.md`（10.8 KB，中文学术前后对照）
   - 自动加载：当 CJK token ratio `r ≥ 0.5` 时加载 `rules-zh.md`
2. **方法论引用声明**（v0.3.15 增量）：
   - 在 NOTICE.md 引用 `blader/humanizer`（MIT）+ `koaeraser/ARMS`（MIT）作为方法论上游
   - 这两条**不构成 vendored 代码**，仅声明

## 可选字段

| 字段 | 值 |
|---|---|
| `verify_cmd` | `git -C vendor/academic-humanizer rev-parse HEAD` + 对比 SKILL.md 的 `version` 字段与上游 |
| `refresh_cadence_days` | `30`（jefeerzhang 主动承担 fork 维护；上游更新需主动同步）|
| `criticality` | `core`（xtgc-forge"反黑话"机制唯一实现）|

## ⚠️ fork 维护成本（重要）

本 skill 是 jefeerzhang fork，不是 Nero1688 子 skill。维护责任：

| 风险 | 后果 |
|---|---|
| 上游 AIScientists-Dev 修了 bug | 我们的中文版本没有修复 → 用户踩坑 |
| 上游改了主协议（命令名/输入 schema）| 自动加载 `rules-zh.md` 失败（路径错）|
| 上游换了 license | **必须**同步更新本目录 LICENSE 与 NOTICE.md |

**建议**：在 fork 上游的 GitHub repo 上开 issue / subscribe release，关注前 3 天的 release note。

## 给 check-ready.sh --probe 的判定提示

| 探测结果 | 建议 |
|---|---|
| 上游 version > 0.3.3 | **人工评估**：diff 关键规则文件；中文特化补丁是否冲突 |
| 上游新增 `rules-xxx.md`（非中文）| 看是否值得合并 |
| 上游 license 变更 | **阻塞** —— 必须先合规再 sync |

—— END ——