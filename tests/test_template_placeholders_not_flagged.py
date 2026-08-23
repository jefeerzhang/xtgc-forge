# -*- coding: utf-8 -*-
"""s2 修复验证:init 生成的模板在 Step 1 闸门不应触发占位符 FAIL。

契约:
- `init_project.py` 生成的 Step1-input.md 含 `由 init_project.py 自动生成。请填写或修改。` 之类
  的字面提醒;这条字面文本原先匹配 `r"请填写或修改"` 无锚定正则,导致 Step 1 闸门对刚 init
  出来的项目误报 FAIL。
- 收紧为 `r"<请填写或修改>"`(尖括号锚定)后,模板中无尖括号的提醒不应触发占位符拦截。
"""
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INIT_SCRIPT = ROOT / "scripts" / "init_project.py"
CHECK_SCRIPT = ROOT / "scripts" / "check_step.py"


def _run_init(workdir):
    return subprocess.run(
        [sys.executable, str(INIT_SCRIPT), "--workdir", workdir],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def _run_check(workdir, step):
    return subprocess.run(
        [sys.executable, str(CHECK_SCRIPT), "--workdir", workdir, "--step", step],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def test_freshly_initialized_step1_does_not_flag_placeholders():
    """刚 init 的项目跑 Step 1 闸门,不应因为模板里的「请填写或修改」字面文本而误报。"""
    with tempfile.TemporaryDirectory() as d:
        workdir = str(Path(d) / "proj")
        r_init = _run_init(workdir)
        assert r_init.returncode == 0, (
            f"init 应成功:\nstdout={r_init.stdout}\nstderr={r_init.stderr}"
        )
        # 模板确实包含字面提醒
        step1 = (Path(workdir) / "Step1-input.md").read_text(encoding="utf-8")
        assert "请填写或修改" in step1, "模板应含「请填写或修改」字面提醒"

        r_check = _run_check(workdir, "1")
        # 真正会 FAIL 的是关键词缺失(模糊领域/文献清单模板里实际有,但内容太短),
        # 但占位符相关的错误不应出现。
        out = r_check.stdout + r_check.stderr
        assert "占位" not in out and "请填写或修改" not in out, (
            f"占位符模式不应被字面提醒误触:\n{out}"
        )


def test_placeholder_regex_anchored_to_angle_brackets():
    """直接验证 PLACEHOLDER_PATTERNS_RE 对「请填写或修改」的尖括号锚定行为。"""
    import check_step  # type: ignore

    # 字面「请填写或修改」(无尖括号)不应被「<请填写或修改>」模式拦
    # 注:同串里另有「由 init_project.py 自动生成」模板签名模式,
    # 那条是有意保留的(init 产物识别),与本次 s2 修复正交。
    matched = check_step.PLACEHOLDER_PATTERNS_RE.search("请填写或修改")
    assert matched is None or matched.group(0) != "请填写或修改", (
        f"无尖括号的「请填写或修改」不应被 s2 新规则拦:matched={matched}"
    )
    # 带尖括号的应被拦
    assert check_step.PLACEHOLDER_PATTERNS_RE.search("<请填写或修改>") is not None