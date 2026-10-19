"""
Staromajdansko područje u NOB 1941-1945. godine (Poreklo library): "Poginuli borci i učesnici NOR-a i žrtve fašističkog
terora; umrli borci i učesnici NOR-a ...; živi borci i učesnici NOR-a ... i nosioci Partizanske spomenice 1941.", the
Stari Majdan area of the Sanski Most municipality village by village, as a book across units.

Under each village (a heading in spaced capitals, "D E M 1 S Е V C 1") stand "Borci poginuli u NOR-u:" and "Žrtve
fašističkog terora:"; only the first go in, an entry a paragraph, the first line indented: "DAMJANOVIĆ Maksima
DRAGAN, rođen 1922. godine, stupio u NOB početkom 1942. godine, poginuo novembra 1943. godine kod Bihaća;". Only the
book's scan pp. 177-216 were fetched (2026-10-19): the fallen of the villages from Ališići to Podlug; the villages
after them, and the lists of the dead and living fighters and the spomenica's holders, are not read yet (their
entries will take the numbers after these).

The names are read as the Sanski Most book's (`parse_sanski_most.parse`, the same area and the same kind of list):
the surname and the given name in capitals, the father between, carons the OCR lost read back from the site's names.

Output: data-extraction/poreklo/staromajdansko-entries.json (IDs 9063xxxxxx in the list's order).
Usage: python data-extraction/parse_staromajdansko.py [--sample N]
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
import parse_ofanziva_1942 as ofz  # noqa: E402
import parse_sanski_most as sm  # noqa: E402
from parse_ostrvica import death_of, level_lines  # noqa: E402
from poreklo_text import load, page_words, viewer_url  # noqa: E402

BOOK = 'staromajdansko.json'
OUT = HERE / 'poreklo' / 'staromajdansko-entries.json'
PREFIX = '9063'
PAGES = range(177, 217)
OFFSET = 0                                  # the scan's pages are the book's
TITLE = 'Staromajdansko područje u NOB 1941-1945. godine'
LIST = 'Borci poginuli u NOR-u'
# the two headings as the OCR gives them: "Borci", "Ват!", "Banci poginuli u NOR-u:", "Poginuli borci u NOR-u:";
# "Žrtve", "Žnve", "Žn've fašističkog terora:"
FALLEN = re.compile(r'^(?:\S+\s+poginul\w*|Poginul\w*\s+borc\w*)\s+\S+\s+NOR', re.I)
VICTIMS = re.compile(r'^Ž\S*\s+fa[sš]', re.I)
# the headings' carons the OCR lost, and "OŠTRALUKA" printed as one word
VILLAGE_FIX = {'Alisici': 'Ališići', 'Demisevci': 'Demiševci', 'Pobrijezje': 'Pobriježje', 'Oštraluka': 'Oštra Luka',
               'Podvidaca': 'Podvidača'}
# Cyrillic letters the OCR set in a Latin name, as the Latin they look like ("Реге" Pere)
LOOKALIKE = str.maketrans('АВЕКМНОРСТХаеорсухнвтгмкиЈј', 'ABEKMHOPCTXaeopcyxhbtrmkuJj')


def heading(t: str) -> str:
    """a village's heading, its letters spaced and read with 1 for I and 0 for O ("A L 1 S 1 C 1" = ALIŠIĆI is printed
    so, the caron lost); else ''"""
    t = t.translate(LOOKALIKE).strip()
    words = t.split()
    if len(words) > 2 and all(len(w) <= 2 for w in words):
        t = ''.join(words)
    t = t.replace('1', 'I').replace('0', 'O')
    return t if sm.is_village(t) and not re.search(r'TEROR|NOR|POGIN', t) else ''


def raw_entries(book: dict) -> list[dict]:
    out, village, kind, ended = [], '', '', True
    for page in PAGES:
        for l in level_lines(page_words(book, page)):
            t = re.sub(r"^[•·■*^_'’`]+\s*", '', l.text.strip())
            t = re.sub(r"^'I'", 'T', t)                                   # "'I'RKULJA" = TRKULJA
            if re.fullmatch(r'\d{1,3}', t) or re.search(r'Staro\w*\s+područje u NOB \d+$', t):
                continue
            h = heading(t)
            if h and not re.search(r',', t):
                village, kind, ended = h, '', True
                continue
            if FALLEN.match(t):
                kind, ended = 'fallen', True
                continue
            if VICTIMS.match(t):
                kind, ended = 'victims', True
                continue
            was_ended, ended = ended, bool(re.search(r'[;.:]\s*$', t))
            if kind != 'fallen':
                continue
            if sm.START.match(t) and re.match(r'^[^,]{3,70},', t) and was_ended:
                out.append({'kind': 'fallen', 'list': LIST, 'village': village, 'lines': [t], 'page': page,
                            'pdf_page': page, 'pdf_x': 0, 'pdf_y': 0})
            elif out and out[-1]['page'] in (page, page - 1):
                out[-1]['lines'].append(t)
    return out


def main():
    ofz.corpus()
    book = load(BOOK)
    entries = []
    for i, e in enumerate(raw_entries(book), 1):
        e['lines'] = [ln.translate(LOOKALIKE) if re.search('[А-Яа-я]', ln) else ln for ln in e['lines']]
        r = sm.parse(e, i)
        for k in ('pdf_file', 'pdf_page', 'pdf_x', 'pdf_y', 'kind'):
            r.pop(k, None)
        village = VILLAGE_FIX.get(sm.village_name(e['village']), sm.village_name(e['village']))
        info = r['additional_info'].split(': ', 1)[1] if ': ' in r['additional_info'] else r['additional_info']
        death = death_of(info)
        r.update({
            'soldier_id': f'{PREFIX}{i:06d}',
            'born_in': f'{village}, Sanski Most',
            'additional_info': f'{LIST}, {village}: {info}',
            'death_year': death.get('year') or r.get('death_year', ''),
            **({'death_date': death['date']} if death.get('date') else {}),
            'survived': False,
            'list': LIST, 'book_title': TITLE,
            'source_url': viewer_url(book, e['page']), 'source_page': e['page'] - OFFSET,
        })
        if not r.get('death_place') and death.get('place'):
            r['death_place'] = death['place']
        entries.append(r)
    OUT.write_text(json.dumps(entries, ensure_ascii=False, indent=1), encoding='utf-8')
    print(len(entries), 'fighters ->', OUT.name, Counter(r['born_in'] for r in entries).most_common())
    if '--sample' in sys.argv:
        random.seed(2)
        for r in random.sample(entries, min(int(sys.argv[sys.argv.index('--sample') + 1]), len(entries))):
            print(f"  {r['last_name']}|{r['fathers_name']}|{r['first_name']} {r['birth_year']} [{r['born_in']}] "
                  f"† {r['death_year']} {r.get('death_place', '')!r} | {r['additional_info'][:110]}")


if __name__ == '__main__':
    main()
