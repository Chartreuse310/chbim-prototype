---
status: accepted
date: 2026-09-07
---

# ADR-0006 · V1 交互层用 Web 工作台

## 背景

V1 交互层需要在「输入 D → 查构件 → 查看模型 → 导出图纸/模型」四步
之间切换。备选：

- CLI 先行：纯 Python 命令行驱动，最快
- Web 工作台：HTML/JS + Python 后端 + 浏览器内 3D 预览

## 决策

V1 直接做 **Web 工作台**。理由：用户偏好 HTML/JS + Python 工作台模式
，且能在浏览器内即时看到
3D 预览（three.js + STLLoader）比 CLI 体验好得多。

实现选型：
- 后端：Python **标准库** `http.server`（零依赖、与 `bridge.pipeline`
  无缝衔接）
- 前端：单页 HTML，three.js 走 jsdelivr CDN（`importmap`），失败时
  自动 fallback 到 OpenSCAD 渲染的 PNG
- 端口：默认 8765，环境变量 `CHBIM_PORT` 可覆盖

## 后果

- V1 即可分享给研究者一个可点击的 demo（`make serve`）
- 后续 V2 可平滑演进到节点式 3D 编辑（拖拽构件、轴线实时编辑）
- 依赖网络：仅在 three.js CDN 加载时需要；离线场景下 PNG 预览仍可用
