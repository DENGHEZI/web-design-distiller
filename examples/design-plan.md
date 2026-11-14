# 设计方案：棱镜文档落地页（PrismDocs Demo）

> 由 `web-design-distiller` P0–P4 产出。所有「现状值」来自 `reports/before.json`，所有「目标值」在 `examples/after.html` 中可逐条核验。
> 本页是**虚构演示对象**，产品与数据均非真实，仅用于验证技能可执行性。

## P0 范围界定

| 项 | 内容 |
| --- | --- |
| 页面类型 | `landing`（首次访问，目标为转化；权重表 landing） |
| 用户任务 | 让首次访问的团队决策者理解「棱镜文档解决什么」，并完成一次注册入口点击 |
| 唯一主 CTA | 「免费开始使用」 |
| 硬约束 | 浅色主题；保留青绿 `#0fa693` 的品牌识别；文案可改；不引入外部资源 |
| 采样边界声明 | 依据 `references/sources.md` §0 的目的性抽样，**未覆盖所有 GitHub 项目与所有网页** |

## P1 基线结论

```bash
python scripts/audit_page.py examples/before.html --json reports/before.json
```

- 28 项检查：**23 fail / 1 warn / 4 pass**。
- 硬门槛：G1 对比度 FAIL、G2 图片 alt FAIL、G3 键盘焦点 FAIL、G4 主 CTA FAIL、G5 lang/viewport FAIL —— **五项全失败，整体判定 FAIL，等级作废**。
- 客观总分 16.4（见 `examples/evaluation-report.md`）。
- 审计脚本已标注：`gradient backgrounds present; contrast against them needs manual review`。渐变背景上的白字对比度**静态不可判定**，属于不确定性，不是已证实达标。

## P2 诊断（逐条带证据）

```
[P1] 现状=cta_count 3（html:46,47,48） → 违背=首屏仅 1 个主 CTA / Hick's Law(S09) → 影响=决策者不知点哪个，转化路径分叉
[P2] 现状=h1_count 2、h1 27px / body 15px → 违背=单一主标题 + 标题与正文明确字号差 → 影响=去色后层级几乎不可辨
[P7] 现状=正文 #aaaaaa 2.32:1、#cccccc 1.61:1、最小 1.00:1 → 违背=WCAG 1.4.3 ≥4.5:1(S13) → 影响=弱视与强光下正文不可读
[P7] 现状=a{outline:none} 且无补偿、无 :focus-visible → 违背=WCAG 2.4.7/2.4.13 → 影响=键盘用户完全失去位置感
[P3] 现状=13 处间距越界(13/17/22px)、7 处字号越界(15/19/27px) → 违背=约束尺度(S10/S07) → 影响=同类卡片视觉不一致，改一处要改多处
[P4] 现状=3 处渐变、14 种颜色字面量、无 max-width → 违背=单色基底 + 一个强调色 / 45–75 字符行宽 → 影响=装饰抢占内容注意力
[P8] 现状=7 个外部资源、3 处样式引入、4 张图无尺寸 → 违背=CLS 风险与资源受控(S11) → 影响=首屏跳动、弱网加载不确定
[P5] 现状=仅 :hover，无任何加载/空/错误态，无 reduced-motion → 违背=NN/g #1/#3/#9(S08) → 影响=操作无反馈、动效不可关闭
[P6] 现状=4 处内联 style、无 token → 违背=Open Code / Composition(S01/S02) → 影响=样式无法局部复用与维护
```

## P3 改动清单（按 ROI 排序）

| # | 现状值 | 目标值 | 依据 | 验证判据 | 工作量 |
| --- | --- | --- | --- | --- | --- |
| 1 | `<html>` 无 `lang`，无 viewport meta | `lang="zh-CN"` + `viewport` | P7 / WCAG 3.1.1 | `lang_attr`、`meta_viewport` fail→pass | 零成本 |
| 2 | `a { outline:none }`，0 个 `:focus-visible` | 删除 `outline:none`；统一 2px 焦点环 + 3px 外圈 | P5 / P7 / S08 #1, S13 2.4.7 | `focus_visible_defined`、`outline_none_uncompensated` fail→pass | 零成本 |
| 3 | 4 张 `<img>` 无 alt、无尺寸 | 全部带 `alt` + `width`/`height`；内联 SVG data URI | P7 / P8 / S11 CLS | `img_alt_missing`、`img_unsized` fail→pass | 零成本 |
| 4 | 3 个 `.btn-primary` | 1 个主 CTA + 1 个次级描边按钮；表单按钮降为次级 | P1 / S09 Hick's Law / S08 #8 | `cta_count` 3→1 | 改结构 |
| 5 | 2 个 `<h1>`，nav 8 项 | 1 个 `<h1>`，nav 4 项 | P1 / P2 / S09 Miller's Law | `h1_count`、`nav_items` fail→pass | 改结构 |
| 6 | 最小对比度 1.00:1，8 处失败 | 正文 `#1c1c1e`(≈16:1)、次要 `#5f5f66`(≈6.3:1)；最小 4.83:1 | P7 / S13 1.4.3 | `contrast_failures` 8→0、`contrast_min_ratio` fail→pass | 改样式 |
| 7 | 品牌青绿 `#0fa693` 若作白字按钮底仅 **3.05:1** | 主 CTA 底色改 `#0b7f72`（白字 **4.83:1**）；`#0fa693` 仅用于图标/边框/焦点环（≥3:1 的 UI 场景） | P7 / S13 1.4.11 + P4 | 见 `reports/after.json` 的 `contrast_details` | 改样式 |
| 8 | 3 处渐变、14 种颜色 | 0 处渐变、12 个 token 化颜色；单色基底 + 青绿/金色小面积 | P4 / S06 Deference / O01 | `gradient_count` 3→0、`unique_colors` 14→12 | 改样式 |
| 9 | 13 处间距越界、7 处字号越界、字号全用 px | 全部落在 4/8/12/16/24/32/48/64 与 12/14/16/18/24/30/48；改用 rem 与 `--space-*` | P3 / S10 Designing with constraints | `spacing_violations` 13→0、`type_scale_violations` 7→0、`absolute_font_units` 1.0→0 | 改样式 |
| 10 | 无 `max-width`，正文撑满 | `.container max-width:960px` + `.prose 65ch` | P4 / S15 45–75 字符 | `max_width_defined`、`whitespace_token` fail→pass | 改样式 |
| 11 | 只有 `<nav>`，缺 header/main/footer | 补齐 4 个语义地标 | P7 / S13 1.3.1 | `semantic_tags` ['nav']→4 项 | 改结构 |
| 12 | 仅 `:hover`；无状态文案；无动效降级 | 补齐 hover/focus/active/disabled；新增加载、空状态、错误与「重试」；`prefers-reduced-motion` 降级 | P5 / S08 #1,#3,#9 | `interaction_states` 1→4、`status_feedback` 0→4、`reduced_motion` fail→pass | 改文案 |
| 13 | 7 个外部资源、3 处样式引入、4 处内联 style | 0 外部资源、0 样式引入、0 内联 style；单文件自包含 | P6 / P8 / S01 Open Code | `external_resources` 7→0、`css_imports` 3→0、`inline_style_count` 4→0 | 改结构 |
| 14 | h1 27px / body 15px（1.8×） | h1 3rem(48px) / body 1rem(16px)（3.0×），层级靠尺寸+字重+中性色 | P2 / S06 Clarity | `heading_size_ratio` 与去色自检 | 改样式 |

**冲突仲裁记录**：
- 「灰度优先 vs 真实颜色起步」→ 采用 **真实颜色起步 + 去色自检**。理由：品牌色已给定，纯灰度流程会掩盖 `#0fa693` 作白字底不达标的问题（第 7 条正是这样被发现的）；去色自检仍能在改造后验证层级。见 `references/principles.md` §冲突仲裁 4。
- 「渐变」→ 不全局禁止，但本页渐变不承担品牌资产，且使对比度静态不可判定，故减到 0 以消除不确定性。见 §冲突仲裁 6。

## P4 实施顺序

1. 结构与层级（第 4、5、11 条）→ 2. token 约束（第 9、10、13 条）→ 3. 可访问性（第 1、2、3、6、7、12 条）→ 4. 颜色与动效（第 8、14 条，含 reduced-motion 降级）。

产出：`examples/after.html`（自包含单文件，token 与 `assets/tokens.css` 同源）。

## P5 效果评估

```bash
python scripts/audit_page.py examples/after.html --json reports/after.json
python scripts/score.py --before reports/before.json --after reports/after.json \
  --type landing --out examples/evaluation-report.md
```

结果：客观总分 **16.4 → 100.0（+83.6）**，等级 **FAIL → A**，硬门槛 **5 项全失败 → 全部通过**，fail 检查项 **23 → 0**。

**结论边界（必读）**：100 分只表示「通过本 rubric 的全部静态检查项」。真实 LCP / INP / CLS 未实测，主观美学未打分，跨浏览器与动态交互未覆盖；`after.html` 是按本 rubric 构造的示范页，因此拿满分在预期之内，**不能据此宣称该页面在真实世界最优**。完整未覆盖项见 `examples/evaluation-report.md` §10。

---

## 第 2 轮修订：视觉重做（用户反馈「效果不行」后）

第 1 轮虽然静态合规分 100，真实浏览器截图显示仍是**合规模板**。逐条重做：

| # | 第 1 轮问题 | 第 2 轮做法 | 依据 |
| --- | --- | --- | --- |
| 1 | 每个 section 一条全宽横线，页面被切成等高条带 | 去掉全宽分隔线，改用 `#ffffff` / `#fafafa` 背景分区 + 大留白做节奏 | P4 / S06 Deference |
| 2 | 三等分卡片网格机械重复 | 特性区改为「左侧 sticky 大标题 + 右侧 01/02/03 编号横向列表」 | P2 / O01 |
| 3 | 首屏灰色骨架条占位图，明显是占位符 | 用纯 CSS 构建带真实文案的产品界面窗口（侧栏、文档、callout、标签），加浮动指标徽标 | P1 / P2 |
| 4 | h1 27px→30px，没有视觉主张 | h1 提到 72px（4.5rem）、字距 -0.045em、两行断句，与产品窗口形成左右张力 | P2 |
| 5 | 指标是三张等宽小卡 | 改为一行三个 48px 大数字 + 细竖线分隔，放在浅灰 band 里 | P2 / P4 |
| 6 | 状态区三等分小方框 | 改为一个白色面板内三行状态示例（加载 / 空状态 / 错误 + 操作） | P5 |

**关键发现**：第 1 轮与第 2 轮的静态合规分**同为 100.0**，但视觉盲评为 **5.0 vs 8.0 / 10**。这说明 rubric 只能验合规，不能验美感——因此第 2 轮同时重写了评估体系。

## 第 3 轮修订：动态设计 + 反自证评估（用户反馈「分数依然虚高」「加入动态设计」后）

**评估体系去自证**
- 新增 `scripts/browser_audit.py`：Playwright + Edge 真实渲染，测 LCP/FCP/CLS、渲染后文字对比度（含继承色与祖先背景）、破图、横向溢出、可聚焦元素、动效降级可见性。
- 新增 `reports/visual-review.json`：只基于截图、不看 rubric 与源码的视觉盲评，明确标注为主观、不并入任何分数。
- 新增独立样本 `examples/third-party.html`（抓自 `https://example.com`）：验证脚本对非自造页面也能产出结论，并披露「极简单页被落地页 rubric 扣分」的已知偏差。
- `score.py` 重写为三层结论，新增反自证声明、体验门槛 B1–B7、反向指标披露。

**动态设计（保持克制、有意义）**
| 动效 | 表达什么 | 安全约束 |
| --- | --- | --- |
| 首屏分层入场（80/160/240/320ms stagger） | 信息层级顺序 | 主视觉 h1 与产品窗口**只用 transform**，始终可见，不延迟 LCP |
| 19 个元素滚动揭示 | 阅读节奏 | 只用 `transform`/`opacity`，CLS 保持 0 |
| 指标数字计数（0→2,000+） | 数据感 | reduced-motion 下直接显示终值 |
| 顶部 2px 滚动进度条 | 阅读位置 | 纯 width 过渡，不触发布局 |
| 导航下划线、按钮上浮、编号平移、产品窗口抬升、徽标轻微浮动 | 可交互性 | 均只改 transform/颜色 |
| **1600ms 超时兜底** | 飞快滚动时 IntersectionObserver 可能漏触发 | 保证内容**永不永久隐藏** |

**实测验收**：19 个揭示元素滚动后全部可见（B7 PASS）、`prefers-reduced-motion` 下全部可见（B6 PASS）、CLS=0、渲染后对比度 0 失败、LCP 608ms（本地单次，波动范围内）。动效最初让 LCP 涨到 1176ms，随后把主视觉改为 transform-only 入场修回 608ms——这个代价与修复都记录在评估报告 §5。

## 第 4 轮修订：品牌识别与真实影像（用户「继续优化」后）

只攻一个点：**页面全靠排版撑，规整但没有记忆点**。

| # | 改动 | 依据 / 约束 |
| --- | --- | --- |
| 1 | 品牌标记从小方块升级为**棱镜三角形**（CSS `clip-path`），带一个金色端点做折射暗示 | 建立可复用的几何品牌语言 |
| 2 | 新增**棱镜折射线**符号（三条发丝线 SVG），首屏 eyebrow 与页脚品牌签名呼应 | 青绿 + 金仅小面积，不用渐变 |
| 3 | 新增 editorial 区块：左侧真实浅色摄影图（文生图生成，去水印、压缩为 30KB WebP）+ 右侧大引号客户引述与署名 | 补「内容温度」，打破纯排版 demo 感 |
| 4 | 导航加「客户故事」→ 5 项（rubric 上限内） | 提升信息真实感 |
| 5 | 图文区与上一区块之间 192px 空白收紧为 144px | Law of Proximity / 节奏 |

**度量修正（不放宽规则，修的是尺子）**
- `audit_page.py` 的 `bytes_total` 曾把内联 `<style>` **重复计一次**（HTML 全文已含 CSS），导致 41KB 误判为 warn；改为「HTML 字节 + 外部 CSS 字节」，实测 25.7KB。
- `browser_audit.py` 改为 **N 个全新浏览器上下文分别冷加载**，主值取首次冷启动。此前 reload 缓存让 LCP 掉到 36ms，会伪造「性能大幅提升」；现在保留全部样本披露区间，区间重叠时禁止宣称性能差异。
- 报告 §5 明确：冷启动 548ms → 588ms，区间 80–548 / 128–588 重叠，**不得据此说两版性能有差异**。

**证据链补齐**：`examples/after-v2.html`（第 2 轮）从 git 恢复并单独截图 `reports/screenshots/after-v2.png`；四个版本（before / v1 / v2 / v4）各有独立截图，视觉盲评 2.0 → 5.0 → 8.0 → **8.8 / 10**，而合规分 v1/v2/v4 **均为 100.0**。

**最终验收**：静态 28 项 0 fail / 0 warn；渲染后对比度 0 失败、破图 0、CLS 0、21/21 揭示元素滚动与降级后全部可见、外部资源 1（本地 WebP，带 alt 与尺寸）。合规分仍 100，但报告首段继续明确「该分数不代表视觉质量」。
