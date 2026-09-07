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
        p = resolver.parse_axis_id("JIAN_0")
        self.assertEqual(p["kind"], "JIAN")
        self.assertEqual(p["direction"], None)
        self.assertEqual(p["ordinal"], "0")
        self.assertEqual(p["inner_outer"], None)

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
        self.assertEqual(ax["CAO_Fo"]["coord"], -600)   # F=南，2D=600
        self.assertEqual(ax["CAO_Bo"]["coord"], 600)    # B=北
        self.assertEqual(ax["JIAN_L1"]["coord"], 1200)  # L=东，4D
        self.assertEqual(ax["JIAN_0"]["coord"], 0)
        self.assertEqual(ax["TUAN_0"]["coord"], 0)
        self.assertEqual(ax["TUAN_F1"]["coord"], -300)  # 前第1槫缝在南侧
        self.assertEqual(ax["CAO_Fo"]["runs"], "X")
        self.assertEqual(ax["JIAN_L1"]["runs"], "Y")

    def test_cao_direction_runs(self):
        """CAO 走向由方向字母决定：F/B 沿 X（定位 y），L/R 沿 Y（定位 x）〔坐北朝南〕。"""
        spec = resolver.resolve_data({
            "axes": [
                {"id": "CAO_Fo", "kind": "CAO", "distance": "2D"},
                {"id": "CAO_Bo", "kind": "CAO", "distance": "2D"},
                {"id": "CAO_Lo", "kind": "CAO", "distance": "3D"},
                {"id": "CAO_Ro", "kind": "CAO", "distance": "3D"},
            ],
            "default_D": 300, "module_note": "", "member_types": [],
        }, D=300)
        ax = {a["id"]: a for a in spec["axes"]}
        self.assertEqual(ax["CAO_Fo"]["runs"], "X")
        self.assertEqual(ax["CAO_Bo"]["runs"], "X")
        self.assertEqual(ax["CAO_Lo"]["runs"], "Y")   # 东侧槽缝，南北向线
        self.assertEqual(ax["CAO_Ro"]["runs"], "Y")   # 西侧槽缝
        self.assertEqual(ax["CAO_Lo"]["coord"], 900)  # L=东=+X
        self.assertEqual(ax["CAO_Ro"]["coord"], -900) # R=西=−X

    def test_members_intersection(self):
        yz = {m["id"]: m for m in self.spec["members"]}
        self.assertEqual(yz["yanzhu_01"]["x"], 1200)    # JIAN_L1（东）
        self.assertEqual(yz["yanzhu_01"]["y"], -600)    # CAO_Fo（南）
        self.assertEqual(yz["yanzhu_01"]["height_mm"], 3300.0)
        self.assertEqual(yz["yanzhu_01"]["diameter_mm"], 300.0)
        self.assertEqual(yz["yanzhu_04"]["y"], 600)     # CAO_Bo（北）

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
                    {"id": "CAO_Bo", "kind": "CAO", "distance": "2D"},
                    {"id": "JIAN_L1", "kind": "JIAN", "distance": "4D"},
                ],
                "default_D": 300,
                "module_note": "",
                "member_types": [{"type": "yanzhu", "name": "檐柱", "category": "柱",
                    "params": {"height": "11D", "diameter": "1D"},
                    "instances": [{"id": "yanzhu_01", "axes": ["CAO_Fo", "CAO_Bo"]}]}],
            }, D=300)
        self.assertIn("交点定位", str(cm.exception))


if __name__ == "__main__":
    unittest.main()
