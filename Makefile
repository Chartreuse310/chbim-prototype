# CHBIM —— 常用命令入口
#
# 用法：
#   make build D=300    生成模型与图纸到 build/
#   make serve          启动 Web 工作台（默认 http://127.0.0.1:8765）
#   make test           跑全部测试
#   make clean          清理 build/

PY ?= python3
D  ?= 300
PORT ?= 8765

.PHONY: build serve test clean

build:
	$(PY) -m bridge.pipeline --D $(D)

serve:
	CHBIM_PORT=$(PORT) $(PY) -m app.server

test:
	$(PY) -m unittest discover -s tests -v

clean:
	rm -rf build
