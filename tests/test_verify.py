# -*- coding: utf-8 -*-
"""
test_verify.py — check_step_lib 新公共 API 的契约测试。

覆盖:
  - import check_step → 11 个旧 test_* 期望的属性都存在
  - verify(workdir, step) 返回 Verdict 实例
  - Verdict.passed / Verdict.errors 语义
  - list(verdict) == [bool, list] 向后兼容 unpack
  - check_step_router 是 check_step 的别名
  - CLI 入口(`python scripts/check_step.py --help`)能起,不报错
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))


def _import_check_step():
    import check_step
    return check_step


def test_shim_imports_cleanly():
    """旧入口 `import check_step` 仍可用(shim 重导出全部)。"""
    cs = _import_check_step()
    assert cs is not None


def test_shim_exposes_eight_check_gates():
    """8 个 check_X 全部可从 shim 访问。"""
    cs = _import_check_step()
    expected = [
        "check_placeholders", "check_step6_quality", "check_interaction_log",
        "check_rerun_record", "check_readability", "check_topic_scores",
        "check_anti_collapse", "check_review",
    ]
    for name in expected:
        assert hasattr(cs, name), f"shim 缺 {name}"
        assert callable(getattr(cs, name))


def test_shim_exposes_router_and_step_rules():
    """check_step router + STEP_RULES 表都能取到。"""
    cs = _import_check_step()
    assert callable(cs.check_step)
    assert isinstance(cs.STEP_RULES, dict)
    assert set(cs.STEP_RULES.keys()) >= {"2c", "3a", "3b", "6"}


def test_shim_exposes_new_public_api():
    """verify() + Verdict + check_step_router/detail 是新增公共 API。"""
    cs = _import_check_step()
    assert callable(cs.verify)
    assert isinstance(cs.Verdict, type)
    assert callable(cs.check_step_router)
    assert callable(cs.check_step_detail)


def test_verify_returns_verdict_instance():
    """verify(tmp_empty_workdir, '6') → Verdict 实例(空目录必 fail)。"""
    import tempfile
    cs = _import_check_step()
    with tempfile.TemporaryDirectory() as d:
        v = cs.verify(d, "6")
        assert isinstance(v, cs.Verdict)
        assert v.step == "6"
        assert v.workdir == str(Path(d))
        assert isinstance(v.passed, bool)
        assert isinstance(v.errors, tuple)
        assert not v.passed


def test_verdict_unpacking_backward_compat():
    """list(verdict) == [passed, errors] 与旧 (passed, errors) tuple 兼容。"""
    cs = _import_check_step()
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        v = cs.verify(d, "6")
        passed, errors = v  # 旧代码:ok, errs = check_step(workdir, step)
        assert passed == v.passed
        assert list(errors) == list(v.errors)


def test_verify_rejects_unknown_step():
    """未知 step 应返回 errors(行为契约,值不锁死)。"""
    import tempfile
    cs = _import_check_step()
    with tempfile.TemporaryDirectory() as d:
        v = cs.verify(d, "99")
        assert isinstance(v, cs.Verdict)
        assert not v.passed
        assert len(v.errors) >= 1


def test_cli_help_runs():
    """`python scripts/check_step.py --help` 不抛异常。"""
    cli = SCRIPTS / "check_step.py"
    if not cli.exists():
        pytest.skip("scripts/check_step.py 不存在")
    r = subprocess.run(
        [sys.executable, str(cli), "--help"],
        capture_output=True, text=True, timeout=20,
    )
    assert r.returncode == 0, f"--help 失败: stdout={r.stdout!r} stderr={r.stderr!r}"
    assert "--step" in r.stdout


def test_import_path_does_not_break_existing_tests():
    """确保 `import check_step` 后调用 _tier_of 仍然能工作(test_gate_units 用)。"""
    cs = _import_check_step()
    # _tier_of 是私有 helper,但 test_gate_units 通过 from check_step import _tier_of 显式取
    # helpers.__all__ 已经包含它,shim 的 `import *` 也透出
    assert hasattr(cs, "_tier_of")
    assert cs._tier_of(0.6) == "safe"
    assert cs._tier_of(-0.1) == "out_of_band"


def test_self_version_reads_repo_root_skill_md():
    """helpers 在 check_step_lib/ 下,须爬到仓库根 SKILL.md,不能读成 unknown。"""
    cs = _import_check_step()
    ver = cs._self_version()
    skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    import re
    m = re.search(r'^version:\s*["\']?([^"\'\s]+)["\']?', skill, re.MULTILINE)
    assert m, "SKILL.md 应有 version"
    assert ver == m.group(1), f"期望 {m.group(1)!r},实际 {ver!r}"


def test_router_gbk_file_returns_error_not_systemexit():
    """非 UTF-8 产物应收成 errors,不得 sys.exit 杀掉 verify/router。"""
    import tempfile
    cs = _import_check_step()
    with tempfile.TemporaryDirectory() as d:
        wd = Path(d)
        content = "模糊领域:X\n文献清单:\n- a.pdf\n- b.pdf\n"
        (wd / "Step1-input.md").write_bytes(content.encode("gbk"))
        errors = cs.check_step_router(wd, "1")
        assert errors, "GBK 文件应有错误"
        assert any("UTF-8" in e for e in errors), errors
        v = cs.verify(wd, "1")
        assert not v.passed
        assert any("UTF-8" in e for e in v.errors)


def test_cli_pass_printed_once():
    """CLI 成功路径只打一行 PASS(dispatch 不再重复横幅)。"""
    golden = ROOT / "examples" / "漂绿治理-绿贷与环境税组合"
    r = subprocess.run(
        [sys.executable, str(SCRIPTS / "check_step.py"),
         "--workdir", str(golden), "--step", "6"],
        capture_output=True, text=True, encoding="utf-8", timeout=60,
        cwd=str(ROOT),
    )
    assert r.returncode == 0, r.stdout + r.stderr
    assert r.stdout.count("PASS") == 1, r.stdout


def test_step_all_emits_review_soft_warnings_to_stderr():
    """--step all 须把 review 过程建议打到 stderr,不进失败 bullet。"""
    golden = ROOT / "examples" / "漂绿治理-绿贷与环境税组合"
    r = subprocess.run(
        [sys.executable, str(SCRIPTS / "check_step.py"),
         "--workdir", str(golden), "--step", "all"],
        capture_output=True, text=True, encoding="utf-8", timeout=60,
        cwd=str(ROOT),
    )
    assert "review_scan.md" in r.stderr, r.stderr
    assert "过程建议" in r.stderr or "不存在" in r.stderr, r.stderr
    fail = [ln for ln in r.stdout.splitlines() if ln.startswith("  - ")]
    assert not any("review_" in ln for ln in fail), fail


def test_step_all_review_hard_fail_enters_errors():
    """--step all:review verdict 非法(硬 FAIL)须以 [review_scan.md] 前缀计入 errors。

    与软 WARN 相对:WARN 只走 stderr,硬 FAIL 是失败 bullet,进 router 返回列表。
    """
    import tempfile
    cs = _import_check_step()
    with tempfile.TemporaryDirectory() as d:
        wd = Path(d)
        (wd / "review_scan.md").write_text("verdict: MAYBE\n", encoding="utf-8")
        errors = cs.check_step_router(wd, "all")
        hit = [e for e in errors if e.startswith("[review_scan.md]") and "MAYBE" in e]
        assert hit, f"review 硬 FAIL 应带 [review_scan.md] 前缀进 errors,实际:\n{errors}"


def test_cli_step_all_review_hard_fail_exits_1_with_bullet():
    """CLI --step all:review 硬 FAIL → 退出码 1,失败 bullet 进 stdout;软 WARN 仍走 stderr。"""
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        wd = Path(d)
        (wd / "review_scan.md").write_text("verdict: MAYBE\n", encoding="utf-8")
        r = subprocess.run(
            [sys.executable, str(SCRIPTS / "check_step.py"),
             "--workdir", str(wd), "--step", "all"],
            capture_output=True, text=True, encoding="utf-8", timeout=60,
            cwd=str(ROOT),
        )
        assert r.returncode == 1, r.stdout + r.stderr
        bullets = [ln for ln in r.stdout.splitlines() if ln.startswith("  - ")]
        assert any(ln.startswith("  - [review_scan.md]") for ln in bullets), r.stdout
        # topics 的 review 文件缺失仍是软 WARN,只走 stderr
        assert "review_topics.md" in r.stderr, r.stderr


def test_verify_exposes_soft_warnings_without_blocking():
    """verify('--step all') 把过程建议放进 soft_warnings,不进 errors、不挡 passed 半边。"""
    import tempfile
    cs = _import_check_step()
    with tempfile.TemporaryDirectory() as d:
        wd = Path(d)
        # 仅缺 review → soft;其余闸门也会 fail,但 soft 必须非空且不含硬 verdict 错
        v = cs.verify(wd, "all")
        assert v.soft_warnings, "缺 review 时应有过程建议"
        assert any("review_scan.md" in w for w in v.soft_warnings), v.soft_warnings
        assert not any(w in v.errors for w in v.soft_warnings), (
            "soft 不得混进 errors", v.errors, v.soft_warnings
        )
        # 有合法 review 时 soft 可空或仅剩其它建议;硬非法仍只在 errors
        (wd / "review_scan.md").write_text(
            "verdict: PASS\nreviewer: reviewer-deadbeef\n信任边界:无密码学身份保证\n",
            encoding="utf-8",
        )
        (wd / "review_topics.md").write_text(
            "verdict: PASS\nreviewer: reviewer-deadbeef\n信任边界:无密码学身份保证\n",
            encoding="utf-8",
        )
        v2 = cs.verify(wd, "all")
        assert not any("不存在" in w for w in v2.soft_warnings), v2.soft_warnings
        assert not any("MAYBE" in e for e in v2.errors)


def test_step_3a_anti_collapse_section_header_no_extra_space():
    """Step 3a 反坍缩分段头须为「--- 反坍缩校验失败 ---」,不得多空格。"""
    import sys
    import tempfile
    sys.path.insert(0, str(SCRIPTS))
    from check_step_lib.dispatch import _check_step_3a  # type: ignore

    with tempfile.TemporaryDirectory() as d:
        wd = Path(d)
        # 直接打额外规则:空 workdir → scores/反坍缩均失败,断言分段头字面量
        errors = _check_step_3a(wd, "", wd / "dummy.md", False)
        assert "--- 反坍缩校验失败 ---" in errors, errors
        assert "--- 反坍缩 校验失败 ---" not in errors
        assert "--- topic_scores.json 校验失败 ---" in errors, errors


def test_detail_single_pass_soft_matches_verify():
    """check_step_detail 与 verify 同源;CLI soft 与 Verdict.soft_warnings 一致。"""
    import tempfile
    cs = _import_check_step()
    with tempfile.TemporaryDirectory() as d:
        wd = Path(d)
        (wd / "review_scan.md").write_text("verdict: MAYBE\n", encoding="utf-8")
        errs, soft = cs.check_step_detail(wd, "all")
        v = cs.verify(wd, "all")
        assert list(v.errors) == errs
        assert list(v.soft_warnings) == soft
        assert any(e.startswith("[review_scan.md]") and "MAYBE" in e for e in errs)
        assert any("review_topics.md" in w for w in soft)
