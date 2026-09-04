"""
check_step_lib · dispatch.py

Step → 闸门路由表(STEP_RULES) + 顶层路由器。

本模块对外:

  - check_step_detail(workdir, step, ...) -> (errors, soft_warnings)
        纯计算入口:不打印、不写文件、不 sys.exit。
        errors 空=硬闸通过;soft_warnings 是过程建议,永不阻塞。
        review 硬/软同一趟 check_review,避免双读。

  - check_step_router(...) -> list[str]
        detail 的 errors 半边,兼容旧调用面。

  - check_step(workdir, step) -> tuple[bool, list[str]]
        CLI 打印层:失败 bullet → stdout,soft → stderr;
        ✅ PASS 横幅由 cli.py 统一打印。

历史:这两个函数原是同一份代码,耦合 print 副作用;重构后分离,以便
verify() 在 pytest capsys 下能干净运行(不触发 PermissionError)。

order matters:_check_step_* 先于 STEP_RULES 定义(后者 dict literal 引用前者)。
"""
from collections.abc import Callable
from pathlib import Path
import sys

from .gates import (
    check_anti_collapse,
    check_interaction_log,
    check_placeholders,
    check_rerun_record,
    check_review,
    check_step6_quality,
    check_topic_scores,
)
from .helpers import (
    GATES,
    VALID_STEPS,
    Utf8ArtifactError,
    _read_text_utf8,
    _resolve_workdir_file,
)

# Step 3a 分段头:名称 → 固定文案(勿用 f「--- {name} 校验失败 ---」,
# 中文名会多出空格,变成「反坍缩 校验失败」)。
_SCORE_COLLAPSE_SECTION = {
    "topic_scores.json": "--- topic_scores.json 校验失败 ---",
    "反坍缩": "--- 反坍缩校验失败 ---",
}

# ---- 4 个 step-private 额外规则(STEP_RULES 引用) ---------------------

def _check_scores_and_collapse(workdir_path: Path) -> list[tuple[str, list[str]]]:
    """topic_scores.json + 反坍缩两项校验;失败项以 (名称, errors) 返回。

    名称用作 --step all 的「[X]」前缀;Step 3a 分段头走 _SCORE_COLLAPSE_SECTION。
    """
    failed: list[tuple[str, list[str]]] = []
    ts_passed, ts_errors = check_topic_scores(workdir_path)
    if not ts_passed:
        failed.append(("topic_scores.json", ts_errors))
    ac_passed, ac_errors = check_anti_collapse(workdir_path)
    if not ac_passed:
        failed.append(("反坍缩", ac_errors))
    return failed


def _check_step_2c(workdir_path: Path, content: str, file_path: Path, _from_all: bool) -> list[str]:
    """Step 2c 额外校验:「证据来源」≥ 3 条 + 占位符拦截。"""
    errors: list[str] = []
    if content.count("证据来源") < 3:
        errors.append("Step 2c:「证据来源」出现 < 3 次(Gap 条数过少或未展开)")
    errors.extend(check_placeholders(content, "Step 2c"))
    return errors


def _check_step_3a(workdir_path: Path, content: str, file_path: Path, _from_all: bool) -> list[str]:
    """Step 3a 额外校验:topic_scores.json + 反坍缩(_from_all 时由 --step all 顶层统一调用,跳过以避免双前缀)。"""
    if _from_all:
        return []
    errors: list[str] = []
    for name, errs in _check_scores_and_collapse(workdir_path):
        errors.append(_SCORE_COLLAPSE_SECTION[name])
        errors.extend(errs)
    return errors


def _check_step_3b(workdir_path: Path, content: str, file_path: Path, _from_all: bool) -> list[str]:
    """Step 3b 额外校验:对抗压测小节(半强校验)。启用即做完整。"""
    if "对抗压测" not in content:
        return []
    errors: list[str] = []
    # 新格式(v0.3.12):生存标签 + 至少 6 类坍缩攻击名(经管语境)
    attack_kw = ["换情境", "换术语", "识别", "已被占", "不可证伪",
                 "范围过宽", "数据质量", "不可行", "贡献类型"]
    survival_kw = ["存活", "需收窄", "需转向", "坍缩"]
    has_survival = any(k in content for k in survival_kw)
    hit = sum(1 for k in attack_kw if k in content)
    new_style_ok = has_survival and hit >= 6
    # 旧格式(v0.3.6)兼容:魔鬼代言 + 最可能被拒 + 回应
    old_style_ok = all(k in content for k in ["魔鬼代言", "最可能被", "回应"])
    if not (new_style_ok or old_style_ok):
        detail = ""
        if not has_survival:
            detail += "缺少四档生存标签(存活/需收窄/需转向/坍缩)。"
        if hit < 6:
            detail += f"9 类攻击仅命中 {hit}/9(换情境/换术语/识别/已被占/不可证伪/范围过宽/数据质量/不可行/贡献类型),至少攻击 6 类。"
        errors.append(f"Step 3b 已含「对抗压测」小节,但未做完整:{detail}启用即做完整:每条攻击给 1 句回应 + 打 1 个生存标签")
    return errors


def _check_step_6(workdir_path: Path, content: str, file_path: Path, _from_all: bool) -> list[str]:
    """Step 6 额外校验:主报告质量 + 交互留痕 + 复跑授权(_from_all 时由 --step all 顶层统一调用交互/复跑)。"""
    errors: list[str] = []
    errors.extend(check_step6_quality(content))
    if _from_all:
        return errors
    il_passed, il_errors = check_interaction_log(workdir_path)
    if not il_passed:
        errors.append("--- 交互留痕校验失败(5 闸须有用户确认原话,禁止未交互交付)---")
        errors.extend(il_errors)
    rr_passed, rr_errors = check_rerun_record(workdir_path, file_path)
    if not rr_passed:
        errors.append("--- 复跑授权校验失败 ---")
        errors.extend(rr_errors)
    return errors


STEP_RULES: dict[str, Callable[..., list[str]]] = {
    "2c": _check_step_2c,
    "3a": _check_step_3a,
    "3b": _check_step_3b,
    "6": _check_step_6,
}


# ---- 顶层:纯计算路由(verify() / CLI 共用) ---------------------------

def _collect_reviews(
    workdir_path: Path, targets: list[str], *, prefixed: bool
) -> tuple[list[str], list[str]]:
    """一趟 check_review:硬错与软警告一起收齐。

    prefixed=True(--step all):硬/软均带 [review_{rt}.md] 前缀。
    prefixed=False(scan-review / topics-review):保持裸文案。
    """
    hard_out: list[str] = []
    soft_out: list[str] = []
    for rt in targets:
        status, hard, soft = check_review(workdir_path, rt)
        if status == "FAIL":
            if prefixed:
                hard_out.extend(f"[review_{rt}.md] {e}" for e in hard)
            else:
                hard_out.extend(hard)
        for w in soft:
            soft_out.append(f"[review_{rt}.md] {w}" if prefixed else w)
    return hard_out, soft_out


def check_step_detail(
    workdir, step: str, file_name: str | None = None, _from_all: bool = False
) -> tuple[list[str], list[str]]:
    """纯计算:不 print、不 sys.exit。返回 (errors, soft_warnings)。

    soft_warnings 永不进入 errors、不阻塞 passed;CLI 打到 stderr,
    verify() 放进 Verdict.soft_warnings。
    """
    workdir_path = Path(workdir)

    if step == "all":
        all_errors: list[str] = []
        for s in ["1", "2a", "2b", "2c", "3a", "3b", "4", "5", "6"]:
            errs, _soft = check_step_detail(workdir, s, _from_all=True)
            if errs:
                all_errors.extend([f"[step {s}] {e}" for e in errs])
        for name, errs in _check_scores_and_collapse(workdir_path):
            all_errors.extend([f"[{name}] {e}" for e in errs])
        il_passed, il_errors = check_interaction_log(workdir_path)
        if not il_passed:
            all_errors.extend([f"[交互留痕] {e}" for e in il_errors])
        main_report = _resolve_workdir_file(workdir_path, "00_研究计划报告.md")
        if main_report.exists():
            rr_passed, rr_errors = check_rerun_record(workdir_path, main_report)
            if not rr_passed:
                all_errors.extend([f"[复跑授权] {e}" for e in rr_errors])
        # v0.3.18:review 硬 FAIL 进 errors;soft 单独返回(同一趟 check_review)
        hard, soft = _collect_reviews(workdir_path, ["scan", "topics"], prefixed=True)
        all_errors.extend(hard)
        return all_errors, soft

    if step == "scores":
        return (
            [e for _name, errs in _check_scores_and_collapse(workdir_path) for e in errs],
            [],
        )

    review_target = {"scan-review": "scan", "topics-review": "topics"}.get(step)
    if review_target is not None:
        # WARN(只有 soft)不阻塞;FAIL(有 hard)阻塞——同一趟收集
        return _collect_reviews(workdir_path, [review_target], prefixed=False)

    if step not in GATES:
        return [f"未知 step: {step}。合法 step: {', '.join(VALID_STEPS)}"], []

    rule = GATES[step]
    file_path = _resolve_workdir_file(workdir_path, rule["file"])
    errors: list[str] = []

    if not file_path.exists():
        return (
            [f"{rule['fail_msg']}\n  文件不存在:{file_path}(根目录与 process/ 均未找到)"],
            [],
        )

    try:
        content = _read_text_utf8(file_path)
    except Utf8ArtifactError as e:
        return [str(e)], []
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

    extra = STEP_RULES.get(step)
    if extra is not None:
        errors.extend(extra(workdir_path, content, file_path, _from_all))

    return errors, []


def check_step_router(
    workdir, step: str, file_name: str | None = None, _from_all: bool = False
) -> list[str]:
    """纯计算:返回 errors(空=硬闸通过)。soft 见 check_step_detail / Verdict。"""
    errors, _soft = check_step_detail(workdir, step, file_name=file_name, _from_all=_from_all)
    return errors


# ---- 顶层:CLI 打印层(调用 detail + 报告;PASS 横幅留给 cli) -----------

def check_step(workdir, step: str) -> tuple[bool, list[str]]:
    """CLI 打印层:一趟 detail;失败 bullet → stdout,软警告 → stderr。

    与 check_step_detail 的区别:
      - 失败时 print() bullet 到 stdout
      - soft_warnings print() 到 stderr(不进 errors)
      - 成功时不打印 PASS(由 cli.py 统一打 ✅ Step X PASS,避免双份)
      - 返回 (passed: bool, errors: list[str]) 与老 check_step.py 签名兼容
    """
    errors, soft = check_step_detail(workdir, step)
    for w in soft:
        print(w, file=sys.stderr)

    passed = not errors
    if passed:
        return True, []

    print(f"❌ Step {step} FAIL")
    print(f"   workdir: {workdir}")
    # 每个错打 1 个 bullet;多行错后续行用 6 空格缩进保持人类可读
    # (测试用 ln.startswith("  - ") 计数,必须 1 条 err = 1 个 - 行)
    for e in errors:
        lines = e.splitlines() or [""]
        print(f"  - {lines[0]}")
        for ln in lines[1:]:
            print(f"      {ln}")
    return False, errors
