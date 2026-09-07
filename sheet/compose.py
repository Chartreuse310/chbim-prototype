"""sheet/compose.py —— 图纸排版（对齐 GB/T 50001-2017，见 docs/drawing-standard.md）

布局（A4 横式，第一角投影）：
    图框：装订边 a=25（左）、其余边 c=5，粗实线 b=0.7，四边对中标志
    左上 正立面图 | 右上 侧立面图
    左下 平面图   | 右下 标题栏（图名/图号/比例/日期/编码体系版本）

线宽组（b=0.7mm，按 b/0.5b/0.25b 体系）：
    粗 0.7 —— 图框、标题栏外框、构件可见轮廓
    中 0.35 —— 图名细下划线、标题栏分格、对中标志(0.35)
    细 0.18 —— 定位轴线（单点长画线）
注：对中标志线宽 0.35mm（〔3.1.2〕）。

渲染双通道：同一份图元列表分别输出 SVG 与 PDF（reportlab + CID 中文字体，
避免 cairosvg 对系统 cairo 库的依赖，见 docs/adr/ADR-0003）。
"""
from __future__ import annotations

from pathlib import Path

# ---- 页面与图框（GB/T 50001-2017 表 3.1.1，A4 横式）----
PAGE_W, PAGE_H = 297.0, 210.0
BINDING_A = 25.0   # 装订边宽 a
FRAME_C = 5.0      # 非装订边图框距 c（A2~A4）
FX0, FY0 = BINDING_A, FRAME_C
FX1, FY1 = PAGE_W - FRAME_C, PAGE_H - FRAME_C

# ---- 线宽组（b=0.7mm）----
W_THICK = 0.7      # b：图框 / 标题栏外框 / 构件轮廓
W_MED = 0.35       # 0.5b：分格线 / 细下划线 / 对中标志
W_THIN = 0.18      # 0.25b：定位轴线（单点长画线）

# ---- 字高系列（表 5.0.2）----
H_NAME = 5.0       # 图名
H_INFO = 3.5       # 常规注写
H_MIN = 2.5        # 数字/代号最小值

# 定位轴线：单点长画线节距（长划, 空, 点, 空）
AXIS_DASH = (5.0, 1.2, 0.9, 1.2)

# 视图格（x, y, w, h，y 向上、以页面左下角为原点；均在图框内）
CELLS = {
    "front": (30.0, 108.0, 126.0, 92.0),
    "side": (163.0, 108.0, 126.0, 92.0),
    "top": (30.0, 40.0, 126.0, 62.0),
}
VIEW_LABELS = {"front": "正立面图", "side": "侧立面图", "top": "平面图"}
STD_SCALES = [5, 10, 15, 20, 25, 30, 40, 50, 75, 100, 150, 200]

# 标题栏（图框内右下角，简化版：图名/图号/比例/日期/编码体系版本）
TB_W, TB_H = 120.0, 30.0
TB_X, TB_Y = FX1 - TB_W, FY0
SHEET_NO = "CHBIM-01"          # 图号（单图阶段固定；多图时接图纸编号系统）
CODING_VERSION = "缝编码体系 V1"


def compose_sheet(spec: dict, view_polys: dict, svg_out: Path, pdf_out: Path):
    prims = _build_prims(spec, view_polys)
    _render_svg(prims, Path(svg_out))
    _render_pdf(prims, Path(pdf_out))


# ---------------------------------------------------------------- 图元生成

def _build_prims(spec: dict, view_polys: dict) -> list:
    prims: list = []

    # 图框（粗实线 b）〔3.1.1〕
    prims.append(("rect", FX0, FY0, FX1 - FX0, FY1 - FY0, W_THICK, False))

    # 对中标志：四边中点，线宽 0.35，从幅面边伸入图框内 5mm〔3.1.2〕
    cxm = (FX0 + FX1) / 2
    ym = (FY0 + FY1) / 2
    prims.append(("line", 0.0, ym, FX0 + 5, ym, W_MED, False))
    prims.append(("line", PAGE_W, ym, FX1 - 5, ym, W_MED, False))
    prims.append(("line", cxm, 0.0, cxm, FY0 + 5, W_MED, False))
    prims.append(("line", cxm, PAGE_H, cxm, FY1 - 5, W_MED, False))

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
        gx = (info["vb"][0] + info["vb"][2]) / 2
        gy = (info["vb"][1] + info["vb"][3]) / 2
        ccx, ccy = x + w / 2, y + h / 2
        mx = lambda v: ccx + (v - gx) * sc  # noqa: E731
        my = lambda v: ccy + (v - gy) * sc  # noqa: E731

        # 构件可见轮廓（粗实线 b）
        for poly in view_polys[name]:
            pts = [(mx(p[0]), my(p[1])) for p in poly]
            prims.append(("poly", pts, W_THICK))

        # 定位轴线（缝）：细单点长画线 0.25b〔8.0.1〕
        for a in spec["axes"]:
            if name == "top":
                if a["runs"] == "X":
                    sy = my(a["coord"])
                    if y + 6 <= sy <= y + h - 9:
                        prims.append(("auxline", x + 3, sy, x + w - 3, sy))
                        prims.append(("text", x + w - 4.5, sy + 0.9, H_MIN,
                                      a["id"], "r", True))
                else:
                    sx = mx(a["coord"])
                    if x + 6 <= sx <= x + w - 9:
                        prims.append(("auxline", sx, y + 3, sx, y + h - 3))
                        prims.append(("text", sx + 0.9, y + h - 7.2, H_MIN,
                                      a["id"], "l", True))
            elif name == "front":
                if a["runs"] == "Y":
                    sx = mx(a["coord"])
                    if x + 6 <= sx <= x + w - 9:
                        prims.append(("auxline", sx, y + 3, sx, y + h - 3))
                        prims.append(("text", sx + 0.9, y + h - 7.2, H_MIN,
                                      a["id"], "l", True))
            else:  # side：横轴 = 模型 y（进深）
                if a["runs"] == "X":
                    sx = mx(a["coord"])
                    if x + 6 <= sx <= x + w - 9:
                        prims.append(("auxline", sx, y + 3, sx, y + h - 3))
                        prims.append(("text", sx + 0.9, y + h - 7.2, H_MIN,
                                      a["id"], "l", True))

        # 图名 + 双下划线，比例注右侧〔6.0.3〕
        _fig_name(prims, ccx, y + 6.5, VIEW_LABELS[name], scale_txt)

    _title_block(prims, spec, scale_txt)
    return prims


def _fig_name(prims: list, cx: float, y: float, text: str, scale_txt: str) -> None:
    """图名下方一粗一细双横线，比例注写在图名右侧、字高小一号〔6.0.3〕。"""
    w = len(text) * H_NAME  # CJK 字符宽 ≈ 1em
    prims.append(("text", cx, y, H_NAME, text, "c", False))
    prims.append(("line", cx - w / 2, y - 1.4, cx + w / 2, y - 1.4, W_THICK, False))
    prims.append(("line", cx - w / 2, y - 2.3, cx + w / 2, y - 2.3, W_MED, False))
    prims.append(("text", cx + w / 2 + 2.0, y, H_INFO, scale_txt, "l", False))


def _title_block(prims: list, spec: dict, scale_txt: str) -> None:
    """标题栏（右下角，简化版〔3.2.2〕）：外框 b、分格 0.5b〔表 4.0.4〕。"""
    tx, ty = TB_X, TB_Y
    m0 = spec["members"][0] if spec["members"] else None

    prims.append(("rect", tx, ty, TB_W, TB_H, W_THICK, False))
    # 水平分格：图名 / 图号+编码版本 / 比例+日期
    for d in (ty + 10, ty + 20):
        prims.append(("line", tx, d, tx + TB_W, d, W_MED, False))
    # 垂直分格：中列分开 图号|编码版本 与 比例|日期
    mid = tx + TB_W / 2
    for d in (ty + 10, ty + 20):
        prims.append(("line", mid, d, mid, d + 10, W_MED, False))

    # 图名（5mm，居中）
    title = f"{m0['name']}柱网详图" if m0 else "CHBIM Prototype V1"
    prims.append(("text", tx + TB_W / 2, ty + 23.0, H_NAME, title, "c", False))

    # 图号 | 编码体系版本（2.5mm）
    prims.append(("text", tx + 3, ty + 12.2, H_MIN, f"图号  {SHEET_NO}", "l", False))
    prims.append(("text", mid + 3, ty + 12.2, H_MIN, f"版本  {CODING_VERSION}", "l", False))

    # 比例 | 日期（2.5mm）
    prims.append(("text", tx + 3, ty + 2.2, H_MIN, f"比例  {scale_txt}", "l", False))
    prims.append(("text", mid + 3, ty + 2.2, H_MIN, f"日期  {spec['generated']}", "l", False))


def _poly_bbox(polys: list) -> tuple | None:
    xs = [p[0] for poly in polys for p in poly]
    ys = [p[1] for poly in polys for p in poly]
    if not xs:
        return None
    return (min(xs), min(ys), max(xs), max(ys))


# ---------------------------------------------------------------- SVG 渲染

_SVG_FONT = "Songti SC,Songti TC,Noto Serif SC,serif"


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
                       f'x2="{p[3]:.2f}" y2="{fy(p[4]):.2f}" stroke="black" '
                       f'stroke-width="{W_THIN:g}" stroke-linecap="round" '
                       f'stroke-dasharray="{" ".join(str(v) for v in AXIS_DASH)}"/>')
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
            c.setDash(list(AXIS_DASH)); c.setStrokeGray(0)
            c.setLineWidth(W_THIN); c.setLineCap(1)  # 圆头 → 点画线的"点"
            c.line(p[1], p[2], p[3], p[4])
            c.setLineCap(0)
        elif k == "line":
            c.setDash([]); c.setStrokeGray(0.55 if p[6] else 0); c.setLineWidth(p[5])
            c.line(p[1], p[2], p[3], p[4])
        elif k == "rect":
            c.setDash([]); c.setStrokeGray(0.55 if p[6] else 0); c.setLineWidth(p[5])
            c.rect(p[1], p[2], p[3], p[4], stroke=1, fill=0)
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


GRAY = 0.45  # 次要文字灰度
