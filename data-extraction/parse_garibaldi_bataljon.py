"""
Parser: Prva proleterska brigada (brigade code 1) — the members of its battalion "Garibaldi".

Source: "Prva proleterska brigada", knjiga 4, "Spisak pripadnika bataljona »Garibaldi« Prve proleterske
        narodnooslobodilačke udarne brigade" (znaci.org 00001/97, chapter 97_5.pdf, book pp. 1072-1082)  →
        website/public/pdfs/prva-proleterska-garibaldi.pdf. The battalion of Italian soldiers who joined the
        partisans after Italy's capitulation in September 1943. Two columns, all in capitals, the staff first, a duty
        after some names, broken over the next line:
    ŠTAB BATALJONA
    ELIA FRANCESCO, komandant
    ARONICA GIOVANNI, zame-
    nik komandira čete
Most of them stand in the brigade's roster too, with a bio; this list gives the battalion. A word the OCR broke apart
("BAD INI", "BALD AN", "SA VETA") is joined where the joined spelling is a name the site's records have and the
pieces aren't; a Yugoslav's third name is a nickname ("VUJOŠEVIĆ JOVAN LOLA"), an Italian's a second given name.
These get IDs from 800001.
"""
import glob
import json
import re
import sys
from collections import Counter

import pdfplumber

from _parser_scaffold import _record, run_parser
from pdf_coords import viewer_words

PDF = 'website/public/pdfs/prva-proleterska-garibaldi.pdf'
U = 'A-ZČĆŽŠĐÀÈÉÌÒÙ'
TITLE = 'Spisak pripadnika bataljona »Garibaldi« Prve proleterske brigade'
WORDS = [('AMADORIAMATORINO', 'AMADORI AMATORINO'), ('Gì ANN ANDRE A GIOVANNI', 'GIANNANDREA GIOVANNI'), ('INSEL VINI', 'INSELVINI'),
         ('MOGA VERO', 'MOGAVERO'), ('PE ANDORA', 'PEANDORA'), ('RA VASI', 'RAVASI'), ('BAD INI', 'BADINI'), ('BALD AN', 'BALDAN'),
         ('BOMB IERI', 'BOMBIERI'), ('GIOVAN NI', 'GIOVANNI'), ('SAL VINELLI', 'SALVINELLI'), (' /', ''), (" '", '')]
KNOWN: Counter = Counter()
STAFF = {'s': False}


def corpus() -> None:
    for f in glob.glob('website/public/*soldiers.json'):
        for s in json.load(open(f, encoding='utf-8')):
            for k in ('last_name', 'first_name'):
                for w in (s.get(k) or '').split():
                    KNOWN[w.upper()] += 1


PARTICLES = {'DE', 'DI', 'DA', 'DAL', 'DALLA', 'DALL', 'DEL', 'DELLA', 'DELL', 'D', 'LA', 'LO', 'LI', 'LE'}


def join_broken(words: list[str]) -> list[str]:
    """'BAD INI' -> 'BADINI', 'DOMENI CUCCI' -> 'DOMENICUCCI': two pieces joined where the site knows the whole and not
    both pieces, or one piece is too short to be a name; a surname's particle stays apart ('DE CAROLIS')."""
    out = []
    for w in words:
        prev = out[-1] if out else ''
        whole = prev + w
        short = bool(out) and (len(w) <= 3 or len(prev) <= 3) and prev not in PARTICLES and len(out) == 1 + (out[0] in PARTICLES)
        if prev and (KNOWN[whole] and not (KNOWN[prev] and KNOWN[w]) or short and not KNOWN[w]):
            out[-1] = whole
        else:
            out.append(w)
    return out


def column_lines(words: list[dict], n: int) -> list[dict]:
    rows: list = []
    for w in sorted(words, key=lambda w: (w['top'], w['x0'])):
        row = next((r for r in rows if abs(r[0]['top'] - w['top']) <= 3), None)
        (rows.append([w]) if row is None else row.append(w))
    out = []
    for r in sorted(rows, key=lambda r: r[0]['top']):
        r.sort(key=lambda w: w['x0'])
        out.append({'text': ' '.join(w['text'] for w in r), 'x': round(r[0]['x0'], 1), 'y': round(r[0]['top'], 1), 'page': n})
    return out


def read_lines(pdf_path: str, start_page: int, end_page: int | None) -> list[dict]:
    """Each page's header across the page (page 1: the title and the staff), then its two columns, split at the
    widest gap between them (the margins alternate)."""
    out = []
    with pdfplumber.open(pdf_path) as pdf:
        for n, page in enumerate(pdf.pages, 1):
            ws = viewer_words(page)
            top = min((w['top'] for w in ws if w['text'] == 'ABBONATO'), default=0) if n == 1 else 0
            head, body = [w for w in ws if w['top'] < top - 2], [w for w in ws if w['top'] >= top - 2]
            occ = set()
            for w in body:
                occ.update(range(int(w['x0']), int(w['x1']) + 1))
            gaps, start = [], None
            for x in range(150, 280):
                if x not in occ and start is None:
                    start = x
                if x in occ and start is not None:
                    gaps.append((x - start, (start + x) / 2))
                    start = None
            split = max(gaps)[1] if gaps else page.width / 2
            out += column_lines(head, n)
            out += column_lines([w for w in body if w['x0'] < split], n)
            out += column_lines([w for w in body if w['x0'] >= split], n)
    return out


def keep(ln: dict) -> bool:
    t = ln['text'].strip()
    if re.fullmatch(r"'?\d{4}", t) or t.startswith('Spisak pripadnika') or t in (
            'prve proleterske narodnooslobodilačke', 'udarne brigade'):
        return False
    for a, b in WORDS:
        t = t.replace(a, b)
    if t == 'ŠTAB BATALJONA':
        STAFF['s'] = True
        return False
    # "D ALESSANDRO COSIMO", "DIAZ don CARLO", "TINTOR-TUMBAS BOSILJKA", "SAVOROLAC-PARMIĐA-" (the rest lost)
    m = re.match(rf"^(?:D'?\s*)?[{U}]{{2,}}(?:-[{U}]+)*(?:\s+(?:[{U}]+|don)\b)+|^[{U}]{{2,}}-[{U}]+-$", t)
    ln['text'] = ('§§' + ('s' if STAFF['s'] else 'm') + ' ' + t) if m else t
    if m and STAFF['s'] and ln['page'] == 1 and re.match(r'^ABBONATO', t):
        STAFF['s'] = False                                                   # the members start, alphabetically
        ln['text'] = '§§m ' + t
    return True


def parse(text: str) -> dict:
    staff = text[2] == 's'
    text = text[4:]
    text = re.sub(r'(?<=[a-zčćžšđ])-\s+(?=[a-zčćžšđ])', '', text)          # "zame- nik"
    # a word broken over the line, "MICHELANGE- LO", "ANTO-NIO"; not a double surname, "TINTOR-TUMBAS"
    text = re.sub(rf'(?<=[{U}])-(?:\s+|(?=[{U}]{{1,3}}\b))(?=[{U}])', '', text)
    head, _, duty = text.partition(',')
    m = re.search(r'[(]([^)]*)[)]', head)                                  # "GIUPPANI ANTONIO (bivši ital. poručnik)"
    if m:
        head, duty = head[:m.start()] + head[m.end():], (m.group(1) + (', ' + duty if duty else ''))
    title = 'don' if ' don ' in f' {head} ' else ''                           # "DIAZ don CARLO": a priest
    head = head.replace(' don ', ' ')
    head = head.replace('GIOVAN NI', 'GIOVANNI')
    words = join_broken(head.strip(' -').split())
    k = 1
    while k < len(words) - 1 and words[k - 1] in PARTICLES:              # "DE CAROLIS", "DELLA PENNA", "D ALESSANDRO"
        k += 1
    last = ' '.join(w.title() for w in words[:k])
    last = re.sub(r"^(D|Dell|Dall) (?=[A-Z])", lambda m: m.group(1) + "'", last)    # D'Alessandro, Dell'Alma
    rest = [w.title() for w in words[k:]]
    nick = ''
    if (re.search(r'(?:ić|ič)$', last) or last in ('Tintor-Tumbas', 'Jurica')) and len(rest) > 1:   # "VUJOŠEVIĆ JOVAN LOLA"
        nick, rest = ' '.join(rest[1:]), rest[:1]
    duty = duty.strip(' ,.')
    notes = ([title] if title else []) + ([f'zvani {nick}'] if nick else []) + [TITLE + (', štab bataljona' if staff else '') + (f': {duty}' if duty else '')]
    rec = _record(last, ' '.join(rest), '', '; '.join(notes))
    rec['unit_detail'] = 'Bataljon »Garibaldi»'.replace('»Garibaldi»', '»Garibaldi«') + (', štab' if staff else '')
    return rec


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    corpus()
    run_parser(pdf_path=PDF, brigade_code=1, output_path=sys.argv[1] if len(sys.argv) > 1 else 'website/public/prva-proleterska-soldiers.json',
               extract_fn=read_lines, entry_start_re=re.compile(r'^§§'), parse_entry_fn=parse,
               line_filter=keep, id_start=800001, keep_other_sources=True)
