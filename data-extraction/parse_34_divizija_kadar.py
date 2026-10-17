"""
Parser: 34. divizija (brigade code 97) — its command, a second list.

Source: Vladimir Hlaić, *34. udarna divizija* (znaci.org 00003/641, its PDF pp. 407-417, book pp. 389-399)
        →  website/public/pdfs/34-divizija-kadar.pdf: "Vojno i političko-partijsko rukovodstvo 34. udarne divizije
        4. korpusa NOVJ", the officers of the division's staff, committee, political department, intendantura and
        sanitet, of its brigades (»Franjo Ogulinac Seljo«, the 16. omladinska »Joža Vlahović«, the Karlovačka, the
        Žumberačka), the partisan odredi and the units at the division staff: a duty on the left, the names run on
        beside it, given name first, surname in capitals, a list ending with ";" or ".":
    Komesari        Drago GOVORUŠIĆ, Franjo KNEBL;
    Komandanti      1. bat.: Pavao RADOVIĆ, Jovo ROMANIĆ, ...
        A unit's heading is set large, its parts ("ŠTAB BRIGADE", "Četa za vezu", "1. Baterija") on the duties'
        left edge; HEADS gives each the words its posts take. A man in several posts is one record with each; his box
        is around his name at each post on his first post's page. The fallen are the unit's first list (IDs from 1);
        these get IDs from 10001. The officers of the Karlovačka (unit 94) and the Turopoljsko-posavski odred (149)
        are linked to their own units' records by the identity pass.
"""
import re
import sys
from pathlib import Path

import pdfplumber

import parse_8_kordunaska_divizija as k8
from _parser_scaffold import _record, run_parser
from parse_2_dalmatinska_stabovi import rows_of, spelled
from pdf_coords import viewer_words

PDF = 'website/public/pdfs/34-divizija-kadar.pdf'
UNIT = 'website/public/34-divizija-soldiers.json'
SOURCE = Path(__file__).parent / '.cache' / 'znaci_photos' / 'books' / '00003_641.pdf'   # znaci.org 00003/641.pdf
PAGES = range(407, 418)
TITLE = 'Vojno i političko-partijsko rukovodstvo 34. udarne divizije'
DIV = ('34. divizije', '34. divizija')
# a heading, its spaces taken out and in small letters: (level, genitive, nominative); a unit's heading starts a new
# unit, a section its part, a subsection a part of that
HEADS = {
    'vojnoipolitičko-partijskorukovodstvo34.udarnedivizije4.korpusanovj': ('unit',) + DIV,
    'brigada“franjoogulinacseljo”': ('unit', 'brigade »Franjo Ogulinac Seljo«', 'brigada »Franjo Ogulinac Seljo«'),
    '16.omladinskabrigada“jožavlahović”': ('unit', '16. omladinske brigade »Joža Vlahović«',
                                          '16. omladinska brigada »Joža Vlahović«'),
    'udarnakarlovačkabrigada': ('unit', 'Karlovačke brigade', 'Karlovačka brigada'),
    'žumberačkanoubrigada': ('unit', 'Žumberačke brigade', 'Žumberačka brigada'),
    'narodno-oslobodilačkipartizanskiodredi': ('none', '', ''),
    '1.žumberačko-pokupskinopodred': ('unit', '1. Žumberačko-pokupskog NOP odreda', '1. Žumberačko-pokupski NOP odred'),
    '2.karlovačkinopodred(prviidrugisastav)': ('unit', '2. Karlovačkog NOP odreda', '2. Karlovački NOP odred'),
    '3.turopoljsko-posavskinopodred': ('unit', '3. Turopoljsko-posavskog NOP odreda', '3. Turopoljsko-posavski NOP odred'),
    '4.samoborsko-jaskanskinopodred': ('unit', '4. Samoborsko-jaskanskog NOP odreda', '4. Samoborsko-jaskanski NOP odred'),
    '5.posavskinopodred': ('unit', '5. Posavskog NOP odreda', '5. Posavski NOP odred'),
    'samostalnejediniceprištabu34.udarnedivizije': ('unit',) + DIV,
    'štabdivizije': ('sec', ''), 'stabdivizije': ('sec', ''), 'štabbrigade': ('sec', ''), 'stabbrigade': ('sec', ''),
    'divizijskikomitetkpj': ('sec', 'divizijskog komiteta KPJ'), 'političkiodjel': ('sec', 'političkog odjela'),
    'intendantura': ('sec', 'intendanture'), 'sanitet': ('sec', 'saniteta'),
    'komandebataljona': ('sec', 'bataljona'), 'bataljoni': ('sec', 'bataljona'),
    'pratećačeta': ('sec', 'prateće čete'), 'četazavezu': ('sec', 'čete za vezu'),
    'inzinjerijskaceta': ('sec', 'inžinjerijske čete'), 'inžinjerijskačeta': ('sec', 'inžinjerijske čete'),
    'inžinjerskačeta': ('sec', 'inžinjerijske čete'), 'izviđačkivod': ('sec', 'izviđačkog voda'),
    'minerskivod': ('sec', 'minerskog voda'), 'sanitetskivod': ('sec', 'sanitetskog voda'),
    'vodjurišnihpionira': ('sec', 'voda jurišnih pionira'), 'pozadina': ('sec', 'pozadine'),
    'artiljerijskidivizion': ('sec', 'artiljerijskog diviziona'), 'inžinjerijskibataljon': ('sec', 'inžinjerijskog bataljona'),
    'četazavezudivizije': ('sec', 'čete za vezu'), 'izviđačkačetadivizije': ('sec', 'izviđačke čete'),
    'vojnaškoladivizije': ('sec', 'vojne škole'), 'dopunskibataljon': ('sec', 'dopunskog bataljona'),
    'autočetadivizije': ('sec', 'auto čete'),
    '1.baterija': ('sub', '1. baterije'), '2.baterija': ('sub', '2. baterije'), '3.baterija': ('sub', '3. baterije'),
    'štab': ('sub', ''), '1.pionirskačeta': ('sub', '1. pionirske čete'), '2.pontonirskačeta': ('sub', '2. pontonirske čete'),
    '3.minerskačeta': ('sub', '3. minerske čete'),
}
# the duty's first word, by the label's first word in small letters
DUTIES = [('komandant', 'komandant'), ('komandir', 'komandir'), ('komesar', 'komesar'), ('zamj', 'zamjenik'),
          ('načelni', 'načelnik'), ('operativni', 'operativni oficir'), ('obavještajni', 'obavještajni oficir'),
          ('informativni', 'informativni oficir'), ('intendant', 'intendant'), ('sanitet', 'referent saniteta'),
          ('referent', 'referent saniteta'), ('omladinski', 'omladinski rukovodilac'), ('rukovodioci', 'rukovodilac SKOJ-a'),
          ('rukovodilac', 'rukovodilac'), ('sekretar', 'sekretar'), ('član', 'član'), ('pomočni', 'pomoćnik'),
          ('pomoćni', 'pomoćnik'), ('delegat', 'delegat'), ('ađutant', 'ađutant'), ('oficiri', 'oficir OZN-e')]
# labels that name their own object: the section's words don't follow them
OWN = {'intendant prehrane', 'intendant odjevne grupe', 'intendant garnizone grupe', 'komesar prihvatne bolnice',
       'komandir komore', 'komandir bojne komore', 'komesar bojne komore', 'oficir OZN-e', 'rukovodilac SKOJ-a',
       'omladinski rukovodilac', 'operativni oficir', 'obavještajni oficir', 'informativni oficir', 'referent saniteta'}
# names the text layer spoiled, by the surname as printed (given names checked on the page)
LAST_FIXES = {'MEJAŠK1': 'MEJAŠKI', 'HRNNJAK': 'HRNJAK', 'PREDANIC': 'PREDANIĆ', 'DOBROSAVLJEVIČ': 'DOBROSAVLJEVIĆ'}
GIVEN_FIXES = {'Milutun': 'Milutin'}
SAME = {('Grčić', 'Danijel'): 'Daniel'}                                   # one man, printed both ways in the FOS's lists
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


def duty_of(label: str) -> str:
    """'Zamj. k-danta bataljona' -> 'zamjenik komandanta'; 'Intendant garnizone gr.' -> 'intendant garnizone grupe'."""
    t = label.strip().rstrip(':').strip()
    low = t.lower()
    first = next(d for p, d in DUTIES if low.startswith(p))
    rest = low.split(' ', 1)[1] if ' ' in low else ''
    rest = (rest.replace('k-danta', 'komandanta').replace('gr.', 'grupe').replace('prihv.', 'prihvatne')
            .replace('ofiviri', 'oficiri'))
    rest = re.sub(r'\s*(bataljona|komiteta)$', '', rest)
    if first in ('operativni oficir', 'obavještajni oficir', 'informativni oficir', 'omladinski rukovodilac',
                 'referent saniteta', 'rukovodilac SKOJ-a', 'oficir OZN-e'):
        return first
    if first == 'zamjenik':
        return f'zamjenik {rest}'.strip()
    if first == 'načelnik' and rest.startswith('štab'):
        return 'načelnik štaba'
    return f'{first} {rest}'.strip()


def is_label(text: str) -> bool:
    low = text.lower()
    return any(low.startswith(p) for p, _ in DUTIES) and not low.startswith(('sanitetski', 'komande'))


CAPS = r"[A-ZČĆŽŠĐ][A-ZČĆŽŠĐ1-]*"


def people(words: list[dict]) -> list[tuple]:
    """The run-on names of one duty: [(battalion or None, given, SURNAME, nick, words)]."""
    toks = []                                                            # (text, word, ends a name)
    for w in words:
        for part in re.split(r'(?<=,)(?=\S)', w['text']):                # "SAVNIK,Vjekoslav"
            if re.fullmatch(r'\d\.(bat\.:?)?', part):                     # "1." of "1. bat.:", "4.bat.:"
                toks.append((part, w, False))
                continue
            end = bool(re.search(r'[,;.]$', part))
            toks.append((part.rstrip(',;.'), w, end))
    out, bat, cur = [], None, []

    def flush():
        nonlocal cur
        if not cur:
            return
        texts = [t for t, _, _ in cur if t and t != '-']
        given = [t for t in texts if not re.fullmatch(CAPS, t)]
        caps = [t for t in texts if re.fullmatch(CAPS, t)]
        if caps:
            surname, nick = caps[0], ''
            for c in caps[1:]:                                           # "POP AR A", "LUČ AN": the spaced surname
                if len(c) <= 3 or surname.endswith('-'):
                    surname += c
                else:                                                    # "ŠKRINJAR FEDA", "TABOR - RAFKO"
                    nick = c
            surname = LAST_FIXES.get(surname, surname)
            out.append((bat, ' '.join(given[:1]), surname, nick, [w for _, w, _ in cur]))
        cur = []

    i = 0
    while i < len(toks):
        t, w, end = toks[i]
        if re.fullmatch(r'\d\.', t) and i + 1 < len(toks) and toks[i + 1][0].startswith('bat'):
            flush()
            bat = int(t[0])
            i += 2
            continue
        if re.fullmatch(r'\d\.bat\.:?', t):                               # "4.bat.:", "2.bat.:"
            flush()
            bat = int(t[0])
            i += 1
            continue
        if t == 'i':
            flush()
            i += 1
            continue
        if not cur and re.fullmatch(CAPS, t) is None and cur == [] and out and t and t[0].islower():
            i += 1
            continue
        cur.append((t, w, end))
        # a comma after the given name only ("Milan, KRALJ") doesn't end the man
        if end and any(re.fullmatch(CAPS, x) for x, _, _ in cur):
            flush()
        i += 1
    flush()
    return out


def lines_in_order(pdf) -> list[tuple]:
    """('head', text), ('label', text, words) and ('names', words) in reading order."""
    out = []
    for n, page in enumerate(pdf.pages, 1):
        words = [{**w, 'page': n} for w in viewer_words(page, extra_attrs=['size'])]
        rows = rows_of(words)
        big: list = []
        for r in rows:
            t = ' '.join(w['text'] for w in r)
            if r[0]['size'] >= 13:                                       # a unit's heading, on one or more lines
                big.append(t)
                continue
            if big:
                out.append(('head', ' '.join(big)))
                big = []
            if r[0]['size'] < 8 or t.startswith('Napomena'):
                if t.startswith('Napomena'):
                    return out
                continue
            if squashed(t) in HEADS:
                out.append(('head', t))
            elif is_label(t):                                            # the duty: its first word and the small
                k = 1                                                    # words after it ("Zamj. k-danta bataljona")
                while k < len(r) and (r[k]['text'][:1].islower() or r[k]['text'] in ('OZN-e', 'SKOJ-a')):
                    k += 1
                out.append(('label', ' '.join(w['text'] for w in r[:k]), r[k:]))
            else:
                out.append(('names', r))
        if big:
            out.append(('head', ' '.join(big)))
    return out


def read_posts(pdf_path: str) -> None:
    with pdfplumber.open(pdf_path) as pdf:
        lines = []
        for item in lines_in_order(pdf):                                 # a duty with all its lines of names
            if item[0] == 'names' and lines and lines[-1][0] == 'label':
                lines[-1] = ('label', lines[-1][1], lines[-1][2] + item[1])
            else:
                lines.append(item)
    unit_gen, unit_nom, sec, sub, duty = DIV[0], DIV[1], '', '', ''
    for item in lines:
        kind = item[0]
        if kind == 'head':
            key = squashed(item[1])
            if key not in HEADS:
                raise ValueError(f'heading {item[1]!r}')
            level, gen, *nom = HEADS[key]
            if level == 'unit':
                unit_gen, unit_nom, sec, sub = gen, nom[0], '', ''
            elif level == 'sec':
                if sec == 'artiljerijskog diviziona' and key == 'četazavezu':
                    sub = 'čete za vezu'                                 # the divizion's own, after its batteries
                else:
                    sec, sub = gen, ''
            elif level == 'sub':
                sub = gen
            duty = ''
            continue
        if kind == 'label':
            duty = duty_of(item[1])
            words = item[2]
        else:
            words = item[1]
        if not duty or not words:
            continue
        for bat, given, surname, nick, ws in people(words):
            d = duty
            if d == 'načelnik' and sec == '':
                d = 'načelnik štaba'
            if d == 'pomoćnik' and sec == 'intendanture':
                d = 'pomoćnik načelnika intendanture'
            parts = [d]
            if sub:
                parts.append(sub)
            if sec == 'bataljona':
                parts.append(f'{bat}. bataljona' if bat else 'bataljona')
            elif sec and d not in OWN and not d.endswith(sec):
                parts.append(sec)
            parts.append(unit_gen)
            last, nicks = surname, [nick] if nick else []
            if '-' in last.strip('-'):
                a, b = last.split('-', 1)
                b_title = b.capitalize()
                if not (k8.known(b_title, 'last_name') >= 20 and k8.known(b_title, 'first_name') == 0):
                    last, nicks = a, [b] + nicks
            title = lambda x: '-'.join(p.capitalize() for p in x.split('-'))
            last = spelled(title(last.strip('-')), 'last_name')
            given = spelled(GIVEN_FIXES.get(given, given), 'first_name') if given else ''
            POSTS.append({'given': SAME.get((last, given), given), 'last': last,
                          'nicks': [n.capitalize() for n in nicks], 'post': ' '.join(parts),
                          'unit': unit_nom, 'page': ws[0]['page'], 'words': ws})


def extract(pdf_path: str, start_page: int, end_page: int | None) -> list[dict]:
    k8.corpus()
    read_posts(pdf_path)
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
            s['_posts'], s['_nicks'], s['_rects'] = [], [], []
            s['unit_detail'] = p['unit']
            out.append(s)
        if p['post'] not in man['_posts']:
            man['_posts'].append(p['post'])
        for n in p['nicks']:
            if n not in man['_nicks']:
                man['_nicks'].append(n)
        if p['page'] == man['pdf_page']:
            ws = p['words']
            for line in rows_of(ws):                                     # a name broken over two lines
                man['_rects'].append([round(min(w['x0'] for w in line), 1), round(min(w['top'] for w in line), 1),
                                      round(max(w['x1'] for w in line), 1), round(max(w['bottom'] for w in line), 1)])
    for s in out:
        s['additional_info'] = '; '.join([f'zvani {n}' for n in s['_nicks']] + [f"{TITLE}: {'; '.join(s['_posts'])}."])
        r = s['_rects']
        s['pdf_x'], s['pdf_y'], s['pdf_x_end'], s['pdf_y_end'] = r[0]
        if len(r) > 1:
            s['pdf_rects'] = r
        for k in ('_post', '_posts', '_nicks', '_rects'):
            s.pop(k)
    return out


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    if not Path(PDF).exists():
        cut_pdf()
    run_parser(pdf_path=PDF, brigade_code=97, output_path=sys.argv[1] if len(sys.argv) > 1 else UNIT,
               extract_fn=extract, entry_start_re=re.compile(r'^§§'), parse_entry_fn=parse, post_fn=men,
               id_start=10001, keep_other_sources=True)
