# -*- coding: utf-8 -*-
"""编码稳健性回归(v0.3.x 审计批次 1)。

背景:Windows 下 stdout 重定向到管道/文件时,Python 默认用 locale 编码(cp936),
print("✅") 抛 UnicodeEncodeError —— 通过的报告也以退出码 1 结束。
旧测试全部强制 PYTHONIOENCODING=utf-8,恰好把这条真实用户路径完全遮蔽。

本文件刻意**不设**该环境变量(甚至显式模拟 GBK stdio),守住无兜底运行场景。
"""

import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CHECK_STEP = ROOT / "scripts" / "check_step.py"
INIT_PROJECT = ROOT / "scripts" / "init_project.py"
REVIEW = ROOT / "scripts" / "review.py"

# 模拟 Windows 传统管道场景:stdio 走 GBK。修复策略是脚本自强制 UTF-8 输出,
# 因此父进程统一按 UTF-8 解码(errors=replace 兜底)。
GBK_STDIO_ENV = {k: v for k, v in os.environ.items() if k != "PYTHONUTF8"}
GBK_STDIO_ENV["PYTHONIOENCODING"] = "gbk"


def _run(script: Path, *args: str):
    return subprocess.run(
        [sys.executable, str(script), *args],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=GBK_STDIO_ENV,
    )


def _make_step1_workdir(workdir: Path) -> None:
    """构造满足 GATES['1'] 的最小工作目录。"""
    workdir.mkdir(parents=True)
    content = "\n".join(
        [
            "# Step 1 输入清单",
            "模糊领域:AI 辅助的文献选题",
            "文献清单:",
            "- paper-a.pdf",
            "- paper-b.pdf",
            "",
        ]
    )
    (workdir / "Step1-input.md").write_text(content, encoding="utf-8")


def test_check_step_pass_survives_gbk_stdio():
    """PASS 场景在 GBK 管道下必须退出码 0,不得因 emoji 崩溃。"""
    with tempfile.TemporaryDirectory() as d:
        wd = Path(d) / "proj"
        _make_step1_workdir(wd)
        r = _run(CHECK_STEP, "--workdir", str(wd), "--step", "1")
        assert r.returncode == 0, (
            f"PASS 应以退出码 0 结束:\nstdout={r.stdout}\nstderr={r.stderr}"
        )
        assert "Traceback" not in r.stderr
        assert "PASS" in r.stdout


def test_check_step_fail_report_survives_gbk_stdio():
    """FAIL 报告同样含 ❌/建议文案,GBK 管道下必须完整打印错误列表。"""
    with tempfile.TemporaryDirectory() as d:
        r = _run(CHECK_STEP, "--workdir", d, "--step", "1")
        assert r.returncode == 1
        assert "Traceback" not in r.stderr
        assert "FAIL" in r.stdout


def test_init_project_survives_gbk_stdio():
    """init 在 14 个文件全部写盘后打印 ✅ —— 崩溃会让调用方误判初始化失败。"""
    with tempfile.TemporaryDirectory() as d:
        wd = Path(d) / "proj"
        r = _run(INIT_PROJECT, "--workdir", str(wd))
        assert r.returncode == 0, f"init 应成功:\n{r.stdout}\n{r.stderr}"
        assert "Traceback" not in r.stderr
        assert (wd / "00_任务元信息.md").exists()


def test_review_topics_survives_gbk_stdio():
    """review --target topics 的 .format 大模板路径顺带补覆盖。"""
    with tempfile.TemporaryDirectory() as d:
        r = _run(REVIEW, "--workdir", d, "--target", "topics")
        assert r.returncode == 0, f"review topics 应成功:\n{r.stdout}\n{r.stderr}"
        assert "Traceback" not in r.stderr
        assert (Path(d) / "review_topics.md").exists()


def test_gbk_encoded_artifact_gets_friendly_error():
    """编辑器存成 GBK 的产物文件应得到「转存 UTF-8」提示,而非裸 traceback。"""
    with tempfile.TemporaryDirectory() as d:
        wd = Path(d)
        content = "模糊领域:X\n文献清单:\n- a.pdf\n- b.pdf\n"
        (wd / "Step1-input.md").write_bytes(content.encode("gbk"))
        # 用默认(非 GBK 强制)环境跑,贴近真实用户双击/agent 直调场景
        env = {k: v for k, v in os.environ.items() if k != "PYTHONIOENCODING"}
        r = subprocess.run(
            [sys.executable, str(CHECK_STEP), "--workdir", str(wd), "--step", "1"],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=env,
        )
        assert r.returncode != 0
        assert "UTF-8" in r.stderr, f"应有转存提示:\n{r.stderr}"
        assert "Traceback" not in r.stderr
