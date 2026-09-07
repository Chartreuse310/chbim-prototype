# 当前生效决策索引

本项目采用 ADR（Architecture Decision Record）记录架构决策。本文件为 活文档，对所有生效决策给出索引与一句话概要；详细推理见各 ADR 文件。推翻旧决策 = 写新 ADR 标记 supersede，旧 ADR 不删，保留推理链。

| 编号 | 标题 | 状态 | 一句话 |
|---|---|---|---|
| [ADR-0001](adr/ADR-0001-openscad-core-python-bridge.md) | 以 OpenSCAD 为建模核心 · Python 为粘合层 | ✅ 生效 | OpenSCAD 只做几何，Python 做数据解析与图纸排版 |
| [ADR-0002](adr/ADR-0002-data-layer-json.md) | 数据层采用 JSON + JSON Schema | ✅ 生效 | 可校验、可 diff、可被任意前端消费 |
| [ADR-0003](adr/ADR-0003-sheet-pipeline.md) | 图纸两步走：projection SVG + Python 排版 | ✅ 生效 | 几何归 OpenSCAD，注释归 Python；PDF 用 reportlab 避免 cairo 依赖 |
| [ADR-0004](adr/ADR-0004-position-semantics.md) | 构件位置 = 所属缝的交点 | ✅ 生效（附开放项） | 一横一纵；整排布置的紧凑写法待排 |
| [ADR-0005](adr/ADR-0005-license-mit.md) | 开源协议选 MIT | ✅ 生效 | 仅调用 OpenSCAD CLI，代码不受其 GPL 传染 |
| [ADR-0006](adr/ADR-0006-interaction-web-workbench.md) | V1 交互层用 Web 工作台 | ✅ 生效 | 标准库 HTTP + 静态前端 + three.js CDN（PNG 兜底） |
