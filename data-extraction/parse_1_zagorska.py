"""
Parser: 1. zagorska udarna brigada (brigade code 105).

Source: Vladimir Hlaić, "Grebeni Ivančice — Prva zagorska udarna brigada" (znaci.org 00003/625.pdf, its pages 207-221,
        book pp. 191-205)  →  website/public/pdfs/1-zagorska.pdf. Latin, a table, prepared by Ivica Družinec:
    "Spisak boraca i rukovodilaca Prve zagorske udarne brigade poginulih od 8. svibnja 1944. do 15. svibnja 1945."
        Prezime i ime | God. rođ. | Mjesto rođenja i općina | Poginuo
        ANTOLIC MILENA | 1925 | Razdrto, Tuhelj | 3. 8. 1944 / Petrova gora
A row's second line (the place of death, the rest of a birthplace) stands under it, and the text layer drifts against
the names by up to 13pt down a page. read_rows takes each page's columns from its header (a year by its digits), makes
each column's cells (a cell's second line runs on from its first) and aligns them with the names in order (_align). The scan loses carons in the
capitals ("ANTOLIC"): names are put right from the spellings the other units print (parse_8_kordunaska_divizija's
helpers).
"""
import re

import pdfplumber

import parse_8_kordunaska_divizija as k8
from _parser_scaffold import _record, run_parser
from pdf_coords import viewer_words

U, L = 'A-ZČĆŽŠĐ', 'a-zčćžšđ'


def corpus() -> None:
    import glob
    import json
    from collections import Counter, defaultdict
    for f in ('last_name', 'first_name', 'middle_name'):
        k8._spell[f] = defaultdict(Counter)
    for fn in glob.glob('website/public/*soldiers.json'):
        if not fn.replace('\\', '/').endswith('/1-zagorska-soldiers.json'):
            for s in json.load(open(fn, encoding='utf-8')):
                for f in k8._spell:
                    if s.get(f):
                        k8._spell[f][k8.fold(s[f])][s[f].upper()] += 1


def _lines(words: list[dict]) -> list[list[dict]]:
    out: list[list[dict]] = []
    for w in sorted(words, key=lambda w: (w['top'], w['x0'])):
        if out and abs(out[-1][0]['top'] - w['top']) <= 2.5:
            out[-1].append(w)
        else:
            out.append([w])
    return [sorted(ln, key=lambda w: w['x0']) for ln in out]


def _align(cells: list[float], names: list[float]) -> list[int]:
    """Give each cell (its first line's y, top down) a row, in order. The text layer drifts against the names by up to
    13pt down a page, so a cell's offset from its name is held close to the one above it rather than to nil; a row
    may lack a cell, and two cells share one only where a name was lost."""
    inf = float('inf')
    n, m = len(cells), len(names)
    if not n:
        return []
    cost = [[inf] * m for _ in range(n)]
    back = [[0] * m for _ in range(n)]
    for j in range(m):
        cost[0][j] = abs(cells[0] - names[j] + 2) + 3 * j
    for i in range(1, n):
        for j in range(m):
            d = cells[i] - names[j]
            for k in range(j + 1):
                if cost[i - 1][k] < inf:
                    c = cost[i - 1][k] + abs(d - (cells[i - 1] - names[k])) + 3 * max(0, j - k - 1) + 15 * (k == j)
                    if c < cost[i][j]:
                        cost[i][j], back[i][j] = c, k
    j = min(range(m), key=lambda j: cost[n - 1][j] + 3 * (m - 1 - j))
    out = [j]
    for i in range(n - 1, 0, -1):
        j = back[i][j]
        out.append(j)
    return out[::-1]


def read_rows(pdf_path: str, start_page: int, end_page: int | None) -> list[dict]:
    rows = []
    with pdfplumber.open(pdf_path) as pdf:
        for pno, page in enumerate(pdf.pages[start_page - 1:end_page], start_page):
            words = viewer_words(page)
            hdr = {w['text'].rstrip('.,'): w for w in words if w['top'] < 70 and w['text'].rstrip('.,') in ('God', 'Mjesto', 'Poginuo')}
            if 'Mjesto' not in hdr or 'Poginuo' not in hdr:
                continue                                                     # the list's title page
            top = max(w['top'] for w in hdr.values()) + 6
            year = hdr['God']['x0'] - 5 if 'God' in hdr else hdr['Mjesto']['x0'] - 32
            death = hdr['Poginuo']['x0'] - 15
            note = [w['top'] for w in words if w['text'] == 'NAPOMENA:']
            words = [w for w in words if top < w['top'] < (note[0] - 2 if note else 999) and not (w['top'] > 425 and re.fullmatch(r'\d{3}', w['text']))]   # the page number
            mid = [w for w in words if year <= w['x0'] < death]
            years = [w for w in mid if w['x0'] < hdr['Mjesto']['x0'] - 3 and re.fullmatch(r'1[89D]\d[\dS]?[.,]?', w['text'])]
            cols = [[w for w in words if w['x0'] < year], years, [w for w in mid if w not in years],
                    [w for w in words if w['x0'] >= death]]
            anchors = []
            for ln in _lines(cols[0]):
                name = ' '.join(w['text'] for w in ln)
                if not re.match(rf'^[{U}]', name) or re.search(r'[a-km-zčćžšđ]', name):   # "BOZlC": l read for I
                    continue
                if anchors and len(anchors[-1]['name'].split()) == 1 and ln[0]['top'] - anchors[-1]['y'] < 12:
                    anchors[-1]['name'] += ' ' + name                        # "GRABROVEČKI / VLADIMIR"
                    continue
                anchors.append({'y': ln[0]['top'], 'x': ln[0]['x0'], 'name': name, 'cells': [[], [], []]})
            if not anchors:
                continue
            year_ys = [ln[0]['top'] for ln in _lines(cols[1])]
            for c in (1, 2, 3):
                cells: list[list] = []
                for ln in _lines(cols[c]):
                    y, text = ln[0]['top'], ' '.join(w['text'] for w in ln)
                    first = (c == 1 or (c == 2 and any(abs(y - t) <= 2.5 for t in year_ys))
                             or (c == 3 and re.search(r'19\d[\dS]', text)))
                    if cells and not first and y - cells[-1][0][0]['top'] < 14:
                        cells[-1].append(ln)                                 # a cell's second line
                    else:
                        cells.append([ln])
                for cell, a in zip(cells, _align([cell[0][0]['top'] for cell in cells], [a['y'] for a in anchors])):
                    anchors[a]['cells'][c - 1].extend(cell)
            for a in anchors:
                cells = [[' '.join(w['text'] for w in ln) for ln in sorted(lns, key=lambda ln: ln[0]['top'])] for lns in a['cells']]
                rows.append({'page': pno, 'x': a['x'], 'y': a['y'],
                             'text': '§t§ ' + '¦'.join([a['name'], ' '.join(cells[0]), ' '.join(cells[1]), '¤'.join(cells[2])])})
    return rows


# The text layer's slips in place names, put right from the page image.
PLACES = {
    'Ce trnje': 'Cetinje', 'ZapreSić': 'Zaprešić', 'Pušca': 'Pušća', 'V«jnić': 'Vojnić', 'Badkovica': 'Bačkovica',
    'Simljanik': 'Šimljanik', 'Simljanica': 'Šimljanica', 'Simljanska': 'Šimljanska', 'Gudoveo': 'Gudovec',
    'Guđovec': 'Gudovec', 'Suđovec': 'Sudovec', 'Lađislav': 'Ladislav', 'Široko Selb': 'Široko Selo', 'Zitomir': 'Žitomir',
    'Sumarica': 'Šumarica', 'Trgovišce': 'Trgovišće', 'Sandrovac': 'Šandrovac', 'Sanđrovac': 'Šandrovac', 'OmiS': 'Omiš',
    'Boreva kosa': 'Borova kosa', 'Sveđnožje': 'Svednožje', 'Piemenšćina': 'Plemenšćina', 'Cepelovac': 'Čepelovac',
    'Salovec': 'Šalovec', 'Zabno': 'Žabno', 'Ivanee': 'Ivanec', 'Brdovee': 'Brdovec', 'Martljanec': 'Martijanec',
    'Letovcani': 'Letovčani', 'Ljubešcica': 'Ljubeščica', 'Luzani': 'Lužani', 'v. Ves': 'V. Ves', 'Raca': 'Rača',
    'Trvanac': 'Trnavac', 'Doljiee': 'Doljiće', 'Đurđič': 'Đurđić', 'Sumanovac': 'Šumanovac', 'Durmanec': 'Đurmanec',
    'Kasina': 'Kašina', 'Vađnija': 'Vadnija', 'Simunec': 'Šimunec', 'Vukosa vi j e vica': 'Vukosavljevica',
    'Desinič': 'Desinić', 'Cueerje': 'Čučerje', 'BUdiščina': 'Budiščina', 'poljanice': 'Poljanice', 'jakovlje': 'Jakovlje',
    'Jako vi je': 'Jakovlje', 'Koštan jevac': 'Kostanjevac', 'N. Maroi': 'N. Marof', 'Seđlarica': 'Sedlarica',
    'Sid': 'Šid', 'Celnice': 'Čelnice', 'valentinovo': 'Valentinovo',
}
_PLACES = re.compile(r'(?<!\w)(?:' + '|'.join(re.escape(k) for k in sorted(PLACES, key=len, reverse=True)) + r')(?!\w)')


def places(text: str) -> str:
    return _PLACES.sub(lambda m: PLACES[m.group(0)], text).lstrip('. ')       # ". Ladislav": a speck before the name


# Surnames whose carons the text layer lost, as the page image prints them.
NAMES = {
    'Banjsek': 'Banjšek', 'Cucek': 'Čuček', 'Klambeb': 'Klamber', 'Kramcer': 'Kramčer', 'Jakesić': 'Jakešić',
    'Jumsić': 'Jumšić', 'Kolencak': 'Kolenčak', 'Lukasek': 'Lukašek', 'Limpersak': 'Limperšak', 'Kostajnski': 'Koštajnski',
    'Kozić': 'Kožić', 'Kranjcev': 'Kranjčev', 'Klobuctc': 'Klobučić', 'Kalecak': 'Kalečak', 'Kletus': 'Kletuš',
    'Malis': 'Mališ', 'Mokac': 'Mokač', 'Markozet': 'Markožet', 'Prosinicki': 'Prosinički', 'Pogačič': 'Pogačić',
    'Slamrscak': 'Slamršćak', 'Susicek': 'Sušiček', 'Skanba': 'Škanba', 'Safrenko': 'Šafrenko', 'Santelić': 'Šantelić',
    'Siljhan': 'Šiljhan', 'Vlahovcek': 'Vlahovček', 'Vidloza': 'Vidloža', 'Zelenić': 'Želenić', 'Zujanić': 'Žujanić',
    'Glozinić': 'Gložinić',
}


def post(soldiers: list[dict]) -> list[dict]:
    soldiers = k8.post(soldiers)
    for s in soldiers:
        s['last_name'] = NAMES.get(s['last_name'], s['last_name'])
        s['full_name'] = f"{s['last_name']} {s['first_name']}".strip()
    return soldiers


def parse(text: str) -> dict:
    name, year, born, death = (p.strip() for p in (text[4:].split('¦') + [''] * 4)[:4])
    words = name.replace('2', 'Ž').split()                                 # "BLA2UNAJ", "RU2A": Ž read as 2
    last = k8.join_parts([k8.caps_word(w) for w in words[:-1]], 'last_name') if len(words) > 1 else (words[0] if words else '')
    given = k8.caps_word(words[-1]).title() if len(words) > 1 else ''
    parts = [p.strip() for p in death.split('¤') if p.strip()]
    parts = [re.sub(r'(?<=19\d)S\b', '5', p) for p in parts]                # "194S"
    parts = [re.sub(r'^S(?=\.)', '5', re.sub(r'^(\d{1,2}),', r'\1.', re.sub(r'(?<=\. )U(?=\.)', '11', p))) for p in parts]
    date = next((p for p in parts if re.search(r'19\d\d', p)), '')         # "S. 12.", "23, 4.", "8. U." read for 5., 23., 11.
    place = places(' '.join(p for p in parts if p != date))
    when = re.search(r'\d{1,2}\.\s*\d{1,2}\.\s*19\d\d|19\d\d', date)
    if when and date[when.end():].strip():
        place = places(date[when.end():].strip() + ' ' + place)              # "15. 1. 1945 Zrinjska" on one line
    born = places(re.sub(r'\s+', ' ', born.replace('-', ' ')).strip(' ,'))
    year = re.sub(r'(?<=1)D(?=\d)', '9', year)                               # "1D13" = 1913
    fell = ', '.join(p for p in ((when.group(0) if when else ''), place) if p)
    info = ', '.join(p for p in (year, born, 'poginuo ' * bool(fell) + fell) if p)   # the column "Poginuo"
    rec = _record(last, given, '', info)
    rec['birth_year'] = year if re.fullmatch(r'1[89]\d\d', year) else ''
    if born:
        rec['birth_place'] = born
    if when:
        rec['death_date'] = when.group(0)
    if place:
        rec['death_place'] = place
    rec['death_type'] = 'poginuo'
    return rec


if __name__ == '__main__':
    corpus()
    run_parser(
        pdf_path='website/public/pdfs/1-zagorska.pdf',
        brigade_code=105,
        output_path='website/public/1-zagorska-soldiers.json',
        start_page=1,
        end_page=None,
        layout='single',
        extract_fn=read_rows,
        script='latin',
        entry_start_re=re.compile(r'^§t§'),
        parse_entry_fn=parse,
        post_fn=post,
    )
