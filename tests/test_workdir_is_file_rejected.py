# -*- coding: utf-8 -*-
"""s1 修复:init_project.py 在 --workdir 路径已存在但不是目录时拒绝。

契约:
- 路径是已存在的文件(不是目录)→ sys.exit(1)
- 路径是已存在的目录 → 正常处理
- 路径不存在 → 创建目录,正常处理
"""
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "init_project.py"


def _run(workdir: str, *extra: str):
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--workdir", workdir, *extra],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def test_workdir_is_file_rejected():
    """把一个 FILE 当作 --workdir 传进去,应拒绝并退出码 1。"""
    with tempfile.TemporaryDirectory() as d:
        # 在临时目录里建一个文件,而不是目录
        file_path = Path(d) / "this-is-a-file.txt"
        file_path.write_text("not a directory", encoding="utf-8")
        assert file_path.is_file()
        assert not file_path.is_dir()

        r = _run(str(file_path))
        assert r.returncode == 1, (
            f"--workdir 是文件时应拒绝:\nstdout={r.stdout}\nstderr={r.stderr}"
        )
        assert "不是目录" in r.stderr or "不是目录" in r.stdout, (
            f"stderr 应提示「不是目录」:\nstderr={r.stderr}"
        )
        # 文件本身应保持不变(init 没有破坏它的语义)
        assert file_path.read_text(encoding="utf-8") == "not a directory"