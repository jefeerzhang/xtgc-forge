# 选题工坊

> 社科人文向的「文献 → 选题 + 假设」流程纪律产品。
> 不替你检索，不替你思考，但强制你在 5 个关键决策点停下来确认、留痕、出 verdict。
> 反坍缩：先点名最安全题再分层替代，不让 AI 出千篇一律的「X 对 Y 的影响」。
> 贡献类型门：每个候选必答「揭示了什么」，换标签的老题当场回炉。
> 反黑箱：主报告自带「Gap 判定方法」+ 威胁文献清单，缺口怎么判出来的、谁可能抢先，一眼看穿。

![选题工坊工作流](assets/xtgc-workflow.png)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Version: v0.3.17](https://img.shields.io/badge/Version-v0.3.17-blue)](CHANGELOG.md)
[![Checkpoints: 5 hard stops](https://img.shields.io/badge/Checkpoints-5%20hard%20stops-red)](SKILL.md#-强制-5-次-checkpoint硬规则v029)
[![Vendored: 5 sub-skills (MIT)](https://img.shields.io/badge/Vendored-5%20sub--skills%20(MIT)-success)](vendor/)
[![Anti-Collapse: T-Score](https://img.shields.io/badge/Anti--Collapse-T--Score-blue)](references/anti-collapse.md)
[![Anti-Blackbox: Gap 判定方法](https://img.shields.io/badge/Anti--Blackbox-Gap%20判定方法-green)](references/delivery-spec.md#31-附录-c-的gap-判定方法段反黑箱v035)
[![Anti-Jargon: 黑话+断句](https://img.shields.io/badge/Anti--Jargon-黑话%2B断句-orange)](references/delivery-spec.md#33-可读性层术语翻译--断句反黑话v038)
[![De-AI: humanizer vendored](https://img.shields.io/badge/De--AI-humanizer%20vendored-purple)](vendor/academic-humanizer/)
[![Examples: 2 (1 gold · 1 LEGACY)](https://img.shields.io/badge/Examples-2%20(1%20gold%20%C2%B7%201%20LEGACY)-green)](examples/漂绿治理-绿贷与环境税组合/)
[![Runtime: Claude Code](https://img.shields.io/badge/Runtime-Claude%20Code-blueviolet)](check-ready.sh)

## 30 秒看明白

```
📚 你的 5–50 篇 PDF + 一句话模糊领域
        ↓
🛠  6 步流水线(vendor/ 内置 5 个子 skill):
    读 PDF → 建矩阵 → 找 gap → 出主题 → 提假设 → 设计识别
        ↓
🔒 5 个硬闸(每次暂停,你点头才能过)
        ↓
📄 1 份六段式研究计划报告(00_研究计划报告.md)
```

**与同类最大的不同**:**仓库自带** `vendor/` 5 个 MIT 子 skill(bilingual-paper-reader / literature-matrix-builder / causal-inference-architect / research-method-selector / academic-humanizer),`git clone` 即自洽可跑,不依赖任何外部检索或额外安装。

## 你什么时候需要它

```
你有 5-50 篇 PDF + 一句话领域
   ↓
[ 6 步流水线：读 → 矩阵 → gap → 主题 → 假设 → 识别 ]
       └─ vendor/ 内置 5 个子 skill 直接调用，无需外部安装
   ↓
5 个硬闸（流程停顿点，你拍板）↔ 6 道防线（质量机制，机器把关）
   ↓
反坍缩：先点名最安全题（T≥0.80）规避，3 主推覆盖 ≥2 层级、至少 1 个 T≤0.50
   ↓
贡献类型门：每个候选必答「揭示了什么」，答不上或抄标题 = 回炉
   ↓
（可选）对抗压测：选定后魔鬼代言人出「最可能被拒的理由」+ 回应
   ↓
反黑箱：附录 C 自带「Gap 判定方法」，五类规则 + 证据链 + 威胁文献清单
   ↓
反黑话：正文禁黑话（GAP/SESOI/Checkpoint），长句 ≤100 字，报告读得懂
   ↓
去 AI 味：vendor/academic-humanizer/ 调用 + 六大病灶兜底，文风不再像 AI 生成
   ↓
★ 一份六段式研究计划报告（题目 → 为何选题 → 意义 → 假设 → 依据 → 怎么做）
  （+ 过程附录：矩阵 / gap / scores / 审查，默认不必通读）
```

- **硕博开题**：导师说「自己找方向」，5 篇 PDF + 一句话领域就开跑
- **青年学者跨方向**：换了领域，文献已读但找不出 gap
- **实证经管/金融/管理**：需要从综述自然涌现研究问题 + 因果识别
- **AI Agent 工具方**：想给用户「读 PDF → 出选题」的工作流
- **社科人文工作者**：教育学 / 传播学 / 公共管理 / 社会学 / 经管类开题与论文打磨

## 5 闸硬暂停（本 skill 唯一差异化）

| # | 时机 | 用户最小确认 |
|---|---|---|
| **#1** | 文献上传后 | 「文献确认」 |
| **#2** | 矩阵审阅后 | 「矩阵确认」 |
| **#3** | 主题涌现后 | **点名选 1 个候选**（如「选候选 2」） |
| **#4** | 假设提炼后 | 「假设确认」或逐条 |
| **#5** | 交付完成后 | 「交付收工」或下一步 |

> 硬规则：`check_step.py PASS ≠ 用户已确认`。脚本通过后仍须等用户口头/点选确认。
> Agent 不得写「若无异议我将默认选 Q1 / 默认假设通过」。
> 跑全部时至少 5 轮对话闸门（开场信息未齐时另有开场三问）。

[详细 6 步流水线 →](SKILL.md) · [与同行对比 →](assets/comparison.md) · [图示 →](assets/diagram/) · [反坍缩方法论 →](references/anti-collapse.md)

## 触发方式

```
/选题工坊/跑全部            # 跑完整流程
/选题工坊/建矩阵            # 只建矩阵
/选题工坊/出gap             # 只找研究缺口
/选题工坊/出主题            # 只出候选主题
/选题工坊/出假设            # 只提假设
/选题工坊/识别策略          # 因果识别
/选题工坊/选题对抗预演      # 对抗压测
```

自然语言也一样：`用选题工坊帮我做选题`、`帮我开题`、`我的文献已读但不知道怎么选题`、`从 PDF 出研究主题`，英文可用 `research question from literature`、`lit-driven`、`hypothesis from review`。

## 它会交付什么

### 用户主交付（只看这一份）

打开目录先看 `00_交付说明.md`，主交付是 `00_研究计划报告.md`。

- 正文六段（先亮题）：题目 → 为什么 → 意义 → 假设 → 依据 → 怎么做
- 文内附录：矩阵 · 要点 · Gap · 候选与选定 · 识别 · 元信息
- **附录 C 反黑箱**：主报告必须自带「Gap 判定方法」段，含五类判定规则（已知 / 矛盾 / 空白 / 方法局限 / 外推）、证据链要件、至少一条真实推理链示例；另列「威胁文献清单」（谁能杀掉这个题，分级 + 本题靠什么活下来）。缺口不是「感觉出来的」，是推出来的、可审计的（delivery-spec §3.1 / §3.2）
- 详细规格：[`references/delivery-spec.md`](references/delivery-spec.md)
- **金样例**：[`examples/漂绿治理-绿贷与环境税组合/`](examples/漂绿治理-绿贷与环境税组合/)（v0.3.2+ 六段式 + 反黑箱 + 反坍缩，完整可复验）
- **⚠️ 旧样例（LEGACY）**：[`examples/气候风险对企业绿色转型/`](examples/气候风险对企业绿色转型/) 是 **v0.2.x 旧形态**（`Step6-summary.md` 而非 `00_研究计划报告.md`），**不通过 v0.3 闸门**；仅供历史对照，不要当作完成态参照，详见该目录 `LEGACY.md`

Step1–5 / review / scores 是过程审计，默认不必通读。
`check_step --step 6` 会拒绝空壳主报告（字数 / 段落 / 矩阵行 / 占位符 / 缺 Gap 判定方法）。

### 六道防线（0.3.4–0.3.13）

**反坍缩（Step 3a）**：AI 选题不再千篇一律。
1. **模态识别**：生成候选前先点名 2-3 个「谁都会提」的最安全题（T ≥ 0.80），写清为何避免
2. **分层替代**：候选按典型性梯度出，safe（0.55-0.80）/ differentiated（0.35-0.55）/ innovative（<0.35）；3 主推必须覆盖 ≥2 层级且至少 1 个 T ≤ 0.50
3. **闸门校验**：3 主推全落安全层，`check_step --step 3a` FAIL，退回重生成

**反黑箱（Step 6 / 附录 C）**：缺口判定可审计。
- 五类判定规则表 + 证据链要件（文献 X 做了 A → Y 做了 B → 差什么 → 所以是 gap）
- 每条 gap 标证据来源、为什么是 gap、重要性分级
- `check_step --step 6` 强制主报告含「Gap 判定方法」「证据链」

**反黑话（Step 6 · 可读性层）**：报告不再生硬。
- 正文（开头→整合附录前）禁内部黑话：GAP 编号 / Checkpoint / SESOI / t_score / 反坍缩 等须按 delivery-spec §3.3 翻译表改成人话（编号只在附录 C 对照）
- 超长句闸门：正文 >100 字句子 FAIL，目标 ≤60 字

**去 AI 味（Step 6 · 固定润色环节）**：文风不再像 AI 生成。
- v0.3.15+ 内置 `vendor/academic-humanizer/`（jefeerzhang fork，MIT），调用它润色；若 vendor 缺失，退到 `references/deai-checklist.md` 六大病灶自查（套话 / 价值词 / 抽象主语 / 名词化 / 排比 / 元评论）
- 顺序铁律：先翻译（反黑话）→ 后润色（去 AI 味），humanizer 治不了黑话
- 只动文风，数字 / 引文 / 术语一字不改
- deai-checklist 作 humanizer 润色后**自查**（补 humanizer 边缘 case）

**主题对抗压测（Step 3b · 可选增强）**：选定后被审稿人拒之前先自拒。
- 魔鬼代言人按 **9 类坍缩攻击清单**（换情境 / 换术语 / 识别 / 已被占 / 不可证伪 / 范围过宽 / 数据质量 / 不可行 / 贡献类型）逐类攻击选定主题，每类 1 句回应
- 打 **四档生存标签**：存活 / 需收窄 / 需转向 / 坍缩；需转向或坍缩时把降级建议带给用户
- 单代言人 1-2 轮深迭代（实证：深迭代优于多批判者并行，SIGDIAL 2025）
- 用户说「不用」即跳过，不新增硬闸；启用则 `check_step --step 3b` 半强校验（要求生存标签 + 至少 6 类攻击名）

**贡献类型门（Step 3a）+ 威胁文献清单（附录 C）**：防止「换标签的老题」与「被抢先的题」。
- 每个候选必答「这个题揭示了什么？」答不上或与标题雷同，视为工程任务 / 重复验证，回炉
- 附录 C 列「威胁文献清单」：谁能杀掉这个题（致命 / 高 / 中），本题靠什么活下来；不在本批文献内的威胁须诚实标注「需复跑核实」

**三层假设闸（Step 4）**：假设提炼前先过三关，防止「看似严谨实则空泛」的假设。
- 结论优先测试：先写 2-3 句理想结论，写不出具体有力的结论（只会写「X 与 Y 显著相关」）→ 影响不足，回 Step 3b
- 单句金句：核心洞见压成一句话，须能当摘要首句、让人停下读；与贡献类型门「揭示了什么」呼应
- 最险假设 + 1-2 周可测：找出单一最可能杀死选题的假设，给 mini 验证路径，按风险排序而非逻辑顺序
- `check_step --step 4` 强制 `Step4-hypotheses.md` 含「三层假设闸」小节

## 快速开始

```bash
# 1. 装选题工坊本体（含 vendor/ 内置的 4 个 Nero1688 子 skill，v0.3.14 起无需额外 clone）
git clone --depth 1 https://github.com/jefeerzhang/xtgc-forge.git
cd xtgc-forge
mkdir -p ~/.claude/skills/选题工坊
cp SKILL.md ~/.claude/skills/选题工坊/SKILL.md
cp -r references/ scripts/ vendor/ ~/.claude/skills/选题工坊/

# 2. 装 vendored 脚本的 Python 依赖（仅在调用 scripts/*.py 时需要；纯 prose 流程可跳过）
pip install pypdf requests openpyxl

# 3. 就绪检查（可选传 PDF 目录做完整检查）
bash check-ready.sh

# 4. 在 Claude Code 中调用
#    输入 /选题工坊，然后对 Claude 说：跑全部
```

或者直接对 Claude 说：「我要用选题工坊，我有一些 PDF 在 X 目录下，主题是 X」。

> 高级用户覆盖口：若你已经在 `$HOME/.claude/skills/<name>/` 装过 Nero1688 上游同名子 skill，
> `check-ready.sh` 会优先探测仓库内 `vendor/<name>/`，未命中才退回外部。
> 想强制走外部，可设 `export CLAUDE_SKILLS_DIR=/your/path`。

> 调用 `vendor/literature-matrix-builder/scripts/litmatrix.py` 走 CrossRef 时建议设置 polite pool：
> `export CROSSREF_MAILTO=you@example.com`（不设置也能跑，响应优先级略低）。

## 输入要求

```yaml
📥 文献清单: "5-50 篇 PDF(可读)/ 引用列表"
📝 模糊领域: "1-2 句话描述关注的研究领域/现象"
⚙️ 方法偏好(可选): "DID/IV/RDD/实验/质性/混合"

可选附加:
  - 目标期刊:AER/经济研究/管理世界...
  - 数据可得性:CSMAR/WIND/CHARLS...
  - 时长约束:硕论/博士开题/期刊
```

**最小输入**：5 篇可读 PDF + 1 句话模糊领域。
**理想输入**：8-15 篇混合（2-3 综述 + 5-12 实证）+ 清晰方法偏好 + 目标期刊。

## 与同类有什么不同

| 工具 | 自动检索 | 接收用户文献 | 中文社科向 | 输出可执行选题 | 反坍缩（T-Score） | 反黑箱（Gap 判定进报告） |
|---|:-:|:-:|:-:|:-:|:-:|:-:|
| **选题工坊**（本工具） | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Diverga | ❌ | 部分 | ❌（教育/HRD） | ✅ | ✅ | ❌ |
| claude-scholar research-ideation | ❌ | 部分 | ❌（英文） | ✅ | ❌ | ❌ |
| open-science-skills | ❌ | ✅ | ❌（英文） | ✅ | ❌ | ❌ |
| Nero1688 academic-skills | ❌ | ✅ | ✅ | ❌（分散技能） | ❌ | ❌ |
| Tri-Research | ✅ | ❌ | 部分 | ❌ | ❌ | ❌ |
| OpenScholar / 文献综述 Agent | ✅ | ❌ | ❌ | ✅ | ❌ | ❌ |

**核心定位**：不替你检索，只替你整合。你提供原料（文献），它给菜肴（选题 + 假设），过程和防坍缩都透明可审计。

## 安全边界

**绝对不做**：
- ❌ 不调用任何自动文献检索（WebSearch / arXiv / PubMed / Semantic Scholar / Sci-Hub）
- ❌ 不复制任何受版权保护的 skill 代码或方法论条款原文
- ❌ 不 OCR（扫描版 PDF 直接舍弃 + 提醒，不做预 OCR 处理）
- ❌ 不替你做实证跑回归（只给识别策略 + IV 建议）

**会做**：
- ✅ 基于你上传的 PDF 直接读取
- ✅ 基于公开学术标准（PRISMA / JARS / Pearl DAG / VanderWeele 反事实 / SESOI）的方法论参考
- ✅ 用通用语言描述方法论，不复制具体条款
- ✅ 中文输出（全文 + 中文触发词 + 中文示例）

## 文件结构

```
选题工坊/
├── SKILL.md                              主入口
├── README.md                              本文件
├── LICENSE                                MIT
├── references/
│   ├── delivery-spec.md                 主交付规格（§3.1/3.2 反黑箱、§3.3 反黑话、§5 复跑契约）
│   ├── anti-collapse.md                 反坍缩方法论（T-Score 分层，借鉴 Diverga MIT 的 VS）
│   ├── deai-checklist.md                去 AI 味自查清单（Step 6 润色兜底）
│   └── methodology-sources.md           方法论参考来源（参见用）
├── examples/
│   ├── 漂绿治理-绿贷与环境税组合/        ★ 金样例（主报告完成态 + Gap 判定方法示例）
│   └── 气候风险对企业绿色转型/           旧过程样例（见 LEGACY.md，已升级反坍缩格式）
├── check-ready.sh                        就绪检查脚本
├── test-prompts.json                     固化测试样例（3 条）
├── scripts/                              init/check/review 闸门脚本
└── outputs/                              本地运行的中间文件（.gitignore 排除，不入库）
```

## 实测案例

参考 `examples/气候风险对企业绿色转型/`：
- 6 篇 PDF → 文字层直接读取（扫描版舍弃）→ 6 步流水线全跑通
- 反坍缩候选（v0.3.4+）：**气候风险背景下数字化转型对企业避税的影响（T 0.48 / 差异化）** 等 3 主推 + 2 备选，模态题先点名规避
- 9 个产出文件 + 5 个研究假设 + 完整因果识别 + IV 候选

> 注：旧版主推 2 标题「气候风险对企业绿色转型的影响——基于 A 股上市公司」接近模态模板，已标注 T 0.62 / safe 留作反坍缩闸门价值的对照，不建议照抄该选题写法。

## 依赖

**已内置子 skill**（v0.3.14+ 随仓库 `vendor/` 发布，MIT；详见各子目录 `LICENSE` 与 `NOTICE.md`）：

| 路径 | 上游 | 对应 xtgc-forge 步骤 |
|---|---|---|
| `vendor/bilingual-paper-reader/` | Nero1688 MIT | Step 2a 读 PDF（可选增强） |
| `vendor/literature-matrix-builder/` | Nero1688 MIT | Step 2b 建文献矩阵 |
| `vendor/causal-inference-architect/` | Nero1688 MIT | Step 5 因果识别（可选增强） |
| `vendor/research-method-selector/` | Nero1688 MIT | Phase 0 方向未定时引路（可选） |
| `vendor/academic-humanizer/` | jefeerzhang fork, AIScientists-Dev MIT | Step 6 去 AI 味润色 |

> 上游 [Nero1688/claude-academic-skills](https://github.com/Nero1688/claude-academic-skills) 共 35 个 skill，本仓库仅取与工作流直接相关的 4 个。
> [jefeerzhang/academic-humanizer-zh](https://github.com/jefeerzhang/academic-humanizer-zh) 是 [AIScientists-Dev/academic-humanizer](https://github.com/AIScientists-Dev/academic-humanizer) 的中文增强 fork（添加 `references/rules-zh.md` C7 中文规则层），本仓库取 fork 版。
> 调用 vendored Python 脚本时需 `pip install pypdf requests openpyxl`（纯 prose 流程不依赖）。

**不依赖**（避免协议冲突）：
- ❌ open-science-skills（CC BY-NC 4.0 非商用）
- ❌ 任何自动文献检索工具

## 协议

MIT（可商用、可改编）。

方法论参考来源：`references/methodology-sources.md`（JARS / DA-RT / PRISMA / Pearl DAG / VanderWeele / SESOI，只标「参见 + URL」，不复述条款）；反坍缩机制借鉴 [Diverga](https://github.com/HosungYou/Diverga)（MIT）的 Verbalized Sampling 方法，经中文社科实证化改写，详见 `references/anti-collapse.md`。

## 版本

- **v0.3.17**(2026-08-13):**审稿反馈闭环 + 发布通道归档**。对 v0.3.16 跑双轴 `code-review`,收口 4 处遗留 + 归档发布通道。①`process/Step1-input.md:3` 旧路径 `outputs/漂绿与金融市场风险` → `process/`(v0.3.16 §4 字面承诺闭合);②`marketplace.json` description 把「9 类对抗压测」改成「对抗压测·9 类攻击清单·可选增强」,防线口径与 SKILL.md 对齐;③占位符正则从 1 字起步(`<[一-鿿][^>]*>`)收紧为 4 字起步 + 关键词白名单兜底,过滤合法正文 `<文献>`/`<用户>`/`<什么>`/`<中文>` 误报;④`marketplace.json` 字段全合规但 v0.3.16 漏归档,本次显式记入。`--step all` 失败项数与 v0.3.16 持平(4 项 = Step2a/5/review 有意缺省),Step 6 主报告闸仍 PASS。
- **v0.3.16**（2026-08-13）：**金样例可复验性加固**。占位符闸门补漏（新增通用 `<中文>` 占位模式，原枚举 3 个漏掉 init 模板 20+ 个）；清除金样例 3 处 `<用户文献目录>` 占位残留；`check_step.py` 支持 `process/` 子目录回退，金样例过程文件 Step1/2b/2c/3a/3b/4 + topic_scores 全部可复验（`--step all` 失败项 12 → 4，仅缺省 Step2a/5/review）；金样例 README 断链修复（`outputs/漂绿与金融市场风险/` → `process/`）。
- **v0.3.15**（2026-08-13）：**内置 academic-humanizer（jefeerzhang fork）**。把 Step 6 去 AI 味润色从「可选外部依赖」升级为「仓库自带 vendor/ 副本」；`vendor/academic-humanizer/` 镜像 jefeerzhang fork，包含上游 AIScientists-Dev 的英文规则 + fork 增量添加的中文规则层 `references/rules-zh.md` 与 `examples/before-after-zh-academic.md`；LICENSE 放子目录（`vendor/academic-humanizer/LICENSE`，MIT Copyright 2026 AIScientists-Dev）；`NOTICE.md` 新增独立段声明上游 + 上游之上游（`blader/humanizer` / `koaeraser/ARMS`）三方 attribution；`check-ready.sh` 加 vendor probe，头部 `[1/5]→[1/6]`；无 transitive deps（无 Python / 无 pip）；`references/deai-checklist.md` 同步降级为 humanizer 兜底。
- **v0.3.14**（2026-08-13）：**内置 4 个 Nero1688 子 skill**（`vendor/<name>/` drop-in，MIT）。把「可选外部依赖」换成仓库自带副本，首次 `git clone` 即自洽可跑，无需额外 clone Nero1688 上游；`check-ready.sh` 改为 vendor-first 探测，`CLAUDE_SKILLS_DIR` 仍作外置覆盖口；MIT 合规：`vendor/LICENSE` + `NOTICE.md` 双重声明；`.gitignore` 增 `Nero1688/`。SKILL.md 4 处引用、依赖块、致谢、`assets/comparison.md` 第 43 行同步更新；`scripts/check_step.py` 等闸门脚本不改动（原本就不调用 sub-skill）。
- **v0.3.13**（2026-08-13）：**Step 4 三层假设闸（结论 → 金句 → 最险假设）**。假设提炼前先过三关：结论优先测试（先写理想结论，套话式「X 与 Y 相关」= 影响不足）、单句金句（一句话洞见，能当摘要首句）、最险假设 + 1-2 周可测（单一最可能杀死选题的假设 + mini 验证路径）。check_step Step 4 强制含「三层假设闸」；借鉴 Carlini 结论优先测试 + researcher-pack（MIT）RS2/RS3/RS4。
- **v0.3.12**（2026-08-13）：**主题对抗压测升级为 9 类坍缩攻击 + 四档生存标签**。魔鬼代言人按经管语境翻译的 9 类攻击清单（换情境 / 换术语 / 识别 / 已被占 / 不可证伪 / 范围过宽 / 数据质量 / 不可行 / 贡献类型）逐类攻击选定主题并给回应，打 `存活 / 需收窄 / 需转向 / 坍缩` 生存标签；check_step 3b 校验升级；借鉴 zhangjunhuan846-hash 8 类坍缩攻击理念（经管化改写，不复制原文）。
- **v0.3.11**（2026-08-13）：**去 AI 味固定环节**。Step 6 强制润色：已装 `academic-humanizer-zh`（MIT）则调用它，未装按 `references/deai-checklist.md` 六大病灶自查；顺序铁律「先翻译（反黑话）后润色（去 AI 味）」；只动文风，数字 / 引文 / 术语一字不改。
- **v0.3.10**（2026-08-13）：**复跑契约收紧**。附录 F 决策表不再是复跑授权；复跑授权必须由 `00_复跑决策记录.md`（当次原话 + 时间）提供；声明复跑却无记录 / 空壳记录 → `check_step --step 6` FAIL；复跑仍须 interaction-log 5 闸留痕。
- **v0.3.9**（2026-08-13）：**交互留痕（5 闸的证据）**。新增 `interaction-log.md`：每闸确认后追加一行（含用户原话，禁止代填）；`check_step --step 6 / all` 强制 5 闸各有确认，缺任一闸 → FAIL，禁止未交互交付。
- **v0.3.8**（2026-08-13）：**可读性层（反黑话）**。主报告正文禁内部黑话（GAP/Checkpoint/SESOI/t_score 等，按 delivery-spec §3.3 翻译表改成人话）+ 超长句闸门（>100 字 FAIL）；金样例正文 10 处黑话全翻译。可选：装 `academic-humanizer-zh`（MIT）做文风润色，先翻译后润色。
- **v0.3.7**（2026-08-13）：**贡献类型门 + 威胁文献清单**。每个候选必答「揭示了什么」（3a + topic_scores 双校验，禁与标题雷同）；附录 C 强制「威胁文献清单」段（分级 + 本题靠什么活下来 + 诚实标注）；delivery-spec §3.2 + init 模板同步。
- **v0.3.6**（2026-08-13）：**主题对抗压测（可选增强）**。魔鬼代言人对选定主题出 2-3 条「最可能被审稿人拒的理由」+ 回应，写入 Step3b「对抗压测」小节；check_step 3b 半强校验；借鉴 research-companion 7 维压测 + MultiAgent-Research-Ideator 实证（深迭代优于并行批判者）。
- **v0.3.5**（2026-08-13）：**反黑箱交付**。主报告附录 C 强制加「Gap 判定方法」段（五类判定规则 + 证据链要件 + 真实推理链示例）；`check_step --step 6` 校验「Gap 判定方法」+「证据链」；规格见 delivery-spec §3.1。
- **v0.3.4**（2026-08-13）：**反坍缩机制**。Step 3a 强制三阶段（模态识别 → 分层替代 → 闸门校验）；topic_scores.json 加 `t_score` / `tier`；新增 `references/anti-collapse.md`。
- **v0.3.3**（2026-08-11）：**鲁班三刀**。`check_step` Step6 加固；金样例 `examples/漂绿治理-绿贷与环境税组合/`；delivery-spec 外置；依赖改可选；Step5 不强制 IV。
- **v0.3.2**（2026-08-11）：**交付纪律全局化**。主报告 = 正文六段 + 文内矩阵 / 要点 / Gap / 候选 / 识别；论述须充分；Step2a 允许文字层抽取（非 OCR）。
- **v0.3.1**（2026-08-11）：**六段式研究计划报告定型**。Step 6 主产品改为 `00_研究计划报告.md`；Step1–5 降为过程附录；先亮题再论证。
- **v0.3.0**（2026-08-10）：**精雕，可视化 + 传播资产**。README 首屏徽章 / 流程图 / 触发词云；新增 CHANGELOG.md / assets/diagram/ / assets/comparison.md。
- **v0.2.9**（2026-08-10）：**强制 5 次 Checkpoint 硬暂停**。禁止代选 / 合并跳过 / 用 check_step 代替用户确认。
- **v0.2.0–v0.2.8**：8 个边界拷问决策、模块化命令、gap 派生规则、实测驱动修复、topic_scores 6 维评分、独立审查分离、P1 复现性等，详见 [CHANGELOG.md](CHANGELOG.md)。

## 致谢

- 灵感来自 Matt Pocock 的 `grill-me` / `wayfinder`（MIT）
- **v0.3.14 起内置 4 个 Nero1688 子 skill**（来自 [Nero1688/claude-academic-skills](https://github.com/Nero1688/claude-academic-skills)，MIT；详见 `vendor/LICENSE` 与 `NOTICE.md`）
- **v0.3.15 起内置 academic-humanizer**（jefeerzhang fork，[GitHub](https://github.com/jefeerzhang/academic-humanizer-zh)；上游 [AIScientists-Dev/academic-humanizer](https://github.com/AIScientists-Dev/academic-humanizer) MIT；详见 `vendor/academic-humanizer/LICENSE` 与 `NOTICE.md`）
- 反坍缩方法借鉴 Diverga 的 Verbalized Sampling（MIT）
- 方法论参考了 JARS / PRISMA / DA-RT / Pearl DAG / VanderWeele / SESOI 等公开学术标准