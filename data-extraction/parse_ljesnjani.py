"""
*Lješnjani u borbi za slobodu* (Mitar Đurišić, Miomir Radunović, Miloš T. Uskoković; doc 00002814 of the Poreklo
library), a book across units: the lists after its chapter on the Lješanska nahija (by Podgorica) in the NOP, in
Cyrillic:

    "Poginuli u NOR-u" (scan pp. 184-199), 218 numbered entries and a "5a": "1. Благојевић Томов Андрија, рођен 1921.
        у Станисељићима. Стријељан 10. априла 1942. на Врелима рибничким." The father is a possessive (as printed:
        the matcher reads it so); some entries give the name alone ("12. Брновић Б. Михаило.").
    "Narodni heroji" (p. 201): three names, the one the fallen list prints too (Čelebić Milovan) joined to his entry.
    "Nosioci Partizanske spomenice 1941" (pp. 202-203): 39 names, two columns read row by row.

The lists of those killed in the April war, of the victims of fascist terror, and the appendices (the Chetniks of
colonel Stanišić who died, those who fled the country) stay out.

The OCR sets Ђ and Ћ alike as a small ћ, a quote before it at times ("ћуров", '"ћуришић', '"ћетковић'), which the
site's names decide (`soft_c`); it reads Ђуро as '"hypo' and breaks a few words ("Богој евић").

Output: data-extraction/poreklo/ljesnjani-entries.json (IDs 9112xxxxxx: the fallen from 000001 in the list's order,
the heroes from 001001, the spomenica holders from 002001 by the book's number).
Usage: python data-extraction/parse_ljesnjani.py
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

BOOK = 'ljesnjani.json'
OUT = HERE / 'poreklo' / 'ljesnjani-entries.json'
PREFIX = '9112'
OFFSET = 0                                   # the scan's pages are the book's
TITLE = 'Lješnjani u borbi za slobodu'
FALLEN = 'Poginuli u NOR-u'
HEROES = 'Narodni heroji'
SPOMENICA = 'Nosioci Partizanske spomenice 1941'
MUNICIPALITY = 'Podgorica'
CU, CL = 'А-ЯЂЈЉЊЋЏ', 'а-яђјљњћџ'
# the surname, the father's possessive with what he was called after a dash ("Ристов – Шитов") or an initial, none
# at times ("88. Давидовић Даница"), the given name and a nickname after a dash
NAME = (rf'([{CU}ћ][{CL}]+(?:\s*[—–-]\s*[{CU}ћ][{CL}]+)?)'
        rf'(?:\s+((?:[{CU}ћ][{CL}]+|[{CU}]\.|др)(?:\s*[—–-]\s*[{CU}ћ][{CL}]+)?))?\s+([{CU}ћ][{CL}]+)'
        rf'(?:\s*[—–-]\s*([{CU}ћ][{CL}]+))?')
ENTRY = re.compile(rf'^(\d{{1,3}}[аa]?)\s*[.,]?\s+{NAME}\s*[,.]?\s*(.*)$')
# the spomenica's names, two to a line; a woman's father in the feminine possessive ("Божинина")
SPOM = re.compile(rf'(\d{{1,2}})\s*\.?\s+([{CU}ћ][{CL}]+(?:\s*[—–-]\s*[{CU}ћ][{CL}]+)?)\s+([{CU}ћ][{CL}]+|[{CU}]\.)'
                  rf'(?:\s+([{CU}ћ][{CL}]+))?(?:\s+([{CU}ћ][{CL}]+))?')


# the OCR's slips past the rules: Burzanović Ilijin Đoko, as the Spomenica crnogorskim antifašistima prints him
READ = {'"Bono': 'Ђоко', 'Стај кић (Радусиновић) Божова Мариј а': 'Стајкић-Радусиновић Божова Марија'}


def soft_c(word: str) -> str:
    """a name the OCR begins with a small ћ: Ђ or Ћ, whichever the site's names have more often ("ћуришић" is
    Đurišić, "ћетковић" Ćetković)"""
    rest = word[1:]

    def n(c):
        return max(V.T._names[latin((c + rest).upper())], V.T._given[latin((c + rest).upper())])
    return max(('Ђ', 'Ћ'), key=n) + rest


def clean(t: str) -> str:
    t = re.sub(r'["\']?\bhypo\b', 'Ђуро', t).replace('Владшшр', 'Владимир')
    for a, b in READ.items():
        t = t.replace(a, b)
    t = re.sub(r'["\']\s*ћ', 'ћ', t)                     # '"ћуров', '"ћетковић': the quote is no Ђ (see soft_c)
    t = re.sub(rf'([{CU}])\)\.', r'\1.', t)                                # "Т)." for "Т."
    t = re.sub(rf'\b([{CU}]) ([{CL}]{{2,}})', r'\1\2', t)                   # "Г аврило"
    t = re.sub(rf'([{CL}]) (евић|ић|овић)\b', r'\1\2', t)                   # "Богој евић"
    return re.sub(rf'(?<=[{CL}])([{CU}]+)(?=[{CL}])', lambda m: m.group(1).lower(), t)   # "БогОјевић"


def lines(book: dict, pages) -> list[tuple[int, str]]:
    out = []
    for page in pages:
        for l in level_lines(page_words(book, page)):
            t = l.text.strip().lstrip('\'"’ ')                     # "' 143. Пејовић Илијин Мило"
            if re.fullmatch(r'[\d\s.]{1,6}', t):
                continue
            out.append((page, clean(t)))
    return out


def person(sur: str, fath: str | None, given: str, nick: str | None) -> tuple[str, str, str, str, str]:
    """the name as the site writes it, and the father as printed with what he was called ("Ristov – Šitov")"""
    fix = lambda w: soft_c(w) if w.startswith('ћ') else w                     # noqa: E731
    last = '-'.join(V.name_word(fix(x)) for x in re.split(r'\s*[—–-]\s*', sur))
    if fath == 'др':                                      # "121. Кажић др Милутин": a title, no father
        return last, '', V.given_word(fix(given)), V.given_word(fix(nick)) if nick else '', 'dr'
    fparts = [latin(fix(x)) for x in re.split(r'\s*[—–-]\s*', fath or '') if x]
    return (last, fparts[0] if fparts else '', V.given_word(fix(given)), V.given_word(fix(nick)) if nick else '',
            ' – '.join(fparts))


def fallen(book: dict) -> list[dict]:
    raw = []
    for page, t in lines(book, range(184, 200)):
        if t.startswith('ПОГИНУЛИ'):
            continue
        m = ENTRY.match(t)
        last_no = int(re.sub(r'\D', '', raw[-1]['no'])) if raw else 0
        if m and (not raw or 0 <= int(re.sub(r'\D', '', m.group(1))) - last_no <= 2):
            raw.append({'no': m.group(1), 'page': page, 'head': m.groups()[1:5], 'parts': [m.group(6)]})
        elif raw:
            raw[-1]['parts'].append(t)
    out = []
    for i, r in enumerate(raw, 1):
        last, fath, first, nick, fprinted = person(*r['head'])
        info = V.read_cyr(' '.join(r['parts'])).strip()
        d = V.death(info)
        born = re.search(r'\brođen[a]?\s+(?:\d{1,2}\.\s*\w+\s+)?(1[89]\d\d)', info)
        printed = f"{r['no']}. {' '.join(x for x in (last, fprinted, first) if x)}{' — ' + nick if nick else ''}"
        e = {'soldier_id': f'{PREFIX}{i:06d}', 'name': ' '.join(x for x in (last, fath, first) if x), 'last_name': last,
             'also': [],
             'first_name': first, 'nick': nick, 'fathers_name': fath, 'birth_year': born.group(1) if born else '',
             'born_in': V.born_in(info, MUNICIPALITY), 'death_year': d.get('year', ''),
             **({'death_date': d['date']} if d.get('date') else {}),
             **({'death_place': d['place']} if d.get('place') else {}),
             'survived': False, 'units': V.units_of(info),
             'additional_info': f"{FALLEN}: {printed}{', ' + info if info else '.'}", 'list': FALLEN,
             'book_title': TITLE, 'source_url': viewer_url(book, r['page']), 'source_page': r['page'] - OFFSET}
        role = V.role(e['additional_info'])
        if role == 'activist':
            e['role'] = 'activist'
        out.append(e)
    return out


def main():
    V.corpus()
    book = load(BOOK)
    entries = fallen(book)
    counts = Counter(f"fallen {e.get('role', 'fighter')}" for e in entries)
    # the heroes (p. 201), the one of the fallen joined to his entry
    started = False
    n = 0
    for page, t in lines(book, [201]):
        started = started or t.startswith('НАРОДНИ ХЕРОЈИ')
        m = re.match(rf'^(\d)\.\s+{NAME}$', t) if started else None
        if not m:
            continue
        last, fath, first, _, _ = person(*m.groups()[1:5])
        hits = [e for e in entries if e['last_name'] == last and e['first_name'] == first and e['fathers_name'][:1] == fath[:1]]
        if hits:
            hits[0]['additional_info'] += f' {HEROES}: {m.group(1)}. {last} {fath} {first}.'
            counts['heroes joined'] += 1
            continue
        n += 1
        entries.append({'soldier_id': f'{PREFIX}{1000 + n:06d}', 'name': f'{last} {fath} {first}', 'last_name': last,
                        'also': [], 'first_name': first, 'nick': '', 'fathers_name': fath, 'birth_year': '',
                        'born_in': '', 'death_year': '', 'survived': False, 'units': [],
                        'additional_info': f'{HEROES}: {m.group(1)}. {last} {fath} {first}', 'list': HEROES,
                        'book_title': TITLE, 'source_url': viewer_url(book, page), 'source_page': page - OFFSET})
        counts['heroes'] += 1
    # the spomenica holders (pp. 202-203), two columns run into one line
    started = False
    seen = set()
    for page, t in lines(book, [202, 203]):
        started = started or 'СПОМЕНИЦЕ' in t
        if not started:
            continue
        for m in SPOM.finditer(t):
            no = int(m.group(1))
            if no in seen or not 1 <= no <= 39:
                continue
            seen.add(no)
            sur, fath, given, nick = m.group(2), m.group(3), m.group(4), m.group(5)
            if no == 20:                          # "20. Милошевић Ускоковић / Васова Вукосава", set over two lines
                sur, fath, given, nick = 'Милошевић-Ускоковић', 'Васова', 'Вукосава', None
            elif not given:                       # "25. Радусиновић Митар": no father
                fath, given = '', fath
            last, fath, first, nick, _ = person(sur, fath, given, nick)
            entries.append({'soldier_id': f'{PREFIX}{2000 + no:06d}', 'name': ' '.join(x for x in (last, fath, first) if x),
                            'last_name': last, 'also': [], 'first_name': first, 'nick': nick, 'fathers_name': fath,
                            'birth_year': '', 'born_in': '', 'death_year': '', 'survived': True, 'units': [],
                            'additional_info': f"{SPOMENICA}: {no}. {' '.join(x for x in (last, fath, first, nick) if x)}",
                            'list': SPOMENICA, 'book_title': TITLE, 'source_url': viewer_url(book, page),
                            'source_page': page - OFFSET})
            counts['spomenica'] += 1
    if 20 not in seen:                    # "20. Милошевић – Ускоковић / Васова Вукосава", set over two lines
        entries.append({'soldier_id': f'{PREFIX}002020', 'name': 'Milošević-Uskoković Vasova Vukosava',
                        'last_name': 'Milošević-Uskoković', 'also': [], 'first_name': 'Vukosava', 'nick': '',
                        'fathers_name': 'Vasova', 'birth_year': '', 'born_in': '', 'death_year': '', 'survived': True,
                        'units': [], 'additional_info': f'{SPOMENICA}: 20. Milošević-Uskoković Vasova Vukosava',
                        'list': SPOMENICA, 'book_title': TITLE, 'source_url': viewer_url(book, 203), 'source_page': 203})
        seen.add(20)
        counts['spomenica'] += 1
    entries.sort(key=lambda e: e['soldier_id'])
    missing = sorted(set(range(1, 40)) - seen)
    OUT.write_text(json.dumps(entries, ensure_ascii=False, indent=1), encoding='utf-8')
    print(len(entries), 'entries ->', OUT.name, dict(counts), 'spomenica missing', missing)
    for e in entries:
        print(f"  {e['soldier_id']} {e['name']} {e['nick']} | {e['birth_year']} {e['born_in']} | {e['death_year']} "
              f"{e.get('death_place', '')} {e['units']} {e.get('role', '')}")


if __name__ == '__main__':
    main()
