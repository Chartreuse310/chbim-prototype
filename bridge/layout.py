"""bridge/layout.py —— 间数生成柱网（G17）

输入「面阔 X 间，进深 Y 间」按 docs/coding-system.md「间数生成柱网」一节的
规律生成 axes + members 数据（与 data/ 数据层同构，可直接喂 resolver）：

    1. X 间 = X+1 根柱/排；仅支持奇数间（奇数间才有明间作基准）
    2. 间宽递减：明间 W，向两侧每出一间 ×0.8（次间 0.8W、梢间 0.64W…）
    3. 柱位：第 k 对柱线 = W/2 + W·(0.8 + … + 0.8^(k-1))，距明间中线
    4. 柱高全柱等高：H = 0.8 × 明间面阔宽
    5. 缝命名：JIAN_L1..Ln/R1..Rn（自明间向外）；CAO 外圈 Fo/Bo、内圈 F1..Fn/B1..Bn

用法：
    from bridge.layout import generate_layout
    data = generate_layout(mian_kuo=5, jin_shen=3)   # → {"axes": [...], "member_types": [...]}
"""
from __future__ import annotations

import re

_MING_RE = re.compile(r"^\s*(\d+(?:\.\d+)?)\s*D\s*$")  # 明间宽仅接受 D 表达式

DEFAULT_MING_W = "8D"  # 明间面阔/进深默认 8D（与静态示例 JIAN ±4D 一致）


def _parse_ming_w(expr: str, label: str) -> float:
    """明间宽表达式 → D 倍数（float）。仅接受 "8D"/"7.5D" 形式。"""
    m = _MING_RE.match(str(expr))
    if not m:
        raise ValueError(
            f"{label} 仅支持 D 表达式（如 \"8D\"），收到 {expr!r}")
    return float(m.group(1))


def bay_widths(ming_w: float, n_bays: int) -> list[float]:
    """自明间向两侧的间宽序列 [W, 0.8W, 0.64W, ...]，共 n_bays 项。"""
    return [round(ming_w * 0.8 ** k, 6) for k in range(n_bays)]


def column_offsets(ming_w: float, n_per_side: int) -> list[float]:
    """一侧柱线距明间中线的偏移（D 倍数，升序）：[W/2, W/2+0.8W, ...]。"""
    offsets, acc = [], 0.0
    for k in range(n_per_side):
        acc += ming_w * 0.8 ** k if k > 0 else 0.0
        offsets.append(round(ming_w / 2 + acc, 6))
    return offsets  # [c1, c2, ...] 升序；另一侧取负


def _fmt_d(x: float) -> str:
    """D 倍数 → 表达式字符串，去尾零：4.0→"4D"，10.4→"10.4D"。"""
    s = f"{x:.6f}".rstrip("0").rstrip(".")
    return f"{s}D"


def _side_ids(kind: str, side: str, n_per_side: int) -> list[str]:
    """一侧缝 ID，自明间向外：JIAN → L1..Ln/R1..Rn；CAO → F1..Fn-1,Fo / B1..Bn-1,Bo。"""
    if kind == "JIAN":
        return [f"JIAN_{side}{k}" for k in range(1, n_per_side + 1)]
    # CAO：最外一圈用 o（檐槽），内圈数字编号（金槽）
    ids = [f"CAO_{side}{k}" for k in range(1, n_per_side)]
    ids.append(f"CAO_{side}o")
    return ids


def generate_layout(mian_kuo: int, jin_shen: int,
                    ming_kuo_w: str = DEFAULT_MING_W,
                    ming_shen_w: str = DEFAULT_MING_W) -> dict:
    """间数 → 柱网数据（axes + member_types，与 data/ 同构）。

    mian_kuo / jin_shen: 间数，必须为奇数且 ≥3
    ming_kuo_w / ming_shen_w: 明间面阔/进深渊宽，D 表达式（默认 "8D"）
    """
    for name, n in (("面阔", mian_kuo), ("进深", jin_shen)):
        if n % 2 == 0 or n < 3:
            raise ValueError(
                f"{name}间数须为 ≥3 的奇数（奇数间才有正中明间作基准），收到 {n}")

    w_kuo = _parse_ming_w(ming_kuo_w, "明间面阔")
    w_shen = _parse_ming_w(ming_shen_w, "明间进深")

    # 面阔方向：JIAN 列缝（沿 Y 走向，定位 x；L=东=+x，R=西=-x）
    # 数据层惯例：distance 存正数幅值，符号由方向字母在 resolver 中施加
    # （_SIGN_XPOS={L:+1,R:-1}、_SIGN_YPOS={F:-1,B:+1}）
    n_j = (mian_kuo + 1) // 2
    off_j = column_offsets(w_kuo, n_j)          # 升序 [c1..cn]，自明间向外
    axes: list[dict] = []
    jian_ids = {}                                # id → 带符号坐标（D 倍数）
    for side, sign in (("L", +1), ("R", -1)):    # L=东=+x，R=西=-x（ADR-0007）
        for aid, off in zip(_side_ids("JIAN", side, n_j), off_j):
            jian_ids[aid] = sign * off
            axes.append({"id": aid, "kind": "JIAN",
                         "distance": _fmt_d(off),
                         "note": "间缝（生成）"})

    # 进深方向：CAO 行缝（沿 X 走向，定位 y；F=南=-y，B=北=+y）
    n_c = (jin_shen + 1) // 2
    off_c = column_offsets(w_shen, n_c)
    cao_ids = {}
    for side, sign in (("F", -1), ("B", +1)):    # F=南=-y，B=北=+y（ADR-0007）
        for aid, off in zip(_side_ids("CAO", side, n_c), off_c):
            cao_ids[aid] = sign * off
            axes.append({"id": aid, "kind": "CAO",
                         "distance": _fmt_d(off),
                         "note": "槽缝（生成）"})

    # 柱高 = 0.8 × 明间面阔（全柱等高，类型级参数）
    height_expr = _fmt_d(0.8 * w_kuo)

    instances = []
    seq = 0
    for cao_id in sorted(cao_ids, key=lambda a: -cao_ids[a]):    # y 降序 = 北→南
        for jian_id in sorted(jian_ids, key=lambda a: -jian_ids[a]):  # x 降序 = 东→西
            seq += 1
            instances.append({"id": f"yanzhu_{seq:02d}",
                              "axes": [cao_id, jian_id]})

    return {
        "axes": axes,
        "member_types": [{
            "type": "yanzhu", "name": "檐柱", "category": "柱",
            "params": {"height": height_expr, "diameter": "1D"},
            "instances": instances,
        }],
        "meta": {
            "mian_kuo": mian_kuo, "jin_shen": jin_shen,
            "ming_kuo_w": ming_kuo_w, "ming_shen_w": ming_shen_w,
            "rule": "间宽自明间每向外一间 ×0.8；柱高 = 0.8×明间面阔；见 docs/coding-system.md G17",
        },
    }


def write_layout(data: dict, out_dir, D_mm: float | None = None) -> None:
    """把生成数据写到目录（axes.json + members/yanzhu.json），供 resolver.load_data。

    D_mm：整体模数（mm）。生成语义上 D 属于调用方（交互层/测试）的输入——
    显式传入则写入数据层缺省值；缺省 None 时写 null，此时 resolve() 必须
    显式给 D，否则 resolver 会以明确报错拒绝（fail fast，不再暗含 300）。
    """
    import json
    from pathlib import Path
    out = Path(out_dir)
    (out / "members").mkdir(parents=True, exist_ok=True)
    axes = {"module": {"D_mm": D_mm,
                       "note": "生成布局；D 由调用方显式传入（null 时 resolve() 必须给 D）"},
            "axes": data["axes"]}
    (out / "axes.json").write_text(
        json.dumps(axes, ensure_ascii=False, indent=2), encoding="utf-8")
    for mt in data["member_types"]:
        (out / "members" / f"{mt['type']}.json").write_text(
            json.dumps(mt, ensure_ascii=False, indent=2), encoding="utf-8")
