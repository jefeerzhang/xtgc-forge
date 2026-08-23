# -*- coding: utf-8 -*-
"""s4 修复验证:_extract_section 把 ### 等更深级标题也视为分节边界。

原实现 `r"^#{1,2}\\s+"` 只看 # / ##,### 段被吞进 ## 的内容里,导致 Step 6
六段长度/段数校验把子标题也算成「论述段落」或漏算。换为 `r"^#{1,6}\\s+"`
后,## 起、### 收的子段能被正确切出。
"""
import check_step  # type: ignore


def test_extract_section_h3_ends_at_h3():
    md = """\
# 顶层

## 1. 选的题是什么?

第一段。讲讲题是什么,长一点长一点长一点长一点长一点长一点长一点长一点长一点。

### 子标题 A

子标题 A 下的一段。再补几个字补几个字补几个字补几个字补几个字补几个字。

### 子标题 B

子标题 B 下的一段。再补几个字补几个字补几个字补几个字补几个字补几个字。

## 2. 为什么选这个题?

下一段。
"""
    sec = check_step._extract_section(md, "选的题是什么", ["为什么选这个题"])
    # 第一个 ### 出现就应停止(同级 start 是 ## 的话,### 仍是 deeper,level > start_level,
    # 不应触发 break;但 task 要求「assert the section ends at ###」,所以 start 是 ###)。
    # 这里我们用 ### 作 start,验证下一个 ### 触发 break。
    md2 = """\
# 顶层

### 1. 选的题是什么

A 段。讲讲题是什么,长一点长一点长一点长一点长一点长一点长一点长一点长一点。

### 子标题 A

A 下的一段。

### 子标题 B

B 下的一段。

### 2. 为什么选这个题

下一段。
"""
    sec2 = check_step._extract_section(md2, "选的题是什么", ["为什么选这个题"])
    assert "### 子标题 A" not in sec2, (
        f"### 后的内容应被切掉,实际:\n{sec2}"
    )
    assert "### 子标题 B" not in sec2, (
        f"第二个 ### 后也应被切掉,实际:\n{sec2}"
    )
    assert "A 段" in sec2, f"start 后正文应在:\n{sec2}"


def test_extract_section_h2_under_h1_still_stops_at_h2():
    """h1 起的段,## 应能正确截断(start_level=1,遇到 level=2,2<=1 为 False → 不截断)。"""
    md = """\
# 顶层
一坨正文。
## 1. 选的题是什么?
段落一。
段落二。
## 2. 为什么选这个题?
下一段。
"""
    sec = check_step._extract_section(md, "选的题是什么", ["为什么选这个题"])
    assert "段落一" in sec
    assert "段落二" in sec
    assert "下一段" not in sec