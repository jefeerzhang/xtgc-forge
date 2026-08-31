#!/usr/bin/env python3
"""
选题工坊 · 机器闸门检查脚本 (版本号动态读取自 SKILL.md;v0.3.18 起审查降级为过程建议)

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
from typing import Callable

import md_doc  # 文档解析深 module:切分语义唯一来源(标题树/附录范围/正文/散文提取)
import templates  # 模板契约深 module:模板字面量与其占位符拦截规则同址


# === 模块常量(闸门阈值 / 可读性边界)===
# 反坍缩:至少 1 个主推 t_score ≤ 此值,防止 3 主推全落安全层
ANTI_COLLAPSE_LOW_TIER = 0.50
# 复跑决策记录:去除空白后 < 此值视为空壳拦截
RERUN_EMPTY_THRESHOLD = 30
# 贡献类型门:reveals 字段最短字数
MIN_REVEALS_LEN = 8
# 正文段落最小有效字符数(用于 _count_paragraphs 过滤纯标题/纯表格/纯占位的伪段)
MIN_PARAGRAPH_CHARS = 40
# 正文句子最大长度(以 。；？！为界),超过即 FAIL(断句规则)
MAX_BODY_SENTENCE = 100


def _force_utf8_stdio() -> None:
    """强制 stdout/stderr 走 UTF-8(管道重定向时 Windows 默认 cp936,
    ✅/❌ 等 emoji 会抛 UnicodeEncodeError,导致 PASS 也以退出码 1 结束)。
    输出消费方(Claude Code / 测试)统一按 UTF-8 解码。"""
    for stream in (sys.stdout, sys.stderr):
        if stream is not None and hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")


def _read_text_utf8(path: Path) -> str:
    """读产物文件;非 UTF-8(常见:编辑器存成 GBK/ANSI)时给可操作的提示。"""
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        print(
            f"❌ {path.name} 不是有效的 UTF-8 文本(可能被存成了 GBK/ANSI)。"
            f"请将其转存为 UTF-8 后重试。({exc})",
            file=sys.stderr,
        )
        sys.exit(1)


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
            "附录 F",
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
    # ① 模板契约(派生自 templates.py——模板与其占位符同址,
    #    不再手写第二份副本;模板改了,拦截规则自动跟随)
    *templates.placeholder_patterns(),
    # ② 通用规则(用户自造占位符的闸语义,与模板契约正交)。
    # 通用中文占位符收紧:v0.3.17 起 4 汉字起步(原 1 字起步 → v0.3.16 通用匹配,
    # 误判 "<文献>" "<用户>" 等合法正文)。
    r"<[一-鿿]{4,}[^>]*>",
    r"<请填写",
    r"\bTODO\b",
    r"\bTBD\b",
    r"（待填）",
    r"\(待填\)",
    # ③ 模板家族关键词兑底:覆盖旧版模板 token 与短于 4 汉字、②拦不到的变体。
    # 来源是模板家族词汇而非具体模板文本——当前模板的精确拦截已由 ① 派生保证。
    r"<[^>]*?(?:候选主题|候选标题|用户文献目录|来源\s*Gap|具体哪几篇|这个题揭示了|推断性研究才填|证据来源|研究类型\s*标签|Gap\s*编号|填哪几篇|填这里|填什么|填进去|标题雷同|题揭示|待填|请填写)[^>]*?>",
]
# 组合正则:用于「含任一模板占位符」的快速判定(如复跑决策记录空壳拦截)
PLACEHOLDER_PATTERNS_RE = re.compile("|".join(PLACEHOLDER_PATTERNS))
def _count_cjk_and_alnum(text: str) -> int:
    """粗算有效字符数(中日韩 + 字母数字)。"""
    return len(re.findall(r"[\u4e00-\u9fffA-Za-z0-9]", text))


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
        if _count_cjk_and_alnum(c) >= MIN_PARAGRAPH_CHARS:
            n += 1
    return n


def _is_table_separator(s: str) -> bool:
    """markdown 表格分隔行(| --- | --- | 等)。"""
    return bool(re.match(r"^\|?\s*:?-+:?\s*\|", s.strip()))


def _count_matrix_data_rows(content: str) -> int:
    """
    统计文献矩阵数据行。
    优先:附录 A 区域内 | L1 | / | L2 | 或首列像文献 ID 的表行;
    回退:全文 markdown 表中非表头、非分隔行。
    """
    # 截取附录 A(标题优先、文本标记回退,语义集中在 md_doc)
    appendix = md_doc.appendix_range(content, "A") or content
    lines = appendix.splitlines()

    rows = 0
    for i, line in enumerate(lines):
        s = line.strip()
        # Markdown 表格行:首尾必须是 |
        if not s.startswith("|") or not s.endswith("|"):
            continue
        if _is_table_separator(s):
            continue
        # markdown 表头行恒是其下紧跟的分隔行:该行是表头,不是文献数据行。
        # (首列常见「序号/文献编号/文献标识」等表头不在下方白名单内,不靠白名单判定。)
        nxt = lines[i + 1].strip() if i + 1 < len(lines) else ""
        if _is_table_separator(nxt):
            continue
        # 数据行:含 L1/L2… 或至少 5 个单元格
        cells = [c.strip() for c in s.strip("|").split("|")]
        if len(cells) < 5:
            continue
        # 表头判定:整行同时含「作者」+「年份」(分列形式)
        if "作者" in s and "年份" in s:
            continue
        # 表头判定:首格同时含「作者」+「年份」(合并表头 / 多列合一)
        first = cells[0]
        if "作者" in first and "年份" in first:
            continue
        # 表头白名单:ID / 编号 / — / -
        if first in ("ID", "编号", "—", "-"):
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

    content = _read_text_utf8(log_file)
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
    main_report = _read_text_utf8(main_report_path) if main_report_path.exists() else ""

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

    content = _read_text_utf8(rerun_file)
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
    # 探索性括号:同时匹配 ASCII (探索性) 与全角 （探索性）,防止半全角混写漏报
    r"(?:[\(（]\s*探索性\s*[\)）])",
]

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


# T-Score 典型性分界(与 references/anti-collapse.md 一致:≥0.80 为模态区,应避免)
TIER_BANDS = {
    "safe": (0.55, 0.80),  # 0.55 ≤ t < 0.80
    "differentiated": (0.35, 0.55),
    "innovative": (0.0, 0.35),
}


def _tier_of(t_score: float) -> str:
    """由 t_score 推导层级(与 anti-collapse.md 分界一致)。

    越界(< 0 或 > 1)直接抛 ValueError,不再静默回退到 "safe"。
    静默回退会让 check_anti_collapse 同时报「tier 非法」和「推导层级为 safe」两条
    互相矛盾的消息,反而更难定位 bug。
    """
    if t_score < 0 or t_score > 1:
        raise ValueError(f"t_score={t_score} 不在 0-1 范围")
    for tier, (lo, hi) in TIER_BANDS.items():
        if lo <= t_score < hi:
            return tier
    return "safe"  # t ≥ 0.80 落入模态区;candidate 层级枚举无 modal,归为 safe(模态题由 Phase 1 模态识别拦截)


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
            # t_score 越界时 _tier_of 会抛 ValueError;此时上面的「不在 0-1 范围」
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

    content = _read_text_utf8(review_file)

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


def _check_step_2c(workdir_path: Path, content: str, file_path: Path, _from_all: bool) -> list[str]:
    """Step 2c 额外校验:「证据来源」≥ 3 条 + 占位符拦截。"""
    errors: list[str] = []
    if content.count("证据来源") < 3:
        errors.append("Step 2c:「证据来源」出现 < 3 次(Gap 条数过少或未展开)")
    errors.extend(check_placeholders(content, "Step 2c"))
    return errors


def _check_step_3a(workdir_path: Path, content: str, file_path: Path, _from_all: bool) -> list[str]:
    """Step 3a 额外校验:topic_scores.json + 反坍缩(_from_all 时由 --step all 顶层统一调用,跳过以避免双前缀)。"""
    errors: list[str] = []
    if _from_all:
        return errors
    ts_passed, ts_errors = check_topic_scores(workdir_path)
    if not ts_passed:
        errors.append("--- topic_scores.json 校验失败 ---")
        errors.extend(ts_errors)
    ac_passed, ac_errors = check_anti_collapse(workdir_path)
    if not ac_passed:
        errors.append("--- 反坍缩校验失败 ---")
        errors.extend(ac_errors)
    return errors


def _check_step_3b(workdir_path: Path, content: str, file_path: Path, _from_all: bool) -> list[str]:
    """Step 3b 额外校验:对抗压测小节(半强校验)。启用即做完整。"""
    if "对抗压测" not in content:
        return []
    errors: list[str] = []
    # 新格式(v0.3.12):生存标签 + 至少 6 类坍缩攻击名(经管语境)
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
    return errors


def _check_step_6(workdir_path: Path, content: str, file_path: Path, _from_all: bool) -> list[str]:
    """Step 6 额外校验:主报告质量 + 交互留痕 + 复跑授权(_from_all 时由 --step all 顶层统一调用交互/复跑)。"""
    errors: list[str] = []
    errors.extend(check_step6_quality(content))
    if _from_all:
        return errors
    il_passed, il_errors = check_interaction_log(workdir_path)
    if not il_passed:
        errors.append("--- 交互留痕校验失败(5 闸须有用户确认原话,禁止未交互交付)---")
        errors.extend(il_errors)
    rr_passed, rr_errors = check_rerun_record(workdir_path, file_path)
    if not rr_passed:
        errors.append("--- 复跑授权校验失败 ---")
        errors.extend(rr_errors)
    return errors


# Per-step extra 规则分发:key=step 名,value=调用 (workdir, content, file_path, _from_all) 返回 list[str]
# 顶层 check_step() 只负责基础 GATES 校验 + 调这里的 per-step 额外规则。
STEP_RULES: dict[str, Callable[..., list[str]]] = {
    "2c": _check_step_2c,
    "3a": _check_step_3a,
    "3b": _check_step_3b,
    "6": _check_step_6,
}


def check_step(workdir: str, step: str, _from_all: bool = False) -> tuple[bool, list[str]]:
    """检查单个 step 的产物完整性。返回 (passed, errors)。

    _from_all 私有参数:当本函数由 check_step("all") 递归调用时为 True,
    用于跳过 topic_scores / anti_collapse / interaction_log / rerun_record 等
    「已被 --step all 顶层统一调用」的 helpers,避免同一错误双前缀重复上报。
    """
    workdir_path = Path(workdir)

    if step == "all":
        all_errors = []
        for s in ["1", "2a", "2b", "2c", "3a", "3b", "4", "5", "6"]:
            passed, errors = check_step(workdir, s, _from_all=True)
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

    content = _read_text_utf8(file_path)
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

    # 基础 GATES 通过后,分发到 per-step 额外规则(2c/3a/3b/6)
    extra = STEP_RULES.get(step)
    if extra is not None:
        errors.extend(extra(workdir_path, content, file_path, _from_all))

    return (len(errors) == 0, errors)


def main():
    VERSION = _self_version()
    parser = argparse.ArgumentParser(description=f"选题工坊 · 机器闸门检查 v{VERSION}(v0.3.18 起审查降级为过程建议)")
    parser.add_argument("--workdir", "-w", required=True, help="工作目录(产出文件所在)")
    parser.add_argument("--step", "-s", required=True, help=f"Step 编号:{', '.join(VALID_STEPS)}")
    args = parser.parse_args()

    # 展开 ~ 与 . / ..(Windows 下 os.path.isdir 不识别 ~,原实现会把 ~/foo 判为不存在)
    args.workdir = str(Path(args.workdir).expanduser().resolve())

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
    _force_utf8_stdio()
    main()
