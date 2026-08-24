# -*- coding: utf-8 -*-
"""review.py 行为测试:覆盖 v0.3.x 工作目录解析回显契约。

mi21 验证:打印的下一步命令必须用 resolve 后的绝对路径,
而不是 --workdir 原始入参(避免 ~/foo、含 .. 的路径原样回显,
调用方复制命令后又跑不通)。
"""
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "review.py"

# 子进程强制 UTF-8 stdio:Windows 默认 cp936 会让中文输出乱码,测试按 utf-8 解码后断言失配
SUBPROCESS_ENV = {**os.environ, "PYTHONIOENCODING": "utf-8"}


def _run(workdir: str, *extra: str):
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--workdir", workdir, *extra],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=SUBPROCESS_ENV,
    )


def test_review_suggests_command_with_resolved_workdir():
    """review.py 把含 .. 的 --workdir resolve 为绝对路径后再回显。"""
    with tempfile.TemporaryDirectory() as d:
        # 先建好 subdir(且其父级目录存在),然后用含 .. 的路径指向它,
        # 模拟「Windows 下用户传一个没清干净 .. 的路径」场景
        nested = Path(d) / "subdir"
        nested.mkdir()
        weird = str(Path(d) / "subdir" / ".." / "subdir")
        r = _run(weird, "--target", "scan")
        assert r.returncode == 0, (
            f"review 应成功:\nstdout={r.stdout}\nstderr={r.stderr}"
        )
        # 下一步命令行的 --workdir 应是 resolve 后的绝对路径,不含原始 .. 组件
        out = r.stdout + r.stderr
        assert "--workdir" in out, f"应打印下一步命令:\n{out}"
        # 取出命令行中 --workdir 后到下一个空格分隔 token 之前的路径
        marker = "--workdir "
        idx = out.find(marker)
        assert idx != -1, f"应含 --workdir 提示:\n{out}"
        rest = out[idx + len(marker):]
        # 用下一个 space 作为路径边界(支持绝对路径中可能含 .. 但不含空格)
        end = rest.find(" --step ")
        assert end != -1, f"应含 --step 段以界定路径尾部:\n{rest}"
        after = rest[:end].strip()
        # v0.3.x 起回显命令给路径加引号(含空格路径复制即可用),剥掉引号再校验
        if after.startswith('"') and after.endswith('"'):
            after = after[1:-1]
        # resolve 后应得到真实子目录的绝对路径,不含 .. 组件
        assert ".." not in after, (
            f"resolve 后回显路径不应再含 .. 组件:raw='{weird}' → printed='{after}'"
        )
        assert Path(after).is_absolute(), f"回显路径应是绝对路径:{after}"
        # 而且应能定位回真实的 subdir
        assert Path(after).resolve() == nested.resolve(), (
            f"resolve 后应回到真实 subdir:printed='{after}'"
        )


def test_review_refuses_on_existing_template():
    """已存在的 review_*.md 应被拒绝(防静默覆盖)。"""
    with tempfile.TemporaryDirectory() as d:
        workdir = str(Path(d) / "proj")
        Path(workdir).mkdir()

        r1 = _run(workdir, "--target", "scan")
        assert r1.returncode == 0, f"首次生成应成功:\n{r1.stdout}{r1.stderr}"

        r2 = _run(workdir, "--target", "scan")
        assert r2.returncode == 1, "已存在审查模板时应拒绝"
        assert "已存在" in r2.stdout or "已存在" in r2.stderr


def test_review_rejects_invalid_target():
    """未知 --target 应被 argparse choices 拒绝。"""
    with tempfile.TemporaryDirectory() as d:
        workdir = str(Path(d) / "proj")
        Path(workdir).mkdir()
        r = _run(workdir, "--target", "bogus")
        assert r.returncode != 0, "未知 target 应被拒绝"
        err = r.stdout + r.stderr
        assert "invalid choice" in err or "未知" in err, (
            f"应含 invalid choice 提示:\n{err}"
        )
