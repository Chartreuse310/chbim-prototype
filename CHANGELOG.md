# 变更日志

本项目遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/) 规范。

## [Unreleased]

### Added
- 测试扩充 26 → 52 例：新增 `tests/test_codegen.py`（构件与轴线逐实例生成、`core/` 相对路径引用、入口与三视图文件集）与 `tests/test_sheet.py`（图框/图名/标题栏/线宽图元断言、SVG 为合法 XML 且 A4 横式、PDF 文件头、OpenSCAD SVG 解析含 y 翻转）；`tests/test_smoke.py` 由「产物存在即通过」升级为格式与内容断言（STL ASCII solid、OBJ 顶点行、图纸 SVG 含三视图名与图号、PDF/PNG 文件头），并改为单次构建共享

### Fixed
- **`Makefile` 解释器路径硬编码**：`PY` 由写死的本机绝对路径改为默认 `python3`，本机自定义解释器/虚拟环境写入 `Makefile.local`（已 gitignore）。外部研究者 clone 后 `make build/serve/test` 开箱可用——原写法会让 README「快速开始」第一步直接失败
- **`app/server.py` 启动横幅死代码**：删除 `if False` 恒假的 OpenSCAD 探测表达式，改为真实调用 `openscad.find_binary()`，缺失时打印警告（不必等到点「生成」才发现）
- **CI 冒烟测试兼容旧版 OpenSCAD**（ubuntu-latest apt 版为 2021.01）：OBJ 导出失败时用 trimesh 从 STL 兜底转换（无 trimesh 则跳过并警告）；离屏 PNG 预览失败时警告并跳过（非关键产物）。CI workflow 补装 fontTools/trimesh，触发条件加 `tags: ['v*']`

## [0.3.5] - 2026-09-08

### Added
- 间数生成柱网（G17）：输入「面阔 X 间，进深 Y 间」自动生成柱网——X 间 = X+1 柱/排，仅支持奇数间（明间基准）；间宽自明间每向外一间 ×0.8（次间 0.8W、梢间 0.64W…）；柱高全柱等高 = 0.8×明间面阔；缝命名 JIAN_L1..Ln/R1..Rn（自明间向外）+ CAO 内圈 F1..Fn/B1..Bn、外圈 Fo/Bo（檐槽/金槽区分）。规律记录于 docs/coding-system.md；运算层 `bridge/layout.py`；交互 `POST /api/layout`。工作台改为单一「生成」入口：D + 面阔/进深间数 + 明间面阔/进深一次提交（原「生成模型与图纸」读取静态示例的路径由 `/api/build` 保留供 API/测试，UI 不再使用）；生成数据写 `build/generated/`，不覆盖 `data/` 静态示例；生成后轴线表联动刷新为解析坐标。新增 tests/test_layout.py（15 例）
- README 示例快照更新为 5间×3间 生成柱网（24 根檐柱，D=300，FandolFang 图纸），中英 README 补 CLI 复现命令

### Changed
- **工作台布局重排**：左栏收敛为输入区（D / 面阔间数 / 进深间数 / 明间面阔 / 明间进深）+「生成」按钮 + 状态提示，导出下载链接移至「生成」下方；右栏改为 3D 预览 → 图纸 → 轴线表与构件表（双列并排）
- three.js 加载失败的兜底提示同步更新

### Removed
- **3D 静态图**：OpenSCAD `preview.png` 不再显示在页面，导出胶囊中移除 PREVIEW 项（构建管线仍生成该文件，供 CLI / 离屏渲染使用）

## [0.3.4] - 2026-09-08

### Added
- 图纸 SVG 嵌入 FandolFang 长仿宋字体子集（fontTools + woff2，base64 `@font-face` data URI）：Web 工作台与离线打开 `sheet.svg` 都用同一仿宋字形，不再依赖系统字体；子集仅含图纸实际用到的字（含 ASCII + ~60 个 CJK），sheet.svg 体积 14 KB → 40 KB
- `Makefile` 默认 `PY` 指向 managed venv（`envs/default`，含 reportlab + fontTools），`make build/serve/snapshot/test` 直接可用，可 `PY=...` 覆盖

### Fixed
- Web 工作台图纸不应用 FandolFang：旧版仅 PDF 嵌入字体，SVG 路径字体栈 `Songti SC,...,serif` 在多数环境回落无衬线
- 8765 端口上的工作台进程是用早期代码启动的（运行 31h+），导致 Web UI 看到的图纸是 v0.3.0 之前的旧朝向；重启用当前代码后平面图按坐北朝南排布（CAO_Bo 北在上、CAO_Fo 南在下）

## [0.3.3] - 2026-09-08

### Added
- 图纸 PDF 嵌入 FandolFang 长仿宋字体（OTF→TTF 转换 + 子集嵌入，跨平台一致显示；GPL+字体例外许可，可随仓库分发）。替代 STSong-Light CID 非嵌入方案（决策点 D 定案）
- 需求池新增 G16 构件引文标注层（粒度 / 版权边界 / CSV 导出，MVP 一天量级），并备注未来测试数据来源 ancient-chinese-architecture-wiki（项目未上传）

### Changed
- 决策点 A 定案：轴线编号双轨存储（缝 `id` + 国标 `gb_no`），导出时选择显示
- 决策同步审计：DECISIONS.md 补 ADR-0007 与生效决策索引，drawing-standard 决策点 B/C/D 标记定案，PROGRESS 图纸区同步 Phase 1 实况
- README 示例快照刷新（FandolFang 长仿宋版本）

## [0.3.2] - 2026-09-07

### Changed
- README 目标读者扩展（研究者 / 古建筑爱好者 / 创作者），users.md 新增用户三（古建筑爱好者/创作者）画像，英文版同步
- README 示例输出改为等高左右双列布局（table 双列）

### Fixed
- 全库 Markdown 合并句中软换行（中文语境下软换行会渲染为空格导致断句错乱），并恢复 README 表格多行结构

## [0.3.1] - 2026-09-07

### Added
- README 示例输出：`docs/images/` 收录三视图 SVG 与 3D 预览 PNG 快照（`build/` 仍整体忽略，快照经 `make snapshot` 手动刷新）
- 需求池新增 G15 构件筛选（按缝/类型/大类过滤 + 3D 联动高亮，导出不受影响）
- 开放问题 1 更新：新朝向语义下 `CAO_Fo × CAO_Ro` 角柱交点已天然支持，pattern 语法剩余难点收敛为展开设计（枚举谓词 / ID 分配 / schema 形状）

## [0.3.0] - 2026-09-07

### Added
- `docs/drawing-standard.md`：《房屋建筑制图统一标准》GB/T 50001-2017规则对照（11 项差距分析）与三阶段改造策略
- **图纸 Phase 1 合规化**：A4 图框（装订边 a=25 / 对中标志）、简化标题栏（图名/图号/比例/日期/编码体系版本）、图名双下划线 + 比例右侧注写、定位轴线改细单点长画线、线宽组 b=0.7（0.7/0.35/0.18）、字高系列2.5/3.5/5、视图名改正立面图/侧立面图/平面图
- 新增 `test_cao_direction_runs`

### Changed
- **朝向语义重构（破坏性变更，ADR-0007）**：方向字母以建筑自身朝向为基准（坐北朝南）——`F`=南/`B`=北/`L`=东/`R`=西；+X=东、+Y=北，平面图北在上。**CAO 走向按方向字母分流**：F/B 线沿 X（定位 y）、L/R 线沿 Y（定位 x，外圈槽缝两侧线）。旧数据需迁移：北行槽缝`CAO_Ro` → `CAO_Bo`，各缝坐标符号按新语义重算。顺带修复`CAO_Lo` 静默归零隐患
- 术语：构件英文 = member 定案并写入术语表（随 0.2.1 补记）

### Added
- README 双语化：新增英文版 `README.en.md`，中英版互链

## [0.2.0] - 2026-09-07

### Added
- 需求盘点合入 `PROGRESS.md`（一次性 PRD 评审完成，评审稿已移除）：
  - 矩阵新增「位置语义」区：z 向定位（G1）、构件朝向（G2），并为全部未完成项标注优先级 `[P0/P1/P2]`
  - 需求池分组重排（构件与体系 / 工程与体验），新增 11 项：G3 屋顶举折 · G4 斗栱 · G5 基础台明 · G6 门窗 · G7 材份/斗口制 ·G8 构建缓存 · G9 产物元数据戳 · G10 错误字段定位 ·G11 CITATION/DOI · G12 Web 数据编辑 · G13 Windows 验证
  - 新增「开放问题」区块：pattern 语法 / z 向语义 / 消隐选型 /DXF 需求确认 / 首扩展构件路径
  - 毕业条件补注：枋/槫路径以 z 向 + 朝向为硬前置
- `docs/users.md`：用户画像与工作流 / 痛点分析（研究者 + 游戏开发者）
- `docs/coding-system.md`：缝的七类语义分类；构件/缝术语英文对照
- 著作权双轨声明 `LICENSE-docs.md`（代码 MIT / 文档暂保留所有权利，论文见刊后转 CC BY 4.0）
- README 致谢：WorkBuddy（GLM-5.3 / GLM-5.3-Flash）、Trae（Trae Work）

### Changed
- **间中缝编码 `JIAN_C` → `JIAN_0`（破坏性变更）**：中线统一用「默认方向 + 序数 0」表达（与 `TUAN_0` 中槫缝一致）；后缀正则移除`C` 标记，简化为 `^([FBLR]?)(\d*)([io]?)$`。旧数据中的 `JIAN_C`需手动改为 `JIAN_0`
- 术语定案：构件英文 = member（对齐 IFC `IfcMember`），不用 component

## [0.1.1] - 2026-09-07

### Changed
- **构件实例 ID 命名规范**：`{类型全拼小写}_{序号}`（如 `yanzhu_01`），替代缩写式 `YZ-01`，避免缩写撞名；与缝编码统一下划线分隔，ID 前缀 = type 字段 = 数据文件名
- `member.schema.json`：实例 `id` 由自由字符串改为正则强校验`^[a-z][a-z0-9]*_[0-9]+$`

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
