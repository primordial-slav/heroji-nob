"""The unit on the site an entry names without doubt (2026-11-20, the user's rule after Dragosavac Jovice Dušan of
Borci drugih jedinica, whose entry says "Poginuo u 2. bat. 3. brig. 6. lič. prol. DNT": he fell with the 3. lička,
which is on the site; such men become records of their unit).

Every unit an entry names is read against the whole order of battle of the war (data-extraction/novj, from Anić,
Joksimović, Gutić, Narodnooslobodilačka vojska Jugoslavije: 367 brigades, 68 divisions, 512 odreds), and counts only
where novj/site_links.json ties it to a unit on the site; so a name that fits two units of the war fits none here:

- a brigade with its division ("3. brig. 6. lič. prol. DNT", "1. brigadi VII banijske divizije"): the brigade the
  table names so ("Sedma banijska udarna brigada (1. brigada 7. divizije)"); else, where the division is on the site,
  the division (a brigade known only by its number there is not sure); else the one brigade of that number that served
  in the division (3. brig. 6. div. is the 3. lička, 23. brig. 45. div. the 23. srpska), unless the number could also
  be the brigade's place in the division, where the division's brigades bear other numbers ("3. brigada 7. divizije"
  is the 16. banijska or the 3. banijska): no unit;
- a brigade by its number and name, the one brigade of the war so named, under any of its names ("4. sandžačke NOU
  brigade", "II krajiškoj brigadi", "3. lič. brig.", "1. hrvatske brigade" for the 1. lička);
- a division alone ("8. div.", "2. proleterske divizije"); a KNOJ division only where KNOJ is printed, and its
  adjectives must fit the division's names ("3. prolet. divizija" fits none);
- an odred by its name ("Tuzlanskog NOP odreda").

A bare number ("3. brigada", "borac 1. bataljona") names no unit; the enemy's units ("7. SS divizija") are skipped,
and so is a list's heading before the entry. The division pages that hold only their staff at Sutjeska (STAFF_ONLY)
take no one: a man of their brigades goes to the brigade where it is on the site, else no unit (the user's choice).

    unit_of(texts) -> (code, how) or (None, why): one unit on the site, or none
"""
from __future__ import annotations

import json
import re
import unicodedata
from collections import defaultdict
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NOVJ = ROOT / 'data-extraction' / 'novj'

# units on the site that novj/site_links.json doesn't tie to the table, each read against its name (2026-11-20; the
# 4. prekomorska and the 4. brigada Slavonije the table lacks)
SITE_LINKS_MORE = {('brigades', 3): 123, ('brigades', 31): 124, ('brigades', 171): 127, ('brigades', 183): 128,
                   ('brigades', 175): 165, ('brigades', 16): 146, ('brigades', 236): 143, ('brigades', 232): 144,
                   ('brigades', 233): 144, ('brigades', 142): 141, ('brigades', 156): 142, ('brigades', 150): 167,
                   ('divisions', 9): 145, ('divisions', 64): 140, ('detachments', 452): 126, ('detachments', 377): 147,
                   ('detachments', 290): 148, ('detachments', 360): 149, ('detachments', 432): 164,
                   ('detachments', 526): 169, ('detachments', 430): 171}
# the division pages that hold only the staff and its services at Sutjeska ("Štab divizije, njegove službe i prateće
# jedinice u bici na Sutjesci"): no brigade's man goes there (2026-11-20)
STAFF_ONLY = {113, 114, 115, 116}
# the table's KNOJ brigades ("brigada NO" after the word, "divizije NO", the Slovene and Croatian security troops), and a
# text that names KNOJ: the army's "NO udarna brigada" has NO before the word
# the table's misprints (novj/brigades.json, OCR of Anić et al.), mended before its names are read: "Peta proterska (cr
# nogorska)" hid the 5. proleterska crnogorska, "Treća krajška" the 3. krajiška (05, 2026-11-24, Lekić Mahmut)
TABLE_MENDS = [(r'\bproterska\b', 'proleterska'), (r'\bcr nogorsk', 'crnogorsk'), (r'\bkrajšk', 'krajišk'),
               (r'\bbrgad', 'brigad'), (r'\bdivizje\b', 'divizije'), (r'\bdiVizij', 'divizij'), (r'\budama\b', 'udarna'),
               (r'\bproterske\b', 'proleterske')]
KNOJ_NAME = re.compile(r'\bbri?gad\w*\s+NO\b|\bdi[vV]iz\w*\s+NO\b|državne varnosti|zaštitu naroda')  # the table's "brgada", "divizje"
KNOJ_TEXT = re.compile(r'KNOJ|[Nn]arodne odbrane|\bbrigad\w*\s+NO\b')


def fold(t: str) -> str:
    return ''.join(c for c in unicodedata.normalize('NFD', (t or '').lower())
                   if not unicodedata.combining(c)).replace('đ', 'd')


ORD = [('dvadeset', 20), ('trideset', 30), ('cetrdeset', 40), ('pedeset', 50), ('jedanaest', 11), ('dvanaest', 12),
       ('trinaest', 13), ('cetrnaest', 14), ('petnaest', 15), ('sesnaest', 16), ('sedamnaest', 17),
       ('sedaemnaest', 17), ('osamnaest', 18), ('devetnaest', 19), ('prv', 1), ('drug', 2), ('trec', 3),
       ('cetvrt', 4), ('pet', 5), ('sest', 6), ('sedm', 7), ('osm', 8), ('devet', 9), ('deset', 10)]
ROMAN = {'i': 1, 'ii': 2, 'iii': 3, 'iv': 4, 'v': 5, 'vi': 6, 'vii': 7, 'viii': 8, 'ix': 9, 'x': 10, 'xi': 11,
         'xii': 12, 'xiii': 13, 'xiv': 14, 'xv': 15, 'xvi': 16, 'xvii': 17, 'xviii': 18, 'xix': 19, 'xx': 20}
# (with the diacritics too: WB reads the text as written, "Treće proleterske sandžačke brigade", 2026-11-23)
ORD_WORD = (r'(?:dvadeset|trideset|[cč]etrdeset|pedeset|jedanaest|dvanaest|trinaest|[cč]etrnaest|petnaest|[sš]esnaest|'
            r'sedamnaest|osamnaest|devetnaest|prv|drug|tre[cć]|[cč]etvrt|pet|[sš]est|sedm|osm|devet|deset)[a-zčćžšđ]*')


def ord_value(words: list[str]) -> int | None:
    """the number a unit's name opens with: "dvadeset peta" 25, "treca" 3, "13" 13, "xiii" 13"""
    words = [w for w in words if w]
    if not words:
        return None
    w0 = words[0].rstrip('.')
    if w0.isdigit():
        return int(w0)
    if w0 in ROMAN:
        return ROMAN[w0]
    total = 0
    for w in words[:2]:
        for stem, v in ORD:
            if w.startswith(stem):
                if total and total % 10 == 0 and v < 10:
                    total += v
                elif not total:
                    total = v
                break
        else:
            break
    return total or None


# words of a unit's name that say nothing of which unit it is
FILLER = {'no', 'nou', 'nob', 'nov', 'udarna', 'udarne', 'udarnoj', 'udarnu', 'udar', 'brigada', 'brigade', 'brigadi',
          'brig', 'brigadu', 'narodnooslobodilacka', 'narodnooslobodilacke', 'i', 'od', 'do', 'u', 'pri', 'formiranju',
          'kasnije', 'je', 'bila', 'naziv', 'dobila', 'nop', 'novj', 'njih', 'ili'}


def words_of(t: str) -> list[str]:
    return [w for w in re.findall(r'[a-z]+', fold(t)) if w not in FILLER and len(w) >= 2]


def wmatch(t: str, a: str) -> bool:
    """a text's word (perhaps cut: "lic", "prol", "dalm") against a name's word, in another case ("licke", "licka")"""
    n = 0
    for x, y in zip(t, a):
        if x != y:
            break
        n += 1
    return n >= 3 and (n == len(t) or n >= min(len(t), len(a)) - 1 and n >= 4)


@lru_cache(maxsize=1)
def tables() -> dict:
    """the order of battle read once: the site's units by table entry, the brigades' names as (number, words), the
    brigades named "N. brigada D. divizije", each brigade's divisions and numbers, the divisions by number, the odreds
    by the stem of their name"""
    import sys
    sys.path.insert(0, str(ROOT / 'scripts'))
    from name_utils import BRIGADE_CONFIGS, OSTALI_CODES
    files = {cfg['json_file']: code for code, cfg in BRIGADE_CONFIGS.items() if code not in OSTALI_CODES}
    ts = (ROOT / 'website' / 'app' / 'data' / 'units.ts').read_text(encoding='utf-8')
    id_code = {m.group(1): files.get(m.group(2).lstrip('/'))
               for m in re.finditer(r"id:\s*'([^']+)'[\s\S]*?dataFile:\s*'([^']+)'", ts)}
    links = json.loads((NOVJ / 'site_links.json').read_text(encoding='utf-8'))
    site = {(v['table'], v['no']): id_code[uid] for uid, v in links.items() if id_code.get(uid)}
    site.update(SITE_LINKS_MORE)
    brig = json.loads((NOVJ / 'brigades.json').read_text(encoding='utf-8'))
    aliases, in_div, div_of, num_of = [], defaultdict(set), defaultdict(set), defaultdict(set)
    knoj = set()                                  # KNOJ's brigades: "Treća brigada 7. divizije NO (3. vojvođanska brigada NO)"
    for b in brig:
        key = ('brigades', b['no'])
        name = b['name'].replace('\n', ' ')
        for wrong, right in TABLE_MENDS:
            name = re.sub(wrong, right, name)
        if KNOJ_NAME.search(name):
            knoj.add(key)
        for m in re.finditer(r'(\d{1,2})\.\s*(?:NOU\s+|NO\s+|udarna\s+)?brigad\w*\s+(\d{1,2})\.\s*divizij', name):
            in_div[(int(m.group(1)), int(m.group(2)))].add(key)
        for p in b.get('periods') or ():
            if p.get('division'):
                div_of[key].add(int(p['division']))
        # (a date is no name: "proleterska od 19. III 1944" gave a 9.; nor the division a name ends with: "Treća
        # banijska brigada 7. divizija")
        name = re.sub(r'\b(?:od|do)\s+(?:\d{1,2}\.\s*)?(?:[IVX]{1,4}\b\.?|[a-zčćžšđ]+)?\s*\'?\d{2,4}\.?', ' ', name)
        name = re.sub(r'\d{1,2}\.\s*(?:operativne\s+zone|divizij\w*|korpus\w*)[^,;()]*', ' ', name)
        inline = re.sub(r'\(([^()\d]*)\)', r' \1 ', name)
        # a name the brigade had before or after, without its number, is the same brigade's ("Osma dalmatinska brigada
        # (udarna) pri formiranju šibenska brigada": "8. šibenska brigada" is the 8. dalmatinska; 2026-11-24, Perkov Ante)
        later = set()
        segs = []
        for i, part in enumerate(re.split(r'\bpri formiranju\b|\bkasnije\b|\bformirana kao\b', name)):
            pieces = re.split(r'[(),;]', part)
            if i:
                later.add(len(segs))
            segs += pieces
        if inline != name:
            segs += re.split(r'[,;]|\bpri formiranju\b|\bkasnije\b|\bformirana kao\b', inline)[:1]
        first = None
        for n_seg, seg in enumerate(segs):
            w = re.findall(r'[a-z0-9]+', fold(seg))
            num = ord_value(w[:2]) if w else None
            if num and first is None:
                first = num
            if not num and n_seg in later and first:
                num = first
            if key == ('brigades', 76) and num == 20:
                num = 21      # the table's "Dvadesetprva slavonska" in one word: the 21. slavonska (2026-11-23, Dvorski Martin)
            if not num:
                continue
            rest = frozenset(x for x in w if x not in FILLER and not x.isdigit() and not re.fullmatch(ORD_WORD, x)
                             and x not in ROMAN and not x.startswith(('divizij', 'korpus')))
            aliases.append((num, rest, key))
            num_of[key].add(num)
    members = defaultdict(set)                    # division -> the brigades that served in it
    for key, ds in div_of.items():
        for d in ds:
            members[d].add(key)
    div_num, knoj_num, div_words = defaultdict(set), defaultdict(set), {}
    for dv in json.loads((NOVJ / 'divisions.json').read_text(encoding='utf-8')):
        w = re.findall(r'[a-z0-9]+', fold(dv['name']))
        n = ord_value(w[:2])
        if n:
            key = ('divisions', dv['no'])
            (knoj_num if 'knoj' in w else div_num)[n].add(key)
            div_words[key] = [x for x in w if x not in FILLER]
    det_stem = defaultdict(set)
    for d in json.loads((NOVJ / 'detachments.json').read_text(encoding='utf-8')):
        for seg in re.split(r'[(),;]', d['name']):
            w = re.findall(r'[a-z]+', fold(seg))
            if w and w[0] not in ('odred', 'nop', 'partizanski'):
                det_stem[re.sub(r'(ski|ki)$', '', w[0])[:7]].add(('detachments', d['no']))
    return {'site': site, 'aliases': aliases, 'in_div': in_div, 'div_of': div_of, 'num_of': num_of, 'knoj': knoj,
            'members': members, 'div_num': div_num, 'knoj_num': knoj_num, 'div_words': div_words, 'det_stem': det_stem}


def brigade_by_name(num: int, words: list[str], knoj: bool = False):
    """the one brigade of the war of this number whose name has these words: the same words first, else a name holding
    them (a region's word among them); (key or None, how many fit)"""
    words = [w for w in words if w not in FILLER]
    region = [w for w in words if not w.startswith(('prol', 'omlad', 'udar'))]
    if not words:
        return None, 0
    # KNOJ's brigades share the army's numbers and names (its 3. vojvođanska of December 1944 and the army's): one counts
    # only where the text says KNOJ or "narodne odbrane", as with its divisions (2026-11-24, Petrenj Mara)
    t = tables()
    cands = [(set(a), k) for n, a, k in t['aliases'] if n == num and (k in t['knoj']) == knoj]
    exact = {k for a, k in cands if len(a) == len(words) and all(any(wmatch(t, x) for x in a) for t in words)}
    if len(exact) == 1:
        return exact.pop(), 1
    if not region:
        return None, len(exact)
    sub = {k for a, k in cands if all(any(wmatch(t, x) for x in a) for t in words)}
    return (sub.pop(), 1) if len(sub) == 1 else (None, len(sub))


def division(n: int, adj: str, near: str) -> set:
    """the divisions of this number: KNOJ's only where the text says KNOJ (its 1., 3., 7. and 8. share the army's
    numbers); every adjective must fit the division's names, "proleterska" too ("DNT" is the 6. lička's Nikola Tesla)"""
    t = tables()
    keys = (t['knoj_num'] if 'KNOJ' in near else t['div_num']).get(n, set())
    words = [x for x in words_of(adj) if not x.startswith(('udar', 'div', 'nov')) and x not in ('dnt', 'nt', 'd')]
    if words:
        keys = {k for k in keys if all(any(wmatch(w, x) for x in t['div_words'][k]) for w in words)}
    return keys


# the divisions whose brigades the books name by the brigade's own number, read against the table (2026-11-20): the
# 6. lička's 1., 2. and 3. lička; the 7. banijska's 7., 8. and 16. banijska (its 3. and 4. banijska bear numbers that
# may be a brigade's place in the division: "3. brigada 7. divizije" is the 16. or the 3. banijska); Serbia's divisions
# their srpske brigade by its number ("9. brig. 23. div.", "23. brigade 45. divizije")
OWN_NUMBERS = {6: ('lick', None), 7: ('ban', {7, 8, 16}), 21: ('srp', None), 22: ('srp', None), 23: ('srp', None),
               24: ('srp', None), 25: ('srp', None), 45: ('srp', None), 46: ('srp', None), 47: ('srp', None)}


def numbered_in(b: int, d: int):
    """the one brigade of division d that the books call b. brigada by its own number (OWN_NUMBERS)"""
    stem, numbers = OWN_NUMBERS.get(d, (None, None))
    if not stem or (numbers and b not in numbers):
        return None
    cands = {k for n, words, k in tables()['aliases'] if n == b and any(w.startswith(stem) for w in words)}
    return cands.pop() if len(cands) == 1 else None


ADJ = r'(?:[A-Za-zČĆŽŠĐčćžšđ][A-Za-zČĆŽŠĐčćžšđ-]*\.?\s+){0,4}?'
ENEMY = re.compile(r'\bSS\b|legion|njema|nema[cč]k|talijan|italijan|usta[sš]|domobran|[cč]etni|bugar|ma[dđ]ar|wehrm|'
                   r'nijem', re.I)
UNITWORD = re.compile(r'\b(?:brig|bat|čet|cet|vod|odred|korp|odelj|odjelj)', re.I)
# (a Roman number in capitals only: "i u X krajišku brigadu" is the 10. krajiška, not the "i" of a 1.)
BD = re.compile(r'(?<![\d.])(\d{1,2})\.\s*brig(?:ad\w*|\.)?\s*,?\s*(\d{1,2}\.|(?-i:[IVX]{1,5})\.?)\s*(' + ADJ +
                r')(?:div\w*\.?|D[A-ZŠ]{1,3}\b)', re.I)
NB = re.compile(r'(?<![\d.\w])(\d{1,2}|(?-i:[IVX]{1,5}))\.?\s+(' + ADJ + r')brig(?:ad\w*|\.)', re.I)
WB = re.compile(r'\b(' + ORD_WORD + r'(?:\s+' + ORD_WORD + r')?)\s+(' + ADJ + r')brigad\w*', re.I)
DV = re.compile(r'(?<![\d.])(\d{1,2})\.\s*(' + ADJ + r')(?:divizij\w*|div\.)', re.I)
OD = re.compile(r'\b([A-ZČĆŽŠĐ][a-zčćžšđ]+(?:sko-[a-zčćžšđ]+)?)\s+(?:NOP\s+|NO\s+|partizansk\w*\s+|'
                r'narodnooslobodila\w*\s+)?(?:odred\w*|NOPO|POd?)\b')


def strip_heading(t: str) -> str:
    """the entry's text without a list's heading before it ("Mosorski partizanski odred, II dio: ...: 1921, Krilo";
    the field reader's own rule, extract_structured_fields.Extractor.heading)"""
    import extract_structured_fields as esf
    if not t:
        return t
    first = esf.sentences(t)[0]
    colons = esf.list_colons(first, at_end=True)
    if not colons:
        return t
    end = colons[0]
    for c in colons[1:]:
        if re.search(r'\d', first[end:c]):
            break
        end = c
    return t[end + 1:]


def mentions(t: str) -> list[tuple]:
    """(site code or None, how, text) for each unit the text names"""
    tb = tables()
    site = tb['site']
    out, used = [], []

    def near(m):
        return t[max(0, m.start() - 25):m.end() + 25]
    for m in BD.finditer(t):
        if ENEMY.search(near(m)) or UNITWORD.search(m.group(3)):
            continue
        b, d = int(m.group(1)), ord_value([fold(m.group(2)).rstrip('.')])
        if not d:
            continue
        used.append(m.span())
        named = tb['in_div'].get((b, d), set())
        if len(named) == 1 and next(iter(named)) in site:
            out.append((site[next(iter(named))], 'brigade of its division by name', m.group(0)))
            continue
        dsite = {site[k] for k in division(d, m.group(3), near(m)) if k in site}
        if len(dsite) == 1 and not dsite & STAFF_ONLY:
            out.append((dsite.pop(), 'division of the brigade', m.group(0)))
            continue
        key = numbered_in(b, d)
        if key and key in site:
            out.append((site[key], 'brigade of its division by number', m.group(0)))
        else:
            out.append((None, 'brigade of a division, unsure', m.group(0)))
    def again(rx):
        pos = 0
        while True:
            m = rx.search(t, pos)
            if not m:
                return
            pos = m.start() + 1
            yield m
    for rx in (NB, WB):
        for m in again(rx):
            if any(s <= m.start() < e for s, e in used) or ENEMY.search(near(m)):
                continue
            num = ord_value(re.findall(r'[a-z0-9]+', fold(m.group(1))))
            words = words_of(m.group(2))
            if not num or not words or any(w.startswith(('bat', 'cet', 'vod', 'div', 'korp', 'odel')) for w in words):
                continue
            key, n = brigade_by_name(num, words, knoj=bool(KNOJ_TEXT.search(near(m))))
            used.append(m.span())
            if key and key not in site:
                dsite = {site[('divisions', d)] for d in tb['div_of'].get(key, ()) if ('divisions', d) in site}
                if len(tb['div_of'].get(key, ())) == 1 and len(dsite) == 1 and not dsite & STAFF_ONLY:
                    out.append((dsite.pop(), 'division of the brigade by name', m.group(0)))
                    continue
            if key:
                out.append((site.get(key), 'brigade by name' if key in site else 'brigade not on the site', m.group(0)))
            elif any(not w.startswith(('prol', 'omlad', 'udar')) for w in words):
                out.append((None, f'brigade by name, {n} fit', m.group(0)))
    for m in DV.finditer(t):
        if any(s <= m.start() < e for s, e in used) or ENEMY.search(near(m)) or UNITWORD.search(m.group(2)):
            continue
        keys = division(int(m.group(1)), m.group(2), near(m))
        if len(keys) == 1:
            k = next(iter(keys))
            code = site.get(k)
            if code in STAFF_ONLY:
                out.append((None, 'division whose page is its staff', m.group(0)))
            else:
                out.append((code, 'division' if code else 'division not on the site', m.group(0)))
    for m in OD.finditer(t):
        stem = re.sub(r'(skog|skom|skoga|ski|ški|škog|škom|sko)$', '', fold(m.group(1)).split('-')[0])[:7]
        if len(stem) < 4 or stem in ('partiz', 'gerils', 'borac', 'narodn', 'udarn'):
            continue
        keys = tb['det_stem'].get(stem, set())
        if len(keys) == 1:
            k = next(iter(keys))
            out.append((site.get(k), 'odred' if k in site else 'odred not on the site', m.group(0)))
        elif keys:
            out.append((None, f'odred, {len(keys)} of the name', m.group(0)))
    return out


def division_codes() -> set:
    """the site's units that are divisions"""
    return {c for k, c in tables()['site'].items() if k[0] == 'divisions'}


@lru_cache(maxsize=None)
def own_books(code: int) -> frozenset:
    """the unit's own PDFs (units.ts pdfFiles): an entry of these that its parser left out of the unit (the Mosor list's
    activists, a deserter) stays where it is, though it names the unit ("držao u ilegalnosti 2. četu ... Mosorskog PO")"""
    import sys
    sys.path.insert(0, str(ROOT / 'scripts'))
    from name_utils import BRIGADE_CONFIGS
    ts = (ROOT / 'website' / 'app' / 'data' / 'units.ts').read_text(encoding='utf-8')
    m = re.search(r"dataFile:\s*'/" + re.escape(BRIGADE_CONFIGS[code]['json_file']) + r"',\s*pdfFiles:\s*\[([^\]]*)\]", ts)
    return frozenset(re.findall(r"/pdfs/([^']+)'", m.group(1))) if m else frozenset()


def unit_of(texts: list[str]) -> tuple:
    """the unit on the site the texts name, and how; (None, why) where they name none on the site. Two on the site or
    more: the first named; one on the site and another: the one on the site (the user, 2026-11-24). A name of several
    odreds ("Gerilski odred") says nothing. A brigade and the division it served in are the brigade."""
    import extract_structured_fields as esf
    tb = tables()
    # (the next man's entry glued on after his is not his: "Ubile ga ustaše u Cetingradu 20. 4. 1942. JASIKA Milića
    # JANKO, ... 8. div.")
    texts = [esf.GLUED_RE.split(strip_heading(t or ''), maxsplit=1)[0] for t in texts]
    ms = [x for t in texts for x in mentions(t)]
    if not ms:
        return None, 'names no unit'
    units = {c for c, _, _ in ms if c}
    others = [x for x in ms if not x[0] and not x[1].startswith('odred, ')]
    divisions = {c for k, c in tb['site'].items() if k[0] == 'divisions'}
    if len(units) == 2 and len(units & divisions) == 1:
        dv = (units & divisions).pop()
        br = (units - {dv}).pop()
        dkeys = {k for k, c in tb['site'].items() if c == dv}
        dnums = {n for n, keys in tb['div_num'].items() if keys & dkeys}
        if any(tb['div_of'][k] & dnums for k, c in tb['site'].items() if c == br and k[0] == 'brigades'):
            units = {br}
    if len(units) == 1 and not others:
        return units.pop(), '; '.join(f'{h}: {txt}' for c, h, txt in ms)
    if units:
        # two units on the site or more: the first his entries name, the others stand in his row; one on the site and
        # another: the one on the site (the user, 2026-11-24, on Janković Radoš, "1, and count", "for both groups";
        # docs/claude/feedback-rules.md). The first by where it stands in the text, the record's own entry first
        order = []
        for i, t in enumerate(texts):
            for c, h, txt in mentions(t):
                if c in units:
                    order.append(((i, t.find(txt)), c, h, txt))
        order.sort(key=lambda x: x[0])
        first = order[0][1]
        rest = sorted({txt for _, c, _, txt in order if c != first} | {txt for _, _, txt in others})
        return first, (f'first of the units named: {order[0][3]}' + (f'; also: {", ".join(rest)}' if rest else ''))
    return None, 'names no unit on the site'


def others_named(texts: list[str], code: int) -> list[str]:
    """The units the texts name besides the one the record went to (unit_of), as printed, in the order they stand:
    they belong in his row (unit_detail), as both of Vučković's do"""
    import extract_structured_fields as esf
    texts = [esf.GLUED_RE.split(strip_heading(t or ''), maxsplit=1)[0] for t in texts]
    seen, out = set(), []
    for i, t in enumerate(texts):
        for c, h, txt in sorted(mentions(t), key=lambda m: t.find(m[2])):
            # (not the division of the brigade he went to: "4. splitske brigade 9. divizije" is one unit)
            if c != code and txt not in seen and not h.startswith(('odred, ', 'division')):
                seen.add(txt)
                out.append(txt)
    return out
