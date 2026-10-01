# -*- coding: utf-8 -*-
"""Рендер зразків: fonts/*.ttf -> docs/preview-<назва>.png

Шейпінг — через HarfBuzz (uharfbuzz), щоб у зразках працювали
OpenType-фічі liga/calt/mark; Pillow без libraqm їх не застосовує.
Контури гліфів — штрихові полігони без дірок, тож пошарова заливка
полігонів одним кольором дає коректне об'єднання.
"""
from pathlib import Path

import uharfbuzz as hb
from fontTools.ttLib import TTFont
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
FONTS = ROOT / 'fonts'
DOCS = ROOT / 'docs'

# (заголовок секції, рядки) — повна абетка, цифри, пунктуація, приклади
SECTIONS = [
    ("Абетка", [
        "а б в г ґ д е є ж з и і ї й к л",
        "м н о п р с т у ф х ц ч ш щ ь ю я",
    ]),
    ("Цифри та пунктуація", [
        "0 1 2 3 4 5 6 7 8 9",
        ". , ! ? - : ; … — – ( ) « »",
    ]),
    ("Приклади", [
        "Чуєш їх, доцю, га? Кумедна ж ти,",
        "прощайся без ґольфів!",
        "Реве та стогне Дніпр широкий,",
        "сердитий вітер завива.",
        "М'яч, джміль, дзвін, щастя, її мрія!",
        "Рік 1847 — «Кобзар»; 25 (чи 360?) дум…",
    ]),
]
BG, INK, CAPTION, HEAD = '#1B2A23', '#D3AE62', '#93A98F', '#C8B98B'


def caption_font(size):
    """Системний шрифт із кирилицею; дефолтний Pillow її не має."""
    for p in ('/System/Library/Fonts/Helvetica.ttc',
              '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'):
        if Path(p).exists():
            return ImageFont.truetype(p, size)
    return ImageFont.load_default(size)


def draw_line(d, glyf, order, upm, hbfont, text, x, baseline, size, fill):
    scale = size / upm
    buf = hb.Buffer()
    buf.add_str(text)
    buf.guess_segment_properties()
    hb.shape(hbfont, buf)
    pen = x
    for info, pos in zip(buf.glyph_infos, buf.glyph_positions):
        g = glyf[order[info.codepoint]]
        if g.numberOfContours > 0:
            coords, ends, _ = g.getCoordinates(glyf)
            start = 0
            for end in ends:
                pts = [(pen + (gx + pos.x_offset) * scale,
                        baseline - (gy + pos.y_offset) * scale)
                       for gx, gy in coords[start:end + 1]]
                d.polygon(pts, fill=fill)
                start = end + 1
        pen += pos.x_advance * scale


def main():
    DOCS.mkdir(exist_ok=True)
    ttfs = sorted(FONTS.glob('*.ttf'))
    if not ttfs:
        raise SystemExit('Спершу зберіть шрифти: make build')
    n_lines = sum(len(lns) for _, lns in SECTIONS)
    height = 90 + len(SECTIONS) * 46 + n_lines * 160
    for ttf in ttfs:
        tt = TTFont(ttf)
        glyf = tt['glyf']
        order = tt.getGlyphOrder()
        upm = tt['head'].unitsPerEm
        ascent = tt['hhea'].ascent
        full = tt['name'].getDebugName(4)
        version = tt['name'].getDebugName(5)
        hbfont = hb.Font(hb.Face(hb.Blob.from_file_path(str(ttf))))
        cap = caption_font(22)
        head = caption_font(28)
        img = Image.new('RGB', (1500, height), BG)
        d = ImageDraw.Draw(img)
        d.text((50, 24), f'{full} · {version}', font=head, fill=HEAD)
        size, y = 64, 90
        for title, lines in SECTIONS:
            d.text((50, y), title.upper(), font=cap, fill=CAPTION)
            y += 46
            for ln in lines:
                baseline = y + ascent / upm * size
                draw_line(d, glyf, order, upm, hbfont, ln, 50, baseline, size, INK)
                d.text((50, y + 104), ln, font=cap, fill=CAPTION)
                y += 160
        out = DOCS / f'preview-{ttf.stem}.png'
        img.save(out)
        print(f'  ✓ {out.relative_to(ROOT)}')


if __name__ == '__main__':
    main()
