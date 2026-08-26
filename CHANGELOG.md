# Changelog · 选题工坊

> 维护原则:本文件按"为什么改"叙事,而非"改了什么"列表。每版聚焦一段决策主线。
> 详细 commit history 见 `git log`。release tag 由人工打。

## v0.3.22 · 2026-08-26 · 模板契约深化:`templates` 深 module,模板与其占位符拦截规则同址

**主线**:v0.3.21 收口的是「切分语义散在三处」,本次收口的是「模板长什么样散在两个 module」。init 内嵌 410 行模板字面量,check 用手写正则反向描述同一批占位符,注释自认「全部来自 init 生成的模板」却无任何机制保证——s2 事故(模板文本「请填写或修改」误触闸门)就是契约断裂的实证,此后只靠兜底测试事后抓。v0.3.17 的白名单正则更是漂移活化石:它引用的 token(<Gap 编号>/<研究类型 标签>/<填这里>)在当前模板里已不存在。

**方案**:新增 `scripts/templates.py` 作为「产物文件应该长什么样」的单一真源:14 个模板字面量迁入;占位符拦截模式从模板文本自动派生(19 个 token,精确匹配+空白放宽,HTML 注释行是编辑提示不参与派生);`FILL_TOKENS` 声明 init 的参数化 token 集合,与替换实现用断言双向锚定。`init_project.py` 只剩写盘与参数替换;`check_step.py` 的 PLACEHOLDER_PATTERNS 改为三段式:①模板契约(派生)、②通用闸规则(用户自造占位,与契约正交)、③家族关键词兜底(覆盖旧版模板与短于 4 汉字的变体)——后两段保留且解耦标注,不放松拦截语义。

**防线转移**:契约断裂从「事后被兜底测试抓到」变成「不变式测试即时变红」——模板里出现的每个占位必被拦截。s2 端到端测试与行为级用例原样保留。

**影响范围**:`scripts/init_project.py` 544→138 行(尾行无换行符,`wc -l` 计 137,与前值同用编辑器计数);新增 `scripts/templates.py`(471 行,其中 413 行为迁入的模板字面量)与 `tests/test_templates_contract.py`(7 用例)。测试 80 → 87(80 个已有回归锚 + 7 个新增模板契约不变式;全量 87 passed 耗时约 2.1s,无性能回归;s2 修复用例 `tests/test_template_placeholders_not_flagged.py` 原样保留并被 `test_s2_semantics_preserved` 交叉验证)。

**对账更正**(2026-08-26,随 P2-2 全量复核):本条与历史条目的行数/数量声明逐项对照代码修正——本条 `templates.py` 总行数 486→471(模板字面量 413 行核对无误)、`init_project.py` 544→137 更正为 544→138;v0.3.21 `check_step.py` 1075→992 更正为 1075→993;v0.3.18 WARNING 块 5 行更正为 6 行 blockquote(分两段 3+3);v0.3.17 白名单关键词 15 个更正为 18 个(③段实测)。均为计数口径修正,不改变任何行为与语义。

## v0.3.21 · 2026-08-26 · 文档解析深化:三套章节切分合并为 `md_doc` 深 module

**主线**:v0.3.20 收口的是「测试全绿,真实环境仍不可靠」,本次收口的是「同一份报告的切分语义散在三处,边界 bug 反复在同一位置爆发」。上一轮七项低危修复全部落在章节切分边界(`_extract_section` off-by-one、层级感知、附录 B 截取层级泛化)——这不是巧合,是三套各自实现的切分(六段按标题候选切 / 附录 A→B 按正则切 / 正文按整合附录正则切)共用了同一个脆弱概念却互不同步。测试直测下划线函数(`_extract_section`、`_strip_md_structure`)则是另一个信号:seam 实际存在,只是没被承认为 interface。

**方案**:新增 `scripts/md_doc.py` 作为切分语义唯一来源(标题树模型):解析一次,分节边界统一为「同级或更高级标题」,深层同名小节不截断;三个切分调用点变成对树的查询(`section_text` 取六段正文 / `appendix_range` 取附录范围 / `body_before` 取正文);`strip_structure` 一并收入。`check_step.py` 删除 `_extract_section` 与 `_strip_md_structure`,顺带消灭从未真正起作用的 `next_headings` 参数。

**语义契约**:拦截行为不变。附录范围查询标题优先、文本标记回退(沿用历史正则语义),不给无 # 前缀附录标题的既有报告形态制造新误报——与仓库「只消除误报、不放松拦截」的方向一致。直测下划线的用例迁移到 `md_doc` interface,行为级用例(64 个)原样保留作回归锚。

**影响范围**:`scripts/check_step.py` 判定路径重构(1075→993 行);新增 `scripts/md_doc.py`(153 行)与 `tests/test_md_doc.py`(16 用例);术语登记入仓库根 `CONTEXT.md`。测试 64 → 80(64 个已有行为级用例 + 16 个新增 md_doc interface 单元测试;全量 80 passed 耗时稳定在 ~2.0s)。

## v0.3.20 · 2026-08-24 · 审计驱动稳健性收口(17 项缺陷 + 测试 38 → 64)

> 历史注记: 2026-08-23 曾短暂提交过内置 superpowers-zh 子 skill 的草案版本并标为 v0.3.20 (commit `4554a757`); 同日经仓库评审认为与选题主领域偏离过远而完整回滚至 v0.3.19 (commit `ea5980d`, yanked)。当前正式发布的 v0.3.20 版本号为重用, 专注于审计驱动的稳健性收口。

**主线**:v0.3.19 收口的是「规范说一套,代码做另一套」,本次收口的是「测试全绿,真实环境仍不可靠」。两个并行只读审计 agent 深读三个脚本,产出 17 个全部经临时脚本验证的 bug 候选 + 一批覆盖缺口。最刺眼的事实:全套测试强制 `PYTHONIOENCODING=utf-8`,恰好把「Windows 管道默认 GBK 时 `print("✅")` 抛 UnicodeEncodeError、通过的报告也 exit 1」这条必踩路径完全遮蔽;`init_project.py --name/--branch/--language` 要替换的占位符在模板里根本不存在,是空操作,而 SKILL.md 还在教用户传;四个核心闸函数(`check_interaction_log` / `check_rerun_record` / `check_topic_scores` / `check_readability`)零直测,golden 只走 happy path。修复按四批落地,每批先写会红的测试再修,独立 commit。

1. **批次 1 — 编码稳健性**:`check_step.py` / `init_project.py` / `review.py` 入口新增 `_force_utf8_stdio()`(GBK 管道下 emoji 崩溃导致 PASS 也 exit 1、init 在 14 个文件写盘后崩溃);`check_step.py` 新增 `_read_text_utf8()`,编辑器存成 GBK 的产物文件得到「转存 UTF-8」提示而非裸 traceback。新增 `tests/test_encoding_robustness.py`,刻意以 GBK stdio 子进程运行(5 用例)
2. **批次 2 — 校验器误报(合规产物被误拦)**:`check_review` verdict 改取最后一次声明(正文转述历史轮次「verdict: FAIL」不再压过最终 PASS);interaction-log 原话过滤从「含 `<`/待填即整条丢弃」改为剥占位标记后无实义才跳过(「要求 t_score<0.5」保留);闸门匹配 `\b` → `(?!\d)`(汉字算 word char,「CP#1已确认」曾失配);附录豁免从字面串「# 整合附录」改为 markdown 标题行正则(带序号/无空格变体均豁免)。新增 `tests/test_false_positive_gates.py`(5 用例,含防豁免扩大化守卫)
3. **批次 3 — init 参数生效 + 文档对齐**:`00_任务元信息.md` 头部新增参数化摘要、Step1 模糊领域预填 `--name`;拒绝覆盖提示去重;回显命令给 `--workdir` 路径加引号;review.py 错误统一走 stderr 并删除 argparse 已限死的不可达分支;SKILL.md 文件树对齐实际产物(init 生成 14 个模板,`00_复跑决策记录.md` 与 `review_*.md` 标注为过程产物)。新增 `tests/test_init_params.py`(5 用例)
4. **批次 4 — 低危清扫 + 测试补强**:topic_scores 整数校验排除 bool;断句句界补全角 `!`;`_extract_section` off-by-one(`j > start` → `j >= start`)+ next_headings 层级感知(深层同名小节不再提前截断);reveals 抄题检测对 title 同步 strip;附录 A 截取边界泛化到任意标题层级;tier 不一致文案改由 `TIER_BANDS` 动态生成并注明模态区(消除 t_score=0.85 时「0.55≤safe<0.80」自相矛盾)。新增 `tests/test_gate_units.py`(rerun 三分支/topic_scores 变异/断句与切分边界直测,11 用例);空壳测试 `test_workdir_path_is_resolved` 改为真调 `check_step`;`test_golden_step_all_exactly_2_failures` 更名 `_1_failure`(名实对齐);弱断言收紧
5. **不修项(明确 wonfix)**:`_strip_md_structure` 对 `\字母` 行的整行删除 —— 宽松方向、有专项测试锚定,改动收益低于回归风险
6. **版本**:SKILL.md frontmatter / 标题、README 版本徽章与版本列表、marketplace.json、CHANGELOG 本条目五处同步至 0.3.20;`check-ready.sh` 自取 frontmatter 自动跟随
7. **提交**:`ad2c8a8`(批次 1)→ `11cdd91`(批次 2)→ `8b4c3da`(批次 3)→ `54da2a4`(批次 4)→ 本条目;测试 38 → 64 passed

---

## v0.3.19 · 2026-08-23 · 三轮 code review 收口 51 项(规范-脚本-样例闭环)

**主线**:v0.3.18 的"诚实化运动"让规范对用户说真话,但仓库自己还有大量「规范说一套,代码做另一套」的不一致——spec 上写 Checkpoint #5 在 Step 6 之前,文本流程图却写在 Step 6 之后;verdict 正则会贪婪吃掉中文句读,`verdict: PASS,继续` 被静默判 FAIL;`init_project.py` 只要 `00_任务元信息.md` 不在就静默覆盖已写的 Step 1–5;SKILL.md 文件树列出两个 vendor 子 skill 但 Step 2a/Phase 0 正文从没调用它们。这些 latent 问题让「Skill 写一套对的事,Agent 跑出另一套对的事」同时成立,用户被骗不动但结果不可信。本次对仓库做三轮 code review(规范 / 脚本 / 样例,三个并行的 general-purpose agent),收口 51 项,效果是把 Skill spec、Python script、黄金样例三者之间的所有关键路径都用测试和样例内容实际覆盖,事后任何一处规范说「应如此」都在代码或样例里有对应证据。

1. **第 1 轮 — 阻塞级(9 项)**
   - **流程图 Checkpoint #5 顺序对齐**(SKILL.md L239-241):文本 ASCII 流程图原写 `Step 5 → Checkpoint #5 → Step 6`,Mermaid 块写 `Step 5 → Step 6 → Checkpoint #5`,agent 两次读到相反顺序会随机选一种执行。本次以 Mermaid 为准,文本图改为同序,避免 agent 出现"先审后产出"
   - **`verdict` 正则贪婪捕获**(check_step.py:693/722/734):原 `[^\s\*\`]+` 把 `verdict: PASS,继续` 捕获成 `PASS,继续` → 不在合法集 → 硬 FAIL。锚定为 `REVIEW_VALID_VERDICTS`(单一真源 = `{PASS, P0_OPEN, FAIL, NEEDS_HUMAN}`),中文自然写法不再误判
   - **`init_project.py` 静默覆盖**(init_project.py:436-462):原检查只挡 `00_任务元信息.md`,目录里有 `Step1-input.md` 等半成品时会被整盘覆盖。新增 `TRACKED_FILES` 16 项 + `--force` 闸门,`sys.exit(1) + stderr` 提示,`--force` 才覆盖并列出受影响文件
   - **`--workdir ~` 解析**(check_step.py:931-934):`os.path.isdir(args.workdir)` 不展开 `~`,与 `init_project.py` / `review.py` 的 `.expanduser().resolve()` 不一致,导致 `--workdir ~/projects/x` 误报"目录不存在"。入口处统一 `.expanduser().resolve()`
   - **v0.2.X 变更日志去重**(SKILL.md L806-826):v0.2.7 同一行出现 3 次,描述互相冲突(`独立审查分离` / `安装链路修复` / 重复块)。合并为单行,删除整段重复块;行为归属从此可被 agent 一眼查到
   - **`用户决策` 措辞歧义**(SKILL.md L281):"看 total 分数,选最高的"读起来像让 agent 代选算法,与 L455(原 L453)`禁止默认选 total 最高项`硬规则直接冲突。改为「用户决策建议」(建议性语气),强制用户**显式点名**(`选候选 2`)并加 L455 交叉引用
   - **黄金样例 `Step3b` 对抗压测 2 → 9 类**:原 2 类(`识别策略` / `理论增量`),spec 要求 ≥ 6 类攻击。扩展到 spec §7.1 全部 9 类(识别 / 贡献类型 / 换情境 / 换术语 / 已被占 / 数据质量 / 不可行 / 不可证伪 / 范围过宽),每类 1 句攻击 + 1 句回应 + 1 个生存标签(PASS / TIGHTEN / RERUN / REFRAME / DROP),综合 6 存活 / 3 需收窄
   - **恢复 `Step5-identification-strategy.md`**(黄金样例):该文件 v0.3.18 时被折进主报告附录 E 只剩 8 行,用户追溯 H1–H5 的识别细节要回主报告翻。独立为 `process/Step5-identification-strategy.md`(89 行,每假设 200–400 字,覆盖基准回归 / 内生性来源 + 主识别 / 一句话稳健性清单),主报告附录 E 保留紧凑版作交叉引用
   - **黄金样例补充**:其余格式瑕疵(Q2/H1–H5 裸 ID、L823 "鲁班方案 A" 历史归属保留等)在后续轮次统一处理

2. **第 2 轮 — 重要级(21 项)**:**SKILL.md 9 项 + 脚本 8 项 + 黄金样例 4 项**。
   - **SKILL.md**:复跑定义补「5 闸全部仍须各停一次(L399 优先)」(m1);`grill-me` 与 `Grill` 双义显式区分(Phase 0 = 分次追问法,Grill = 闸门内子问)(m2);Phase 0 显式调用 `research-method-selector`,Step 2a 显式调用 `bilingual-paper-reader`(m3);7 个首字母缩写首现展开(PRISMA 2020 / JARS / DA-RT / Pearl DAG / VanderWeele / SESOI / Carlini / RS2/RS3/RS4 / RTS v1.5.2 / VS)(m4);T-Score 内联 60-80 字启发式阈值 + t_score/Gap-C1/Checkpoint 同期展开(m5);「明确确认」定义(用户原话含「确认/通过/选 X/OK/同意」之一,「继续/好的/嗯」不算)(m6);对抗压测 opt-in 显式 `AskUserQuestion`(m7);`输入过薄` 阈值 ≥ 1 完整子句 + ≥ 1 个研究对象(m8);`methodology-sources.md` 加 section 锚点(m9)
   - **脚本**:`--workdir` 是文件时 `sys.exit(1)` 防 path traversal(s1);`PLACEHOLDER_PATTERNS` 加组合正则 + 锚定尖括号(s2);`--step all` 用 `_from_all` 标记去重,s3a/6 的 helpers 只跑一次(s3);`_extract_section` 接受 `#{1,6}` 同级比较(s4);`_count_matrix_data_rows` 用前后 `|` 边界的 Markdown 行检测 + 全行「作者+年份」头检测(s5);`check_placeholders` 标签改为中性 `main` 避免重复 `Step6:` 前缀(s6);`is_empty` 用 `PLACEHOLDER_PATTERNS_RE` 替代 substring 检查(s7);`_tier_of` 超界(`≤ 0` 或 `≥ 1`)抛 `ValueError`,`check_anti_collapse` 仍不崩溃(s8)
   - **黄金样例**:§2.5 决策链裸 ID → 「政策组合候选（候选 2）/ 五条假设」(g1);H5 SESOI 锚定到 L3/L4 已报告 DID 主效应下界(≥ 25% 主效应),其余 4 条保留探索性(g2);附录 B 加 Step 2a 要点卡合并说明(g3);§3.1 第三主张删冗余 1 句(披露质量可比性已述于 §2.3)(g4)

3. **第 3 轮 — 轻微级(21 项)**:**SKILL.md 13 项 + 脚本 8 项**。
   - **SKILL.md**:frontmatter 与正文 section 名「依据」→「假设依据」(mi1);`鲁班三刀` → `三件加固`(mi2);`P1 复现性` 补全(m3);`半强校验` → `条件校验`(mi4);--branch 可选值注释推断性/描述性/质性/混合(m5);`生成 11 个模板` 改为 16 文件名显式枚举(m6);RTS 首次出现补全 Research Topic Skills(m7);Diverga 加交叉指针(m8);`诚实声明` 方括号标记为已知局限附注(m9);三条「禁止」规则统一为「反跳过三铁律 · 三不可」(mi10);变更日志顶加金样例缺省状态对账(mi11);`已确认·复跑授权` 声明为字面 token + 匹配正则(mi12);v0.2.7 时间序澄清(mi13)
   - **脚本**:删 init_project.py / review.py 未用 `import os`(mi14/15);`BODY_JARGON` 全/半角括号统一为 `(?:[\(（]\s*探索性\s*[\)])` 同步匹配(mi16);`--branch` / `--language` argparse choices(mi17);`_strip_md_structure` 改为按词边界移除 `\`*_+`,保留 `snake_case` / `4*5` / `x*2` 中字符(mi18);5 个 magic numbers 提为模块常量(`MIN_PARAGRAPH_CHARS=40` / `ANTI_COLLAPSE_LOW_TIER=0.50` / `RERUN_EMPTY_THRESHOLD=30` / `MIN_REVEALS_LEN=8` / `MAX_BODY_SENTENCE=100`)(mi19);`check_step()` 137 行拆为 4 个 per-step rule 函数 + `STEP_RULES` 字典调度(mi20);review.py 打印的 `--workdir` 提示改为已解析绝对路径(mi21)
   - **历史归属保护**:v0.2.7 changelog entry 中"鲁班方案 A"(mi2 之外、专为历史归属保留)按 m3 历史型修复不动,避免删除历史借词导致 v0.2.x 引用脱节

4. **测试覆盖率**:17 → 21 → 30 → 33 passed(每次提交后)。新增 6 文件:`test_init_overwrite.py`(s3/f 合并,4 case)、`test_workdir_is_file_rejected.py`(s1)、`test_template_placeholders_not_flagged.py`(s2,2 case)、`test_anti_collapse_tier_out_of_band.py`(s8,4 case)、`test_extract_section_h3.py`(s4,2 case)、`test_review.py`(mi21,3 case)

5. **不破坏**:5 个 Checkpoint / 6 道防线 / 六段式主报告闸 / 反坍缩·反黑箱·反黑话校验全部保留;`--step 6` 与 `--step all` 在黄金样例上结果与 v0.3.18 一致(Step 6 PASS;--step all 仅 Step 2a 仍 FAIL,系金样例无 PDF 输入的有意缺省);`check_ready.sh` 跨文件对账 / `verify_workdir` / `_resolve_workdir_file` / review 三态返回全部沿用

6. **版本**:SKILL.md frontmatter `version: "0.3.18"` → `"0.3.19"` + 标题 + README 版本徽章 + CHANGELOG 顶部 + `check-ready.sh` 自取 frontmatter(自动跟随,无需手动改 banner)

7. **三轮提交**:`0922d41`(pass 1 阻塞)→ `73c0e93`(pass 2 重要)→ `19f04d2`(pass 3 轻微),已依次 `git push origin main`,远程 `main: d90f53e..19f04d2`

---

## v0.3.18 · 2026-08-23 · 审查降级为过程建议 + 版本对账(诚实化运动)

**主线**:之前 SKILL.md 把"独立审查"说成"刚性闸门",但 CHANGELOG v0.2.7 已经诚实承认 verdict "没有密码学身份保证"、"理论上审查者也可伪造"。这个矛盾让用户产生虚假合规感。本次把审查定位从「不可绕过的硬关」降级为「强烈推荐的过程建议」,让用户的期望与机器实际能保证的范围对齐。同时加 `check-ready.sh` 版本对账,解决「双来源 skill 谁先加载」的新手排错痛点。

1. **`check-ready.sh` 加版本对账(vendor + 仓库根 SKILL.md 跨文件)**
   - 双来源探测:vendor/ 与 `$SKILLS_DIR/` 同时存在同名子 skill 时,读两边 `SKILL.md` frontmatter `version:` 对账;academic-humanizer 带 version: 0.3.3 → 自动报告 `vendor 0.3.3 = external 0.3.3 ✅`;Nero1688 4 个 skill 缺 version: 字段 → 诚实报告「双来源均存在,但两边 SKILL.md 都缺 version: 字段,无法自动对账,请手动 diff」+ 给出处理建议(A 升级 / B 临时改名 / C 接受外部覆盖)
   - 跨文件对账:SKILL.md frontmatter version ↔ README badge Version ↔ CHANGELOG 顶部第一行,任一不一致报 ⚠️(防止 banner 漂移;v0.2.9 曾硬编码 SKILL.md 滞后)
   - 不破坏:Nero1688 子 skill 自报「无 version」是诚实的,不假装"对账失败";跨文件对账只在三处都存在版本号时校验
2. **`scripts/check_step.py` `check_review()` 重写,从 hard FAIL 改为 status 三态**
   - 返回 `(status, hard_errors, soft_warnings)` 而非 `(passed, errors)`
   - status=PASS / WARN / FAIL;FAIL 仅在 verdict 字段缺失或值非法时返回;WARN 用于「文件缺失 / verdict=FAIL / 信任边界声明缺失 / reviewer 仍是模板占位」等——都不阻塞 `--step all`
   - verdict 合法值扩到 {PASS, P0_OPEN, FAIL, **NEEDS_HUMAN**};新增 NEEDS_HUMAN 表示审查者明确自承「拿不准,需人类专家复核」,比伪造 PASS 更诚实
   - `--step scan-review` / `--step topics-review` 子命令只在 status=FAIL 时 sys.exit(1);WARN 仍返回 True
   - `--step all` 循环:review 缺失/警告写到 stderr(便于 grep),但不计入 failures;金样例 review 缺失从 FAIL 降为 stderr 警告,失败项不变(只剩有意缺省的 Step2a/5)
3. **SKILL.md 「机器闸门 + 独立审查」段降级措辞**:「刚性闸门」→「机器闸门(过程建议)」;新增「审查作为过程建议」子段,解释为什么降级、列出 NEEDS_HUMAN 语义、引用 CHANGELOG v0.2.7 同款诚实声明
4. **`scripts/review.py` 两个 VERDICT_TEMPLATES 块加 WARNING 块**:信任边界段(`## 7. 信任边界声明`)开头加 **WARNING · v0.3.18 审查降级说明**(6 行 blockquote,分两段 3+3),明确「verdict 仅作过程留痕,不可作为合规依据、不可作为学术可信度背书」,并把 `verdict` 行的合法值扩到 `PASS / P0_OPEN / FAIL / NEEDS_HUMAN`(加 NEEDS_HUMAN 选项)。
   - **更正**:原提交说明写「同时简化信任边界声明(原本 4 行,新版 2 行)」,事实是 *baseline 已是 2 行,新版叠加 WARNING 块后实际为 6 行 blockquote*——本次按诚实原则更正:信任边界声明本身**未压缩**,WARNING 块是**新增的诚实免责声明**,二者并列存在而非简化
5. **README.md Examples badge + LEGACY 提示**:`2 (1 gold)` → `2 (1 gold · 1 LEGACY)`;加一行明确说明「气候风险…/ 是 v0.2.x 旧形态,不通过 v0.3 闸门」
6. **`examples/气候风险对企业绿色转型/README.md` 头部加 ⚠️ LEGACY 块**:指向 LEGACY.md + 金样例路径,第一次进仓库的人不会被旧样例的 FAIL 误导
7. **不破坏**:5 个 Checkpoint、六道防线、六段式主报告闸、反坍缩/反黑话/反黑箱校验全部保留;Step6 主报告闸、Step3a 反坍缩、topic_scores 评分等仍 FAIL-as-before
8. **版本**:待 SKILL.md frontmatter 升级 `version: "0.3.17"` → `"0.3.18"` 后,README badge / CHANGELOG 顶部 / `check-ready.sh` 自动跟随(`SELF_VERSION=$(grep ...)` 已支持)

---

## v0.3.17 · 2026-08-13 · 审稿反馈闭环 + 发布通道归档

**主线**:对 v0.3.16 改动跑了一次双轴 code-review(`code-review` skill,Standards + Spec 并行子代理),收口 4 处遗留 + 归档发布通道。本版不是新功能,是 v0.3.16 的边角收口与对外发布准备。

1. **断链修复字面闭合(A1)**:v0.3.16 §4 承诺「金样例 README 引用的 `outputs/漂绿与金融市场风险/` → 真实存在的 `process/`」,改了 README 与主报告,但 `process/Step1-input.md:3` 仍写「工作目录 `outputs/漂绿与金融市场风险`」,字面承诺未完全闭合。本次把该行改成「复盘归位 · 工作目录 `process/`」并加注释说明 v0.3.16 起过程文件统一进 process/、根目录仅留主交付;`check_step --step 1` 仍 PASS,`--step all` 失败项数与 v0.3.16 持平(4 项,均为有意缺省)

2. **发布通道归档(B1)**:c2278d0「feat(发布通道): 添加 plugin marketplace 元数据」新增 `.claude-plugin/marketplace.json`(Claude Plugin Marketplace 字段规范全合规:plugins[*].name/source/description/version/keywords/homepage/license/skills),但 v0.3.16 CHANGELOG 6 条承诺与 SKILL.md `## 版本` v0.3.16 段(①②③④)均未提及,属「借版本打包发布通道」。本次显式归档:`description` 同步修正 6 道防线口径(详见 §3);SKILL.md `## 版本` v0.3.16 段补 ⑤「新增 `.claude-plugin/marketplace.json`,声明发布通道元数据」

3. **「6 道防线」口径对齐(A2 + Standards #1)**:`marketplace.json` 原 description 写「6 道防线(... / 9 类对抗压测)」,把 v0.3.12 内的「9 类攻击清单数」当防御名,与 SKILL.md「对抗压测(可选增强,不新增硬闸)」口径不一致。本次改成「对抗压测·9 类攻击清单·可选增强」,明文标「可选」,防止从 marketplace 安装的用户误为硬约束

4. **占位符正则收紧(C1 + Standards #4)**:`scripts/check_step.py` 原通用匹配 `r"<[\u4e00-\u9fff][^>]*>"` 1 字起步,会误判合法正文「用户 <文献> 目录」「<中文摘要>」等。本次收紧为双层:
   - **通用**:4 汉字起步 `r"<[一-鿿]{4,}[^>]*>"`,过滤掉 1-3 字尖括号(`<文献>`/`<用户>`/`<什么>`/`<中文>`)
   - **关键词白名单兜底**:覆盖 `<来源 Gap 编号>` / `<Gap 编号>` / `<研究类型 标签>` / `<填这里>` 等 1-3 字或含空格/Gap 的混合占位符(18 个 init 模板家族关键词,2026-08-26 P2-2 复核实测③段 18 个,原写 15 个)
   - 实测 init 模板 12 个占位符全部命中、金样例全部 clean;仍存在的 corner case:4 字以上纯描述性尖括号(如 `<中文摘要>` `<显著水平>`)会被拦,建议改写成「中文摘要」「显著水平」(无尖括号),CHANGELOG 在此注明 trade-off

5. **不破坏**:`--step all` 失败项数与 v0.3.16 持平(4 项 = Step2a/5/review,均为金样例有意缺省);Step 6 主报告闸仍 PASS;`process/` 子目录回退、占位符拦截、五道防线、`check_step.py` 自身闸门逻辑全部保留;`_resolve_workdir_file` 行为不变(主报告 `00_研究计划报告.md` 仍走「根目录 → process/」回退,与 v0.3.16 一致)

6. **版本**:SKILL.md frontmatter `version: "0.3.16"` → `"0.3.17"` + 标题 + README 版本徽章 + CHANGELOG 顶部;`check-ready.sh` 自取 frontmatter(自动跟随)

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
