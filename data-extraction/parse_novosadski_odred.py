"""
Parser: Novosadski partizanski odred (brigade code 169).

Source: Vanja Sanader, "Novosadski partizanski odred - dva puta rođen" (SUBNOR Novog Sada, 2025; edicija Vojvodina
        u borbi 78; znaci.org 00003/2851.pdf) →  website/public/pdfs/novosadski-odred.pdf (book pp. 85-92):
    "Popis pripadnika Novosadskog partizanskog odreda 1941. godine" (the odred of 1941, broken up that autumn) and
    "... 1944. godine" (formed anew in August 1944 at Palenkašev salaš), Cyrillic, one a line under letter headings:
        Балаж Павел Дадо, борац Новосадског одреда, из Бачког Пет-
        ровца
The year of the list goes into each entry. A third name before the comma is what he was called.
"""
import re

from _parser_scaffold import _record, cyrillic_to_latin, extract_lines_single_column, run_parser

U, L = 'A-ZČĆŽŠĐ', 'a-zčćžšđ'


def extract(pdf_path: str, start: int, end: int | None) -> list[dict]:
    out, year, prev = [], '', ''
    for ln in extract_lines_single_column(pdf_path, start, end):
        t = cyrillic_to_latin(ln['text']).strip()
        m = re.search(r'ODREDA (19\d\d)\. GODINE', t)
        if m:
            year = m.group(1)
            continue
        if re.fullmatch(rf'[{U}]|\d{{1,3}}|POPIS PRIPADNIKA.*', t) or re.match(r'^\d{2}\s+Podatke', t):
            continue
        words = t.split()
        starts = (len(words) >= 2 and re.match(rf'^[{U}]', words[0]) and re.match(rf'^[{U}]', words[1])
                  and not prev.endswith('-') and (',' in t or len(words) <= 3) and not re.search(r'\d', words[1]))
        out.append(dict(ln, text=(f'§x§{year}§ ' if starts else '') + t))
        prev = t
    return out


def parse_entry(text: str) -> dict:
    m = re.match(r'^§x§(\d*)§\s*(.*)$', text, re.S)
    year, t = m.group(1), re.sub(r'(?<=[a-zčćžšđ])-\s+(?=[a-zčćžšđ])', '', m.group(2))
    t = re.sub(r'\s+', ' ', t).strip()
    head, _, rest = t.partition(',')
    words = head.split()
    last, given = words[0], words[1] if len(words) > 1 else ''
    notes = ['zvani ' + ' '.join(words[2:])] if len(words) > 2 else []
    rest = rest.strip()
    rest = re.sub(r'\bkomdant\b', 'komandant', rest)
    rest = re.sub(r'(?<=[\s.])H(?=\s*(?:-|–|19))', 'X', rest)                 # Cyrillic Х, the Roman ten
    info = '; '.join(notes + ([rest] if rest else []) + [f'u odredu {year}. godine'] if year else notes + [rest])
    rec = _record(last, given, '', info)
    home = re.search(r'\biz ([^,;]+)', rest)
    if home:
        rec['_from'] = home.group(1)
    return rec


def post(soldiers: list[dict]) -> list[dict]:
    for s in soldiers:
        s.pop('_from', None)
    return soldiers


if __name__ == '__main__':
    run_parser(
        pdf_path='website/public/pdfs/novosadski-odred.pdf',
        brigade_code=169,
        output_path='website/public/novosadski-odred-soldiers.json',
        start_page=1,
        end_page=None,
        extract_fn=extract,
        script='latin',                                                       # read into Latin in extract
        entry_start_re=re.compile(r'^§x§'),
        parse_entry_fn=parse_entry,
        post_fn=post,
    )
