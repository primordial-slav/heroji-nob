"""
*Остружница* (the village's chronicle, Biblioteka "Hronika sela"; Poreklo library, doc 00008195), a book across units:
its lists of the village's fighters (scan pp. 284-288, book pp. 260-264), in Cyrillic:

    "Првоборци из Остружнице": seven, given name first ("Љуба Ранковић, погинуо 1943. код села Барајева").
    "Изгинули у борбама": 29 numbered ("4. Костић М. Радисав, борац од 1944. погинуо у Славонији 1944").
    "Преживели борци": 130 numbered ("11 Деспотовић С. Илија, борац од октобра 1944"), with those of the command of the
        place (komanda mjesta), and "Сушић Радиша, за време рата помагао НОП" as an activist.

Out: those the occupier shot at the Sava in 1942 and those the Chetniks killed in 1943-1944, all but "Станковић
Богосав, полит. радник", who is an activist. No. 97 of the survivors, which the OCR runs into one unreadable word
("97ЈеппП1Рћпђа,бораЦ(л10ктобраводник 1944"), is left out until the scan is read.

Output: data-extraction/poreklo/ostruznica-entries.json (IDs 9117xxxxxx: the first fighters 000001-000007, the
fallen 000101 on by their number, Stanković Bogosav 000201, the survivors 001001 on by their number).
Usage: python data-extraction/parse_ostruznica.py
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

BOOK = 'ostruznica.json'
OUT = HERE / 'poreklo' / 'ostruznica-entries.json'
PREFIX = '9117'
OFFSET = 24                                  # scan page minus the book's page (scan 284 is p. 260)
TITLE = 'Ostružnica'
VILLAGE = 'Ostružnica, Beograd'
FIRST = 'Prvoborci iz Ostružnice'
FALLEN = 'Izginuli u borbama'
KILLED = 'Zaklani od strane četnika'
ALIVE = 'Preživeli borci'
CU, CL = 'А-ЯЂЈЉЊЋЏ', 'а-яђјљњћџ'

# lines the OCR ran together, and its slips in the names
FIX = {'58СћанковићЈБубомир,боршдодоктобра': '58 Станковић Љубомир, борац од октобра',
       '88ћдаринковићћдилорад,бораЦ(л10ктобра': '88 Маринковић Милорад, борац од октобра',
       'Деспотовдћ': 'Деспотовић', 'Станк0вић': 'Станковић', 'Стонковић': 'Станковић', 'Б анковић': 'Банковић',
       '17.0стојић': '17. Остојић', 'Тзорђевић': 'Ђорђевић', 'Борђевић': 'Ђорђевић', '"Бура': 'Ђура',
       '1О4': '104', '] еротијевић': 'Јеротијевић', 'Ј еротијевић': 'Јеротијевић', 'Њубомир': 'Љубомир',
       'Њубисав': 'Љубисав', 'Њубиша': 'Љубиша', 'Њ.': 'Љ.', 'живко': 'Живко', 'идџџ← љуба': 'Љуба',
       '\'Бурић': 'Ђурић', '"Бођевић "Борђе': 'Ђорђевић Ђорђе', 'четнИчке кане': 'четничке каме', 'окбобра': 'октобра',
       'Петровић I Чедомир': 'Петровић Чедомир', "Та'лић": 'Талић'}
SKIP_97 = '97ЈеппП1Рћпђа'


def lines(book: dict) -> list[tuple[int, str]]:
    out = []
    for page in range(284, 289):
        for l in level_lines(page_words(book, page)):
            t = l.text.strip()
            if re.fullmatch(r'\d{3}', t) and int(t) == page - OFFSET:
                continue                                                  # the page's number
            t = {'144': '1944'}.get(t, t)                                 # a wrapped year
            for a, b in FIX.items():
                t = t.replace(a, b)
            t = re.sub(r'^[\s\\.·"“\'IG←]+(?=[\d' + CU + '])', '', t)
            out.append((page, re.sub(r'^(\d{1,3})\s*[“"\'’]+', r'\1 ', t)))
    return out


def tidy(t: str) -> str:
    """the duty as printed, the words the OCR ran together set apart"""
    t = re.sub(r'(\d)\s+(\d{3})\b', r'\1\2', t)                                # "1 945"
    t = re.sub(r'(?<=[а-я])(водник|капетан|поручник)', r' \1', t)             # "од мартаводник 1944"
    t = re.sub(r'\bод(?=ст\.|водник)', 'од ', t)
    t = re.sub(r'(?<=[а-я])(?=[А-Я])', ' ', t)                                 # "новембраВодник"
    t = re.sub(r',(?=\S)', ', ', t)
    t = re.sub(r'(?<=[а-я])(19\d\d)', r' \1', t)                               # "Босни1944"
    return re.sub(r'\s+', ' ', t).strip(' .,')


NUMBERED = re.compile(rf'^(\d{{1,3}})\s*\.?\s*([{CU}][{CL}]+)\s+(?:([{CU}])\s*\.\s*)?([{CU}][{CL}]+)\s*,?\s*(.*)$')
GIVEN_FIRST = re.compile(rf'^([{CU}][{CL}]+)\s+(?:([{CU}])\.\s*)?([{CU}][{CL}]+),\s*(.*)$')


def main():
    V.corpus()
    book = load(BOOK)
    section, raw = None, []
    for page, t in lines(book):
        if t.startswith('ИЗБЕГАО'):
            break
        head = re.sub(r'[^А-ЯЂЈЉЊЋЏ ]', '', t).strip()
        if head.startswith('ПРВОБОРЦИ'):
            section = FIRST
            continue
        if head.startswith('СТРЕ'):
            section = 'shot'
            continue
        if head.startswith('ЗАКЛАНИ'):
            section = KILLED
            continue
        if head.startswith('ИЗГИНУЛИ'):
            section = FALLEN
            continue
        if head.startswith('ПРЕЖИВЕЛИ'):
            section = ALIVE
            continue
        if section in (None, 'shot') or t.startswith(SKIP_97):
            continue
        m = GIVEN_FIRST.match(t) if section == FIRST else NUMBERED.match(t)
        if section == FALLEN and not m:                                    # "←" then ". Андрејић Павле, ..."
            m = re.match(rf'^()([{CU}][{CL}]+)\s+(?:([{CU}])\s*\.\s*)?([{CU}][{CL}]+)\s*,\s*(.*)$', t)
        if m:
            raw.append({'section': section, 'page': page, 'g': m.groups()})
        elif raw and raw[-1]['section'] == section:
            raw[-1]['g'] = raw[-1]['g'][:-1] + (raw[-1]['g'][-1] + ' ' + t,)    # a wrapped year, "1944"
        else:
            print('   unread:', page, section, t[:90])
    entries, counts, seen = [], Counter(), Counter()
    for r in raw:
        s = r['section']
        if s == FIRST:
            given, init, last, rest = r['g']
            no = None
        else:
            no, last, init, given, rest = r['g']
            no = int(no) if no else 1
        if s == KILLED and 'полит' not in rest:
            counts['killed out'] += 1
            continue
        last, given = V.name_word(last), V.given_word(given)
        info = V.read_cyr(tidy(rest))
        seen[s] += 1
        if s == FIRST:
            sid = seen[s]
        elif s == FALLEN:
            sid = 100 + (no if no else seen[s])
        elif s == KILLED:
            sid = 201
        else:
            sid = 1000 + no
        father = V.read_cyr(init) if init else ''
        d = V.death(info) if s != ALIVE else {}
        name = ' '.join(x for x in (last, father + '.' if father else '', given) if x)
        printed = f"{given} {father + '. ' if father else ''}{last}" if s == FIRST else name
        prefix = f'{s}: {no}. ' if s != FIRST else f'{s}: '
        e = {'soldier_id': f'{PREFIX}{sid:06d}', 'name': ' '.join(x for x in (last, father, given) if x),
             'last_name': last, 'also': [], 'first_name': given, 'nick': '', 'fathers_name': father, 'birth_year': '',
             'born_in': VILLAGE, 'death_year': d.get('year', ''),
             **({'death_place': d['place']} if d.get('place') else {}),
             'survived': s == ALIVE or 'преживео' in rest, 'units': V.units_of(info),
             'additional_info': f'{prefix}{printed}, {info}.', 'list': s, 'book_title': TITLE,
             'source_url': viewer_url(book, r['page']), 'source_page': r['page'] - OFFSET}
        if s == KILLED or re.search(r'pomagao NOP|pol\.\s*teren|pol\.\s*rad|polit\.\s*rad', info) and 'borac' not in info:
            e['role'] = 'activist'
        entries.append(e)
        counts[f"{s} {e.get('role', 'fighter')}"] += 1
    ids = Counter(e['soldier_id'] for e in entries)
    assert not [i for i, n in ids.items() if n > 1], [i for i, n in ids.items() if n > 1]
    entries.sort(key=lambda e: e['soldier_id'])
    OUT.write_text(json.dumps(entries, ensure_ascii=False, indent=1), encoding='utf-8')
    alive = sorted(int(e['soldier_id'][-3:]) for e in entries if e['list'] == ALIVE)
    fallen = sorted(int(e['soldier_id'][-3:]) - 100 for e in entries if e['list'] == FALLEN)
    print(len(entries), 'entries ->', OUT.name, dict(counts), 'survivors missing', sorted(set(range(1, 131)) - set(alive)),
          'fallen missing', sorted(set(range(1, 30)) - set(fallen)))
    for e in entries:
        print(f"  {e['soldier_id']} {e['name']} | {e['death_year']} {e.get('death_place', '')} {e.get('role', '')} | "
              f"{e['additional_info'][:100]}")


if __name__ == '__main__':
    main()
