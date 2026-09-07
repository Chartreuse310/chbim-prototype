// axes.scad —— 轴线几何（缝）在 3D 空间中的可视化
//
// 轴线的「数值」由 bridge/resolver.py 解析（缝编码 → mm 坐标），
// 本文件只提供在 z=0 平面绘制轴线实体的模块，供 3D 预览使用；
// 图纸中的辅助线（虚线）由 sheet/compose.py 直接绘制。

// 沿 X 方向延伸的轴线（槽缝/槫缝类），位于 y = const
module axis_x(y, x0, x1, w = 2) {
    translate([x0, y - w / 2, -w / 2])
        cube([x1 - x0, w, w]);
}

// 沿 Y 方向延伸的轴线（间缝类），位于 x = const
module axis_y(x, y0, y1, w = 2) {
    translate([x - w / 2, y0, -w / 2])
        cube([w, y1 - y0, w]);
}
