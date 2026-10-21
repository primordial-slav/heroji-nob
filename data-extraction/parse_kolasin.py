"""
Колашин (Poreklo library, doc 00001484): the people of the Kolašin area who fell in the war and the holders of the
Partizanska spomenica 1941, as a book across units. Cyrillic, a bio each, "АНЂЕЛИЋ Михаила ВОЈИН, рођен 1917.,
Мушовића Ријека, студент права. У НОП од 1941. Погинуо 1942. у Барама Краљским, командир чете у Липовско-
колашинско-речинском батаљону. Члан КПЈ од 1941."; the OCR sets a speck in the place of the font's Ђ and Ћ ("АН'БЕЛИ'Б")
and sets some names in Latin look-alikes ("AHTnEJIM'H"): names are read back as the site spells them (_village_books).
Lists:
  - "Погинули у НОР-у и Револуцији" (scan pp. 328-369): fighters, and the movement's people killed (a secretary or
    an odbornik of an NOO shot by the Chetniks), whom parse_mosorski_odred_2's rule marks `role: 'activist'`;
  - "Жртве фашизма и рата 1941-1945" (pp. 371-376): only the movement's people among them, by the same rule, and a
    fighter the book set there; the civilians stay out;
  - "Носиоци Партизанске споменице 1941" (pp. 377-388): those living at the end of the war, with the duty they then
    held; the activists marked as above, the rest counted as the other books' spomenica holders are.
Out: the wars of 1875-1918, Spain and the April war of 1941 (pp. 312-327), the tables of p. 370 and the authors' notes
(p. 389).

Output: data-extraction/poreklo/kolasin-entries.json, IDs 9090xxxxxx in each list's order: the fallen from 9090000001,
the victims from 9090010001, the spomenica's holders from 9090020001.
Usage: python data-extraction/parse_kolasin.py
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
from _parser_scaffold import cyrillic_to_latin as latin  # noqa: E402
from parse_ostrvica import level_lines  # noqa: E402
from poreklo_text import load, page_words, viewer_url  # noqa: E402

BOOK = 'kolasin.json'
OUT = HERE / 'poreklo' / 'kolasin-entries.json'
PREFIX = '9090'
TITLE = 'Kolašin'
OFFSET = -355                               # scan page minus the book's page (p. 329 is the book's 684)
MUNICIPALITY = 'Kolašin'
UC, LC = 'А-ЯЂЈЉЊЋЏ', 'а-яђјљњћџ'
LISTS = [('Poginuli u NOR-u i Revoluciji', range(328, 370), 'Погинули у', 0),
         ('Žrtve fašizma i rata 1941-1945', range(371, 377), 'Жртве фашизма', 10000),
         ('Nosioci Partizanske spomenice 1941', range(377, 389), 'Носиоци Партизанске', 20000)]
# surnames in Latin look-alikes or garbled past the reader, as the family's other entries print them
SURNAMES = {"AHTnEJIM'H": 'АНЂЕЛИЋ', "BAJITM'B": 'БАЛТИЋ'}
WORD = rf"[{UC}A-Z'][{UC}A-Z'’`nm]+"
HEAD = re.compile(rf"^({WORD}(?:\s*[—–-]\s*{WORD})?)\.?\s+([{UC}][{LC}]+)\s+"
                  rf"({WORD}(?:\s*[—–-]\s*{WORD})?|[{UC}][{LC}]+)(?:\s*,\s*удата\s+({WORD}))?\s*,\s*(.*)$")


def running_head(t: str) -> bool:
    return bool(re.search(r'Револуциј|споменице 1941|Жртве фашизма|фашизма u|HOP-', t)) and len(t.split()) <= 10 \
        and not re.search(r'рођен', t)


def read(book: dict, pages, start: str) -> list[dict]:
    raw, cur, started = [], None, False
    for page in pages:
        for l in level_lines(page_words(book, page)):
            t = l.text.strip()
            if not started:
                started = t.startswith(start)
                continue
            if running_head(t) or re.fullmatch(r'[\s\d.,_—–-]{1,12}', t) or t.startswith(('"\' дужности', '—')):
                continue
            m = HEAD.match(t)
            if m and re.match(rf"[{UC}A-Z]", t):
                cur = {'page': page, 'head': m.groups()[:4], 'parts': [m.group(5)]}
                raw.append(cur)
            elif cur:
                cur['parts'].append(t)
    return raw


# names as read -> as the book prints them, from the family's other entries and the village (Б and В, Ђ, Ћ and Н, Љ
# set as "jb", Л as "Ji", in Latin look-alikes); a few the scan garbled past reading stay as read ("Mmi-Ikb",
# "Jipjbebmh", "Jaelhmmb")
LAST_FIX = {'Vulatović': 'Bulatović', 'Annjelić': 'Anđelić', 'Anvelić': 'Anđelić', 'Lakinević': 'Lakićević',
            'Šnepanović': 'Šćepanović', 'Šbepanovitb': 'Šćepanović', 'Vaošić': 'Baošić', 'Vebirović': 'Bećirović',
            'Vraunović': 'Braunović', 'Bularović': 'Bulatović', 'Vidakovivd': 'Vidaković', 'Drjbević': 'Drljević',
            'Cejipib': 'Selić', 'Vošković': 'Bošković', 'Rrujić': 'Grujić', 'Jahkobmb': 'Janković', 'Jiakethb': 'Laketić',
            'Jiarmhebhh': 'Lakićević', 'Radovik': 'Radović'}
FIRST_FIX = {'Matije': 'Matija', 'Mjiabeh': 'Mlađen', 'Blazko': 'Blažo', 'Vejbko': 'Veljko', 'Njorbije': 'Đorđije',
             'Vogdan': 'Bogdan', 'Vojkidar': 'Božidar', 'Borvije': 'Đorđije', 'Kovijbka': 'Koviljka', 'Mmjira': 'Mira',
             'Ojiia': 'Olga', 'Dragšca': 'Dragiša', 'Pegar': 'Petar', 'Mihailojbago': 'Mihailo'}


def name(w: str) -> str:
    w = SURNAMES.get(w, w)
    return '-'.join(V.name_word(re.sub(r"['’`]", '', x)) for x in re.split(r'\s*[—–-]\s*', w))


def main():
    V.corpus()
    book = load(BOOK)
    entries, counts = [], Counter()
    for title, pages, start, base in LISTS:
        n = 0
        for r in read(book, pages, start):
            sur, fath, given, married = r['head']
            info = V.read_cyr(' '.join(r['parts']))
            role = V.role(info)
            if base == 10000 and role == 'out':
                counts['victims: out'] += 1
                continue
            last, also = name(sur), [name(married)] if married else []
            last = '-'.join(LAST_FIX.get(x, x) for x in last.split('-'))
            first, *more = [V.given_word(re.sub(r"['’`]", '', x)) for x in re.split(r'\s*[—–-]\s*', given)]
            first = FIRST_FIX.get(first, first)
            nick = more[0] if more else ''
            if base == 0 and role == 'out':
                # the list doesn't call its people fighters and the bio says only "U NOP od 1941": a participant (the
                # user's decision of 2026-10-20), unless it names him a member of CASNO, the council
                role = 'activist' if re.search(r'\b(?:CASNO|ZAVNO\w*|AVNOJ)\b', info) else 'participant'
            fath = V.father(fath)
            n += 1
            d = V.death(info) if base != 20000 else {}
            born = re.search(r'\brođen[a]?\s+(?:\d{1,2}\.\s*\w+\s+)?(1[89]\d\d)', info)
            printed = f'{last.upper()} {fath} {first.upper()}{"-" + nick.upper() if nick else ""}' \
                      f'{", udata " + also[0].upper() if also else ""}'
            e = {'soldier_id': f'{PREFIX}{base + n:06d}', 'name': ' '.join(x for x in (last, fath, first) if x),
                 'last_name': last, 'also': also, 'first_name': first, 'nick': nick, 'fathers_name': fath,
                 'birth_year': born.group(1) if born else '', 'born_in': V.born_in(info, MUNICIPALITY),
                 'death_year': d.get('year', ''), **({'death_date': d['date']} if d.get('date') else {}),
                 **({'death_place': d['place']} if d.get('place') else {}),
                 'survived': base == 20000, 'units': V.units_of(info),
                 'additional_info': f'{title}: {printed}, {info}', 'list': title, 'book_title': TITLE,
                 'source_url': viewer_url(book, r['page']), 'source_page': r['page'] - OFFSET}
            if role in ('activist', 'participant'):
                e['role'] = role
            entries.append(e)
            counts[f'{title}: {role or "fighter"}'] += 1
    OUT.write_text(json.dumps(entries, ensure_ascii=False, indent=1), encoding='utf-8')
    print(len(entries), 'entries ->', OUT.name, dict(counts))


if __name__ == '__main__':
    main()
