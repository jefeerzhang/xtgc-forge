# -*- coding: utf-8 -*-
"""md_doc interface 测试（v0.3.21 深化：三套切分合并为标题树模型）。

行为锚自原 _extract_section / _strip_md_structure 直测用例迁移而来：
seam 被承认后，测试打在 md_doc 的公开 interface 上，不再直测下划线内部。
"""
import md_doc  # type: ignore


# ---------- 标题树 ----------

def test_headings_levels_and_text():
    md = "# 顶层\n\n## 一、选题\n正文。\n### 子节\n更多。\n## 二、意义\n"
    tree = md_doc.headings(md)
    assert [(h.level, h.text) for h in tree] == [
        (1, "顶层"), (2, "一、选题"), (3, "子节"), (2, "二、意义")
    ]


def test_headings_end_is_same_or_higher_boundary():
    md = "## 甲\n一。\n### 甲-子\n二。\n## 乙\n三。\n"
    tree = md_doc.headings(md)
    jia = tree[0]
    lines = md.splitlines()
    # 甲节包含 ### 子节，止于同级 ## 乙
    assert "甲-子" in lines[jia.end - 1] or "二。" in "\n".join(lines[jia.start + 1:jia.end])
    assert "三。" not in "\n".join(lines[jia.start + 1:jia.end])


def test_headings_skip_fenced_code_comments():
    """fence 内的 # 注释不是标题（Python/Stata 代码块不得切断章节）。"""
    md = (
        "# 报告\n"
        "## 选的题是什么\n"
        "正文段。\n"
        "```python\n"
        "# 这是注释不是标题\n"
        "x = 1\n"
        "```\n"
        "## 为什么选这个题\n"
        "下一段。\n"
    )
    tree = md_doc.headings(md)
    assert [h.text for h in tree] == ["报告", "选的题是什么", "为什么选这个题"]
    sec = md_doc.section_text(md, "选的题是什么")
    assert "正文段。" in sec
    assert "下一段" not in sec


def test_headings_skip_four_space_indented_code():
    """CommonMark 4 空格缩进代码块里的 # 不是标题。"""
    md = "# 报告\n    # 缩进注释\n## 下一节\n"
    tree = md_doc.headings(md)
    assert [h.text for h in tree] == ["报告", "下一节"]


def test_indented_backticks_do_not_open_fence():
    """四空格缩进的 ``` 是代码内容，不得吞掉后续真实标题。"""
    md = "# 报告\n    ```python\n## 下一节\n正文。\n"
    tree = md_doc.headings(md)
    assert [h.text for h in tree] == ["报告", "下一节"]


# ---------- section_text（原 _extract_section 语义）----------

def test_section_h2_keeps_deeper_h3_subsections():
    """start 是 ## 时，### 子段属于该节内容（deeper，不截断），节在下一个 ## 处结束。"""
    md = """\
# 顶层

## 1. 选的题是什么?

第一段。讲讲题是什么,长一点长一点长一点长一点长一点长一点长一点长一点长一点。

### 子标题 A

子标题 A 下的一段。再补几个字补几个字补几个字补几个字补几个字补几个字。

## 2. 为什么选这个题?

下一段。
"""
    sec = md_doc.section_text(md, "选的题是什么")
    assert "子标题 A 下的一段" in sec, f"### 子段应归入 ## 节:\n{sec}"
    assert "下一段" not in sec, f"下一个 ## 之后应被切掉:\n{sec}"


def test_section_h3_ends_at_same_level_h3():
    md = """\
# 顶层

### 1. 选的题是什么

A 段。讲讲题是什么,长一点长一点长一点长一点长一点长一点长一点长一点长一点。

### 子标题 A

A 下的一段。

### 2. 为什么选这个题

下一段。
"""
    sec = md_doc.section_text(md, "选的题是什么")
    assert "A 段" in sec, f"start 后正文应在:\n{sec}"
    assert "子标题 A" not in sec, f"同级 ### 应截断:\n{sec}"


def test_section_adjacent_heading_bounds_section():
    content = "# 报告\n## 第一节\ntext\n## 第二节\ntext2\n"
    sec = md_doc.section_text(content, "第一节")
    assert "text" in sec and "text2" not in sec


def test_section_deep_same_name_subsection_not_boundary():
    content = "# 报告\n## 第一节\ntext\n### 第一节补充\ndeep\n## 第二节\ntext2\n"
    sec = md_doc.section_text(content, "第一节")
    assert "deep" in sec, f"深层同名小节不得提前截断:\n{sec}"


def test_section_missing_returns_empty():
    assert md_doc.section_text("# 报告\n正文", "不存在") == ""


# ---------- appendix_range（标题优先、文本标记回退）----------

def test_appendix_range_by_heading():
    md = "# 报告\n正文。\n## 附录 A 文献矩阵\n| L1 | x |\n## 附录 B 编号\n对照。\n"
    rng = md_doc.appendix_range(md, "A")
    assert "| L1 | x |" in rng and "对照。" not in rng


def test_appendix_range_plain_text_fallback():
    """附录 A 标题无 # 前缀（现状正则容忍的报告形态）仍可截出范围，不产生新误报。
    回退保持历史正则语义：起始可是纯文本，截断认 # 标题的附录 B。"""
    md = "# 报告\n正文。\n附录 A 文献矩阵\n| L1 | x |\n## 附录 B 编号\n对照。\n"
    rng = md_doc.appendix_range(md, "A")
    assert "| L1 | x |" in rng and "对照。" not in rng


def test_appendix_range_to_eof_when_no_next():
    md = "# 报告\n## 附录 A 矩阵\n行一。\n行二。\n"
    rng = md_doc.appendix_range(md, "A")
    assert "行一。" in rng and "行二。" in rng


def test_appendix_range_stops_at_same_level_non_appendix():
    """附录 A 在同级「参考文献」处截断，不得吞掉后续表格（矩阵误计回归）。"""
    md = (
        "# 报告\n"
        "## 附录 A 文献矩阵\n"
        "| L1 | x |\n"
        "## 参考文献\n"
        "| L9 | 不该算进附录 A |\n"
        "## 附录 B 编号\n"
        "对照。\n"
    )
    rng = md_doc.appendix_range(md, "A")
    assert "| L1 | x |" in rng
    assert "L9" not in rng
    assert "对照。" not in rng


def test_appendix_range_fallback_stops_at_h2():
    """无 # 前缀的附录 A，回退时在同级 h1/h2 处停，不只认附录 B。"""
    md = (
        "# 报告\n正文。\n"
        "附录 A 文献矩阵\n| L1 | x |\n"
        "## 参考文献\n| L9 | y |\n"
        "## 附录 B 编号\n对照。\n"
    )
    rng = md_doc.appendix_range(md, "A")
    assert "| L1 | x |" in rng
    assert "L9" not in rng


# ---------- body_before（正文 = 整合附录标题前）----------

def test_body_before_integration_appendix():
    md = "# 报告\n正文段。\n## 三、整合附录\n附录内容。\n"
    body = md_doc.body_before(md, "整合附录")
    assert "正文段。" in body and "附录内容。" not in body


def test_body_before_missing_returns_full():
    md = "# 报告\n只有正文。\n"
    assert md_doc.body_before(md, "整合附录") == md


def test_body_before_ignores_fence_fake_appendix():
    """代码块里的「# 整合附录」不得把后续正文划进豁免区。"""
    md = (
        "# 报告\n开场。\n"
        "```python\n"
        "# 整合附录\n"
        "x = 1\n"
        "```\n"
        "无句界连续长文无句界连续长文。\n"
        "## 整合附录\n"
        "附录内容。\n"
    )
    body = md_doc.body_before(md, "整合附录")
    assert "开场。" in body
    assert "无句界连续长文" in body
    assert "附录内容。" not in body


def test_body_before_ignores_tilde_fence_fake_appendix():
    """~~~ fence 内的假附录标题不得截断正文。"""
    md = (
        "# 报告\n开场。\n"
        "~~~python\n"
        "# 整合附录\n"
        "x = 1\n"
        "~~~\n"
        "正文继续。\n"
        "## 整合附录\n"
        "附录内容。\n"
    )
    body = md_doc.body_before(md, "整合附录")
    assert "开场。" in body
    assert "正文继续。" in body
    assert "附录内容。" not in body


def test_body_before_tilde_fence_ignores_backtick_closer():
    """~~~ fence 内的 ``` 不得提前关闭代码块。"""
    md = (
        "# 报告\n开场。\n"
        "~~~text\n"
        "```\n"
        "# 整合附录\n"
        "~~~\n"
        "正文继续。\n"
        "## 整合附录\n"
        "附录内容。\n"
    )
    body = md_doc.body_before(md, "整合附录")
    assert "正文继续。" in body
    assert "附录内容。" not in body


def test_body_before_long_fence_ignores_shorter_closer():
    """四字符 fence 不得被三字符 fence 提前关闭。"""
    md = (
        "# 报告\n开场。\n"
        "````text\n"
        "```\n"
        "# 整合附录\n"
        "````\n"
        "正文继续。\n"
        "## 整合附录\n"
        "附录内容。\n"
    )
    body = md_doc.body_before(md, "整合附录")
    assert "正文继续。" in body
    assert "附录内容。" not in body


def test_body_before_fence_ignores_indented_closer():
    """四空格缩进的 fence 标记是代码内容，不得关闭代码块。"""
    md = (
        "# 报告\n开场。\n"
        "```text\n"
        "    ```\n"
        "# 整合附录\n"
        "```\n"
        "正文继续。\n"
        "## 整合附录\n"
        "附录内容。\n"
    )
    body = md_doc.body_before(md, "整合附录")
    assert "正文继续。" in body
    assert "附录内容。" not in body


# ---------- strip_structure（原 _strip_md_structure 语义）----------

def test_cjk_adjacent_emphasis_stripped():
    out = md_doc.strip_structure("这是**重点**句子和`代码`片段。")
    assert "*" not in out and "`" not in out
    assert "重点" in out and "代码" in out


def test_snake_case_underscore_preserved():
    out = md_doc.strip_structure("使用 topic_scores 与 snake_case 变量。")
    assert "topic_scores" in out and "snake_case" in out


def test_boundary_underscore_stripped():
    out = md_doc.strip_structure("行首 _斜体_ 标记应剥离。")
    assert "_斜体_" not in out and "斜体" in out


def test_structure_lines_removed():
    md = "## 标题\n| a | b |\n```\ncode\n```\n---\n- 列表项\n> 引用文"
    out = md_doc.strip_structure(md)
    assert "标题" not in out and "code" not in out and "a | b" not in out
    assert "列表项" in out and "引用文" in out


def test_strip_structure_tilde_fence_removed():
    """~~~ fence 内的行不进散文提取。"""
    md = "## 标题\n~~~python\ncode_line\n~~~\n正文。"
    out = md_doc.strip_structure(md)
    assert "code_line" not in out and "标题" not in out
    assert "正文。" in out


def test_strip_structure_tilde_fence_ignores_backtick_closer():
    """~~~ fence 内的 ``` 不得提前关闭，代码块内容仍被剥除。"""
    md = "## 标题\n~~~text\n```\ncode_line\n~~~\n正文。"
    out = md_doc.strip_structure(md)
    assert "code_line" not in out and "```" not in out
    assert "正文。" in out


def test_strip_structure_long_fence_not_closed_by_shorter():
    """四字 fence 不得被三字 fence 提前关闭。"""
    md = "````text\n```\ncode_line\n````\n正文。"
    out = md_doc.strip_structure(md)
    assert "code_line" not in out
    assert "正文。" in out


def test_strip_structure_indented_closer_is_content():
    """四空格缩进的 fence 标记是内容，不得关闭代码块。"""
    md = "```text\n    ```\ncode_line\n```\n正文。"
    out = md_doc.strip_structure(md)
    assert "code_line" not in out
    assert "正文。" in out


def test_strip_structure_indented_code_block_removed():
    """四空格缩进的代码块（非围栏）也应从散文提取中剥除。"""
    md = "# 标题\n    code_line\n正文。"
    out = md_doc.strip_structure(md)
    assert "code_line" not in out and "标题" not in out
    assert "正文。" in out


def test_english_cite_line_kept_for_sentence_gate():
    """含 \\cite 的英文句子是散文，不是公式行。"""
    line = (
        "This identification strategy uses \\cite{smith2020} and continues without "
        "any period so the sentence stays far longer than one hundred characters"
    )
    out = md_doc.strip_structure(line)
    assert "identification" in out
    assert "smith2020" in out


def test_short_english_cite_line_kept_for_gate():
    """短英文正文含引用命令时仍是散文，不能因词数少被整行剥除。"""
    line = r"The t_score \cite{x}"
    out = md_doc.strip_structure(line)
    assert "t_score" in out
    assert "cite{x}" in out


def test_english_prose_with_inline_equation_is_kept():
    """含 LaTeX 等式的英文陈述仍是散文，不能整行剥除。"""
    line = r"The coefficient \beta = 0.5 is positive"
    assert md_doc.strip_structure(line) == line


def test_pure_equation_line_still_stripped():
    """纯符号回归方程仍按公式行剥离（金样例回归方程无中文）。"""
    line = r"Y_{it} = \beta_1 X_{it} + \epsilon_{it}"
    out = md_doc.strip_structure(line)
    assert "beta" not in out.lower()
    assert "X_{it}" not in out
