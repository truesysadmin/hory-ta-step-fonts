# -*- coding: utf-8 -*-
"""Синхронізація контурів: sources/*/glyphs.json -> docs/interactive.html.

Перегенеровує JS-константи CONS/VOW/SOFT/DIG/PUNCT (та *_P для друкованого
стилю) з єдиного джерела правди — glyphs.json. Запуск: make sync.
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HTML = ROOT / 'docs' / 'interactive.html'
GLYPHS = ROOT / 'sources' / 'hory-ta-step' / 'glyphs.json'

CONS_GROUPS = [
    ('губні — дуга праворуч', ['п', 'б', 'ф', 'в', 'м']),
    ('зубні — дуга ліворуч', ['т', 'д', 'с', 'з', 'н']),
    ('африкати — печать-риска', ['ц', 'ДЗ']),
    ('шиплячі — завиток на кінці дуги / подвоєння', ['ч', 'ДЖ', 'ш', 'ж', 'щ']),
    ('задньоязикові — петля крізь стебло', ['к', 'ґ', 'х', 'г']),
    ('плавні — вільні розчерки', ['л', 'р', 'й', '_']),
]
JS_KEY = {'ДЖ': 'дж', 'ДЗ': 'дз'}
VOW_ORDER = ['а', 'о', 'у', 'е', 'и', 'і']
DIG_ORDER = list('0123456789')
PUNCT_ORDER = ['.', ',', '!', '?', '-', ':', ';', '…', '—', '–',
               '(', ')', '«', '»', "'"]


def jstr(s):
    return '"' + s.replace('\\', '\\\\').replace('"', '\\"') + '"'


def emit_cons(g):
    lines = []
    last_key = CONS_GROUPS[-1][1][-1]
    for comment, keys in CONS_GROUPS:
        lines.append(f' /* {comment} */')
        for k in keys:
            comma = '' if k == last_key else ','
            tail = ' /* курган-носій */' if k == '_' else ''
            lines.append(f" '{JS_KEY.get(k, k)}':{jstr(g['cons'][k])}{comma}{tail}")
    return '\n'.join(lines)


def emit_map(d, order):
    lines = []
    for k in order:
        comma = '' if k == order[-1] else ','
        lines.append(f" {jstr(k)}:{jstr(d[k])}{comma}")
    return '\n'.join(lines)


def replace_block(html, name, body):
    pat = re.compile(r'const ' + name + r' = \{.*?\};', re.S)
    if not pat.search(html):
        raise SystemExit(f'Не знайдено блок const {name} у {HTML}')
    return pat.sub(lambda m: f'const {name} = {{\n{body}\n}};', html, count=1)


def replace_str(html, name, value):
    pat = re.compile(r'const ' + name + r' = "[^"]*";')
    if not pat.search(html):
        raise SystemExit(f'Не знайдено const {name} у {HTML}')
    return pat.sub(f'const {name} = {jstr(value)};', html, count=1)


def main():
    sets = json.loads(GLYPHS.read_text(encoding='utf-8'))
    html = HTML.read_text(encoding='utf-8')
    for suffix, gset in (('', sets['hand']), ('_P', sets['print'])):
        html = replace_block(html, 'CONS' + suffix, emit_cons(gset))
        html = replace_block(html, 'VOW' + suffix, emit_map(gset['vow'], VOW_ORDER))
        html = replace_str(html, 'SOFT' + suffix, gset['soft'])
        html = replace_block(html, 'DIG' + suffix, emit_map(gset['dig'], DIG_ORDER))
        html = replace_block(html, 'PUNCT' + suffix,
                             emit_map(gset['punct'], PUNCT_ORDER))
    HTML.write_text(html, encoding='utf-8')
    print(f'  ✓ {HTML.relative_to(ROOT)} синхронізовано з {GLYPHS.relative_to(ROOT)}')


if __name__ == '__main__':
    main()
