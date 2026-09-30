"""
Parser: 7. crnogorska omladinska NOU brigada "Budo Tomović" (brigade code 28) — the fallen.

Source: Mitar Đurišić — "Sedma crnogorska omladinska brigada »Budo Tomović«", chapter "Spisak poginulih boraca"
        znaci.org/00001/64_4.pdf  →  website/public/pdfs/7-crnogorska-omladinska.pdf
pp. 2-37 a table of the 439 fallen, one row per soldier (then the book's indexes), in Cyrillic and Latin:
    Red. broj | Prezime, očevo ime i ime | Godina i mjesto rođenja | U kojoj je jedinici bio | Kad je i gdje poginuo
    1.        | AVDIĆ / Hajradina / ĆAZIM | 1926, Biševo, Rožaj  | 4. bataljon  | 24. I 1945, na Senokosu, Goražde
Each page starts with a row of column numbers "1 2 3 4 5"; read_rows puts each column's left edge ~30pt left of
its number, starts a row at a gap in the name column, and hands run_parser one line per row:
    "AVDIĆ⁣ Hajradina ĆAZIM, 1926, Biševo, Rožaj, 4. bataljon, poginuo 24. I 1945, na Senokosu, Goražde"
"""
import re

import pdfplumber

from _parser_scaffold import _record, cyrillic_to_latin, extract_birth_year, repair_cyrillic_ocr, repair_lj_ocr, \
    restore_diacritics, run_parser
from pdf_coords import viewer_words

MARK = '⁣'


def _lines(words: list[dict]) -> list[list[dict]]:
    rows = []
    for w in sorted(words, key=lambda w: (w['top'], w['x0'])):
        if rows and abs(rows[-1][0]['top'] - w['top']) < 4:
            rows[-1].append(w)
        else:
            rows.append([w])
    return [sorted(r, key=lambda w: w['x0']) for r in rows]


def read_rows(pdf_path: str, start: int, end: int | None) -> list[dict]:
    out, by_parity = [], {}              # a page without the header row: the last page of the same parity
    with pdfplumber.open(pdf_path) as pdf:
        for pno in range(start, (end or len(pdf.pages)) + 1):
            page = pdf.pages[pno - 1]
            words = viewer_words(page)
            page.close()
            header = next((ln for ln in _lines(words) if [w['text'] for w in ln] == ['1', '2', '3', '4', '5']), None)
            row_no_x = min((w['x0'] for w in words if re.fullmatch(r'\d{1,3}[.,]', w['text']) and w['x0'] < 100), default=None)
            if header:
                c = [(w['x0'] + w['x1']) / 2 for w in header]
                # a column's text starts ~30pt left of its number (the name column's ~50pt)
                by_parity[pno % 2] = ([c[1] - 52, c[2] - 31, c[3] - 31, c[4] - 34], row_no_x)
                top = header[0]['bottom']
            else:
                top = 0
            if pno % 2 not in by_parity:
                continue
            bounds, ref_x = by_parity[pno % 2]
            if not header and row_no_x is not None and ref_x is not None:      # shifted like the row numbers
                bounds = [b + row_no_x - ref_x for b in bounds]
            body = [w for w in words if w['top'] > top + 2 and not re.fullmatch(r'\d{1,3}\*?', w['text'])]  # page no.
            col = lambda w: sum(w['x0'] >= b for b in bounds)       # 0 = number, 1 = name, 2-4 the rest
            names = [ln for ln in _lines([w for w in body if col(w) == 1])]
            if not names:
                continue
            # a row's name cell is SURNAME / [Father] / GIVEN: a caps line starts a row once the row has both caps
            # lines. Neither gaps (a blank father line leaves the same gap as a new row: "JOKIĆ / / MILORAD") nor
            # the row numbers (sometimes read on the row's last line) mark rows reliably.
            # A numbered caps line that the next name line follows at the line pitch also starts one (after a row
            # with no given name). On p. 25 the numbers sit on a row's last line, which a gap follows.
            numbered = [w['top'] for w in body if col(w) == 0 and re.fullmatch(r'\d{1,3}[.,]', w['text'])]
            starts, caps, prev = [], 0, ''
            for i, ln in enumerate(names):
                first_word = ln[0]['text'].strip('.,*„"\'')
                # "MILOVAN-MI-" / "LOSAV": the second line finishes the given name
                is_caps = len(first_word) > 1 and first_word.isupper() and not prev.endswith('-')
                prev = ln[-1]['text']
                gap_next = names[i + 1][0]['top'] - ln[0]['top'] if i + 1 < len(names) else 99
                anchored = is_caps and any(abs(ln[0]['top'] - y) < 4 for y in numbered) and gap_next <= 12
                if is_caps and (not starts or caps >= 2 or anchored):
                    starts.append(ln[0]['top'])
                    caps = 1
                elif is_caps:
                    caps += 1
            for i, y in enumerate(starts):
                y_end = starts[i + 1] - 3 if i + 1 < len(starts) else 1e9
                cells = {k: [w for w in body if col(w) == k and y - 4 <= w['top'] < y_end] for k in (1, 2, 3, 4)}
                name_lines = [' '.join(w['text'] for w in ln) for ln in _lines(cells[1])]
                first = cells[1][0] if cells[1] else None
                if not first or not name_lines or not re.match(r'^[A-ZČĆŽŠĐА-ЯЂЋЏЉЊЈ]{2}', name_lines[0]):
                    continue                                          # the closing note on p. 37
                name_lines[0] = re.sub(r'^(\S+)', r'\1' + MARK, name_lines[0], count=1)
                born, unit, death = (' '.join(w['text'] for w in _flat(cells[k])) for k in (2, 3, 4))
                out.append({'text': ' '.join(name_lines) + ' | ' + ' | '.join((born, unit, death)),
                            'x': first['x0'], 'y': round(first['top'], 1), 'page': pno})
    return out


def _flat(words: list[dict]) -> list[dict]:
    return [w for ln in _lines(words) for w in ln]


def parse_entry(text: str) -> dict:
    """SURNAME [Father] GIVEN [(note)] | born | unit | killed"""
    cells = re.split(r'\s*\|\s*', text.replace(MARK, '')) + ['', '', '']          # an empty last cell loses its space
    name, born, unit, death = (re.sub(r'(\w)- (\w)', r'\1\2', x) for x in cells[:4])
    note = re.findall(r'\(([^)]*)\)', name)
    name = [re.sub(r"[^A-Za-zčćžšđČĆŽŠĐ\-]", '', w) for w in re.sub(r'\s*\([^)]*\)', '', name).split()]
    name = [w for w in name if w]
    last = name[0] if name else ''
    father = next((w for w in name[1:] if re.match(r'^[A-ZČĆŽŠĐ][a-zčćžšđ]', w)), '')
    given = [w for w in name[1:] if w != father]
    while len(given) > 1 and len(given[0]) <= 2:                        # "KO NSTANTIN"
        given[0:2] = [given[0] + given[1]]
    if len(given) > 1:                                                  # "ĐORĐE Đoko": a nickname
        note.append('zvani ' + ' '.join(w.capitalize() for w in given[1:]))
    given = given[0] if given else ''
    death = death.strip()
    if death and re.match(r'^(\d|na |u |kod |[A-ZČĆŽŠĐ][a-zčćžšđ]+ 19)', death):
        death = 'poginuo ' + death
    info = ', '.join(x.strip(' ,') for x in (', '.join(note), born, unit, death) if x.strip(' ,'))
    rec = _record(last, given, father, info)
    rec['birth_year'] = rec['birth_year'] or extract_birth_year(born) or (re.match(r'^(1[89]\d\d)', born.strip()) or [''])[0][:4]
    return rec


def post(soldiers: list[dict]) -> list[dict]:
    return repair_lj_ocr(restore_diacritics(repair_cyrillic_ocr(soldiers)))


if __name__ == '__main__':
    run_parser(
        pdf_path='website/public/pdfs/7-crnogorska-omladinska.pdf',
        brigade_code=28,
        output_path='website/public/7-crnogorska-soldiers.json',
        start_page=2,
        end_page=37,
        script='cyrillic',
        extract_fn=read_rows,
        entry_start_re=re.compile(r'^\S+' + MARK),
        parse_entry_fn=parse_entry,
        post_fn=post,
    )
