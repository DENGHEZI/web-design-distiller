# 网页设计改造效果评估报告（v2 · 三层结论）

- 生成时间：2026-11-14T10:06:05+08:00
- 页面类型：`landing`（权重评估前已固定）
- 工具：`score.py v2.0.0` + `audit_page.py` + `browser_audit.py`
- 依据：`references/rubric.md` v2、`references/principles.md` P1–P8、`references/sources.md` S01–S15

> **三层结论分开报，禁止合并成一个「设计评分」**：
> ① 静态合规分（只看源码规则）② 真实浏览器测量（渲染与性能）③ 视觉质量盲评（主观）。

## 0. 反自证声明（先读这一段）

**本次为自证样本**：`before` / `after` 都出自本仓库 `examples/`，且改造页是按本 rubric 逐条构造的。因此「静态合规分接近满分」是设计上的必然结果，**不能作为技能有效性的证据**。

**实测反证**：本仓库第 1 轮版本（`examples/after-v1.html`，视觉模板感明显）与第 2 轮重做版本（`examples/after.html`）在同一把 rubric 下**静态合规分同为 100.0**，但视觉盲评分别为 **5.0 / 10 与 8.0 / 10**。

→ **合规分对视觉质量零区分度。分数提升 ≠ 视觉效果提升。** 本技能的有效性只能由「真实浏览器测量 + 独立样本验证 + 视觉盲评」共同支撑。

## 1. 三层结论

| 层 | 指标 | 改造前 | 改造后 | 变化 |
| --- | --- | --- | --- | --- |
| ① 静态合规 | 合规分（0–100） | 16.4 | 100.0 | +83.6 |
| ① 静态合规 | 合规档位 | FAIL | A | — |
| ① 静态合规 | 硬门槛 | 存在失败 | 全部通过 | — |
| ① 静态合规 | fail 检查项 | 23 | 0 | -23 |
| ② 真实渲染 | 渲染后对比度失败 | 12 | 0 | -12 |
| ② 真实渲染 | 破图数 | 4 | 0 | -4 |
| ② 真实渲染 | 语义地标 | 1 | 4 | +3 |
| ② 真实渲染 | LCP（本地单次） | 536ms | 608ms | +72ms |
| ② 真实渲染 | CLS（本地单次） | 0 | 0 | — |
| ② 真实渲染 | 体验门槛 | 存在失败 | 全部通过 | — |
| ③ 视觉盲评 | 主观分（0–10，**不并入**） | 2.0 | 8.0 | — |

**静态合规判定：全部检查通过。该判定只说明源码符合本 rubric，不代表视觉质量。**

> **反向指标**：本地 LCP 从 536ms 变慢到 608ms。合规分上升并不代表所有体验指标改善。本地单次测量波动大，需线上 75 分位数据才能定论。

> **满分含义**：100 分只表示「通过本 rubric 的全部静态检查项」。评分表本身是目的性抽样的产物，边界见 `references/sources.md` §0。

## 2. 硬门槛

### 2.1 静态硬门槛（G）

| 门槛 | 改造前 | 改造后 | 证据 / 备注 |
| --- | --- | --- | --- |
| G1 对比度达标 (WCAG 1.4.3/1.4.11) | FAIL | PASS | min over 39 text-color declarations (per-rule background when declared; fallback bg=rgb(255, 255, 255)) |
| G2 图片 alt 完整 | FAIL | PASS | none |
| G3 键盘焦点可见且未被抹除 | FAIL | PASS | focus-visible=pass, outline-none=pass |
| G4 主 CTA 不超过一个 | FAIL | PASS | html:356 |
| G5 lang 与 viewport 齐备 | FAIL | PASS | lang=pass, viewport=pass |

### 2.2 真实渲染体验门槛（B）

| 门槛 | 改造前 | 改造后 | 证据 / 备注 |
| --- | --- | --- | --- |
| B1 渲染后文字对比度达标 | FAIL | PASS | checked=61 failures=0 min_ratio=4.89 |
| B2 无破图 | FAIL | PASS | brokenImages=0 |
| B3 无横向溢出 | PASS | PASS | scrollWidth=1440 / viewport=1440 |
| B4 CLS ≤ 0.1（本地） | PASS | PASS | CLS=0 |
| B5 LCP ≤ 2500ms（本地） | PASS | PASS | LCP=608ms |
| B6 动效降级后内容仍可见 | PASS | PASS | reduced-motion min opacity=1 |
| B7 滚动后揭示元素全部可见 | PASS | PASS | reveals=19 min opacity=1 |

> B4/B5 使用本地 file:// 单次测量，仅作冒烟检查，不等同线上达标。

## 3. 静态合规六维度（仅反映源码规则符合度）

| 维度 | 权重 | 改造前 | 改造后 | Δ |
| --- | --- | --- | --- | --- |
| 目标与层级 (`clarity`) | 20 | 1.0（加权 5.0） | 4.0（加权 20.0） | +3 |
| 系统性约束 (`system`) | 20 | 0.5（加权 2.5） | 4.0（加权 20.0） | +3.5 |
| 克制与密度 (`restraint`) | 15 | 0.5（加权 1.88） | 4.0（加权 15.0） | +3.5 |
| 可访问性 (`a11y`) | 20 | 0.8（加权 4.0） | 4.0（加权 20.0） | +3.2 |
| 性能与稳定性 (`perf`) | 15 | 0.8（加权 3.0） | 4.0（加权 15.0） | +3.2 |
| 惯例与状态 (`convention`) | 10 | 0.0（加权 0.0） | 4.0（加权 10.0） | +4 |

> `unique_colors`、`reduced_motion` 按 rubric 同时归属两个维度，属设计而非重复计分。

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
| `unique_colors` | warn | pass | 14 | 11 |
| `whitespace_token` | fail | pass | False | True |

## 5. 真实浏览器测量（Playwright + Edge）

| 指标 | 改造前 | 改造后 | 说明 |
| --- | --- | --- | --- |
| LCP | 536ms | 608ms | 本地单次，波动大 |
| FCP | 536ms | 608ms | 本地单次 |
| CLS | 0 | 0 | 加载阶段，无用户交互 |
| 渲染后对比度检查数 | 25 | 61 | 含继承色与祖先背景 |
| 渲染后对比度失败 | 12 | 0 | WCAG 1.4.3 |
| 最小对比度 | 1 | 4.89 | — |
| 破图 | 4 | 0 | — |
| 横向溢出 | False | False | — |
| 可聚焦元素 | 11 | 10 | — |
| LCP 元素 | `<p>` | `<h1>` | — |

**动效验收（第 3 轮新增）**

| 检查 | 改造前 | 改造后 |
| --- | --- | --- |
| 揭示元素数量 | 0 | 19 |
| 滚动后全部可见 | True | True |
| reduced-motion 下全部可见 | True | True |

> 动效只用 `transform` / `opacity`，因此不产生布局位移；`prefers-reduced-motion: reduce` 下所有内容强制 `opacity: 1`。帧率与卡顿未测。

> **测量边界**：本地 `file://`、单次、无网络、桌面 1440px。INP 未测；这些数字**不能**替代 CrUX/RUM 的 75 分位线上数据，也不能用来宣称「性能达标」。

## 6. 视觉质量盲评（主观，不并入任何分数）

- 方法：基于真实浏览器全页截图（Playwright + Edge，1440px 视口）的视觉盲评：评审时只看截图，不看 rubric、不看源码、不看任何分数。由同一多模态模型执行，属主观判断。
- 量纲：0-10

| 版本 | 主观分 | 评审要点 |
| --- | --- | --- |
| `before` | 2.0 | 紫红渐变 hero 刺眼、三个并列主按钮、低对比浅灰正文几乎不可读、四张破图、信息层级靠颜色堆砌。首屏没有视觉主张，属典型的未设计页面。 |
| `after_v1` | 5.0 | 合规但模板感强：等宽全屏横线把页面切成条带、三等分卡片机械重复、首屏是灰色骨架占位图、标题字号与留白缺少张力、整体像后台管理页而非产品官网。静态合规分已 100，视觉仍平庸。 |
| `after_v2` | 8.0 | 首屏 72px 两行标题形成主张，右侧用真实文案的 CSS 产品窗口替代骨架占位图，浮动指标徽标增加层次；去掉全宽横线，改用浅灰/纯白分区与大留白做节奏；特性区改为左标题 + 右编号列表，打破三等分网格。仍偏规整、品牌识别较弱、缺少真实影像，故未给更高分。 |

截图（可复核）：`reports/screenshots/before.png`、`reports/screenshots/after-v1.png`、`reports/screenshots/after.png`

- 局限：同一模型既参与改造又参与评审，存在立场偏差；理想做法是找未看过项目的人做盲评。
- 局限：静态截图无法体现动效、交互反馈、真实内容量与加载过程。
- 局限：0-10 分是主观序数，不是可复现的客观测量，禁止与静态合规分相加或换算。
- 局限：截图来自本地 file:// 渲染，字体与线上环境可能不同。
- 局限：静态截图无法呈现滚动揭示、数字计数、hover 与滚动进度条等动态设计；动效质量仅由 browser_audit.py 的 B6/B7 与 CLS=0 间接验证，未测帧率与卡顿，也未对动效美感另行打分。

> 该分数由模型/人工基于截图给出，**没有**参考 rubric 与源码，属主观判断，非真人用户研究。

## 7. 独立第三方样本验证

- 样本：`https://example.com（独立第三方样本）`（SHA-256 `25ddf2c883e0d195`）
- 该页面**不是**按本 rubric 构造的，用于检验脚本对陌生输入是否仍能产出稳定结论。
- 结果：28 项检查，fail=7，warn=1。

主要失败项：`focus_visible_defined`、`h1_count`、`interaction_states`、`reduced_motion`、`semantic_tags`、`status_feedback`、`whitespace_token`

> **已知偏差（必须披露）**：极简的单页文档（如 `example.com`）没有导航、地标、状态文案，按面向落地页的 rubric 会被扣不少分，但页面本身可能完全适用。这说明本 rubric 是**类型相关的工具，不是普适的「设计好坏」裁判**；跨类型比较必须重新定 P0 与权重。

## 8. 静态客观项明细（改造后）

| 检查 id | 状态 | 值 | 证据 |
| --- | --- | --- | --- |
| `absolute_font_units` | pass | 0.0 | 0px / 38 font-size declarations |
| `bytes_total` | pass | 36673 | html + provided css bytes |
| `contrast_failures` | pass | 0 | none |
| `contrast_min_ratio` | pass | 4.89 | min over 39 text-color declarations (per-rule background when declared; fallback bg=rgb(255, 255, 255)) |
| `css_imports` | pass | 0 | @import + <link rel=stylesheet> |
| `cta_count` | pass | 1 | html:356 |
| `external_resources` | pass | 0 | none |
| `focus_visible_defined` | pass | True | :focus-visible in CSS |
| `gradient_count` | pass | 0 | count(*-gradient() in CSS) |
| `h1_count` | pass | 1 | count(<h1>) |
| `heading_size_ratio` | pass | 2.25 | h1=36.0px body=16.0px |
| `img_alt_missing` | pass | 0 | none |
| `img_unsized` | pass | 0 | none |
| `inline_style_count` | pass | 0 | none |
| `interaction_states` | pass | {"hover": true, "focus": true, "active": true, "disabled": true} | hover, focus, active, disabled |
| `lang_attr` | pass | zh-CN | html:6 |
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
| `unique_colors` | pass | 11 | #0b7f72, #0fa693, #1c1c1e, #5f5f66, #767680, #8a6418, #e5e5ea, #fafafa, #ffffff, rgba(28,28,30,0.05), rgba(28,28,30,0.08) |
| `whitespace_token` | pass | True | --space* token definitions |

## 9. 人工评分（可选，不并入）

本次未提供 `--manual`。品牌气质、文案说服力、业务信息架构均未打分。

## 10. 未覆盖项（必读，禁止省略）

1. 线上 75 分位 Core Web Vitals 未测：browser_audit.py 是本地 file:// 单次测量，不等同 CrUX/RUM 现场数据；INP 需要真实交互，本工具完全未测。
2. 本地 LCP 单次测量波动可达 ±100ms，不能用来比较两版快慢；跨弱网、低端设备与移动端未测。
3. 跨浏览器与真机渲染、字体实际加载效果、动态交互后的可访问性（弹窗焦点陷阱、路由切换）。
4. 打包后的 CSS-in-JS / 编译产物样式（仅解析 HTML 内联 <style> 与 --css 传入的文件）。
5. 渐变、图片、半透明背景上的实际文字对比度仍需人工复核。
6. 视觉质量评分是模型/人工主观判断，不是真人用户研究，也不预测转化率。
7. 动效的帧率与卡顿（jank）未测；只验证 reduced-motion 降级后内容可见、以及加载阶段 CLS。
8. 内容真实性、文案说服力与业务信息架构。

## 11. 复现

- 改造前：`examples\before.html` SHA-256 `2a6ba6e1b6a1da39ca8362fed075b8d7b6cb24a7371eb18cb0938f53c283e882`
- 改造后：`examples\after.html` SHA-256 `53689adc1b9f33e6a2cb8f966153aa69887f144e3272fb8adbf452b5213bbd5f`
- 审计 JSON：`reports\before.json` / `reports\after.json`

```bash
python scripts/audit_page.py <before.html> --type landing --json before.json
python scripts/audit_page.py <after.html>  --type landing --json after.json
python scripts/browser_audit.py <before.html> --json browser_before.json --screenshot shots/before.png
python scripts/browser_audit.py <after.html>  --json browser_after.json  --screenshot shots/after.png
python scripts/score.py --before before.json --after after.json --type landing \
  --browser-before browser_before.json --browser-after browser_after.json \
  --visual visual-review.json --independent third_party.json --out evaluation.md
```

用相同输入与脚本版本重跑，静态合规分应完全一致；浏览器指标会有环境波动。

---

来源与版权：规则蒸馏自 `references/sources.md` S01–S15。NN/g 十大可用性启发式归 Jakob Nielsen / Nielsen Norman Group 所有，引用时保留署名。本技能不覆盖「所有」GitHub 项目与「所有」网页，采样边界见 `references/sources.md` §0。