#!/usr/bin/env python3
"""
选题工坊 · 独立审查脚本 (v0.3.18 · 审查降级为过程建议)

借鉴 research-topic-selection v1.5.2 的审查分离机制:
- scan / topics 两道闸建议独立审查(非强制,v0.3.18 起降级为过程建议)
- reviewer_agent_id ≠ producer_agent_id(推荐)
- 审查者上下文不含产出过程,只读落盘产物(推荐)

本脚本生成 verdict 模板(空),由独立子 agent 填入审查结论。
verdict 通过 check_step.py 的 --step <target>-review 验证。
v0.3.18 起,verdict 值允许 {PASS, P0_OPEN, FAIL, NEEDS_HUMAN};
缺失文件 / 信任边界声明缺失 / reviewer ID 占位 等都不再视为硬错,只 WARN。

用法:
  # Step 2c 后:扫描阶段独立审查
  python scripts/review.py --workdir <dir> --target scan

  # Step 4 后:选题阶段独立审查
  python scripts/review.py --workdir <dir> --target topics
"""

import argparse
import os
import sys
from datetime import datetime
from pathlib import Path


# 审查产物模板
VERDICT_TEMPLATES = {
    "scan": """# Scan Review Verdict

> 独立审查者(producer 之外)对 Step 2a/2b/2c 的产物进行审查。

> 生成时间:{timestamp}
> 审查目标:{target}
> 审查者 ID:reviewer-<hash>(必须 ≠ producer)

---

## 1. 审查依据

| 审查文件 | 路径 |
|---|---|
| Step 2a 要点卡 | Step2a-points.md |
| Step 2b 矩阵 | Step2b-literature-matrix.md |
| Step 2c Gap 裁定 | Step2c-gap-verdicts.md |

---

## 2. 审查维度

### 2.1 文献覆盖性(weight=3)
- 文献数量是否足够(目标 ≥5 篇):
- 是否包含近 3 年综述:
- 是否覆盖学科分支足够:

### 2.2 要点卡质量(weight=2)
- 每篇要点卡是否含"研究问题 / 方法 / 主要发现 / 自报局限":
- 是否准确反映原文核心:
- 与本研究关联初判是否合理:

### 2.3 矩阵完整性(weight=2)
- 字段是否齐全(作者 / 年份 / 方法 / IV / DV / 主要发现):
- 同质化识别是否清晰:
- Gap 候选派生是否合理:

### 2.4 Gap 质量(weight=3)
- Gap 数量是否 ≥5:
- 每条 Gap 是否有"证据来源 + 重要性 + 派生依据":
- Gap 排序是否合理:
- 是否有"无中生有"的 Gap:

### 2.5 与用户主题契合度(weight=2)
- 文献主题与用户模糊领域的关联性:

---

## 3. 评分(各维度 1-5)

- 文献覆盖性:
- 要点卡质量:
- 矩阵完整性:
- Gap 质量:
- 与用户主题契合度:

---

## 4. P0 问题(必须修复才能放行)

列出 P0(open=必须改,不改不能进入下一阶段):

### P0-1
- 问题:
- 修正建议:

### P0-2
- 问题:
- 修正建议:

---

## 5. P1 问题(可放行但需记录)

### P1-1
- 问题:
- 建议:

---

## 6. 总评

- **verdict**:`PASS` / `P0_OPEN` / `FAIL` / `NEEDS_HUMAN`
- **理由**:
- **p0_open 数量**:
- **建议**:

---

## 7. 信任边界声明(诚实声明 · v0.3.18 降级)

> **WARNING · v0.3.18 审查降级说明**:本审查由独立 subagent 填写 verdict,但**没有密码学身份保证**。verdict 仅作过程留痕,
> 不可作为合规依据、不可作为学术可信度背书。完整闭合需要受控 runner 外部登记审查行为(host fingerprint + 时间戳 + hash 链),
> 超出本 skill 范围(同 RTS v1.5.2 残留,详见 CHANGELOG v0.2.7 与 SKILL.md 独立审查段)。
>
> 自 v0.3.18 起,`scripts/check_step.py --step scan-review` / `--step topics-review` 把缺失文件 / 信任边界声明缺失 / reviewer ID 占位
> 等从"硬错"降级为"软警告",不阻塞交付;verdict 值允许 {{PASS, P0_OPEN, FAIL, **NEEDS_HUMAN**}},其中 NEEDS_HUMAN 表示审查者明确
> 自承"拿不准,需人类专家复核"——比伪造一个 PASS 更诚实。
""",

    "topics": """# Topics Review Verdict

> 独立审查者(producer 之外)对 Step 3a/3b/4 的产物进行审查。

> 生成时间:{timestamp}
> 审查目标:{target}
> 审查者 ID:reviewer-<hash>(必须 ≠ producer)

---

## 1. 审查依据

| 审查文件 | 路径 |
|---|---|
| Step 3a 候选主题 | Step3a-candidate-themes.md |
| Step 3a 评分 | topic_scores.json |
| Step 3b 选定主题 | Step3b-selected-theme.md |
| Step 4 假设 | Step4-hypotheses.md |

---

## 2. 审查维度

### 2.1 候选主题质量(weight=3)
- 3 主推 + 2 备选结构是否齐全:
- 每条候选是否含"来源 Gap / RQ / 理论贡献 / 方法 / 研究类型 / 降级条件":

### 2.2 评分合理性(weight=3)
- 6 维评分是否都填了 1-5 整数:
- decision 字段(selected / parked / dropped)是否与场景一致:
- 是否有评分明显不合理的候选:

### 2.3 选定主题合理性(weight=2)
- 用户选的是否是 score 最高的:
- 降级场景(若选备选)是否合理:

### 2.4 假设质量(weight=3)
- ≥3 个假设是否齐全:
- 每个假设是否含"假设陈述 / DAG / 反事实 / 可证伪 / SESOI / 检验策略":
- DAG 因果路径是否合理:
- SESOI 是否具有实质意义:

### 2.5 可检验性(weight=2)
- 假设是否可被推翻:
- 检验策略是否有数据 / 方法支撑:

---

## 3. 评分(各维度 1-5)

- 候选主题质量:
- 评分合理性:
- 选定主题合理性:
- 假设质量:
- 可检验性:

---

## 4. P0 问题(必须修复)

### P0-1
- 问题:
- 修正建议:

### P0-2
- 问题:
- 修正建议:

---

## 5. P1 问题

### P1-1
- 问题:
- 建议:

---

## 6. 总评

- **verdict**:`PASS` / `P0_OPEN` / `FAIL` / `NEEDS_HUMAN`
- **理由**:
- **p0_open 数量**:
- **建议**:

---

## 7. 信任边界声明(诚实声明 · v0.3.18 降级)

> **WARNING · v0.3.18 审查降级说明**:本审查由独立 subagent 填写 verdict,但**没有密码学身份保证**。verdict 仅作过程留痕,
> 不可作为合规依据、不可作为学术可信度背书。完整闭合需要受控 runner 外部登记审查行为(host fingerprint + 时间戳 + hash 链),
> 超出本 skill 范围(同 RTS v1.5.2 残留,详见 CHANGELOG v0.2.7 与 SKILL.md 独立审查段)。
>
> 自 v0.3.18 起,`scripts/check_step.py --step scan-review` / `--step topics-review` 把缺失文件 / 信任边界声明缺失 / reviewer ID 占位
> 等从"硬错"降级为"软警告",不阻塞交付;verdict 值允许 {{PASS, P0_OPEN, FAIL, **NEEDS_HUMAN**}},其中 NEEDS_HUMAN 表示审查者明确
> 自承"拿不准,需人类专家复核"——比伪造一个 PASS 更诚实。
""",
}


def create_review_template(workdir: str, target: str) -> str:
    """生成审查产物模板。"""
    workdir_path = Path(workdir).expanduser().resolve()

    # --workdir 必须是已存在的目录(与 init_project.py 一致的「文件拒绝」契约)。
    if not workdir_path.exists() or not workdir_path.is_dir():
        print(f"❌ 工作目录不存在或不是目录:{workdir_path}")
        sys.exit(1)

    if target not in VERDICT_TEMPLATES:
        print(f"❌ 未知 target: {target}。合法:scan / topics")
        sys.exit(1)

    review_file = workdir_path / f"review_{target}.md"

    if review_file.exists():
        print(f"❌ 审查产物已存在:{review_file}")
        print("  拒绝覆盖。如需重新审查:rm 该文件后再跑")
        sys.exit(1)

    content = VERDICT_TEMPLATES[target].format(
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        target=target
    )

    review_file.write_text(content, encoding="utf-8")

    print(f"✅ 审查模板生成:{review_file}")
    print()
    print("🔧 下一步:")
    print("  1. 由独立子 agent 填入 verdict:")
    print("     - reviewer context 必须为空(不含产出过程)")
    print("     - reviewer_agent_id ≠ producer_agent_id")
    print("     - v0.3.18+ verdict 允许值:PASS / P0_OPEN / FAIL / NEEDS_HUMAN")
    print(f"  2. 填完后跑:python scripts/check_step.py --workdir {workdir} --step {target}-review")
    print("  3. PASS / NEEDS_HUMAN → 继续下一阶段")
    print("     P0_OPEN → 修复后重审(≤3 轮)")
    print("     FAIL → 用户决定是否重跑(过程建议,不强制)")


def main():
    parser = argparse.ArgumentParser(description="选题工坊 · 独立审查模板")
    parser.add_argument("--workdir", "-w", required=True, help="工作目录")
    parser.add_argument("--target", "-t", required=True, choices=["scan", "topics"], help="审查目标")
    args = parser.parse_args()

    create_review_template(args.workdir, args.target)


if __name__ == "__main__":
    main()