"""check_step_lib · helpers.py

底层纯函数 + 闸门常量。gates / dispatch / cli 三层从这里取数。

组织:
  - 16 顶层 UPPER 常量(原 check_step.py 全量搬入,无新增无删除)
  - 9 私有 helper 函数(下划线前缀)

依赖:md_doc(语义唯一来源)、templates(模板字面量与拦截规则同址)。
"""
import json
import re
import sys
from pathlib import Path

import md_doc
import templates

# 注意:__all__ 除 16 常量与 9 个下划线 helper 外,还显式透传
#  Path / re / sys / json / md_doc / templates 等依赖,使 `from .helpers import *`
#  的 gates.py 能直接裸用这些名字(不透传的话,函数体内会 NameError)。

ANTI_COLLAPSE_LOW_TIER = 0.50
# __all__ 必须显式列出,否则 `from .helpers import *` 默认排除下划线开头
# 名称,_count_cjk_and_alnum / _tier_of 等 9 个 helper 全部漏到 check_step_lib
# 命名空间外,gates.py 里会 NameError。
__all__ = [
    # 16 常量(老 check_step.py 顶层裸名,shim 透传)
    "ANTI_COLLAPSE_LOW_TIER",
    "BODY_JARGON",
    "GATES",
    "MAX_BODY_SENTENCE",
    "MIN_PARAGRAPH_CHARS",
    "MIN_REVEALS_LEN",
    "PLACEHOLDER_PATTERNS",
    "PLACEHOLDER_PATTERNS_RE",
    "REQUIRED_GATES",
    "RERUN_DECLARE_PATTERNS",
    "RERUN_EMPTY_THRESHOLD",
    "RERUN_PHRASES",
    "REVIEW_VALID_VERDICTS",
    "SCORE_KEYS",
    "TIER_BANDS",
    "VALID_STEPS",
    # 标准依赖透传(gates.py 的 def 用 Path 注解,靠 * 传播)
    "Path",
    # 9 私有 helper(下划线开头,import * 默认不传播,必须显式列)
    "_count_cjk_and_alnum",
    "_count_matrix_data_rows",
    "_count_paragraphs",
    "_force_utf8_stdio",
    "_is_table_separator",
    "Utf8ArtifactError",
    "_read_text_utf8",
    "_resolve_workdir_file",
    "_self_version",
    "_tier_of",
    "json",
    "md_doc",
    "re",
    "sys",
    "templates",
]

RERUN_EMPTY_THRESHOLD = 30

MIN_REVEALS_LEN = 8

MIN_PARAGRAPH_CHARS = 40

MAX_BODY_SENTENCE = 100

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

PLACEHOLDER_PATTERNS_RE = re.compile("|".join(PLACEHOLDER_PATTERNS))

REQUIRED_GATES = ["#1", "#2", "#3", "#4", "#5"]

RERUN_PHRASES = ["按上次", "复跑", "不要再问", "沿用"]

RERUN_DECLARE_PATTERNS = [
    r"复跑说明",                 # 顶部复跑说明
    r"本复跑",                   # 正文/附录叙事「本复跑…」
    r"\|\s*复跑\s*\|\s*(?!\s*否)",  # 附录 F 表格行 | 复跑 | (值非「否」)
]

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

TIER_BANDS = {
    "safe": (0.55, 0.80),  # 0.55 ≤ t < 0.80
    "differentiated": (0.35, 0.55),
    "innovative": (0.0, 0.35),
}

REVIEW_VALID_VERDICTS = {"PASS", "P0_OPEN", "FAIL", "NEEDS_HUMAN"}


# --- 9 私有 helper 函数 ---------------------------------

class Utf8ArtifactError(Exception):
    """产物文件不是有效 UTF-8。由 router/gates 收成 errors;cli 再映射退出码。

    不在这里 sys.exit:verify() / check_step_router 承诺无杀进程副作用。
    """


def _read_text_utf8(path: Path) -> str:
    """读产物文件;非 UTF-8(常见:编辑器存成 GBK/ANSI)时抛 Utf8ArtifactError。"""
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise Utf8ArtifactError(
            f"❌ {path.name} 不是有效的 UTF-8 文本(可能被存成了 GBK/ANSI)。"
            f"请将其转存为 UTF-8 后重试。({exc})"
        ) from exc


def _self_version() -> str:
    """从仓库根 SKILL.md frontmatter 读取版本号(唯一真源),避免硬编码滞后。

    与 check-ready.sh 的 SELF_VERSION 同源,防止脚本 banner 与仓库版本漂移。
    本文件在 scripts/check_step_lib/,仓库根是 parents[2](不是 parent.parent)。
    """
    skill = Path(__file__).resolve().parents[2] / "SKILL.md"
    try:
        text = skill.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return "unknown"
    m = re.search(r'^version:\s*["\']?([^"\'\s]+)["\']?\s*$', text, re.MULTILINE)
    return m.group(1) if m else "unknown"

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

def _count_cjk_and_alnum(text: str) -> int:
    """粗算有效字符数(中日韩 + 字母数字)。"""
    return len(re.findall(r"[\u4e00-\u9fffA-Za-z0-9]", text))

def _force_utf8_stdio() -> None:
    """强制 stdout/stderr 走 UTF-8(管道重定向时 Windows 默认 cp936,
    ✅/❌ 等 emoji 会抛 UnicodeEncodeError,导致 PASS 也以退出码 1 结束)。
    输出消费方(Claude Code / 测试)统一按 UTF-8 解码。"""
    for stream in (sys.stdout, sys.stderr):
        if stream is not None and hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")

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

def _tier_of(t_score: float) -> str:
    """由 t_score 推导层级(与 anti-collapse.md 分界一致)。

    越界(< 0 或 > 1)返回 "out_of_band" 而非抛异常:防止越界分被静默
    映射成某个合法层级。调用方 check_anti_collapse 在调用前已用
    0 <= t <= 1 守卫并单独报「不在 0-1 范围」,正常路径不会拿到该哨兵,
    它仅是防御性兜底。
    """
    if t_score < 0 or t_score > 1:
        return "out_of_band"
    for tier, (lo, hi) in TIER_BANDS.items():
        if lo <= t_score < hi:
            return tier
    return "safe"  # t ≥ 0.80 落入模态区;candidate 层级枚举无 modal,归为 safe(模态题由 Phase 1 模态识别拦截)

