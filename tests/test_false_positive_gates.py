# -*- coding: utf-8 -*-
"""校验器误报回归(v0.3.x 审计批次 2)。

四个「合规产物被误拦」类缺陷:
1. check_review 取全文第一个 verdict —— 正文转述历史轮次的 FAIL 压过真正的 PASS
2. interaction-log 用户原话含 < 或「待填」即整条丢弃 —— 合法确认被判无效
3. 闸门编号紧贴汉字时 \b 不成立(CJK 算 word char)—— CP#1已确认 误报缺闸
4. 附录豁免锚死在字面串「# 整合附录」—— 标题变体导致附录黑话误报
"""

import tempfile
from pathlib import Path

import check_step


def _write(name, text):
    td = tempfile.TemporaryDirectory()
    Path(td.name, name).write_text(text, encoding="utf-8")
    return td


def test_verdict_historical_mention_does_not_mask_final():
    """正文转述历史轮次 verdict: FAIL 不应压过后文最终 verdict: PASS。"""
    td = _write(
        "review_scan.md",
        "## 审查历史\n"
        "第 1 轮 verdict: FAIL(历史轮次,P0 已修复)\n"
        "\n## 最终结论\n"
        "verdict: PASS\n\nreviewer: someone\n信任边界: 仅过程留痕\n",
    )
    try:
        status, hard, soft = check_step.check_review(Path(td.name), "scan")
        assert status == "PASS", f"最终 verdict 应生效;hard={hard} soft={soft}"
    finally:
        td.cleanup()


def _write_log(rows):
    lines = ["| 闸门 | 状态 | 时间 | 用户原话 |", "| --- | --- | --- | --- |"] + rows
    return "\n".join(lines) + "\n"


def test_interaction_log_quote_with_lt_and_placeholder_words():
    """含 < 或数学比较的原话是合法确认;纯占位符行仍然无效。"""
    rows = [
        "| CP#1 | 确认 | 2026-08-24 | 要求 t_score<0.5 才算过关 |",
        "| CP#2 | 确认 | 2026-08-24 | 就按主推方案 A 走 |",
        "| CP#3 | 确认 | 2026-08-24 | 备选保留两个即可 |",
        "| CP#4 | 通过 | 2026-08-24 | 附录对照表可以接受 |",
        "| CP#5 | 确认 | 2026-08-24 | 同意进入交付阶段 |",
        "| CP#5 | 确认 | 2026-08-24 | <待填> |",
    ]
    td = _write("interaction-log.md", _write_log(rows))
    try:
        ok, errors = check_step.check_interaction_log(Path(td.name))
        assert ok, f"< 比较符不应废掉整条确认;errors={errors}"
    finally:
        td.cleanup()


def test_gate_number_adjacent_to_cjk():
    """CP#1已确认(编号后紧跟汉字,无空格)应命中对应闸门。"""
    rows = [
        f"| CP#{i}已确认 | 确认 | 2026-08-24 | 第 {i} 闸通过 |" for i in range(1, 6)
    ]
    td = _write("interaction-log.md", _write_log(rows))
    try:
        ok, errors = check_step.check_interaction_log(Path(td.name))
        assert ok, f"紧贴汉字的编号应匹配;errors={errors}"
    finally:
        td.cleanup()


def test_appendix_heading_variants_are_exempt():
    """附录标题带序号/不同层级/无空格时,豁免仍应生效。"""
    appendix = (
        "GAP-C1 对照:t_score<0.50 的条目全部映射到人话表述,详见下表。\n"
        "这一句故意拉得很长没有任何句读符号用来测试断句规则不会越界扫描到附录区域"
        "因为附录属于技术对照区按设计应当整体豁免可读性检查的所有限制规则\n"
    )
    for heading in ["## 三、整合附录", "### 整合附录", "#整合附录"]:
        td = _write(
            "Step6-report.md",
            f"# 主报告\n\n正文短句。表达清楚。\n\n{heading}\n\n{appendix}",
        )
        try:
            content = Path(td.name, "Step6-report.md").read_text(encoding="utf-8")
            errors = check_step.check_readability(content)
            assert errors == [], f"{heading!r} 变体应豁免附录;errors={errors}"
        finally:
            td.cleanup()


def test_body_without_appendix_still_checked():
    """没有附录标题时全文仍受检(防修复把豁免扩大化)。"""
    td = _write(
        "Step6-report.md",
        "正文出现 GAP-C1 内部术语,且没有附录标题兜底。\n",
    )
    try:
        content = Path(td.name, "Step6-report.md").read_text(encoding="utf-8")
        errors = check_step.check_readability(content)
        assert errors, "正文黑话仍应被抓"
    finally:
        td.cleanup()
