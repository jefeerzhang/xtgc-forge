# Changelog · 选题工坊

> 维护原则:本文件按"为什么改"叙事,而非"改了什么"列表。每版聚焦一段决策主线。
> 详细 commit history 见 `git log`。release tag 由人工打。

## v0.3.0 · 2026-08-10 · 鲁班工坊精雕

**主线**:**从"骨架 + 纪律"升级到"可视化 + 传播资产"**。逻辑骨架未动(v0.2.9 的 5 闸硬暂停保留),
新增:Frontmatter 触发词扩写、SKILL.md 流水线 mermaid 图、README 首屏徽章 + 30 秒看明白、
触发词云、与 6 同行横向对比可视化版。

### Face 1-5 详细

- **Face 1**:`SKILL.md` description 改写为"流程纪律产品",触发词 19 条,顶部 mermaid 流程图,版本 0.2.9 → 0.3.0(`f12c8a2`)
- **Face 2**:`README.md` 首屏 6 个 shields.io 徽章 + ASCII 流程图 + 5 闸硬暂停表格 + 触发词云(`468b7bb`)
- **Face 3**:本 CHANGELOG 文件
- **Face 4**:`assets/diagram/` mermaid 源文件 + README
- **Face 5**:`assets/comparison.md` 与 6 同行横向对比

### 与 v0.2.x 的关系

v0.3.0 **不破坏** v0.2.x 的任何承诺:5 闸硬暂停、check_step.py、独立审查 verdict、topic_scores.json、
"绝不自动检索"安全边界 —— 全部继承并保留。

### 已知边界损耗

- README 徽章用 `shields.io` 静态 URL,不会因仓库事件自动更新(社区常态)
- mermaid 渲染依赖 GitHub 内置或本地 `npx @mermaid-js/mermaid-cli`(见 `assets/diagram/README.md`)
- 跨学科案例仍只有 1 个(经管),第 2 案例(教育/传播/公共管理之一)留待后续

---

## v0.2.x · 历史(简表)

| 版本 | 主线 | 关键产物 | commit |
|---|---|---|---|
| v0.2.9 | 流程纪律封顶 | 5 闸硬暂停 + 反跳过 6 规则 | `1da0bcd` |
| v0.2.8 | 复现性 P1 | `inputs/` 输入端 + `test-prompts.json` 3 用例 + Step1 与气候案例对齐 | `2c59388` |
| v0.2.7 细修 | 安装链路 | 鲁班方案 A:check-ready.sh 去私有路径 + slash 语法合规 | `3293b25` |
| v0.2.7 | 独立审查分离 | 借鉴 RTS v1.5.2:`review.py` + scan / topics verdict | `67a037f` |
| v0.2.6 | 评分系统化 | `topic_scores.json` 6 维 + `init_project.py` 11 模板 | `6698a7f` |
| v0.2.5 | 闸门脚本化 | 3+2 课题选项 + 刚性闸门 GATES 字典 | `02a6613` |
| v0.2.4 | Checkpoint + Grill 双增 | 流程纪律第一层成形 | `e00c99d` |
| v0.2.3 | 用户交互增强 | 三问启动 + AskUserQuestion | `436a3fd` |
| v0.2.2 | 初稿 + 实测驱动 | 7 步流水线骨架 + 不做 OCR 决策 | `33900aa` |

### 历史决策回顾

- **v0.2.2 · 不做 OCR**:学术用户的文献通常本身可读,OCR 工具的 token/安装/配置门槛太高,舍弃比硬挤更有价值。
- **v0.2.2 · 不调自动检索**:明确"用户自备文献为唯一出发点",这是与 Tri-Research / OpenScholar 的根本区分。
- **v0.2.7 · 独立审查分离**:借鉴 research-topic-selection v1.5.2 的强制审查分离,reviewer ≠ producer。
- **v0.2.9 · 5 闸硬暂停**:把"软建议"升级为"硬规则",承认 Skill 没有技术闸门,只能靠文档约束 + 用户守门。

---

## 协议

本项目 MIT 协议。详见 [LICENSE](LICENSE)。

## 致谢

- 灵感:Matt Pocock 的 `grill-me` / `wayfinder`(MIT)
- 依赖:Nero1688 的 4 个子 skill(bilingual-paper-reader / literature-matrix-builder / causal-inference-architect / research-method-selector,MIT)
- 方法论参考:JARS / PRISMA / DA-RT / Pearl DAG / VanderWeele / SESOI 公开学术标准
- 工坊:鲁班 Skill 打磨工坊