"""
Parser: Viktor Kučan, *Borci Sutjeske* — "Prozivka boraca sa Sutjeske", every fighter of the units in the battle.

Source: znaci.org 00001/129, one PDF per brigade (129_10 … 129_25)  →  website/public/pdfs/borci-sutjeske-<unit>.pdf
Two columns, Latin, a clean text layer (the book was typeset in 1980). Each chapter opens with the brigade's name and
a paragraph of figures (how many fought, fell, their trades and nations), then the roll in alphabetical order:

    AKSAMIJA Jakuba ADEM, referent saniteta brigade, rođen 1920, Rogatica, student, Musliman, u NOB od 1941, član
    KPJ, krajem rata politički komesar 16. muslimanske brigade.
    ANĐELIĆ Vaje SAVO ČARUGA desetar u 4. bataljonu, rođen 1919, Bjeloševac, Bijeljina, ... poginuo na brdu Kumić ...
    BARARON SUMBUL, borac, rođen u Bosanskoj Krupi, radnik, Jugosloven, u NOB od 1942, poginuo na Sutjesci juna 1943.

SURNAME, the father in the genitive (title case; missing for some), the GIVEN name, nicknames in capitals after it
("ČARUGA", "CRNI", "BIRČAK" → "zvani Čaruga"). A name broken over two lines ("ALEKSAN-" / "DAR AGO") is joined back,
and its second line does not start an entry. Running heads ("Prva majevička brigada 1143", "Viktor Kučan - Borci
Sutjeske") sit above a gap at the top of each page.

For units already on the site this is a second book (IDs from 100001; `merge` corrections join the soldiers both
books print); for the others it is the unit's first.

    python data-extraction/parse_borci_sutjeske.py 49          # one unit by code
    python data-extraction/parse_borci_sutjeske.py new         # the ten units the book brings to the site
"""
import glob
import json
import re
import sys
from collections import Counter, defaultdict

from _parser_scaffold import _record, repair_lj_ocr, restore_diacritics, run_parser
from scripts.name_utils import genitive_to_nominative

U, L = 'A-ZČĆŽŠĐ', 'a-zčćžšđ'

# code: (znaci.org chapter, PDF on the site, the unit's data file, first ID)
UNITS = {
    1: ('129_10', 'borci-sutjeske-prva-proleterska.pdf', 'prva-proleterska-soldiers.json', 100001),
    39: ('129_11', 'borci-sutjeske-druga-proleterska.pdf', 'druga-proleterska-soldiers.json', 100001),
    5: ('129_12', 'borci-sutjeske-treca-proleterska.pdf', 'treca-proleterska-soldiers.json', 100001),
    40: ('129_13', 'borci-sutjeske-4-proleterska.pdf', '4-proleterska-soldiers.json', 1),
    41: ('129_14', 'borci-sutjeske-5-proleterska.pdf', '5-proleterska-soldiers.json', 1),
    42: ('129_15', 'borci-sutjeske-6-istocnobosanska.pdf', '6-istocnobosanska-soldiers.json', 1),
    43: ('129_16', 'borci-sutjeske-10-hercegovacka.pdf', '10-hercegovacka-soldiers.json', 1),
    10: ('129_17', 'borci-sutjeske-3-krajiska.pdf', '3-krajiska-proleterska-soldiers.json', 100001),
    44: ('129_18', 'borci-sutjeske-7-banijska.pdf', '7-banijska-soldiers.json', 1),
    36: ('129_19', 'borci-sutjeske-1-dalmatinska.pdf', '1-dalmatinska-soldiers.json', 100001),
    45: ('129_20', 'borci-sutjeske-8-banijska.pdf', '8-banijska-soldiers.json', 1),
    7: ('129_21', 'borci-sutjeske-2-dalmatinska.pdf', '2-dalmatinska-soldiers.json', 100001),
    46: ('129_22', 'borci-sutjeske-3-dalmatinska.pdf', '3-dalmatinska-soldiers.json', 1),
    47: ('129_23', 'borci-sutjeske-16-banijska.pdf', '16-banijska-soldiers.json', 1),
    48: ('129_24', 'borci-sutjeske-7-krajiska.pdf', '7-krajiska-soldiers.json', 1),
    49: ('129_25', 'borci-sutjeske-15-majevicka.pdf', '15-majevicka-soldiers.json', 1),
}
NEW = [40, 41, 42, 43, 44, 45, 46, 47, 48, 49]
# pages the scan repeats (the same printed page again, rescanned): the second copy is skipped
SKIP_PAGES = {
    'borci-sutjeske-4-proleterska.pdf': {36, 37},            # = pp. 34-35 (book pp. 396-397)
    'borci-sutjeske-3-dalmatinska.pdf': {22, 23, 62, 63},    # = pp. 20-21 and 60-61
}

SOFT = '­'      # a name broken over two lines: "ALEKSAN-" + "DAR" → "ALEKSANDAR"
HOLD = 'ǂ'           # marks the second line of a broken name so that it starts no entry (a letter: the scaffold
                     # strips leading punctuation)

# The scan's capitals: accented ones ("JÒCO", "DÄNE") and digits for letters ("SAV1Ć", "T1HOMIR", "13ANIJEL")
UA = U + 'ÀÁÂÄÈÉÊËÌÍÎÏÒÓÔÖÙÚÛÜ'
LA = L + 'àáâäèéêëìíîïòóôöùúûü'
EDGE = 'Ø'          # a surname whose first letter the scan garbled at the column's edge ("3UDIĆ", "4ARJANOVIĆ",
                    # "•SLIJEPČEVIĆ"): the letter is read back from the alphabetical order (post)
CAPW0 = rf"[{UA}0][{UA}'013]+"
CAPW = rf"[{UA}][{UA}'013]*"
SURNAME = rf"{EDGE}?{CAPW0}(?:\s+{CAPW})*?(?:\s*-\s*{CAPW}(?:\s+{CAPW})*?)?"
# the father: "Jakuba", "Jeli seja" / "Ahmed a" (a word the scan split), "T.", "C.vije" / "(Vije" (Cvije), "lome" (Tome,
# Ibre, Lazara: a capital read as l), "Ha-" at the end of the line; "ing." / "dr" before him
FATHER = (rf"(?:(?:ing\.|dr\.?)\s+)?(?:\(?[{U}]\.?[{LA}]+(?:\s+[{LA}]{{1,5}}(?=\s+[{UA}013]))?|[{U}][{LA}]?\."
          rf"|l[{LA}]{{2,}}(?=\s+[{UA}013]{{2}})|[{U}][{LA}]+-$)")
ABBREV = (r'(?!(?:AFŽ|NOB|MOB|NOR|NOV|KPJ|KIM|KPH|SKOJ|JNA|OZN|OZNA|AVNOJ|ZAVNOBiH|SSSR|NOO|POJ|SUBNOR|UDB|UDBA|SFRJ|FNRJ'
          r'|CK|OK|SK|KK|MK|NDH)\b)')
# SURNAME [Father] GIVEN, or SURNAME Father at the end of a line (the given name is on the next)
START = re.compile(rf"^{ABBREV}{SURNAME}(?:\s+{FATHER}(?:\s+{FATHER})?(?:\s+[{UA}013](?:[{UA}'013]|\s|$)|\s*$)"
                   rf"|\s+[{UA}013][{UA}'013]+)")
CAPS = re.compile(rf"^{EDGE}?[{UA}013][{UA}'013\-.]*$")
# junk at the column's edge in place of (or before) the first letter: "3UDIĆ", "30SANĆIĆ", ")AKOVIĆ", "X)IDOŠ", "\NJIĆ"
EDGE_JUNK = re.compile(rf"^(?:[A-Z]?[^\w\s(]{{1,2}}|\d{{1,2}}|[ìÌü]){{1,2}}\s?(?=[{UA}0])")
FIX_CAPS = str.maketrans('ÀÁÂÄÈÉÊËÌÍÎÏÒÓÔÖÙÚÛÜàáâäèéêëìíîïòóôöùúûü', 'AAAAEEEEIIIIOOOOUUUUaaaaeeeeiiiioooouuuu')
# what the scan makes of the end of a surname split off with a space: "DANILO VIĆ", "STEVAN OVIĆ", "MIĆANO VI Ć"
SUFFIX = re.compile(r'^(?:[A-ZČĆŽŠĐ]{0,4}(?:IĆ|IC)|VI|OVI|EVI|Ć|ĆE|ĆI|OV|EV)$')
TITLES = ('ing.', 'dr', 'dr.')


def prepare(lines: list[dict]) -> None:
    """Drop each page's running head and page 1's title and figures; mark broken names."""
    by_page = defaultdict(list)
    for ln in lines:
        by_page[ln['page']].append(ln)
    for page, pl in by_page.items():
        ys = sorted(ln['y'] for ln in pl)
        if page == 1:
            # everything above the first entry: the brigade's name and the paragraph of figures
            starts = [ln['y'] for ln in pl if START.match(ln['text']) and re.search(rf'[,{L}]', ln['text'])]
            cut = min(starts) - 1 if starts else -1
        else:
            # a running head: lines in the top 12 pt above a gap of 14 pt or more
            top = [y for y in ys if y <= ys[0] + 12]
            rest = [y for y in ys if y > top[-1]]
            cut = top[-1] if rest and rest[0] - top[-1] >= 14 else -1
        for ln in pl:
            if ln['y'] <= cut:
                ln['drop'] = True
    name_open = False
    for ln in lines:
        if ln.get('drop'):
            continue
        t = re.sub(rf"(?<=[{LA}])'(?=[{U}])", ' ', ln['text'].strip())      # "Adama'MIRKO"
        t = re.sub(rf"^(\W*\d)0(?=[{U}])", r'\1O', t)                         # "30SNIĆ": the 0 is an O
        jm = EDGE_JUNK.match(t)
        if jm and not START.match(t) and START.match(EDGE + re.sub('^0', 'O', t[jm.end():])):
            t = EDGE + re.sub('^0', 'O', t[jm.end():])
        if name_open and START.match(t):
            t = HOLD + t                                        # "DAR AGO, zamenik ..." continues "ALEKSAN-"
        elif START.match(t):
            name_open = True
        if name_open:
            _, rest, comma = split_name(t.replace(HOLD, ''))
            if comma or rest:                                    # the name ends at a comma or a lowercase word
                name_open = False
            elif re.search(rf'[{UA}{LA}]-$', t):
                t = t[:-1] + SOFT                                # the name runs on to the next line
        ln['text'] = t


def keep(ln: dict) -> bool:
    return not ln.get('drop') and ln['page'] not in SKIP_PAGES.get(ln['file'], ())


def is_father_word(t: str) -> bool:
    return bool(re.match(rf'^\(?[{U}]\.?[{LA}]', t) or re.match(rf'^[{U}][{LA}]?\.$', t))


def l_father(toks: list[str], i: int) -> bool:
    """'lome', 'lazara', 'lbre': a father whose capital the scan read as l, between the surname and the given name"""
    return (toks[i].startswith('l') and len(toks[i]) > 2 and all(CAPS.match(t) for t in toks[:i])
            and i + 1 < len(toks) and bool(CAPS.match(toks[i + 1])))


def split_name(text: str) -> tuple[list[str], str, bool]:
    """The name's words, the bio after them, and whether a comma ended the name. The name ends at the first
    comma, or at a lowercase word once the given name has begun ("ANĐELIĆ Vaje SAVO ČARUGA desetar u ...");
    a short lowercase word right after the father is the scan's split of his name ("Jeli seja")."""
    head, comma, tail = text.partition(',')
    toks = head.split()
    for i, t in enumerate(toks):
        if i == 0 or not re.match(rf'^[{LA}]', t) or t in TITLES:
            continue
        father_split = is_father_word(toks[i - 1]) and len(t) <= 5 and i + 1 < len(toks) and CAPS.match(toks[i + 1])
        if not father_split and not l_father(toks, i):
            return toks[:i], ' '.join(toks[i:]) + comma + tail, False
    return toks, tail, bool(comma)


_first: Counter = Counter()


def name_counts() -> None:
    for f in glob.glob('website/public/*soldiers.json'):
        for s in json.load(open(f, encoding='utf-8')):
            _first[s['first_name'].upper()] += 1


def fix_caps(t: str) -> str:
    t = re.sub(r'^13', 'D', t.translate(FIX_CAPS))               # "13ANIJEL"
    return t.replace('1', 'I').replace('3', 'E').replace('0', 'O')


def parse_entry(text: str) -> dict:
    text = text.replace(SOFT + ' ', '').replace(SOFT, '').replace(HOLD, '')
    toks, bio, _ = split_name(text)
    toks = [t.strip(',') for t in toks if t.strip(',')]
    fat = [i for i, t in enumerate(toks)
           if i > 0 and (is_father_word(t) or t in TITLES or l_father(toks, i)
                         or (re.match(rf'^[{LA}]', t) and is_father_word(toks[i - 1])))]
    title = [t for t in toks if t in TITLES]
    if fat:
        # everything before the father is the surname, however the scan split it: "DANILO VIĆ", "MIĆANO VI Ć-VUKO VIĆ"
        last = ''.join(fix_caps(t) for t in toks[:fat[0]])
        fwords = [toks[i] for i in fat if toks[i] not in TITLES]
        father = ''.join(fwords) if len(fwords) > 1 and fwords[1][0].islower() else ' '.join(fwords)
        caps = [fix_caps(t) for t in toks[fat[-1] + 1:]]
    else:
        caps = [fix_caps(t) for t in toks]
        last = caps.pop(0) if caps else ''
        while caps and SUFFIX.match(caps[0].strip('-')):
            last += caps.pop(0)
        father = ''
    father = father.translate(FIX_CAPS).replace('.', '')
    father = {'Pavia': 'Pavla', 'Pavie': 'Pavle'}.get(father, father)      # the scan reads "vl" as "vi"
    father = re.sub(r'^\((\w)', lambda m: 'C' + m.group(1).lower(), father)       # "(Vije" = Cvije
    if father.startswith('l'):                                          # "lome", "lazara", "lbre"
        father = max((c + father[1:] for c in 'ITL'), key=lambda f: _ref['middle_name'][f])
    if father and not (_first[father.upper()[:-1]] or _first[father.upper()]):
        alt = father.replace('rn', 'm')                          # "Ornera" = Omera
        if alt != father and (_first[alt.upper()[:-1]] or _first[alt.upper()]):
            father = alt
    # a given name the scan split ("Z AH ARIJE", "STA NIS A"): join while the part is no name and the whole is,
    # or a part is a lone letter
    given = caps.pop(0) if caps else ''
    while caps and _first[given] < 3:
        joined = given + caps[0]
        if _first[joined] >= 3 or len(caps[0]) == 1 or len(given) == 1:
            given = joined
            caps.pop(0)
        else:
            break
    nick = []
    for n in (n for n in caps if n.strip('-')):
        if nick and len(n) <= 2:
            nick[-1] += n                                        # "STANIS A", "VO JE": a piece the scan split off
        else:
            nick.append(n)
    bio = re.sub(r'\brod[e]n(a?)\b', r'rođen\1', bio.strip(' ,'))   # the scan's "roden"
    notes = []
    if title:
        notes.append(' '.join(title))
    if nick:
        notes.append('zvani ' + ' '.join(n.capitalize() for n in nick))
    info = '; '.join(notes + ([bio] if bio else []))
    return _record(last, given, father, info)


# The scan's misreads in names: t as l ("Pelar", "Rislo", "Slevan"), lj as li/lt ("Liubiša", "Ltubomir"), j as i or
# a dot ("Radivoie", "Vo.io", "Ign.tat"), v as y ("Borislay"), m as rn, Đ as D ("Dorđo"), ć as c
SWAPS = [('l', 't'), ('li', 'lj'), ('lt', 'lj'), ('Li', 'Lj'), ('Lt', 'Lj'), ('i', 'j'), ('.i', 'j'), ('.t', 'j'),
         ('.', 'j'), ('y', 'v'), ('rn', 'm'), ('D', 'Đ'), ('c', 'ć'), ('ie', 'je'), ('ui', 'uj'), ('Jl', 'T'), ('n', 'u'),
         ('u', 'n'), ('h', 'b'), ('e', 'c')]
RISKY = {('l', 't'), ('rn', 'm'), ('h', 'b'), ('e', 'c'), ('n', 'u'), ('u', 'n')}
_ref: dict[str, Counter] = {}
_dalmatian: Counter = Counter()
DALMATIAN = {7, 36, 46}
CURRENT = [0]
REPAIRS: list[tuple[str, str]] = []
EDGES: list[tuple[str, str, str, str]] = []


def name_reference() -> None:
    for f in ('2-dalmatinska-soldiers.json', '4-splitska-soldiers.json'):
        for r in json.load(open(f'website/public/{f}', encoding='utf-8')):
            _dalmatian[r['first_name']] += 1
    for field in ('first_name', 'last_name', 'middle_name'):
        _ref[field] = Counter()
    for f in glob.glob('website/public/*soldiers.json'):
        if any(f.replace('\\', '/').endswith(u[2]) for c, u in UNITS.items() if c in NEW):
            continue                                              # not this book's own earlier output
        for s in json.load(open(f, encoding='utf-8')):
            for field, counts in _ref.items():
                if s.get(field):
                    counts[s[field]] += 1


def repair_name(v: str, field: str) -> str:
    """A name unknown in every unit takes the spelling one or two of the scan's misreads give, if that is well known."""
    counts = _ref[field]
    v = v.strip(';:,')
    if not v or counts[v]:
        return v
    best = (0, v)
    frontier = {(v, False)}
    for depth in (1, 2):
        nxt = set()
        for w, risky in frontier:
            for a, b in SWAPS:
                for m in re.finditer(re.escape(a), w):
                    if a == 'D' and m.start() != 0 or a == 'c' and m.end() != len(w):
                        continue
                    cand = w[:m.start()] + b + w[m.end():]
                    # a swap that turns one real name into another (Ćalović/Ćatović, Bajlo/Bajto) needs a much
                    # better known result in a surname; "Vnjatović" (no name starts so) is no real name
                    r = risky or ((a, b) in RISKY and not (a == 'n' and re.match(r'^[^aeiouAEIOU]n[^aeiou]', w)))
                    nxt.add((cand, r))
                    need = (10 if r else 2) if field == 'last_name' else 3
                    if counts[cand] >= need and counts[cand] > best[0]:
                        best = (counts[cand], cand)
        if best[0]:
            break
        frontier = nxt
    return best[1]


ALPHABET = ['A', 'B', 'C', 'Č', 'Ć', 'D', 'Dž', 'Đ', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'Lj', 'M', 'N', 'Nj', 'O',
            'P', 'R', 'S', 'Š', 'T', 'U', 'V', 'Z', 'Ž']


def collate(name: str) -> list[int]:
    """Sort key in the order of the Serbo-Croatian Latin alphabet (Č after C, Lj after L, Dž after D)."""
    key, s, i = [], name.upper(), 0
    letters = [x.upper() for x in ALPHABET]
    while i < len(s):
        two = s[i:i + 2]
        if two in ('DŽ', 'LJ', 'NJ'):
            key.append(letters.index(two))
            i += 2
        else:
            key.append(letters.index(s[i]) if s[i] in letters else 99)
            i += 1
    return key


def first_letter(name: str) -> str:
    return ALPHABET[collate(name)[0]] if name and collate(name)[0] < len(ALPHABET) else ''


def edge_letters(soldiers: list[dict]) -> None:
    """The left edge of the scan garbles a surname's first letter: into junk ("Øudić" from "3UDIĆ") or into another
    letter ("Iulat", "Iartinović", "Otkozarac"). Between two surnames the other units know (document order is
    alphabetical), the letter is read back:
    - after junk, the candidate that fits the order and the other units know best; junk before a whole surname
      ("•SLIJEPČEVIĆ") is just dropped; with no known candidate, the letter of the section both neighbours are in;
    - a surname no unit knows, whose first letter is not its section's, takes the section's letter when that gives a
      surname the other units know (Iulat → Bulat)."""
    known = lambda n: _ref['last_name'][n] >= 2                   # one occurrence may be another book's misread
    trusted = [i for i, s in enumerate(soldiers) if not s['last_name'].startswith(EDGE) and known(s['last_name'])]
    for i, s in enumerate(soldiers):
        name = s['last_name']
        if not name.startswith(EDGE) and known(name):
            continue
        prev = next((soldiers[j]['last_name'] for j in reversed(trusted) if j < i), '')
        nxt = next((soldiers[j]['last_name'] for j in trusted if j > i), '')
        sec = first_letter(prev) if prev and first_letter(prev) == first_letter(nxt) else ''
        fits = lambda c: (not prev or collate(prev) <= collate(c)) and (not nxt or collate(c) <= collate(nxt))
        if name.startswith(EDGE):
            rest = name[1:]
            cands = [rest[:1].upper() + rest[1:]] + [x + rest for x in ALPHABET]
            good = [c for c in cands if fits(c) and known(c)]
            # neighbours out of order (a column read out of turn): a known spelling in either neighbour's section
            near = [c for c in cands if known(c) and first_letter(c) in (first_letter(prev), first_letter(nxt))]
            if good or near:
                best = max(good or near, key=lambda c: (_ref['last_name'][c], c == cands[0]))
            elif sec and not cands[0].startswith(sec):
                best = sec + rest
            else:
                best = cands[0]
        else:
            if not sec or name.startswith(sec):
                continue
            tail = name[2:] if name[:2] in ('Lj', 'Nj', 'Dž') else name[1:]
            cand = sec + tail
            if not (known(cand) and fits(cand)):
                continue
            best = cand
        EDGES.append((prev, name, best, nxt))
        s['last_name'] = best


def nominative(g: str) -> str:
    """The father's name in the nominative: of the forms the genitive can come from (Pere: Pero, Pera, Pere; Milenka:
    Milenko, Milenka, Milenak; Mitra: Mitar), the one most common as a soldier's given name in the other units."""
    if not g or ' ' in g or g.endswith('.'):
        return g
    cands = {g, genitive_to_nominative(g)}
    if g.endswith('a'):
        stem = g[:-1]
        cands |= {stem, stem + 'o', stem + 'a', stem + 'e'}           # Vasilija → Vasilije
        if len(stem) > 2 and stem[-1] in 'rlnk' and stem[-2] not in 'aeiou':
            cands.add(stem[:-1] + 'a' + stem[-1])                      # Mitra → Mitar, Petra → Petar
    elif g.endswith('e'):
        stem = g[:-1]
        cands |= {stem + 'o', stem + 'a'}
    # Dalmatian fathers by the Dalmatian books: Mate, Ante, Šime stay as printed (the corpus at large says Mato)
    counts = _dalmatian if CURRENT[0] in DALMATIAN and any(_dalmatian[c] for c in cands) else _ref['first_name']
    best = max(cands, key=lambda c: (counts[c], c == g))
    return best if counts[best] else g


def post(soldiers: list[dict]) -> list[dict]:
    edge_letters(soldiers)
    soldiers = repair_lj_ocr(restore_diacritics(soldiers))
    for s in soldiers:
        for field in ('first_name', 'last_name', 'middle_name'):
            new = repair_name(s[field], field)
            # specks the scan left in a name: "Dušan'", "Nikola^", "Krst'o", "S'vorcan", "Pe.tka"
            clean = re.sub(r'\s*-\s*', '-', re.sub(r"[^\w\s-]|[\d_" + EDGE + r"]", '', new)).strip(' -')
            if clean != new:
                new = repair_name(clean, field)
            if new != s[field]:
                REPAIRS.append((s[field], new))
            s[field] = new
        s['fathers_name'] = nominative(s['middle_name'])
        s['full_name'] = ' '.join(p for p in (s['last_name'], s['middle_name'], s['first_name']) if p)
    return soldiers


def run(code: int) -> None:
    CURRENT[0] = code
    chapter, pdf, json_file, id_start = UNITS[code]
    run_parser(
        pdf_path=f'website/public/pdfs/{pdf}',
        brigade_code=code,
        output_path=f'website/public/{json_file}',
        layout='two_column',
        col_split_x='auto',
        entry_start_re=START,
        parse_entry_fn=parse_entry,
        prepare_fn=prepare,
        line_filter=keep,
        post_fn=post,
        id_start=id_start,
        keep_other_sources=id_start > 1,
    )


if __name__ == '__main__':
    args = sys.argv[1:] or ['new']
    codes = NEW if args == ['new'] else [int(a) for a in args]
    name_counts()
    name_reference()
    for c in codes:
        run(c)
        print(f'  names repaired: {len(REPAIRS)}', ', '.join(f'{a}→{b}' for a, b in REPAIRS[:400]))
        REPAIRS.clear()
        print(f'  first letters read back: {len(EDGES)}', '; '.join(f'{p} < {e}→{b} < {n}' for p, e, b, n in EDGES))
        EDGES.clear()
