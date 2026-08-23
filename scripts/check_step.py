#!/usr/bin/env python3
"""
选题工坊 · 刚性闸门检查脚本 (版本号动态读取自 SKILL.md)

校验每个 Step 产物的完整性、关键字段、最小内容长度。
Step 6 额外校验主报告质量:附录结构、矩阵表行、段落深度、禁模板占位符。

支持:
  --step 1/2a/2b/2c/3a/3b/4/5/6      单 Step 校验
  --step all                         一次性校验全部(含 review)
  --step scores                      topic_scores.json 校验(含反坍缩 t_score/tier)
  --step scan-review                 review_scan.md 校验
  --step topics-review               review_topics.md 校验

用法:
  python scripts/check_step.py --workdir <dir> --step <step>
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path


def _self_version() -> str:
    """从仓库根 SKILL.md frontmatter 读取版本号(唯一真源),避免硬编码滞后。

    与 check-ready.sh 的 SELF_VERSION 同源,防止脚本 banner 与仓库版本漂移。
    """
    skill = Path(__file__).resolve().parent.parent / "SKILL.md"
    try:
        text = skill.read_text(encoding="utf-8")
    except Exception:
        return "unknown"
    m = re.search(r'^version:\s*["\']?([^"\'\s]+)["\']?\s*$', text, re.MULTILINE)
    return m.group(1) if m else "unknown"


# 每个 Step 的闸门校验规则
GATES = {
    "1": {
        "file": "Step1-input.md",
        "min_lines": 5,
        "required_keywords": ["模糊领域", "文献清单"],
        "fail_msg": "Step 1: 输入清单缺少'模糊领域'或'文献清单'字段",
    },
    "2a": {
        "file": "Step2a-points.md",
        "min_lines": 10,
        "required_keywords": ["研究问题", "主要发现"],
        "fail_msg": "Step 2a: 文献要点卡缺少'研究问题'或'主要发现'",
    },
    "2b": {
        "file": "Step2b-literature-matrix.md",
        "min_lines": 5,
        "required_keywords": ["作者", "年份", "方法", "主要发现"],
        "fail_msg": "Step 2b: 文献矩阵缺少关键字段(作者/年份/方法/主要发现)",
    },
    "2c": {
        "file": "Step2c-gap-verdicts.md",
        "min_lines": 8,
        "required_keywords": ["gap", "证据来源", "重要性"],
        "fail_msg": "Step 2c: Gap 裁定缺少'证据来源'或'重要性'字段",
        "ban_placeholders": True,
    },
    "3a": {
        "file": "Step3a-candidate-themes.md",
        "min_lines": 15,
        "required_keywords": ["主推", "备选", "理论贡献", "方法可行性", "研究类型", "模态识别", "揭示了什么"],
        "min_count": {
            "主推": 3,
            "备选": 2,
            "研究类型": 5,
            "揭示了什么": 5,
        },
        "fail_msg": "Step 3a: 候选主题格式不对。需要 3 主推 + 2 备选,各含理论贡献 + 方法可行性 + 研究类型 + 揭示了什么(贡献类型门);且须含「模态识别」小节(反坍缩 Phase 1)",
    },
    "3b": {
        "file": "Step3b-selected-theme.md",
        "min_lines": 5,
        "required_keywords": ["研究问题", "理论贡献", "研究类型"],
        "fail_msg": "Step 3b: 选定主题缺少关键字段",
    },
    "4": {
        "file": "Step4-hypotheses.md",
        "min_lines": 15,
        "required_keywords": ["假设", "DAG", "反事实", "可证伪", "SESOI", "三层假设闸"],
        "min_count": {
            "假设陈述": 3,
        },
        "fail_msg": "Step 4: 假设文件缺少'三层假设闸(结论优先/金句/最险假设)/假设陈述/DAG/反事实/可证伪/SESOI'字段,或假设数 < 3",
        "ban_placeholders": True,
    },
    "5": {
        "file": "Step5-identification-strategy.md",
        "min_lines": 10,
        # 工具变量不再强制:纯 DID 可写「本节不适用」
        "required_keywords": ["识别策略", "稳健性"],
        "fail_msg": "Step 5: 因果识别策略缺少'识别策略/稳健性'字段",
    },
    "6": {
        "file": "00_研究计划报告.md",
        "min_lines": 120,
        "required_keywords": [
            "选的题是什么",
            "为什么选这个题",
            "选题的意义",
            "假设是什么",
            "为什么能写出这样的假设",
            "后面应该怎么做",
            "可证伪",
            "文献矩阵",
            "Gap",
            "Gap 判定方法",
            "证据链",
            "威胁文献",
            "附录 A",
            "附录 B",
            "附录 C",
            "附录 D",
            "附录 E",
        ],
        "fail_msg": "Step 6: 缺少 00_研究计划报告.md,或未按六段+整合附录框架撰写。附录 C 须含「Gap 判定方法」段(反黑箱)+「威胁文献清单」段,见 delivery-spec §3.1",
    },
}


SCORE_KEYS = [
    "importance",
    "feasibility",
    "falsifiability",
    "evidence_leverage",
    "originality",
    "negative_value",
]

VALID_STEPS = list(GATES.keys()) + ["all", "scores", "scan-review", "topics-review"]

# 模板/空壳残留(出现则 FAIL)
PLACEHOLDER_PATTERNS = [
    r"<请填写",
    r"<YYYY-MM-DD>",
    r"<研究主题>",
    # 通用中文占位符收紧:v0.3.17 起 4 汉字起步(原 1 字起步 → v0.3.16 通用匹配,
    # 误判 "<文献>" "<用户>" 等合法正文)。关键词白名单兜底 1-3 字占位符。
    # 全部来自 init_project.py 生成的模板,填充前不得通过闸门。
    r"<[一-鿿]{4,}[^>]*>",
    # 关键词白名单:即使 < 4 字或含空格/Gap 等混合占位符也强制拦。
    # 覆盖 init 模板家族(<来源 Gap 编号> / <Gap 编号> / <研究类型 标签> / <填这里> 等)。
    r"<[^>]*?(?:候选主题|候选标题|用户文献目录|来源\s*Gap|具体哪几篇|这个题揭示了|推断性研究才填|证据来源|研究类型\s*标签|Gap\s*编号|填哪几篇|填这里|填什么|填进去|标题雷同|题揭示|待填|请填写)[^>]*?>",
    r"\bTODO\b",
    r"\bTBD\b",
    r"（待填）",
    r"\(待填\)",
    r"请填写或修改",
    r"由 `?init_project\.py`? 自动生成",
]
def _count_cjk_and_alnum(text: str) -> int:
    """粗算有效字符数(中日韩 + 字母数字)。"""
    return len(re.findall(r"[\u4e00-\u9fffA-Za-z0-9]", text))


def _extract_section(content: str, heading_substr: str, next_headings: list[str]) -> str:
    """按标题子串截取章节正文,直到下一个一级/二级标题候选。"""
    # 找含 heading_substr 的 markdown 标题行
    lines = content.splitlines()
    start = None
    for i, line in enumerate(lines):
        if line.lstrip().startswith("#") and heading_substr in line:
            start = i + 1
            break
    if start is None:
        return ""
    end = len(lines)
    for j in range(start, len(lines)):
        line = lines[j]
        if not line.lstrip().startswith("#"):
            continue
        # 遇到其他六段标题或附录标题则停
        for nh in next_headings:
            if nh in line and heading_substr not in line:
                end = j
                return "\n".join(lines[start:end])
        if re.match(r"^#{1,2}\s+", line) and j > start:
            # 同级或更高级标题
            level = len(line) - len(line.lstrip("#"))
            start_line = lines[start - 1]
            start_level = len(start_line) - len(start_line.lstrip("#"))
            if level <= start_level and heading_substr not in line:
                end = j
                break
    return "\n".join(lines[start:end])


def _count_paragraphs(section: str) -> int:
    """非空段落数(空行分隔,且不是纯表格行/纯标题)。"""
    chunks = re.split(r"\n\s*\n", section.strip())
    n = 0
    for c in chunks:
        c = c.strip()
        if not c:
            continue
        if c.startswith("#"):
            continue
        # 纯表格块不算论述段落
        rows = [ln for ln in c.splitlines() if ln.strip()]
        if rows and all(ln.strip().startswith("|") for ln in rows):
            continue
        if _count_cjk_and_alnum(c) >= 40:
            n += 1
    return n


def _count_matrix_data_rows(content: str) -> int:
    """
    统计文献矩阵数据行。
    优先:附录 A 区域内 | L1 | / | L2 | 或首列像文献 ID 的表行;
    回退:全文 markdown 表中非表头、非分隔行。
    """
    # 截取附录 A
    appendix = content
    m = re.search(r"附录\s*A[^\n]*\n([\s\S]*?)(?=\n##\s*附录\s*B|\n#\s*附录\s*B|\Z)", content)
    if m:
        appendix = m.group(1)

    rows = 0
    for line in appendix.splitlines():
        s = line.strip()
        if not s.startswith("|"):
            continue
        if re.match(r"^\|?\s*:?-+:?\s*\|", s):
            continue
        # 表头
        if "作者" in s and "年份" in s:
            continue
        if re.match(r"^\|\s*ID\s*\|", s, re.I):
            continue
        # 数据行:含 L1/L2… 或至少 5 个单元格
        cells = [c.strip() for c in s.strip("|").split("|")]
        if len(cells) < 5:
            continue
        if re.search(r"\bL\d+\b", s) or (cells[0] and cells[0] not in ("ID", "编号", "—", "-")):
            # 排除仍是表头变体
            if cells[0] in ("作者", "文献", "字段"):
                continue
            rows += 1
    return rows


def check_placeholders(content: str, label: str) -> list[str]:
    errors = []
    for pat in PLACEHOLDER_PATTERNS:
        if re.search(pat, content):
            errors.append(f"{label}: 含模板/占位残留,匹配 /{pat}/")
    return errors


def _resolve_workdir_file(workdir: Path, filename: str) -> Path:
    """按「根目录 → process/ 子目录」顺序解析工作目录产物文件路径。

    金样例把 Step*/topic_scores/review_* 放在 process/ 子目录(主交付 00_* 在根),
    脚本历史上只查根目录,导致已存在的过程文件无法复验。此 helper 统一回退:
    根目录有则用根目录,否则回退 process/,两者皆无则返回根目录路径(由调用方报错)。
    """
    root = workdir / filename
    if root.exists():
        return root
    sub = workdir / "process" / filename
    return sub if sub.exists() else root


def check_step6_quality(content: str) -> list[str]:
    """Step 6 主报告质量闸(防空壳)。"""
    errors = []
    errors.extend(check_placeholders(content, "Step6 主报告"))

    # 附录标题
    for app in ["附录 A", "附录 B", "附录 C", "附录 D", "附录 E"]:
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
    next_heads = [h for h, _, _ in six] + ["附录 A", "附录 B", "整合附录"]

    for heading, min_chars, min_paras in six:
        sec = _extract_section(content, heading, next_heads)
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


# 5 闸交互留痕校验(v0.3.9):interaction-log.md 须含 5 闸各自至少 1 条用户确认记录(原话)
REQUIRED_GATES = ["#1", "#2", "#3", "#4", "#5"]


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
                "interaction-log.md 不存在。5 闸确认必须留痕(每闸一条用户原话),"
                "否则视为未交互,禁止交付。用 init_project.py 生成模板,或补记确认记录"
            ],
        )

    content = log_file.read_text(encoding="utf-8")
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
        if not quote or "<" in quote or "待填" in quote:
            continue  # 占位符不算确认
        for g in REQUIRED_GATES:
            if re.search(rf"(?:CP)?{re.escape(g)}\b", gate):
                confirmed.setdefault(g, []).append(quote)

    missing = [g for g in REQUIRED_GATES if g not in confirmed]
    if missing:
        errors.append(
            f"交互留痕不足:闸门 {', '.join(missing)} 无用户确认记录(interaction-log.md)。"
            "5 闸须各至少 1 条用户原话;未确认的闸门 = 未交互,禁止交付"
        )

    return (len(errors) == 0, errors)


# 复跑契约收紧(v0.3.10):附录 F 决策表不再是复跑授权;复跑记录必须含当次原话
RERUN_PHRASES = ["按上次", "复跑", "不要再问", "沿用"]

# 复跑声明(精确模式):只认「本次运行是复跑」的声明位
# 「需复跑核实」「复跑核实」是威胁文献清单的语义(要再查证),不是复跑模式声明,不匹配
# 附录 F 表行「| 复跑 | 否」表示当次新跑,不是复跑声明,排除
RERUN_DECLARE_PATTERNS = [
    r"复跑说明",                 # 顶部复跑说明
    r"本复跑",                   # 正文/附录叙事「本复跑…」
    r"\|\s*复跑\s*\|\s*(?!\s*否)",  # 附录 F 表格行 | 复跑 | (值非「否」)
]


def check_rerun_record(workdir: Path, main_report_path: Path) -> tuple[bool, list[str]]:
    """校验复跑授权合法性。

    规则:
    1. 主报告附录 F 声明「复跑」但无 00_复跑决策记录.md → FAIL(附录 F 只是历史记录,不是当次授权)
    2. 00_复跑决策记录.md 存在但只有模板/占位符(无当次原话、无时间)→ FAIL(空壳拦截)
    """
    errors = []
    rerun_file = _resolve_workdir_file(workdir, "00_复跑决策记录.md")
    main_report = main_report_path.read_text(encoding="utf-8") if main_report_path.exists() else ""

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

    content = rerun_file.read_text(encoding="utf-8")
    has_quote = any(p in content for p in RERUN_PHRASES)
    has_time = bool(re.search(r"\d{4}-\d{2}-\d{2}|\d{4}/\d{1,2}/\d{1,2}", content))
    is_empty = len(content.strip()) < 30 or "待填" in content or "<" in content

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


BODY_JARGON = [
    r"GAP-[A-Za-z][0-9A-Za-z]*",  # GAP 编号
    r"\bt_score\b",  # 典型性评分
    r"evidence_leverage",
    r"negative_value",
    r"feasibility\s*=",
    r"topic_scores",
    r"反坍缩",
    r"Checkpoint",
    r"\bSESOI\b",
    r"（探索性）",
]

# 正文句子最大长度(以 。；为界),超过即 FAIL(断句规则)
MAX_BODY_SENTENCE = 100


def _strip_md_structure(text: str) -> str:
    """剥离 markdown 结构行(标题/表格/代码块/公式块/分隔线/列表标记/引用标记),只留真散文。"""
    lines = text.splitlines()
    out = []
    in_code = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("```"):
            in_code = not in_code
            continue
        if in_code:
            continue
        if re.match(r"^#{1,6}\s", stripped):  # 标题
            continue
        if re.match(r"^---+\s*$", stripped):  # 分隔线
            continue
        if stripped.startswith("|"):  # 表格行
            continue
        if stripped.startswith("\\[") or stripped.startswith("\\]"):  # LaTeX 公式块
            continue
        if re.search(r"\\[a-zA-Z]+", stripped):  # LaTeX 公式内容行(如 \beta1 GC{it}...)
            continue
        if stripped.startswith(">"):  # 引用:去标记保留内容
            out.append(re.sub(r"^>\s?", "", line))
            continue
        # 列表行:去列表标记,保留内容
        out.append(re.sub(r"^([-*]\s|\d+\.\s)", "", stripped))
    joined = "\n".join(out)
    # 去行内 markdown 符号,避免计数字符虚高
    return re.sub(r"[`*_]", "", joined)


def check_readability(content: str) -> list[str]:
    """可读性闸门:正文(开头→「# 整合附录」前)反黑话 + 断句。附录为技术对照区,豁免。"""
    errors = []
    idx = content.find("# 整合附录")
    body = content if idx == -1 else content[:idx]

    # 1. 黑话禁止
    for pat in BODY_JARGON:
        hits = re.findall(pat, body)
        if hits:
            errors.append(
                f"Step6: 正文出现内部术语「{pat}」×{len(hits)}(如 {hits[:2]})。"
                "主报告是给读者/导师看的,须按 delivery-spec §3.3 术语翻译表改成人话;编号只在附录 C 对照"
            )

    # 2. 断句(超长句)——逐行测句长,避免跨行合并(标题+段/引用块+列表/公式拼成一坨)
    prose = _strip_md_structure(body)
    long_sentences = []
    for line in prose.splitlines():
        line = line.strip()
        if not line:
            continue
        for piece in re.split(r"[。；？]", line):
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
        data = json.loads(score_file.read_text(encoding="utf-8"))
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
            elif not isinstance(scores[key], int):
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
            if len(reveals) < 8:
                errors.append(
                    f"{prefix}: 'reveals' 过短({len(reveals)}字 < 8)。『揭示了什么』答不上 = 工程任务/重复验证,回炉"
                )
            elif reveals == c.get("title"):
                errors.append(
                    f"{prefix}: 'reveals' 与标题完全相同——只是抄了题目,未回答『揭示了什么』,回炉"
                )

    return (len(errors) == 0, errors)


# T-Score 典型性分界(与 references/anti-collapse.md 一致)
TIER_BANDS = {
    "safe": (0.55, 0.81),  # 0.55 ≤ t < 0.81
    "differentiated": (0.35, 0.55),
    "innovative": (0.0, 0.35),
}


def _tier_of(t_score: float) -> str:
    """由 t_score 推导层级(与 anti-collapse.md 分界一致)。"""
    for tier, (lo, hi) in TIER_BANDS.items():
        if lo <= t_score < hi:
            return tier
    return "safe"  # t ≥ 0.81 一律视为模态/安全层


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
        data = json.loads(score_file.read_text(encoding="utf-8"))
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
        elif _tier_of(t_score) != tier:
            # 层级与分界不一致:提示但不断言(启发式标尺,防误杀)
            errors.append(
                f"{prefix}: 't_score'={t_score} 推导层级为 '{_tier_of(t_score)}',"
                f"与所填 '{tier}' 不一致(0.55≤safe<0.81 / 0.35≤differentiated<0.55 / <0.35 innovative)"
            )

    selected = [c for c in candidates if c.get("decision") == "selected"]
    if len(selected) != 3:
        errors.append(f"decision='selected' 的候选数 {len(selected)} ≠ 3(应 3 主推池)")
    else:
        tiers_used = {c.get("tier") for c in selected if c.get("tier") in valid_tiers}
        has_low = any(
            isinstance(c.get("t_score"), (int, float)) and not isinstance(c.get("t_score"), bool)
            and 0 <= c["t_score"] <= 0.50
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


# v0.3.18 审查降级:从"刚性闸门"降为"过程建议"
# 返回 (status, hard_errors, soft_warnings)
#   status=PASS   无硬错,verdict 字段有效
#   status=WARN   无硬错,但有软警告(如文件缺失、verdict=FAIL、P0 缺具体项)
#   status=FAIL   有硬错(verdict 字段缺失、值非法)
# 调用方应只把 status=FAIL 视为阻塞;WARN 仅打印提示,不阻塞 --step all
REVIEW_VALID_VERDICTS = {"PASS", "P0_OPEN", "FAIL", "NEEDS_HUMAN"}


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

    content = review_file.read_text(encoding="utf-8")

    # ----- 硬错:verdict 字段本身有问题 -----
    # 先用宽正则抓"verdict: <任何非空白串>"行,再判断值是否合法
    verdict_row = re.search(
        r"verdict\s*:\s*\**\s*\`?\s*([^\s\*\`]+)\s*\`?",
        content,
        re.IGNORECASE,
    )
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

    if verdict == "P0_OPEN":
        if "P0-1" not in content and "P0-2" not in content:
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


def check_step(workdir: str, step: str) -> tuple[bool, list[str]]:
    """检查单个 step 的产物完整性。返回 (passed, errors)。"""
    workdir_path = Path(workdir)

    if step == "all":
        all_errors = []
        for s in ["1", "2a", "2b", "2c", "3a", "3b", "4", "5", "6"]:
            passed, errors = check_step(workdir, s)
            if not passed:
                all_errors.extend([f"[step {s}] {e}" for e in errors])
        ts_passed, ts_errors = check_topic_scores(workdir_path)
        if not ts_passed:
            all_errors.extend([f"[topic_scores.json] {e}" for e in ts_errors])
        ac_passed, ac_errors = check_anti_collapse(workdir_path)
        if not ac_passed:
            all_errors.extend([f"[反坍缩] {e}" for e in ac_errors])
        il_passed, il_errors = check_interaction_log(workdir_path)
        if not il_passed:
            all_errors.extend([f"[交互留痕] {e}" for e in il_errors])
        main_report = _resolve_workdir_file(workdir_path, "00_研究计划报告.md")
        if main_report.exists():
            rr_passed, rr_errors = check_rerun_record(workdir_path, main_report)
            if not rr_passed:
                all_errors.extend([f"[复跑授权] {e}" for e in rr_errors])
        # v0.3.18 审查降级:review 缺失/警告不再阻塞 --step all,仅做过程留痕
        for rt in ["scan", "topics"]:
            r_status, r_hard, r_soft = check_review(workdir_path, rt)
            if r_status == "FAIL":
                all_errors.extend([f"[review_{rt}.md] {e}" for e in r_hard])
            elif r_soft:
                # 软警告写到 stderr 风格前缀,便于 grep,但不算错
                for w in r_soft:
                    print(f"[review_{rt}.md] {w}", file=sys.stderr)
        return (len(all_errors) == 0, all_errors)

    if step == "scores":
        ts_passed, ts_errors = check_topic_scores(workdir_path)
        ac_passed, ac_errors = check_anti_collapse(workdir_path)
        combined = ts_errors + ac_errors
        return (ts_passed and ac_passed, combined)

    if step == "scan-review":
        # v0.3.18 审查降级:3-tuple,只在 FAIL 时 sys.exit(1);WARN 仍返回 True
        status, hard, soft = check_review(workdir_path, "scan")
        if soft:
            for w in soft:
                print(w, file=sys.stderr)
        if status == "FAIL":
            return (False, hard)
        return (True, [] if status == "PASS" else hard)  # WARN 也算过(只打印)

    if step == "topics-review":
        status, hard, soft = check_review(workdir_path, "topics")
        if soft:
            for w in soft:
                print(w, file=sys.stderr)
        if status == "FAIL":
            return (False, hard)
        return (True, [] if status == "PASS" else hard)

    if step not in GATES:
        return (False, [f"未知 step: {step}。合法 step: {', '.join(VALID_STEPS)}"])

    rule = GATES[step]
    file_path = _resolve_workdir_file(workdir_path, rule["file"])
    errors = []

    if not file_path.exists():
        return (False, [f"{rule['fail_msg']}\n  文件不存在:{file_path}(根目录与 process/ 均未找到)"])

    content = file_path.read_text(encoding="utf-8")
    lines = content.splitlines()

    if len(lines) < rule["min_lines"]:
        errors.append(
            f"{rule['fail_msg']}\n  文件行数 {len(lines)} < 最小要求 {rule['min_lines']}"
        )

    for kw in rule["required_keywords"]:
        if kw not in content:
            errors.append(f"缺少关键词: '{kw}'")

    if "min_count" in rule:
        for kw, min_n in rule["min_count"].items():
            count = content.count(kw)
            if count < min_n:
                errors.append(f"'{kw}' 出现 {count} 次,要求 ≥ {min_n} 次")

    if rule.get("ban_placeholders"):
        errors.extend(check_placeholders(content, f"Step {step}"))

    if step == "3a":
        ts_passed, ts_errors = check_topic_scores(workdir_path)
        if not ts_passed:
            errors.append("--- topic_scores.json 校验失败 ---")
            errors.extend(ts_errors)
        ac_passed, ac_errors = check_anti_collapse(workdir_path)
        if not ac_passed:
            errors.append("--- 反坍缩校验失败 ---")
            errors.extend(ac_errors)

    if step == "3b" and "对抗压测" in content:
        # 半强校验(v0.3.12):启用对抗压测就必须做完整;未启用不拦
        # 新格式:生存标签 + 至少 6 类坍缩攻击名(经管语境)
        attack_kw = ["换情境", "换术语", "识别", "已被占", "不可证伪",
                     "范围过宽", "数据质量", "不可行", "贡献类型"]
        survival_kw = ["存活", "需收窄", "需转向", "坍缩"]
        has_survival = any(k in content for k in survival_kw)
        hit = sum(1 for k in attack_kw if k in content)
        new_style_ok = has_survival and hit >= 6
        # 旧格式(v0.3.6)兼容:魔鬼代言 + 最可能被拒 + 回应
        old_style_ok = all(k in content for k in ["魔鬼代言", "最可能被", "回应"])
        if not (new_style_ok or old_style_ok):
            detail = ""
            if not has_survival:
                detail += "缺少四档生存标签(存活/需收窄/需转向/坍缩)。"
            if hit < 6:
                detail += f"9 类攻击仅命中 {hit}/9(换情境/换术语/识别/已被占/不可证伪/范围过宽/数据质量/不可行/贡献类型),至少攻击 6 类。"
            errors.append(f"Step 3b 已含「对抗压测」小节,但未做完整:{detail}启用即做完整:每条攻击给 1 句回应 + 打 1 个生存标签")

    if step == "6":
        errors.extend(check_step6_quality(content))
        il_passed, il_errors = check_interaction_log(workdir_path)
        if not il_passed:
            errors.append("--- 交互留痕校验失败(5 闸须有用户确认原话,禁止未交互交付)---")
            errors.extend(il_errors)
        rr_passed, rr_errors = check_rerun_record(workdir_path, file_path)
        if not rr_passed:
            errors.append("--- 复跑授权校验失败 ---")
            errors.extend(rr_errors)

    # 2c 额外:至少 3 条证据来源
    if step == "2c":
        if content.count("证据来源") < 3:
            errors.append("Step 2c:「证据来源」出现 < 3 次(Gap 条数过少或未展开)")
        errors.extend(check_placeholders(content, "Step 2c"))

    return (len(errors) == 0, errors)


def main():
    VERSION = _self_version()
    parser = argparse.ArgumentParser(description=f"选题工坊 · 刚性闸门检查 v{VERSION}")
    parser.add_argument("--workdir", "-w", required=True, help="工作目录(产出文件所在)")
    parser.add_argument("--step", "-s", required=True, help=f"Step 编号:{', '.join(VALID_STEPS)}")
    args = parser.parse_args()

    if not os.path.isdir(args.workdir):
        print(f"❌ 目录不存在:{args.workdir}")
        sys.exit(1)

    passed, errors = check_step(args.workdir, args.step)

    if passed:
        print(f"✅ Step {args.step} PASS")
        sys.exit(0)

    print(f"❌ Step {args.step} FAIL")
    for err in errors:
        print(f"  - {err}")
    print()
    print("修复建议:")
    print("  1. 重新跑对应 step 的子命令")
    print("  2. 按上面错误信息补全缺失字段/加厚论述/补附录矩阵")
    print("  3. 再跑一次:python scripts/check_step.py --workdir <dir> --step " + args.step)
    sys.exit(1)


if __name__ == "__main__":
    main()
