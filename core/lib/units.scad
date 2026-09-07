// units.scad —— 模数与单位约定
//
// 全仓以 mm 为单位。整体模数 D = 柱径，由数据层（data/axes.json）
// 定义、可在交互层覆盖；D 表达式（如 "11D"）由 bridge/resolver.py
// 求值为数值后，经 bridge/codegen.py 显式传入各构件模块。
//
// 因此 core/ 内的模块只接收纯数值参数，不解析任何字符串——
// OpenSCAD 负责几何，Python 负责数据（见 docs/adr/ADR-0001）。

FN = 64;  // 圆柱面数默认约定（可行性阶段取 64，兼顾圆滑与文件体积）
