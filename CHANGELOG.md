# Changelog · 选题工坊

> 维护原则:本文件按"为什么改"叙事,而非"改了什么"列表。每版聚焦一段决策主线。
> 详细 commit history 见 `git log`。release tag 由人工打。

## v0.3.12 · 2026-08-13 · 对抗压测从自由发挥升级为攻击清单

**主线**:把「魔鬼代言人靠自觉压测」升级为「9 类坍缩攻击 + 四档生存标签」的机器可校验质检。

1. **9 类坍缩攻击清单(经管语境)**:换情境 / 换术语 / 识别 / 已被占 / 不可证伪 / 范围过宽 / 数据质量 / 不可行 / 贡献类型。理念借鉴 zhangjunhuan846-hash 的 8 类坍缩攻击(collapse-test),按经管实证语境逐条翻译并补「贡献类型攻击」,见 `references/anti-collapse.md` §7
2. **四档生存标签**:存活 / 需收窄 / 需转向 / 坍缩;需转向或坍缩时把降级建议带给用户,不替代用户拍板
3. **闸门升级**:`check_step --step 3b` 半强校验改为「生存标签 + 至少 6 类攻击名」;旧格式(魔鬼代言 + 最可能被拒 + 回应)兼容放行,未启用对抗不拦
4. **版本号统一**:SKILL.md frontmatter `0.3.12` + 正文标题 v0.3.12(修复历史漂移:标题此前停留在 v0.3.3)

## v0.3.3 · 2026-08-11 · 鲁班三刀落地

**主线**:把「必须充分论述 + 主报告自洽」从愿望变成可强制执行。

1. **闸门**:`check_step.py` Step6 校验有效字数/段落数/附录 A 矩阵≥5 行/禁模板占位;空壳 FAIL;Step5 不强制 IV  
2. **金样例**:`examples/漂绿治理-绿贷与环境税组合/00_研究计划报告.md`;旧气候案例标 `LEGACY.md`  
3. **双轨收敛**:`references/delivery-spec.md` 外置详细规格;SKILL 顶部只留索引;工作目录 `00_交付说明.md` 入口;依赖改可选  

---

## v0.3.2 · 2026-08-11 · 交付纪律全局化

**主线**:把 v0.3.1 的「主报告形态」提升为 skill 全局规格:最终产品定义、材料整合、论述深度、复跑模式、PDF 文字层抽取,全部写进 `SKILL.md` 顶部必读区。

---

## v0.3.1 · 2026-08-11 · 用户主交付定型

**主线**:实测发现「过程文件堆成交付」淹没选题目标。最终产品收束为 **1 份六段式研究计划报告**。

### 六段固定框架(先亮题,再论证)

1. 选的题是什么?
2. 为什么选这个题?
3. 选题的意义是什么?
4. 假设是什么?
5. 为什么能写出这样的假设?
6. 后面应该怎么做?

### 改动面

- `SKILL.md` Step 6 / CP#5 / 启动说明 / frontmatter → v0.3.1
- 主报告顺序:**题目 → 为何 → 意义 → 假设 → 依据 → 怎么做**;要求充分论述
- 主报告须**文内整合**文献矩阵、要点、Gap、候选与识别要点(禁止只丢 Step 路径)
- `check_step.py --step 6` 校验六段标题 + 文献矩阵/Gap 等关键词
- `init_project.py` 生成主报告模板(含附录骨架);Step6-summary 降为过程指针
- `README.md` 交付物表区分主交付 vs 过程附录

### 不破坏

5 闸硬暂停、独立审查、topic_scores、不自动检索 —— 全部保留。

---

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