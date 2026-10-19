"""
Požega u NOR i revoluciji 1941-1945 (Jovan R. Radovanović; znaci.org 00003/696), the appendix by Dragoljub Munjić,
"Spisak palih boraca NOR-a, žrtava fašističkog terora i civilnih žrtava rata 1941-1945. godine u srezu požeškom"
(696_1.pdf → website/public/pdfs/pozega-pali.pdf): a book across units, its fighters added to the records of the
soldiers it describes (see scripts/match_references.py).

The list names the dead of the Požega municipality by village: the fallen fighters of the NOV and POJ (also those from
elsewhere who joined the rising there, and those of the NOVJ's units who fell freeing it in late 1944), sympathisers of
the NOP killed or dead in prisons and camps, and the old Yugoslav army's dead. Only the fighters are read, as in
parse_cacanski_kraj.py: an entry that names a partisan unit or calls the man a "borac", a commander, commissar, courier
or medic; never one of the Chetnik side or of the old army ("vojnik bivše jugoslovenske vojske", "u aprilskom ratu"),
nor a civilian or sympathiser without a fighter's word. The author's notes after some villages ("NAPOMENA: ...")
are not read.
Cyrillic, one column, each entry's first line indented:
    SRETIĆ Marinka MILUN, rođen u Gornjoj Dobrinji, 1919. godine, zemljoradnik, borac 9. brigade 23 divizije,
    poginuo u borbi protiv Nemaca, kod Ljubovije, 19. decembra 1944.
The Užički odred (whose Požega companies these men of 1941 were) gives the entry unit 26, the Serbian brigades on the
site their units.

Output: data-extraction/znaci/pozega-pali-entries.json (IDs 9017xxxxxx, in the book's order).

Usage: python data-extraction/parse_pozega_pali.py [--sample N]
"""
from __future__ import annotations

import json
import random
import re
import shutil
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / 'scripts'))
import entry_boxes  # noqa: E402
from _parser_scaffold import cyrillic_to_latin, extract_lines_single_column  # noqa: E402
from extract_life_events import iso, parse_when  # noqa: E402
from parse_cacanski_kraj import CAPS, CHETNIK, FIGHTER, L, U, join, name_of  # noqa: E402
from parse_cacanski_kraj import kind as ck_kind  # noqa: E402
from parse_cacanski_odred import fix_digits  # noqa: E402

PDF = 'pozega-pali.pdf'
PDF_PATH = HERE.parent / 'website' / 'public' / 'pdfs' / PDF
SOURCE = HERE / '.cache' / 'pozega' / '696_1.pdf'                   # znaci.org/00003/696_1.pdf
OUT = HERE / 'znaci' / 'pozega-pali-entries.json'
PREFIX = '9017'
OLD_ARMY = re.compile(r'bivše jugoslovensk\w* vojsk|aprilsk\w* rat|kraljevsk\w* vojsk|\bVKJ\b|\bBJV\b', re.I)
# the Serbian brigades on the site, by number (the book: "borac 14. brigade 23. divizije")
SERBIAN = {4: 21, 5: 127, 7: 85, 8: 87, 10: 88, 12: 90, 14: 27, 15: 86, 17: 55, 18: 128, 19: 73, 20: 91, 21: 80,
           22: 74, 23: 89, 25: 31}


def units_of(info: str) -> list[int]:
    out = set()
    if re.search(r'Užičk\w* (?:NOP |partizansk\w* )?odred|Požešk\w* (?:partizansk\w* )?čet', info, re.I):
        out.add(26)
    if re.search(r'Drug\w* proletersk\w* brigad', info):
        out.add(39)
    for m in re.finditer(r'\b(\d{1,2})\.\s*(srpsk\w*\s+)?brigad\w*(?:\s+(2[1-5])\.?\s*divizij)?', info):
        if (m.group(2) or m.group(3)) and int(m.group(1)) in SERBIAN:
            out.add(SERBIAN[int(m.group(1))])
    return sorted(out)


def read() -> list[dict]:
    lines = extract_lines_single_column(str(PDF_PATH), 3, None)
    left: dict = {}
    for ln in lines:
        ln['text'] = fix_digits(cyrillic_to_latin(ln['text'].strip()))
        if re.search(rf'[{L}]', ln['text']):
            left[ln['page']] = min(left.get(ln['page'], 10 ** 6), ln['x'])
    entries, village, note = [], '', False
    for ln in lines:
        t, page = ln['text'], ln['page']
        if re.fullmatch(r'[\d\W]{1,5}', t):
            continue                                                   # the page number
        if not re.search(rf'[{L}\d,;]', t):
            village, note = t, False                                   # a village heading
            continue
        if re.match(r'^NAPOMENA', t):
            note = True                                                # the author's note, to the next entry
            continue
        indent = ln['x'] > left.get(page, 0) + 15
        if indent and re.match(rf'^{CAPS}\s', t):
            note = False
            entries.append({'lines': [t], 'pdf_page': page, 'pdf_x': ln['x'], 'pdf_y': ln['y'], 'village': village})
        elif entries and not note:
            entries[-1]['lines'].append(t)
    return entries


def parse(e: dict, n: int) -> dict:
    last_name, father, first_name, nick, info = name_of(join(e['lines']))
    info = re.sub(r'\bro[đćdcnN]e{1,2}n(a?)\b', r'rođen\1', info.strip())
    rec = {'soldier_id': f'{PREFIX}{n:06d}',
           'name': ' '.join(x for x in (last_name, father, first_name) if x) + (f' — {nick}' if nick else ''),
           'last_name': last_name, 'first_name': first_name, 'nick': nick, 'fathers_name': father}
    # "rođen u Gornjoj Dobrinji, 1919. godine" or "rođen u selu Čubri kod Ražnja, 1914. godine"
    b = re.search(rf'\brođen[a]?\s+u\s+(?:selu\s+)?([{U}][{L}]+(?:\s+[{U}]?[{L}]+){{0,2}})', info)
    rec['born_in'] = b.group(1) if b else ''
    y = re.search(r'\brođen[a]?\b[^;]{0,60}?\b(1[89]\d\d)\.?\s*godin', info) or re.search(r'\brođen[a]?\b[^;]{0,60}?\b(1[89]\d\d)\b', info)
    rec['birth_year'] = y.group(1) if y else ''
    years = re.findall(r'\b(19[34]\d)\b', info[y.end() if y else 0:])
    rec['death_year'] = years[-1] if years else ''
    when = re.search(rf'\b\d{{1,2}}\.\s*(?:[{L}]+|\d{{1,2}}\.)\s*19[34]\d', info[y.end() if y else 0:])
    parsed = parse_when(when.group(0)) if when else None
    rec['death_date'] = iso(parsed[0]) if parsed and parsed[0][2] else ''
    rec['units'] = units_of(info)
    rec['village'] = e['village'].title()
    rec['additional_info'] = info
    rec.update(pdf_file=PDF, pdf_page=e['pdf_page'], pdf_x=round(e['pdf_x'], 1), pdf_y=round(e['pdf_y'], 1))
    return rec


def fighter(rec: dict) -> bool:
    info = rec['additional_info']
    return bool(FIGHTER.search(info)) and not CHETNIK.search(info) and not OLD_ARMY.search(info)


def main():
    if not PDF_PATH.exists():
        shutil.copy(SOURCE, PDF_PATH)
    raw = read()
    recs = [parse(e, i) for i, e in enumerate(raw, 1)]
    for r in recs:
        # the book sets a narodni heroj's biography after his village's list: one of another man ("Rođen je 12.
        # oktobra 1917. godine, u Otnju" after Trnavac Jevto, born 1905) is not this entry's
        m = re.search(r'\.\s+Rođen[a]? je\b', r['additional_info'])
        if m:
            year = re.search(r'\b(1[89]\d\d)\b', r['additional_info'][m.end():m.end() + 80])
            own = re.search(r'\b(1[89]\d\d)\b', r['additional_info'][:m.start()])
            if year and own and year.group(1) != own.group(1):
                r['additional_info'] = r['additional_info'][:m.start() + 1]
    # the activists in too, marked, and the fighters by the rule of the mixed lists (the user's decision of
    # 2026-10-19; parse_cacanski_kraj.kind): the old army's men count by what they did in this war
    kinds = {r['soldier_id']: ck_kind(r) for r in recs}
    for r in recs:
        if kinds[r['soldier_id']] == 'activist':
            r['role'] = 'activist'
    kept = [r for r in recs if kinds[r['soldier_id']]]
    print(f"by the old rule {sum(fighter(r) for r in recs)}; now {sum(v == 'fighter' for v in kinds.values())} fighters, "
          f"{sum(v == 'activist' for v in kinds.values())} activists")
    stats = entry_boxes.fill_boxes(kept)
    OUT.write_text(json.dumps(kept, ensure_ascii=False, indent=1), encoding='utf-8')
    print(f'{len(recs)} entries read, {len(kept)} fighters -> {OUT.relative_to(HERE.parent)}; '
          f'units {sum(1 for r in kept if r["units"])}, birth year {sum(1 for r in kept if r["birth_year"])}')
    print(f"boxes: {entry_boxes.describe(stats, stats['boxed'])}")
    if '--sample' in sys.argv:
        random.seed(2)
        for r in random.sample(kept, int(sys.argv[sys.argv.index('--sample') + 1])):
            print(f"  {r['name']!r} [{r['born_in']}] {r['birth_year']} d{r['death_year']} {r['death_date']} | {r['units']}")
            print(f"      {r['additional_info'][:150]}")
        print('-- left out:')
        for r in random.sample([r for r in recs if not fighter(r)], 6):
            print(f"  {r['name']!r}: {r['additional_info'][:140]}")


if __name__ == '__main__':
    main()
