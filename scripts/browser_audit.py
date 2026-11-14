#!/usr/bin/env python3
"""Real-browser design audit (optional companion to audit_page.py).

Measures what a static source audit cannot: actual LCP / CLS / FCP,
rendered text contrast (including inherited colors and ancestor backgrounds),
horizontal overflow, font loading and keyboard-reachable elements.

Requires: playwright + a Chromium-based browser (Microsoft Edge recommended).
    pip install playwright
    playwright install chromium        # or use system Edge via --channel msedge

IMPORTANT: local file:// measurements are NOT field data. They do not replace
CrUX / RUM 75th-percentile LCP, INP and CLS on real networks and devices.
INP specifically needs real user interactions and is NOT measured here.
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import sys
from pathlib import Path

TOOL_VERSION = "1.0.0"
SCHEMA = "web-design-distiller/browser-audit@1"

INIT_SCRIPT = r"""
window.__wdd = { lcp: 0, cls: 0, fcp: 0, lcpTag: '', lcpText: '' };
try {
  new PerformanceObserver(function (list) {
    for (const e of list.getEntries()) {
      window.__wdd.lcp = e.startTime;
      const t = e.element;
      if (t) {
        window.__wdd.lcpTag = t.tagName.toLowerCase();
        window.__wdd.lcpText = (t.textContent || '').trim().slice(0, 60);
      }
    }
  }).observe({ type: 'largest-contentful-paint', buffered: true });
} catch (e) {}
try {
  new PerformanceObserver(function (list) {
    for (const e of list.getEntries()) {
      if (!e.hadRecentInput) window.__wdd.cls += e.value;
    }
  }).observe({ type: 'layout-shift', buffered: true });
} catch (e) {}
try {
  new PerformanceObserver(function (list) {
    for (const e of list.getEntries()) {
      if (e.name === 'first-contentful-paint') window.__wdd.fcp = e.startTime;
    }
  }).observe({ type: 'paint', buffered: true });
} catch (e) {}
"""

CONTRAST_JS = r"""
() => {
  function parse(s) {
    const m = s.match(/rgba?\(([^)]+)\)/);
    if (!m) return null;
    const p = m[1].split(/[,\s/]+/).filter(Boolean).map(Number);
    if (p.length < 3) return null;
    return [p[0], p[1], p[2], p.length > 3 ? p[3] : 1];
  }
  function lum(c) {
    const f = (v) => { v /= 255; return v <= 0.04045 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); };
    return 0.2126 * f(c[0]) + 0.7152 * f(c[1]) + 0.0722 * f(c[2]);
  }
  function ratio(a, b) {
    const la = lum(a), lb = lum(b);
    return (Math.max(la, lb) + 0.05) / (Math.min(la, lb) + 0.05);
  }
  function effectiveBg(el) {
    let cur = el;
    while (cur && cur !== document.documentElement) {
      const c = parse(getComputedStyle(cur).backgroundColor);
      if (c && c[3] > 0.95) return c;
      cur = cur.parentElement;
    }
    const c = parse(getComputedStyle(document.body).backgroundColor);
    return (c && c[3] > 0.95) ? c : [255, 255, 255, 1];
  }
  const bad = [], checked = [];
  const all = document.querySelectorAll('body *');
  for (const el of all) {
    const own = Array.from(el.childNodes).some(n => n.nodeType === 3 && n.textContent.trim());
    if (!own) continue;
    const cs = getComputedStyle(el);
    if (cs.display === 'none' || cs.visibility === 'hidden' || Number(cs.opacity) === 0) continue;
    const r = el.getBoundingClientRect();
    if (r.width === 0 && r.height === 0) continue;
    const fg = parse(cs.color);
    if (!fg) continue;
    const bg = effectiveBg(el);
    const fs = parseFloat(cs.fontSize) || 16;
    const w = parseInt(cs.fontWeight, 10) || 400;
    const large = fs >= 24 || (fs >= 18.66 && w >= 700);
    const need = large ? 3.0 : 4.5;
    const v = ratio(fg, bg);
    const item = { tag: el.tagName.toLowerCase(), cls: (el.className || '').toString().slice(0, 40),
                   text: el.textContent.trim().slice(0, 40), color: cs.color,
                   background: `rgb(${bg[0]}, ${bg[1]}, ${bg[2]})`,
                   font_px: fs, ratio: Math.round(v * 100) / 100, required: need, pass: v >= need };
    checked.push(item);
    if (!item.pass) bad.push(item);
  }
  return { checked: checked.length, failures: bad.length, bad: bad.slice(0, 15),
           min_ratio: checked.length ? Math.min(...checked.map(x => x.ratio)) : null };
}
"""

LAYOUT_JS = r"""
() => {
  const focusables = document.querySelectorAll(
    'a[href], button:not([disabled]), input:not([disabled]), select, textarea, [tabindex]:not([tabindex="-1"])'
  );
  const imgs = Array.from(document.images).map(i => ({
    src: (i.getAttribute('src') || '').slice(0, 70),
    hasAlt: i.hasAttribute('alt'),
    hasSize: (i.hasAttribute('width') && i.hasAttribute('height')) || !!i.style.aspectRatio,
    complete: i.complete, naturalWidth: i.naturalWidth
  }));
  return {
    viewportWidth: window.innerWidth,
    scrollWidth: document.documentElement.scrollWidth,
    scrollHeight: document.documentElement.scrollHeight,
    horizontalOverflow: document.documentElement.scrollWidth > window.innerWidth + 1,
    focusableCount: focusables.length,
    images: imgs,
    brokenImages: imgs.filter(i => i.complete && i.naturalWidth === 0).length,
    fontStatus: document.fonts ? document.fonts.status : 'unknown',
    h1Count: document.querySelectorAll('h1').length,
    landmarks: ['header','nav','main','footer'].filter(t => document.querySelector(t)).length,
    bodyFont: getComputedStyle(document.body).fontFamily.slice(0, 90)
  };
}
"""


def run(html: Path, channel: str, wait_ms: int, screenshot: Path | None, viewport_w: int):
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        raise SystemExit("playwright is required: pip install playwright")
    raw = html.read_bytes()
    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(channel=channel, headless=True)
            engine = channel
        except Exception:
            browser = p.chromium.launch(headless=True)
            engine = "bundled-chromium"
        ctx = browser.new_context(viewport={"width": viewport_w, "height": 900}, device_scale_factor=1)
        ctx.add_init_script(INIT_SCRIPT)
        page = ctx.new_page()
        page.goto(html.resolve().as_uri(), wait_until="load")
        page.wait_for_timeout(200)
        # Scroll once through the document to fire IntersectionObserver reveals.
        # Without this, a full-page screenshot would capture invisible sections.
        page.evaluate("""async () => {
          const h = document.documentElement.scrollHeight;
          for (let y = 0; y < h; y += 400) {
            window.scrollTo({ top: y, behavior: 'instant' });
            await new Promise(r => setTimeout(r, 70));
          }
          window.scrollTo({ top: 0, behavior: 'instant' });
        }""")
        page.wait_for_timeout(wait_ms)
        perf = page.evaluate("window.__wdd")
        contrast = page.evaluate(CONTRAST_JS)
        layout = page.evaluate(LAYOUT_JS)
        motion = {"reveal_count": 0}
        try:
            vis = page.evaluate(
                "() => Array.from(document.querySelectorAll('.reveal, .lift'))"
                ".map(e => parseFloat(getComputedStyle(e).opacity))")
            motion["reveal_count"] = len(vis)
            motion["normal_min_opacity_after_scroll"] = min(vis) if vis else None
            motion["normal_all_visible"] = (not vis) or all(v >= 0.99 for v in vis)
            ctx2 = browser.new_context(viewport={"width": viewport_w, "height": 900},
                                       reduced_motion="reduce")
            pg2 = ctx2.new_page()
            pg2.goto(html.resolve().as_uri(), wait_until="load")
            pg2.wait_for_timeout(250)
            op = pg2.evaluate(
                "() => Array.from(document.querySelectorAll('.reveal, .lift'))"
                ".map(e => parseFloat(getComputedStyle(e).opacity))")
            motion["reduced_motion_min_opacity"] = min(op) if op else None
            motion["reduced_motion_ok"] = (not op) or all(v >= 0.99 for v in op)
            ctx2.close()
        except Exception as e:
            motion["error"] = str(e)[:120]
        if screenshot:
            screenshot.parent.mkdir(parents=True, exist_ok=True)
            page.screenshot(path=str(screenshot), full_page=True)
        browser.close()

    return {
        "schema": SCHEMA,
        "tool_version": TOOL_VERSION,
        "generated_at": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
        "input": {"path": str(html), "sha256": hashlib.sha256(raw).hexdigest()},
        "engine": engine,
        "viewport_width": viewport_w,
        "settle_ms": wait_ms,
        "performance": {
            "lcp_ms": round(perf.get("lcp", 0), 1),
            "fcp_ms": round(perf.get("fcp", 0), 1),
            "cls": round(perf.get("cls", 0), 4),
            "lcp_element": perf.get("lcpTag", ""),
            "lcp_text": perf.get("lcpText", "")[:60],
            "good_thresholds": {"lcp_ms": 2500, "cls": 0.1, "note": "INP not measurable without real interactions"},
        },
        "rendered_contrast": contrast,
        "layout": layout,
        "motion": motion,
        "notes": [
            "Local file:// measurement, not CrUX/RUM field data; not the 75th percentile across devices.",
            "INP requires real user interactions and is NOT measured here.",
            "Contrast is computed on rendered computed styles; gradients/images behind text still need manual review.",
        ],
    }


def main():
    ap = argparse.ArgumentParser(description="Real-browser design measurement (playwright)")
    ap.add_argument("html", type=Path)
    ap.add_argument("--channel", default="msedge")
    ap.add_argument("--wait", type=int, default=1800)
    ap.add_argument("--width", type=int, default=1440)
    ap.add_argument("--screenshot", type=Path)
    ap.add_argument("--json", type=Path)
    args = ap.parse_args()
    if not args.html.is_file():
        print(f"error: file not found: {args.html}", file=sys.stderr)
        return 2
    r = run(args.html, args.channel, args.wait, args.screenshot, args.width)
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(r, ensure_ascii=False, indent=2), encoding="utf-8")
    p, c, l = r["performance"], r["rendered_contrast"], r["layout"]
    print(f"browser {r['input']['path']}  engine={r['engine']}  sha256={r['input']['sha256'][:12]}")
    print(f"  LCP={p['lcp_ms']}ms  FCP={p['fcp_ms']}ms  CLS={p['cls']}  "
          f"LCP element=<{p['lcp_element']}> {p['lcp_text'][:30]}")
    print(f"  rendered contrast: checked={c['checked']} failures={c['failures']} min_ratio={c['min_ratio']}")
    print(f"  layout: overflow={l['horizontalOverflow']} scrollW={l['scrollWidth']} "
          f"focusable={l['focusableCount']} brokenImages={l['brokenImages']} landmarks={l['landmarks']}")
    m = r["motion"]
    print(f"  motion: reveals={m.get('reveal_count')} allVisibleNormal={m.get('normal_all_visible')} "
          f"reducedMotionOK={m.get('reduced_motion_ok')}"
          + (f" error={m.get('error')}" if m.get("error") else ""))
    if args.json:
        print(f"  JSON -> {args.json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
