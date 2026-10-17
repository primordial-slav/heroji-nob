"""
Parser: 11. dalmatinska brigada (brigade code 53) — its staffs and commands, a third list.

Source: Milan Rako, Slavko Družijanić, *Jedanaesta dalmatinska udarna brigada* (znaci.org 00003/547, its PDF pp.
        599-612)  →  website/public/pdfs/11-dalmatinska-stabovi.pdf: "Pregled štabova i komandi 11. dalmatinske
        brigade", made with the brigade's surviving officers. Part I, the brigade staff with the days each held his
        post, then the units at the staff (the prateća četa, četa za vezu, inžinjerijska and vozarska četa, the NCO
        course); part II, the staffs of the battalions and the commands of their companies by duty only. A numbered
        name a line, surname first, under each duty:
    Komandanti brigade:
    1. Pecotić Bogdan, od 2. oktobra do 14. oktobra 1943.
        From the second page on, two columns: a heading across the page ("Drugi bataljon", "(od 2. 10. 1943. do
        25. 2. 1944)", "3. četa") or a note under a battalion's lists ("Ovaj bataljon je ...") starts a band, read
        left column before right; a list runs on from the left column's foot to the right column's head.
A word joined to the given name by a hyphen, or set between the surname and the given name ("Tabain Koka Antun"),
is what he was called; a word in brackets after the surname is his father. A man in several posts is one record
with each; his box is around his name at each post on his first post's page. The roll is the unit's first list
(IDs from 1), the women of Žene Hrvatske from 10001; these get IDs from 20001.
"""
import json
import re
import sys
from collections import Counter
from pathlib import Path

import pdfplumber

import parse_8_kordunaska_divizija as k8
from _parser_scaffold import _record, run_parser
from parse_2_dalmatinska_stabovi import rows_of
from pdf_coords import viewer_words

PDF = 'website/public/pdfs/11-dalmatinska-stabovi.pdf'
UNIT = 'website/public/11-dalmatinska-soldiers.json'
SOURCE = Path(__file__).parent / '.cache' / 'znaci_photos' / 'books' / '00003_547.pdf'   # znaci.org 00003/547.pdf
PAGES = range(599, 613)
TITLE = 'Pregled štabova i komandi 11. dalmatinske brigade'
BATS = {'prvi': 1, 'pri': 1, 'drugi': 2, 'treći': 3, 'četvrti': 4, 'peti': 5, 'šesti': 6}
# the units at the staff (part I) and in a battalion (part II), by the heading with its spaces taken out
ATTACHED = [(r'pratećačeta', 'prateće čete', 'prateća četa'), (r'četazavezu', 'čete za vezu', 'četa za vezu'),
            (r'inžinjerijskačeta', 'inžinjerijske čete', 'inžinjerijska četa'),
            (r'vozarskačeta', 'vozarske čete', 'vozarska četa'),
            (r'podoficirskikurspriš?tabubrigade', 'podoficirskog kursa pri štabu', 'podoficirski kurs')]
# a duty's words in the singular
WORDS = [(r'\bkomandanti\b', 'komandant'), (r'\bkomandiri\b', 'komandir'), (r'\bpolitički komesari\b', 'politički komesar'),
         (r'\bpolitkomesari?\b', 'politički komesar'), (r'\bzamjenici\b', 'zamjenik'),
         (r'\bpolitičkih komesara\b|\bpolitkomesara\b', 'političkog komesara'), (r'\bnačelnici\b', 'načelnik'),
         (r'\bobave(?:j)?štajni oficiri?\b', 'obavještajni oficir'), (r'\boficiri\b', 'oficir'),
         (r'\bomladinski rukovodioci\b', 'omladinski rukovodilac'), (r'\bsekretari\b', 'sekretar'),
         (r'\bintenda(?:nt|m)i\b', 'intendant'), (r'\breferenti\b', 'referent'), (r'\bnastavnici\b', 'nastavnik'),
         (r'\bbrigadnih previjališta\b', 'brigadnog previjališta'), (r'\bŠtaba\b', 'štaba')]
# names the print or its text layer spoiled, read from the page and the unit's roll
NAME_FIXES = {'Kris tic Luka': 'Kristić Luka', 'Matnasevic v Mate': 'Matijašević Mate',
              'Marević-Stanko Prpić': 'Marević Stanko-Prpić', 'Svrdlina Jovica': 'Svrdlin Jovica'}
SAME = {('Munitić', 'Franjo'): 'Frane'}                                    # Frane-Špica, the roll's Munitić Ivana Frane
ADDS = {('c', 'č'), ('c', 'ć'), ('s', 'š'), ('z', 'ž'), ('d', 'đ')}
NAMES: dict = {}
POSTS: list = []


def spelled(word: str, field: str) -> str:
    """The print keeps its carons; where it lost one, the spelling of the unit's own roll ("Svagelj" = Švagelj),
    never a form the roll doesn't have ("Satara", "Dokić" stay)."""
    if not NAMES:
        for s in json.load(open(UNIT, encoding='utf-8')):
            if s['soldier_id'][4:6] in ('00', '01'):
                for f in ('last_name', 'first_name'):
                    for part in s.get(f, '').split('-'):
                        NAMES.setdefault(f, Counter())[part] += 1
    names, out = NAMES[field], []
    for part in word.split('-'):
        if not names[part]:
            cands = [n for n in names if len(n) == len(part) and n != part
                     and all(a == b or (a.lower(), b.lower()) in ADDS for a, b in zip(part, n))]
            part = max(cands, key=names.get) if cands else part
        out.append(part)
    return '-'.join(out)


def cut_pdf() -> None:
    from pypdf import PdfReader, PdfWriter
    r, w = PdfReader(str(SOURCE)), PdfWriter()
    for i in PAGES:
        w.add_page(r.pages[i - 1])
    with open(PDF, 'wb') as f:
        w.write(f)


def squashed(t: str) -> str:
    return t.replace(' ', '').lower()


def is_heading(t: str) -> bool:
    s = squashed(t)
    return bool(re.fullmatch(r'(pri|prvi|drugi|treći|četvrti|peti|šesti)bataljon|\d\.četa(\d\.bataljona)?|\(od.*\)\.?|'
                             r'i{1,2}dio|pregled.*', s) or any(re.fullmatch(a[0], s) for a in ATTACHED))


def lines_in_order(pdf) -> list[tuple]:
    """('head', text) for the headings across the page, ('row', words) for a column's lines, in reading order."""
    out, prose = [], False
    for n, page in enumerate(pdf.pages, 1):
        words = [{**w, 'page': n} for w in viewer_words(page, extra_attrs=['size'])]
        if n == 1:
            words = [w for w in words if w['size'] >= 9]                  # the footnote on how the list was made
        right = sorted(w['x0'] for w in words if re.fullmatch(r'\d{1,2}\.', w['text']) and w['x0'] > 200   # a name's
                       and any(0 < v['x0'] - w['x1'] < 25 and abs(v['top'] - w['top']) < 3 and v['text'][:1].isupper()
                               and v['text'][1:2].islower() for v in words))   # number, not a date's or the title's
        split = right[len(right) // 2] - 20 if right else None
        band: list = []

        def flush():
            if not band:
                return
            cols = [band] if split is None else [[w for w in band if w['x0'] < split], [w for w in band if w['x0'] >= split]]
            for col in cols:
                for r in rows_of(col):
                    out.append(('row', r))
            band.clear()

        for r in rows_of(words):
            t = ' '.join(w['text'] for w in r)
            if is_heading(t):
                flush()
                out.append(('head', t))
                prose = False
                continue
            if t.startswith(('Ovaj ', 'Ova ', 'Napomena', 'Prateća četa je')):
                prose = True
            elif prose and (t.rstrip().endswith(':') or re.match(r'^\d{1,2}\.\s+[A-ZČĆŽŠĐ][a-zčćžšđ]', t)):
                prose = False
            if prose:
                flush()
                continue
            band.extend(r)
        flush()
    return out


def singular(label: str) -> str:
    h = label.strip().rstrip(':').strip()
    h = h[:1].lower() + h[1:]
    for p, d in WORDS:
        h = re.sub(p, d, h)
    return re.sub(r'\s+(bataljona|brigade)$', '', h)


NAME = re.compile(r'^(?P<last>[A-ZČĆŽŠĐ][a-zčćžšđ]+(?:-[A-ZČĆŽŠĐ][a-zčćžšđ]+)?)\s+(?:\((?P<father>[^)]+)\)\s+)?'
                  r'(?:(?P<title>dr)\s+)?(?P<names>[A-ZČĆŽŠĐ][^()]*?)\s*(?:\((?P<alias>[^)]+)\))?$')
NUMBER = re.compile(r'^\s*(?:\d{1,2}\s*[.•,]?|[>\\lL]\s*[.•]?)\s+(?=[A-ZČĆŽŠĐ])')


def person(text: str) -> dict | None:
    """'Jerković (Mije) Ivan-Lazarić' -> surname, father, given name, what he was called; ', st. med.' the rest."""
    text = NUMBER.sub('', text.strip()).strip()
    name, _, rest = text.partition(',')
    name = NAME_FIXES.get(name.strip(), name.strip())
    m = NAME.match(name)
    if not m:
        return None
    parts = m.group('names').split()
    if len(parts) > 2:
        return None
    nicks = [parts[0]] if len(parts) == 2 else []                        # "Tabain Koka Antun"
    given, *more = parts[-1].split('-')
    return {'last': m.group('last'), 'given': given, 'nicks': nicks + more, 'father': (m.group('father') or '').replace(' ', ''),
            'title': m.group('title') or '', 'alias': m.group('alias') or '', 'rest': rest.strip().rstrip('.,').strip()}


def read_posts(pdf_path: str) -> None:
    with pdfplumber.open(pdf_path) as pdf:
        lines = lines_in_order(pdf)
    part, duty, of, unit, last = 1, '', 'brigade', 'Štab brigade', None
    bat, of_bat, comp = 0, '', ''                                        # comp: the company in the genitive
    for kind, x in lines:
        if kind == 'head':
            s = squashed(x)
            if s == 'iidio':
                part = 2
            elif s in ('idio',) or s.startswith('pregled'):
                pass
            elif s.startswith('(od'):                                    # the period of the heading above
                period = x.strip().rstrip('.')
                if last == 'bat':
                    of_bat = of = f'{of_bat} {period}'
                else:                                                    # a company's own, not its battalion's
                    of = f"{comp} {'brigade' if part == 1 else f'{bat}. bataljona'} {period}"
            elif s.endswith('bataljon'):
                bat = BATS[s[:-len('bataljon')]]
                of_bat = of = f'{bat}. bataljona'
                unit, last = f'{bat}. bataljon', 'bat'
            elif re.match(r'\d\.četa', s):
                c, b = re.match(r'(\d)\.četa(?:(\d)\.bataljona)?', s).groups()
                if b:
                    bat, of_bat = int(b), f'{b}. bataljona'
                comp = f'{c}. čete'
                of = f'{comp} {of_bat}'
                unit, last = f'{c}. četa, {bat}. bataljon', 'company'
            else:
                a = next(a for a in ATTACHED if re.fullmatch(a[0], s))
                comp = a[1]
                of = f'{comp} brigade' if part == 1 else f'{comp} {of_bat}'
                unit = a[2] + (' brigade' if part == 1 else f', {bat}. bataljon')
                last = 'company'
            duty = ''
            continue
        t = ' '.join(w['text'] for w in x)
        if not re.search(r'[A-Za-zČĆŽŠĐčćžšđ]{2}', t):
            continue                                                     # the scan's specks
        if t.rstrip().endswith(':'):
            d = singular(t)
            if part == 1 and last is None:                               # the brigade staff
                duty = d if d.endswith(('previjališta', 'jedinica')) else f'{d} brigade'
            else:
                duty = f'{d} {of}'
            continue
        p = person(t)
        if p and duty:
            ws = [w for w in x if not NUMBER.match(w['text'] + ' A')] or x
            last_name, given = spelled(p['last'], 'last_name'), spelled(p['given'], 'first_name')
            POSTS.append({**p, 'given': SAME.get((last_name, given), given), 'last': last_name,
                          'post': f"{duty}, {p['rest']}" if p['rest'] else duty,
                          'unit': unit if part == 2 or last else 'Štab brigade', 'page': x[0]['page'], 'words': ws})


def extract(pdf_path: str, start_page: int, end_page: int | None) -> list[dict]:
    k8.corpus()
    read_posts(pdf_path)
    return [{'text': '§§post' + str(i), 'x': round(p['words'][0]['x0'], 1), 'y': round(p['words'][0]['top'], 1),
             'page': p['page']} for i, p in enumerate(POSTS)]


def parse(text: str) -> dict:
    p = POSTS[int(text[6:])]
    rec = _record(p['last'], p['given'], p['father'], '')
    rec['_post'] = int(text[6:])
    return rec


def men(soldiers: list[dict]) -> list[dict]:
    out, seen = [], {}
    for s in soldiers:
        p = POSTS[s['_post']]
        key = (k8.fold(p['last']), k8.fold(p['given']))
        man = seen.get(key)
        if man is None:
            man = seen[key] = s
            s['_posts'], s['_nicks'], s['_rects'], s['_notes'] = [], [], [], []
            s['unit_detail'] = p['unit']
            out.append(s)
        if p['father'] and not man.get('middle_name'):
            man['middle_name'] = p['father']
        if p['post'] not in man['_posts']:
            man['_posts'].append(p['post'])
        for n in p['nicks']:
            if n not in man['_nicks']:
                man['_nicks'].append(n)
        for n in ([p['title']] if p['title'] else []) + ([f"({p['alias']})"] if p['alias'] else []):
            if n not in man['_notes']:
                man['_notes'].append(n)
        if p['page'] == man['pdf_page']:
            ws = p['words']
            man['_rects'].append([round(min(w['x0'] for w in ws), 1), round(min(w['top'] for w in ws), 1),
                                  round(max(w['x1'] for w in ws), 1), round(max(w['bottom'] for w in ws), 1)])
    for s in out:
        s['additional_info'] = '; '.join(([' '.join(s['_notes'])] if s['_notes'] else [])
                                         + [f'zvani {n}' for n in s['_nicks']] + [f"{TITLE}: {'; '.join(s['_posts'])}."])
        r = s['_rects']
        s['pdf_x'], s['pdf_y'], s['pdf_x_end'], s['pdf_y_end'] = r[0]
        if len(r) > 1:
            s['pdf_rects'] = r
        s['full_name'] = ' '.join(x for x in (s['last_name'], s['middle_name'], s['first_name']) if x)
        for k in ('_post', '_posts', '_nicks', '_rects', '_notes'):
            s.pop(k)
    return out


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    if not Path(PDF).exists():
        cut_pdf()
    run_parser(pdf_path=PDF, brigade_code=53, output_path=sys.argv[1] if len(sys.argv) > 1 else UNIT,
               extract_fn=extract, entry_start_re=re.compile(r'^§§'), parse_entry_fn=parse, post_fn=men,
               id_start=20001, keep_other_sources=True)
