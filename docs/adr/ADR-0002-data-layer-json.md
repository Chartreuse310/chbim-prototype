---
status: accepted date: 2026-09-07
---

# ADR-0002 · 数据层采用 JSON + JSON Schema

## 背景

构件实例与轴线定义是「事实」——版本控制友好的格式才是研究者协作的 前提。OpenSCAD 语言自身可作数据（include 数据文件），但无 schema 校验、与外部工具集成差。

## 决策

- 轴线定义：`data/axes.json` + `data/schema/axis.schema.json`
- 构件定义：`data/members/*.json` + `data/schema/member.schema.json`
- JSON Schema draft-07，仅在数据层做静态参考；resolver 不强制运行时校验（V1），但任何上传到 Web 工作台的数据建议先通过 schema 校验

## 后果

- `git diff` 自然可读，研究者 PR 时一眼看出改了哪些参数
- 可被 JS / Python / Rust 任意前端直接消费
- V1 schema 仅字段级约束；复杂语义（如「交点定位要求一横一纵」）由 resolver 运行时校验
