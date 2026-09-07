"""sheet/ —— 图纸导出管线

两步走（见 docs/adr/ADR-0003）：
1. 几何：OpenSCAD projection() 生成三视图轮廓 SVG
2. 注释：Python 排版（图名 / 比例尺 / 日期 / 线型 / 辅助线），
   同一份图元列表分别渲染为 SVG 与 PDF（reportlab）。
"""
