---
status: accepted date: 2026-09-07
---

# ADR-0003 · 图纸两步走：OpenSCAD projection SVG + Python 排版

## 背景

图纸需求（来自 prototype V1）：三视图 + 图名 + 比例尺 + 日期 + 边缘线 实线/辅助线虚线。OpenSCAD 几何稳定、CLI 可输出 2D SVG；但 2D 文字标注（特别是中文）OpenSCAD 内排版痛苦、字体处理能力差。cairo 系渲染（cairosvg）对系统 cairo 库依赖不友好（纯 pip 装不上）。

## 决策

1. **几何**：OpenSCAD `projection()` 旋转后导出 SVG（仅轮廓/剖切多边形）
2. **解析**：`sheet/views.py` 把 SVG 多边形解析为 Python 列表
3. **排版**：`sheet/compose.py` 构建统一图元列表（`("poly", pts, lw)` 等 抽象），应用布局变换
4. **双渲染**：同一份图元列表分别生成 SVG（手写 `<line>`/`<polygon>`/`<text>`）和 PDF（reportlab + CID 字体 `STSong-Light` 内置中文支持）

放弃 cairosvg 的原因：macOS 系统 cairo 库安装繁琐，且 reportlab 自带 CID 中文字体（`STSong-Light`），PDF 质量与稳定性更好。

## 后果

- SVG（兼容 Illustrator）+ PDF（通用查看/打印）双交付
- 文本统一由 Python 控制，避免 OpenSCAD 内文字布局的繁琐
- 图元抽象层为后续 2D 渲染后端（DXF、CAD 格式）留出扩展点
- V1 限制：`projection()` 无隐线消隐；本决策仅解决「能做」，隐线消隐列入 [PROGRESS.md 需求池](../PROGRESS.md)
