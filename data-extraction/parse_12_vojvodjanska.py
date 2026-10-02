"""
Parser: 12. vojvođanska udarna brigada (brigade code 75).

Source: Branislav Popov Miša, "12. vojvođanska udarna brigada" (znaci.org 00003/443.pdf, PDF pages 207-258)
        →  website/public/pdfs/12-vojvodjanska.pdf:
    pp. 1-33    "Spisak boraca 12. vojvođanske udarne brigade": names only, under the place each lived in before joining
                (the book's note: where that wasn't known, where they lived after the war). The place is centered, the
                names in two columns under it (a single name centered):
                        ALIBUNAR
                    ČUBRILOVIČ Bogosav      PETROVIČ Nedeljko
    pp. 34-52   "Spisak poginulih": a soldier a line or two
                    ACANSKI Radomir iz Sombora, rođ. 1919, poginuo kod Koprivnice.
The roster's place goes into the bio, not into birth_place (it is no birthplace); a fallen soldier "iz Sombora" is
read as from Sombor, as in the other books. A soldier on both lists is merged (see docs).
"""
import re

import pdfplumber

import json
from collections import Counter
from pathlib import Path

from _parser_scaffold import _page_lines, _record, restore_diacritics, run_parser
from pdf_coords import viewer_offset

U, L = 'A-ZČĆŽŠĐ', 'a-zčćžšđ'
ROSTER_TO = 33


def _title(place: str) -> str:
    """'BAČKA PALANKA' = Bačka Palanka, 'ŽABLJAK (SR CRNA GORA)' = Žabljak (SR Crna Gora)."""
    return ' '.join(('(' if w.startswith('(') else '') + (w.strip('(') if w.strip('()') in ('SR', 'SAP', 'SFRJ') else w.strip('(').capitalize())
                    for w in place.split())


# The roster's last block (p. 33, under ŽITIŠTE) has no heading: a place, where given, follows the name in brackets
# or stands on the line under it in its column ("CAVIC Nikola / (mesto nepoznato)"); "i? ir lt" above it is illegible
APPENDIX = [(188.1, 376.6, 'CAVIC Nikola', 'mesto nepoznato'), (187.6, 397.7, 'DEVCIC Ivan', 'iz Like'),
            (187.9, 408.5, 'GRUJIC Lazar', ''), (187.6, 419.0, 'GRUBIC Petar', ''),
            (187.4, 429.8, 'FILIPOVIC Đuro', 'Dalmacija'), (187.9, 440.6, 'FILIPOVIC Maksim', ''),
            (316.5, 387.1, 'OCOKOLJIĆ Marko', ''), (316.3, 397.7, 'POSAVEC Ružica', ''),
            (316.0, 408.5, 'VUČINIC Vukašin', 'SR Crna Gora'), (316.0, 429.8, 'ŽARDIN Zvonko', ''),
            (316.0, 440.6, 'SABADOŠ Mihaj', '')]


def extract(pdf_path: str, start_page: int, end_page: int | None) -> list[dict]:
    """The roster: a line per place heading ('§h§ ...') and per name (split at the gap between the columns); the
    list of the fallen: its lines as they are."""
    out: list[dict] = []
    with pdfplumber.open(pdf_path) as pdf:
        stop = min(end_page or len(pdf.pages), len(pdf.pages))
        for n in range(start_page - 1, stop):
            page = pdf.pages[n]
            offset = viewer_offset(page)
            dx, dy = offset
            if n + 1 > ROSTER_TO:
                for ln in page.extract_text_lines():
                    out.append({'page': n + 1, 'x': round(ln['x0'] - dx, 1), 'y': round(ln['top'] - dy, 1), 'text': ln['text'],
                                'x1': round(ln['x1'] - dx, 1), 'bottom': round(ln['bottom'] - dy, 1)})
                continue
            note = min((ln['top'] for ln in page.extract_text_lines() if re.match(r'^1 Spisak boraca', ln['text'])), default=1e9)
            for ln in page.extract_text_lines(return_chars=True):
                if ln['top'] >= note - 1 or ln['text'].startswith('SPISAK BORACA'):
                    continue
                if n + 1 == ROSTER_TO and ln['top'] - dy > 350:                # the last block: APPENDIX
                    continue
                words = [w for w in page.extract_words() if abs(w['top'] - ln['top']) < 2 and ln['x0'] - 1 <= w['x0'] <= ln['x1'] + 1]
                words.sort(key=lambda w: w['x0'])
                if not words:
                    continue
                text = ' '.join(w['text'] for w in words)
                bold = 'Bold' in ln['chars'][0]['fontname']
                if bold or (re.fullmatch(rf'[{U}\s().,-]+', text) and not re.search(rf'[{U}]{{2,}}\s+[{U}]\.', text)
                            and ln['x0'] - dx > 190):
                    out.append({'page': n + 1, 'x': round(ln['x0'] - dx, 1), 'y': round(ln['top'] - dy, 1),
                                'text': '§h§ ' + text})
                    continue
                if re.fullmatch(r'\(?[^A-ZČĆŽŠĐ]*\)?|\W*\w{1,2}\W*', text) or text.startswith('('):
                    if text.startswith('('):                                 # "(mesto nepoznato)", "(Dalmacija)"
                        out.append({'page': n + 1, 'x': round(words[0]['x0'] - dx, 1), 'y': round(ln['top'] - dy, 1),
                                    'text': '§h§ ' + text})
                    continue
                parts, cur = [], [words[0]]
                for a, b in zip(words, words[1:]):                          # a gap of 15 pt: the other column
                    if b['x0'] - a['x1'] > 15:
                        parts.append(cur)
                        cur = []
                    cur.append(b)
                parts.append(cur)
                split = []
                for p in parts:                                              # "MLADENOVIĆ Nikola-Pikec PEST Karlo": two names
                    cur = [p[0]]
                    for a, b in zip(p, p[1:]):
                        if re.search(rf'[{L}.]$', a['text']) and re.match(rf'^[{U}]{{2,}}(?:-|$)', b['text']):
                            split.append(cur)
                            cur = []
                        cur.append(b)
                    split.append(cur)
                parts = split
                for p in parts:
                    out.append({'page': n + 1, 'x': round(p[0]['x0'] - dx, 1), 'y': round(ln['top'] - dy, 1),
                                'text': '§s§ ' + ' '.join(w['text'] for w in p),
                                'x1': round(p[-1]['x1'] - dx, 1), 'bottom': round(max(w['bottom'] for w in p) - dy, 1)})
            if n + 1 == ROSTER_TO:
                out.append({'page': n + 1, 'x': 188.0, 'y': 370.0, 'text': '§h§ '})
                out += [{'page': n + 1, 'x': x, 'y': y, 'text': f'§s§ {nm}' + (f' ({pl})' if pl else ''),
                         'x1': x + 110, 'bottom': y + 8.5} for x, y, nm, pl in APPENDIX]
    LINES[:] = [ln for ln in out if 'x1' in ln]
    return out


LINES: list[dict] = []                                                       # what extract read, for the boxes


def boxes(soldiers: list[dict]) -> list[dict]:
    """Each entry's box, which this book's layout defeats entry_boxes (a roster line holds two names; the list's
    line pitch, measured on the spaced-out roster, is no guide): a roster name's own words; a fallen soldier's
    lines down to the next entry. The file is in entry_boxes.INLINE_ENTRIES, which keeps these."""
    by_page: dict = {}
    for ln in LINES:
        by_page.setdefault(ln['page'], []).append(ln)
    starts = {(s['pdf_page'], round(s['pdf_x'], 1), round(s['pdf_y'], 1)) for s in soldiers}
    for s in soldiers:
        lines = sorted(by_page.get(s['pdf_page'], []), key=lambda ln: (ln['y'], ln['x']))
        i = next((k for k, ln in enumerate(lines) if abs(ln['x'] - s['pdf_x']) < 1 and abs(ln['y'] - s['pdf_y']) < 1), None)
        if i is None:
            continue
        mine = [lines[i]]
        if s['pdf_page'] > ROSTER_TO:
            for ln in lines[i + 1:]:
                if (ln['page'], round(ln['x'], 1), round(ln['y'], 1)) in starts or ln['y'] - mine[-1]['y'] > 14:
                    break
                mine.append(ln)
        s['pdf_x_end'] = max(ln['x1'] for ln in mine)
        s['pdf_y_end'] = max(ln['bottom'] for ln in mine)
    return soldiers


_place = {'name': ''}


def keep(ln: dict) -> bool:
    t = ln['text'].strip()
    if t.startswith('§h§'):
        _place['name'] = _title(t[4:].strip())
        return False
    if ln['page'] <= ROSTER_TO:
        ln['text'] = t + ' ¦ ' + _place['name']
        return True
    if re.fullmatch(r'[\d\W]{1,5}|\W*\w{1,2}\W*', t) or t.startswith('SPISAK POGINULIH'):
        return False
    if re.match(rf'^[{U}]{{2,}}', t.replace('2IV', 'ŽIV')):                     # "2IVAN0VIĆ"
        t = '§p§ ' + t
    ln['text'] = t
    return True


def name(head: str) -> tuple[str, str, list[str]]:
    """'ATANACKOV (IĆ) Vasa', 'BEŠLIN Žarko Bata', 'VESELINOVIĆ-Korica Savka', 'DEKIĆ B. Marin', 'PAUN JEŠKU Pa j a'"""
    notes = []
    head = re.sub(r'^[°"\'\s]+|["\'’]', '', head).replace(',', '')               # "°EJIĆ", "Rajić "Aleksandar", "Nedelj,ko"
    head = re.sub(rf'(?<=[{U}])1|1(?=[{U}])', 'I', head)                        # "TERZ1C", "EG1Ć"
    head = re.sub(rf'(?<=[{U}])2|2(?=[{U}{L}])', 'Ž', head)                     # "RU2IĆ", "2ivan"
    head = re.sub(rf'(?<=[{U}])5(?=[{U}])', 'Š', head)                          # "NE5IĆ"
    head = re.sub(rf'(?<=[{U}])0|0(?=[{U}])', 'O', head)                        # "2IVAN0VIĆ"
    head = re.sub(r'(?<=[A-Za-zčćžšđ]) (?=[a-zčćžšđ]{1,2}\b)', '', head)         # "Pa j a" = Paja, "Vel j ko"
    head = re.sub(rf'^([{U}]{{3,}})([{U}][{L}])', r'\1 \2', head)              # "PAROSKIJoca"
    toks = head.split()
    caps = 0
    while caps < len(toks) and re.fullmatch(rf'[{U}]+(?:-[{U}]+)?', toks[caps]) and not re.fullmatch(rf'[{U}]\.', toks[caps]):
        caps += 1
    joined = ''.join(toks[:caps])                                             # "KALE NT IĆ", "M ILO VAC", "PAVKO V"
    if caps > 1 and (any(len(w) <= 3 for w in toks[:caps - (1 if caps == len(toks) else 0)])
                     or re.search(r'(?:IĆ|IČ|IC|OV|EV|IN|AK|AC|SKI|ČKI)$', joined) and not re.search(r'(?:IĆ|IČ|IC|OV|EV|IN)$', toks[0])):
        head = ' '.join([joined] + toks[caps:])
    dr = re.search(r'\s(dr|Dr)\.?\s', head)                                    # "KOVAČEV dr Milorad"
    if dr:
        notes.append('dr.')
        head = head[:dr.start()] + ' ' + head[dr.end():]
    head = head.strip().rstrip('.')
    m = re.match(rf'^((?:[{U}]{{2,}}(?:-[{U}]?[{L}]*[{U}]*)?\s*)+?)(?:\(([^)]*)\)\s*)?((?:[{U}]\.\s*)?)([{U}][{L}]+.*|[{U}]{{2,}})?$', head.strip())
    if not m:
        toks = head.split()
        return (toks[0].title() if toks else ''), ' '.join(t[:1].upper() + t[1:] for t in toks[1:]), notes
    last = ' '.join('-'.join(p.title() if p.isupper() else p for p in w.split('-')) for w in m.group(1).split())
    last = re.sub(r'\s*-\s*', '-', last)
    if m.group(2):
        notes.append('ili ' + (last + m.group(2).lower() if len(m.group(2)) <= 3 else m.group(2).title()))   # "(IĆ)" = Atanacković
    given = (m.group(4) or '').strip()
    if given.isupper() or given[:1].islower():
        given = given.title()                                                # "ADAM", "momir"
    extra = given.split()[1:]
    given = given.split()[0] if given else ''
    if '-' in given:                                                         # "Nikola-Pikec", "Vukašin-švaba"
        given, alias = given.split('-', 1)
        extra = [alias[:1].upper() + alias[1:]] + extra
    if extra:
        notes.append('zvani ' + ' '.join(extra))                             # "Žarko Bata", "Živa Totarica"
    initial = m.group(3).strip()
    return last, given, ([initial] if initial else []) + notes


def parse(text: str) -> dict:
    if text.startswith('§s§'):
        head, _, place = text[4:].partition('¦')
        own = re.search(r'\s*\(([^)]*)\)\s*$', head)                          # "DEVCIC Ivan (iz Like)"
        if own and not re.match(r'^[A-ZČĆŽŠĐ]{1,3}$', own.group(1)):
            head, place = head[:own.start()], own.group(1)
        last, given, notes = name(head.strip())
        father = notes.pop(0) if notes and re.fullmatch(r'[A-ZČĆŽŠĐ]\.', notes[0]) else ''
        return _record(last, given, father, '; '.join(notes + [place.strip()]))
    text = re.sub(r'^§p§\s*', '', text)
    text = re.sub(r'(?<=[a-zčćžšđ])- (?=[a-zčćžšđ])', '', text)
    m = re.search(rf'\s(?=iz\s|rođ|\d{{4}}|poginu|umr|nesta|,)|,', text)
    head, rest = (text[:m.start()], text[m.start():].strip().lstrip(',').strip()) if m else (text, '')
    last, given, notes = name(head.strip())
    father = notes.pop(0) if notes and re.fullmatch(r'[A-ZČĆŽŠĐ]\.', notes[0]) else ''
    rec = _record(last, given, father, '; '.join(notes + ([rest] if rest else [])))
    rec['death_type'] = 'poginuo'
    y = re.match(r'^(?:iz\s[^,]*,\s*)?(?:rođ\.?\s*|rođen\w*\s*)?(1[89][0-3]\d)\b', rest)   # "iz Pančeva, rođen 1925,"
    if y:
        rec['birth_year'] = y.group(1)
    return rec


def diacritics(soldiers: list[dict]) -> list[dict]:
    """The roster's scan lost most carons and accents ("KOVACEVIC") and reads -ić as -ič ("PETROVIČ"): the spelling
    the other units print takes over (restore_diacritics), and -ič becomes -ić where that is far the commoner."""
    soldiers = restore_diacritics(soldiers)
    ref = Counter()
    for f in Path('website/public').glob('*soldiers.json'):
        if f.name != '12-vojvodjanska-soldiers.json':
            for r in json.loads(f.read_text(encoding='utf-8')):
                ref[r.get('last_name') or ''] += 1
    for s in soldiers:
        v = s['last_name']
        if v.endswith('ič') and ref[v[:-1] + 'ć'] >= max(2, 3 * ref[v]):
            s['last_name'] = v[:-1] + 'ć'
        s['middle_name'] = s.get('fathers_name', s['middle_name']) or s['middle_name']
        s['full_name'] = ' '.join(p for p in (s['last_name'], s['middle_name'], s['first_name']) if p)
    return soldiers


if __name__ == '__main__':
    run_parser(
        pdf_path='website/public/pdfs/12-vojvodjanska.pdf',
        brigade_code=75,
        output_path='website/public/12-vojvodjanska-soldiers.json',
        start_page=1,
        end_page=None,
        layout='single',
        extract_fn=extract,
        script='latin',
        entry_start_re=re.compile(r'^§[sp]§'),
        parse_entry_fn=parse,
        line_filter=keep,
        post_fn=lambda soldiers: boxes(diacritics(soldiers)),
    )
