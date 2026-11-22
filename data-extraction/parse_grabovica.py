"""
*Грабовица у Дробњаку и породице у њој* (Todor Janjić; Poreklo library, doc 00009740), a book across units: in its
chapter "Грабовица у НОР-у 1941-1945" (scan pp. 134-142, book pp. 123-131), the village's people in the NOB by family,
"Из породице Јањић, учествовали у НОБ-у" and "Из породице Јанковића", a paragraph each, the given name and the
father's possessive:

    "– Јеврем Јованов, члан КПЈ од почетка 1942. учесник 13-тојулског устанка, ... Од почетка 1942. године борац
    Дурмиторског партизанског одреда на сињајевинском сектору. Погинуо 16. априла 1942. г. на Сињајевини."

The fighters (a unit, a duty in one) without a role, the committee members and the NOP's helpers as activists, the
rest as participants, by the mixed lists' rule; a quoted memoir of one of them (Vidoje Žarković's of Danica Janjić)
is part of her entry.

Output: data-extraction/poreklo/grabovica-entries.json (IDs 9128xxxxxx in the list's order).
Usage: python data-extraction/parse_grabovica.py
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
from poreklo_text import load, page_lines, viewer_url  # noqa: E402

BOOK = 'grabovica.json'
OUT = HERE / 'poreklo' / 'grabovica-entries.json'
PREFIX = '9128'
OFFSET = 11                                  # scan page minus the book's page (scan 134 is p. 123)
TITLE = 'Grabovica u Drobnjaku i porodice u njoj'
VILLAGE = 'Grabovica, Šavnik'
CU, CL = 'А-ЯЂЈЉЊЋЏ', 'а-яђјљњћџ'
FAMILIES = {'ЈАЊИ': 'Janjić', 'ЈАНКОВИ': 'Janković'}
START = re.compile(rf"^[–—\-Ч.\s]*([{CU}][{CL}]+)\s+(?:\(?)([{CU}][{CL}']+)\s*,?\s+(.*)$")
FOUGHT = re.compile(r'борац|бригад|одред|батаљон|команд|комесар|курир|болничар|делегат|руководилац|ескадрил', re.I)
HELPED = re.compile(r'одборник|помагао|помагала|сарадник|НОП|СКОЈ|КПЈ|илегал', re.I)


def main():
    V.corpus()
    book = load(BOOK)
    raw, family = [], ''
    for page in range(134, 143):
        lines = page_lines(book, page, 1)[0]
        base = min(l.x0 for l in lines if len(l.text) > 30)
        for l in lines:
            t = l.text.strip().replace("М'ијајлов", 'Мијајлов').replace('Мпјајло', 'Мијајло')
            if 'ОРГАНИЗАЦИЈА НАР' in t:
                break
            hm = re.search(rf'ПОРОДИЦЕ\s+([{CU}]+)', t)
            if hm:
                family = next((v for k, v in FAMILIES.items() if hm.group(1).startswith(k)), latin(hm.group(1).title()))
                continue
            if re.fullmatch(r'\d{3}', t) or not family:
                continue
            m = START.match(t)
            indented = l.x0 > base + 120
            if m and indented and re.match(r'^[–—\-Ч.]', t) and not m.group(2).endswith('ић'):   # not "Видоје Жарковић"'s memoir
                raw.append({'page': page, 'family': family, 'given': m.group(1), 'father': m.group(2), 'text': [m.group(3)]})
            elif raw:
                raw[-1]['text'].append(t)
    entries, counts = [], Counter()
    for r in raw:
        cyr = re.sub(r'\s+', ' ', V.unhyphen(' '.join(r['text'])))
        role = None if FOUGHT.search(cyr) else ('activist' if HELPED.search(cyr) else 'participant')
        given, father = V.given_word(r['given']), latin(r['father'].strip("'"))
        last = r['family']
        info = V.read_cyr(cyr).strip(' .')
        d = V.death(info)
        fell = bool(re.search(r'[Пп]огину|[Пп]огибе|умр[лo]\w* (?:у|од)|стријељ|убијен|нестао', cyr)) and \
            not re.search(r'[Уу]мро (?:је )?19[5-9]\d|послије рата', cyr)
        name = f'{last} {father} {given}'
        e = {'soldier_id': f'{PREFIX}{len(entries) + 1:06d}', 'name': name, 'last_name': last, 'also': [],
             'first_name': given, 'nick': '', 'fathers_name': father, 'birth_year': '', 'born_in': VILLAGE,
             'death_year': d.get('year', '') if fell else '', **({'death_place': d['place']} if fell and d.get('place') else {}),
             'survived': not fell, 'units': V.units_of(info),
             'additional_info': f"Iz porodice {last}, učestvovali u NOB-u: {given} {father}, {info}.",
             'list': 'Grabovica u NOR-u 1941–1945.', 'book_title': TITLE, 'source_url': viewer_url(book, r['page']),
             'source_page': r['page'] - OFFSET}
        if role:
            e['role'] = role
        entries.append(e)
        counts[role or 'fighter'] += 1
    OUT.write_text(json.dumps(entries, ensure_ascii=False, indent=1), encoding='utf-8')
    print(len(entries), 'entries ->', OUT.name, dict(counts))
    for e in entries:
        print(f"  {e['soldier_id']} {e['name']} | {e['death_year']} {'survived' if e['survived'] else 'fell'} "
              f"{e.get('role', '')} | {e['additional_info'][:100]}")


if __name__ == '__main__':
    main()
