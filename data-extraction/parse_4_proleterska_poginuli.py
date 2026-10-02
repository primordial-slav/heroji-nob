"""
Parser: 4. proleterska (crnogorska) brigada (brigade code 40) — the brigade's fallen, a second book.

Source: Blažo Janković, "Četvrta proleterska crnogorska brigada" (znaci.org 00001/148_13.pdf) →
        website/public/pdfs/4-proleterska-poginuli.pdf: "Borci i starješine brigade poginuli od 1942. do 1945.
        godine" (pp. 1-107), numbered anew under each year:
    102. ДОЖИЋ Илијин БЛАЖО, рођен 1903. у Колашину, земљорадник, замјеник политичког комесара чете, погинуо
    августа 1942. у подручју Купреса.
Cyrillic, one column. The father as a Montenegrin possessive (Илијин, Комненов, Машанов), a genitive (Иве) or an
initial. Not parsed: the brigade's officers by battalion and duty (pp. 109-131). The unit's first book is its
Borci Sutjeske chapter (IDs 1-); these get IDs from 10001; the same soldier in both is merged.
"""
import glob
import json
import re
from collections import Counter

from _parser_scaffold import (DEFAULT_ENTRY_START, extract_lines_single_column, parse_standard_entry,
                              repair_cyrillic_ocr, run_parser)

U, L = 'A-ZČĆŽŠĐ', 'a-zčćžšđ'
ENTRY = re.compile(rf'^(?:\.?\d{{1,4}}[.,]?\s+[{U}]{{2}}|{DEFAULT_ENTRY_START.pattern[1:]})')   # a number, or none the OCR kept
_first: Counter = Counter()


def corpus() -> None:
    for f in glob.glob('website/public/*soldiers.json'):
        for s in json.load(open(f, encoding='utf-8')):
            _first[s['first_name']] += 1


# an entry glued after a full stop: ". ВУЈИСИЋ Благојев ДРАГУТИН"
GLUED = re.compile(r'(?<=\.)\s+(?=[А-ЯЂЋЏЉЊЈ]{3,}\s+[А-ЯЂЋЏЉЊЈ][а-яђћџљњј]+\s+[А-ЯЂЋЏЉЊЈ]{2,})')


def extract(pdf_path: str, start: int, end: int | None) -> list[dict]:
    lines = []
    for ln in extract_lines_single_column(pdf_path, start, end):
        for part in GLUED.split(ln['text']):
            lines.append({**ln, 'text': part})
    return lines


def keep(ln: dict) -> bool:
    t = ln['text'].strip()
    if re.fullmatch(r'[\d\W]{1,6}|19[45]\d\.?', t) or re.match(r'^(?:BORCI I STARJEŠINE BRIGADE|POGINULI OD 1942)', t):
        return False                                                         # page numbers, year headings, the title
    t = t.replace('J1', 'L').replace('j1', 'l')                             # Л read as Ј1: "JEJ1ENA" = Jelena
    t = re.sub(r'(?<=[A-Za-zčćžšđČĆŽŠĐ])[Jj]b(?=[a-zA-Z])', 'lj', t).replace('Jb', 'Lj').replace('JB', 'LJ')   # Љ read as Јб: "VEJBKO"
    ln['text'] = t
    return True


def nominative(father: str) -> str:
    """Montenegrin possessives: Ilijin → Ilija, Komnenov → Komnen, Radojev → Radoje, Ljubov → Ljubo."""
    if not father or father.endswith('.'):
        return father
    father = re.sub(r'(?<=[oei][vn])a$', '', father)                       # a daughter's "Jovanova", "Blažova"
    m = re.match(r'^(.+?)(in|ov|ev)$', father)
    if not m:
        return ''                                                           # a genitive: normalize converts it
    stem, suf = m.groups()
    fleeting = stem[:-1] + 'a' + stem[-1] if len(stem) > 2 and stem[-1] not in 'aeiou' and stem[-2] not in 'aeiou' else ''
    options = [stem + 'a', stem + 'o', stem] if suf == 'in' else [o for o in (stem, stem + 'o', stem + 'e', fleeting) if o]
    best = max(options, key=lambda c: _first[c])
    return best if _first[best] else father


def parse_entry(text: str) -> dict:
    text = re.sub(r'^\.?\d{1,4}[.,]?\s+', '', text)
    text = re.sub(rf"^([{U}]+)\s*[—–-]\s*([{U}]+)", r'\1-\2', text)            # "ĆALETA–CAR"
    text = re.sub(rf"^([{U}\-]+)\s+'?([{L}])", lambda m: m.group(1) + ' ' + m.group(2).upper(), text)   # "PJEVAC steve"
    text = re.sub(rf'^([{U}\-]+\s+[{U}][{L}]+)\s+\([{U}][{L}]+\)', r'\1', text)   # "Miladinov (Migrov)"
    text = re.sub(rf'^([{U}\-]+\s+[{U}][{L}]+)\s+[{U}]\.\s+(?=[{U}]{{2}})', r'\1 ', text)   # "Milanov K. RADOMIR"
    dr = re.search(r'\sdr\s+(?=[A-ZČĆŽŠĐ]{2})', text.split(',')[0])
    if dr:
        text = text[:dr.start()] + ' ' + text[dr.end():]
    text = re.sub(rf'^([{U}\-]+\s+[{U}][{L}]+\s+)([{U}][{L}]+)(?=,)', lambda m: m.group(1) + m.group(2).upper(), text)
    rec = parse_standard_entry(text)
    if dr:
        rec['additional_info'] = 'dr. ' + rec['additional_info']
    return rec


def post(soldiers: list[dict]) -> list[dict]:
    soldiers = repair_cyrillic_ocr(soldiers)                                # resets the father to the printed form
    for s in soldiers:
        nom = nominative(s['middle_name'])
        if nom:
            s['fathers_name'] = nom
        parts = s['first_name'].split(' ')
        if len(parts) == 2 and _first[parts[0]] >= 3:
            s['first_name'] = parts[0]                                       # "DIMITRIJE MITAR": the name and a nickname
            s['additional_info'] = f'zvani {parts[1]}; ' + s['additional_info']
            s['full_name'] = ' '.join(p for p in (s['last_name'], s['middle_name'], s['first_name']) if p)
        if not s['first_name'] and not s['middle_name'] and _first[s['last_name']] >= 3:
            s['first_name'], s['last_name'] = s['last_name'], ''              # "LUIĐI, pripadnik talijanske vojske"
            s['full_name'] = s['first_name']
    return soldiers


if __name__ == '__main__':
    import sys
    corpus()
    run_parser(
        pdf_path='website/public/pdfs/4-proleterska-poginuli.pdf',
        brigade_code=40,
        output_path=sys.argv[1] if len(sys.argv) > 1 else 'website/public/4-proleterska-soldiers.json',
        start_page=1,
        end_page=107,
        layout='single',
        extract_fn=extract,
        script='cyrillic',
        entry_start_re=ENTRY,
        parse_entry_fn=parse_entry,
        line_filter=keep,
        post_fn=post,
        id_start=10001,
        keep_other_sources=len(sys.argv) <= 1,
    )
