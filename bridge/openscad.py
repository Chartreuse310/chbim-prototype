"""bridge/openscad.py —— OpenSCAD CLI 封装

仅在进程级调用 OpenSCAD 可执行文件，本项目代码不链接其任何库，
因此不受 GPL 传染（见 docs/adr/ADR-0005）。
"""
from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

_MAC_BIN = "/Applications/OpenSCAD.app/Contents/MacOS/OpenSCAD"


def find_binary() -> str:
    if os.environ.get("OPENSCAD_BIN"):
        return os.environ["OPENSCAD_BIN"]
    if shutil.which("openscad"):
        return "openscad"
    if Path(_MAC_BIN).exists():
        return _MAC_BIN
    raise FileNotFoundError(
        "未找到 OpenSCAD。请安装（openscad.org），或设置环境变量 OPENSCAD_BIN 指向可执行文件")


def export(scad: Path, out: Path, extra: tuple = ()) -> Path:
    """调用 OpenSCAD 导出（按扩展名决定格式：stl/obj/svg/png…）。"""
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    cmd = [find_binary(), "-o", str(out), *extra, str(scad)]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
    if proc.returncode != 0 or not out.exists():
        raise RuntimeError(
            f"OpenSCAD 导出失败（{out.name}）:\n{proc.stderr[-800:]}")
    return out


def render_png(scad: Path, out: Path, eye: tuple, center: tuple = (0, 0, 0),
               imgsize: tuple = (1280, 960)) -> Path:
    extra = (
        f"--camera={','.join(str(v) for v in eye)},{','.join(str(v) for v in center)}",
        "--viewall", "--autocenter",
        f"--imgsize={imgsize[0]},{imgsize[1]}",
        "--projection=perspective",
        "--colorscheme=Tomorrow",
    )
    return export(scad, out, extra)
