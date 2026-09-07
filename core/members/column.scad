// column.scad —— 柱类构件
//
// 参数一律为 mm 数值；D 表达式由数据层求值后传入（见 core/lib/units.scad）。
// V1 阶段为直圆柱（可行性验证）；收分 / 卷杀 / 侧脚列入 PROGRESS.md 需求池。

// yanzhu 檐柱：柱径 1D，柱高 11D（D = 柱径，营造模数）
module yanzhu(D, H, fn = 64) {
    cylinder(h = H, d = D, $fn = fn);
}
