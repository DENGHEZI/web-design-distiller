# 采样方法、来源清单与覆盖边界

> 抓取日期：**2026-11-14**（GMT+8）。本文件是本技能所有结论的事实底座，改动原则或评分前先读这里。

## 0. 先说清楚边界（必读）

「读取所有 GitHub 高星项目的设计理念以及所有网页的设计」在物理上不可穷尽，也不诚实。GitHub 上 star > 50,000 的仓库在抓取时刻为 **543 个**（API `total_count`），其中绝大多数是 awesome 清单、教程、算法题库、AI Agent 框架，与网页视觉设计没有直接关系。网页更是无限集合。

因此本技能采用**三层目的性抽样**，并把原始数据留在 `research/`，任何人都能复核：

| 层 | 抽样对象 | 作用 | 可复核性 |
| --- | --- | --- | --- |
| L1 事实层 | GitHub REST API 真实 star 榜单 + 12 个设计类仓库 | 证明「高星」不是主观挑的 | `research/*.json`，含 `fetched_at` |
| L2 一手规范层 | 官方设计系统 / 官方仓库文档 / W3C / Google web.dev | 蒸馏成可执行规则与阈值 | 每条来源有 URL 与抓取日期 |
| L3 二手观察层 | 产品官网设计观察、Refactoring UI 的社区转述 | 补充落地手法与风格倾向 | **明确标注为二手，且记录冲突** |

**覆盖边界**：未覆盖移动端原生 UI 全貌、Awwwards 实验性 WebGL 站点的一手规范、中文互联网产品的设计体系、以及暗色优先的官网（仅作为可选风格记录）。评分表默认面向**浅色信息型网页**；其他类型按 `rubric.md` 调整权重，且必须在报告中声明。

**抽样偏差**：L2 有一半来自大厂设计系统（Apple / Google / GOV.UK / Ant / Vercel 生态），偏「克制、系统化、企业级」。对强品牌表达型、娱乐型页面，本技能的「克制」维度会系统性打低分——这是已知偏差，不是页面缺陷。

---

## 1. L1 · GitHub 真实采样数据

### 1.1 榜单查询

```
GET https://api.github.com/search/repositories?q=stars:%3E50000&sort=stars&order=desc&per_page=40
```

- `total_count = 543`
- 原始数据：`research/github_top_starred.json`
- Top 10 快照：

| # | 仓库 | stars | 类型 |
| --- | --- | --- | --- |
| 1 | codecrafters-io/build-your-own-x | 562,349 | 教程清单 |
| 2 | sindresorhus/awesome | 536,470 | 清单 |
| 3 | public-apis/public-apis | 498,791 | 清单 |
| 4 | freeCodeCamp/freeCodeCamp | 459,101 | 教育站点 |
| 5 | morluto/rea | 457,695 | Agent 工具 |
| 6 | EbookFoundation/free-programming-books | 401,555 | 清单 |
| 7 | openclaw/openclaw | 394,399 | Agent 工具 |
| 8 | donnemartin/system-design-primer | 377,802 | 教程 |
| 9 | nilbuild/developer-roadmap | 371,965 | 教育站点 |
| 10 | jwasham/coding-interview-university | 364,357 | 教程 |

**可蒸馏的结论**：高星仓库里「内容即界面」占绝对多数——列表、导航、检索、可扫描性优先于装饰。这与 GOV.UK「Build digital services, not websites」和 Apple「Deference」指向同一件事：**界面退后，内容上前**。

### 1.2 设计类仓库单独查询

`GET https://api.github.com/repos/{owner}/{repo}`，原始数据：`research/design_repos.json`。

| 仓库 | stars | 定位 |
| --- | --- | --- |
| microsoft/vscode | 195,350 | 高密度工具界面 |
| vercel/next.js | 143,506 | React 框架 |
| shadcn-ui/ui | 128,131 | 可组合、可访问、有默认美感 |
| ant-design/ant-design | 100,195 | 企业级设计语言 |
| mui/material-ui | 99,345 | Material 实现 |
| tailwindlabs/tailwindcss | 98,598 | 约束式 utility 系统 |
| bradtraversy/design-resources-for-developers | 67,398 | 设计资源清单 |
| vuejs/core | 55,014 | 渐进式框架 |
| chakra-ui/chakra-ui | 40,726 | 组件系统 |
| radix-ui/primitives | 19,499 | 无样式可访问原语 |
| alphagov/govuk-frontend | 1,483 | 公共服务设计系统实现 |

> star 数是抓取时刻快照，会变化；以 JSON 内 `fetched_at` 为准，不要写成「永久事实」。

---

## 2. L2 · 一手规范来源（规则与阈值以此为准）

| 编号 | 来源 | URL | 本技能引用的内容 |
| --- | --- | --- | --- |
| S01 | shadcn/ui 官方 Introduction | https://ui.shadcn.com/docs | Open Code / Composition / Distribution / Beautiful Defaults / AI-Ready；「This is not a component library. It is how you build your component library.」 |
| S02 | React 官方 Design Principles（legacy 文档，v18.2.0） | https://legacy.reactjs.org/docs/design-principles.html | Composition、Common Abstraction、Escape Hatches、Stability、Interoperability、Debugging、Implementation（「We prefer boring code to clever code」「Elegance is secondary」）、Optimized for Tooling、Dogfooding 等 13 条 |
| S03 | Ant Design 官方 Design Values | https://ant.design/docs/spec/values | Natural / Certain / Meaningful / Growing；其中 Certain 下的 Keep restraint、Object-oriented、Modular design |
| S04 | GOV.UK Government Design Principles | https://www.gov.uk/guidance/government-design-principles | 11 条：Start with user needs / Do less / Design with data / Do the hard work to make it simple / Iterate / This is for everyone / Understand context / Build digital services, not websites / Be consistent, not uniform / Make things open / Minimise environmental impact |
| S05 | GOV.UK Design System 首页 | https://design-system.service.gov.uk/ | 组件与模式复用、一致性、无障碍策略 |
| S06 | Apple Human Interface Guidelines（三大主题，经二手汇编核对） | https://developer.apple.com/design/human-interface-guidelines/ | Clarity / Deference / Depth；颜色克制、系统字体、留白；最小触控 44×44pt |
| S07 | Material Design 3 | https://m3.material.io/ | Material as metaphor / Bold, graphic, intentional / Motion provides meaning；4dp–8dp 栅格；48×48dp 触控；design tokens |
| S08 | NN/g 十大可用性启发式 | https://www.nngroup.com/articles/ten-usability-heuristics/ | 10 条标题（系统状态可见、撤销、一致性、防错、识别优于回忆、极简美学、错误恢复等） |
| S09 | Laws of UX | https://lawsofux.com/ | Jakob's Law、Hick's Law、Fitts's Law、Miller's Law、Cognitive Load、Doherty Threshold(<400ms)、Aesthetic-Usability Effect、Law of Proximity 等 |
| S10 | Tailwind CSS 官方 Styling with utility classes | https://tailwindcss.com/docs/styling-with-utility-classes | 「Designing with constraints」：从预定义设计系统取值，避免 magic number；状态变体与响应式变体 |
| S11 | web.dev Web Vitals | https://web.dev/articles/vitals | Core Web Vitals 好阈值（75 分位）：LCP ≤ 2.5s、INP ≤ 200ms、CLS ≤ 0.1；需分移动端/桌面端 |
| S12 | Google Search Console CWV 报告说明 | https://support.google.com/webmasters/answer/9205520 | 良好 / 需要改进 / 不良 分档：LCP 2.5s/4s、INP 200ms/500ms、CLS 0.1/0.25 |
| S13 | WCAG 2.2（W3C Recommendation） | https://www.w3.org/TR/WCAG22/ | 1.4.3 正文对比度 ≥ 4.5:1、大字号 ≥ 3:1；1.4.11 非文本 ≥ 3:1；1.4.4 文字放大 200%；1.4.1 不只用颜色传达信息；2.5.8 Target Size (Minimum) 24×24 CSS px；2.4.13 Focus Appearance |
| S14 | W3C Design System 对比度说明 | https://design-system.w3.org/settings/ | 对 1.4.3 / 1.4.6 / 1.4.11 的工程化转述与理想对比区间 7:1–15:1 |
| S15 | Refactoring UI（Wathan & Schoger, 2018） | https://www.refactoringui.com/ | 层级三杠杆（尺寸/字重/颜色）、约束尺度、留白、深度与阴影尺度。**注意：本条的具体数值来自社区转述（L3），非官方全文** |

### 关键阈值速查（写进脚本常量的依据）

| 项 | 阈值 | 来源 |
| --- | --- | --- |
| 正文文本对比度 | ≥ 4.5:1 | S13 / S14 |
| 大字号（≥24px 常规 或 ≥18.66px 粗体） | ≥ 3:1 | S13 / S14 |
| UI 组件与焦点指示 | ≥ 3:1 | S13 1.4.11 |
| 文本放大 | 200% 不丢内容 | S13 1.4.4 |
| 最小目标尺寸 | 24×24 CSS px（AA）；触控建议 44pt/48dp | S13 2.5.8 / S06 / S07 |
| 交互反馈 | < 400ms（Doherty Threshold） | S09 |
| LCP / INP / CLS | 2.5s / 200ms / 0.1（75 分位） | S11 / S12 |
| 间距栅格 | 4 / 8dp 基准 | S07 / S10 / S15 |
| 单行文本长度 | 45–75 字符 | S15（二手） |

---

## 3. L3 · 二手观察（仅作风格参考，不作硬判据）

| 编号 | 来源 | 观察点 |
| --- | --- | --- |
| O01 | https://www.pixeldarts.com/post/four-design-principles-behind-stripe-linear-and-vercel | Stripe / Linear / Vercel 共性：高对比、大留白、单色基底 + 单一强调色、锐利字体 |
| O02 | https://www.alphonsolabs.com/?p=5785/ | 2026 产品官网趋势：超大字号、滚动叙事、克制动效、暗色优先、性能即设计 |
| O03 | https://muffingroup.com/blog/minimalist-website-design | 极简站点样本：Apple（白/黑/灰 + 留白）、Stripe（白 + 紫）、Linear（黑 + 白 + Inter） |
| O04 | https://github.com/JohannWilfridCalixte/agentic/blob/main/src/agentic/skills/refactoring-ui/SKILL.md 等社区 skill 转述 | Refactoring UI 的尺度表、层级表、阴影表、反模式清单 |

**已发现的冲突（必须在报告中说明所选分支）**：

1. **灰度优先 vs 真实颜色起步**：O04 内部两份转述互相矛盾（一份写 "Work in grayscale first"，另一份写 "Don't design in grayscale - work with real colors"）。本技能采用可验证的折中规则，见 `principles.md` 的「冲突仲裁」。
2. **暗色 vs 浅色**：Linear / Vercel 暗色优先（O01/O02），Apple / GOV.UK / Notion 浅色优先。这是**产品类型差异**，不是对错；由 P0 的硬约束决定，不参与评分。
3. **渐变**：Stripe 式渐变是品牌资产（O01/O02），但对多数信息型页面是噪声。`principles.md` P4 只限制「渐变数量与面积」，不禁止渐变本身。

---

## 4. 版权与合规

- 本仓库**不复制**上述文档的全文。原则名称、阈值与一句话摘要属于事实性引用；每条都附来源 URL。
- NN/g 十大启发式版权归 Jakob Nielsen / Nielsen Norman Group，其页面要求使用时注明作者与 URL：本文件 S08 已注明，衍生报告引用时须保留 `NN/g, Jakob Nielsen, 10 Usability Heuristics` 署名。
- Apple HIG、Material Design、GOV.UK、shadcn/ui、Ant Design、Tailwind CSS、web.dev、W3C 文档各自版权归其所有者；商标与产品名称仅作指代。
- 本仓库的**原创代码与原创文字**采用 MIT 许可证（见 `LICENSE`）。第三方规范文本、品牌名称、字体不在此授权范围内。
- GitHub star 数据来自公开 API，仅作为采样事实快照，不构成对任何项目的评价。
