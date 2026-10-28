"""
Stevo Dapčević, "Жртве села Лежимира 1941-1945." (Годишњак за истраживање геноцида, св. 12/1, 2020; Poreklo
library, doc 00005912, scan pp. 96-121): every dead of Ležimir in Srem, numbered, one column, Cyrillic, "Презиме,
име оца, име, година рођења, начин страдања, време страдања, место страдања": "41. Бабић (Радован) Петар, рођен
1914, погинуо 1943. у НОБ-у, код ...". A book across units: only the fighters go in, the entries that put the man in
the movement's army ("погинуо у НОБ-у", "у НОП-у", "припадник НОВ и ПОЈ", "као члан НОБ-а"); the movement's
helpers killed for it ("сарадник НОП-а") are marked `role: 'activist'`. The victims of the Ustaša and German
terror, those the partisans killed and the men of other armies stay out.

Output: data-extraction/poreklo/lezimir-entries.json (IDs 9096xxxxxx, by the article's number).
Usage: python data-extraction/parse_lezimir.py [--sample N]
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

BOOK = 'lezimir.json'
OUT = HERE / 'poreklo' / 'lezimir-entries.json'
PREFIX = '9096'
OFFSET = 1                                  # scan page minus the volume's page
TITLE = 'Godišnjak za istraživanje genocida, sv. 12/1 (2020)'
LIST = 'Stevo Dapčević, Žrtve sela Ležimira 1941-1945.'
UC, LC = 'А-ЯЂЈЉЊЋЏ', 'а-яђјљњћџ'
START = re.compile(r'^(\d{1,3})?\s*\.\s+(.*)$')
FIGHTER = re.compile(r'\bu\s*NOB|\bu\s+NOP|NOB-a|pripadnik\s+(?:NOV|NOP)|\bu\s+NOV\b|partizansk\w*\s+(?:odred|brigad|jedinic)',
                     re.I)
HELPER = re.compile(r'saradnik\w*\s+NOP|aktivist|odbornik', re.I)
BY_PARTISANS = re.compile(r'od\s+partizana', re.I)


def raw_entries(book: dict) -> list[dict]:
    out, started = [], False
    for page in range(96, 122):
        for l in level_lines(page_words(book, page)):
            t = l.text.strip()
            if not started:
                started = t.startswith('1. Аврамовић')
                if not started:
                    continue
            if re.match(r'^Годишњак|^Стево Дапчевић|^\d{2,3}$', t):
                continue
            if t.startswith('Микица Илић') or 'УДК' in t or re.match(r'^\d{2}:\d', t):
                return out
            m = START.match(t)
            last = out[-1]['no'] if out else 0
            n = int(m.group(1)) if m and m.group(1) else None
            if m and re.match(rf'[{UC}]', m.group(2)) and (n is not None and last < n <= last + 3 or n is None and l.x0 < 900 and
                                                           re.search(r'(?:рођен|убијен|погинул|стрељан)', t)):
                out.append({'no': n or last + 1, 'page': page, 'lines': [m.group(2)]})
            elif out:
                out[-1]['lines'].append(t)
    return out


def main():
    book = load(BOOK)
    entries, counts = [], Counter()
    for r in raw_entries(book):
        text = re.sub(r'\s+', ' ', V.unhyphen(' '.join(r['lines']))).strip()
        # the OCR's Ђ: "Тзорђе", "Т)ока", "ћорђе"
        text = re.sub(r'Тз|Т\)|(?<![\w])ћ(?=ор|ок|ур)', 'Ђ', text)
        # its Љ read as Њ ("Њубомир"), a word broken by a space ("Андриј а"), and one name read with Д for Л
        text = re.sub(r'(?<![\w])Њуб', 'Љуб', text)
        text = re.sub(r'(\w)ј а\b', r'\1ја', text).replace('Кдичарић (Вдада) Миденко', 'Кличарић (Влада) Миленко')
        info = V.read_cyr(text)
        if BY_PARTISANS.search(info) or not (FIGHTER.search(info) or HELPER.search(info)):
            counts['out'] += 1
            continue
        role = 'activist' if not FIGHTER.search(info) else None
        # the name, read in the site's spelling where the OCR read Л as Д ("Кдичарић (Вдада) Миденко"): the
        # surname, the father in brackets, the given name, a nickname after a dash, the author's note in brackets
        cyr = re.match(r'^(\S+?)\s+(?:\(([^)]*)\)\s+)?([^,(]+?)\s*(?:\([^)]*\)\s*)?,', text)
        if not cyr:
            print('  no name:', info[:100])
            continue
        given, nick = cyr.group(3).strip(), ''
        if re.search(r'\s[–—-]\s', given):
            given, nick = [x.strip() for x in re.split(r'\s[–—-]\s', given, 1)]
        last = V.name_word(cyr.group(1))
        fath = V.given_word(cyr.group(2)) if cyr.group(2) else ''
        given = V.given_word(given)
        nick = V.read_cyr(nick) if nick else ''
        y = re.search(r'\brođen[a]?\s+(1[89]\d\d)', info)
        d = V.death(re.sub(r',?\s*\b(?:u|i)\s+(?:NOB|NOP|NOV)\S*', '', info))
        entries.append({
            'soldier_id': f"{PREFIX}{r['no']:06d}", 'name': ' '.join(x for x in (last, fath, given) if x),
            'last_name': last, 'also': [], 'first_name': given, 'nick': nick, 'fathers_name': fath,
            'birth_year': y.group(1) if y else '', 'born_in': 'Ležimir, Sremska Mitrovica',
            'death_year': d.get('year', ''), **({'death_date': d['date']} if d.get('date') else {}),
            **({'death_place': d['place']} if d.get('place') else {}),
            'survived': False, 'units': V.units_of(info), **({'role': role} if role else {}),
            'additional_info': f"{LIST}: {r['no']}. {info}", 'list': LIST, 'book_title': TITLE,
            'source_url': viewer_url(book, r['page']), 'source_page': r['page'] - OFFSET})
        counts[role or 'fighter'] += 1
    nos = [r['no'] for r in raw_entries(book)]
    print('read', len(nos), 'last', max(nos), 'gaps', [n for n in range(1, max(nos) + 1) if n not in nos][:20])
    OUT.write_text(json.dumps(entries, ensure_ascii=False, indent=1), encoding='utf-8')
    print(dict(counts), '->', OUT.name, len(entries))
    if '--sample' in sys.argv:
        random.seed(8)
        for e in random.sample(entries, min(int(sys.argv[sys.argv.index('--sample') + 1]), len(entries))):
            print(f"  {e['name']} — {e['nick']} | {e['birth_year']} † {e['death_year']} {e.get('death_place', '')!r} "
                  f"{e.get('role', '')} | {e['additional_info'][:120]}")


if __name__ == '__main__':
    main()
