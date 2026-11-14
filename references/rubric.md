# 评分表（Rubric v2.0）

> 总分只能由 `scripts/score.py` 计算。本文件定义锚点、权重、硬门槛，以及检查 id 到维度的映射。

## 0. 反自证条款（v2 新增，优先于本文其余内容）

**静态合规分只反映源码规则符合度，不反映视觉质量。**

实测反证：本仓库 `examples/after-v1.html`（模板感明显）与 `examples/after.html`（视觉重做）在同一 rubric 下静态合规分**同为 100.0**，而基于截图的视觉盲评分别为 **5.0 / 10 与 8.0 / 10**。因此合规分对视觉质量**零区分度**。

强制约束：

1. 结论必须分三层报告，禁止合并成一个「设计评分」：① 静态合规分 ② 真实浏览器测量 ③ 视觉质量盲评。
2. 视觉盲评与人工评分**不并入**静态合规分，也不得换算或相加。
3. 若 `before` / `after` 出自本仓库 `examples/`，报告必须标注「自证样本」，并说明「改造页按本 rubric 构造，满分在预期内，不能作为技能有效性的证据」。
4. 必须运行 `scripts/browser_audit.py` 做真实渲染测量；必须至少审计一个**非本 rubric 构造**的独立样本，并披露已知偏差。
5. 禁止用静态合规分做跨页面类型比较；类型不同时先重定 P0 与权重。
6. 禁止把「分数提升」表述为「视觉效果提升」。
7. 报告中若出现反向指标（例如 LCP 变慢、体积增大），必须原样列出，不得省略。

## 1. 六个维度与默认权重（landing）

| 维度 | id | 权重 | 对应原则 | 主要检查 id |
| --- | --- | --- | --- | --- |
| 目标与层级 | `clarity` | 20 | P1, P2 | `h1_count`, `cta_count`, `nav_items`, `heading_size_ratio` |
| 系统性约束 | `system` | 20 | P3, P6 | `spacing_violations`, `type_scale_violations`, `unique_colors`, `inline_style_count` |
| 克制与密度 | `restraint` | 15 | P4 | `gradient_count`, `unique_colors`, `max_width_defined`, `whitespace_token` |
| 可访问性 | `a11y` | 20 | P7 | `contrast_failures`, `contrast_min_ratio`, `img_alt_missing`, `focus_visible_defined`, `outline_none_uncompensated`, `semantic_tags`, `lang_attr`, `title_present`, `absolute_font_units`, `reduced_motion` |
| 性能与稳定性 | `perf` | 15 | P8 | `img_unsized`, `external_resources`, `css_imports`, `bytes_total`, `meta_viewport` |
| 惯例与状态 | `convention` | 10 | P5 | `interaction_states`, `status_feedback`, `reduced_motion` |

### 按页面类型调整权重（P0 确定类型后套用）

| 类型 | clarity | system | restraint | a11y | perf | convention |
| --- | --- | --- | --- | --- | --- | --- |
| `landing` | 20 | 20 | 15 | 20 | 15 | 10 |
| `app` | 20 | 20 | 10 | 20 | 10 | 20 |
| `docs` | 25 | 15 | 10 | 25 | 15 | 10 |
| `commerce` | 20 | 15 | 10 | 20 | 20 | 15 |

> 调整权重必须在报告首页声明。不得在看完分数后回头改权重。

## 2. 单项判定与维度得分

- 每个检查项输出 `pass` / `warn` / `fail`，分别记 **1.0 / 0.5 / 0.0**。
- 维度原始分 = 该维度所有检查项的平均值（0–1）。
- 维度得分 = 原始分 × 4，保留 2 位小数 → 0–4 分锚点：

| 锚点 | 含义 |
| --- | --- |
| 4.0 | 全部检查通过，无豁免 |
| 3.0 | 多数通过，少量 warn |
| 2.0 | 约一半失败或多项 warn |
| 1.0 | 大面积失败 |
| 0.0 | 全部失败或无法检测 |

- 总分 = Σ(维度得分 / 4 × 权重)，0–100，保留 1 位小数。

### 等级

| 合规分 | 档位 | 含义（**仅静态检查通过率**） |
| --- | --- | --- |
| 90–100 | A | 静态检查高通过率（不代表可交付、不代表好看） |
| 75–89 | B | 仍有少量静态项未过 |
| 60–74 | C | 多项静态项未过 |
| < 60 | D | 大面积静态项未过 |

## 3. 硬门槛（Hard Gates）

**任一失败 → 整体判定 `FAIL`，等级作废。** 硬门槛优先于总分，防止「好看但不可用」拿高分。

| id | 条件 | 依据 |
| --- | --- | --- |
| G1 | `contrast_failures == 0`（正文/大字号/UI 对比度达标） | WCAG 2.2 1.4.3 / 1.4.11（S13） |
| G2 | `img_alt_missing == 0` | WCAG 1.1.1 |
| G3 | `focus_visible_defined == pass` 且 `outline_none_uncompensated == 0` | WCAG 2.4.7 / 2.4.13 |
| G4 | `cta_count <= 1` | P1 / Hick's Law（S09） |
| G5 | `lang_attr == pass` 且 `meta_viewport == pass` | WCAG 3.1.1 / 移动端基线 |

> 静态脚本的对比度以 `body` / `:root` 背景为基准近似计算。若页面使用渐变、图片背景或半透明层，脚本会输出 `contrast_note` 并要求人工复核；此时 G1 判为 `warn`，报告必须写明「需人工复核」，不得自动判 pass。

## 4. 客观项 / 主观项分区

**客观（进总分）**：上表所有检查 id，均由 `audit_page.py` 从源码确定性计算。

**主观（不进总分，单独列区）**：
- 品牌气质与文案说服力
- 视觉美感的最终裁决
- 信息架构是否符合业务
- 真实用户转化率

若确需人工打分，用 `score.py --manual manual.json` 传入 0–4 分，报告输出到「主观附加分（不并入总分）」区块，**禁止**与客观总分相加后宣称「综合客观评分」。

## 5. 未覆盖项（每份报告必须原样列出）

1. 真实 LCP / INP / CLS：静态脚本只测风险代理指标（`img_unsized`、`external_resources`、`bytes_total`），未实测。需 Lighthouse / CrUX 现场数据，按 75 分位、分移动端与桌面端评估（S11）。
2. 跨浏览器与真机渲染、字体加载、网络抖动。
3. 动态交互后的可访问性（弹窗焦点陷阱、路由切换后焦点管理）。
4. 打包后 CSS-in-JS / 编译产物中的样式（脚本只解析 HTML 内联 `<style>` 与 `--css` 传入的文件）。
5. 色彩在渐变 / 图片 / 半透明背景上的实际对比度。
6. 内容真实性与转化效果。

## 6. 复现要求

报告末尾必须包含：输入文件路径、文件 SHA-256、完整命令序列、脚本版本、抓取/运行时间。第三方用同样的输入必须得到同样的分数。
