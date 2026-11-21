"""
*Трепча код Андријевице* (Biblioteka "Hronika sela"; Poreklo library, doc 00000113), a book across units: the village's
fighters of 1941-1945 (scan pp. 280-283, book pp. 273-276), in Cyrillic:

    "Трепчани у јединицама Народноослободилачке војске": the men by the unit they fought in (the Andrijevica partisan
        battalion, the 4., 5., 6., 7., 8. and 9. crnogorska, the 10. bokeljska, the 2. proleterska, the Kosmet units,
        the Komski odred, the 1. prekomorska, ...), two columns in rows under each unit's heading; "Свега бораца НОП-а
        од 1941. до 1945. у Трепчи је било 91";
    "Погинули борци НОВ" (pp. 282-283): 21 with a line each, "13. – Нововић Радошев Милић, земљорадник, ... борац 4.
        прол. црногор. бригаде, на Боркову, ...".

A man in both is one entry: the fallen's line is added to his unit's. Out: those killed in the April war's bombings,
the hostages shot by the Germans, Italians and Chetniks (pp. 283-284), and Raičević Milićkov Akso, shot by mistake
for another man (the list's no. 21).

Output: data-extraction/poreklo/trepca-entries.json (IDs 9126xxxxxx: the men of the units from 000001, the fallen the
units don't name from 001001).
Usage: python data-extraction/parse_trepca.py
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

BOOK = 'trepca.json'
OUT = HERE / 'poreklo' / 'trepca-entries.json'
PREFIX = '9126'
OFFSET = 7                                   # scan page minus the book's page (scan 280 is p. 273)
TITLE = 'Trepča kod Andrijevice'
UNITS = 'Trepčani u jedinicama Narodnooslobodilačke vojske'
FALLEN = 'Poginuli borci NOV'
VILLAGE = 'Trepča, Andrijevica'
CU, CL = 'А-ЯЂЈЉЊЋЏ', 'а-яђјљњћџ'
NAME = re.compile(rf"(?:^|\s)(?:\d{{1,2}}\s*\.?\s*[–—-]?\s*|[|\s]+)?([{CU}][{CL}]+(?:–[{CU}][{CL}]+)?)\s+(?:([{CU}][{CL}]+|[{CU}]\.)\s+)?"
                  rf"(['\"]?[{CU}][{CL}]+(?:\s*[-–—]\s*['\"]?[{CU}][{CL}]+)?)(?=\s*(?:,|у\s|$|\d))")
HEAD = re.compile(rf'^\W*(\d{{1,2}})\s*\.\s*[–—-]\s*(.*(?:бригад|одред|батаљон|чет[иа]|јединиц|корпус|артиљериј).*)$', re.I)


def clean(t: str) -> str:
    t = re.sub(r"['\"]\s*[Бћ](?=[уо]р|ор)", 'Ђ', t).replace('Нивовић', 'Нововић').replace('љубомир', 'Љубомир')
    return t.replace('Алексадра', 'Александра').replace('Миш/ша', 'Миша').replace('ДОбРО', '')


def roster(book: dict) -> list[dict]:
    """every name under a unit's heading, the heading the nearest above it on the page, in either column"""
    out = []
    for page in (280, 281, 282):
        items = []
        for col in page_lines(book, page, 2):
            for l in col:
                items.append((l.top, l.x0, clean(l.text.strip())))
        items.sort()
        unit = out[-1]['unit'] if out else ''
        for top, x0, t in items:
            if t.startswith('Свега бораца') or t.startswith('1.– Погинули') or 'Погинули борци' in t:
                return out
            h = HEAD.match(t)
            if h:
                unit = re.sub(r'\s+', ' ', h.group(2)).strip(' .')
                continue
            if not unit or re.search(r'ТРЕПЧЕ|НАРОДНООСЛОБОДИЛАЧКЕ|^\d{3}$', t):
                continue
            for m in NAME.finditer(t):
                last, father, given = m.group(1), m.group(2) or '', m.group(3)
                if last in ('Свега', 'Овај', 'Сви', 'Трепчани') or len(given) < 3:
                    continue
                out.append({'page': page, 'unit': unit, 'last': last, 'father': father, 'given': given})
    return out


def fallen(book: dict) -> list[dict]:
    raw, on = [], False
    for page in (282, 283):
        for l in page_lines(book, page, 1)[0]:
            t = clean(l.text.strip())
            if 'Погинули борци НОВ' in t:
                on = True
                continue
            if not on:
                continue
            if t.startswith('2. — Погинули од бомбардовања') or 'Погинули од бомбардовања' in t:
                return raw
            m = re.match(rf'^\W*(\d{{1,2}})?\s*\.?\s*[–—-]?\s*([{CU}][{CL}]+)\s+([{CU}][{CL}]+)\s+([{CU}][{CL}]+(?:\s*[–-]\s*[{CU}][{CL}]+)?)\s*,\s*(.*)$', t)
            if m and l.x0 < 700:
                raw.append({'page': page, 'last': m.group(2), 'father': m.group(3), 'given': m.group(4), 'text': m.group(5)})
            elif raw and not re.fullmatch(r'[–—~\-\s]+', t):
                raw[-1]['text'] += ' ' + t
    return raw


def stem(f: str) -> str:
    return re.sub(r'(?:ова|ева|ина|ов|ев|ин|а|е|о)$', '', f.lower())


def main():
    V.corpus()
    book = load(BOOK)
    men = roster(book)
    entries, counts = [], Counter()
    for r in men:
        gparts = re.split(r'\s*[-–—]\s*', r['given'].strip('\'"'))
        e = {'last': V.name_word(r['last'].split('–')[0]), 'first': V.given_word(gparts[0]),
             'nick': V.given_word(gparts[1]) if len(gparts) > 1 else '', 'father': latin(r['father']),
             'father_c': r['father'], 'units_text': [latin(r['unit'])], 'fell': '', 'page': r['page']}
        same = [x for x in entries if x['last'] == e['last'] and x['first'] == e['first'] and stem(x['father_c'])[:4] == stem(e['father_c'])[:4]]
        if same:                                             # in two units' lists
            same[0]['units_text'].append(latin(r['unit']))
            continue
        entries.append(e)
    counts['units'] = len(entries)
    n = 0
    for r in fallen(book):
        info = V.read_cyr(re.sub(r'\s+', ' ', r['text'])).strip(' ."')
        if 'grešk' in info:                                 # Akso, shot by mistake for another man
            counts['out'] += 1
            continue
        gparts = re.split(r'\s*[-–—]\s*', r['given'])
        last, first = V.name_word(r['last']), V.given_word(gparts[0])
        hit = [x for x in entries if x['last'] == last and x['first'] == first and stem(x['father_c'])[:4] == stem(r['father'])[:4]]
        if hit:
            hit[0]['fell'] = info
            hit[0]['page_f'] = r['page']
            counts['fallen joined'] += 1
            continue
        n += 1
        entries.append({'last': last, 'first': first, 'nick': V.given_word(gparts[1]) if len(gparts) > 1 else '',
                        'father': latin(r['father']), 'father_c': r['father'], 'units_text': [], 'fell': info,
                        'page': r['page'], 'id': f'{PREFIX}{1000 + n:06d}'})
        counts['fallen'] += 1
    out = []
    for i, e in enumerate(entries, 1):
        sid = e.get('id') or f'{PREFIX}{i:06d}'
        name = ' '.join(x for x in (e['last'], e['father'], e['first']) if x)
        parts = []
        if e['units_text']:
            parts.append(f"{UNITS}: {'; '.join(e['units_text'])}: {name}{' – ' + e['nick'] if e['nick'] else ''}.")
        if e['fell']:
            parts.append(f"{FALLEN}: {name}, {e['fell']}.")
        info = ' '.join(parts)
        d = V.death(e['fell']) if e['fell'] else {}
        out.append({'soldier_id': sid, 'name': name, 'last_name': e['last'], 'also': [], 'first_name': e['first'],
                    'nick': e['nick'], 'fathers_name': e['father'], 'birth_year': '', 'born_in': VILLAGE,
                    'death_year': d.get('year', ''), **({'death_place': d['place']} if d.get('place') else {}),
                    'survived': False, 'units': V.units_of(info.replace('prol.', 'proleterske').replace('crnogor.', 'crnogorske')),
                    'additional_info': info, 'list': UNITS if e['units_text'] else FALLEN, 'book_title': TITLE,
                    'source_url': viewer_url(book, e.get('page_f', e['page'])), 'source_page': e.get('page_f', e['page']) - OFFSET})
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding='utf-8')
    print(len(out), 'entries ->', OUT.name, dict(counts))
    for e in out:
        print(f"  {e['soldier_id']} {e['name']} {e['nick']} | {e['death_year']} {e['units']} | {e['additional_info'][:110]}")


if __name__ == '__main__':
    main()
