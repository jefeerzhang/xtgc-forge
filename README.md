# 选题工坊

> **社科/人文向的"用户文献 → 综述 → 主题 → 假设"流水线工具**。基于你自己准备的高质量文献,提炼可检验的研究主题与研究假设。不调用任何自动文献检索(不抓 WebSearch / arXiv / PubMed / Semantic Scholar)。

## 🎯 你什么时候需要它?

- **硕士/博士生开题**:导师说"自己找方向",你需要从一堆文献里看出能写什么
- **青年学者跨方向**:换了研究领域,文献已读但,不知道怎么找 gap
- **实证经济 / 金融 / 管理论文**:需要从文献综述自然涌现研究问题 + 因果识别策略
- **社科工作论文打磨**:已经有一批文献,想系统化识别"还没被研究过"的角度
- **AI Agent 工具开发方**:你想给最终用户提供"读 PDF → 出选题"的工作流

## ✨ 它会交付什么?

| 阶段 | 产出 | 文件 |
|---|---|---|
| Step 1 | 输入确认 | `Step1-input.md` |
| Step 2a | 文献要点卡 | `Step2a-points.md` |
| Step 2b | 文献矩阵(Excel 友好) | `Step2b-literature-matrix.md` |
| Step 2c | Gap 裁定 | `Step2c-gap-verdicts.md` |
| Step 3 | 候选研究主题 + 选定 | `Step3a-candidate-themes.md` + `Step3b-selected-theme.md` |
| Step 4 | 研究假设 + DAG | `Step4-hypotheses.md` |
| Step 5 | 因果识别策略(可选) | `Step5-identification-strategy.md` |
| Step 6 | 总结 + 后续步骤 | `Step6-summary.md` |

## 🚀 快速开始

```bash
# 安装到 Claude Code 全局
mkdir -p ~/.claude/skills/选题工坊
cp SKILL.md ~/.claude/skills/选题工坊/SKILL.md
cp -r references/ ~/.claude/skills/选题工坊/

# 在 Claude Code 中调用
/选题工坊/跑全部
```

或者**直接给 Claude 说**:"我要用选题工坊,我有一些 PDF 在 X 目录下,主题是 X"。

## 🎬 触发示例

- "用选题工坊帮我做选题,我有 8 篇 PDF 在 Downloads/我的文献,主题是数字化转型对企业创新"
- "/选题工坊/建矩阵"
- "/选题工坊/出gap"
- "/选题工坊/出主题"
- "/选题工坊/出假设"
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

| 工具 | 自动检索 | 接收用户文献 | 中文社科向 | 输出可执行选题 |
|---|:-:|:-:|:-:|:-:|
| **选题工坊**(本工具)| ❌ | ✅ | ✅ | ✅ |
| Diverga | ❌ | 部分 | ❌(教育/HRD)| ✅ |
| open-science-skills | ❌ | ✅ | ❌(英文)| ✅ |
| Nero1688 academic-skills | ❌ | ✅ | ✅ | ❌(分散技能)|
| claude-scholar research-ideation | ❌ | 部分 | ❌ | ✅ |
| Tri-Research | ✅ | ❌ | 部分 | ❌ |
| OpenScholar / 文献综述 Agent | ✅ | ❌ | ❌ | ✅ |

**核心定位**:**不替你检索,只替你整合**——你提供"原料"(文献),它给"菜肴"(选题 + 假设)。

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
│   └── methodology-sources.md            方法论参考来源(参见用)
├── examples/
│   └── 气候风险对企业绿色转型/            完整跑通的 9 个产出文件
├── check-ready.sh                        就绪检查脚本
└── outputs/                              当前运行的中间文件
```

## 🔬 实测案例

参考 `examples/气候风险对企业绿色转型/`:
- 6 篇 PDF → OCR(扫描版)→ 直接读取 → 6 步流水线全跑通
- 主题:**气候风险对企业绿色转型的影响 — 基于 A 股上市公司的实证**
- 9 个产出文件 + 5 个研究假设 + 完整因果识别 + IV 候选

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

方法论参考来源:`references/methodology-sources.md`,列出 JARS / DA-RT / PRISMA / Pearl DAG / VanderWeele / SESOI 等公开学术标准,只标"参见 + URL",不复述条款。

## 🔄 版本

- **v0.1.0**(2026-08-10):初稿。7 步流水线骨架。
- **v0.2.0**:应用 8 个边界拷问决策。砍 Step 6,拆为模块化命令,加 gap 派生规则。
- **v0.2.1**:UX 修复。加"使用前必读"段,Step 1 引导用户上传文献。
- **v0.2.2**:实测驱动修复。Step 2a 改为"Read 直接读,读不出的舍弃"——不做 OCR,降低门槛。

## 🙏 致谢

- 灵感来自 Matt Pocock 的 `grill-me` / `wayfinder`(MIT)
- 复用了 Nero1688 的 4 个子 skill(MIT)
- 方法论参考了 JARS / PRISMA / DA-RT / Pearl DAG / VanderWeele / SESOI 等公开学术标准