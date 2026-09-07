# CHBIM 进展总览（功能矩阵 · 随开发滚动更新）

图例：✅ 已实现 · 🚧 进行中 · ⬜ 未开始 · 💡 需求池

## V1 目标状态

### 整体模数
- ✅ 整体模数 D（柱径）由用户输入，覆盖默认
- ✅ 模数表达式 `nD` 由 resolver 求值为 mm

### 轴线类型（缝）
- ✅ 槽缝 CAO（横缝，定位 y）
- ✅ 间缝 JIAN（纵缝，定位 x，含 `JIAN_0` 间中缝/明间中线）
- ✅ 槫缝 TUAN（V1 仅作辅助线显示于俯视图）
- ⬜ 栿缝 FU / 铺作缝 PUZUO / 跳心缝 TIAO / 槫间缝 TUANJIAN

### 构件
- ✅ 檐柱 yanzhu（柱径 1D，柱高 11D）
- ⬜ 内柱 / 金柱 / 槫 tuan / 栿 fu / 额枋 efang / ...

### 交互层
- ✅ Web 工作台（标准库 HTTP + 静态前端）
- ✅ D 输入 → 一键重建模型与图纸
- ✅ 构件表 / 轴线表实时刷新
- ✅ three.js STL 预览（CDN，PNG 兜底）
- ⬜ 多构件组合、断面/柱脚编辑
- ⬜ 节点式 3D 编辑（V2）

### 导出格式
- ✅ STL（OpenSCAD 直出 → Blender）
- ✅ OBJ（OpenSCAD 2026 原生直出；保底 trimesh 转换）
- ✅ SVG（projection 三视图轮廓 + Python 排版 → Illustrator）
- ✅ PDF（reportlab 自带中文字体，零系统依赖）
- ⬜ DXF（OpenSCAD 原生 2D 导出，零成本可加——等 AutoCAD 需求）

### 图纸
- ✅ 三视图（第一角投影：正/侧/俯 + 标题栏）
- ✅ 边缘线（实线 0.7 mm）vs 辅助线（虚线 0.3 mm 灰）
- ✅ 图名 · 比例尺（自动 snap 到标准比例）· 日期
- ✅ 比例尺可视化（0-1000 mm 黑白段 + 标注）
- ✅ 线型图例（实线/虚线）
- ⬜ 隐线消隐（projection 仅出轮廓；后续可评估 Blender Freestyle 或自实现）
- ⬜ 尺寸标注（柱间距、柱高等自动标注）
- ⬜ 图层管理（轴线 / 边缘 / 标注独立图层）
- ⬜ 剖面图（剖切符号 + 断面填充）

### 工程化
- ✅ 测试：单元（resolver）+ 冒烟（端到端 OpenSCAD 调用）
- ✅ Makefile 入口（build / serve / test / clean）
- ✅ 跨平台：macOS OpenSCAD / Python stdlib + reportlab
- ✅ CI 草稿（GitHub Actions，ubuntu + apt-get install openscad）
- ⬜ Release 流程（CHANGELOG + git tag + GitHub Releases 附样例产物）
- ⬜ 贡献指南 CONTRIBUTING.md

## 需求池（开发中新需求 · 待排）

💡 **整排布置的紧凑写法**：`yanzhu[CAO_Fo, CAO_Ro]` 表示沿前后槽缝各一排檐柱——两条平行缝无交点，需在数据层约定 pattern 语法（如 `yanzhu[CAO_Fo, all JIAN]`）。当前用 `instances` 枚举单根，已在 ADR-0004 标记为开放项。

💡 柱收分 / 卷杀 / 侧脚：营造法式柱体非等径直圆柱。

💡 图纸字号按 ISO/AutoCAD 标准（粗体 5mm / 常规 3.5mm 等）而非随意设定。

💡 单位制切换：当前硬编码 mm；支持 营造尺 / 公分 / 英寸。

💡 数据校验：JSON Schema 在交互层上传时实时校验（当前仅文档层说明）。

💡 翻译：中英双语 README、ADR。

## 版本策略

遵循 SemVer：**迭代期固定 `0.x.x`**（允许小版本内含破坏性变更），
达成毕业条件后发布 **`1.0.0`**（承诺数据格式稳定，升级附迁移说明）。

1.0.0 毕业条件：

- [ ] 构件类型 ≥3 类（如柱 / 枋 / 桁），编码体系经真实案例校验
- [ ] 数据 schema 冻结并版本化（schema 加 `$version` 字段）
- [ ] 至少一位外部研究者成功复现端到端流程
- [ ] 三视图图纸达到可交付 / 出版质量
