"""
Parser: Četvrti pomorski obalni sektor (IV POS) Mornarice NOVJ (brigade code 168).

Source: Kažimir Pribilović, "Četvrti pomorski obalni sektor Mornarice NOVJ" (znaci.org 00003/652, the appendices
        652_1.pdf) →  website/public/pdfs/4-pomorski-sektor.pdf (book pp. 418-478):
    pp. 2-55    Prilog II, "Borci IV pomorskog obalskog sektora 1943-1945.": the joint list of the Sekcija boraca and
                the author, 4,702 names, two columns, each entry hanging:
                    ABAZA Ivana ANTE, Prapratnica, Trogir
                    ALA VAN JA Šimuna BISER, Ugljan, o.
                        Ugljan
                (the surname in capitals, the father in the genitive or his initial, the given name in capitals, a
                nickname in »«; where he came from, the island after "o.")
    pp. 56-61   Prilog III, "Poginuli i umrli borci IV POS-a 1943-1945": the name and birth on the left, the duty and
                the death on the right at the same height:
                    ALAČ Ivana ANTE, r. 1922, Drašni-     - mornar-mitraljezac PĆ-54 »Turist«, Primorska
                    ce, Makarska                            flotila IV POS-a, poginuo 15. 12.1943. u uvali ...
                The roster leaves them out (4,624 + 79: the book's 4,702 give or take one).
The parser boxes each entry (both columns for the fallen): the PDF is in entry_boxes.INLINE_ENTRIES.
The OCR reads LJ as U in capitals (MIUENKO, DRAŽICA-UUBO; repair_lj_ocr) and breaks some surnames (ALA VAN JA).
"""
import re
import unicodedata
from collections import Counter
from pathlib import Path

import pdfplumber

from _parser_scaffold import _record, find_gutter, repair_lj_ocr, run_parser, title_case
from pdf_coords import viewer_offset

U, L = 'A-ZČĆŽŠĐ', 'a-zčćžšđ'
FALLEN_FROM = 56                                   # the PDF page where Prilog III starts
LINE = 10.0
BOXES: dict[tuple, dict] = {}                     # (page, y, x) of an entry's first line → its box


def fold(text: str) -> str:
    t = (text or '').lower().replace('đ', 'dj')
    return ''.join(c for c in unicodedata.normalize('NFD', t) if not unicodedata.combining(c))


def _corpus() -> tuple[Counter, Counter, Counter]:
    last, given, spelled = Counter(), Counter(), Counter()
    import json
    for f in Path('website/public').glob('*soldiers.json'):
        if f.name.startswith('4-pomorski'):
            continue
        for s in json.loads(f.read_text(encoding='utf-8')):
            last[fold(s.get('last_name'))] += 1
            given[fold(s.get('first_name'))] += 1
            spelled[s.get('last_name')] += 1
    return last, given, spelled


SURNAMES, GIVEN, SPELLED = _corpus()
# names the text layer garbled past the rules, read from the page image (the OCR's text → the page's)
SCAN = {'DFI FNTĆ ANTF': 'DELENIĆ ANTE', 'MORA VICA NIKŠA': 'MORAVICA NIKŠA', 'TRA VAŠ IVAN': 'TRAVAŠ IVAN',
        'TOP \\': 'TOMA', 'PETE! Petra': 'PETEJ Petra', 'BATALIJOŠKO': 'BATALI JOŠKO', 'DALEIVKA': 'ĐALE IVKA',
        'KOVAĆPAVE': 'KOVAČ PAVE', 'ZGAGAFRANC': 'ZGAGA FRANC', 'BRESSINI - Sambucini Mauro': 'BRESSINI-SAMBUCINI MAURO'}


def _lines(page, offset, keep) -> list[dict]:
    dx, dy = offset
    sub = page.filter(lambda o: o.get('object_type') != 'char' or keep(o['x0'] - dx))
    out = []
    for ln in sub.extract_text_lines(strip=True, return_chars=False):
        t = ln['text'].replace('­', '-').strip()
        if t:
            out.append({'text': t, 'x': round(ln['x0'] - dx, 1), 'x1': round(ln['x1'] - dx, 1),
                        'y': round(ln['top'] - dy, 1), 'y1': round(ln['bottom'] - dy, 1)})
    return out


def _junk(t: str) -> bool:
    return bool(re.fullmatch(r'\d{1,3}|BORCI|IV POS-a|PRILOG III|POGINULI I|UMRLI BORCI IV POS-a|1943-1945|n/m', t))


def _starts(t: str) -> bool:
    w = t.split()[0] if t.split() else ''
    letters = [c for c in w if c.isalpha()]
    if len(letters) >= 2 and sum(c.isupper() for c in letters) / len(letters) >= 0.7:
        return True
    # a whole name in small letters ("kućina s. zvonko", "kukanović ivo"), or a speck before it ("rjAUS MATE")
    return bool(re.match(rf'^[{L}]{{1,2}}[{U}]{{2,}}|^[{L}]+(?:ić|ović|ević)\b', t))


def _box(page: int, rows: list[dict], first: dict) -> None:
    BOXES[(page, first['y'], first['x'])] = {
        'pdf_x_end': max(r['x1'] for r in rows), 'pdf_y_end': max(r['y1'] for r in rows) + 1.5}


def extract(pdf_path: str, start: int, end: int | None) -> list[dict]:
    out = []
    with pdfplumber.open(pdf_path) as pdf:
        stop = min(end or len(pdf.pages), len(pdf.pages))
        for pn in range(start, stop + 1):
            page = pdf.pages[pn - 1]
            off = viewer_offset(page)
            gut = find_gutter(page, off)
            cols = [_lines(page, off, lambda x: x < gut), _lines(page, off, lambda x: x >= gut)]
            cols = [[ln for ln in c if not _junk(ln['text'])] for c in cols]
            if pn < FALLEN_FROM:
                for col in cols:
                    if not col:
                        continue
                    xs = sorted(ln['x'] for ln in col)
                    left = xs[len(xs) // 10]
                    groups = []
                    for ln in col:                                 # entries hang: a flush line starts one
                        new = ln['x'] < left + 5 and not re.match(r'^(?:o[.,]\s|[^\w»(]+$)', ln['text'])
                        if new or not groups:
                            groups.append([ln])
                        else:
                            groups[-1].append(ln)
                    for g in groups:
                        _box(pn, g, g[0])
                        for i, ln in enumerate(g):
                            out.append({'text': ('§r§ ' if i == 0 else '') + ln['text'],
                                        'x': ln['x'], 'y': ln['y'], 'page': pn})
            else:
                left, right = cols
                heads = [ln for i, ln in enumerate(left)               # not "»DRAGO- / MAN«, r. 19. 4. 1904."
                         if _starts(ln['text']) and not re.match(rf'^»|^[{U}]+«', ln['text'])
                         and not (i and left[i - 1]['text'].endswith('-'))]
                groups = {id(h): [h] for h in heads}
                for ln in left + right:
                    if ln in heads:
                        continue
                    above = [h for h in heads if h['y'] <= ln['y'] + 3]
                    if above:
                        groups[id(max(above, key=lambda h: h['y']))].append(ln)
                    elif out:                                      # the last entry of the page before runs on
                        out.append({'text': ln['text'], 'x': ln['x'], 'y': ln['y'], 'page': pn})
                for h in heads:
                    g = groups[id(h)]
                    lft = [ln for ln in g if ln['x'] < gut]
                    rgt = [ln for ln in g if ln['x'] >= gut]
                    _box(pn, g, h)
                    for i, ln in enumerate(lft + rgt):
                        mark = '§f§ ' if i == 0 else ('§d§ ' if ln is (rgt[0] if rgt else None) else '')
                        out.append({'text': mark + ln['text'], 'x': ln['x'], 'y': ln['y'], 'page': pn})
    return out


NICK = re.compile(r'\s*(»[^«]*«?|\([^)]*\))')


def _caps(w: str) -> bool:
    letters = [c for c in w if c.isalpha()]
    return len(letters) >= 1 and sum(c.isupper() for c in letters) >= 0.7 * len(letters)


def _join_given(ws: list[str]) -> list[str]:
    """The OCR spaces some given names apart: "SLA VOMIR", "PA VAL", "C VITAN", "LJUBOM IR". Other books' OCR left
    such fragments in the corpus too ("Sla" 8, "Slavomir" 21), so the whole name must be the far commoner one."""
    ws, i = list(ws), 0
    while i < len(ws) - 1:
        a, b = ws[i], ws[i + 1]
        if (GIVEN[fold(a + b)] >= 2 and GIVEN[fold(a + b)] > 2 * min(GIVEN[fold(a)], GIVEN[fold(b)])) or len(a) <= 2:
            ws[i:i + 2] = [a + b]
        else:
            i += 1
    return ws


def lj(w: str) -> str:
    """The OCR reads LJ as U in capitals; a doubled U is always one: UUBO = LJUBO, PEUUK = PELJUK, ŽUUEVIĆ =
    ŽULJEVIĆ, RAKUUIĆ = RAKULJIĆ, BUUUŠIĆ = BULJUŠIĆ. (A single one is read back from the corpus: repair_lj_ocr.)"""
    w = re.sub(r'(?<![A-ZČĆŽŠĐ])UU', 'LJU', w)
    w = re.sub(r'UU(?=[AEIOU])', 'ULJ', w)
    return re.sub(r'UU', 'LJU', w)


def name(head: str):
    """SURNAME Father GIVEN »NICK«  /  SURNAME F. GIVEN  /  SURNAME GIVEN  /  "kućina s. zvonko".
    Returns the name and the words after it that are no part of it (a place the comma before was lost)."""
    nicks = [n.strip('»«() ') for n in NICK.findall(head)]
    head = NICK.sub(' ', head)
    words = head.replace(',', ' ').split()
    father, extra = '', []
    if not any(sum(c.isupper() for c in w) >= 2 for w in words):          # the whole name in small letters
        words = [w.upper() for w in words]
        if len(words) >= 3 and re.fullmatch(rf'[{U}]\.', words[1]):
            father, words = words[1].rstrip('.'), words[:1] + words[2:]
        last_words, given_words = words[:1], words[1:]
    else:
        ti = next((i for i, w in enumerate(words[1:], 1) if re.fullmatch(rf'[{U}][{L}]+', w)), None)
        ii = next((i for i, w in enumerate(words[1:-1], 1) if re.fullmatch(rf'[{U}]\.?|[LNlnD][jJžŽ]\.', w)), None)
        if ti is not None and (ii is None or ii > ti or ii == ti - 1 and len(words[ii]) == 1):
            father, last_words, given_words = words[ti], words[:ti], words[ti + 1:]   # "CUKRO V Jere NJEGOSLAV"
        elif ii is not None:
            father, last_words, given_words = words[ii].rstrip('.'), words[:ii], words[ii + 1:]
        else:
            last_words, given_words = words[:1], words[1:]
            while len(given_words) >= 2 and (SURNAMES[fold(''.join(last_words + given_words[:1]))]
                                             or re.fullmatch(r'(?:L?I[ĆC]|VI[ĆC]|JA|NJA|KO)', given_words[0])
                                             or len(given_words[0]) <= 2):
                last_words.append(given_words.pop(0))           # "ANDRIJO LIĆ MARIN", "MEN AC PETAR"
        k = next((i for i, w in enumerate(given_words) if not _caps(w)), len(given_words))
        given_words, extra = given_words[:k], given_words[k:]               # "BUBLE Ante ANTE Split"
        if not given_words and extra:                                       # "PRŽEN ratko"
            given_words, extra = extra[:1], extra[1:]
        if not given_words and father and len(father) > 2:                  # "VRGA Spiro", "BOTICA Nikola »MUŠKO«"
            given_words, father = [father], ''
    last = ''.join(last_words)
    last = re.sub(r'^[a-zčćžšđ]{1,2}(?=[A-ZČĆŽŠĐ]{2})', '', last)   # "rjAUS", "iPAVEC": a speck
    last = re.sub(r'^[38](?=[0O])', 'B', last).replace('0', 'O').replace('1', 'I')   # "30RĆIĆ"
    last = lj(re.sub(r"[^\w-]", '', last))
    given = lj(' '.join(_join_given([w.replace('1', 'I') for w in given_words])))
    fix = lambda w: title_case(w.upper()) if w else w
    last = fix(last)
    if last.endswith('ic') and SPELLED[last[:-1] + 'ć'] > SPELLED[last]:
        last = last[:-1] + 'ć'                                            # "SABLlC": the caron lost with the l
    return last, fix(given), father, nicks, ' '.join(extra)


def place(parts: list[str]) -> str:
    """'Prapratnica', 'Trogir' → 'Prapratnica, Trogir'; 'Zlarin', 'o. Zlarin' → 'Zlarin'; the island without "o."."""
    parts = [re.sub(r'^o[.,]\s*', '', p).strip(' .') for p in parts if p.strip(' .')]
    parts = [p for p in parts if not re.match(r'^(?:žena|rođ\.|r\.|\d)', p)]
    if len(parts) >= 2 and parts[0] == parts[1]:
        parts = parts[:1] + parts[2:]
    return ', '.join(parts)


def parse_entry(text: str) -> dict:
    kind = text[1]
    text = re.sub(r'^§[rf]§\s*', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    for a, b in SCAN.items():
        if text.startswith(a):
            text = b + text[len(a):]
    text = text.translate(str.maketrans('àèìòùÀÈÌÒÙ', 'aeiouAEIOU'))       # "ANDRÒ", "Jurjà": specks read as accents
    text = text.replace('--', '-')                                         # "DINKO- / -ANTE"
    duty = ''
    if kind == 'f':
        text, _, duty = text.partition('§d§')
        duty = re.sub(r'^\s*-\s*', '', duty).strip()
        text = text.strip()
    head, _, rest = text.partition(',')
    head = re.sub(r'»([^«]*)«', lambda m: '»' + re.sub(r'-\s*', '', m.group(1)) + '«', head)   # "»ČANGALI- / JA«"
    head = re.sub(rf'(?<![»\w-])([{U}][{U}-]+«)', r'»\1', head)             # the » lost at a line's start
    if re.fullmatch(r'\s*[A-ZČĆŽŠĐ]{2,}(?:-[A-ZČĆŽŠĐ]+)?\s*', rest.split(',')[0] or '') and len(head.split()) <= 2:
        head, rest = head + ' ' + rest.split(',')[0].strip(), ','.join(rest.split(',')[1:])   # "LESIĆ Vicka, IVAN, ..."
    if re.fullmatch(rf'[{U}]{{2,}}\s+[{U}]\.', head.strip()):
        head = head.strip()[:-1] + '_'                                     # "VIDOVIĆ A.": the given name an initial
    last, given, father, nicks, extra = name(head)
    given = given.replace('_', '.')
    if not last or not given:
        return {}
    rest = ', '.join(x for x in (extra, rest.strip(' ,')) if x)
    rest = re.sub(r'\bo,\s', 'o. ', rest)
    notes = [f'zvani {title_case(n.upper())}' for n in nicks if n]
    info = '; '.join(notes + ([rest] if rest else []) + ([duty] if duty else []))
    rec = _record(last, given, father, info)
    parts = [p.strip() for p in rest.split(',')]
    if kind == 'f':
        born = re.match(r'^r\.\s*((?:\d{1,2}\.\s*){0,2}(1[89]\d\d))\.?$', parts[0]) if parts else None
        if born:
            rec['birth_year'] = born.group(2)
            parts = parts[1:]
        else:
            m = re.match(r'^r\.\s*', parts[0]) if parts else None
            if m:                                                  # "r. 6. 11. 1911" with the year on the next line
                parts = parts[1:]
        died = re.search(r'\b(poginu\w*|umr\w*|ubijen\w*|strijeljan\w*|nestao)\b', duty, re.I)
        if died:
            rec['death_type'] = death_word(died.group(1))
            d = re.search(r'(?:noću\s+)?(?:\d{1,2}/)?(\d{1,2})\.\s*(\d{1,2})\.\s*(19\d\d)', duty[died.end():died.end() + 40])
            y = re.search(r'\b(19\d\d)\b', duty[died.end():died.end() + 30])
            if d:
                rec['death_date'] = f'{int(d.group(1))}. {int(d.group(2))}. {d.group(3)}'
            elif y:
                rec['death_date'] = y.group(1)
            after = re.sub(r'^\s*(?:noću\s+)?(?:(?:\d{1,2}/)?\d{1,2}\.\s*\d{1,2}\.\s*)?19\d\d\.?', '', duty[died.end():])
            at = re.match(r'\s*((?:u|kod|na|između|ispred|blizu)\s+.+?)(?=\s+(?:od|prilikom|kada|kad|nesretnim|zbog|'
                          r'gdje|kao|pri|uslijed|za vrijeme|noću|u borbi)\b|\s+\d|[,;]|(?<!\bo)(?<!\bSv)\.(?:\s|$)|$)', after)
            if at:                                                 # "u Sućurju na Hvaru", not "... od artiljerijske vatre"
                where = at.group(1).strip()
                rec['death_place'] = where + (')' if where.count('(') > where.count(')') else '')
        rec['_list'] = 'fallen'
    p = place(parts)
    if p and not re.search(r'\d', p):
        rec['birth_place'] = p
    return rec


def death_word(w: str) -> str:
    w = w.lower()
    return ('umro' if w.startswith('umr') else 'streljan' if w.startswith('strij') else 'nestao' if w == 'nestao'
            else 'poginuo')                                        # poginuo, ubijen


def post(soldiers: list[dict]) -> list[dict]:
    for s in soldiers:
        s.pop('_list', None)
        box = BOXES.get((s.get('pdf_page'), s.get('pdf_y'), s.get('pdf_x')))
        if box:
            s.update(box)
    return repair_lj_ocr(soldiers)


if __name__ == '__main__':
    run_parser(
        pdf_path='website/public/pdfs/4-pomorski-sektor.pdf',
        brigade_code=168,
        output_path='website/public/4-pomorski-sektor-soldiers.json',
        start_page=2,
        end_page=None,
        extract_fn=extract,
        script='latin',
        entry_start_re=re.compile(r'^§[rf]§'),
        parse_entry_fn=parse_entry,
        post_fn=post,
    )
