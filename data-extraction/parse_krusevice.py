"""
*Крушевице (Сврчуге – Петијевићи – Бијелићи)* (Vojin S. Murišić, Biblioteka "Hronika sela"; Poreklo library, doc
00000186), a book across units: three of its lists of the villages by Herceg Novi, in Cyrillic, every man named by his
surname, his father's possessive and his given name:

    The Kruševička partizanska četa as formed in 1941 (scan pp. 177-182), its command and five platoons: "· Радовић
        Трифков – Бела Петар, командир чете," (a nickname after a dash, the father's or his own).
    "Погинули у НОР и жртве фашистичког терора" (pp. 242-251), by village, a biography each: "Вавић Божов Радован –
        Раус, рођен 25. августа 1921, Крушевице, борац Крушевичке партизанске чете, ..., погинуо у Јасенику (Лика),
        октобра 1943." The victims of fascist terror stand under their own heading: out.
    "Носиоци Споменице 1941" (pp. 253-254), fifteen names in the dative ("· Милошевић Пера Обраду,"), the survivors.

A man in two of the lists is one entry: the biography or the spomenica's line is added to his line in the company.

The OCR swaps letters ("Рааовић" Радовић, "Сдасојев" Спасојев, "Рисшо" Ристо, "Бировић" Ћировић, "Ковић" Косић):
each word of a name is read as the variant of its letters the site's names know best (`best`).

Output: data-extraction/poreklo/krusevice-entries.json (IDs 9120xxxxxx: the company from 000001 in its order, the
fallen it doesn't name from 001001, the spomenica's holders it doesn't name from 002001).
Usage: python data-extraction/parse_krusevice.py
"""
from __future__ import annotations

import itertools
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

BOOK = 'krusevice.json'
OUT = HERE / 'poreklo' / 'krusevice-entries.json'
PREFIX = '9120'
OFFSET = 2                                   # scan page minus the book's page (scan 177 is p. 175)
TITLE = 'Kruševice (Svrčuge – Petijevići – Bijelići)'
COMPANY = 'Kruševička partizanska četa 1941.'
FALLEN = 'Poginuli u NOR'
SPOMENICA = 'Nosioci Spomenice 1941'
CU, CL = 'А-ЯЂЈЉЊЋЏ', 'а-яђјљњћџ'
VILLAGES = {'Крушевице': 'Kruševice', 'Крушевиие': 'Kruševice', 'Сврчуге': 'Svrčuge', 'Сврчубе': 'Svrčuge', 'Петијевићи': 'Petijevići',
            'Бијелићи': 'Bijelići'}
CONF = {'а': 'ад', 'ш': 'шт', 'и': 'ип', 'б': 'бгђ', 'Б': 'БЂЋ', 'Т': 'ТЋ', 'д': 'дп', 'о': 'од', 'у': 'уд',
        'Њ': 'ЊЉ', 'њ': 'њљ'}
FIX = {'Тхировић': 'Ћировић', '"ћировић': 'Ћировић', '"Бировић': 'Ћировић', '"Еуро': 'Ђуро', "'Борђо": 'Ђорђо',
       'Вировић': 'Ћировић', 'Ковић': 'Косић', "'Беклић": 'Ђеклић', '"Буре': 'Ђуре', '"Буров': 'Ђуров',
       '"Боко': 'Ђоко', "'Борђе": 'Ђорђе', '"ћировић': 'Ћировић', "'ћеклић": 'Ђеклић', 'Беклић': 'Ђеклић',
       'Прњшб': 'Прњат', 'Бироаић': 'Ћировић', 'Бурде': 'Ђурђе', 'Бура': 'Ђура', 'Њубу': 'Љубу'}


def variants(word: str, limit: int = 2048):
    choices = [CONF.get(c, c) for c in word]
    n = 1
    for c in choices:
        n *= len(c)
    return [word] if n > limit else [''.join(p) for p in itertools.product(*choices)]


def best(word: str, part: str) -> str:
    """the reading of a name word the site's names know best (as printed if it knows none), in Latin"""
    word = FIX.get(word, word).strip('.,;:\'"“')
    if not word:
        return ''
    if part == 'father':                                    # a possessive: Трифков, Божов, Перова, Лукин
        stem_ok = lambda c: max(V.T._given[latin(s.upper())] for s in                              # noqa: E731
                                (re.sub(r'(?:ов|ев|ин|ова|ева|ина)$', x, c) for x in ('', 'о', 'а', 'е')))
        top = max(variants(word), key=lambda c: (stem_ok(c), -sum(a != b for a, b in zip(c, word))))
        return latin(top)
    table = V.T._names if part == 'last' else V.T._given
    if table[latin(word.upper())]:                          # a name the site knows stays as printed (Vavić, not Vasić)
        return latin(word)
    top = max(variants(word), key=lambda c: (table[latin(c.upper())], -sum(a != b for a, b in zip(c, word))))
    return latin(top if table[latin(top.upper())] else word)


def stem(f: str) -> str:
    f = latin(f).lower() if re.search('[а-я]', f) else f.lower()
    f = re.sub(r'^đurđ(?=[aeu]?$)', 'đur', f)        # Đurđe of the fallen is the company's Đurov (Ćirović Janko)
    return re.sub(r'(?:ova|eva|ina|ov|ev|in|a|e|o|u)$', '', f)


# a fallen man found to be a company man after the entries' numbers were given (2026-11-22): joined to him, his own
# number left unused so that every later number stays put
LATE_JOINS = {('Ćirović', 'Janko')}


def lines(book: dict, pages) -> list[tuple[int, str]]:
    out = []
    for page in pages:
        for l in level_lines(page_words(book, page)):
            t = l.text.strip()
            if re.fullmatch(r'[\d\s.]{1,5}', t) or 'ХРОНИКА СЕЛА' in t or 'Муришић' in t and len(t) < 25:
                continue
            t = re.sub(rf'\b([ЈГ]) (?=[{CL}])', r'\1', t)                    # "Ј овов", "Г ајо"
            t = t.replace('"ћировић', 'Ћировић').replace("'ћеклић", 'Ђеклић')
            out.append((page, re.sub(r'^[·•\s]+', '', t)))
    return out


NAME = rf'(["\']?[{CU}][{CU}{CL}]+)\s+(\(Х\)|["\']?[{CU}][{CL}]+)(?:\s*[–—-]\s*([{CU}][{CL}]+))?\s+(?:[{CU}]\.\s*)?' \
       rf'(["\']?[{CU}][{CL}]+)(?:\s*[–—-]\s*(["\']?[{CU}][{CL}]+))?'
ROSTER = re.compile(rf'^{NAME}\s*,\s*(.*?)\s*(?:,\s*и|,|\s+и)?\s*\.?$')
BIO = re.compile(rf'^{NAME}\s*,\s*(рођен.*)$')


def person(g, dative=False):
    last, fath, fnick, given, nick = g[:5]
    if fath == '(Х)':                                      # no father given
        fath = ''
        if re.search(r'ић$', given) and not re.search(r'ић$', last):    # "Паско (Х) Чупић": the given name first
            last, given = given, last
    last = best(last, 'last')
    first = best(given, 'first')
    if dative:                                             # "Обраду", "Николи", "Саву", "Јованки"
        root = latin(FIX.get(given, given))
        cands = [root[:-1] + 'a'] if root.endswith('i') else [root[:-1], root[:-1] + 'o', root[:-1] + 'a']
        first = max(cands, key=lambda c: V.T._given[c.upper()])
    return last, best(fath, 'father') if fath else '', latin(fnick or ''), first, latin(FIX.get(nick, nick) or '')


def main():
    V.corpus()
    book = load(BOOK)
    entries, counts = [], Counter()
    unit = ''
    for page, t in lines(book, range(177, 183)):
        if re.match(r'^(Команда чете|\S+ вод):', t):
            unit = t.rstrip(':')
            continue
        m = ROSTER.match(t)
        if not m:
            continue
        last, father, fnick, first, nick = person(m.groups())
        duty = m.group(6).strip()
        entries.append({'last_name': last, 'fathers_name': father, 'first_name': first, 'nick': nick,
                        'birth_year': '', 'born_in': '', 'death_year': '', 'survived': False, 'units': [],
                        'text': [f"{COMPANY}, {latin(unit)}: {last} {father}{' – ' + fnick if fnick else ''} {first}"
                                 f"{' – ' + nick if nick else ''}, {V.read_cyr(duty)}."],
                        'list': COMPANY, 'page': page})
    for i, e in enumerate(entries, 1):
        e['soldier_id'] = f'{PREFIX}{i:06d}'
    counts['company'] = len(entries)

    def join(e):
        for x in entries:
            if x['last_name'] == e['last_name'] and x['first_name'] == e['first_name'] and \
                    stem(x['fathers_name'])[:4] == stem(e['fathers_name'])[:4]:
                x['text'] += e['text']
                for k in ('birth_year', 'born_in', 'death_year', 'death_place', 'death_date'):
                    if e.get(k) and not x.get(k):
                        x[k] = e[k]
                x['units'] = sorted(set(x['units']) | set(e['units']))
                if e['list'] == FALLEN:
                    x['survived'] = False
                elif e['list'] == SPOMENICA:
                    x['survived'] = True
                return True
        return False

    raw, village, victims = [], '', False
    for page, t in lines(book, range(242, 252)):
        if t.startswith('И 3 8 0 р') or t.startswith('Извор'):
            break
        head = t.rstrip(':').strip()
        if t.endswith(':') and head in VILLAGES:
            village, victims = VILLAGES[head], False
            continue
        if t.startswith('Жртве фашистичког терора'):
            victims = True
            continue
        m = BIO.match(t)
        if m:
            raw.append({'page': page, 'g': m.groups()[:5], 'text': m.group(6), 'village': village, 'victim': victims})
        elif raw:
            raw[-1]['text'] += ' ' + t
    n = 0
    for r in raw:
        if r['victim']:
            counts['victims out'] += 1
            continue
        info = V.read_cyr(r['text']).strip(' ;.')
        info = re.sub(r'\s*biblioteka\s*\W?\s*HRONIKA\s*S\s*ELA\s*\W?\s+', ' ', info, flags=re.I)   # the page's header
        role = None if re.search(r'borac|partizansk|komandir|komesar|kurir|bolničar|brigad|odred|bataljon', info, re.I) \
            else V.role(info)
        if role == 'out':
            counts['fallen out'] += 1
            print('   out:', r['g'][0], r['g'][3], '|', info[:100])
            continue
        last, father, fnick, first, nick = person(r['g'])
        d = V.death(info)
        born = re.search(r'rođen[a]?\s+(?:\d{1,2}\.\s*(?:\w+\s+|\d{1,2}\.))?(1[89]\d\d)', info)
        e = {'last_name': last, 'fathers_name': father, 'first_name': first, 'nick': nick,
             'birth_year': born.group(1) if born else '', 'born_in': f"{r['village']}, Herceg Novi" if r['village'] else '',
             'death_year': d.get('year', ''), **({'death_date': d['date']} if d.get('date') else {}),
             **({'death_place': d['place']} if d.get('place') else {}), 'survived': False,
             'units': V.units_of(info), 'role': role,
             'text': [f"{FALLEN}, {r['village']}: {last} {father}{' – ' + fnick if fnick else ''} {first}"
                      f"{' – ' + nick if nick else ''}, {info}."], 'list': FALLEN, 'page': r['page']}
        if join(e):
            counts['fallen joined'] += 1
            n += (e['last_name'], e['first_name']) in LATE_JOINS
            continue
        n += 1
        e['soldier_id'] = f'{PREFIX}{1000 + n:06d}'
        entries.append(e)
        counts['fallen'] += 1
    n, on = 0, False
    for page, t in lines(book, [253, 254]):
        on = on or 'Споменице 1941' in t and 'додјељене' not in t or 'додјељене' in t
        m = ROSTER.match(t.replace('др ', '')) if on else None
        if not m:
            continue
        last, father, fnick, first, nick = person(m.groups(), dative=True)
        nick = latin(m.group(5) or '')
        nick = nick[:-1] + 'o' if nick.endswith('u') else nick              # "Јовану — Јову"
        e = {'last_name': last, 'fathers_name': father, 'first_name': first, 'nick': nick, 'birth_year': '',
             'born_in': '', 'death_year': '', 'survived': True, 'units': [],
             'text': [f"{SPOMENICA}: {last} {father}{' – ' + fnick if fnick else ''} {first}"
                      f"{' – ' + nick if nick else ''}."], 'list': SPOMENICA, 'page': page}
        if join(e):
            counts['spomenica joined'] += 1
            continue
        n += 1
        e['soldier_id'] = f'{PREFIX}{2000 + n:06d}'
        entries.append(e)
        counts['spomenica'] += 1
    out = []
    for e in sorted(entries, key=lambda e: e['soldier_id']):
        name = ' '.join(x for x in (e['last_name'], e['fathers_name'], e['first_name']) if x)
        rec = {'soldier_id': e['soldier_id'], 'name': name, 'last_name': e['last_name'], 'also': [],
               'first_name': e['first_name'], 'nick': e['nick'], 'fathers_name': e['fathers_name'],
               'birth_year': e['birth_year'], 'born_in': e['born_in'] or 'Kruševice, Herceg Novi',
               'death_year': e['death_year'], **({'death_date': e['death_date']} if e.get('death_date') else {}),
               **({'death_place': e['death_place']} if e.get('death_place') else {}), 'survived': e['survived'],
               'units': e['units'], 'additional_info': ' '.join(e['text']), 'list': e['list'], 'book_title': TITLE,
               'source_url': viewer_url(book, e['page']), 'source_page': e['page'] - OFFSET}
        if e.get('role'):
            rec['role'] = e['role']
        out.append(rec)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding='utf-8')
    print(len(out), 'entries ->', OUT.name, dict(counts))
    for e in out:
        print(f"  {e['soldier_id']} {e['name']} {e['nick']} | {e['birth_year']} | {e['death_year']} "
              f"{e.get('death_place', '')} {e.get('role', '')} | {e['additional_info'][:80]}")


if __name__ == '__main__':
    main()
