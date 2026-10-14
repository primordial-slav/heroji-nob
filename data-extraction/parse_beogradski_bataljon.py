"""
Parser: Prva proleterska brigada (brigade code 1), its Beogradski bataljon: the battalion's roster 1941-1945.

Source: *Beogradski bataljon* (Beograd; znaci.org 00003/499, the whole book's PDF pp. 393-452: "Spisak boraca
Beogradskog bataljona 1941-1945.") → website/public/pdfs/beogradski-bataljon.pdf. After the battalion's command staff
by period (not read: its men are in the roster), every fighter who served in it from the first days of the rising to
1 March 1945, when it became the 3. bataljon of the Prva proleterska, grouped by when he came (the fallen of 1941
before the brigade was formed, those on the day it was formed, 1942, 1943, ...), alphabetical, three columns:
    DAVIDOVIĆ Milutina BUDIMIR — BUDA
    Zemljoradnik, rođen 1920, Stubline, Obrenovac; član KPJ pre ustanka 1941. ... Poginuo 29. novembra 1941. na
    Kadinjači.
The name alone on its line(s) in capitals: SURNAME, the father in small letters (or none), the given name, a nickname
after a dash ("— BUDA"), a duty after a comma ("ALEKSIĆ ŽIVKA — MILA, bolničarka"), two surnames joined by a dash
("BLAGOJEVIĆ — PETROVIĆ JELENA"); then the bio. PyMuPDF's text blocks hold an entry each, or the name and the bio
apart, or a bio carried over to the next column: a block that doesn't start with a name belongs to the one before.
These get 0001300001 on (id_start=300001: the brigade's other books use 0001000001-, 0001100001-, 0001200001-), and the
same man in the brigade's roster is merged (scripts/find_source_duplicates.py --brigade 1).
Usage: python data-extraction/parse_beogradski_bataljon.py
"""
import re

import fitz

import parse_8_kordunaska_divizija as k8
from _parser_scaffold import _record, run_parser

U, L = 'A-ZČĆŽŠĐ', 'a-zčćžšđ'
CAPS = rf'[{U}][{U}1\-]+'                                      # "Ž1VORAD": 1 for I
NAME_START = re.compile(rf'^{CAPS}(?:\s|$)')
FIRST_ROSTER_PAGE = 5                                          # the site PDF's page where the roster begins


def is_name_line(t: str) -> bool:
    """A line of a name: capitals, at most one word in small letters (the father), dashes, a duty after a comma"""
    head = t.split(',')[0]
    words = [w for w in head.replace('—', ' ').split() if w]
    small = [w for w in words if not re.fullmatch(rf'{CAPS}|[{U}]\.', w)]
    return bool(words) and len(small) <= (2 if 'Mali' in small else 1) and not re.search(r'\d{3}', t)


def extract(pdf_path: str, start: int, end: int | None) -> list[dict]:
    lines = []
    with fitz.open(pdf_path) as doc:
        for pno, page in enumerate(doc, 1):
            if pno < FIRST_ROSTER_PAGE:
                continue
            dx, dy = page.mediabox.x0, 1.0
            blocks = [b for b in page.get_text('blocks') if b[4].strip()]
            col = lambda b: 0 if b[0] < 150 else 1 if b[0] < 330 else 2
            for b in sorted(blocks, key=lambda b: (col(b), b[1])):
                rows = [r.strip() for r in b[4].split('\n') if r.strip()]
                text = ' '.join(rows)
                if re.fullmatch(r'[\d\W]{1,5}', text):
                    continue                                   # page numbers
                if re.match(r'^(?:BORCI|Š T A B|ŠTAB BATALJONA|\d{4}\. GODINA|KOMANDNO)', text) or (
                        re.fullmatch(r'[\d. ]*[A-ZČĆŽŠĐ .\-]+', text) and len(text) > 25):
                    continue                                   # the groups' headings
                if NAME_START.match(rows[0]) and is_name_line(rows[0]):
                    n = 1
                    # "ĐURĐEVIĆ / Dragoslava / BRANI- / SLAV": a line in small letters is the father only when the name
                    # goes on in capitals after it ("BARTEN — BUNČIĆ EMILIJA / Krojačka radnica" is the trade)
                    while (n < len(rows) and is_name_line(rows[n]) and not re.search(rf'[{L}]{{3}},', rows[n])
                           and (re.search(rf'{CAPS}|—', rows[n]) or (n + 1 < len(rows) and NAME_START.match(rows[n + 1])
                                                                        and is_name_line(rows[n + 1])))):
                        n += 1
                    name = ''
                    for r in rows[:n]:
                        name = name[:-1] + r if name.endswith('-') else (name + ' ' + r).strip()
                    text = '§x§ ' + name + ' §§ ' + ' '.join(rows[n:])
                lines.append({'text': text, 'x': round(b[0] + dx, 1), 'y': round(b[1] + dy, 1), 'page': pno})
    return lines


def parse(text: str) -> dict:
    name, _, bio = re.sub(r'^§x§\s*', '', text).partition('§§')
    name = name.strip()
    bio = re.sub(r'\s+', ' ', re.sub(r'(?<=[a-zčćžšđ])- (?=[a-zčćžšđ])', '', bio)).strip()
    note = re.search(r'\s*\((.*)$', name)
    if note:                                                   # "BABINAC Joze NEDELJKO (Postoji Bobonac ... spisku)"
        name, bio = name[:note.start()], f'({note.group(1).strip()} {bio}'.strip()
    name = re.sub(rf'\b([{U}])\.(?=[{U}])', r'\1. ', name)    # "ALAGIĆ M.BEĆIR": the father's initial
    duty = ''
    if ',' in name:                                            # "ALEKSIĆ ŽIVKA — MILA, bolničarka"
        name, duty = (x.strip() for x in name.split(',', 1))
    nick = ''
    words = name.replace('—', ' — ').split()
    if len(words) > 2 and words[1] == '—':                    # "BLAGOJEVIĆ — PETROVIĆ JELENA": two surnames
        words = [f'{words[0]}-{words[2]}'] + words[3:]
    if '—' in words:                                           # "VUJIĆ Velimira ĐORĐE — DOKA": the nickname
        i = words.index('—')
        nick, words = ' '.join(words[i + 1:]), words[:i]
    caps = [k8.caps_word(w) for w in words]
    small = [w for w in words if re.fullmatch(rf'[{U}][{L}]+|[{U}]\.', w)]          # the father, or his initial
    big = [c for w, c in zip(words, caps) if w not in small]
    last = big[0] if big else ''
    given = k8.join_parts(big[1:], 'first_name') if len(big) > 1 else ''   # "STE VAN" = Stevan
    father = small[0] if small else ''
    notes = ([f"zvani {nick.title()}"] if nick else []) + ([duty] if duty else [])
    info = '; '.join(notes + ([bio] if bio else []))
    rec = _record(k8.caps_word(last).title() if last.isupper() else last, given.title(), father, info)
    y = re.search(r'\bro[dđ]en[a]?\s+(1[89]\d\d)', bio)
    rec['birth_year'] = y.group(1) if y else ''
    return rec


if __name__ == '__main__':
    k8.corpus()
    run_parser(
        pdf_path='website/public/pdfs/beogradski-bataljon.pdf',
        brigade_code=1,
        output_path='website/public/prva-proleterska-soldiers.json',
        start_page=1,
        end_page=None,
        layout='single',
        script='latin',
        entry_start_re=re.compile(r'^§x§'),
        parse_entry_fn=parse,
        extract_fn=extract,
        post_fn=k8.post,
        id_start=300001,
        keep_other_sources=True,
    )
