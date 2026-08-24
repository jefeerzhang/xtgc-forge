# -*- coding: utf-8 -*-
"""闸门函数直测(v0.3.x 审计批次 4)。

check_rerun_record / check_topic_scores / check_readability 的分支此前
零直测,golden 只走 happy path。本文件逐分支构造输入。
"""

import json
import tempfile
from pathlib import Path

import check_step


def _td():
    return tempfile.TemporaryDirectory()


def _write(td, name, text):
    Path(td.name, name).write_text(text, encoding="utf-8")


# ---------- check_rerun_record 三分支 ----------

def test_rerun_declared_without_record_fails():
    td = _td()
    try:
        wd = Path(td.name)
        report = wd / "00_研究计划报告.md"
        report.write_text("## 复跑说明\n本次为复跑。\n", encoding="utf-8")
        ok, errors = check_step.check_rerun_record(wd, report)
        assert not ok and any("00_复跑决策记录" in e for e in errors)
    finally:
        td.cleanup()


def test_rerun_empty_shell_record_fails():
    td = _td()
    try:
        wd = Path(td.name)
        report = wd / "00_研究计划报告.md"
        report.write_text("复跑说明:本次运行是复跑。\n", encoding="utf-8")
        _write(td, "00_复跑决策记录.md", "<占位>\n")
        ok, errors = check_step.check_rerun_record(wd, report)
        assert not ok, f"空壳记录应拦截;errors={errors}"
        assert any("空壳" in e for e in errors)
    finally:
        td.cleanup()


def test_rerun_valid_record_passes():
    td = _td()
    try:
        wd = Path(td.name)
        report = wd / "00_研究计划报告.md"
        report.write_text("复跑说明:本次运行是复跑。\n", encoding="utf-8")
        content = (
            "# 复跑决策记录\n\n"
            "用户当次原话:「按上次的选题继续跑一遍,不要再问我问题」\n"
            "决策时间:2026-08-24\n"
            "说明:沿用既有文献清单与主推主题,仅重跑校验环节。\n"
        )
        _write(td, "00_复跑决策记录.md", content)
        ok, errors = check_step.check_rerun_record(wd, report)
        assert ok, f"合法记录应通过;errors={errors}"
    finally:
        td.cleanup()


# ---------- check_topic_scores 变异 ----------

def _candidate(label, decision, t_score, tier, **overrides):
    c = {
        "label": label,
        "title": f"{label}的标准标题文本",
        "decision": decision,
        "scores": {k: 3 for k in check_step.SCORE_KEYS},
        "research_type": "推断性研究",
        "reveals": f"{label}揭示了机制层面的因果链条差异",
        "t_score": t_score,
        "tier": tier,
    }
    if decision == "dropped":
        c["kill_rule"] = "证据不足以支撑因果识别"
    c.update(overrides)
    return c


def _baseline_json(tmp_name="topic_scores.json"):
    candidates = [
        _candidate("甲", "selected", 0.40, "innovative"),
        _candidate("乙", "selected", 0.60, "safe"),
        _candidate("丙", "selected", 0.45, "differentiated"),
        _candidate("丁", "dropped", 0.70, "safe"),
        _candidate("戊", "dropped", 0.30, "innovative"),
    ]
    return json.dumps({"candidates": candidates}, ensure_ascii=False)


def _run_scores(json_text):
    td = _td()
    try:
        _write(td, "topic_scores.json", json_text)
        return check_step.check_topic_scores(Path(td.name))
    finally:
        td.cleanup()


def test_bool_score_rejected():
    data = json.loads(_baseline_json())
    data["candidates"][0]["scores"]["importance"] = True
    ok, errors = _run_scores(json.dumps(data, ensure_ascii=False))
    assert not ok and any("importance" in e and "不是整数" in e for e in errors), errors


def test_dropped_without_kill_rule_flagged():
    data = json.loads(_baseline_json())
    del data["candidates"][3]["kill_rule"]
    ok, errors = _run_scores(json.dumps(data, ensure_ascii=False))
    assert not ok and any("kill_rule" in e for e in errors), errors


def test_reveals_copying_title_flagged_even_with_padded_title():
    """标题带尾随空格不应绕过抄题检测。"""
    long_title = "数字平台的算法透明度如何重塑劳动者议价能力的实证考察"
    data = json.loads(_baseline_json())
    data["candidates"][0]["title"] = long_title + "\u3000"  # 尾随空白
    data["candidates"][0]["reveals"] = long_title
    ok, errors = _run_scores(json.dumps(data, ensure_ascii=False))
    assert not ok and any("抄了题目" in e for e in errors), errors


# ---------- check_readability 断句 ----------

def test_exclamation_mark_bounds_sentences():
    """全角 ！ 是句界:两短句以 ！ 相邻不得拼成超长句误报。"""
    s1 = "句界测试第一分句" * 8  # 64 字,单句不越线
    s2 = "句界测试第二分句" * 8  # 64 字
    assert len(s1) <= check_step.MAX_BODY_SENTENCE
    assert len(s1) + len(s2) > check_step.MAX_BODY_SENTENCE
    content = f"{s1}！{s2}。\n"
    errors = check_step.check_readability(content)
    assert errors == [], f"！ 应作句界,不应报超长句;errors={errors}"


def test_exclamation_adjacent_long_sentence_still_caught():
    """守卫:修复不得把断句闸整个放空 —— 无句界真超长仍要报。"""
    long_text = "无句界连续长文" * 20  # 140 字,无任何句读
    errors = check_step.check_readability(long_text + "\n")
    assert any("超过" in e for e in errors), f"无句界超长文本应被抓;errors={errors}"


# ---------- _extract_section 边界 ----------

def test_extract_section_adjacent_heading_bounds_section():
    """紧贴标题行下方(无空行)的同级标题应作分节边界(off-by-one 回归)。"""
    content = "# 第一段\n# 第二段\n第二段的正文内容。\n"
    sec = check_step._extract_section(content, "第一段", ["第二段"])
    assert "第二段" not in sec, f"同级相邻标题应截断本节;got={sec!r}"


def test_extract_section_deep_same_name_subsection_not_boundary():
    """上级章节内的深层同名小节不得提前截断(层级感知回归)。"""
    content = (
        "# 第一章\n"
        "### 第二章(草稿小节)\n"
        "第一章的正文内容继续展开。\n"
        "# 第二章\n"
        "第二章正式正文。\n"
    )
    sec = check_step._extract_section(content, "第一章", ["第二章"])
    assert "第一章的正文内容继续展开" in sec, f"深层同名小节不应提前截断;got={sec!r}"
    assert "第二章正式正文" not in sec


# ---------- 反坍缩错误信息自洽 ----------

def test_tier_mismatch_message_mentions_modal_zone_for_high_tscore():
    """t_score=0.85 时错误信息不得声称「0.55≤safe<0.80」自相矛盾。"""
    td = _td()
    try:
        data = json.loads(_baseline_json())
        data["candidates"][1]["t_score"] = 0.85
        data["candidates"][1]["tier"] = "differentiated"  # 推导应为 safe → 触发不一致提示
        _write(td, "topic_scores.json", json.dumps(data, ensure_ascii=False))
        ok, errors = check_step.check_anti_collapse(Path(td.name))
        msg = "\n".join(errors)
        assert not ok
        assert "模态区" in msg, f"高 t_score 提示应指向模态区:\n{msg}"
        assert "0.55≤safe<0.80" not in msg, f"旧文案与实际值矛盾:\n{msg}"
    finally:
        td.cleanup()
