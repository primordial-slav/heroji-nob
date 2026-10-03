"""
Parser: 3. banijska NOU udarna brigada (brigade code 108).

Source: Jovo Borojević, "Sinovi Šamarice — Treća banijska narodnooslobodilačka udarna brigada" (znaci.org 00003/447.pdf,
        its pages 203-213, book pp. 195-205)  →  website/public/pdfs/3-banijska.pdf. Latin, three columns:
    "Spisak rukovodilaca i boraca Treće brigade", names only, surname first, in alphabetical order:
        Abramović Stojan    Babić Branko    Beronja Ilija
The columns stand at different places on odd and even pages, so read_names splits each line where the gap between
two words is wide, and gives every name its own box on the page (entry_boxes.py leaves these alone: INLINE_ENTRIES).
The scan spaces names apart ("Abramo vić Stoj an"), reads Ž as 2 and k as lc ("Žarlcović"), and loses carons;
names are put right from the spellings the other units print (parse_8_kordunaska_divizija's helpers). The author's
note after the list (book p. 205) is not read.
"""
import re

import pdfplumber

import parse_8_kordunaska_divizija as k8
from _parser_scaffold import _record, run_parser
from pdf_coords import viewer_words

U, L = 'A-ZČĆŽŠĐ', 'a-zčćžšđ'
_box: dict = {}


def corpus() -> None:
    import glob
    import json
    from collections import Counter, defaultdict
    for f in ('last_name', 'first_name', 'middle_name'):
        k8._spell[f] = defaultdict(Counter)
    for fn in glob.glob('website/public/*soldiers.json'):
        if not fn.replace('\\', '/').endswith('/3-banijska-soldiers.json'):
            for s in json.load(open(fn, encoding='utf-8')):
                for f in k8._spell:
                    if s.get(f):
                        k8._spell[f][k8.fold(s[f])][s[f].upper()] += 1


def _boxes(ws: list[dict]) -> dict:
    rect = [round(min(w['x0'] for w in ws), 1), round(min(w['top'] for w in ws), 1),
            round(max(w['x1'] for w in ws), 1), round(max(w['bottom'] for w in ws), 1)]
    out = {'pdf_x_end': rect[2], 'pdf_y_end': rect[3], 'rect': rect}
    lines = sorted({round(w['top']) for w in ws})
    if len(lines) > 1:                                                       # a nickname run over to the next line
        out['pdf_rects'] = [[round(min(w['x0'] for w in ws if round(w['top']) == t), 1), round(min(w['top'] for w in ws if round(w['top']) == t), 1),
                             round(max(w['x1'] for w in ws if round(w['top']) == t), 1), round(max(w['bottom'] for w in ws if round(w['top']) == t), 1)]
                            for t in lines]
    return out


def read_names(pdf_path: str, start: int, end: int | None) -> list[dict]:
    """One line per name ('§b§ Surname Given') at its first word, in reading order (column by column)."""
    out = []
    with pdfplumber.open(pdf_path) as pdf:
        for pno, page in enumerate(pdf.pages[start - 1:end], start):
            words = viewer_words(page)
            note = [w['top'] for w in words if w['text'] == 'NAPOMENA']
            words = [w for w in words if w['top'] < (note[0] - 2 if note else 9999)
                     and not re.fullmatch(r'\d{3}|SPISAK|RUKOVODILACA|I|BORACA|TREĆE|BRIGADE', w['text'])]
            lines: list[list[dict]] = []
            for w in sorted(words, key=lambda w: (w['top'], w['x0'])):
                if lines and abs(lines[-1][0]['top'] - w['top']) < 3:
                    lines[-1].append(w)
                else:
                    lines.append([w])
            starts = []
            for ln in lines:                                                 # the page's columns: where most names start
                ln.sort(key=lambda w: w['x0'])
                starts.append(ln[0]['x0'])
                starts += [b['x0'] for a, b in zip(ln, ln[1:]) if b['x0'] - a['x1'] > 12]
            cols: list[float] = []
            for x in sorted(starts):
                if not cols or x - cols[-1] > 40:
                    cols.append(x)
            cols = [c for c in cols if sum(abs(x - c) < 6 for x in starts) >= 5]
            by_col: list[list[list[dict]]] = [[] for _ in cols]
            for ln in lines:
                groups: dict = {}
                for w in ln:
                    k = max([i for i, c in enumerate(cols) if w['x0'] >= c - 5] or [0])
                    groups.setdefault(k, []).append(w)
                for k, ws in groups.items():
                    text = ' '.join(w['text'] for w in ws)
                    if re.fullmatch(r'\d+»?', text):
                        continue                                             # the page number
                    if text.startswith('(') and by_col[k]:
                        by_col[k][-1] += ws                                  # "(Uglješa)": the line above's nickname, run over
                        continue
                    by_col[k].append(ws)
            for col in by_col:
                for c in col:
                    x, y = round(c[0]['x0'], 1), round(c[0]['top'], 1)
                    _box[(pno, x, y)] = _boxes(c)
                    out.append({'page': pno, 'x': x, 'y': y, 'text': '§b§ ' + ' '.join(w['text'] for w in c)})
    # "Sulejmanović" at a column's foot, "Sulejman" at the next one's head: one name broken over the columns
    for a, b in zip(out, out[1:]):
        if (len(a['text'].split()) == 2 and len(b['text'].split()) == 2 and a['text'] != '§b§'
                and a['page'] == b['page'] and b['y'] < a['y']):
            a['text'] += ' ' + b['text'][4:]
            b['text'] = '§b§'
            _box[(a['page'], a['x'], a['y'])]['pdf_rects'] = [_box[(a['page'], a['x'], a['y'])]['rect'], _box[(b['page'], b['x'], b['y'])]['rect']]
    out = [ln for ln in out if ln['text'] != '§b§']
    return out


FIXES = {'Žfiić': 'Žilić', 'EIdžija': 'Eldžija'}


def fix_word(w: str) -> str:
    w = re.sub(r'^[^\wČĆŽŠĐčćžšđ]+', '', w)                                  # '"Božić', '•Bogdanić': specks
    w = re.sub(r'^2(?=[a-zčćžšđ])', 'Ž', w)                                  # "2ivko" = Živko
    w = w.replace("'", '')                                                  # "Živlcov'ič"
    w = re.sub(r'(?<=[a-z])-(?=j$)', '', w)                                  # "Vasil-j"
    if re.search(r'[a-zčćžšđ][A-ZČĆŽŠĐ]', w):
        w = w[0] + w[1:].lower()                                             # "BogoVić"
    if w.endswith('ie') and k8.known(w[:-2] + 'ić'):
        w = w[:-2] + 'ić'                                                    # "Zilie", "Maglie": -ić
    w = FIXES.get(w, w)
    if 'lc' in w and not k8.known(w) and k8.known(w.replace('lc', 'k')):
        w = w.replace('lc', 'k')                                             # "Žarlcović" = Žarković
    return w[:1].upper() + w[1:]                                             # "šušnjar Janko"


def parse(text: str) -> dict:
    text = text[4:].strip()
    note = ''
    m = re.search(r'\s*\(([^)]*)\)\s*$', text)
    if m:
        note, text = m.group(1).replace('Ugljeia', 'Uglješa'), text[:m.start()]   # "Rajković Milan (mlađi)", "(Ugljeia)"
        note = note if note in ('mlađi', 'stariji') else 'zvani ' + note      # "Dabić Milan (Mačak)"
    parts: list[str] = []
    for w in text.split():
        if parts and re.match(rf'^[{L}]', w) and not re.fullmatch(r'(?:de|di|da|van|von)', w):
            parts[-1] += w                                                   # "Abramo vić Stoj an"
        else:
            parts.append(w)
    parts = [fix_word(p) for p in parts]
    father = ''
    if len(parts) >= 3 and re.fullmatch(rf'[{U}]\.', parts[-2]):
        father = parts.pop(-2)                                               # "Miljević A. Pero"
    if len(parts) == 1:
        return _record(parts[0], '', '', note)
    return _record(parts[0], ' '.join(parts[1:]), father, note)


def post(soldiers: list[dict]) -> list[dict]:
    for s in soldiers:
        box = _box.get((s.get('pdf_page'), s.get('pdf_x'), round(s.get('pdf_y') or 0, 1)))
        if box:
            rects = box.get('pdf_rects')
            s.update({k: v for k, v in box.items() if k != 'rect'})
            if rects and len({r[1] for r in rects}) == len(rects) and rects[-1][0] < rects[0][0]:
                s['pdf_x_left'] = min(r[0] for r in rects)
            if rects:
                s['pdf_x_end'] = max(r[2] for r in rects)
                s['pdf_y_end'] = max(r[3] for r in rects)
    return k8.post(soldiers)


if __name__ == '__main__':
    corpus()
    run_parser(
        pdf_path='website/public/pdfs/3-banijska.pdf',
        brigade_code=108,
        output_path='website/public/3-banijska-soldiers.json',
        start_page=1,
        end_page=None,
        layout='single',
        extract_fn=read_names,
        script='latin',
        entry_start_re=re.compile(r'^§b§'),
        parse_entry_fn=parse,
        post_fn=post,
    )
