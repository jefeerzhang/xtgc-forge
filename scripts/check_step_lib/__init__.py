"""check_step_lib — 公共闸门面(package 入口)。

历史:此模块原是单一脚本 scripts/check_step.py(1005 行,11 个 test_*.py 引用)。
重构后拆为 helpers / gates / dispatch / cli 四层(同包)。

向后兼容:旧 scripts/check_step.py 已改写为 thin shim,re-export 下面这些名字,
所有 11 个 test_*.py 的 `import check_step` 不需要改任何代码。

新增公共 API(本 package 的正式入口):
  - Verdict:报告闸门输出(errors + soft_warnings;passed 只看 errors)
  - verify(workdir, step, file_name=None) -> Verdict:无 print/exit 的纯校验入口
  - check_step_detail(...) -> (errors, soft_warnings):完整纯计算面
  - check_step_router(...) -> list[str]:仅 errors 半边(向后兼容)
  - 其余 check_X / 16 个常量 / 9 个 helper 仍可 from .gates / .helpers 取
"""
from dataclasses import dataclass
from pathlib import Path

from .dispatch import (
    STEP_RULES,
    check_step,
    check_step_detail,
    check_step_router,
)
from .gates import *
from .helpers import Utf8ArtifactError  # noqa: F401 — 显式列入 __all__
from .helpers import *


@dataclass(frozen=True)
class Verdict:
    """verify() 的返回类型。

    errors 为空即硬闸通过(passed=True)。
    soft_warnings 是过程建议(如缺 review_*.md),永不阻塞 passed;
    与 CLI stderr 同源,供编排/agent 程序化消费。
    """
    step: str
    workdir: str
    file: str | None
    errors: tuple  # tuple[str, ...],只读
    soft_warnings: tuple = ()  # tuple[str, ...],只读

    @property
    def passed(self) -> bool:
        return not self.errors

    def __iter__(self):
        """允许 unpacking:ok, errs = verify(...) 与旧 (passed, errors) tuple 兼容。"""
        yield self.passed
        yield list(self.errors)


def verify(workdir, step: str, file_name: str | None = None) -> Verdict:
    """无 print/exit 副作用的校验入口(只读产物文件)。

    Returns:
        Verdict(step, workdir, file, errors, soft_warnings)
        verdict.passed = (len(errors) == 0)
        list(verdict) == [passed, errors]  # soft 不进 unpacking,保旧契约
    """
    workdir_path = Path(workdir)
    errors, soft = check_step_detail(workdir_path, step, file_name=file_name)
    return Verdict(
        step=step,
        workdir=str(workdir_path),
        file=file_name,
        errors=tuple(errors),
        soft_warnings=tuple(soft),
    )


__all__ = [
    # 16 常量(老 check_step.py 顶层全部;STEP_RULES 另列公共入口)
    "ANTI_COLLAPSE_LOW_TIER",
    "BODY_JARGON",
    "GATES",
    "MAX_BODY_SENTENCE",
    "MIN_PARAGRAPH_CHARS",
    "MIN_REVEALS_LEN",
    "PLACEHOLDER_PATTERNS",
    "PLACEHOLDER_PATTERNS_RE",
    "REQUIRED_GATES",
    "RERUN_DECLARE_PATTERNS",
    "RERUN_EMPTY_THRESHOLD",
    "RERUN_PHRASES",
    "REVIEW_VALID_VERDICTS",
    "SCORE_KEYS",
    # 公共入口
    "STEP_RULES",
    "TIER_BANDS",
    "VALID_STEPS",
    "Verdict",
    "Utf8ArtifactError",
    # 9 私有 helper(老 check_step.py 也是裸名暴露,shim 透传)
    "_count_cjk_and_alnum",
    "_count_matrix_data_rows",
    "_count_paragraphs",
    "_force_utf8_stdio",
    "_is_table_separator",
    "_read_text_utf8",
    "_resolve_workdir_file",
    "_self_version",
    "_tier_of",
    # 8 个 check_X 闸门 + 路由
    "check_anti_collapse",
    "check_interaction_log",
    "check_placeholders",
    "check_readability",
    "check_rerun_record",
    "check_review",
    "check_step",
    "check_step6_quality",
    "check_step_detail",
    "check_step_router",
    "check_topic_scores",
    "verify",
]
