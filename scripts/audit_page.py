#!/usr/bin/env python3
"""Static, deterministic web-page design audit (stdlib only).

Part of the web-design-distiller skill.
Reads an HTML file (plus optional CSS files) and emits JSON evidence for
every check id referenced in references/rubric.md.

IMPORTANT: This is a SOURCE audit, not a browser measurement.
Real LCP / INP / CLS must be measured with Lighthouse or CrUX field data.
"""
from __future__ import annotations

import argparse
import colorsys
import datetime
import hashlib
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

TOOL_VERSION = "1.0.0"
SCHEMA = "web-design-distiller/audit@1"

SPACING_SCALE = {0, 1, 2, 3, 4, 8, 12, 16, 24, 32, 48, 64, 96}
TYPE_SCALE = {12, 14, 16, 18, 20, 24, 30, 36, 48, 60, 72}
SPACING_PROPS = {
    "padding", "padding-top", "padding-right", "padding-bottom", "padding-left",
    "margin", "margin-top", "margin-right", "margin-bottom", "margin-left",
    "gap", "row-gap", "column-gap", "top", "right", "bottom", "left",
}
NAMED_COLORS = {
    "white": (255, 255, 255), "black": (0, 0, 0), "red": (255, 0, 0),
    "green": (0, 128, 0), "blue": (0, 0, 255), "gray": (128, 128, 128),
    "grey": (128, 128, 128), "transparent": None, "currentcolor": None,
    "none": None, "inherit": None, "initial": None,
}
RULE_RE = re.compile(r"([^{}]+)\{([^{}]*)\}", re.S)
VAR_DEF_RE = re.compile(r"(--[\w-]+)\s*:\s*([^;]+)")
VAR_USE_RE = re.compile(r"var\(\s*(--[\w-]+)\s*(?:,\s*([^)]*))?\)")
HEX_RE = re.compile(r"#([0-9a-fA-F]{3,8})\b")
PX_RE = re.compile(r"(?<![\w.-])(\d+(?:\.\d+)?)px\b")
FONT_SIZE_RE = re.compile(r"font-size\s*:\s*([^;]+)")


# ---------------------------------------------------------------- HTML parsing
class DocParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.tags = []            # (tag, attrs, line)
        self.style_blocks = []    # (css_text, start_line)
        self.text_parts = []
        self._in_style = False
        self._style_buf = []
        self._style_line = 0
        self._in_title = False
        self.title = ""
        self._nav_depth = 0
        self.nav_links = 0

    def handle_starttag(self, tag, attrs):
        a = {k.lower(): (v or "") for k, v in attrs}
        line = self.getpos()[0]
        self.tags.append((tag.lower(), a, line))
        if tag.lower() == "style":
            self._in_style = True
            self._style_buf = []
            self._style_line = line
        if tag.lower() == "title":
            self._in_title = True
        if tag.lower() == "nav":
            self._nav_depth += 1
        if tag.lower() == "a" and self._nav_depth > 0:
            self.nav_links += 1

    def handle_endtag(self, tag):
        t = tag.lower()
        if t == "style" and self._in_style:
            self.style_blocks.append(("".join(self._style_buf), self._style_line))
            self._in_style = False
        if t == "title":
            self._in_title = False
        if t == "nav" and self._nav_depth > 0:
            self._nav_depth -= 1

    def handle_data(self, data):
        if self._in_style:
            self._style_buf.append(data)
        else:
            self.text_parts.append(data)
            if self._in_title:
                self.title += data


# ---------------------------------------------------------------- CSS utilities
def strip_comments(css: str) -> str:
    return re.sub(r"/\*.*?\*/", "", css, flags=re.S)


def parse_rules(css: str, source: str):
    """Return list of dicts: selector, decls, vars, line, source."""
    css = strip_comments(css)
    out = []
    for m in RULE_RE.finditer(css):
        selector = m.group(1).strip()
        body = m.group(2)
        if selector.startswith("@"):
            continue
        decls = {}
        variables = {}
        for raw in body.split(";"):
            if ":" not in raw:
                continue
            prop, val = raw.split(":", 1)
            prop, val = prop.strip().lower(), val.strip()
            if not prop:
                continue
            decls[prop] = val
            if prop.startswith("--"):
                variables[prop] = val
        line = css[: m.start()].count("\n") + 1
        out.append({"selector": selector, "decls": decls, "vars": variables,
                    "line": line, "source": source})
    return out


def collect_vars(rules):
    v = {}
    for r in rules:
        for k, val in r["vars"].items():
            if re.match(r"^#|^rgb|^hsl|^[a-z]+$", val.strip(), re.I):
                v[k] = val.strip()
    return v


def parse_color(value: str, var_map: dict, depth: int = 0):
    """Resolve a CSS color to an (r,g,b) tuple. Returns None if not resolvable."""
    if depth > 5 or not value:
        return None
    v = value.strip().lower()
    m = VAR_USE_RE.search(v)
    if m:
        replacement = var_map.get(m.group(1), m.group(2) or "")
        v = VAR_USE_RE.sub(replacement, v, count=1).strip()
        return parse_color(v, var_map, depth + 1)
    if v in NAMED_COLORS:
        return NAMED_COLORS[v]
    hm = HEX_RE.search(v)
    if hm:
        h = hm.group(1)
        if len(h) in (3, 4):
            h = "".join(c * 2 for c in h[:3])
        if len(h) >= 6:
            return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
    nums = re.findall(r"-?\d+(?:\.\d+)?", v)
    if v.startswith("rgb") and len(nums) >= 3:
        return tuple(max(0, min(255, int(float(n)))) for n in nums[:3])
    if v.startswith("hsl") and len(nums) >= 3:
        h, s, l = float(nums[0]) / 360.0, float(nums[1]) / 100.0, float(nums[2]) / 100.0
        rr, gg, bb = colorsys.hls_to_rgb(h, l, s)
        return (round(rr * 255), round(gg * 255), round(bb * 255))
    return None


def luminance(rgb):
    def f(c):
        c /= 255.0
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = rgb
    return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b)


def contrast_ratio(a, b):
    la, lb = luminance(a), luminance(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def font_px(value: str, var_map: dict) -> float | None:
    v = value.strip().lower()
    m = VAR_USE_RE.search(v)
    if m:
        v = VAR_USE_RE.sub(var_map.get(m.group(1), m.group(2) or ""), v, count=1).strip()
    m = re.match(r"^(\d+(?:\.\d+)?)\s*(px|rem|em|pt)$", v)
    if not m:
        return None
    n, unit = float(m.group(1)), m.group(2)
    return n * {"px": 1, "rem": 16, "em": 16, "pt": 1.333}[unit]


def grade(status_pass, status_warn="warn"):
    return status_pass


def make_check(status, value, evidence, note=""):
    c = {"status": status, "value": value, "evidence": evidence}
    if note:
        c["note"] = note
    return c


def verdict(n_fail, n_warn=0, pass_at=0, warn_at=1, hard_fail_at=1):
    if n_fail >= hard_fail_at:
        return "fail"
    if n_fail or n_warn >= warn_at:
        return "warn"
    return "pass"


# ---------------------------------------------------------------- main audit
def audit(html_path: Path, css_paths, page_type: str):
    raw = html_path.read_bytes()
    html_text = raw.decode("utf-8", errors="replace")
    parser = DocParser()
    parser.feed(html_text)

    css_sources = []
    for i, (block, start_line) in enumerate(parser.style_blocks):
        css_sources.append({"name": f"{html_path.name}#style[{i}]", "text": block,
                            "offset": start_line - 1})
    for p in css_paths:
        css_sources.append({"name": p.name, "text": p.read_text(encoding="utf-8", errors="replace"),
                            "offset": 0})
    all_css = "\n".join(c["text"] for c in css_sources)
    rules = parse_rules(all_css, "combined")
    var_map = collect_vars(rules)

    checks = {}
    notes = []

    def ev(line, source="html"):
        return f"{source}:{line}"

    # --- document basics
    html_tag = next((a for t, a, _ in parser.tags if t == "html"), {})
    checks["lang_attr"] = make_check(
        "pass" if html_tag.get("lang") else "fail",
        html_tag.get("lang", ""),
        ev(next((l for t, _, l in parser.tags if t == "html"), 1)),
    )
    has_viewport = any(t == "meta" and a.get("name", "").lower() == "viewport"
                       for t, a, _ in parser.tags)
    checks["meta_viewport"] = make_check("pass" if has_viewport else "fail", has_viewport,
                                         "meta[name=viewport]")
    checks["title_present"] = make_check(
        "pass" if parser.title.strip() else "fail", parser.title.strip()[:60], "<title>")

    h1_count = sum(1 for t, _, _ in parser.tags if t == "h1")
    checks["h1_count"] = make_check("pass" if h1_count == 1 else "fail", h1_count,
                                    "count(<h1>)")

    # --- CTA / navigation
    cta_tags = [(t, a, l) for t, a, l in parser.tags
                if t in ("a", "button")
                and re.search(r"primary|\bcta\b|hero-btn", (a.get("class", "") + " " + a.get("id", "")), re.I)]
    checks["cta_count"] = make_check("pass" if len(cta_tags) <= 1 else "fail", len(cta_tags),
                                     ", ".join(ev(l) for _, _, l in cta_tags) or "none")
    checks["nav_items"] = make_check(
        "pass" if parser.nav_links <= 5 else ("warn" if parser.nav_links <= 7 else "fail"),
        parser.nav_links, "count(<nav> a)")

    # --- images
    imgs = [(a, l) for t, a, l in parser.tags if t == "img"]
    missing_alt = [l for a, l in imgs if "alt" not in a]
    checks["img_alt_missing"] = make_check("pass" if not missing_alt else "fail",
                                           len(missing_alt),
                                           ", ".join(ev(l) for l in missing_alt) or "none")
    has_aspect = bool(re.search(r"aspect-ratio\s*:", all_css))
    unsized = [l for a, l in imgs if not (a.get("width") and a.get("height"))]
    if has_aspect:
        unsized = []
    checks["img_unsized"] = make_check(
        "pass" if not unsized else ("warn" if len(unsized) == 1 else "fail"),
        len(unsized), ", ".join(ev(l) for l in unsized) or "none")

    # --- focus / outline
    has_fv = bool(re.search(r":focus-visible", all_css))
    checks["focus_visible_defined"] = make_check("pass" if has_fv else "fail", has_fv,
                                                 ":focus-visible in CSS")
    outline_bad = []
    for r in rules:
        d = r["decls"]
        ov = d.get("outline", "") + " " + d.get("outline-style", "")
        if re.search(r"\bnone\b|\b0(px)?\b", ov, re.I) and "outline" in d:
            compensated = any(k in d for k in ("box-shadow", "border", "background", "background-color"))
            if not compensated:
                outline_bad.append(f"{r['source']}:{r['line']} {r['selector']}")
    checks["outline_none_uncompensated"] = make_check(
        "pass" if not outline_bad else "fail", len(outline_bad), "; ".join(outline_bad) or "none")

    # --- background baseline + contrast
    bg = (255, 255, 255)
    bg_note = ""
    for r in rules:
        if re.search(r"(^|[\s,])body\b|:root", r["selector"]):
            val = r["decls"].get("background-color") or r["decls"].get("background")
            if val:
                if "gradient" in val:
                    bg_note = "body background is a gradient; contrast needs manual review"
                    continue
                c = parse_color(val, var_map)
                if c:
                    bg = c
                    break
    gradient_in_bg = any("gradient" in (r["decls"].get("background", "") + r["decls"].get("background-color", ""))
                         for r in rules)
    if gradient_in_bg:
        bg_note = bg_note or "gradient backgrounds present; contrast against them needs manual review"
        notes.append(bg_note)

    contrast_rows = []
    for r in rules:
        d = r["decls"]
        val = d.get("color")
        if not val or "gradient" in val:
            continue
        fg = parse_color(val, var_map)
        if not fg:
            continue
        # Use the rule's own background when declared (white text on a dark CTA),
        # otherwise fall back to the page body background.
        local_bg = bg
        for key in ("background-color", "background"):
            bval = d.get(key)
            if not bval or "gradient" in bval:
                continue
            bc = parse_color(bval, var_map)
            if bc:
                local_bg = bc
                break
        fs = font_px(d.get("font-size", ""), var_map) if d.get("font-size") else 16.0
        bold = bool(re.search(r"\b(600|700|800|900|bold)\b", d.get("font-weight", "")))
        large = (fs or 16) >= 24 or ((fs or 16) >= 18.66 and bold)
        required = 3.0 if large else 4.5
        ratio = contrast_ratio(fg, local_bg)
        contrast_rows.append({
            "line": r["line"], "selector": r["selector"], "color": val,
            "background": "rgb%s" % (local_bg,), "font_px": fs,
            "ratio": round(ratio, 2), "required": required,
            "pass": ratio >= required,
        })
    bad_contrast = [x for x in contrast_rows if not x["pass"]]
    min_ratio = min((x["ratio"] for x in contrast_rows), default=None)
    checks["contrast_failures"] = make_check(
        "pass" if not bad_contrast else "fail", len(bad_contrast),
        "; ".join(f"L{x['line']} {x['selector']} {x['color']} {x['ratio']}:1 < {x['required']}:1"
                  for x in bad_contrast) or "none",
        bg_note)
    checks["contrast_min_ratio"] = make_check(
        "pass" if (min_ratio is None or min_ratio >= 4.5) else ("warn" if min_ratio >= 3 else "fail"),
        round(min_ratio, 2) if min_ratio is not None else None,
        f"min over {len(contrast_rows)} text-color declarations "
        f"(per-rule background when declared; fallback bg=rgb{bg})")

    # --- constrained scales
    spacing_bad, spacing_total = [], 0
    for r in rules:
        for prop, val in r["decls"].items():
            if prop not in SPACING_PROPS:
                continue
            for px in PX_RE.findall(val):
                spacing_total += 1
                n = float(px)
                if n not in SPACING_SCALE:
                    spacing_bad.append(f"L{r['line']} {prop}:{px}px")
    checks["spacing_violations"] = make_check(
        "pass" if not spacing_bad else ("warn" if len(spacing_bad) <= 2 else "fail"),
        len(spacing_bad), "; ".join(spacing_bad[:8]) or "none",
        f"{spacing_total} px spacing values inspected")

    type_bad, type_total, px_fonts, rem_fonts = [], 0, 0, 0
    h1_size = body_size = None
    for r in rules:
        val = r["decls"].get("font-size")
        if not val:
            continue
        type_total += 1
        if re.search(r"\bpx\b", val):
            px_fonts += 1
        if re.search(r"\b(rem|em)\b", val) or "var(" in val:
            rem_fonts += 1
        fs = font_px(val, var_map)
        if fs:
            if re.search(r"(^|[\s,.])h1\b", r["selector"]):
                h1_size = fs
            if re.search(r"(^|[\s,.])body\b|(^|[\s,.])p\b", r["selector"]):
                body_size = body_size or fs
            if fs not in TYPE_SCALE:
                type_bad.append(f"L{r['line']} {r['selector']} {val}({fs:g}px)")
    checks["type_scale_violations"] = make_check(
        "pass" if not type_bad else ("warn" if len(type_bad) <= 2 else "fail"),
        len(type_bad), "; ".join(type_bad[:8]) or "none",
        f"{type_total} font-size declarations inspected")

    ratio_hb = (h1_size / body_size) if (h1_size and body_size) else None
    checks["heading_size_ratio"] = make_check(
        "pass" if (ratio_hb and ratio_hb >= 1.5) else ("warn" if ratio_hb else "warn"),
        round(ratio_hb, 2) if ratio_hb else None,
        f"h1={h1_size}px body={body_size}px",
        "not detectable from CSS" if not ratio_hb else "")

    px_share = px_fonts / type_total if type_total else 0
    checks["absolute_font_units"] = make_check(
        "pass" if px_share < 0.4 else ("warn" if px_share < 0.8 else "fail"),
        round(px_share, 2), f"{px_fonts}px / {type_total} font-size declarations")

    all_colors = set()
    for c in css_sources:
        for h in HEX_RE.findall(strip_comments(c["text"])):
            all_colors.add("#" + h.lower())
        for rgb in re.findall(r"rgba?\([^)]*\)", c["text"]):
            all_colors.add(re.sub(r"\s+", "", rgb))
    checks["unique_colors"] = make_check(
        "pass" if len(all_colors) <= 12 else ("warn" if len(all_colors) <= 20 else "fail"),
        len(all_colors), ", ".join(sorted(all_colors)[:14]))

    grads = len(re.findall(r"(linear|radial|conic)-gradient\s*\(", all_css))
    checks["gradient_count"] = make_check(
        "pass" if grads <= 1 else ("warn" if grads == 2 else "fail"), grads,
        "count(*-gradient() in CSS)")

    inline_styles = [(t, l) for t, a, l in parser.tags if "style" in a]
    checks["inline_style_count"] = make_check(
        "pass" if not inline_styles else ("warn" if len(inline_styles) <= 2 else "fail"),
        len(inline_styles), ", ".join(ev(l) for _, l in inline_styles) or "none")

    checks["max_width_defined"] = make_check(
        "pass" if re.search(r"max-(width|inline-size)\s*:", all_css) else "fail",
        bool(re.search(r"max-(width|inline-size)\s*:", all_css)), "max-width in CSS")
    checks["whitespace_token"] = make_check(
        "pass" if re.search(r"--space|--spacing", all_css) else "fail",
        bool(re.search(r"--space|--spacing", all_css)), "--space* token definitions")

    # --- performance proxies
    externals = []
    for t, a, l in parser.tags:
        if t in ("link", "script", "img") and (a.get("href") or a.get("src")):
            u = a.get("href") or a.get("src")
            if not u.startswith("data:"):
                externals.append(ev(l))
    checks["external_resources"] = make_check(
        "pass" if len(externals) <= 3 else ("warn" if len(externals) <= 6 else "fail"),
        len(externals), ", ".join(externals[:8]) or "none")
    imports = len(re.findall(r"@import", all_css)) + sum(
        1 for t, a, _ in parser.tags if t == "link" and "stylesheet" in a.get("rel", ""))
    checks["css_imports"] = make_check(
        "pass" if imports == 0 else ("warn" if imports == 1 else "fail"), imports,
        "@import + <link rel=stylesheet>")
    total_bytes = len(raw) + sum(len(c["text"].encode("utf-8")) for c in css_sources)
    checks["bytes_total"] = make_check(
        "pass" if total_bytes <= 40000 else ("warn" if total_bytes <= 120000 else "fail"),
        total_bytes, "html + provided css bytes")

    # --- semantics / states / a11y preferences
    present = {t for t, _, _ in parser.tags} & {"main", "nav", "header", "footer"}
    checks["semantic_tags"] = make_check(
        "pass" if len(present) >= 3 else ("warn" if len(present) == 2 else "fail"),
        sorted(present), "landmark elements present")
    checks["reduced_motion"] = make_check(
        "pass" if "prefers-reduced-motion" in all_css else "fail",
        "prefers-reduced-motion" in all_css, "@media (prefers-reduced-motion)")

    states = {s: (f":{s}" in all_css) for s in ("hover", "focus", "active", "disabled")}
    n_states = sum(states.values())
    checks["interaction_states"] = make_check(
        "pass" if n_states >= 4 else ("warn" if n_states >= 2 else "fail"),
        states, ", ".join(k for k, v in states.items() if v) or "none")

    blob = (" ".join(parser.text_parts) + " " + " ".join(a.get("class", "") for _, a, _ in parser.tags)).lower()
    fb = [k for k in ("loading", "skeleton", "error", "retry", "empty", "加载", "错误", "空状态", "重试")
          if k in blob]
    checks["status_feedback"] = make_check(
        "pass" if len(fb) >= 2 else ("warn" if len(fb) == 1 else "fail"),
        fb, "loading / error / empty state signals in markup")

    # --- notes (explicit non-coverage)
    notes += [
        "Real LCP/INP/CLS are NOT measured here; only static risk proxies.",
        "Contrast is computed against a single body background; gradients/images/alpha need manual review.",
        "Compiled CSS-in-JS and stylesheets not passed via --css are out of scope.",
        "Aesthetic judgement, copy quality and conversion are human-only items.",
    ]

    return {
        "schema": SCHEMA,
        "tool_version": TOOL_VERSION,
        "generated_at": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
        "input": {"path": str(html_path), "sha256": hashlib.sha256(raw).hexdigest(),
                  "bytes": len(raw)},
        "css_sources": [c["name"] for c in css_sources],
        "page_type": page_type,
        "background_rgb": list(bg),
        "checks": checks,
        "contrast_details": contrast_rows,
        "metrics": {"rules": len(rules), "imgs": len(imgs), "tags": len(parser.tags),
                    "spacing_values": spacing_total, "font_size_values": type_total,
                    "css_bytes": sum(len(c["text"].encode("utf-8")) for c in css_sources)},
        "notes": notes,
    }


def main():
    ap = argparse.ArgumentParser(description="Static web design audit (stdlib only)")
    ap.add_argument("html", type=Path)
    ap.add_argument("--css", type=Path, nargs="*", default=[])
    ap.add_argument("--type", default="landing",
                    choices=["landing", "app", "docs", "commerce"])
    ap.add_argument("--json", type=Path, help="write full JSON evidence here")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()
    if not args.html.is_file():
        print(f"error: file not found: {args.html}", file=sys.stderr)
        return 2
    result = audit(args.html, args.css, args.type)
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    if not args.quiet:
        fails = {k: v for k, v in result["checks"].items() if v["status"] == "fail"}
        warns = {k: v for k, v in result["checks"].items() if v["status"] == "warn"}
        print(f"audit {result['input']['path']}  sha256={result['input']['sha256'][:12]}  "
              f"checks={len(result['checks'])} fail={len(fails)} warn={len(warns)}")
        for k, v in sorted(fails.items()):
            print(f"  FAIL  {k:<30} value={v['value']}  {v['evidence'][:110]}")
        for k, v in sorted(warns.items()):
            print(f"  WARN  {k:<30} value={v['value']}  {v['evidence'][:110]}")
        if args.json:
            print(f"  JSON -> {args.json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
