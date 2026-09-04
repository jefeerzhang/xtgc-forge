"""
check_step_lib · dispatch.py

Step → 闸门路由表(STEP_RULES) + 顶层路由器。

本模块暴露两个对外函数,语义完全不同:

  - check_step_router(workdir, step, _from_all=False) -> list[str]
        纯计算入口:不打印、不写文件、不 sys.exit。返回所有错误信息列表,
        空列表代表通过。是 verify() 与测试层的唯一调用面。

  - check_step(workdir, step) -> tuple[bool, list[str]]
        CLI 打印层:内部调用 check_step_router,把失败结果格式化到 stdout,
        把 review 软警告打到 stderr;返回 (passed, errors)。
        成功时的 ✅ PASS 横幅由 cli.py 统一打印,避免双份。

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

# ---- 4 个 step-private 额外规则(STEP_RULES 引用) ---------------------

def _check_step_2c(workdir_path: Path, content: str, file_path: Path, _from_all: bool) -> list[str]:
    """Step 2c 额外校验:「证据来源」≥ 3 条 + 占位符拦截。"""
    errors: list[str] = []
    if content.count("证据来源") < 3:
        errors.append("Step 2c:「证据来源」出现 < 3 次(Gap 条数过少或未展开)")
    errors.extend(check_placeholders(content, "Step 2c"))
    return errors


def _check_step_3a(workdir_path: Path, content: str, file_path: Path, _from_all: bool) -> list[str]:
    """Step 3a 额外校验:topic_scores.json + 反坍缩(_from_all 时由 --step all 顶层统一调用,跳过以避免双前缀)。"""
    errors: list[str] = []
    if _from_all:
        return errors
    ts_passed, ts_errors = check_topic_scores(workdir_path)
    if not ts_passed:
        errors.append("--- topic_scores.json 校验失败 ---")
        errors.extend(ts_errors)
    ac_passed, ac_errors = check_anti_collapse(workdir_path)
    if not ac_passed:
        errors.append("--- 反坍缩校验失败 ---")
        errors.extend(ac_errors)
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


# ---- 顶层:纯计算路由(verify() 调用这一层) ---------------------------

def check_step_router(workdir, step: str, file_name: str | None = None, _from_all: bool = False) -> list[str]:
    """纯计算:不 print、不 sys.exit。返回 errors list(空=通过)。

    设计要点:
      - 返回 list[str] 而非 (bool, list),与 verify()/tests 期望一致
      - soft warnings(如 review 警告)不进 errors;由 check_step() 打印层打到 stderr。
        原先在旧 check_step 里直接 stderr 的行为迁回打印层,router 保持纯计算。
    """
    workdir_path = Path(workdir)

    if step == "all":
        all_errors: list[str] = []
        for s in ["1", "2a", "2b", "2c", "3a", "3b", "4", "5", "6"]:
            errs = check_step_router(workdir, s, _from_all=True)
            if errs:
                all_errors.extend([f"[step {s}] {e}" for e in errs])
        ts_passed, ts_errors = check_topic_scores(workdir_path)
        if not ts_passed:
            all_errors.extend([f"[topic_scores.json] {e}" for e in ts_errors])
        ac_passed, ac_errors = check_anti_collapse(workdir_path)
        if not ac_passed:
            all_errors.extend([f"[反坍缩] {e}" for e in ac_errors])
        il_passed, il_errors = check_interaction_log(workdir_path)
        if not il_passed:
            all_errors.extend([f"[交互留痕] {e}" for e in il_errors])
        main_report = _resolve_workdir_file(workdir_path, "00_研究计划报告.md")
        if main_report.exists():
            rr_passed, rr_errors = check_rerun_record(workdir_path, main_report)
            if not rr_passed:
                all_errors.extend([f"[复跑授权] {e}" for e in rr_errors])
        # v0.3.18 审查降级:review FAIL 计入 hard errors;soft 警告不计入失败列表
        for rt in ["scan", "topics"]:
            r_status, r_hard, _r_soft = check_review(workdir_path, rt)
            if r_status == "FAIL":
                all_errors.extend([f"[review_{rt}.md] {e}" for e in r_hard])
        return all_errors

    if step == "scores":
        ts_passed, ts_errors = check_topic_scores(workdir_path)
        ac_passed, ac_errors = check_anti_collapse(workdir_path)
        combined = []
        if not ts_passed:
            combined.extend(ts_errors)
        if not ac_passed:
            combined.extend(ac_errors)
        return combined

    if step == "scan-review":
        status, hard, _soft = check_review(workdir_path, "scan")
        # v0.3.18 审查降级:WARN(只有 soft)视为 PASS,不阻塞;FAIL(有 hard)阻塞
        if status == "FAIL":
            return list(hard)
        return []

    if step == "topics-review":
        status, hard, _soft = check_review(workdir_path, "topics")
        if status == "FAIL":
            return list(hard)
        return []

    if step not in GATES:
        return [f"未知 step: {step}。合法 step: {', '.join(VALID_STEPS)}"]

    rule = GATES[step]
    file_path = _resolve_workdir_file(workdir_path, rule["file"])
    errors: list[str] = []

    if not file_path.exists():
        return [f"{rule['fail_msg']}\n  文件不存在:{file_path}(根目录与 process/ 均未找到)"]

    try:
        content = _read_text_utf8(file_path)
    except Utf8ArtifactError as e:
        return [str(e)]
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

    # 基础 GATES 通过后,分发到 per-step 额外规则(2c/3a/3b/6)
    extra = STEP_RULES.get(step)
    if extra is not None:
        errors.extend(extra(workdir_path, content, file_path, _from_all))

    return errors


# ---- 顶层:CLI 打印层(调用 router + 报告;PASS 横幅留给 cli) -----------

def _emit_review_soft_warnings(workdir, step: str) -> None:
    """过程建议打到 stderr,不进入 errors、不阻塞退出码。"""
    workdir_path = Path(workdir)
    if step == "all":
        for rt in ["scan", "topics"]:
            _status, _hard, soft = check_review(workdir_path, rt)
            for w in soft:
                print(f"[review_{rt}.md] {w}", file=sys.stderr)
        return
    if step == "scan-review":
        _status, _hard, soft = check_review(workdir_path, "scan")
        for w in soft:
            print(w, file=sys.stderr)
        return
    if step == "topics-review":
        _status, _hard, soft = check_review(workdir_path, "topics")
        for w in soft:
            print(w, file=sys.stderr)


def check_step(workdir, step: str) -> tuple[bool, list[str]]:
    """CLI 打印层:调路由,失败时输出 bullet 报告;软警告走 stderr。

    与 check_step_router 的区别:
      - 本函数在失败时 print() bullet 到 stdout
      - review 过程建议 print() 到 stderr(不进 errors)
      - 成功时不打印 PASS(由 cli.py 统一打 ✅ Step X PASS,避免双份)
      - 返回 (passed: bool, errors: list[str]) 与老 check_step.py 签名兼容

    业务逻辑全部委托给 check_step_router。
    """
    _emit_review_soft_warnings(workdir, step)
    errors = check_step_router(workdir, step)
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