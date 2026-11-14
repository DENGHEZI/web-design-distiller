# 蒸馏后的 8 条原则

> 每条 = 来源 + 可执行判定 + 反例 + 落地手法。判定项与 `scripts/audit_page.py` 的检查 id 对应，便于自动复核。
> 来源编号见 `sources.md`。

---

## P1 · 目标优先于外壳（User need before chrome）

**来源**：S04（Start with user needs / Build digital services, not websites / Do less）、S02（Common Abstraction: 默认抵制可在 userland 实现的功能）、Refactoring UI「Start with a feature, not a layout」（O04）、S03（Meaningful）。

**可执行判定**
- 页面能用一句话说清「用户来这里完成什么」，且该任务在首屏可见。
- 首屏存在且仅存在 **1 个主 CTA**（检查 `cta_count`）。
- 导航项 ≤ 5（Hick's Law，S09）。
- 不存在与任务无关的装饰区块占据首屏 > 30% 面积。

**❌ 反例**：三枚并排的彩色主按钮「立即开始 / 免费试用 / 联系我们」，用户不知道点哪个；先做花哨导航栏再做核心表单。

**✅ 落地**：先写核心功能块（表单 / 数据 / 内容），再补导航与页脚；次级动作降级为文字链或描边按钮。

---

## P2 · 层级靠尺寸、字重、灰度建立；颜色最后加

**来源**：S06（Clarity / Deference）、S03（Keep restraint）、NN/g #8 Aesthetic and Minimalist Design（S08）、Refactoring UI 层级三杠杆（S15/O04）、S09（Von Restorff / Cognitive Load）。

**可执行判定**
- 同一视图内三级层级可辨：主信息 / 支撑信息 / 元信息，且主要靠 `font-size` × `font-weight` × 中性色明度区分。
- 强调色不用于承载层级（把整页去色后，层级依然成立）。
- 标题与正文有明确字号差（≥ 1.5×），不是 16px 正文配 18px 标题。
- 检查 `type_scale_violations`、`gradient_count`、`unique_colors`。

**❌ 反例**：靠 5 种彩色文字区分重要性；灰色小字当正文；纯靠颜色标注状态。

**✅ 落地**：先定 type scale 与 neutral 色阶，再给唯一强调色；颜色只用于主 CTA、状态、焦点。

> **去色自检**：把页面截图转灰度后仍能一眼看出先看哪里，则层级成立。这是本技能对「高级感」唯一可操作的定义。

---

## P3 · 约束先于创作（Constrained systems）

**来源**：S10（Designing with constraints / no magic numbers）、S07（4–8dp 栅格与 design tokens）、S02（Common Abstraction / Optimized for Tooling）、S03（Object-oriented / Modular design）、S01（Composition）。

**可执行判定**
- 间距值全部来自有限尺度：`4, 8, 12, 16, 24, 32, 48, 64, 96`（检查 `spacing_violations`）。
- 字号来自有限尺度：`12, 14, 16, 18, 20, 24, 30, 36, 48, 60, 72`（检查 `type_scale_violations`）。
- 颜色来自具名 token，不出现一次性 hex（检查 `unique_colors`、`inline_style_count`）。
- 组件共享同一套接口；同类元素（卡片、按钮）视觉参数一致。

**❌ 反例**：`padding: 13px 17px`；`font-size: 15px`；每处按钮各写一个十六进制色值；`w-[423px]` 这类任意值。

**✅ 落地**：先落 `assets/tokens.css`，所有样式引用变量；确需动态值（来自接口/数据库）才用内联 style。

---

## P4 · 克制：留白、单色基底、一个强调色

**来源**：S06（Deference / 颜色克制）、S03（Keep restraint：「 perfection is achieved when there is nothing left to take away」）、S08 #8、S09（Hick's Law / Choice Overload / Aesthetic-Usability Effect）、O01（Stripe/Linear/Vercel 共性）、S04（Do less）。

**可执行判定**
- 中性色（黑/白/灰）占比 ≥ 80%，强调色仅出现在小面积（主 CTA、状态点、图标）。
- 渐变 `gradient_count` ≤ 1，且不承担信息承载。
- 组间间距 > 组内间距（Law of Proximity，S09）。
- 正文行宽 45–75 字符；不要撑满视口（检查 `max_width_defined`）。

**❌ 反例**：彩虹渐变 hero + 彩色卡片 + 每段一个强调色；元素铺满 100% 宽度；相关项与无关项间距相同。

**✅ 落地**：留白先给多再收；把装饰性色块换成发丝边框与层次阴影；一屏只讲一件事。

> **边界**：这是浅色信息型页面的默认规则。娱乐、游戏、强品牌站点可放宽，但必须在 P0 声明豁免，且不能用它去扣「一致性」以外的分。

---

## P5 · 惯例、状态可见、可恢复

**来源**：S08（NN/g 10 条，尤其 #1 状态可见、#3 用户控制与自由、#4 一致性、#5 防错、#9 错误恢复）、S09（Jakob's Law / Fitts's Law / Doherty Threshold）、S04（Be consistent, not uniform）、S03（Meaning of result：即时反馈）。

**可执行判定**
- 每个交互元素有 hover / focus / active / disabled 状态；`:focus-visible` 存在且未被 `outline:none` 无补偿地抹掉（检查 `focus_visible_defined`、`outline_none_uncompensated`）。
- 反馈 < 400ms；加载/空/错误态都有明确文案，不是泛泛的「加载中」。
- 可撤销（Undo / Cancel）；不可逆操作有确认与后果说明。
- 使用平台惯用控件与文案（Jakob's Law），不自造手势或图标语义。

**❌ 反例**：`a { outline: none; }` 且无替代；按钮点完没反应；错误提示只给错误码；自创一套导航图标。

**✅ 落地**：先补齐状态与反馈，再谈美化；为键盘用户保留完整路径。

---

## P6 · 开放、可组合、可维护

**来源**：S01（Open Code / Composition / Distribution / AI-Ready）、S02（Composition / Interoperability / Escape Hatches / Optimized for Tooling）、S04（Make things open / Be consistent, not uniform）、S05（复用组件与模式）。

**可执行判定**
- 样式与结构能被局部修改，改一处不破坏另一处（无全局选择器连锁影响）。
- 同类组件有统一接口；第三方组件接入后仍符合本页 token。
- 代码可读可被 LLM 理解：类名语义明确、无隐式全局配置、无魔法字符串。
- 检查 `inline_style_count`、`global_selector_count`（若脚本支持）。

**❌ 反例**：靠 `.card .card > div:nth-child(2) span` 覆盖样式；为改一个按钮写全局 CSS；把组件锁死在黑盒依赖里。

**✅ 落地**：复制式组件 + 局部作用域 + 明确的 token 接口；保留逃生口。

---

## P7 · 默认可访问（Accessibility is a default, not a fix）

**来源**：S13（WCAG 2.2）、S14、S04（This is for everyone）、S06（Accessibility 章节）、S07（Accessible）。

**可执行判定（硬门槛，逐条）**
| 项 | 要求 | 检查 id |
| --- | --- | --- |
| 正文对比度 | ≥ 4.5:1 | `contrast_body` |
| 大字号 / UI 组件 / 焦点 | ≥ 3:1 | `contrast_ui` |
| 图片替代文本 | 每个 `<img>` 有 `alt`（装饰图用 `alt=""`） | `img_alt_missing` |
| 键盘焦点 | `:focus-visible` 可见 | `focus_visible_defined` |
| 文字放大 | 200% 不丢内容（用 rem / 相对单位） | `absolute_font_units` |
| 语义结构 | `lang`、`viewport`、`main/nav/header/footer`、单一 `h1` | `semantics` |
| 不只用颜色 | 状态另有文字/图标 | 人工项 |
| 目标尺寸 | ≥ 24×24 CSS px（AA），触控建议 44/48 | `small_targets`（近似） |
| 动效降级 | `prefers-reduced-motion` | `reduced_motion` |

**❌ 反例**：浅灰 `#aaa` 正文写在白底（≈2.3:1）；placeholder 当 label；纯图标按钮无 `aria-label`。

**✅ 落地**：把对比度检查放进 CI（本仓库 `audit_page.py` 可直接当 CI 步骤）；AAA（7:1）只用于长文与密集数据，不必全站拉满。

---

## P8 · 性能与稳定性属于设计

**来源**：S11 / S12（Core Web Vitals）、S04（Minimise environmental impact）、S09（Doherty Threshold）、O02（Performance as design）。

**可执行判定（静态代理指标）**
- 图片带 `width` / `height` 或 `aspect-ratio`，避免布局位移（检查 `img_unsized`）。
- 外部资源数与字体数受控；无阻塞式 `@import` 链（检查 `external_resources`、`css_imports`）。
- 单文件体积可控，无内联大图（检查 `bytes_total`）。
- 首屏最大内容不依赖 JS 异步注入。

**⚠️ 必写声明**：静态脚本**不能**测出真实 LCP / INP / CLS。报告中必须写「LCP/INP/CLS 未实测，需 Lighthouse / CrUX 现场数据」，否则属于虚假结论。

**❌ 反例**：无尺寸大图导致首屏跳动；首屏靠 5 个同步脚本拼装；为动效引入整套 3D 库。

---

## 冲突仲裁规则

二手资料互相矛盾时，按以下顺序裁决，并在报告里记录所选分支：

1. **一手优先**：S01–S14 的原文 > 社区转述（O04）> 个人博客。
2. **可验证优先**：能给出阈值或可运行判据的规则 > 只有形容词的规则。
3. **任务优先**：与 P0 用户任务冲突时，任务胜出，并把该维度标记为「豁免」而非扣分。
4. **具体冲突：灰度优先 vs 真实颜色起步**
   - 采用「**真实颜色起步 + 去色自检**」：先用真实配色实现，再把截图/页面转灰度检验层级（P2）。
   - 理由：纯灰度流程会掩盖品牌色本身的对比度问题；而去色自检能在真实配色下得到与灰度流程相同的层级验证，且额外覆盖 WCAG 对比度风险。
   - 若项目处于早期线框阶段（尚无品牌色），允许灰度起步，但必须在落地配色后补做去色自检。
5. **具体冲突：暗色 vs 浅色**：由 P0 硬约束决定，不参与评分；`tokens.css` 默认提供浅色，暗色需另建 token 集。
6. **具体冲突：渐变**：不禁止，但计入 P4 的 `gradient_count`；超过 1 处或覆盖信息区域时判定为装饰过载。
