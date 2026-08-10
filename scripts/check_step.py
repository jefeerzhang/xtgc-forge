#!/usr/bin/env python3
"""
选题工坊 · 刚性闸门检查脚本 (v0.2.5)

校验每个 Step 产物的完整性、关键字段、最小内容长度。
失败返回非 0 退出码,提示用户修复。

用法:
  python scripts/check_step.py --workdir <dir> --step <1|2a|2b|2c|3a|3b|4|5|6|all>
"""

import argparse
import json
import os
import sys
from pathlib import Path


# 每个 Step 的闸门校验规则
GATES = {
    "1": {
        "file": "Step1-input.md",
        "min_lines": 5,
        "required_keywords": ["模糊领域", "文献清单"],
        "fail_msg": "Step 1: 输入清单缺少'模糊领域'或'文献清单'字段"
    },
    "2a": {
        "file": "Step2a-points.md",
        "min_lines": 10,
        "required_keywords": ["研究问题", "主要发现"],
        "fail_msg": "Step 2a: 文献要点卡缺少'研究问题'或'主要发现'"
    },
    "2b": {
        "file": "Step2b-literature-matrix.md",
        "min_lines": 5,
        "required_keywords": ["作者", "年份", "方法", "主要发现"],
        "fail_msg": "Step 2b: 文献矩阵缺少关键字段(作者/年份/方法/主要发现)"
    },
    "2c": {
        "file": "Step2c-gap-verdicts.md",
        "min_lines": 8,
        "required_keywords": ["gap", "证据来源", "重要性"],
        "fail_msg": "Step 2c: Gap 裁定缺少'证据来源'或'重要性'字段"
    },
    "3a": {
        "file": "Step3a-candidate-themes.md",
        "min_lines": 15,
        "required_keywords": ["主推", "备选", "理论贡献", "方法可行性", "研究类型"],
        "min_count": {
            "主推": 3,
            "备选": 2,
            "研究类型": 5  # 3 主推 + 2 备选
        },
        "fail_msg": "Step 3a: 候选主题格式不对。需要 3 主推 + 2 备选,各含理论贡献 + 方法可行性 + 研究类型"
    },
    "3b": {
        "file": "Step3b-selected-theme.md",
        "min_lines": 5,
        "required_keywords": ["研究问题", "理论贡献", "研究类型"],
        "fail_msg": "Step 3b: 选定主题缺少关键字段"
    },
    "4": {
        "file": "Step4-hypotheses.md",
        "min_lines": 15,
        "required_keywords": ["假设", "DAG", "反事实", "可证伪", "SESOI"],
        "min_count": {
            "假设陈述": 3
        },
        "fail_msg": "Step 4: 假设文件缺少'假设陈述/DAG/反事实/可证伪/SESOI'字段,或假设数 < 3"
    },
    "5": {
        "file": "Step5-identification-strategy.md",
        "min_lines": 10,
        "required_keywords": ["识别策略", "工具变量", "稳健性"],
        "fail_msg": "Step 5: 因果识别策略缺少'识别策略/工具变量/稳健性'字段"
    },
    "6": {
        "file": "Step6-summary.md",
        "min_lines": 10,
        "required_keywords": ["核心结论", "后续步骤"],
        "fail_msg": "Step 6: 总结文件缺少'核心结论'或'后续步骤'字段"
    }
}


# topic_scores.json 特殊校验(Step 3a 必跑)
SCORE_KEYS = ["importance", "feasibility", "falsifiability", "evidence_leverage", "originality", "negative_value"]


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

    # 校验 decision 计数
    selected_count = sum(1 for c in candidates if c.get("decision") == "selected")
    parked_count = sum(1 for c in candidates if c.get("decision") == "parked")
    dropped_count = sum(1 for c in candidates if c.get("decision") == "dropped")

    if selected_count != 3:
        errors.append(f"decision='selected' 的候选数 {selected_count} ≠ 3(应 3 主推)")

    # 校验每个 candidate
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
                errors.append(f"{prefix}: 评分 '{key}' 不是整数({type(scores[key]).__name__})")
            elif not (1 <= scores[key] <= 5):
                errors.append(f"{prefix}: 评分 '{key}'={scores[key]} 不在 1-5 范围")

        if "decision" not in c:
            errors.append(f"{prefix}: 缺少 'decision' 字段")
        elif c["decision"] == "dropped" and not c.get("kill_rule"):
            errors.append(f"{prefix}: decision='dropped' 必须填 'kill_rule'")

        if "research_type" not in c:
            errors.append(f"{prefix}: 缺少 'research_type' 字段")

    return (len(errors) == 0, errors)


def check_step(workdir: str, step: str) -> tuple[bool, list[str]]:
    """
    检查单个 step 的产物完整性。
    返回 (passed, errors)。
    """
    if step == "all":
        all_errors = []
        for s in ["1", "2a", "2b", "2c", "3a", "3b", "4", "5", "6"]:
            passed, errors = check_step(workdir, s)
            if not passed:
                all_errors.extend(errors)
        # 同时校验 topic_scores.json
        ts_passed, ts_errors = check_topic_scores(Path(workdir))
        if not ts_passed:
            all_errors.extend([f"[topic_scores.json] {e}" for e in ts_errors])
        return (len(all_errors) == 0, all_errors)

    if step == "scores":
        return check_topic_scores(Path(workdir))

    if step not in GATES:
        return (False, [f"未知 step: {step}。合法 step: 1, 2a, 2b, 2c, 3a, 3b, 4, 5, 6, all, scores"])

    rule = GATES[step]
    workdir_path = Path(workdir)
    file_path = workdir_path / rule["file"]

    errors = []

    # 检查文件存在
    if not file_path.exists():
        return (False, [f"{rule['fail_msg']}\n  文件不存在:{file_path}"])

    # 读取内容
    content = file_path.read_text(encoding="utf-8")
    lines = content.splitlines()

    # 检查行数
    if len(lines) < rule["min_lines"]:
        errors.append(f"{rule['fail_msg']}\n  文件行数 {len(lines)} < 最小要求 {rule['min_lines']}")

    # 检查关键词
    for kw in rule["required_keywords"]:
        if kw not in content:
            errors.append(f"缺少关键词: '{kw}'")

    # 检查最小计数(如"主推 ≥ 3")
    if "min_count" in rule:
        for kw, min_n in rule["min_count"].items():
            count = content.count(kw)
            if count < min_n:
                errors.append(f"'{kw}' 出现 {count} 次,要求 ≥ {min_n} 次")

    # Step 3a 额外校验 topic_scores.json
    if step == "3a":
        ts_passed, ts_errors = check_topic_scores(workdir_path)
        if not ts_passed:
            errors.append("--- topic_scores.json 校验失败 ---")
            errors.extend(ts_errors)

    return (len(errors) == 0, errors)


def check_step(workdir: str, step: str) -> tuple[bool, list[str]]:
    """
    检查单个 step 的产物完整性。
    返回 (passed, errors)。
    """
    if step == "all":
        # 全部检查
        all_errors = []
        for s in ["1", "2a", "2b", "2c", "3a", "3b", "4", "5", "6"]:
            passed, errors = check_step(workdir, s)
            if not passed:
                all_errors.extend(errors)
        return (len(all_errors) == 0, all_errors)

    if step not in GATES:
        return (False, [f"未知 step: {step}。合法 step: 1, 2a, 2b, 2c, 3a, 3b, 4, 5, 6, all"])

    rule = GATES[step]
    file_path = Path(workdir) / rule["file"]

    errors = []

    # 检查文件存在
    if not file_path.exists():
        return (False, [f"{rule['fail_msg']}\n  文件不存在:{file_path}"])

    # 读取内容
    content = file_path.read_text(encoding="utf-8")
    lines = content.splitlines()

    # 检查行数
    if len(lines) < rule["min_lines"]:
        errors.append(f"{rule['fail_msg']}\n  文件行数 {len(lines)} < 最小要求 {rule['min_lines']}")

    # 检查关键词
    for kw in rule["required_keywords"]:
        if kw not in content:
            errors.append(f"缺少关键词: '{kw}'")

    # 检查最小计数(如"主推 ≥ 3")
    if "min_count" in rule:
        for kw, min_n in rule["min_count"].items():
            count = content.count(kw)
            if count < min_n:
                errors.append(f"'{kw}' 出现 {count} 次,要求 ≥ {min_n} 次")

    return (len(errors) == 0, errors)


def main():
    parser = argparse.ArgumentParser(description="选题工坊 · 刚性闸门检查")
    parser.add_argument("--workdir", "-w", required=True, help="工作目录(产出文件所在)")
    parser.add_argument("--step", "-s", required=True, help="Step 编号: 1, 2a, 2b, 2c, 3a, 3b, 4, 5, 6, all")
    args = parser.parse_args()

    if not os.path.isdir(args.workdir):
        print(f"❌ 目录不存在:{args.workdir}")
        sys.exit(1)

    passed, errors = check_step(args.workdir, args.step)

    if passed:
        print(f"✅ Step {args.step} PASS")
        sys.exit(0)
    else:
        print(f"❌ Step {args.step} FAIL")
        for err in errors:
            print(f"  - {err}")
        print()
        print("修复建议:")
        print("  1. 重新跑对应 step 的子命令")
        print("  2. 按上面错误信息补全缺失字段")
        print("  3. 再跑一次:python scripts/check_step.py --workdir <dir> --step " + args.step)
        sys.exit(1)


if __name__ == "__main__":
    main()