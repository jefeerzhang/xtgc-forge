# -*- coding: utf-8 -*-
"""strip_structure 行内符号剥离测试。

契约:
- * 与 ` 无条件剥离:中文强调常紧贴汉字(如「**重点**」),两侧无空白,
  若只在字边界剥离会漏,残留的 * 会让断句闸句长虚高(每对强调 +4 字);
- _ 仅在字边界处剥,snake_case 标识符保留下划线。

v0.3.21:散文提取收进 md_doc 深 module,本文件从直测
check_step._strip_md_structure 迁移为打 md_doc.strip_structure 的 interface。
"""

import md_doc  # type: ignore


def test_cjk_adjacent_emphasis_stripped():
    out = md_doc.strip_structure("这是**重点**句子和`代码`片段。")
    assert "*" not in out, f"紧贴汉字的 ** 应被剥掉:\n{out}"
    assert "`" not in out, f"行内代码反引号应被剥掉:\n{out}"
    assert "重点" in out and "代码" in out


def test_snake_case_underscore_preserved():
    out = md_doc.strip_structure("使用 topic_scores 与 snake_case 变量。")
    assert "topic_scores" in out, f"snake_case 下划线不应被吞:\n{out}"
    assert "snake_case" in out


def test_boundary_underscore_stripped():
    out = md_doc.strip_structure("行首 _斜体_ 标记应剥离。")
    assert "_斜体_" not in out, f"字边界处的 _ 标记应剥掉:\n{out}"
    assert "斜体" in out
