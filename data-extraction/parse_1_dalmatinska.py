"""
Parser: 1. dalmatinska proleterska NOU brigada (brigade code 36) — the fallen.

Source: Mirko Novović, "Prva dalmatinska proleterska brigada", chapter "Spisak boraca Prve dalmatinske proleterske
        NOU brigade poginuli u toku narodnooslobodilačkog rata", published by znaci.org only as a web page:
        https://znaci.org/00001/32_1.htm  →  data-extraction/sources/1-dalmatinska-poginuli.htm (a saved copy)
2,165 numbered entries, A-Ž, one paragraph each:
    1. Acalija I. Ante, rođen 1921. godine u Sinju, borac 1 bat, poginuo u V ofanzivi.
    8. Alaber Antun "Pubo", rođen u SIavonskom Brodu, delegat voda IV bat, poginuo u IV ofanzivi, marta 1943. godine.
SURNAME, the father's initial, the given name (and a nickname in quotes), then the bio. There is no scan: the
records carry `source_url` (the list on znaci.org) instead of a PDF position.
"""
import html
import json
import re
from collections import Counter
from pathlib import Path

from _parser_scaffold import _record, repair_lj_ocr, restore_diacritics, run_parser

SOURCE = 'data-extraction/sources/1-dalmatinska-poginuli.htm'
SOURCE_URL = 'https://znaci.org/00001/32_1.htm'
MARK = '⁣'
U, L = 'A-ZČĆŽŠĐ', 'a-zčćžšđ'


def read_entries(path: str, start: int, end: int | None) -> list[dict]:
    """One line per numbered entry. Three numbers lack their space ("215.'Boban", "1433.r)n. Novak") and one
    entry is glued to the end of the one before ("... decembra 1942. godine,652. Glučina J. David", no. 658)."""
    text = html.unescape(re.sub(r'<[^>]+>', '\n', Path(path).read_text(encoding='utf-8')))
    paras = [p.strip() for p in text.split('\n') if re.match(r'^\s*\d{1,4}\.', p)]
    out, expect = [], 1
    for p in paras:
        m = re.match(r'^(\d{1,4})\.\W*(?:[a-z]\)?\w?\.\s*)?', p)          # "1433.r)n. Novak"
        num, body = int(m.group(1)), p[m.end():]
        parts = [(num, body)]
        glued = re.search(rf'(?<=[,.])\s?(\d{{3,4}})\.\s*(?=[{U}][{L}]+ )', body)
        if glued and abs(int(glued.group(1)) - (num + 1)) <= 10:
            parts = [(num, body[:glued.start()]), (num + 1, body[glued.end():])]
        for n, b in parts:
            out.append({'text': MARK + b.strip(), 'x': 0, 'y': float(len(out)), 'page': 1, 'num': n})
            expect = n + 1
    return out


INITIAL = rf'(?:[{U}][{L}]?|0)\.?'


def parse_entry(text: str) -> dict:
    """Surname [Family name] [F.] Given ["Nick" | — Nick | Nick], bio"""
    text = text.replace(MARK, '').strip()
    text = re.sub(rf'\b([{U}])I(?=[{L}])', r'\1l', text)                 # "VIado", "SIavonskom": l read as I
    text = re.sub(rf'\s,\s*({INITIAL})\s', r' \1 ', text)               # "Begović ,T. Damjan"
    text = re.sub(rf'^(\S+(?: \S+)? [{U}])\s*,\s*(?=[{U}][{L}]+[,;])', r'\1. ', text)   # "Korljan J, Milan,"
    text = re.sub(rf'^(\S+)\.\s+(?=[{U}])', r'\1 ', text)                # "Mrđen. Srećko"
    # the name ends at a comma, a semicolon, ">" (a comma misread), a full stop before "rođen", or "rođen"/"iz"
    end = re.search(r'[,;>]|\.(?=\s*rođen)|\s(?=rođen[a]?\s|iz\s)', text)
    head, bio = (text[:end.start()], text[end.end():].strip(' ,;')) if end else (text, '')
    notes = [f'zvani {n}' for n in re.findall(r'["„“”]([^"„“”]+)["„“”]?', head)]
    head = re.sub(r'\s*["„“”][^"„“”]*["„“”]?', '', head)
    dash = re.search(r'\s[—–-]\s(?!(?:I|[A-Z])\.)(\S.*)$', head)             # "Ante — Toni": a nickname
    if dash:
        notes.append('zvani ' + dash.group(1))
        head = head[:dash.start()]
    head = re.sub(r'\s[—–-]\s', ' ', head)                                # "Kustro — I. Ivan"
    head = re.sub(r'(?<=\w)[—–](?=\w)', '-', head)                         # "Čičin—Sain"
    if re.search(r'\s[Dd]r\.?(?=\s|$)', head):                           # "Žunković D. dr Orest"
        notes.insert(0, 'dr.')
        head = re.sub(r'\s[Dd]r\.?(?=\s|$)', '', head)
    # ".P." an initial between specks, "Ali.ja" a speck inside a name
    toks = [t.strip('.') + '.' if re.fullmatch(INITIAL, t.strip('.') + '.') else t.replace('.', '') for t in head.split()]
    toks = [re.sub(rf'^([{U}][{L}]+)([{U}][{L}]+)$', r'\1-\2', t) for t in toks]   # "KljakovićGašpić", "MatijaMešara"
    last = toks[0] if toks else ''
    rest = toks[1:]
    # a second surname or family name before the father's initial ("Separović Markota I. Petar"), or ending as a
    # surname before the given name ("Eterović Sorić Ante")
    if len(rest) >= 3 and re.fullmatch(rf'[{U}][{L}]{{2,}}', rest[0]) and re.fullmatch(INITIAL, rest[1]) \
            or len(rest) == 2 and re.search(r'(?:ić|ov|ev)$', rest[0]) and re.fullmatch(rf'[{U}][{L}]+', rest[1]):
        last = last + ' ' + rest.pop(0)
    father = ''
    if len(rest) >= 2 and re.fullmatch(INITIAL, rest[0]):                 # "I. Ante", "L Mira", "0. Đuro"
        father = rest.pop(0).rstrip('.').replace('0', 'O')
    given = rest[0] if rest else ''
    if '-' in given and not re.search(r'(?:ić|vić)-', given):            # "Matija-Mešara": a glued nickname
        given, nick = given.split('-', 1)
        notes.append('zvani ' + nick)
    notes += ['zvani ' + ' '.join(rest[1:])] if len(rest) > 1 else []   # "Drago Bagatela"
    bio = re.sub(r'(?<=\.)[\s.,\d]+$', '', bio).strip()                  # ". .1.4." at the end
    return _record(last, given, father, '; '.join(notes + ([bio] if bio else [])))


def fix_given(soldiers: list[dict]) -> list[dict]:
    """A given name the corpus doesn't know takes the best-known spelling one usual misread gives
    ("Jnre" → Jure, "Menmed" → Mehmed, "Arrte" → Ante)."""
    first = Counter()
    for f in Path('website/public').glob('*soldiers.json'):
        if f.name != '1-dalmatinska-soldiers.json':
            first.update(s['first_name'] for s in json.loads(f.read_text(encoding='utf-8')))
    subs = [('n', 'u'), ('u', 'n'), ('rr', 'n'), ('ir', 'n'), ('r', 'n'), ('rn', 'm'), ('m', 'rn'), ('n', 'h'), ('h', 'n'),
            ('c', 'e'), ('e', 'c'), ('i', 'l'), ('l', 'i'), ('I', 'L'), ('o', 'a'), ('a', 'o'), ('t', 'l')]
    for s in soldiers:
        g = s['first_name']
        if not g or first[g] >= 2:
            continue
        cands = {g[:m.start()] + b + g[m.end():] for a, b in subs for m in re.finditer(re.escape(a), g)}
        if g[0].islower():                                            # "nušan": the capital misread
            cands |= {c + g[1:] for c in 'ABCČĆDĐEFGHIJKLMNOPRSŠTUVZŽ'}
        best = max(cands, key=lambda c: first[c], default=None)
        if best and first[best] >= 10:
            s['first_name'] = best
            s['full_name'] = ' '.join(p for p in (s['last_name'], s['middle_name'], s['first_name']) if p)
    return soldiers


def post(soldiers: list[dict]) -> list[dict]:
    for s in soldiers:
        for k in ('pdf_page', 'pdf_y', 'pdf_x', 'pdf_y_end', 'pdf_file'):
            s.pop(k, None)
        s['source_url'] = SOURCE_URL
    return fix_given(repair_lj_ocr(restore_diacritics(soldiers)))


if __name__ == '__main__':
    run_parser(
        pdf_path=SOURCE,
        brigade_code=36,
        output_path='website/public/1-dalmatinska-soldiers.json',
        start_page=1,
        end_page=1,
        script='latin',
        extract_fn=read_entries,
        entry_start_re=re.compile('^' + MARK),
        parse_entry_fn=parse_entry,
        post_fn=post,
    )
