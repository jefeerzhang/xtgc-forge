# Notice · Third-Party Software Attribution

本仓库 `选题工坊 (xtgc-forge)` 自 v0.3.14 起内置第三方子 skill,作为「最小可运行集」随仓库发布:
- v0.3.14:4 个 [Nero1688/claude-academic-skills](https://github.com/Nero1688/claude-academic-skills) 子 skill
- v0.3.15:1 个 [jefeerzhang/academic-humanizer-zh](https://github.com/jefeerzhang/academic-humanizer-zh) fork(上游 [AIScientists-Dev/academic-humanizer](https://github.com/AIScientists-Dev/academic-humanizer))
- v0.3.20:2 个 [jnMetaCode/superpowers-zh](https://github.com/jnMetaCode/superpowers-zh) 子 skill

合计 7 个 MIT 子 skill,覆盖文献读取 / 矩阵构建 / 因果识别 / 方法选择 / 中文润色 / 中文 commit 规范 / 中文文档排版。

## 上游版权与协议

- **来源仓库**: https://github.com/Nero1688/claude-academic-skills
- **版权所有**: Copyright 2026 Nero1688
- **协议**: MIT(完整文本见 `vendor/LICENSE`)

上游 35 个 skill 中,**4 个与本 skill 工作流直接相关**的子 skill 被 drop-in 复制到 `vendor/<name>/`,其余 31 个未取。

## 内置子 skill 清单

| 路径 | 用途 | 对应 xtgc-forge 步骤 |
|---|---|---|
| `vendor/bilingual-paper-reader/` | 单篇英文论文双栏对照精读(逐段翻译 + 五色高亮 + 离线 HTML 阅读器 + Markdown 笔记导出) | Step 2a 读 PDF(可选增强) |
| `vendor/literature-matrix-builder/` | PDF → 文献库 + Excel 横向比较矩阵(自动抓 DOI / 查 CrossRef / APA7 / 20 列字段) | Step 2b 建文献矩阵 |
| `vendor/causal-inference-architect/` | 现代 DiD(TWFE 偏误 / Goodman-Bacon / Callaway & Sant'Anna / Sun & Abraham / Rambachan-Roth 诚实区间)、IV、RDD、SCM 的识别策略 + R 语法 + 审稿人攻防表 | Step 5 因果识别(可选增强) |
| `vendor/research-method-selector/` | 量化 / 质化 / 实验 / 混合方法选择顾问(Edmondson & McManus 方法论适配框架),5 条 Q1 过程路线 + 同族 skill 串接链 | Phase 0 / Step 0 方向未定时引路(可选) |

每个子 skill 自带的 `ATTRIBUTION.md`(如有)保留原样,作为上游内部 provenance 记录,详见:
- `vendor/bilingual-paper-reader/ATTRIBUTION.md`
- `vendor/literature-matrix-builder/ATTRIBUTION.md`

## 传递依赖(transitive runtime dependencies)

子 skill 脚本在运行时通过 `pip` 安装以下第三方包(**本仓库不内嵌这些包**,按其各自协议使用):

| 包 | 协议 | 用途 | 出处 |
|---|---|---|---|
| `pypdf` | BSD-3-Clause | 从 PDF 抽取文字层(用于 `pdf_to_paper.py` 与 `litmatrix.py` 的 DOI 抓取) | https://github.com/py-pdf/pypdf |
| `requests` | Apache-2.0 | HTTP 调用 CrossRef REST API(用于 `litmatrix.py` 抓书目) | https://requests.readthedocs.io |
| `openpyxl` | MIT | 生成 Excel 文献矩阵(用于 `litmatrix.py build`) | https://openpyxl.readthedocs.io |

安装一行:

```bash
pip install pypdf requests openpyxl
```

## CrossRef polite pool 礼仪

`vendor/literature-matrix-builder/scripts/litmatrix.py` 调用 CrossRef REST API。
按 CrossRef polite pool 惯例,**建议在使用前设置环境变量**:

```bash
export CROSSREF_MAILTO=you@example.com
```

不设置也能跑,只是不进入 polite pool(响应优先级略低)。

## 内置 academic-humanizer(jefeerzhang fork,v0.3.15 新增)

- **本 fork 仓库**: <https://github.com/jefeerzhang/academic-humanizer-zh>
- **上游仓库(AIScientists-Dev)**: <https://github.com/AIScientists-Dev/academic-humanizer>
- **本仓库内路径**: `vendor/academic-humanizer/`
- **SKILL.md frontmatter `name`**: `academic-humanizer`(无 `-zh` 后缀,匹配 v0.3.14 vendor 命名约定)
- **版权所有**: Copyright 2026 AIScientists-Dev(jefeerzhang fork **未重署版权**,沿用上游版权)
- **协议**: MIT(完整文本见 `vendor/academic-humanizer/LICENSE`)

### Fork 增量(中文增强层)

jefeerzhang 在 AIScientists-Dev 上游之上添加了 C7 中文规则层:

- `vendor/academic-humanizer/references/rules-zh.md`(中文去 AI 味规则,14413 B)
- `vendor/academic-humanizer/examples/before-after-zh-academic.md`(中文学术前后对照,10762 B)
- 自动加载规则:当 CJK token ratio `r ≥ 0.5` 时,humanizer 自动加载 `rules-zh.md`

### 上游之上游的 attribution(完整方法论链)

| 项目 | 协议 | URL | 关系 |
|---|---|---|---|
| `AIScientists-Dev/academic-humanizer` | MIT | <https://github.com/AIScientists-Dev/academic-humanizer> | 本仓库版权方;fork 之母 |
| `blader/humanizer` | MIT | <https://github.com/blader/humanizer> | AIScientists-Dev 上游的核心方法论来源(Layer 1 AI-tell 目录) |
| `koaeraser/ARMS` | MIT | <https://github.com/koaeraser/ARMS> | 去 AI 味检测与重写算法的早期参考(claim↔evidence / 数值精度) |

完整 attribution 链:AIScientists-Dev(版权方) → jefeerzhang(增量贡献方) → blader/humanizer + koaeraser/ARMS(方法论上游)。

### 传递依赖

**无**。academic-humanizer 是纯 prompt/contract skill,无 Python 脚本、无 pip 依赖、无 API key。`allowed-tools: [Read, Write, Edit, Grep, Glob, AskUserQuestion]`。

> 注意:本节声明 blader/humanizer 与 koaeraser/ARMS 为**方法论引用**,非 vendored 代码,因此其后续协议变更不直接约束本仓库,但本文档保留 attribution 以尊重原作者贡献。

## 内置 superpowers-zh 子 skill(jnMetaCode 上游,v0.3.20 新增)

- **来源仓库**: <https://github.com/jnMetaCode/superpowers-zh>
- **本仓库内路径**: `vendor/chinese-commit-conventions/`、`vendor/chinese-documentation/`
- **版权所有**: Copyright 2026 jnMetaCode
- **协议**: MIT(完整文本见各子目录 `LICENSE`)
- **许可证分发**:源仓库 `LICENSE` 单文件随 2 个子目录各 drop-in 复制一份,与 v0.3.15 academic-humanizer 模式相同(每一 vendored 子 skill 单独持有一份 MIT 原件,便于合规审计)

### 内置子 skill 清单

| 路径 | 用途 | 调用场景 |
|---|---|---|
| `vendor/chinese-commit-conventions/` | Conventional Commits 中文适配(commitlint / husky / commitizen / conventional-changelog 中文模板) | 用户显式 `/chinese-commit-conventions` 时调用;不自动触发 |
| `vendor/chinese-documentation/` | 中文技术文档排版参考(中英文空格 / 全半角标点 / 术语保留 / 中文文案排版指北) | 用户显式 `/chinese-documentation` 时调用;不自动触发 |

### 上游之上的传递依赖

**无**。两个子 skill 均为单文件 `SKILL.md`(纯 prompt/contract),无 Python 脚本、无 pip 依赖、无 API key。`allowed-tools` 取决于用户在被调时具体传入,默认走标准 Read/Edit 工具链。

### 与本 skill 的关系

`chinese-commit-conventions` 对应**交付前最后一步**(commit message / CHANGELOG 写作时的规范参考),`chinese-documentation` 对应**交付内容的中文排版参考**(报告/文档/注释)。两者均处于 v0.3.7 提到的「去 AI 味」(humanizer)与 v0.3.18 提到的「反黑话」链路更下游的位置——humanizer 处理文风,这两个 skill 处理格式与术语。

## MIT §(c) 合规声明

本 `NOTICE.md` 与以下 LICENSE 文件共同满足所有上游协议的 §(c) 要求:

- `vendor/LICENSE`(Nero1688 MIT,覆盖 `vendor/bilingual-paper-reader/`、`vendor/literature-matrix-builder/`、`vendor/causal-inference-architect/`、`vendor/research-method-selector/` 4 个子 skill)
- `vendor/academic-humanizer/LICENSE`(AIScientists-Dev MIT,覆盖 `vendor/academic-humanizer/`)
- `vendor/chinese-commit-conventions/LICENSE`(jnMetaCode MIT,覆盖 `vendor/chinese-commit-conventions/`)
- `vendor/chinese-documentation/LICENSE`(jnMetaCode MIT,覆盖 `vendor/chinese-documentation/`)

> The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

被声明的 MIT 上游版权方:**Nero1688**(2026) + **AIScientists-Dev**(2026) + **jnMetaCode**(2026);方法论引用:`blader/humanizer`(MIT)、`koaeraser/ARMS`(MIT)。

## 主机项目信息

- **主机项目**: 选题工坊(xtgc-forge)
- **主机协议**: MIT(完整文本见仓库根 `LICENSE`)
- **本 NOTICE 起始版本**: v0.3.14(2026-08-13);v0.3.15 新增 academic-humanizer 段;v0.3.20 新增 2 个 superpowers-zh 子 skill 段