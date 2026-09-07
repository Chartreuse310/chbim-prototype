# 基于缝的编码体系

> 引用《营造法式》中“缝”的概念（参见吴国源等人2024年刊于《建筑史学刊》的文章《〈营造法式〉大木作“缝”内涵考释（一）：综述与文本》），将“缝”作为控制构件位置的辅助线，决定构件的基准位置。

## 字段

| 类型 | 描述 | 编码示例 |
|---|---|---|
| 朝向 | F：正（front）/ B：背（back）/ L：左（left）/ R：右（right） | |
| 内外 | i：内（inner）/ o：外（outer） | |
| 位置 | 0+：距中线距离（mm 或 D 表达式） | |
| 缝   | CAO 槽缝 / JIAN 间缝 / FU 栿缝 / TUAN 槫缝 / TUANJIAN 槫间缝 / PUZUO 铺作缝 / TIAO 跳心缝 | `CAO_Fo`（前槽缝外侧）`JIAN_L1`（左一间缝）`TUAN_0`（中槫缝）`TUAN_F1`（前第 1 槫缝）|
| 构件 | 名称拼音小写 + 参数（mm 或 D 表达式）+ 所属缝 | `yanzhu[CAO_Fo, JIAN_L1]` |

## 缝编码结构

缝编码形如 `{KIND}_{SUFFIX}`：

- `KIND`：上述 7 种缝类型之一
- `SUFFIX`：正则 `^([FBLR]?)(\d*)([ioC]?)$`
  - 第 1 段：朝向（可选）
  - 第 2 段：序数（可选，如 `L1` 的 1）
  - 第 3 段：内外或中心标记（可选，`C` 表示间中缝）

## 缝的平面走向

| 类型 | 走向 | 位置定义于 |
|---|---|---|
| CAO / TUAN / TUANJIAN | 沿 X（面阔方向）延伸 | Y 轴（前后） |
| JIAN | 沿 Y（进深方向）延伸 | X 轴（左右） |

FU / PUZUO / TIAO 的走向尚未定义（V2 再议）。

## 构件位置：交点定位（V1）

构件的 `instances[].axes` 须**一横一纵**（如 `["CAO_Fo", "JIAN_L1"]`），
构件中心 = 两条缝的交点坐标。

不满足的实例在 `resolver.resolve` 时抛错并提示使用 `instances` 枚举。
整排布置的紧凑写法（开放项）见 `docs/adr/ADR-0004.md`。

## 数据层 JSON 映射

缝定义示例（`data/axes.json`）：

```json
{ "id": "CAO_Fo",  "kind": "CAO",  "distance": "2D", "note": "前槽缝（外）" }
```

构件实例示例（`data/members/yanzhu.json`）：

```json
{ "id": "yanzhu_01", "axes": ["CAO_Fo", "JIAN_L1"] }
```

## 构件 ID 命名

构件实例 ID 形如 `{类型全拼}_{序号}`，正则 `^[a-z][a-z0-9]*_[0-9]+$`（已固化
在 `data/schema/member.schema.json`）：

- 前缀 = `type` 字段 = 数据文件名，全拼小写（如 `yanzhu`），**不用缩写**，
  避免不同构件缩写撞名（缩写 `YZ` 无法区分檐柱/游柱/圆作等）
- 分隔符统一用下划线，与缝编码 `{KIND}_{SUFFIX}` 语法一致
- 构件用小写、缝 `KIND` 用大写，正好区分两个命名空间
- 示例：`yanzhu_01`；将来的 `efang_01`（额枋）、`dougong_01`（斗栱）同规则

D 表达式（`"11D"`、`"2D"`）由 `bridge/resolver.py` 在生成代码前求值为
mm 数值，OpenSCAD 永远接收纯数字。
