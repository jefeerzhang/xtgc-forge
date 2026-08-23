# -*- coding: utf-8 -*-
"""init_project.py 防静默覆盖测试(v0.3.x 起的 TRACKED_FILES + --force 契约)。

用 subprocess 跑真实脚本(隔离 sys.path),不直接 import init_project,
确保覆盖 argparse / sys.exit / stderr 路径。
"""

import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "init_project.py"

# 子进程强制 UTF-8 stdio:Windows 默认 cp936 会让中文输出乱码,测试按 utf-8 解码后断言失配
SUBPROCESS_ENV = {**os.environ, "PYTHONIOENCODING": "utf-8"}


def _run(workdir: str, *extra: str):
    """调用 init_project.py --workdir <workdir> [extra...]。"""
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--workdir", workdir, *extra],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=SUBPROCESS_ENV,
    )


def test_init_then_refuse_then_force_overwrites():
    with tempfile.TemporaryDirectory() as d:
        workdir = str(Path(d) / "proj")

        # 1) 空目录首跑 → exit 0,模板就位
        r1 = _run(workdir)
        assert r1.returncode == 0, f"首次 init 应成功:\n{r1.stdout}{r1.stderr}"
        assert (Path(workdir) / "00_任务元信息.md").exists()
        assert (Path(workdir) / "Step1-input.md").exists()

        # 2) 手动改写一个 Step1-input.md,模拟用户已编辑
        user_content = "# 用户已编辑的内容(不应被静默覆盖)\n"
        (Path(workdir) / "Step1-input.md").write_text(user_content, encoding="utf-8")

        # 3) 不带 --force 再跑 → 退出码 1,原文件保持原样
        r2 = _run(workdir)
        assert r2.returncode == 1, f"已存在项目文件时 init 应拒绝:\n{r2.stdout}{r2.stderr}"
        assert "工作目录已存在项目文件" in r2.stderr
        assert (Path(workdir) / "Step1-input.md").read_text(encoding="utf-8") == user_content

        # 4) 带 --force 再跑 → exit 0,文件被覆盖(模板内容会替换用户内容)
        r3 = _run(workdir, "--force")
        assert r3.returncode == 0, f"--force 应允许覆盖:\n{r3.stdout}{r3.stderr}"
        # stderr 应列出将被覆盖的文件
        assert "--force" in r3.stderr or "覆盖" in r3.stderr
        overwritten = (Path(workdir) / "Step1-input.md").read_text(encoding="utf-8")
        assert "用户已编辑的内容" not in overwritten, "--force 后模板应替换用户内容"
        assert "Step 1" in overwritten or "模糊领域" in overwritten, "应为模板内容"


def test_delivery_note_alone_triggers_overwrite_protection():
    """目录里只有 00_交付说明.md(TRACKED_FILES 成员)时,init 也应拒绝覆盖。"""
    with tempfile.TemporaryDirectory() as d:
        workdir = Path(d) / "proj"
        workdir.mkdir()
        note = workdir / "00_交付说明.md"
        note.write_text("# 用户自己的交付说明\n", encoding="utf-8")

        r = _run(str(workdir))
        assert r.returncode == 1, f"仅有 00_交付说明.md 时也应拒绝:\n{r.stdout}{r.stderr}"
        assert "工作目录已存在项目文件" in r.stderr
        assert note.read_text(encoding="utf-8") == "# 用户自己的交付说明\n"