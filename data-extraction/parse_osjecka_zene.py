"""
Parser: Osječka udarna brigada (brigade code 104), second book: its women fighters, by battalion.

Source: *Žene Hrvatske u narodnooslobodilačkoj borbi* (znaci.org 00003/585, the whole book's PDF pp. 279-282: Dokument
420, "Žene borci Osječke brigade XII. udarne divizije", the women of each battalion as the brigade's staff listed them
for the I. kongres AFŽ Hrvatske) → website/public/pdfs/osjecka-zene.pdf. A table: number, surname and given name,
date of birth, place, "u partizanima od", under each battalion's heading ("Drugarice II. bataljona Osječke brigade:").
The cells of a row don't stand on one line in the text layer, so each is given to the name nearest it.
These get 0104010001 on, after the brigade's book (parse_osjecka.py), and a woman in both is merged
(scripts/find_source_duplicates.py --brigade 104).
Usage: python data-extraction/parse_osjecka_zene.py
"""
import re

import pdfplumber

import parse_8_kordunaska_divizija as k8
from _parser_scaffold import _record, run_parser
from pdf_coords import viewer_words

U, L = 'A-ZČĆŽŠĐ', 'a-zčćžšđ'
ROMAN = {'I': 1, 'II': 2, 'III': 3, 'IV': 4, 'V': 5}


def extract(pdf_path: str, start: int, end: int | None) -> list[dict]:
    out, battalion = [], 1
    with pdfplumber.open(pdf_path) as pdf:
        for pno, page in enumerate(pdf.pages, 1):
            words = viewer_words(page, keep_blank_chars=False)
            head = {}
            for w in words:
                if w['text'] in ('PREZIME', 'Mjesto', 'U') and w['text'] not in head:
                    head[w['text']] = w
                if w['text'].startswith('Rođ') and 'Rođ' not in head:
                    head['Rođ'] = w
            x_name, x_born = head['PREZIME']['x0'] - 15, head['Rođ']['x0'] - 15
            x_place, x_joined = head['Mjesto']['x0'] - 25, head['U']['x0'] - 15
            top = max(w['bottom'] for w in words if abs(w['top'] - head['PREZIME']['top']) < 25 and w['x0'] > x_name - 60) + 1
            body = [w for w in words if w['top'] > top]
            end = next((w['top'] for w in body if w['text'].startswith(('Spisak', 'Listu')) and w['top'] > 600), None)
            if pno == len(pdf.pages):                    # the staff's note under the last rows
                notes = [w['top'] for w in body if re.match(r'[„»]?Ž?Štab|poslao|Smrt', w['text'])]
                end = min(notes) - 2 if notes else end
            body = [w for w in body if end is None or w['top'] < end]
            rows = []
            for w in sorted([w for w in body if x_name <= w['x0'] < x_born], key=lambda w: (round(w['top']), w['x0'])):
                if rows and abs(rows[-1][0]['top'] - w['top']) <= 3:
                    rows[-1].append(w)
                else:
                    rows.append([w])
            anchors = []
            for r in rows:
                text = ' '.join(w['text'] for w in sorted(r, key=lambda w: w['x0']))
                m = re.search(r'\b(I{1,3}|IV|V)\.\s*bataljona', text + ' ' + ' '.join(
                    w['text'] for w in body if abs(w['top'] - r[0]['top']) < 3 and w['x0'] >= x_born))
                if m or 'bataljona' in text or re.search(r'rugarice|ugarice', text):
                    battalion = ROMAN.get(m.group(1), battalion) if m else battalion
                    continue
                if not re.search(rf'[{U}][{L}]', text) or text.startswith('Ovaj'):
                    continue                                 # specks; the editors' note under the table
                anchors.append({'top': r[0]['top'], 'x': r[0]['x0'], 'name': text, 'born': [], 'place': [], 'joined': [],
                                 'battalion': battalion})
            for w in body:
                if w['x0'] < x_born or not anchors:
                    continue
                a = min(anchors, key=lambda a: abs(a['top'] - w['top']))
                if abs(a['top'] - w['top']) > 12:
                    continue
                a['born' if w['x0'] < x_place else 'place' if w['x0'] < x_joined else 'joined'].append(w)
            for a in anchors:
                order = lambda ws: ' '.join(w['text'] for w in sorted(ws, key=lambda w: (round(w['top']), w['x0'])))
                text = f"§x§ {a['name']} ¦ {order(a['born'])} ¦ {order(a['place'])} ¦ {order(a['joined'])} ¦ {a['battalion']}"
                out.append({'text': text, 'x': a['x'], 'y': a['top'], 'page': pno})
    return out


def date(t: str) -> str:
    """Day, month, year, whichever line of the cell each stands on ("6. 1927 X." = 6. X. 1927)"""
    t = re.sub(r'(?<=[IVX])\s(?=[IVX])', '', t.replace('i.', '1.').replace('l.', '1.'))   # "V I I I" = VIII
    day = re.search(r'(?<![\w.])(\d{1,2})\.(?!\d)', t)
    month = re.search(r'\b([IVX]{1,4})\b\.?', t)
    year = re.search(r'\b(1[89]\d\d)\b', t)
    if month and year:
        return ' '.join(x for x in (f'{day.group(1)}.' if day else '', f'{month.group(1)}.', f'{year.group(1)}.') if x)
    return re.sub(r'\s+', ' ', t).strip()


def parse(text: str) -> dict:
    name, born, place, joined, bat = [x.strip() for x in re.sub(r'^§x§\s*', '', text).split('¦')]
    name = re.sub(r'^(?:\d{1,2}|[IVXl]{1,2}|i8|IO|l i)\s+', '', name).replace('E vica', 'Evica')
    words = name.split()
    last, given = words[0], ' '.join(words[1:])
    info = f"{bat}. bataljon; rođena {date(born)} {place}; u partizanima od {date(joined)}"
    rec = _record(last, given, '', info.replace(', ;', ';').replace('rođena ,', 'rođena').strip())
    y = re.search(r'\b(1[89]\d\d)\b', born)
    rec['birth_year'] = y.group(1) if y else ''
    return rec


if __name__ == '__main__':
    k8.corpus()
    run_parser(
        pdf_path='website/public/pdfs/osjecka-zene.pdf',
        brigade_code=104,
        output_path='website/public/osjecka-soldiers.json',
        start_page=1,
        end_page=None,
        layout='single',
        script='latin',
        entry_start_re=re.compile(r'^§x§'),
        parse_entry_fn=parse,
        extract_fn=extract,
        post_fn=k8.post,
        id_start=10001,
        keep_other_sources=True,
    )
