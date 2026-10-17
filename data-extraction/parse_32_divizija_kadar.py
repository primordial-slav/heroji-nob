"""
Parser: 32. divizija (brigade code 35) — its command, a third list.

Source: *32. divizija NOVJ* (znaci.org 00003/542, its PDF pp. 373-382)  →  website/public/pdfs/32-divizija-kadar.pdf:
        the officers of the division's staff and the units at it, and of its brigades (»Braća Radić«, »Matija Gubec«,
        »Mihovil Pavlek Miškina«, the 1. zagorska) with their battalions and escort companies: a duty on the left, the
        names run on beside it, given name first and what he was called after the surname:
    Načelnici štaba:  v.d. Vjekoslav Smeh Alibaba, Miloš Manojlović Mima, Bogdan Jovanović,
        A name can carry its own post, before it ("ratni dopisnik Zdenko Vitasović", "v.d."), after it ("Ana Adamić,
        apotekarica") or as the next item for the man before it ("Mirko Lovrec, ratni dopisnik"). The paragraph on the
        units at the division staff (PDF p. 374) sets duty and name in no one order, so its posts are typed from the
        page (TYPED). A man in several posts is one record with each; his box is around his name at each post on his
        first post's page. The roll is the unit's first list (IDs from 1), "Borci 32. divizije" from 100001; these get
        IDs from 200001. The officers of the 1. zagorska (unit 105) are linked to its records by the identity pass.
"""
import re
import sys
from pathlib import Path

import pdfplumber

import parse_8_kordunaska_divizija as k8
from _parser_scaffold import _record, run_parser
from parse_2_dalmatinska_stabovi import rows_of, spelled
from pdf_coords import viewer_words

PDF = 'website/public/pdfs/32-divizija-kadar.pdf'
UNIT = 'website/public/32-divizija-soldiers.json'
SOURCE = Path(__file__).parent / '.cache' / 'znaci_photos' / 'books' / '00003_542.pdf'   # znaci.org 00003/542.pdf
PAGES = range(373, 383)
TITLE = 'Komandni sastav 32. divizije i njenih brigada'
DIV = ('32. divizije', 'Štab 32. divizije')
# headings, spaces out and in small letters: (level, genitive, unit_detail)
HEADS = {
    'štab32.divizije': ('unit',) + DIV,
    'rukovodiociprištapskihjedinica': ('typed', '', ''),
    'udarnabrigada»braćaradić«': ('unit', 'brigade »Braća Radić«', 'brigada »Braća Radić«'),
    'štabbrigade»matijagubec«': ('unit', 'brigade »Matija Gubec«', 'brigada »Matija Gubec«'),
    'brigada»mihovilpavlekmiškina«': ('unit', 'brigade »Mihovil Pavlek Miškina«', 'brigada »Mihovil Pavlek Miškina«'),
    '1.zagorskaudarnanobrigada': ('unit', '1. zagorske brigade', '1. zagorska brigada'),
    'pratećačetabrigade': ('company', 'prateće čete', 'prateća četa'), 'pratećačeta': ('company', 'prateće čete', 'prateća četa'),
}
BAT = re.compile(r'^štab(i{1,3}|iv)bataljona:?$')
ROMAN = {'i': 1, 'ii': 2, 'iii': 3, 'iv': 4}
# the units at the division staff (PDF p. 374, "Rukovodioci prištapskih jedinica"), typed from the page:
# (surname, given name, what he was called, post)
TYPED = [
    ('Radulović', 'Božo', '', 'komandant podoficirske škole'), ('Tustić', 'Franjo', '', 'komandant podoficirske škole'),
    ('Krstanović', 'Stipe', '', 'politički komesar podoficirske škole'),
    ('Oštrolučan', 'Mićo', '', 'politički komesar podoficirske škole'),
    ('Branilović', 'Josip', '', 'zamjenik komandanta podoficirske škole'),
    ('Mikulčić', 'Marijan', '', 'komandant inžinjerijskog bataljona'),
    ('Drožđek', 'Aleksa', '', 'politički komesar inžinjerijskog bataljona'),
    ('Kušen', 'Ivica', '', 'politički komesar inžinjerijskog bataljona'),
    ('Culjaga', 'Josip', '', 'zamjenik političkog komesara inžinjerijskog bataljona'),
    ('Hadrović', 'Ivica', '', 'zamjenik komandanta inžinjerijskog bataljona'),
    ('Šebek', 'Franjo', '', 'komandir čete za vezu'), ('Babić', 'Mirko', '', 'komandir čete za vezu'),
    ('Vitez', 'Ivan', '', 'komandir čete za vezu'), ('Filipaj', 'Zlatko', '', 'politički komesar čete za vezu'),
    ('Čleković', 'Dragutin', '', 'politički komesar čete za vezu'),
    ('Bašić', 'Vid', '', 'zamjenik političkog komesara čete za vezu'),
    ('Vdović', 'Branko', '', 'komandir prateće čete'), ('Kos', 'Erika', '', 'politički komesar prateće čete'),
    ('Belia', 'Slavko', '', 'komandir izviđačke čete'), ('Milinović', 'Božo', '', 'komandir izviđačke čete'),
    ('Livić', 'Lovro', '', 'politički komesar izviđačke čete'),
    ('Bregović', 'Franjo', '', 'komandir divizijske glazbe'), ('Ligo', 'Milan', '', 'politički komesar divizijske glazbe'),
    ('Lončarić', 'Juraj', '', 'kapelnik divizijske glazbe'), ('Karuzo', 'Josip', '', 'dirigent divizijske glazbe'),
]
# a duty's words in the singular
WORDS = [(r'\bkomandanti\b', 'komandant'), (r'\bkomandiri\b', 'komandir'), (r'\bpolit[,.]? komesari?\b', 'politički komesar'),
         (r'(?<!politički )\bkomesar\b', 'politički komesar'), (r'\bzamj ?enici\b', 'zamjenik'), (r'\bpolit[,.]? komesara\b', 'političkog komesara'),
         (r'\bnačelnici\b', 'načelnik'), (r'\boficiri\b', 'oficir'), (r'\bintendanti\b', 'intendant'),
         (r'\breferenti\b', 'referent'), (r'\bliječnici\b', 'liječnik'), (r'\bađutanti\b|\badutant\b', 'ađutant'),
         (r'\bšifranti\b', 'šifrant'), (r'\bčlanovi\b', 'član'), (r'\brukovodioci\b', 'rukovodilac'), (r'\bsuci\b', 'sudac'),
         (r'\bveterinari\b', 'veterinar'), (r'\bčete\b', 'čete'), (r'\bčeta\b', 'čete'), (r'\bštaba\b', 'štaba'),
         (r'\bkomandiri četa za vezu\b', 'komandir čete za vezu'), (r'\bkomandira\b', 'komandira')]
# a label that is a body, not a duty: its members' duty and the words a role inside it takes
BODIES = {'politički odjel': ('član političkog odjela', 'političkog odjela'), 'agitprop': ('član Agitpropa', 'Agitpropa')}
ROLES = [(r'^rukovodilac\b', 'rukovodilac'), (r'^članovi\b|^član\b', 'član'), (r'^v\.?d\.?$', 'v.d.'),
         (r'^ratni dopisnik', 'ratni dopisnik'), (r'^urednik lista', 'urednik lista'), (r'^sekretar suda', 'sekretar Suda'),
         (r'^upravnici veterin', 'upravnik veterinarske ambulante'), (r'^apotekarica', 'apotekarica')]
FIX = {'Milice vic': 'Milićević', 'Senj an': 'Senjan', 'Zamj enici': 'Zamjenici',
       'Filippi Jugo': 'Jugo Filippi'}                                    # broken over the page, surname first
# one man the list prints two ways in one brigade: (surname, given name) -> (surname, given name)
SAME = {('Cikojević', 'Branislav'): ('Cikojević', 'Branimir'), ('Došen', 'Stevan'): ('Došen', 'Stevo'),
        ('Gorenc', 'Radovan'): ('Gorenec', 'Radovan')}
DUTY_START = re.compile(r'^(komandant|komandir|polit|komesar|zamj|načelni|operativni|obavještajni|intendant|referent|'
                        r'liječni|ađutant|adutant|personalni|šifrant|član|politički odjel|agitprop|oficir|suci|veterinar|'
                        r'rukovodi|3k0o8m)', re.I)
POSTS: list = []


def cut_pdf() -> None:
    from pypdf import PdfReader, PdfWriter
    r, w = PdfReader(str(SOURCE)), PdfWriter()
    for i in PAGES:
        w.add_page(r.pages[i - 1])
    with open(PDF, 'wb') as f:
        w.write(f)


def squashed(t: str) -> str:
    return t.replace(' ', '').lower()


def duty_of(label: str) -> tuple[str, str]:
    """'Polit, komesari Čete za vezu:' -> ('politički komesar čete za vezu', ''); 'Politički odjel:' -> the body's."""
    t = re.sub(r'\s+', ' ', label.strip().rstrip(':').strip(' :'))
    if t.lower().startswith('3k0o8m'):
        t = 'Komandanti'                                                 # "3K0o8m andanti:", the text layer's
    low = t[:1].lower() + t[1:]
    if low.lower() in BODIES:
        return BODIES[low.lower()]
    for p, d in WORDS:
        low = re.sub(p, d, low, flags=re.I)
    low = re.sub(r'\s*\(ujedno komandiri? četa za vezu\)', ' (ujedno komandir čete za vezu)', low)
    low = re.sub(r'\bŠtaba\b', 'štaba', low).replace('u štabu - ađutant', '').replace('oficir ađutant', 'ađutant')
    low = re.sub(r'\s+(bataljona|brigade|čete)$', '', low)
    low = re.sub(r'^(komandir|politički komesar)$', r'\1', low)
    obj = low.split(' ', 1)[1] if low.startswith('član ') else ''
    return low.strip(), obj


def items_of(words: list[dict]) -> list[list[dict]]:
    """The words of each name, at ',' and ' i ' (a comma after a duty word too)."""
    out, cur = [], []
    for w in words:
        t = w['text']
        if t in ('i', '—', '-'):
            if cur:
                out.append(cur)
            cur = []
            continue
        cur.append(w)
        if t.endswith((',', ';', '.')) and not re.fullmatch(r'(v\.d\.?|dr|polit[,.]|veterin,|ambul\.|[A-ZČĆŽŠĐ]\.)', t):
            out.append(cur)
            cur = []
    if cur:
        out.append(cur)
    return out


def person(ws: list[dict]) -> tuple[dict | None, str]:
    """A name's words -> the man and a role before or after his name ('', 'v.d.', 'ratni dopisnik')."""
    texts = [w['text'].strip(',;.:»«') for w in ws]
    text = FIX.get(' '.join(texts), ' '.join(texts))
    for a, b in FIX.items():
        text = text.replace(a, b)
    text = re.sub(r'\bdr(?=[A-ZČĆŽŠĐ])', 'dr ', text)
    role, title = '', ''
    words = text.split()
    while words and (words[0][:1].islower() or words[0] in ('v.d', 'v.d.')):
        lead = ' '.join(words)
        r = next((d for p, d in ROLES if re.match(p, lead, re.I)), None)
        if r is None:
            break
        if r == 'v.d.':
            words = words[1:]
        else:
            words = words[len(r.split()) if r not in ('upravnik veterinarske ambulante', 'član') else
                          (3 if lead.startswith('upravnici') else 1):]
        role = ', '.join(x for x in (role, r) if x)
    if words and words[0] == 'dr':
        title, words = 'dr', words[1:]
    tail = []
    while words and words[-1][:1].islower():
        tail.insert(0, words.pop())
    if tail:                                                             # a known post only, not the scan's garble
        r = next((d for p, d in ROLES if re.match(p, ' '.join(tail), re.I)), '')
        role = ', '.join(x for x in (role, r) if x)
    if not words:
        return None, role
    names = [w for w in words if re.fullmatch(r"[A-ZČĆŽŠĐ][a-zčćžšđ]+(?:-[A-ZČĆŽŠĐ][a-zčćžšđ]+)?", w)]
    if len(names) != len(words) or not 1 <= len(names) <= 3:
        return None, role
    kn = k8.known
    if len(names) == 1:
        return {'last': names[0], 'given': '', 'nicks': [], 'title': title}, role
    a, b = names[0], names[1]
    if kn(a, 'last_name') > 2 * kn(a, 'first_name') + 2 and kn(b, 'first_name') > 2 * kn(b, 'last_name') + 2 or \
            3 * kn(a, 'first_name') < kn(b, 'first_name') and 3 * kn(b, 'last_name') < kn(a, 'last_name') + 3:
        last, given, rest = a, b, names[2:]                              # "Juraković Josip", "Barić Stjepan Štef"
    elif len(names) == 3 and len(b) <= 4 and kn(b, 'last_name') < 3 <= kn(names[2], 'last_name'):
        last, given, rest = names[2], a, [b]                             # "Ivan Ico Simčić"
    else:
        last, given, rest = b, a, names[2:]                              # "Juraj Pezelj Nagari"
    nicks = rest
    if '-' in given:                                                     # "Stjepan-Stevo", "Ivan-Ico"
        given, more = given.split('-', 1)
        nicks = [more] + nicks
    return {'last': last, 'given': given, 'nicks': nicks, 'title': title}, role


def people_in(ws: list[dict]) -> list[tuple]:
    """[(man, role, words)]: two names a line's end ran together without a comma ("Božidar Milinović" / "Božo
    Starki,") are parted where the second's given name starts."""
    if ws[0]['text'].startswith('»'):                                    # "Veseljko Sokolović, »Tetak«"
        return [(None, 'zvani ' + ws[0]['text'].strip('»«,;.'), ws)]
    p, role = person(ws)
    if p is not None or role or len(ws) < 4:
        return [(p, role, ws)]
    cuts = []
    for cut in range(2, len(ws) - 1):
        a, b = person(ws[:cut]), person(ws[cut:])
        if a[0] and b[0] and a[0]['given'] and b[0]['given']:
            cuts.append((k8.known(ws[cut]['text'].strip(',;.'), 'first_name'), cut, a, b))
    if not cuts:
        return [(None, role, ws)]
    _, cut, a, b = max(cuts)
    return [(a[0], a[1], ws[:cut]), (b[0], b[1], ws[cut:])]


def lines_in_order(pdf) -> list[tuple]:
    """('head', text), ('label', text, words) and ('names', words) in reading order."""
    out = []
    for n, page in enumerate(pdf.pages, 1):
        words = [{**w, 'page': n} for w in viewer_words(page, extra_attrs=['size'])]
        rows = rows_of(words)
        lefts = sorted(round(r[0]['x0']) for r in rows if r[0]['size'] > 9)
        left = lefts[0] if lefts else 0
        starts = [round(w['x0']) for r in rows for w in r[1:] if r[0]['size'] > 9]
        firsts = sorted(round(r[0]['x0']) for r in rows if r[0]['x0'] > left + 60 and r[0]['size'] > 9)
        namex = firsts[len(firsts) // 4] - 12 if firsts else left + 120
        started = n > 1
        for r in rows:
            t = ' '.join(w['text'] for w in r)
            if not started:                                              # the hero's biography above the list
                started = squashed(t) == 'štab32.divizije'
                if not started:
                    continue
            key = squashed(t)
            if BAT.match(key) or key in HEADS:                           # some set in the body's size
                out.append(('head', t))
                continue
            if r[0]['size'] < 9:
                if r[0]['size'] > 8:
                    raise ValueError(f'heading {t!r}')
                continue
            if DUTY_START.match(t) and r[0]['x0'] >= namex:              # a row the page set further right
                k = next((i for i, w in enumerate(r) if w['text'].endswith(':')), 0) + 1
                out.append(('label', ' '.join(w['text'] for w in r[:k]), r[k:]))
                continue
            lw = [w for w in r if w['x0'] < namex]
            nw = [w for w in r if w['x0'] >= namex]
            if lw:
                out.append(('label', ' '.join(w['text'] for w in lw), nw))
            else:
                out.append(('names', nw))
    return out


def read_posts(pdf_path: str) -> None:
    with pdfplumber.open(pdf_path) as pdf:
        lines = lines_in_order(pdf)
    # a label over two lines ("Članovi Divizijskog" / "komiteta KPH:"), names before their label (p. 375's
    # "3K0o8m andanti:"): a duty with all its words
    groups, orphans = [], []
    for item in lines:
        if item[0] == 'label' and groups and groups[-1][0] == 'label' and not groups[-1][1].rstrip().endswith(':') \
                and item[1][:1].islower():
            groups[-1] = ('label', groups[-1][1] + ' ' + item[1], groups[-1][2] + item[2])
        elif item[0] == 'label':
            groups.append(('label', item[1], orphans + item[2]))
            orphans = []
        elif item[0] == 'names' and groups and groups[-1][0] == 'label':
            groups[-1] = ('label', groups[-1][1], groups[-1][2] + item[1])
        elif item[0] == 'names':
            orphans += item[1]
        else:
            groups.append(item)
    unit_gen, unit_nom, of, unit, typed = DIV[0], DIV[1], DIV[0], DIV[1], False
    for g in groups:
        if g[0] == 'head':
            key = squashed(g[1])
            m = BAT.match(key)
            if m:
                n = ROMAN[m.group(1)]
                of, unit = f'{n}. bataljona {unit_gen}', f'{n}. bataljon, {unit_nom}'
            elif key in HEADS:
                level, gen, nom = HEADS[key]
                typed = level == 'typed'
                if level == 'unit':
                    unit_gen, unit_nom, of, unit = gen, nom, gen, nom
                elif level == 'company':
                    of, unit = f'{gen} {unit_gen}', f'{nom}, {unit_nom}'
            else:
                raise ValueError(f'heading {g[1]!r}')
            continue
        if typed:
            continue
        duty, obj = duty_of(g[1])
        prev = None
        for p, role, ws in [x for item in items_of(g[2]) for x in people_in(item)]:
            if p is None:
                if role.startswith('zvani ') and prev:
                    prev['nicks'] = prev['nicks'] + [role[6:]]
                elif role and prev:                                     # "Mirko Lovrec, ratni dopisnik"
                    prev['post'] = post_of(role, obj, of)
                continue
            acting = 'v.d.' in role
            role = ', '.join(x for x in role.split(', ') if x != 'v.d.')
            post = post_of(role, obj, of) if role else f'{duty} {of}'
            last, given = spelled(p['last'], 'last_name'), spelled(p['given'], 'first_name') if p['given'] else ''
            last, given = SAME.get((last, given), (last, given))
            p = {**p, 'last': last, 'given': given,
                 'post': post + (' (v.d.)' if acting else ''), 'unit': unit, 'page': ws[0]['page'], 'words': ws}
            POSTS.append(p)
            prev = p


def post_of(role: str, obj: str, of: str) -> str:
    return ' '.join(x for x in (role, obj if role in ('rukovodilac', 'član') else '', of) if x)


def typed_posts(pdf_path: str) -> None:
    """TYPED's men, each boxed at his surname on PDF p. 374 (page 2 here)."""
    with pdfplumber.open(pdf_path) as pdf:
        words = viewer_words(pdf.pages[1])
    seen: dict = {}
    for last, given, nick, post in TYPED:
        cands = [w for w in words if w['text'].strip(',.:;').lower() == last.lower() and w['top'] > 180]   # "ligo"
        i = seen.get(last, 0)
        w = cands[min(i, len(cands) - 1)] if cands else None
        seen[last] = i + 1
        g = [v for v in words if v['text'].strip(',.') in (given, 'dr' + given) and w and abs(v['top'] - w['top']) < 3]
        ws = ([g[0]] if g else []) + ([w] if w else [])
        if not ws:
            raise ValueError(f'{last} not on the page')
        POSTS.append({'last': last, 'given': given, 'nicks': [nick] if nick else [], 'title': '',
                      'post': f'{post} {DIV[0]}', 'unit': DIV[1], 'page': 2, 'words': [{**x, 'page': 2} for x in ws]})


def extract(pdf_path: str, start_page: int, end_page: int | None) -> list[dict]:
    k8.corpus()
    read_posts(pdf_path)
    typed_posts(pdf_path)
    return [{'text': '§§post' + str(i), 'x': round(p['words'][0]['x0'], 1), 'y': round(p['words'][0]['top'], 1),
             'page': p['page']} for i, p in enumerate(POSTS)]


def parse(text: str) -> dict:
    p = POSTS[int(text[6:])]
    rec = _record(p['last'], p['given'], '', '')
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
            s['_posts'], s['_nicks'], s['_rects'], s['_title'] = [], [], [], ''
            s['unit_detail'] = p['unit']
            out.append(s)
        man['_title'] = man['_title'] or p['title']
        if p['post'] not in man['_posts']:
            man['_posts'].append(p['post'])
        for n in p['nicks']:
            if n not in man['_nicks']:
                man['_nicks'].append(n)
        if p['page'] == man['pdf_page']:
            for line in rows_of(p['words']):                            # a name broken over two lines
                man['_rects'].append([round(min(w['x0'] for w in line), 1), round(min(w['top'] for w in line), 1),
                                      round(max(w['x1'] for w in line), 1), round(max(w['bottom'] for w in line), 1)])
    for s in out:
        s['additional_info'] = '; '.join(([s['_title']] if s['_title'] else []) + [f'zvani {n}' for n in s['_nicks']]
                                         + [f"{TITLE}: {'; '.join(s['_posts'])}."])
        r = s['_rects']
        s['pdf_x'], s['pdf_y'], s['pdf_x_end'], s['pdf_y_end'] = r[0]
        if len(r) > 1:
            s['pdf_rects'] = r
        for k in ('_post', '_posts', '_nicks', '_rects', '_title'):
            s.pop(k)
    return out


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    if not Path(PDF).exists():
        cut_pdf()
    run_parser(pdf_path=PDF, brigade_code=35, output_path=sys.argv[1] if len(sys.argv) > 1 else UNIT,
               extract_fn=extract, entry_start_re=re.compile(r'^§§'), parse_entry_fn=parse, post_fn=men,
               id_start=200001, keep_other_sources=True)
