"""
Parser: 4. brigada Slavonije (2. brodska; brigade code 129): its fallen and its wounded.

Source: Stanko Obradović, Antun Miletić, *4. NOU brigada Slavonije (Druga brodska brigada)* (znaci.org 00001/190,
the chapter 190_6.pdf "Fotografije, spisak poginulih i ranjenih boraca", its PDF pp. 19-41, book p. 164 on) →
website/public/pdfs/4-brigada-slavonije.pdf. Two tables:
    Prilog 2, "Spisak poginulih boraca i rukovodilaca brigade" (PDF pp. 20-31): surname, father and given name;
        company, rank and duty; date and place of birth; date and place of death:
        ADAMOVIĆ Laze PERO | int. oficir 4. bataljona | 5. VIII 1922. Osijek | 14. II 1945. Slav. Drenovac
    Prilog 3, "Spisak ranjenih boraca i rukovodilaca brigade" (pp. 32-41): name; unit, rank and duty; when wounded.
The columns stand at a different place on every page, so each page's header ("PREZIME", "JEDINICA", "DATUM",
"DATUM") gives them; an entry starts where the first column has a surname in capitals, and the lines under it hold
the rest of its cells. The tables' footnotes are not read. The scan loses carons ("ADAMOVIC"), which the corpus gives
back (parse_8_kordunaska_divizija.post).
Usage: python data-extraction/parse_4_brigada_slavonije.py
"""
import re

import pdfplumber

import parse_8_kordunaska_divizija as k8
from _parser_scaffold import run_parser
from pdf_coords import viewer_words

U = 'A-ZČĆŽŠĐ'
FALLEN, WOUNDED = range(2, 14), range(14, 24)      # the site PDF's pages (its p. 1 is the list's title page)


def undouble(w: str) -> str:
    """Some lines' text layer prints each letter twice ("JJAAKKUUPPAACC", "bbaattaalljjoonn")"""
    return w[0::2] if len(w) >= 4 and len(w) % 2 == 0 and w[0::2] == w[1::2] else w


def extract(pdf_path: str, start: int, end: int | None) -> list[dict]:
    lines = []
    with pdfplumber.open(pdf_path) as pdf:
        for pno, page in enumerate(pdf.pages, 1):
            kind = 'f' if pno in FALLEN else 'w' if pno in WOUNDED else ''
            if not kind:
                continue
            words = viewer_words(page, keep_blank_chars=False)
            # the header: the lines around "PREZIME, OČEVO IME I IME", wherever the page sets it
            pz = next((w for w in words if w['text'].startswith('PREZIME')), None)
            top = max(w['bottom'] for w in words if pz and pz['top'] - 12 <= w['top'] <= pz['top'] + 16) if pz else 0
            rows = []
            for w in sorted([w for w in words if w['top'] > top + 2], key=lambda w: (round(w['top']), w['x0'])):
                if rows and abs(rows[-1][0]['top'] - w['top']) <= 3:
                    rows[-1].append(w)
                else:
                    rows.append([w])
            # the footnote: the first line that starts with "*" and runs on ("* Spisak je rađen prema ...")
            end = next((i for i, r in enumerate(rows) if r[0]['text'].startswith('*') and len(r) > 6), len(rows))
            rows = [r for r in rows[:end] if not re.fullmatch(r'\d{1,3}', ' '.join(w['text'] for w in r))]
            # the columns: the strips no word of the table's body crosses (headers are centred over their columns,
            # so their own places would cut "2. četa" off its column)
            spans = sorted((w['x0'], w['x1']) for r in rows for w in r)
            starts, reach = [], None
            for x0, x1 in spans:
                if reach is None or x0 > reach + 6:
                    starts.append(x0)
                reach = x1 if reach is None else max(reach, x1)
            if len(starts) != (4 if kind == 'f' else 3):
                # the wounded table's names nearly touch the next column: its edges just left of the header's words
                marks = [w['x0'] for w in words if w['text'].startswith(('JEDINICA', 'KADA', 'DATUM'))
                         and pz and abs(w['top'] - pz['top']) < 14]
                starts = [0] + sorted(m - 18 for m in marks)
            name, prev_top = '', None
            for r in rows:
                cols = [[] for _ in starts]
                for w in sorted(r, key=lambda w: w['x0']):
                    i = max([j for j, s in enumerate(starts) if w['x0'] >= s - 6] or [0])
                    cols[i].append(undouble(w['text']))
                cells = [' '.join(c) for c in cols]
                first = cells[0] if cells else ''
                new = bool(re.match(rf'^[{U}][{U}lI1\-]{{1,}}(?:\s|$)', first))
                # "LUPTOVSKI Stjepana" / "SLAVKO", "GASPAREVIC" / "DRAGAN": the given name on the entry's next line, a
                # line's height below (entries start a line and a half apart), while its name has no given name yet
                close = prev_top is not None and r[0]['top'] - prev_top < 12
                if new and close and not re.search(rf'\s[{U}][{U}lI1\-]+$', name):
                    new = False
                prev_top = r[0]['top']
                name = first if new else f'{name} {first}'.strip()
                # a row's cells between "¦", the row closed by "¦¦" (the scaffold joins an entry's rows with spaces)
                text = ('§' + kind + '§ ' if new else '') + ' ¦ '.join(cells) + ' ¦¦'
                lines.append({'text': text, 'x': r[0]['x0'], 'y': r[0]['top'], 'page': pno})
    return lines


def parse(text: str) -> dict:
    m = re.match(r'^§([fw])§\s*(.*)$', text)
    kind, body = m.group(1), m.group(2)
    n = 4 if kind == 'f' else 3
    cols = [[] for _ in range(n)]                     # each column's cells, row by row
    for row in body.split('¦¦'):
        for i, cell in enumerate(row.split(' ¦ ')[:n]):
            if cell.strip():
                cols[i].append(cell.strip())
    name, unit = ' '.join(cols[0]).strip(), ' '.join(cols[1]).strip()
    if kind == 'f':
        born, died = ' '.join(cols[2]).strip(), ' '.join(cols[3]).strip()
        info = '; '.join(x for x in (unit, f'rođen {born}' if born else '', f'poginuo {died}' if died else '') if x)
    else:
        when = ' '.join(cols[2]).strip()
        info = '; '.join(x for x in (unit, f'ranjen {when}' if when else '') if x)
    info = re.sub(r'(?<=[a-zčćžšđ])- (?=[a-zčćžšđ])', '', info)          # "Daru- var": a word broken in its cell
    rec = k8.parse_entry(f'{name}, {info}.' if info else name)
    rec.pop('unit_detail', None)
    y = re.search(r'\b(1[89]\d\d)\b', ' '.join(cols[2]) if kind == 'f' else '')
    rec['birth_year'] = y.group(1) if y else ''
    return rec


if __name__ == '__main__':
    k8.corpus()
    run_parser(
        pdf_path='website/public/pdfs/4-brigada-slavonije.pdf',
        brigade_code=129,
        output_path='website/public/4-brigada-slavonije-soldiers.json',
        start_page=1,
        end_page=None,
        layout='single',
        script='latin',
        entry_start_re=re.compile(r'^§[fw]§'),
        parse_entry_fn=parse,
        extract_fn=extract,
        post_fn=k8.post,
    )
