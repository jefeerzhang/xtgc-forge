# 与同行 Skill 横向对比 · 2026-08

> 维护原则:本表只列**直接同行**(从用户文献到选题/假设的端到端 skill)。间接同行
> 列在下方"对照参考"。所有 URL 来自访行时实搜,2026-08 截止。
>
> ⚠️ 本表是**鲁班工坊访行产物**,不是评分。读者自行判断各家差异。

## 直接同行核心维度

| 维度 | **选题工坊(本)** | research-companion | research-gap-finder | meta-research | academic-deep-research |
|---|---|---|---|---|---|
| 自动文献检索 | ❌ 显式拒绝 | ❌ | ✅ | ⚠️ 部分 | ✅ |
| **5 闸硬暂停** | ✅ | ❌ | ❌ | ❌ | 3 |
| **独立审查 verdict** | ✅ 2(scan/topics) | ❌ | ❌ | ❌ | ❌ |
| topic_scores 评分 | ✅ 6 维定量 | ❌ 7 维定性 | ✅ 3 维 | ✅ 3 维 | ❌ |
| 闸门脚本 | ✅ `check_step.py` | ❌ | ❌ | ❌ | ❌ |
| 测试 prompt | ✅ 3+ 用例 | ❌ | ❌ | ❌ | ❌ |
| 中文社科向 | ✅ | ❌ | ❌ | ❌ | ❌ |
| 跨学科案例 | 1(经管) | ❓ | ❓ | ❓ | ❓ |
| 协议 | MIT | MIT | MIT | MIT | 不明 |
| 不依赖私有路径 | ✅ | ✅ | ✅ | ✅ | ❓ |

**缩写**:
- ❌ = 不做/没有
- ✅ = 做/有
- ⚠️ = 部分/混合
- ❓ = 未查证(下一轮回炉)

## 直接同行一句话定位

| Skill | 一句话 |
|---|---|
| **选题工坊**(本) | 社科人文向的"用户文献 → 选题 + 假设"流程纪律产品,5 闸硬暂停 + 独立审查 verdict |
| research-companion | Seed→Diverge→Evaluate→Deepen→Frame→Decide 6 阶段,7 维 idea critique + Carlini conclusion-first test |
| research-gap-finder | 4 类 gap(method/theory/application/interdisciplinary)+ Innovation/Feasibility/Impact 1-5 评分 |
| meta-research | 6 阶段 hypothesis-driven + YAML hypothesis tree + judgment gate |
| academic-deep-research | 两轮研究循环 + 证据等级 + APA 7 引文 + 3 用户检查点 |

## 对照参考(间接同行 / 依赖 / 手艺同行)

| Skill | 类型 | 与本 skill 的关系 |
|---|---|---|
| Nero1688/claude-academic-skills(35 skill) | **依赖(v0.3.14 内置)** | 选 4 个子 skill 置于 `vendor/`(MIT,源自此仓库);其余 31 个未取 |
| K-Dense-AI/claude-scientific-skills | 间接同行 | 50+ skill 矩阵,自动检索;本 skill 立场相反但品牌策略值得学 |
| Imbad0202/academic-research-skills v3.19 | 间接同行 | 13-agent deep research + 12-agent 写作;数字堆叠但**无用户硬闸** |
| Tanue-Hou/research-topic-auditor(中文) | 间接同行 | 中文社科向,但部分功能 planned;无完整案例 |
| bgpopescu.net "4 Skills" lecture | 手艺同行 | 动词链命名 + 系列感;**值得学的命名钩子** |
| kthorn/research-superpower | 间接同行 | PubMed + 筛选 rubric + 引文遍历;**自动检索,立场冲突** |
| daltonhaslam/lit-review-agent | 间接同行 | 16 阶段 PICO + 多源;**主动检索,本 skill 不学** |
| slr-prisma / meta-analysis-skill | 间接同行 | PRISMA 2020 合规;**本 skill 不做 PRISMA(立场不同)** |

## 来源 URL(访行实搜)

| Skill | URL |
|---|---|
| research-companion | <https://github.com/andrehuang/research-companion/blob/main/skills/research-companion/SKILL.md> |
| research-gap-finder | <https://github.com/LengFeng00/research-gap-finder> |
| meta-research | <https://github.com/AmberLJC/meta-research> |
| academic-deep-research | <https://github.com/kesslerio/academic-deep-research-clawhub-skill> |
| Nero1688/claude-academic-skills(依赖) | <https://github.com/Nero1688/claude-academic-skills> |
| K-Dense-AI/claude-scientific-skills | <https://github.com/K-Dense-AI/claude-scientific-skills> |
| Imbad0202/academic-research-skills | <https://github.com/imbad0202/academic-research-skills> |
| Tanue-Hou/research-topic-auditor | <https://github.com/Tanue-Hou/research-topic-auditor> |
| bgpopescu lecture 4 | <https://bgpopescu.net/teaching/agentic/lecture4.html> |
| kthorn/research-superpower | <https://github.com/kthorn/research-superpower> |
| daltonhaslam/lit-review-agent | <https://github.com/daltonhaslam/lit-review-agent> |
| slr-prisma | <https://github.com/keemanxp/slr-prisma> |
| 文献综述 ecosystem 综述(arXiv) | <https://arxiv.org/html/2606.17819> |
| AI Agent × 社科(arXiv) | <https://arxiv.org/html/2602.22401v1> |
| Anthropic 1260 社科 Coding Agent 调查 | <https://www.anthropic.com/research/coding-agents-social-sciences> |

## 维护纪律

- **每次 release 前对照本表**。新增直接同行 → 加一行;新增维度 → 加一列(注意控制列数 ≤10)
- **不复制条款**。所有对比只标 URL + 一句话定位,不引用任何 skill 的具体方法论文本
- **下轮回炉清单**(访行时发现的待持续观察):
  - research-companion 的 7 维定性评分是否会被改成定量(若改,可考虑是否融合)
  - research-gap-finder 的 3 档模式(QS/Standard/Comprehensive)是否值得学
  - bgpopescu "4 Skills" 系列感是否扩到 8 skill
  - AI Agent × 社科 arXiv 后续是否更新"delegation boundary framework"

## 与同行相比最该打穿的 3 件事

1. **"5 闸硬暂停"做成可视化 + 可被截图** — 同行无
2. **"流程纪律作为产品"明确命名** — 同行命名都偏功能(读文献 / 找 gap / 出假设)
3. **topic_scores.json + 独立审查 verdict 的机器可读产物** — 同行无;可被其他 skill 消费