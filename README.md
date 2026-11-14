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
python scripts/score.py --before before.json --after after.json --type landing --out evaluation.md
```

Extra stylesheets: `--css site.css`. Page types: `landing | app | docs | commerce` (they change the weights).

## Worked example (verified, not hypothetical)

| | before | after |
| --- | --- | --- |
| Objective score | 16.4 | 100.0 |
| Grade | FAIL (5 hard gates failed) | A |
| Failed checks | 23 | 0 |

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
scripts/score.py             before/after score → Markdown report
assets/tokens.css            light, restrained design tokens
assets/report-template.md    plan + report template
examples/                    complete worked example
research/                    raw GitHub API snapshots (reproducibility)
reports/                     generated audit JSON for the example
```

## Sources and license

Principles are summarised with links only; no third-party documentation is reproduced verbatim. NN/g's 10 usability heuristics are credited to Jakob Nielsen / Nielsen Norman Group as required by their page. Apple HIG, Material Design, GOV.UK, shadcn/ui, Ant Design, Tailwind CSS, web.dev and W3C documents remain the property of their respective owners.

Original code and original text in this repository: **MIT** (see [`LICENSE`](LICENSE)). Third-party specs, brand names and fonts are not covered by this license.

## Contributing

Improvements should keep three invariants: every conclusion must have evidence, every score must come from `score.py`, and every report must list what was **not** measured. If you add a check id, update `references/rubric.md` and `DIMENSION_CHECKS` in `score.py` together.
