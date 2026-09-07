"""bridge/ —— 数据层到几何层的粘合层（Python）

OpenSCAD 语言没有哈希表与字符串解析能力，因此缝编码（如 CAO_Fo）
到空间坐标的解析放在本包完成；几何逻辑全部留在 core/ 的 .scad 库中。
见 docs/adr/ADR-0001。
"""
