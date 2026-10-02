"""
Read the dated steps of a soldier's life from his entries, for the line ("Životni put") in the record dialog:
born, joined SKOJ or the KPJ, joined the NOB, came to the unit, a duty held from a date, wounded, captured,
exchanged, discharged, and the death.

Precision over recall: a step is read only where a keyword and a date stand together in the text
("član KPJ od 1940", "u brigadi od decembra 1941", "ranjen 20. aprila 1945. kod Vrčin Dola"). A date nothing
claims is left alone ("Nosilac Partizanske spomenice 1941" is no step). Birth and death come from the structured
fields (birth_year, death_date, death_type), which corrections may have set, and only their place in the text
is looked up here.

Each step is kept as
    {"k": kind, "d": "1941-12", "e": "1943-06" (end of a period, optional), "at": [start, end] of the words in the entry,
     "x": what the step is about, as printed (a duty, a place; optional), "s": which entry (0 own, n the n-th
     of other_sources; left out when 0)}
with dates as YYYY, YYYY-MM or YYYY-MM-DD.

The dialog draws the line from three steps on; website/data/life-events/<unit data file> keeps those soldiers' steps
by soldier_id, and the route that serves the dialog's full records merges them in as life_events.

Usage:
    python scripts/extract_life_events.py                       # dry run: coverage per unit, samples
    python scripts/extract_life_events.py --brigade 1 --sample 20
    python scripts/extract_life_events.py --leftover 40         # dated phrases no rule reads, most common first
    python scripts/extract_life_events.py --check 15            # random steps of each kind, to read for mistakes
    python scripts/extract_life_events.py --write [--brigade N] # write website/data/life-events/
"""
from __future__ import annotations

import argparse
import json
import random
import re
import sys
from collections import Counter
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, str(Path(__file__).parent))
from extract_structured_fields import PARSER_FIELDS, ROOT, load_live, sentences  # noqa: E402
from name_utils import BRIGADE_CONFIGS  # noqa: E402

OUT = ROOT / 'website' / 'data' / 'life-events'

# ── dates ───────────────────────────────────────────────────────────────────
MONTH_NAMES = {
    1: 'januar januara januaru januarja siječanj siječnja siječnju',
    2: 'februar februara februaru februarja veljača veljače veljači',
    3: 'mart marta martu marca ožujak ožujka ožujku',
    4: 'april aprila aprilu travanj travnja travnju aprnjla aprnjta aprma',     # the last three: 4. srpska's text layer
    5: 'maj maja maju svibanj svibnja svibnju',
    6: 'jun juna junu junij junija lipanj lipnja lipnju',
    7: 'jul jula julu julij julija srpanj srpnja srpnju',
    8: 'avgust avgusta avgustu august augusta augustu kolovoz kolovoza kolovozu',
    9: 'septembar septembra septembru september rujan rujna rujnu',
    10: 'oktobar oktobra oktobru oktober listopad listopada listopadu oktora',
    11: 'novembar novembra novembru november studeni studenoga studenog studenom',
    12: 'decembar decembra decembru december prosinac prosinca prosincu',
}
MONTH_OF = {w: n for n, words in MONTH_NAMES.items() for w in words.split()}
MON = '(?:' + '|'.join(sorted(MONTH_OF, key=len, reverse=True)) + ')'
ROMAN_OF = {'I': 1, 'II': 2, 'III': 3, 'IV': 4, 'V': 5, 'VI': 6, 'VII': 7, 'VIII': 8, 'IX': 9, 'X': 10, 'XI': 11, 'XII': 12}
# Roman months only in capitals, even in a rule read without case: "i" and "v" are words
ROM = '(?-i:XII|XI|X|IX|VIII|VII|VI|V|IV|III|II|I)'
Y = r'(?:18[89]\d|19\d\d)'
D1 = r'\d{1,2}(?:\s?[/-]\s?\d{1,2})?'                    # a night or days: 29/30. X 1944, 29-31. XI 1944
# "krajem 1943", "u toku 1942", "od jeseni 1944" (a season leaves the year)
QUAL = (r'(?:(?:krajem|početkom|sredinom|polovinom|koncem|potkraj|tokom|u\s+toku|u|početka|kraja|polovine|sredine|konca|'
        r'jeseni|jesen|proleća|proljeća|proleće|proljeće|leta|ljeta|leto|ljeto|zime|zimi|zima)\s+)?')
GOD = r'(?:\.?\s*god(?:ine|\.|\b))?'
# one date: 17. 01. 1945 / 1.11.1944 / 14. XII1944 / 3. decembra 1944 / aprila 1945 / IX 1944 / 1941
ONE = (rf'(?:{D1}[.,]\s?(?:\d{{1,2}}|{ROM})[.,]?\s?{Y}'
       rf'|(?:{D1}[.,]?\s?)?{MON}\s(?:mesecu\s|mjesecu\s|meseca\s|mjeseca\s)?{Y}'
       rf'|(?<!\w){ROM}\.?\s{Y}'                                           # not the V of "NOV 1943"
       rf'|{Y})')
# a period: januar-mart 1943 / od marta do juna 1943 / od 20. 10. 1944. do 15. 5. 1945 / 1941-1945
SPAN = (rf'(?:{MON}\s?(?:-|–|—|\sdo\s)\s?{MON}\s{Y}'
        rf'|{ONE}\.?\s?(?:-|–|—|\sdo\s)\s?{ONE})')
WHEN = rf'(?:od\s*)?{QUAL}(?:{SPAN}|{ONE}){GOD}'
WHEN_RE = re.compile(WHEN, re.I)
ANY_DATE_RE = re.compile(rf'{QUAL}(?:{SPAN}|{ONE}){GOD}', re.I)


def parse_one(s: str) -> tuple[int, int, int] | None:
    s = s.strip()
    m = re.search(rf'({D1})[.,]\s?(\d{{1,2}}|{ROM})[.,]?\s?({Y})', s)
    if m:
        day = int(re.split(r'\s?[/-]', m.group(1))[0])
        mon = ROMAN_OF.get(m.group(2)) or int(m.group(2))
        if 1 <= mon <= 12:
            return int(m.group(3)), mon, day if 1 <= day <= 31 else 0
        return int(m.group(3)), 0, 0
    m = re.search(rf'(?:({D1})[.,]?\s?)?({MON})\s(?:mesecu\s|mjesecu\s|meseca\s|mjeseca\s)?({Y})', s, re.I)
    if m:
        day = int(re.split(r'\s?[/-]', m.group(1))[0]) if m.group(1) else 0
        return int(m.group(3)), MONTH_OF[m.group(2).lower()], day if 1 <= day <= 31 else 0
    m = re.search(rf'\b({ROM})\.?\s({Y})', s)
    if m:
        return int(m.group(2)), ROMAN_OF[m.group(1)], 0
    m = re.search(Y, s)
    return (int(m.group(0)), 0, 0) if m else None


def parse_when(s: str) -> tuple[tuple, tuple | None] | None:
    """The start of a date or period, and its end when it is a period."""
    s = re.sub(rf'^od\s*|{GOD}$', '', s.strip(), flags=re.I)
    m = re.fullmatch(rf'{QUAL}({MON})\s?(?:-|–|—|\sdo\s)\s?({MON})\s({Y})', s, re.I)
    if m:
        y = int(m.group(3))
        return (y, MONTH_OF[m.group(1).lower()], 0), (y, MONTH_OF[m.group(2).lower()], 0)
    m = re.fullmatch(rf'{QUAL}({ONE})\.?\s?(?:-|–|—|\sdo\s)\s?({ONE})', s, re.I)
    if m:
        a, b = parse_one(m.group(1)), parse_one(m.group(2))
        if a and b and a[:2] <= b[:2]:
            return a, b
    one = parse_one(s)
    return (one, None) if one else None


def iso(d: tuple) -> str:
    y, m, day = d
    return f'{y}' + (f'-{m:02d}' if m else '') + (f'-{day:02d}' if m and day else '')


# ── the steps ───────────────────────────────────────────────────────────────
# the place after a date: "ranjen 20. aprila 1945. kod Vrčin Dola", "zarobljen ... na Mokrcu"
CAP = '(?-i:[A-ZČĆŽŠĐ])'                                       # a capital, even in a rule read without case
PLACE_AFTER = (rf'(?:\s*(?:,\s*)?(?P<place>(?:kod|na|u|pri|v|iznad|blizu)\s+(?:s\.\s|sela\s|selu\s)?{CAP}'
               r'(?:(?!\s(?:i|in|pa|a|te|gde|gdje|kada|kad|od|kao|sa|s|u\s+borbi|u\s+napadu)\b)[^,.;()\d]){1,40}))?')
DUTY = (r'(?:(?:zam(?:j)?enik|pomoćnik|pompćnik)\s+)?(?:(?:politički|polit\.|političkog|polit\.)\s+)?'
        r'(?:komandant\w*|komandir\w*|komesar\w*|delegat\w*|načelnik\w*|intendant\w*|referent\w*|sekretar\w*|rukovodil\w*|'
        r'vodnik|desetar|ekonom|zastavnik|general\w*|pukovnik|potpukovnik|major|kapetan|poručnik|potporučnik)'
        r'(?:\s+(?:štaba\s+)?(?:\d{1,2}\.\s*|(?-i:[IVX]{1,4})\.?\s*)?(?:[a-zčćžšđ]+(?:skog|ske|čkog|čke|škog|ške|ckog|cke)\s+)?'
        r'(?:prolet\.\s+|proleterske\s+|udarne\s+)?'
        r'(?:(?:brigadnog|bataljonskog|divizijskog|četnog)\s+)?'
        r'(?:odeljenja|odjeljenja|desetine|voda|čete|baterije|bataljona|brigade|divizije|korpusa|odreda|štaba|grupe|komande|saniteta))*')
# where a soldier joined, printed after the date: "U NOV od 15. 7. 1944. u 2. dalm. brigadi"
INTO = r'(?P<into>\.?\s*u\s+(?:\d{1,2}\.\s*)?(?:[\w.]+\s+){0,2}(?:brigadi|odredu|bataljonu|četi)\b)?'
WOUND = (r'(?:(?:teško|teže|lakše|lako|ponovo|smrtno)\s+)?(?:ranjen[a]?|kontuzovan[a]?|kontuzijom)(?![a-zčćžšđ])'
         r'(?:,?\s*(?:teže|teško|lakše|lako)\.?)?(?:\s*\([^)]{0,20}\))?(?:\s+noću)?')
CAUGHT = r'(?:zarobljen[a]?|ujet[a]?|uhapšen[a]?|uhvaćen[a]?)(?![a-zčćžšđ])(?:\s+od\s+[a-zčćžšđ]+)?'
ILL = r'(?:obole[oa]\w*|razbole[oa]\w*|promrz\w+(?:\s+mu\s+noge)?)(?![a-zčćžšđ])'
# the place before the date: "Ranjen na Gračacu 14. 01. 1943", "ranjena kod Ležimira novembra 1944"
PLACE_BEFORE = (rf'\s+(?P<place>(?:kod|na|u|pri)\s+{CAP}'
                r'(?:(?!\s(?:i|in|pa|a|te|gde|gdje|kada|kad|od|kao|sa|s)\b)[^,.;\d()]){1,30}?)\s+')
# the unit, also as the text layer garbles it: "Brngadi", "Bršadi", "Brigadp" (4. srpska)
BRIGADE = r'[Bb]r[inš]g?ad[a-zp]'
# sent or transferred elsewhere, and where: "prekomandovan u 5. brigadu", "upućen u bolnicu Sehovići"
MOVED_WORD = r'(?:prekomand\w+|premje?šten[a]?|upućen[a]?)(?![a-zčćžšđ])'
MOVED = rf'{MOVED_WORD}(?:\s+(?:u|na|za)\s+[^.,;()\d]{{2,40}}?(?=[.,;(]|\s\d|$))?'
I = re.I

RULES = [
    # "član SKOJ-a od 1942", "Član SKOJ-a od decembra 1943", "Član SKOJ-a 1941."
    ('skoj', rf'\b[čc]lan\w*\s+SKOJ(?:-a)?\s+(?:od\s+)?(?P<when>{WHEN})', I),
    # "član KPJ od 1940", "..., a KPJ od juna 1944", "primljen u KPJ 1942", "Član SKOJ-a od 1932. KPJ od 1940."
    ('kpj', rf'(?:\b[čc]lan\w*\s+|,\s*a\s+(?:[čc]lan\w*\s+)?|\bprimljen\w*\s+u\s+|(?<=[.;]\s))(?-i:KPJ|KP|SKJ|Partij\w+)\b\s*(?:od\s+)?'
            rf'(?P<when>{WHEN})', I),
    # "u NOB od avgusta 1941", "U NOB-1944.", "stupio u NOVJ 1943", "u NOB stupio 1942. godine", "V NOB od 25. I 1944"
    # and "U IOVJ" (the text layer), "u NOB i u Brigadi od 8. 10. 1944" (both), "borac od 14. 10. 1944"
    ('nob', rf'(?:\b[UuV][\s.]?(?:NOB|NOIB|NOV|NOVJ|IOVJ|NOR|NOP)(?:-[iu])?|\b[Ss]tupi\w*\s+u\s+(?:NOB|NOV|NOVJ|NOR|partizan\w*)|\bu\s+partizan\w*'
            rf'|\b[Bb]orac\s+od(?=\s*\d)|(?<=[,.;]\s)(?:NOB|NOV|NOVJ)\b)'
            rf'\s*(?:-|—)?\s*(?:i\s+(?:u\s+)?[Bb]rigad\w*\s+)?(?:je\s+)?(?:stupi\w*\s+)?(?P<when>{WHEN}){INTO}', 0),
    # "U Čačanski NOP odred stupio 10. VII 1941."
    ('nob', rf'\b[Uu]\s+(?P<what>[A-ZČĆŽŠĐ]\w+\s+(?:NOP\s+|partizansk\w+\s+)?odred)\s+(?:je\s+)?stupi\w*\s+(?P<when>{WHEN})', 0),
    # "u brigadi od decembra 1941", "U 2. dalm. brigadi od prosinca 1942", "a u Brigadu oktobra 1943", "U brigadu
    # došao januara 1945", "U Odredu od 20. 10. 1944. do 15. 5. 1945", "u Brigadiod20. oktobra 1944" (glued)
    ('unit', rf'\b[Uu]\s+(?:\d{{1,2}}\.\s*[\w.]+\s+(?:prolet\.\s+|proleterskoj\s+)?)?(?:{BRIGADE}|[Oo]dred[u]?|[Dd]iviziji|[Dd]iviziju)'
             rf',?\s*(?:je\s+)?(?:stupi\w*\s+|doša[ol]\w*\s+|preša[ol]\w*\s+|upućen\w*\s+)?(?P<when>{WHEN})', 0),
    # "U 2. dalm. od 3. 10. 1942." (2. dalmatinska names its brigade so), "stupio u 7. brigadu, januara 1945."
    ('unit', rf'\b[Uu]\s+\d{{1,2}}\.\s*[\'’]?dalm\.\s+(?:brigadi,?\s+)?(?P<when>(?:od\s*)?{WHEN})', 0),
    ('unit', rf'\b[Ss]tupi\w*\s+u\s+\d{{1,2}}\.\s*brigadu,?\s*(?P<when>{WHEN})', 0),
    # "borac 3. brigade od 15. januara 1945" (Treća proleterska)
    ('unit', rf'\b[Bb]orac\s+\d{{1,2}}\.\s+brigade\s+(?P<when>od\s*{WHEN})', 0),
    # "NOP-u pristupio oktobra 1943" (11. dalmatinska)
    ('nob', rf'\bNOP-u\s+pristupi\w*\s+(?P<when>{WHEN})', 0),
    # "u KPO od srpnja 1943" (the Kalnički partizanski odred's own book)
    ('unit', rf'\b[Uu]\s+KPO\s+(?P<when>(?:od\s*)?{WHEN})', 0),
    # "Marta meseca 1945. godine prekomandovan", "Lipnja 1943. upućen u bolnicu Sehovići", "premješten u 3. bataljon"
    ('moved', rf'(?P<when>{WHEN})\.?\s*,?\s*(?:je\s+)?(?P<what>{MOVED})', I),
    ('moved', rf'\b(?P<what>{MOVED})\s*,?\s*(?P<when>{WHEN})', I),
    # "ranjen 20. aprila 1945. kod Vrčin Dola", "Ranjen20. aprila 1945", "Ranjen (verovatno) 20. aprila 1945",
    # "Ranjen u ofanzivi 1945. godine", "u spisku ranjenih 12. 4. 1945", "Kontuzovan ..."
    ('wounded', rf'\b(?:{WOUND}|u\s+spisku\s+ranjenih)(?:\s*\([^)]{{0,20}}\))?,?\s*(?:je\s+)?(?:u\s+(?:borbi|ofanzivi|napadu)\s+)?'
                rf'(?P<when>{WHEN}){PLACE_AFTER}', I),
    ('wounded', rf'\b{WOUND}{PLACE_BEFORE}(?P<when>{WHEN})', I),
    ('wounded', rf'(?P<when>{WHEN})\s*,?\s*(?:je\s+)?{WOUND}{PLACE_AFTER}', I),
    # "zarobljen 20. 9. 1944", "aprila 1944. zarobljena", "Decembra 1943. godine zarobljen", "zarobljen od ustaša
    # 25. 12. 1942", "ujet" (Slovene)
    ('captured', rf'\b{CAUGHT},?\s*(?:je\s+)?(?P<when>{WHEN}){PLACE_AFTER}', I),
    ('captured', rf'\b{CAUGHT}(?:\s+u\s+borbi)?{PLACE_BEFORE}(?P<when>{WHEN})', I),
    ('captured', rf'(?P<when>{WHEN})\s*,?\s*(?:je\s+)?{CAUGHT}{PLACE_AFTER}', I),
    # "Oboleo februara 1945", "Promrzle mu noge 14. januara 1945", "promrzao ... krajem januara 1943"
    ('ill', rf'\b(?P<what>{ILL})\s*,?\s*(?:je\s+)?(?:od\s+\w+\s+)?(?P<when>{WHEN}){PLACE_AFTER}', I),
    ('ill', rf'\b(?P<what>{ILL}){PLACE_BEFORE}(?P<when>{WHEN})', I),
    # "zamijenjen 30. 10. 1944" (a prisoner exchanged)
    ('exchanged', rf'\b(?:zami?jenjen[a]?|razmi?jenjen[a]?|razmenjen[a]?|zamenjen[a]?)\b\s*(?P<when>{WHEN})', I),
    # "otpušten iz odreda", "demobilisan 1945"
    ('left', rf'\b(?P<what>(?:otpušten[a]?|demobili[sz]an[a]?)\b(?:\s+iz\s+\w+)?)\s*(?P<when>{WHEN})', I),
    ('left', rf'(?P<when>{WHEN})\s*,?\s*(?:je\s+)?(?P<what>(?:otpušten[a]?|demobili[sz]an[a]?)\b(?:\s+iz\s+\w+)?)', I),
    # a duty from a date: "komandant 1. bataljona januar-mart 1943", "zamjenik komandanta brigade od marta do juna 1943",
    # "zamjenik komandanta 4. bataljona od 17. maja 1944"; or the date first: "aprila 1944. komandant 5. ruskog bataljona"
    # Not a duty after a bare date or a comma: "1928, Burćevo, 20.10.1944, komandir čete" (7. vojvođanska) and "U 2. dalm.
    # brigadi od 3. 10. 1942. Komandant bataljona" give the day he came, not the day the duty began
    ('duty', rf'(?<![\w-])(?P<what>{DUTY})\s+(?P<when>{WHEN})', I),
    ('duty', rf'(?P<when>{WHEN})\.?\s*,?\s*(?:postao|postala|postavljen\w*\s+za|imenovan\w*\s+za)\s+(?P<what>{DUTY})(?![\w-])', I),
]
RULES = [(k, re.compile(rx, fl)) for k, rx, fl in RULES]
# Words a kind's rules cannot match without: a text that has none of them skips those rules (a pass over every unit
# would otherwise try each date-first rule at every character)
GATE = {
    'skoj': ('skoj',), 'kpj': ('kpj', 'kp ', 'skj', 'partij'),
    'nob': ('nob', 'nov', 'iovj', 'noib', 'nor', 'nop', 'stupi', 'partizan', 'borac od', 'pristupi'),
    'unit': ('brig', 'bršad', 'brngad', 'odred', 'divizij', 'dalm', 'stupi', 'borac', 'kpo'),
    'wounded': ('ranj', 'kontuz'), 'captured': ('zarob', 'ujet', 'uhapš', 'uhvać'), 'ill': ('obole', 'razbole', 'promrz'),
    'exchanged': ('mijenjen', 'menjen'), 'left': ('otpušt', 'demobil'), 'moved': ('prekomand', 'mješten', 'mešten', 'upućen'),
    'duty': ('koman', 'komes', 'deleg', 'načel', 'intend', 'refer', 'sekret', 'rukovod', 'vodnik', 'desetar', 'ekonom',
             'zastav', 'general', 'pukov', 'major', 'kapetan', 'poručn'),
}

ORDER = ['born', 'skoj', 'kpj', 'nob', 'unit', 'duty', 'moved', 'wounded', 'ill', 'captured', 'exchanged', 'left', 'death']
ONCE = {'born', 'skoj', 'kpj', 'nob', 'unit', 'death'}          # one step of these per soldier
DEATH_WORD = re.compile(r'\b(?:poginu\w*|pog\.(?=\s)|pognu\w*|padel\w*|padl\w*|umr\w*|preminu\w*|podlega\w*|podlegl\w*|nesta[ol]\w*|'
                        r'stri?jeljan\w*|streljan\w*|ustreljen\w*|ubijen\w*|ubit\w*|zaklan\w*|utopi\w*|smrtno\s+ponesreči\w*)', re.I)
# A date that belongs to something that is no step of a life
NOT_A_STEP = re.compile(r'spomenic\w*\s*(?:»|«|")?\s*(?:od\s+)?1941|1941\s*(?:»|«|")', re.I)


def in_war(d: tuple, kind: str) -> bool:
    lo = 1919 if kind in ('skoj', 'kpj') else 1941
    hi = 1946 if kind not in ('left',) else 1947
    return lo <= d[0] <= hi


# Abbreviations printed in capitals inside a bio; two other words in capitals are the next soldier's name, glued on
# where the parser missed his entry ("... ranjen 1945. 1D AVIDOVIĆ NIKOLA, r. 1924, ...", 32. Zagorska)
CAPS_WORDS = {'KPJ', 'SKOJ', 'SKJ', 'NOB', 'NOV', 'NOVJ', 'NOR', 'NOP', 'NOO', 'JNA', 'SSSR', 'AVNOJ', 'KNOJ', 'OZNA', 'NDH',
              'ZAVNOH', 'USAOJ', 'SUBNOR', 'AFŽ', 'SAD', 'SFRJ', 'PKJ', 'VOS', 'SNOS', 'ZAVNOBIH', 'ASNOM', 'IOVJ', 'NOIB'}
GLUED_NAME = re.compile(r'(?<![\w-])([A-ZČĆŽŠĐ]{3,})\s+\(?([A-ZČĆŽŠĐ]{3,})\b')


def own_part(text: str) -> str:
    """The entry up to another soldier's name glued on after it"""
    for m in GLUED_NAME.finditer(text):
        if m.start() > 0 and m.group(1) not in CAPS_WORDS and m.group(2) not in CAPS_WORDS:
            return text[:m.start()]
    return text


def read_entry(text: str) -> list[dict]:
    """The dated steps one entry's text gives (birth and death are added from the fields)"""
    text = own_part(text)
    low = text.lower()
    found, taken = [], []
    for kind, rx in RULES:
        if not any(word in low for word in GATE[kind]):
            continue
        for m in rx.finditer(text):
            span = m.span('when')
            if any(a < span[1] and span[0] < b for a, b in taken):
                continue                                                 # a date read once
            if NOT_A_STEP.search(text[max(0, span[0] - 25):span[1] + 3]):
                continue
            # a duty named with the death is the duty he fell in, not a step of its own: "poginuo ..., 2. maj 1945,
            # politički delegat voda", "umro ... kao komandir voda"
            if kind == 'duty' and DEATH_WORD.search(text[max(0, m.start() - 60):m.start()]):
                continue
            when = parse_when(m.group('when'))
            if not when or not in_war(when[0], kind):
                continue
            start, end = when
            step = {'k': kind, 'd': iso(start), 'at': trimmed(text, m.start(), m.end()), '_at': m.start(), '_span': span}
            if end and end != start:
                step['e'] = iso(end)
            groups = m.groupdict()
            x = groups.get('what') or groups.get('into') or groups.get('place')
            if x:
                step['x'] = re.sub(r'\s+', ' ', x).strip(' ,.')
            found.append(step)
            taken.append(span)
    return found


def death_phrase(text: str) -> tuple[int, str] | None:
    """Where the entry tells the death: the death word to the end of its clause"""
    m = DEATH_WORD.search(text)
    if not m:
        return None
    rest = text[m.start():]
    clause = sentences(rest)[0] if rest.strip() else rest
    clause = re.split(r';|[,.]?\s*(?:sahranjen|sahranjena|pokopan|mesto sahrane|mjesto sahrane)\b', clause)[0]
    return m.start(), clause.strip(' ,;.')


def born_phrase(text: str, year: str) -> tuple[int, str, tuple] | None:
    """The birth date as printed (a whole date where the book gives one) and its words"""
    m = re.search(rf'(?:\b[Rr][oođ]?đen[a]?\s+(?:je\s+)?)?(?P<when>{ONE}){GOD}', text[:80])
    if not m or year not in m.group('when'):
        return None
    d = parse_one(m.group('when'))
    return (m.start(), text[m.start():m.end()].strip(' ,;.'), d) if d else None


def trimmed(text: str, a: int, b: int) -> list[int]:
    """[start, end] of text[a:b] without the punctuation and spaces at its ends"""
    while a < b and text[a] in ' ,;.':
        a += 1
    while b > a and text[b - 1] in ' ,;.':
        b -= 1
    return [a, b]


def phrase_of(s: dict, e: dict) -> str:
    """The words a step was read from, as printed"""
    if 'at' not in e:
        return ''
    entry = ([s] + list(s.get('other_sources') or []))[e.get('s', 0)]
    return (entry.get('additional_info') or '')[e['at'][0]:e['at'][1]]


def life_events(s: dict, code: int) -> list[dict]:
    entries = [s] + list(s.get('other_sources') or [])
    steps: list[dict] = []
    if code not in PARSER_FIELDS:
        for i, e in enumerate(entries):
            for step in read_entry(e.get('additional_info') or ''):
                step['s'] = i
                steps.append(step)
    own = s.get('additional_info') or ''
    year = re.search(r'(?:18|19)\d\d', s.get('birth_year') or '')
    if year:
        born = born_phrase(own, year.group(0))
        d = born[2] if born else (int(year.group(0)), 0, 0)
        step = {'k': 'born', 'd': iso(d), 's': 0, '_at': born[0] if born else -1}
        if born:
            step['at'] = [born[0], born[0] + len(born[1])]
        steps.append(step)
    if s.get('death_date'):
        when = parse_when(s['death_date'])
        if when and 1941 <= when[0][0] <= 2000:
            step = {'k': 'death', 'd': iso(when[0]), 's': 0, '_at': 10 ** 6}
            for i, e in enumerate(entries):
                ph = death_phrase(e.get('additional_info') or '')
                if ph:
                    step['at'], step['s'], step['_at'] = [ph[0], ph[0] + len(ph[1])], i, ph[0]
                    break
            steps.append(step)
    # one of each kind that happens once: the soldier's own entry wins over another book's
    kept, seen = [], set()
    for st in sorted(steps, key=lambda st: (st['s'], st.get('_at', 0))):
        key = st['k'] if st['k'] in ONCE else (st['k'], st['d'], st.get('x'))
        if key in seen:
            continue
        seen.add(key)
        kept.append(st)

    def when_key(st):
        y, *rest = (int(p) for p in st['d'].split('-'))
        return (y, rest[0] if rest else 0, rest[1] if len(rest) > 1 else 0, ORDER.index(st['k']), st.get('_at', 0))
    out = []
    for st in sorted(kept, key=when_key):
        st = {k: v for k, v in st.items() if not k.startswith('_')}
        if not st.get('s'):
            st.pop('s', None)
        out.append(st)
    return out


def middle_steps(events: list[dict]) -> int:
    return sum(1 for e in events if e['k'] not in ('born', 'death'))


def shows_line(events: list[dict]) -> bool:
    """The dialog draws the line from three steps on (birth, one step, death), or two steps between them"""
    return len(events) >= 3 or middle_steps(events) >= 2


def unit_events(code: int, data: list[dict]) -> dict[str, list[dict]]:
    """Each soldier's steps whose line the dialog draws, by soldier_id, in the data file's order"""
    out = {}
    for s in data:
        ev = life_events(s, code)
        if shows_line(ev):
            out[s['soldier_id']] = ev
    return out


def write_events(brigades: dict) -> dict[str, int]:
    """website/data/life-events/<data file>: the steps of every soldier with a line, for the records the dialog
    loads (app/records/[unit]/[part]/route.ts merges them in as life_events). Returns soldiers per file written."""
    OUT.mkdir(parents=True, exist_ok=True)
    written = {}
    for code, (fname, data) in brigades.items():
        events = unit_events(code, data)
        path = OUT / fname
        if not events:
            path.unlink(missing_ok=True)                                 # no soldier of this unit has a line
            continue
        text = json.dumps(events, ensure_ascii=False, separators=(',', ':'))
        if not path.exists() or path.read_text(encoding='utf-8') != text:
            path.write_text(text, encoding='utf-8')
        written[fname] = len(events)
    return written


def leftovers(s: dict, code: int) -> list[str]:
    """Dates in the soldier's own entry that no rule (and not the birth or death) reads"""
    text = re.sub(r'\s+', ' ', s.get('additional_info') or '')
    taken = [st['_span'] for st in read_entry(text)]
    out = []
    dm = DEATH_WORD.search(text)
    for m in ANY_DATE_RE.finditer(text):
        if any(a < m.end() and m.start() < b for a, b in taken):
            continue
        if m.start() < 25 or (dm and m.start() > dm.start()) or NOT_A_STEP.search(text[max(0, m.start() - 25):m.end() + 3]):
            continue                                                     # birth at the start, the death clause
        if not re.search(r'19[34]\d', m.group(0)):
            continue
        out.append(text[max(0, m.start() - 45):m.end() + 10])
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--brigade', type=int, help='only this unit code')
    ap.add_argument('--sample', type=int, default=3, help='samples to print per unit')
    ap.add_argument('--leftover', type=int, default=0, help='print this many dated phrases no rule reads')
    ap.add_argument('--check', type=int, default=0, help='print this many random steps of each kind, from all units')
    ap.add_argument('--write', action='store_true', help='write website/data/life-events/ (all units, or --brigade N)')
    args = ap.parse_args()

    if args.write:
        brigades = {c: v for c, v in load_live().items() if not args.brigade or c == args.brigade}
        written = write_events(brigades)
        size = sum((OUT / f).stat().st_size for f in written)
        print(f'{sum(written.values())} soldiers with a line in {len(written)} files, {size / 1e6:.1f} MB, in {OUT}')
        return

    if args.check:
        random.seed(5)
        by_kind: dict[str, list] = {}
        for code, (_, data) in load_live().items():
            for s in data:
                for e in life_events(s, code):
                    by_kind.setdefault(e['k'], []).append((code, s, e))
        for kind in ORDER:
            items = by_kind.get(kind, [])
            print(f'\n== {kind} ({len(items)})')
            for code, s, e in random.sample(items, min(args.check, len(items))):
                span = f"{e['d']}{'–' + e['e'] if e.get('e') else ''}"
                print(f"   {code:2d} {span:23s} {e.get('x', '')[:34]:34s} | {phrase_of(s, e)[:90]}")
        return

    random.seed(2)
    brigades = load_live()
    tot = Counter()
    kinds_all = Counter()
    left = []
    print(f"{'unit':30s} {'records':>7s} {'1+ step':>8s} {'2+ steps':>8s} {'line':>6s}   kinds")
    for code, (_, data) in brigades.items():
        if args.brigade and code != args.brigade:
            continue
        one = two = line = 0
        kinds, samples = Counter(), []
        for s in data:
            ev = life_events(s, code)
            mid = middle_steps(ev)
            one += mid >= 1
            two += mid >= 2
            line += len(ev) >= 3 or mid >= 2                             # the dialog shows the line from three steps
            kinds.update(e['k'] for e in ev)
            if mid:
                samples.append((s, ev))
            if args.leftover:
                left.extend(leftovers(s, code))
        n = len(data)
        tot.update(records=n, one=one, two=two, line=line)
        kinds_all.update(kinds)
        pct = lambda v: f'{100 * v / n:5.1f}%' if n else '   -'
        print(f"{BRIGADE_CONFIGS[code]['name'][:30]:30s} {n:7d} {pct(one):>8s} {pct(two):>8s} {pct(line):>6s}   "
              + ', '.join(f'{k} {v}' for k, v in sorted(kinds.items(), key=lambda kv: ORDER.index(kv[0])) if k not in ('born', 'death')))
        for s, ev in random.sample(samples, min(args.sample, len(samples))):
            print(f"      {s['additional_info'][:150]!r}")
            for e in ev:
                print(f"         {e['d']:10s}{('–' + e['e']) if e.get('e') else '':12s} {e['k']:9s} {e.get('x', ''):30s} | {phrase_of(s, e)[:60]}")
    n = tot['records']
    print(f"\nAll units: {n} records; a step between birth and death: {tot['one']} ({100 * tot['one'] / n:.1f}%), "
          f"two or more: {tot['two']} ({100 * tot['two'] / n:.1f}%), a line of three steps or more: {tot['line']} ({100 * tot['line'] / n:.1f}%)")
    print('Steps:', ', '.join(f'{k} {v}' for k, v in sorted(kinds_all.items(), key=lambda kv: ORDER.index(kv[0]))))
    if args.leftover:
        words = Counter()
        for ctx in left:
            w = re.findall(r'[A-Za-zČĆŽŠĐčćžšđ]{3,}', ctx[:45])
            words.update(w[-2:])
        print(f'\n{len(left)} dated phrases no rule reads; the words before them, most common:')
        print('   ', ', '.join(f'{w} {c}' for w, c in words.most_common(40)))
        for ctx in random.sample(left, min(args.leftover, len(left))):
            print('   ', repr(ctx))


if __name__ == '__main__':
    main()
