"""
Shared scaffolding for new brigade parsers.

Provides:
- PDF text extraction (single-column and two-column with x-coordinate splitting)
- Cyrillic → Latin transliteration helper (Serbian srpska/vojvodjanska/šumadijska brigades)
- Common entry-parsing primitives (year extraction, comma-split, father-in-parens)
- Consistent JSON output shape matching the existing website Soldier interface

New parser files (parse_<brigade>.py) call:
  soldiers = run_parser(
      pdf_path=...,
      brigade_code=...,
      output_path=...,
      start_page=..., end_page=...,
      layout='single' | 'two_column' | 'table',
      col_split_x=...,           # only for two_column
      script='latin' | 'cyrillic',
      entry_regex=...,           # optional custom entry-start pattern
      parse_entry_fn=...,        # optional custom per-entry parser
  )

Each new brigade will need format-specific tuning; this scaffold provides the
90% common infrastructure so brigade-specific stubs stay short.
"""

from __future__ import annotations

import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Callable, Iterable

import pdfplumber

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))

from pdf_coords import viewer_offset  # noqa: E402
from scripts.name_utils import extract_birth_info  # noqa: E402
from scripts.soldier_id_utils import assign_ids_to_soldiers  # noqa: E402


# ─────────────────────────────────────────────
# Cyrillic → Latin (Serbian)
# ─────────────────────────────────────────────

_CYR_TO_LAT = str.maketrans({
    'А': 'A', 'Б': 'B', 'В': 'V', 'Г': 'G', 'Д': 'D', 'Ђ': 'Đ', 'Е': 'E',
    'Ж': 'Ž', 'З': 'Z', 'И': 'I', 'Ј': 'J', 'К': 'K', 'Л': 'L', 'Љ': 'Lj',
    'М': 'M', 'Н': 'N', 'Њ': 'Nj', 'О': 'O', 'П': 'P', 'Р': 'R', 'С': 'S',
    'Т': 'T', 'Ћ': 'Ć', 'У': 'U', 'Ф': 'F', 'Х': 'H', 'Ц': 'C', 'Ч': 'Č',
    'Џ': 'Dž', 'Ш': 'Š',
    'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'ђ': 'đ', 'е': 'e',
    'ж': 'ž', 'з': 'z', 'и': 'i', 'ј': 'j', 'к': 'k', 'л': 'l', 'љ': 'lj',
    'м': 'm', 'н': 'n', 'њ': 'nj', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's',
    'т': 't', 'ћ': 'ć', 'у': 'u', 'ф': 'f', 'х': 'h', 'ц': 'c', 'ч': 'č',
    'џ': 'dž', 'ш': 'š',
})


_CYR_UPPER = 'А-ЯЂЈЉЊЋЏ'
# In ALL-CAPS words the digraphs must stay all-caps: ЉУБИЋ → LJUBIĆ, not LjUBIĆ
_CAPS_DIGRAPH_RE = re.compile(rf'([ЉЊЏ])(?=[{_CYR_UPPER}])|(?<=[{_CYR_UPPER}])([ЉЊЏ])')
_CAPS_DIGRAPHS = {'Љ': 'LJ', 'Њ': 'NJ', 'Џ': 'DŽ'}


def cyrillic_to_latin(text: str) -> str:
    text = _CAPS_DIGRAPH_RE.sub(lambda m: _CAPS_DIGRAPHS[m.group(1) or m.group(2)], text)
    return text.translate(_CYR_TO_LAT)


# ─────────────────────────────────────────────
# PDF text extraction
# ─────────────────────────────────────────────

def _page_lines(page, page_num: int, offset: tuple[float, float]) -> list[dict]:
    # extract_text_lines clusters chars by vertical proximity, which copes with
    # slightly skewed scans far better than fixed-height y buckets.
    # offset (from pdf_coords.viewer_offset) maps pdfplumber coordinates onto
    # the page space the website's PdfViewer draws in.
    dx, dy = offset
    return [
        {'text': ln['text'], 'x': round(ln['x0'] - dx, 1), 'y': round(ln['top'] - dy, 1), 'page': page_num}
        for ln in page.extract_text_lines(strip=True, return_chars=False)
        if ln['text'].strip()
    ]


def extract_lines_single_column(pdf_path: str, start_page: int, end_page: int | None) -> list[dict]:
    """Extract each line as {text, x, y, page} in reading order (viewer coordinates)."""
    lines: list[dict] = []
    with pdfplumber.open(pdf_path) as pdf:
        stop = min(end_page, len(pdf.pages)) if end_page else len(pdf.pages)
        for page_num in range(start_page - 1, stop):
            page = pdf.pages[page_num]
            lines.extend(_page_lines(page, page_num + 1, viewer_offset(page)))
    return lines


def find_gutter(page, offset: tuple[float, float], lo_frac: float = 0.35, hi_frac: float = 0.65) -> float:
    """The x (viewer space) in the middle band of the page that the fewest words cross —
    the column gutter. Books alternate the gutter between odd and even pages."""
    dx = offset[0]
    words = page.extract_words(keep_blank_chars=False)
    width = float(page.width)
    best = None
    for x in range(int(width * lo_frac), int(width * hi_frac)):
        cover = sum(1 for w in words if w['x0'] - dx - 1 <= x <= w['x1'] - dx + 1)
        if best is None or cover < best[0]:
            best = (cover, x)
    return float(best[1]) if best else width / 2


def extract_lines_two_column(pdf_path: str, start_page: int, end_page: int | None, col_split_x) -> list[dict]:
    """Split each page at col_split_x (by char x0) and return lines in reading
    order: left column, then right column, then the next page — so entries that
    wrap across a column or page boundary stay contiguous.
    col_split_x='auto' finds the gutter on every page (find_gutter)."""
    lines: list[dict] = []
    with pdfplumber.open(pdf_path) as pdf:
        stop = min(end_page, len(pdf.pages)) if end_page else len(pdf.pages)
        for page_num in range(start_page - 1, stop):
            page = pdf.pages[page_num]
            offset = viewer_offset(page)
            dx = offset[0]
            # col_split_x is in viewer coordinates, like everything the scaffold emits
            split = find_gutter(page, offset) if col_split_x == 'auto' else col_split_x
            lpage = page.filter(lambda o: o.get('object_type') != 'char' or o['x0'] - dx < split)
            rpage = page.filter(lambda o: o.get('object_type') != 'char' or o['x0'] - dx >= split)
            lines.extend(_page_lines(lpage, page_num + 1, offset))
            lines.extend(_page_lines(rpage, page_num + 1, offset))
    return lines


# ─────────────────────────────────────────────
# Entry grouping — heuristic that most brigades share
# ─────────────────────────────────────────────

LINE_HEIGHT = 10         # pt; typical VII-series body text leading (~9pt) plus margin

U = 'A-ZČĆŽŠĐ'          # uppercase (Cyrillic is transliterated before matching)
L = 'a-zčćžšđ'

# SURNAME[ — SURNAME][.][*] [(MAIDEN)] [(F)] [F.] [Father-genitive-titlecase [i Mother]] GIVEN
_SURNAME = rf'[{U}]{{2,}}[{U}\-]*(?:\.?\s*[—–]\s*[{U}]{{2,}}[{U}\-]*)?'
_INITIAL = rf'[{U}][jJ]?'          # R, Lj, Nj, Dž-style father's initial
DEFAULT_ENTRY_START = re.compile(
    rf'^{_SURNAME}[.,]?\*?'
    rf'(?:\s+\([{U}]{{2,}}[{U}\-]*\)|,?\s+rođ\.\s+[{U}]{{2,}}[{U}\-]*)?'
    rf'(?:\s+\([{U}]\))?'
    rf'(?:\s+{_INITIAL}\.?)?'
    rf'(?:\s+[{U}][{L}]+(?:\s+i\s+[{U}][{L}]+)?)?'
    rf'\s+[{U}][{U}\-]+'
)

# Page numbers with scan noise ("'400", "26- 403"). A bare 18xx/19xx year is kept:
# it can be a genuine continuation line.
_JUNK_LINE = re.compile(r'^[^\w]*\d{1,3}(?:[^\w]+\d{1,3})*[^\w]*$|^[^\w]+$')

def _fix_caps_token(tok: str) -> str:
    letters = [c for c in tok if c.isalpha()]
    if len(letters) >= 4 and 'l' in tok and sum(c.isupper() for c in letters) / len(letters) >= 0.7:
        return tok.replace('l', 'I')
    return tok


_CAPS_WORD = re.compile(rf'[{U}]{{3,}}')

# Scan specks before a name: "| KRSTIĆ", "! KUDRA", "* KUZMANOVIĆ", "1 MANIĆANIN", "I RISTIĆ", "'PURIĆ"
_LEADING_JUNK = re.compile(rf'^(?:[^\w\s(]+\s*|(?:\d|[Iil])\s+)(?=[{U}]{{3,}})')


def garbled_name_start(text: str) -> bool:
    """Entry start whose surname contains OCR junk (BAJ1AN ČEDE JOVAN,
    GR^UJIĆ MILANA KOSTA): a mostly-uppercase first token followed by a clean
    ALL-CAPS token. Without this such soldiers merge into the previous entry."""
    tokens = text.split(maxsplit=2)
    if len(tokens) < 2:
        return False
    t0, t1 = tokens[0], tokens[1].rstrip(',*')
    return (len(t0) >= 4 and t0[0].isupper()
            and sum(c.isupper() for c in t0) / len(t0) >= 0.7
            and bool(_CAPS_WORD.fullmatch(t1)))


def repair_caps_ocr(text: str) -> str:
    """OCR often reads 'I' as 'l' inside ALL-CAPS names (BOSIOClC, ZlVAN).
    Fix it in the leading tokens of a line, where names live."""
    parts = text.split(' ', 5)
    return ' '.join([_fix_caps_token(t) for t in parts[:5]] + parts[5:])


def group_into_entries(
    lines: Iterable[dict],
    entry_start_re: re.Pattern = DEFAULT_ENTRY_START,
    skip_re: re.Pattern | None = None,
) -> list[dict]:
    """Merge continuation lines into whole entries; a line matching
    entry_start_re begins a new entry."""
    entries: list[dict] = []
    current: dict | None = None
    for line in lines:
        text = repair_caps_ocr(_LEADING_JUNK.sub('', line['text'].strip()))
        if not text:
            continue
        if skip_re and skip_re.search(text):
            continue
        if _JUNK_LINE.match(text):
            continue

        is_new = bool(entry_start_re.match(text)) or (
            entry_start_re is DEFAULT_ENTRY_START and garbled_name_start(text))

        if is_new:
            if current:
                entries.append(current)
            current = {'text': text, 'first_line': line, 'last_y': line['y']}
        elif current is not None:
            if line['page'] == current['first_line']['page']:
                current['last_y'] = line['y']
            prev = current['text']
            if prev.endswith('-') and not prev.endswith(' -'):
                # "Bije-" + "ljina" → "Bijeljina";  "Žepa-" + "Rogatica" → "Žepa-Rogatica"
                current['text'] = (prev[:-1] if text[0].islower() else prev) + text
            else:
                current['text'] = prev + ' ' + text

    if current:
        entries.append(current)
    return entries


# ─────────────────────────────────────────────
# Field extraction primitives
# ─────────────────────────────────────────────

_BORN_FULL_DATE = re.compile(r'ro[đć]en[a]?\s+\d{1,2}\.\s*[IVX\d]{1,4}\.?\s*(1[89]\d{2})')


# Same vocabulary the daily-soldier-validation routine task uses for death_type
_DEATH_TYPES = [
    (re.compile(r'(?i)\bpoginu'), 'poginuo'),
    (re.compile(r'(?i)\bumr[ol]'), 'umro'),
    (re.compile(r'(?i)\bnesta[ol]'), 'nestao'),
    (re.compile(r'(?i)\bstreljan'), 'streljan'),
    (re.compile(r'(?i)\bzarobljen'), 'zarobljen'),
]


def death_type_from_text(info: str) -> str:
    """First fate keyword in the text, mapped to the controlled vocabulary."""
    hits = [(m.start(), value) for rx, value in _DEATH_TYPES for m in [rx.search(info)] if m]
    return min(hits)[1] if hits else ''


def extract_birth_year(info: str) -> str:
    # Never take the first year found: it is often the death or enlistment year
    # ("rođen u s. Poljavnice, ... poginuo novembra 1942").
    _, year = extract_birth_info(info)
    if not year:
        m = _BORN_FULL_DATE.search(info)
        year = m.group(1) if m else ''
    return year


NAME_RE = re.compile(
    rf'^(?:\d+\.\s*)?'
    rf'(?P<last>{_SURNAME})[.,]?\*?'
    rf'(?:\s+\((?P<maiden>[{U}]{{2,}}[{U}\-]*)\)|,?\s+rođ\.\s+(?P<maiden2>[{U}]{{2,}}[{U}\-]*))?'
    rf'(?:\s+\((?P<finit>[{U}])\))?'
    rf'(?:\s+(?P<finit2>{_INITIAL})\.)?'
    rf'(?:\s+(?P<ftitle>[{U}][{L}]+(?:\s+i\s+[{U}][{L}]+)?))?'
    rf'(?P<given>(?:\s+[{U}][{U}\-]+\*?)+)'
    rf'(?:\s*\((?P<nick>[{U}][{U}{L}]+)\))?'
    rf'(?:\s+[-–—]\s*(?P<nick2>[{U}][{L}]+)\b)?'
    rf'(?P<rest>.*)$'
)

_GENITIVE_ENDINGS = ('A', 'E')
_SURNAME_SUFFIX = re.compile(r'(?i)(?:ić|ski|ska|čki|čka)$')


def title_case(name: str) -> str:
    """KOVAČEVIĆ → Kovačević, LJUBOMIR → Ljubomir, PETROVIĆ-NJEGOŠ → Petrović-Njegoš.
    Mixed-case input is returned unchanged."""
    if not name or name != name.upper():
        return name
    return re.sub(r'[^\s\-—–()]+', lambda m: m.group(0)[:1] + m.group(0)[1:].lower(), name)


def _record(last: str, first: str, father: str, info: str, **extra) -> dict:
    last, first, father = title_case(last), title_case(first), title_case(father)
    # Project convention: middle_name = father's name as printed (usually genitive);
    # normalize_all_json.py derives the nominative fathers_name from it.
    rec = {
        'last_name': last,
        'middle_name': father,
        'first_name': first,
        'fathers_name': father,
        'full_name': ' '.join(p for p in (last, father, first) if p),
        'additional_info': info,
        'birth_year': extract_birth_year(info),
    }
    rec.update(extra)
    return rec


def parse_standard_entry(text: str) -> dict:
    """
    Parse ALL-CAPS-name entries. Handles:
      SURNAME FIRST, info                    SURNAME. FATHER-GEN FIRST*, info
      SURNAME (F) FIRST, info                SURNAME F. FIRST, info
      SURNAME Father-gen [i Mother] FIRST (NICK), info
      SURNAME FIRST - Nick, info             184. SURNAME FIRST, info
    Returns '_asterisk': True when the name carried a '*' marker.
    """
    text = text.strip()
    m = NAME_RE.match(text)
    if not m:
        # Name = leading mostly-uppercase tokens (tolerates OCR junk like BAJ1AN)
        tokens = text.split()
        n = 0
        for tok in tokens:
            core = tok.strip('.,;:*')
            if not core or sum(c.isupper() for c in core) / len(core) < 0.6:
                break
            n += 1
            if tok.rstrip('*').endswith(','):
                break
        words = [t.strip('.,;:*') for t in tokens[:n]]
        info = ' '.join(tokens[n:]).lstrip(' .,;:*-–—').strip()
        last = words[0] if words else ''
        rest = words[1:]
        father = rest.pop(0) if len(rest) >= 2 and rest[0].endswith(_GENITIVE_ENDINGS) else ''
        return _record(last, ' '.join(rest), father, info, _asterisk='*' in ' '.join(tokens[:n + 1]))

    name_span = text[:m.start('rest')]
    rest = m.group('rest')
    asterisk = '*' in name_span or rest.lstrip(' ,').startswith('*')

    given = [t.rstrip('*') for t in m.group('given').split()]
    father = ''
    extra: dict = {}
    if m.group('finit'):
        father = m.group('finit') + '.'
    elif m.group('finit2'):
        father = m.group('finit2') + '.'
    elif m.group('ftitle'):
        parents = m.group('ftitle').split(' i ')
        father = parents[0]
        if len(parents) > 1:
            extra['mothers_name'] = parents[1]
    elif len(given) >= 2 and given[0].endswith(_GENITIVE_ENDINGS):
        father = given.pop(0)

    # normalize_all_json strips parentheticals from name fields, so aliases and
    # maiden names are kept in additional_info where they stay searchable.
    prefix = []
    maiden = m.group('maiden') or m.group('maiden2')
    nick = m.group('nick') or m.group('nick2')
    if nick and _SURNAME_SUFFIX.search(nick):
        # "VUKICA (ŠIĆARSKI)" — a surname after the given name is a maiden name
        maiden, nick = maiden or nick, None
    if maiden:
        prefix.append(f"rođ. {title_case(maiden)}")
    if nick:
        prefix.append(f"zvani {title_case(nick)}")

    info = rest.lstrip(' .,;:*-–—').strip()
    if prefix:
        info = '; '.join(prefix) + (f'; {info}' if info else '')
    return _record(m.group('last'), ' '.join(given), father, info, _asterisk=asterisk, **extra)


# ─────────────────────────────────────────────
# Diacritic restoration (for scans whose OCR dropped č/ć/ž/š/đ)
# ─────────────────────────────────────────────

_FOLD = str.maketrans('čćžšđČĆŽŠĐ', 'cczsdCCZSD')
_REFERENCE_CODES = range(1, 10)   # the original, hand-verified brigades


def _fold(s: str) -> str:
    return s.translate(_FOLD)


def _load_name_reference() -> dict[str, dict[str, Counter]]:
    from scripts.name_utils import BRIGADE_CONFIGS
    ref: dict[str, dict[str, Counter]] = {f: defaultdict(Counter) for f in ('last_name', 'first_name', 'middle_name')}
    for code in _REFERENCE_CODES:
        path = _ROOT / 'website' / 'public' / BRIGADE_CONFIGS[code]['json_file']
        for s in json.loads(path.read_text(encoding='utf-8')):
            for field, counts in ref.items():
                v = s.get(field) or ''
                if v:
                    counts[_fold(v).lower()][v] += 1
    return ref


def restore_diacritics(soldiers: list[dict], min_share: float = 0.8) -> list[dict]:
    """Replace diacritic-less names with the dominant spelling seen in the
    reference brigades (ACIMOVIC → Aćimović). Surnames with no match fall back
    to -ic → -ić, which holds for South Slavic surnames."""
    ref = _load_name_reference()
    changed = 0
    for s in soldiers:
        for field, counts in ref.items():
            v = s.get(field) or ''
            if not v:
                continue
            new = v
            cands = counts.get(v.lower()) if _fold(v) == v else None
            if cands:
                best, n = cands.most_common(1)[0]
                if n >= 2 and n / sum(cands.values()) >= min_share and _fold(best) != best:
                    new = best
            if new == v and field == 'last_name' and v.endswith('ic'):
                new = v[:-2] + 'ić'
            if new != v:
                s[field] = new
                changed += 1
        s['fathers_name'] = s['middle_name']
        s['full_name'] = ' '.join(p for p in (s['last_name'], s['middle_name'], s['first_name']) if p)
    print(f"  restored diacritics in {changed} name fields")
    return soldiers


def repair_cyrillic_ocr(soldiers: list[dict], ik_is_ic: bool = False) -> list[dict]:
    """Cyrillic scans where Ћ at the end of a surname comes out as Б/Е/Н/К/В (АДАМОВИБ, АДАМОВИЕ,
    АДАМОВИН) and Ђ at the start of a name as Б (БУРО). "-ib"/"-ie" never end a surname, so they always
    become "-ić"; "-in"/"-ik"/"-iv"/"-ih" only when the name is unknown as printed and known with "-ić".
    A leading B becomes Đ when only the Đ spelling is known (Buro → Đuro)."""
    ref = _load_name_reference()
    count = lambda field, v: sum((ref.get(field, {}).get(_fold(v).lower()) or {}).values())
    known = lambda field, v: count(field, v) > 0
    changed = 0
    for s in soldiers:
        last = s.get('last_name') or ''
        parts = []
        for p in last.split('-'):
            if re.search(r'i[beđ]$', p) or re.search(r'[oe]vi[nkvh]$', p) or (ik_is_ic and re.search(r'i[kv]$', p)):
                p = p[:-1] + 'ć'                                   # -ović/-ević are never -ovin/-evik
            elif re.search(r'i[nkvh]$', p) and count('last_name', p[:-1] + 'ć') >= 10 * max(count('last_name', p), 1):
                p = p[:-1] + 'ć'
            parts.append(p)
        new_last = '-'.join(parts)
        if new_last != last:
            s['last_name'] = new_last
            changed += 1
        for field in ('last_name', 'first_name', 'middle_name'):
            v = s.get(field) or ''
            if not re.search('[Bb]', v) or known(field, v):
                continue
            # any one or two B's may be a misread Đ (or D): БОРБЕ → ĐORĐE, БУРАБ → ĐURAĐ, АБАМОВИЋ → Adamović
            spots = [i for i, ch in enumerate(v) if ch in 'Bb']
            best = None
            for k in (1, 2):
                for combo in __import__('itertools').combinations(spots, k):
                    for repl in ('Đđ', 'Dd'):
                        cand = ''.join((repl[0] if ch == 'B' else repl[1]) if i in combo else ch for i, ch in enumerate(v))
                        n = (ref.get(field, {}).get(_fold(cand).lower()) or {}).get(cand, 0)   # exact spelling: fold(đ) == d
                        if n >= (3 if field == 'last_name' else 2) and (best is None or n > best[0]):
                            best = (n, cand)
            if best:
                s[field] = best[1]
                changed += 1
        s['fathers_name'] = s.get('middle_name', '')
        s['full_name'] = ' '.join(p for p in (s['last_name'], s['middle_name'], s['first_name']) if p)
    print(f"  repaired Cyrillic OCR in {changed} name fields")
    return soldiers


MUSLIM_NAMES = {'Vahid', 'Ibro', 'Ibra', 'Ibrahim', 'Nezir', 'Musa', 'Mehmed', 'Sakib', 'Šaban', 'Husa', 'Alija',
                'Ilijaš', 'Čelim', 'Rifat', 'Sulejman', 'Kadro', 'Mujo', 'Suljo', 'Hasan', 'Huso', 'Salih', 'Osman',
                'Ahmet', 'Adem', 'Omer', 'Mustafa', 'Smajo', 'Avdo', 'Halil', 'Ismet', 'Hamdija', 'Muharem', 'Ramiz',
                'Safet', 'Asim', 'Hamid', 'Idriz', 'Jusuf', 'Meho', 'Rasim', 'Redžep', 'Selim', 'Sejdo', 'Emin'}
# books whose scans never read a capital Ћ: their names are no evidence for the spelling of others
CAPITAL_C_MISREAD = ('4-krajiska-soldiers.json', '7-vojvodjanska-soldiers.json', '19-bircanska-soldiers.json')


def repair_capital_c(soldiers: list[dict]) -> list[dict]:
    """For Cyrillic scans that never read a capital Ћ as Ћ (7. Vojvođanska: ИН ×1653, ИБ, ИЕ, ИК, ИЋ ×0): at the
    end of a surname it comes out as Н, Б, Е or К, and at the start as Н, while real "-in" surnames are ~4% of
    the Vojvodina lists. repair_cyrillic_ocr fixes "-ib"/"-ie" and "-in" where "-ić" is far more common; here
    a surname that no other unit knows is repaired when the repaired spelling is known: "-in" → "-ić" (Stojšin
    → Stojšić, Avdin → Avdić) and a leading N → Ć (Nirić → Ćirić). Known "-in" surnames (Vujin, Lukin) and
    demonyms (Bugarin) stay, except for Bosniak soldiers (Alibašin Ibro → Alibašić). Given names: Б read for
    Ђ (Bura → Đura) when the Đ spelling is far more common."""
    ref, first = Counter(), Counter()
    for f in Path('website/public').glob('*soldiers.json'):
        if f.name not in CAPITAL_C_MISREAD:
            for s in json.loads(f.read_text(encoding='utf-8')):
                ref[s['last_name']] += 1
                first[s['first_name']] += 1
    n = 0
    for s in soldiers:
        parts = s['last_name'].split('-')
        for i, p in enumerate(parts):
            q = p
            if q.startswith('N') and not ref[q] and ref['Ć' + q[1:]]:
                q = 'Ć' + q[1:]
            if q.endswith('in') and not q.endswith('anin') and not ref[q] and \
                    (ref[q[:-1] + 'ć'] >= 2 or s['first_name'] in MUSLIM_NAMES):
                q = q[:-1] + 'ć'
            n += q != p
            parts[i] = q
        s['last_name'] = '-'.join(parts)
        g = s['first_name']
        if g.startswith('B') and first['Đ' + g[1:]] >= 10 * max(first[g], 1):
            s['first_name'] = 'Đ' + g[1:]
            n += 1
        s['full_name'] = ' '.join(x for x in (s['last_name'], s.get('middle_name') or '', s['first_name']) if x)
    print(f'  capital Ћ/Ђ restored in {n} names')
    return soldiers


def repair_lj_ocr(soldiers: list[dict]) -> list[dict]:
    """Some scans read "LJ" as "U" (KRAGUU, UUBO, VUEVIĆ). A name that is unknown as printed but known
    with one "u" read back as "lj" takes the known spelling (Kragulj, Ljubo, Vljević)."""
    ref = _load_name_reference()
    changed = 0
    for s in soldiers:
        for field in ('last_name', 'first_name'):
            v = s.get(field) or ''
            counts = ref.get(field, {})
            if not v or 'u' not in v.lower() or counts.get(_fold(v).lower()):
                continue
            low = _fold(v).lower()
            found = Counter()
            for i, ch in enumerate(low):
                if ch == 'u':
                    for spelling, n in counts.get(low[:i] + 'lj' + low[i + 1:], {}).items():
                        found[spelling] += n
            if found and sum(found.values()) >= 2:
                s[field] = found.most_common(1)[0][0]
                changed += 1
        s['full_name'] = ' '.join(p for p in (s['last_name'], s['middle_name'], s['first_name']) if p)
    print(f"  repaired LJ->U OCR in {changed} name fields")
    return soldiers


# ─────────────────────────────────────────────
# Runner
# ─────────────────────────────────────────────

def run_parser(
    pdf_path: str,
    brigade_code: int,
    output_path: str,
    start_page: int = 1,
    end_page: int | None = None,
    layout: str = 'single',
    col_split_x: float | None = None,
    script: str = 'latin',
    entry_start_re: re.Pattern = DEFAULT_ENTRY_START,
    parse_entry_fn: Callable[[str], dict] = parse_standard_entry,
    skip_re: re.Pattern | None = None,
    additional_pdfs: list[dict] | None = None,
    asterisk_marks_death: bool = False,
    line_filter: Callable[[dict], bool] | None = None,
    post_fn: Callable[[list[dict]], list[dict]] | None = None,
    prepare_fn: Callable[[list[dict]], None] | None = None,
    id_start: int = 1,
    keep_other_sources: bool = False,
) -> list[dict]:
    """
    Common runner. Extract → group → parse → assign IDs → save.

    asterisk_marks_death: the book marks killed/died soldiers with '*'; for those,
    record death_type from the entry text (left unset if the text doesn't say).
    line_filter: return False to drop a line ({text, x, y, page, file}) before
    grouping — for footnotes, running headers, back matter.
    prepare_fn: sees each source's lines before line_filter (e.g. to measure page margins).
    id_start, keep_other_sources: add another book to a unit whose file already holds records from other
    PDFs — this run's records get IDs from id_start and replace only the records read from this run's PDFs.

    Returns list of soldier dicts (also written to output_path).
    """
    print(f"[{brigade_code}] parsing {pdf_path} (pages {start_page}-{end_page or 'end'})")

    sources = [{'pdf_path': pdf_path, 'start_page': start_page, 'end_page': end_page}]
    if additional_pdfs:
        sources.extend(additional_pdfs)

    all_entries: list[dict] = []
    for src in sources:
        p = src['pdf_path']
        sp = src.get('start_page', 1)
        ep = src.get('end_page')
        if layout == 'two_column':
            assert col_split_x is not None, "col_split_x required for two_column"
            lines = extract_lines_two_column(p, sp, ep, col_split_x)
        else:
            lines = extract_lines_single_column(p, sp, ep)
        for ln in lines:
            ln['file'] = Path(p).name
            if script == 'cyrillic':
                ln['text'] = cyrillic_to_latin(ln['text'])
        if prepare_fn:
            prepare_fn(lines)
        if line_filter:
            lines = [ln for ln in lines if line_filter(ln)]
        all_entries.extend(group_into_entries(lines, entry_start_re, skip_re=skip_re))

    print(f"  extracted {len(all_entries)} raw entries")

    soldiers: list[dict] = []
    for e in all_entries:
        rec = parse_entry_fn(e['text'])
        asterisk = rec.pop('_asterisk', False)
        if not rec.get('last_name'):
            continue
        if asterisk and asterisk_marks_death:
            death_type = death_type_from_text(rec['additional_info'])
            if death_type:
                rec['death_type'] = death_type
        fl = e.get('first_line') or {}
        if 'page' in fl:
            rec['pdf_page'] = fl['page']
            rec['pdf_y'] = fl.get('y')
            rec['pdf_x'] = round(fl.get('x', 0), 1)
            rec['pdf_y_end'] = round(e['last_y'] + LINE_HEIGHT, 1)
            rec['pdf_file'] = fl.get('file', Path(pdf_path).name)
        soldiers.append(rec)

    if post_fn:
        soldiers = post_fn(soldiers)
    soldiers.sort(key=lambda s: (s['last_name'].lower(), s['first_name'].lower()))
    soldiers = assign_ids_to_soldiers(soldiers, brigade_code, id_start)

    with_birth = sum(1 for s in soldiers if s['birth_year'])
    with_father = sum(1 for s in soldiers if s['fathers_name'])
    print(f"  {len(soldiers)} soldiers  |  birth_year: {with_birth}  |  fathers_name: {with_father}")
    if soldiers:
        print("  samples:")
        for s in soldiers[:3] + soldiers[-2:]:
            print(f"    {s['soldier_id']} — {s['full_name']}  ({s['additional_info'][:60]})")

    out = soldiers
    if keep_other_sources and Path(output_path).exists():
        mine = {Path(src['pdf_path']).name for src in sources}
        with open(output_path, encoding='utf-8') as f:
            kept = [s for s in json.load(f) if s.get('pdf_file') not in mine]
        clash = {s['soldier_id'] for s in kept} & {s['soldier_id'] for s in soldiers}
        assert not clash, f"IDs from id_start={id_start} are already used: {sorted(clash)[:5]}"
        out = kept + soldiers
        print(f"  kept {len(kept)} records from other sources")

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"  → {output_path}")

    return soldiers
