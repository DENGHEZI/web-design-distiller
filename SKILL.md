---
name: web-design-distiller
description: "从 GitHub 高星项目与权威设计系统中蒸馏出的网页设计审计与改造方法论。当需要评估网页设计质量、生成具体可执行的 UI 改造方案、做设计打分、产出改造前后对比报告、或按苹果风/克制风格重做页面时，应使用本技能。提供 6 维度加权评分表、硬性不达标门槛，以及 stdlib-only 的 Python 静态审计脚本，保证结论可复核。触发词包括：评估这个页面、设计评分、UI 审计、生成设计方案、redesign this page、audit UI、design review、前后对比报告。"
agent_created: true
---

# 网页设计蒸馏器（Web Design Distiller）

## 用途

把「高星开源项目的设计哲学 + 权威设计系统 + 网页体验工程规范」压缩成一套**可判定、可复跑、可打分**的工作流：输入一个页面，输出具体改造方案、改造后的代码、以及带证据的前后效果评估报告。

核心主张：**设计结论必须落在可测量的数值或文件行号上**。禁止用「不够高级」「感觉乱」「更有质感」这类不可复核的表述作为结论。

**v2 反自证原则（优先于本文件其余内容）**：静态合规分只衡量源码规则符合度，**不衡量视觉质量**。实测中两个视觉质量差异明显的页面（第 1 轮模板感版本 vs 第 2 轮重做版本）拿到同样的 100 分。因此结论必须分三层单独报告——① 静态合规 ② 真实浏览器测量 ③ 视觉质量盲评——禁止合并，禁止用「分数提升」代替「效果提升」。详见 `references/rubric.md` §0。

## 何时使用

- 需要评估某个 HTML 页面 / 组件 / 落地页的设计质量。
- 需要生成一份**具体到数值**的 UI 改造方案（不是风格建议）。
- 需要给出设计评分，或比较改造前后的效果。
- 需要从零搭一个符合现代主流审美的网页，并自带验收标准。
- 需要为设计决策找权威依据（Apple HIG / Material 3 / GOV.UK / shadcn/ui / Ant Design / NN/g / Laws of UX / WCAG / Core Web Vitals）。

## 不适用场景与能力边界

- **不要声称覆盖「所有」GitHub 项目或「所有」网页。** 采样方法、抓取日期、样本清单与覆盖边界写在 `references/sources.md`，每次引用时一并说明。
- 静态脚本审计的是**源码**。`scripts/browser_audit.py`（可选，需 Playwright + Edge）能补上本地真实渲染测量；但线上 CrUX/RUM 的 75 分位数据与 INP 仍需真实现场测量，报告里必须显式标注。
- 脚本不解析打包后的 CSS-in-JS、Tailwind 编译产物或跨文件样式表（除非用 `--css` 追加）。遇到这类项目，先说明覆盖范围缩小，再执行。
- 美学判断（品牌气质、文案说服力）属于主观项，必须由人给出，报告里单独列区，禁止伪装成客观分数。

## 工作流

严格按 P0 → P5 顺序执行，不要跳步。

### P0 · 界定范围（Scope）

先确定四项，写入方案头部：

1. **页面类型**：`landing`（首次访问、目标转化）/ `app`（日常高频、目标效率）/ `docs`（目标检索）/ `commerce`（目标决策）。类型决定评分权重，见 `references/rubric.md`。
2. **用户任务**：一句话写清用户来这一页要完成什么。
3. **唯一主 CTA**：整页只允许一个主要动作。
4. **硬约束**：品牌色、浅色/深色、必须保留的组件、内容与文案是否可改。

若第 2 或第 3 项无法确定，先向用户提问，不要擅自开工。

### P1 · 基线审计（Baseline）

对目标 HTML 运行静态审计，保留原始 JSON 作为证据：

```bash
python scripts/audit_page.py <target.html> --json reports/before.json
```

按需补充外部样式：`--css path/to/site.css`。读取输出，列出所有 `fail` 项与 `warn` 项，逐条记录 `id`、`value`、`evidence`（行号/数值）。

**立即检查硬门槛**（`references/rubric.md` 的 Hard Gates）。任一硬门槛失败，无论总分多高一律判定 `FAIL`，并在报告首行写明。

### P2 · 诊断（Diagnose）

读取 `references/principles.md` 的 8 条原则，把每个 `fail` 映射到具体原则。每条诊断必须包含三段：

```
[原则编号] 现状=<实测值/文件行号> → 违背=<规则原文> → 影响=<对 P0 用户任务的具体损害>
```

按「见效速度 × 影响面」排序，不按美观程度排序。遇到二手资料之间互相矛盾的规则（例如灰度优先 vs 真实颜色起步），按 `references/principles.md` 末尾的仲裁规则处理，并在报告里记录所选分支及理由。

### P3 · 开方案（Prescribe）

用 `assets/report-template.md` 生成 `design-plan.md`。每条改动必须写成四元组，缺一不可：

| 现状值 | 目标值 | 依据（原则编号 / 规范条款） | 验证命令或判据 |
| --- | --- | --- | --- |

按 ROI 排序，标注「零成本 / 需改样式 / 需改结构 / 需改文案」四级工作量。禁止输出「优化整体视觉」「提升质感」这类无法验收的条目。

### P4 · 实施（Implement）

按方案改代码。复用 `assets/tokens.css` 的 token 体系（浅色、纯白卡、发丝边框、单一强调色），不要临场发明 hex 值或任意 px 值。

实施顺序固定：**先结构与层级 → 再 token 约束 → 再可访问性 → 最后才加颜色与动效**。动效必须带 `prefers-reduced-motion` 降级。

### P5 · 验收与效果评估（Verify & Score）

复跑静态审计，**并额外做真实浏览器验收**，再生成三层结论报告：

```bash
python scripts/audit_page.py <after.html> --json reports/after.json
python scripts/browser_audit.py <before.html> --json reports/browser_before.json --screenshot shots/before.png
python scripts/browser_audit.py <after.html>  --json reports/browser_after.json  --screenshot shots/after.png
python scripts/score.py --before reports/before.json --after reports/after.json \
  --browser-before reports/browser_before.json --browser-after reports/browser_after.json \
  --visual reports/visual-review.json --independent reports/third_party.json \
  --out reports/evaluation.md
```

报告必须包含：① 静态合规分与 6 个维度前后分、硬门槛 G1–G5；② 真实浏览器测量与体验门槛 B1–B7；③ 视觉盲评（主观，不并入）；以及未覆盖项清单与反向指标。

**动效验收（页面含动画时强制）**：确认滚动揭示元素全部可见、`prefers-reduced-motion` 下内容一个都不能消失、动效只用 `transform`/`opacity` 因而 CLS 为 0、LCP 关键元素不被透明度淡入延迟。若发现 LCP 明显变慢，改用 transform-only 入场。

**独立样本验证**：至少审计一个非本 rubric 构造的页面（本仓库用 `examples/third-party.html`），并披露 rubric 的类型偏差。

若有人工打分，用 `--manual manual.json` 传入并标注为主观分。报告末尾附**完全可复现的命令序列**与输入文件哈希。

## 硬性规则

- 每条结论附证据：数值、CSS 规则、或 `文件:行号`。无证据的结论直接删除。
- 分数只能由 `scripts/score.py` 计算，禁止心算或手写总分。
- 客观项与主观项分区呈现，禁止混算后宣称「客观评分」。
- **禁止把静态合规分当作视觉质量结论**：三层分开报，自证样本必须声明；禁止把「分数提升」写成「效果提升」。见 `references/rubric.md` §0。
- 动效必须可降级：`prefers-reduced-motion` 下内容不得隐藏，且要有超时兜底防止快速滚动导致内容永久不可见。
- 不要为了凑分而违反 P0 的用户任务；分数服务于任务，不是反过来。
- 引用外部规范时给出 `references/sources.md` 中的来源编号与 URL，不复制受版权保护的全文。
- 报告里必须写明本技能的采样边界，禁止暗示「已学习所有网页设计」。

## 文件索引

| 路径 | 用途 |
| --- | --- |
| `references/sources.md` | 采样方法、样本清单、来源 URL、抓取日期、版权与覆盖边界 |
| `references/principles.md` | 蒸馏后的 8 条原则：可执行判定、反例、落地手法、冲突仲裁 |
| `references/rubric.md` | 6 维度评分锚点、权重、页面类型调整、硬门槛 |
| `scripts/audit_page.py` | stdlib-only 静态 HTML 审计，输出 JSON 证据 |
| `scripts/browser_audit.py` | Playwright + Edge 真实渲染测量（LCP/CLS/渲染对比度/溢出/动效降级） |
| `scripts/score.py` | 由审计 JSON 生成三层结论 Markdown 报告 |
| `assets/tokens.css` | 可直接复用的浅色 token 体系 |
| `assets/report-template.md` | 方案 + 评估报告模板 |
| `examples/after-v1.html` | 第 1 轮反例：合规 100 分但视觉模板感 |
| `examples/third-party.html` | 独立第三方样本（非本 rubric 构造） |
| `examples/` | 完整实跑样例：before / after / 方案 / 评估报告 |
| `reports/visual-review.json` | 视觉盲评记录（主观，不并入分数） |
| `reports/screenshots/` | 真实浏览器全页截图 |
| `research/` | 真实 GitHub API 采样原始数据，用于复核 star 数与时间 |

## 快速复现实跑样例

```bash
python scripts/audit_page.py examples/before.html --json /tmp/before.json
python scripts/audit_page.py examples/after.html  --json /tmp/after.json
python scripts/browser_audit.py examples/before.html --json /tmp/browser_before.json
python scripts/browser_audit.py examples/after.html  --json /tmp/browser_after.json
python scripts/score.py --before /tmp/before.json --after /tmp/after.json \
  --browser-before /tmp/browser_before.json --browser-after /tmp/browser_after.json \
  --visual reports/visual-review.json --independent reports/third_party.json \
  --out /tmp/evaluation.md
```
