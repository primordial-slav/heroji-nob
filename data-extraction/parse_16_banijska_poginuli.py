"""
Parser: 16. banijska brigada (brigade code 47), its second book: the brigade's own list of its fallen.

Source: Ljuban P. Đurić (ed.), "Šesnaesta banijska narodnooslobodilačka udarna brigada" (1984), in the Digital library of
        Poreklo (biblioteka.poreklo.rs, collection "Drugi svetski rat"; for members only). The library's OCR text of the
        list pages is kept in data-extraction/poreklo/16-banijska.json (poreklo_text.py). "Spisak poginulih boraca i
        rukovodilaca šesnaeste banijske udarne brigade od 26. XII 1942. do 30. VI 1943. godine" (scan pages 213-259, book
        pp. 201-247): 557 fallen, by the editor's note partial, from the SUBNOR records of the Sisak municipalities and
        checked against Kučan's Sutjeska book (Borci Sutjeske, the unit's first book here). One entry a paragraph, the
        first line hanging:
            ADAMOVIĆ Sime MILOŠ: borac, rođen 1922. godine, Gornja Mlinoga, Petrinja, zemljoradnik, Srbin, u NOVJ od
            1942. godine, poginuo na rijeci Tari početkom juna 1943. godine.
The records get IDs from 0047010001 and go into the unit's file beside Borci Sutjeske's (keep_other_sources); a man in
both books is merged by corrections. There is no scan on the site: records carry `source_url` and `source_page`.
"""
import re

from _parser_scaffold import _record, run_parser
from poreklo_text import (VIEWER_URL, load, name_counts, page_lines, printed_page, restore_diacritics,
                          viewer_url)

BOOK = load('16-banijska.json')
PAGES = range(213, 260)
MARK = 'ꙮ '                                          # starts an entry (a letter: the scaffold strips leading marks)
U, L = 'A-ZČĆŽŠĐ', 'a-zčćžšđ'
LOOKALIKE = str.maketrans({'Ј': 'J', 'В': 'B', 'А': 'A', 'Е': 'E', 'О': 'O', 'Р': 'P', 'С': 'C', 'Т': 'T', 'Н': 'H',
                           'К': 'K', 'М': 'M', 'Х': 'X', 'а': 'a', 'е': 'e', 'о': 'o', 'р': 'p', 'с': 'c', 'у': 'y'})
# SURNAME (or two, with a dash), the father in the genitive (or his initial, or "(?)"), GIVEN, a nickname after a dash
HEAD = re.compile(rf'^(?P<last>[{U}]{{2,}}(?:\s?[—–-]\s?[{U}]{{2,}})?)\s+'
                  rf'(?:(?P<father>[{U}][{L}]+(?:-[{U}][{L}]+)?|[{U}]\.|\(\?\))\s+)?(?:[—–-]\s?(?P<nth>I{{1,3}})\s+)?'
                  rf'(?P<given>[{U}]{{2,}}|[{U}][{L}]+)'
                  rf'(?:\s?[—–-]\s?(?P<nick>[{U}]{{2,}}|[{L}]+|I{{1,3}}))?\s*[:;,.]\s*')


def head_text(text: str) -> str:
    """The OCR's slips in the names: a word split after J ("HALAVANJ A", "LJ UBAN", "J andrije"), Đ read as 1r' or 1:
    ("1r'DURO"), the colon read as Č ("GRUJOČborac"), a hyphen inside a father's name ("Nik-ole")"""
    text = re.sub(rf'(?<=[{U}]J) (?=[{U}]+(?=[\s:;,.]))|(?<=\sJ) (?=[{L}])|(?<=\bLJ) (?=[{U}])', '', text)
    text = re.sub(r"\b1[r:'’]*'?D(?=[A-Z])", 'Đ', text)
    text = text.replace('MILJEVIĆ Bигo RADE', 'MILJEVIĆ Đuro RADE')             # book p. 224 (scan 236), read from the scan
    text = re.sub(rf'^([{U}]+\s+[{U}]{{3,}})Č(?=[{L}])', r'\1: ', text)
    return re.sub(rf'(?<=[{L}])-(?=[{L}])', '', text, count=1)


def read_lines(_path: str, _start: int, _end) -> list[dict]:
    out = []
    for page in PAGES:
        lines = page_lines(BOOK, page)[0]
        left = min((l.x0 for l in lines if len(l.text) > 3), default=0)
        for line in lines:
            text = re.sub(r'^[^\w]+', '', line.text.translate(LOOKALIKE)).strip()
            text = re.sub(rf'(?<=[{U}])([čćžšđ])(?=[{U}]|\b)', lambda m: m.group(1).upper(), text)
            text = re.sub(rf'(?<=[{U}])l(?=[{U}])', 'I', text)
            if not text or re.fullmatch(r'[\d\s]+', text) or re.fullmatch(rf'(?:[{U}]|DŽ|LJ|NJ)\.?', text):
                continue                                                     # page numbers, the letter headings
            start = line.x0 - left < 800 and bool(re.match(rf'^[{U}]{{2,}}', text))
            out.append({'text': (MARK if start else '') + text, 'x': line.x0, 'y': line.top, 'page': page})
    return out


def parse_entry(text: str) -> dict:
    text = text.replace(MARK, '').strip()
    text = re.sub(r'(?<=[a-zčćžšđ])[—–-]\s+(?=[a-zčćžšđ])', '', text)       # "ро– ginuo", "Ne— retvi"
    text = head_text(text)
    m = HEAD.match(text)
    if not m:
        return {}
    last = re.sub(r'\s?[—–-]\s?', '-', m.group('last'))
    father = m.group('father') or ''
    father = '' if father == '(?)' else father.rstrip('.')
    info = text[m.end():].strip()
    nick = m.group('nick')
    if nick:
        # "VASO—VAĆO": a nickname; "ILIJA — mlađi", "BRANKO — II": which of two of the name
        info = (f'zvani {nick.title()}; ' if nick.isupper() and len(nick) > 3 else f'{nick}; ') + info
    if m.group('nth'):
        info = f"{m.group('nth')}; " + info                                   # "POLIMAC Dure — II BRANKO": the second Branko
    if m.group('father') == '(?)':
        info = 'otac (?); ' + info                                           # the book doesn't know the father
    return _record(last, m.group('given'), father, info)


def post(soldiers: list[dict]) -> list[dict]:
    for s in soldiers:
        page = s.pop('pdf_page')
        for k in ('pdf_y', 'pdf_x', 'pdf_y_end', 'pdf_file'):
            s.pop(k, None)
        s['source_url'] = viewer_url(BOOK, page)
        s['source_page'] = printed_page(BOOK, page)
    counts = name_counts('16-banijska-soldiers.json')
    printed = {id(s): s['last_name'] for s in soldiers}
    n = restore_diacritics(soldiers, counts)
    for s in soldiers:                               # Banija's surnames end in -ić, whatever the OCR made of the Ć
        if re.search(r'i[cčć]$', printed[id(s)], re.I):
            ic = s['last_name'][:-1] + 'ć'
            if s['last_name'] != ic and counts['last_name'][ic] > 0:
                s['last_name'], n = ic, n + 1
        s['full_name'] = ' '.join(x for x in (s['last_name'], s['middle_name'], s['first_name']) if x)
    print(f'  diacritics restored in {n} names')
    return soldiers


if __name__ == '__main__':
    run_parser(
        pdf_path='poreklo/16-banijska.json',
        brigade_code=47,
        output_path='website/public/16-banijska-soldiers.json',
        extract_fn=read_lines,
        entry_start_re=re.compile('^' + MARK),
        parse_entry_fn=parse_entry,
        post_fn=post,
        id_start=10001,
        keep_other_sources=True,
        source_url_prefix=VIEWER_URL.split('{')[0] + BOOK['id'],
    )
