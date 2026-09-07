# 变更日志

本项目遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/) 规范。

## [Unreleased]

### Added
- README 双语化：新增英文版 `README.en.md`，中英版互链

## [0.2.0] - 2026-09-07

### Added
- 需求盘点合入 `PROGRESS.md`（一次性 PRD 评审完成，评审稿已移除）：
  - 矩阵新增「位置语义」区：z 向定位（G1）、构件朝向（G2），
    并为全部未完成项标注优先级 `[P0/P1/P2]`
  - 需求池分组重排（构件与体系 / 工程与体验），新增 11 项：
    G3 屋顶举折 · G4 斗栱 · G5 基础台明 · G6 门窗 · G7 材份/斗口制 ·
    G8 构建缓存 · G9 产物元数据戳 · G10 错误字段定位 ·
    G11 CITATION/DOI · G12 Web 数据编辑 · G13 Windows 验证
  - 新增「开放问题」区块：pattern 语法 / z 向语义 / 消隐选型 /
    DXF 需求确认 / 首扩展构件路径
  - 毕业条件补注：枋/槫路径以 z 向 + 朝向为硬前置
- `docs/users.md`：用户画像与工作流 / 痛点分析（研究者 + 游戏开发者）
- `docs/coding-system.md`：缝的七类语义分类；构件/缝术语英文对照
- 著作权双轨声明 `LICENSE-docs.md`（代码 MIT / 文档暂保留所有权利，
  论文见刊后转 CC BY 4.0）
- README 致谢：WorkBuddy（GLM-5.3 / GLM-5.3-Flash）、Trae（Trae Work）

### Changed
- **间中缝编码 `JIAN_C` → `JIAN_0`（破坏性变更）**：中线统一用
  「默认方向 + 序数 0」表达（与 `TUAN_0` 中槫缝一致）；后缀正则移除
  `C` 标记，简化为 `^([FBLR]?)(\d*)([io]?)$`。旧数据中的 `JIAN_C`
  需手动改为 `JIAN_0`
- 术语定案：构件英文 = member（对齐 IFC `IfcMember`），不用 component

## [0.1.1] - 2026-09-07

### Changed
- **构件实例 ID 命名规范**：`{类型全拼小写}_{序号}`（如 `yanzhu_01`），
  替代缩写式 `YZ-01`，避免缩写撞名；与缝编码统一下划线分隔，
  ID 前缀 = type 字段 = 数据文件名
- `member.schema.json`：实例 `id` 由自由字符串改为正则强校验
  `^[a-z][a-z0-9]*_[0-9]+$`

### Fixed
- `.gitignore` 补充 `.workbuddy/`、Python 环境缓存、跨平台系统文件、`*.bak`

## [0.1.0] - 2026-09-07

### Added
- 构建层：OpenSCAD 纯 .scad 构件库（core/）
- 数据层：轴线（缝）与构件 JSON + JSON Schema
- 粘合层：bridge/（resolver · codegen · openscad · pipeline）
- 图纸管线：sheet/（OpenSCAD projection → Python 排版 → SVG + PDF）
- 交互层：Web 工作台 app/（标准库 HTTP + three.js STL 预览 + PNG 兜底）
- 导出：STL · OBJ · SVG · PDF · 预览 PNG
- 治理：ADR-0001..0006 · DECISIONS.md · journal/ · coding-system.md
- 测试：resolver 单元测试 + 端到端冒烟测试
- Makefile + GitHub Actions 草稿
- README / CHANGELOG / LICENSE (MIT)

### Known limitations
- projection() 仅出轮廓/剖切，图纸无隐线消隐（记入 journal/2026-09-07.md）
- 构件类型仅 yanzhu（檐柱）；其他构件类型列入需求池
- OBJ 导出依赖 OpenSCAD 版本，2026.06 原生支持；旧版需 trimesh 转换（已记录兜底方案）
