"""
Parser: 1. bokeljska NOU brigada (code 102), its second book: the brigade's roster by unit.

Source: Dušan Živković, "Prva bokeljska NOU brigada" (znaci.org 00003/384.pdf, its pages 287-309, book pp. 291-314)
        →  website/public/pdfs/1-bokeljska-spisak.pdf. "Spisak Prve bokeljske NOU brigade", the brigade's unit roster
        ("jedinični spisak") from its formation (5 October 1944) to the end of the war, in which the battalions and
        the units at the staff entered their fighters and officers as they came; a man transferred was entered again
        in his new unit and not struck from the old (the book's footnote), so some stand twice, as printed. The
        author added those the roster had missed (numbered "879a", "1200a"). A table on each page, two side by side:
        the number, the duty (",," for the one above), the name (surname, the father in the genitive or an initial,
        the given name), under the units' headings (Štab brigade, Ekonomat, Kuriri, 1. bataljon, ..., Brigadna
        bolnica, "Ne zna se jedinica brigade"). The table that closes it (the brigade's men by municipality) is not
        read. The book's count is 3,255.

The pages are scans without a text layer: the text is Tesseract's (data-extraction/ocr_scan.py, `--lang hrv
--columns 2`), saved in data-extraction/ocr/1-bokeljska-spisak.json; this parser reads only that file. The first page
(the brigade staff, eleven men in two tables the OCR runs together) is typed from the page (`STAFF`).

Each record's text is its unit and duty ("1. bataljon: komandir čete"). The records are a second book of the unit
(IDs from 0102010001): `run_parser(..., id_start=10001, keep_other_sources=True)`.
"""
from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import ocr_scan  # noqa: E402
from _ocr_readback import LAT, Corpus, fold, title  # noqa: E402
from _parser_scaffold import _record, run_parser  # noqa: E402

PDF = 'website/public/pdfs/1-bokeljska-spisak.pdf'
NAME = Path(PDF).name
OUT = 'website/public/1-bokeljska-soldiers.json'
TITLE = 'Spisak Prve bokeljske NOU brigade'
NUMBER = re.compile(r'^(\d{1,4})\s*(a)?[.,:;)]*$')
# the units' headings, as the book prints them, and as the entries name them
HEADINGS = [(r'EKONOMAT', 'Ekonomat'), (r'KURIRI', 'Kuriri'), (r'^(?:1|I)\.?\s*BATALJON', '1. bataljon'),
            (r'^(?:2|II)\.?\s*BATALJON', '2. bataljon'), (r'^(?:3|III)\.?\s*BATALJON', '3. bataljon'),
            (r'^(?:4|IV)\.?\s*BATALJON', '4. bataljon'), (r'ČETA\s+PRATEĆIH', 'Četa pratećih oruđa'),
            (r'BOLNIČKI\s+VOD', 'Bolnički vod'), (r'KOMANDA\s+POZADINE', 'Komanda pozadine'),
            (r'IZVIĐAČKI\s+VOD', 'Izviđački vod'), (r'BRIGADNA\s+BOLNICA', 'Brigadna bolnica'),
            (r'NE\s*ŽNA|NE\s+ZNA', 'Ne zna se jedinica brigade'), (r'^PIONERI', 'Pioneri'), (r'^PRATEĆI\s+VOD', 'Prateći vod'),
            (r'JEDINICE\s+ZA\s+VEZU', 'Jedinice za vezu'), (r'^MUZIKA', 'Muzika')]
END = re.compile(r'POPUNA\s+BRIGADE')
# the brigade staff (p. 1, the book's p. 291), typed: number, duty, surname, father, given name
STAFF = [(1, 'Komandant brigade', 'Jovanović', 'Danila', 'Božo'), (2, 'Politkomesar brigade', 'Petrović', 'Ivana', 'Mato'),
         (3, 'Zamjenik komandanta brigade', 'Boreta', 'Nika', 'Joko'),
         (4, 'Pom. politkom. brigade', 'Mihaljević', 'Sava', 'Jovo'), (5, 'Nač. štaba brigade', 'Janjević', 'Đurice', 'Vojin'),
         (6, 'Pom. politkom. brigade', 'Medigović', 'Sava', 'Milo'), (7, 'Sekretar SKOJ-a brigade', 'Danilović', '', 'Božo'),
         (8, 'Oficir OZNE brigade', 'Šoljaga', 'Laza', 'Stevo'), (9, 'Sekretar SKOJ-a brigade', 'Rizoniko', 'Anta', 'Marija'),
         (10, 'Obavještajni oficir brigade', 'Rajčević', 'Radojice', 'Vuksan'),
         (11, 'Intendant brigade', 'Vuksanović', 'Boža', 'Mitar')]
# a duty's word (else the cell is a ditto mark the OCR read as letters: "m", "ša", "»", "4,", "#6")
DUTY_WORD = re.compile(r'^(?:[A-ZČĆŽŠĐa-zčćžšđ]{4,}[.,]?|Šef|šef|Pom\.|Zam\.|Ref\.|Kom\.|Nač\.|Sek\.|Pol\.|ofic\.|bat\.|brig\.|'
                       r'boln\.|sanit\.|batalj\.|čet|md\.|pozad\.|person\.|politič\.|kom\.|SKOJ-a|OZNE|voda|čete)$')
# a word that names a duty (the rest of the cell, "čete", "brigade", follows it)
DUTY = re.compile(r'(?:borac|vodnik|vvodnik|desetar|d\w?le\w?gat|komandir|komandant|politkom|politič|pom\.|zam\.|zamj|'
                  r'zamjenik|bolničar|kurir|kapelnik|ekonom|obav|sekretar|sek\.|intendant|ref\.|referent|upravnik|'
                  r'apotekar|kuvar|magaciner|telefonista|fotoreporter|šifrant|šef|oficir|nač\.|rukov|glavna|četna|'
                  r'muzičar|trubač|bubnjar|vozač|kovač|krojač|obućar|pekar|mesar|berberin|stražar|tumač|pisar|daktilograf)')
CORPUS: Corpus | None = None
QUOTES = '\'"„“”«»'


NAMELIKE = re.compile(r'-?[A-ZČĆŽŠĐ][a-zčćžšđ]+|[A-ZČĆŽŠĐ]\.$|ll[a-z]')


def has_name(e: dict, least: int = 1) -> bool:
    return sum(1 for w in e['name_words'] if NAMELIKE.match(w[4].strip(QUOTES + ' '))) >= least


def is_heading(text: str) -> str | None:
    for pat, name in HEADINGS:
        if re.search(pat, text) and not re.match(r'^\d{1,4}[a.,]', text.replace('1. BATALJON', '').strip()[:0] or 'x'):
            return name
    return None


def column_lines(page: dict, col: int) -> list[dict]:
    lines = [ln for ln in page['lines'] if ln['col'] == col]
    head = next((ln['top'] for ln in lines if re.fullmatch(r'\W*1\W+2\W+3\W*', ' '.join(w[4] for w in ln['words']))), None)
    start = (head + 3) if head is not None else 165
    return [ln for ln in lines if ln['top'] > start]


def entries_of(page: dict, pno: int, col: int, state: dict) -> list[dict]:
    lines = column_lines(page, col)
    # the column's x: its numbers' and its names' (the commonest start of a word well right of the numbers)
    nums = [ln['words'][0][0] for ln in lines if ln['words'] and NUMBER.match(ln['words'][0][4])]
    if not nums:
        return []
    num_x = Counter(round(x) for x in nums).most_common(1)[0][0]
    starts = Counter(round(w[0] / 2) * 2 for ln in lines for w in ln['words'] if w[0] > num_x + 50)
    name_x = starts.most_common(1)[0][0] if starts else num_x + 76
    out: list[dict] = []
    for ln in lines:
        words = ln['words']
        text = ' '.join(w[4] for w in words)
        if END.search(text):
            state['end'] = True
            break
        heading = is_heading(text) if not NUMBER.match(words[0][4]) or re.search(r'BATALJON', text) else None
        if heading and not re.search(r'[a-zčćžšđ]{3}', text.replace('BATALJON', '')):
            state['unit'] = heading
            continue
        # an entry starts at the numbers' column, whatever the OCR made of its number ("uu." for 1111.), or where a
        # line has a name and the entry before has one already (a number lost: "su brigade i Brozičević M. Branko");
        # a line whose first word is in small letters continues one (the rest of a duty: "čete", "bataljona"), as
        # does a given name that ran over to the next line
        while len(words) > 1 and (not re.search(r'[\w]', words[0][4]) or
                                  (len(words[0][4].strip('.,')) <= 2 and not re.search(r'\d', words[0][4]))):
            words = words[1:]                          # a speck before the number or the duty
        first = words[0]
        named = sum(1 for w in words if w[0] >= name_x - 6 and NAMELIKE.match(w[4].strip(QUOTES + ' ')))
        if (first[0] < num_x + 7 and not re.match(r'[a-zčćžšđ]', first[4])) or (
                named >= 2 and (not out or has_name(out[-1]))):
            m = NUMBER.match(first[4])
            no = (m.group(1) + (m.group(2) or '')) if m else ''
            out.append({'no': no, 'page': pno, 'unit': state['unit'], 'duty_words': [], 'name_words': [],
                        'x0': first[0], 'top': ln['top'], 'x1': ln['x1'], 'bottom': ln['bottom']})
            if m or first[0] < num_x + 7:
                words = words[1:]                      # the number (else the line's first word is the duty's)
        elif not out:
            continue                                   # (a column's first line continues the last entry of the one
            #                                            before: rare, a wrapped given name; left out)
        e = out[-1]
        for w in words:
            (e['name_words'] if w[0] >= name_x - 5 else e['duty_words']).append(w)
        e['x1'] = max(e['x1'], ln['x1'])
        e['bottom'] = max(e['bottom'], ln['bottom'])
    # two entries the OCR ran into one line ("Bošković Marka Vlado Đuričković Gliga Sreten"): split; an entry
    # with no name (a number read twice, specks under the table's head) is none
    split = []
    for e in out:
        nw = e['name_words']
        k = next((i for i in range(3, len(nw)) if i >= 2 and re.match(r'[A-ZČĆŽŠĐ][a-zčćžšđ]+ić$|[A-ZČĆŽŠĐ][a-zčćžšđ]{3,}$',
                                                                         nw[i][4]) and len(nw) - i >= 2), None)
        if len(nw) >= 5 and k:
            second = dict(e, no='', name_words=nw[k:], duty_words=[], top=e['top'] + 6.5)
            e['name_words'] = nw[:k]
            split += [e, second]
        else:
            split.append(e)
    state.setdefault('dropped', []).extend(e for e in split if not has_name(e, 2))
    out = [e for e in split if has_name(e, 2)]
    # one printed line the OCR read twice, a few points apart ("1575 Barčić Vuka Nikola"): once
    out = [e for i, e in enumerate(out) if not (i and abs(e['top'] - out[i - 1]['top']) < 9 and
                                                [w[4] for w in e['name_words']] == [w[4] for w in out[i - 1]['name_words']])]
    # the duty: as written, or the one above where the cell holds a ditto mark
    for e in out:
        if e['unit'] != state.get('duty_unit'):
            state['duty'], state['duty_unit'] = '', e['unit']          # a new unit's list starts afresh
        real = [w[4] for w in e['duty_words'] if DUTY_WORD.match(w[4]) or w[4] in ('-', '—')]
        if any(DUTY.match(t.lower()) for t in real):
            duty = ' '.join(real).strip(' -—')
            duty = duty[:1].upper() + duty[1:].lower() if duty.isupper() else duty
            state['duty'] = duty
        e['duty'] = state['duty']
    return out


def name_of(words: list[list]) -> tuple[str, str, str, str]:
    """surname, father (as printed), given name, a note (a title, a bracket as printed: "(Krile)"); the OCR's specks
    dropped, and the full stops and commas it set after a name ("Dušan.", "Kašiković.", "M," for M.)"""
    toks = []
    for w in words:
        t = w[4].strip(QUOTES + ' ,;:!|')
        t = re.sub(r'^ll(?=[a-zčćžšđ])', 'Il', t)                       # "llija" = Ilija
        t = re.sub(r'^([A-ZČĆŽŠĐ][a-z]?),$', r'\1.', w[4].strip(' ')) if re.fullmatch(r'[A-ZČĆŽŠĐ][a-z]?,', w[4].strip(' ')) else t
        t = t.lstrip('-')
        if not re.fullmatch(r'[A-ZČĆŽŠĐ][a-zj]{0,2}\.', t):
            t = t.rstrip('.')                                            # "Dušan." (an initial keeps its stop)
        if t:
            toks.append(t)
    notes = [t for t in toks if t.startswith('(') or t.endswith(')')]
    toks = [t for t in toks if t not in notes]
    toks = [t for t in toks if re.search(r'[A-Za-zČĆŽŠĐčćžšđ]{2}', t) or re.fullmatch(r'[A-ZČĆŽŠĐ]\.', t)]
    titles = [t for t in toks if t.lower() in ('dr', 'ing', 'inž')]
    toks = [t for t in toks if t not in titles and t[:1].isupper()]
    note = ' '.join(titles + notes)
    if not toks:
        return '', '', '', note
    last = toks[0]
    if len(toks) >= 3:
        father, given = toks[1], ' '.join(toks[2:])
    else:
        father, given = '', ' '.join(toks[1:])
    c = CORPUS
    last = '-'.join(title(c.best(p, c.surnames, LAT)) for p in last.split('-'))
    if father and not father.endswith('.'):
        father = title(c.best(father, c.fathers, LAT))
    given = ' '.join(title(c.best(g, c.givens, LAT)) for g in given.split())
    return last, father, given, note


SCAN_FILE = HERE / 'ocr' / '1-bokeljska-spisak.scan.json'


def scan_fix(e: dict, last: str, father: str, given: str, note: str) -> tuple[str, str, str, str]:
    """A row read from the page image (SCAN_FILE: page, y = the row's top, x where two columns share a y)"""
    if not hasattr(scan_fix, 'rows'):
        scan_fix.rows = json.loads(SCAN_FILE.read_text(encoding='utf-8')) if SCAN_FILE.exists() else []
    for r in scan_fix.rows:
        if r['page'] == e['page'] and abs(r['y'] - (e['top'] - 1)) < 1.5 and ('x' not in r or abs(r['x'] - e['x0']) < 40):
            r['used'] = True
            return (r.get('last', last), r.get('father', father), r.get('given', given), r.get('note', note))
    return last, father, given, note


def read() -> list[dict]:
    ocr = ocr_scan.load(NAME)
    entries, state = [], {'unit': 'Štab brigade', 'duty': '', 'end': False}
    page1 = ocr['pages']['1']
    for no, duty, last, father, given in STAFF:
        w = next(w for ln in page1['lines'] for w in ln['words'] if w[4].strip(',.') == last)
        entries.append({'no': str(no), 'page': 1, 'unit': 'Štab brigade', 'duty': duty, 'typed': (last, father, given),
                        'x0': w[0], 'top': w[1], 'x1': w[2] + 60, 'bottom': w[3]})
    for pno in range(2, len(ocr['pages']) + 1):
        for col in (0, 1):
            if state['end']:
                break
            entries += entries_of(ocr['pages'][str(pno)], pno, col, state)
    DROPPED[:] = state.get('dropped', [])
    return entries


DROPPED: list[dict] = []


def lines(pdf_path: str, start_page: int, end_page: int | None) -> list[dict]:
    """run_parser's lines: one an entry, its text "§no§ unit | duty | surname | father | given | title\""""
    out = []
    for e in read():
        last, father, given, dr = e['typed'] + ('',) if 'typed' in e else scan_fix(e, *name_of(e['name_words']))
        text = f"§{e['no']}§ {e['unit']} | {e['duty']} | {last} | {father} | {given} | {dr}"
        out.append({'text': text, 'x': round(e['x0'], 1), 'y': round(e['top'] - 1, 1), 'page': e['page'],
                    'box': (round(e['x1'] + 1, 1), round(e['bottom'] + 1, 1))})
        BOXES[(e['page'], round(e['top'] - 1, 1))] = (round(e['x1'] + 1, 1), round(e['bottom'] + 1, 1))
    return out


BOXES: dict[tuple, tuple] = {}


def parse(text: str) -> dict:
    no, rest = re.match(r'^§(.*?)§\s*(.*)$', text).groups()
    unit, duty, last, father, given, dr = [p.strip() for p in rest.split('|')]
    duty_l = duty[:1].lower() + duty[1:] if duty else ''
    info = f'{unit}: {duty_l}' if duty_l else unit
    if dr:
        info += f'; {dr}'
    return _record(last, given, father, info)


def post(soldiers: list[dict]) -> list[dict]:
    for s in soldiers:
        box = BOXES.get((s['pdf_page'], s['pdf_y']))
        if box:
            s['pdf_x_end'], s['pdf_y_end'] = box
    return soldiers


def main() -> None:
    global CORPUS
    CORPUS = Corpus(skip_units=('1-bokeljska-soldiers.json',))
    if '--check' in sys.argv:
        ents = read()
        nos = [e['no'] for e in ents]
        print(len(ents), 'entries;', Counter(e['unit'] for e in ents))
        plain = [int(n) for n in nos if n.isdigit()]
        print('numbers', plain[:3], plain[-3:], 'missing', sorted(set(range(1, max(plain) + 1)) - set(plain))[:80])
        print('added:', [n for n in nos if n.endswith('a')], 'unreadable numbers:', nos.count(''))
        for e in DROPPED:
            print('  dropped', e['page'], round(e['top']), e['no'], [w[4] for w in e['duty_words']], [w[4] for w in e['name_words']])
        return
    unused = lambda: [r for r in getattr(scan_fix, 'rows', []) if not r.get('used')]
    run_parser(
        pdf_path=PDF, brigade_code=102, output_path=OUT, start_page=1, end_page=None,
        entry_start_re=re.compile(r'^§'), parse_entry_fn=parse, extract_fn=lines, post_fn=post,
        id_start=10001, keep_other_sources=True)
    assert not unused(), f'hand readings that fit no row: {unused()}'


if __name__ == '__main__':
    main()
