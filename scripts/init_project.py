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
import sys
from datetime import datetime
from pathlib import Path

from templates import TEMPLATES, FILL_TOKENS  # 模板契约单一真源


def _force_utf8_stdio() -> None:
    """强制 stdout/stderr 走 UTF-8(管道重定向时 Windows 默认 cp936,
    ✅/❌ 等 emoji 会抛 UnicodeEncodeError,导致成功初始化也以退出码 1 结束)。"""
    for stream in (sys.stdout, sys.stderr):
        if stream is not None and hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")


# 模板文件名
# init_project.py 输出的文件名 + 不由本脚本生成但仍属"已存在项目"语义的文件,
# 出现任一项 + 非 --force → 拒绝覆盖(防静默丢失用户已写内容)。
TRACKED_FILES = (
    "00_交付说明.md",
    "00_任务元信息.md",
    "Step1-input.md",
    "Step2a-points.md",
    "Step2b-literature-matrix.md",
    "Step2c-gap-verdicts.md",
    "Step3a-candidate-themes.md",
    "Step3b-selected-theme.md",
    "Step4-hypotheses.md",
    "Step5-identification-strategy.md",
    "Step6-summary.md",
    "00_研究计划报告.md",
    "00_复跑决策记录.md",
    "interaction-log.md",
    "topic_scores.json",
    "review_topics.md",
    "review_scan.md",
)


def init_project(workdir: str, name: str, branch: str, language: str, force: bool = False):
    """初始化研究项目目录。

    当 --workdir 已含任一 TRACKED_FILES 中声明的文件时:
    - 未传 --force → 退出码 1,提示需 --force 或换 --workdir;
    - 传了 --force → 在 stderr 列出将被覆盖的文件,继续写入。
    """
    workdir_path = Path(workdir).expanduser().resolve()

    if workdir_path.exists():
        # 检查是否已有任意已跟踪文件(v0.3.x 起扩到 TRACKED_FILES 全集,
        # 不只 00_任务元信息.md,防静默覆盖用户已写内容)。
        existing = [f for f in TRACKED_FILES if (workdir_path / f).exists()]
        if existing:
            if not force:
                print(f"❌ 工作目录已存在项目文件:{workdir_path}", file=sys.stderr)
                print(f"  命中 {len(existing)} 个已跟踪文件:{', '.join(existing[:5])}"
                      + ("…" if len(existing) > 5 else ""), file=sys.stderr)
                print("需 --force 覆盖,或换 --workdir", file=sys.stderr)
                sys.exit(1)
            print(f"⚠️  --force 已启用,以下 {len(existing)} 个文件将被覆盖:",
                  file=sys.stderr)
            for f in existing:
                print(f"  - {f}", file=sys.stderr)

    # 创建目录前,确保 --workdir 不是已存在的文件(否则 mkdir 会抛 FileExistsError,
    # 且语义上「对文件路径做 init」是用户错误,应显式拒绝)。
    if workdir_path.exists() and not workdir_path.is_dir():
        print(f"❌ --workdir 路径已存在但不是目录:{workdir_path}", file=sys.stderr)
        sys.exit(1)

    # 创建目录
    workdir_path.mkdir(parents=True, exist_ok=True)

    # 生成所有模板
    # 参数化 token 替换:契约在 templates.FILL_TOKENS(token 集合即契约),
    # 此处提供当次值;两集合必须一致(测试锚定),杜绝占位符再成空操作。
    fill_values = {
        "<YYYY-MM-DD>": datetime.now().strftime("%Y-%m-%d"),
        "<研究主题>": name,
        "<推断性|描述性|质性>": branch,
        "<zh-CN|en-US>": language,
    }
    assert set(fill_values) == set(FILL_TOKENS), "fill_values 与 FILL_TOKENS 契约不一致"
    created = []
    for filename, content in TEMPLATES.items():
        file_path = workdir_path / filename
        content_filled = content
        for tok, val in fill_values.items():
            content_filled = content_filled.replace(tok, val)

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
    print(f"  3. 运行:python scripts/check_step.py --workdir \"{workdir_path}\" --step 1")


def main():
    parser = argparse.ArgumentParser(description="选题工坊 · 项目初始化")
    parser.add_argument("--workdir", "-w", required=True, help="工作目录路径(将创建)")
    parser.add_argument("--name", "-n", default="未命名研究主题", help="研究主题名称")
    parser.add_argument("--branch", "-b", default="推断性",
                        choices=["推断性", "描述性", "质性", "混合"],
                        help="学科分支:推断性 / 描述性 / 质性 / 混合")
    parser.add_argument("--language", "-l", default="zh-CN",
                        choices=["zh-CN", "en-US"],
                        help="语言:zh-CN / en-US")
    parser.add_argument("--force", action="store_true",
                        help="允许覆盖已存在的项目文件(默认拒绝,以防静默丢失)")
    args = parser.parse_args()

    init_project(args.workdir, args.name, args.branch, args.language, args.force)


if __name__ == "__main__":
    _force_utf8_stdio()
    main()