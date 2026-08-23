# -*- coding: utf-8 -*-
"""检查脚本的占位符闸门(PLACEHOLDER_PATTERNS)。

契约(见 CHANGELOG v0.3.17):
- 1-3 字纯中文尖括号(如 <用户> <文献> <什么>)属于合法正文,放行;
- 4 汉字以上描述性尖括号(如 <中文摘要> <显著水平>)视为模板残留(已在 trade-off 声明);
- 关键词白名单覆盖含空格/数字/短词的模板家族(如 <来源 Gap 编号> <填这里> <待填> <请填写>),必须拦截。
"""

import check_step


def _errors(s):
    return check_step.check_placeholders(s, "probe")


def test_short_cjk_allowed():
    for s in ["<用户>", "<文献>", "<什么>", "<中文>"]:
        assert _errors(s) == [], f"{s} 不应被判为占位符"


def test_template_filler_words_blocked():
    for s in ["<待填>", "<请填写>", "<填这里>", "<研究主题>"]:
        assert _errors(s), f"{s} 应被判为占位符"


def test_hybrid_whitelist_blocked():
    for s in ["<来源 Gap 编号>", "<Gap 编号>", "<具体哪几篇文献>", "<用户文献目录>"]:
        assert _errors(s), f"{s} 应被判为占位符"


def test_generic_4char_descriptive_blocked_contract():
    # v0.3.17 契约:4 汉字以上描述性尖括号一律视为模板残留(见 CHANGELOG trade-off)
    for s in ["<中文摘要>", "<显著水平>"]:
        assert _errors(s), f"{s} 应按契约拦截"


def test_clean_prose_no_false_positive():
    # 不含尖括号的正文不应命中
    assert _errors("用户目录与文献清单见附录。") == []
