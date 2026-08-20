# Changelog · 选题工坊

> 维护原则:本文件按"为什么改"叙事,而非"改了什么"列表。每版聚焦一段决策主线。
> 详细 commit history 见 `git log`。release tag 由人工打。

## v0.3.17 · 2026-08-13 · 审稿反馈闭环 + 发布通道归档

**主线**:对 v0.3.16 改动跑了一次双轴 code-review(`code-review` skill,Standards + Spec 并行子代理),收口 4 处遗留 + 归档发布通道。本版不是新功能,是 v0.3.16 的边角收口与对外发布准备。

1. **断链修复字面闭合(A1)**:v0.3.16 §4 承诺「金样例 README 引用的 `outputs/漂绿与金融市场风险/` → 真实存在的 `process/`」,改了 README 与主报告,但 `process/Step1-input.md:3` 仍写「工作目录 `outputs/漂绿与金融市场风险`」,字面承诺未完全闭合。本次把该行改成「复盘归位 · 工作目录 `process/`」并加注释说明 v0.3.16 起过程文件统一进 process/、根目录仅留主交付;`check_step --step 1` 仍 PASS,`--step all` 失败项数与 v0.3.16 持平(4 项,均为有意缺省)

2. **发布通道归档(B1)**:c2278d0「feat(发布通道): 添加 plugin marketplace 元数据」新增 `.claude-plugin/marketplace.json`(Claude Plugin Marketplace 字段规范全合规:plugins[*].name/source/description/version/keywords/homepage/license/skills),但 v0.3.16 CHANGELOG 6 条承诺与 SKILL.md `## 版本` v0.3.16 段(①②③④)均未提及,属「借版本打包发布通道」。本次显式归档:`description` 同步修正 6 道防线口径(详见 §3);SKILL.md `## 版本` v0.3.16 段补 ⑤「新增 `.claude-plugin/marketplace.json`,声明发布通道元数据」

3. **「6 道防线」口径对齐(A2 + Standards #1)**:`marketplace.json` 原 description 写「6 道防线(... / 9 类对抗压测)」,把 v0.3.12 内的「9 类攻击清单数」当防御名,与 SKILL.md「对抗压测(可选增强,不新增硬闸)」口径不一致。本次改成「对抗压测·9 类攻击清单·可选增强」,明文标「可选」,防止从 marketplace 安装的用户误为硬约束

4. **占位符正则收紧(C1 + Standards #4)**:`scripts/check_step.py` 原通用匹配 `r"<[\u4e00-\u9fff][^>]*>"` 1 字起步,会误判合法正文「用户 <文献> 目录」「<中文摘要>」等。本次收紧为双层:
   - **通用**:4 汉字起步 `r"<[一-鿿]{4,}[^>]*>"`,过滤掉 1-3 字尖括号(`<文献>`/`<用户>`/`<什么>`/`<中文>`)
   - **关键词白名单兜底**:覆盖 `<来源 Gap 编号>` / `<Gap 编号>` / `<研究类型 标签>` / `<填这里>` 等 1-3 字或含空格/Gap 的混合占位符(15 个 init 模板家族关键词)
   - 实测 init 模板 12 个占位符全部命中、金样例全部 clean;仍存在的 corner case:4 字以上纯描述性尖括号(如 `<中文摘要>` `<显著水平>`)会被拦,建议改写成「中文摘要」「显著水平」(无尖括号),CHANGELOG 在此注明 trade-off

5. **不破坏**:`--step all` 失败项数与 v0.3.16 持平(4 项 = Step2a/5/review,均为金样例有意缺省);Step 6 主报告闸仍 PASS;`process/` 子目录回退、占位符拦截、五道防线、`check_step.py` 自身闸门逻辑全部保留;`_resolve_workdir_file` 行为不变(主报告 `00_研究计划报告.md` 仍走「根目录 → process/」回退,与 v0.3.16 一致)

6. **版本**:SKILL.md frontmatter `version: "0.3.16"` → `"0.3.17"` + 标题 + README 版本徽章 + CHANGELOG 顶部;`check-ready.sh` 自取 frontmatter(自动跟随)

---

## v0.3.16 · 2026-08-13 · 金样例可复验性加固(占位符闸门补漏 + process/ 布局兼容)

**主线**:金样例是「Agent 应模仿的完成态」,但它本身不可复验——主报告附录 F 残留模板占位符、过程文件放进 `process/` 子目录后闸门脚本全部报「文件不存在」、README 还指向一个被 `.gitignore` 排除、仓库里从未存在的 `outputs/` 目录。本次把这三处一起收口:占位符闸门从「枚举拦截」升级为「通用拦截」,脚本文件解析支持 `process/` 子目录回退,文档引用对齐真实仓库。

1. **占位符闸门补漏(根因修复)**:`PLACEHOLDER_PATTERNS` 原来只枚举 `<请填写` / `<YYYY-MM-DD>` / `<研究主题>` 等 3 个特定模式,而 init 模板家族实际有 20+ 个 `<中文...>` 形态占位符(`<用户文献目录>` / `<候选主题标题>` / `<来源 Gap 编号>` / `<具体哪几篇文献>` / `<这个题揭示了什么?禁止与标题雷同>` 等)全部漏网。新增通用模式 `r"<[\u4e00-\u9fff][^>]*>"`,整个 `<中文>` 占位符家族一次覆盖;模板生成后未填充即跑闸门 → 立即 FAIL(填充前不得过闸)
2. **金样例占位残留清除(3 处)**:主报告附录 F「文献」行 `<用户文献目录>\测试文献\2` → 「6 篇(用户自备,见附录 A)」;`process/Step1-input.md` 文献源目录同款残留 → 「用户自备 6 篇 PDF」;旧样例 `Step2a-points.md` OCR 目录树头部 `<用户文献目录>\测试文献-OCR\` → 「测试文献-OCR\」
3. **process/ 子目录布局兼容**:`check_step.py` 新增 `_resolve_workdir_file()` helper,所有产物文件(Step*/topic_scores/review_*/interaction-log/复跑记录/主报告)统一按「根目录 → `process/` 子目录」顺序解析,根目录优先、process/ 回退、皆无则报错。金样例 `process/` 下 Step1/2b/2c/3a/3b/4 + topic_scores 从「文件不存在」变为**全部 PASS**;`--step all` 失败项从 12 收敛到 4,仅剩金样例有意缺省的 Step2a/Step5/两个 review 文件
4. **断链修复**:金样例 README 引用的 `outputs/漂绿与金融市场风险/`(被 `.gitignore` 排除、仓库中不存在)改为指向仓库内真实存在的 `process/`,校验章节更新为可执行命令并注明「`--step all` FAIL 是预期(有意缺省),非损坏;Step 6 主报告闸必须 PASS」;主 README 文件结构图 `outputs/` 标注改为「本地运行的中间文件(.gitignore 排除,不入库)」
5. **不破坏**:5 个 Checkpoint、六道防线、六段式主报告闸、反坍缩/反黑话/反黑箱校验全部保留;未填充模板仍被拦截(helper 只影响文件查找位置,不影响校验逻辑)
6. **版本**:SKILL.md frontmatter `version: "0.3.15"` → `"0.3.16"` + 标题 + README 版本块 + CHANGELOG 顶部 + `check-ready.sh` 自取 frontmatter(自动跟随)

## v0.3.15 · 2026-08-13 · 内置 academic-humanizer(jefeerzhang fork)

**主线**:把 Step 6「去 AI 味润色」从「可选外部依赖」升级为「仓库自带 vendor/ 副本」,与 v0.3.14 把 Nero1688 子 skill 内置的逻辑一致——首次 `git clone` 即自洽可跑,不再需要用户额外 clone jefeerzhang 上游。

1. **布局**:`vendor/academic-humanizer/` 镜像 [jefeerzhang/academic-humanizer-zh](https://github.com/jefeerzhang/academic-humanizer-zh),但**剔除** 5 个资产文件(banner.svg / rednote-zh.svg / rednote-zh.png / x-en.svg / x-en.png,共约 300KB,纯社交卡片)、`.skill_id`、上游 `.gitignore`、上游 `README.md`(与 v0.3.14 剔除 `.git*`/`dist/`/`docs/` 同思路)。保留:`SKILL.md` + `LICENSE` + `references/rules-zh.md`(fork 增量 C7 中文层) + `examples/before-after.md`(上游英文样例) + `examples/before-after-zh-academic.md`(fork 增量中文样例)
2. **命名**:SKILL.md frontmatter `name` 沿用上游 `academic-humanizer`(无 `-zh`),vendor 目录名 = frontmatter name(`vendor/academic-humanizer/`),与 v0.3.14 4 个子 skill 命名约定一致(host 文档历史使用的 `-zh` 是 GitHub repo slug,非 canonical name,本次统一)
3. **法务**:`vendor/academic-humanizer/LICENSE` 单放(MIT, Copyright 2026 AIScientists-Dev;fork 未重署版权);`NOTICE.md` 新增独立段,声明 AIScientists-Dev(本仓库版权方)+ jefeerzhang(增量贡献方)+ blader/humanizer + koaeraser/ARMS(方法论上游)三方 attribution;传递依赖 = **无**(纯 prompt/contract skill,无 Python / 无 pip / 无 API key)
4. **探测**:`check-ready.sh` 新增 vendor probe,`EXPECTED_SKILLS` 数组第 5 项加入 `academic-humanizer`,头部 `[1/5]…[5/5]` → `[1/6]…[6/6]`,vendor 缺失不阻塞(退到 deai-checklist 兜底)
5. **文档**:`SKILL.md` 协议块新增 academic-humanizer 子段;`references/deai-checklist.md` 借鉴来源从 GitHub URL 改为 `vendor/academic-humanizer/references/rules-zh.md` 本地路径,角色从「首选润色器」降为「humanizer 兜底 + 润色后自查」;`references/delivery-spec.md` §3.3 由「可选增强(不强制)」改为「v0.3.15 起内置」;`README.md` 依赖块 4 项 → 5 项表格化、Nero1688 与 academic-humanizer 各自归口不同上游;`assets/comparison.md` **不更新**(academic-humanizer 不是直接同行,是上游依赖)
6. **不破坏**:5 个 Checkpoint、`scripts/check_step.py` 闸门、六道防线(v0.3.4–v0.3.13)、Nero1688 vendor 子段、`vendor/LICENSE`(Nero1688 MIT 仍独占 root)—— 全部保留
7. **版本**:SKILL.md frontmatter `version: "0.3.14"` → `"0.3.15"` + 标题 + README 版本块 + CHANGELOG 顶部 + `check-ready.sh` 自取 frontmatter(自动跟随)
8. **升级路径**(给维护者):`git pull` jefeerzhang 上游 → `cp -r upstream/* vendor/academic-humanizer/`(覆盖,但需手工剔除新增 assets/) → 校验 SKILL.md frontmatter `name` 仍为 `academic-humanizer`(不要变成 `academic-humanizer-zh`)→ 跑 check-ready

## v0.3.14 · 2026-08-13 · 内置 4 个 Nero1688 子 skill(vendor/)

**主线**:把"可选外部依赖"换成"仓库自带 vendor/ 副本",让首次 `git clone` 即自洽可跑,不再需要用户额外 clone 上游 Nero1688 仓库。

1. **布局**:`vendor/<skill>/` 镜像上游 `Nero1688/skills/<skill>/`,4 个 sub-skill 全部 drop-in 拷贝(SKILL.md + scripts/ + references/ + ATTRIBUTION.md),不拷贝上游 `.git*` / `dist/` / `docs/` / `CONTRIBUTING.md`(聚合仓库级维护产物,非 skill 内容)
2. **法务**:`vendor/LICENSE` 复制 Nero1688 MIT 原件;新增 `NOTICE.md` 汇总上游声明与传递依赖(`pypdf` BSD-3-Clause、`requests` Apache-2.0、`openpyxl` MIT);host `LICENSE` 不动(MIT 对 MIT 兼容)
3. **文档**:`SKILL.md` Step 2b/5 + 协议段 + 与同族 skill 分工表引用全部改走 `vendor/<name>/` 路径;`README.md` 快速开始删除 Nero1688 clone/cp loop,新增 `pip install pypdf requests openpyxl` 与 `CROSSREF_MAILTO` 礼仪提示,保留 `CLAUDE_SKILLS_DIR` 覆盖口供外置用户
4. **探测**:`check-ready.sh` 新增 vendor-first 探测,global fallback 仍保留;头部 `[1/4]…[4/4]` 改为 `[1/5]…[5/5]`,新增第 5 段检查 `vendor/LICENSE` + `NOTICE.md` 存在
5. **清理**:`.gitignore` 增 `Nero1688/` 一行,防探测期 clone 产物再被提交
6. **不破坏**:5 个 Checkpoint、自写路径、`scripts/check_step.py` 闸门、六道防线(v0.3.4–v0.3.13)全部保留 —— `scripts/*.py` 原本就不调用 sub-skill(纯本地闸门),本次零闸门脚本改动
7. **版本**:SKILL.md frontmatter `version` + 标题 + README 版本块 + CHANGELOG 顶部 + `check-ready.sh` 自取 frontmatter(自动跟随)
8. **升级路径**(给维护者):`git pull` Nero1688 上游 → `cp -r upstream/skills/<name>/* vendor/<name>/` 覆盖 4 个目录 → `cp upstream/LICENSE vendor/LICENSE` → 跑 check-ready 校验

## v0.3.13 · 2026-08-13 · Step 4 三层假设闸

**主线**:把「假设提炼」从「列出可证伪假设」升级为「先证明值得做,再写假设」——结论、金句、最险假设三层闸门,防止"看似严谨实则空泛"的假设。

1. **第 1 层 · 结论优先测试**:先写 2-3 句理想结论;写不出具体有力的结论(只会套话「X 与 Y 显著相关」)→ 影响不足,回 Step 3b 换题或收窄
2. **第 2 层 · 单句金句**:核心洞见压成一句话,须能当摘要首句、让人停下来读;与 Step 3a 贡献类型门「揭示了什么」呼应(金句 = 一句话版的揭示了什么)
3. **第 3 层 · 最险假设 + 1-2 周可测**:找出单一最可能杀死选题的假设,给 1-2 周 mini 验证路径(平行趋势初探/关键协变量检验);按风险排序而非逻辑顺序
4. **闸门**:`check_step --step 4` 强制 `Step4-hypotheses.md` 含「三层假设闸」;金样例 Step4 同步补三层闸示范
5. **来源**:借鉴 Carlini 结论优先测试 + researcher-pack(MIT)RS2/RS3/RS4,经管实证语境改写,见 `references/methodology-sources.md`

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
- 依赖(已内置 vendor/):
  - Nero1688/claude-academic-skills 的 4 个子 skill(bilingual-paper-reader / literature-matrix-builder / causal-inference-architect / research-method-selector,MIT;详见 `vendor/LICENSE` 与 `NOTICE.md`)
  - v0.3.15+ academic-humanizer(jefeerzhang fork,MIT, 上游 AIScientists-Dev;详见 `vendor/academic-humanizer/LICENSE` 与 `NOTICE.md`)
- 方法论参考:JARS / PRISMA / DA-RT / Pearl DAG / VanderWeele / SESOI 公开学术标准
- 工坊:鲁班 Skill 打磨工坊