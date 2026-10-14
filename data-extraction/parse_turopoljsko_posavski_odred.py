"""
Parser: Turopoljsko-posavski partizanski odred (brigade code 149): its fallen, and its men shot or dead in the war.

Source: Višnja Huzjak, *Turopoljsko-posavski partizanski odred* (Muzej Turopolja, Velika Gorica 1983; znaci.org bk=835,
00003/835.pdf, PDF pp. 19-22, book pp. 17-20) → website/public/pdfs/turopoljsko-posavski-odred.pdf. Two tables:
    "Popis poginulih boraca Turopoljsko-posavskog partizanskog odreda" (pp. 1-3 of the site PDF), 99 numbered rows:
        surname and given name (capitals), birthplace, when and where he fell, the source ("M T", "V H I", "S B");
    "Strijeljani i umrli borci ... za vrijeme narodnooslobodilačkog rata" (p. 4), 16 rows: "shot", "died of typhus".
The cells of a row don't stand on one line in the text layer (the date sits a few points above or below the name),
so each cell is given to the name nearest it. The sources' abbreviations are left out.
Usage: python data-extraction/parse_turopoljsko_posavski_odred.py
"""
import re

import pdfplumber

import parse_8_kordunaska_divizija as k8
from _parser_scaffold import _record, run_parser
from pdf_coords import viewer_words

U, L = 'A-ZČĆŽŠĐ', 'a-zčćžšđ'


# rows whose name the OCR garbled, by what it read on the name's second line: no. 64 and no. 80, the odred's first
# commander and a later one (both in the book's list of its commanders, "Milan Mraović Simić", "Milan Radović — Čokara")
FIX_NAME = {'MILAN': 'MRAOVIĆ-ŠIMIĆ MILAN', 'ČOKARA': 'RADOVIĆ MILAN »Čokara«', 'VRANEKMATO': 'VRANEK MATO'}
# cells the OCR garbled or put in the wrong row, read from the page images
FIX_CELLS = {
    'Mraović-Šimić Milan': ('', 'prvi komandant odreda, poginuo 22. VIII 1943. Kupčina'),
    'Dolački Stjepan': ('Veleševec', 'ubijen u Sisku 26. IV 1945.'),
    'Večerin Josip': ('Čička Poljana', '1944. Čerkezi strijeljali kao taoca'),
    'Kruhan Milan': ('Jezero', 'umro 17. IV 1944. u vojnoj bolnici na Siciliji (Italija)'),
    'Vađić Janko': ('Lukavec', 'nestao iz zatvora u Savskoj cesti'),
    'Cerovski Tomo': ('Dubranec', 'umro od tifusa u bolnici'),
    'Munić Dragutin': ('Bukevje', 'poginuo 20. X 1944. Trebovac (D. Selo)'),
    'Smolković Mirko': ('Pokupski, Lomnica Donja', 'poginuo 11. V 1944. Kupčina'),
}


def extract(pdf_path: str, start: int, end: int | None) -> list[dict]:
    out, offsets = [], (0, 0, 0)
    with pdfplumber.open(pdf_path) as pdf:
        for pno, page in enumerate(pdf.pages, 1):
            words = viewer_words(page, keep_blank_chars=False)
            # the columns: by the header where the page has one, else as far from the row numbers as on the first page
            # (the scan sets each page at its own place)
            nums = sorted(w['x0'] for w in words if re.fullmatch(r'\d{1,3}\.', w['text']))
            x_num = nums[len(nums) // 2]
            head = {w['text']: w for w in words if w['text'] in ('Mjesto', 'Poginuli', 'Strijeljan', 'Podaci')}
            if 'Mjesto' in head:
                x_place, x_death = head['Mjesto']['x0'], (head.get('Poginuli') or head['Strijeljan'])['x0']
                x_src, top = head['Podaci']['x0'], head['Mjesto']['bottom'] + 2
                offsets = (x_place - x_num, x_death - x_num, x_src - x_num)
            else:
                x_place, x_death, x_src = (x_num + o for o in offsets)
                top = 0
            body = [w for w in words if w['top'] > top]
            legend = [w['top'] for w in body if w['text'].startswith(('*Legenda', 'Legenda'))]
            if legend:                                       # the sources' legend under the last rows
                body = [w for w in body if w['top'] < min(legend) - 2]
            names = [w for w in body if w['x0'] < x_place - 4 and not re.fullmatch(r'\d+\.?|\.', w['text'])]
            rows = []
            for w in sorted(names, key=lambda w: (round(w['top']), w['x0'])):
                if rows and abs(rows[-1][0]['top'] - w['top']) <= 3:
                    rows[-1].append(w)
                else:
                    rows.append([w])
            anchors = [(r[0]['top'], r) for r in rows]
            cells = [{'name': ' '.join(w['text'] for w in sorted(r, key=lambda w: w['x0'])), 'place': [], 'death': []}
                     for _, r in anchors]
            # a date stands right-aligned, its day often left of the column's heading: a word with a digit or a
            # Roman month right of the birthplaces is the date's, as is all right of the heading
            for w in body:
                if w['x0'] < x_place - 4 or w['x0'] >= x_src - 6 or not anchors:
                    continue
                if not re.search(r'[A-Za-zČĆŽŠĐčćžšđ0-9]', w['text']) or re.search(r'[«»/]|^\W|[a-z]\d|\d[a-z]', w['text']):
                    continue                                 # the scan's specks the OCR read as letters
                i = min(range(len(anchors)), key=lambda i: abs(anchors[i][0] - w['top']))
                if abs(anchors[i][0] - w['top']) > 13:
                    continue
                dated = re.search(r'\d|^[IVX]{1,4}\.?$|^ljeto$', w['text']) and w['x0'] > x_place + 55
                cells[i]['death' if w['x0'] >= x_death - 4 or dated else 'place'].append(w)
            for (top, r), c in zip(anchors, cells):
                c['name'] = FIX_NAME.get(c['name'], c['name'])
                if not re.fullmatch(rf'[{U}][{U}{L}]+(?:\s*-\s*[{U}][{U}{L}]+)?(?:\s+[{U}][{U}{L}.]*)*(?:\s+»[{U}][{L}]+«)?', c['name']):
                    continue                                 # the OCR's misreading of a name the next row gives
                order = lambda ws: ' '.join(w['text'] for w in sorted(ws, key=lambda w: (round(w['top']), w['x0'])))
                text = f"§x§ {c['name']} ¦ {order(c['place'])} ¦ {order(c['death'])} ¦ {'f' if pno < 4 else 'd'}"
                out.append({'text': text, 'x': r[0]['x0'], 'y': top, 'page': pno})
    return out


def parse(text: str) -> dict:
    name, place, death, kind = [x.strip() for x in re.sub(r'^§x§\s*', '', text).split('¦')]
    name = re.sub(r'\s*-\s*', '-', name)                    # "DOROTIĆ - ŠIMEC MARA"
    name = re.sub(rf'(?<=[{L}])(?=[{U}][{L}])', ' ', name)  # "HlopecSlavko", "VađićJanko"
    nick = re.search(r'\s*»([^«]+)«', name)
    if nick:
        name = name[:nick.start()]
        place = f'zvani {nick.group(1)}; {place}'.strip('; ')
    trailing = re.match(rf'^(.*[{U}]{{2,}})\s+([{U}][{L}]+)$', name)
    if trailing:                                      # "DOROTIĆ - ŠIMEC MARA Dubranec": the birthplace on the name's line
        name, place = trailing.group(1), f'{trailing.group(2)} {place}'.strip()
    words = name.split()
    caps = lambda w: k8.caps_word(w).title() if sum(c.isupper() for c in w) > len(w) / 2 else w   # "MiJO"
    last, given = caps(words[0]), ' '.join(caps(w) for w in words[1:])
    fix = FIX_CELLS.get(f'{last} {given}')
    if fix:
        place, death = fix[0], fix[1]
        kind = 'fixed'
    death = re.sub(r'(\d{1,2})\.\s?(1{2,3})\s?(19\d\d)', lambda m: f'{m.group(1)}. {"I" * len(m.group(2))} {m.group(3)}',
                   death)                                    # "13.111944." = 13. III 1944.
    if kind == 'f':
        info = '; '.join(x for x in (place, f'poginuo {death}' if death else 'poginuo') if x)
    elif kind == 'fixed':
        info = '; '.join(x for x in (place, death.rstrip('.')) if x)
    else:
        info = '; '.join(x for x in (place, death) if x)
    rec = _record(last, given, '', info + '.')
    rec['birth_year'] = ''
    return rec


if __name__ == '__main__':
    k8.corpus()
    run_parser(
        pdf_path='website/public/pdfs/turopoljsko-posavski-odred.pdf',
        brigade_code=149,
        output_path='website/public/turopoljsko-posavski-odred-soldiers.json',
        start_page=1,
        end_page=None,
        layout='single',
        script='latin',
        entry_start_re=re.compile(r'^§x§'),
        parse_entry_fn=parse,
        extract_fn=extract,
        post_fn=k8.post,
    )
