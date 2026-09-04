# -*- coding: utf-8 -*-
"""
scripts/check_step.py — THIN SHIM,保留向后兼容。

历史:原为 1005 行单体脚本(详见 scripts/check_step_lib/__init__.py docstring)。
重构后实现迁到 `check_step_lib` 包;本文件仅 re-export。

向后兼容:
  - `python scripts/check_step.py --step 6 ...` 仍可用(走 CLI main())
  - `import check_step` 后 `check_step.check_xxx` / `check_step.CONST` 全部命中
  - 11 个 test_*.py 与 .github/workflows/gate-check.yml 都不需要改

新增公共 API(从 check_step_lib 透出,推荐):
  - check_step.verify(workdir, step, file_name=None) -> Verdict
  - check_step.Verdict(typed)
  - check_step.check_step_router(...) 旧 check_step() 的别名

迁移路径:下次大改时删除本 shim,把 `import check_step` 改为
  `from scripts.check_step_lib import check_step_router as check_step`。
"""
from check_step_lib import *  # noqa: F401,F403  (17 常量 + 9 helper)
from check_step_lib import (  # noqa: F401  (8 闸门 + 路由)
    check_placeholders,
    check_step6_quality,
    check_interaction_log,
    check_rerun_record,
    check_readability,
    check_topic_scores,
    check_anti_collapse,
    check_review,
    check_step,
    check_step_router,
    STEP_RULES,
    Verdict,
    verify,
)


def _self_version() -> str:
    """shim 版本(供 --version 与调试)。"""
    return "check_step.py shim → check_step_lib (refactored)"


if __name__ == "__main__":
    # CLI 入口:转交 check_step_lib.cli(由 cli.py 的 if __name__ 触发)
    from check_step_lib.cli import main

    main()
