"""check_step_lib · gates.py

8 个 check_X 闸门(无路由,无 CLI)。每个闸门返回 (passed:bool, errors:list[str])。

调用方式:
  from .gates import check_rerun_record
  ok, errs = check_rerun_record(workdir, report)

依赖通过 `from .helpers import *` 取得 17 常量 + 9 helper;gates 函数体内
对裸名(如 TIER_BANDS / _tier_of / _count_cjk_and_alnum)的引用会通过 helpers 解析。
"""
from .helpers import *


def check_placeholders(content: str, label: str) -> list[str]:
    errors = []
    for pat in PLACEHOLDER_PATTERNS:
        if re.search(pat, content):
            errors.append(f"{label}: 含模板/占位残留,匹配 /{pat}/")
    return errors


def check_step6_quality(content: str) -> list[str]:
    """Step 6 主报告质量闸(防空壳)。"""
    errors = []
    errors.extend(check_placeholders(content, "main"))

    # 附录标题
    for app in ["附录 A", "附录 B", "附录 C", "附录 D", "附录 E", "附录 F"]:
        if app not in content:
            errors.append(f"Step6: 缺少整合附录标题「{app}」")

    # 禁止只丢路径
    if re.search(r"详见\s*`?Step2b", content) and _count_matrix_data_rows(content) < 1:
        errors.append("Step6: 不得以「详见 Step2b」代替文内文献矩阵")

    # 矩阵数据行
    matrix_rows = _count_matrix_data_rows(content)
    if matrix_rows < 5:
        errors.append(
            f"Step6: 附录 A 文献矩阵数据行 {matrix_rows} < 5"
            f"(须收录完整矩阵,至少 5 篇文献行)"
        )

    # 六段最小论述量
    six = [
        ("选的题是什么", 200, 1),
        ("为什么选这个题", 600, 3),
        ("选题的意义", 300, 2),
        ("假设是什么", 600, 3),
        ("为什么能写出这样的假设", 400, 2),
        ("后面应该怎么做", 300, 2),
    ]
    for heading, min_chars, min_paras in six:
        sec = md_doc.section_text(content, heading)
        if not sec.strip():
            errors.append(f"Step6: 未能解析章节「{heading}」正文")
            continue
        chars = _count_cjk_and_alnum(sec)
        paras = _count_paragraphs(sec)
        if chars < min_chars:
            errors.append(
                f"Step6:「{heading}」有效字符约 {chars} < 最低 {min_chars}"
                f"(论述过薄,禁止一句话观点)"
            )
        if paras < min_paras:
            errors.append(
                f"Step6:「{heading}」有效段落 {paras} < 最低 {min_paras}"
                f"(须分段展开,表格不能代替论述)"
            )

    # 假设可证伪出现次数(防只在目录出现一次)
    if content.count("可证伪") < 2:
        errors.append("Step6:「可证伪」出现不足 2 次(假设段须真正写可证伪条件)")

    # 总长度
    if _count_cjk_and_alnum(content) < 3000:
        errors.append(
            f"Step6: 全文有效字符约 {_count_cjk_and_alnum(content)} < 3000"
            f"(主报告过短,未达开题框架厚度)"
        )

    # 可读性层(v0.3.8):正文(开头→整合附录前)禁内部黑话 + 禁超长句
    errors.extend(check_readability(content))

    return errors


def check_interaction_log(workdir: Path) -> tuple[bool, list[str]]:
    """校验 5 闸交互留痕。缺任一闸确认 → FAIL,禁止交付。

    设计意图:5 闸硬暂停过去只存在于提示词里,没有任何机器证明「用户确认过」,
    弱 Agent 可静默跳过全程。此函数让「没交互」变成可见失败,而不是静默假成功。
    """
    errors = []
    log_file = _resolve_workdir_file(workdir, "interaction-log.md")

    if not log_file.exists():
        return (
            False,
            [
                (
                    "interaction-log.md 不存在。5 闸确认必须留痕(每闸一条用户原话),"
                    "否则视为未交互,禁止交付。用 init_project.py 生成模板,或补记确认记录"
                )
            ],
        )

    try:
        content = _read_text_utf8(log_file)
    except Utf8ArtifactError as e:
        return (False, [str(e)])
    confirmed: dict[str, list[str]] = {}
    for line in content.splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) < 4:
            continue
        # 表结构:闸门 | 状态 | 时间 | 用户原话
        gate, status, _time, quote = cells[0], cells[1], cells[2], cells[3]
        if "确认" not in status and "通过" not in status:
            continue
        if not quote:
            continue
        # 占位符不算确认:剥掉占位标记后无实义内容的原话(<待填>/<用户原话>)跳过;
        # 含 < 的真实原话(如「要求 t_score<0.5」)必须保留
        if not re.sub(r"[<>【】《》\[\]]|待填", "", quote).strip():
            continue
        for g in REQUIRED_GATES:
            # (?!\d) 而非 \b:\b 把汉字算 word char,「CP#1已确认」会失配;
            # 它只排除编号延伸(CP#10 不误配 #1)
            if re.search(rf"(?:CP)?{re.escape(g)}(?!\d)", gate):
                confirmed.setdefault(g, []).append(quote)

    missing = [g for g in REQUIRED_GATES if g not in confirmed]
    if missing:
        errors.append(
            f"交互留痕不足:闸门 {', '.join(missing)} 无用户确认记录(interaction-log.md)。"
            "5 闸须各至少 1 条用户原话;未确认的闸门 = 未交互,禁止交付"
        )

    return (len(errors) == 0, errors)


def check_rerun_record(workdir: Path, main_report_path: Path) -> tuple[bool, list[str]]:
    """校验复跑授权合法性。

    规则:
    1. 主报告附录 F 声明「复跑」但无 00_复跑决策记录.md → FAIL(附录 F 只是历史记录,不是当次授权)
    2. 00_复跑决策记录.md 存在但只有模板/占位符(无当次原话、无时间)→ FAIL(空壳拦截)
    """
    errors = []
    rerun_file = _resolve_workdir_file(workdir, "00_复跑决策记录.md")
    try:
        main_report = _read_text_utf8(main_report_path) if main_report_path.exists() else ""
    except Utf8ArtifactError as e:
        return (False, [str(e)])

    # 只认声明位:复跑说明 / 本复跑 / 附录F 表行「| 复跑 |」;「需复跑核实」等提及不算
    declares_rerun = any(re.search(p, main_report) for p in RERUN_DECLARE_PATTERNS)
    if declares_rerun and not rerun_file.exists():
        errors.append(
            "主报告声明「复跑」,但不存在 00_复跑决策记录.md。附录 F 决策表只是历史记录,"
            "不是当次授权;复跑授权必须由 00_复跑决策记录.md(含当次原话)提供"
        )
        return (len(errors) == 0, errors)

    if not rerun_file.exists():
        return (True, [])  # 未复跑,无需复跑记录

    try:
        content = _read_text_utf8(rerun_file)
    except Utf8ArtifactError as e:
        return (False, [str(e)])
    has_quote = any(p in content for p in RERUN_PHRASES)
    has_time = bool(re.search(r"\d{4}-\d{2}-\d{2}|\d{4}/\d{1,2}/\d{1,2}", content))
    is_empty = len(content.strip()) < RERUN_EMPTY_THRESHOLD or PLACEHOLDER_PATTERNS_RE.search(content) is not None

    if is_empty:
        errors.append("00_复跑决策记录.md 为空壳(无内容/占位符),不得视为复跑授权")
    if not has_quote:
        errors.append(
            "00_复跑决策记录.md 缺少用户当次原话引用(如「按上次选择」「复跑」「不要再问」)。"
            "复跑授权必须引用用户当次真实说的话"
        )
    if not has_time:
        errors.append("00_复跑决策记录.md 缺少决策时间(YYYY-MM-DD)")

    return (len(errors) == 0, errors)


def check_readability(content: str) -> list[str]:
    """可读性闸门:正文(开头→整合附录标题前)反黑话 + 断句。附录为技术对照区,豁免。

    正文边界由 md_doc 按标题树定位(任意层级/可带序号/空格可选),
    如「# 整合附录」「## 三、整合附录」「#整合附录」均豁免。
    """
    errors = []
    body = md_doc.body_before(content, "整合附录")

    # 1. 黑话禁止
    for pat in BODY_JARGON:
        hits = re.findall(pat, body)
        if hits:
            errors.append(
                f"Step6: 正文出现内部术语「{pat}」×{len(hits)}(如 {hits[:2]})。"
                "主报告是给读者/导师看的,须按 delivery-spec §3.3 术语翻译表改成人话;编号只在附录 C 对照"
            )

    # 2. 断句(超长句)——逐行测句长,避免跨行合并(标题+段/引用块+列表/公式拼成一坡)
    prose = md_doc.strip_structure(body)
    long_sentences = []
    for line in prose.splitlines():
        line = line.strip()
        if not line:
            continue
        for piece in re.split(r"[。；？！]", line):
            if len(piece.strip()) > MAX_BODY_SENTENCE:
                long_sentences.append(piece.strip())

    if long_sentences:
        longest = max(len(s) for s in long_sentences)
        errors.append(
            f"Step6: 正文有 {len(long_sentences)} 句超过 {MAX_BODY_SENTENCE} 字(最长 {longest} 字)。"
            "长句拆短(目标 ≤60 字),每句一个主谓;超长段落拆段(见 delivery-spec §3.3)"
        )

    return errors


def check_topic_scores(workdir: Path) -> tuple[bool, list[str]]:
    """校验 topic_scores.json。"""
    errors = []
    score_file = _resolve_workdir_file(workdir, "topic_scores.json")

    if not score_file.exists():
        return (False, ["topic_scores.json 不存在,请用 init_project.py 创建或手动生成"])

    try:
        data = json.loads(_read_text_utf8(score_file))
    except Utf8ArtifactError as e:
        return (False, [str(e)])
    except json.JSONDecodeError as e:
        return (False, [f"topic_scores.json 不是合法 JSON:{e}"])

    if "candidates" not in data:
        return (False, ["topic_scores.json 缺少 'candidates' 字段"])

    candidates = data["candidates"]
    if len(candidates) != 5:
        return (False, [f"candidates 长度 {len(candidates)} ≠ 5(应 3 主推 + 2 备选)"])

    selected_count = sum(1 for c in candidates if c.get("decision") == "selected")

    if selected_count != 3:
        errors.append(f"decision='selected' 的候选数 {selected_count} ≠ 3(应 3 主推池;非用户最终唯一)")

    for i, c in enumerate(candidates):
        prefix = f"候选 #{i+1} ({c.get('label', '?')})"

        if "scores" not in c:
            errors.append(f"{prefix}: 缺少 'scores' 字段")
            continue

        scores = c["scores"]
        for key in SCORE_KEYS:
            if key not in scores:
                errors.append(f"{prefix}: 缺少评分 '{key}'")
            elif isinstance(scores[key], bool) or not isinstance(scores[key], int):
                # bool 是 int 子类,True/False 会通过范围检查,显式排除(与 t_score 口径一致)
                errors.append(f"{prefix}: 评分 '{key}' 不是整数")
            elif not (1 <= scores[key] <= 5):
                errors.append(f"{prefix}: 评分 '{key}'={scores[key]} 不在 1-5 范围")

        if "decision" not in c:
            errors.append(f"{prefix}: 缺少 'decision' 字段")
        elif c["decision"] == "dropped" and not c.get("kill_rule"):
            errors.append(f"{prefix}: decision='dropped' 必须填 'kill_rule'")

        if "research_type" not in c:
            errors.append(f"{prefix}: 缺少 'research_type' 字段")

        # 贡献类型门(v0.3.7):每个候选必须回答「这个题揭示了什么」
        reveals = c.get("reveals")
        if not reveals or not isinstance(reveals, str) or not reveals.strip():
            errors.append(
                f"{prefix}: 缺少 'reveals' 字段(贡献类型门)。每个候选必须回答『这个题揭示了什么』——答不上 = 工程任务/重复验证,回炉"
            )
        else:
            reveals = reveals.strip()
            if len(reveals) < MIN_REVEALS_LEN:
                errors.append(
                    f"{prefix}: 'reveals' 过短({len(reveals)}字 < {MIN_REVEALS_LEN})。『揭示了什么』答不上 = 工程任务/重复验证,回炉"
                )
            elif reveals == (c.get("title") or "").strip():
                # title 同样 strip:标题带尾随空格不应绕过抄题检测
                errors.append(
                    f"{prefix}: 'reveals' 与标题完全相同——只是抄了题目,未回答『揭示了什么』,回炉"
                )

    return (len(errors) == 0, errors)


def check_anti_collapse(workdir: Path) -> tuple[bool, list[str]]:
    """反坍缩闸门(v0.3.4):校验 topic_scores.json 的 t_score/tier 字段 + 主推多样性。

    规则:
    1. 每个候选必须有 t_score(0-1)与 tier(枚举)。
    2. 3 个 decision=selected 主推必须覆盖 ≥ 2 个不同层级,且至少 1 个 t_score ≤ 0.50。
       全落安全层即「选题坍缩」→ FAIL,退回 Phase 2 重生成。
    """
    errors = []
    score_file = _resolve_workdir_file(workdir, "topic_scores.json")
    if not score_file.exists():
        return (False, ["topic_scores.json 不存在,无法做反坍缩校验"])

    try:
        data = json.loads(_read_text_utf8(score_file))
    except Utf8ArtifactError as e:
        return (False, [str(e)])
    except json.JSONDecodeError as e:
        return (False, [f"topic_scores.json 不是合法 JSON:{e}"])

    candidates = data.get("candidates", [])
    if len(candidates) != 5:
        return (False, [f"candidates 长度 {len(candidates)} ≠ 5(应 3 主推 + 2 备选)"])

    valid_tiers = {"safe", "differentiated", "innovative"}
    for i, c in enumerate(candidates):
        prefix = f"候选 #{i+1} ({c.get('label', '?')})"
        t_score = c.get("t_score")
        tier = c.get("tier")
        if t_score is None:
            errors.append(f"{prefix}: 缺少 't_score'(0-1 典型性分,反坍缩必填)")
            continue
        if not isinstance(t_score, (int, float)) or isinstance(t_score, bool):
            errors.append(f"{prefix}: 't_score' 不是数值")
            continue
        if not (0 <= t_score <= 1):
            errors.append(f"{prefix}: 't_score'={t_score} 不在 0-1 范围")
        if tier is None:
            errors.append(f"{prefix}: 缺少 'tier'(safe/differentiated/innovative)")
        elif tier not in valid_tiers:
            errors.append(f"{prefix}: 'tier'='{tier}' 非法,应为 safe/differentiated/innovative")
        elif 0 <= t_score <= 1 and (derived := _tier_of(t_score)) != tier:
            # 层级与分界不一致:提示但不断言(启发式标尺,防误杀)。
            # t_score 越界时 _tier_of 返回 out_of_band;上面的「不在 0-1 范围」
            # 已足够定位问题,不再追加「推导层级为…」的迷惑错。
            errors.append(
                f"{prefix}: 't_score'={t_score} 推导层级为 '{derived}',"
                f"与所填 '{tier}' 不一致(分界:" + " / ".join(
                    f"{t}:{lo}≤t<{hi}" for t, (lo, hi) in TIER_BANDS.items()
                ) + ";t≥0.80 归入模态区,由模态识别拦截)"
            )

    selected = [c for c in candidates if c.get("decision") == "selected"]
    if len(selected) != 3:
        errors.append(f"decision='selected' 的候选数 {len(selected)} ≠ 3(应 3 主推池)")
    else:
        tiers_used = {c.get("tier") for c in selected if c.get("tier") in valid_tiers}
        has_low = any(
            isinstance(c.get("t_score"), (int, float)) and not isinstance(c.get("t_score"), bool)
            and 0 <= c["t_score"] <= ANTI_COLLAPSE_LOW_TIER
            for c in selected
        )
        if len(tiers_used) < 2:
            errors.append(
                f"选题坍缩:3 主推层级集合 {sorted(tiers_used)} 只有 1 层,"
                "需覆盖 ≥ 2 层(如 safe + differentiated/innovative),退回 Step 3a Phase 2 重生成"
            )
        if not has_low:
            errors.append(
                "选题坍缩:3 主推均 T > 0.50(全落安全层)。"
                "至少 1 个主推 t_score ≤ 0.50(差异化/创新层),退回 Step 3a Phase 2 重生成"
            )

    return (len(errors) == 0, errors)


def check_review(workdir: Path, target: str) -> tuple[str, list[str], list[str]]:
    """校验 review_{target}.md 状态。

    v0.3.18 起降级为"过程建议":
    - 文件缺失 / 信任边界声明缺失 / reviewer ID 未替换 都不再视为硬错,只 WARN
    - verdict 缺失或值不在 {PASS, P0_OPEN, FAIL, NEEDS_HUMAN} 才视为硬错(FAIL)
    - verdict=FAIL 或 verdict=P0_OPEN 缺具体 P0 列表也只 WARN(用户已说"不行",无需机器拦)
    - verdict=PASS 但 reviewer 仍是模板占位符 <hash>,只 WARN(诚实声明这不算合规)
    """
    hard_errors: list[str] = []
    soft_warnings: list[str] = []
    review_file = _resolve_workdir_file(workdir, f"review_{target}.md")

    if not review_file.exists():
        soft_warnings.append(
            f"⚠️  review_{target}.md 不存在(过程建议,推荐跑 scripts/review.py --target {target} 后由独立 subagent 填 verdict);不阻塞交付"
        )
        return ("WARN", hard_errors, soft_warnings)

    try:
        content = _read_text_utf8(review_file)
    except Utf8ArtifactError as e:
        return ("FAIL", [str(e)], soft_warnings)

    # ----- 硬错:verdict 字段本身有问题 -----
    # 两段式:先宽捕获 verdict 值(在空白/中英文句读/markdown 符号处截断,
    # 避免把 "verdict: PASS,继续" 里的 ",继续" 一起吃进来),再校验合法集合。
    # 这样非法值(如 verdict: MAYBE)能报出「值 X 不在合法集合」,而不是误报「缺少字段」。
    # 取最后一次匹配:正文转述历史轮次(如「第 1 轮 verdict: FAIL」)先于最终结论出现,
    # 最近一次声明才是权威 verdict。
    verdict_matches = list(
        re.finditer(
            r"verdict\s*:\s*\**\s*\`?([^\s,，;；。\*\`]+)",
            content,
            re.IGNORECASE,
        )
    )
    verdict_row = verdict_matches[-1] if verdict_matches else None
    if not verdict_row:
        hard_errors.append(
            "review_" + target + ".md 缺少 verdict 字段(需 `verdict: PASS|P0_OPEN|FAIL|NEEDS_HUMAN`)"
        )
        return ("FAIL", hard_errors, soft_warnings)

    verdict = verdict_row.group(1).upper()
    if verdict not in REVIEW_VALID_VERDICTS:
        hard_errors.append(
            f"verdict 值 {verdict!r} 不在合法集合 {{PASS, P0_OPEN, FAIL, NEEDS_HUMAN}} 内(v0.3.18 起需要写明 verdict 类型)"
        )
        return ("FAIL", hard_errors, soft_warnings)

    # ----- 软警告 -----
    if verdict == "FAIL":
        soft_warnings.append(
            f"review_{target}.md verdict=FAIL(审查者明确拒收;推荐按其理由修后重审或重跑)"
        )

    if verdict == "P0_OPEN" and "P0-1" not in content and "P0-2" not in content:
        soft_warnings.append(
            f"review_{target}.md verdict=P0_OPEN 但未列出具体 P0 问题(推荐补 P0-1 / P0-2 等条目)"
        )

    if verdict == "NEEDS_HUMAN":
        soft_warnings.append(
            f"review_{target}.md verdict=NEEDS_HUMAN(独立 subagent 自承拿不准,推荐人类专家复核)"
        )

    if "reviewer" not in content.lower():
        soft_warnings.append(
            f"review_{target}.md 缺审查者 ID(可填 reviewer-<hash> 占位)"
        )

    if "密码学身份保证" not in content and "信任边界" not in content:
        soft_warnings.append(
            f"review_{target}.md 缺信任边界声明(v0.3.18 推荐保留,即使不做密码学保证)"
        )

    # verdict=PASS 但 reviewer 仍是模板占位符 <hash> —— 这本是合规问题,降级为软警告
    if re.search(r"reviewer-<hash>", content) and verdict == "PASS":
        soft_warnings.append(
            f"review_{target}.md verdict=PASS 但 reviewer 仍是模板占位符 <hash>(诚实声明:不可作合规依据,只作过程留痕)"
        )

    if hard_errors:
        return ("FAIL", hard_errors, soft_warnings)
    if soft_warnings:
        return ("WARN", hard_errors, soft_warnings)
    return ("PASS", hard_errors, soft_warnings)


# check_step6_quality 见文件头部第 23 行(F811 提示该函数被重复定义;
# 此处仅为模块结尾的 __all__ 占位,真正实现统一收敛于上方单一版本)

