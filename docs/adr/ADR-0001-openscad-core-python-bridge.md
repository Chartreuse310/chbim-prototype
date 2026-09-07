---
status: accepted
date: 2026-09-07
---

# ADR-0001 · 以 OpenSCAD 为建模核心 · Python 为粘合层

## 背景

`openscad.org` 推荐 OpenSCAD 用于脚本化参数化建模，但其语言没有哈希
表、字符串解析弱、3D 文本排版痛苦。要让中国古建的「缝编码 + 构件」
系统发挥研究者协作价值，需要一个能把数据与几何解耦的架构。

## 决策

- `core/` 100% 纯 `.scad`：只放可复用的 OpenSCAD 模块（构件、轴线工具）
- `data/` 100% JSON：缝定义与构件实例，可 schema 校验
- `bridge/` Python：
  - `resolver.py` 把缝编码（`CAO_Fo`）解析为 mm 数值坐标
  - `codegen.py` 生成 build/ 下的实例代码（translate/rotate 调用）
  - `openscad.py` 封装 CLI
  - `pipeline.py` 编排（res → codegen → openscad → views → sheet）

OpenSCAD 接收的永远是纯数值参数（`yanzhu(D=300, H=3300)`），不解析任何
字符串——把「OpenSCAD 不会的事」一律交给 Python。

## 后果

- 几何逻辑 100% 可在 OpenSCAD GUI 中手动调试（`core/assembly.scad`）
- 数据可被未来任意前端（CLI、桌面、Web）消费
- OpenSCAD CLI 是唯一外部依赖；CI 可在任意系统跑（含 ubuntu apt）
