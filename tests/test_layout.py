"""tests/test_layout.py —— 间数生成柱网（G17）单元测试

规律（docs/coding-system.md「间数生成柱网」）：
    X 间 = X+1 柱/排；仅奇数间；间宽自明间每向外一间 ×0.8；
    柱高 = 0.8×明间面阔；JIAN_L1..Ln/R1..Rn；CAO 外圈 Fo/Bo、内圈 F1..Fn-1。
"""
import unittest

from bridge.layout import (bay_widths, column_offsets, generate_layout,
                           write_layout, _fmt_d)


class TestBayWidths(unittest.TestCase):
    def test_ratio(self):
        ws = bay_widths(8.0, 4)
        self.assertEqual(ws, [8.0, 6.4, 5.12, 4.096])

    def test_offsets_cumulative(self):
        # 明间 8D：柱位 4, 4+6.4=10.4, 10.4+5.12=15.52
        self.assertEqual(column_offsets(8.0, 3), [4.0, 10.4, 15.52])

    def test_fmt_d(self):
        self.assertEqual(_fmt_d(4.0), "4D")
        self.assertEqual(_fmt_d(10.4), "10.4D")
        self.assertEqual(_fmt_d(15.52), "15.52D")


class TestGenerateLayout(unittest.TestCase):
    def setUp(self):
        self.data = generate_layout(5, 3)
        self.axes = {a["id"]: a for a in self.data["axes"]}

    def test_member_count(self):
        inst = self.data["member_types"][0]["instances"]
        self.assertEqual(len(inst), (5 + 1) * (3 + 1))  # 6 列 × 4 排

    def test_jian_seams(self):
        # 5 间 → 3 柱/侧，自明间向外 4D / 10.4D / 15.52D，无 JIAN_0（无中柱）
        self.assertEqual(self.axes["JIAN_L1"]["distance"], "4D")
        self.assertEqual(self.axes["JIAN_L2"]["distance"], "10.4D")
        self.assertEqual(self.axes["JIAN_L3"]["distance"], "15.52D")
        self.assertNotIn("JIAN_0", self.axes)
        self.assertNotIn("JIAN_Lo", self.axes)

    def test_cao_seams(self):
        # 3 间 → 内圈 F1/B1（金槽）、外圈 Fo/Bo（檐槽）
        self.assertEqual(self.axes["CAO_F1"]["distance"], "4D")
        self.assertEqual(self.axes["CAO_Fo"]["distance"], "10.4D")
        self.assertEqual(self.axes["CAO_Bo"]["distance"], "10.4D")
        self.assertNotIn("CAO_F2", self.axes)

    def test_distance_positive_magnitude(self):
        # 数据层惯例：distance 存正数幅值，符号由方向字母施加
        for a in self.data["axes"]:
            self.assertFalse(a["distance"].startswith("-"),
                             f"{a['id']} 距离应为正幅值")

    def test_height_rule(self):
        # 柱高 = 0.8 × 明间面阔 = 0.8 × 8D = 6.4D
        self.assertEqual(self.data["member_types"][0]["params"]["height"],
                         "6.4D")

    def test_height_uniform_via_resolver(self):
        from bridge import resolver
        spec = resolver.resolve_data(self.data, D=300)
        heights = {m["height_mm"] for m in spec["members"]}
        self.assertEqual(heights, {1920.0})  # 6.4 × 300

    def test_coordinates_symmetric(self):
        from bridge import resolver
        spec = resolver.resolve_data(self.data, D=300)
        xs = sorted({round(m["x"]) for m in spec["members"]})
        ys = sorted({round(m["y"]) for m in spec["members"]})
        self.assertEqual(xs, [-4656, -3120, -1200, 1200, 3120, 4656])
        self.assertEqual(ys, [-3120, -1200, 1200, 3120])

    def test_ids_sequential(self):
        inst = self.data["member_types"][0]["instances"]
        self.assertEqual(inst[0]["id"], "yanzhu_01")
        self.assertEqual([i["id"] for i in inst],
                         [f"yanzhu_{k:02d}" for k in range(1, 25)])

    def test_even_bays_rejected(self):
        with self.assertRaises(ValueError):
            generate_layout(4, 3)
        with self.assertRaises(ValueError):
            generate_layout(5, 2)

    def test_min_bays_rejected(self):
        with self.assertRaises(ValueError):
            generate_layout(1, 3)

    def test_custom_ming_w(self):
        d = generate_layout(3, 3, ming_kuo_w="10D", ming_shen_w="8D")
        axes = {a["id"]: a["distance"] for a in d["axes"]}
        self.assertEqual(axes["JIAN_L1"], "5D")        # 10/2
        self.assertEqual(axes["JIAN_L2"], "13D")       # 5 + 0.8×10=8 → 13（外圈，JIAN 无 o）
        self.assertEqual(axes["CAO_Fo"], "10.4D")      # 4 + 0.8×8（外圈檐槽）
        self.assertEqual(d["member_types"][0]["params"]["height"], "8D")

    def test_custom_ming_w_rejects_non_d(self):
        with self.assertRaises(ValueError):
            generate_layout(3, 3, ming_kuo_w="2400")


if __name__ == "__main__":
    unittest.main()


class TestWriteLayout(unittest.TestCase):
    """T1：write_layout 的 D_mm 语义——显式传入或 null（fail fast），不再暗含 300。"""

    def setUp(self):
        import tempfile
        self._tmp = tempfile.TemporaryDirectory()
        from pathlib import Path
        self.out = Path(self._tmp.name) / "gen"
        self.data = generate_layout(3, 3)

    def tearDown(self):
        self._tmp.cleanup()

    def test_d_mm_explicit(self):
        import json
        from bridge import resolver
        write_layout(self.data, self.out, D_mm=250)
        module = json.loads((self.out / "axes.json").read_text())["module"]
        self.assertEqual(module["D_mm"], 250)
        spec = resolver.resolve(self.out)          # 用数据层缺省 D
        self.assertEqual(spec["D"], 250.0)

    def test_d_mm_none_writes_null(self):
        import json
        write_layout(self.data, self.out)          # 未传 D_mm
        module = json.loads((self.out / "axes.json").read_text())["module"]
        self.assertIsNone(module["D_mm"])

    def test_d_missing_everywhere_fails_fast(self):
        from bridge import resolver
        write_layout(self.data, self.out)          # null + 不给 D
        with self.assertRaises(ValueError):
            resolver.resolve(self.out)
        spec = resolver.resolve(self.out, D=300)   # 显式给 D → 正常
        self.assertEqual(spec["D"], 300.0)
