# -*- coding: utf-8 -*-
"""金样例集成断言:主报告闸 PASS + --step all 恰好 2 个失败条目(仅 Step2a/5)。"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GOLDEN = ROOT / "examples" / "漂绿治理-绿贷与环境税组合"
SCRIPT = ROOT / "scripts" / "check_step.py"


def _run(step):
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--workdir", str(GOLDEN), "--step", step],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def test_golden_step6_passes():
    r = _run("6")
    assert r.returncode == 0, r.stdout + r.stderr


def test_golden_step_all_exactly_2_failures():
    r = _run("all")
    out = r.stdout + r.stderr
    # 失败条目形如 "  - [step 2a] ..."(两个空格 + 连字符),不能用 strip() 后再比前缀
    fail = [ln for ln in out.splitlines() if ln.startswith("  - ")]
    # 截至本次金样例:仅 Step2a 产物文件有意缺省(Step5 已补齐),
    # 故 --step all 仅 1 项失败。后续若 Step5 产物变缺省,把 1 改回 2 并补 [step 5] 断言。
    assert len(fail) == 1, f"预期恰好 1 项失败条目(Step2a),实际 {len(fail)}\n{out}"
    joined = "\n".join(fail)
    assert "[step 2a]" in joined, joined
    assert "review_" not in joined, f"review 不应出现在失败条目\n{joined}"


def test_golden_review_now_warn_not_fail():
    # v0.3.18 审查降级:缺省 review 文件在 scan-review/topics-review 仍应 PASS(WARN 不算失败)
    for step in ("scan-review", "topics-review"):
        r = _run(step)
        assert r.returncode == 0, f"{step} 应因软警告通过\n{r.stdout}{r.stderr}"
