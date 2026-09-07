"""tests/test_resolver.py —— 解析器单元测试（快速、无 OpenSCAD 调用）"""
import unittest
from pathlib import Path

from bridge import resolver

ROOT = Path(__file__).resolve().parents[1]


class TestExpr(unittest.TestCase):
    def test_D_expression(self):
        self.assertEqual(resolver.eval_expr("11D", 300), 3300.0)
        self.assertEqual(resolver.eval_expr("1D", 300), 300.0)
        self.assertEqual(resolver.eval_expr("0", 300), 0.0)
        self.assertEqual(resolver.eval_expr("0.5D", 300), 150.0)
        self.assertEqual(resolver.eval_expr(250, 300), 250.0)

    def test_invalid_expr(self):
        with self.assertRaises(ValueError):
            resolver.eval_expr("abc", 300)


class TestAxisId(unittest.TestCase):
    def test_cao(self):
        p = resolver.parse_axis_id("CAO_Fo")
        self.assertEqual(p["kind"], "CAO")
        self.assertEqual(p["direction"], "F")
        self.assertEqual(p["inner_outer"], "o")

    def test_jian_center(self):
        p = resolver.parse_axis_id("JIAN_C")
        self.assertEqual(p["kind"], "JIAN")
        self.assertEqual(p["direction"], None)
        self.assertEqual(p["inner_outer"], "C")

    def test_tuan(self):
        p = resolver.parse_axis_id("TUAN_F1")
        self.assertEqual(p["kind"], "TUAN")
        self.assertEqual(p["direction"], "F")
        self.assertEqual(p["ordinal"], "1")


class TestResolve(unittest.TestCase):
    def setUp(self):
        self.spec = resolver.resolve(ROOT / "data", D=300)

    def test_axes_coords(self):
        ax = {a["id"]: a for a in self.spec["axes"]}
        self.assertEqual(ax["CAO_Fo"]["coord"], 600)    # 2D = 600
        self.assertEqual(ax["CAO_Ro"]["coord"], -600)
        self.assertEqual(ax["JIAN_L1"]["coord"], -1200) # 4D
        self.assertEqual(ax["JIAN_C"]["coord"], 0)
        self.assertEqual(ax["TUAN_0"]["coord"], 0)
        self.assertEqual(ax["TUAN_F1"]["coord"], 300)
        self.assertEqual(ax["CAO_Fo"]["runs"], "X")
        self.assertEqual(ax["JIAN_L1"]["runs"], "Y")

    def test_members_intersection(self):
        yz = {m["id"]: m for m in self.spec["members"]}
        self.assertEqual(yz["yanzhu_01"]["x"], -1200)   # JIAN_L1
        self.assertEqual(yz["yanzhu_01"]["y"], 600)     # CAO_Fo
        self.assertEqual(yz["yanzhu_01"]["height_mm"], 3300.0)
        self.assertEqual(yz["yanzhu_01"]["diameter_mm"], 300.0)
        self.assertEqual(yz["yanzhu_04"]["y"], -600)    # CAO_Ro

    def test_bbox(self):
        bb = self.spec["bbox"]
        self.assertEqual(bb["xmin"], -1350.0)
        self.assertEqual(bb["xmax"], 1350.0)
        self.assertEqual(bb["ymin"], -750.0)
        self.assertEqual(bb["ymax"], 750.0)
        self.assertEqual(bb["zmax"], 3300.0)

    def test_parallel_axes_rejected(self):
        """交点定位要求一横一纵；两条平行槽缝应报错（开放问题，见 ADR-0004）。"""
        with self.assertRaises(ValueError) as cm:
            resolver.resolve_data({
                "axes": [
                    {"id": "CAO_Fo", "kind": "CAO", "distance": "2D"},
                    {"id": "CAO_Ro", "kind": "CAO", "distance": "2D"},
                    {"id": "JIAN_L1", "kind": "JIAN", "distance": "4D"},
                ],
                "default_D": 300,
                "module_note": "",
                "member_types": [{"type": "yanzhu", "name": "檐柱", "category": "柱",
                    "params": {"height": "11D", "diameter": "1D"},
                    "instances": [{"id": "yanzhu_01", "axes": ["CAO_Fo", "CAO_Ro"]}]}],
            }, D=300)
        self.assertIn("交点定位", str(cm.exception))


if __name__ == "__main__":
    unittest.main()
