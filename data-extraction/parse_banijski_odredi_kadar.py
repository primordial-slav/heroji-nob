"""
Ljuban Đurić, *Banijski partizanski odredi* (VINC; znaci.org 00003/549, its PDF pp. 354-360 →
website/public/pdfs/banijski-odredi-kadar.pdf, book pp. 372-378): "Pregled starješinskog kadra banijskih partizanskih
odreda 1941-1945.", a book across units: its entries are added to the records of the officers it names, the rest go to
Ostali borci (the odredi are not on the site; their men served later in the Banija brigades).

Page 372: the small odredi and village groups of 1941, two columns, a duty and its men after a dash:
    Partizanski odred »Kaline«:      komandant - Artur Turkulin, Franjo Ogulinac Seljo,
Pages 373-378: the Banijski partizanski odred and its battalions, the odredi of 1944 and their battalions, a duty and
the names run on beside it, given name first, what he was called after the surname, words broken over lines with a
hyphen ("Trni-" / "nić"):
    Komandanti:   Vasilj Gaćeša, Stanko Bjelajac Ćane, Milan Trninić Mićo, ...
A man in several posts is one entry with each of them, in the book's order (the same given name and surname). The
lists give no fate, so an entry neither dies nor lives.

Output: data-extraction/znaci/banijski-odredi-kadar-entries.json (IDs 9077xxxxxx, by each man's first post).
Usage: python data-extraction/parse_banijski_odredi_kadar.py [out.json]
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pdfplumber

sys.stdout.reconfigure(encoding='utf-8')
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from parse_2_dalmatinska_stabovi import rows_of  # noqa: E402
from pdf_coords import viewer_words  # noqa: E402

PDF = 'banijski-odredi-kadar.pdf'
SOURCE = HERE / '.cache' / 'znaci_photos' / 'books' / '00003_549.pdf'          # znaci.org 00003/549.pdf
PAGES = range(354, 361)
OUT = HERE / 'znaci' / 'banijski-odredi-kadar-entries.json'
PREFIX = '9077'
BOOK_PAGE = {p: 371 + p for p in range(1, 8)}
TITLE = 'Starješinski kadar banijskih partizanskih odreda'
# the duty's words in the singular
WORDS = [(r'\bkomandanti\b', 'komandant'), (r'\bkomandiri\b', 'komandir'), (r'\bkomesari\b', 'komesar'),
         (r'\bzamjenici\b', 'zamjenik'), (r'\bnačelnici\b', 'načelnik'), (r'\boficiri\b', 'oficir'),
         (r'\bintendanti\b', 'intendant'), (r'\breferenti\b', 'referent'), (r'\bčlanovi\b', 'član'),
         (r'obavještajno-informa- ?tivni', 'obavještajno-informativni'), (r'^zamjenik komandanta - načelnik', 'zamjenik komandanta i načelnik')]
# the scan's slips in names, read from the page
FIX = {'Zivko': 'Živko', 'Sunžnjević': 'Sužnjević', 'branko': 'Branko', 'martinović': 'Martinović', 'božo': 'Božo',
       'Cane': 'Ćane'}                                                    # p. 372 lost the accent
FOLD = str.maketrans('ČĆŽŠĐčćžšđ', 'CCZSDcczsd')


def cut_pdf() -> None:
    from pypdf import PdfReader, PdfWriter
    r, w = PdfReader(str(SOURCE)), PdfWriter()
    for i in PAGES:
        w.add_page(r.pages[i - 1])
    with open(HERE.parent / 'website' / 'public' / 'pdfs' / PDF, 'wb') as f:
        w.write(f)


def singular(label: str) -> str:
    t = re.sub(r'\s+', ' ', label.strip().rstrip(':').strip())
    t = t[:1].lower() + t[1:]
    for p, d in WORDS:
        t = re.sub(p, d, t)
    return t


def units_of(head: str, cur: dict) -> dict:
    """The unit a heading names, in the words a post takes ('1. bataljona Banijskog partizanskog odreda')."""
    h = re.sub(r'\s+', ' ', head).strip().rstrip(':').rstrip('.')
    low = h.lower()
    if low.startswith(('štab', 'stab')) and 'odreda banije' in low:
        if 'prvog' not in low and 'drugog' not in low:                   # the staff of the odred above
            return {'top': cur['top'], 'of': cur['top']}
        name = f"{'Prvog' if 'prvog' in low else 'Drugog'} partizanskog odreda Banije"
        return {'top': name, 'of': name}
    if low.startswith('dva partizanska odreda banije'):                  # the heading over the two odredi
        return cur
    m = re.match(r'^(\d)\. (?:\(([^)]*)\) )?bataljon(?: \(([^)]*)\))?(?: (Prvog|Drugog) partizanskog odreda Banije)?:?$', h)
    if m:
        top = f'{m.group(4)} partizanskog odreda Banije' if m.group(4) else cur['top']
        what = m.group(2) or m.group(3)
        return {'top': top, 'of': f"{m.group(1)}. bataljona{f' ({what})' if what else ''} {top}"}
    named = {'banijski partizanski odred': 'Banijskog partizanskog odreda',
             'novi partizanski odred banije (24. 11. 1944)': 'Partizanskog odreda Banije (od 24. 11. 1944)',
             'banijska proleterska četa': 'Banijske proleterske čete',
             'banijska partizanska četa »matija gubec«': 'Banijske partizanske čete »Matija Gubec«',
             'udarni bataljon 1. udarne brigade hrvatske (lički)': 'Udarnog bataljona 1. udarne brigade Hrvatske (ličkog)',
             'udarni bataljon banije': 'Udarnog bataljona Banije', '1. hrvatski bataljon (1943.)': '1. hrvatskog bataljona (1943)',
             '4. udarni bataljon za »banijski trokut« (1944.)': '4. udarnog bataljona za »banijski trokut« (1944)'}
    if low in named:
        return {'top': named[low] if low.startswith(('banijski', 'novi')) else cur['top'], 'of': named[low]}
    raise ValueError(f'heading {head!r}')


def genitive(unit: str) -> str:
    """Book p. 372's odredi and groups in the words a post takes: 'partizanskog odreda »Kaline«'."""
    u = re.sub(r'\s+', ' ', unit).strip().rstrip(':')
    if u == 'Sisački partizanski odred':
        return 'Sisačkog partizanskog odreda'
    m = re.match(r'^Partizanski odred (»[^«]+«)(.*)$', u)
    if m:
        return f'partizanskog odreda {m.group(1)}{m.group(2)}'.replace('(Gaćešin odred)', '(Gaćešinog odreda)')
    m = re.match(r'^Grupa (?:boraca )?sela (.+)$', u)
    if m:
        return f'grupe boraca sela {m.group(1)[:1].upper()}{m.group(1)[1:]}'
    raise ValueError(f'unit {unit!r}')


def page_one(page, n: int) -> list[tuple]:
    """Book p. 372: [(unit, duty, words)] by column, the small odredi and village groups."""
    words = [{**w, 'page': n} for w in viewer_words(page, extra_attrs=['size']) if w['size'] < 11]
    rows = rows_of(words)
    out = []
    bands, cur = [], []
    for r in rows:
        t = ' '.join(w['text'] for w in r)
        if t.startswith(('Kasnije', 'iz Bosne')):                        # the note across the page
            bands.append(cur)
            cur = []
            continue
        cur.extend(r)
    bands.append(cur)
    for band in bands:
        for col in ([w for w in band if w['x0'] < 270], [w for w in band if w['x0'] >= 270]):
            unit, pending = '', ''
            for r in rows_of(col):
                t = ' '.join(w['text'] for w in r)
                m = re.match(r'^([a-zčćžšđ ]+?) [-—] (.*)$', t)
                if m:
                    dash = next(i for i, w in enumerate(r) if w['text'] in ('-', '—'))
                    out.append([genitive(unit), m.group(1), r[dash + 1:], unit])
                elif t[:1].isupper() and not re.match(r'^[A-ZČĆŽŠĐ][a-zčćžšđ]+ [A-ZČĆŽŠĐ][a-zčćžšđ]+[,.]?$', t) \
                        and ('odred' in t or 'Grup' in t or t.startswith('(')) or t.startswith('Partizanski'):
                    unit = (pending + ' ' + t).strip() if t.startswith('(') else t
                    pending = t
                elif out and out[-1][3] == unit:
                    out[-1][2] = out[-1][2] + r                          # "Mićun,", "i Mile Joka."
    return out


def runs(pdf) -> list[tuple]:
    """[(unit 'of', duty, words)] for every duty, in the book's order."""
    out = [(u, d, ws) for u, d, ws, _ in page_one(pdf.pages[0], 1)]
    cur = {'top': 'Banijskog partizanskog odreda', 'of': 'Banijskog partizanskog odreda'}
    duty, ws, early = None, [], []                                   # early: names set above their own label
    for n, page in enumerate(pdf.pages[1:], 2):
        words = [{**w, 'page': n} for w in viewer_words(page, extra_attrs=['size'])]
        for r in rows_of(words):
            t = ' '.join(w['text'] for w in r)
            if re.fullmatch(r'\d{3}', t):
                continue
            if r[0]['size'] >= 11 or re.match(r'^Š?S?TAB [A-ZČĆŽŠĐ ]+BANIJE$', t):
                if duty:
                    out.append((cur['of'], duty, ws))
                duty, ws, early = None, [], []
                cur = units_of(t, cur)
                continue
            left = [w for w in r if w['x0'] < 205]
            right = [w for w in r if w['x0'] >= 205]
            lt = ' '.join(w['text'] for w in left)
            if left and (lt.endswith(':') or re.match(r'^(Komand|Komesar|Zamjeni|Operativ|Obavje|Informat|Intendan|'
                                                       r'Referent|Oficir|Načelni|-)', lt)):
                if duty and not duty.endswith(('-', 'informa-')) and not lt.startswith('-') and not lt[:1].islower():
                    out.append((cur['of'], duty, ws))
                    duty, ws = lt, early
                else:
                    duty = f'{duty} {lt}' if duty else lt
                    ws += early
                early = []
                ws += right
            elif ws and ws[-1]['text'].endswith('.') and not re.fullmatch(r'[A-ZČĆŽŠĐ]\.', ws[-1]['text']):
                early += r                                               # a list ends with "."; these are the next one's
            else:
                ws += early + r
                early = []
    if duty:
        out.append((cur['of'], duty, ws))
    return out


def names(words: list[dict]) -> list[tuple]:
    """[(given, surname, nick, father initial, extra, role, words)] from a run of names."""
    toks = []
    for w in words:
        t = w['text']
        if toks and toks[-1][0].endswith('-') and (t[:1].islower() or t[:1] in 'ĆČŠŽĐ' and len(toks[-1][0]) > 3
                                                     and toks[-1][0][-2:-1].islower()):
            toks[-1] = (toks[-1][0][:-1] + t, toks[-1][1] + [w])         # "Trni-" / "nić"
        else:
            toks.append((t, [w]))
    items, cur = [], []
    for t, ws in toks:
        if t in ('i', '—', '-'):
            if cur:
                items.append(cur)
            cur = []
            continue
        cur.append((t, ws))
        if re.search(r'[,.;]$', t) and not re.fullmatch(r'[A-ZČĆŽŠĐ]\.', t):
            items.append(cur)
            cur = []
    if cur:
        items.append(cur)
    out = []
    for item in items:
        texts = [FIX.get(t.strip(',.;'), t.strip(',.;')) for t, _ in item]
        ws = [w for _, wl in item for w in wl]
        role = ''
        if texts and texts[0] == 'zamjenik':                             # "Mirko Bajić, zamjenik Đuro Slavuj."
            role, texts = 'zamjenik komandanta', texts[1:]
        extra = ' '.join(t for t in texts if t.startswith('('))
        texts = [t for t in texts if not t.startswith('(')]
        if texts == ['Engel', 'Elias', 'Andžić']:                         # "Engel Elias (Ilija) Andžić"
            out.append(('Engel Elias', 'Andžić', 'Ilija', '', '', role, ws))
            continue
        father = next((t for t in texts if re.fullmatch(r'[A-ZČĆŽŠĐ]\.', t)), '')
        texts = [t for t in texts if t != father]
        if not texts or not all(re.fullmatch(r'[A-ZČĆŽŠĐ][a-zčćžšđ]+(?:-[A-ZČĆŽŠĐ][a-zčćžšđ]+)?', t) for t in texts):
            continue
        if len(texts) == 1:
            out.append(('', texts[0], '', father, extra, role, ws))
        else:
            out.append((texts[0], texts[1], ' '.join(texts[2:]), father, extra, role, ws))
    return out


def main():
    if not (HERE.parent / 'website' / 'public' / 'pdfs' / PDF).exists():
        cut_pdf()
    with pdfplumber.open(HERE.parent / 'website' / 'public' / 'pdfs' / PDF) as pdf:
        duty_runs = runs(pdf)
    people: dict[tuple, dict] = {}
    order = []
    for of, duty, ws in duty_runs:
        d = singular(duty)
        for given, last, nick, father, extra, role, w in names(ws):
            post = f"{role or d} {of}".strip()
            k = (given.translate(FOLD).lower(), last.translate(FOLD).lower())
            e = people.get(k)
            if e is None:
                e = people[k] = {'given': given, 'last': last, 'nicks': [], 'father': father, 'extra': extra,
                                 'posts': [], 'words': w}
                order.append(k)
            if nick and nick not in e['nicks']:
                e['nicks'].append(nick)
            if post not in e['posts']:
                e['posts'].append(post)
    recs = []
    for no, k in enumerate(order, 1):
        e = people[k]
        w = e['words']
        first = [x for x in w if x['page'] == w[0]['page'] and abs(x['top'] - w[0]['top']) < 4]
        nick = ', '.join(e['nicks'])
        recs.append({'soldier_id': f'{PREFIX}{no:06d}',
                     'name': ' '.join(x for x in (e['last'], e['father'], e['given']) if x) + (f' — {nick}' if nick else ''),
                     'last_name': e['last'], 'first_name': e['given'], 'also': [], 'nick': nick,
                     'fathers_name': e['father'], 'birth_year': '', 'born_in': '', 'death_year': '', 'death_date': '',
                     'death_type': '', 'survived': False, 'units': [], 'no': no, 'list': TITLE,
                     'additional_info': f"{TITLE}: {'; '.join(e['posts'])}." + (f" {e['extra']}" if e['extra'] else ''),
                     'source_page': BOOK_PAGE[w[0]['page']], 'pdf_file': PDF, 'pdf_page': w[0]['page'],
                     'pdf_x': round(min(x['x0'] for x in first), 1), 'pdf_y': round(min(x['top'] for x in first), 1),
                     # his first post's name (the PDF is in entry_boxes.INLINE_ENTRIES)
                     'pdf_x_end': round(max(x['x1'] for x in first), 1), 'pdf_y_end': round(max(x['bottom'] for x in first), 1)})
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(recs, ensure_ascii=False, indent=1), encoding='utf-8')
    print(f'{len(duty_runs)} duties, {len(recs)} men -> {out}')
    for r in recs:
        print(f"  {r['no']:3} {r['name']}: {r['additional_info'][len(TITLE) + 2:200]}")


if __name__ == '__main__':
    main()
