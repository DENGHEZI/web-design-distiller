# 网页设计改造效果评估报告

- 生成时间：2026-11-14T09:31:18+08:00
- 页面类型：`landing`（权重见下表，评估前已固定）
- 评分工具：`score.py v1.0.0` + `audit_page.py v1.0.0`
- 依据：`references/rubric.md` v1.0、`references/principles.md` P1–P8、`references/sources.md` S01–S15

> 本报告的所有分数均由脚本从审计 JSON 计算，不含人工估算。客观项与主观项分区呈现；未测项在文末显式列出。

## 1. 结论

| 指标 | 改造前 | 改造后 | 变化 |
| --- | --- | --- | --- |
| 客观总分 | 16.4 | 100.0 | +83.6 |
| 等级 | FAIL | A | — |
| 硬门槛 | 存在失败 | 全部通过 | — |
| fail 检查项 | 23 | 0 | -23 |

**整体判定：A 级，硬门槛全部通过。**

> **满分含义**：100 分只表示「通过本 rubric 的全部静态检查项」，不代表真实用户体验最优，也不覆盖第 7 节列出的未测项。评分表本身是目的性抽样的产物，边界见 `references/sources.md` §0。

## 2. 硬门槛前后对照

| 门槛 | 改造前 | 改造后 | 证据 / 备注 |
| --- | --- | --- | --- |
| G1 对比度达标 (WCAG 1.4.3/1.4.11) | FAIL | PASS | min over 16 text-color declarations (per-rule background when declared; fallback bg=rgb(255, 255, 255)) |
| G2 图片 alt 完整 | FAIL | PASS | none |
| G3 键盘焦点可见且未被抹除 | FAIL | PASS | focus-visible=pass, outline-none=pass |
| G4 主 CTA 不超过一个 | FAIL | PASS | html:171 |
| G5 lang 与 viewport 齐备 | FAIL | PASS | lang=pass, viewport=pass |

## 3. 六维度得分（原始分 0–4，加权后计入总分）

| 维度 | 权重 | 改造前 | 改造后 | Δ |
| --- | --- | --- | --- | --- |
| 目标与层级 (`clarity`) | 20 | 1.0（加权 5.0） | 4.0（加权 20.0） | +3 |
| 系统性约束 (`system`) | 20 | 0.5（加权 2.5） | 4.0（加权 20.0） | +3.5 |
| 克制与密度 (`restraint`) | 15 | 0.5（加权 1.88） | 4.0（加权 15.0） | +3.5 |
| 可访问性 (`a11y`) | 20 | 0.8（加权 4.0） | 4.0（加权 20.0） | +3.2 |
| 性能与稳定性 (`perf`) | 15 | 0.8（加权 3.0） | 4.0（加权 15.0） | +3.2 |
| 惯例与状态 (`convention`) | 10 | 0.0（加权 0.0） | 4.0（加权 10.0） | +4 |

> 部分检查项按 rubric 同时归属两个维度（`unique_colors`、`reduced_motion`），属设计而非重复计分。

## 4. 逐项改造验证（fail → pass）

| 检查 id | 前 | 后 | 前值 | 后值 |
| --- | --- | --- | --- | --- |
| `contrast_failures` | fail | pass | 8 | 0 |
| `contrast_min_ratio` | fail | pass | 1.0 | 4.89 |
| `css_imports` | fail | pass | 3 | 0 |
| `cta_count` | fail | pass | 3 | 1 |
| `external_resources` | fail | pass | 7 | 0 |
| `focus_visible_defined` | fail | pass | False | True |
| `gradient_count` | fail | pass | 3 | 0 |
| `h1_count` | fail | pass | 2 | 1 |
| `img_alt_missing` | fail | pass | 4 | 0 |
| `img_unsized` | fail | pass | 4 | 0 |
| `inline_style_count` | fail | pass | 4 | 0 |
| `interaction_states` | fail | pass | {"hover": true, "focus": false, "active": false, "disabled": false} | {"hover": true, "focus": true, "active": true, "disabled": true} |
| `lang_attr` | fail | pass |  | zh-CN |
| `max_width_defined` | fail | pass | False | True |
| `meta_viewport` | fail | pass | False | True |
| `nav_items` | fail | pass | 8 | 4 |
| `outline_none_uncompensated` | fail | pass | 1 | 0 |
| `reduced_motion` | fail | pass | False | True |
| `semantic_tags` | fail | pass | ["nav"] | ["footer", "header", "main", "nav"] |
| `spacing_violations` | fail | pass | 13 | 0 |
| `status_feedback` | fail | pass | [] | ["error", "加载", "错误", "空状态", "重试"] |
| `type_scale_violations` | fail | pass | 7 | 0 |
| `unique_colors` | warn | pass | 14 | 12 |
| `whitespace_token` | fail | pass | False | True |

## 5. 客观项明细（改造后）

| 检查 id | 状态 | 值 | 证据 |
| --- | --- | --- | --- |
| `absolute_font_units` | pass | 0.0 | 0px / 19 font-size declarations |
| `bytes_total` | pass | 16346 | html + provided css bytes |
| `contrast_failures` | pass | 0 | none |
| `contrast_min_ratio` | pass | 4.89 | min over 16 text-color declarations (per-rule background when declared; fallback bg=rgb(255, 255, 255)) |
| `css_imports` | pass | 0 | @import + <link rel=stylesheet> |
| `cta_count` | pass | 1 | html:171 |
| `external_resources` | pass | 0 | none |
| `focus_visible_defined` | pass | True | :focus-visible in CSS |
| `gradient_count` | pass | 0 | count(*-gradient() in CSS) |
| `h1_count` | pass | 1 | count(<h1>) |
| `heading_size_ratio` | pass | 1.88 | h1=30.0px body=16.0px |
| `img_alt_missing` | pass | 0 | none |
| `img_unsized` | pass | 0 | none |
| `inline_style_count` | pass | 0 | none |
| `interaction_states` | pass | {"hover": true, "focus": true, "active": true, "disabled": true} | hover, focus, active, disabled |
| `lang_attr` | pass | zh-CN | html:5 |
| `max_width_defined` | pass | True | max-width in CSS |
| `meta_viewport` | pass | True | meta[name=viewport] |
| `nav_items` | pass | 4 | count(<nav> a) |
| `outline_none_uncompensated` | pass | 0 | none |
| `reduced_motion` | pass | True | @media (prefers-reduced-motion) |
| `semantic_tags` | pass | ["footer", "header", "main", "nav"] | landmark elements present |
| `spacing_violations` | pass | 0 | none |
| `status_feedback` | pass | ["error", "加载", "错误", "空状态", "重试"] | loading / error / empty state signals in markup |
| `title_present` | pass | 棱镜文档 PrismDocs — 让团队知识有条理 | <title> |
| `type_scale_violations` | pass | 0 | none |
| `unique_colors` | pass | 12 | #096b60, #0b7f72, #0fa693, #1c1c1e, #5f5f66, #767680, #8a6418, #e5e5ea, #fafafa, #ffffff, rgba(28,28,30,0.05), rgba(28,28,30,0.08) |
| `whitespace_token` | pass | True | --space* token definitions |

## 6. 主观分区（不并入总分）

本次未提供人工评分（`--manual`）。品牌气质、文案说服力、业务信息架构均未打分，**不得**把客观总分表述为「综合设计评分」。

## 7. 未覆盖项（必读，禁止省略）

1. 真实 LCP / INP / CLS 未实测（脚本只测 img 尺寸、外部资源数、体积等风险代理指标）；需 Lighthouse / CrUX 现场数据，按 75 分位、分移动端与桌面端评估。
2. 跨浏览器与真机渲染、字体加载过程、弱网抖动。
3. 动态交互后的可访问性（弹窗焦点陷阱、路由切换后的焦点管理）。
4. 打包后的 CSS-in-JS / 编译产物样式（仅解析 HTML 内联 <style> 与 --css 传入的文件）。
5. 渐变、图片、半透明背景上的实际文字对比度（脚本按单一 body 背景近似计算）。
6. 内容真实性、文案说服力与转化效果（主观项，不并入总分）。

- 审计脚本注释：Real LCP/INP/CLS are NOT measured here; only static risk proxies.
- 审计脚本注释：Contrast is computed against a single body background; gradients/images/alpha need manual review.
- 审计脚本注释：Compiled CSS-in-JS and stylesheets not passed via --css are out of scope.
- 审计脚本注释：Aesthetic judgement, copy quality and conversion are human-only items.

## 8. 复现

- 改造前：`examples\before.html` SHA-256 `2a6ba6e1b6a1da39ca8362fed075b8d7b6cb24a7371eb18cb0938f53c283e882`
- 改造后：`examples\after.html` SHA-256 `c657a877b9771ba25fb98ff159c23e6ad75baeed8f31cf436b8b9421834c6f5e`
- 审计 JSON：`reports\before.json` / `reports\after.json`

```bash
python scripts/audit_page.py <before.html> --type landing --json before.json
python scripts/audit_page.py <after.html>  --type landing --json after.json
python scripts/score.py --before before.json --after after.json --type landing --out evaluation.md
```

用相同输入与脚本版本重跑，应得到完全相同的分数。

---

来源与版权：评分规则蒸馏自 `references/sources.md` 所列 S01–S15。NN/g 十大可用性启发式归 Jakob Nielsen / Nielsen Norman Group 所有，引用时保留署名。本技能不覆盖「所有」GitHub 项目与「所有」网页，采样边界见 `references/sources.md` §0。