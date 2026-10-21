"""
What the Poreklo library's village books of 2026-10-20 share (Han Pijesak, Skakavac, Žitorađe, Brod, Revolucionarno
Grahovo, Kolašin, Božiće): their bios read as the site spells them, the birthplace, the death, the role a mixed list
gives a man, and the site's units a bio names. Each book's parser keeps its own lists and slips.

  read_cyr(text)    a Cyrillic text in Latin, each word read back as the site's records spell it (the OCR's Б for
                    Ћ, Њ for Љ: parse_trebinjci_pali's reader), the lines' hyphens joined
  name_word(w)      a word of a name, as the site spells it (-нћ is -нић: "Батиннћ")
  father(w)         a father's genitive, as the site spells it
  born_in(text, m)  the birthplace after "rođen", in the case printed, with the municipality it names, else m
  death(text)       {year, date, place} of the death in the war: parse_ostrvica.death_of, and a day printed in
                    figures ("19.01.1942."), a place after the date ("poginuo 7. marta 1942. na Kršu"), never a unit
                    taken for a place ("u Prvoj južnomoravskoj brigadi")
  role(text)        None for a fighter, 'activist' for the movement's other people, 'out' for neither
                    (parse_mosorski_odred_2's rules)
  units_of(text)    the site's unit codes a bio names ("borac 4. proleterske", "Šeste istočnobosanske", "VII srp.")
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import parse_mosorski_odred_2 as mos  # noqa: E402
import parse_trebinjci_pali as T  # noqa: E402
from _parser_scaffold import cyrillic_to_latin as latin  # noqa: E402
from parse_divoselo import father_word  # noqa: E402
from parse_ostrvica import WHEN, death_of  # noqa: E402

corpus = T.corpus


def unhyphen(text: str) -> str:
    return re.sub(r'(\w)[–—-]\s+(\w)', r'\1\2', re.sub(r'\s+', ' ', text)).strip()


def read_cyr(cyr: str) -> str:
    cyr = re.sub(r'(?<![\w])Њуб', 'Љуб', re.sub(r'(?<![\w])њуб', 'љуб', cyr))      # "Њубљана", "Њубиша"
    return re.sub(r'\bu(?=[A-ZČĆŽŠĐ])', 'u ', latin(T.decode_text(unhyphen(cyr))))  # "uŽeravicama", "uNOB"


def name_word(w: str) -> str:
    w = re.sub(r"['’`.,;:]", '', w).strip('()')
    if not w:
        return ''
    w = re.sub(r'[нН][ћЋ]$', lambda m: 'ић' if m.group(0).islower() else 'ИЋ', w)       # Бјелаковнћ, Батиннћ
    best = T.best_name(w.upper())
    if not T._names[latin(best)]:
        best = re.sub(r'И[БНПВЕ]$', 'ИЋ', w.upper())           # a surname the site doesn't know: its -ић
    return latin(best).capitalize()


def given_word(w: str) -> str:
    """a given name, read as the site's given names know it best ("Пејчин", which name_word reads as the surname
    Pejčić)"""
    w = re.sub(r"['’`.,;:]", '', w).strip('()')
    if not w:
        return ''
    cands = T.candidates(w.upper())
    best = max(cands, key=lambda c: (T._given[latin(c)], -sum(a != b for a, b in zip(c, w.upper()))))
    return latin(best).capitalize() if T._given[latin(best)] else latin(w).capitalize()     # unknown: as printed


def father(w: str) -> str:
    w = re.sub(r"['’`]", '', w).strip()
    return father_word(w.split()[0]) if w else ''


COUNTRIES = {'Srbija', 'Bosna i Hercegovina', 'BiH', 'Slovenija', 'Hrvatska', 'Crna Gora', 'Austrija', 'Čehoslovačka',
             'Makedonija', 'Italija'}
ETHNIC = re.compile(r'^(?:Srbin|Srpkinja|Hrvat|Hrvatica|Slovenac|Slovenka|Jevrejin|Jevrejka|Crnogorac|Crnogorka|Čeh|'
                    r'Musliman|Muslimanka)\b')


def born_in(text: str, municipality: str) -> str:
    """the birthplace after "rođen": "1923. u Malom Polju" (the locative, as printed), "1919, Sovljak, Ub, Srbija",
    "1921. godine u Blacu · Prokuplje"; the municipality it names, else the book's"""
    m = re.search(r'\brođen[a]?\s+(?:je\s+)?(?:\d{1,2}\.\s*\w+\s+)?(?:1[89]\d\d\.?\s*(?:godine\s*)?,?\s*)?'
                  r'(?:(?:u|na)\s+(?:selu\s+|zaseoku\s+)?)?(.+)', text)
    if not m:
        return ''
    parts = [p.strip(' .') for p in re.split(r',|\s[·–-]\s|\s\(|\)|\s+u\s+(?=[A-ZČĆŽŠĐ])', m.group(1))]
    places = []
    for p in parts[:3]:
        p = re.sub(r'^(?:opština|opštini|srez|srezu|kotar)\s+', '', p)
        if not p or not p[0].isupper() or ETHNIC.match(p) or p in COUNTRIES or re.match(r'(?:u|od|na)\s', p) \
                or re.search(r'\d', p) or len(p.split()) > 3:
            break
        places.append(p)
    if not places:
        return ''
    if len(places) == 1 and municipality and places[0] != municipality:
        places.append(municipality)
    return ', '.join(places[:2])


UNIT_NOUN = re.compile(r'^\s*\w*\s*(?:brigad|bataljon|čet[iae]|odred|divizij|korpus|južnomoravsk|proletersk|krajišk|'
                       r'istočnobosansk|crnogorsk|srpsk|NOU|udarn)', re.I)
NUMERIC = re.compile(r'\b(\d{1,2})\.\s?(\d{1,2})\.\s?(19[34]\d)\b')
PLACE_AFTER = re.compile(r'^[.,]?\s*(?:godine\s+)?(?:u\s+borbi\s+)?(?:u|na|kod)\s+([A-ZČĆŽŠĐ][\w–-]*(?:\s+[A-ZČĆŽŠĐ][\w–-]*)?)')


def death(text: str) -> dict:
    d = dict(death_of(text))
    own = text
    verb = re.search(r'\b(?:pogin|umr|ubij|strelj|strijelj|nesta|strada)\w*(?:[^;]|\.\d){0,80}', own, re.I)
    if verb and not d.get('date'):
        num = NUMERIC.search(verb.group(0))                 # "19.01.1942."
        if num:
            d.update({'year': num.group(3), 'date': f'{num.group(3)}-{int(num.group(2)):02d}-{int(num.group(1)):02d}'})
    if verb and not d.get('year'):                          # "stradao 1944. kod Prače"
        when = WHEN.search(verb.group(0))
        if when and when.group(3):
            d.update({'year': when.group(3), 'date': d.get('date', ''), 'place': d.get('place', '')})
    if d.get('place'):
        at = own.find(d['place'])
        if at >= 0 and UNIT_NOUN.match(own[at + len(d['place']):]):
            d['place'] = ''                                 # "u Prvoj južnomoravskoj brigadi"
    if not d.get('place') and d.get('year'):
        verb = re.search(r'\b(?:pogin|umr|ubij|strelj|strijelj|nesta|strada)\w*', own, re.I)
        if verb:
            span = own[verb.end():verb.end() + 160]
            year = re.search(rf'\b{d["year"]}\b\.?', span)
            if year:
                after = PLACE_AFTER.search(span[year.end():])
                if after and not UNIT_NOUN.match(span[year.end() + after.end():]):
                    d['place'] = after.group(1)
    return d


def role(text: str) -> str | None:
    if mos.fighter_or_officer({'additional_info': text}):
        return None
    if mos.activist({'additional_info': text}):
        return 'activist'
    return 'out'


ORDINALS = ['prv', 'drug', 'treć', 'četvrt', 'pet', 'šest', 'sedm', 'osm', 'devet', 'deset', 'jedanaest', 'dvanaest',
            'trinaest', 'četrnaest', 'petnaest', 'šesnaest', 'sedamnaest', 'osamnaest', 'devetnaest', 'dvadeset']
ROMAN = {'I': 1, 'II': 2, 'III': 3, 'IV': 4, 'V': 5, 'VI': 6, 'VII': 7, 'VIII': 8, 'IX': 9, 'X': 10, 'XI': 11, 'XII': 12,
         'XIII': 13, 'XIV': 14, 'XV': 15, 'XVI': 16, 'XVII': 17, 'XVIII': 18, 'XIX': 19, 'XX': 20, 'XXI': 21, 'XXII': 22,
         'XXIII': 23, 'XXIV': 24, 'XXV': 25}
# the site's brigades by number and the word of their name (CLAUDE.md's table)
BRIGADES = {
    'proletersk': {1: 1, 2: 39, 3: 5, 4: 40, 5: 41, 6: 42, 13: 6},
    'srpsk': {4: 21, 5: 127, 7: 85, 8: 87, 9: 165, 10: 88, 12: 90, 14: 27, 15: 86, 17: 55, 18: 128, 19: 73, 20: 91,
              21: 80, 22: 74, 23: 89, 25: 31},
    'krajišk': {1: 123, 2: 24, 3: 10, 4: 11, 5: 12, 6: 13, 7: 48, 8: 14, 11: 107, 12: 54, 13: 124},
    'crnogorsk': {4: 40, 5: 41, 6: 106, 7: 28, 8: 38},
    'sandžačk': {3: 5, 4: 98},
    'istočnobosansk': {6: 42},
    'hercegovačk': {10: 43, 12: 101, 13: 100, 14: 81},
    'dalmatinsk': {1: 36, 2: 7, 3: 46, 6: 103, 11: 53, 12: 50},
    'banijsk': {3: 108, 4: 20, 7: 44, 8: 45, 16: 47},
    'ličk': {1: 2, 2: 3, 3: 118},
    'vojvođansk': {1: 9, 2: 18, 3: 57, 4: 76, 5: 82, 6: 83, 7: 22, 8: 78, 12: 75, 13: 84},
    'majevičk': {15: 49, 17: 29},
    'slavonsk': {12: 146, 16: 37, 17: 16, 18: 17, 21: 34},
    'hrvatsk': {18: 52},
    'srednjobosansk': {14: 56},
    'kozaračk': {5: 12, 11: 107},
    'bokeljsk': {1: 102},
    'kosovsko': {1: 77},
    'makedonsk': {3: 51},
    'šumadijsk': {1: 15, 2: 80},
    'južnomoravsk': {3: 127, 5: 85},
    'birčansk': {19: 23},
    'tuzlansk': {21: 32},
    'brodsk': {25: 30},
    'konjičk': {1: 92},
    'zagorsk': {1: 105},
    'primorsko': {3: 99, 14: 95},
    'omladinsk': {7: 28, 14: 81, 16: 37},
}
# the region a "proleterska" brigade is of, after it ("2. proleterske dalmatinske" is the 2. dalmatinska)
REGION_AFTER = re.compile(r'\s*\(?(dalmatinsk|crnogorsk|sandžačk|istočnobosansk|krajišk|vojvođansk|slavonsk)', re.I)
ODREDI = [(r'Toplič\w*\s+(?:partizansk\w*\s+|NOP\s+)?odred', 93), (r'Užič\w*\s+(?:partizansk\w*\s+|NOP\s+)?odred', 26),
          (r'Čačansk\w*\s+(?:partizansk\w*\s+|NOP\s+)?odred', 126), (r'Kalničk\w*\s+(?:partizansk\w*\s+)?odred', 58),
          (r'Tuzlansk\w*\s+(?:partizansk\w*\s+|NOP\s+)?odred', 25), (r'Požarevačk\w*\s+(?:partizansk\w*\s+|NOP\s+)?odred', 119),
          (r'Mačvansk\w*\s+(?:partizansk\w*\s+|NOP\s+)?odred', 109), (r'Vrhovn\w*\s+štab', 112),
          (r'Centraln\w*\s+(?:partizansk\w*\s+)?bolnic', 117)]
NUMBER = rf"(\d{{1,2}})\.?|\b({'|'.join(sorted(ROMAN, key=len, reverse=True))})\b\.?|\b({'|'.join(ORDINALS)})\w*"
UNIT = re.compile(rf"(?:{NUMBER})\s+(?:[\w()«»„“\"–-]+\s+){{0,3}}?\(?({'|'.join(BRIGADES)})\w*", re.I)


def number_of(m: re.Match) -> int | None:
    if m.group(1):
        return int(m.group(1))
    if m.group(2):
        return ROMAN.get(m.group(2).upper())
    word = m.group(0).split()[0].lower()                     # the whole word: the regex stops "petnaeste" at "pet"
    if word.startswith('dvadeset'):                         # "dvadeset prve", "dvadesete"
        rest = m.group(0)[len('dvadeset'):].lower()
        return 20 + next((i + 1 for i, o in enumerate(ORDINALS[:9]) if re.match(rf'\w*\s+i?\s*{o}', rest)), 0)
    # the longest ordinal the word begins with ("petnaest" before "pet", "šesnaest" before "šest")
    return max((i + 1 for i, o in enumerate(ORDINALS) if word.startswith(o)), default=None,
               key=lambda n: len(ORDINALS[n - 1]))


def units_of(text: str) -> list[int]:
    found = set()
    for m in UNIT.finditer(text):
        n, key = number_of(m), m.group(4).lower()
        tail = text[m.end():m.end() + 40]
        proleterska = key == 'proletersk'
        region = REGION_AFTER.match(re.sub(r'^\w*', '', tail)) if proleterska else None
        if region and n in BRIGADES[region.group(1).lower()]:
            key = region.group(1).lower()
        plain = re.sub(r'[()«»„“"]', ' ', tail)
        if n and n in BRIGADES[key] and (re.match(r'\w*\s*(?:\w+\s+){0,2}?(?:NOU\s+|udarn\w*\s+|narodno\w*\s+)?brig', plain, re.I)
                                         or proleterska or re.search(r'brig', m.group(0), re.I)):
            found.add(BRIGADES[key][n])
    for pat, code in ODREDI:
        if re.search(pat, text):
            found.add(code)
    return sorted(found)
