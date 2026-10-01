# Локальна розробка

Як налаштувати проєкт на власному комп'ютері й працювати з ним так само,
як це робить CI.

## Що потрібно

- **Git**
- **Python 3.10+** (перевірити: `python3 --version`)
- **make** — є в macOS/Linux з коробки; на Windows найпростіше працювати
  через WSL або Git Bash (див. нижче)

## Налаштування (один раз)

```bash
git clone https://github.com/hory-ta-step/hory-ta-step.github.io.git
cd hory-ta-step-fonts
make setup        # створює .venv і ставить залежності
```

`make setup` створює ізольоване віртуальне середовище у `.venv/` —
системний Python лишається чистим. Усі подальші `make`-цілі самі
підхоплюють `.venv`, активувати його вручну не обов'язково.

## Щоденний цикл

```bash
make              # build + test + preview — все одразу
```

або окремо:

| Команда | Що робить |
|---|---|
| `make build` | збирає шрифти з `sources/` у `fonts/*.ttf` |
| `make test` | ганяє smoke-тести (`tests/test_font.py`) |
| `make preview` | рендерить зразки у `docs/preview-*.png` |
| `make clean` | видаляє зібрані артефакти |

Типовий цикл правки гліфа:

1. Змінюєте контур у `sources/hory-ta-step/glyphs.json`
   (або метрики/стилі у `family.json`).
2. `make` — шрифти, тести і превью оновлюються.
3. Дивитесь `docs/preview-*.png` або встановлюєте `fonts/*.ttf`
   у систему і перевіряєте в редакторі.

## Встановити шрифт у систему

- **macOS**: подвійний клік по `fonts/HoryTaStep-Drukovanyi.ttf` → «Install Font»
  (або скопіювати у `~/Library/Fonts/`).
- **Linux**: `cp fonts/*.ttf ~/.local/share/fonts/ && fc-cache -f`
- **Windows**: правий клік по `.ttf` → «Install».

Після зміни шрифту кеш деяких програм треба скинути (перезапустити
редактор/браузер), інакше побачите стару версію.

## Інтерактивний довідник

`docs/interactive.html` — самодостатня сторінка, відкривається просто
у браузері:

```bash
open docs/interactive.html        # macOS
xdg-open docs/interactive.html    # Linux
```

## Windows без make

У PowerShell ті самі кроки вручну:

```powershell
py -m venv .venv
.venv\Scripts\pip install -r requirements.txt
.venv\Scripts\python tools\build.py
.venv\Scripts\python -m pytest tests -q
.venv\Scripts\python tools\preview.py
```

## Перед пушем

CI (`.github/workflows/build.yml`) на кожен push виконує те саме, що й
локальний `make`, тож якщо `make` пройшов чисто — CI теж буде зелений.
Тег `v*` додатково публікує реліз із зібраними `.ttf`.
