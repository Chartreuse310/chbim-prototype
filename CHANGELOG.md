# 变更日志

本项目遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/) 规范。

## [Unreleased]

### Changed
- 间中缝编码 `JIAN_C` → `JIAN_0`：中线统一用「默认方向 + 序数 0」表达
  （与 `TUAN_0` 中槫缝一致）；后缀正则移除 `C` 标记，
  简化为 `^([FBLR]?)(\d*)([io]?)$`

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
