# CHBIM Prototype V1

简体中文 | [English](README.en.md)

**以 OpenSCAD 为几何核心的中国古建参数化建模原型**

Chinese Historic Building Information Modeling——基于中国古代营造体系的 BIM 组织方法 Prototype V1 是一个面向研究者、古建筑爱好者和需要快速制作古建筑模型的创作者的开源可行性验证原型。目标是用 [OpenSCAD](https://openscad.org) 作为脚本化、可版本化、可复现的几何核心，把轴线（缝）与构件用 JSON 数据描述，由 Python 粘合层把它们转成 OpenSCAD 实例代码，并自动导出可在 Blender / Adobe Illustrator / AutoCAD 复用的模型与三视图图纸。

> **当前能力**：仅 yanzhu（檐柱），Web 工作台支持 D 模数即时调整。见 [PROGRESS.md](PROGRESS.md) 与 [docs/DECISIONS.md](docs/DECISIONS.md)了解 V1 已实现与未实现项。

## 示例输出（D=300，快照于 v0.3.0 语义）

<table>
  <tr>
    <td align="center">
      <img src="docs/images/sheet-sample.svg" width="339" alt="三视图图纸示例（SVG）"><br>
      <sub>三视图图纸 · <code>make build D=300</code>（A4，GB/T 50001-2017 图框/标题栏）</sub>
    </td>
    <td align="center">
      <img src="docs/images/preview-sample.png" width="320" alt="3D 预览示例（PNG）"><br>
      <sub>同一模型（STL）的离屏渲染</sub>
    </td>
  </tr>
</table>

快照由 `make snapshot` 手动刷新；`build/` 本身不入库。

---

## 为什么选 OpenSCAD

- **纯函数式几何**——参数化、无 GUI 状态，适合 CI 与版本控制
- **CLI 完整**——无头渲染导出 stl / obj / svg / png
- **免费开源**——降低研究者复现门槛
- **可与 Python 协作**——OpenSCAD 做几何，Python 做数据与排版（分工见下）

## 仓库结构

```
core/    构建层：纯 .scad 构件库（OpenSCAD 建模核心）
data/    数据层：轴线与构件 JSON
bridge/  粘合层：缝编码→坐标→.scad 实例代码
sheet/   图纸管线：三视图 + 图名 + 比例尺 + 日期
app/     Web 工作台（标准库 HTTP，three.js 预览）
tests/   冒烟测试
docs/    ADR / journal / 编码体系
```

## 快速开始

依赖：

- OpenSCAD ≥ 2021.01（开发验证于 2026.06.12，macOS）
- Python 3.10+ 与 `reportlab`（`pip install reportlab`）

```bash
git clone <repo>
cd chbim-prototype
pip install reportlab
make build D=300    # 生成 build/ 下的 stl/obj/svg/pdf/preview
make serve          # 启动 Web 工作台：http://127.0.0.1:8765
make test           # 运行冒烟测试
```

## 编码体系

V1 缝编码遵循“基于缝的编码体系”（详见 [docs/coding-system.md](docs/coding-system.md)）：

- 朝向：`F` 正 / `B` 背 / `L` 左 / `R` 右
- 内外：`i` 内 / `o` 外
- 缝类型：`CAO` 槽缝 / `JIAN` 间缝 / `TUAN` 槫缝（其余 V1 暂未支持）
- 构件：`{类型拼音小写}[{缝1}, {缝2}]`，位置 = 所属缝交点

例：`yanzhu[CAO_Fo, JIAN_L1]` = 位于前槽缝与左一间缝交点处的一根檐柱。

## 文档导航

- [PROGRESS.md](PROGRESS.md) —— 功能矩阵与需求池
- [docs/users.md](docs/users.md) —— 用户画像与工作流 / 痛点分析
- [docs/DECISIONS.md](docs/DECISIONS.md) —— 当前生效的架构决策索引
- [docs/coding-system.md](docs/coding-system.md) —— 基于缝的编码体系
- [docs/drawing-standard.md](docs/drawing-standard.md) —— 图纸规范对照（GB/T 50001-2017）与改造策略
- [docs/adr/](docs/adr/) —— 架构决策记录（不可变）
- [docs/journal/](docs/journal/) —— 开发日志（成败都记）
- [CHANGELOG.md](CHANGELOG.md) —— release 变更

## 致谢 Acknowledgments

本项目为「人机协作」开发：作者负责架构设计、营造术语与编码体系的全部学术决策；[WorkBuddy](https://www.workbuddy.cn) 、[Trae](https://www.trae.ai) 及 GLM 系列大模型（开发期间使用 GLM-5.3 与 GLM-5.3-Flash，截至 2026-09）承担了代码脚手架、文档初稿与工程实现辅助。

- AI 参与范围：代码实现辅助、文档起草、测试搭建；所有架构决策与学术内容（缝编码体系等）均由作者审定并对内容负责。
- 学术论文中的 AI 使用声明将按目标期刊政策另行披露。

## 协议

- **代码**：MIT License —— 见 [LICENSE](LICENSE)。
- **文档与编码体系**：暂保留所有权利（学术论文准备中），见[LICENSE-docs.md](LICENSE-docs.md)；论文见刊后将变更为 CC BY 4.0。
- **字体**：`assets/fonts/` 内的 FandolFang 为 GPL + 字体例外许可（见 [assets/fonts/Fandol-COPYING](assets/fonts/Fandol-COPYING)），PDF 中以子集形式嵌入。

> 仅以进程级调用 OpenSCAD 可执行文件，仓库代码不链接其任何库，因此不受 OpenSCAD GPL 传染。研究者引用、改写、再发布代码均无负担；引用文档中的编码体系请先联系作者（学术引用与讨论不受限）。
