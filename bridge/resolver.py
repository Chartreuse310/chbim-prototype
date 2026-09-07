"""bridge/resolver.py —— 数据层解析：缝编码 → 空间坐标

职责（对应 ADR-0001 / ADR-0004）：
1. 读取 data/ 下的轴线与构件 JSON
2. 求值模数表达式（"11D" → mm 数值，D = 柱径）
3. 按「交点定位」语义将构件实例解析为 (x, y) 坐标：
   构件所属缝须一横（CAO/TUAN 类，定位 y）一纵（JIAN 类，定位 x），
   两缝交点即构件中心。
"""
from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path

_EXPR_RE = re.compile(r"^\s*(\d+(?:\.\d+)?)\s*D\s*$")
_SUFFIX_RE = re.compile(r"^([FBLR]?)(\d*)([io]?)$")

# 缝类型 → 平面走向：
#   RUNS_X：沿 X（面阔）延伸、位置定义在 Y（前后）—— 槽缝、槫缝
#   RUNS_Y：沿 Y（进深）延伸、位置定义在 X（左右）—— 间缝
RUNS_X = {"CAO", "TUAN", "TUANJIAN"}
RUNS_Y = {"JIAN"}
_KNOWN = {"CAO", "JIAN", "FU", "TUAN", "TUANJIAN", "PUZUO", "TIAO"}

# 朝向字母的符号因缝走向而异：
#   X 走向（CAO/TUAN 等，定位 y）：F=+Y, B=−Y, R=−Y（rear = 后）
#   Y 走向（JIAN，定位 x）：L=−X, R=+X
_SIGN_XRUN = {"F": 1, "B": -1, "R": -1}
_SIGN_YRUN = {"L": -1, "R": 1}


def eval_expr(expr, D: float) -> float:
    """求值模数表达式："11D" → 11×D；"0"/"250" → 原值（mm）。"""
    if isinstance(expr, (int, float)):
        return float(expr)
    m = _EXPR_RE.match(str(expr))
    if m:
        return float(m.group(1)) * D
    try:
        return float(expr)
    except (TypeError, ValueError):
        raise ValueError(f"无法求值的模数表达式: {expr!r}") from None


def parse_axis_id(axis_id: str) -> dict:
    """解析缝编码：CAO_Fo → kind=CAO / direction=F / inner_outer=o。"""
    for k in sorted(_KNOWN, key=len, reverse=True):
        if axis_id.startswith(k + "_"):
            kind, suffix = k, axis_id[len(k) + 1:]
            break
    else:
        raise ValueError(f"未知缝编码: {axis_id}")
    m = _SUFFIX_RE.match(suffix)
    if not m:
        raise ValueError(f"无法解析缝编码后缀: {axis_id}（{suffix}）")
    return {
        "kind": kind,
        "direction": m.group(1) or None,
        "ordinal": m.group(2) or None,
        "inner_outer": m.group(3) or None,
    }


def resolve_axis(axis: dict, D: float) -> dict:
    p = parse_axis_id(axis["id"])
    kind = p["kind"]
    if kind not in RUNS_X and kind not in RUNS_Y:
        raise NotImplementedError(
            f"缝类型 {kind} 的平面走向尚未定义（FU/PUZUO/TIAO 留待后续版本）")
    dist = eval_expr(axis.get("distance", 0), D)
    sign_map = _SIGN_XRUN if kind in RUNS_X else _SIGN_YRUN
    coord = dist * sign_map.get(p["direction"], 0)
    return {
        "id": axis["id"], "kind": kind,
        "runs": "X" if kind in RUNS_X else "Y",
        "coord": coord, "direction": p["direction"],
        "inner_outer": p["inner_outer"], "note": axis.get("note", ""),
    }


def load_data(data_dir: Path) -> dict:
    """读取数据层原始 JSON（供交互层展示用）。"""
    data_dir = Path(data_dir)
    axes_doc = json.loads((data_dir / "axes.json").read_text(encoding="utf-8"))
    member_types = [
        json.loads(f.read_text(encoding="utf-8"))
        for f in sorted((data_dir / "members").glob("*.json"))
    ]
    return {
        "axes": axes_doc.get("axes", []),
        "default_D": axes_doc.get("module", {}).get("D_mm"),
        "module_note": axes_doc.get("module", {}).get("note", ""),
        "member_types": member_types,
    }


def resolve(data_dir: Path, D: float | None = None) -> dict:
    """读取数据层目录 → 完整模型规格（坐标 mm）。"""
    return resolve_data(load_data(Path(data_dir)), D=D)


def resolve_data(data: dict, D: float | None = None) -> dict:
    """直接接受 load_data 返回的 dict，跳过文件读取（便于测试与编程调用）。"""
    D_mm = float(D) if D else float(data["default_D"])
    axes = [resolve_axis(a, D_mm) for a in data["axes"]]
    axes_by_id = {a["id"]: a for a in axes}

    members = []
    for mt in data["member_types"]:
        params = {}
        for k, v in mt.get("params", {}).items():
            try:
                params[k] = eval_expr(v, D_mm)
            except ValueError:
                params[k] = v  # 非数值参数原样保留
        height = params.get("height", 0.0)
        diameter = params.get("diameter", 0.0)
        for inst in mt.get("instances", []):
            xs, ys, missing = [], [], []
            for aid in inst["axes"]:
                ax = axes_by_id.get(aid)
                if ax is None:
                    missing.append(aid)
                    continue
                (xs if ax["runs"] == "Y" else ys).append(ax["coord"])
            if missing:
                raise ValueError(f"{inst['id']}: 未定义的缝 {missing}")
            if len(xs) != 1 or len(ys) != 1:
                raise ValueError(
                    f"{inst['id']}: 交点定位要求一横一纵缝，实际 横×{len(ys)} 纵×{len(xs)}"
                    f"（axes={inst['axes']}）。整排布置的紧凑写法见 docs/coding-system.md 待讨论项")
            members.append({
                "id": inst["id"], "type": mt["type"], "name": mt["name"],
                "category": mt["category"], "x": xs[0], "y": ys[0],
                "height_mm": height, "diameter_mm": diameter,
            })

    spec = {
        "D": D_mm, "axes": axes, "members": members,
        "generated": date.today().isoformat(),
        "bbox": _bbox(members),
    }
    return spec


def _bbox(members: list) -> dict:
    if not members:
        return {k: 0.0 for k in ("xmin", "xmax", "ymin", "ymax", "zmin", "zmax")}
    xs = [(m["x"], m["diameter_mm"] / 2) for m in members]
    ys = [(m["y"], m["diameter_mm"] / 2) for m in members]
    return {
        "xmin": min(x - r for x, r in xs), "xmax": max(x + r for x, r in xs),
        "ymin": min(y - r for y, r in ys), "ymax": max(y + r for y, r in ys),
        "zmin": 0.0, "zmax": max(m["height_mm"] for m in members),
    }
