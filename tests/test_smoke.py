"""tests/test_smoke.py —— 端到端冒烟测试（调用 OpenSCAD CLI）

一次构建覆盖全链路：数据解析 → codegen → STL/OBJ 导出 → 三视图投影 →
图纸 SVG/PDF 排版。断言不止「文件存在」，还校验格式与内容可用。
约 3-8 秒。
"""
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from bridge import pipeline


class TestSmoke(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory()
        cls.result = pipeline.build(D=300, build_dir=Path(cls._tmp.name))
        cls.files = {k: Path(v) for k, v in cls.result["files"].items()}

    @classmethod
    def tearDownClass(cls):
        cls._tmp.cleanup()

    def test_core_artifacts_exist_and_non_empty(self):
        for key in ("stl", "svg", "pdf"):
            self.assertIn(key, self.files, f"缺少关键产物：{key}")
        for key, p in self.files.items():
            self.assertTrue(p.is_file(), f"{key} 不存在：{p}")
            self.assertGreater(p.stat().st_size, 1024, f"{key} 文件过小：{p}")

    def test_spec_matches_static_sample(self):
        """静态示例：6 根檐柱，D=300，柱高 11D=3300mm。"""
        spec = self.result["spec"]
        self.assertEqual(spec["D"], 300.0)
        self.assertEqual(len(spec["members"]), 6)
        self.assertEqual({m["height_mm"] for m in spec["members"]}, {3300.0})
        self.assertEqual(spec["bbox"]["zmax"], 3300.0)

    def test_stl_is_ascii_solid(self):
        self.assertEqual(self.files["stl"].read_bytes()[:5].lower(), b"solid")

    def test_obj_has_vertex_lines(self):
        obj = self.files.get("obj")
        if obj is None:
            self.skipTest("OBJ 未导出（OpenSCAD 版本过旧且无 trimesh 兜底）")
        text = obj.read_text(encoding="utf-8", errors="replace")
        self.assertRegex(text, r"(?m)^v ")

    def test_sheet_svg_is_labelled_drawing(self):
        ET.parse(self.files["svg"])              # 非法 XML 会直接抛异常
        text = self.files["svg"].read_text(encoding="utf-8")
        self.assertIn("<polygon", text)
        for label in ("正立面图", "侧立面图", "平面图", "CHBIM-01"):
            self.assertIn(label, text)

    def test_pdf_header(self):
        self.assertEqual(self.files["pdf"].read_bytes()[:4], b"%PDF")

    def test_preview_png_if_rendered(self):
        png = self.files.get("preview")
        if png is None:
            self.skipTest("离屏渲染不可用，预览 PNG 已跳过（非关键产物）")
        self.assertEqual(png.read_bytes()[:4], b"\x89PNG")


if __name__ == "__main__":
    unittest.main()
