#!/usr/bin/env python3
"""Compute the rubric score and a reproducible three-layer evaluation report.

Part of the web-design-distiller skill, v2 (anti-self-certification).

Three layers are reported SEPARATELY and must never be merged into one "design score":
  1. Static compliance score  - from audit_page.py (source rules only)
  2. Real browser measurement - from browser_audit.py (LCP/CLS/rendered contrast/overflow)
  3. Visual quality review    - subjective, screenshot-based, never merged into layer 1

All numeric scores come from scripts. Nothing is estimated by hand.
"""
from __future__ import annotations

import argparse
import datetime
import json
import sys
from pathlib import Path

TOOL_VERSION = "2.0.0"

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
    "线上 75 分位 Core Web Vitals 未测：browser_audit.py 是本地 file:// 单次测量，不等同 CrUX/RUM 现场数据；INP 需要真实交互，本工具完全未测。",
    "本地 LCP 单次测量波动可达 ±100ms，不能用来比较两版快慢；跨弱网、低端设备与移动端未测。",
    "跨浏览器与真机渲染、字体实际加载效果、动态交互后的可访问性（弹窗焦点陷阱、路由切换）。",
    "打包后的 CSS-in-JS / 编译产物样式（仅解析 HTML 内联 <style> 与 --css 传入的文件）。",
    "渐变、图片、半透明背景上的实际文字对比度仍需人工复核。",
    "视觉质量评分是模型/人工主观判断，不是真人用户研究，也不预测转化率。",
    "动效的帧率与卡顿（jank）未测；只验证 reduced-motion 降级后内容可见、以及加载阶段 CLS。",
    "内容真实性、文案说服力与业务信息架构。",
]


def load(path: Path):
    d = json.loads(path.read_text(encoding="utf-8"))
    if "checks" not in d:
        raise ValueError(f"{path}: not an audit JSON (missing 'checks')")
    return d


def load_json(path: Path | None):
    return json.loads(path.read_text(encoding="utf-8")) if path else None


def status(data, key):
    return data["checks"].get(key, {}).get("status", "fail")


def hard_gates(data):
    c = data["checks"]
    def ok(k):
        return status(data, k) == "pass"
    needs_manual = bool(c.get("contrast_failures", {}).get("note"))
    g1 = c.get("contrast_min_ratio", {}).get("evidence", "")
    if needs_manual:
        g1 += "（渐变/半透明背景需人工复核）"
    return [
        ("G1 对比度达标 (WCAG 1.4.3/1.4.11)", ok("contrast_failures"), g1),
        ("G2 图片 alt 完整", ok("img_alt_missing"),
         c.get("img_alt_missing", {}).get("evidence", "")[:120]),
        ("G3 键盘焦点可见且未被抹除", ok("focus_visible_defined") and ok("outline_none_uncompensated"),
         f"focus-visible={status(data,'focus_visible_defined')}, "
         f"outline-none={status(data,'outline_none_uncompensated')}"),
        ("G4 主 CTA 不超过一个", ok("cta_count"), c.get("cta_count", {}).get("evidence", "")[:120]),
        ("G5 lang 与 viewport 齐备", ok("lang_attr") and ok("meta_viewport"),
         f"lang={status(data,'lang_attr')}, viewport={status(data,'meta_viewport')}"),
    ]


def browser_gates(d):
    if not d:
        return []
    p, c, l = d["performance"], d["rendered_contrast"], d["layout"]
    gates = [
        ("B1 渲染后文字对比度达标", c["failures"] == 0,
         f"checked={c['checked']} failures={c['failures']} min_ratio={c['min_ratio']}"),
        ("B2 无破图", l["brokenImages"] == 0, f"brokenImages={l['brokenImages']}"),
        ("B3 无横向溢出", not l["horizontalOverflow"],
         f"scrollWidth={l['scrollWidth']} / viewport={l['viewportWidth']}"),
        ("B4 CLS ≤ 0.1（本地）", p["cls"] <= 0.1, f"CLS={p['cls']}"),
        ("B5 LCP ≤ 2500ms（本地）", p["lcp_ms"] <= 2500, f"LCP={p['lcp_ms']}ms"),
    ]
    if d.get("motion"):
        m = d["motion"]
        gates.append(("B6 动效降级后内容仍可见", m.get("reduced_motion_ok") is True,
                      f"reduced-motion min opacity={m.get('reduced_motion_min_opacity')}"))
        gates.append(("B7 滚动后揭示元素全部可见", m.get("normal_all_visible") is True,
                      f"reveals={m.get('reveal_count')} min opacity={m.get('normal_min_opacity_after_scroll')}"))
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
    band = ("FAIL" if not gates_ok else
            "A" if total >= 90 else "B" if total >= 75 else "C" if total >= 60 else "D")
    return {"total": total, "band": band, "dimensions": dims,
            "weights": w, "gates": gates, "gates_ok": gates_ok, "missing": missing}


def val(data, key):
    v = data["checks"].get(key, {}).get("value")
    return v if not isinstance(v, (dict, list)) else json.dumps(v, ensure_ascii=False)


def fmt(v):
    return "—" if v is None else str(v)


def report(before, after, before_path, after_path, page_type, manual,
           bb, ba, visual, independent, independent_name):
    b, a = score(before, page_type), score(after, page_type)
    bg_b, bg_a = browser_gates(bb), browser_gates(ba)
    bg_a_ok = all(g[1] for g in bg_a) if bg_a else None
    now = datetime.datetime.now().astimezone().isoformat(timespec="seconds")
    self_authored = ("examples" in before["input"]["path"].replace("\\", "/") or
                     "examples" in after["input"]["path"].replace("\\", "/"))
    L = []
    add = L.append

    add("# 网页设计改造效果评估报告（v2 · 三层结论）")
    add("")
    add(f"- 生成时间：{now}")
    add(f"- 页面类型：`{page_type}`（权重评估前已固定）")
    add(f"- 工具：`score.py v{TOOL_VERSION}` + `audit_page.py` + `browser_audit.py`")
    add(f"- 依据：`references/rubric.md` v2、`references/principles.md` P1–P8、`references/sources.md` S01–S15")
    add("")
    add("> **三层结论分开报，禁止合并成一个「设计评分」**：")
    add("> ① 静态合规分（只看源码规则）② 真实浏览器测量（渲染与性能）③ 视觉质量盲评（主观）。")
    add("")
    add("## 0. 反自证声明（先读这一段）")
    add("")
    if self_authored:
        add("**本次为自证样本**：`before` / `after` 都出自本仓库 `examples/`，且改造页是按本 rubric "
            "逐条构造的。因此「静态合规分接近满分」是设计上的必然结果，**不能作为技能有效性的证据**。")
        add("")
    add("**实测反证**：本仓库第 1 轮版本（`examples/after-v1.html`，视觉模板感明显）与第 2 轮重做版本"
        "（`examples/after.html`）在同一把 rubric 下**静态合规分同为 100.0**，但视觉盲评分别为 "
        "**5.0 / 10 与 8.0 / 10**。")
    add("")
    add("→ **合规分对视觉质量零区分度。分数提升 ≠ 视觉效果提升。** 本技能的有效性只能由"
        "「真实浏览器测量 + 独立样本验证 + 视觉盲评」共同支撑。")
    add("")
    add("## 1. 三层结论")
    add("")
    add("| 层 | 指标 | 改造前 | 改造后 | 变化 |")
    add("| --- | --- | --- | --- | --- |")
    add(f"| ① 静态合规 | 合规分（0–100） | {b['total']} | {a['total']} | {round(a['total']-b['total'],1):+g} |")
    add(f"| ① 静态合规 | 合规档位 | {b['band']} | {a['band']} | — |")
    add(f"| ① 静态合规 | 硬门槛 | {'全部通过' if b['gates_ok'] else '存在失败'} | "
        f"{'全部通过' if a['gates_ok'] else '存在失败'} | — |")
    fail_b = [k for k, v in before["checks"].items() if v["status"] == "fail"]
    fail_a = [k for k, v in after["checks"].items() if v["status"] == "fail"]
    add(f"| ① 静态合规 | fail 检查项 | {len(fail_b)} | {len(fail_a)} | {len(fail_a)-len(fail_b):+g} |")
    if bb and ba:
        cb, ca = bb["rendered_contrast"], ba["rendered_contrast"]
        lb, la = bb["layout"], ba["layout"]
        pb, pa = bb["performance"], ba["performance"]
        add(f"| ② 真实渲染 | 渲染后对比度失败 | {cb['failures']} | {ca['failures']} | "
            f"{ca['failures']-cb['failures']:+g} |")
        add(f"| ② 真实渲染 | 破图数 | {lb['brokenImages']} | {la['brokenImages']} | "
            f"{la['brokenImages']-lb['brokenImages']:+g} |")
        add(f"| ② 真实渲染 | 语义地标 | {lb['landmarks']} | {la['landmarks']} | "
            f"{la['landmarks']-lb['landmarks']:+g} |")
        add(f"| ② 真实渲染 | LCP（首次冷启动） | {pb['lcp_ms']}ms | {pa['lcp_ms']}ms | "
            f"{round(pa['lcp_ms']-pb['lcp_ms'],1):+g}ms |")
        add(f"| ② 真实渲染 | CLS（本地单次） | {pb['cls']} | {pa['cls']} | — |")
        add(f"| ② 真实渲染 | 体验门槛 | {'—' if not bg_b else ('全部通过' if all(g[1] for g in bg_b) else '存在失败')} | "
            f"{'全部通过' if bg_a_ok else '存在失败'} | — |")
    else:
        add("| ② 真实渲染 | 未运行 `browser_audit.py` | — | — | 不可声称已测 |")
    if visual:
        sc = visual.get("scores", {})
        vb = sc.get("before", {}).get("score")
        v2 = (sc.get("after_v4", {}).get("score")
              or sc.get("after_v2", {}).get("score")
              or sc.get("after", {}).get("score"))
        add(f"| ③ 视觉盲评 | 主观分（0–10，**不并入**） | {fmt(vb)} | {fmt(v2)} | — |")
    else:
        add("| ③ 视觉盲评 | 未做 | — | — | 不可声称视觉质量提升 |")
    add("")
    add(f"**静态合规判定：{'全部检查通过' if a['gates_ok'] and all(v['status']!='fail' for v in after['checks'].values()) else '存在未通过项'}。"
        "该判定只说明源码符合本 rubric，不代表视觉质量。**")
    add("")
    if bb and ba and ba["performance"]["lcp_ms"] > bb["performance"]["lcp_ms"]:
        add(f"> **反向指标**：本地 LCP 从 {bb['performance']['lcp_ms']}ms 变慢到 "
            f"{ba['performance']['lcp_ms']}ms。合规分上升并不代表所有体验指标改善。"
            "本地测量波动大、区间重叠，需线上 75 分位数据才能定论。")
        add("")
    add("> **满分含义**：100 分只表示「通过本 rubric 的全部静态检查项」。评分表本身是目的性抽样的产物，"
        "边界见 `references/sources.md` §0。")
    add("")

    add("## 2. 硬门槛")
    add("")
    add("### 2.1 静态硬门槛（G）")
    add("")
    add("| 门槛 | 改造前 | 改造后 | 证据 / 备注 |")
    add("| --- | --- | --- | --- |")
    for (gid, okb, _), (_, oka, deta) in zip(b["gates"], a["gates"]):
        add(f"| {gid} | {'PASS' if okb else 'FAIL'} | {'PASS' if oka else 'FAIL'} | {deta} |")
    add("")
    if bg_a:
        add("### 2.2 真实渲染体验门槛（B）")
        add("")
        add("| 门槛 | 改造前 | 改造后 | 证据 / 备注 |")
        add("| --- | --- | --- | --- |")
        for (gid, okb, _), (_, oka, deta) in zip(bg_b, bg_a):
            add(f"| {gid} | {'PASS' if okb else 'FAIL'} | {'PASS' if oka else 'FAIL'} | {deta} |")
        add("")
        add("> B4/B5 使用本地 file:// 单次测量，仅作冒烟检查，不等同线上达标。")
        add("")

    add("## 3. 静态合规六维度（仅反映源码规则符合度）")
    add("")
    add("| 维度 | 权重 | 改造前 | 改造后 | Δ |")
    add("| --- | --- | --- | --- | --- |")
    for dim in DIMENSION_CHECKS:
        wb, wa = b["dimensions"][dim], a["dimensions"][dim]
        add(f"| {DIMENSION_LABEL[dim]} (`{dim}`) | {b['weights'][dim]} | "
            f"{wb['score']}（加权 {wb['weighted']}） | {wa['score']}（加权 {wa['weighted']}） | "
            f"{round(wa['score']-wb['score'],2):+g} |")
    add("")
    add("> `unique_colors`、`reduced_motion` 按 rubric 同时归属两个维度，属设计而非重复计分。")
    add("")

    add("## 4. 逐项改造验证（fail → pass）")
    add("")
    fixed, still_bad, regressed = [], [], []
    for k in sorted(set(before["checks"]) | set(after["checks"])):
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
        add("**改造后仍失败：**")
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

    if bb and ba:
        add("## 5. 真实浏览器测量（Playwright + Edge）")
        add("")
        add("| 指标 | 改造前 | 改造后 | 说明 |")
        add("| --- | --- | --- | --- |")
        add(f"| LCP | {bb['performance']['lcp_ms']}ms | {ba['performance']['lcp_ms']}ms | 本地单次，波动大 |")
        add(f"| FCP | {bb['performance']['fcp_ms']}ms | {ba['performance']['fcp_ms']}ms | 本地单次 |")
        add(f"| CLS | {bb['performance']['cls']} | {ba['performance']['cls']} | 加载阶段，无用户交互 |")
        add(f"| 渲染后对比度检查数 | {bb['rendered_contrast']['checked']} | {ba['rendered_contrast']['checked']} | 含继承色与祖先背景 |")
        add(f"| 渲染后对比度失败 | {bb['rendered_contrast']['failures']} | {ba['rendered_contrast']['failures']} | WCAG 1.4.3 |")
        add(f"| 最小对比度 | {bb['rendered_contrast']['min_ratio']} | {ba['rendered_contrast']['min_ratio']} | — |")
        add(f"| 破图 | {bb['layout']['brokenImages']} | {ba['layout']['brokenImages']} | — |")
        add(f"| 横向溢出 | {bb['layout']['horizontalOverflow']} | {ba['layout']['horizontalOverflow']} | — |")
        add(f"| 可聚焦元素 | {bb['layout']['focusableCount']} | {ba['layout']['focusableCount']} | — |")
        add(f"| LCP 元素 | `<{bb['performance']['lcp_element']}>` | `<{ba['performance']['lcp_element']}>` | — |")
        add("")
        if bb.get("motion") and ba.get("motion"):
            mb, ma = bb["motion"], ba["motion"]
            add("**动效验收（第 3 轮新增）**")
            add("")
            add("| 检查 | 改造前 | 改造后 |")
            add("| --- | --- | --- |")
            add(f"| 揭示元素数量 | {mb.get('reveal_count')} | {ma.get('reveal_count')} |")
            add(f"| 滚动后全部可见 | {mb.get('normal_all_visible')} | {ma.get('normal_all_visible')} |")
            add(f"| reduced-motion 下全部可见 | {mb.get('reduced_motion_ok')} | {ma.get('reduced_motion_ok')} |")
            add("")
            add("> 动效只用 `transform` / `opacity`，因此不产生布局位移；`prefers-reduced-motion: reduce` "
                "下所有内容强制 `opacity: 1`。帧率与卡顿未测。")
            add("")
        if ba.get("repeat"):
            add(f"> **重复测量**：每个页面用 {bb.get('repeat',1)} / {ba.get('repeat',1)} 个**全新浏览器上下文**分别冷加载；"
                "主值取首次冷启动，缓存后的快速重载不计入结论。"
                f"LCP 实测区间 before {bb['performance'].get('lcp_min_ms')}–{bb['performance'].get('lcp_max_ms')}ms、"
                f"after {ba['performance'].get('lcp_min_ms')}–{ba['performance'].get('lcp_max_ms')}ms。"
                "区间重叠且为本地测量时，**不得宣称两版性能有差异**。")
            add("")
        add("> **测量边界**：本地 `file://`、无网络、桌面 1440px。INP 未测；"
            "这些数字**不能**替代 CrUX/RUM 的 75 分位线上数据，也不能用来宣称「性能达标」。")
        add("")

    if visual:
        add("## 6. 视觉质量盲评（主观，不并入任何分数）")
        add("")
        add(f"- 方法：{visual.get('method','')}")
        add(f"- 量纲：{visual.get('scale','0-10')}")
        add("")
        add("| 版本 | 主观分 | 评审要点 |")
        add("| --- | --- | --- |")
        for key, item in visual.get("scores", {}).items():
            add(f"| `{key}` | {item.get('score')} | {item.get('notes','')} |")
        add("")
        shots = visual.get("screenshots", {})
        if shots:
            add("截图（可复核）：" + "、".join(f"`{v}`" for v in shots.values()))
            add("")
        for lim in visual.get("limitations", []):
            add(f"- 局限：{lim}")
        add("")
        add("> 该分数由模型/人工基于截图给出，**没有**参考 rubric 与源码，属主观判断，非真人用户研究。")
        add("")

    if independent:
        ic = independent.get("checks", {})
        n_fail = sum(1 for v in ic.values() if v.get("status") == "fail")
        n_warn = sum(1 for v in ic.values() if v.get("status") == "warn")
        add("## 7. 独立第三方样本验证")
        add("")
        add(f"- 样本：`{independent_name or independent.get('input',{}).get('path','third-party')}`"
            f"（SHA-256 `{independent.get('input',{}).get('sha256','')[:16]}`）")
        add(f"- 该页面**不是**按本 rubric 构造的，用于检验脚本对陌生输入是否仍能产出稳定结论。")
        add(f"- 结果：{len(ic)} 项检查，fail={n_fail}，warn={n_warn}。")
        add("")
        fails = [k for k, v in ic.items() if v.get("status") == "fail"]
        if fails:
            add("主要失败项：" + "、".join(f"`{k}`" for k in sorted(fails)))
            add("")
        add("> **已知偏差（必须披露）**：极简的单页文档（如 `example.com`）没有导航、地标、状态文案，"
            "按面向落地页的 rubric 会被扣不少分，但页面本身可能完全适用。这说明本 rubric 是"
            "**类型相关的工具，不是普适的「设计好坏」裁判**；跨类型比较必须重新定 P0 与权重。")
        add("")

    add("## 8. 静态客观项明细（改造后）")
    add("")
    add("| 检查 id | 状态 | 值 | 证据 |")
    add("| --- | --- | --- | --- |")
    for k in sorted(after["checks"]):
        c = after["checks"][k]
        e = str(c.get("evidence", "")).replace("|", "\\|")[:150]
        add(f"| `{k}` | {c['status']} | {fmt(val(after,k))} | {e} |")
    add("")

    add("## 9. 人工评分（可选，不并入）")
    add("")
    if manual:
        for k, v in manual.items():
            if k != "note":
                add(f"- {k}：{v} / 4")
        if manual.get("note"):
            add(f"- 备注：{manual['note']}")
    else:
        add("本次未提供 `--manual`。品牌气质、文案说服力、业务信息架构均未打分。")
    add("")

    add("## 10. 未覆盖项（必读，禁止省略）")
    add("")
    for i, t in enumerate(NOT_COVERED, 1):
        add(f"{i}. {t}")
    add("")

    add("## 11. 复现")
    add("")
    add(f"- 改造前：`{before['input']['path']}` SHA-256 `{before['input']['sha256']}`")
    add(f"- 改造后：`{after['input']['path']}` SHA-256 `{after['input']['sha256']}`")
    add(f"- 审计 JSON：`{before_path}` / `{after_path}`")
    add("")
    add("```bash")
    add(f"python scripts/audit_page.py <before.html> --type {page_type} --json before.json")
    add(f"python scripts/audit_page.py <after.html>  --type {page_type} --json after.json")
    add("python scripts/browser_audit.py <before.html> --json browser_before.json --screenshot shots/before.png")
    add("python scripts/browser_audit.py <after.html>  --json browser_after.json  --screenshot shots/after.png")
    add(f"python scripts/score.py --before before.json --after after.json --type {page_type} \\")
    add("  --browser-before browser_before.json --browser-after browser_after.json \\")
    add("  --visual visual-review.json --independent third_party.json --out evaluation.md")
    add("```")
    add("")
    add("用相同输入与脚本版本重跑，静态合规分应完全一致；浏览器指标会有环境波动。")
    add("")
    add("---")
    add("")
    add("来源与版权：规则蒸馏自 `references/sources.md` S01–S15。NN/g 十大可用性启发式归 "
        "Jakob Nielsen / Nielsen Norman Group 所有，引用时保留署名。本技能不覆盖「所有」"
        "GitHub 项目与「所有」网页，采样边界见 `references/sources.md` §0。")
    return "\n".join(L), b, a


def main():
    ap = argparse.ArgumentParser(description="Three-layer before/after design evaluation")
    ap.add_argument("--before", type=Path, required=True)
    ap.add_argument("--after", type=Path, required=True)
    ap.add_argument("--type", default="landing", choices=list(WEIGHTS))
    ap.add_argument("--manual", type=Path)
    ap.add_argument("--browser-before", type=Path)
    ap.add_argument("--browser-after", type=Path)
    ap.add_argument("--visual", type=Path)
    ap.add_argument("--independent", type=Path)
    ap.add_argument("--independent-name", default="")
    ap.add_argument("--out", type=Path)
    ap.add_argument("--score-json", type=Path)
    args = ap.parse_args()
    before, after = load(args.before), load(args.after)
    bb, ba = load_json(args.browser_before), load_json(args.browser_after)
    visual, independent, manual = load_json(args.visual), load_json(args.independent), load_json(args.manual)
    md, b, a = report(before, after, args.before, args.after, args.type, manual,
                      bb, ba, visual, independent, args.independent_name)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(md, encoding="utf-8")
    if args.score_json:
        args.score_json.parent.mkdir(parents=True, exist_ok=True)
        args.score_json.write_text(json.dumps({"before": b, "after": a,
                                               "browser_gates_after": browser_gates(ba)},
                                              ensure_ascii=False, indent=2), encoding="utf-8")
    if args.out:
        bg = browser_gates(ba)
        print(f"static_compliance {b['total']} -> {a['total']}  gates_after={'PASS' if a['gates_ok'] else 'FAIL'}"
              f"  browser_gates={'PASS' if all(g[1] for g in bg) else 'FAIL'}" if bg else
              f"static_compliance {b['total']} -> {a['total']}  gates_after={'PASS' if a['gates_ok'] else 'FAIL'}")
        print(f"report={args.out}")
    else:
        print(md)
    return 0


if __name__ == "__main__":
    sys.exit(main())
