"""sheet/views.py —— 解析 OpenSCAD 2D SVG 导出

OpenSCAD 的 2D SVG 导出格式（实测于 2026.06 版）：
- 单位 mm，viewBox 即几何范围
- path 仅含 M / L / Z 命令（圆等曲线已被离散为多边形）
- y 坐标已翻转（emitted_y = -geometry_y），此处翻回几何坐标
"""
from __future__ import annotations

import re
from pathlib import Path

_TOKEN = re.compile(r"([MLZmlz])|(-?\d+(?:\.\d+)?)[ ,](-?\d+(?:\.\d+)?)")


def parse_openscad_svg(path) -> list[list[tuple[float, float]]]:
    """返回多边形列表（几何坐标，mm，y 向上）。"""
    text = Path(path).read_text(encoding="utf-8")
    polys: list[list[tuple[float, float]]] = []
    for d in re.findall(r"<path[^>]*\bd=\"([^\"]+)\"", text):
        poly: list[tuple[float, float]] = []
        for m in _TOKEN.finditer(d):
            if m.group(1):  # 命令符
                if m.group(1) in ("Z", "z") and poly:
                    polys.append(poly)
                    poly = []
            else:
                x = float(m.group(2))
                y = -float(m.group(3))  # 翻回几何坐标
                poly.append((x, y))
        if poly:
            polys.append(poly)
    return polys
