"""
Parser: 4. Banijska NOU Brigada (brigade code 20).

Source: "ČETVRTA BANIJSKA NOU BRIGADA — Zbornik sjećanja", chapter "Spisak boraca"
        znaci.org/00001/188_4.pdf  →  website/public/pdfs/4-banijska.pdf
Single column, Latin. p.1 title, pp. 2-51 one alphabetical list with a capital letter heading per
letter group, pp. 52-53 the book's table of contents.
    ADAMOVIĆ Petra JANKO, rođen 1919. u Segestinu (Dvor na Uni)
    AKIK J. STOJAN, rođen 1922. u Udetinu (Dvor na Uni)
    GRUBOR Gojko, rođen u Primišlju (Slunj).          (given name not in caps)
    VUJIČIĆ Jove MILAN — SNJACO, rođen 1924. ...        (nickname after a dash)
    MIKULIN (ili MIŠKULIN) JAKOV, rođen u Praćnom.
    ANDREJ, rodom iz SSSR                              (one name only: Soviet volunteers, nicknames)
    CA VIĆ Janka STOJAN, ...                           (OCR split the surname: ČAVIĆ)
Continuation lines are indented ~16pt, so an entry starts where a caps word sits at the page's
left margin; lines the scaffold's pattern can't read get a marker and their own name parser.
"""
import json
import re
from collections import Counter, defaultdict

from _parser_scaffold import (DEFAULT_ENTRY_START, _record, parse_standard_entry, repair_lj_ocr,
                              restore_diacritics, run_parser, title_case)

U, L = 'A-ZČĆŽŠĐ', 'a-zčćžšđ'
LETTER_HEADING = re.compile(rf'^[{U}]{{1,2}}$')
TOC_LINE = re.compile(r'(?:—\s*){2,}|_\s*_|^Strana$|^S A D R Ž')
ABBR = {'SSSR', 'KPJ', 'SKOJ', 'NOB', 'NOP', 'NOV', 'NOVJ', 'JNA', 'SFRJ', 'SAD', 'BIH'}
MARK = '⁣'                                  # invisible separator after the first word: "this line starts an entry"
ENTRY_START = re.compile(rf'^(?:[{U}][{U}\-]*{MARK}|{DEFAULT_ENTRY_START.pattern})')
BIO_START = re.compile(r'\s(?:rođen|rođena|rodom|iz|poginuo|poginula|umro|umrla)\b')

_left: dict[int, float] = defaultdict(lambda: 1e9)


def _join_split_surname(t: str) -> str:
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


def keep_line(ln: dict) -> bool:
    t = ln['text'].strip()
    if LETTER_HEADING.match(t) or TOC_LINE.search(t) or re.fullmatch(r'[•.\s]*\d{3}', t):
        return False
    t = re.sub(rf'^[{U}]*[li][{U}li]*\b', lambda m: m.group(0).replace('l', 'I').replace('i', 'I')
               if sum(c.isupper() for c in m.group(0)) >= 2 else m.group(0), t)                  # "ZlVKOVlC", "SUZiC"
    t = _join_split_surname(t)
    _left[ln['page']] = min(_left[ln['page']], ln['x'])
    m = re.match(rf'^([{U}][{U}\-]+)', t)
    if ln['x'] <= _left[ln['page']] + 6 and m and m.group(1) not in ABBR and not DEFAULT_ENTRY_START.match(t):
        t = m.group(1) + MARK + t[m.end():]
    ln['text'] = t
    return True


def _alias(txt: str) -> str:
    return ' '.join(title_case(w) for w in txt.split())


def parse_entry(text: str) -> dict:
    """Marked lines: SURNAME [(ili ALT) | (note)] [dr] [Father] Given [— NICK], bio."""
    if MARK not in text:
        return parse_standard_entry(text)
    last, rest = text.split(MARK, 1)
    prefix = []
    m = re.match(r'^\s*\((ili\s+)?([^)]*)\)\s*', rest)
    if m:
        inner = m.group(2).strip()
        if m.group(1):
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
    # the name part ends at the first comma, a final period, or where the bio starts
    cut = len(rest)
    for pat in (r',', r'\.\s*$', BIO_START.pattern):
        mm = re.search(pat, rest)
        if mm:
            cut = min(cut, mm.start())
    name, info = rest[:cut].strip(), rest[cut:].lstrip(' ,.').strip()
    nick = re.split(r'\s+[—–-]\s+', name, 1)
    if len(nick) == 2:
        name = nick[0]
        prefix.append('zvani ' + _alias(nick[1]))
    # OCR broke a father's name ("Dmitri ja", "Moj ana"): rejoin a lowercase fragment
    name = re.sub(rf'\b([{U}][{L}]+) ([{L}]{{1,3}})\b', r'\1\2', name)
    words = name.split()
    father, first = '', ''
    if len(words) >= 2:
        father, first = words[0], ' '.join(words[1:])
    elif words:
        first = words[0]
    if prefix:
        info = '; '.join(prefix) + (f'; {info}' if info else '')
    return _record(last, first, father, info)


def post(soldiers: list[dict]) -> list[dict]:
    soldiers = repair_lj_ocr(restore_diacritics(soldiers))
    first_counts, last_counts = Counter(), Counter()
    for f in ('prva-proleterska-soldiers.json', 'soldiers.json', '13-proleterska-soldiers.json', '6-krajiska-soldiers.json'):
        for s in json.load(open('website/public/' + f, encoding='utf-8')):
            first_counts[s['first_name']] += 1
            last_counts[s['last_name']] += 1
    for s in soldiers:
        info = s.get('additional_info') or ''
        # "KAMPOS Jakova MORIC MOCO": a caps nickname right after the name reads as the start of the bio
        prefix = []
        while True:
            m = re.match(rf'^\((ili\s+)?([{U}][{U} \-]*)\),?\s*', info)                   # "(ili STANKO), rođen"
            if m:
                prefix.append(('ili ' if m.group(1) else 'zvani ') + _alias(m.group(2) if m.group(1) else m.group(2).replace(' ', '')))
                info = info[m.end():]
                continue
            m = re.match(rf'^([{U}]{{3,}})[,.]\s*', info)                                  # "MOCO, rođen 1913."
            if m and m.group(1) not in ABBR:
                prefix.append('zvani ' + _alias(m.group(1)))
                info = info[m.end():]
                continue
            break
        for k in ('first_name', 'last_name'):                                               # "MIKULIN (ili MIŠKULIN)"
            m = re.search(r'\s*\((?:ili\s+)?([^)]*)\)\s*', s.get(k) or '')
            if m:
                prefix.append('ili ' + _alias(m.group(1).replace(' ', '')))
                s[k] = (s[k][:m.start()] + ' ' + s[k][m.end():]).strip()
        if prefix:
            info = '; '.join(prefix) + ('; ' + info if info else '')
        s['additional_info'] = info
        # a lone name: a surname if it looks like one, otherwise a given name ("ANDREJ, rodom iz SSSR")
        if s['last_name'] and not s['first_name'] and not s.get('middle_name'):
            n = s['last_name']
            looks_surname = re.search(r'(?:ić|ic|ač|ak|ar|ec|ek|ov|ev|ija|ina|ak)$', n.lower()) or last_counts[n] > first_counts[n]
            if not looks_surname and first_counts[n] >= 1:
                s['first_name'], s['last_name'] = n, ''
        s['full_name'] = ' '.join(x for x in (s['last_name'], s.get('middle_name') or '', s['first_name']) if x)
    return soldiers


if __name__ == '__main__':
    run_parser(
        pdf_path='website/public/pdfs/4-banijska.pdf',
        brigade_code=20,
        output_path='website/public/4-banijska-soldiers.json',
        start_page=2,
        end_page=51,
        layout='single',
        script='latin',
        entry_start_re=ENTRY_START,
        parse_entry_fn=parse_entry,
        line_filter=keep_line,
        post_fn=post,
    )
