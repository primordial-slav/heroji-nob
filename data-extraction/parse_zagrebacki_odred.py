"""
Parser: Zagrebački partizanski odred (brigade code 147): the roster of its fighters.

Source: *Zagrebački partizanski odred - zbornik dokumenata i sjećanja* (znaci.org 00003/607, the whole book's PDF
pp. 417-428, book pp. 407-418: "Popis boraca Zagrebačkog partizanskog odreda") →
website/public/pdfs/zagrebacki-odred.pdf. 906 fighters, by the editors' note mostly those who registered with the
SUBNOR of Zelina after the war, and the fallen the odred's papers and its men's memoirs name; the battalions that
went whole to the "Matija Gubec" and Zagorska brigades are not in it. A fighter a line, alphabetical, one column:
    ANTOLKOVIĆ TOMO, Kalinje, Zelina, poginuo u Karivarošu, Donja Stubica, 15. 3. 1944. pokopan u Mateju, ...
    ROČIĆ Mirka MIRKO, Dešćevec, Zagreb
    RIHTER MILAN - TEŠKI, Radoboj, Krapina
The surname and the given name in capitals, the father in small letters between them (genitive) at times, a
nickname after a dash; then the village and the municipality, and what became of him.
Usage: python data-extraction/parse_zagrebacki_odred.py
"""
import re

import pdfplumber

import parse_8_kordunaska_divizija as k8
from _parser_scaffold import _record, run_parser
from pdf_coords import viewer_words

U, L = 'A-ZČĆŽŠĐ', 'a-zčćžšđ'
CAPS = rf'[{U}][{U}\-]+'
FIRST_ENTRY = 'ANDRIŠEVIĆ'                              # the list's first name, under the editors' note


def gutter(words: list[dict]) -> float:
    """The x between the two columns: the middle of the widest strip near the page's text middle no word crosses"""
    lo, hi = min(w['x0'] for w in words), max(w['x1'] for w in words)
    mid = (lo + hi) / 2
    best, x = (0, mid), mid - 120
    while x < mid + 120:
        if not any(w['x0'] < x < w['x1'] for w in words):
            run = x
            while run < mid + 120 and not any(w['x0'] < run < w['x1'] for w in words):
                run += 1
            if run - x > best[0]:
                best = (run - x, (x + run) / 2)
            x = run
        x += 1
    return best[1]


def extract(pdf_path: str, start: int, end: int | None) -> list[dict]:
    lines = []
    with pdfplumber.open(pdf_path) as pdf:
        for pno, page in enumerate(pdf.pages, 1):
            words = viewer_words(page, keep_blank_chars=False)
            if pno == 1:                                  # the title and the editors' note, across both columns
                top = min(w['top'] for w in words if w['text'] == FIRST_ENTRY)
                words = [w for w in words if w['top'] >= top - 2]
            split = gutter(words)
            rows = []
            for col in (0, 1):                            # two columns: the left one down the page, then the right
                for w in sorted([w for w in words if (w['x0'] >= split) == bool(col)],
                                key=lambda w: (round(w['top']), w['x0'])):
                    if rows and rows[-1][0]['col'] == col and abs(rows[-1][0]['top'] - w['top']) <= 3:
                        rows[-1].append({**w, 'col': col})
                    else:
                        rows.append([{**w, 'col': col}])
            for r in rows:
                r.sort(key=lambda w: w['x0'])
                text = ' '.join(w['text'] for w in r)
                if re.fullmatch(r'[\d\W]{1,5}', text):
                    continue                          # page numbers
                lines.append({'text': text, 'x': r[0]['x0'], 'y': r[0]['top'], 'page': pno})
    out = []
    for ln in lines:
        t = ln['text'] = ln['text'].replace('Frošinić Janko NIKOLA', 'GROŠINIĆ Janko NIKOLA').replace('H-UČIĆ', 'HUČIĆ')
        # an entry: a line that starts with a surname in capitals ("ROČIĆ Mirka MIRKO", "KALAFATIĆ puškomitraljezac",
        # "MALTARIĆ (mama)", "SUTLAR-Stjepana STJEPAN"); the lines of an entry that run on start in small letters,
        # with a number or with a place
        if re.match(rf'^[{U}ÜÖÄ]{{2}}[{U}ÜÖÄ\-]*(?=[\s,;(\-—]|$)', t) \
                and not re.match(r'^(?:NOB|NOV|KPJ|KPH|SKOJ|SSSR|ZAVNOH|SAD|VPB|OK|KK)\b', t):
            t = '§x§ ' + t
        ln['text'] = t
        out.append(ln)
    return out


def parse(text: str) -> dict:
    t = re.sub(r'^§x§\s*', '', text)
    t = re.sub(r'(?<=[a-zčćžšđ])- (?=[a-zčćžšđ])', '', t)        # "po- ginuo"
    head, _, info = re.split(r'[,;]', t, 1)[0], None, ''
    if re.search(r'[,;]', t):
        head, info = re.split(r'[,;]', t, 1)
    notes = []
    head = re.sub(rf'(?<=[{U}])-(?=[{U}][{L}])', ' ', head.strip())     # "SUTLAR-Stjepana STJEPAN": the father
    head = re.sub(r'\s*—\s*', '-', head)                                 # "ŠKRLIN — BATINA Petra PETAR"
    given_after = re.match(rf'^\s*({CAPS})\s*,\s*(.*)$', info)
    if given_after and re.fullmatch(rf'{CAPS}\s+[{U}][{L}]+', head):      # "KIRINEC Ignaca, IVAN, Orešje Gornje"
        head, info = f'{head} {given_after.group(1)}', given_after.group(2)
    head = re.sub(r'\s*-\s*', '-', head)
    words = head.split()
    if len(words) >= 2 and '-' in words[-1] and re.fullmatch(rf'{CAPS}-{CAPS}', words[-1]) and len(words) >= 2:
        given, nick = words[-1].split('-', 1)               # "ANTOLKOVIĆ FRANJO-DAŠA", "RIHTER MILAN - TEŠKI"
        words[-1] = given
        notes.append(f'zvani {k8.caps_word(nick).title()}')
    caps = [w for w in words if re.fullmatch(CAPS, w)]
    small = [w for w in words if not re.fullmatch(CAPS, w)]
    last = caps[0] if caps else (words[0] if words else '')
    given = ' '.join(caps[1:2]) or (small[-1] if small and len(caps) == 1 else '')
    father = small[0] if small and len(caps) >= 2 else ''
    rest = caps[2:]                                      # "SAVELJEV MIHAIL PAVLOVIĆ": a Russian's patronymic
    if rest:
        notes.append(' '.join(k8.caps_word(w).title() for w in rest))
    rec = _record(k8.caps_word(last).title(), k8.caps_word(given).title() if given.isupper() else given, father,
                  '; '.join(notes + ([info.strip()] if info.strip() else [])))
    rec['birth_year'] = ''
    return rec


if __name__ == '__main__':
    k8.corpus()
    run_parser(
        pdf_path='website/public/pdfs/zagrebacki-odred.pdf',
        brigade_code=147,
        output_path='website/public/zagrebacki-odred-soldiers.json',
        start_page=1,
        end_page=None,
        layout='single',
        script='latin',
        entry_start_re=re.compile(r'^§x§'),
        parse_entry_fn=parse,
        extract_fn=extract,
        post_fn=k8.post,
    )
