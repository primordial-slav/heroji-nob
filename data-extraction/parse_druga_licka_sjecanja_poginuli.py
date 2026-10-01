"""
Parser: Druga lička proleterska brigada (brigade code 3) — the fallen, from the memoir book.

Source: "DRUGA LIČKA PROLETERSKA BRIGADA — Sjećanja", chapter "Spisak poginulih, umrlih i nestalih boraca Druge
        ličke proleterske brigade" (author of the lists: Đuro Mileusnić)
        znaci.org  →  website/public/pdfs/druga-licka-sjecanja-poginuli.pdf
The same author and layout as the book's list of survivors (parse_druga_licka_prezivjeli.py, whose reader this
uses): two columns, Latin, entries separated by a blank line, the father in caps like the name.
    AJDUKOVIĆ SIME DANE rođen 1915. u s. Oraovac - D. Lapac. Komandir voda u 2. četi 1. bataljona. Poginuo ...

Most of these men are also on the Military History Institute's list of the fallen (druga-licka-spisak.pdf): merge
corrections make each one record with both entries (scripts/find_source_duplicates.py). These records get IDs from
0003020001 and a re-run replaces only them.
"""
import re

from _parser_scaffold import run_parser
from parse_druga_licka_prezivjeli import keep_line, parse_entry, post

U = 'A-ZČĆŽŠĐ'
# entry starts the reader would miss: a double surname printed "HINIĆ - BATINIĆ", a nickname between surname and
# name, a name broken into pieces
LINE_FIXES = [
    (re.compile(rf'^([{U}]{{3,}}) - ([{U}1]{{3,}}) '), r'\1-\2 '),
    (re.compile(r'^UZELAC zvana KONCAR JELA '), 'UZELAC JELA zvana Končar, '),
    (re.compile(r'^J ELISA VĆIČ MIO DRAG '), 'JELISAVČIĆ MIODRAG '),
]
NAME_FIXES = {'B-Uqisavltević': 'Budisavljević', 'CiTAKOVIĆ': 'Čitaković', 'Hand2a': 'Handža', 'SiRANOVIĆ': 'Širanović',
              'Vul0vić': 'Vulović', 'Nikosavuević': 'Nikosavljević'}
# fathers' names the OCR misread: LJ as U, LI as U, Č and Đ without their marks
FATHER_FIXES = {'Uubomira': 'Ljubomira', 'Utjbomira': 'Ljubomira', 'Bogouuba': 'Bogoljuba', 'Miuvoja': 'Milivoja',
                'Veumira': 'Velimira', 'Velimire': 'Velimira', 'Illje': 'Ilije', 'Živoina': 'Živojina',
                'Cedomira': 'Čedomira', 'Dorđa': 'Đorđa', 'Dorđija': 'Đorđija', 'Pilipa': 'Filipa', 'Laže': 'Laze'}


def fix_line(ln: dict) -> bool:
    t = ln['text'].strip()
    for rx, rep in LINE_FIXES:
        t = rx.sub(rep, t)
    head = re.match(rf'^[{U}1\- ]+(?=\s)', t)                       # "VUKOBRATOVIĆ M1ĆANA BUDE": 1 for I in the name
    if head:
        t = re.sub(rf'(?<=[{U}])1|1(?=[{U}])', 'I', head.group(0)) + t[head.end():]
    ln['text'] = t
    return keep_line(ln)


def post_fix(soldiers: list[dict]) -> list[dict]:
    soldiers = post(soldiers)
    for s in soldiers:
        s['last_name'] = NAME_FIXES.get(s['last_name'], s['last_name'])
        if s.get('middle_name') in FATHER_FIXES:
            s['middle_name'] = s['fathers_name'] = FATHER_FIXES[s['middle_name']]
        s['full_name'] = ' '.join(x for x in (s['last_name'], s.get('middle_name') or '', s['first_name']) if x)
    return soldiers


if __name__ == '__main__':
    run_parser(
        pdf_path='website/public/pdfs/druga-licka-sjecanja-poginuli.pdf',
        brigade_code=3,
        output_path='website/public/druga-licka-soldiers.json',
        start_page=2,
        end_page=133,
        layout='two_column',
        col_split_x='auto',
        script='latin',
        parse_entry_fn=parse_entry,
        line_filter=fix_line,
        post_fn=post_fix,
        id_start=20001,
        keep_other_sources=True,
    )
