"""
Jovo Ilije Krsmanović, *Соколац путевима Романије и историје* (Poreklo library, doc 00002506): its chapter XII,
"Списак погинулих бораца у II светском рату 1941-1945." (scan pp. 522-569, book pp. 524-571), the fallen fighters
of the Sokolac area, as a book across units. One column, Cyrillic, numbered 1-503, a bio each: "2. Амовић Косте
Милован (1922) из Ћаварина. Ступио у НОВ 1. августа 1941. године. Погинуо 7. априла 1943. као борац Шесте источно
босанске бригаде на Копиту у борби против усташа. Члан КПЈ." The surname, the father in the genitive and the given
name; most served in the Romanijski partizanski odred and the 20. romanijska brigada, which the site has not.
The OCR loses some numbers ("1 I.", ". Шука Неђа Бранко"): an entry starts where the name, father, given name and a
year or "из" stand at a line's start in the list's order. The list ends with the author's note ("За друге изгинуле
борце немамо податке ..."); the chapter after it, the Chetniks' dead (book p. 572 on), is out.

Output: data-extraction/poreklo/sokolac-entries.json (IDs 9093xxxxxx, by the book's number).
Usage: python data-extraction/parse_sokolac.py [--sample N]
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
import _village_books as V  # noqa: E402
from parse_ostrvica import level_lines  # noqa: E402
from poreklo_text import load, page_words, viewer_url  # noqa: E402

BOOK = 'sokolac.json'
OUT = HERE / 'poreklo' / 'sokolac-entries.json'
PREFIX = '9093'
OFFSET = -2                                 # scan page minus the book's page (the running heads: "525" on scan 523)
TITLE = 'Sokolac putevima Romanije i istorije'
LIST = 'Spisak poginulih boraca u II svetskom ratu 1941-1945.'
MUNICIPALITY = 'Sokolac'
UC, LC = 'А-ЯЂЈЉЊЋЏ', 'а-яђјљњћџ'
NAME = rf"['’\"]?[{UC}ћђљњ][{LC}'’]+(?:\s*[–—-]\s*[{UC}][{LC}]+)?"
# an entry's first line: the number (or what the OCR left of it), surname, father, given name, then the year or "из"
START = re.compile(rf"^(?:([\dlIі ]{{1,5}})\s*\.?\s*|\.\s*)?({NAME})\s+({NAME})\s+({NAME}|[A-Z][a-z]+)"
                   rf"((?:\s+{NAME})?)\s*(?=\(|из\s|са\s|\d)")


def lines(book: dict) -> list[tuple[int, str]]:
    out = []
    for page in range(522, 570):
        for l in level_lines(page_words(book, page)):
            t = l.text.strip()
            if re.match(r'^(?:Соколац пут|\d{3}\s+Јово|Јово\s)', t) or re.search(r'Крсмановић$', t) and len(t) < 40:
                continue                                    # the running heads
            out.append((page, t))
    return out


def number(s: str | None) -> int | None:
    if not s:
        return None
    d = s.replace(' ', '').replace('l', '1').replace('I', '1').replace('і', '1')
    return int(d) if d.isdigit() else None


# a numbered line in the list's order whose next word is a name, however the OCR garbled it ("348. Onom-111 Илије
# Спасоје (1896.)", "74. Војновић Глигор (1917)", "347. Одовнћ (Маринка) Тане"): the name runs to the year, "из",
# "са" or the first comma or full stop
LOOSE = re.compile(rf"^([\dlIі]{{1,3}}|\d\s\d)\s*\.?\s+([^\s\d(][^(]*?(?:\([^)\d]*\)[^(]*?)?)\s*"
                   rf"(?=\(\s*[\dlI)]|\s+из\s|\s+са\s|,|\.\s)")
# entries whose start no rule sees, the OCR having garbled the name: the line's start -> the book's number and name
FORCE = {"'ћајлћ (\"тојка Марко": (446, ('Ćajić', 'Stojka', 'Marko', '')),
         "'ћерат-тнћ Тимоша Јован": (455, ('Ćeranić', 'Timoša', 'Jovan', '')),
         'Цт–цњ–и-ш "ћорћа Бранко': (459, ('Cicmil', 'Đorđa', 'Branko', ''))}
# names the OCR garbled, read from the list's alphabetical order and the site's records of the Sokolac area
# (Ćajić of Nepravdići, Ćeranić of Sokolovići, Cicmil): by the book's number, (surname, father, given name, nickname)
NAMES = {48: ('Bošković', 'Radovana', 'Đoko', ''), 64: ('Vajner', 'Dušana', 'Slaviša', 'Čiča'),
         65: ('Višnjić', 'Neđa', 'Milana', ''), 113: ('Đerić', 'Mila', 'Ljubomir', ''),
         121: ('Đokić', 'Pera', 'Mlađen', ''), 124: ('Đukić', 'Janka', 'Đuro', ''), 127: ('Đukić', 'Rista', 'Bogdan', ''),
         128: ('Đukić', 'Save', 'Maksim', ''), 130: ('Đurković', 'Janka', 'Drago', ''),
         131: ('Đurović', 'Blagoja', 'Rade', ''), 134: ('Đurović', 'Jovana', 'Milan', ''),
         186: ('Jolović', 'Danila', 'Đoko', ''), 341: ('Nešković', '', 'Neđo', ''), 348: ('Odović', 'Ilije', 'Spasoje', ''),
         422: ('Stanić', 'Todora', 'Milorad', ''), 442: ('Ćajić', 'Đorđa', 'Budimir', ''),
         457: ('Frganja', 'Milenka', 'Novica', ''),         # the census's Frganja Milenko Novica, 1925, Šenkovići
         458: ('Hrljić', 'Ibrahima', 'Bero', ''),           # the given name as the OCR read it
         460: ('Cicmil', 'Pera', 'Stevo', '')}


def split_name(head: str) -> tuple[str, str, str, str]:
    """surname, father, given name and nickname of a name as printed: "Шука Неђа Бранко", "Војновић Глигор",
    "Одовнћ (Маринка) Тане", "Беатовић Стјепана Илија Бибо".
    """
    head = re.sub(r"^['’“\"]+", '', head).strip()
    m = re.match(r'^(\S+)\s+\(([^)]+)\)\s+(\S+)(.*)$', head)
    if m:
        return m.group(1), m.group(2), m.group(3), m.group(4).strip()
    w = head.split()
    if len(w) == 1:
        return w[0], '', '', ''
    if len(w) == 2:
        return w[0], '', w[1], ''
    return w[0], w[1], w[2], ' '.join(w[3:])


def raw_entries(book: dict) -> list[dict]:
    raw, started = [], False
    for page, t in lines(book):
        if not started:
            started = t.startswith('1941')
            continue
        if t.startswith('За друге изгинуле'):
            break
        t = re.sub(rf'(?<![{UC}{LC}])([{UC}])\s(?=[{LC}]{{2}})', r'\1', t)     # "Г алавић"
        forced = next((v for k, v in FORCE.items() if k in t[:45]), None)
        if forced:
            raw.append({'no': forced[0], 'page': page, 'names': forced[1], 'read': True,
                        'parts': [t[t.index(' ('):] if ' (' in t else '']})
            continue
        last = raw[-1]['no'] if raw else 0
        m = START.match(t)
        n = number(m.group(1)) if m else None
        loose = LOOSE.match(t) if not m or n is None else None
        ln = number(loose.group(1)) if loose else None
        if loose and ln is not None and last + 1 <= ln <= last + 3:
            raw.append({'no': ln, 'page': page, 'names': split_name(loose.group(2)), 'parts': [t[loose.end():]]})
        elif m and (n is None and raw or n is not None and last + 1 <= n <= last + 3):
            raw.append({'no': n if n is not None else last + 1, 'page': page,
                        'names': (m.group(2), m.group(3), m.group(4), m.group(5).strip()), 'parts': [t[m.end():]]})
        elif raw:
            raw[-1]['parts'].append(t)
    return raw


def main():
    book = load(BOOK)
    raw = raw_entries(book)
    entries, counts = [], Counter()
    for r in raw:
        sur, fath, given, nick = r['names']
        if r['no'] in NAMES or r.get('read'):
            last, fath, first, nick = NAMES.get(r['no'], r['names'])
        else:
            last = '-'.join(V.name_word(x) for x in re.split(r'\s*[–—-]\s*', sur) if x)
            first, fath = (V.given_word(given) if given else ''), (V.father(fath) if fath else '')
            nick = V.read_cyr(nick) if nick else ''

        body = re.sub(r'\s+', ' ', V.unhyphen(' '.join(r['parts']))).strip()
        info = re.sub(r'^[,.\s]+', '', V.read_cyr(body))
        info = re.sub(r'\bH(OB|OV)\b', r'N\1', info)       # the OCR's Latin H for Н ("stupio u HOB")
        y = re.match(r'^\(\s*([1l][89][\d ]{2,3})\s*[.,(]?\s*\)?', info)
        year = re.sub(r'\s', '', y.group(1)).replace('l', '1') if y else ''
        year = year if re.fullmatch(r'1[89]\d\d', year) else ''
        born = re.search(rf'\b(?:iz|sa)\s+([A-ZČĆŽŠĐ][\w]+(?:\s+[A-ZČĆŽŠĐ][\w]+)?)', info)
        # the brigade's name set in two words ("Šeste istočno bosanske"), read as one for the unit and the role
        units_text = re.sub(r'(istočn)o\s+(bosansk)', r'\1o\2', info, flags=re.I)
        d = V.death(info)
        role = V.role(units_text)
        if role == 'out':                           # a list of fighters: a courier of a staff, "stupio u Deveteačku četu"
            role = None
            counts['read as fighter'] += 1
        e = {'soldier_id': f"{PREFIX}{r['no']:06d}", 'name': f'{last} {fath} {first}'.replace('  ', ' '),
             'last_name': last, 'also': [], 'first_name': first, 'nick': nick, 'fathers_name': fath,
             'birth_year': year,
             'born_in': f"{born.group(1)}, {MUNICIPALITY}" if born and born.group(1) != MUNICIPALITY else '',
             'death_year': d.get('year', ''), **({'death_date': d['date']} if d.get('date') else {}),
             **({'death_place': d['place']} if d.get('place') else {}),
             'survived': False, 'units': V.units_of(units_text),
             **({'role': role} if role else {}),
             'additional_info': f"{LIST}: {r['no']}. {last} {fath} {first}{' ' + nick if nick else ''} {info}",
             'list': LIST, 'book_title': TITLE,
             'source_url': viewer_url(book, r['page']), 'source_page': r['page'] - OFFSET}
        entries.append(e)
        counts[role or 'fighter'] += 1
    OUT.write_text(json.dumps(entries, ensure_ascii=False, indent=1), encoding='utf-8')
    print(dict(counts), '->', OUT.name, len(entries), 'last no', raw[-1]['no'] if raw else 0)
    nos = [r['no'] for r in raw]
    print('gaps/dups:', [n for n in range(1, nos[-1] + 1) if n not in nos], [n for n, c in Counter(nos).items() if c > 1])
    print(Counter(u for e in entries for u in e['units']).most_common())
    if '--sample' in sys.argv:
        random.seed(5)
        for e in random.sample(entries, min(int(sys.argv[sys.argv.index('--sample') + 1]), len(entries))):
            print(f"  {e['name']} | {e['birth_year']} [{e['born_in']}] † {e['death_year']} {e.get('death_place', '')!r} "
                  f"{e['units']} | {e['additional_info'][:130]}")


if __name__ == '__main__':
    main()
