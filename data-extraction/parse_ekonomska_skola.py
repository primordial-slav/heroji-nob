"""
*100 година Прве економске школе "Владимир Перић Валтер" у Београду* (Poreklo library, doc 00008734), a book across
units: two of the lists of its pupils and teachers, a short biography each, in Cyrillic, two columns:

    "Погинули у априлском рату 1941, НОБ-и, стрељани и умрли у фашистичким логорима" (scan pp. 191-199): "Атијас
        Азриел, ученик / Рођен је 4. децембра 1923. године у Београду. Био је активиста омладинског покрета у Школи
        1940. године и уредник листа „Чепркало". Пао је у народноослободилачкој борби."
    "Преживели учесници априлског рата и НОБ-а" (pp. 200-216): "Агатоновић Јелисавета, ученица / ... У шумадијски
        партизански одред отишла је априла 1943. године. Била је борац 2. шумадијске бригаде, ...".

By the mixed lists' rule: those who fought in the NOB (a unit, "пао у народноослободилачкој борби", a partisan duty)
are fighters; the movement's people (the party, SKOJ, illegal work, those who helped the NOP) activists; those the
lists name for the April war alone, the captivity, or as victims of the occupier with no word of the movement (the
Jewish pupils killed at the Sajmište camp) are out. The participants of the wars to 1918 (pp. 187-190) are out.

Output: data-extraction/poreklo/ekonomska-skola-entries.json (IDs 9124xxxxxx: the dead from 000001, the survivors
from 001001, in the lists' order).
Usage: python data-extraction/parse_ekonomska_skola.py
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

BOOK = 'ekonomska-skola.json'
OUT = HERE / 'poreklo' / 'ekonomska-skola-entries.json'
PREFIX = '9124'
OFFSET = 4                                   # scan page minus the book's page (scan 191 is p. 187)
TITLE = '100 godina Prve ekonomske škole „Vladimir Perić Valter” u Beogradu'
DEAD = 'Poginuli u aprilskom ratu 1941, NOB-i, streljani i umrli u fašističkim logorima'
ALIVE = 'Preživeli učesnici aprilskog rata i NOB-a'
CU, CL = 'А-ЯЂЈЉЊЋЏ', 'а-яђјљњћџ'
START = re.compile(rf'^([{CU}][{CL}]+(?:\s*[-–]\s*[{CU}][{CL}]+)?)\s+(?:\S{{1,3}}\.\s*)?([{CU}][{CU}{CL}]+(?:\s*[-–—]\s*[{CU}][{CL}]+)?)'
                   r'\s*,\s*(ученик|ученица|професор\w*|наставни\w*|службени\w*|директор\w*|секретар\w*|'
                   r'послужитељ\w*|радни\w*|библиотекар\w*)\s*\.?$')
FOUGHT = re.compile(r'(?:[Пп]а[оо]|[Пп]ала|[Пп]огину\w+)\s+(?:је\s+)?(?:[уy]|као)\s+(?:народноослободилач[кн]|партизан)|партизан|'
                    r'борац|бригад|одред|дивизиј|[Уу]чесни\w+\s+(?:[јj][еe]\s+)?(?:[уy]\s+)?(?:НОР|НОБ|[Нн]ародноослободилач)|'
                    r'[Уу]чествова\w+\s+(?:[јj][еe]\s+)?[уy]\s+(?:народноослободилач|завршним борбама)|[Уу]\s+НОБ|комесар|командир|'
                    r'командант|обавештајн|курир|болничар|ОЗН|КНОЈ|НОВЈ|Сремск\w+ фронт|Партизанске споменице')
MOVEMENT = re.compile(r'КПЈ|НПЈ|СКОЈ|СНОЈ|скојев|комунист|илегал|НОП|народноослободилачки покрет|активист|омладинск\w+ покрет|'
                      r'БОТИЧ|Народн\w+ помоћ|напредн\w+ покрет|УСАОЈ|АФЖ')


def entries_of(book: dict, pages, start: str, stop: str) -> list[dict]:
    raw, on = [], False
    for page in pages:
        for col in page_lines(book, page, 2):
            for l in col:
                t = l.text.strip()
                if not on:
                    on = t.startswith(start)
                    continue
                if t.startswith(stop):
                    return raw
                if re.fullmatch(r'[\d\s.·_—–\-|\\]{1,6}', t):
                    continue
                t = re.sub(r"[\"'‘]\s*ћ(?=[уо])", 'Ђ', t)                      # "'ћуро", "'ћорђе"
                t = t.replace('ћоковић драгомир', 'Ђоковић Драгомир')
                t = re.sub(r'(?<=[а-я])0|0(?=[а-я])', 'о', re.sub(r'(?<=[а-я])6(?=[а-я])', 'б', t))   # "нар0дноосло60дилачкој"
                # an entry run into the line before ("... борби. Нахмијаз Ђуро, ученик")
                for part in re.split(rf'(?<=[.!])\s+(?=[{CU}][{CL}]+\s+\S+\s*,\s*(?:ученик|ученица|професор))', t):
                    m = START.match(part)
                    if m:
                        raw.append({'page': page, 'last': m.group(1), 'given': m.group(2), 'post': m.group(3),
                                    'text': []})
                    elif raw:
                        raw[-1]['text'].append(part)
    return raw


def main():
    V.corpus()
    book = load(BOOK)
    entries, counts = [], Counter()
    for raw, list_name, base, survived in ((entries_of(book, range(191, 201), 'Погинули', 'Преживели учесници'),
                                            DEAD, 0, False),
                                           (entries_of(book, range(200, 218), 'Преживели учесници', 'Део четврти'),
                                            ALIVE, 1000, True)):
        n = 0
        for r in raw:
            cyr = re.sub(r'\s+', ' ', V.unhyphen(' '.join(r['text'])))
            if FOUGHT.search(cyr) and not re.fullmatch(r'.*(?:априлском рату|заробљеништв)[^.]*\.(?:\s*Одликован[^.]*\.)*\s*', cyr):
                role = None
            elif MOVEMENT.search(cyr):
                role = 'activist'
            else:
                counts[f'{list_name[:9]} out'] += 1
                continue
            last = '-'.join(V.name_word(x) for x in re.split(r'\s*[-–]\s*', r['last']))
            gparts = re.split(r'\s*[-–—]\s*', r['given'])
            given = V.given_word(gparts[0])
            nick = V.given_word(gparts[1]) if len(gparts) > 1 else ''
            info = V.read_cyr(cyr).strip(' .')
            born = re.search(r'Rođen[a]?\s+(?:je\s+)?(?:\d{1,2}\.?\s*\w+\s+)?(1[89]\d\d)', info)
            place = re.search(r'Rođen[a]?\s+(?:je\s+)?(?:\d{1,2}\.?\s*\w+\s+)?1[89]\d\d\.?\s*(?:godine)?\s*u\s+([A-ZČĆŽŠĐ][\w]+'
                              r'(?:\s+[A-ZČĆŽŠĐ][\w]+)?)', info)
            d = V.death(info) if not survived else {}
            n += 1
            post = latin(r['post'])
            name = f'{last} {given}'
            e = {'soldier_id': f'{PREFIX}{base + n:06d}', 'name': name, 'last_name': last, 'also': [],
                 'first_name': given, 'nick': nick, 'fathers_name': '', 'birth_year': born.group(1) if born else '',
                 'born_in': place.group(1) if place else '', 'death_year': d.get('year', ''),
                 **({'death_date': d['date']} if d.get('date') else {}),
                 **({'death_place': d['place']} if d.get('place') else {}), 'survived': survived,
                 'units': V.units_of(info),
                 'additional_info': f"{list_name}: {name}{' – ' + nick if nick else ''}, {post}. {info}.",
                 'list': list_name, 'book_title': TITLE, 'source_url': viewer_url(book, r['page']),
                 'source_page': r['page'] - OFFSET}
            if role:
                e['role'] = role
            entries.append(e)
            counts[f"{list_name[:9]} {role or 'fighter'}"] += 1
    OUT.write_text(json.dumps(entries, ensure_ascii=False, indent=1), encoding='utf-8')
    print(len(entries), 'entries ->', OUT.name, dict(counts))
    for e in entries:
        print(f"  {e['soldier_id']} {e['name']} {e['nick']} | {e['birth_year']} {e['born_in']} | {e['death_year']} "
              f"{e.get('role', '')} | {e['additional_info'][:100]}")


if __name__ == '__main__':
    main()
