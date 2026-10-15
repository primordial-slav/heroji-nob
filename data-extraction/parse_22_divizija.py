"""
Parser: 22. udarna divizija NOVJ (brigade code 96).

Source: Živojin Nikolić Brka, "22. divizija" (znaci.org 00001/235_8.pdf, its pages 3-34, book pp. 445-476)
        →  website/public/pdfs/22-divizija.pdf. Cyrillic, a table of four columns, by brigade (8. srpska, pp. 1-13;
        10. srpska, pp. 14-21; 12. srpska, pp. 22-32):
    "Spisak poginulih boraca i rukovodilaca iz 22. divizije u NOR-u"
        Prezime i ime | mesto rođenja | dan pogibije | mesto pogibije
        Анђелковић Јован | Одоровци | 15. XII 1944. | Сјеница
The rows don't sit level: a date's year or a place often stands a line above or below its name. read_rows takes
each page's column edges from its header ("1 2 3 4") and gives every cell line to the nearest name, a name's own
second line ("Стоја- / дин") to that name, and a cell's second line ("Липовица (Вла-" / "сотинце)", "Кумарево" /
"(Врање)") to the row of its first, with what stands beside it off any name's line. A note at a page's foot ("Борци
за које је наведено ...") is no row's. The book's re-typeset text spaces some names out ("Ж и в о ј и н").
The brigade goes to unit_detail; the birthplace, the date and the place of death to their fields.
"""
import re

import pdfplumber

from _parser_scaffold import _record, run_parser
from pdf_coords import viewer_words

U, L = 'A-ZČĆŽŠĐ', 'a-zčćžšđ'
SECTIONS = ((22, '12. srpska brigada'), (14, '10. srpska brigada'), (1, '8. srpska brigada'))
# cells the OCR garbled (znaci's re-typeset page shows them so) or the page cut off at its edge: the place as named
SLIPS = {'Strezimirova]': 'Strezimirovac', 'Osogovo planin;': 'Osogovo planina', 'Lipovac (Srem;': 'Lipovac (Srem)',
         'Suvo.1nica': 'Suvojnica', 'Ogošte (Kosovs': 'Ogošte (Kosovska Kamenica)', 'Tumba (Vlasotince': 'Tumba (Vlasotince)',
         'Plačkovica P': 'Plačkovica'}



def _lines(words: list[dict]) -> list[list[dict]]:
    out: list[list[dict]] = []
    for w in sorted(words, key=lambda w: (w['top'], w['x0'])):
        if out and abs(out[-1][0]['top'] - w['top']) <= 2.5:
            out[-1].append(w)
        else:
            out.append([w])
    return [sorted(ln, key=lambda w: w['x0']) for ln in out]


def _columns(words: list[dict]) -> tuple[float, float, float]:
    """Where columns 2, 3 and 4 begin: from the header row "1 2 3 4", else from where the names start."""
    hd = {w['text']: w['x0'] for w in words if w['text'] in ('1', '2', '3', '4') and w['top'] < 270}
    if '1' in hd:
        h1 = hd['1']
    else:                                                                    # no header: the names' left edge
        starts = [round(w['x0']) for w in words if w['x0'] < 150 and re.match(r'^[А-ЯЂЈЉЊЋЏ][а-яђјљњћџ]+$', w['text'])]
        h1 = max(set(starts), key=starts.count) + 52
    return h1 + 50, h1 + 118, h1 + 176


def read_rows(pdf_path: str, start_page: int, end_page: int | None) -> list[dict]:
    rows: list[dict] = []
    prev: dict | None = None                                                 # the last name of the page before
    with pdfplumber.open(pdf_path) as pdf:
        for pno, page in enumerate(pdf.pages[start_page - 1:end_page], start_page):
            words = viewer_words(page)
            b12, b23, b34 = _columns(words)
            top = max((w['top'] for w in words if w['text'] in ('1', '2', '3', '4') and w['top'] < 270), default=0) + 5
            notes = [w['top'] for w in words if w['text'].startswith('*)') and w['top'] > 300]
            notes += [ln[0]['top'] for ln in _lines([w for w in words if w['top'] > 300])     # "Борци за које је
                      if ln[0]['x0'] < b12 and re.match(r'^[А-ЯЂЈЉЊЋЏ]\S*\s+[а-яђјљњћџ]{2,}\s+[а-яђјљњћџ]{2,}\s',  # наведено ...":
                                                        ' '.join(w['text'] for w in ln))]          # a note, to the foot
            bottom = min(notes + [page.height * 0.875])
            words = [w for w in words if top < w['top'] < bottom - 2 and not re.fullmatch(r'\d{2,3}\*?', w['text'])]
            head = [w for w in words if re.match(r'Из$', w['text']) or 'бригад' in w['text']]
            if head:                                                         # "Из 10. српске бригаде*": the section heading
                hy = head[0]['top']
                words = [w for w in words if abs(w['top'] - hy) > 3]
            cols = [[w for w in words if w['x0'] < b12], [w for w in words if b12 <= w['x0'] < b23],
                    [w for w in words if b23 <= w['x0'] < b34], [w for w in words if w['x0'] >= b34]]
            anchors = []                                                     # the rows' names, with their own second lines
            for ln in _lines(cols[0]):
                text = ' '.join(w['text'] for w in ln)
                if re.match(r'^\S+\s+[а-яђјљњћџ]{2,}\s', text):
                    continue                                                 # "Борци за које је наведено ...": a note
                if not anchors and prev and text[:1].islower():
                    prev['text'].append(text)                                # "Мило-" / "рад" over a page break
                    rows[-1]['text'] = rows[-1]['text'].split(' | ')[0] + ' | ' + ' | '.join(
                        [_name(prev)] + rows[-1]['text'].split(' | ')[2:])
                elif anchors and (text[:1].islower() or anchors[-1]['text'][-1].endswith('-')
                                  or re.fullmatch(r'\S+\s+\S{1,2}\.', anchors[-1]['text'][-1]) and len(anchors[-1]['text']) == 1
                                  and len(text.split()) == 1):
                    anchors[-1]['text'].append(text)                         # "Станисављевић М." / "Живко"
                    anchors[-1]['last'] = ln[0]['top']
                elif re.match(r'^[А-ЯЂЈЉЊЋЏ]', text):
                    anchors.append({'y': ln[0]['top'], 'x': ln[0]['x0'], 'last': ln[0]['top'], 'text': [text],
                                    'cells': [[], [], []]})
            if not anchors:
                continue
            def dist(a: dict, y: float) -> float:                            # 0 within the name's own lines
                return 0 if a['y'] - 1 <= y <= a['last'] + 1 else min(abs(a['y'] - y), abs(a['last'] - y))

            # a cell broken over two lines ("Липовица (Вла-" / "сотинце)", "Кумарево" / "(Врање)") goes with its
            # first line, and so does what stands beside its second line off any name's line (the date under
            # "Широка Пла-" / "нина"); else a line between two rows went to the lower one
            cells = sorted(((ln[0]['top'], c, ln) for c in (1, 2, 3) for ln in _lines(cols[c])), key=lambda t: t[0])
            physical: list[list[tuple]] = []
            for t in cells:
                if physical and t[0] - physical[-1][0][0] <= 3:
                    physical[-1].append(t)
                else:
                    physical.append([t])
            above: dict[int, tuple[str, dict]] = {}                          # each column's last cell so far and its row

            def wraps(c: int, text: str) -> dict | None:
                """The row whose cell this line ends: "(Врање)" under a place, or a line that starts small or
                closes a bracket under one that breaks a word or leaves a bracket open; not "умро у Београду"."""
                prev_text, prev_a = above.get(c, ('', None))
                if prev_a and (re.match(r'^\([А-ЯЂЈЉЊЋЏ]', text)
                               or (re.match(r'^[а-яђјљњћџ]', text) or text.count(')') > text.count('('))
                               and (prev_text.endswith('-') or prev_text.count('(') > prev_text.count(')'))):
                    return prev_a
                return None

            for group in physical:
                cont = next((a for a in (wraps(c, ' '.join(w['text'] for w in ln)) for _, c, ln in group) if a), None)
                for y, c, ln in group:
                    text = ' '.join(w['text'] for w in ln)
                    own = wraps(c, text)
                    if own:
                        a = own
                    elif cont and min(dist(b, y) for b in anchors) > 0:
                        a = cont
                    else:
                        a = min(anchors, key=lambda a: (dist(a, y), -a['y']))
                    a['cells'][c - 1].append(ln)
                    above[c] = ((above[c][0] + ' ' if c in above and above[c][1] is a else '') + text, a)
            for i in range(len(anchors) - 1, 0, -1):                         # "Мицко" alone on a row: the line above's
                a = anchors[i]
                if len(a['text']) == 1 and len(a['text'][0].split()) == 1 and not any(a['cells']):
                    up = anchors[i - 1]
                    up['text'].append(a['text'][0] if re.search(r'\s\S{1,2}\.$', up['text'][-1]) else '— ' + a['text'][0])
                    up['last'] = a['last']
                    del anchors[i]
            for a in anchors:                                                # two dates: keep the row the birthplace is on
                dated = [ln for ln in a['cells'][1] if any(re.search(r'1[89]\d\d', w['text']) for w in ln)]
                if len(dated) > 1:
                    born = [ln[0]['top'] for ln in a['cells'][0]]
                    y = min(dated, key=lambda ln: abs(ln[0]['top'] - (born[0] if born else a['last'])))[0]['top']
                    a['cells'][1] = [ln for ln in a['cells'][1] if abs(ln[0]['top'] - y) <= 4 or
                                     (ln not in dated and abs(ln[0]['top'] - y) <= 6)]
                    a['cells'][2] = [ln for ln in a['cells'][2] if abs(ln[0]['top'] - y) <= 4] or a['cells'][2]
                    if born:
                        a['cells'][0] = [min(a['cells'][0], key=lambda ln: abs(ln[0]['top'] - y))]
            section = next(name for first, name in SECTIONS if pno >= first)
            for a in anchors:
                cells = []
                for lns in a['cells']:
                    ws = [w for ln in sorted(lns, key=lambda ln: ln[0]['top']) for w in ln]
                    ws = sorted(ws, key=lambda w: (round(w['top'] / 4), w['x0'])) if len(lns) > 1 else ws
                    cells.append(' '.join(w['text'] for w in ws))
                rows.append({'page': pno, 'x': a['x'], 'y': a['y'], 'y_end': max(a['last'], a['y']),
                             'text': '§t§ ' + ' | '.join([section, _name(a)] + cells)})
            prev = anchors[-1]
    return rows


def _name(a: dict) -> str:
    """A name's lines as one: "Стоја- / дин" = Стојадин, "Божи- / Дар" = Божидар."""
    name = ' '.join(a['text'])
    return re.sub(r'(?<=[а-яђјљњћџ])-\s+(\w)', lambda m: m.group(1).lower(), name)


def spaced(text: str) -> str:
    """"Ж и в о ј и н" = Живојин: a run of three or more single letters is one word."""
    return re.sub(r'\b(?:\w ){2,}\w\b', lambda m: m.group(0).replace(' ', ''), text)


def parse(text: str) -> dict:
    section, name, born, date, place = (p.strip() for p in (text[4:].split(' | ') + ['', '', ''])[:5])
    name = spaced(name).replace('J1', 'L').replace('Drago-g slav', 'Dragoslav')   # Л read as Ј1
    name = re.sub(r'\bJB(?=[a-z])', 'Lj', re.sub(r'\bJB\.', 'Lj.', name))   # Љ read as ЈБ
    name = re.sub(r'(?<=\s)3\.', 'Z.', name)                                 # З read as 3
    place, date, born = spaced(place), re.sub(r'\s+', ' ', date), spaced(born)
    date = re.sub(r'\.?\^111', '. VIII ', re.sub(r'\b[6G](?=944\b)', '1', date))  # "26.^1111944", "G944", "6944"
    notes = []
    dash = re.search(r'\s*—\s*(\S+)$', name)                                 # "Mile—Burča": a nickname
    if dash:
        notes.append('zvani ' + dash.group(1))
        name = name[:dash.start()]
    place = re.sub(r'(?<=\w),?-\s+(?=[a-zčćžšđ])', '', place).strip(' —-')     # "Doganica pla,- nina"
    born = re.sub(r'(?<=\w)-\s+(?=[a-zčćžšđ])', '', born)                     # "Široka Pla- nina"
    place, born = SLIPS.get(place, place), SLIPS.get(born, born)
    date = re.sub(r"['/]", ' ', date)
    date = re.sub(r'(?<=[IVX]) (?=[IVX])', '', re.sub(r'\s+', ' ', date))     # "X I I" = XII
    tail = re.search(r'\s([A-Z]\.)$', name)                                  # "Jovanča D." | "Stajovac": the place's initial
    if tail and born[:1].isupper() and not re.match(r'[A-Z][a-z]?\.', born):
        name, born = name[:tail.start()], tail.group(1) + ' ' + born
    alt = re.search(r'\s*\(([^)]+)\)', name)                                 # "Аљоша (Рус)"
    if alt:
        notes.append('(' + alt.group(1) + ')')
        name = (name[:alt.start()] + name[alt.end():]).strip()
    toks = [t for t in re.sub(r'(?<=[.])(?=\S)', ' ', name).split() if t != '.']
    toks = [t + '.' if re.fullmatch(rf'[{U}]', t) else t for t in toks]   # "Анђелковић М Стојадин"
    if len(toks) == 1:                                                       # "Аљоша (Рус)", "Петар | СССР": one name
        last, father, given = '§', '', toks[0]
    elif len(toks) >= 3 and re.fullmatch(rf'(?:[{U}][{L}]?\.)', toks[1]):
        last, father, given = toks[0], toks[1], ' '.join(toks[2:])
    elif len(toks) >= 2:
        last, father, given = toks[0], '', ' '.join(toks[1:])
    else:
        last, father, given = (toks[0] if toks else ''), '', ''
    date = re.sub(r'^(\d)\1(\d)\2\.\.', r'\1\2.', date)                      # "1122.. IV": the day set twice
    date = re.sub(r'(?<=[IVX])(?=1[89]\d\d)', ' ', date).replace(',', '.').strip(' .\'')
    info =', '.join(p for p in (born, date, place) if p and p not in ('—', '-'))
    rec = _record(last, given, father, '; '.join(notes + [info]))
    if born and born not in ('—', '-'):
        rec['birth_place'] = born
    if re.search(r'1[89]\d\d', date):
        rec['death_date'] = re.sub(r'\.$', '', date)
    fate = place.lower()
    rec['death_type'] = ('umro' if re.search(r'\bumr', fate) else 'streljan' if 'streljan' in fate
                         else 'nestao' if 'nesta' in fate else 'poginuo')
    later = re.search(r'\((?:umro|(?:zarobljen i )?streljan)\s+u\s+([^)]+)\)', place)  # "Sakar (umro u Šapcu)",
                                                                             # "Lipovica (zarobljen i streljan u Vlasotincu)"
    if later:
        rec['_death_at'] = later.group(1)
    elif place and not re.match(r'^\(.*\)$', place):                          # "(umro kod kuće)": no place
        m = re.match(r'^(?:umro|umrla|streljan|nestao)\s+(?:u|kod|na)\s+(.+)$', place, re.I)   # "Umro u Beogradu"
        if m:
            rec['_death_at'] = m.group(1)
        elif not re.search(r'\bumr', fate) and fate not in ('nestao', 'nestala'):   # "od zadobijenih kod kuće,
            rec['death_place'] = place                                       # rana umro"; "nestao" is no place
    rec['unit_detail'] = section
    return rec


def post(soldiers: list[dict]) -> list[dict]:
    import sys
    from itertools import product
    import parse_toplicki_odred as top
    sys.path.insert(0, 'scripts')
    from extract_structured_fields import Extractor
    known = top._corpus()[0]
    for s in soldiers:
        at = s.pop('_death_at', None)
        if at:                                                               # "umro u Beogradu" = Beograd
            forms = [' '.join(c) for c in product(*(Extractor._variants(Extractor, w) for w in at.split()))]
            s['death_place'] = {'Šapcu': 'Šabac', 'Beogradu': 'Beograd', 'Vlasotincu': 'Vlasotince'}.get(at) or (
                max(forms, key=lambda f: known[f]) if any(known[f] for f in forms) else at)
        if s['last_name'] == '§':                                            # "Aljoša (Rus)": one name
            s['last_name'] = ''
        s['full_name'] = ' '.join(p for p in (s['last_name'], s['middle_name'], s['first_name']) if p)
    return soldiers


if __name__ == '__main__':
    run_parser(
        pdf_path='website/public/pdfs/22-divizija.pdf',
        brigade_code=96,
        output_path='website/public/22-divizija-soldiers.json',
        start_page=1,
        end_page=None,
        layout='single',
        extract_fn=read_rows,
        script='cyrillic',
        entry_start_re=re.compile(r'^§t§'),
        parse_entry_fn=parse,
        post_fn=post,
    )
