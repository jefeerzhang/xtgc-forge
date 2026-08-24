# -*- coding: utf-8 -*-
"""init_project 参数生效性 + 输出契约回归(v0.3.x 审计批次 3)。

背景:init_project 的 --name/--branch/--language 曾是空操作 —— 要替换的
占位符在任何模板正文中都不存在,自定义参数与默认参数生成逐字节相同的
14 个文件,而 SKILL.md 却在教用户传这些参数。
"""

import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INIT = ROOT / "scripts" / "init_project.py"
REVIEW = ROOT / "scripts" / "review.py"

SUBPROCESS_ENV = {**os.environ, "PYTHONIOENCODING": "utf-8"}


def _run(script: Path, *args: str):
    return subprocess.run(
        [sys.executable, str(script), "--workdir", *args],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=SUBPROCESS_ENV,
    )


def test_custom_params_change_generated_files():
    """不同的 --name/--branch/--language 必须产生可观测差异。"""
    with tempfile.TemporaryDirectory() as d:
        wd_a = Path(d) / "a"
        wd_b = Path(d) / "b"
        r_a = _run(INIT, str(wd_a), "--name", "县域数字治理研究", "--branch", "质性", "--language", "en-US")
        r_b = _run(INIT, str(wd_b))
        assert r_a.returncode == 0 and r_b.returncode == 0

        meta_a = (wd_a / "00_任务元信息.md").read_text(encoding="utf-8")
        meta_b = (wd_b / "00_任务元信息.md").read_text(encoding="utf-8")

        assert meta_a != meta_b, "自定义参数与默认参数不应生成相同文件"
        assert "县域数字治理研究" in meta_a
        assert "质性" in meta_a
        assert "en-US" in meta_a


def test_name_prefills_step1_theme():
    """--name 应落到 Step1-input.md 的模糊领域区,而非只改一个不存在的占位符。"""
    with tempfile.TemporaryDirectory() as d:
        wd = Path(d) / "proj"
        r = _run(INIT, str(wd), "--name", "平台算法透明度与劳动者权益")
        assert r.returncode == 0
        step1 = (wd / "Step1-input.md").read_text(encoding="utf-8")
        assert "平台算法透明度与劳动者权益" in step1


def test_refusal_message_printed_once():
    """拒绝覆盖时,同一句「工作目录已存在项目文件」不得重复打印两遍。"""
    with tempfile.TemporaryDirectory() as d:
        wd = Path(d) / "proj"
        assert _run(INIT, str(wd)).returncode == 0
        r2 = _run(INIT, str(wd))
        assert r2.returncode == 1
        count = r2.stderr.count("工作目录已存在项目文件")
        assert count == 1, f"提示应只出现一次,实际 {count} 次:\n{r2.stderr}"


def test_echoed_next_command_quotes_workdir_with_spaces():
    """回显的下一步命令必须给含空格路径加引号,复制即可用。"""
    with tempfile.TemporaryDirectory() as d:
        wd = Path(d) / "my proj"
        r = _run(INIT, str(wd))
        assert r.returncode == 0
        assert '--workdir "' in r.stdout or f"--workdir '{wd}" in r.stdout, (
            f"回显命令应对路径加引号:\n{r.stdout}"
        )


def test_review_reuse_error_goes_to_stderr():
    """拒绝覆盖错误应走 stderr(与 init_project 契约一致)。"""
    with tempfile.TemporaryDirectory() as d:
        r1 = _run(REVIEW, d, "--target", "scan")
        assert r1.returncode == 0
        r2 = _run(REVIEW, d, "--target", "scan")
        assert r2.returncode == 1
        combined = r2.stdout + r2.stderr
        assert "已存在" in combined
        assert "已存在" in r2.stderr, (
            f"拒绝覆盖信息应走 stderr:\nstdout={r2.stdout}\nstderr={r2.stderr}"
        )
