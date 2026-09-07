# 当前生效决策索引

本项目采用 ADR（Architecture Decision Record）记录架构决策。本文件为活文档，对所有生效决策给出索引与一句话概要；详细推理见各 ADR 文件。推翻旧决策 = 写新 ADR 标记 supersede，旧 ADR 不删，保留推理链。

| 编号 | 标题 | 状态 | 一句话 |
|---|---|---|---|
| [ADR-0001](adr/ADR-0001-openscad-core-python-bridge.md) | 以 OpenSCAD 为建模核心 · Python 为粘合层 | ✅ 生效 | OpenSCAD 只做几何，Python 做数据解析与图纸排版 |
| [ADR-0002](adr/ADR-0002-data-layer-json.md) | 数据层采用 JSON + JSON Schema | ✅ 生效 | 可校验、可 diff、可被任意前端消费 |
| [ADR-0003](adr/ADR-0003-sheet-pipeline.md) | 图纸两步走：projection SVG + Python 排版 | ✅ 生效 | 几何归 OpenSCAD，注释归 Python；PDF 用 reportlab 避免 cairo 依赖 |
| [ADR-0004](adr/ADR-0004-position-semantics.md) | 构件位置 = 所属缝的交点 | ✅ 生效（附开放项） | 一横一纵；整排布置的紧凑写法待排 |
| [ADR-0005](adr/ADR-0005-license-mit.md) | 开源协议选 MIT | ✅ 生效 | 仅调用 OpenSCAD CLI，代码不受其 GPL 传染 |
| [ADR-0006](adr/ADR-0006-interaction-web-workbench.md) | V1 交互层用 Web 工作台 | ✅ 生效 | 标准库 HTTP + 静态前端 + three.js CDN（PNG 兜底） |
| [ADR-0007](adr/ADR-0007-orientation-convention.md) | 朝向约定：坐北朝南，方向字母以建筑自身为基准 | ✅ 生效 | F=南/B=北/L=东/R=西；CAO 走向按方向字母分流（F/B→X，L/R→Y）；**部分修正 ADR-0004 的前提**——CAO F/B × CAO L/R 现在存在交点（角柱） |

## 其他生效决策（记录于专门文档）

| 决策 | 状态 | 记录位置 |
|---|---|---|
| 构件实例 ID 命名：`{类型全拼小写}_{序号}`（如 yanzhu_01） | ✅ 生效（schema 强校验） | [coding-system.md](coding-system.md) |
| 术语：构件英文 = member（对齐 IFC，不用 component） | ✅ 生效 | [coding-system.md](coding-system.md) |
| 轴线编号双轨：缝编码 `id` 主键 + `gb_no` 自动推导（决策点 A） | ✅ 生效（Phase 2 实施） | [drawing-standard.md](drawing-standard.md) |
| 图纸线宽组 b=0.7 / 标题栏简化版（决策点 B/C） | ✅ 生效（Phase 1 已实施） | [drawing-standard.md](drawing-standard.md) |
| 图纸字体：嵌入 FandolFang 长仿宋（GPL+字体例外，OTF→TTF 子集嵌入；决策点 D） | ✅ 生效 | [drawing-standard.md](drawing-standard.md) |
| 著作权双轨：代码 MIT，文档暂保留所有权利（论文见刊后 CC BY 4.0） | ✅ 生效 | [LICENSE-docs.md](../LICENSE-docs.md) |
| 版本策略：0.x 迭代，达成毕业条件后发 1.0.0 | ✅ 生效 | [PROGRESS.md](../PROGRESS.md) |
