# -*- coding: utf-8 -*-
"""版本单源一致性 + CHANGELOG 同版本重复检测(与 check-ready.sh 对账逻辑对齐)。

这几个测试不依赖 claude,可在 CI 直接跑。
"""

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _read_skill_version():
    text = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    m = re.search(r'^version:\s*["\']?([^"\'\s]+)["\']?', text, re.MULTILINE)
    return m.group(1) if m else None


def _read_readme_version():
    text = (ROOT / "README.md").read_text(encoding="utf-8")
    m = re.search(r"Version-v?(0\.[0-9]+\.[0-9]+)", text)
    return m.group(1) if m else None


def _read_changelog_top_version():
    text = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    m = re.search(r"^## v(0\.[0-9]+\.[0-9]+)", text, re.MULTILINE)
    return m.group(1) if m else None


def _marketplace_versions():
    p = ROOT / ".claude-plugin" / "marketplace.json"
    d = json.loads(p.read_text(encoding="utf-8"))
    vs = [d.get("metadata", {}).get("version")]
    vs += [x.get("version") for x in d.get("plugins", []) if isinstance(x, dict)]
    return [v for v in vs if v]


def _duplicate_headers(sample: str):
    headers = re.findall(r"^## v(0\.[0-9]+\.[0-9]+)", sample, re.MULTILINE)
    return {h for h in headers if headers.count(h) > 1}


def test_skill_readme_changelog_consistent():
    v = _read_skill_version()
    assert v, "SKILL.md 未读到版本号"
    assert _read_readme_version() == v, "README badge 与 SKILL.md 版本不一致"
    assert _read_changelog_top_version() == v, "CHANGELOG 顶部版本与 SKILL.md 不一致"


def test_marketplace_consistent_with_skill():
    v = _read_skill_version()
    assert v
    mp = _marketplace_versions()
    assert mp, "marketplace.json 未读到 version"
    for fv in mp:
        assert fv == v, f"发布通道版本 {fv} 与 SKILL.md {v} 不一致"


def test_duplicate_changelog_header_detected():
    sample = "# Changelog\n\n## v0.3.17 · a\n\n## v0.3.17 · b\n\n## v0.3.16 · c\n"
    dups = _duplicate_headers(sample)
    assert "0.3.17" in dups


def test_unique_changelog_header_not_flagged():
    sample = "# Changelog\n\n## v0.3.18 · a\n\n## v0.3.17 · b\n"
    dups = _duplicate_headers(sample)
    assert "0.3.18" not in dups
