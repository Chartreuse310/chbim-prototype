---status: accepted date: 2026-09-07 supersedes: (none)
---

# ADR-0004 · 构件位置 = 所属缝的交点

## 背景

用户的缝编码示例 `yanzhu[CAO_Fo, CAO_Ro]` 让 resolver 必须定义「位置如何由编码决定」。备选语义：

- A. 整排布置：沿每条轴线各一排（如沿 CAO_Fo 和 CAO_Ro 各一列檐柱）
- B. 交点定位：构件中心位于所属缝的交点（要求一横一纵）
- C. 仅归属标签：轴线只做检索，坐标另行输入

## 决策

采用 **B 交点定位**。`yanzhu[CAO_Fo, CAO_Ro]` 这种两条平行缝的写法不合法——`resolver.resolve` 抛错并提示「交点定位要求一横一纵缝」。当前数据用 `instances` 逐根枚举每根檐柱的两条正交缝（如`["CAO_Fo", "JIAN_L1"]`）。

## 开放项：整排布置的紧凑写法

`yanzhu[CAO_Fo, CAO_Ro]` 表达「沿两槽缝整排」是营造建模中极常见的场景。需要约定 pattern 语法，候选：

- `yanzhu[CAO_Fo, *JIAN]` —— 沿 CAO_Fo 与所有 JIAN 的交点
- `yanzhu[CAO_Fo ∪ CAO_Ro, JIAN]` —— 沿两个 CAO 与 JIAN 的交点
- 显式 `instances` 列表（V1 已支持）

该语法将随 V1.1 在 ADR-0004 下追加一段 supersede 解决。

## 后果

- V1 resolver 简单清晰
- 数据更冗长（每根柱一条 instance），但每条都自描述
- 紧凑写法需求明确，进入 [PROGRESS.md 需求池](../PROGRESS.md)
