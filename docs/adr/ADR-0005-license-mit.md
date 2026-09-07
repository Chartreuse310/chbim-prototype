---
status: accepted date: 2026-09-07
---

# ADR-0005 · 开源协议选 MIT

## 背景

本项目目标是「向研究者分享实现策略」。需要平衡：
- 让研究者最自由地引用、改写、集成
- 不引入协议传染风险

OpenSCAD 自身是 GPL-2+。但本项目仅在进程级调用其可执行文件，**不 链接任何 OpenSCAD 代码或库**，因此本项目代码不受 OpenSCAD GPL 传染。

## 决策

代码采用 **MIT License**。文档（`docs/`、`README.md` 等）可补充**CC BY 4.0**（后续可在 LICENSE 旁加 LICENSE-docs 文件）。

## 后果

- 学术项目最友好：可自由 fork、改名、内部集成
- 商业使用也允许；如要保护策略不被闭源 fork，可改 AGPL-3.0（V2 再议）
- 与 OpenSCAD 无协议冲突（仅 CLI 调用关系）
