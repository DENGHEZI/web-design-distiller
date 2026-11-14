# web-design-distiller

A WorkBuddy / Claude-style **Agent Skill** that turns "good web design" into measurable, reproducible rules.

It distils design philosophy from high-star GitHub projects and authoritative design systems into:

- 8 executable principles,
- a 6-dimension weighted rubric with 5 hard gates,
- two stdlib-only Python scripts that audit HTML/CSS and compute the score,
- a complete worked example: bad page → concrete plan → fixed page → before/after report.

## Honest scope (please read first)

**This skill has NOT read "all" high-star GitHub repositories or "all" web pages.** That is impossible.

On 2026-11-14 the GitHub API reported **543 repositories with >50,000 stars**. Most of them are awesome-lists, tutorials, algorithm collections and AI-agent frameworks with little to say about visual design. This project therefore uses a **declared, reproducible, purposive sample**:

1. Real GitHub star data (`research/*.json`, fetched from the public API with a timestamp),
2. First-party design documentation (shadcn/ui, React, Ant Design, GOV.UK, Apple HIG, Material 3, NN/g, Laws of UX, Tailwind, web.dev, WCAG 2.2),
3. Second-hand observations of product websites, explicitly labelled as second-hand.

The full list of sources, URLs, fetch date, known sampling bias and copyright notes is in [`references/sources.md`](references/sources.md). Every generated report must state this boundary.

**What the scripts cannot do**: measure real LCP/INP/CLS (browser/CrUX field data required), judge aesthetics, evaluate copy, or parse compiled CSS-in-JS. These are listed as non-covered items in every report.

## Install as a skill

```bash
# user scope (available in all projects)
cp -r web-design-distiller ~/.workbuddy/skills/

# or project scope (shared with the repo)
cp -r web-design-distiller <your-project>/.workbuddy/skills/
```

The skill triggers on: design review, UI audit, "score this page", "generate a redesign plan", "评估这个页面", "设计评分", "UI 审计", "生成设计方案".

## Quick start

```bash
python scripts/audit_page.py path/to/page.html --json before.json
# ... apply the plan from assets/report-template.md ...
python scripts/audit_page.py path/to/fixed.html --json after.json
python scripts/browser_audit.py path/to/page.html  --json browser_before.json --screenshot shots/before.png
python scripts/browser_audit.py path/to/fixed.html --json browser_after.json  --screenshot shots/after.png
python scripts/score.py --before before.json --after after.json --type landing \
  --browser-before browser_before.json --browser-after browser_after.json \
  --visual reports/visual-review.json --out evaluation.md
```

`browser_audit.py` needs `pip install playwright` and a Chromium browser (system Edge works via `--channel msedge`). It is optional but **required** for the three-layer report.

Extra stylesheets: `--css site.css`. Page types: `landing | app | docs | commerce` (they change the weights).

## Worked example (verified, not hypothetical)

| Layer | Metric | before | after |
| --- | --- | --- | --- |
| ① Static compliance | score 0–100 | 16.4 | 100.0 |
| ① Static compliance | failed checks | 23 | 0 |
| ② Real browser | rendered contrast failures | 12 | 0 |
| ② Real browser | broken images | 4 | 0 |
| ② Real browser | CLS / LCP (local, single run) | 0 / 536ms | 0 / 608ms |
| ③ Visual review | subjective 0–10, **not merged** | 2.0 | 8.8 |

> **Anti-self-certification (v2)**: the first-round page with obvious template feel and the
> visually redesigned second-round page **both score 100.0** on this rubric, while blind
> visual review gives **5.0/10 vs 8.0/10**. Static compliance has **zero discriminatory
> power** for visual quality. Never present a score increase as proof the design got better.

> **v3 motion**: 19 scroll-reveal elements, staggered hero entrance, count-up metric,
> scroll progress bar and restrained hover micro-interactions. LCP-critical elements
> animate with `transform` only (no opacity fade), so LCP is not delayed; CLS stays 0;
> `prefers-reduced-motion` forces every element visible (verified by `browser_audit.py`).

> **v4 identity**: a prism geometry brand language (triangle mark + hairline refraction rays
> echoed in header and footer), one real editorial photograph (30KB WebP, generated and
> watermark-cleaned) with a large-quote customer story. Visual review 8.0 → 8.8 while the
> compliance score stays 100.0 — a fourth demonstration that the two layers are unrelated.

> **Measurement fixes**: `audit_page.py` no longer double-counts inline CSS in `bytes_total`;
> `browser_audit.py` uses N fresh browser contexts and reports the first cold load plus the
> full sample range (cached reloads used to fabricate a fake LCP gain).

Reproduce it:

```bash
python scripts/audit_page.py examples/before.html --json /tmp/before.json
python scripts/audit_page.py examples/after.html  --json /tmp/after.json
python scripts/score.py --before /tmp/before.json --after /tmp/after.json \
  --type landing --out /tmp/evaluation.md
```

Files: [`examples/design-plan.md`](examples/design-plan.md) (the concrete plan), [`examples/evaluation-report.md`](examples/evaluation-report.md) (generated report), [`examples/before.html`](examples/before.html), [`examples/after.html`](examples/after.html).

> A score of 100 only means "passes every static check in this rubric". It does **not** mean the page is optimal in the real world. The demo page was built against this rubric, so a perfect score is expected.

## How scoring works

| Dimension | Weight (landing) |
| --- | --- |
| Clarity & hierarchy | 20 |
| Constrained systems | 20 |
| Restraint & density | 15 |
| Accessibility | 20 |
| Performance & stability | 15 |
| Convention & states | 10 |

Each check is `pass / warn / fail` → `1.0 / 0.5 / 0.0`. Dimension score = mean × 4. Total = Σ(dimension/4 × weight).

**Hard gates override the score**: contrast (WCAG 1.4.3/1.4.11), image `alt`, visible keyboard focus, ≤1 primary CTA, `lang` + viewport. Any failure ⇒ overall `FAIL`, regardless of the total. Details: [`references/rubric.md`](references/rubric.md).

## Repository layout

```
SKILL.md                     skill entry point (P0–P5 workflow)
references/sources.md        sampling method, sources, bias, copyright
references/principles.md     8 distilled principles + conflict arbitration
references/rubric.md         scoring anchors, weights, hard gates
scripts/audit_page.py        static HTML/CSS audit → JSON evidence
scripts/browser_audit.py     Playwright + Edge real rendering measurement (optional dep)
scripts/score.py             three-layer before/after report
examples/after-v1.html       round-1 counter-example: 100/100 compliance, weak visuals
examples/third-party.html    independent sample (not built to this rubric)
reports/                     audit JSON, screenshots, visual review
research/                    raw GitHub API snapshots (reproducibility)
```

## Sources and license

Principles are summarised with links only; no third-party documentation is reproduced verbatim. NN/g's 10 usability heuristics are credited to Jakob Nielsen / Nielsen Norman Group as required by their page. Apple HIG, Material Design, GOV.UK, shadcn/ui, Ant Design, Tailwind CSS, web.dev and W3C documents remain the property of their respective owners.

Original code and original text in this repository: **MIT** (see [`LICENSE`](LICENSE)). Third-party specs, brand names and fonts are not covered by this license.

## Contributing

Improvements should keep three invariants: every conclusion must have evidence, every score must come from `score.py`, and every report must list what was **not** measured. If you add a check id, update `references/rubric.md` and `DIMENSION_CHECKS` in `score.py` together.
