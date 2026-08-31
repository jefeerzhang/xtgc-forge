# -*- coding: utf-8 -*-
"""vendor_sync / probe 根目录解析与 VERSION.md 契约。"""
import os
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SUBPROCESS_ENV = {**os.environ, "PYTHONIOENCODING": "utf-8"}


def _bash(args, cwd):
    return subprocess.run(
        ["bash", *args],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=SUBPROCESS_ENV,
    )


def test_vendor_sync_list_from_scripts_cwd_finds_vendor():
    """从 scripts/ 调用 list 必须扫到仓库根的 vendor/，不能用 pwd。"""
    r = _bash(["./vendor_sync.sh", "list"], cwd=ROOT / "scripts")
    out = r.stdout + r.stderr
    assert r.returncode == 0, out
    assert "academic-humanizer" in out, out
    assert "NO VERSION.md" not in out, out


def test_vendor_sync_list_from_repo_root():
    r = _bash(["scripts/vendor_sync.sh", "list"], cwd=ROOT)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "academic-humanizer" in r.stdout


def test_academic_humanizer_path_is_backticked_dot():
    text = (ROOT / "vendor" / "academic-humanizer" / "VERSION.md").read_text(
        encoding="utf-8"
    )
    m = re.search(r"`upstream_skill_path`\s*\|\s*`([^`]+)`", text)
    assert m is not None, "upstream_skill_path 未用反引号包住，parse_version_md 会得到空 path"
    assert m.group(1) == ".", m.group(1)
