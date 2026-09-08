"""bridge/pipeline.py —— 构建编排：data → OpenSCAD → 模型 / 图纸

用法：
    python -m bridge.pipeline --D 300
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from . import codegen, openscad, resolver
from sheet import compose, views

ROOT = Path(__file__).resolve().parents[1]


def _obj_via_trimesh(stl: Path, obj: Path) -> Path | None:
    """STL → OBJ 兜底转换（旧版 OpenSCAD 无 .obj 导出时使用）。"""
    try:
        import trimesh
    except ImportError:
        return None
    mesh = trimesh.load(stl)
    mesh.export(obj)
    return obj if obj.exists() and obj.stat().st_size > 200 else None


def build(D: float | None = None, data_dir: Path | None = None,
          build_dir: Path | None = None) -> dict:
    data_dir = Path(data_dir) if data_dir else ROOT / "data"
    build_dir = Path(build_dir) if build_dir else ROOT / "build"
    build_dir.mkdir(parents=True, exist_ok=True)

    # 1. 数据层 → 模型规格（坐标 mm）
    spec = resolver.resolve(data_dir, D=D)

    # 2. 生成 OpenSCAD 实例代码
    codegen.emit(spec, build_dir, ROOT)

    # 3. 3D 模型导出（STL / OBJ → Blender）
    files: dict[str, Path] = {}
    files["stl"] = openscad.export(build_dir / "model.scad", build_dir / "model.stl")
    try:
        files["obj"] = openscad.export(build_dir / "model.scad", build_dir / "model.obj")
    except RuntimeError as e:
        # OpenSCAD < 2026.06 不支持 .obj 后缀导出（如 Ubuntu apt 版 2021.01）——
        # 兜底：trimesh 从 STL 转换；无 trimesh 则跳过 OBJ（STL 已可进 Blender）
        obj = _obj_via_trimesh(build_dir / "model.stl", build_dir / "model.obj")
        if obj:
            files["obj"] = obj
        else:
            print(f"  [warn] OBJ 导出已跳过（OpenSCAD 版本过旧且无 trimesh）：{e}")

    # 4. 三视图投影（SVG 轮廓 → 解析为多边形）
    polys = {}
    for name in ("front", "side", "top"):
        svg = openscad.export(build_dir / f"view_{name}.scad",
                              build_dir / f"view_{name}.svg")
        polys[name] = views.parse_openscad_svg(svg)

    # 5. 图纸排版（SVG + PDF）
    files["svg"] = build_dir / "sheet.svg"
    files["pdf"] = build_dir / "sheet.pdf"
    compose.compose_sheet(spec, polys, files["svg"], files["pdf"])

    # 6. 预览渲染（非关键产物：无 GPU/显示环境的老版 OpenSCAD 离屏 PNG 会失败，
    #    Web UI 也不再使用静态预览图——失败时跳过并警告）
    bb = spec["bbox"]
    ext = max(bb["xmax"] - bb["xmin"], bb["ymax"] - bb["ymin"], 1.0)
    eye = (ext * 1.5, -ext * 1.5, bb["zmax"] * 1.1 + ext * 0.4)
    center = ((bb["xmin"] + bb["xmax"]) / 2, (bb["ymin"] + bb["ymax"]) / 2,
              bb["zmax"] * 0.45)
    try:
        files["preview"] = openscad.render_png(
            build_dir / "model.scad", build_dir / "preview.png", eye=eye, center=center)
    except Exception as e:
        print(f"  [warn] 预览 PNG 已跳过（离屏渲染不可用）：{e}")

    # 7. 规格存档（供交互层与测试使用）
    files["spec"] = build_dir / "model_spec.json"
    files["spec"].write_text(
        json.dumps(spec, ensure_ascii=False, indent=2), encoding="utf-8")

    return {"files": {k: str(v) for k, v in files.items() if k != "spec"},
            "spec": spec}


def main() -> None:
    ap = argparse.ArgumentParser(description="CHBIM 构建管线")
    ap.add_argument("--D", type=float, default=None,
                    help="整体模数 D（柱径，mm），缺省用 data/axes.json")
    ap.add_argument("--data", default=str(ROOT / "data"))
    ap.add_argument("--out", default=str(ROOT / "build"))
    args = ap.parse_args()
    result = build(D=args.D, data_dir=Path(args.data), build_dir=Path(args.out))
    for k, v in result["files"].items():
        print(f"  {k:8s} {v}")
    print(f"  构件 {len(result['spec']['members'])} 根 · "
          f"D={result['spec']['D']}mm")


if __name__ == "__main__":
    main()
