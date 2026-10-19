"""
The Mosorski partizanski odred's part II, the people it holds who were no fighters, as a book across units: "Popis
boraca komandnih mjesta, partijsko-političkih i terenskih radnika na području Mosora" (Velić, Petrić, *Mosorski
partizanski odred*, znaci.org 00003/794, website/public/pdfs/mosorski-odred-2.pdf, book pp. 573-648).

parse_mosorski_odred_2.py gives unit 148 the fighters of the list (0148010001-, by parse_mosorski_odred_2.fighter).
The user decided on 2026-10-19 that the mixed lists' activists go in too, marked: here the party and field workers,
the NOO's and the AFŽ's people of the Mosor villages, the komande mjesta's men without a military duty, the rear
units' and pioneer companies' people. They are not the odred's, so they are entries of a book across units, matched
to the records of the units that print them and otherwise records of Ostali borci (122), each with `role: 'activist'`;
a man the wider rule of the books across units calls a fighter (a rank, a unit the entry puts him in, "u partizane":
parse_mosorski_odred_2.fighter_or_officer) has no role.

The part II reader runs into a scratch file (the unit's file is not touched), and its left-out records are taken in
the book's order (page, line).
Output: data-extraction/znaci/mosorski-odred-2-aktivisti-entries.json (IDs 9078xxxxxx).
Usage: python data-extraction/parse_mosorski_odred_2_aktivisti.py   (from the project root)
"""
from __future__ import annotations

import json
import re
import shutil
import sys
import tempfile
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / 'scripts'))
import entry_boxes  # noqa: E402
import parse_8_kordunaska_divizija as k8  # noqa: E402
import parse_mosorski_odred as m1  # noqa: E402
import parse_mosorski_odred_2 as m2  # noqa: E402
from _parser_scaffold import run_parser  # noqa: E402

OUT = HERE / 'znaci' / 'mosorski-odred-2-aktivisti-entries.json'
PREFIX = '9078'
TITLE = 'Mosorski partizanski odred, II dio: komande mjesta, partijsko-politički i terenski radnici Mosora'
UNIT_FILE = HERE.parent / 'website' / 'public' / 'mosorski-odred-soldiers.json'
DEATH = re.compile(r'\b(?:Poginu\w*|poginu\w*|Ubijen\w*|ubijen\w*|Umr\w*|umr\w*|Strijelj\w*|strijelj\w*|Ubil\w*|'
                   r'ubil\w*|Nesta\w*|nesta\w*)\b[^.]{0,80}?\b(19[34]\d)\b')


def dropped() -> list[dict]:
    """The records parse_mosorski_odred_2.post leaves out, read into a copy of the unit's file"""
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / UNIT_FILE.name
        shutil.copy(UNIT_FILE, out)
        k8.corpus()
        run_parser(
            pdf_path=str(m2.PDF.relative_to(HERE.parent)).replace('\\', '/'),
            brigade_code=148, output_path=str(out), start_page=1, end_page=None, layout='single', script='latin',
            entry_start_re=re.compile(r'^§x§'), parse_entry_fn=m1.parse, line_filter=m2.keep, post_fn=m2.post,
            id_start=10001, keep_other_sources=True)
    return sorted(m2.DROPPED, key=lambda s: (s['pdf_page'], s['pdf_y']))


def main() -> None:
    entries = []
    for i, s in enumerate(dropped(), 1):
        info = s['additional_info']
        death = DEATH.search(info)
        born = re.search(r'\brođen[a]?\s+(?:[\d.\s]*?)(1[89]\d\d)\.?\s*(?:godine\s*)?u\s+([^,.]+(?:,\s*[A-ZČĆŽŠĐ][^,.]+)?)', info)
        nick = re.match(r'zvan[ia]\s+([^;]+);\s*', info)
        rec = {'soldier_id': f'{PREFIX}{i:06d}',
               'name': ' '.join(x for x in (s['last_name'], s.get('middle_name', ''), s['first_name']) if x),
               'last_name': s['last_name'], 'first_name': s['first_name'], 'nick': nick.group(1) if nick else '',
               'fathers_name': s.get('middle_name', ''), 'birth_year': s.get('birth_year') or (born.group(1) if born else ''),
               'born_in': born.group(2).strip() if born else '',
               'death_year': death.group(1) if death else '', 'survived': not death,
               'additional_info': f'{TITLE}: {info}', 'list': TITLE, 'book_title': 'Mosorski partizanski odred',
               'pdf_file': s['pdf_file'], 'pdf_page': s['pdf_page'], 'pdf_x': s['pdf_x'], 'pdf_y': s['pdf_y']}
        if not m2.fighter_or_officer({'additional_info': info}):
            rec['role'] = 'activist'
        entries.append(rec)
    stats = entry_boxes.fill_boxes(entries)
    OUT.write_text(json.dumps(entries, ensure_ascii=False, indent=1), encoding='utf-8')
    print(f"{len(entries)} entries ({sum(bool(e.get('role')) for e in entries)} activists, "
          f"{sum(not e.get('role') for e in entries)} fighters by the wider rule) -> {OUT.relative_to(HERE.parent)}; "
          f"boxes: {entry_boxes.describe(stats, stats['boxed'])}")
    for e in entries:
        if not e.get('role'):
            print('  F ', e['name'], '|', e['additional_info'][len(TITLE) + 2:][:160])


if __name__ == '__main__':
    main()
