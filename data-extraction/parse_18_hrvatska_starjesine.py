"""
Parser: 18. hrvatska istočnobosanska brigada (brigade code 52) — its officers, a second list.

Source: the monograph's "Spisak starješinskog sastava brigade" (znaci.org 00001/251_4.pdf, PDF pp. 2-10, book
        pp. 573-581, just before the roster of its fighters)  →  website/public/pdfs/18-hrvatska-starjesine.pdf.
Under each staff, attached unit and company (ŠTAB BRIGADE, PRIŠTAPSKE JEDINICE BRIGADE, ŠTAB I BATALJONA, KOMANDE
ČETA / I BATALJON / 1. ČETA) a duty with a colon and its holders run on, comma after comma, surname first, a
nickname after the given name; the first holder of a post marked "na formiranju", and in the attached units each
name followed by its duty:
    Komandanti Brigade:
    Herljević Franjo, na formiranju, Janković Veljko, Kezunović Slobodan
    Prateći vod:
    Cvjetić Pejo, komandir voda na formiranju, Pavljašević Marko, zamjenik komandira voda na formiranju, ...
The book says the order of each post's holders is alphabetical, not in time. A man in several posts is one record
with each of them; his box is around his name at each post on his first post's page. The roster's records are the
unit's first list (IDs from 1); these get IDs from 10001.
"""
import json
import re
import sys
from pathlib import Path

import pdfplumber

from _parser_scaffold import _record, run_parser
from pdf_coords import viewer_words

PDF = 'website/public/pdfs/18-hrvatska-starjesine.pdf'
SOURCE = Path(__file__).parent / '.cache' / 'znaci_photos' / 'books' / '00001_251_4.pdf'   # znaci.org 00001/251_4.pdf
FIRST_PAGE, LAST_PAGE = 2, 10
TITLE = 'Spisak starješinskog sastava 18. hrvatske brigade'
U = 'A-ZČĆŽŠĐ'
# the text layer's slips, read from the page
WORDS = [('lapajner', 'Lapajner'), ('Jovanovicćć', 'Jovanović'), ('Hu sein', 'Husein'), ('Živ ković', 'Živković'),
         ('Đorde', 'Đorđe'), ('Camdžić-Božić', 'Čamdžić-Božić'), ('Čamdžić Božić', 'Čamdžić-Božić'), ('Julka Soša', 'Julka Šoša')]
UNIT_HEAD = re.compile(rf'^(?:ŠTAB [IV]+ BATALJONA|ŠTAB BRIGADE|PRIŠTAPSKE JEDINICE BRIGADE|KOMANDE ČETA|[IV]+ BATALJON|\d\. [CČ]ETA)$')
POSTS: list = []                                                             # each holder of each post, in order


def cut_pdf() -> None:
    from pypdf import PdfReader, PdfWriter
    r, w = PdfReader(str(SOURCE)), PdfWriter()
    for i in range(FIRST_PAGE - 1, LAST_PAGE):
        w.add_page(r.pages[i])
    with open(PDF, 'wb') as f:
        w.write(f)


def page_lines(page) -> list[list[dict]]:
    rows: list = []
    for w in sorted(viewer_words(page), key=lambda w: (w['top'], w['x0'])):
        row = next((r for r in rows if abs(r[0]['top'] - w['top']) <= 3), None)
        (rows.append([w]) if row is None else row.append(w))
    return [sorted(r, key=lambda w: w['x0']) for r in sorted(rows, key=lambda r: r[0]['top'])]


def unit_name(staff: str, bataljon: str, ceta: str) -> str:
    """'Štab brigade', 'Štab III bataljona', 'I bataljon, 1. četa', 'Prištapske jedinice brigade'."""
    def low(t: str) -> str:
        words = [w if re.fullmatch(r'[IV]+', w) else w.lower() for w in t.replace('CETA', 'ČETA').split()]
        return ' '.join(words)
    if ceta:
        return f'{low(bataljon)}, {low(ceta)}'
    t = low(staff)
    return t[:1].upper() + t[1:]


def read_posts(pdf_path: str) -> None:
    """POSTS: {unit, duty, name, note, page, words} for each holder, the words his name takes on the page."""
    staff = bataljon = ceta = duty = ''
    buf: list = []                                                           # the current duty's words, in order

    def flush():
        if not buf:
            return
        tokens, cur = [], []
        for w in buf:                                                        # split at commas and full stops
            t = w['text']
            end = re.search(r'[,.]$', t) and not re.fullmatch(r'dr\.?|\.\.\.', t)
            cur.append({**w, 'text': t.rstrip(',.') if end else t})
            if end:
                tokens.append(cur)
                cur = []
        if cur:
            tokens.append(cur)
        for tok in tokens:
            text = ' '.join(w['text'] for w in tok).strip()
            for a, b in WORDS:
                text = text.replace(a, b)
            if not text:
                continue
            if text[0].islower():                                            # "na formiranju", "komandir voda"
                if POSTS and POSTS[-1]['duty'] == duty:
                    POSTS[-1]['note'] = (POSTS[-1]['note'] + ', ' + text).strip(', ')
                continue
            POSTS.append({'unit': unit_name(staff, bataljon, ceta), 'duty': duty, 'name': text, 'note': '',
                          'page': tok[0]['page'], 'words': tok})
        buf.clear()

    with pdfplumber.open(pdf_path) as pdf:
        for n, page in enumerate(pdf.pages, 1):
            stop = False
            for row in page_lines(page):
                for w in row:
                    w['page'] = n
                t = ' '.join(w['text'] for w in row).strip()
                if t.startswith('*)') or stop:                               # the footnote under the first page
                    stop = True
                    continue
                if (re.fullmatch(r'\d{3}', t) or t.startswith('S P I S') or t.startswith('STARJEŠINSKOG')
                        or re.fullmatch(r'\d+ 18\. hrvatska brigada', t) or len(re.findall(rf'[a-z{U.lower()}]', t.lower())) < len(t) / 2):
                    continue
                if UNIT_HEAD.match(t):
                    flush()
                    if t.startswith('ŠTAB') or t.startswith('PRIŠTAPSKE'):
                        staff, bataljon, ceta = t, '', ''
                    elif t == 'KOMANDE ČETA':
                        staff = ''
                    elif t.endswith('BATALJON'):
                        bataljon, ceta = t, ''
                    else:
                        ceta = t
                    continue
                if re.search(r'[:.]$', t) and re.match(rf'^[{U}][a-zčćžšđ]', t) and ',' not in t and len(t.split()) <= 5:
                    flush()
                    duty = t.rstrip(':.')
                    continue
                if buf and buf[-1]['text'].endswith('-') and row[0]['text'][:1].islower():   # "Mata-" / "nović"
                    last = buf.pop()
                    row = [{**row[0], 'text': last['text'][:-1] + row[0]['text'], 'split': last}] + row[1:]
                buf.extend(row)
            flush()


def extract(pdf_path: str, start_page: int, end_page: int | None) -> list[dict]:
    read_posts(pdf_path)
    first = [p['words'][0].get('split', p['words'][0]) for p in POSTS]      # "Mata-" / "nović": where it starts
    return [{'text': '§§post' + str(i), 'x': round(f['x0'], 1), 'y': round(f['top'], 1), 'page': p['page']}
            for i, (p, f) in enumerate(zip(POSTS, first))]


def parse(text: str) -> dict:
    p = POSTS[int(text[6:])]
    name = p['name']
    title = ''
    m = re.match(r'^(\S+)\s+dr\.?\s+(.*)$', name)                           # "Goldner dr Milan"
    if m:
        name, title = f'{m.group(1)} {m.group(2)}', 'dr.'
    if name.startswith('...'):                                               # "... Jozo Dalmatinac": no surname
        last, rest = '?', name.strip('. ').split()                            # run_parser keeps only a surname's
    else:
        last, *rest = name.split()
    given, nick = (rest[0] if rest else ''), ' '.join(rest[1:])
    rec = _record(last, given, '', '')
    rec['_post'], rec['_nick'], rec['_title'] = int(text[6:]), nick, title
    return rec


def rects(words: list[dict]) -> list[list[float]]:
    """The name's words, a box a line ("Mata-" / "nović" gives two)."""
    lines: dict = {}
    for w in words:
        for part in ([w['split'], w] if 'split' in w else [w]):
            key = round(part['top'])
            box = lines.setdefault(key, [part['x0'], part['top'], part['x1'], part['bottom']])
            box[0], box[1] = min(box[0], part['x0']), min(box[1], part['top'])
            box[2], box[3] = max(box[2], part['x1']), max(box[3], part['bottom'])
    return [[round(v, 1) for v in b] for b in lines.values()]


def men(soldiers: list[dict]) -> list[dict]:
    """One record a man (surname and given name): his posts in the list's order."""
    out, seen = [], {}
    for s in soldiers:
        key = (s['last_name'], s['first_name'])
        man = seen.get(key)
        if man is None:
            man = seen[key] = s
            s['_posts'], s['_nicks'], s['_rects'] = [], [], []
            s['unit_detail'] = POSTS[s['_post']]['unit']
            out.append(s)
        p = POSTS[s['_post']]
        man['_posts'].append(f"{p['unit']}, {p['duty'][:1].lower() + p['duty'][1:]}"
                             + (f" ({p['note']})" if p['note'] else ''))
        if s['_nick'] and s['_nick'] not in man['_nicks']:
            man['_nicks'].append(s['_nick'])
        man['_title'] = man['_title'] or s['_title']
        if p['page'] == man['pdf_page']:
            man['_rects'] += rects(p['words'])
    for s in out:
        notes = ([s['_title']] if s['_title'] else []) + [f'zvani {n}' for n in s['_nicks']]
        s['additional_info'] = '; '.join(notes + [f"{TITLE}: {'; '.join(s['_posts'])}"])
        r = s['_rects']
        s['pdf_x'], s['pdf_y'], s['pdf_x_end'], s['pdf_y_end'] = r[0]
        if len(r) > 1:
            s['pdf_rects'] = r
        if s['last_name'] == '?':
            s['last_name'] = ''
        s['full_name'] = f"{s['last_name']} {s['first_name']}".strip()
        for k in ('_post', '_nick', '_title', '_posts', '_nicks', '_rects'):
            s.pop(k)
    return out


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    if not Path(PDF).exists():
        cut_pdf()
    run_parser(pdf_path=PDF, brigade_code=52, output_path=sys.argv[1] if len(sys.argv) > 1 else 'website/public/18-hrvatska-soldiers.json',
               extract_fn=extract, entry_start_re=re.compile(r'^§§'), parse_entry_fn=parse, post_fn=men,
               id_start=10001, keep_other_sources=True)
