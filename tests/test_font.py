# -*- coding: utf-8 -*-
"""Smoke-тести зібраних шрифтів."""
from pathlib import Path

import pytest
import uharfbuzz as hb
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parent.parent
TTFS = sorted((ROOT / 'fonts').glob('*.ttf'))

UKR = "абвгґдежзиійклмнопрстуфхцчшщьюяєї"

MARKS = ('a.mark', 'o.mark', 'u.mark', 'e.mark', 'y.mark', 'i.mark',
         'soft.mark')


@pytest.fixture(params=TTFS, ids=[p.stem for p in TTFS])
def ttf_path(request):
    return request.param


@pytest.fixture
def font(ttf_path):
    return TTFont(ttf_path)


def shape(ttf_path, text):
    """(ім'я гліфа, позиція) після шейпінгу HarfBuzz."""
    order = TTFont(ttf_path).getGlyphOrder()
    hbfont = hb.Font(hb.Face(hb.Blob.from_file_path(str(ttf_path))))
    buf = hb.Buffer()
    buf.add_str(text)
    buf.guess_segment_properties()
    hb.shape(hbfont, buf)
    return [(order[i.codepoint], p)
            for i, p in zip(buf.glyph_infos, buf.glyph_positions)]


def test_fonts_built():
    assert TTFS, 'fonts/*.ttf відсутні — запустіть make build'


def test_ukrainian_coverage(font):
    cmap = font.getBestCmap()
    missing = [ch for ch in UKR + UKR.upper() if ord(ch) not in cmap]
    assert not missing, f'Немає гліфів для: {missing}'


def test_punctuation_and_space(font):
    cmap = font.getBestCmap()
    for ch in " .,!?-:;…—–()«»'’":
        assert ord(ch) in cmap, f'Немає гліфа для {ch!r}'


def test_digits_coverage(font):
    cmap = font.getBestCmap()
    glyf = font['glyf']
    for ch in '0123456789':
        assert ord(ch) in cmap, f'Немає гліфа для цифри {ch}'
        assert glyf[cmap[ord(ch)]].numberOfContours > 0, \
            f'Порожній контур для цифри {ch}'


def test_ligatures_present(font):
    assert 'GSUB' in font, 'Відсутня таблиця GSUB'
    glyph_order = font.getGlyphOrder()
    assert 'dzhe' in glyph_order and 'dze' in glyph_order


def test_unicase(font):
    cmap = font.getBestCmap()
    for ch in UKR:
        assert cmap[ord(ch)] == cmap[ord(ch.upper())], \
            f'Велика і мала {ch} мають різні гліфи'


def test_outlines_nonempty(font):
    glyf = font['glyf']
    cmap = font.getBestCmap()
    for ch in UKR:
        g = glyf[cmap[ord(ch)]]
        assert g.numberOfContours > 0, f'Порожній контур для {ch}'


def test_metrics(font):
    hmtx = font['hmtx']
    cmap = font.getBestCmap()
    widths = {hmtx[cmap[ord(ch)]][0] for ch in UKR}
    assert all(w > 0 for w in widths)


def test_marks_zero_width(font):
    hmtx = font['hmtx']
    for nm in MARKS:
        assert hmtx[nm][0] == 0, f'Марка {nm} має ненульову ширину'


def test_gdef_mark_classes(font):
    classdefs = font['GDEF'].table.GlyphClassDef.classDefs
    for nm in MARKS:
        assert classdefs[nm] == 3, f'{nm} не позначена як mark у GDEF'
    assert classdefs['te'] == 1, 'приголосний не позначений як base'


def test_abugida_vowel_attaches(ttf_path):
    names = [n for n, _ in shape(ttf_path, 'та')]
    assert names == ['te', 'a.mark']


def test_abugida_word_initial_vowel_standalone(ttf_path):
    names = [n for n, _ in shape(ttf_path, 'ана')]
    assert names == ['a', 'en', 'a.mark']


def test_abugida_soft_and_vowel_stack(ttf_path):
    names = [n for n, _ in shape(ttf_path, 'тьох')]
    assert names == ['te', 'soft.mark', 'o.mark', 'kha']


def test_abugida_ligature_takes_mark(ttf_path):
    names = [n for n, _ in shape(ttf_path, 'джміль')]
    assert names == ['dzhe', 'em', 'i.mark', 'el', 'soft.mark']


def test_abugida_apostrophe_breaks_syllable(ttf_path):
    names = [n for n, _ in shape(ttf_path, "м'яч")]
    assert names == ['em', 'apostrophe', 'ya', 'che']


def test_iotated_after_consonant_decomposes(ttf_path):
    # я/ю/є після приголосного = вітер унизу + голосна вгорі
    assert [n for n, _ in shape(ttf_path, 'ля')] == \
        ['el', 'soft.mark', 'a.mark']
    assert [n for n, _ in shape(ttf_path, 'нюх')] == \
        ['en', 'soft.mark', 'u.mark', 'kha']
    assert [n for n, _ in shape(ttf_path, 'сє')] == \
        ['es', 'soft.mark', 'e.mark']


def test_iotated_word_initial_standalone(ttf_path):
    names = [n for n, _ in shape(ttf_path, 'яр')]
    assert names == ['ya', 'er']


def test_iotated_after_vowel_standalone(ttf_path):
    names = [n for n, _ in shape(ttf_path, 'моя')]
    assert names == ['em', 'o.mark', 'ya']


def test_iotated_after_yot_standalone(ttf_path):
    names = [n for n, _ in shape(ttf_path, 'йя')]
    assert names == ['yot', 'ya']


def test_iotated_after_softsign_standalone(ttf_path):
    names = [n for n, _ in shape(ttf_path, 'лья')]
    assert names == ['el', 'soft.mark', 'ya']


def test_yi_never_decomposes(ttf_path):
    # «ї» — завжди й+і, навіть одразу після приголосного
    assert [n for n, _ in shape(ttf_path, 'тї')] == ['te', 'yi']
    assert [n for n, _ in shape(ttf_path, 'воїн')] == \
        ['ve', 'o.mark', 'yi', 'en']


def test_iotated_double_consonant_word(ttf_path):
    names = [n for n, _ in shape(ttf_path, 'рілля')]
    assert names == ['er', 'i.mark', 'el', 'el', 'soft.mark', 'a.mark']


def test_mark_positioning(ttf_path):
    (_, base_pos), (_, mark_pos) = shape(ttf_path, 'та')
    assert mark_pos.x_advance == 0
    # якорі збігаються, тож марка повертається рівно на початок знака
    assert mark_pos.x_offset == -base_pos.x_advance
    assert mark_pos.y_offset == 0
