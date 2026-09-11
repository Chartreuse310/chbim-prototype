"""tests/test_sheet.py —— 图纸排版单元测试

覆盖图元生成（纯函数，与渲染后端无关）、SVG 渲染、PDF 渲染
（缺 reportlab 则跳过）、以及 OpenSCAD 2D SVG 解析。除 PDF 外不触发 OpenSCAD。
"""
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from bridge import resolver
from sheet import compose, views

ROOT = Path(__file__).resolve().parents[1]

# 三个视图各一个 100×100 方框，模拟 projection() 的输出
POLYS = {name: [[(0.0, 0.0), (100.0, 0.0), (100.0, 100.0), (0.0, 100.0)]]
         for name in ("front", "side", "top")}

try:
    import reportlab  # noqa: F401
    HAS_REPORTLAB = True
except ImportError:
    HAS_REPORTLAB = False


class TestBuildPrims(unittest.TestCase):
    """图元层：spec + polys → 与渲染后端无关的图元列表。"""

    @classmethod
    def setUpClass(cls):
        cls.spec = resolver.resolve(ROOT / "data", D=300)
        cls.prims = compose._build_prims(cls.spec, POLYS)

    def _of(self, kind):
        return [p for p in self.prims if p[0] == kind]

    def test_frame_rect(self):
        self.assertIn(("rect", compose.FX0, compose.FY0,
                       compose.FX1 - compose.FX0, compose.FY1 - compose.FY0,
                       compose.W_THICK, False), self._of("rect"))

    def test_view_labels(self):
        texts = [p[4] for p in self._of("text")]
        for label in ("正立面图", "侧立面图", "平面图"):
            self.assertIn(label, texts)

    def test_member_outlines_use_thick_line(self):
        polys = self._of("poly")
        self.assertEqual(len(polys), 3)          # 每视图一个轮廓
        for p in polys:
            self.assertEqual(p[2], compose.W_THICK)

    def test_axes_drawn_as_auxlines(self):
        self.assertTrue(self._of("auxline"))

    def test_title_block(self):
        texts = [p[4] for p in self._of("text")]
        self.assertIn(f"图号  {compose.SHEET_NO}", texts)
        self.assertIn(f"版本  {compose.CODING_VERSION}", texts)
        self.assertIn(f"日期  {self.spec['generated']}", texts)
        self.assertTrue(any(t.startswith("比例  1:") for t in texts), texts)

    def test_everything_inside_frame(self):
        for p in self.prims:
            if p[0] == "rect":
                _, x, y, w, h = p[:5]
                self.assertGreaterEqual(x, compose.FX0)
                self.assertGreaterEqual(y, compose.FY0)
                self.assertLessEqual(x + w, compose.FX1)
                self.assertLessEqual(y + h, compose.FY1)


class TestRenderSvg(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory()
        cls.path = Path(cls._tmp.name) / "sheet.svg"
        spec = resolver.resolve(ROOT / "data", D=300)
        compose._render_svg(compose._build_prims(spec, POLYS), cls.path)

    @classmethod
    def tearDownClass(cls):
        cls._tmp.cleanup()

    def test_well_formed_xml(self):
        ET.parse(self.path)                      # 非法 XML 会直接抛异常

    def test_page_size_is_a4_landscape(self):
        root = ET.parse(self.path).getroot()
        self.assertEqual(root.get("width"), "297mm")
        self.assertEqual(root.get("height"), "210mm")

    def test_contains_shapes_and_labels(self):
        text = self.path.read_text(encoding="utf-8")
        self.assertIn("<polygon", text)
        for label in ("正立面图", "侧立面图", "平面图", compose.SHEET_NO):
            self.assertIn(label, text)


@unittest.skipUnless(HAS_REPORTLAB, "未安装 reportlab，跳过 PDF 渲染测试")
class TestRenderPdf(unittest.TestCase):
    def test_pdf_header_and_size(self):
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "sheet.pdf"
            spec = resolver.resolve(ROOT / "data", D=300)
            compose._render_pdf(compose._build_prims(spec, POLYS), out)
            self.assertEqual(out.read_bytes()[:4], b"%PDF")
            self.assertGreater(out.stat().st_size, 5000)


class TestParseOpenscadSvg(unittest.TestCase):
    """views.parse_openscad_svg：OpenSCAD 2D 导出 → 多边形（y 翻回几何坐标）。"""

    def _parse(self, body: str):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "v.svg"
            p.write_text(f'<svg xmlns="http://www.w3.org/2000/svg">{body}</svg>',
                         encoding="utf-8")
            return views.parse_openscad_svg(p)

    def test_polygon_with_y_flip(self):
        polys = self._parse('<path d="M 0,0 L 100,0 L 100,-100 Z"/>')
        self.assertEqual(polys, [[(0.0, 0.0), (100.0, 0.0), (100.0, 100.0)]])

    def test_multiple_paths(self):
        polys = self._parse('<path d="M 0,0 L 1,0 L 1,1 Z"/>'
                            '<path d="M 5,5 L 6,5 L 6,6 Z"/>')
        self.assertEqual(len(polys), 2)

    def test_missing_z_still_collected(self):
        self.assertEqual(len(self._parse('<path d="M 0,0 L 1,0 L 1,1"/>')), 1)

    def test_empty_svg(self):
        self.assertEqual(self._parse(""), [])


if __name__ == "__main__":
    unittest.main()
