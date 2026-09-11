"""tests/test_server.py —— Web 工作台 HTTP 层测试

在后台线程起真实的 ThreadingHTTPServer，走完整 HTTP 栈验证端点契约与错误分级。

本文件的存在理由：T1 修复曾在 `/api/layout` 中引用尚未赋值的局部变量 `D`，
55 例业务测试全绿仍漏掉它在真实请求下返回 500——HTTP 层必须有独立回归网。
"""
import json
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

import app.server as server_mod
from app.server import Handler


class ServerCase(unittest.TestCase):
    """共享一个后台 HTTP 服务；产物目录重定向到临时目录，不写仓库 build/。"""

    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory()
        cls._orig_build = server_mod.BUILD
        server_mod.BUILD = Path(cls._tmp.name) / "build"
        cls.httpd = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        cls.port = cls.httpd.server_address[1]
        cls.thread = threading.Thread(target=cls.httpd.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()
        cls.httpd.server_close()
        cls.thread.join(timeout=5)
        server_mod.BUILD = cls._orig_build
        cls._tmp.cleanup()

    def _url(self, path):
        return f"http://127.0.0.1:{self.port}{path}"

    def get(self, path):
        try:
            with urllib.request.urlopen(self._url(path), timeout=90) as r:
                return r.status, r.read()
        except urllib.error.HTTPError as e:
            return e.code, e.read()

    def post(self, path, payload=None, raw=None):
        data = raw if raw is not None else json.dumps(payload).encode()
        req = urllib.request.Request(
            self._url(path), data=data,
            headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=180) as r:
                return r.status, r.read()
        except urllib.error.HTTPError as e:
            return e.code, e.read()


class TestStaticAndData(ServerCase):
    def test_index_is_html(self):
        code, body = self.get("/")
        self.assertEqual(code, 200)
        self.assertIn(b"CHBIM", body)

    def test_api_data_shape(self):
        code, body = self.get("/api/data")
        self.assertEqual(code, 200)
        data = json.loads(body)
        self.assertTrue(data["axes"])
        self.assertTrue(data["member_types"])
        self.assertEqual(data["default_D"], 300)

    def test_unknown_path_404(self):
        self.assertEqual(self.get("/nope")[0], 404)

    def test_path_traversal_blocked(self):
        """路径穿越不得读到仓库文件（403 拒绝或 404 未命中，都不能是 200）。"""
        code, body = self.get("/files/../Makefile")
        self.assertIn(code, (403, 404))
        self.assertNotIn(b"PY ?=", body)


class TestLayoutEndpoint(ServerCase):
    def test_endpoint_end_to_end(self):
        """「生成」主链路：请求 D 同时进数据层与构建（T1 回归点），产物齐备。"""
        code, body = self.post("/api/layout",
                               {"D": 250, "mian_kuo": 3, "jin_shen": 3})
        self.assertEqual(code, 200, body[:300])
        d = json.loads(body)
        for key in ("stl", "svg", "pdf"):
            self.assertIn(key, d["files"])
        self.assertEqual(len(d["spec"]["members"]), 16)     # 4 列 × 4 排
        self.assertEqual(d["spec"]["D"], 250.0)
        self.assertEqual(d["layout"]["mian_kuo"], 3)
        gen = server_mod.BUILD / "generated" / "axes.json"
        self.assertEqual(json.loads(gen.read_text())["module"]["D_mm"], 250)

    def test_even_bays_rejected_400(self):
        code, body = self.post("/api/layout",
                               {"D": 300, "mian_kuo": 4, "jin_shen": 3})
        self.assertEqual(code, 400, body[:300])
        self.assertIn("奇数", json.loads(body)["error"])

    def test_missing_d_rejected_400(self):
        """数据层 D 落 null 且请求不给 D → fail fast，不再暗含 300。"""
        code, body = self.post("/api/layout", {"mian_kuo": 3, "jin_shen": 3})
        self.assertEqual(code, 400, body[:300])
        self.assertIn("未提供 D", json.loads(body)["error"])

    def test_malformed_json_400(self):
        code, body = self.post("/api/layout", raw=b"{not json")
        self.assertEqual(code, 400, body[:300])


if __name__ == "__main__":
    unittest.main()
