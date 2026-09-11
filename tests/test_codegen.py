"""tests/test_codegen.py —— 代码生成层单元测试（快速，不调用 OpenSCAD）

验证 bridge/codegen.py 把模型规格写成 build/ 下的 .scad：
构件与轴线逐实例一行、core/ 以相对路径引用（build 目录可任意位置）、
模型入口与三视图投影文件齐备。
"""
import tempfile
import unittest
from pathlib import Path

from bridge import codegen, resolver

ROOT = Path(__file__).resolve().parents[1]


class TestEmit(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.spec = resolver.resolve(ROOT / "data", D=300)
        cls._tmp = tempfile.TemporaryDirectory()
        cls.dir = Path(cls._tmp.name)
        cls.out = codegen.emit(cls.spec, cls.dir, ROOT)

    @classmethod
    def tearDownClass(cls):
        cls._tmp.cleanup()

    def _read(self, name: str) -> str:
        return (self.dir / name).read_text(encoding="utf-8")

    def test_one_call_per_member(self):
        body = self._read("model_body.scad")
        self.assertEqual(body.count("translate(["), len(self.spec["members"]))
        self.assertIn("yanzhu(D=300.000, H=3300.000)", body)

    def test_axis_calls_split_by_runs(self):
        """走向决定画法：定位 y 的缝用 axis_x，定位 x 的缝用 axis_y。"""
        body = self._read("model_body.scad")
        n_x = sum(1 for a in self.spec["axes"] if a["runs"] == "X")
        n_y = sum(1 for a in self.spec["axes"] if a["runs"] == "Y")
        self.assertEqual(body.count("axis_x("), n_x)
        self.assertEqual(body.count("axis_y("), n_y)

    def test_core_path_is_relative(self):
        """生成的 .scad 要以相对路径引 core/，否则换个 build 目录就断。"""
        body = self._read("model_body.scad")
        uses = [ln[len("use <"):-1] for ln in body.splitlines()
                if ln.startswith("use <")]
        self.assertEqual(len(uses), 2)
        for p in uses:
            self.assertFalse(p.startswith("/"), f"绝对路径：{p}")
            self.assertIn("core/", p.replace("\\", "/"))

    def test_model_entry_includes_body(self):
        model = self._read("model.scad")
        self.assertIn("include <model_body.scad>", model)
        self.assertIn("body();", model)

    def test_view_files_use_projection(self):
        self.assertIn("projection()", self._read("view_front.scad"))
        self.assertIn("rotate([0, -90, 0])", self._read("view_side.scad"))
        self.assertIn("projection() body();", self._read("view_top.scad"))

    def test_return_value_and_file_set(self):
        self.assertEqual(Path(self.out["entry"]).name, "model.scad")
        self.assertEqual(sorted(self.out["views"]), ["front", "side", "top"])
        self.assertEqual(
            sorted(p.name for p in self.dir.glob("*.scad")),
            ["model.scad", "model_body.scad",
             "view_front.scad", "view_side.scad", "view_top.scad"])


if __name__ == "__main__":
    unittest.main()
