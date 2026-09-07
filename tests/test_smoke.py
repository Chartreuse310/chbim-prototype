"""tests/test_smoke.py —— 端到端冒烟测试（调用 OpenSCAD CLI）

约 5-8 秒。验证：编译、3D 导出、三视图 SVG 解析、图纸排版、
预览 PNG 全部成功且非空。
"""
import tempfile
import unittest
from pathlib import Path

from bridge import pipeline


class TestSmoke(unittest.TestCase):
    def test_end_to_end(self):
        with tempfile.TemporaryDirectory() as td:
            result = pipeline.build(D=300, build_dir=Path(td))
            files = result["files"]
            for key, p in files.items():
                self.assertTrue(Path(p).exists(), f"{key} 不存在: {p}")
                self.assertGreater(Path(p).stat().st_size, 200, f"{key} 文件过小: {p}")


if __name__ == "__main__":
    unittest.main()
