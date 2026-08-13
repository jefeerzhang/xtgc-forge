#!/usr/bin/env python3
"""
选题工坊 · 项目初始化脚本 (v0.3.1)

一键创建研究项目的工作目录,生成过程模板 + 用户主交付六段式研究计划报告模板。

用法:
  python scripts/init_project.py --workdir <dir> --name "<研究主题>"
                                --branch "<推断性|描述性|质性|混合>"
                                --language <zh-CN|en-US>
"""

import argparse
import os
import sys
from datetime import datetime
from pathlib import Path


# 模板文件名
TEMPLATES = {
    "00_交付说明.md": """# 交付说明(请先读)

## 你只需要打开这一份

**主交付**:[`00_研究计划报告.md`](./00_研究计划报告.md)

内含:选题正文六段(先亮题) + 文献矩阵/要点/Gap/候选与选定/识别要点。

## 其他文件是什么?

`Step1`–`Step5`、`topic_scores.json`、`review_*.md` 等是**过程审计**材料,默认不必通读。

## 规格

见技能库 `references/delivery-spec.md` 与金样例 `examples/漂绿治理-绿贷与环境税组合/`。
""",

    "00_任务元信息.md": """# 任务元信息(Phase 0 三问回答)

> 由 `init_project.py` 自动生成。请填写或修改。

## 1. 学科背景与研究方向
- 一级学科:
- 二级学科:
- 方法训练:
- 是否跨学科:

## 2. 当前阶段
- 本科 / / 硕士 / / 博士 / / 青年教师 / / 在职科研
- 离毕业或考核还有多久:

## 3. 历史沿革
- 之前做过什么研究:
- 为什么转向现在这个方向:
- 是否有半途而废的方向:

## 4. 研究基础
- 已有数据:
- 方法能力:
- 合作方或导师支持:
- 已发表成果:

## 5. 交付目标
- [ ] 课程论文
- [ ] 学位论文(硕/博)
- [ ] 期刊投稿
- [ ] 基金申报
- [ ] 研究构想
- [ ] 政策报告

## 6. 时间约束
- 什么时候要交:
- 中间节点:

## 7. 学科分支
- 实证量化 / / 描述性 / / 质性 / / 混合 / / 工程应用

## 8. 语言偏好
- 中文 / / 英文 / / 双语

## 9. 利害关系档
- 高(顶刊 / 国基) / / 中(核心 / 教育部) / / 低(普通期刊 / 一般项目)
""",

    "Step1-input.md": """# Step 1 · 输入确认

> 由 ` `init_project.py` 自动生成。请填写或修改。

## 模糊领域

```
<请填写:1-2 句话描述研究兴趣 / 现象 / 直觉>
```

## 文献清单

<请填写:5-50 篇 PDF / 引用列表,至少包含 2-3 篇近 3 年综述>

## 方法偏好(可选)
<请填写:你倾向的识别策略 DID/IV/RDD/实验/质性/混合>

## 可选附加
- 目标期刊:
- 数据可得性提示:
- 时长约束:
""",

    "Step2a-points.md": """# Step 2a · 文献要点卡

> 每篇可读文献 1 张要点卡。读不出的舍弃 + 提醒。

## 文献 L1
- **作者 / 年份**:
- **研究问题**:
- **理论框架**:
- **数据 / 样本**:
- **方法**:
- **主要发现**:
- **自报局限**:
- **关联初判**:

(继续添加 L2, L3 ...)
""",

    "Step2b-literature-matrix.md": """# Step 2b · 文献矩阵

| 作者 | 年份 | 期刊 | 理论 | 样本 | 方法 | IV | DV | 主要发现 | 自报局限 | 与本研究关联 |
|---|---|---|---|---|---|---|---|---|---|---|

(继续添加)
""",

    "Step2c-gap-verdicts.md": """# Step 2c · Gap 裁定

> 每条 gap 含 **证据来源 + 重要性 + 派生依据**。

## 已知区(避免)

### GAP-K1
- **证据来源**:<具体哪几篇文献>
- **重要性**:

## 空白区(高价值)

### GAP-B1
- **证据来源**:
- **重要性**:
- **派生依据**:

(继续添加)
""",

    "Step3a-candidate-themes.md": """# Step 3a · 候选研究主题(3 主推 + 2 备选)

> 配合 `topic_scores.json`,每个候选含 6 维评分 + 反坍缩字段(t_score / tier)。

## 模态识别(反坍缩 Phase 1)
| 模态题 | T-Score | 避免理由 |
|---|---|---|
| <最安全、最可预测的题 1> | 0.9 | <为何避免> |

> 不点名,坍缩不可见。以下候选均刻意偏离上述模态。

## 🥇 主推 1
- **来源 gap**:
- **研究问题(RQ)**:
- **理论贡献**:
- **方法可行性**:
- **预期效应方向**:
- **研究类型标签**:推断性
- **降级条件**:
- **T-Score(0-1) + 层级**:0.0 / safe

(继续添加 主推 2 / 主推 3 / 备选 1 / 备选 2)

## 📊 主推 vs 备选 对比

| 维度 | 主推 1 | 主推 2 | 主推 3 | 备选 1 | 备选 2 |
|---|---|---|---|---|---|
| **核心问题** |
| **数据可得** |
| **理论贡献** |
| **方法成熟度** |
| **顶刊命中率** |

---

## 🛑 Checkpoint #3 · 用户选 1

参考 `topic_scores.json` 的 6 维评分 + 反坍缩字段,选分数最高的;或说明降级到备选的原因。禁止默认选 total 最高项。
""",

    "topic_scores.json": """{
  "step": "3a",
  "created_at": "<YYYY-MM-DD>",
  "rubric": {
    "importance": "理论 + 实践价值(1-5)",
    "feasibility": "数据 + 方法可获取性(1-5)",
    "falsifiability": "能否被推翻(1-5)",
    "evidence_leverage": "现有文献能支撑多少(1-5)",
    "originality": "与已有研究的差异度(1-5)",
    "negative_value": "被推翻后学界仍感兴趣(1-5)"
  },
  "candidates": [
    {
      "id": "Q1",
      "label": "主推1",
      "title": "<候选主题标题>",
      "source_gap": "<来源 Gap 编号>",
      "research_type": "推断性|描述性|质性",
      "t_score": 0.0,
      "tier": "safe|differentiated|innovative",
      "scores": {
        "importance": 0,
        "feasibility": 0,
        "falsifiability": 0,
        "evidence_leverage": 0,
        "originality": 0,
        "negative_value": 0
      },
      "total": 0,
      "max_total": 30,
      "decision": "selected|parked|dropped",
      "kill_rule": "<若 dropped 必填:为何淘汰>"
    }
  ]
}
""",

    "Step3b-selected-theme.md": """# Step 3b · 选定研究主题

> 由用户在 CP#3 根据 topic_scores.json 选定。

## 选定主题
**主题标题:**

### 研究问题(RQ)
```
主问题:
子问题:
```

### 理论贡献
1.
2.
3.

### 研究类型标签
推断性 / / 描述性 / / 质性

### 预期效应方向
- 预期 + (正向) / / 预期 - (负向) / / 开放
""",

    "Step4-hypotheses.md": """# Step 4 · 研究假设

> ≥3 个假设,各含 **假设陈述 + DAG + 反事实 + 可证伪 + SESOI + 检验策略**。

## 核心命题
<一句话总结>

---

## 假设 H1

### 假设陈述
<请填写>

### DAG 图(文字描述)
```
X → M1, M2 → Y
      ↑
      Z(混杂)
```

### 反事实表述
> "如果 ..."

### 可证伪条件
<什么观察会让该假设被拒绝>

### 最小效应量(SESOI)
- 数值:

### 检验策略
- 主检验:
- 机制检验:
- 稳健性:

(继续添加 H2, H3 ...)
""",

    "Step5-identification-strategy.md": """# Step 5 · 因果识别策略

> 基于选定主题与研究类型(推断性才启用)。

## 研究类型判断
推断性 / / 描述性 / / 质性 / / 混合

## 推断性策略
<推断性研究才填>

### 模型
<双向固定效应 / DID / IV / ...>

### 变量度量
- IV:
- DV:
- 中介:

### 工具变量(IV)候选
- IV1:
- IV2:
- IV3:

### 稳健性检验清单
- [ ] 替换 IV 度量
- [ ] 缩短样本期
- [ ] 子样本分组
- [ ] Placebo
- [ ] 共同方法偏差

### 反例与威胁
- 威胁 1:
- 威胁 2:
- 威胁 3:
""",

    "Step6-summary.md": """# Step 6 · 过程汇总(非用户主交付)

> ⚠️ **用户主交付**见同目录 `00_研究计划报告.md`(六段式)。本文件仅作过程指针。

## 主交付路径

`00_研究计划报告.md`

## 过程文件状态

| Step | 文件 | 状态 |
|---|---|---|
| 1 | Step1-input.md |  |
| 2a | Step2a-points.md |  |
| 2b | Step2b-literature-matrix.md |  |
| 2c | Step2c-gap-verdicts.md |  |
| 3a | Step3a-candidate-themes.md / topic_scores.json |  |
| 3b | Step3b-selected-theme.md |  |
| 4 | Step4-hypotheses.md |  |
| 5 | Step5-identification-strategy.md |  |
| 6 | 00_研究计划报告.md |  |
""",

    "00_研究计划报告.md": """# 研究计划报告

> ★ **用户主交付**(六段式)。由 Step 6 根据 Step1–5 与 Checkpoint 决策填写。
> 过程文件(Step1–5 / review / scores)为附录,用户默认只读本文件。
> 顺序硬规则:**先亮题 → 再为什么 → 再意义 → 假设 → 依据 → 怎么做**。
> 论述硬规则:用文献/理论/推理**充分展开**,禁止只有标题+一句话;第 2、4、5 段尤须写透。

## 1. 选的题是什么?

<!-- 用段落写清:工作标题、RQ 及其展开、对象/情境、研究类型、明确不做什么 -->

## 2. 为什么选这个题?

<!-- 充分论述:用户文献分别证明了什么、缺口在哪、理论直觉、Checkpoint 决策如何收束到此题。宜多段,勿三五行。 -->

## 3. 选题的意义是什么?

<!-- 现实 / 学术 / 对用户可执行,分段论述 -->

## 4. 假设是什么?

<!-- 每条假设写:主张 + 理论/经验直觉 + 可证伪方式(+SESOI 可选)。禁止只列口号式 H1/H2。 -->

### H1

### H2

### H3

## 5. 为什么能写出这样的假设?

<!-- 推理链:文献锚点 → gap → 用户决策 → 为何是这些 H;勿与第 4 段简单重复 -->

## 6. 后面应该怎么做?

<!-- 设计一句话、变量操作化、步骤、数据、风险预案、最小行动;写具体 -->

---

# 整合附录(与正文同属主交付,不可只写「见 Step 文件」)

## 附录 A · 文献矩阵

<!-- 完整表:作者/年/刊/理论/样本/方法/IV-DV/发现/局限/关联 -->

## 附录 B · 文献要点卡(压缩版)

## 附录 C · 关键 Gap 裁定

## 附录 D · 候选主题、评分与选定

## 附录 E · 因果识别要点

## 附录 F · 任务元信息与闸门摘要
""",
}


def init_project(workdir: str, name: str, branch: str, language: str):
    """初始化研究项目目录。"""
    workdir_path = Path(workdir).expanduser().resolve()

    if workdir_path.exists():
        # 检查是否已有协议
        protocol_file = workdir_path / "00_任务元信息.md"
        if protocol_file.exists():
            print(f"❌ 目录已存在协议:{workdir_path}")
            print(f"  已有 00_任务元信息.md,拒绝覆盖")
            print()
            print("如需重新初始化:")
            print(f"  rm -rf {workdir_path}  # 谨慎操作")
            sys.exit(1)

    # 创建目录
    workdir_path.mkdir(parents=True, exist_ok=True)

    # 生成所有模板
    created = []
    for filename, content in TEMPLATES.items():
        file_path = workdir_path / filename
        # 替换占位符
        content_filled = content.replace("<YYYY-MM-DD>", datetime.now().strftime("%Y-%m-%d"))
        content_filled = content_filled.replace("<研究主题>", name)
        content_filled = content_filled.replace("<推断性|描述性|质性>", branch)
        content_filled = content_filled.replace("<zh-CN|en-US>", language)
        # 处理 language 在 frontmatter 中的格式
        content_filled = content_filled.replace('"--language <zh-CN|en-US>"', f'--language {language}')

        file_path.write_text(content_filled, encoding="utf-8")
        created.append(str(file_path.relative_to(workdir_path)))

    print(f"✅ 项目初始化完成:{workdir_path}")
    print()
    print("📁 生成的文件:")
    for f in created:
        print(f"  • {f}")
    print()
    print("🔧 下一步:")
    print(f"  1. 编辑 00_任务元信息.md(三问回答)")
    print(f"  2. 编辑 Step1-input.md(文献清单)")
    print(f"  3. 运行:python scripts/check_step.py --workdir {workdir_path} --step 1")


def main():
    parser = argparse.ArgumentParser(description="选题工坊 · 项目初始化")
    parser.add_argument("--workdir", "-w", required=True, help="工作目录路径(将创建)")
    parser.add_argument("--name", "-n", default="未命名研究主题", help="研究主题名称")
    parser.add_argument("--branch", "-b", default="推断性", help="学科分支:推断性 / 描述性 / 质性 / 混合")
    parser.add_argument("--language", "-l", default="zh-CN", help="语言:zh-CN / en-US")
    args = parser.parse_args()

    init_project(args.workdir, args.name, args.branch, args.language)


if __name__ == "__main__":
    main()