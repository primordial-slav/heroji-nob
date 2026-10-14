"""
Parser: Vrhovni štab NOV i POJ (brigade code 112), second book: the workers of its Vojnotehnička radionica (the
military workshop) in Grmeč, 1942-1943.

Source: *Vojnotehnička radionica Vrhovnog štaba NOV i POJ u Grmeču* (grupa autora; znaci.org 00003/766.pdf, PDF pp.
        359-362) → website/public/pdfs/vtr-grmec.pdf (book pp. 361-364), one column, a worker a line or two:
    "Ljubičić Mile Meho, inženjer, upravnik radionice, iz Zagreba,"
Five lists: the workers, those who fell or died during or after the war, workers of whom the editors know nothing
more, the workshop's guards, the workers of the Drvar foundry. The prose after them (villagers who came now and then)
is not read, nor is the one "odbornik" (a member of a people's committee, not of the workshop) among the dead. A line
starts an entry where the line before closed one (with a comma or a full stop); a third name is what he was called.
The OCR's broken names are read back (`WORDS`), a lost caron from the site's spellings and -ič as -ić.
IDs from 0112010001 (`id_start=10001`, `keep_other_sources`).
Usage: python data-extraction/parse_vtr_grmec.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import fitz

sys.stdout.reconfigure(encoding='utf-8')
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import _karlovac_lists as kl  # noqa: E402
import parse_ofanziva_1942 as ofz  # noqa: E402
from _parser_scaffold import _record, extract_lines_single_column, run_parser  # noqa: E402

PDF = HERE.parent / 'website' / 'public' / 'pdfs' / 'vtr-grmec.pdf'
SOURCE = HERE / '.cache' / 'vtr' / '766.pdf'                         # znaci.org/00003/766.pdf
OUTPUT = HERE.parent / 'website' / 'public' / 'vrhovni-stab-soldiers.json'
U, L = 'A-ZČĆŽŠĐ', 'a-zčćžšđ'
SECTIONS = [('SPISAK', 'Radnici Vojnotehničke radionice VŠ u Grmeču'),
            ('POGINULI ILI UMRLI', 'Radnici Vojnotehničke radionice VŠ u Grmeču, poginuli ili umrli u toku rata i posle rata'),
            ('RADNICI KOJI SU BILI U VOJNOTEHNIČKOJ', 'Radnici Vojnotehničke radionice VŠ u Grmeču za koje redakcija nema detaljnijih podataka'),
            ('DRUGOVI KOJI SU BILI NA OBEZBEĐENJU', 'Obezbeđenje Vojnotehničke radionice VŠ u Grmeču'),
            ('RADNICI KOJI SU RADILI U DRVARSKOJ LIVNICI', 'Radnici drvarske livnice (Vojnotehnička radionica VŠ)')]
HEADING_LINES = re.compile(r'^(?:SPISAK|RADNIKA KOJI|RADIONICI|POGINULI ILI|RADNICI KOJI|DRUGOVI KOJI|VOJNOTEHNIČKE|'
                           r'DETALJNIJIH|\d{3})')
WORDS = {'Ra di voj evie': 'Radivojević', 'Stoj an': 'Stojan', 'Maj kič': 'Majkić', 'Voj in': 'Vojin',
         'Živkoviić': 'Živković', 'Basic': 'Bašić', 'Dorđe': 'Đorđe', 'Cučković': 'Čučković'}
NOT_WORKERS = {'Štrbac Kajica'}                                       # "odbornik, umro u toku rata"


def build_pdf() -> None:
    if not PDF.exists():
        out = fitz.open()
        out.insert_pdf(fitz.open(SOURCE), from_page=358, to_page=361)
        out.save(PDF, garbage=4, deflate=True)


def extract(pdf_path: str, start: int, end: int | None) -> list[dict]:
    out, section, prev_closed, done = [], '', True, False
    for ln in extract_lines_single_column(pdf_path, start, end):
        t = ln['text'].strip()
        if done:
            break
        if t.startswith('Sjećanja su izbledjela'):
            done = True
            continue
        hit = next((title for key, title in SECTIONS if t.startswith(key)), None)
        if hit:
            section, prev_closed = hit, True
            continue
        if HEADING_LINES.match(t) or not section:
            continue
        t = re.sub(r'^[šžč](?=[a-zčćžšđ])', lambda m: m.group(0).upper(), t)   # "šop Mijat" = Šop
        for a, b in WORDS.items():
            t = t.replace(a, b)
        starts = prev_closed and re.match(rf'^[{U}][{L}]+\s+[{U}]', t)
        out.append(dict(ln, text=(f'§{SECTIONS.index(next(s for s in SECTIONS if s[1] == section))}§ ' if starts else '') + t))
        prev_closed = bool(re.search(r'[,.]$', t)) and not re.search(r'\biz\s*s?\.?$|\bs\.$', t)
    return out


def spell(word: str) -> str:
    w = re.sub(r'(?<=[{L}])i[cč]$'.format(L=L), 'ić', word)
    c = ofz._spell['last'].get(w.upper().translate(ofz.FOLD), {})
    fits = [s for s, n in sorted(c.items(), key=lambda x: -x[1]) if n >= 3 and len(s) == len(w)
            and all(a == b or (a != 'Đ' and b in ofz.LOST.get(a, '')) for a, b in zip(w.upper(), s))]
    return kl.title(fits[0]) if fits else w


def parse_entry(text: str) -> dict:
    m = re.match(r'^§(\d)§\s*(.*)$', text, re.S)
    title, t = SECTIONS[int(m.group(1))][1], re.sub(r'\s+', ' ', m.group(2)).strip()
    t = re.sub(r'(?<=[a-zčćžšđ])[-\xad]\s(?=[a-zčćžšđ])', '', t).replace('>', '').replace('iz. ', 'iz ').rstrip(',.')
    head, _, rest = t.partition(',')
    words = head.split()
    last, given = spell(words[0]), words[1] if len(words) > 1 else ''
    nick = ' '.join(words[2:])
    if f'{words[0]} {given}' in NOT_WORKERS or f'{last} {given}' in NOT_WORKERS:
        return {'last_name': ''}                                       # dropped by the scaffold
    info = f"{title}: {('zvani ' + nick + '; ') if nick else ''}{rest.strip()}".rstrip(': ')
    rec = _record(last, given, '', info)
    d = re.search(r'\b(poginu\w+|umr\w+)\s+u toku rata', rest)
    if d:
        rec['death_type'] = 'poginuo' if d.group(1).startswith('poginu') else 'umro'
    home = re.search(r'\biz\s+(?:s\.\s*)?([^,]+)', rest)
    if home:
        rec['_from'] = home.group(1).strip()
    return rec


def post(soldiers: list[dict]) -> list[dict]:
    for s in soldiers:
        s.pop('_from', None)
    return soldiers


if __name__ == '__main__':
    build_pdf()
    ofz.corpus()
    run_parser(
        pdf_path=str(PDF),
        brigade_code=112,
        output_path=str(OUTPUT),
        extract_fn=extract,
        entry_start_re=re.compile(r'^§\d§'),
        parse_entry_fn=parse_entry,
        post_fn=post,
        id_start=10001,
        keep_other_sources=True,
    )
