"""
The rosters and lists of the fallen at the back of the Knjižnica NOV in POS monographs (znaci.org 00003/7xx).

Two columns, a hanging indent, the names in ordinary letters (surname first):
    Seznam borcev   Adam Jože-Ciril, 1920, Sodražica
                    Adamič Bara-Beba, roj. Cemič, 1921, Maribor
    Padli           Afal Jože-Branko, Stružnica 1922—1944
"Jože-Ciril" is the given name and the partisan name he went by (written "zvani Ciril;" as in Ljubljanska).
The scans are skewed, so an entry is told from its continuation lines by the indent against the line before,
not by a fixed margin. The text layer reads Ž as 2 ("2ebovec"), š and č inside a word as S and C ("AdleSič"),
l as I after a capital ("AIojz"), and 9 as 0 in years ("1011" = 1911).
"""
import glob
import json
import re
from collections import Counter

import pdfplumber

from _parser_scaffold import _page_lines, _record
from pdf_coords import viewer_offset

U, L = 'A-ZČĆŽŠĐ', 'a-zčćžšđ'


_GIVEN: Counter = Counter()
OWN = {'file': ''}                                                           # the parser's own output, left out of the corpus


_SURNAMES: Counter = Counter()
_PLACES: Counter = Counter()


def surnames_and_places() -> tuple[Counter, Counter]:
    """How often each word is a surname, and a place (birthplaces), in the other units: "Intihar, 1922" is a
    soldier, "Brezje, Oplotnica" the second line of one."""
    if not _SURNAMES:
        for f in glob.glob('website/public/*soldiers.json'):
            if OWN['file'] and f.replace('\\', '/').endswith('/' + OWN['file']):
                continue
            for r in json.load(open(f, encoding='utf-8')):
                _SURNAMES[r.get('last_name') or ''] += 1
                for w in re.split(r',\s*', r.get('birth_place') or ''):
                    _PLACES[w] += 1
    return _SURNAMES, _PLACES


def given_names() -> Counter:
    """Every given name the other units print, with how often (to tell "Ažman Ivan" from a place, "Velika Loka",
    and to read back a misread name)."""
    if not _GIVEN:
        for f in glob.glob('website/public/*soldiers.json'):
            if OWN['file'] and f.replace('\\', '/').endswith('/' + OWN['file']):
                continue
            for r in json.load(open(f, encoding='utf-8')):
                if r.get('first_name'):
                    _GIVEN[r['first_name']] += 1
    return _GIVEN


# the first word of a place, not of a name
PLACE_WORD = re.compile(r'^(?:Sv|Vel|Mal|Zg|Sp|Gor|Dol|Nova?|Stara?|Gorenj[aei]|Dolenj[aei]|Spodnj[aei]|Zgornj[aei]|Velik[aeio]|Mal[aeio]|'
                        r'Gornj[aei]|Donj[aei]|Srednj[aei]|Trbovlje|Tolmin|Postojna|Ljubljana|Jesenice)\b')


class Indent:
    """prepare_fn and line_filter: marks each line that starts an entry with '§<kind>§ ' (kind: 's' roster, 'p'
    fallen) and drops headings and page numbers. An entry starts at the column's margin, measured near the line
    (within 60 pt above and below), so the scan's skew doesn't move it; continuation lines sit ~9 pt in."""

    def __init__(self, padli_from: int | None, headings: re.Pattern, padli_to: int | None = None,
                 comma_after_first_line: bool = False, every_line: bool = False):
        self.comma = comma_after_first_line                                  # books that print no commas: the place's line
        self.every_line = every_line                                         # a soldier a line (XII. SNOUB)
        self.padli_from = padli_from                                         # the pages of the list of the fallen
        self.padli_to = padli_to
        self.headings = headings
        self.split: dict = {}                                                # page -> where each column after the first starts
        self.cols: dict = {}

    def prepare(self, lines: list[dict]) -> None:
        keep = [ln for ln in lines if ln['text'].strip() and not re.fullmatch(r'[\d\W]{1,5}', ln['text'].strip())
                and not self.headings.match(ln['text'].strip())]
        for page in {ln['page'] for ln in keep}:                            # columns: line starts more than 40 pt apart
            xs = sorted(ln['x'] for ln in keep if ln['page'] == page)
            self.split[page] = [b for a, b in zip(xs, xs[1:]) if b - a > 40]
        for ln in keep:
            self.cols.setdefault(self.col(ln), []).append((ln['y'], ln['x']))

    def col(self, ln: dict) -> tuple:
        return ln['page'], sum(1 for b in self.split.get(ln['page'], []) if ln['x'] >= b - 1)

    def margin(self, ln: dict) -> float:
        near = sorted(x for y, x in self.cols.get(self.col(ln), []) if abs(y - ln['y']) <= 60)
        for x in near:                                                       # the leftmost x two other lines share
            if sum(1 for o in near if abs(o - x) <= 3) >= 3:
                return x
        return near[0] if near else ln['x']

    def __call__(self, ln: dict) -> bool:
        t = ln['text'].strip()
        t = re.sub(r'^1(19\d\d)$', r'† \1', t)                                  # "11946": † 1946, on a line of its own
        if re.fullmatch(r'[\d\W]{1,5}', t) or self.headings.match(t):
            return False
        kind = 'p' if (self.padli_from and ln['page'] >= self.padli_from
                       and (self.padli_to is None or ln['page'] <= self.padli_to)) else 's'
        indent = ln['x'] - self.margin(ln)
        starts = re.match(rf'^(?:[{U}]|[2šžčć][{L}])', t)                     # "žužek": a lowercase Ž
        # "Surname Given," or "Surname Given-Alias, 1920": where the scan curves or was pasted, entries drift in
        # and continuation lines out, so a line that doesn't start at the margin must read as a name
        name = rf'^[^\s,]+ (?:(?:dr|ing|arh)\. )?[{U}][{L}]+(?:-[{U}]\S*)?'
        strict = re.match(name + r'(?:[,.]| 1[89]\d\d)', t)
        bare = re.fullmatch(r'\S+ (\S+)', t)                                       # "Ažman Ivan": a name and nothing else
        two = re.match(rf'^([{U}][{L}]+)(?:-[{U}][{L}]+)? ([{U}][{L}]+)', t)            # "Hujs Friderik": a name and nothing else
        pair = bare or two
        second = pair.group(pair.lastindex) if pair else ''
        # "Gorenja Trebuša", "Sv. Ana": a place, unless the second word is a name ("Mali Anton")
        place = re.match(r'^\w{1,5}\.(?:\s|$)', t) or (re.match(PLACE_WORD, t) and given_names()[second] < 3)
        head = re.split(r',|\s(?=1[89]\d\d)', t, 1)[0].split()                      # "Brezje, Oplotnica": one word, a place
        sur, plc = surnames_and_places()
        one = len(head) == 1 and (sur[head[0]] > plc[head[0]]                 # "Intihar, 1922": a surname
                                  or (not plc[head[0]] and re.search(r'1[89]\d\d', t)))   # "Anzeljc, ..., —1944"
        dated = (',' in t or re.search(r'1[89]\d\d', t)) and (len(head) >= 2 or one) and not place
        strict = strict and not place
        loose = strict or dated or (pair and not place)
        if starts and (self.every_line or (indent < 4 and loose) or (indent < 16 and strict)):
            t = f'§{kind}§ ' + t + (',' if self.comma and not t.endswith(',') else '')
        ln['text'] = t
        return True


def fix_ocr(t: str) -> str:
    t = re.sub(rf'(?<![\w])2(?=[{L}])', 'Ž', t)                              # "2ebovec"
    t = re.sub(r'(^|,\s)([šžčć])', lambda m: m.group(1) + m.group(2).upper(), t)   # "žužek", ", črneča vas"
    t = re.sub(rf'(?<=[{L}])([ČŠŽ])', lambda m: m.group(1).lower(), t)      # "KarlovŠek"
    t = t.replace('đ', 'd')                                                  # "Lađo", "Zđenka": Slovene has no đ
    t = t.replace('\\j', 'lj').replace('^j', 'aj')                             # "Terez^a" = Terezija, "Pice\\j" = Picelj, "M^jer" = Majer
    t = re.sub(r'\^(?=[aeiou])', 'ij', t)                                     # "Terez^a" = Terezija
    t = re.sub(r'(?<=[a-zčšž])\^(?=[a-zčšž])', 'a', t).replace('^', '')         # "Mil^n" = Milan; a stray ^ goes
    t = re.sub(r'\u00ad\s*', '', t)                                          # a soft hyphen at a line break
    t = re.sub(r',?\s+1(19\d\d)\s*$', r' † \1', t)                         # "Mokronog, 11967"
    t = re.sub(r'\s+[ft]$', ' †', t)                                     # "Novo mesto f": died after the war
    t = re.sub(rf'(?<=[{L}])S(?=[{L}])', 'š', t)                             # "AdleSič"
    t = re.sub(rf'(?<=[{L}])C(?=[{L}]|\b)', 'č', t)                          # "ZemljariC"
    t = re.sub(rf'(?<=\b[{U}])I(?=[{L}])', 'l', t)                           # "AIojz"
    t = re.sub(r'\b10(\d\d)\b', r'19\1', t)                                  # "1011" = 1911
    return re.sub(r'\s+[f†]\s?(19\d\d)\b', r' † \1', t)                      # "f 1970": died after the war


# The scans' misreadings in given names: "Karei" = Karel, "Jemej" = Jernej, "Vmko" = Vinko, "Fnanc" = Franc,
# "MUko" = Milko, "Mlha" = Miha, "Süvo" = Silvo, "Jakiob" = Jakob, "Andrei" = Andrej
OCR_PAIRS = [('ei', 'el'), ('ei', 'ej'), ('m', 'rn'), ('rn', 'm'), ('m', 'in'), ('n', 'r'), ('U', 'il'), ('ü', 'il'),
             ('Ml', 'Mi'), ('l', 'i'), ('i', 'l'), ('io', 'o'), ('fe', 'e'), ('y', 'ij')]


def read_given(given: str) -> str:
    """A given name the corpus doesn't know, one misread letter away from one it knows well."""
    if not given:
        return given
    have = given_names()[given]
    best = (0, given)
    for a, b in OCR_PAIRS:
        for m in re.finditer(re.escape(a), given):
            cand = given[:m.start()] + b + given[m.end():]
            n = given_names()[cand]
            if n >= 10 and n >= 10 * have and n > best[0]:
                best = (n, cand)
    return best[1]


def name_part(head: str) -> tuple[str, str, list[str]]:
    """'Ahčin dr. Marjan-Marjan' -> ('Ahčin', 'Marjan', ['dr.', 'zvani Marjan'])."""
    notes = []
    for m in list(re.finditer(r'\(?\b((?:roj|por|ud)\.)\s*([^\s,()]+)\)?', head)):   # "Justina roj. Kavšek", "(por. Zgavec)"
        notes.append(f'{m.group(1)} {m.group(2)}')
    head = re.sub(r'\(?\b(?:roj|por|ud)\.\s*[^\s,()]+\)?', ' ', head)
    m = re.search(r'\s[rR]\.(?:\s*)([A-ZČŠŽ][a-zčšž]+)', head)                       # "Fidel r. Maslo Kristina"
    if m:
        notes.append('roj. ' + m.group(1))
        head = head[:m.start()] + head[m.end():]
    if '†' in head:                                                         # "Butara Ema†"
        notes.append('†')
    head = re.sub(r'(?<=[a-zčšž])—(?=[A-ZČŠŽ])', '-', head.replace('†', ' '))   # "Jože—Mito"
    head = re.sub(r"[\d'’]+", ' ', head.replace('ä', 'a').replace('ö', 'o'))   # "Grdad'olnik"; "Markovič 1942"
    toks = head.replace('.', '. ').split()
    out = []
    for w in toks:                                                           # "Zara n Ludvik": a letter cut off the word
        if out and re.fullmatch(rf'[{L}]{{1,3}}', w) and w not in ('pri', 'na', 'v') and not out[-1].endswith('.'):
            out[-1] += w
        else:
            out.append(w)
    if len(out) > 2 and out[1][:1].islower() and out[1] not in ('pri', 'na', 'v') and not out[1].endswith('.'):
        out[:2] = [out[0] + out[1]]                                          # "No vina Rado"
    other = [w.strip('()') for w in out[1:2] if w.startswith('(') and w.endswith(')')]
    out = [w for w in out if w.strip('()') not in other]                     # "Čok (Cioch) Anton"
    nick = [w.strip('()') for w in out[2:] if w.startswith('(') and w.endswith(')')]
    out = [w for w in out if w.strip('()') not in nick]                      # "Bavčar Emil (Rajko)"
    pre = [w for w in out if w in ('dr.', 'ing.', 'mr.', 'arh.', 'ml.', 'st.')]                # "Ivan ml.": the younger
    out = [w for w in out if w not in pre]
    if len(out) > 2 and out[0] in ('De', 'Del', 'Della', 'D.', 'Di', 'Da', 'Van', 'Von'):    # "De Gleria Mitja"
        out[:2] = [out[0] + ' ' + out[1]]
    last = out[0] if out else ''
    rest = ' '.join(out[1:])
    given, _, alias = rest.partition('-')
    parts = given.split()
    if len(parts) > 1 and any(len(w) <= 2 or w[0].islower() for w in parts[1:]):
        given = ''.join(parts)                                               # "Pa vel", "J anko": one name spaced apart
    given = read_given(given.strip())
    alias = re.sub(r'\s+(?=[{L}])'.replace('{L}', L), '', alias.strip())     # "Dra vin" = Dravin
    notes = pre + ['ili ' + o for o in other] + (['zvani ' + alias] if alias else []) + ['zvani ' + n for n in nick] + notes
    return last, given, notes


def parse_roster(text: str) -> dict:
    """'Adamič Bara-Beba, roj. Cemič, 1921, Maribor'"""
    text = fix_ocr(re.sub(r'^§s§\s*', '', text))
    m = re.search(r',|\s(?=1[89]\d\d)|(?<![ (]ing)(?<![ (]arh)(?<![ (]roj)(?<![ (]por)(?<=[a-zčšž]{3})\.\s(?=[A-ZČŠŽ])', text)   # "Berkopec Janez. Maribor"
    head, rest = (text[:m.start()], text[m.end():].strip()) if m else (text, '')
    last, given, notes = name_part(head if re.search(r'\b(?:ml|st)\.$', head) else head.rstrip('.'))
    born = re.match(r'^((?:roj|por)\.\s*[^,]+),\s*', rest)                   # maiden or married name
    if born:
        notes.append(born.group(1))
        rest = rest[born.end():]
    rest = re.sub(r'^(1[89]\d\d)\.?\s', r'\1, ', rest)
    rec = _record(last, given, '', '; '.join(notes + ([rest] if rest else [])))
    by = re.match(r'^(1[89]\d\d)\b', rest)
    if by:
        rec['birth_year'] = by.group(1)
    return rec


def parse_fallen(text: str) -> dict:
    """'Afal Jože-Branko, Stružnica 1922—1944': the place, the years of birth and death."""
    text = fix_ocr(re.sub(r'^§p§\s*', '', text))
    head, _, rest = text.partition(',')
    if not rest:                                                             # "Cad Justin —1944": no comma
        m = re.search(r'\s(?=(?:1[89]\d\d)?\s*[—–-]+\s*19\d\d)', text)
        if m:
            head, rest = text[:m.start()], text[m.end():]
    last, given, notes = name_part(head)
    rest = rest.strip()
    rec = _record(last, given, '', '; '.join(notes + ([rest] if rest else [])))
    yrs = re.search(r'(1[89]\d\d)?\s*[—–-]+\s*(19\d\d)\s*$', rest)
    place = re.sub(r'(?<=\w{4})\.$', '', rest[:yrs.start()].strip(' ,')) if yrs else ''   # "Velike Češnjice."; "na Dol." keeps its stop
    if yrs and yrs.group(1):
        rec['birth_year'] = yrs.group(1)
    rec['death_type'] = 'poginuo'
    if yrs:
        rec['death_date'] = yrs.group(2)
    if place and not re.search(r'\d', place):
        rec['birth_place'] = place
    return rec


def parse(text: str) -> dict:
    return parse_fallen(text) if text.startswith('§p§') else parse_roster(text)


def gutters(page, offset: tuple[float, float], ncols: int) -> list[float]:
    """The ncols - 1 x positions (viewer space) that the fewest words cross, one near each k/ncols of the page."""
    dx = offset[0]
    words = page.extract_words(keep_blank_chars=False)
    width = float(page.width)
    out = []
    xs0 = [w['x0'] - dx for w in words]
    lo, hi = (min(xs0), max(w['x1'] - dx for w in words)) if words else (0, width)
    for k in range(1, ncols):
        centre = lo + (hi - lo) * k / ncols                                  # between the text's own edges
        xs = range(int(centre - (hi - lo) / (2 * ncols)), int(centre + (hi - lo) / (2 * ncols)))
        cover = [sum(1 for w in words if w['x0'] - dx - 1 <= x <= w['x1'] - dx + 1) for x in xs]
        low = min(cover)
        runs, start = [], None                                               # the widest run of the least-crossed x
        for i, c in enumerate(cover + [low + 1]):
            if c == low and start is None:
                start = i
            elif c != low and start is not None:
                runs.append((i - start, start, i - 1))
                start = None
        _, a, b = max(runs)
        out.append(float(xs[(a + b) // 2]))
    return out


def columns_reader(ncols: int):
    """extract_fn for books in ncols columns: each page's lines, column by column."""
    def extract(pdf_path: str, start_page: int, end_page: int | None) -> list[dict]:
        lines: list[dict] = []
        with pdfplumber.open(pdf_path) as pdf:
            stop = min(end_page, len(pdf.pages)) if end_page else len(pdf.pages)
            for n in range(start_page - 1, stop):
                page = pdf.pages[n]
                offset = viewer_offset(page)
                dx = offset[0]
                cuts = [-1e9] + gutters(page, offset, ncols) + [1e9]
                for a, b in zip(cuts, cuts[1:]):
                    part = page.filter(lambda o, a=a, b=b: o.get('object_type') != 'char' or a <= o['x0'] - dx < b)
                    lines.extend(_page_lines(part, n + 1, offset))
        return lines
    return extract


def _inversions(keys: list[str]) -> int:
    return sum(1 for i, a in enumerate(keys) for b in keys[i + 1:] if b < a)


def caron_block(run: list[dict]) -> int:
    """Where the Č (Š, Ž) names start among a list's C and Č names, in printed order: the split that leaves
    both parts closest to alphabetical order (the books slip here and there: "Sršen", "Sprajcer"). len(run)
    when the names read as one alphabetical run."""
    keys = [s['last_name'][1:].lower() + ' ' + s['first_name'].lower() for s in run]
    whole = _inversions(keys)
    best, at = whole, len(run)
    for k in range(1, len(run)):
        cost = _inversions(keys[:k]) + _inversions(keys[k:])
        if cost < best:
            best, at = cost, k
    return at if best * 3 < whole else len(run)                              # a clear second run, not noise


def restore_carons(soldiers: list[dict], list_of) -> list[dict]:
    """Scans that drop the caron of a surname's capital ("Cerne" = Černe, "Saruga" = Šaruga): the lists run in the
    Slovene alphabet (C, Č, ... S, Š, ... Z, Ž), so in each list (list_of(s), in printed order) the C, S and Z
    names printed after the list has moved on to Č, Š or Ž take the caron back ("Cvetko", then "Cakarevič"). A
    given name the corpus doesn't know as printed, but well with a caron, too."""
    n = 0
    for which in sorted({list_of(s) for s in soldiers}):
        listed = [s for s in soldiers if list_of(s) == which]
        for plain, caron in (('C', 'Č'), ('S', 'Š'), ('Z', 'Ž')):
            run = [s for s in listed if s['last_name'][:1] in (plain, caron)]
            for s in run[caron_block(run):]:
                if s['last_name'][:1] == plain:
                    s['last_name'] = caron + s['last_name'][1:]
                    n += 1
    for s in soldiers:
        g = s['first_name']
        caron = {'C': 'Č', 'S': 'Š', 'Z': 'Ž'}.get(g[:1])
        if caron and not given_names()[g] and given_names()[caron + g[1:]] >= 10:
            s['first_name'] = caron + g[1:]
            n += 1
        s['full_name'] = ' '.join(p for p in (s['last_name'], s['first_name']) if p)
    print(f'  carons restored in {n} names')
    return soldiers
