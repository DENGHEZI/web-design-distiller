# 设计方案与评估报告模板

> 复制本模板到项目 `reports/` 下填写。P3 填「一、设计方案」，P5 由 `scripts/score.py` 自动生成「二、效果评估」。
> 禁止出现「提升质感 / 优化整体视觉 / 更有高级感」这类无法验收的条目。

---

## 一、设计方案（P0 → P3）

### P0 范围界定

| 项 | 内容 |
| --- | --- |
| 页面类型 | `landing` / `app` / `docs` / `commerce`（决定权重表） |
| 用户任务 | 一句话：用户来这一页要完成什么 |
| 唯一主 CTA | 例如「免费开始使用」 |
| 硬约束 | 品牌色、浅/深色、不可改的组件、文案是否可改 |
| 采样边界声明 | 固定写：「依据 `references/sources.md` §0 的目的性抽样，未覆盖所有 GitHub 项目与所有网页」 |

### P1 基线结论

```bash
python scripts/audit_page.py <target.html> --json reports/before.json
```

- fail 项数：__，warn 项数：__
- 硬门槛状态：G1 __ / G2 __ / G3 __ / G4 __ / G5 __
- 任一硬门槛 FAIL → 整体判定 FAIL，等级作废。

### P2 诊断（逐条带证据）

```
[P?] 现状=<实测值 / 文件:行号> → 违背=<规则原文> → 影响=<对用户任务的具体损害>
```

### P3 改动清单（按 ROI 排序）

| # | 现状值 | 目标值 | 依据（原则/规范） | 验证判据 | 工作量 |
| --- | --- | --- | --- | --- | --- |
| 1 | | | P? / S?? | `check id` 由 fail→pass | 零成本 / 改样式 / 改结构 / 改文案 |

**冲突仲裁记录**（如有）：所选分支 + 理由，见 `references/principles.md` §冲突仲裁。

### P4 实施顺序

1. 结构与层级 → 2. token 约束 → 3. 可访问性 → 4. 颜色与动效（含 `prefers-reduced-motion` 降级）

---

## 二、效果评估（P5，由脚本生成）

```bash
python scripts/audit_page.py <after.html> --json reports/after.json
python scripts/score.py --before reports/before.json --after reports/after.json \
  --type landing --out reports/evaluation.md
```

报告须含：总分与等级、硬门槛前后、六维度前后、逐项 fail→pass、客观项明细、主观分区、未覆盖项、复现命令与 SHA-256。

### 主观评审（可选，不并入总分）

| 项目 | 评分 0–4 | 备注 |
| --- | --- | --- |
| 品牌气质 | | |
| 文案说服力 | | |
| 信息架构 | | |

---

## 三、结论模板

> 改造前客观总分 __（等级 __，硬门槛 __），改造后客观总分 __（等级 __，硬门槛 __），提升 __ 分。
> 共 __ 项检查由 fail 转为 pass，仍有 __ 项未通过：__。
> 真实 LCP / INP / CLS **未实测**，需 Lighthouse / CrUX 现场数据；本次结论只覆盖源码静态质量。
> 本结论基于 `references/sources.md` §0 所述的目的性抽样，**不代表**已学习所有 GitHub 项目或所有网页设计。
