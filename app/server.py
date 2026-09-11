"""app/server.py —— CHBIM Web 工作台（仅依赖 Python 标准库）

启动：python -m app.server
默认端口 8765（环境变量 CHBIM_PORT 可覆盖）。
"""
from __future__ import annotations

import json
import mimetypes
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from bridge import openscad, pipeline, resolver

ROOT = Path(__file__).resolve().parents[1]
STATIC = ROOT / "app" / "static"
BUILD = ROOT / "build"

mimetypes.add_type("model/stl", ".stl")
mimetypes.add_type("model/obj", ".obj")


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):  # 静默标准日志（启动期看到一次即可）
        pass

    # --------------------------------------------------------- 工具

    def _send(self, code: int, body, ctype: str = "application/json; charset=utf-8"):
        if isinstance(body, (dict, list)):
            body = json.dumps(body, ensure_ascii=False)
        if isinstance(body, str):
            body = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _serve_file(self, path: Path, ctype: str | None = None):
        if not path.is_file():
            return self._send(404, {"error": "not found"})
        mt = ctype or mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        return self._send(200, path.read_bytes(), mt)

    # --------------------------------------------------------- GET

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/":
            return self._serve_file(STATIC / "index.html", "text/html; charset=utf-8")
        if path == "/api/data":
            return self._send(200, resolver.load_data(ROOT / "data"))
        if path.startswith("/files/"):
            name = path[len("/files/"):]
            # 防御：拒绝路径穿越
            target = (BUILD / name).resolve()
            if BUILD.resolve() not in target.parents and target != BUILD:
                return self._send(403, {"error": "forbidden"})
            return self._serve_file(target)
        # 静态资源
        if path.startswith("/static/"):
            return self._serve_file(STATIC / path[len("/static/"):])
        return self._send(404, {"error": "not found"})

    # --------------------------------------------------------- POST

    def do_POST(self):
        path = urlparse(self.path).path
        if path == "/api/build":
            return self._handle_build(self._read_body())
        if path == "/api/layout":
            return self._handle_layout(self._read_body())
        return self._send(404, {"error": "not found"})

    def _read_body(self) -> dict:
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length) if length else b"{}"
        try:
            return json.loads(raw.decode("utf-8")) if raw else {}
        except json.JSONDecodeError as e:
            raise ValueError(f"invalid JSON: {e}") from None

    def _handle_build(self, body: dict):
        D = body.get("D")
        try:
            result = pipeline.build(D=float(D) if D else None)
        except Exception as e:
            return self._send(500, {"error": f"{type(e).__name__}: {e}"})
        return self._send(200, result)

    def _handle_layout(self, body: dict):
        """间数生成柱网（G17）：body = {mian_kuo, jin_shen, D?,
        ming_kuo_w?, ming_shen_w?}。生成数据写入 build/generated/
        后走常规构建管线（不覆盖 data/ 静态示例）。"""
        try:
            from bridge import layout
            mian = int(body.get("mian_kuo", 0))
            shen = int(body.get("jin_shen", 0))
            data = layout.generate_layout(
                mian_kuo=mian, jin_shen=shen,
                ming_kuo_w=body.get("ming_kuo_w", layout.DEFAULT_MING_W),
                ming_shen_w=body.get("ming_shen_w", layout.DEFAULT_MING_W))
            gen_dir = BUILD / "generated"
            layout.write_layout(data, gen_dir)
            D = body.get("D")
            result = pipeline.build(D=float(D) if D else None,
                                    data_dir=gen_dir)
            result["layout"] = data["meta"]
        except ValueError as e:      # 间数/明间宽校验失败 → 4xx
            return self._send(400, {"error": str(e)})
        except Exception as e:
            return self._send(500, {"error": f"{type(e).__name__}: {e}"})
        return self._send(200, result)


def main() -> None:
    port = int(os.environ.get("CHBIM_PORT", "8765"))
    addr = ("127.0.0.1", port)
    print(f"CHBIM Web 工作台：http://{addr[0]}:{addr[1]}/")
    try:
        print(f"OpenSCAD：{openscad.find_binary()}")
    except FileNotFoundError as e:
        print(f"[warn] {e}\n        「生成」将不可用；图纸与数据表不受影响。")
    ThreadingHTTPServer(addr, Handler).serve_forever()


if __name__ == "__main__":
    main()
