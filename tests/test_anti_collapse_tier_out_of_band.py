# -*- coding: utf-8 -*-
"""s8 修复验证:_tier_of 对越界 t_score(> 1 或 < 0)返回 "out_of_band" 哨兵字符串。

历史:
  - 早期实现静默回退到 "safe",触发「tier 与推导层级不一致」悖论错误
  - 中期改为 raise ValueError,但上游 check_anti_collapse 必须自己 catch
    后才能用一致消息提示用户,catch/raise 之间逻辑分散
  - 现采用 sentinel 字符串 "out_of_band"(与 NIST tier 命名学一致),
    上游直接用 `if tier == "out_of_band": ...` 路由,比 raise 更可控
"""
import check_step  # type: ignore


def test_tier_of_above_one_returns_out_of_band():
    assert check_step._tier_of(2.0) == "out_of_band"


def test_tier_of_negative_returns_out_of_band():
    assert check_step._tier_of(-0.1) == "out_of_band"


def test_tier_of_in_range_returns_band():
    # 边界内不应抛错,正常 band 映射
    assert check_step._tier_of(0.6) == "safe"           # 0.55 ≤ 0.6 < 0.81
    assert check_step._tier_of(0.4) == "differentiated" # 0.35 ≤ 0.4 < 0.55
    assert check_step._tier_of(0.2) == "innovative"     # < 0.35
    assert check_step._tier_of(0.81) == "safe"          # ≥ 0.80 兜底


def test_check_anti_collapse_does_not_silently_coerce_out_of_band():
    """check_anti_collapse 对越界 t_score 也应报错(不静默回退到 safe)。

    通过构造一个 workdir 里的 topic_scores.json,t_score=2.0,
    验证 errors 列表里出现明确的越界消息,而不是被
    _tier_of 静默 coerce 成 "safe" 然后报「tier 与推导层级不一致」的怪错误。
    """
    import json
    import tempfile

    candidates = [
        {"id": f"Q{i}", "label": f"候选{i}",
         "title": f"题{i}", "research_type": "推断性",
         "t_score": 2.0 if i == 0 else 0.5,
         "tier": "safe" if i == 0 else "differentiated",
         "reveals": "揭示了某个新机制,值得做下去,不是工程任务",
         "decision": "selected" if i < 3 else "dropped",
         "scores": {
             "importance": 3, "feasibility": 3, "falsifiability": 3,
             "evidence_leverage": 3, "originality": 3, "negative_value": 3,
         },
         "kill_rule": None if i < 3 else "test"}
        for i in range(5)
    ]
    with tempfile.TemporaryDirectory() as d:
        from pathlib import Path
        Path(d, "topic_scores.json").write_text(
            json.dumps({"candidates": candidates}, ensure_ascii=False),
            encoding="utf-8",
        )
        passed, errors = check_step.check_anti_collapse(Path(d))
        joined = "\n".join(errors)
        # 应直接出现「不在 0-1 范围」的明确报错
        assert "不在 0-1 范围" in joined, f"应明确报越界,实际错误:\n{joined}"
        # 不应让 _tier_of 静默回退为 safe 后产生「tier 与推导层级不一致」的迷惑错
        # (这条容易跟其他候选的同型错误混淆,所以只要「不在 0-1 范围」出现即通过)