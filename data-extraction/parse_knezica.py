"""
Миливој Родић, *Кнежица у Кнешпољу* (Poreklo library, doc 00002790), the villages of Knežica under Kozara, as a book
across units. Its Prilozi, Cyrillic, a name a line under each village (Велико Двориште, Мало Двориште, Доњи Јеловац,
Доња Јутрогошта, Горња Градина, Крива Ријека, Мурати, Ушивац, Стригова, Читлук):
    "Остали на вјечној стражи отаџбине (Погинули борци кнежичких села у НОР-у)" (scan pp. 453-465, book pp. 451-463),
        one column: "Будимир (Марка) Мирко, 1913—1943. Земун" (the father in brackets, the years of birth and death,
        where he died; many in the camps of Jasenovac and Zemun after the Kozara offensive, as the book counts them);
    "Носиоци Партизанске споменице 1941. године" (pp. 503-504) and "Преживјели борци НОР-а мјесног подручја Кнежица"
        (pp. 505-510), two columns, names alone; they lived through the war (`survived`).
Out: "Душманима ни дужни ни криви" (pp. 466-502), the victims of the Ustaša terror, and the dead of 1991-1995.

Output: data-extraction/poreklo/knezica-entries.json (IDs 9104xxxxxx: the fallen from 000001, the spomenica holders
from 001001, the survivors from 002001, in the book's order, left column first).
Usage: python data-extraction/parse_knezica.py
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
from poreklo_text import load, page_words, viewer_url  # noqa: E402

BOOK = 'knezica.json'
OUT = HERE / 'poreklo' / 'knezica-entries.json'
PREFIX = '9104'
OFFSET = 2                                  # scan page minus the book's page
TITLE = 'Knežica u Knešpolju'
MUNICIPALITY = 'Bosanska Dubica'                 # as the book's SUBNOR list and the census name it
LISTS = [('fallen', range(453, 466), 0, 'Ostali na vječnoj straži otadžbine (Poginuli borci knežičkih sela u NOR-u)'),
         ('spomenica', range(503, 505), 1000, 'Nosioci Partizanske spomenice 1941. godine'),
         ('alive', range(505, 511), 2000, 'Preživjeli borci NOR-a mjesnog područja Knežica')]
UC, LC = 'А-ЯЂЈЉЊЋЏ', 'а-яђјљњћџ'
VILLAGES = ['Велико Двориште', 'Мало Двориште', 'Доњи Јеловац', 'Доња Јутрогошта', 'Горња Градина', 'Крива Ријека',
            'Мурати', 'Ушивац', 'Стригова', 'Читлук']
# the village headings as the OCR garbled them, read from the order of the lists
HEADINGS = {'ДоњаЈуШробошШа': 'Доња Јутрогошта', 'ДоњаЈутробошта': 'Доња Јутрогошта', 'ГорњаГрауина': 'Горња Градина',
            'МалоДворшшђе': 'Мало Двориште', 'Мурата': 'Мурати', 'Мypaiáu': 'Мурати', 'Ушиваи': 'Ушивац',
            "CLEpuz'osa": 'Стригова', 'Страбова': 'Стригова', 'KpueaРијека': 'Крива Ријека', '[(pusaPlejerch': 'Крива Ријека'}
NAME = re.compile(rf"^([{UC}][{LC}]+(?:\s*[–-]\s*[{UC}][{LC}]+)?)\s*(?:\(\s*([^)]+?)\s*\))?\s+"
                  rf"([{UC}][{LC}]+)(?:\s*[–—-]\s*([{UC}][{LC}]+)|\s*\(([{UC}][{LC}]+)\))?\s*(?:[,.]?\s*(\d.*))?$")
# Latin letters the OCR set for the Cyrillic they look like ("Bepa (Вучена)" Вера, "(Byje)" Вује)
LOOKALIKE = str.maketrans('ABCEHKMOPTXaceopxyjB', 'АВСЕНКМОРТХасеорхујВ')


def village_of(t: str) -> str:
    key = t.replace(' ', '')
    return HEADINGS.get(key) or next((v for v in VILLAGES if v.replace(' ', '') == key), '')


def clean(t: str) -> str:
    t = re.sub(r"^[_'’\"“;:\[\s]+|^ј\s+", '', t)                    # specks before the name: "_Бјелајац", "ј Карлица"
    t = re.sub(r'(?<![\w])([{}J])\s(?=[{}])'.format(UC, LC), lambda m: m.group(1).replace('J', 'Ј'), t)  # "Ј ове", "Г њатовић"
    t = re.sub(r'\),\s*', ') ', t)                                     # "(Лазе),Благоја"
    t = re.sub(rf'(?<=[{LC}])\s([{LC}])(?=\s*\()', r'\1', t)            # "Бенадиј а (Милана)"
    t = re.sub(rf'(?<=[{LC}])([{UC}])', lambda m: m.group(1).lower(), t)   # "МазалИца"
    t = re.sub(r'(?<![\w])[A-Za-z]+(?![\w])', lambda m: m.group(0).translate(LOOKALIKE)
               if re.fullmatch(r'[ABCEHKMOPTXaceopxyj]+', m.group(0)) else m.group(0), t)
    t = re.sub(r"['’\"“]([БВ])(?=[{}])".format(LC), 'Ђ', t)             # "'Борђо", "('Вурђа)": the hook of Ђ
    t = re.sub(r"(?<=\s)['’\"“](?=[{}])".format(UC), '', t)            # "Дашић “Урош"
    return t[0].upper() + t[1:] if t else t                           # "ћурчија"


def dje(w: str, given: bool) -> str:
    """the OCR reads Ђ as Б: "Буро", "(Борђе)", "(Бурана)" are Ђуро, Ђорђе, Ђурана; a surname only where the site
    spells it with Ђ more often"""
    if not w.startswith('Б'):
        return w
    if given:
        return re.sub(r'^Б(?=ур|орђ)', 'Ђ', w)
    b, d = V.T._names[V.latin(w).upper()], V.T._names[V.latin('Ђ' + w[1:]).upper()]
    return 'Ђ' + w[1:] if d > b else w


def lines(book: dict, page: int, two: bool) -> list[str]:
    words = page_words(book, page)
    if not two:
        return [l.text.strip() for l in level_lines(words)]
    out = []
    for side in (True, False):
        out += [l.text.strip() for l in level_lines([w for w in words if (w.x0 < 9000) == side])]
    return out


def main():
    V.corpus()
    book = load(BOOK)
    entries, counts = [], Counter()
    for kind, pages, base, title in LISTS:
        village, no = '', 0
        for page in pages:
            for t in lines(book, page, kind != 'fallen'):
                if re.search(r'Род\s*И|Р[оe]д\s*ИП|КНЕ|hHE|ћНЕ|ПАРТИЗАНСКЕ|ГОДИНЕ|ПРЕЖИВЈЕЛИ|ПОЦРУЧЈА|ПОДРУЧЈА|ОСТАЛИ|Погинули|^\d{3}$', t):
                    continue
                v = village_of(t)
                if v:
                    village = v
                    continue
                t = clean(t)
                m = NAME.match(t)
                if not m:
                    if t:
                        print('  ?', kind, page, t)
                    continue
                sur, fath, given, nick, nick2, rest = m.groups()
                nick = nick or nick2
                last = '-'.join(V.name_word(dje(re.sub(r'\s', '', x), False)) for x in re.split(r'\s*[–-]\s*', sur))
                first = V.given_word(dje(given, True))
                fath = V.father(dje(fath, True)) if fath else ''
                nick = V.read_cyr(nick) if nick else ''
                vil = V.read_cyr(village) if village else ''
                no += 1
                e = {'soldier_id': f'{PREFIX}{base + no:06d}', 'name': ' '.join(x for x in (last, fath, first) if x),
                     'last_name': last, 'also': [], 'first_name': first, 'nick': nick, 'fathers_name': fath,
                     'birth_year': '', 'born_in': f'{vil}, {MUNICIPALITY}' if vil else '', 'death_year': '',
                     'survived': kind != 'fallen', 'units': [], 'list': title, 'book_title': TITLE,
                     'source_url': viewer_url(book, page), 'source_page': page - OFFSET}
                printed = f"{last}{f' ({fath})' if fath else ''} {first}" + (f' – {nick}' if nick else '')
                if kind == 'fallen' and rest:
                    rest = re.sub(r'([–—-])\s*1([34]\d)\.', r'\g<1>19\2.', rest.strip())        # "1925—142."
                    years = re.match(r'(1[89]\d\d|\d{4})\s*[–—-]\s*(19[34]\d)\.?\s*(.*)$', rest)
                    if years:
                        e['birth_year'] = years.group(1) if years.group(1).startswith(('18', '19')) else ''
                        e['death_year'] = years.group(2)
                        place = re.split(r'\s+[–—]\s+', V.read_cyr(years.group(3)).strip(' .,'))[0]  # "Zemun — Ostrovačka ada"
                        if place:
                            e['death_place'] = re.sub(r'^[BV]oc\.|^Vos\.', 'Bos.', place)    # the OCR's "Boc.", "Vos."
                    printed += re.sub(r' (?:[BV]oc|Vos)\.', ' Bos.', f', {V.read_cyr(rest)}')
                e['additional_info'] = f'{title}, {vil}: {printed}' if vil else f'{title}: {printed}'
                entries.append(e)
                counts[kind] += 1
    # a holder of the spomenica the survivors' list names too is one man: his entry holds both lines
    key = lambda e: (e['born_in'], e['last_name'], e['fathers_name'], e['first_name'])
    holders = {key(e): e for e in entries if e['soldier_id'][4:7] == '001'}
    joined = set()
    for e in entries:
        h = holders.get(key(e))
        if e['soldier_id'][4:7] == '002' and h and h['soldier_id'] not in joined:
            h['additional_info'] += '. ' + e['additional_info']
            joined.add(h['soldier_id'])
            e['joined'] = True
    entries = [e for e in entries if not e.pop('joined', False)]
    counts['joined'] = len(joined)
    OUT.write_text(json.dumps(entries, ensure_ascii=False, indent=1), encoding='utf-8')
    print(dict(counts), '->', OUT.name, len(entries))
    print(Counter(e['born_in'] for e in entries).most_common())


if __name__ == '__main__':
    main()
