"""
Fill the structured fields shown in the soldier modal from each record's additional_info:
birth_place, ethnicity, occupation, rank, unit_detail, death_type, death_date, death_place.

Only EMPTY fields are filled; values set by corrections (or by hand) are never touched.
Precision over recall: a field is left empty unless the text says it plainly.

The books differ in layout, but share the building blocks:
    Prva proleterska   1925, Trlić, Ub, Srbija, Srbin, muzičar, u NOB od ..., IV bataljon, borac, poginuo 17. 01. 1945, Orolik, Vinkovci
    Prva lička         5. 5. 1927, Božidarevac, Trstenik, zemljoradnik, u NOB od 5. 11. 1944, 1. bataljon
    Druga lička        rođen 1924. u s. Ćuić Krčevina - T. Korenica. Borac 2. bataljona. Poginuo na Udbini 22. 08. 1942. godine
    Ljubljanska        1914, Sanski most, SR Bih, padel 1.11.1944 v Trnovcu, Metlika
    Treća proleterska  desetar 3. desetine, rođen 1920, Radoinja, Nova Varoš, radnik, član KPJ od 1941.
    13. proleterska    1923. Ljubljana. Poginuo 16. IV 1944. u Cvitanovićima kod Jajca.
    2. dalmatinska     11.11. 1923. Mali Iž, Zadar. Hrvat, zemljoradnik. U NOV od 26. 7. 1942. ... Poginuo 20. 5. 1943. na Sutjesci.
    4. splitska        1923, Donji Dolac, Omiš, 3. bat., borac, poginuo 8. 12. 1944, Inkuša, Otrić, Gračac
    Prva vojvođanska   1921, Budisava (Titel), borac, umro u bolnici, mesto smrti: Sombor
    5. kozaračka       borac, rođen 1912, u s. Gornji Usorac, Sanski Most, poginuo 3. decembra 1944, u Erdeviku, Srem
    2. vojvođanska     rođen 1920, Brajići — Boka kotorska, Crnogorac, zemljoradnik, stupio u NOVJ 1944, borac.

Death places are printed in the locative/genitive ("na Sutjesci", "kod Šida"); they are turned into the nominative
("Sutjeska", "Šid") only when that form is a known place (a birthplace or an existing death place in the data).
Otherwise the printed phrase is kept as is.

Usage:
    python scripts/extract_structured_fields.py            # dry run: coverage per brigade + samples
    python scripts/extract_structured_fields.py --apply    # write the brigade JSONs
    python scripts/extract_structured_fields.py --sample 20 --brigade 7
"""
from __future__ import annotations

import argparse
import difflib
import json
import random
import re
import sys
from collections import Counter
from itertools import product
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, str(Path(__file__).parent))
from name_utils import BRIGADE_CONFIGS  # noqa: E402
from cleanup_text_fields import live_json_files  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
FIELDS = ['birth_place', 'ethnicity', 'occupation', 'rank', 'unit_detail', 'death_type', 'death_date', 'death_place']
# Units whose parser sets the fields itself and whose text is written from them, not printed: Druga proleterska's
# list gives only names under a place and date ("poginuo 1. juna 1943, Tjentište (Sutjeska); ..."), and read again
# its campaign's period would be a death date, "poginuo ili nestao" a death
PARSER_FIELDS = {39, 121}                  # Druga proleterska; the pioneer company (its 1990s deaths are no falls)
# Borci Sutjeske prints the duty at the battle, then "krajem rata ..." the duty at the war's end: the first is the rank
DUTY_BEFORE_WAR_END = set(range(40, 50))
U, L = 'A-ZČĆŽŠĐ', 'a-zčćžšđ'

MONTHS = ('januara|februara|marta|aprila|maja|juna|jula|avgusta|augusta|septembra|oktobra|novembra|decembra|'
          'siječnja|veljače|ožujka|travnja|svibnja|lipnja|srpnja|kolovoza|rujna|listopada|studenoga?|prosinca|'
          'januar|februar|mart|april|maj|jun|jul|avgust|august|septembar|oktobar|novembar|decembar|jeseni|proleća|leta|zime|proljeća|ljeta')
YEAR = r'(?:18|19)\d\d'
DATE = (rf'(?:(?:\d{{1,2}}|00)\.\s?(?:\d{{1,2}}|[IVX]{{1,4}})\.?\s?{YEAR}'      # 17. 01. 1945 / 1.11.1944 / 16. IV 1944
        rf'|\d{{1,2}}\.?\s?(?:{MONTHS})\s{YEAR}'                              # 3. decembra 1944 / 4 januara 1945
        rf'|(?:(?:krajem|početkom|sredinom|polovinom|koncem|tokom|u toku|u)\s)?(?:{MONTHS})\s(?:mesecu\s|mjesecu\s)?{YEAR}'   # aprila 1945
        rf'|(?:(?:krajem|početkom|sredinom|polovinom|koncem|tokom|u toku|[Pp]roljeće|[Pp]roleće|[Ll]jeto|[Ll]eto|[Jj]esen|[Zz]ima)\s)?{YEAR})'
        rf'(?:\.?\s*god(?:ine|\.))?')
DATE_RE = re.compile(DATE)
MONTH_SET = set(MONTHS.split('|'))
BIRTH_DATE_RE = re.compile(rf'^(?:[Rr]ođen[a]?\s+(?:je\s+)?)?(?:{DATE}|[\s.,]*\.\.[\s.]*)[.,]?\s*')

DEATH_KW = {
    'poginuo': 'poginuo', 'poginula': 'poginuo', 'padel': 'poginuo', 'padla': 'poginuo', 'pal': 'poginuo',
    'umro': 'umro', 'umrla': 'umro', 'umrl': 'umro', 'preminuo': 'umro', 'podlegao': 'umro', 'podlegla': 'umro',
    'nestao': 'nestao', 'nestala': 'nestao', 'pogrešan': None,
    'streljan': 'streljan', 'streljana': 'streljan', 'strijeljan': 'streljan', 'strijeljana': 'streljan', 'ustreljen': 'streljan',
    'ubijen': 'ubijen', 'ubijena': 'ubijen', 'zaklan': 'ubijen', 'zaklana': 'ubijen',
}
DEATH_RE = re.compile(r'\b(' + '|'.join(k for k, v in DEATH_KW.items() if v) + r')\b', re.I)
# the next soldier's entry glued into a bio: a sentence that starts with a surname in capitals (the scan may garble
# its first letters: "iRCEGOVIĆ", "miMUNOVIĆ"); not an abbreviation such as "NOB" or "KPJ"
GLUED_RE = re.compile(r'[.;]\s+\S{0,2}(?!(?:NOB|NOV|NOVJ|NOR|NOO|NOP|KPJ|SKOJ|SSSR|JNA|BiH|SAD|SFRJ|SUBNOR|KNOJ|OZNA|UDB|AVNOJ|'
                      r'ZAVNOH|ZAVNOBiH|ASNOM|SNOS|AFŽ|USAOJ|VŠ|NDH|SS)\b)[A-ZČĆŽŠĐ]{3,}')

ETHNIC = {
    'Srbin', 'Srpkinja', 'Hrvat', 'Hrvatica', 'Crnogorac', 'Crnogorka', 'Slovenac', 'Slovenka', 'Slovenec', 'Slovenka',
    'Musliman', 'Muslimanka', 'Makedonac', 'Makedonka', 'Jevrejin', 'Jevrejka', 'Židov', 'Židovka', 'Mađar', 'Mađarica',
    'Slovak', 'Slovakinja', 'Albanac', 'Albanka', 'Šiptar', 'Rus', 'Ruskinja', 'Rumun', 'Rumunka', 'Italijan', 'Italijanka',
    'Talijan', 'Talijanka', 'Nemac', 'Nijemac', 'Čeh', 'Čehinja', 'Bugarin', 'Bugarka', 'Rusin', 'Rusinka', 'Ukrajinac',
    'Poljak', 'Poljakinja', 'Grk', 'Rom', 'Ciganin', 'Turčin', 'Jugosloven', 'Jugoslaven', 'Francuz', 'Englez', 'Austrijanac',
}

# functions / ranks, longest first; genitive forms after a number are units, not ranks
_UNITS_GEN = r'(?:odeljenja|odjeljenja|desetine|voda|čete|baterije|bataljona|brigade|divizije|korpusa|odreda|štaba)'
RANK_PATTERNS = [
    rf'zam(?:j)?enik (?:političkog |polit\. )?komesara(?: {_UNITS_GEN})?',
    rf'pomoćnik (?:političkog |polit\. )?komesara(?: {_UNITS_GEN})?',
    rf'zam(?:j)?enik komand(?:ira|anta)(?: {_UNITS_GEN})?',
    rf'(?:politički|polit\.) (?:komesar|delegat)(?: {_UNITS_GEN})?',
    rf'komesar(?: {_UNITS_GEN})',
    rf'komand(?:ir|ant)(?: {_UNITS_GEN})',
    rf'načelnik (?:štaba|saniteta)(?: {_UNITS_GEN})?',
    rf'referent (?:saniteta|za vezu|za ishranu)(?: {_UNITS_GEN})?',
    rf'sanitetski referent(?: {_UNITS_GEN})?',
    rf'obaveštajni oficir(?: {_UNITS_GEN})?', rf'obavještajni oficir(?: {_UNITS_GEN})?',
    rf'(?:omladinski|skojevski) rukovodilac(?: {_UNITS_GEN})?', rf'sekretar SKOJ-a(?: {_UNITS_GEN})?',
    rf'intendant(?: {_UNITS_GEN})?', rf'ekonom(?: {_UNITS_GEN})?',
    r'(?:vodni|četni|politički) delegat', r'delegat voda',
    r'(?:mlađi|stariji) vodnik', r'(?:ml|st)\.\s?vodnik', r'vodnik I\. klase', r'kapetan I\. klase',
    r'general-(?:major|lajtnant|potpukovnik)',
    r'borac', r'borec', r'kuvar(?:ica)?', r'kuhar(?:ica)?', r'bolničar(?:ka)?', r'kurir(?:ka)?', r'desetar', r'vodnik', r'podnarednik', r'narednik', r'zastavnik',
    r'potporučnik', r'poručnik', r'kapetan', r'major', r'potpukovnik', r'pukovnik',
    r'puškomitraljezac', r'mitraljezac', r'nišand[žz]ija', r'minobacačlija', r'bombaš', r'izviđač', r'obave[šs]tajac', r'obavještajac',
    r'telefonist(?:a|kinja)', r'telegrafist(?:a|kinja)', r'radiotelegrafist(?:a|kinja)', r'vezist(?:a|kinja)',
]
RANK_RE = re.compile(r'(?<![\w-])(' + '|'.join(RANK_PATTERNS) + r')(?![\w-])', re.I)

# A sub-unit named without a number is no place either: "Jurišna četa", "PK baterija", "Bat. pri diviziji",
# "Zamjenik (pomoćnik) komesara bataljona"
UNIT_WORD_RE = re.compile(r'\bčet[aeiu]\b|bataljon|\bbat\.|baterij', re.I)
UNIT_RE = re.compile(r'(?<![\w.])(\d{1,2}\.|[IVX]{1,4}\.?)\s?(četa|čete|četi|č\.?|bataljon|bataljona|bataljonu|bat\.?|desetina|desetine|vod|voda|vodu)'
                     r'(?![\w])', re.I)
SPECIAL_UNITS = [
    (re.compile(r'\b(\d\.\s?(?:kordunaški|makedonski|slovenački|slovenski|ličk[i]|dalmatinski|udarni|omladinski))\s+bataljon', re.I), '{} bataljon'),
    (re.compile(r'\bprateć(?:a|e|oj)\s+čet[aeiu]\b', re.I), 'prateća četa'),
    (re.compile(r'\bomladinsk(?:a|e|oj) čet[aei]', re.I), 'omladinska četa'),
    (re.compile(r'\bradn(?:a|e|oj)\s+čet[aeiu]\b', re.I), 'radna četa'),
    (re.compile(r'\bbataljon(?:a|u)? Garibaldi', re.I), 'bataljon Garibaldi'),
    (re.compile(r'\bprištapsk(?:e|ih) jedinic', re.I), 'prištapske jedinice'),
    (re.compile(r'\b(izviđačk|inžinjerijsk|protivtenkovsk|protivavionsk|protivoklopn|prištapsk|sanitetsk|mitraljesk)(?:a|e|oj)\s+čet[aei]\b', re.I), '{}a četa'),
    (re.compile(r'\bčet[aei]\s+za\s+vezu\b', re.I), 'četa za vezu'),
    (re.compile(r'\b(protivtenkovsk|protivavionsk|artiljerijsk)(?:a|e|oj)\s+baterij[aei]\b', re.I), '{}a baterija'),
    (re.compile(r'\bintendantur(?:a|e|i)\b', re.I), 'intendantura'),
]

# the soldier's duty printed after where he fell, to the end (8. krajiška ends every bio so); all lowercase,
# so a name glued on after it (5. kozaračka, 21. slavonska) keeps the clause from passing for a place
DUTY_AFTER_PLACE = re.compile(
    r',\s*(?:[a-z]\s+)?(?:(?:politi\w+|zamjenik\w*|zamenik\w*|pomoćnik\w*|pompćnik\w*)\s+)*'
    r'(?:komandir\w*|komandant\w*|komesar\w*|vodnik|desetar|ekonom|četn\w+\s+bolničar\w*|bolničar\w*|borac|kurir|'
    r'intendant\w*|\w*mitraljez\w*)\b[^A-ZČĆŽŠĐ]*$')
PREP = r'(?:u|na|kod|v|pri|nad|pod|iznad|ispod|blizu|kraj|pored|oko|između|izmedu|prema|pred|za|iz|na putu za|u selu|u s\.|s\.|selo|u rejonu|rejon)'
STOP_PLACE = re.compile(r'^(?:u NOB|u NOV|u NOVJ|u NOR|u brigadi|u \d|član|stupio|stupila|borac od|od \d|od [a-z]|sa |iz |zvan[ai]|ili |'
                        r'drugih|nema |ostali|nepoznat|\(drugih|\(nema|\(nedostaju)', re.I)

# Books whose list has no column for a trade: 22. divizija (birthplace | date | place of death), 34. divizija (duty,
# brigade, birth, joined, place and date of death: its duty "miner" is a sapper, "Mrežn. Venac" a village)
NO_OCCUPATION = {96, 97}
# 34. divizija's column "Datum pogibije" as the book abbreviates it: "07.09.44", "04.1945", "trav. 45", "jes.1944"
HR_MONTHS = ('siječnja', 'veljače', 'ožujka', 'travnja', 'svibnja', 'lipnja', 'srpnja', 'kolovoza', 'rujna', 'listopada',
             'studenoga', 'prosinca')
HR_MONTH_STEMS = (('sij', 1), ('velj', 2), ('ožuj', 3), ('trav', 4), ('svib', 5), ('lip', 6), ('srp', 7), ('kolov', 8),
                  ('ruj', 9), ('list', 10), ('stud', 11), ('pros', 12))
HR_SEASONS = (('prolj', 'proljeća'), ('jes', 'jesen'), ('ljet', 'ljeto'), ('kraj', 'krajem'))   # "pro." is spring or December
# 6. dalmatinska's place of death as its parser takes it: "za Knin", "kod Mokrog Polja", "kod Livna, Dragnić"; not one
# the scan garbled ("za Sop-Ije", "kod Ur~ kiča", "za Dragi nić", "kod Kule Atlagića lì. VI")
_NAME_103 = rf'[{U}][{L}]+(?:\s+(?:[{U}][{L}]+|kod|na)){{0,3}}'
PLACE_103 = re.compile(rf'(?:{PREP}\s+)?{_NAME_103}(?:,\s+{_NAME_103})*')


ABBREV = {'Podr', 'Grub', 'Bos', 'Vel', 'Gor', 'Gornj', 'Donj', 'Mal', 'Slav', 'Pož', 'Nov', 'Star', 'Dol', 'Hrv', 'Sjev', 'Sev',
          'Juž', 'Zap', 'Ist', 'Crn', 'Kos', 'Mitr', 'Aleks', 'Petr', 'Brd', 'Polj', 'Sel', 'Gradiš', 'Orah', 'Mikl'}


def sentences(t: str) -> list[str]:
    """Split at sentence ends, not at the dots of dates, abbreviations ("Podr. Slatina") or initials."""
    out, start = [], 0
    for m in re.finditer(rf'(?:(?<=[{L}]{{3}})|(?<=[{L}]\))|(?<=\d{{4}}))\.\s+(?=[{U}])', t):
        word = re.search(r'(\w+)$', t[:m.start()])
        if word and word.group(1) in ABBREV:
            continue
        out.append(t[start:m.start()])
        start = m.end()
    out.append(t[start:])
    return [p for p in out if p]


def clean_segment(s: str) -> str:
    return re.sub(r'\s+', ' ', s).strip(' .,;:-—\'"«»')


def looks_ethnic(s: str) -> bool:
    """An OCR-damaged ethnicity ("Srbvd") is not a place."""
    return len(s) <= 10 and ' ' not in s and any(
        difflib.SequenceMatcher(None, s, e).ratio() >= 0.75 for e in ('Srbin', 'Hrvat', 'Srpkinja', 'Crnogorac', 'Musliman'))


def is_placeholder(s: str) -> bool:
    return not re.search(r'[^\s.,…]', s)


FOLD = str.maketrans('čćđšž', 'ccdsz')
# Short words that end a trade honestly ("kmečki sin", "kmečka hči"); any other of three letters or fewer at the end
# of one is an abbreviation cut off at its dot: "podoficir bjv", "podoficir biv. RM", "radnik čl."
SHORT_TAILS = {'sin', 'hči'}
# a duty in a unit, printed where a trade could stand: "četna bolničarka"
UNIT_DUTY_RE = re.compile(r'^(?:četn|vodn|bataljonsk|brigadn|divizijsk|korpusn)\w*\s')


def plausible_occupations(occ: Counter) -> Counter:
    """The words read as trades, without a stray letter ("ž"), a word cut short ("zemlj." for zemljoradnik, "radni"),
    an abbreviation left at the end ("podoficir bjv") or a duty ("četna bolničarka")."""
    whole = {o: n for o, n in occ.items() if ' ' not in o and n >= 50}

    def ok(w: str) -> bool:
        tokens = w.split()
        if len(w) < 3 or not re.search('[aeiou]', w):
            return False
        if len(tokens) > 1 and whole.get(''.join(tokens), 0) >= 20 * occ[w]:
            return True                                                     # a word split in two: "kroj ač"
        if len(tokens) > 1 and len(tokens[-1]) <= 3 and tokens[-1] not in SHORT_TAILS:
            return False
        if UNIT_DUTY_RE.match(w) and RANK_RE.search(w):
            return False
        # the start of a far more common trade, cut there ("zemlj", "radni"); not a word of its own ("stolar")
        return not (len(tokens) == 1 and any(o.startswith(w) and len(o) > len(w) and n >= 20 * occ[w]
                                             for o, n in whole.items()))
    return Counter({w: n for w, n in occ.items() if ok(w)})


def same_word(a: str, b: str) -> bool:
    """b is a, misread: a letter read wrong ("zemljoradiik", "domađica", "radnmk"), its marks lost ("dak" for đak), or
    in a long word a letter more or less, or two read wrong ("zemljradnik", "zemljroadnik"). Never another word read
    into it: "kotlar" is not "kolar", "učesnik" not "učenik", "seljanka" not "seljak", "podoficir biv" not
    "podoficir bjv", the genitive "zemljoradnika" not the woman's "zemljoradnica", the Slovene "trgovec" and
    "študent" not "trgovac" and "student"."""
    if a.translate(FOLD) == b.translate(FOLD):
        return a.translate(FOLD) == a
    ta, tb = a.split(), b.split()
    if len(ta) != len(tb) or sum(x != y for x, y in zip(ta, tb)) != 1:
        return False
    a, b = next((x, y) for x, y in zip(ta, tb) if x != y)
    if a[0] != b[0] or a[-1] != b[-1]:
        return False
    if len(a) != len(b):
        return min(len(a), len(b)) >= 9 and abs(len(a) - len(b)) == 1 and difflib.SequenceMatcher(None, a, b).ratio() >= 0.9
    diff = [(x, y) for x, y in zip(a, b) if x != y]
    if len(diff) == 1:
        (x, y), = diff
        if {x, y} == {'k', 'c'} or (x in 'aeiou' and y in 'aeiou' and len(a) < 9):
            return False
        return len(a) >= 6
    return len(diff) == 2 and len(a) >= 9


class Extractor:
    def __init__(self, occupations: Counter, places: Counter):
        self.occupations = set(occupations)
        self.places = places
        # OCR-misspelt occupations map to the common spelling: "zemljradnik", "zemljoradiik" -> "zemljoradnik",
        # "domačica" -> "domaćica" (the commonest such spelling, twenty times as common at least); a genitive to its
        # nominative: "zemljoradnika" -> "zemljoradnik"
        self.occ_spelling = {}
        common = sorted(((n, w) for w, n in occupations.items() if n >= 50), reverse=True)
        for w, n in occupations.items():
            target = next((c for m, c in common if m >= 20 * n and c != w and same_word(w, c)), None)
            if not target and w.endswith('a') and occupations.get(w[:-1], 0) >= max(50, 20 * n):
                target = w[:-1]
            if not target and ' ' in w and occupations.get(w.replace(' ', ''), 0) >= max(50, 20 * n):
                target = w.replace(' ', '')                                 # "zemljo radnik", "kroj ač"
            if target:
                self.occ_spelling[w] = target
        for w, target in self.occ_spelling.items():                 # "zemllradnik" -> "zemjoradnik" -> "zemljoradnik"
            while target in self.occ_spelling and self.occ_spelling[target] != w:
                target = self.occ_spelling[target]
            self.occ_spelling[w] = target

    def occupation(self, w: str) -> str:
        return self.occ_spelling.get(w, w)

    def is_occupation(self, w: str) -> bool:
        """A trade, unless the word is a known place written as one: "Drvar" (the town; "drvar" is a woodcutter), or
        where she was born: "u činovničkoj porodici"."""
        if re.match(r'u\s', w):
            return False
        return w.lower() in self.occupations and not (w[:1].isupper() and self.places.get(w, 0) >= 2)

    # ── birth / ethnicity / occupation ───────────────────────
    def life(self, text: str, code: int) -> dict:
        out = {}
        t = text
        if code == 58:
            t = re.sub(r'^(?:dr\.;\s*)?r\.\s*(?=1[89]\d\d)', 'rođen ', t)     # Kalnički odred: "r. 1922; Martinišće, Zabok"
        if code == 75 and not re.match(r'^(?:iz|rođ)\b', t):
            t = ''                                                        # 12. vojvođanska's roster: where they lived, no birthplace
        if code == 84:
            t = ''              # 13. vojvođanska's roster: names only; "POPOV MILAN (MOKRIN)" tells namesakes apart, no birthplace
        if code == 71 and re.match(r'^(?:pad(?:el|la)\s+)?[a-z]+a\s+19[34]\d\b', t):
            t = ''                                                        # 1. slovenska artilerijska: "novembra 1944, Jama" is a death
        if code == 51:
            # 3. makedonska: where he came from, then the year: "iz s. Nikuline, rođen 1922. god., poginuo ..."
            t = re.sub(r',?\s*\brođen[a]?\s+[^,]*', '', t)
        if code == 119:
            # Požarevački odred: "iz Smoljinca" is where he came from; only "rođen 1910. g. u Kučevu" says where he was born
            t = re.sub(r'\b([Rr])ođ\.', r'\1ođen', t)
        # a maiden name set before the bio (5. proleterska's Partizanke: "rođena Perunović; Rođena 1894. godine u ...")
        t = re.sub(r'(?:^|(?<=;\s))rođena\s+[A-ZČĆŽŠĐ][\w-]*;\s*', '', t)
        # a function printed before "rođen" (Treća proleterska, 5. kozaračka): "desetar 3. desetine, rođen 1920, ..."
        m = re.search(r'\b[Rr]ođen[a]?\b', t)
        head = t[:m.start()] if m else ''
        if m:
            t = t[m.start():]
        elif code in (15, 119):
            t = ''                                                        # 1. šumadijska always says "Rođen ..."
        elif code == 35 and ',' not in t:
            t = ''                                                        # the 32. division's roster: a nickname at most
        elif code == 50:
            # 12. dalmatinska: the duty, then where he came from: "borac 3. č, 2. bat., iz Svirča, Hvar, pog. ..."
            im = re.search(rf'\biz\s+(?=[{U}])', t)
            head = t[:im.start()] if im else t
            t = t[im.start():] if im else ''
        elif code in (25, 32):
            # the duty, the year of birth, the birthplace: "borac, 1920, Valjak - Orahovica, u NOB od ..." (Tuzlanski
            # odred, 21. tuzlanska); a year after the enlistment or the death is no year of birth
            ym = re.match(r'^[^\d]*?\b1[89]\d\d[.,]\s*', t)
            t = t[ym.end():] if ym and not re.search(r'pogin|umr|nesta|NOB|Brigad|Odred|\bod\b', ym.group(0)) else ''
        bm = BIRTH_DATE_RE.match(t)
        if bm and (bm.group(0).strip() or m):
            t = t[bm.end():]
        elif m:
            t = re.sub(r'^[Rr]ođen[a]?\s+', '', t)
        else:
            # "Jere, 1919. Šibenik" (a name glued in front) — a date after one word: the place follows it
            dm = DATE_RE.search(t[:30])
            if dm and dm.start() > 0 and re.fullmatch(rf'[{U}][{L}]+[,.]?\s*', t[:dm.start()]):
                t = t[dm.end():].lstrip('., ')
            elif re.match(r'^\s*(?:\.\s*)+', t):
                t = re.sub(r'^[\s.,…]+', '', t)
        t = re.sub(r'^us\.\s*', 'u s. ', t.strip())                            # OCR "us. Lalincu"
        # where he came from: "iz Zavlake, Donji Lapac" (Prva lička), "iz Gostuše, srez nišavski" (25. srpska brigada)
        from_place = code in (2, 31, 50, 51, 58, 73, 75, 79, 118) and re.match(rf'^iz\s+[{U}]', t) is not None
        if from_place:
            t = re.sub(r',\s*srez\s+[a-zčćžšđ]+', '', t[3:])
        elif re.match(rf'^(?:kod|na|pri|v|nad|pod|blizu|iz)\s', t):
            t = ''                                                            # "1944. kod Tovarnika." is not a birthplace
        locative = from_place or re.match(r'^u\s+(?!s\.?\s|selu)', t) is not None   # "rođen u Donjem Lapcu" (locative)
        t = re.sub(r'^(?:u\s+selu|u\s+s\.?|u|s\.?|selo|g\.)\s+', '', t)
        t = re.sub(r'\s[—–-]\s', ', ', t)                                     # "Studenec - Ig", "Brajići — Boka kotorska"
        if code in (3, 25, 32):
            t = re.sub(rf'(?<=[{L}])-(?=[{U}])', ', ', t)                       # Druga lička: "Nebljusi-D. Lapac"
        first_sentence = sentences(t)[0] if t else ''
        segs = [clean_segment(s) for s in re.split(r',|;', first_sentence)]
        place = []
        for s in segs:
            if not s or is_placeholder(s):
                if place:
                    break
                continue
            tail = re.match(r'^(.*\S)\s+(\S+)$', s)
            if (tail and (tail.group(2) in ETHNIC or tail.group(2) in self.occupations)   # "Italija Talijan" (comma missing)
                    and re.match(rf'^[{U}]', tail.group(1))):                      # not "brigadni telegrafist"
                # a sentence the split above missed ends the place: "Mali Mokri Lug. Beograd. zemljoradnnk"
                cut = next((m.start() for m in re.finditer(rf'\.\s+(?=[{U}])', tail.group(1))
                            if not re.search(rf'(?:^|\s)(?:[{U}][{L}]?|{"|".join(ABBREV)})$', tail.group(1)[:m.start()])), None)
                place.append(clean_segment(tail.group(1)[:cut]))
                break
            if (s in ETHNIC or looks_ethnic(s) or self.is_occupation(s) or RANK_RE.fullmatch(s) or UNIT_RE.search(s)
                    or UNIT_WORD_RE.search(s)
                    or any(rx.search(s) for rx, _ in SPECIAL_UNITS)
                    or STOP_PLACE.match(s) or DEATH_RE.search(s) or re.search(r'\d', s) or len(s) > 40 or len(s.split()) > 4
                    or not re.match(rf'^(?:[{U}]|\((?=[{U}])|(?:s|sv|st)\.\s[{U}])', s)):
                break
            place.append(s)
            if len(place) == 3:
                break
        if place:
            if locative or any(' kod ' in p for p in place):                  # "u selu Makcima kod Velikog Gradišta"
                place = [self.nominative(p, keep=True, locative=bool(locative) and i == 0) for i, p in enumerate(place)]
            bp = ', '.join(place)
            bp = re.sub(r',\s*\(', ' (', bp)                               # "Budisava, (Titel)"
            bp = re.sub(r'\s+-\s+', ', ', bp)                              # "Ćuić Krčevina - T. Korenica"
            out['birth_place'] = bp
        # ethnicity and occupation: the words of the bio up to the death clause
        words = [clean_segment(s) for s in re.split(r'[,;]\s*|\.\s', text)]
        for i, w in enumerate(words):
            if w in ETHNIC:
                out['ethnicity'] = w
                if i + 1 < len(words) and self.is_occupation(words[i + 1]):
                    out['occupation'] = self.occupation(words[i + 1].lower())
                break
        if code in NO_OCCUPATION:
            out.pop('occupation', None)
        elif 'occupation' not in out:
            for w in words[:8]:
                if self.is_occupation(w) and w.lower() not in ('borac',):
                    out['occupation'] = self.occupation(w.lower())
                    break
        if head:
            out['_head'] = head
        return out

    # ── death ────────────────────────────────────────────────
    # The Slovene books mark a death with a dagger: "† 1944 Pohorje" in the war (the parsers read those), and in the
    # rosters of survivors "† 1962", "† po osvoboditvi" (after liberation) or a bare "†" for one who has died since
    DAGGER_RE = re.compile(rf'†\s*[;,]?\s*(?:(?P<date>{DATE})|(?P<after>po\s+osvoboditvi|po\s+vojni))?\s*,?\s*(?P<rest>[^;]*)')

    def dagger(self, text: str) -> dict:
        m = self.DAGGER_RE.search(text)
        if not m:
            return {}
        if m.group('after'):
            return {'death_type': 'umro', 'death_date': re.sub(r'\s+', ' ', m.group('after'))}
        if not m.group('date'):
            return {'death_type': 'umro'}
        date = re.sub(r'\.?\s*god(?:ine|\.)$', '', m.group('date')).rstrip('.').strip()
        year = int(re.search(YEAR, date).group(0))
        out = {'death_type': 'poginuo' if year <= 1945 else 'umro', 'death_date': date}
        place = re.sub(r'^(?:v|pri|na|nad|pod)\s+', '', clean_segment(m.group('rest')))
        if place and len(place) <= 60 and re.match(rf'^[{U}]', place) and not re.search(r'\d', place):
            out['death_place'] = place
        return out

    def death(self, text: str, place_re: re.Pattern | None = None, converted_only: bool = False) -> dict:
        """place_re: the form a book's place of death must have, else none is read; converted_only: only a place put
        in the nominative (a book whose places other units' data repeat in the case it prints)"""
        out = {}
        m = DEATH_RE.search(text)
        mesto = re.search(r'mesto smrti\s*:\s*([^,;.]+(?:\s\([^)]*\))?)', text, re.I)
        if not m:
            if mesto:
                out['death_place'] = clean_segment(mesto.group(1))
            elif '†' in text:
                out = self.dagger(text)
            return out
        kw = m.group(1).lower()
        out['death_type'] = DEATH_KW[kw]
        rest = text[m.end():]
        # the death clause runs to the end of its sentence, or to "sahranjen" / a new clause
        clause = sentences(rest)[0] if rest.strip() else ''
        clause = clause.split(';')[0]                                        # "poginuo u NOB; zvani ...": a note follows
        clause = re.split(r'[,;]?\s*(?:sahranjen|sahranjena|pokopan|pokopana|mesto sahrane|mjesto sahrane|a sahranjen|ostao na|nije sahranjen)', clause)[0]
        # not the day a wound was received: "Umro od rane zadobijene 29. septembra 1944. god. u borbi za ..."
        dm = next((d for d in DATE_RE.finditer(clause) if not re.search(r'\bzadobijen\w*\s+$', clause[:d.start()])), None)
        if dm and not 1941 <= int(re.search(YEAR, dm.group(0)).group(0)) <= 2000:
            dm = None                                                     # "umro u bolnici, 1926, Vršac" — that is the birth year
        if dm:
            date = re.sub(r'\.?\s*god(?:ine|\.)$', '', dm.group(0)).rstrip('.').strip()
            date = re.sub(r'^u\s', '', date)
            start = dm.start()
            if dm.group(0).startswith('u ') and start and clause[start - 1].isalpha():
                start += 2                                  # "u Šapcu marta 1945": the "u" is the end of the word before
            after = re.sub(r'^\.?\s*god\b\.?', '', clause[dm.end():])   # "1944. god s. Bukovice", "1944. god" at a sentence's end
            if re.match(r'\.\s*\(', after) or (dm.group(0).endswith('godine') and after.startswith('.')):
                after = ''     # a remark: "Oruglica 29/30. jula 1944. (raznela ga bugarska granata)", "... 1942. godine. z"
            night = re.search(r'\d{1,2}\s?/\s?$', clause[:start])         # "u noći 28/29. decembra 1943": the day it ended
            either = re.search(r'\d{1,2}\.\s+ili\s+$', clause[:start])    # "10. ili 12. maja 1945": as printed
            if night:
                start = night.start()
            elif either:
                start = either.start()
                date = either.group(0) + date
            elif re.search(r'\d[.,]$', clause[:start]):
                date = re.search(YEAR, date).group(0)                     # "Senja 2.9. IV 1945": the day is garbled, the year is not
            out['death_date'] = date
            clause = clause[:start] + ' ' + after
        clause = re.sub(r'\s+kao\s+.*$', '', clause)                     # "poginuo 1943. kao borac 19. divizije"
        clause = re.sub(r'\b(?:u borbi|u napadu|u akciji|u zarobljeništvu|u bolnici|u logoru|u ratu|u NO[BR](?:-[iu])?|u noći|noću)'
                        r'(?![\w-])\s*', '', clause)
        # a massacre is no place: "u Vranićkom pokolju", "u pokolju Vranićana"
        clause = re.sub(rf'\bu\s+(?:[{U}]\w+\s+)?pokolju(?:\s+[{U}]\w+)?', '', clause)
        # an offensive is no place: "poginuo u V ofanzivi", "u Grmeču u toku četvrte neprijateljske ofanzive", "na Grmeču
        # tokom četvrte neprijateljske ofanzive"
        clause = re.sub(r'(?:\bu\s+toku\s+|\btokom\s+|\bu\s+)?\b(?:[IVX]+\.?|prv\w*|drug\w*|treć\w*|četvrt\w*|pet\w*|šest\w*|sedm\w*)\s+'
                        r'(?:neprijateljsk\w+\s+)?ofanziv\w*[,.]?\s*', '', clause, flags=re.I)
        clause = re.sub(r'(?:,\s*|\s+)(?:i tu|gde|gdje|protiv|dok|pošto|jer|kada|kad|zajedno|sa(?=\s))\b.*$', '', clause)   # "kod Vrbovca i tu", "..., gdje je i", "(u borbi) sa SS-ovcima"
        clause = re.sub(r'\s*\((?:nema|drugih|nedostaju|ostali)[^)]*\)?', '', clause)
        clause = re.sub(rf'^[{U}]\.,\s*', '', clause.strip())                # "S., Soljani" (OCR)
        clause = re.sub(r'^[\s,]*(?:od|usled|uslijed|zbog)\s+[^,]*?(?=,|\s(?:u|na|kod|v|pri)\s|$)', '', clause.strip())   # cause of death
        place = DUTY_AFTER_PLACE.sub('', clause)                            # "s. Topola kod Banja Luke, ekonom čete"
        if not re.search(r'\b[A-ZČĆŽŠĐ]{3,}\b', place):                     # unless the next entry's NAME is glued on
            clause = place
        clause = clean_segment(re.sub(r'\s+', ' ', clause))
        if mesto:
            out['death_place'] = clean_segment(mesto.group(1))
        elif (clause and len(clause) <= 70 and not re.search(r'\d', clause)
              # every part a place: not "u Centralnoj , bolnici u Sandžaku", "Sombor, uisled i teških rana"
              and all(re.match(rf'^(?:{PREP}\s+)?(?:s\.\s)?[{U}]', p.strip()) for p in clause.split(','))
              and (place_re is None or place_re.fullmatch(clause))):
            place = self.nominative(clause)
            if not converted_only or self.in_nominative(clause, place):
                out['death_place'] = place
        return out

    @staticmethod
    def in_nominative(clause: str, place: str) -> bool:
        """Every part of the place was put in the nominative, or was printed in it: after "za" a masculine or neuter
        ("za Knin", "za Očestovo"), not "za Rečinu"; never one left as printed after "kod", "na", "u" ("kod Poličnika")"""
        printed, got = [p.strip() for p in clause.split(',')], [p.strip() for p in place.split(',')]
        if re.match(rf'^{PREP}\s', place) or len(printed) != len(got):
            return False
        for p, g in zip(printed, got):
            m = re.match(rf'^({PREP})\s+(.*)$', p)
            prep, bare = (m.group(1), m.group(2)) if m else ('', p)
            if g == bare and (prep not in ('', 'za') or bare.endswith('u')):
                return False
        return True

    def table_22_division(self, text: str) -> dict:
        """22. divizija's table of the fallen, its cells joined by commas, any of them may be empty: the birthplace, the
        day and the place of death ("Pakleštica, 12. IV 1945, Bosut", "4. X 1944, D. Slatina", "Bogojevac, 2. II 1945,
        (umro od rana u Šapcu)"). Without a date the cells can't be told apart."""
        segs = [s.strip() for s in re.split(r';\s+', text)[-1].split(',')]   # "(Rus); SSSR, ...": a note first
        i = next((k for k, s in enumerate(segs) if re.search(r'\d', s)), None)
        if i is None or not re.search(YEAR, segs[i]):
            return {}
        born, date, place = ', '.join(segs[:i]), segs[i], ', '.join(s for s in segs[i + 1:] if s)
        out = {'death_type': 'poginuo'}                                    # a list of the fallen
        if born and re.match(rf'^[({U}]', born) and not re.search(r'[\d;|]', born):
            out['birth_place'] = born
        dm = DATE_RE.fullmatch(date)
        if dm:
            out['death_date'] = re.sub(r'\.?\s*god(?:ine|\.|\b)$', '', date).rstrip('.').strip()
        fate = place.lower()
        if re.search(r'\bumr', fate):
            out['death_type'] = 'umro'
        elif 'streljan' in fate:
            out['death_type'] = 'streljan'
        elif 'nesta' in fate:
            out['death_type'] = 'nestao'
        # where he died of his wounds: "Sakar (umro u Šapcu)", "(umro od rana u Šapcu)", "umro u Beogradu"
        later = (re.search(rf'\(\s*(?:umro|umrla)\b[^()]*?\b(u|kod|na)\s+([{U}][^()]+)\)', place)    # not "(umro kod kuće)"
                 or re.match(rf'^(?:umro|umrla|streljan|nestao)\s+(u|kod|na)\s+([{U}][^()]+)$', place))
        if later:
            at = later.group(2).strip()
            nom = self.nominative(f'{later.group(1)} {at}')
            out['death_place'] = at if nom.startswith(later.group(1) + ' ') else nom
        elif not re.search(r'\bumr', fate) and re.fullmatch(rf'[{U}][^();|]*(?:\([^();|]+\))?', place):
            out['death_place'] = place                                    # the column prints the nominative
        return out

    @staticmethod
    def date_34_division(cell: str) -> str:
        """34. divizija's date of death: "07.09.44" = 7. 9. 1944 (as its parser writes it), "04.1945" = travnja 1945,
        "trav. 45", "jes.1944" = jesen 1944, "1943"; a cell the scan garbled ("14.1044") gives nothing."""
        c = cell.strip(' .,-—')
        m = re.fullmatch(r'(\d{1,2})[.,-]\s?(\d{1,2})(?:[.,-]\s?|\s)(?:19)?(4[1-5])', c)
        if m:
            day, mon = int(m.group(1)), int(m.group(2))
            return f'{day}. {mon}. 19{m.group(3)}' if 1 <= day <= 31 and 1 <= mon <= 12 else ''
        m = re.fullmatch(r'(\d{1,2})[.,]\s?(?:19)?(4[1-5])', c)
        if m:
            mon = int(m.group(1))
            return f'{HR_MONTHS[mon - 1]} 19{m.group(2)}' if 1 <= mon <= 12 else ''
        m = re.fullmatch(r'(?:19)?(4[1-5])', c)
        if m:
            return f'19{m.group(1)}'
        m = re.fullmatch(rf'([{L}]+)\.?[\s.-]*(?:19)?(4[1-5])', c.lower())
        if m:
            word, year = m.group(1), f'19{m.group(2)}'
            mon = next((n for stem, n in HR_MONTH_STEMS if word.startswith(stem)), None)
            if mon:
                return f'{HR_MONTHS[mon - 1]} {year}'
            season = next((s for stem, s in HR_SEASONS if word.startswith(stem)), None)
            return f'{season} {year}' if season else year if word == 'pro' else ''
        return ''

    # ── locative/genitive -> nominative, only when the result is a known place ──
    _WORD_RULES = [
        ('ima', 'i'), ('ama', 'e'), ('iji', 'ija'), ('ci', 'ka'), ('ci', 'ca'), ('zi', 'ga'), ('si', 'ha'), ('u', ''), ('u', 'o'), ('u', 'a'),
        ('ju', 'j'), ('ju', 'je'), ('om', 'o'), ('em', 'e'), ('i', 'a'), ('i', 'e'), ('oj', 'a'), ('oj', 'o'), ('om', 'i'), ('om', ''), ('em', 'i'),
        ('eg', 'i'), ('og', 'i'), ('og', 'o'), ('e', 'a'), ('a', ''), ('a', 'o'), ('a', 'e'), ('a', 'i'), ('ova', 'ovi'), ('eva', 'evi'), ('aca', 'ci'),
        ('ije', 'ija'), ('ske', 'ska'), ('ke', 'ka'), ('cu', 'ec'), ('cu', 'ac'), ('ca', 'ac'), ('ca', 'ec'), ('ga', 'g'), ('ka', 'ak'), ('e', 'i'), ('ih', 'i'), ('i', 'o'),
        ('aka', 'ci'), ('ra', 'ar'),
        ('pcu', 'bac'), ('pca', 'bac'), ('ocu', 'olac'), ('oca', 'olac'),          # "u Šapcu" = Šabac, "u Stocu" = Stolac
    ]

    def _variants(self, word: str) -> set[str]:
        out = {word}
        for suf, rep in self._WORD_RULES:
            if word.endswith(suf) and len(word) - len(suf) >= 2:
                out.add(word[:-len(suf)] + rep)
        return out

    def _known(self, phrase: str, locative: bool = False) -> str | None:
        """locative: the phrase follows "u" ("u Gradačcu"), so a form read earlier as printed may be in the corpus
        too; a nominative far more common than it wins."""
        words = phrase.split()
        if not words or len(words) > 4:
            return None
        n0 = self.places.get(phrase, 0)
        if n0 and not locative:
            return phrase                                                 # already a known nominative
        best = None
        for combo in product(*(self._variants(w) for w in words)):
            cand = ' '.join(combo)
            n = self.places.get(cand, 0)
            if cand != phrase and n and (best is None or n > best[0]):
                best = (n, cand)
        if n0 and not (best and best[0] >= (max(5, n0 / 2) if locative else 3 * n0)):
            if locative and not best and len(words[-1]) >= 7 and re.search(r'(?:ima|ama)$', words[-1]):
                return None                     # "u Mucalovićima": a plural's locative that a record kept, not a nominative
            return phrase
        return best[1] if best else None

    def nominative(self, clause: str, keep: bool = False, locative: bool = False) -> str:
        """'na Sutjesci' -> 'Sutjeska'; 'u selu Grabovo kod Vukovara' -> 'Grabovo, Vukovar'; unknown -> as printed
        (keep=True: unknown parts stay as they are, the known ones are still converted; locative=True: the clause
        followed "u", its first part is in the locative)."""
        parts = [p for p in re.split(r',\s*|\s+-\s+|\s+(?=kod\s|pri\s)', clause) if p.strip()]
        names, bare = [], []
        for p in parts:
            prep = re.match(rf'^{PREP}\s+', p.strip())
            p = re.sub(rf'^{PREP}\s+', '', p.strip())
            p = re.sub(r'^(?:selu|selo|s\.)\s+', '', p)
            bare.append(not prep or prep.group(0).strip() in ('s.', 'selo'))
            known = self._known(p, locative=(locative and not names) or not bare[-1])   # after u/kod/na: inflected
            if not known:
                if keep or bare[-1]:
                    names.append(p)                                       # printed in the nominative already: "s. Nijemci, Vinkovci"
                    continue
                return clause
            names.append(known)
        return ', '.join(dict.fromkeys(names)) if names else clause

    # ── rank / unit ──────────────────────────────────────────
    @staticmethod
    def ranks(text: str) -> str:
        found = []
        for m in RANK_RE.finditer(text):
            r = m.group(1).lower().replace('polit. ', 'politički ').replace('skoj-a', 'SKOJ-a')
            r = re.sub(r'^st\.\s?vodnik$', 'stariji vodnik', re.sub(r'^ml\.\s?vodnik$', 'mlađi vodnik', r))   # "st.vodnik"
            if r not in found:
                found.append(r)
        # a specific function makes the generic "borac" redundant; "politički komesar" is covered by "politički komesar brigade"
        if len(found) > 1 and 'borac' in found:
            found.remove('borac')
        found = [r for r in found if not any(o != r and o.startswith(r + ' ') for o in found)]
        return ', '.join(found[:3])

    @staticmethod
    def unit_text(t: str) -> str:
        """The printed forms of a sub-unit number, made regular for UNIT_RE"""
        # glued to the word before it: "u 3. četi2. bataljona", "u 1. četiZ. bataljona" (4. srpska; Z is the Cyrillic З
        # the text layer reads for the digit 3 there)
        t = re.sub(rf'(?<=[{L}])(?=(?:\d{{1,2}}|Z)\.\s?(?:bataljon|bat\.|čet[aeiu]\b))', ' ', t)
        t = re.sub(r'(?<=\b(?:18|19)\d\d[.,])(?=\d{1,2}\.\s?(?:bataljon|bat\.|čet[aeiu]\b))', ' ', t)   # "1944.1. četa"
        t = re.sub(r'(?<![\w.])Z(?=\.\s?(?:bataljon|bat\.|čet[aeiu]\b))', '3', t)
        # a battalion number printed without its dot or with an epithet in brackets: "1 bat", "1944,1 bataljon",
        # "4 (ruskog) bataljona" (7. vojvođanska's 4th battalion was the Russian one)
        t = re.sub(rf'(?<![\w.])(\d{{1,2}})\.?\s?(?:\([{L}]+\)\s?)?(?=(?:bataljon|bat\b))', r'\1. ', t)
        # a comma after the Roman numeral: "u brigadi od januara 1944, VI, bataljon"
        t = re.sub(r'(?<![\w.])([IVX]{1,4}),\s?(?=bataljon)', r'\1 ', t)
        return t

    # A numbered company or battalion named for its district: "borac 1. zlatiborske čete" (Užički odred),
    # "3. kordunaškog bataljona"
    NAMED_UNIT_RE = re.compile(rf'(?<![\w.])(\d{{1,2}})\.\s?([{L}]+?(?:sk|čk|šk|ck))(?:a|e|oj|u|i|og|oga|om|ome)\s+'
                               rf'(čet[aeiu]|bataljon[au]?)\b')

    @staticmethod
    def unit(text: str) -> str:
        # 2. dalmatinska: "U NOV od 1941. u Kamešničkoj četi ... U 2. dalm. brigadi od ...": the units before the brigade
        t = re.split(r'\b(?:u NOV|U NOV)\s+od\b', text)[0] if re.search(r'\bu 2\. dalm', text, re.I) else text
        t = Extractor.unit_text(t)
        units = [p for p in Extractor.numbered_units(t).split(', ') if p]
        # A company or battalion named for its district, for a level the numbers above leave empty
        # ("2. bataljon ... u 5. mitraljeskom bataljonu" stays the 2nd)
        named = Extractor.NAMED_UNIT_RE.search(t)
        # not another brigade's battalion: "upućen ... u 5. ruski bataljon 5. crnogorske prolet. brigade"
        if named and not re.match(r'\s+\d{1,2}\.\s+[\w.]+\s+(?:[\w.]+\s+)?brigad', t[named.end():]):
            num, stem, kind = named.groups()
            battalion = not kind.startswith('čet')
            label = f"{num}. {stem.lower()}{'i bataljon' if battalion else 'a četa'}"
            if not any(('bataljon' in p) if battalion else re.match(r'\d+\.\s(?:\S+\s)?četa$', p) for p in units):
                units = units + [label] if battalion else [label] + units
        return ', '.join(units)

    @staticmethod
    def numbered_units(t: str) -> str:
        parts, seen = [], set()
        for rx, fmt in SPECIAL_UNITS:
            m = rx.search(t)
            if m:
                val = fmt.format(m.group(1).lower()) if '{}' in fmt else fmt
                parts.append(val)
                seen.add('bataljon' if 'bataljon' in val else 'četa')
        order = {'vod': 0, 'desetina': 0, 'četa': 1, 'bataljon': 2}
        found = {}
        for m in UNIT_RE.finditer(t):
            num, kind = m.group(1), m.group(2).lower().rstrip('.')
            kind = {'č': 'četa', 'čete': 'četa', 'četi': 'četa', 'bat': 'bataljon', 'bataljona': 'bataljon', 'bataljonu': 'bataljon',
                    'desetine': 'desetina', 'voda': 'vod', 'vodu': 'vod'}.get(kind, kind)
            if kind in found or kind in seen:
                continue
            if re.fullmatch(r'[IVX]{1,4}', num) and kind != 'bataljon':
                continue
            found[kind] = f'{num} {kind}' if not num.endswith('.') or kind != 'bataljon' or True else f'{num} {kind}'
        units = [found[k] for k in sorted(found, key=lambda k: order[k])]
        return ', '.join(units + parts)

    def extract(self, info: str, code: int, duty_first: bool = False) -> dict:
        if code in PARSER_FIELDS:
            return {}
        # a nickname, another surname, a title ("dr.; ", "ing.; " in the Slovene lists) before the bio
        text = re.sub(r'^(?:(?:zvan[ai]|ili|rođ\.|roj\.|por\.)\s[^;]{0,60};\s*|(?:dr|ing|arh|mr)\.;\s*)+', '', info or '').strip()
        text = re.sub(r'\s*\((?:općina [^)]*|ČSSR)\)$', '', text)          # 17. slavonska: section the soldier was listed under
        text = re.sub(r'\s+', ' ', text)
        if not text or len(text) < 3:
            return {}
        # a month the scan read with a capital inside it: "krajem oKtobra 1944"
        text = re.sub(rf'\b[{L}]+[{U}][{L}]*\b', lambda m: m.group(0).lower() if m.group(0).lower() in MONTH_SET else m.group(0), text)
        text = re.sub(rf'\bSI\.(?=\s?[{U}])', 'Sl.', text)                   # "kod SI. Broda": Sl(avonskog), the l read as I
        if code == 96:
            return self.table_22_division(text)
        place_re, converted_only = None, False
        if code == 101:
            # 12. hercegovačka: "iznad Ivanice-Dubrovnik", "u Vilusima-Crna Gora": the village, then its municipality
            text = re.sub(rf'(?<=[{L}])-(?=[{U}])', ', ', text)
            text = re.sub(r'\bčet\^', 'čete', text)                         # "Zamjenik komandira čet^."
        if code == 103:
            # 6. dalmatinska's text layer reads the digit 2 as Ž: "kod Livna Ž9. XII 1943", "za Mostar 1Ž. II 1945"
            text = re.sub(r'(?<!\w)[\dŽ]*Ž[\dŽ]*(?=\.)', lambda m: m.group(0).replace('Ž', '2'), text)
            # and its Roman months I and II as 1 and 11: "za Smoković 5. 1 1944", "kod Mostara 22. 11 1945"
            text = re.sub(r'(?<=\d\.\s)1{1,3}(?=\s(?:18|19)\d\d)', lambda m: 'I' * len(m.group(0)), text)
            text = re.sub(rf'(?<=[{L}])\s*—\s*(?=[{U}])', ', ', text)           # "kod Livna— Dragnić"
            place_re = PLACE_103
            converted_only = True
        if code == 50:
            text = re.sub(r'\bpog\.', 'poginuo', text)                    # 12. dalmatinska's abbreviation
            # its day and month without a year ("poginuo 27. 4. kod Klane"; the parser dated it by the heading)
            text = re.sub(r'\b(poginu[ol]a?|umr[ol]a?)\s+\d{1,2}[.,]\s*\d{1,2}\.(?!\s*19)\s*', r'\1 ', text)
        if code == 10:
            # the brigade's roster (zbornik, knj. 3) abbreviates "rođ.", which the OCR also reads "rod."
            text = re.sub(r'^-?ro[dđ]\.,?\s*', 'rođen ', text)
        if code == 35:
            # "Borci 32. divizije NOVJ": "r. 1923, s. Kloštar, Ivanić Grad, Hrvat, ..." (the roster has names only)
            text = re.sub(r'^r\.\s*(?=1[89]\d\d)', 'rođen ', text)
        if code == 58:
            # Kalnički odred: "r. 1922; Martinišće, Zabok; u KPO od lipnja 1943." or "iz Luke Ludbreške, Ludbreg."
            text = re.sub(r'^(?:dr\.;\s*)?r\.\s*(?=1[89]\d\d)', 'rođen ', text)
            # "poginuo u Šemovcu (Varaždin)": the municipality in brackets
            text = re.sub(r'\b((?:u|kod|na)\s+[A-ZČĆŽŠĐ][\w ]*?)\s*\(([A-ZČĆŽŠĐ][\w ]*)\)', r'\1, \2', text)
        if code == 53:
            # 11. dalmatinska: the duty, then "r. 18. 3. 1924, Kulen Vakuf, Bihać, zemljoradnik, ..."
            text = re.sub(r'(^|[\s,])r\.\s*(?=\d)', r'\1rođen ', text, count=1)
            # "Poginuo u borbi s Nijemcima za Ston, 17. 10. 1944.": where he fell follows the enemy
            text = re.sub(r'\b([Pp]oginu[ol]a?)\s+u\s+borbi\s+(?:s|sa)\s+\S+(?:\s+i\s+\S+)?\s+(?:za|kod)\s+', r'\1 kod ', text)
        if code == 56:
            # 14. srednjobosanska's survivors: "1922, Kladari (opština Prnjavor)": the municipality heading they were under
            text = re.sub(r'\s*\(opština ([^)]*)\)$', r', \1', text)
            text = re.sub(r'\b([A-ZČĆŽŠĐ][\w ]+), \1$', r'\1', text)                 # "Prnjavor, Prnjavor"
            # the fallen: "poginuo 6. maja 1945. god. Perković Han, Maglaj.": the place follows the date
            text = re.sub(r'\b((?:pogin|umr|nesta)\w*\s+(?:\d{1,2}\.\s*\w+\s+)?1[89]\d\d\.?\s*(?:god\.|godine)?)\s+'
                          r'(?=[A-ZČĆŽŠĐ])', r'\1 kod ', text)
        if code == 57:
            # 3. vojvođanska: "poginuo 29. 4. 1944. Stupari u istočnoj Bosni": the place follows the date
            text = re.sub(r'\b((?:pogin|umr|nesta)\w*\s+(?:\d{1,2}\.\s*\d{1,2}\.\s*|\w+\s+)?1[89]\d\d\.?)\s+'
                          r'(?=[A-ZČĆŽŠĐ])', r'\1 kod ', text)
        if code == 55:
            # 17. srpska: "rođen 1924. u Pečenjevcima, Leskovac, Srbija, Srbin, ..."
            text = re.sub(r',\s*Srbija\b', '', text)
        if code == 52:
            # 18. hrvatska: "rođen 1920. godine u Gradačcu, SRBiH, Musliman. zemljoradnik": the republic is no place
            text = re.sub(r',?\s*\b(?:SR\s*-?\s*BiH|SRBiH|BiH|SR Srbija|SR Hrvatska|SR Crna Gora|SR Slovenija|SAP Vojvodina)\b', '',
                          text)
            text = re.sub(r'\b(Musliman|Srbin|Hrvat|Jugosloven)(ka|kinja|ica)?\.\s', r'\1\2, ', text)
            text = re.sub(r'^(ro[dđ]en[a]?\s+1[89]\d\d)\.?\s*godine\s+(?=u\s)', r'\1, ', text)   # "... godine u Gradačcu"
        if code == 51:
            # 3. makedonska's dates have Roman months the scan garbled ("16-1U-1945. god."); the parser reads them
            text = re.sub(r'\s+\S+-\S*-\S*\d\S*(?:\s*god\.)?', '', text)
            text = re.sub(r'\b[pl]oginuo\s+(?:kod|hod|kd)\s', 'poginuo kod ', text)
        if code == 109:
            # Mačvanski odred: the heading the entry stands under leads ("Banja Koviljača (Jadranski srez): ")
            text = re.sub(r'^[^:;]{2,80}:\s*(?:(?:zvan[ai]|dr\.)[^;]{0,60};\s*)*', '', text)
        dm = DEATH_RE.search(text) or re.search('†', text)
        life_text = text[:dm.start()] if dm else text
        out = self.life(life_text, code)
        head = out.pop('_head', '')
        if code == 109:
            out = {k: v for k, v in out.items() if k == 'ethnicity'}       # its parser reads the birthplace and the trade
        # the next entry glued on before the first death: "... krajem rata politički komesar bolničke čete. iRCEGOVIĆ Stipe
        # ANTE, borac ..., poginuo na Zelengori": that death is the other soldier's
        if not (dm and GLUED_RE.search(text[:dm.start()])):
            out.update(self.death(text, place_re, converted_only))
        if code == 97:
            # 34. divizija: the last column is the date of death, printed as the parser could not always read it
            date = self.date_34_division(text.split(', ')[-1])
            if date:
                out['death_date'] = date
        rank_text = (head + ' ' if head else '') + text
        if code in DUTY_BEFORE_WAR_END or duty_first:
            rank_text = re.split(r'\bkrajem rata\b', rank_text)[0]
        if code == 118:
            # 3. lička's narodni heroji: "Danas je general-major JNA" is the rank after the war
            rank_text = re.sub(r'\b(?:Danas|Sada)\s+je\b[^.]*\.', ' ', rank_text)
        rank = self.ranks(rank_text)
        if rank:
            out['rank'] = rank
        unit = self.unit(text)
        if unit:
            out['unit_detail'] = unit
        return {k: v for k, v in out.items() if v}


def load_live():
    live = live_json_files()
    return {code: (cfg['json_file'], json.loads((ROOT / 'website' / 'public' / cfg['json_file']).read_text(encoding='utf-8')))
            for code, cfg in sorted(BRIGADE_CONFIGS.items()) if cfg['json_file'] in live}


def build_extractor(brigades) -> Extractor:
    # the units' own records teach the vocabulary; Ostali borci (122), made of many books' OCR, would teach it wrong
    # ("španski borac" for an occupation)
    all_recs = [s for code, (_, d) in brigades.items() if code != 122 for s in d]
    # occupations: what follows the ethnicity in the books that print both, plus values already in the data
    occ = Counter()
    for s in all_recs:
        words = [clean_segment(w) for w in re.split(r'[,;.]\s', s.get('additional_info') or '')]
        for i, w in enumerate(words[:-1]):
            if w in ETHNIC and re.fullmatch(rf'[{L}]+(?: [{L}]+){{0,2}}', words[i + 1]):
                occ[words[i + 1]] += 1
        if s.get('occupation'):
            occ[s['occupation'].lower()] += 3
    # 'grad' is the abbreviation in "grad. tehničar" (građevinski); as an occupation it would match "St. Grad".
    # A clause after the ethnicity is no occupation: "Hrvat, rođen u s. Garčin", "živi u s. Sibinj"
    occupations = Counter({w: n for w, n in occ.items() if n >= 2 and not RANK_RE.fullmatch(w) and w not in ('u', 'i', 'borac', 'grad', 'rođ', 'rod')
                           and not re.match(r'(?:rođen|živ|pogin|umr|nesta|ubijen|stri?jeljan|streljan|ranjen|zarobljen)\w*\b', w)
                           and not UNIT_RE.search(w) and not any(rx.search(w) for rx, _ in SPECIAL_UNITS)})
    occupations = plausible_occupations(occupations)
    # known places (nominative): existing birth/death places, then birthplaces the extractor itself reads
    places = Counter()
    for s in all_recs:
        for f in ('birth_place', 'death_place'):
            for p in re.split(r',\s*', s.get(f) or ''):
                if p and re.match(rf'^[{U}]', p):
                    places[p] += 1
    ex = Extractor(occupations, places)
    for code, (_, d) in brigades.items():
        for s in d:
            info = re.sub(r'^(?:(?:zvan[ai]|ili|rođ\.|roj\.|por\.)\s[^;]{0,60};\s*|(?:dr|ing|arh|mr)\.;\s*)+', '', s.get('additional_info') or '')
            if re.search(r'\bro[dđ]en[a]?\s+(?:\S+\s+){0,2}u\s+(?!s\.|selu)', info[:50]):   # "rođen 1923. godine u"
                continue                                                  # "rođen u Donjem Lapcu" is a locative, not a place name
            bp = ex.life(info, code).get('birth_place', '')
            for p in re.split(r',\s*', bp):
                if p and re.match(rf'^[{U}][{L}]', p) and '(' not in p:
                    places[p] += 1
    for extra in ('Sutjeska', 'Zelengora', 'Neretva', 'Romanija', 'Majevica', 'Kozara', 'Grmeč', 'Srem', 'Bosna', 'Slavonija',
                  'Hercegovina', 'Lika', 'Kordun', 'Banija', 'Dalmacija', 'Crna Gora', 'Sandžak', 'Istra', 'Italija', 'Nemačka', 'Njemačka',
                  'Mađarska', 'Austrija', 'Albanija', 'Grčka', 'Bugarska', 'Rumunija'):
        places[extra] += 5
    return ex


_EXTRACTOR = None


def get_extractor() -> Extractor:
    global _EXTRACTOR
    if _EXTRACTOR is None:
        _EXTRACTOR = build_extractor(load_live())
    return _EXTRACTOR


def brigade_of(soldier: dict) -> int:
    return int(soldier['soldier_id'][:4])


def forget_stale(soldier: dict, old_info: str, keep=()) -> None:
    """additional_info was rewritten: drop the structured values that had been read from the old text
    (values set by hand differ from what the extractor reads, so they stay)."""
    old = get_extractor().extract(old_info, brigade_of(soldier))
    for f in FIELDS:
        if f not in keep and soldier.get(f) and soldier[f] == old.get(f):
            del soldier[f]


# "Partizanke Pete proleterske crnogorske brigade" (the Poreklo library): long bios that also tell how her brothers,
# father or husband died ("brat Radisav, koji je poginuo na Kablenoj glavi"); only a death in her own words is hers
PARTIZANKE = '00005897'
RELATIVE = re.compile(r'\b(?:brat|brata|bratom|braća|braće|sestr[aeiu]|sestrom|otac|oca|ocem|majk[aeu]|majkom|muž|muža|mužem'
                      r'|sin|sina|sinom|sinovi|sinova|kći|kćerk[aeu]|kćeri|djeca|djece|roditelji|roditelja'
                      r'|članovi|člana porodice|saborc[ai]|saborci|drugovi|drugarice)\b', re.I)
MASCULINE_DEATH = re.compile(r'\b(?:poginu[oli]|poginuše|umr[oli]|umriješe|stri?jeljan[i]?|ubijen[i]?|nesta[oli])\b', re.I)
FEMININE_DEATH = re.compile(r'\b(?:poginula|umrla|stri?jeljana|ubijena|nestala)\b', re.I)


def her_own_deaths(info: str) -> str:
    """The bio without the sentences about other people's deaths: a death verb in the masculine or plural, or one
    beside a relative or comrade"""
    keep = []
    for sent in re.split(r'(?<=[.!?])\s+', info):
        if (MASCULINE_DEATH.search(sent) and not FEMININE_DEATH.search(sent)) or \
                ((MASCULINE_DEATH.search(sent) or FEMININE_DEATH.search(sent)) and RELATIVE.search(sent)):
            continue
        keep.append(sent)
    return ' '.join(keep)


def read_all(ex: Extractor, s: dict, code: int) -> dict:
    """The fields the soldier's bio gives, then those only the entries of other books merged into the record
    (other_sources) give."""
    got = {}
    # another unit's entries: its own fields; a book across units (a hero's portrait): read by no rule here
    entries = [s] + [o for o in s.get('other_sources', ()) if not o.get('unit_file') and not o.get('ref_book')]
    for e in entries:
        info = e.get('additional_info', '')
        if PARTIZANKE in (e.get('source_url') or ''):
            info = her_own_deaths(info)
        sutjeska = (e.get('pdf_file') or '').startswith('borci-sutjeske')          # the duty at the battle comes first
        for k, v in ex.extract(info, code, duty_first=sutjeska).items():
            if k == 'death_place' and PARTIZANKE in (e.get('source_url') or ''):
                continue            # the bios tell the death in a story: "poginula Plana", "Tako se ugasio ..." are no places
            got.setdefault(k, v)
    return got


def fill(soldiers: list[dict]) -> int:
    """Fill empty structured fields in place; returns how many records gained a field."""
    ex, n = get_extractor(), 0
    for s in soldiers:
        new = {k: v for k, v in read_all(ex, s, brigade_of(s)).items() if not s.get(k)}
        if new:
            s.update(new)
            n += 1
    return n


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--apply', action='store_true', help='write the brigade JSON files')
    ap.add_argument('--sample', type=int, default=6, help='samples to print per brigade (dry run)')
    ap.add_argument('--brigade', type=int, help='only this brigade code')
    args = ap.parse_args()

    brigades = load_live()
    ex = build_extractor(brigades)
    random.seed(1)
    total = Counter()
    for code, (fname, d) in brigades.items():
        if args.brigade and code != args.brigade:
            continue
        filled, samples, touched = Counter(), [], 0
        for s in d:
            got = read_all(ex, s, code)
            new = {k: v for k, v in got.items() if not s.get(k)}
            if new:
                touched += 1
                filled.update(new.keys())
                samples.append((s['additional_info'], new))
                if args.apply:
                    s.update(new)
        with_any = sum(1 for s in d if any(s.get(f) for f in FIELDS)) if args.apply else None
        total.update(filled)
        print(f"{BRIGADE_CONFIGS[code]['name'][:28]:28s} {len(d):6d} records, {touched:6d} gain fields  {dict(filled)}")
        if not args.apply:
            for info, new in random.sample(samples, min(args.sample, len(samples))):
                print(f'     {info[:120]!r}\n        -> {new}')
        if args.apply and touched:
            (ROOT / 'website' / 'public' / fname).write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding='utf-8')
    print('TOTAL', dict(total))
    if not args.apply:
        print('\nDry run. Use --apply to write.')


if __name__ == '__main__':
    main()
