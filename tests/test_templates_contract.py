# -*- coding: utf-8 -*-
"""模板契约不变式测试（v0.3.22 深化：模板与其占位符契约同址）。

契约：
- 模板里出现的每个 <...> 占位 token，都必须被闸门占位符模式拦截
  （模板改了，拦截规则自动跟随——这是 templates.py 深 module 的核心承诺）；
- HTML 注释行是编辑提示，不是占位符，不得混入派生；
- init 的替换 token 集合与 templates.FILL_TOKENS 一致（fill_values 断言锚定）；
- 空白放宽匹配覆盖 <来源 Gap 编号> 等模板家族变体；
- s2 语义保留：无尖括号的字面提醒不拦，尖括号占位必拦。
"""
import re

import check_step  # type: ignore
import templates  # type: ignore


def test_every_template_token_is_blocked():
    """模板中出现的每个占位 token 都必须被闸门拦截——契约断裂即红。"""
    for tok in templates.template_placeholders():
        assert check_step.PLACEHOLDER_PATTERNS_RE.search(tok) is not None, (
            f"模板占位未被拦截（契约断裂）: {tok!r}"
        )


def test_html_comments_not_derived():
    toks = templates.template_placeholders()
    assert toks, "派生结果为空说明模板扫描失效"
    assert not any(t.startswith("<!--") for t in toks), "HTML 注释混入派生"


def test_fill_tokens_are_template_tokens():
    assert set(templates.FILL_TOKENS) <= set(templates.template_placeholders())


def test_whitespace_loose_variants_blocked():
    # 派生模式对 token 内空白放宽；家族关键词兜底覆盖无空格变体
    for variant in ["<来源 Gap 编号>", "<来源  Gap  编号>", "<来源Gap编号>"]:
        assert check_step.PLACEHOLDER_PATTERNS_RE.search(variant) is not None, variant


def test_s2_semantics_preserved():
    """无尖括号的字面「请填写或修改」不拦；尖括号形态必拦（s2 修复语义）。"""
    m = check_step.PLACEHOLDER_PATTERNS_RE.search("请填写或修改")
    assert m is None or m.group(0) != "请填写或修改"
    assert check_step.PLACEHOLDER_PATTERNS_RE.search("<请填写或修改>") is not None


def test_generator_signature_blocked():
    assert check_step.PLACEHOLDER_PATTERNS_RE.search(
        "由 init_project.py 自动生成"
    ) is not None
    assert check_step.PLACEHOLDER_PATTERNS_RE.search(
        "由 `init_project.py` 自动生成"
    ) is not None


def test_derived_patterns_compile_and_self_match():
    pats = templates.placeholder_patterns()
    toks = templates.template_placeholders()
    assert len(pats) == len(toks) + 1  # +1 = 产物签名行
    for tok, pat in zip(toks, pats):
        assert re.search(pat, tok) is not None, f"派生模式未命中自身 token: {tok!r}"
