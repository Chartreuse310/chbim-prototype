// assembly.scad —— 装配入口（供 OpenSCAD GUI 手动调试 / CLI 导出）
//
// 实例数据由 bridge/codegen.py 生成到 build/model_body.scad：
//     python -m bridge.pipeline --D 300
// 生成 build/ 后本文件即可直接预览（F5 / F6）。

include <../build/model_body.scad>

body();

// 取消注释以在 3D 预览中显示轴线（缝）：
// axes3d();
