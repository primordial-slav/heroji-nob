"""
Хан Пијесак, простор-вријеме-људи (Poreklo library, doc 00004058): the fighters of the Han Pijesak municipality and
those who fell on its ground, as a book across units. Cyrillic; the OCR reads the font's Ћ as Б, В or Н ("АЛЕКСИБ",
"ТЕРЗИВ", "Бјелаковнћ") and its Љ as Њ: names and text are read back as the site spells them (_village_books).
Three lists go in:
  - "Погинули у Пјеновцу" (scan pp. 107-110): the Prva proleterska's Šumadijski (5th) and 6th battalion and the
    Romanijski NOP odred, killed on 21 January 1942 at Pjenovac (47), and the ten of the battalions killed elsewhere
    in the municipality in the 2nd offensive, numbered, "11. ИЛИБ Радоја МИЛАН Чича Шумадијски, командант 5. бат.,
    рођен 1886, Горња Трешњевица, Аранђеловац ...": the surname and the given name in capitals, the father between,
    a nickname after;
  - "Народни хероји и истакнути учесници НОБ-а" (pp. 148-151): fourteen bios, the given name first ("Светозар
    (Јосипа) Косорић"), the names typed from the OCR (`HEROES`); a man another list names too is one entry with both
    texts, under that list's number; three of them lived through the war;
  - "Погинули борци у Другом свјетском рату од 1941. до 1945." (pp. 152-162): 150 numbered bios, "14. Дрљић
    (Љубисава) Мићо, рођен 1923. у Малом Пољу, у НОВ од 15. септембра 1944, ...", the number often lost. Its
    activists (a field or party worker, "активиста", "активни сарадник") are marked `role: 'activist'` by
    parse_mosorski_odred_2's rule; two killed by Chetnik bands in 1946 are in as the book counts them.
Out: the Chetniks' dead (p. 201 on) and the 1992-1995 war's (p. 254 on), not fetched.

Output: data-extraction/poreklo/han-pijesak-entries.json, IDs 9085xxxxxx: Pjenovac 9085000001-047, the ten
9085000101-110, the heroes no other list names 9085000201-214 (by their number), the fallen 9085001001-150.
Usage: python data-extraction/parse_han_pijesak.py
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

BOOK = 'han-pijesak.json'
OUT = HERE / 'poreklo' / 'han-pijesak-entries.json'
PREFIX = '9085'
OFFSET = 1                                  # scan page minus the book's page
TITLE = 'Han Pijesak, prostor-vrijeme-ljudi'
MUNICIPALITY = 'Han Pijesak'
PJENOVAC = 'Poginuli u Pjenovcu 21. januara 1942'
OFFENSIVE = 'Poginuli u borbama protiv Nijemaca na području opštine Han Pijesak u 2. neprijateljskoj ofanzivi'
HERO_LIST = 'Narodni heroji i istaknuti učesnici NOB-a sa područja opštine'
FALLEN = 'Poginuli borci u Drugom svjetskom ratu od 1941. do 1945. godine'
UC, LC = 'А-ЯЂЈЉЊЋЏ', 'а-яђјљњћџ'
# the heroes' list, by its number: surname, father (genitive), given name, nickname, the other list's entry he is
# in (list, number) or None, and whether he lived through the war (his bio says he died after it)
HEROES = {1: ('Kosorić', 'Josipa', 'Svetozar', 'Kostreš', ('fallen', 47), False),
          2: ('Bjelaković', 'Vidaka', 'Mihajlo', '', ('fallen', 10), False),
          3: ('Ilić', '', 'Milan', 'Čiča Šumadijski', ('pjenovac', 11), False),
          4: ('Pavlović', '', 'Dragoslav', 'Šiljo', ('pjenovac', 27), False),
          5: ('Vajner', 'Dušana', 'Slaviša', 'Čiča romanijski', ('pjenovac', 44), False),
          6: ('Bešlagić', 'Agana', 'Refik', '', None, False),
          7: ('Vuksanović', 'Obrena', 'Slavoljub', 'Jajko', None, False),
          8: ('Jovanović', 'Miloša', 'Dušan', '', None, True),
          9: ('Abazović', '', 'Rade', '', None, True),
          10: ('Stanišić', 'Ljube', 'Rade', 'Cicmil', ('fallen', 124), False),
          11: ('Pejanović', 'Arsena', 'Miladin', '', ('fallen', 84), False),
          12: ('Rubež', 'Riste', 'Branko', '', ('fallen', 107), False),
          13: ('Gligorović', 'Uroša', 'Rajko', 'Minja', None, True),
          14: ('Radulović-Babić', 'Mile', 'Mićo', '', ('fallen', 103), False)}
# the fathers no rule reads, as the hero's other entry shows ("Ендака" is Видака)
WORDS = {'Endaka': 'Vidaka', 'Tocora': 'Todora', 'Tedora': 'Todora'}


def lines(book: dict, pages) -> list[tuple[int, str]]:
    out = []
    for page in pages:
        for l in level_lines(page_words(book, page)):
            t = l.text.strip()
            if l.x0 > 3000 or re.fullmatch(r'[\d\s.,:*~“"\'?šit]{1,8}', t) or \
                    re.match(r'^\d{3}\s+(?:Исто|Види|Јеремија)', t):
                continue                                    # specks in a photo, page numbers, footnotes
            out.append((page, t))
    return out


def father(w: str) -> str:
    f = V.father(w)
    return WORDS.get(f, f)


def year_of(info: str) -> str:
    m = re.search(r'\brođen[a]?\s+(?:je\s+)?(?:u\s+[^,]{2,30}?\s+)?(?:\d{1,2}\.\s*\w+\s+)?(1[89]\d\d)', info)
    return m.group(1) if m else ''


def death_fields(info: str) -> dict:
    d = V.death(info)
    return {'death_year': d.get('year', ''), **({'death_date': d['date']} if d.get('date') else {}),
            **({'death_place': d['place']} if d.get('place') else {})}


def pjenovac(book: dict) -> list[dict]:
    """The two numbered lists of the 2nd offensive's fallen (scan pp. 107-110)"""
    raw, cur, which, started = [], None, 'pjenovac', False
    for page, t in lines(book, range(107, 111)):
        if not started:
            started = 'слједећи борци' in t and 'Шумадијског' in t
            continue
        if t.startswith('На споменику у Пјеновцу'):
            break
        if 'сљедећи борци у 2. непријатељској' in t:
            which, cur = 'offensive', None
            continue
        if t.startswith('Прве пролетерске и Романијског') or t.startswith('У борбама против Нијемаца на подручју'):
            continue
        m = re.match(r'^(\d{1,2})\s*\.\s+(.*)', t)
        if m and (not cur or int(m.group(1)) == cur['no'] + 1):
            cur = {'list': which, 'no': int(m.group(1)), 'page': page, 'parts': [m.group(2)]}
            raw.append(cur)
        elif cur:
            cur['parts'].append(t)
    out = []
    for r in raw:
        text = V.unhyphen(' '.join(r['parts']))
        head, _, rest = text.partition(',')
        words = [w for w in re.split(r'\s+', head.replace('(', ' ').replace(')', ' ')) if w and w not in '–—-']
        caps = [i for i, w in enumerate(words) if re.fullmatch(rf"[{UC}'’]+", w) and len(w) > 1]
        sur_i, giv_i = caps[0], caps[-1]
        last, first = V.name_word(words[sur_i]), V.name_word(words[giv_i])
        fath = father(' '.join(words[sur_i + 1:giv_i])) if giv_i > sur_i + 1 else ''
        nick = V.read_cyr(' '.join(words[giv_i + 1:])) if giv_i + 1 < len(words) else ''
        info = V.read_cyr(rest)
        title = PJENOVAC if r['list'] == 'pjenovac' else OFFENSIVE
        head_text = ' '.join(x for x in (last.upper(), fath, first.upper(), nick) if x)
        e = {'soldier_id': f"{PREFIX}{(0 if r['list'] == 'pjenovac' else 100) + r['no']:06d}",
             'name': ' '.join(x for x in (last, fath, first) if x), 'last_name': last, 'also': [], 'first_name': first,
             'nick': nick, 'fathers_name': fath, 'birth_year': year_of(info),
             'born_in': V.born_in(info, ''), 'survived': False,
             'units': [] if re.search(r'Romanijsk', info) else [1],
             'additional_info': f'{title}: {r["no"]}. {head_text},{info}', 'list': title, 'book_title': TITLE,
             'source_url': viewer_url(book, r['page']), 'source_page': r['page'] - OFFSET}
        if r['list'] == 'pjenovac':
            e.update({'death_year': '1942', 'death_date': '1942-01-21', 'death_place': 'Pjenovac'})
        else:
            e.update(death_fields(info))
        out.append(e)
    return out


START_C = re.compile(rf"^(?:(\d{{1,3}})\s*\.\s*)?([{UC}][{LC}]+(?:\s*[–—-]\s*[{UC}][{LC}]+)?)\s+\(([^)]{{2,30}})\)\s+"
                     rf"([{UC}A-Z][{LC}a-z]+)((?:\s+[{UC}][{LC}]+)?)\s*,\s*ро")
NUMBERED_C = re.compile(rf"^(\d{{1,3}})\s*\.\s*([{UC}][{LC}]+)\s+([{UC}][{LC}]+)\s*(?:,|из\s)")


def fallen(book: dict) -> list[dict]:
    raw, cur, started = [], None, False
    for page, t in lines(book, range(152, 163)):
        if not started:
            started = t.startswith('Погинули борци у Другом')
            continue
        m, n = START_C.match(t), NUMBERED_C.match(t)
        last_no = cur['no'] if cur else 0
        if m and (not m.group(1) or int(m.group(1)) == last_no + 1):
            cur = {'no': last_no + 1, 'page': page, 'names': (m.group(2), m.group(3), m.group(4), m.group(5).strip()),
                   'parts': [t[m.end(5):]]}
            raw.append(cur)
        elif n and int(n.group(1)) == last_no + 1:
            cur = {'no': last_no + 1, 'page': page, 'names': (n.group(2), '', n.group(3), ''),
                   'parts': [t[n.end(3):]]}
            raw.append(cur)
        elif cur:
            cur['parts'].append(t)
    out = []
    for r in raw:
        sur, fath, given, nick = r['names']
        last = '-'.join(V.name_word(x) for x in re.split(r'\s*[–—-]\s*', sur))
        first, fath = V.name_word(given), father(fath)
        nick = V.name_word(nick) if nick else ''
        info = V.read_cyr(re.sub(r'^[,\s]+', '', ' '.join(r['parts'])))
        info = re.split(r'\s*NAPOMENA:', info)[0]           # the author's note after the list's last entry
        head_text = f'{last}{f" ({fath})" if fath else ""} {first}{" " + nick if nick else ""}'
        e = {'soldier_id': f"{PREFIX}{1000 + r['no']:06d}", 'name': ' '.join(x for x in (last, fath, first) if x),
             'last_name': last, 'also': [], 'first_name': first, 'nick': nick, 'fathers_name': fath,
             'birth_year': year_of(info), 'born_in': V.born_in(info, MUNICIPALITY), **death_fields(info),
             'survived': False, 'units': V.units_of(info),
             'additional_info': f'{FALLEN}: {r["no"]}. {head_text}, {info}', 'list': FALLEN, 'book_title': TITLE,
             'source_url': viewer_url(book, r['page']), 'source_page': r['page'] - OFFSET}
        if V.role(info) == 'activist':
            e['role'] = 'activist'
        out.append(e)
    return out


def heroes(book: dict) -> dict[int, tuple[int, str]]:
    """The heroes' list: number -> (scan page, text after the number)"""
    out, cur, skip = {}, None, False
    for page, t in lines(book, range(148, 153)):
        if t.startswith('Погинули борци у Другом'):
            break
        if t.startswith('Поред ратних заслуга'):
            skip = True                                     # the paragraph before the list's living fighters
        if skip:
            skip = not t.rstrip().endswith('дали су:')
            continue
        if re.fullmatch(rf'(?:[{UC}][{LC}]+\s*){{2,4}}', t):
            continue                                        # a photograph's caption ("Светозар Косорић Михајло ...")
        m = re.match(r'^(\d{1,2})\s*\.\s+(.*)', t)
        if m and int(m.group(1)) == (cur or 0) + 1 and int(m.group(1)) in HEROES:
            cur = int(m.group(1))
            out[cur] = [page, [m.group(2)]]
        elif cur:
            out[cur][1].append(t)
    return {k: (p, V.unhyphen(' '.join(parts))) for k, (p, parts) in out.items()}


def main():
    V.corpus()
    book = load(BOOK)
    entries = pjenovac(book) + fallen(book)
    by_list = {('pjenovac', int(e['soldier_id'][-3:])): e for e in entries if e['soldier_id'] < f'{PREFIX}000100'}
    by_list.update({('fallen', int(e['soldier_id'][-6:]) - 1000): e for e in entries if e['soldier_id'] > f'{PREFIX}001000'})
    counts = Counter()
    for no, (page, text) in heroes(book).items():
        last, fath, first, nick, other, survived = HEROES[no]
        # the text after the name: from its first comma (or "rođen") on
        body = V.read_cyr(re.sub(r'^.*?(?=,\s*ро|\s+ро[ђћ]ен)', '', text, count=1)).lstrip(', ')
        head_text = ' '.join(x for x in (first, f'({fath})' if fath else '', last) if x) + (f' – {nick}' if nick else '')
        hero_text = f'{HERO_LIST}: {no}. {head_text}, {body}'
        if other:
            target = by_list[other]
            target['additional_info'] += f'. {hero_text}'
            if not target.get('nick') and nick:
                target['nick'] = nick
            counts['heroes joined to another list'] += 1
            continue
        entries.append({'soldier_id': f'{PREFIX}{200 + no:06d}', 'name': ' '.join(x for x in (last, fath, first) if x),
                        'last_name': last, 'also': [], 'first_name': first, 'nick': nick, 'fathers_name': fath,
                        'birth_year': year_of(body), 'born_in': V.born_in(body, MUNICIPALITY),
                        **(death_fields(body) if not survived else {'death_year': ''}),
                        'survived': survived, 'units': V.units_of(body),
                        'additional_info': hero_text, 'list': HERO_LIST, 'book_title': TITLE,
                        'source_url': viewer_url(book, page), 'source_page': page - OFFSET})
        counts['heroes alone'] += 1
    counts.update(e['list'] for e in entries)
    counts.update(f"role {e.get('role')}" for e in entries)
    OUT.write_text(json.dumps(entries, ensure_ascii=False, indent=1), encoding='utf-8')
    print(len(entries), 'entries ->', OUT.name, dict(counts))


if __name__ == '__main__':
    main()
