"""
*Вилуси (заједница села: Балосаве, Броћанац, Долови, Околишта, Подбожур, Ријечани, Спила)* (Biblioteka "Hronika
sela"; Poreklo library, doc 00000367), a book across units: "Погинули и страдали у Другом свјетском рату 1941-1945.
године" (scan pp. 264-275), the dead of the villages of Vilusi by Grahovo, numbered, in Cyrillic:

    "11. БАБИЋ Стевана ВИДАК, Вилуси, жељезнички службеник; борац НОВ и члан КПЈ од 1941. године; командант
    батаљона "Лука Вукаловић" у Херцеговини и илегални позадински радник; погинуо 4. августа 1943. године од четника
    на Клобуцима."

The surname in capitals, the father as a possessive (at times a genitive, "Стевана", "Новице др"), the given name in
capitals. The list is every death of the war: the partisans, the Chetniks (the Vučedol brigade, the retreat to
Slovenia in 1945), those the NOP's organs shot, the victims of fascist terror ("ЖФТ"). Only the fighters are taken,
and the movement's other people as activists (`role`), as in Grahovski Kovačevići, whose Kovačevići are this list's
too.

Output: data-extraction/poreklo/vilusi-entries.json (IDs 9119xxxxxx by the list's number).
Usage: python data-extraction/parse_vilusi.py
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
from _parser_scaffold import cyrillic_to_latin as latin  # noqa: E402
from poreklo_text import load, page_words, viewer_url  # noqa: E402

BOOK = 'vilusi.json'
OUT = HERE / 'poreklo' / 'vilusi-entries.json'
PREFIX = '9119'
OFFSET = 2                                   # scan page minus the book's page (scan 264 is p. 262)
TITLE = 'Vilusi (zajednica sela: Balosave, Broćanac, Dolovi, Okolišta, Podbožur, Riječani, Spila)'
LIST = 'Poginuli i stradali u Drugom svjetskom ratu 1941–1945. godine'
MUNICIPALITY = 'Nikšić'
CU, CL = 'А-ЯЂЈЉЊЋЏ', 'а-яђјљњћџ'
OUT_RE = re.compile(r'ЖФТ|четни[кцч]\w*\s+(?:покрет|бригад|чет|батаљон|одред)|у четницима|у Четниц|четничк\w+ покрет|'
                    r'приступи\w* четни|присталица четника|одступи\w* (?:са четницима )?према Словенији|'
                    r'приликом одступања|Драже Михајловића|органа НО[ПГ]|војног суда|од стране партизана|'
                    r'од партизана|дезертер|са четницима у блоку|у четничком блоку|учесник четни|у четничк|'
                    r'командант четничк|био у четн|затим у четни|жртва фашистичког', re.I)
FIGHTER = re.compile(r'борац|учесни\w+ НО[ВП]|учествовао у НОВ|партизанск|командир|командант|комесар|делегат|'
                     r'курир|болничар|НОВЈ|бригаде|одреда|батаљона', re.I)
ACTIVIST = re.compile(r'присталица НОП|позадинск|сарадник НОП|илегал|одборник|СКОЈ|члан КПЈ|АФЖ|НОО', re.I)


def clean(t: str) -> str:
    t = re.sub(r"И[‘'’]?(?:ћ|Б|Т1|Тт|Тх|Т;|Т:|ТТ|В|П)(?=[\sЈ,])", 'ИЋ', t)           # "КОВАЧЕВИ'ћ", "КОВАЧЕВИТ1"
    t = t.replace('Лз', 'Љ').replace("ЂОР'ВИЈЕ-ТЈОКА", 'ЂОРЂИЈЕ-ЂОКА').replace('АТ1ИМ', 'АЋИМ')
    t = re.sub(r'(?<=[ИЋ])\s?[ЈJ] (?=[{0}])'.format(CL), ' Ј', t)                        # "ВИЋЈ евремов"
    t = re.sub(r"[\"“'‘]\s*[ЋћБ](?=[УОЕуоеи])", 'Ђ', t)                              # "'БУРО", "“ћУРО", "\"ћуров"
    t = re.sub(r"(?<=[{0}])'[Б](?=[{0}])".format(CU), 'Ђ', t)                         # "'БОР'БО"
    t = t.replace('Сцила', 'Спила').replace('ВУКАШРШ', 'ВУКАШИН').replace('Радоавнов', 'Радованов')
    t = t.replace('>КИВКО', 'ЖИВКО').replace('15 1.', '151.')
    t = re.sub(r'\b([ЈГ]) (?=[{0}]{{2,}})'.format(CU), r'\1', t)                     # "Ј ОВАН"
    t = re.sub(r'([{0}]{{2,}}) ([{0}]{{1,2}})(?=[\s,])'.format(CU), r'\1\2', t)       # "ВОЈ ИН"
    t = t.replace("ЂОР'ВИЈЕ-ТЈОКА", 'ЂОРЂИЈЕ-ЂОКА')
    return re.sub(r'([{0}]) ј ([{0}])'.format(CL), r'\1ј\2', t)                       # "Спасо ј ев"


ENTRY = re.compile(rf'^(\d{{1,3}})\s*\.\s*([{CU}][{CU}ЋЂ]+(?:[-–][{CU}]+)?)\s+'
                   rf'((?:[{CU}][{CL}]+)(?:\s+др)?)\s+([{CU}][{CU}{CL}\-–]+(?:\s*[-–]\s*[{CU}]+)?)'
                   r'(?:\s+["“][^"”]+["”])?\s*[,;]\s*(.*)$')


def lines(book: dict) -> list[tuple[int, str]]:
    out, on = [], False
    for page in range(264, 276):
        for l in level_lines(page_words(book, page)):
            t = l.text.strip()
            if 'ДРУГОМ СВЈЕТСКОМ РАТУ' in t:
                on = True
                continue
            if not on or re.fullmatch(r'[\d\s.]{1,5}', t) or l.x0 > 3000:
                continue
            if t.startswith('УСПОМЕНА СА'):
                return out
            out.append((page, clean(t)))
    return out


def main():
    V.corpus()
    book = load(BOOK)
    raw = []
    for page, t in lines(book):
        m = ENTRY.match(t)
        if m and (not raw or 0 < int(m.group(1)) - raw[-1]['no'] <= 6):
            raw.append({'no': int(m.group(1)), 'page': page, 'g': m.groups()[1:4], 'text': m.group(5)})
        elif raw:
            raw[-1]['text'] += ' ' + t
    entries, counts = [], Counter()
    for r in raw:
        sur, fath, given = r['g']
        cyr = r['text']
        village = re.split(r'[,;]', cyr, 1)[0].strip()
        if OUT_RE.search(cyr) and not re.search(r'борац НОВ|учесник НОВ од 1941', cyr) or \
                re.search(r'ЖФТ|приступио четни|затим (?:био )?у четни|у четницима', cyr):
            counts['out'] += 1
            continue
        info = V.read_cyr(cyr).strip(' .;')
        role = None if FIGHTER.search(cyr) else ('activist' if ACTIVIST.search(cyr) else V.role(info))
        if role == 'out':
            counts['out'] += 1
            print('   out:', r['no'], sur, given, '|', info[:100])
            continue
        last = V.name_word(sur.split('-')[0]) + ''.join('-' + V.name_word(x) for x in sur.split('-')[1:])
        gparts = re.split(r'\s*[-–]\s*', given)
        first = V.given_word(gparts[0].capitalize())
        nick = V.given_word(gparts[1].capitalize()) if len(gparts) > 1 else ''
        father = latin(fath.replace(' др', ''))
        d = V.death(info)
        name = ' '.join(x for x in (last, father, first) if x)
        place = latin(village) if village and len(village) < 25 else ''
        e = {'soldier_id': f"{PREFIX}{r['no']:06d}", 'name': name, 'last_name': last, 'also': [], 'first_name': first,
             'nick': nick, 'fathers_name': father, 'birth_year': '',
             'born_in': f'{place}, {MUNICIPALITY}' if place else '', 'death_year': d.get('year', ''),
             **({'death_date': d['date']} if d.get('date') else {}),
             **({'death_place': d['place']} if d.get('place') else {}),
             'survived': False, 'units': V.units_of(info),
             'additional_info': f"{LIST}: {r['no']}. {last} {latin(fath)} {first}{' – ' + nick if nick else ''}, {info}.",
             'list': LIST, 'book_title': TITLE, 'source_url': viewer_url(book, r['page']),
             'source_page': r['page'] - OFFSET}
        if role:
            e['role'] = role
        entries.append(e)
        counts[role or 'fighter'] += 1
    nos = [r['no'] for r in raw]
    OUT.write_text(json.dumps(entries, ensure_ascii=False, indent=1), encoding='utf-8')
    print(len(entries), 'entries ->', OUT.name, dict(counts), 'read', len(raw), 'numbers missing',
          sorted(set(range(1, max(nos) + 1)) - set(nos)))
    for e in entries:
        print(f"  {e['soldier_id']} {e['name']} {e['nick']} | {e['born_in']} | {e['death_year']} "
              f"{e.get('death_place', '')} {e['units']} {e.get('role', '')}")


if __name__ == '__main__':
    main()
