"""
Parser: 7. srpska (5. južnomoravska) NOU brigada (brigade code 85).

Source: Đura Zlatković, Miloš D. Bakić, "Sedma srpska brigada" (znaci.org 00001/277_6.pdf, its pages 2-44, book
        pp. 459-501)  →  website/public/pdfs/7-srpska.pdf. Cyrillic, two lists:
    pp. 1-11    "Spisak boraca Pete južnomoravske (Sedme srpske) brigade početkom maja 1944. godine", by village,
                numbered within each village, two names a line:
                    BROD - Crna Trava:
                    1. Anđelković Đura          23. Milutinović Tihomir
                    2. Dinčić I. Dragiša        24. Mitrović Aleksandar
                (the names of the fallen are set in bold, which the text layer doesn't keep)
    pp. 12-43   "Spisak poginulih, umrlih i nestalih boraca Sedme srpske brigade NOVJ", numbered, a hanging indent:
                    12. ANTIĆ Stanoja ŽIVOJIN, (10.7. 1909. u s. Šarkamenu kod Negotina), u NOB od 20. 10. 1944,
                        poginuo decembra 1944. na Drini kod Ljubovije.
A roster line holds two names, so the parser reads the roster itself (a name starts at its number after a wide gap;
a number after a surname is the father's initial З, "Janić 3. Božidar") and gives every entry its own box
(entry_boxes.INLINE_ENTRIES).
"""
import re
from collections import Counter, defaultdict
from itertools import product

import pdfplumber

from _parser_scaffold import _fold, _load_name_reference, _record, death_type_from_text, repair_cyrillic_ocr, run_parser
from pdf_coords import viewer_offset

U, L = 'A-ZČĆŽŠĐ', 'a-zčćžšđ'
ROSTER_TO = 11
LINES: list[dict] = []                                                       # every line (and roster item) with its extent


def extract(pdf_path: str, start_page: int, end_page: int | None) -> list[dict]:
    out: list[dict] = []
    with pdfplumber.open(pdf_path) as pdf:
        stop = min(end_page, len(pdf.pages)) if end_page else len(pdf.pages)
        for n in range(start_page - 1, stop):
            page = pdf.pages[n]
            dx, dy = viewer_offset(page)
            if n + 1 > ROSTER_TO:
                for ln in page.extract_text_lines(strip=True, return_chars=False):
                    if ln['text'].strip():
                        item = {'text': ln['text'], 'x': round(ln['x0'] - dx, 1), 'y': round(ln['top'] - dy, 1), 'page': n + 1,
                                'x1': round(ln['x1'] - dx, 1), 'bottom': round(ln['bottom'] - dy, 1)}
                        out.append(item)
                continue
            rows = defaultdict(list)
            for w in page.extract_words(x_tolerance=1.5):
                rows[round(w['top'] / 3)].append(w)
            for key in sorted(rows):
                ws = sorted(rows[key], key=lambda w: w['x0'])
                items: list[list[dict]] = []
                for prev, w in zip([None] + ws[:-1], ws):
                    if prev is None or (w['x0'] - prev['x1'] > 20 and re.fullmatch(r'\d+[.,]?', w['text'])):
                        items.append([w])                                    # a name starts at its number after a gap
                    else:
                        items[-1].append(w)
                for it in items:
                    out.append({'text': ' '.join(w['text'] for w in it), 'x': round(it[0]['x0'] - dx, 1),
                                'y': round(min(w['top'] for w in it) - dy, 1), 'page': n + 1,
                                'x1': round(it[-1]['x1'] - dx, 1), 'bottom': round(max(w['bottom'] for w in it) - dy, 1)})
    LINES.extend(out)
    return out


_state = {'village': ''}
VILLAGES = {'CRNL TRAVA': 'Crna Trava', 'CRVENAJABUKA': 'Crvena Jabuka', 'DOBROVIŠ (i Stranjevo)': 'Dobroviš',
            'GJRESLAP': 'Preslap', 'JLBUKOVIK': 'Jabukovik', 'SGRELAC': 'Strelac', 'PETROVAC (kod Pirota)': 'Petrovac, Pirot',
            'RAVNA GORA (Vlasotinačka)': 'Ravna Gora, Vlasotince'}                 # the roster's headings, as the fallen list spells them


def keep(ln: dict) -> bool:
    t = ln['text'].strip()
    page = ln['page']
    if re.fullmatch(r'[\d\W]{1,5}|\W*\w{0,2}\W*', t) or t.startswith(('S P I S A K', 'SPISAK', '- *', '*')) \
            or re.match(r'^(?:BORACA PETE|POČETKOM MAJA|POGINULIH, UMRLIH|SRPSKE BRIGADE NOVJ|Imena poginulih|Podaci za)', t):
        return False                                                         # headings, footnotes, page numbers
    if page <= ROSTER_TO:
        if not re.match(r'^\d', t):
            if re.match(rf'^[{U}]{{2,}}', t):
                v = t.rstrip(':').strip()                                    # "BROD- Crna Trava:", "VLASINA"
                _state['village'] = VILLAGES.get(v, v)
            return False
        ln['text'] = f'§r§{_state["village"]}§ ' + t
        return True
    if ln['page'] == ROSTER_TO + 1 and ln['y'] > 560:
        return False
    if re.match(rf'^\d+[a-zа]?\.\s*[{U}]{{2,}}', t):
        t = '§p§ ' + t
    ln['text'] = t
    return True


def roster(text: str) -> dict:
    village, _, item = text[3:].partition('§ ')
    item = re.sub(r'^\d+[.,]?\s*', '', item.strip())
    item = re.sub(rf'(?<=\s)3\.(?=\s)', 'Z.', item)                           # the initial З read as the digit
    notes = []
    m = re.search(r'\s+-\s*[„"]?([^"“”]+?)[“”"]?\s*$', item)                  # "Stevo - „Bukarka"", "Mladenović Đ. Ranđel - Čelik"
    if m:
        notes.append('zvani ' + m.group(1).strip())
        item = item[:m.start()]
    item = re.sub(rf'\b([{U}][{L}]+) ([{L}]{{2,4}})\b', r'\1\2', item)       # "Drag iša"
    alt = re.search(rf'\s*\(([{U}][{L}]+)\)', item)                          # "Ranđelović (Veljić) Milovan"
    if alt:
        notes.append('ili ' + alt.group(1))
        item = item[:alt.start()] + item[alt.end():]
    toks = item.split()
    last = toks[0] if toks else ''
    father = toks[1] if len(toks) > 2 and re.fullmatch(INITIAL, toks[1]) else ''
    rest = [t for t in toks[1:] if t != father]
    given = rest[0] if rest else ''
    if len(rest) > 1:
        notes.append('zvani ' + ' '.join(rest[1:]))
    place = re.sub(r'\s*-\s*', ', ', village).strip(' ,')
    place = ', '.join(p.strip().title() if p.strip().isupper() else p.strip() for p in place.split(','))
    rec = _record(last, given, initial(father), '; '.join(notes + ([f'iz {place}'] if place else [])))
    if place:
        rec['_village'] = place
    return rec


INITIAL = rf"(?:[{U}]|Lj|Nj|Dž|Jb|JB|II|Ii|G1|11|3|[jl])[.,]?'?"             # "Lj.", "Jb." (Љ), "II." (П), "3." (З)


def initial(tok: str) -> str:
    tok = tok.rstrip(".,'")
    return {'Jb': 'Lj', 'JB': 'Lj', 'II': 'P', 'Ii': 'P', 'G1': 'P', '11': 'N', '3': 'Z', 'j': 'J', 'l': 'L'}.get(tok, tok) + '.' if tok else ''


def fallen(text: str) -> dict:
    text = re.sub(r'^§p§\s*\d+[a-zа]?\.\s*', '', text)
    text = re.sub(r'(?<=[a-zčćžšđ])-\s+(?=[a-zčćžšđ])', '', text)            # "zemljo- radnik"
    text = text.replace('^9', '(19')                                          # "DIMITRIJE ^926 s. Krivelj"
    text = re.sub(r'(?<=\d)\.\s*G\.', '. godine.', text)                      # "poginuo 3. 3. 1945.G."
    notes = []
    alt = re.match(rf'^([{U}]{{2,}})\s+\(([{U}]{{2,}})\)\s*', text)            # "CVETKOVIĆ (MILČIĆ) BRANISLAV"
    if alt:
        notes.append('ili ' + alt.group(2).title())
        text = alt.group(1) + ' ' + text[alt.end():]
    m = re.search(r'\s*\(|,|\s+(?=iz\s|poginu|umr|nesta|streljan|borac\s)', text)
    head, rest = (text[:m.start()], text[m.start():].lstrip(', ')) if m else (text, '')
    head = re.sub(rf'^([{U}]{{2,}})\s+([{U}]{{2,}})\s*-', r'\1\2-', head)     # "AL EKSIĆ-STOJANOVIĆ"
    nick = re.search(rf'\s+-\s*([{U}][{L}]+)?\s*$', head)                      # "MARINKO - Mika", "GRADA - "
    if nick:
        if nick.group(1):
            notes.append('zvani ' + nick.group(1))
        head = head[:nick.start()]
    toks = head.split()
    caps = []
    while toks and re.fullmatch(rf'[{U}]{{2,}}(?:-[{U}]{{2,}})?', toks[0]):
        caps.append(toks.pop(0))
    father = ''
    if toks and re.fullmatch(INITIAL, toks[0]) and len(toks) > 1:
        father = initial(toks.pop(0))                                        # "M.", "Lj.", "j."
    elif toks and re.fullmatch(rf'[{U}][{L}]+', toks[0]) and (len(toks) > 1 or len(caps) < 2):
        father = toks.pop(0)                                                 # "Stanoja"
    given = ' '.join(toks)
    if len(caps) >= 2 and (not given or re.fullmatch(rf'[{U}][{L}]+(?:\s+[{U}][{L}]+)*', given)):
        if given:
            notes.append('zvani ' + given)                                   # "IGNJATOVIĆ NIKODIJE Profir"
        given = caps.pop()                                                   # "ARIZANOVIĆ NIKOLA"
    if not given and father and re.fullmatch(rf'[{U}][{L}]+', father):
        given, father = father, ''
    last = ''.join(caps) if len(caps) > 1 and any(len(c) <= 3 for c in caps) else ' '.join(caps)
    rec = _record(last, given, father, '; '.join(notes + ([rest.strip()] if rest.strip() else [])))
    y = re.search(r'\((?:\d{1,2}\.\s*\d{1,2}\.\s*)?(1[89]\d\d)', rest)
    if y:
        rec['birth_year'] = y.group(1)
    dt = death_type_from_text(rest)
    rec['death_type'] = dt or ('umro' if re.search(r'samoubi|umr', rest) else 'poginuo')
    b = re.match(rf'^\(?(?:rođen[a]?\s+)?(?:[^,)]*?1[89]\d\d\.?\s*(?:godine)?[,.]?\s*)?(?:(u|iz)\.?\s*)?(?:(s\.|s(?=\s)|sela|selo)\s*)?([{U}][^,()]*?)(?:\s*(?:,|-|kod)\s*([{U}][^,()]*?))?\s*[,)]', rest)
    if b:
        rec['_birth'] = (b.group(1) or '', bool(b.group(2)), b.group(3).strip(), (b.group(4) or '').strip())
    return rec


def parse(text: str) -> dict:
    return roster(text) if text.startswith('§r§') else fallen(text)


def _known_places() -> Counter:
    import json
    from pathlib import Path
    from scripts.name_utils import BRIGADE_CONFIGS
    known = Counter()                                                        # the places the other units print, a file at a time
    for code, cfg in BRIGADE_CONFIGS.items():
        f = Path('website/public') / cfg['json_file']
        if code != 85 and f.exists():
            for s in json.loads(f.read_text(encoding='utf-8')):
                for k in ('birth_place', 'death_place'):
                    for part in filter(None, (s.get(k) or '').split(', ')):
                        known[part] += 1
    return known


ODD = {'1': ('t', 'l', 'i'), '|': ('t',), "'": ('',), '>': ('u', 'j', 'lj'), '.': ('l', 't', ''), '^': ('',), ']': ('j',)}


def repair_names(soldiers: list[dict]) -> list[dict]:
    """Names the text layer spells with a digit or a sign for a Cyrillic letter ("Gol>bović" = Golubović,
    "S|amenković" = Stamenković, "Cve1Ković" = Cvetković, "JBubomir" = Ljubomir): the reading the reference units
    know best, in their spelling. Names no reading makes known stay as printed."""
    ref = _load_name_reference()
    for s in soldiers:
        for field in ('last_name', 'first_name'):
            v = s.get(field) or ''
            v2 = re.sub(r'^J[bB]', 'Lj', re.sub(r"^S'?\|", 'St', v)).replace('G1', 'P')   # "G1etronije" (Г1 = П)
            spots = [i for i, ch in enumerate(v2) if ch in ODD]
            if (v2 == v and not spots) or len(spots) > 3:
                continue
            best, hits = v2, 0
            for combo in product(*(ODD[v2[i]] for i in spots)):
                chars = list(v2)
                for i, r in zip(spots, combo):
                    chars[i] = r
                key = _fold(''.join(chars)).lower()
                counts = ref[field].get(key)
                if counts and sum(counts.values()) > hits:
                    best, hits = counts.most_common(1)[0][0], sum(counts.values())
            if hits or not spots:
                s[field] = best
        s['full_name'] = ' '.join(p for p in (s['last_name'], s['middle_name'], s['first_name']) if p)
    return soldiers


def post(soldiers: list[dict]) -> list[dict]:
    soldiers = repair_names(repair_cyrillic_ocr(soldiers))
    """Birthplaces in the nominative (the village after "u", the municipality after "kod", in the form the other units
    know), and each entry's box."""
    import sys
    sys.path.insert(0, 'scripts')
    from extract_structured_fields import Extractor
    known = _known_places()

    def nominative(word: str) -> str:
        forms = [' '.join(c) for c in product(*(Extractor._variants(Extractor, w) for w in word.split()))]
        forms = [f for f in forms if f != word and known[f] > known[word]]
        return max(forms, key=lambda f: known[f]) if forms else word

    for s in soldiers:
        village = s.pop('_village', '')
        if village:
            s['birth_place'] = village                                       # the roster's village (and its district)
        birth = s.pop('_birth', None)
        if birth:
            prep, sel, place, muni = birth
            place = nominative(place) if prep else place                     # "u s. Šarkamenu" = Šarkamen
            muni = nominative(muni) if muni and not known[muni] else muni    # "kod Negotina" = Negotin
            s['birth_place'] = place + (', ' + muni if muni and muni != place else '')
    by_page = defaultdict(list)
    for ln in LINES:
        by_page[ln['page']].append(ln)
    starts = {(s['pdf_page'], round(s['pdf_x'], 1), round(s['pdf_y'], 1)) for s in soldiers}
    for s in soldiers:
        lines = sorted(by_page.get(s['pdf_page'], []), key=lambda ln: (ln['y'], ln['x']))
        i = next((k for k, ln in enumerate(lines) if abs(ln['x'] - s['pdf_x']) < 1 and abs(ln['y'] - s['pdf_y']) < 1), None)
        if i is None:
            continue
        mine = [lines[i]]
        if s['pdf_page'] > ROSTER_TO:
            for ln in lines[i + 1:]:
                if (ln['page'], round(ln['x'], 1), round(ln['y'], 1)) in starts or ln['y'] - mine[-1]['y'] > 14 or ln['y'] > 560:
                    break
                mine.append(ln)
        s['pdf_x_end'] = max(ln['x1'] for ln in mine)
        s['pdf_y_end'] = max(ln['bottom'] for ln in mine)
    return soldiers


if __name__ == '__main__':
    run_parser(
        pdf_path='website/public/pdfs/7-srpska.pdf',
        brigade_code=85,
        output_path='website/public/7-srpska-soldiers.json',
        start_page=1,
        end_page=None,
        layout='single',
        extract_fn=extract,
        script='cyrillic',
        entry_start_re=re.compile(r'^§[rp]§'),
        parse_entry_fn=parse,
        line_filter=keep,
        post_fn=post,
    )
