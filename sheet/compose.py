"""sheet/compose.py —— 图纸排版：三视图 + 图名 + 比例尺 + 日期 + 线型

布局（A4 横排，第一角投影）：
    左上 正视图 | 右上 侧视图
    左下 俯视图 | 右下 标题栏

线型体系：
    边缘线（模型轮廓）—— 实线 0.5 mm
    辅助线（缝/轴线）  —— 虚线 0.25 mm 灰

渲染双通道：同一份图元列表分别输出 SVG 与 PDF（reportlab + CID 中文字体，
避免 cairosvg 对系统 cairo 库的依赖，见 docs/adr/ADR-0003）。
"""
from __future__ import annotations

from pathlib import Path

PAGE_W, PAGE_H = 297.0, 210.0  # A4 横排 (mm)
MARGIN = 10.0

# 视图格（x, y, w, h，y 向上、以页面左下角为原点）
CELLS = {
    "front": (14.0, 107.0, 138.0, 92.0),
    "side": (162.0, 107.0, 121.0, 92.0),
    "top": (14.0, 14.0, 138.0, 92.0),
    "title": (162.0, 14.0, 121.0, 92.0),
}
VIEW_LABELS = {"front": "正视图", "side": "侧视图", "top": "俯视图"}
STD_SCALES = [5, 10, 15, 20, 25, 30, 40, 50, 75, 100, 150, 200]

EDGE_W = 0.7          # 边缘线宽 (mm) — A4 图纸上的视觉权重
AUX_W = 0.3           # 辅助线宽 (mm)
AUX_DASH = (2.2, 1.4)  # 虚线节距 (mm)
GRAY = 0.45


def compose_sheet(spec: dict, view_polys: dict, svg_out: Path, pdf_out: Path):
    prims = _build_prims(spec, view_polys)
    _render_svg(prims, Path(svg_out))
    _render_pdf(prims, Path(pdf_out))


# ---------------------------------------------------------------- 图元生成

def _build_prims(spec: dict, view_polys: dict) -> list:
    prims: list = []

    # 页面图框
    prims.append(("rect", MARGIN, MARGIN, PAGE_W - 2 * MARGIN,
                  PAGE_H - 2 * MARGIN, 0.7, False))

    # 各视图：包围盒 → 统一标准比例
    infos, s_fit = {}, None
    for name in ("front", "side", "top"):
        vb = _poly_bbox(view_polys.get(name) or [])
        x, y, w, h = CELLS[name]
        if vb is None:
            continue
        vw = max(vb[2] - vb[0], 1e-6)
        vh = max(vb[3] - vb[1], 1e-6)
        fit = min((w - 10) / vw, (h - 12) / vh)
        infos[name] = {"vb": vb, "fit": fit}
        s_fit = fit if s_fit is None else min(s_fit, fit)

    if s_fit is not None:
        ratio = 1.0 / s_fit
        den = next((s for s in STD_SCALES if s >= ratio), None)
        if den:
            sc, scale_txt = 1.0 / den, f"1:{den}"
        else:  # 模型过小/过大时退化为非标准比例
            sc, scale_txt = s_fit, f"≈1:{ratio:.0f}"
    else:
        sc, scale_txt = 1.0, "—"

    for name in ("front", "side", "top"):
        info = infos.get(name)
        if not info:
            continue
        x, y, w, h = CELLS[name]
        prims.append(("rect", x, y, w, h, 0.2, True))  # 视图格（浅灰）

        gx = (info["vb"][0] + info["vb"][2]) / 2
        gy = (info["vb"][1] + info["vb"][3]) / 2
        ccx, ccy = x + w / 2, y + h / 2
        mx = lambda v: ccx + (v - gx) * sc  # noqa: E731
        my = lambda v: ccy + (v - gy) * sc  # noqa: E731

        # 边缘线（模型轮廓）
        for poly in view_polys[name]:
            pts = [(mx(p[0]), my(p[1])) for p in poly]
            prims.append(("poly", pts, EDGE_W))

        # 辅助线（缝）
        for a in spec["axes"]:
            if name == "top":
                if a["runs"] == "X":
                    sy = my(a["coord"])
                    if y + 6 <= sy <= y + h - 9:
                        prims.append(("auxline", x + 3, sy, x + w - 3, sy))
                        prims.append(("text", x + w - 4.5, sy + 0.9, 2.2,
                                      a["id"], "r", True))
                else:
                    sx = mx(a["coord"])
                    if x + 6 <= sx <= x + w - 9:
                        prims.append(("auxline", sx, y + 3, sx, y + h - 3))
                        prims.append(("text", sx + 0.9, y + h - 7.2, 2.2,
                                      a["id"], "l", True))
            elif name == "front":
                if a["runs"] == "Y":
                    sx = mx(a["coord"])
                    if x + 6 <= sx <= x + w - 9:
                        prims.append(("auxline", sx, y + 3, sx, y + h - 3))
                        prims.append(("text", sx + 0.9, y + h - 7.2, 2.2,
                                      a["id"], "l", True))
            else:  # side：横轴 = 模型 y（进深）
                if a["runs"] == "X":
                    sx = mx(a["coord"])
                    if x + 6 <= sx <= x + w - 9:
                        prims.append(("auxline", sx, y + 3, sx, y + h - 3))
                        prims.append(("text", sx + 0.9, y + h - 7.2, 2.2,
                                      a["id"], "l", True))

        prims.append(("text", x + 2, y + 2.2, 3.0,
                      f"{VIEW_LABELS[name]} · {scale_txt}", "l", False))

    _title_block(prims, spec, sc, scale_txt)
    return prims


def _title_block(prims: list, spec: dict, sc: float, scale_txt: str) -> None:
    tx, ty, tw, th = CELLS["title"]
    ms = spec["members"]
    m0 = ms[0] if ms else None
    D = spec["D"] or 1.0

    prims.append(("rect", tx, ty, tw, th, 0.5, False))
    div = [ty + th - 16, ty + th - 34, ty + th - 54, ty + th - 72, ty + 20]
    for d in div:
        prims.append(("line", tx, d, tx + tw, d, 0.25, True))

    # 图名
    title = f"{m0['name']}柱网 · CHBIM V1" if m0 else "CHBIM Prototype V1"
    prims.append(("text", tx + tw / 2, div[0] + 5.5, 5.2, title, "c", False))

    # 构件信息
    if m0:
        prims.append(("text", tx + 5, div[0] - 4.5, 3.0,
                      f"构件 {len(ms)} × {m0['name']}（{m0['category']}）", "l", False))
        prims.append(("text", tx + 5, div[0] - 9.0, 3.0,
                      f"柱高 {m0['height_mm'] / D:.0f}D = {m0['height_mm']:.0f} mm"
                      f" · 柱径 {m0['diameter_mm'] / D:.0f}D = {m0['diameter_mm']:.0f} mm",
                      "l", False))

    # 比例 / 图幅 / 日期 / 模数
    prims.append(("text", tx + 5, div[1] - 4.5, 3.0,
                  f"比例 {scale_txt}　图幅 A4　日期 {spec['generated']}", "l", False))
    prims.append(("text", tx + 5, div[1] - 9.0, 3.0,
                  f"整体模数 D = {spec['D']} mm（柱径）", "l", False))

    # 线型图例
    prims.append(("line", tx + 5, div[2] - 4.2, tx + 17, div[2] - 4.2, EDGE_W, False))
    prims.append(("text", tx + 19, div[2] - 5.5, 3.0, "边缘线（实线 0.5 mm）", "l", False))
    prims.append(("auxline", tx + 5, div[2] - 9.8, tx + 17, div[2] - 9.8))
    prims.append(("text", tx + 19, div[2] - 11.0, 3.0, "辅助线 · 缝（虚线 0.25 mm）", "l", False))

    # 比例尺
    total = 1000 if 1000 * sc <= tw - 14 else 500
    if total * sc > tw - 14:
        total = 250
    seg = total / 5
    x0, ybar = tx + 5, div[3] - 8
    prims.append(("text", tx + 5, div[3] - 3.2, 3.0, "比例尺", "l", False))
    for i in range(5):
        if i % 2 == 0:
            prims.append(("fillrect", x0 + i * seg * sc, ybar, seg * sc, 1.6))
    prims.append(("rect", x0, ybar, total * sc, 1.6, 0.25, False))
    prims.append(("text", x0, ybar - 4.2, 2.4, "0", "c", False))
    prims.append(("text", x0 + total * sc / 2, ybar - 4.2, 2.4,
                  f"{total / 2:.0f}", "c", False))
    prims.append(("text", x0 + total * sc, ybar - 4.2, 2.4,
                  f"{total:.0f} mm", "c", False))

    # 页脚
    prims.append(("text", tx + tw / 2, ty + 2.6, 2.4,
                  "CHBIM Prototype V1 · OpenSCAD 建模核心 · bridge/sheet 管线",
                  "c", True))


def _poly_bbox(polys: list) -> tuple | None:
    xs = [p[0] for poly in polys for p in poly]
    ys = [p[1] for poly in polys for p in poly]
    if not xs:
        return None
    return (min(xs), min(ys), max(xs), max(ys))


# ---------------------------------------------------------------- SVG 渲染

_SVG_FONT = "PingFang SC,Songti SC,Noto Sans SC,sans-serif"


def _esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _render_svg(prims: list, path: Path) -> None:
    fy = lambda v: PAGE_H - v  # noqa: E731
    out = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{PAGE_W:g}mm" '
        f'height="{PAGE_H:g}mm" viewBox="0 0 {PAGE_W:g} {PAGE_H:g}">',
        "<title>CHBIM 三视图图纸</title>",
    ]
    for p in prims:
        k = p[0]
        if k == "poly":
            pts = " ".join(f"{x:.2f},{fy(y):.2f}" for x, y in p[1])
            out.append(f'<polygon points="{pts}" fill="none" stroke="black" '
                       f'stroke-width="{p[2]:g}" stroke-linejoin="round"/>')
        elif k == "auxline":
            out.append(f'<line x1="{p[1]:.2f}" y1="{fy(p[2]):.2f}" '
                       f'x2="{p[3]:.2f}" y2="{fy(p[4]):.2f}" '
                       f'stroke="rgb(115,115,115)" stroke-width="{AUX_W:g}" '
                       f'stroke-dasharray="2.2,1.4"/>')
        elif k == "line":
            gray = p[6]
            color = "rgb(140,140,140)" if gray else "black"
            out.append(f'<line x1="{p[1]:.2f}" y1="{fy(p[2]):.2f}" '
                       f'x2="{p[3]:.2f}" y2="{fy(p[4]):.2f}" stroke="{color}" '
                       f'stroke-width="{p[5]:g}"/>')
        elif k == "rect":
            gray = p[6]
            color = "rgb(140,140,140)" if gray else "black"
            out.append(f'<rect x="{p[1]:.2f}" y="{fy(p[2] + p[4]):.2f}" '
                       f'width="{p[3]:.2f}" height="{p[4]:.2f}" fill="none" '
                       f'stroke="{color}" stroke-width="{p[5]:g}"/>')
        elif k == "fillrect":
            out.append(f'<rect x="{p[1]:.2f}" y="{fy(p[2] + p[4]):.2f}" '
                       f'width="{p[3]:.2f}" height="{p[4]:.2f}" fill="black"/>')
        elif k == "text":
            _, x, y, size, s, anchor, gray = p
            a = {"l": "start", "c": "middle", "r": "end"}[anchor]
            fill = "rgb(115,115,115)" if gray else "black"
            out.append(f'<text x="{x:.2f}" y="{fy(y):.2f}" font-size="{size:g}" '
                       f'text-anchor="{a}" fill="{fill}" '
                       f'font-family="{_SVG_FONT}">{_esc(s)}</text>')
    out.append("</svg>")
    path.write_text("\n".join(out), encoding="utf-8")


# ---------------------------------------------------------------- PDF 渲染

def _render_pdf(prims: list, path: Path) -> None:
    from reportlab.lib.units import mm
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.cidfonts import UnicodeCIDFont
    from reportlab.pdfgen import canvas as rl_canvas

    pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))
    c = rl_canvas.Canvas(str(path), pagesize=(PAGE_W * mm, PAGE_H * mm))
    c.setTitle("CHBIM 三视图图纸")
    c.scale(mm, mm)  # 之后所有坐标 / 线宽 / 字号均以 mm 计
    font = "STSong-Light"

    for p in prims:
        k = p[0]
        if k == "poly":
            c.setDash([]); c.setStrokeGray(0); c.setLineWidth(p[2])
            pts = p[1]
            b = c.beginPath()
            b.moveTo(*pts[0])
            for q in pts[1:]:
                b.lineTo(*q)
            b.close()
            c.drawPath(b, stroke=1, fill=0)
        elif k == "auxline":
            c.setDash(list(AUX_DASH)); c.setStrokeGray(GRAY); c.setLineWidth(AUX_W)
            c.line(p[1], p[2], p[3], p[4])
        elif k == "line":
            c.setDash([]); c.setStrokeGray(0.55 if p[6] else 0); c.setLineWidth(p[5])
            c.line(p[1], p[2], p[3], p[4])
        elif k == "rect":
            c.setDash([]); c.setStrokeGray(0.55 if p[6] else 0); c.setLineWidth(p[5])
            c.rect(p[1], p[2], p[3], p[4], stroke=1, fill=0)
        elif k == "fillrect":
            c.setDash([]); c.setFillGray(0)
            c.rect(p[1], p[2], p[3], p[4], stroke=0, fill=1)
        elif k == "text":
            _, x, y, size, s, anchor, gray = p
            c.setDash([]); c.setFillGray(GRAY if gray else 0)
            c.setFont(font, size)
            if anchor == "l":
                c.drawString(x, y, s)
            elif anchor == "c":
                c.drawCentredString(x, y, s)
            else:
                c.drawRightString(x, y, s)
    c.showPage()
    c.save()
