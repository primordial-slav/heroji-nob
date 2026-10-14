"""
Parser: 12. proleterska slavonska brigada (brigade code 146): its women fighters.

Source: Jovan Kokot, *Dvanaesta slavonska* (znaci.org 00001/46), the chapter "Spisak žena - boraca 12. proleterske
slavonske brigade (poginule, umrle i preživjele)", published by znaci.org only as a web page:
https://znaci.org/00001/46_225.htm → data-extraction/sources/12-slavonska-46_225.htm (a saved copy). The book's list
of all the brigade's fighters (46_226) is announced there as "u pripremi" and was never put up.
A paragraph a woman, alphabetical (loosely), the surname in bold, the given name in capitals, then her short bio:
    Anđelić RUŽICA, rođena 1924. u Grahovljanima - Daruvar, u NOV od 1943. Poginula 1944. godine.
    Blanuša DARINKA, (majka Dobrile i Vide). U NOVJ od 1941. zajedno sa šestoro djece. ...
A bio may run on into the next paragraph ("Ranjavana više puta, ..."). There is no scan: the records carry
`source_url` (the list on znaci.org) instead of a PDF position.
Usage: python data-extraction/parse_12_slavonska_zene.py
"""
import html
import re
from pathlib import Path

from _parser_scaffold import _record, repair_lj_ocr, restore_diacritics, run_parser

SOURCE = 'data-extraction/sources/12-slavonska-46_225.htm'
SOURCE_URL = 'https://znaci.org/00001/46_225.htm'
MARK = '⁣'
U, L = 'A-ZČĆŽŠĐ', 'a-zčćžšđ'


def read_entries(path: str, start: int, end: int | None) -> list[dict]:
    """A paragraph that opens with the bold surname starts a woman's entry; the others run on."""
    raw = Path(path).read_text(encoding='utf-8')
    body = raw[raw.index('poginule, umrle i preživjele'):]
    out = []
    for p in re.findall(r'<p\b.*?</p>', body, flags=re.S):
        bold = re.match(r'<p[^>]*>\s*<span[^>]*class="BodytextBold\d*"[^>]*>', p)
        text = re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', p))).strip()
        if not text or text in ('Sadržaj', 'Prethodni dokument', 'Sledeći dokument'):
            continue
        if bold and re.match(rf'^[{U}][{L}]+(?:\s*-\s*[{U}][{L}]+)?\s+[{U}]{{2,}}', text):     # "Varga - Bulović ANICA"
            out.append({'text': MARK + text, 'x': 0, 'y': float(len(out)), 'page': 1})
        elif out:
            out.append({'text': text, 'x': 0, 'y': float(len(out)), 'page': 1})
    return out


def parse_entry(text: str) -> dict:
    """Surname GIVEN [GIVEN], bio"""
    text = text.replace(MARK, '').strip()
    m = re.match(rf'^([{U}][{L}]+(?:\s*-\s*[{U}][{L}]+)?)\s+([{U}]{{2,}}(?:[- ][{U}]{{2,}})?)\s*,?\s*(.*)$', text)
    last, given, bio = re.sub(r'\s*-\s*', '-', m.group(1)), m.group(2).title(), m.group(3).strip()
    notes = []
    mother = re.match(r'^\((majka [^)]+)\)\.?\s*', bio)
    if mother:                                    # "Blanuša DARINKA, (majka Dobrile i Vide). U NOVJ od 1941. ..."
        bio = mother.group(1) + '. ' + bio[mother.end():]
    rec = _record(last, given, '', '; '.join(notes + ([bio] if bio else [])))
    y = re.search(r'\brođena\s+(?:u\s+[^.,]+\s+)?(1[89]\d\d)', bio)
    rec['birth_year'] = y.group(1) if y else ''
    return rec


def post(soldiers: list[dict]) -> list[dict]:
    for s in soldiers:
        for k in ('pdf_page', 'pdf_y', 'pdf_x', 'pdf_y_end', 'pdf_file'):
            s.pop(k, None)
        s['source_url'] = SOURCE_URL
    return repair_lj_ocr(restore_diacritics(soldiers))


if __name__ == '__main__':
    run_parser(
        pdf_path=SOURCE,
        brigade_code=146,
        output_path='website/public/12-slavonska-soldiers.json',
        start_page=1,
        end_page=1,
        script='latin',
        extract_fn=read_entries,
        entry_start_re=re.compile('^' + MARK),
        parse_entry_fn=parse_entry,
        post_fn=post,
    )
