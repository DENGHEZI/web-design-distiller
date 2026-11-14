# web-design-distiller · 网页设计蒸馏器

把「高星开源项目的设计哲学 + 权威设计系统 + 网页体验工程规范」压缩成一套 **可判定、可复跑、可打分** 的 Agent Skill：输入一个页面，输出具体改造方案、改造后代码、以及带证据的前后效果评估报告。

> 一句话主张：**设计结论必须落在可测量的数值或文件行号上。** 禁止用「不够高级」「感觉乱」「更有质感」当结论。

## 先说清楚边界

用户最初的诉求是「读取所有 GitHub 高 star 项目的设计理念以及所有网页的设计」——这个**做不到**，任何声称做到的都是假的。

- 2026-11-14 抓取时，GitHub API 返回 star > 50,000 的仓库共 **543 个**（`research/github_top_starred.json`），其中绝大多数是 awesome 清单、教程、算法题库、AI Agent 框架，与网页视觉设计无关。
- 网页本身是无限集合。

所以本技能采用**已声明、可复核的三层目的性抽样**：

| 层 | 内容 | 复核方式 |
| --- | --- | --- |
| L1 事实层 | GitHub REST API 真实 star 榜单 + 12 个设计类仓库 | `research/*.json`，含 `fetched_at` |
| L2 一手规范层 | shadcn/ui、React、Ant Design、GOV.UK、Apple HIG、Material 3、NN/g、Laws of UX、Tailwind、web.dev、WCAG 2.2 官方文档 | 每条来源有 URL 与抓取日期 |
| L3 二手观察层 | 产品官网观察、Refactoring UI 社区转述 | 明确标注二手，**记录内部矛盾** |

采样偏差、来源编号 S01–S15、版权声明见 [`references/sources.md`](references/sources.md) §0。每份报告都必须声明该边界。

**脚本做不到的**：真实 LCP/INP/CLS（需 Lighthouse / CrUX 现场数据）、美学裁决、文案评判、打包后 CSS-in-JS 解析、动态交互后的可访问性。这些在报告里逐条列为「未覆盖项」。

## 安装为 Skill

```bash
# 用户级（所有项目可用）
cp -r web-design-distiller ~/.workbuddy/skills/

# 项目级（随仓库共享）
cp -r web-design-distiller <项目>/.workbuddy/skills/
```

触发词：设计评分、UI 审计、评估这个页面、生成设计方案、redesign this page、audit UI、design review、前后对比报告。

## 五阶段工作流（SKILL.md）

| 阶段 | 做什么 |
| --- | --- |
| P0 Scope | 定页面类型、用户任务、唯一主 CTA、硬约束；类型决定权重 |
| P1 Baseline | 跑 `audit_page.py`，保留 JSON 证据；先查 5 条硬门槛 |
| P2 Diagnose | 把每个 fail 映射到 P1–P8 原则，三段式诊断带证据 |
| P3 Prescribe | 产出四元组方案：现状值 / 目标值 / 依据 / 验证判据，按 ROI 排序 |
| P4 Implement | 结构→token→可访问性→颜色动效，复用 `assets/tokens.css` |
| P5 Verify | 复跑审计 + `score.py` 生成前后报告，列出未覆盖项与复现命令 |

## 快速开始

```bash
python scripts/audit_page.py path/to/page.html --json before.json
# 按 assets/report-template.md 实施改造
python scripts/audit_page.py path/to/fixed.html --json after.json
python scripts/browser_audit.py path/to/page.html  --json browser_before.json --screenshot shots/before.png
python scripts/browser_audit.py path/to/fixed.html --json browser_after.json  --screenshot shots/after.png
python scripts/score.py --before before.json --after after.json --type landing \
  --browser-before browser_before.json --browser-after browser_after.json \
  --visual reports/visual-review.json --independent reports/third_party.json \
  --out evaluation.md
```

`browser_audit.py` 需要 `pip install playwright` 与 Chromium 系浏览器（本机 Edge 用 `--channel msedge`），是三层结论报告的必要环节。

追加外部样式：`--css site.css`。页面类型：`landing | app | docs | commerce`（权重不同）。

## 实跑验证结果（不是设想，是跑出来的）

| 层 | 指标 | 改造前 | 改造后 |
| --- | --- | --- | --- |
| ① 静态合规 | 合规分（0–100） | **16.4** | **100.0**（+83.6） |
| ① 静态合规 | fail 检查项 | 23 | 0 |
| ② 真实渲染 | 渲染后对比度失败 / 破图 | 12 / 4 | 0 / 0 |
| ② 真实渲染 | CLS / LCP（本地单次） | 0 / 536ms | 0 / 608ms |
| ③ 视觉盲评 | 主观分 0–10，**不并入** | 2.0 | 8.8 |

**反自证（v2 重点）**：第 1 轮模板感版本与第 2 轮视觉重做版本在本 rubric 下**合规分同为 100.0**，视觉盲评却是 **5.0 / 10 与 8.0 / 10**。合规分对视觉质量**零区分度**，禁止用「分数提升」冒充「效果提升」。

**动态设计（v3）**：19 个滚动揭示元素、首屏分层入场、数字计数、顶部滚动进度条、克制的 hover 微交互。LCP 关键元素只用 `transform` 不做透明度淡入，避免延迟最大内容绘制；CLS 保持 0；`prefers-reduced-motion` 下强制全部可见，由 `browser_audit.py` 实测验证。

**品牌与真实影像（v4）**：建立「棱镜」几何语言（三角形标记 + 发丝折射线，在首屏与页脚呼应），新增一张浅色真实感影像（30KB WebP，已去水印）配大引号客户引述的 editorial 区块。视觉盲评 8.0 → **8.8**，而合规分依旧 100.0——第四次证明两层无关。

**度量修正（修尺子，不放宽规则）**：`audit_page.py` 曾把内联 CSS 重复计入 `bytes_total`；`browser_audit.py` 改用 N 个全新上下文冷加载，主值取首次冷启动并披露完整波动区间（此前缓存 reload 会伪造 LCP 提升）。

复现：

```bash
python scripts/audit_page.py examples/before.html --json /tmp/before.json
python scripts/audit_page.py examples/after.html  --json /tmp/after.json
python scripts/score.py --before /tmp/before.json --after /tmp/after.json --type landing --out /tmp/evaluation.md
```

- 具体方案：[`examples/design-plan.md`](examples/design-plan.md)（14 条改动，每条含现状值、目标值、依据、验证判据）
- 评估报告：[`examples/evaluation-report.md`](examples/evaluation-report.md)（脚本生成，141 行）
- 对照页面：[`examples/before.html`](examples/before.html) / [`examples/after.html`](examples/after.html)

**满分含义**：100 分只代表「通过本 rubric 的全部静态检查项」。示范页本来就是按 rubric 构造的，拿满分在预期内，**不能**据此宣称它在真实世界最优。

### 方案里一个具体的取舍

品牌青绿 `#0fa693` 作白字按钮底时对比度只有 **3.05:1**，不满足 WCAG 1.4.3 的 4.5:1。方案第 7 条把它降到图标/发丝边框/焦点环（3:1 的 UI 场景够用），主 CTA 底色改为 `#0b7f72`（白字 **4.83:1**）。审美偏好与硬门槛冲突时，硬门槛优先——这正是「可复核」比「好看」更值钱的地方。

## 评分规则

| 维度 | landing 权重 |
| --- | --- |
| 目标与层级 clarity | 20 |
| 系统性约束 system | 20 |
| 克制与密度 restraint | 15 |
| 可访问性 a11y | 20 |
| 性能与稳定性 perf | 15 |
| 惯例与状态 convention | 10 |

检查项 `pass / warn / fail` → `1.0 / 0.5 / 0.0`；维度分 = 均值 × 4；总分 = Σ(维度分/4 × 权重)。

**硬门槛压倒总分**：对比度、图片 alt、键盘焦点、主 CTA ≤ 1、lang + viewport。任一失败 ⇒ 整体 `FAIL`，等级作废。防止「好看但不可用」拿高分。详见 [`references/rubric.md`](references/rubric.md)。

## 目录

```
SKILL.md                      技能入口（P0–P5）
references/sources.md         采样方法、来源、偏差、版权
references/principles.md      8 条原则 + 冲突仲裁
references/rubric.md          评分锚点、权重、硬门槛
scripts/audit_page.py         静态审计 → JSON 证据（stdlib-only）
scripts/browser_audit.py      真实浏览器测量（Playwright + Edge，可选依赖）
scripts/score.py              三层结论报告
examples/after-v1.html        第 1 轮反例：合规 100 分但视觉模板感
examples/third-party.html     独立第三方样本（非本 rubric 构造）
reports/                      审计 JSON、截图、视觉盲评记录
```

## 版权与许可

只做事实性摘要与链接，不复制第三方文档全文。NN/g 十大启发式按原页要求署名 Jakob Nielsen / Nielsen Norman Group；Apple HIG、Material、GOV.UK、shadcn/ui、Ant Design、Tailwind、web.dev、W3C 文档版权各归其主。

本仓库**原创代码与原创文字**采用 MIT 许可（[`LICENSE`](LICENSE)）；第三方规范、品牌名与字体不在授权范围内。

## 贡献

三条不可破的约束：① 每条结论必须有证据；② 每个分数必须来自 `score.py`；③ 每份报告必须列出**没有测到什么**。新增检查 id 时，同步更新 `references/rubric.md` 与 `score.py` 的 `DIMENSION_CHECKS`。
