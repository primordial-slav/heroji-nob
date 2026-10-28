"""
*Užička gimnazija 1839-1989* (Stevan Ignjić, Milutin Pašić, Vojislav Lazović, Dragutin Korać; Titovo Užice 1989; doc
00008615 of the Poreklo library), a book across units: "Učenici, profesori i bivši učenici užičke Gimnazije poginuli u
narodnooslobodilačkoj borbi od 1941. do 1945. godine" (scan pp. 300-320), in Cyrillic, two numbered lists, the
teachers and staff (1-8) and the pupils and former pupils (1-252), a bio each:

    "7. Бакочевић Р. Бранислава, ученица, рођена је 4. маја 1923. године у Мокрој Гори код Ужица. Погинула је ..."

The list counts those the occupier shot or who died in its camps with the fallen fighters: by the mixed lists' rule
(`_village_books.role`) the fighters go in as such, the movement's people as activists, and those the entry names
with no more than the list's title `role: 'participant'`. The footnotes at the pages' feet, in smaller type, are
dropped from the first line that opens with its number ("227 На РС, књ. I").

The OCR reads д as у in some given names ("Рауомир", "Алексануар") and sets a few in Latin look-alikes ("Muogpai"):
a name the site lacks is tried with д for у.

Output: data-extraction/poreklo/uzicka-gimnazija-entries.json (IDs 9114xxxxxx: the teachers from 000001, the pupils
from 001001, by the book's numbers).
Usage: python data-extraction/parse_uzicka_gimnazija.py
"""
from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path
from statistics import median

sys.stdout.reconfigure(encoding='utf-8')
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import _village_books as V  # noqa: E402
from _parser_scaffold import cyrillic_to_latin as latin  # noqa: E402
from parse_ostrvica import level_lines  # noqa: E402
from poreklo_text import load, page_words, viewer_url  # noqa: E402

BOOK = 'uzicka-gimnazija.json'
OUT = HERE / 'poreklo' / 'uzicka-gimnazija-entries.json'
PREFIX = '9114'
OFFSET = 3                                   # scan page minus the book's page (scan 300 is p. 297)
PAGES = range(300, 321)
TITLE = 'Užička gimnazija 1839-1989'
LIST = 'Učenici, profesori i bivši učenici užičke Gimnazije poginuli u narodnooslobodilačkoj borbi od 1941. do 1945. godine'
TEACHERS, PUPILS = 'Profesori i drugi radnici Gimnazije poginuli u NOB', 'Učenici i bivši učenici Gimnazije poginuli u NOB'
CU, CL = 'А-ЯЂЈЉЊЋЏ', 'а-яђјљњћџ'
W = rf'[{CU}][{CL}A-Za-z]+'
ENTRY = re.compile(rf'^(\d{{1,3}})\s*\.\s*({W}(?:\s*-\s*{W})?)\s+(?:([{CU}A-Z][.,)]|[{CU}]{{1,2}}\))\s*)?(?:([гд][рp])\s+)?(\S+?)\s*,\s*(.*)$')
# headings the OCR garbled past the pattern, as the page reads them: dr Frida Gutman of the Centralna bolnica, the
# father's initial of Bjelović-Barački read as "73.", Bogdanović's "љ." (Ljubomir's)
FIX = {'7. ГуШман gp Фрауела Фриуа,': '7. Гутман др Фрида,', 'Бјеловић Барачки 73. Милка': 'Бјеловић-Барачки Милка',
       'Богуановић љ. Славка': 'Богдановић Љ. Славка', '39. Давиуоваи, Ж. HeHag,': '39. Давидовић Ж. Ненад,',
       '142. Миловановић В. љубоураг рођен': '142. Миловановић В. Љубодраг, рођен', 'Г аврило': 'Гаврило',
       '141. Миловановић В. bečogpai je рођен': '141. Миловановић В. —, рођен',     # his given name past reading
       'Слобоуан Секулић, Поручник': 'Слободан Секулић, Поручник'}                # a photo's caption
# names the OCR set in Latin look-alikes (у and g for д, p for р, m and w for ш), as the letters read; the unclear
# ones ("Drašć", "Doiuća") stay as printed
NAME_FIX = {'Nauežua': 'Nadežda', 'O/zia': 'Olga', 'Iipegpaf': 'Predrag', 'Hpegpai': 'Predrag', 'Pagom': 'Radoš',
            'Paguwa': 'Radiša', 'Dratoljub': 'Dragoljub', 'Drajan': 'Dragan', 'Alaksanuar': 'Aleksandar',
            'Grujiia': 'Grujica', 'C/mčogau': 'Slobodan', 'Hop/]e': 'Đorđe', 'Rauulovački': 'Radulovački',
            'Ječmeniia': 'Ječmenica', 'Šaionjić': 'Šaponjić'}
# a fighter, though the mixed lists' rule would not say so: he fell in battle, or the bio names a unit or a duty in one
FOUGHT = re.compile(r'\bu borbi\b|\bpartizan|\bodred|\bbrigad|\bbataljon|\bčet[ieu]\b|\bkomandant|\bkomesar|\bborac\b|'
                    r'\bpilot|\bdivizij|\bkurir', re.I)
# an entry glued on after a full stop: its number lost or garbled, a small initial ("љ."), a name in capitals
GLUED = re.compile(r'(?<=[.])\s+(?=(?:\d{1,3}\s*\.\s*)?[А-ЯЂЈЉЊЋЏA-Z][А-Яа-яђјљњћџЂЈЉЊЋЏ0-9A-Za-z]+\s+'
                   r'(?:[\'"]?[А-ЯЂЈЉЊЋЏA-Z0-9][љњ]?\)?|[љњ])\.\s+'
                   r'(?:\S+?,\s*(?:учени|студент|учитељ|професор|рођен|радник|службеник|трговачки|свршени|питомац|'
                   r'судија|адвокат|земљорадник|правник|инжењер|штампарски)|\S+\s+је\s+рођен))')
LENIENT = re.compile(r'^(?:(\d{1,3})\s*\.\s*)?(\S+)\s+(\S+)\s+(\S+?)(?:,|\s+(?=је\s+рођен))\s*(.*)$')
# a photo's caption set between the entries, the given name first ("Душан Вишић, студент", "Добросав Симић, адвокатски
# приправник"): cut off where a name the site knows as a given name opens it
CAPTION = re.compile(r"(?<=[.])\s+[·•]?\s*([А-ЯЂЈЉЊЋЏ][а-яђјљњћџ]+)\s+['\"]?([А-ЯЂЈЉЊЋЏ][а-яђјљњћџ]+),\s")
LATIN_LOOK = str.maketrans({'M': 'М', 'u': 'и', 'o': 'о', 'g': 'д', 'p': 'р', 'a': 'а', 'i': 'г', 'b': 'б', 'e': 'е',
                            'c': 'с', 'y': 'у', 'x': 'х', 'O': 'О', 'P': 'Р', 'H': 'Н', 'K': 'К', 'T': 'Т', 'B': 'В',
                            'A': 'А', 'E': 'Е', 'C': 'С', 'X': 'Х', 'l': 'л', 'z': 'з', '/': ''})


def known(cyr: str, given: bool) -> int:
    table = V.T._given if given else V.T._names
    return table[latin(cyr.upper())]


def name(word: str, given: bool) -> str:
    """a name as the site knows it: as printed, else in Cyrillic for Latin look-alikes, else with д for у"""
    w = re.sub(r"['’`.,;:]", '', word)
    tries = [w, w.translate(LATIN_LOOK)]
    tries += [t[:i] + 'д' + t[i + 1:] for t in list(tries) for i, c in enumerate(t) if c == 'у' and i > 0]
    best = max(tries, key=lambda t: known(t, given))
    best = best if known(best, given) else w
    return V.given_word(best) if given else V.name_word(best)


def main():
    V.corpus()
    book = load(BOOK)
    raw, part = [], None
    for page in PAGES:
        words = page_words(book, page)
        if not words:
            continue
        body = median(w.height for w in words)
        for l in level_lines(words):
            t = l.text.strip()
            if not t or re.fullmatch(r'[\d\s.]{1,5}', t):
                continue
            if re.match(r'^\d{3}\s+\S', t):
                break                                           # the page's footnotes ("227 На РС, књ. I")
            for a, b in FIX.items():
                t = t.replace(a, b)
            t = re.sub(rf'([{CL}])! ([{CL}])', r'\1г\2', t)               # "Дра! ољуб": the OCR's "! " for г
            t = re.sub(rf'^(\d{{1,3}}\.\s*[{CU}][{CL}]+\s+[{CU}])\s+([{CL}])', lambda x: x.group(1) + '. ' + x.group(2).upper(), t)
            if re.match(r'^Професори и', t):
                part = TEACHERS
                continue
            if re.match(r'^Ученици и бивши', t):
                part = PUPILS
                continue
            m = ENTRY.match(t)
            if part and m and (not raw or raw[-1]['part'] != part or 0 < int(m.group(1)) - raw[-1]['no'] <= 6):
                raw.append({'part': part, 'no': int(m.group(1)), 'page': page, 'm': m.groups(), 'lines': []})
            elif raw and part:
                raw[-1]['lines'].append(t)
    split = []                                  # the entries a heading the OCR garbled left glued on, split off
    for r in raw:
        s = ' '.join([r['m'][-1]] + r['lines'])
        for c in CAPTION.finditer(s):
            if known(c.group(1), True) >= 20 and re.search(r'(?:ић|ски|ац|ин|ов|ица)$', c.group(2)):
                nxt = GLUED.search(s, c.end())
                s = s[:c.start()] + (' ' + s[nxt.start():] if nxt else '')
                break
        bounds = [0]
        for m in GLUED.finditer(s):             # a cut, four words or more after the one before (not "71." alone)
            if len(s[bounds[-1]:m.start()].split()) >= 4:
                bounds.append(m.start())
        bounds.append(len(s))
        r['m'] = r['m'][:-1] + (s[:bounds[1]].strip(),)
        r['lines'] = []
        split.append(r)
        for a, b in zip(bounds[1:-1], bounds[2:]):
            m = LENIENT.match(s[a:b].strip())
            if not m:
                print('  not split:', s[a:b][:80])
                continue
            no = int(m.group(1)) if m.group(1) else split[-1]['no'] + 1
            split.append({'part': r['part'], 'no': no, 'page': r['page'], 'lines': [],
                          'm': (str(no), m.group(2), m.group(3), None, m.group(4), m.group(5))})
    raw = split
    out, counts = [], Counter()
    for r in raw:
        _, sur, initial, title, given, rest = r['m']
        last = '-'.join(name(x, False) for x in re.split(r'\s*-\s*', sur))
        first = name(given, True) if given != '—' else ''
        last, first = NAME_FIX.get(last, last), NAME_FIX.get(first, first)
        fath = latin(initial.rstrip('.,)') + '.') if initial else ''
        info = V.read_cyr(' '.join([rest] + r['lines'])).strip()
        info = re.sub(r'(?<=\.)\s*[:!”"\']*\d{2,3}\b', '', info)          # a footnote's mark ("godine.227")
        printed = ' '.join(x for x in (last, fath, 'dr' if title else '', first) if x)
        text = f"{printed}, {info}"
        role = V.role(text)
        if role and FOUGHT.search(text):
            role = None                         # "Poginuo je u borbi protiv Nemaca", "partizanski pilot"
        if role == 'out':
            role = 'participant'
        d = V.death(text)
        born = re.search(r'\bro[đd]en[a]?\s+(?:je\s+)?(?:\d{1,2}\.\s*\w+\s+)?(1[89]\d\d)', info)
        place = re.search(r'\bro[đd]en[a]?\s+(?:je\s+)?(?:\d{1,2}\.\s*\w+\s+)?1[89]\d\d\.?\s*(?:godine\s*)?,?\s*(?:u|na|y)\s+'
                          r'([A-ZČĆŽŠĐ][\w-]*(?:\s+[A-ZČĆŽŠĐ][\w-]*){0,2}?)(?=\s*[.,;]|\s+(?:kod|na|u)\b)', info)
        base = 0 if r['part'] == TEACHERS else 1000
        rec = {'soldier_id': f"{PREFIX}{base + r['no']:06d}", 'name': ' '.join(x for x in (last, fath, first) if x),
               'last_name': last, 'also': [], 'first_name': first, 'nick': '', 'fathers_name': fath,
               'birth_year': born.group(1) if born else '', 'born_in': place.group(1) if place else '',
               'death_year': d.get('year', ''), **({'death_date': d['date']} if d.get('date') else {}),
               **({'death_place': d['place']} if d.get('place') else {}),
               'survived': False, 'units': V.units_of(text), **({'role': role} if role else {}),
               'additional_info': f"{LIST}, {r['part']}: {r['no']}. {text}", 'list': LIST, 'book_title': TITLE,
               'source_url': viewer_url(book, r['page']), 'source_page': r['page'] - OFFSET}
        out.append(rec)
        counts[(r['part'] == TEACHERS and 'teacher ' or '') + (role or 'fighter')] += 1
    nos = [r['no'] for r in raw if r['part'] == PUPILS]
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding='utf-8')
    print(len(out), 'entries ->', OUT.name, dict(counts), 'pupils missing',
          sorted(set(range(1, max(nos) + 1)) - set(nos)) if nos else '')
    for r in out:
        if not known(r['last_name'], False) or not known(r['first_name'], True):
            print('  unknown name:', r['soldier_id'], r['name'], '|', r['additional_info'].split(': ', 1)[1][:90])


if __name__ == '__main__':
    main()
