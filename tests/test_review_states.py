# -*- coding: utf-8 -*-
"""check_review 三态(PASS/WARN/FAIL)单元测试,覆盖 v0.3.18 审查降级语义。

用 tempfile.TemporaryDirectory 而非 pytest 的 tmp_path,规避部分 Windows 环境
对 pytest-of-* 基目录的权限拒绝。
"""

import tempfile
from pathlib import Path

import check_step


def _write(name, text):
    td = tempfile.TemporaryDirectory()
    Path(td.name, name).write_text(text, encoding="utf-8")
    return td


def test_missing_file_warns():
    with tempfile.TemporaryDirectory() as d:
        status, hard, soft = check_step.check_review(Path(d), "scan")
    assert status == "WARN"
    assert hard == []
    assert any("不存在" in w for w in soft)


def test_missing_verdict_fails():
    td = _write("review_scan.md", "# Scan\n\n没有 verdict 字段\n")
    try:
        status, hard, soft = check_step.check_review(Path(td.name), "scan")
        assert status == "FAIL"
        assert hard and "verdict" in hard[0]
    finally:
        td.cleanup()


def test_invalid_verdict_fails():
    td = _write("review_scan.md", "verdict: MAYBE\n")
    try:
        status, hard, soft = check_step.check_review(Path(td.name), "scan")
        assert status == "FAIL"
        # 两段式捕获:非法值应报「值 'MAYBE' 不在合法集合」,而不是误报「缺少 verdict 字段」
        assert any("MAYBE" in e and "不在合法集合" in e for e in hard), (
            f"非法 verdict 应报出具体值,实际:\n{hard}"
        )
    finally:
        td.cleanup()


def test_clean_pass():
    td = _write(
        "review_scan.md",
        "verdict: PASS\n\nreviewer: someone\n信任边界: 无密码学身份保证,仅过程留痕\n",
    )
    try:
        status, hard, soft = check_step.check_review(Path(td.name), "scan")
        assert status == "PASS"
        assert hard == []
        assert soft == []
    finally:
        td.cleanup()


def test_placeholder_reviewer_is_warn():
    td = _write(
        "review_scan.md",
        "verdict: PASS\n\nreviewer ID: reviewer-<hash>\n\n信任边界声明\n",
    )
    try:
        status, hard, soft = check_step.check_review(Path(td.name), "scan")
        assert status == "WARN"
        assert any("占位符" in w for w in soft)
    finally:
        td.cleanup()


def test_needs_human_warns():
    td = _write(
        "review_topics.md",
        "verdict: NEEDS_HUMAN\n\nreviewer: x\n信任边界\n",
    )
    try:
        status, hard, soft = check_step.check_review(Path(td.name), "topics")
        assert status == "WARN"
        assert any("NEEDS_HUMAN" in w for w in soft)
    finally:
        td.cleanup()


def test_verdict_with_trailing_chinese_passes():
    # v0.3.x 起 verdict 正则锚定合法 token 集合,自然中文写法
    # 「verdict: PASS,继续」应只捕获 PASS,不再把 ",继续" 一起吃进来。
    td = _write(
        "review_scan.md",
        "verdict: PASS,继续\n\nreviewer: someone\n信任边界: 无密码学身份保证\n",
    )
    try:
        status, hard, soft = check_step.check_review(Path(td.name), "scan")
        assert status == "PASS", f"verdict: PASS,继续 应通过;hard={hard} soft={soft}"
        assert hard == []
    finally:
        td.cleanup()


def test_workdir_path_is_resolved():
    # v0.3.x 起 main() 会把 args.workdir 经 expanduser + resolve 归一化,
    # 以处理 ~/foo(Windows 下 os.path.isdir 不认 ~)。
    td = tempfile.TemporaryDirectory()
    nested = Path(td.name) / "subdir"
    nested.mkdir()
    # 用含 .. 组件的绝对路径,验证 resolve 后能定位到真实目录
    weird = str(Path(td.name) / "subdir" / ".." / "subdir")
    resolved = str(Path(weird).expanduser().resolve())
    assert Path(resolved).is_dir(), f"应能解析含 .. 的路径:{weird} → {resolved}"
    assert Path(resolved).resolve() == nested.resolve(), "resolve 后应回到真实子目录"
    td.cleanup()
