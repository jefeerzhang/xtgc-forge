# -*- coding: utf-8 -*-
"""md_doc · Markdown 结构理解（深 module，v0.3.21 引入）

把原先散在 check_step.py 的三套章节切分语义合并到一处：

- 标题树：解析一次；分节边界统一为「同级或更高级标题」，
  深层同名小节不截断；fenced / 缩进代码块内的 # 不进入标题树；
- 切分查询：取某节正文（六段）、取附录范围（标题优先、
  同级截断 + 下一附录字母取较早者；文本标记回退）、
  取正文（整合附录标题之前）；
- 散文提取：剥离 markdown 结构行与行内标记，只留可断句的真散文。

闸门（check_step.py）只向本 module 查询，不自行切分。
术语定义见仓库根 CONTEXT.md「文档解析」。
"""
from __future__ import annotations

import re
from dataclasses import dataclass

# # 后允许零空白（兼容「#整合附录」写法，与历史闸门语义一致）；
# CommonMark：标题最多缩进 3 空格；4 空格起是代码块，不是标题。
_HEADING_RE = re.compile(r"^(#{1,6})\s*(.*)$")
_FENCE_OPEN_RE = re.compile(r"^(`{3,}|~{3,})")
_LATEX_CMD_RE = re.compile(r"\\[a-zA-Z]+")
_MATH_RELATION_RE = re.compile(r"(?:=|<=|>=|<|>|≈|≤|≥|\\(?:approx|leq|geq|sim)\b)")
_CJK_RE = re.compile(r"[\u4e00-\u9fff]")
_LATIN_PROSE_WORD_RE = re.compile(r"[A-Za-z]{3,}")


@dataclass(frozen=True)
class Heading:
    level: int   # 1-6
    text: str    # 去掉 # 与空白后的标题文本
    start: int   # 标题所在行号（0-based）
    end: int     # 分节边界行号（不含）：其后第一个同级或更高级标题；无则 len(lines)


def headings(content: str) -> list[Heading]:
    """解析标题树。边界语义：同级或更高级的标题才算分节边界。

    fenced code（``` / ~~~）与 4 空格缩进代码块内的行不进入标题树，
    避免 Python/Stata 注释「# 整合附录」把正文切进附录豁免区。
    """
    lines = content.splitlines()
    raw: list[tuple[int, int, str]] = []  # (line_idx, level, text)
    fence: tuple[str, int] | None = None
    for i, line in enumerate(lines):
        stripped = line.strip()
        space_indent = len(line) - len(line.lstrip(" "))
        is_indented_code = line.startswith("\t") or space_indent >= 4
        if fence is not None:
            fence_char, fence_length = fence
            if not is_indented_code and re.fullmatch(
                rf"{re.escape(fence_char)}{{{fence_length},}}\s*", stripped
            ):
                fence = None
            continue
        if is_indented_code:
            continue
        fence_match = _FENCE_OPEN_RE.match(stripped)
        if fence_match:
            opener = fence_match.group(1)
            fence = (opener[0], len(opener))
            continue
        m = _HEADING_RE.match(line.lstrip())
        if not m:
            continue
        raw.append((i, len(m.group(1)), m.group(2).strip()))

    tree: list[Heading] = []
    for k, (i, level, text) in enumerate(raw):
        end = len(lines)
        for j, jlevel, _ in raw[k + 1:]:
            if jlevel <= level:
                end = j
                break
        tree.append(Heading(level=level, text=text, start=i, end=end))
    return tree


def section_text(content: str, heading_substr: str) -> str:
    """取含 heading_substr 的第一个标题之下的正文。

    截断条件：其后第一个同级或更高级、且不含 heading_substr 的标题。
    深层（更低级别）小节——包括同名小节——归入本节，不提前截断。
    """
    lines = content.splitlines()
    tree = headings(content)
    start_h = None
    for h in tree:
        if heading_substr in h.text:
            start_h = h
            break
    if start_h is None:
        return ""
    end = len(lines)
    for h in tree:
        if h.start <= start_h.start:
            continue
        if h.level <= start_h.level and heading_substr not in h.text:
            end = h.start
            break
    return "\n".join(lines[start_h.start + 1:end])


def appendix_range(content: str, letter: str) -> str:
    """取「附录 <letter>」的范围。

    标题优先：按标题树定位（任意层级）。终点取较早者：
    - 该标题的同级或更高级边界（Heading.end）
    - 其后第一个「附录 <下一字母>」标题
    这样「参考文献」等同级非附录标题不会被吞进附录 A，避免矩阵误计。

    回退：附录标题未写成 markdown 标题时，文本标记匹配；
    截断认下一附录字母标题，或任意 h1/h2（视为同级边界）。
    """
    next_letter = chr(ord(letter) + 1)
    lines = content.splitlines()
    tree = headings(content)
    start_h = None
    for h in tree:
        if re.search(rf"附录\s*{letter}", h.text):
            start_h = h
            break
    if start_h is not None:
        end = start_h.end
        for h in tree:
            if h.start > start_h.start and re.search(rf"附录\s*{next_letter}", h.text):
                if h.start < end:
                    end = h.start
                break
        return "\n".join(lines[start_h.start + 1:end])

    m = re.search(
        rf"附录\s*{letter}[^\n]*\n([\s\S]*?)(?=\n#{{1,6}}\s*附录\s*{next_letter}|\n#{{1,2}}\s|\Z)",
        content,
    )
    return m.group(1) if m else ""


def body_before(content: str, heading_substr: str) -> str:
    """取含 heading_substr 的第一个标题之前的全部文本；无该标题则全文。"""
    tree = headings(content)
    for h in tree:
        if heading_substr in h.text:
            return "\n".join(content.splitlines()[:h.start])
    return content


def _is_pure_formula_line(stripped: str) -> bool:
    """整行是公式/符号，不是夹了 LaTeX 的散文。

    同时出现 LaTeX 命令和数学关系运算符，且没有普通英文词时，
    才按公式行处理。英文散文和 Windows 路径均保留给正文闸门。
    """
    if not _LATEX_CMD_RE.search(stripped):
        return False
    if _CJK_RE.search(stripped):
        return False
    if not _MATH_RELATION_RE.search(stripped):
        return False
    without_commands = _LATEX_CMD_RE.sub(" ", stripped)
    return not _LATIN_PROSE_WORD_RE.search(without_commands)


def strip_structure(text: str) -> str:
    """剥离 markdown 结构行（标题/表格/代码块/公式块/分隔线/列表标记/引用标记），只留真散文。"""
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
        # 纯公式行才整行丢弃（回归方程、无散文单词）。
        # 中文正文、英文句子夹 \cite / \beta、Windows 路径均保留，交给断句闸。
        if _is_pure_formula_line(stripped):
            continue
        if stripped.startswith(">"):  # 引用：去标记保留内容
            out.append(re.sub(r"^>\s?", "", line))
            continue
        # 列表行：去列表标记，保留内容
        out.append(re.sub(r"^([-*]\s|\d+\.\s)", "", stripped))
    joined = "\n".join(out)
    # 去行内 markdown 符号，避免断句闸句长虚高。
    # * 与 ` 无条件剥离：中文强调常紧贴汉字（如「**重点**」），两侧无空白，
    # 边界判定会漏剥，残留的 * 会计入句长；_ 见下行规则（保留 snake_case）。
    joined = re.sub(r"[`*]", "", joined)
    # _ 只剥「不夹在两个单词字符中间」的：snake_case 的 _ 两侧都是 [A-Za-z0-9] 保留；
    # _斜体_ / 行首 _ 这类挨着空白或汉字的标记剥离。
    return re.sub(r"(?<![A-Za-z0-9])_+|_+(?![A-Za-z0-9])", " ", joined)
