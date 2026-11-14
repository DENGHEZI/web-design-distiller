#!/usr/bin/env python3
"""Compute the rubric score and a reproducible before/after evaluation report.

Part of the web-design-distiller skill. All numbers come from audit_page.py JSON.
No score is ever estimated by hand.
"""
from __future__ import annotations

import argparse
import datetime
import json
import sys
from pathlib import Path

TOOL_VERSION = "1.0.0"

DIMENSION_CHECKS = {
    "clarity": ["h1_count", "cta_count", "nav_items", "heading_size_ratio"],
    "system": ["spacing_violations", "type_scale_violations", "unique_colors", "inline_style_count"],
    "restraint": ["gradient_count", "unique_colors", "max_width_defined", "whitespace_token"],
    "a11y": ["contrast_failures", "contrast_min_ratio", "img_alt_missing",
             "focus_visible_defined", "outline_none_uncompensated", "semantic_tags",
             "lang_attr", "title_present", "absolute_font_units", "reduced_motion"],
    "perf": ["img_unsized", "external_resources", "css_imports", "bytes_total", "meta_viewport"],
    "convention": ["interaction_states", "status_feedback", "reduced_motion"],
}
DIMENSION_LABEL = {
    "clarity": "目标与层级", "system": "系统性约束", "restraint": "克制与密度",
    "a11y": "可访问性", "perf": "性能与稳定性", "convention": "惯例与状态",
}
WEIGHTS = {
    "landing": dict(clarity=20, system=20, restraint=15, a11y=20, perf=15, convention=10),
    "app": dict(clarity=20, system=20, restraint=10, a11y=20, perf=10, convention=20),
    "docs": dict(clarity=25, system=15, restraint=10, a11y=25, perf=15, convention=10),
    "commerce": dict(clarity=20, system=15, restraint=10, a11y=20, perf=20, convention=15),
}
SCORE_OF_STATUS = {"pass": 1.0, "warn": 0.5, "fail": 0.0}

NOT_COVERED = [
    "真实 LCP / INP / CLS 未实测（脚本只测 img 尺寸、外部资源数、体积等风险代理指标）；需 Lighthouse / CrUX 现场数据，按 75 分位、分移动端与桌面端评估。",
    "跨浏览器与真机渲染、字体加载过程、弱网抖动。",
    "动态交互后的可访问性（弹窗焦点陷阱、路由切换后的焦点管理）。",
    "打包后的 CSS-in-JS / 编译产物样式（仅解析 HTML 内联 <style> 与 --css 传入的文件）。",
    "渐变、图片、半透明背景上的实际文字对比度（脚本按单一 body 背景近似计算）。",
    "内容真实性、文案说服力与转化效果（主观项，不并入总分）。",
]


def load(path: Path):
    d = json.loads(path.read_text(encoding="utf-8"))
    if "checks" not in d:
        raise ValueError(f"{path}: not an audit JSON (missing 'checks')")
    return d


def status(data, key):
    return data["checks"].get(key, {}).get("status", "fail")


def hard_gates(data):
    """Return list of (id, passed, detail)."""
    c = data["checks"]
    def ok(k):
        return status(data, k) == "pass"
    contrast_ok = ok("contrast_failures")
    needs_manual = bool(c.get("contrast_failures", {}).get("note"))
    g1_detail = c.get("contrast_min_ratio", {}).get("evidence", "")
    if needs_manual:
        g1_detail += "（渐变/半透明背景需人工复核）"
    gates = [
        ("G1 对比度达标 (WCAG 1.4.3/1.4.11)", contrast_ok, g1_detail),
        ("G2 图片 alt 完整", ok("img_alt_missing"),
         c.get("img_alt_missing", {}).get("evidence", "")[:120]),
        ("G3 键盘焦点可见且未被抹除", ok("focus_visible_defined") and ok("outline_none_uncompensated"),
         f"focus-visible={status(data,'focus_visible_defined')}, "
         f"outline-none={status(data,'outline_none_uncompensated')}"),
        ("G4 主 CTA 不超过一个", ok("cta_count"),
         c.get("cta_count", {}).get("evidence", "")[:120]),
        ("G5 lang 与 viewport 齐备", ok("lang_attr") and ok("meta_viewport"),
         f"lang={status(data,'lang_attr')}, viewport={status(data,'meta_viewport')}"),
    ]
    return gates


def score(data, page_type):
    w = WEIGHTS[page_type]
    dims, missing = {}, []
    for dim, keys in DIMENSION_CHECKS.items():
        vals = []
        for k in keys:
            if k not in data["checks"]:
                missing.append(k)
                vals.append(0.0)
            else:
                vals.append(SCORE_OF_STATUS[status(data, k)])
        raw = sum(vals) / len(vals) if vals else 0.0
        dims[dim] = {"raw": raw, "score": round(raw * 4, 2),
                     "weighted": round(raw * w[dim], 2), "max": w[dim]}
    total = round(sum(d["weighted"] for d in dims.values()), 1)
    gates = hard_gates(data)
    gates_ok = all(g[1] for g in gates)
    grade = ("FAIL" if not gates_ok else
             "A" if total >= 90 else "B" if total >= 75 else "C" if total >= 60 else "D")
    return {"total": total, "grade": grade, "dimensions": dims,
            "weights": w, "gates": gates, "gates_ok": gates_ok, "missing": missing}


def val(data, key):
    v = data["checks"].get(key, {}).get("value")
    return v if not isinstance(v, (dict, list)) else json.dumps(v, ensure_ascii=False)


def fmt(v):
    return "—" if v is None else str(v)


def report(before, after, before_path, after_path, page_type, manual):
    b, a = score(before, page_type), score(after, page_type)
    now = datetime.datetime.now().astimezone().isoformat(timespec="seconds")
    L = []
    add = L.append
    add("# 网页设计改造效果评估报告")
    add("")
    add(f"- 生成时间：{now}")
    add(f"- 页面类型：`{page_type}`（权重见下表，评估前已固定）")
    add(f"- 评分工具：`score.py v{TOOL_VERSION}` + `audit_page.py v{before.get('tool_version','?')}`")
    add(f"- 依据：`references/rubric.md` v1.0、`references/principles.md` P1–P8、`references/sources.md` S01–S15")
    add("")
    add("> 本报告的所有分数均由脚本从审计 JSON 计算，不含人工估算。"
        "客观项与主观项分区呈现；未测项在文末显式列出。")
    add("")
    add("## 1. 结论")
    add("")
    add("| 指标 | 改造前 | 改造后 | 变化 |")
    add("| --- | --- | --- | --- |")
    add(f"| 客观总分 | {b['total']} | {a['total']} | {round(a['total']-b['total'],1):+g} |")
    add(f"| 等级 | {b['grade']} | {a['grade']} | — |")
    add(f"| 硬门槛 | {'全部通过' if b['gates_ok'] else '存在失败'} | {'全部通过' if a['gates_ok'] else '存在失败'} | — |")
    fail_b = [k for k, v in before["checks"].items() if v["status"] == "fail"]
    fail_a = [k for k, v in after["checks"].items() if v["status"] == "fail"]
    add(f"| fail 检查项 | {len(fail_b)} | {len(fail_a)} | {len(fail_a)-len(fail_b):+g} |")
    add("")
    if not a["gates_ok"]:
        add("**整体判定：FAIL（存在未通过的硬门槛，等级作废）。**")
    else:
        add(f"**整体判定：{a['grade']} 级，硬门槛全部通过。**")
    add("")
    add("> **满分含义**：100 分只表示「通过本 rubric 的全部静态检查项」，不代表真实用户体验最优，"
        "也不覆盖第 7 节列出的未测项。评分表本身是目的性抽样的产物，边界见 `references/sources.md` §0。")
    add("")
    add("## 2. 硬门槛前后对照")
    add("")
    add("| 门槛 | 改造前 | 改造后 | 证据 / 备注 |")
    add("| --- | --- | --- | --- |")
    for (gid, okb, detb), (_, oka, deta) in zip(b["gates"], a["gates"]):
        add(f"| {gid} | {'PASS' if okb else 'FAIL'} | {'PASS' if oka else 'FAIL'} | {deta} |")
    add("")
    add("## 3. 六维度得分（原始分 0–4，加权后计入总分）")
    add("")
    add("| 维度 | 权重 | 改造前 | 改造后 | Δ |")
    add("| --- | --- | --- | --- | --- |")
    for dim in DIMENSION_CHECKS:
        wb, wa = b["dimensions"][dim], a["dimensions"][dim]
        add(f"| {DIMENSION_LABEL[dim]} (`{dim}`) | {b['weights'][dim]} | "
            f"{wb['score']}（加权 {wb['weighted']}） | {wa['score']}（加权 {wa['weighted']}） | "
            f"{round(wa['score']-wb['score'],2):+g} |")
    add("")
    add("> 部分检查项按 rubric 同时归属两个维度（`unique_colors`、`reduced_motion`），属设计而非重复计分。")
    add("")
    add("## 4. 逐项改造验证（fail → pass）")
    add("")
    fixed, still_bad, regressed = [], [], []
    keys = sorted(set(before["checks"]) | set(after["checks"]))
    for k in keys:
        sb, sa = status(before, k), status(after, k)
        if SCORE_OF_STATUS[sb] < SCORE_OF_STATUS[sa]:
            fixed.append((k, sb, sa, val(before, k), val(after, k)))
        elif SCORE_OF_STATUS[sb] > SCORE_OF_STATUS[sa]:
            regressed.append((k, sb, sa, val(before, k), val(after, k)))
        elif sa == "fail":
            still_bad.append((k, val(after, k), after["checks"][k].get("evidence", "")))
    if fixed:
        add("| 检查 id | 前 | 后 | 前值 | 后值 |")
        add("| --- | --- | --- | --- | --- |")
        for k, sb, sa, vb, va in fixed:
            add(f"| `{k}` | {sb} | {sa} | {fmt(vb)} | {fmt(va)} |")
    else:
        add("（无状态改善项）")
    add("")
    if still_bad:
        add("**改造后仍失败（需继续处理）：**")
        add("")
        for k, v, e in still_bad:
            add(f"- `{k}` = {fmt(v)} — {e[:140]}")
        add("")
    if regressed:
        add("**回退项（必须解释或修复）：**")
        add("")
        for k, sb, sa, vb, va in regressed:
            add(f"- `{k}`：{sb} → {sa}（{fmt(vb)} → {fmt(va)}）")
        add("")
    add("## 5. 客观项明细（改造后）")
    add("")
    add("| 检查 id | 状态 | 值 | 证据 |")
    add("| --- | --- | --- | --- |")
    for k in sorted(after["checks"]):
        c = after["checks"][k]
        e = str(c.get("evidence", "")).replace("|", "\\|")[:150]
        add(f"| `{k}` | {c['status']} | {fmt(val(after,k))} | {e} |")
    add("")
    add("## 6. 主观分区（不并入总分）")
    add("")
    if manual:
        add("| 项目 | 人工评分 (0–4) |")
        add("| --- | --- |")
        for k, v in manual.items():
            if k != "note":
                add(f"| {k} | {v} |")
        if manual.get("note"):
            add("")
            add(f"> 评审备注：{manual['note']}")
    else:
        add("本次未提供人工评分（`--manual`）。品牌气质、文案说服力、业务信息架构均未打分，"
            "**不得**把客观总分表述为「综合设计评分」。")
    add("")
    add("## 7. 未覆盖项（必读，禁止省略）")
    add("")
    for i, t in enumerate(NOT_COVERED, 1):
        add(f"{i}. {t}")
    add("")
    for n in after.get("notes", [])[:4]:
        add(f"- 审计脚本注释：{n}")
    add("")
    add("## 8. 复现")
    add("")
    add(f"- 改造前：`{before['input']['path']}` SHA-256 `{before['input']['sha256']}`")
    add(f"- 改造后：`{after['input']['path']}` SHA-256 `{after['input']['sha256']}`")
    add(f"- 审计 JSON：`{before_path}` / `{after_path}`")
    add("")
    add("```bash")
    add(f"python scripts/audit_page.py <before.html> --type {page_type} --json before.json")
    add(f"python scripts/audit_page.py <after.html>  --type {page_type} --json after.json")
    add(f"python scripts/score.py --before before.json --after after.json --type {page_type} --out evaluation.md")
    add("```")
    add("")
    add("用相同输入与脚本版本重跑，应得到完全相同的分数。")
    add("")
    add("---")
    add("")
    add("来源与版权：评分规则蒸馏自 `references/sources.md` 所列 S01–S15。"
        "NN/g 十大可用性启发式归 Jakob Nielsen / Nielsen Norman Group 所有，引用时保留署名。"
        "本技能不覆盖「所有」GitHub 项目与「所有」网页，采样边界见 `references/sources.md` §0。")
    return "\n".join(L), b, a


def main():
    ap = argparse.ArgumentParser(description="Score before/after design audits")
    ap.add_argument("--before", type=Path, required=True)
    ap.add_argument("--after", type=Path, required=True)
    ap.add_argument("--type", default="landing", choices=list(WEIGHTS))
    ap.add_argument("--manual", type=Path, help="optional JSON with human-only scores")
    ap.add_argument("--out", type=Path, help="write markdown report here")
    ap.add_argument("--score-json", type=Path, help="write machine-readable scores here")
    args = ap.parse_args()
    before, after = load(args.before), load(args.after)
    manual = json.loads(args.manual.read_text(encoding="utf-8")) if args.manual else None
    md, b, a = report(before, after, args.before, args.after, args.type, manual)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(md, encoding="utf-8")
    if args.score_json:
        args.score_json.parent.mkdir(parents=True, exist_ok=True)
        args.score_json.write_text(json.dumps({"before": b, "after": a}, ensure_ascii=False, indent=2),
                                   encoding="utf-8")
    print(md if not args.out else
          f"before={b['total']} ({b['grade']})  after={a['total']} ({a['grade']})  "
          f"delta={round(a['total']-b['total'],1):+g}  gates_after={'PASS' if a['gates_ok'] else 'FAIL'}"
          f"  report={args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
