"""
Otočac i Brinje u NOB 1941-1945 (Poreklo library): the book's "Popis palih boraca, žrtava fašističkog terora i
preživjelih boraca i aktivnih učesnika u NOB", compiled by the local SUBNOR boards of the Otočac općina, as a book
across units. Two columns, village by village (a heading in capitals: OTOČAC, BRINJE, LIČKO LESCE, ŠVICA, ...), an
entry each, flush: "Marković Ivana Mijo, rođen 1906. u Otočcu, stupio u NOB-u 1941, poginuo 1943. u Crnoj Gori,
proglašen za narodnog heroja."

    "Pali borci" (scan pp. 415-437, book pp. 411-433): every entry goes in;
    "Preživjeli borci i aktivni učesnici NOP" (pp. 465-535, book pp. 461-531): the fighters and the activists of the
        movement together, and both go in: the user decided on 2026-10-19, against the rule of the other mixed lists,
        that this list's activists (the NOO's, SKOJ's and AFŽ's people, field and political workers, "stupio u NOP
        1943") are added too. They lived through the war (`survived`).
The list between them, "Žrtve fašističkog terora" (pp. 439-462), is of civilians and stays out (its pages after 440
were not fetched).

The name is the surname, the father in the genitive and the given name ("Trtica Ilije Anka"), a heading of the
fallen given name first where the book sets a hero's title ("Uzelac Steve Srđan, Narodni heroj"); carons the OCR
lost come back from the site's names (`_karlovac_lists.spelled`).

Output: data-extraction/poreklo/otocac-brinje-entries.json (IDs 9064xxxxxx: the fallen from 000001, the survivors
from 010001, each in the list's order).
Usage: python data-extraction/parse_otocac_brinje.py [--sample N]
"""
from __future__ import annotations

import json
import random
import re
import sys
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / 'scripts'))
import _karlovac_lists as kl  # noqa: E402
import parse_ofanziva_1942 as ofz  # noqa: E402
from parse_mosorski_odred_2 import fighter, fighter_or_officer  # noqa: E402
from parse_ostrvica import death_of  # noqa: E402
from parse_vrebac import columns  # noqa: E402
from poreklo_text import load, viewer_url  # noqa: E402

BOOK = 'otocac-brinje.json'
OUT = HERE / 'poreklo' / 'otocac-brinje-entries.json'
PREFIX = '9064'
OFFSET = 4                                  # scan page minus the book's page (the contents: "Pali borci 411")
TITLE = 'Otočac i Brinje u NOB 1941-1945'
LISTS = [(range(415, 438), 'fallen', 'Pali borci', 0),
         (range(465, 536), 'alive', 'Preživjeli borci i aktivni učesnici NOP', 10000)]
U, L = 'A-ZČĆŽŠĐ', 'a-zčćžšđ'
NAME = rf'[{U}][{L}]+(?:-[{U}][{L}]+)?'
# an entry's first line: the surname, father and given name and a comma; two words (no father) only after a line that
# ended a sentence; never a line of the text that starts so ("Narodni heroj, sekretar ...")
# (a married woman's maiden name after "r.": "Jakšić r. Begović Jose Marija")
START = re.compile(rf'^({NAME})\.?(?:\s+(?:r\.|udata)\s+{NAME})?\s+({NAME})(?:\s+([{U}l]?[{L}]+(?:-[{U}][{L}]+)?))?\s*,')
# the fallen of the last villages (Krišpolje-Kamenica, Prozor, Lipice-Glibodol), names alone, a line each, the
# father's initial between ("Borić I. Ivan", "Ljuština Mišo")
NAME_ONLY = re.compile(rf'^({NAME})\s+(?:([{U}ЈІ\[])\.\s+)?([{U}][{L}\-]+)\.?$')
# where he was born, in the locative the entries print it ("rođen 1909. u Vojduši", "u D. B. Potoku")
BORN = re.compile(rf'\brođen[a]?\s+(?:\d{{1,2}}\.\s*\d{{1,2}}\.\s*)?1[89]\d\d\.?,?\s+(?:godine,?\s+)?u\s+'
                  rf'((?:[{U}][{L}]*\.?\s*){{1,3}}?)(?=[,.;]|\s+[{L}])')
NOT_NAMES = {'Narodni', 'Crnoj', 'Gorskom', 'Gornji', 'Donji', 'Staro', 'Ličko', 'Babin', 'Srpsko', 'Drenov'}
# an officer whose entry gives only his rank in the army ("stupio u NOB 1942. godine, kapetan u NOV", "pukovnik",
# "ekonom, kapetan u NOV"): the mixed-list rule names duties, not ranks, so these are read here, as the Sanski Most
# book's are (parse_sanski_most.MILITARY); "u NOV" is the army itself ("lekar u NOV")
MILITARY = re.compile(r'\b(?:pot?poručnik\w*|poručnik\w*|kapetan\w*|major\w*|potpukovnik\w*|pukovnik\w*|zastavnik\w*|'
                      r'general\w*|podoficir\w*)\b|\bu\s+NOV\b')
# the lists' titles and the verse on the first page of the fallen ("Nek se znade da sam borac bio / Za slobodu život
# položio"), set apart from the columns
DROP = re.compile(r'^(?:Pali|borci|Nek se znade|Za slobodu|Preživjeli|i aktivni|učesnici NOP|Žrtve)\b')


def heading(t: str) -> str:
    words = t.split()
    if len(words) > 2 and all(len(w) <= 2 for w in words):
        t = ''.join(words)                                          # "Z A L U 2 N I C A"
    t = t.replace('2', 'Ž')
    # not an entry's last line in capitals, an organisation ("NOV.", "MNOO.", "u NOV.")
    if t.endswith('.') or re.fullmatch(r'(?:U\s+)?(?:NOV|NOB|NOO|MNOO|KNOO|NOF|KPJ|SKOJ|AFŽ|AFZ|NOP|KNOJ)\.?', t):
        return ''
    return t if re.fullmatch(rf'[{U}][{U} ,\-]+', t) and len(t) > 3 else ''


def raw_entries(book: dict) -> list[dict]:
    out = []
    for pages, kind, title, base in LISTS:
        village, ended, n, names_only = '', True, 0, False
        for page in pages:
            for l in columns(book, page):
                t = re.sub(r"^[•·■*^_'’`\"]+\s*", '', l.text.strip())
                if re.fullmatch(r'\d{1,3}\.?', t) or DROP.match(t):
                    continue
                h = heading(t)
                if h:
                    village, ended = h, True
                    continue
                m = START.match(t)
                starts = bool(m) and m.group(1) not in NOT_NAMES and (m.group(3) or ended)
                only = NAME_ONLY.match(t) if kind == 'fallen' and not m else None
                if only and only.group(1) not in NOT_NAMES and (only.group(2) or names_only):
                    names_only = True
                    n += 1
                    out.append({'kind': kind, 'list': title, 'no': base + n, 'village': village, 'page': page,
                                'lines': [t.rstrip('.')], 'names_only': True})
                    ended = True
                    continue
                was_ended, ended = ended, bool(re.search(r'[.;]\s*$', t))
                if starts:
                    n += 1
                    out.append({'kind': kind, 'list': title, 'no': base + n, 'village': village, 'page': page,
                                'lines': [t]})
                elif out and out[-1]['kind'] == kind:
                    out[-1]['lines'].append(t)
    return out


def join(lines: list[str]) -> str:
    text = ''
    for ln in lines:
        if re.search(r'[—–-]$', text) and re.match(rf'[{L}]', ln):
            text = re.sub(r'[—–-]$', '', text) + ln
        else:
            text += (' ' if text else '') + ln
    return re.sub(r'\s+', ' ', text).strip()


def village_name(v: str) -> str:
    v = v.replace(',ZUTA', ', ŽUTA')                                 # "DOBRICA,ZUTA LOKVA"
    return ' '.join(w if w in ('I',) and 0 < i else kl.title(w) for i, w in enumerate(v.split())).replace(' I ', ' i ')


def main():
    ofz.corpus()
    book = load(BOOK)
    entries, counts = [], Counter()
    for e in raw_entries(book):
        text = join(e['lines'])
        head, _, rest = text.partition(',')
        maiden = re.search(rf'\s+(?:r\.|udata)\s+({NAME})', head)
        also = [kl.spelled(maiden.group(1), 'last')] if maiden else []
        words = re.sub(rf'\s+(?:r\.|udata)\s+{NAME}', '', head).split()
        last = kl.spelled(words[0], 'last')
        father = words[1] if len(words) >= 3 and not re.fullmatch(r'\S\.', words[1]) else ''
        initial = words[1] if len(words) >= 3 and re.fullmatch(r'\S\.', words[1]) else ''
        first = kl.spelled(words[-1][:1].upper() + words[-1][1:], 'first')           # "lgnjatija", "anatija"
        if e.get('names_only'):
            # a name alone: the book prints no more, so the entry says which list and village it stands under
            text = f"{last} {initial + ' ' if initial else ''}{first}"
        village = village_name(e['village'])
        info = text
        # in too, by the user's decision of 2026-10-19, and marked as such (`role`), so the site can tell them apart
        activist = (e['kind'] == 'alive' and not fighter({'additional_info': info}) and not MILITARY.search(rest)
                    and not fighter_or_officer({'additional_info': rest}))      # a rank, a unit, "u partizane"
        counts['activists'] += activist
        y = re.search(r'\brođen[a]?\s+(?:\d{1,2}\.\s*\d{1,2}\.\s*)?(1[89]\d\d)', rest)
        death = death_of(info) if e['kind'] == 'fallen' else {}
        born = BORN.search(text)
        rec = {
            'soldier_id': f"{PREFIX}{e['no']:06d}",
            'name': f"{last} {(father or initial) + ' ' if father or initial else ''}{first}",
            'last_name': last, 'first_name': first, 'nick': '', 'fathers_name': father,
            'birth_year': y.group(1) if y else '', 'also': also,
            # the village the entry names, then the heading it stands under (a village, or the Gornji Kraj of Brinje)
            'born_in': ', '.join(x for x in ((born.group(1).strip() if born else ''), village) if x),
            'death_year': death.get('year', ''),
            **({'death_date': death['date']} if death.get('date') else {}),
            **({'death_place': death['place']} if death.get('place') else {}),
            'survived': e['kind'] == 'alive',
            **({'role': 'activist'} if activist else {}),
            'additional_info': f"{e['list']}, {village}: {info}",
            'list': e['list'], 'book_title': TITLE,
            'source_url': viewer_url(book, e['page']), 'source_page': e['page'] - OFFSET,
        }
        entries.append(rec)
        counts[e['kind']] += 1
    OUT.write_text(json.dumps(entries, ensure_ascii=False, indent=1), encoding='utf-8')
    print(dict(counts), '->', OUT.name, len(entries))
    print(Counter(r['born_in'] for r in entries).most_common())
    if '--sample' in sys.argv:
        random.seed(4)
        for r in random.sample(entries, min(int(sys.argv[sys.argv.index('--sample') + 1]), len(entries))):
            print(f"  {r['name']} | {r['birth_year']} [{r['born_in']}] † {r['death_year']} {r.get('death_place', '')!r} "
                  f"surv={r['survived']} | {r['additional_info'][:110]}")


if __name__ == '__main__':
    main()
