"""bridge/codegen.py —— 生成 OpenSCAD 实例代码

几何逻辑在 core/ 的 .scad 库；本模块把 resolver 解析出的实例坐标
生成为 build/ 下的 .scad 文件（勿手改，由管线重建）。
"""
from __future__ import annotations

import os
from pathlib import Path

# 轴线（3D 预览）伸出模型范围的长度（mm）
AXIS_PAD = 200


def _core_rel(build_dir: Path, repo_root: Path) -> str:
    """生成文件中引用 core/ 的相对路径（保证任意 build 目录可用）。"""
    return os.path.relpath(repo_root / "core", build_dir).replace(os.sep, "/")


def emit(spec: dict, build_dir: Path, repo_root: Path) -> dict:
    build_dir = Path(build_dir)
    build_dir.mkdir(parents=True, exist_ok=True)
    core = _core_rel(build_dir, repo_root)
    bb = spec["bbox"]

    body_calls = [
        f"    translate([{m['x']:.3f}, {m['y']:.3f}, 0]) "
        f"{m['type']}(D={m['diameter_mm']:.3f}, H={m['height_mm']:.3f});"
        for m in spec["members"]
    ]
    axis_calls = []
    for a in spec["axes"]:
        if a["runs"] == "X":
            axis_calls.append(
                f"    axis_x(y={a['coord']:.3f}, "
                f"x0={bb['xmin'] - AXIS_PAD:.1f}, x1={bb['xmax'] + AXIS_PAD:.1f});")
        else:
            axis_calls.append(
                f"    axis_y(x={a['coord']:.3f}, "
                f"y0={bb['ymin'] - AXIS_PAD:.1f}, y1={bb['ymax'] + AXIS_PAD:.1f});")

    model_body = "\n".join([
        "// 由 bridge/codegen.py 生成 —— 勿手改（修改 data/*.json 后重新生成）",
        f"// 模数 D = {spec['D']} mm",
        f"use <{core}/members/column.scad>",
        f"use <{core}/lib/axes.scad>",
        "",
        "module body() {",
        *body_calls,
        "}",
        "",
        "// 在 3D 预览中显示轴线（core/assembly.scad 中取消注释调用）",
        "module axes3d() {",
        *axis_calls,
        "}",
        "",
    ])
    (build_dir / "model_body.scad").write_text(model_body, encoding="utf-8")

    (build_dir / "model.scad").write_text("\n".join([
        "// 由 bridge/codegen.py 生成 —— 模型导出入口（stl/obj/png）",
        "include <model_body.scad>",
        "body();",
        "",
    ]), encoding="utf-8")

    views = {
        "front": "projection() rotate([-90, 0, 0]) body();",
        "side": "projection() rotate([0, -90, 0]) rotate([-90, 0, 0]) body();",
        "top": "projection() body();",
    }
    for name, code in views.items():
        (build_dir / f"view_{name}.scad").write_text(
            "// 由 bridge/codegen.py 生成 —— 勿手改\n"
            "include <model_body.scad>\n" + code + "\n",
            encoding="utf-8")

    return {"entry": str(build_dir / "model.scad"), "views": list(views)}
