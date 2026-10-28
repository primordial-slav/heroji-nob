"""
*Rogatica* (monografija; doc 00001755 of the Poreklo library), a book across units: "Istaknuti prvoborci Narodno-
oslobodilačkog rata" (book pp. 235-254, scan 237-252), the notable first fighters of the Rogatica area, a bio each
under a heading "BIJELJANIN (Jeliseja), Miloš" (the surname in capitals, the father in the genitive, the given name,
a nickname after it): born, SKOJ and KPJ, joined the NOB, the units, the death or the life after the war. Fighters
and, by the mixed lists' rule (`_village_books.role`), the movement's other people as activists.

Output: data-extraction/poreklo/rogatica-entries.json (IDs 9108xxxxxx, in the book's order).
Usage: python data-extraction/parse_rogatica.py
"""
from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import _village_books as V  # noqa: E402
from parse_ostrvica import level_lines  # noqa: E402
from poreklo_text import load, page_words, viewer_url  # noqa: E402

BOOK = 'rogatica.json'
OUT = HERE / 'poreklo' / 'rogatica-entries.json'
PREFIX = '9108'
OFFSET = 2                                  # scan page minus the book's page
TITLE = 'Istaknuti prvoborci Narodnooslobodilačkog rata'
BOOK_TITLE = 'Rogatica'
PAGES = range(237, 254)
HEAD = re.compile(r'^([A-ZČĆŽŠĐ\]]{3,}(?:[- ][A-ZČĆŽŠĐ]{3,})?)\s*(?:\(([^)]+)\))?,\s*(\S+)(?:\s+(.+))?$')
# the OCR's slips in the headings: ] and I for J, D for Đ
FIX = {'AKŠAMIIA': 'AKŠAMIJA', 'IOVIČIĆ': 'JOVIČIĆ', 'Dorđa': 'Đorđa', 'MAKANIIĆ': 'MAKANJIĆ'}


def main():
    V.corpus()
    book = load(BOOK)
    entries, cur = [], None
    for page in PAGES:
        for l in level_lines(page_words(book, page)):
            t = l.text.strip()
            if re.fullmatch(r'\d{3}', t):
                continue
            t2 = t.replace(']', 'J').replace('КРЈ', 'KPJ').replace('KP]', 'KPJ')      # (Cyrillic look-alikes)
            for a, b in FIX.items():
                t2 = re.sub(rf'(?<!\w){a}(?!\w)', b, t2)
            m = HEAD.match(t2)
            if m:
                cur = {'head': m.groups(), 'page': page, 'lines': []}
                entries.append(cur)
            elif cur:
                cur['lines'].append(t2)
    out, roles = [], Counter()
    for no, e in enumerate(entries, 1):
        sur, fath, first, nick = e['head']
        last = '-'.join(p.capitalize() for p in re.split(r'[- ]', sur))
        fath = (fath or '').strip()
        bio = V.unhyphen(' '.join(e['lines']))
        role = V.role(bio)
        if role == 'out':
            role = None                 # the book titles them all its first fighters (Makanjić Veso, of the Seljanska četa)
        born = re.search(r'Rođen[a]? je\s+(?:\d{1,2}\.\s*\w+\s+)?(1[89]\d\d)', bio)
        d = dict(V.death(bio))
        fell = re.search(r'(?:poginu\w*|izgubio (?:je )?život|ubijen\w*|strijeljan\w*|umro od rana)[^.]{0,90}?(19[34]\d)'
                         r'|(19[34]\d)\.?[^.]{0,40}?(?:poginu|izgubio (?:je )?život|ubijen|strijeljan)', bio)
        if not d.get('year') and fell:
            d['year'] = fell.group(1) or fell.group(2)
        died_in_war = bool(fell) or bool(re.search(r'[Pp]oginu|izgubio (?:je )?život|[Uu]bijen|strijeljan|umro od rana|'
                                                   r'samoubistvo|\bUmr(?:o|la) je\b[^.]*\b194[1-5]', bio))
        if not d.get('year') and died_in_war:
            y = re.search(r'(?:samoubistvo|\bUmr(?:o|la) je\b)[^.]*\b(194[1-5])|(194[1-5])\.?\s*god\w*\.?\s*izvršio samoubistvo', bio)
            if y:
                d['year'] = y.group(1) or y.group(2)
        after = re.search(r'\bUmr(?:o|la) je\b[^.]*\b(19[5-9]\d|20\d\d)', bio)
        rec = {'soldier_id': f'{PREFIX}{no:06d}', 'name': ' '.join(x for x in (last, fath, first) if x),
               'last_name': last, 'also': [], 'first_name': first, 'nick': nick or '', 'fathers_name': fath,
               'birth_year': born.group(1) if born else '', 'born_in': V.born_in(bio, 'Rogatica'),
               'death_year': '' if after else d.get('year', ''),
               **({'death_date': d['date']} if d.get('date') and not after else {}),
               **({'death_place': d['place']} if d.get('place') and not after else {}),
               'survived': bool(after) or not died_in_war, 'units': V.units_of(bio), 'list': TITLE,
               'book_title': BOOK_TITLE, 'source_url': viewer_url(book, e['page']), 'source_page': e['page'] - OFFSET,
               'additional_info': f"{TITLE}: {sur}{f' ({fath})' if fath else ''}, {first}{' ' + nick if nick else ''}. {bio}"}
        if role:
            rec['role'] = role
        roles[role or 'fighter'] += 1
        out.append(rec)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding='utf-8')
    print(len(out), 'entries ->', OUT.name, dict(roles))
    for r in out:
        print(f"  {r['soldier_id']} {r['name']} | {r['birth_year']} {r['born_in']} | {r['death_year']} {r.get('death_place', '')} "
              f"surv={r['survived']} {r['units']} {r.get('role', '')}")


if __name__ == '__main__':
    main()
