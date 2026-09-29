"""
Entry starts by position, for books whose continuation lines are indented: a line whose first word is a
caps surname and that sits at the page's left margin starts an entry, whatever follows the surname.
Complements _parser_scaffold.DEFAULT_ENTRY_START, which needs "SURNAME ... GIVEN" in caps and so misses
    ANDREJ, rodom iz SSSR                  (one name only)
    GRUBOR Gojko, rođen u Primišlju        (given name not in caps)
    VUJIČIĆ Jove MILAN — SNJACO, rođen ... (nickname after a dash)
Such lines get a marker after the surname (the scaffold strips leading junk, so it can't go first) and are
read by parse_marked_entry; every other line goes to the scaffold's parse_standard_entry.

    me = MarginEntries()
    def keep_line(ln):
        ...book-specific filtering...
        return me.mark(ln)
    run_parser(..., entry_start_re=me.entry_start, parse_entry_fn=me.parse_entry, line_filter=keep_line,
               prepare_fn=me.prepare)
"""
import re
from collections import defaultdict

from _parser_scaffold import DEFAULT_ENTRY_START, _record, parse_standard_entry, title_case

U, L = 'A-ZČĆŽŠĐ', 'a-zčćžšđ'
MARK = '⁣'
ABBR = {'SSSR', 'KPJ', 'SKOJ', 'NOB', 'NOP', 'NOV', 'NOVJ', 'JNA', 'SFRJ', 'SAD', 'BIH', 'SR', 'MB', 'NN'}
BIO_START = re.compile(r'\s(?:rođen|rođena|rodom|iz|poginuo|poginula|umro|umrla|ranjen|ranjena)\b')


def join_split_surname(t: str) -> str:
    """'CA VIĆ Janka STOJAN' -> 'CAVIĆ Janka STOJAN'; 'TAUF ANO VIĆ Milije NIFA' -> 'TAUFANOVIĆ ...'."""
    toks = t.split(' ')
    for j in range(2, 4):
        head = toks[:j]
        if len(toks) <= j or not all(re.fullmatch(rf'[{U}]{{1,6}}', x) for x in head):
            continue
        word = ''.join(head)
        if re.search(r'(?:VIĆ|VIC|IĆ|IC|AR|AK)$', word) and len(head[-1]) <= 4 and \
                re.match(rf'^(?:[{U}][{L}]+|[{U}]\.|[{U}]{{2,}}[,.]?)$', toks[j]):
            return ' '.join([word] + toks[j:])
    return t


def fix_caps_head(t: str) -> str:
    """OCR 'l'/'i' for capital I inside the leading caps surname: 'ZlVKOVlC' -> 'ZIVKOVIC', 'SUZiC' -> 'SUZIC'."""
    return re.sub(rf'^[{U}]*[li][{U}li]*\b', lambda m: m.group(0).replace('l', 'I').replace('i', 'I')
                  if sum(c.isupper() for c in m.group(0)) >= 2 else m.group(0), t)


def fix_cyrillic_ocr_line(t: str) -> str:
    """Repairs for Cyrillic scans read as Latin (from parse_4_krajiska.py): Ђ read as Ћ in "rođen",
    Л read as "Ј1", and digits inside caps names (О → 0, З → 3, Л/Ј → 1)."""
    t = re.sub(r'\bro[ćc]en', 'rođen', t)
    t = t.replace('J1', 'L').replace('j1', 'l')
    t = re.sub(r'\bJb\s?(?=[a-zčćžšđ])', 'Lj', t)        # Љ read as "Јb": "Jbubomir", "Jb ubomira"
    t = re.sub(r'\bJB(?=[A-ZČĆŽŠĐ])', 'LJ', t)
    head, sep, tail = t.partition(' ')
    if re.fullmatch(r'[A-ZČĆŽŠĐ03]{4,}', head) and re.search(r'[03]', head):
        t = head.replace('0', 'O').replace('3', 'Z') + sep + tail
    name, comma, rest = t.partition(',')
    name = re.sub(r'\b([A-ZČĆŽŠĐ]{2,})\s+(?=[013][A-ZČĆŽŠĐ013]*\b)', r'\1', name)

    def _digits(m: re.Match) -> str:
        w = m.group(0).replace('0', 'O').replace('3', 'Z')
        w = re.sub(r'(?<=O)1$', 'J', w)
        return w.replace('1', 'L')
    name = re.sub(r'\b(?=[A-ZČĆŽŠĐ013]*[A-ZČĆŽŠĐ])(?=[A-ZČĆŽŠĐ013]*[013])[A-ZČĆŽŠĐ013]{3,}\b', _digits, name)
    return name + comma + rest


def _alias(txt: str) -> str:
    return ' '.join(title_case(w) for w in txt.split())


class MarginEntries:
    def __init__(self, margin_tol: float = 6, abbr: set[str] | None = None):
        self.margin_tol = margin_tol
        self.abbr = ABBR | (abbr or set())
        self.left: dict[tuple, float] = defaultdict(lambda: 1e9)
        self.entry_start = re.compile(rf'^(?:[{U}][{U}\-]*{MARK}|{DEFAULT_ENTRY_START.pattern})')

    def prepare(self, lines: list[dict]) -> None:
        """Measure each page's margin from all its lines first (pass as run_parser's prepare_fn); otherwise
        the margin is only known from the lines seen so far, and a continuation line at the top of a page
        reads as an entry start."""
        for ln in lines:
            if re.match(rf'[{U}]', ln['text'].strip()):
                key = (ln.get('file'), ln['page'])
                self.left[key] = min(self.left[key], ln['x'])

    def mark(self, ln: dict) -> bool:
        """Normalize the line's leading surname and mark a margin line the default pattern can't read."""
        t = join_split_surname(fix_caps_head(ln['text'].strip()))
        key = (ln.get('file'), ln['page'])
        self.left[key] = min(self.left[key], ln['x'])
        m = re.match(rf'^([{U}][{U}\-]+)', t)
        if ln['x'] <= self.left[key] + self.margin_tol and m and m.group(1) not in self.abbr \
                and not DEFAULT_ENTRY_START.match(t):
            t = m.group(1) + MARK + t[m.end():]
        ln['text'] = t
        return True

    def parse_entry(self, text: str) -> dict:
        """Marked lines: SURNAME [(ili ALT) | (Nickname) | (note)] [dr] [Father] Given [— NICK], bio."""
        if MARK not in text:
            return parse_standard_entry(text)
        last, rest = text.split(MARK, 1)
        prefix = []
        m = re.match(r'^\s*\((ili\s+)?([^)]*)\)\s*', rest)
        if m:
            inner = m.group(2).strip()
            if m.group(1) or re.fullmatch(rf'[{U}][{L}]+i[ćc]', inner):      # "(Pavić)": another surname
                prefix.append('ili ' + _alias(inner))
            elif inner.lower() == 'djevojačko prezime':
                prefix.append('djevojačko prezime')
            elif re.fullmatch(rf'[{U}][{L}]+', inner) and not inner.lower().startswith(('veterin', 'ljekar', 'lekar')):
                prefix.append('zvani ' + inner)
            else:
                rest = inner + ', ' + rest[m.end():].lstrip(' ,')
                m = None
            if m:
                rest = rest[m.end():]
        rest = rest.strip()
        if re.match(r'^dr\b\.?\s*', rest):
            prefix.append('dr')
            rest = re.sub(r'^dr\b\.?\s*', '', rest)
        cut = len(rest)
        # the name ends at a comma, at a period after a word or right after the surname (not after an
        # initial like "D."), or where the bio starts
        for pat in (r',', rf'(?:(?<=[^{U}])|(?<=[{U}]{{2}}))\.(?=\s|$)', r'^\s*\.', BIO_START.pattern):
            mm = re.search(pat, rest)
            if mm:
                cut = min(cut, mm.start())
        name, info = rest[:cut].strip(), rest[cut:].lstrip(' ,.').strip()
        # only an initial is known: "DEŽMAN J. Autor napisa u brigadnom listu, ..."
        mm = re.match(rf'^([{U}]\.)\s+(?=[{U}][{L}]*\s+\S)', rest)
        if mm and not re.match(rf'^[{U}]\.\s+[{U}]{{2,}}\b', rest):
            name, info = mm.group(1), rest[mm.end():].strip()
        nick = re.split(r'\s+[—–-]\s+', name, 1)
        if len(nick) == 2:
            name = nick[0]
            prefix.append('zvani ' + _alias(nick[1]))
        name = re.sub(rf'\b([{U}][{L}]+) ([{L}]{{1,3}})\b', r'\1\2', name)      # "Dmitri ja" -> "Dmitrija"
        words = name.split()
        father, first = ('', '')
        if len(words) >= 2:
            father, first = words[0], ' '.join(words[1:])
        elif words and re.fullmatch(rf'[{U}]\.', words[0]):
            father = words[0]
        elif words:
            first = words[0]
        if prefix:
            info = '; '.join(prefix) + (f'; {info}' if info else '')
        return _record(last, first, father, info)


def split_leading_aliases(soldiers: list[dict], abbr: set[str] | None = None) -> list[dict]:
    """After parsing: a caps nickname or "(ili X)" left at the start of the bio, or an alias left in a name
    field, moves to the bio prefix ("zvani X; ", "ili X; ")."""
    abbr = ABBR | (abbr or set())
    for s in soldiers:
        info = s.get('additional_info') or ''
        prefix = []
        while True:
            m = re.match(rf'^\((ili\s+)?([{U}][{U} \-]*)\),?\s*', info)
            if m:
                prefix.append(('ili ' if m.group(1) else 'zvani ') + _alias(m.group(2) if m.group(1) else m.group(2).replace(' ', '')))
                info = info[m.end():]
                continue
            m = re.match(rf'^([{U}]{{3,}})[,.]\s*', info)
            if m and m.group(1) not in abbr:
                prefix.append('zvani ' + _alias(m.group(1)))
                info = info[m.end():]
                continue
            break
        for k in ('first_name', 'last_name'):
            m = re.search(r'\s*\((?:ili\s+)?([^)]*)\)\s*', s.get(k) or '')
            if m:
                prefix.append('ili ' + _alias(m.group(1).replace(' ', '')))
                s[k] = (s[k][:m.start()] + ' ' + s[k][m.end():]).strip()
        if prefix:
            info = '; '.join(prefix) + ('; ' + info if info else '')
        s['additional_info'] = info
    return soldiers


def lone_names_to_given(soldiers: list[dict], first_counts, last_counts) -> list[dict]:
    """A one-name entry is parsed as a surname; move it to first_name when it reads as a given name."""
    for s in soldiers:
        if s['last_name'] and not s['first_name'] and not s.get('middle_name'):
            n = s['last_name']
            looks_surname = re.search(r'(?:ić|ic|ač|ak|ar|ec|ek|ov|ev|ija|ina)$', n.lower()) or last_counts[n] > first_counts[n]
            if not looks_surname and first_counts[n] >= 1:
                s['first_name'], s['last_name'] = n, ''
        s['full_name'] = ' '.join(x for x in (s['last_name'], s.get('middle_name') or '', s['first_name']) if x)
    return soldiers
