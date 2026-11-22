"""
*Црна Трава и Црнотравци* (Radomir Kostadinović, the Crna Trava SUBNOR, 1966?; Poreklo library, doc 00006272), a book
across units: its lists at the end (scan pp. 496-511, book pp. 524-539), in Cyrillic:

    "Народни хероји поникли из Црнотравског (Другог јужноморавског) одреда" (p. 524): twelve, a line each;
    "Они који су у наше данас и сутра уградили своје животе" (pp. 525-538): the dead of the war by village, numbered,
        "Анђелковић Ј. Дејан 1944. Брод", the fighters first ("Погинули од:" whom, where, the unit: "Симоновић В.
        Давид 1945. Немаца Срем XII бригада"), then each village's "Жртве фашистичког терора" ("ЖФТ"), which are out;
        a village with no list of victims after it mixes them in, and its entries that name no unit and that the
        census does not count among the fighters are out too (`MIXED`); so are the April war's dead and prisoners
        (`APRIL_WAR`). Each fallen man's death is in his entry's fields (how, the day where printed, the place before
        his unit), which build_ostali_borci.py takes as a column book's, since the line has no verb;
    the holders of the Spomenica 1941 (p. 539), names in two columns.

The OCR reads Д and Л as А ("Аејан" Dejan, "ВАадичин" Vladičin): each word of a name is read as the variant the
site's names know best (`best`). It garbled five village headings (`HEADINGS`: Brod's, whose 52 fighters were read
as victims until 2026-11-22, Dobro Polje's, Kozilo's, Darkovce's, Jabukovik's).

Output: data-extraction/poreklo/crna-trava-entries.json (IDs 9125xxxxxx: the heroes 000001-000012, the fallen from
001001 in the list's order, the spomenica's holders from 002001). The fallen keep the numbers the last run gave them
(`keep_numbers`): an entry read since is numbered after the last, one no longer read leaves its number unused.
Usage: python data-extraction/parse_crna_trava.py
"""
from __future__ import annotations

import itertools
import json
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import _village_books as V  # noqa: E402
from _parser_scaffold import cyrillic_to_latin as latin  # noqa: E402
from poreklo_text import load, page_lines, viewer_url  # noqa: E402

BOOK = 'crna-trava.json'
OUT = HERE / 'poreklo' / 'crna-trava-entries.json'
PREFIX = '9125'
OFFSET = -28                                 # scan page minus the book's page (scan 496 is p. 524)
TITLE = 'Crna Trava i Crnotravci'
HEROES = 'Narodni heroji ponikli iz Crnotravskog (Drugog južnomoravskog) odreda'
FALLEN = 'Oni koji su u naše danas i sutra ugradili svoje živote'
SPOMENICA = 'Nosioci „Spomenice 1941”'
MUNICIPALITY = 'Crna Trava'
CU, CL = 'А-ЯЂЈЉЊЋЏ', 'а-яђјљњћџ'
CONF = {'А': 'АДЛ', 'Б': 'БЂ', 'ћ': 'ћђ', 'Ћ': 'ЋЂ', 'Н': 'НЛ', 'д': 'дл'}
VILLAGE_READ = {'Maačište I Bajince': 'Mlačište i Bajince', 'Kaana I Krivi Aea': 'Kalna i Krivi Del',
                'Pavaičine': 'Pavličine', 'Krstibevo': 'Krstićevo', 'G R A A S K A': 'Gradska'}


def variants(word: str):
    choices = [CONF.get(c, c) if c.isupper() or c in 'ћд' else c for c in word]
    n = 1
    for c in choices:
        n *= len(c)
    return [word] if n > 512 else [''.join(p) for p in itertools.product(*choices)]


def best(word: str, part: str) -> str:
    word = word.strip('.,;:\'"“)(')
    if not word:
        return ''
    if re.search(r'\s*[-–]\s*', word):                     # "Стојичић-Филиповић", "Синадиновић – Гигић"
        return '-'.join(best(x, part) for x in re.split(r'\s*[-–]\s*', word) if x)
    word = re.sub(r'нћ$', 'ић', word.replace('Аоуб', 'Љуб').replace('ии', 'ин'))   # "Аоубомир", "Аоубнћ"
    table = V.T._names if part == 'last' else V.T._given
    top = max(variants(word), key=lambda c: (table[latin(c.upper())], -sum(a != b for a, b in zip(c, word))))
    return latin(top[0] + top[1:].lower()) if table[latin(top.upper())] else latin(word[0] + word[1:].lower())


def fix_text(t: str) -> str:
    """the duty and place as printed, the OCR's А for Д and Л inside words put back"""
    t = re.sub(rf'(?<=[{CL}])А(?=[{CL}])', 'л', t)                                   # "ВАадичин"
    t = re.sub(r'\bА(?=[аеиоуј])', 'Д', t)                                             # "Аејан", "Аимитријевић"
    return t.replace('сеАо', 'село').replace('сеАу', 'селу')


def lines(book: dict, page: int, columns: int = 1):
    for col in page_lines(book, page, columns):
        for l in col:
            t = l.text.strip()
            if t and not re.fullmatch(r'\d{3}', t):
                yield t


# an entry of the fallen: its number, surname, the father's initial ("Ао." is Lj.), the given name (and a second: the
# name he was called by, or Jabukovik's given name after the father in full), the day and month where printed ("16.4.",
# "10.V", "22. XII", or the month alone: "10. 1942."), the year ("44." after a day and month; the OCR's "11944.",
# "'1944.") and the rest: who killed him, where, his unit
NAME = rf'[{CU}][{CU}{CL}]+(?:\s*[-–]\s*[{CU}][{CU}{CL}]+)?'
ENTRY = re.compile(rf'^\W*(\d{{1,3}})?\s*\.?\s*({NAME})\s+(?:([{CU}А][{CL}]?)\.\s*)?([{CU}][{CU}{CL})]+)(?:\s+([{CU}][{CL}]+))?'
                   rf'\s+[^\w\s]?\s*(?:(\d{{1,2}})\s*\.\s*)?(?:(1[0-2]|0?[1-9])\s*\.\s*|([XIVLХПV]+)\s*\.?\s*)?'
                   rf'1?(19[34]\d|4[1-6])\.?-?\s*(.*)$')
# an entry the list prints without a year, his unit after the name ("Stefanović A. Milorad 23. divizija")
NO_YEAR = re.compile(rf'^\W*(\d{{1,3}})?\s*\.?\s*({NAME})\s+(?:([{CU}А][{CL}]?)\.\s*)?([{CU}][{CU}{CL})]+)\s+(\D{{6,}})$')
ROMAN = str.maketrans({'Х': 'X', 'П': 'II', 'І': 'I'})
# lines the OCR or the layout broke: the Latin "Ao." of Lj., a given name read with a small "љ", "3." for the initial З.,
# and Bankovci's first entry, its year wrapped to the next line under the place
LINE_FIX = [(' Ao. ', ' Ао. '), (re.compile(r'(?<=\s)љ(?=[а-яђјљњћџ])'), 'Љ'), (re.compile(r'(?<=\s)3\.(?=\s)'), 'З.'),
            ('Братисдав 14. ХП Немаца Сјеница 12. бригада 22. 1944. дивизија',
             'Братисдав 14. ХП 1944. Немаца Сјеница 12. бригада 22. дивизија')]
# the April war of 1941 and its prisoners, no war of the NOB (the line's "biv. jug. voj.", "biv. JV", "(bombard)"; the
# others read against the census, 2026-11-22): Nikolić J. Toma, 1941 at Niš (the census's Nikačić (Jovanče) Tomo, "u
# aprilskom ratu"), Ranđelović K. Milan, 1941 in Belgrade (the same), Momčilović J. Čedomir, 1942 in Germany (its
# "kao zarobljeni pripadnik VKJ", a stalag), Nedeljković S. Dragoljub, 1941 in Germany
APRIL_WAR = re.compile(r'biv\.\s*j|\(bombard', re.I)
APRIL_MEN = {('nikolic', 'toma', 'J'), ('randjelovic', 'milan', 'K'), ('momcilovic', 'cedomir', 'J'),
             ('nedeljkovic', 'dragoljub', 'S')}
GIVEN_READ = {'Aragosavka': 'Dragosavka', 'Vitomr': 'Vitomir', 'Midtena': 'Miltena'}
# the village headings the OCR garbled, as it reads them (Brod's: two lines of noise over its "Poginuli od:")
HEADINGS = {'в [·1) ;\\': 'Brod', 'A 0 Б Р О П O lb E': 'Dobro Polje', 'К O 3 И А 0': 'Kozilo',
            'ААРК 0 B Ц Е': 'Darkovce', 'с. Ј АБУКОВИК': 'Jabukovik', 'П Р Е С А А П': 'Preslap'}
# the villages the list gives without a list of their own victims of terror after them (Crna Trava's, Brod's,
# Darkovce's, Jabukovik's, Gradska's, Kalna's) or a mark on them (Gornje Gare's and Preslap's "(ŽFT)"): their fallen and
# their victims stand in one list, killed "Bugara Bajince", "Bugara Pavličine", "Bugara Kozilo, streljan"; the census
# counts 31 of those it names as victims of terror and 4 as fighters (2026-11-22)
MIXED = {'Mlačište i Bajince', 'Rupnje', 'Rajčetine', 'Pavličine', 'Bankovci', 'Ostrozub', 'Dobro Polje', 'Bistrica',
         'Kozilo', 'Krstićevo'}
# an entry that names his unit or duty ("12. brigada", "7. br. 23. div.", "Crnotravski odred", "II juž. m. od.",
# "komanda mesta", "biv. jug. voj.", "N. milicije", "poz. radnik", "Samost. bataljon", "Proleterska", "3/12 br.")
UNIT = re.compile(r'brig|\bbr\b|\bbr\.|div|\bd\.|odred|\bod\.|JMO|\bMO\b|bataljon|milicij|kom[na]+da|biv\.|radnik|'
                  r'Proleter|\d/\d+|\b\d{1,2}\s*\.?\s*6\b|\b\d{1,2}\.\s*0\.\s*br', re.I)
KILLER = re.compile(r'^(?:Bugara|Nemaca|Četnika|Šiptara|balista|Balista|dražićevaca|Ustaše|Od bolesti|umro)\s*', re.I)
# the place of death ends at a comma or where the unit begins
PLACE_END = re.compile(r',|\s+(?=\d{1,2}\s*\.|\d/\d|(?:I|II|III|VII|XII)\s|Crn(?:otrav)?\.?\s*(?:odred|od\.)|'
                       r'Crnotravski|Babički|kom[na]+da|biv\.|N\. mil|Samost|Proleter|Drugi|AJMO|JMO|po[dz]\.?\s+radnik|'
                       r'\(Ž)')
PLACE_READ = {'Sar aj evo': 'Sarajevo', 'Saraj evo': 'Sarajevo', 'Prede j ane': 'Predejane', 'Prdejane': 'Predejane',
              'de j ićevo': 'Dejićevo', 'De j ićevo': 'Dejićevo', 'Bsanski Brod': 'Bosanski Brod',
              'Kragoujevac': 'Kragujevac', 'Rruplje': 'Ruplje', 'Mlačšcte': 'Mlačište', 'Ki jevac': 'Kijevac',
              'Kosi/mo': 'Kozilo', 'Lipov.': 'Lipovica', 'Knjaž.': 'Knjaževac', 'Bostut': 'Bosut', 'Bjeljina': 'Bijeljina',
              '.Ilpha Trava': 'Crna Trava', 'Darkovcu': 'Darkovce', 'Bukvik': 'Bukovik', 'Vinkovi': 'Vinkovci',
              'Konop.': 'Konopnica', 'K. Mitrovica': 'Kosovska Mitrovica', 'N. Pazar': 'Novi Pazar',
              'B. Potok': 'Beli Potok', 'V. Plana': 'Velika Plana', 'G. Gare': 'Gornje Gare', 'G. Han': 'Grdelica',
              'Nip': 'Niš', 'Suva plannna': 'Suva planina', 'Vdasiia': 'Vlasina'}


def fold(s: str) -> str:
    return re.sub('[\u0300-\u036f]', '', unicodedata.normalize('NFD', (s or '').lower().replace('đ', 'dj')))


def census_fighters() -> dict[tuple, set]:
    """(surname, given name, the father's initial) -> the years of death of the census's fighters born in the
    municipality (its entries are the fighters only: "u NOBu", "u NORu", captured partisans)"""
    out: dict[tuple, set] = {}
    for e in json.loads((HERE / 'zrtve-rata' / 'zrtve-rata-1964-srb-entries.json').read_text(encoding='utf-8')):
        if e['born_in'] == MUNICIPALITY or e['born_in'].endswith(', ' + MUNICIPALITY):
            for f in {(e['fathers_name'] or ' ')[:1], ''}:
                out.setdefault((fold(e['last_name']), fold(e['first_name']), f), set()).add(e['death_year'])
    return out


def death_fields(rest: str, day, month, year: str) -> dict:
    """The death the line gives: how (shot, died of illness, else fell), the day where printed, and the place before
    his unit: "Bugara Predejane 12. brigada" Predejane, "Nemaca Bosut 7. brigada" Bosut, "Bugara Kozilo, streljan" """
    kind = ('streljan' if re.search(r'\bstreljan', rest) else
            'umro' if re.search(r'\bumr|od bolesti', rest, re.I) else 'poginuo')
    place = PLACE_END.split(KILLER.sub('', rest.strip(' ,.')), 1)[0].strip(' ,.—–-„"')
    place = re.sub(r'^(?:u|na)\s+(?=[A-ZČĆŽŠĐ])|\s+umro$', '', place)
    place = PLACE_READ.get(place, place)
    if (not re.search(r'[a-zčćžšđ]{3}', place) or re.match(r'\d', place)
            or re.fullmatch(r'Bugara|Nemaca|Četnika|Šiptara', place)):
        place = ''
    out = {'death_type': kind, 'death_place': place}
    if year and day and month and month.isdigit():
        out['death_date'] = f'{year}-{int(month):02d}-{int(day):02d}'
    return {k: v for k, v in out.items() if v}


def keep_numbers(out: list[dict]) -> None:
    """The fallen's IDs as the last run gave them, by page and name (Ostali borci's records and the references hold
    them); an entry read since (Brod's fighters, under a heading the OCR garbled; the dates of a month alone) gets the
    next free number, and an entry no longer read (a victim of terror) leaves its number unused"""
    key = lambda e: (e['source_page'], fold(e['last_name']), fold(e['first_name']), (e['fathers_name'] or '')[:1])
    had = defaultdict(list)
    if OUT.exists():
        for e in json.loads(OUT.read_text(encoding='utf-8')):
            if e['list'] == FALLEN:
                had[key(e)].append(e['soldier_id'])
    nxt = max([int(i[4:]) for ids in had.values() for i in ids], default=1000) + 1
    taken = set()
    for e in out:
        if e['list'] != FALLEN:
            continue
        old = [i for i in had.get(key(e), ()) if i not in taken]
        if old:
            e['soldier_id'] = old[0]
        else:
            e['soldier_id'] = f'{PREFIX}{nxt:06d}'
            nxt += 1
        taken.add(e['soldier_id'])


def fallen_lines(book: dict, page: int):
    """A page's lines, an entry whose year the layout wrapped to the next line joined to it"""
    ls = list(lines(book, page))
    i = 0
    while i < len(ls):
        t = ls[i]
        if (i + 1 < len(ls) and re.match(r'^\W*\d{1,3}\s*\.', t) and not re.search(r'19[34]\d|\b4[1-6]\.', t)
                and re.match(r'^\s*1?19[34]\d', ls[i + 1])):
            t, i = f'{t} {ls[i + 1]}', i + 1
        for a, b in LINE_FIX:
            t = a.sub(b, t) if hasattr(a, 'sub') else t.replace(a, b)
        yield t
        i += 1


SPOM = re.compile(rf'(\d{{1,2}})\s*\.?\s*([{CU}][{CU}{CL}]+(?:\s*[-–]\s*[{CU}][{CU}{CL}]+)?)\s+(?:([{CU}А])\.\s*)?'
                  rf'([{CU}][{CU}{CL}]+)')


def main():
    V.corpus()
    book = load(BOOK)
    entries, counts = [], Counter()
    # the heroes (scan 496); Živojin Nikolić Brka, whose surname the OCR lost ("Hmm/mh") and whose lines had run into
    # Pavlović's, was found after the numbers were given (2026-11-22): he is numbered after the last
    n, late = 0, []
    for t in lines(book, 496):
        t = t.replace('Hmm/mh', 'Николић').replace('Бићко', 'Ћићко').replace(' љуба,', ' Љуба,')
        m = re.match(rf'^\W*(\d{{1,2}})?\s*\.?\s*([{CU}][{CL}]+)\s+([{CU}][{CL}]+)(?:\s+([{CU}][{CL}]+))?\s*[,.]?\s*(.*)$', t)
        if not m or 'НАРОАНИ' in t or 'поникди' in t:
            if entries and entries[-1]['list'] == HEROES and t and not re.match(r'^\W*\d', t):
                entries[-1]['_text'] += ' ' + t
            continue
        given, last, nick = best(m.group(2), 'first'), best(m.group(3), 'last'), latin(m.group(4)) if m.group(4) else ''
        e = {'last_name': last, 'first_name': given, 'nick': nick, 'fathers_name': '', '_text': fix_text(m.group(5)),
             'list': HEROES, 'page': 496, 'born_in': ''}
        if last == 'Nikolić' and given == 'Živojin':
            late.append(e)
        else:
            n += 1
            e['soldier_id'] = f'{PREFIX}{n:06d}'
        entries.append(e)
    for e in late:
        n += 1
        e['soldier_id'] = f'{PREFIX}{n:06d}'
    # the fallen (scan 497-511)
    fighters = census_fighters()
    village, victims, prev = MUNICIPALITY, False, ''
    for page in range(497, 512):
        for t in fallen_lines(book, page):
            bare = re.sub(rf'[^{CU} ]', '', t).strip()
            if 'ЖРТВЕ' in t or 'ЖФТ' in t or 'ЖТФ' in t:     # a list of victims, or an entry marked as one ("(ŽFT)")
                victims = True
                continue
            if t.strip() in HEADINGS:
                village, victims = HEADINGS[t.strip()], False
                continue
            if bare and bare == t.strip() and len(bare) > 3 and not re.search(r'\d', t) and 'ОНИ' not in bare:
                village, victims = latin(bare.title()), False
                village = VILLAGE_READ.get(village, village)
                continue
            if 'Имена 32 бораца' in t or 'Споменике' in t:
                break
            m = ENTRY.match(t)
            if m:
                no, last, init, given, extra, day, month, roman, year, rest = m.groups()
                month = month or (roman.translate(ROMAN) if roman else None)
                if len(year) == 2 and not month:             # "44." only after a day and month ("16.10. 44.")
                    continue
                year = year if len(year) == 4 else f'19{year}'
            else:
                m = NO_YEAR.match(t)
                if not m or not UNIT.search(V.read_cyr(m.group(5))):
                    continue
                (no, last, init, given, rest), extra, day, month, year = m.groups(), None, None, None, ''
            if victims:
                counts['victims out'] += 1
                continue
            # Jabukovik prints the father in full, in the genitive ("Ilić Dobrosava Ranđel"); a second given name
            # elsewhere is what he was called ("Sokolović N. Dragoljub Joca")
            nick = ''
            if extra and not init and village == 'Jabukovik':
                father, given = best(given, 'first'), extra
            else:
                father = 'Lj' if init == 'Ао' else latin(init.replace('А', 'Д')) if init else ''
                nick = best(extra, 'first') if extra else ''
            last_l, given_l = best(last, 'last'), best(given, 'first')
            father, given_l = GIVEN_READ.get(father, father), GIVEN_READ.get(given_l, given_l)
            rest = V.read_cyr(fix_text(rest)).strip()
            if rest.strip(' .') in ('„', '"'):                  # ditto: the place and unit of the line above
                rest = prev
            prev = rest
            fields = death_fields(rest, day, month, year)
            if APRIL_WAR.search(rest) or (fold(last_l), fold(given_l), father[:1]) in APRIL_MEN:
                counts['the April war out'] += 1
                continue
            # a village whose list has no victims of its own after it mixes them in: an entry that names no unit and
            # that the census does not count among the fighters is one of its victims of terror (the census counts 31
            # such entries it names as victims, 4 as fighters)
            if (village in MIXED and not UNIT.search(rest)
                    and not (year and fighters.get((fold(last_l), fold(given_l), father[:1]), set())
                             & {year, str(int(year) - 1), str(int(year) + 1)})):
                counts['victims out (no unit, not a fighter in the census)'] += 1
                continue
            date = ((f'{int(day)}. ' if day else '') + (f'{month}. ' if month and not month.isdigit() else
                                                        f'{int(month)}. ' if month else '') + (f'{year}.' if year else '')).strip()
            when = ' '.join(x for x in (date, rest) if x)
            e = {'last_name': last_l, 'first_name': given_l, 'nick': nick, 'fathers_name': father, 'death_year': year,
                 'list': FALLEN, 'page': page, 'survived': False,
                 '_text': f"{no + '. ' if no else ''}{last_l} {father + '. ' if father and len(father) < 3 else ''}"
                          f"{given_l}{' ' + nick if nick else ''}, {when}".strip(),
                 'born_in': f'{village}, {MUNICIPALITY}' if village != MUNICIPALITY else MUNICIPALITY,
                 '_village': village, **fields}
            if len(father) > 2:                               # the full father of Jabukovik's: "Ilić (Dobrosava) Ranđel"
                e['_text'] = f"{no + '. ' if no else ''}{last_l} ({father}) {given_l}, {when}".strip()
            if re.search(r'\bpo[dz]\.?\s+radnik', rest):    # "pozadinski radnik": a man of the movement, no fighter
                e['role'] = 'activist'
            entries.append(e)
            counts['fallen'] += 1
    # the spomenica (scan 511, two columns run into one line)
    on, n = False, 0
    for t in lines(book, 511):
        if 'Имена 32' in t:
            break
        on = on or bool(re.match(r'^\W*\d', t))
        for m in SPOM.finditer(t):
            last, init, given = m.group(2), m.group(3), m.group(4)
            n += 1
            last_l, given_l = best(last, 'last'), best(given, 'first')
            father = latin(init.replace('А', 'Д')) if init else ''
            entries.append({'soldier_id': f'{PREFIX}{2000 + int(m.group(1)):06d}', 'last_name': last_l,
                            'first_name': given_l, 'nick': '', 'fathers_name': father, 'list': SPOMENICA, 'page': 511,
                            '_text': f"{m.group(1)}. {last_l} {father + '. ' if father else ''}{given_l}",
                            'survived': True, 'born_in': ''})
            counts['spomenica'] += 1
    for e in entries:
        if e['list'] == HEROES:
            e['survived'] = not re.search(r'[Пп]о[–-]?\s*гин', e['_text'])   # the whole paragraph ("По– гинуо")
    # (the fallen get their numbers after the join: keep_numbers)
    for i, e in enumerate(x for x in entries if x['list'] == FALLEN):
        e['soldier_id'] = f'P{i}'
    # a hero who fell is in the list of the fallen too ("85. Sotirović V. Mirko, 1943. Duga Luka"): one man, the
    # second entry joined to his first, its number left unused
    joined = {}
    for h in [e for e in entries if e['list'] == HEROES and not e['survived']]:
        same = [e for e in entries if e['list'] == FALLEN and e['last_name'] == h['last_name'] and
                e['first_name'] == h['first_name']]
        if len(same) == 1:
            joined[same[0]['soldier_id']] = h['soldier_id']
    seen, out = set(), []
    for e in entries:
        if e['soldier_id'] in seen:
            continue
        seen.add(e['soldier_id'])
        info = (e['_text'] if e['list'] != HEROES else V.read_cyr(e['_text']).strip()).rstrip(' .')
        d = V.death(info) if e['list'] == HEROES else {}
        born = re.search(r'rođen[a]?\s+(?:\d{1,2}\.\s*\S+\s+)?(1[89]\d\d)', info)
        name = ' '.join(x for x in (e['last_name'], e['fathers_name'], e['first_name']) if x)
        out.append({'soldier_id': e['soldier_id'], 'name': name, 'last_name': e['last_name'], 'also': [],
                    'first_name': e['first_name'], 'nick': e['nick'], 'fathers_name': e['fathers_name'],
                    'birth_year': born.group(1) if born else '', 'born_in': e['born_in'],
                    'death_year': e.get('death_year') or d.get('year', ''),
                    'survived': e['survived'], 'units': V.units_of(info),
                    'additional_info': f"{e['list']}{', ' + e['_village'] if e.get('_village') else ''}: {info}.",
                    'list': e['list'], 'book_title': TITLE, 'source_url': viewer_url(book, e['page']),
                    'source_page': e['page'] - OFFSET,
                    **{k: e[k] for k in ('death_type', 'death_date', 'death_place', 'role') if e.get(k)}})
    by_id = {e['soldier_id']: e for e in out}
    for fid, hid in joined.items():
        f, h = by_id.pop(fid), by_id[hid]
        h['additional_info'] += ' ' + f['additional_info']
        h['death_year'] = h['death_year'] or f['death_year']
        for k in ('death_date', 'death_place'):
            if f.get(k) and not h.get(k):
                h[k] = f[k]
        counts['fallen joined to a hero'] += 1
    keep_numbers(list(by_id.values()))
    out = sorted(by_id.values(), key=lambda e: e['soldier_id'])
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding='utf-8')
    print(len(out), 'entries ->', OUT.name, dict(counts))
    for e in out:
        print(f"  {e['soldier_id']} {e['name']} {e['nick']} | {e['born_in']} | {e['death_year']} | {e['additional_info'][:90]}")


if __name__ == '__main__':
    main()
