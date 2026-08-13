# 选题工坊

> **社科人文向的「文献 → 选题 + 假设」流程纪律产品**。
> 不替你检索,不替你思考,但强制你在 5 个关键决策点停下来确认、留痕、出 verdict;
> **反坍缩**:先点名最安全题再分层替代,不让 AI 出千篇一律的「X 对 Y 的影响」;
> **反黑箱**:主报告自带「Gap 判定方法」,缺口怎么判出来的,一眼看穿。

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Checkpoints: 5 hard stops](https://img.shields.io/badge/Checkpoints-5%20hard%20stops-red)](SKILL.md#-强制-5-次-checkpoint硬规则v029)
[![Anti-Collapse: T-Score](https://img.shields.io/badge/Anti--Collapse-T--Score-blue)](references/anti-collapse.md)
[![Anti-Blackbox: Gap 判定方法](https://img.shields.io/badge/Anti--Blackbox-Gap%20判定方法-green)](references/delivery-spec.md#31-附录-c-的gap-判定方法段反黑箱v035)
[![Examples: 2](https://img.shields.io/badge/Examples-2%20(1%20gold)-green)](examples/漂绿治理-绿贷与环境税组合/)
[![Runtime: Claude Code](https://img.shields.io/badge/Runtime-Claude%20Code-blueviolet)](check-ready.sh)

## 🎯 你什么时候需要它?(30 秒看明白)

```
你有 5-50 篇 PDF + 一句话领域
   ↓
[ 6 步流水线:读 → 矩阵 → gap → 主题 → 假设 → 识别 ]
   ↓
5 个 🛑 硬闸(必须用户点名确认,Agent 不得代选)
   ↓
反坍缩:先点名最安全题(T≥0.80)规避,3 主推覆盖 ≥2 层级、至少 1 个 T≤0.50
   ↓
反黑箱:附录 C 自带「Gap 判定方法」— 五类规则 + 证据链,缺口怎么来的可审计
   ↓
★ 一份六段式研究计划报告(题目→为何选题→意义→假设→依据→怎么做)
  (+ 过程附录:矩阵/gap/scores/审查,默认不必通读)
```

- **硕博开题** — 导师说"自己找方向",5 篇 PDF + 一句话领域就开跑
- **青年学者跨方向** — 换了领域,文献已读但找不出 gap
- **实证经管/金融/管理** — 需要从综述自然涌现研究问题 + 因果识别
- **AI Agent 工具方** — 想给用户"读 PDF → 出选题"的工作流
- **社科人文工作者** — 教育学 / 传播学 / 公共管理 / 社会学 / 经管类开题与论文打磨

## ⚡ 5 闸硬暂停(本 skill 唯一差异化)

| # | 时机 | 用户最小确认 |
|---|---|---|
| **#1** | 文献上传后 | 「文献确认」 |
| **#2** | 矩阵审阅后 | 「矩阵确认」 |
| **#3** | 主题涌现后 | **点名选 1 个候选**(如「选候选 2」)|
| **#4** | 假设提炼后 | 「假设确认」或逐条 |
| **#5** | 交付完成后 | 「交付收工」或下一步 |

> 硬规则:`check_step.py PASS ≠ 用户已确认`。脚本通过后仍须等用户口头/点选确认。
> Agent 不得写「若无异议我将默认选 Q1 / 默认假设通过」。

[详细 6 步流水线 →](SKILL.md) · [与同行对比 →](assets/comparison.md) · [图示 →](assets/diagram/) · [反坍缩方法论 →](references/anti-collapse.md)

## 🎬 触发示例

`/选题工坊/跑全部` · "用选题工坊帮我做选题" · "帮我开题" · "我的文献已读但不知道怎么选题" · "从 PDF 出研究主题" · "出 gap" · "出假设" · "出主题" · "建矩阵" · "识别策略" · "选题对抗预演" · "research question from literature" · "lit-driven" · "hypothesis from review"

## ✨ 它会交付什么?

### ★ 用户主交付(只看这一份)

**★ 用户只读一份**: `00_研究计划报告.md`  
（打开目录先看 `00_交付说明.md`）

- 正文六段（先亮题）: 题目 → 为什么 → 意义 → 假设 → 依据 → 怎么做
- 文内附录: 矩阵 · 要点 · Gap · 候选与选定 · 识别 · 元信息
- **附录 C 反黑箱**: 主报告必须自带「Gap 判定方法」段 — 五类判定规则(已知/矛盾/空白/方法局限/外推)+ 证据链要件 + 至少一条真实推理链示例。缺口不是"感觉出来的",是推出来的、可审计的(delivery-spec §3.1)
- 详细规格: [`references/delivery-spec.md`](references/delivery-spec.md)
- **金样例**: [`examples/漂绿治理-绿贷与环境税组合/`](examples/漂绿治理-绿贷与环境税组合/)

Step1–5 / review / scores = **过程审计**，默认不必通读。
`check_step --step 6` 会拒绝空壳主报告(字数/段落/矩阵行/占位符/缺 Gap 判定方法)。

### 🛡 三道新防线(0.3.4 / 0.3.5 / 0.3.6)

**反坍缩(Step 3a)** — AI 选题不再千篇一律:
1. **模态识别**: 生成候选前先点名 2-3 个"谁都会提"的最安全题(T ≥ 0.80),写清为何避免
2. **分层替代**: 候选按典型性梯度出 — safe(0.55-0.80)/ differentiated(0.35-0.55)/ innovative(<0.35);3 主推必须覆盖 ≥2 层级且至少 1 个 T ≤ 0.50
3. **闸门校验**: 3 主推全落安全层 → `check_step --step 3a` FAIL,退回重生成

**反黑箱(Step 6 / 附录 C)** — 缺口判定可审计:
- 五类判定规则表 + 证据链要件(文献 X 做了 A → Y 做了 B → 差什么 → 所以是 gap)
- 每条 gap 标证据来源、为什么是 gap、重要性分级
- `check_step --step 6` 强制主报告含「Gap 判定方法」「证据链」

**主题对抗压测(Step 3b · 可选增强)** — 选定后被审稿人拒之前先自拒:
- 魔鬼代言人对选定主题出 2-3 条「最可能被审稿人拒的理由」+ 1 句回应(rebuttal)
- 单代言人 1-2 轮深迭代(实证:深迭代优于多批判者并行,SIGDIAL 2025)
- 用户说「不用」即跳过,不新增硬闸;启用则 `check_step --step 3b` 半强校验

## 🚀 快速开始

```bash
# 1. 装选题工坊本体
git clone --depth 1 https://github.com/jefeerzhang/xtgc-forge.git
cd xtgc-forge
mkdir -p ~/.claude/skills/选题工坊
cp SKILL.md ~/.claude/skills/选题工坊/SKILL.md
cp -r references/ scripts/ ~/.claude/skills/选题工坊/

# 2. 装依赖子 skill(可选,不装则走本 skill 自写路径)
git clone --depth 1 https://github.com/Nero1688/claude-academic-skills.git /tmp/cas
for s in bilingual-paper-reader literature-matrix-builder causal-inference-architect research-method-selector; do
  cp -r "/tmp/cas/skills/$s" ~/.claude/skills/
done

# 3. 就绪检查(可选传 PDF 目录做完整检查)
bash check-ready.sh

# 4. 在 Claude Code 中调用
#    输入 /选题工坊,然后对 Claude 说:跑全部
```

或者**直接给 Claude 说**:"我要用选题工坊,我有一些 PDF 在 X 目录下,主题是 X"。

## 🎬 触发示例

- "/选题工坊" + "跑全部,我有 8 篇 PDF 在 Downloads/我的文献,主题是数字化转型对企业创新"
- "/选题工坊" + "建矩阵"
- "/选题工坊" + "出gap"
- "/选题工坊" + "出主题"
- "/选题工坊" + "出假设"
- "我从 PDF 文献里看研究主题"

## 📋 输入要求

```yaml
📥 文献清单: "5-50 篇 PDF(可读)/ 引用列表"
📝 模糊领域: "1-2 句话描述关注的研究领域/现象"
⚙️ 方法偏好(可选): "DID/IV/RDD/实验/质性/混合"

可选附加:
  - 目标期刊:AER/经济研究/管理世界...
  - 数据可得性:CSMAR/WIND/CHARLS...
  - 时长约束:硕论/博士开题/期刊
```

**最小输入**:5 篇可读 PDF + 1 句话模糊领域。
**理想输入**:8-15 篇混合(2-3 综述 + 5-12 实证)+ 清晰方法偏好 + 目标期刊。

## 🛑 与同类有什么不同?

| 工具 | 自动检索 | 接收用户文献 | 中文社科向 | 输出可执行选题 | 反坍缩(T-Score) | 反黑箱(Gap 判定进报告) |
|---|:-:|:-:|:-:|:-:|:-:|:-:|
| **选题工坊**(本工具)| ❌ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Diverga | ❌ | 部分 | ❌(教育/HRD)| ✅ | ✅ | ❌ |
| claude-scholar research-ideation | ❌ | 部分 | ❌(英文)| ✅ | ❌ | ❌ |
| open-science-skills | ❌ | ✅ | ❌(英文)| ✅ | ❌ | ❌ |
| Nero1688 academic-skills | ❌ | ✅ | ✅ | ❌(分散技能)| ❌ | ❌ |
| Tri-Research | ✅ | ❌ | 部分 | ❌ | ❌ | ❌ |
| OpenScholar / 文献综述 Agent | ✅ | ❌ | ❌ | ✅ | ❌ | ❌ |

**核心定位**:**不替你检索,只替你整合**——你提供"原料"(文献),它给"菜肴"(选题 + 假设),且**过程和防坍缩都透明可审计**。

## 🛑 强制 5 次用户确认(跑全部)

跑全部时 Agent **必须**在下列 5 处停下来等你回话,不得自行跳过:

1. **文献确认**(Step1 后) — 你说「确认」
2. **矩阵审阅**(Step2b 后) — 你说「矩阵 OK」
3. **主题选择**(Step3a 后) — 你**点名**选 1 个候选(反坍缩已先点名规避模态题)
4. **假设确认**(Step4 后) — 你说「假设通过」
5. **最终交付**(Step6 后) — 你说「收工」或下一步计划

`check_step.py` 通过 ≠ 你已确认。最少 **5 轮**对话闸门(+ 开场三问若信息未齐)。

## 🔒 安全边界

**绝对不做**:
- ❌ 不调用任何自动文献检索(WebSearch / arXiv / PubMed / Semantic Scholar / Sci-Hub)
- ❌ 不复制任何受版权保护的 skill 代码或方法论条款原文
- ❌ 不 OCR(扫描版 PDF 直接舍弃 + 提醒,不做预 OCR 处理)
- ❌ 不替你做实证跑回归(只给识别策略 + IV 建议)

**会做**:
- ✅ 基于你上传的 PDF 直接读取
- ✅ 基于公开学术标准(PRISMA / JARS / Pearl DAG / VanderWeele 反事实 / SESOI)的方法论参考
- ✅ 用通用语言描述方法论,不复制具体条款
- ✅ 中文输出(全文 + 中文触发词 + 中文示例)

## 🗂 文件结构

```
选题工坊/
├── SKILL.md                              主入口
├── README.md                              本文件
├── LICENSE                                MIT
├── references/
│   ├── delivery-spec.md                 主交付规格(含 §3.1 Gap 判定方法硬要求)
│   ├── anti-collapse.md                 反坍缩方法论(T-Score 分层,借鉴 Diverga MIT 的 VS)
│   └── methodology-sources.md           方法论参考来源(参见用)
├── examples/
│   ├── 漂绿治理-绿贷与环境税组合/        ★ 金样例(主报告完成态 + Gap 判定方法示例)
│   └── 气候风险对企业绿色转型/           旧过程样例(见 LEGACY.md,已升级反坍缩格式)
├── check-ready.sh                        就绪检查脚本
├── test-prompts.json                     固化测试样例(3 条)
├── scripts/                              init/check/review 闸门脚本
└── outputs/                              当前运行的中间文件
```

## 🔬 实测案例

参考 `examples/气候风险对企业绿色转型/`:
- 6 篇 PDF → 文字层直接读取(扫描版舍弃)→ 6 步流水线全跑通
- 反坍缩候选(v0.3.4+):**气候风险背景下数字化转型对企业避税的影响(T 0.48/差异化)** 等 3 主推 + 2 备选,模态题先点名规避
- 9 个产出文件 + 5 个研究假设 + 完整因果识别 + IV 候选

> 注:旧版主推 2 标题「气候风险对企业绿色转型的影响——基于 A 股上市公司」接近模态模板,已标注 T 0.62/safe 留作反坍缩闸门价值的对照,不建议照抄该选题写法。

## 🤝 依赖

**主依赖**(均 MIT,来自 [Nero1688/claude-academic-skills](https://github.com/Nero1688/claude-academic-skills)):
- `bilingual-paper-reader` — Step 2a 读 PDF(可选)
- `literature-matrix-builder` — Step 2b 建矩阵
- `causal-inference-architect` — Step 5 因果识别

**不依赖**(避免协议冲突):
- ❌ open-science-skills(CC BY-NC 4.0 非商用)
- ❌ 任何自动文献检索工具

## 📜 协议

MIT(可商用、可改编)。

方法论参考来源:`references/methodology-sources.md`(JARS / DA-RT / PRISMA / Pearl DAG / VanderWeele / SESOI,只标"参见 + URL",不复述条款);反坍缩机制借鉴 [Diverga](https://github.com/HosungYou/Diverga)(MIT)的 Verbalized Sampling 方法,经中文社科实证化改写,详见 `references/anti-collapse.md`。

## 🔄 版本

- **v0.3.6**(2026-08-13):**主题对抗压测(可选增强)**。魔鬼代言人对选定主题出 2-3 条「最可能被审稿人拒的理由」+ 回应,写入 Step3b「对抗压测」小节;check_step 3b 半强校验;借鉴 research-companion 7 维压测 + MultiAgent-Research-Ideator 实证(深迭代优于并行批判者)。
- **v0.3.5**(2026-08-13):**反黑箱交付**。主报告附录 C 强制加「Gap 判定方法」段(五类判定规则 + 证据链要件 + 真实推理链示例);`check_step --step 6` 校验「Gap 判定方法」+「证据链」;规格见 delivery-spec §3.1。
- **v0.3.4**(2026-08-13):**反坍缩机制**。Step 3a 强制三阶段(模态识别 → 分层替代 → 闸门校验);topic_scores.json 加 `t_score`/`tier`;新增 `references/anti-collapse.md`。
- **v0.3.3**(2026-08-11):**鲁班三刀**。`check_step` Step6 加固;金样例 `examples/漂绿治理-绿贷与环境税组合/`;delivery-spec 外置;依赖改可选;Step5 不强制 IV。
- **v0.3.2**(2026-08-11):**交付纪律全局化**。主报告=正文六段+文内矩阵/要点/Gap/候选/识别;论述须充分;Step2a 允许文字层抽取(非 OCR)。
- **v0.3.1**(2026-08-11):**六段式研究计划报告定型**。Step 6 主产品改为 `00_研究计划报告.md`;Step1–5 降为过程附录;先亮题再论证。
- **v0.3.0**(2026-08-10):**精雕 — 可视化 + 传播资产**。README 首屏徽章/流程图/触发词云;新增 CHANGELOG.md / assets/diagram/ / assets/comparison.md。
- **v0.2.9**(2026-08-10):**强制 5 次 Checkpoint 硬暂停**。禁止代选/合并跳过/用 check_step 代替用户确认。
- **v0.2.0–v0.2.8**:8 个边界拷问决策、模块化命令、gap 派生规则、实测驱动修复、topic_scores 6 维评分、独立审查分离、P1 复现性等,详见 [CHANGELOG.md](CHANGELOG.md)。

## 🙏 致谢

- 灵感来自 Matt Pocock 的 `grill-me` / `wayfinder`(MIT)
- 复用了 Nero1688 的 4 个子 skill(MIT)
- 反坍缩方法借鉴 Diverga 的 Verbalized Sampling(MIT)
- 方法论参考了 JARS / PRISMA / DA-RT / Pearl DAG / VanderWeele / SESOI 等公开学术标准
