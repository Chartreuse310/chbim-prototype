# CHBIM —— 常用命令入口
#
# 用法：
#   make build D=300    生成模型与图纸到 build/
#   make serve          启动 Web 工作台（默认 http://127.0.0.1:8765）
#   make test           跑全部测试
#   make snapshot       将当前 build/ 示例产物快照到 docs/images/（README 展示用）
#   make clean          清理 build/
#
# 依赖 reportlab（PDF 图纸）与 fontTools（SVG 字体子集嵌入）。默认 PY 指向
# managed venv（含上述依赖），可 PY=/path/to/your/python 覆盖。

PY ?= /Users/z/.workbuddy/binaries/python/envs/default/bin/python3
D  ?= 300
PORT ?= 8765

.PHONY: build serve test snapshot clean

build:
	$(PY) -m bridge.pipeline --D $(D)

serve:
	CHBIM_PORT=$(PORT) $(PY) -m app.server

test:
	$(PY) -m unittest discover -s tests -v

snapshot: build
	cp build/sheet.svg docs/images/sheet-sample.svg
	cp build/preview.png docs/images/preview-sample.png
	@echo "快照已刷新：docs/images/{sheet-sample.svg, preview-sample.png}"

clean:
	rm -rf build
