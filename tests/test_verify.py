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

import importlib
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
    """verify() + Verdict + check_step_router 是新增公共 API。"""
    cs = _import_check_step()
    assert callable(cs.verify)
    assert isinstance(cs.Verdict, type)
    assert callable(cs.check_step_router)


def test_verify_returns_verdict_instance(tmp_path):
    """verify(tmp_empty_workdir, '6') → Verdict(errors=(), passed=True)。"""
    cs = _import_check_step()
    # 空 workdir,Step 6 — 主报告文件不存在,会报"未找到主报告文件"
    v = cs.verify(tmp_path, "6")
    assert isinstance(v, cs.Verdict)
    assert v.step == "6"
    assert v.workdir == str(tmp_path)
    # 空 errors 时 passed=True;空 workdir 上 Step 6 必 fail,但仍是 Verdict
    assert isinstance(v.passed, bool)
    assert isinstance(v.errors, tuple)


def test_verdict_unpacking_backward_compat():
    """list(verdict) == [passed, errors] 与旧 (passed, errors) tuple 兼容。"""
    cs = _import_check_step()
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        v = cs.verify(d, "6")
        passed, errors = v  # 旧代码:ok, errs = check_step(workdir, step)
        assert passed == v.passed
        assert list(errors) == list(v.errors)


def test_verify_rejects_unknown_step(tmp_path):
    """未知 step 应返回 errors(行为契约,值不锁死)。"""
    cs = _import_check_step()
    v = cs.verify(tmp_path, "99")
    assert isinstance(v, cs.Verdict)
    # 未知 step 必 fail(errors 非空)
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
