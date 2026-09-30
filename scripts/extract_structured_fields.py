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
BIRTH_DATE_RE = re.compile(rf'^(?:[Rr]ođen[a]?\s+(?:je\s+)?)?(?:{DATE}|[\s.,]*\.\.[\s.]*)[.,]?\s*')

DEATH_KW = {
    'poginuo': 'poginuo', 'poginula': 'poginuo', 'padel': 'poginuo', 'padla': 'poginuo', 'pal': 'poginuo',
    'umro': 'umro', 'umrla': 'umro', 'umrl': 'umro', 'preminuo': 'umro', 'podlegao': 'umro', 'podlegla': 'umro',
    'nestao': 'nestao', 'nestala': 'nestao', 'pogrešan': None,
    'streljan': 'streljan', 'streljana': 'streljan', 'strijeljan': 'streljan', 'strijeljana': 'streljan', 'ustreljen': 'streljan',
    'ubijen': 'ubijen', 'ubijena': 'ubijen', 'zaklan': 'ubijen', 'zaklana': 'ubijen',
}
DEATH_RE = re.compile(r'\b(' + '|'.join(k for k, v in DEATH_KW.items() if v) + r')\b', re.I)

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
    r'(?:mlađi|stariji) vodnik', r'vodnik I\. klase', r'kapetan I\. klase',
    r'general-(?:major|lajtnant|potpukovnik)',
    r'borac', r'borec', r'kuvar(?:ica)?', r'kuhar(?:ica)?', r'bolničar(?:ka)?', r'kurir(?:ka)?', r'desetar', r'vodnik', r'podnarednik', r'narednik', r'zastavnik',
    r'potporučnik', r'poručnik', r'kapetan', r'major', r'potpukovnik', r'pukovnik',
    r'puškomitraljezac', r'mitraljezac', r'nišand[žz]ija', r'minobacačlija', r'bombaš', r'izviđač', r'obave[šs]tajac', r'obavještajac',
    r'telefonist(?:a|kinja)', r'telegrafist(?:a|kinja)', r'radiotelegrafist(?:a|kinja)', r'vezist(?:a|kinja)',
]
RANK_RE = re.compile(r'(?<![\w-])(' + '|'.join(RANK_PATTERNS) + r')(?![\w-])', re.I)

UNIT_RE = re.compile(r'(?<![\w.])(\d{1,2}\.|[IVX]{1,4}\.?)\s?(četa|čete|četi|č\.?|bataljon|bataljona|bataljonu|bat\.?|desetina|desetine|vod|voda|vodu)'
                     r'(?![\w])', re.I)
SPECIAL_UNITS = [
    (re.compile(r'\b(\d\.\s?(?:kordunaški|makedonski|slovenački|slovenski|ličk[i]|dalmatinski|udarni|omladinski))\s+bataljon', re.I), '{} bataljon'),
    (re.compile(r'\bpratećoj?\s+čet[aei]|\bprateć[ae] čete', re.I), 'prateća četa'),
    (re.compile(r'\bomladinsk(?:a|e|oj) čet[aei]', re.I), 'omladinska četa'),
    (re.compile(r'\bbataljon(?:a|u)? Garibaldi', re.I), 'bataljon Garibaldi'),
    (re.compile(r'\bprištapsk(?:e|ih) jedinic', re.I), 'prištapske jedinice'),
    (re.compile(r'\b(izviđačk|inžinjerijsk|protivtenkovsk|protivavionsk|protivoklopn|prištapsk|sanitetsk|mitraljesk)(?:a|e|oj)\s+čet[aei]\b', re.I), '{}a četa'),
    (re.compile(r'\bčet[aei]\s+za\s+vezu\b', re.I), 'četa za vezu'),
    (re.compile(r'\b(protivtenkovsk|protivavionsk|artiljerijsk)(?:a|e|oj)\s+baterij[aei]\b', re.I), '{}a baterija'),
    (re.compile(r'\bintendantur(?:a|e|i)\b', re.I), 'intendantura'),
]

PREP = r'(?:u|na|kod|v|pri|nad|pod|iznad|ispod|blizu|kraj|pored|oko|između|izmedu|prema|pred|za|iz|na putu za|u selu|u s\.|s\.|selo|u rejonu|rejon)'
STOP_PLACE = re.compile(r'^(?:u NOB|u NOV|u NOVJ|u NOR|u brigadi|u \d|član|stupio|stupila|borac od|od \d|od [a-z]|sa |iz |zvani|ili |'
                        r'drugih|nema |ostali|nepoznat|\(drugih|\(nema|\(nedostaju)', re.I)


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


class Extractor:
    def __init__(self, occupations: Counter, places: Counter):
        self.occupations = set(occupations)
        self.places = places
        # OCR-misspelt occupations map to the common spelling: "zemljradnik", "zemloradnik" -> "zemljoradnik"
        common = [w for w, n in occupations.items() if n >= 50]
        self.occ_spelling = {}
        for w, n in occupations.items():
            if n < 10:
                close = difflib.get_close_matches(w, common, n=1, cutoff=0.85)
                if close and close[0] != w:
                    self.occ_spelling[w] = close[0]

    def occupation(self, w: str) -> str:
        return self.occ_spelling.get(w, w)

    # ── birth / ethnicity / occupation ───────────────────────
    def life(self, text: str, code: int) -> dict:
        out = {}
        t = text
        # a function printed before "rođen" (Treća proleterska, 5. kozaračka): "desetar 3. desetine, rođen 1920, ..."
        m = re.search(r'\b[Rr]ođen[a]?\b', t)
        head = t[:m.start()] if m else ''
        if m:
            t = t[m.start():]
        elif code == 15:
            t = ''                                                        # 1. šumadijska always says "Rođen ..."
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
        from_place = code in (2, 31) and re.match(rf'^iz\s+[{U}]', t) is not None
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
            if tail and (tail.group(2) in ETHNIC or tail.group(2) in self.occupations):   # "Italija Talijan" (comma missing)
                place.append(tail.group(1))
                break
            if (s in ETHNIC or looks_ethnic(s) or s.lower() in self.occupations or RANK_RE.fullmatch(s) or UNIT_RE.search(s)
                    or any(rx.search(s) for rx, _ in SPECIAL_UNITS)
                    or STOP_PLACE.match(s) or DEATH_RE.search(s) or re.search(r'\d', s) or len(s) > 40 or len(s.split()) > 4
                    or not re.match(rf'^(?:[{U}]|\((?=[{U}])|(?:s|sv|st)\.\s[{U}])', s)):
                break
            place.append(s)
            if len(place) == 3:
                break
        if place:
            if locative or any(' kod ' in p for p in place):                  # "u selu Makcima kod Velikog Gradišta"
                place = [self.nominative(p, keep=True) for p in place]
            bp = ', '.join(place)
            bp = re.sub(r',\s*\(', ' (', bp)                               # "Budisava, (Titel)"
            bp = re.sub(r'\s+-\s+', ', ', bp)                              # "Ćuić Krčevina - T. Korenica"
            out['birth_place'] = bp
        # ethnicity and occupation: the words of the bio up to the death clause
        words = [clean_segment(s) for s in re.split(r'[,;]\s*|\.\s', text)]
        for i, w in enumerate(words):
            if w in ETHNIC:
                out['ethnicity'] = w
                if i + 1 < len(words) and words[i + 1].lower() in self.occupations:
                    out['occupation'] = self.occupation(words[i + 1].lower())
                break
        if 'occupation' not in out:
            for w in words[:8]:
                if w.lower() in self.occupations and w.lower() not in ('borac',):
                    out['occupation'] = self.occupation(w.lower())
                    break
        if head:
            out['_head'] = head
        return out

    # ── death ────────────────────────────────────────────────
    def death(self, text: str) -> dict:
        out = {}
        m = DEATH_RE.search(text)
        mesto = re.search(r'mesto smrti\s*:\s*([^,;.]+(?:\s\([^)]*\))?)', text, re.I)
        if not m:
            if mesto:
                out['death_place'] = clean_segment(mesto.group(1))
            return out
        kw = m.group(1).lower()
        out['death_type'] = DEATH_KW[kw]
        rest = text[m.end():]
        # the death clause runs to the end of its sentence, or to "sahranjen" / a new clause
        clause = sentences(rest)[0] if rest.strip() else ''
        clause = re.split(r'[,;]?\s*(?:sahranjen|sahranjena|pokopan|pokopana|mesto sahrane|mjesto sahrane|a sahranjen|ostao na|nije sahranjen)', clause)[0]
        dm = DATE_RE.search(clause)
        if dm and not 1941 <= int(re.search(YEAR, dm.group(0)).group(0)) <= 2000:
            dm = None                                                     # "umro u bolnici, 1926, Vršac" — that is the birth year
        if dm:
            date = re.sub(r'\.?\s*god(?:ine|\.)$', '', dm.group(0)).rstrip('.').strip()
            date = re.sub(r'^u\s', '', date)
            out['death_date'] = date
            clause = clause[:dm.start()] + ' ' + clause[dm.end():]
        clause = re.sub(r'\s+kao\s+.*$', '', clause)                     # "poginuo 1943. kao borac 19. divizije"
        clause = re.sub(r'\b(?:u borbi|u napadu|u akciji|u zarobljeništvu|u bolnici|u logoru|u ratu|u NOR-u)\b\s*', '', clause)
        clause = re.sub(r'(?:,\s*|\s+)(?:i tu|gde|gdje|protiv|dok|pošto|jer|kada|kad)\b.*$', '', clause)   # "kod Vrbovca i tu", "..., gdje je i"
        clause = re.sub(r'\s*\((?:nema|drugih|nedostaju|ostali)[^)]*\)?', '', clause)
        clause = re.sub(rf'^[{U}]\.,\s*', '', clause.strip())                # "S., Soljani" (OCR)
        clause = re.sub(r'^[\s,]*(?:od|usled|uslijed|zbog)\s+[^,]*?(?=,|\s(?:u|na|kod|v|pri)\s|$)', '', clause.strip())   # cause of death
        clause = clean_segment(re.sub(r'\s+', ' ', clause))
        if mesto:
            out['death_place'] = clean_segment(mesto.group(1))
        elif clause and len(clause) <= 70 and not re.search(r'\d', clause) and re.match(rf'^(?:{PREP}\s+)?(?:s\.\s)?[{U}]', clause):
            out['death_place'] = self.nominative(clause)
        return out

    # ── locative/genitive -> nominative, only when the result is a known place ──
    _WORD_RULES = [
        ('ima', 'i'), ('ama', 'e'), ('iji', 'ija'), ('ci', 'ka'), ('ci', 'ca'), ('zi', 'ga'), ('si', 'ha'), ('u', ''), ('u', 'o'), ('u', 'a'),
        ('ju', 'j'), ('ju', 'je'), ('om', 'o'), ('em', 'e'), ('i', 'a'), ('i', 'e'), ('oj', 'a'), ('oj', 'o'), ('om', 'i'), ('om', ''), ('em', 'i'),
        ('eg', 'i'), ('og', 'i'), ('og', 'o'), ('e', 'a'), ('a', ''), ('a', 'o'), ('a', 'e'), ('a', 'i'), ('ova', 'ovi'), ('eva', 'evi'), ('aca', 'ci'),
        ('ije', 'ija'), ('ske', 'ska'), ('ke', 'ka'), ('cu', 'ec'), ('ca', 'ac'), ('ga', 'g'), ('ka', 'ak'), ('e', 'i'), ('ih', 'i'), ('i', 'o'),
        ('aka', 'ci'), ('ra', 'ar'),
    ]

    def _variants(self, word: str) -> set[str]:
        out = {word}
        for suf, rep in self._WORD_RULES:
            if word.endswith(suf) and len(word) - len(suf) >= 2:
                out.add(word[:-len(suf)] + rep)
        return out

    def _known(self, phrase: str) -> str | None:
        words = phrase.split()
        if not words or len(words) > 4:
            return None
        if self.places.get(phrase):
            return phrase                                                 # already a known nominative
        best = None
        for combo in product(*(self._variants(w) for w in words)):
            cand = ' '.join(combo)
            n = self.places.get(cand, 0)
            if n and (best is None or n > best[0]):
                best = (n, cand)
        return best[1] if best else None

    def nominative(self, clause: str, keep: bool = False) -> str:
        """'na Sutjesci' -> 'Sutjeska'; 'u selu Grabovo kod Vukovara' -> 'Grabovo, Vukovar'; unknown -> as printed
        (keep=True: unknown parts stay as they are, the known ones are still converted)."""
        parts = [p for p in re.split(r',\s*|\s+-\s+|\s+(?=kod\s|pri\s)', clause) if p.strip()]
        names, bare = [], []
        for p in parts:
            prep = re.match(rf'^{PREP}\s+', p.strip())
            p = re.sub(rf'^{PREP}\s+', '', p.strip())
            p = re.sub(r'^(?:selu|selo|s\.)\s+', '', p)
            bare.append(not prep or prep.group(0).strip() in ('s.', 'selo'))
            known = self._known(p)
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
            if r not in found:
                found.append(r)
        # a specific function makes the generic "borac" redundant; "politički komesar" is covered by "politički komesar brigade"
        if len(found) > 1 and 'borac' in found:
            found.remove('borac')
        found = [r for r in found if not any(o != r and o.startswith(r + ' ') for o in found)]
        return ', '.join(found[:3])

    @staticmethod
    def unit(text: str) -> str:
        t = re.split(r'\b(?:u NOV|U NOV)\s+od\b', text)[0] if re.search(r'\bu 2\. dalm', text) else text
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

    def extract(self, info: str, code: int) -> dict:
        text = re.sub(r'^(?:(?:zvani|ili|rođ\.)\s[^;]{0,60};\s*)+', '', info or '').strip()
        text = re.sub(r'\s*\((?:općina [^)]*|ČSSR)\)$', '', text)          # 17. slavonska: section the soldier was listed under
        text = re.sub(r'\s+', ' ', text)
        if not text or len(text) < 3:
            return {}
        dm = DEATH_RE.search(text)
        life_text = text[:dm.start()] if dm else text
        out = self.life(life_text, code)
        head = out.pop('_head', '')
        out.update(self.death(text))
        rank = self.ranks((head + ' ' if head else '') + text)
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
    all_recs = [s for _, d in brigades.values() for s in d]
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
    occupations = Counter({w: n for w, n in occ.items() if n >= 2 and not RANK_RE.fullmatch(w) and w not in ('u', 'i', 'borac', 'grad')
                           and not re.match(r'(?:rođen|živ|pogin|umr|nesta|ubijen|stri?jeljan)\w*\b', w)
                           and not UNIT_RE.search(w) and not any(rx.search(w) for rx, _ in SPECIAL_UNITS)})
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
            info = re.sub(r'^(?:(?:zvani|ili)\s[^;]{0,60};\s*)+', '', s.get('additional_info') or '')
            if re.search(r'\brođen[a]?\s+(?:\S+\s+)?u\s+(?!s\.|selu)', info[:40]):
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


def fill(soldiers: list[dict]) -> int:
    """Fill empty structured fields in place; returns how many records gained a field."""
    ex, n = get_extractor(), 0
    for s in soldiers:
        new = {k: v for k, v in ex.extract(s.get('additional_info', ''), brigade_of(s)).items() if not s.get(k)}
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
            got = ex.extract(s.get('additional_info', ''), code)
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
