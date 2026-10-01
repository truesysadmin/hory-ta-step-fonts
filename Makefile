.PHONY: setup build test preview sync clean all

# Якщо є локальне віртуальне середовище .venv — використовуємо його,
# інакше системний python3.
PY := $(shell test -x .venv/bin/python && echo .venv/bin/python || echo python3)

all: build test preview

setup:
	python3 -m venv .venv
	.venv/bin/pip install -r requirements.txt
	@echo "Готово. Далі просто: make"

build:
	$(PY) tools/build.py

test:
	$(PY) -m pytest tests/ -q

preview:
	$(PY) tools/preview.py

sync:
	$(PY) tools/sync.py

clean:
	rm -rf fonts/*.ttf docs/preview-*.png
