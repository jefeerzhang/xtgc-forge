"""check_step_lib · cli.py

argparse + main()。薄壳,只 import dispatch.check_step + helpers 必要符号。
"""
import argparse
import os
import sys
from pathlib import Path

from .dispatch import check_step
from .helpers import VALID_STEPS, _force_utf8_stdio, _self_version


def main():
    # 先强制 UTF-8 stdio(必须在 parse_args print 之前,否则 GBK 管道下 ✅ 崩溃)
    _force_utf8_stdio()
    VERSION = _self_version()
    parser = argparse.ArgumentParser(
        description=f"选题工坊 · 机器闸门检查 v{VERSION} (v0.3.18 起审查降级为过程建议)"
    )
    parser.add_argument("--workdir", "-w", required=True, help="工作目录(产出文件所在)")
    parser.add_argument("--step", "-s", required=True, help=f"Step 编号:{', '.join(VALID_STEPS)}")
    args = parser.parse_args()

    # 展开 ~ 与 . / ..(Windows 下 os.path.isdir 不识别 ~,原实现会把 ~/foo 判为不存在)
    args.workdir = str(Path(args.workdir).expanduser().resolve())

    if not os.path.isdir(args.workdir):
        print(f"❌ 目录不存在:{args.workdir}")
        sys.exit(1)

    # dispatch.check_step 失败时已输出 ❌ 与 bullet;成功横幅只在这里打一次。
    # review 软警告由 check_step_detail 一趟收齐后经 check_step 打到 stderr。
    passed, _errors = check_step(args.workdir, args.step)

    if passed:
        print(f"✅ Step {args.step} PASS")
        sys.exit(0)

    print()
    print("修复建议:")
    print("  1. 重新跑对应 step 的子命令")
    print("  2. 按上面错误信息补全缺失字段/加厚论述/补附录矩阵")
    print("  3. 再跑一次:python scripts/check_step.py --workdir <dir> --step " + args.step)
    sys.exit(1)


if __name__ == "__main__":
    _force_utf8_stdio()
    main()
