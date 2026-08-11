#!/usr/bin/env python3
"""
选题工坊 · 刚性闸门检查脚本 (v0.3.3)

校验每个 Step 产物的完整性、关键字段、最小内容长度。
Step 6 额外校验主报告质量:附录结构、矩阵表行、段落深度、禁模板占位符。

支持:
  --step 1/2a/2b/2c/3a/3b/4/5/6      单 Step 校验
  --step all                         一次性校验全部(含 review)
  --step scores                      topic_scores.json 单独校验
  --step scan-review                 review_scan.md 校验
  --step topics-review               review_topics.md 校验

用法:
  python scripts/check_step.py --workdir <dir> --step <step>
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path


# 每个 Step 的闸门校验规则
GATES = {
    "1": {
        "file": "Step1-input.md",
        "min_lines": 5,
        "required_keywords": ["模糊领域", "文献清单"],
        "fail_msg": "Step 1: 输入清单缺少'模糊领域'或'文献清单'字段",
    },
    "2a": {
        "file": "Step2a-points.md",
        "min_lines": 10,
        "required_keywords": ["研究问题", "主要发现"],
        "fail_msg": "Step 2a: 文献要点卡缺少'研究问题'或'主要发现'",
    },
    "2b": {
        "file": "Step2b-literature-matrix.md",
        "min_lines": 5,
        "required_keywords": ["作者", "年份", "方法", "主要发现"],
        "fail_msg": "Step 2b: 文献矩阵缺少关键字段(作者/年份/方法/主要发现)",
    },
    "2c": {
        "file": "Step2c-gap-verdicts.md",
        "min_lines": 8,
        "required_keywords": ["gap", "证据来源", "重要性"],
        "fail_msg": "Step 2c: Gap 裁定缺少'证据来源'或'重要性'字段",
        "ban_placeholders": True,
    },
    "3a": {
        "file": "Step3a-candidate-themes.md",
        "min_lines": 15,
        "required_keywords": ["主推", "备选", "理论贡献", "方法可行性", "研究类型"],
        "min_count": {
            "主推": 3,
            "备选": 2,
            "研究类型": 5,
        },
        "fail_msg": "Step 3a: 候选主题格式不对。需要 3 主推 + 2 备选,各含理论贡献 + 方法可行性 + 研究类型",
    },
    "3b": {
        "file": "Step3b-selected-theme.md",
        "min_lines": 5,
        "required_keywords": ["研究问题", "理论贡献", "研究类型"],
        "fail_msg": "Step 3b: 选定主题缺少关键字段",
    },
    "4": {
        "file": "Step4-hypotheses.md",
        "min_lines": 15,
        "required_keywords": ["假设", "DAG", "反事实", "可证伪", "SESOI"],
        "min_count": {
            "假设陈述": 3,
        },
        "fail_msg": "Step 4: 假设文件缺少'假设陈述/DAG/反事实/可证伪/SESOI'字段,或假设数 < 3",
        "ban_placeholders": True,
    },
    "5": {
        "file": "Step5-identification-strategy.md",
        "min_lines": 10,
        # 工具变量不再强制:纯 DID 可写「本节不适用」
        "required_keywords": ["识别策略", "稳健性"],
        "fail_msg": "Step 5: 因果识别策略缺少'识别策略/稳健性'字段",
    },
    "6": {
        "file": "00_研究计划报告.md",
        "min_lines": 120,
        "required_keywords": [
            "选的题是什么",
            "为什么选这个题",
            "选题的意义",
            "假设是什么",
            "为什么能写出这样的假设",
            "后面应该怎么做",
            "可证伪",
            "文献矩阵",
            "Gap",
            "附录 A",
            "附录 B",
            "附录 C",
            "附录 D",
            "附录 E",
        ],
        "fail_msg": "Step 6: 缺少 00_研究计划报告.md,或未按六段+整合附录框架撰写",
    },
}


SCORE_KEYS = [
    "importance",
    "feasibility",
    "falsifiability",
    "evidence_leverage",
    "originality",
    "negative_value",
]

VALID_STEPS = list(GATES.keys()) + ["all", "scores", "scan-review", "topics-review"]

# 模板/空壳残留(出现则 FAIL)
PLACEHOLDER_PATTERNS = [
    r"<请填写",
    r"<YYYY-MM-DD>",
    r"<研究主题>",
    r"\bTODO\b",
    r"\bTBD\b",
    r"（待填）",
    r"\(待填\)",
    r"请填写或修改",
    r"由 `?init_project\.py`? 自动生成",
]


def _count_cjk_and_alnum(text: str) -> int:
    """粗算有效字符数(中日韩 + 字母数字)。"""
    return len(re.findall(r"[\u4e00-\u9fffA-Za-z0-9]", text))


def _extract_section(content: str, heading_substr: str, next_headings: list[str]) -> str:
    """按标题子串截取章节正文,直到下一个一级/二级标题候选。"""
    # 找含 heading_substr 的 markdown 标题行
    lines = content.splitlines()
    start = None
    for i, line in enumerate(lines):
        if line.lstrip().startswith("#") and heading_substr in line:
            start = i + 1
            break
    if start is None:
        return ""
    end = len(lines)
    for j in range(start, len(lines)):
        line = lines[j]
        if not line.lstrip().startswith("#"):
            continue
        # 遇到其他六段标题或附录标题则停
        for nh in next_headings:
            if nh in line and heading_substr not in line:
                end = j
                return "\n".join(lines[start:end])
        if re.match(r"^#{1,2}\s+", line) and j > start:
            # 同级或更高级标题
            level = len(line) - len(line.lstrip("#"))
            start_line = lines[start - 1]
            start_level = len(start_line) - len(start_line.lstrip("#"))
            if level <= start_level and heading_substr not in line:
                end = j
                break
    return "\n".join(lines[start:end])


def _count_paragraphs(section: str) -> int:
    """非空段落数(空行分隔,且不是纯表格行/纯标题)。"""
    chunks = re.split(r"\n\s*\n", section.strip())
    n = 0
    for c in chunks:
        c = c.strip()
        if not c:
            continue
        if c.startswith("#"):
            continue
        # 纯表格块不算论述段落
        rows = [ln for ln in c.splitlines() if ln.strip()]
        if rows and all(ln.strip().startswith("|") for ln in rows):
            continue
        if _count_cjk_and_alnum(c) >= 40:
            n += 1
    return n


def _count_matrix_data_rows(content: str) -> int:
    """
    统计文献矩阵数据行。
    优先:附录 A 区域内 | L1 | / | L2 | 或首列像文献 ID 的表行;
    回退:全文 markdown 表中非表头、非分隔行。
    """
    # 截取附录 A
    appendix = content
    m = re.search(r"附录\s*A[^\n]*\n([\s\S]*?)(?=\n##\s*附录\s*B|\n#\s*附录\s*B|\Z)", content)
    if m:
        appendix = m.group(1)

    rows = 0
    for line in appendix.splitlines():
        s = line.strip()
        if not s.startswith("|"):
            continue
        if re.match(r"^\|?\s*:?-+:?\s*\|", s):
            continue
        # 表头
        if "作者" in s and "年份" in s:
            continue
        if re.match(r"^\|\s*ID\s*\|", s, re.I):
            continue
        # 数据行:含 L1/L2… 或至少 5 个单元格
        cells = [c.strip() for c in s.strip("|").split("|")]
        if len(cells) < 5:
            continue
        if re.search(r"\bL\d+\b", s) or (cells[0] and cells[0] not in ("ID", "编号", "—", "-")):
            # 排除仍是表头变体
            if cells[0] in ("作者", "文献", "字段"):
                continue
            rows += 1
    return rows


def check_placeholders(content: str, label: str) -> list[str]:
    errors = []
    for pat in PLACEHOLDER_PATTERNS:
        if re.search(pat, content):
            errors.append(f"{label}: 含模板/占位残留,匹配 /{pat}/")
    return errors


def check_step6_quality(content: str) -> list[str]:
    """Step 6 主报告质量闸(防空壳)。"""
    errors = []
    errors.extend(check_placeholders(content, "Step6 主报告"))

    # 附录标题
    for app in ["附录 A", "附录 B", "附录 C", "附录 D", "附录 E"]:
        if app not in content:
            errors.append(f"Step6: 缺少整合附录标题「{app}」")

    # 禁止只丢路径
    if re.search(r"详见\s*`?Step2b", content) and _count_matrix_data_rows(content) < 1:
        errors.append("Step6: 不得以「详见 Step2b」代替文内文献矩阵")

    # 矩阵数据行
    matrix_rows = _count_matrix_data_rows(content)
    if matrix_rows < 5:
        errors.append(
            f"Step6: 附录 A 文献矩阵数据行 {matrix_rows} < 5"
            f"(须收录完整矩阵,至少 5 篇文献行)"
        )

    # 六段最小论述量
    six = [
        ("选的题是什么", 200, 1),
        ("为什么选这个题", 600, 3),
        ("选题的意义", 300, 2),
        ("假设是什么", 600, 3),
        ("为什么能写出这样的假设", 400, 2),
        ("后面应该怎么做", 300, 2),
    ]
    next_heads = [h for h, _, _ in six] + ["附录 A", "附录 B", "整合附录"]

    for heading, min_chars, min_paras in six:
        sec = _extract_section(content, heading, next_heads)
        if not sec.strip():
            errors.append(f"Step6: 未能解析章节「{heading}」正文")
            continue
        chars = _count_cjk_and_alnum(sec)
        paras = _count_paragraphs(sec)
        if chars < min_chars:
            errors.append(
                f"Step6:「{heading}」有效字符约 {chars} < 最低 {min_chars}"
                f"(论述过薄,禁止一句话观点)"
            )
        if paras < min_paras:
            errors.append(
                f"Step6:「{heading}」有效段落 {paras} < 最低 {min_paras}"
                f"(须分段展开,表格不能代替论述)"
            )

    # 假设可证伪出现次数(防只在目录出现一次)
    if content.count("可证伪") < 2:
        errors.append("Step6:「可证伪」出现不足 2 次(假设段须真正写可证伪条件)")

    # 总长度
    if _count_cjk_and_alnum(content) < 3000:
        errors.append(
            f"Step6: 全文有效字符约 {_count_cjk_and_alnum(content)} < 3000"
            f"(主报告过短,未达开题框架厚度)"
        )

    return errors


def check_topic_scores(workdir: Path) -> tuple[bool, list[str]]:
    """校验 topic_scores.json。"""
    errors = []
    score_file = workdir / "topic_scores.json"

    if not score_file.exists():
        return (False, ["topic_scores.json 不存在,请用 init_project.py 创建或手动生成"])

    try:
        data = json.loads(score_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        return (False, [f"topic_scores.json 不是合法 JSON:{e}"])

    if "candidates" not in data:
        return (False, ["topic_scores.json 缺少 'candidates' 字段"])

    candidates = data["candidates"]
    if len(candidates) != 5:
        return (False, [f"candidates 长度 {len(candidates)} ≠ 5(应 3 主推 + 2 备选)"])

    selected_count = sum(1 for c in candidates if c.get("decision") == "selected")

    if selected_count != 3:
        errors.append(f"decision='selected' 的候选数 {selected_count} ≠ 3(应 3 主推池;非用户最终唯一)")

    for i, c in enumerate(candidates):
        prefix = f"候选 #{i+1} ({c.get('label', '?')})"

        if "scores" not in c:
            errors.append(f"{prefix}: 缺少 'scores' 字段")
            continue

        scores = c["scores"]
        for key in SCORE_KEYS:
            if key not in scores:
                errors.append(f"{prefix}: 缺少评分 '{key}'")
            elif not isinstance(scores[key], int):
                errors.append(f"{prefix}: 评分 '{key}' 不是整数")
            elif not (1 <= scores[key] <= 5):
                errors.append(f"{prefix}: 评分 '{key}'={scores[key]} 不在 1-5 范围")

        if "decision" not in c:
            errors.append(f"{prefix}: 缺少 'decision' 字段")
        elif c["decision"] == "dropped" and not c.get("kill_rule"):
            errors.append(f"{prefix}: decision='dropped' 必须填 'kill_rule'")

        if "research_type" not in c:
            errors.append(f"{prefix}: 缺少 'research_type' 字段")

    return (len(errors) == 0, errors)


def check_review(workdir: Path, target: str) -> tuple[bool, list[str]]:
    """校验 review_{target}.md 是否 PASS。"""
    errors = []
    review_file = workdir / f"review_{target}.md"

    if not review_file.exists():
        return (
            False,
            [
                f"review_{target}.md 不存在,请用 scripts/review.py 生成模板,由独立子 agent 填入 verdict"
            ],
        )

    content = review_file.read_text(encoding="utf-8")

    if "verdict" not in content.lower():
        errors.append("缺少 verdict 字段")

    has_pass = (
        "verdict:**`PASS`" in content
        or "verdict:`PASS`" in content
        or "verdict:PASS" in content
        or "**verdict**:`PASS`" in content
    )
    has_p0 = "P0_OPEN" in content or "P0-OPEN" in content

    if not has_pass and not has_p0:
        errors.append("verdict 字段未填写 PASS / P0_OPEN / FAIL")
    elif has_p0:
        if "P0-1" not in content and "P0-2" not in content:
            errors.append("verdict=P0_OPEN 但未列出具体 P0 问题")

    if "reviewer" not in content.lower():
        errors.append("缺少审查者 ID(reviewer-<hash>)")

    if "密码学身份保证" not in content and "信任边界" not in content:
        errors.append("缺少信任边界声明")

    # 模板未填
    if re.search(r"reviewer-<hash>", content) and has_pass:
        errors.append("审查者 ID 仍为模板 reviewer-<hash>,须替换为真实 reviewer id")

    return (len(errors) == 0, errors)


def check_step(workdir: str, step: str) -> tuple[bool, list[str]]:
    """检查单个 step 的产物完整性。返回 (passed, errors)。"""
    workdir_path = Path(workdir)

    if step == "all":
        all_errors = []
        for s in ["1", "2a", "2b", "2c", "3a", "3b", "4", "5", "6"]:
            passed, errors = check_step(workdir, s)
            if not passed:
                all_errors.extend([f"[step {s}] {e}" for e in errors])
        ts_passed, ts_errors = check_topic_scores(workdir_path)
        if not ts_passed:
            all_errors.extend([f"[topic_scores.json] {e}" for e in ts_errors])
        for rt in ["scan", "topics"]:
            r_passed, r_errors = check_review(workdir_path, rt)
            if not r_passed:
                all_errors.extend([f"[review_{rt}.md] {e}" for e in r_errors])
        return (len(all_errors) == 0, all_errors)

    if step == "scores":
        return check_topic_scores(workdir_path)

    if step == "scan-review":
        return check_review(workdir_path, "scan")

    if step == "topics-review":
        return check_review(workdir_path, "topics")

    if step not in GATES:
        return (False, [f"未知 step: {step}。合法 step: {', '.join(VALID_STEPS)}"])

    rule = GATES[step]
    file_path = workdir_path / rule["file"]
    errors = []

    if not file_path.exists():
        return (False, [f"{rule['fail_msg']}\n  文件不存在:{file_path}"])

    content = file_path.read_text(encoding="utf-8")
    lines = content.splitlines()

    if len(lines) < rule["min_lines"]:
        errors.append(
            f"{rule['fail_msg']}\n  文件行数 {len(lines)} < 最小要求 {rule['min_lines']}"
        )

    for kw in rule["required_keywords"]:
        if kw not in content:
            errors.append(f"缺少关键词: '{kw}'")

    if "min_count" in rule:
        for kw, min_n in rule["min_count"].items():
            count = content.count(kw)
            if count < min_n:
                errors.append(f"'{kw}' 出现 {count} 次,要求 ≥ {min_n} 次")

    if rule.get("ban_placeholders"):
        errors.extend(check_placeholders(content, f"Step {step}"))

    if step == "3a":
        ts_passed, ts_errors = check_topic_scores(workdir_path)
        if not ts_passed:
            errors.append("--- topic_scores.json 校验失败 ---")
            errors.extend(ts_errors)

    if step == "6":
        errors.extend(check_step6_quality(content))

    # 2c 额外:至少 3 条证据来源
    if step == "2c":
        if content.count("证据来源") < 3:
            errors.append("Step 2c:「证据来源」出现 < 3 次(Gap 条数过少或未展开)")
        errors.extend(check_placeholders(content, "Step 2c"))

    return (len(errors) == 0, errors)


def main():
    parser = argparse.ArgumentParser(description="选题工坊 · 刚性闸门检查 v0.3.2")
    parser.add_argument("--workdir", "-w", required=True, help="工作目录(产出文件所在)")
    parser.add_argument("--step", "-s", required=True, help=f"Step 编号:{', '.join(VALID_STEPS)}")
    args = parser.parse_args()

    if not os.path.isdir(args.workdir):
        print(f"❌ 目录不存在:{args.workdir}")
        sys.exit(1)

    passed, errors = check_step(args.workdir, args.step)

    if passed:
        print(f"✅ Step {args.step} PASS")
        sys.exit(0)

    print(f"❌ Step {args.step} FAIL")
    for err in errors:
        print(f"  - {err}")
    print()
    print("修复建议:")
    print("  1. 重新跑对应 step 的子命令")
    print("  2. 按上面错误信息补全缺失字段/加厚论述/补附录矩阵")
    print("  3. 再跑一次:python scripts/check_step.py --workdir <dir> --step " + args.step)
    sys.exit(1)


if __name__ == "__main__":
    main()
