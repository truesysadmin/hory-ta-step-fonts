# -*- coding: utf-8 -*-
"""Збирання всіх шрифтів з sources/ у fonts/.

Кожна тека sources/<назва>/ з family.json + glyphs.json — окрема гарнітура.
Використання: python tools/build.py [назва-гарнітури]
"""
import json
import sys
from pathlib import Path

from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.feaLib.builder import addOpenTypeFeaturesFromString

sys.path.insert(0, str(Path(__file__).parent))
from stroker import parse_subpaths, stroke_poly  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
SOURCES = ROOT / 'sources'
FONTS = ROOT / 'fonts'

CONS_NAMES = {
    'б': 'be', 'в': 've', 'г': 'he', 'ґ': 'ghe', 'д': 'de', 'ж': 'zhe',
    'з': 'ze', 'к': 'ka', 'л': 'el', 'м': 'em', 'н': 'en', 'п': 'pe',
    'р': 'er', 'с': 'es', 'т': 'te', 'ф': 'ef', 'х': 'kha', 'ц': 'tse',
    'ч': 'che', 'ш': 'sha', 'щ': 'shcha', 'й': 'yot',
}
VOW_NAMES = {'а': 'a', 'о': 'o', 'у': 'u', 'е': 'e', 'и': 'y', 'і': 'i'}
YOT = (('я', 'ya', 'а'), ('ю', 'yu', 'у'), ('є', 'ye', 'е'), ('ї', 'yi', 'і'))
DIGIT_NAMES = {'0': 'zero', '1': 'one', '2': 'two', '3': 'three',
               '4': 'four', '5': 'five', '6': 'six', '7': 'seven',
               '8': 'eight', '9': 'nine'}
PUNCT_NAMES = {'.': 'period', ',': 'comma', '!': 'exclam', '?': 'question',
               '-': 'hyphen', ':': 'colon', ';': 'semicolon',
               '…': 'ellipsis', '—': 'emdash', '–': 'endash',
               '(': 'parenleft', ')': 'parenright',
               '«': 'guillemetleft', '»': 'guillemetright'}
NARROW = {'period', 'comma', 'apostrophe', 'colon', 'semicolon'}

def make_fea(fam):
    """OpenType-фічі: лігатури, абугідні заміни (calt) та якорі (mark).

    Голосна після приголосного (чи після марки м'якості, як у «тьо») стає
    zero-width маркою над знаком; на початку слова, після голосної чи
    апострофа лишається окремим знаком на кургані. Завиток м'якості після
    приголосного стає маркою під знаком. mkmk не потрібен: марки не
    накладаються з одного боку (одна голосна зверху, одна м'якість знизу).

    Йотовані після приголосного (крім «й») розпадаються на вітер + голосну:
    «ля» = л + завиток унизу + а вгорі. Після «й», м'якого знака, голосної,
    апострофа чи на початку слова я/ю/є лишаються листком-й зі знаком угорі;
    «ї» — завжди й+і.
    """
    def fx(x):
        return round(x * fam['scale'])

    def fy(y):
        return round((fam['baseY'] - y) * fam['scale'])

    cons = ' '.join(list(CONS_NAMES.values()) + ['dzhe', 'dze'])
    cons_nj = ' '.join([n for n in CONS_NAMES.values() if n != 'yot']
                       + ['dzhe', 'dze'])
    vow = ' '.join(VOW_NAMES.values())
    vmark = ' '.join(f'{n}.mark' for n in VOW_NAMES.values())
    top = f'<anchor {fx(20)} {fy(7)}>'   # центр поля голосної (y 0..14)
    bot = f'<anchor {fx(20)} {fy(72)}>'  # центр поля м'якості (y 66..78)
    return f"""
languagesystem DFLT dflt;
languagesystem cyrl dflt;

@CONS = [{cons}];
@CONSNJ = [{cons_nj}];
@VOW = [{vow}];
@VOWMARK = [{vmark}];

feature liga {{
    sub de zhe by dzhe;
    sub de ze by dze;
}} liga;

feature calt {{
    sub @CONS soft' by soft.mark;
    sub [@CONS soft.mark] @VOW' by @VOWMARK;
    sub @CONSNJ ya' by soft.mark a.mark;
    sub @CONSNJ yu' by soft.mark u.mark;
    sub @CONSNJ ye' by soft.mark e.mark;
}} calt;

markClass @VOWMARK {top} @TOP;
markClass soft.mark {bot} @BOTTOM;

feature mark {{
    pos base @CONS {top} mark @TOP
               {bot} mark @BOTTOM;
}} mark;

table GDEF {{
    GlyphClassDef [@CONS @VOW soft ya yu ye yi], , [@VOWMARK soft.mark], ;
}} GDEF;
"""


def build_style(fam, gset, style_name, cfg, out_dir):
    scale = fam['scale']
    base_y = fam['baseY']
    adv = fam['advance']

    def fx(x):
        return round(x * scale)

    def fy(y):
        return round((base_y - y) * scale)

    r_main = cfg['strokeWidth'] / 2
    r_mark = cfg['markWidth'] / 2
    cap = cfg['cap']

    glyph_parts = {}
    cmap = {0x20: 'space'}

    def add(name, parts, codes=()):
        glyph_parts[name] = parts
        for c in codes:
            cmap[ord(c)] = name

    cons, vow, soft = gset['cons'], gset['vow'], gset['soft']
    dig, punct = gset['dig'], gset['punct']
    for ch, nm in CONS_NAMES.items():
        add(nm, [(cons[ch], 16, r_main)], (ch, ch.upper()))
    for ch, nm in VOW_NAMES.items():
        add(nm, [(cons['_'], 16, r_main), (vow[ch], 0, r_mark)], (ch, ch.upper()))
    for ch, nm, v in YOT:
        add(nm, [(cons['й'], 16, r_main), (vow[v], 0, r_mark)], (ch, ch.upper()))
    add('soft', [(soft, 34, r_mark)], ('ь', 'Ь'))
    add('dzhe', [(cons['ДЖ'], 16, r_main)])
    add('dze', [(cons['ДЗ'], 16, r_main)])
    # Zero-width марки абугіди: голосна над знаком, м'якість під ним
    for ch, nm in VOW_NAMES.items():
        add(f'{nm}.mark', [(vow[ch], 0, r_mark)])
    add('soft.mark', [(soft, 66, r_mark)])
    # Цифри-колосся: 0 — зерно, 1..4 — стебло з зернами,
    # 5 — схилений колос, 6..9 — схилений колос із зернами
    for ch, nm in DIGIT_NAMES.items():
        add(nm, [(dig[ch], 16, r_main)], (ch,))
    for ch, nm in PUNCT_NAMES.items():
        add(nm, [(punct[ch], 16, r_mark)], (ch,))
    add('apostrophe', [(punct["'"], 16, r_mark)])
    cmap[0x2019] = 'apostrophe'
    cmap[0x0027] = 'apostrophe'

    order = ['.notdef', 'space'] + list(glyph_parts.keys())
    fb = FontBuilder(fam['upm'], isTTF=True)
    fb.setupGlyphOrder(order)
    fb.setupCharacterMap(cmap)

    glyphs, metrics = {}, {}
    pen = TTGlyphPen(None)
    glyphs['.notdef'] = pen.glyph()
    metrics['.notdef'] = (adv, 0)
    pen = TTGlyphPen(None)
    glyphs['space'] = pen.glyph()
    metrics['space'] = (fam['narrowAdvance'], 0)

    for name, parts in glyph_parts.items():
        pen = TTGlyphPen(None)
        for d, ty, r in parts:
            for sub in parse_subpaths(d):
                shifted = [(x, y + ty) for x, y in sub]
                poly = stroke_poly(shifted, r, cap=cap)
                pen.moveTo((fx(poly[0][0]), fy(poly[0][1])))
                for p in poly[1:]:
                    pen.lineTo((fx(p[0]), fy(p[1])))
                pen.closePath()
        glyphs[name] = pen.glyph()
        if name.endswith('.mark'):
            width = 0
        elif name in NARROW:
            width = fam['narrowAdvance']
        else:
            width = adv
        metrics[name] = (width, 30)

    fb.setupGlyf(glyphs)
    fb.setupHorizontalMetrics(metrics)
    fb.setupHorizontalHeader(ascent=fam['ascent'], descent=fam['descent'])
    ps = f"{fam['familyPs']}-{style_name}"
    fb.setupNameTable({
        'familyName': fam['family'],
        'styleName': style_name,
        'fullName': f"{fam['family']} {style_name}",
        'psName': ps,
        'version': f"Version {fam['version']}",
        'copyright': fam['copyright'],
        'licenseDescription': fam['license'],
    })
    weight = cfg.get('weight', 400)
    fb.setupOS2(sTypoAscender=fam['ascent'], sTypoDescender=fam['descent'],
                usWinAscent=fam['ascent'] + 50, usWinDescent=-fam['descent'] + 40,
                usWeightClass=weight)
    if weight >= 600:
        fb.font['head'].macStyle |= 0x01
        fb.font['OS/2'].fsSelection = (fb.font['OS/2'].fsSelection & ~0x40) | 0x20
    fb.setupPost()
    addOpenTypeFeaturesFromString(fb.font, make_fea(fam))

    out = out_dir / f'{ps}.ttf'
    fb.save(out)
    print(f'  ✓ {out.relative_to(ROOT)} ({len(order)} гліфів)')


def merge_set(base, overrides):
    """Накладає часткові перевизначення контурів (компенсація жирних дуг)."""
    merged = {}
    for key, val in base.items():
        if isinstance(val, dict):
            merged[key] = {**val, **overrides.get(key, {})}
        else:
            merged[key] = overrides.get(key, val)
    return merged


def build_family(src_dir):
    fam = json.loads((src_dir / 'family.json').read_text(encoding='utf-8'))
    sets = json.loads((src_dir / 'glyphs.json').read_text(encoding='utf-8'))
    print(f'Гарнітура: {fam["family"]}')
    FONTS.mkdir(exist_ok=True)
    for style_name, cfg in fam['styles'].items():
        gset = sets[cfg['set']]
        if 'overrides' in cfg:
            gset = merge_set(gset, sets.get(cfg['overrides'], {}))
        build_style(fam, gset, style_name, cfg, FONTS)


def main():
    only = sys.argv[1] if len(sys.argv) > 1 else None
    families = [p for p in sorted(SOURCES.iterdir())
                if (p / 'family.json').exists() and (only in (None, p.name))]
    if not families:
        sys.exit(f'Не знайдено гарнітур у {SOURCES}')
    for src in families:
        build_family(src)


if __name__ == '__main__':
    main()
