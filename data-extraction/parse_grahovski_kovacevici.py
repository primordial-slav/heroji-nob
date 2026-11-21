"""
*Граховски Ковачевићи кроз векове и ратове* (Poreklo library, doc 00001427; edited by Slobodan Kovačević, Herceg
Novi), a book across units: the brotherhood's lists at the end of its chapter on the wars, in Cyrillic capitals, every
man a Kovačević named by his given name and his father's possessive:

    "Погинули Ковачевићи у другом свјетском рату" (scan pp. 284-292): "– АНДРИЈА ГАЈОВ, рођен 1923. године, у
        Никшићу, матурант Никшићке гимназије. Погинуо 1943. године, у Забрђу код Сарајева, као руководилац СКОЈ-а у
        Петој црногорској пролетерској бригади." Some name the grandfather's house too ("МИРКО ПЕТРА ПАЈОВА": Mirko,
        son of Petar of Pajo's house), a nickname after a dash ("ПЕТАР – ПЕРО НИКОЛИН").
    "Народни хероји НОР-а (1941–1945. г.)" (pp. 292-293): eight names, joined to their entries.
    "Носиоци Партизанске споменице 1941. г." (p. 293): 28 numbered names, the survivors.

The fallen list is every Kovačević who died in the war: the partisans, and the Chetniks (who fell with the Vučedol
brigade or in the retreat to Slovenia in 1945), the men the NOP's courts shot, the civilians. Only the fighters are
taken (`role`), and Kovačević Vojinov Radomir, killed by his own gun in the gathering of arms on 21 June 1941, as a
participant. Four entries send the reader to another branch's chapter ("ЈОВАН СИМОВ. (1903.-1942. г.) види огр.
Јездовићи"), which say nothing of what they were here: they stay out until those pages are read.

The OCR reads Ђ as Б ("БУРО", "БОРБИЈЕВ"), Ћ as "Т1" ("ШТ1ЕПАН"), garbles a few capitals into Latin letters
("IVU/IPKO" Мирко, "BOJI/IH" Војин, "T30PT30" Ђорђо) and splits others ("БЛАГ ОЈ Е"): FIX mends those of the
fighters and the spomenica's names, as the book's alphabetical order and the Vilusi book's list place them.

Output: data-extraction/poreklo/grahovski-kovacevici-entries.json (IDs 9115xxxxxx: the fallen from 000001 in the
list's order, the spomenica's holders from 002001 by the book's number).
Usage: python data-extraction/parse_grahovski_kovacevici.py
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

BOOK = 'grahovski-kovacevici.json'
OUT = HERE / 'poreklo' / 'grahovski-kovacevici-entries.json'
PREFIX = '9115'
OFFSET = 6                                   # scan page minus the book's page (scan 284 is p. 278)
TITLE = 'Grahovski Kovačevići kroz vekove i ratove'
SURNAME = 'Kovačević'
FALLEN = 'Poginuli Kovačevići u drugom svjetskom ratu'
HEROES = 'Narodni heroji NOR-a (1941–1945. g.)'
SPAIN = 'Borci španskog građanskog rata'
SPOMENICA = 'Nosioci Partizanske spomenice 1941. g.'
MUNICIPALITY = 'Nikšić'
CU = 'А-ЯЂЈЉЊЋЏ'

FIX = {
    'БЛАГ ОЈ EB': 'БЛАГОЈЕВ', '.1ОВАН': '.ЈОВАН', 'БЛАГ ОЈ Е': 'БЛАГОЈЕ', 'СПАСОЈ Е': 'СПАСОЈЕ', 'ВАСИЛИЈ Е': 'ВАСИЛИЈЕ', 'ДИМИТРИЈ Е': 'ДИМИТРИЈЕ',
    'ДРАГ АН': 'ДРАГАН', 'CABA - МУЈО': 'САВА – МУЈО', 'ВАСИЛИЈЕ · ЧИЛЕ': 'ВАСИЛИЈЕ – ЧИЛЕ', 'ШБЕП': 'ШЋЕП',
    'ЊУБ': 'ЉУБ', 'ВЕЊК': 'ВЕЉК', 'рођен "': 'рођен ',
    'IVU/IPKO': 'МИРКО', 'BOJI/IH': 'ВОЈИН', 'BOKI/IH': 'ЂОКИН',      # (Vilusi's list: "Ђокин РАДОМИР")
    'T30PT30': 'ЂОРЂО', 'TaOPToO': 'ЂОРЂО', 'IBS/BO': 'ЉУБО', 'МИП УТИ Н': 'МИЛУТИН', 'CTAHKO': 'СТАНКО', 'BOCA': 'БОСА', 'Ј OHIO': 'ЈОШО', 'ЦАНИЦА': 'ДАНИЦА',
    'МИПЕ': 'МИЛЕ', 'Т1': 'Ћ', 'БУРО': 'ЂУРО', 'БОРБИЈ': 'ЂОРЂИЈ', 'БОРБОВ': 'ЂОРЂОВ', 'АНБИН': 'АНЂИН',
    "МР'БЕНОВ": 'МРЂЕНОВ', 'МУ ГО': 'МУГО', 'ГОЛУ БОВ': 'ГОЛУБОВ', 'ЦАРИНКА': 'ДАРИНКА',
    'Треће Умцу ( Г )': 'Треће ударне',        # a photo's caption run into the line ("курир штаба Треће ... дивизије")
    'ЈАШО BAT—108': 'ЈОШО ВАТОВ', 'Осјеченицн': 'Осјеченици', 'Осјечаници': 'Осјеченици',
}
# Chetniks, the men the NOP's courts or its men killed, deserters: no record (the user's rule)
OUT_RE = re.compile(r'четни[кцч]\w*\s+(?:покрет|бригад|чет)|у четницима|четничк\w+ покрет|приступи\w* четни|'
                    r'присталица четника|одступи\w* (?:са четницима )?према Словенији|приликом одступања|'
                    r'Драже Михајловића|органа НО[ПГ]|војног суда|од стране партизана|дезертер|са четницима у блоку|'
                    r'у четничком блоку|од јединица НОВ', re.I)
# a fighter's words in an entry V.role misses: "у борби против њемачких и четничких снага", "у борби против Њемаца"
FOUGHT = re.compile(r'у борби против|борац од')
PARTICIPANT = {'Radomir Đokin'}              # killed by his own gun gathering arms, 21 June 1941


def fix(t: str) -> str:
    for a, b in FIX.items():
        t = t.replace(a, b)
    t = re.sub(rf'\b([{CU}]) (?=[{CU}]{{2,}})', r'\1', t)                    # "Г АВРИЛО", "Ј ОВАНОВ"
    return re.sub(rf'([{CU}]{{3,}}) ([ЕЈ]|ОЈ Е)\b', lambda m: m.group(1) + m.group(2).replace(' ', ''), t)   # "СПАСОЈ Е"


def lines(book: dict, pages) -> list[tuple[int, str]]:
    out = []
    for page in pages:
        for l in level_lines(page_words(book, page)):
            t = re.sub(r'^[\s\\_·~%\'"“.|*?]+', '', l.text.strip())
            if re.fullmatch(r'[\d\s.]{1,6}', t) or re.fullmatch(r'[—–\-\s]+', t) or 'СПомен' in t or l.x0 > 2500:
                continue
            out.append((page, fix(t)))
    return out


HEAD = re.compile(rf'^[—–\-\s\'’".]*([{CU}][{CU}\s–—\-]+?)\s*[.,]?\s*(?=\(|рођен|погинуо|Погинуо)')


def person(head: str) -> tuple[str, str, str, str]:
    """(given name, father as printed, the father the site matches on, nickname) of "ВЕЊКО ЈОВАНОВ", "ПЕТАР – ПЕРО
    НИКОЛИН", "МИРКО ПЕТРА ПАЈОВА" (father Petar, of Pajo's house)"""
    nick = ''
    m = re.match(rf'^([{CU}]+)\s*[–—\-]\s*([{CU}]+)\s+(.+)$', head)
    if m:
        head, nick = f'{m.group(1)} {m.group(3)}', V.given_word(m.group(2).capitalize())
    words = head.split()
    given = V.given_word(words[0].capitalize())
    printed = ' '.join(latin(w.capitalize()) for w in words[1:])
    if len(words) == 3:                              # "ПЕТРА ПАЈОВА": the father's genitive, his house's possessive
        father = V.given_word(words[1].capitalize())
        father = {'Petra': 'Petar'}.get(father, father)
    else:
        father = printed
    return given, printed, father, nick


def fallen(book: dict) -> list[dict]:
    raw = []
    for page, t in lines(book, range(284, 293)):
        if t.startswith(('Погинули Ковачевићи', 'у другом свјетском')):
            continue
        if t.startswith('Рат 1991'):
            break
        m = HEAD.match(t)
        if m:
            raw.append({'page': page, 'head': m.group(1).strip(), 'parts': [t[m.end():]]})
        elif raw:
            raw[-1]['parts'].append(t)
    out, counts = [], Counter()
    for r in raw:
        given, printed, father, nick = person(r['head'])
        cyr = ' '.join(r['parts'])
        info = V.read_cyr(cyr).strip(' .')
        if re.search(r'види\s+огр', cyr):
            counts['see another branch'] += 1
            continue
        hero = 'Народни херој' in cyr
        key = f'{given} {printed}'
        if hero or FOUGHT.search(cyr) and not OUT_RE.search(cyr.replace('четничких снага', '')):
            role = None
        elif OUT_RE.search(cyr):
            counts['out'] += 1
            continue
        elif key in PARTICIPANT:
            role = 'participant'
        else:
            role = V.role(info)
            if role == 'out':
                counts['out'] += 1
                print('   out:', key, '|', info[:110])
                continue
        d = V.death(info)
        if not d.get('year'):                # "гдје је 1942. године стријељан": the last war year the entry gives
            war = re.findall(r'\b(194[1-5])\b', info)
            if war and re.search(r'pogin|strelj|strijelj|umr|ubij', info, re.I):
                d['year'] = war[-1]
        years = re.match(r'\((1[89]\d\d)\s*[.]?\s*[–—\-]\s*(19[4]\d)', info)
        born = re.search(r'\brođen[a]?\s+(1[89]\d\d)', info)
        name_printed = ' '.join(x for x in (given, '– ' + nick if nick else '', printed) if x)
        e = {'soldier_id': '', 'name': ' '.join(x for x in (SURNAME, father, given) if x), 'last_name': SURNAME,
             'also': [], 'first_name': given, 'nick': nick, 'fathers_name': father,
             'birth_year': born.group(1) if born else (years.group(1) if years else ''),
             'born_in': birthplace(info), 'death_year': d.get('year', '') or (years.group(2) if years else ''),
             **({'death_date': d['date']} if d.get('date') else {}),
             **({'death_place': d['place']} if d.get('place') else {}),
             'survived': False, 'units': V.units_of(info),
             'additional_info': f'{FALLEN}: {name_printed}, {info}.', 'list': FALLEN,
             'book_title': TITLE, 'source_url': viewer_url(book, r['page']), 'source_page': r['page'] - OFFSET}
        if role:
            e['role'] = role
        out.append(e)
        counts[role or 'fighter'] += 1
    for i, e in enumerate(out, 1):
        e['soldier_id'] = f'{PREFIX}{i:06d}'
    print('fallen:', dict(counts))
    return out


def main():
    V.corpus()
    book = load(BOOK)
    entries = fallen(book)
    counts = Counter()
    tail = lines(book, [292, 293])
    section = None
    for page, t in tail:
        if t.startswith('БОРЦИ ШПАНСКОГ'):
            section = SPAIN
            continue
        if t.startswith('НАРОДНИ ХЕРОЈИ'):
            section = HEROES
            continue
        if t.startswith('ПРЕЖИВЈЕЛИ'):
            section = None
            continue
        if t.startswith('– Носиоци') or t.startswith('Носиоци'):
            section = SPOMENICA
            continue
        if section in (SPAIN, HEROES):
            for name in re.split(r'\s+и\s*$|,', re.sub(r'^[—–\-\s]+', '', t)):
                name = name.strip(' .,и')
                if not name:
                    continue
                given, printed, father, nick = person(name)
                hits = [e for e in entries if e['first_name'] == given and
                        (e['fathers_name'] == father or e['fathers_name'].startswith(father[:4]) or
                         re.search(rf': {given} {father[:4]}', e['additional_info']))]
                if hits:
                    hits[0]['additional_info'] += f' {section}: {name_printed(given, nick, printed)}.'
                    counts[f'{section} joined'] += 1
                else:
                    counts[f'{section} later'] += 1
                    later.append((section, given, nick, printed, father))
        elif section == SPOMENICA:
            m = re.match(r'^(\d{1,2})\s*\.\s*(.+?)[.,]?\s*(?:\bи)?$', t)
            if not m:
                continue
            no = int(m.group(1))
            given, printed, father, nick = person(m.group(2).strip(' .,'))
            woman = printed.endswith('a')
            entries.append({'soldier_id': f'{PREFIX}{2000 + no:06d}', 'name': f'{SURNAME} {father} {given}',
                            'last_name': SURNAME, 'also': [], 'first_name': given, 'nick': nick, 'fathers_name': father,
                            'birth_year': '', 'born_in': '', 'death_year': '', 'survived': True, 'units': [],
                            'additional_info': f'{SPOMENICA}: {no}. {name_printed(given, nick, printed)}',
                            'list': SPOMENICA, 'book_title': TITLE, 'source_url': viewer_url(book, page),
                            'source_page': page - OFFSET, **({'_woman': True} if woman else {})})
            counts['spomenica'] += 1
    # the heroes and Spain's fighters who survived: their entries in the spomenica's list
    for section, given, nick, printed, father in later:
        hits = [e for e in entries if e['list'] == SPOMENICA and e['first_name'] == given and e['fathers_name'] == father]
        if hits:
            hits[0]['additional_info'] += f'. {section}: {name_printed(given, nick, printed)}'
            counts[f'{section} joined to spomenica'] += 1
        else:
            print('   unplaced:', section, given, nick, printed)
    for e in entries:
        e.pop('_woman', None)
        if e['list'] == SPOMENICA and not e['additional_info'].endswith('.'):
            e['additional_info'] += '.'
    entries.sort(key=lambda e: e['soldier_id'])
    OUT.write_text(json.dumps(entries, ensure_ascii=False, indent=1), encoding='utf-8')
    spom = sorted(int(e['soldier_id'][-3:]) for e in entries if e['list'] == SPOMENICA)
    print(len(entries), 'entries ->', OUT.name, dict(counts), 'spomenica missing', sorted(set(range(1, 29)) - set(spom)))
    for e in entries:
        print(f"  {e['soldier_id']} {e['name']} {e['nick']} | {e['birth_year']} {e['born_in']} | {e['death_year']} "
              f"{e.get('death_place', '')} {e['units']} {e.get('role', '')}")


later: list = []
VILLAGES = {'Spila', 'Spili', 'Osječenica', 'Osječenici', 'Osječanici', 'Zaslap', 'Zaslapu', 'Nudo', 'Nudolu',
            'Podbožur', 'Podbožuru', 'Okolišta', 'Okolištima', 'Vilusi', 'Vilusima', 'Grahovo', 'Grahovu', 'Riječani',
            'Riječanima', 'Balosavi', 'Balosavima', 'Bari Graovskoj', 'Bari Grahovskoj', 'Nikšiću'}


def birthplace(info: str) -> str:
    """"rođen 1923. godine. u Nikšiću", "rođen 1927. godine u Gorničetu kod Đevđelije (Makedonija)": the place as
    printed (the locative), Grahovo's villages with the municipality they are in now"""
    m = re.search(r'\brođen[a]?\s+(?:je\s+)?1[89]\d\d\.?\s*(?:godine|g\.)?[.,]?\s*(?:u|na)\s+'
                  r'([A-ZČĆŽŠĐ]\w+(?:\s+(?:kod\s+)?[A-ZČĆŽŠĐ]\w+)?)', info)
    if not m:
        return ''
    place = m.group(1)
    return f'{place}, {MUNICIPALITY}' if place in VILLAGES and place != 'Nikšiću' else place


def name_printed(given: str, nick: str, printed: str) -> str:
    return ' '.join(x for x in (given, '– ' + nick if nick else '', printed) if x)


if __name__ == '__main__':
    main()
