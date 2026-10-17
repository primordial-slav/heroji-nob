"""
Parser: 2. dalmatinska proleterska brigada (brigade code 7) — its staffs and commands, a second list.

Source: the brigade's monograph (znaci.org 00001/33, the chapter 33_21.pdf, "III dio, Prilozi", its PDF pp. 2-14 and
        19, book pp. 473-486; the scan repeats pp. 11-14 as pp. 15-18)  →  website/public/pdfs/2-dalmatinska-stabovi.pdf:
        "Pregled štabova i komandi 2. dalmatinske brigade", made by the brigade's surviving officers. Part I, the
        brigade staff with the days each held his post, and its attached units, one column:
    Komandanti brigade:
    Ljubo Vučković, od 3. X 1942. do 10. VI 1943.
    Komandiri: Stevo Pećanac i Nikola Novaković-Nina, Milorad Ivanović i Đuro Tojaga
        Part II, the staffs of the battalions and the commands of their companies by duty only, two columns,
        numbered names under each duty; a heading across the page ("DRUGI BATALJON", "1. ČETA") starts the staff or
        company below it, so a page is read band by band, the left column before the right.
A word joined to a name by a hyphen is what he was called or a second surname, as printed. A man in several posts is
one record with each; his box is around his name at each post on his first post's page. The fallen are the unit's
first list (IDs from 1), Borci Sutjeske from 100001; these get IDs from 10001.
"""
import re
import sys
from pathlib import Path

import pdfplumber

import parse_8_kordunaska_divizija as k8
from _parser_scaffold import _record, run_parser
from pdf_coords import viewer_words

PDF = 'website/public/pdfs/2-dalmatinska-stabovi.pdf'
UNIT = 'website/public/2-dalmatinska-soldiers.json'
SOURCE = Path(__file__).parent / '.cache' / 'znaci_photos' / 'books' / '00001_33_21.pdf'   # znaci.org 00001/33_21.pdf
PAGES = list(range(2, 15)) + [19]                     # the chapter's pages; 15-18 repeat 11-14
TITLE = 'Pregled štabova i komandi 2. dalmatinske brigade'
SPLIT = 200
BATS = {'PRVI': 1, 'DRUGI': 2, 'TREĆI': 3, 'ČETVRTI': 4, 'PETI': 5}
# the duty's words in the singular, by the heading's first words
SINGULAR = [(r'^komandanti', 'komandant'), (r'^komandiri?\b', 'komandir'), (r'^politički komesari?', 'politički komesar'),
            (r'^komesari?\b', 'politički komesar'), (r'^zam(jenici|jenik|\.) (političkog komesara|polit\w*,? komesara|'
                                                     r'politkomesara)', 'zamjenik političkog komesara'),
            (r'^zamjeni(ci|k) komandan?ta', 'zamjenik komandanta'), (r'^zamjeni(ci|k) komandira', 'zamjenik komandira'),
            (r'^zamjeni(ci|k) komesara', 'zamjenik komesara'),
            (r'^operativci.*', 'operativni oficir, od ljeta 1943. načelnik štaba'), (r'^članovi politodjela', 'član Politodjela'),
            (r'^obavi?ještajni oficiri?', 'obavještajni oficir'), (r'^referenti? saniteta', 'referent saniteta'),
            (r'^intenda\w*', 'intendant'), (r'^omladinski rukovodi\w*', 'omladinski rukovodilac'),   # "Intendami"
            (r'^oficiri ozn-e', 'oficir OZN-e'), (r'^upravnici', 'upravnik'), (r'^pomoćni(ci|k)', 'pomoćnik političkog komesara')]
# part I's units attached to the staff, in the words their duties take
ATTACHED = [(r'^Četa pratećih oruđa', 'čete pratećih oruđa brigade'), (r'^Komanda brigade intendanture', 'brigadne intendanture'),
            (r'^Četa automatičara', 'čete automatičara brigade'), (r'^Zaštitna četa', 'zaštitne čete brigade'),
            (r'^Izviđačka četa', 'izviđačke čete brigade'), (r'^Četa za vezu', 'čete za vezu'),
            (r'^Inžinjerijska četa', 'inžinjerijske čete brigade')]
POSTS: list = []


def cut_pdf() -> None:
    from pypdf import PdfReader, PdfWriter
    r, w = PdfReader(str(SOURCE)), PdfWriter()
    for i in PAGES:
        w.add_page(r.pages[i - 1])
    with open(PDF, 'wb') as f:
        w.write(f)


ADDS = {('c', 'č'), ('c', 'ć'), ('s', 'š'), ('z', 'ž'), ('d', 'đ')}


def spelled(word: str, field: str) -> str:
    """The corpus's spelling where only carons the print lost differ; the OCR's -ie is -ić ("Bilie")."""
    out = []
    for part in word.split('-'):
        if part.endswith('ie') and k8.known(part[:-2] + 'ić', field) > 3 * k8.known(part, field):
            part = part[:-2] + 'ić'
        best = k8.respell(part, field)
        ok = len(best) == len(part) and all(a == b or (a.lower(), b.lower()) in ADDS for a, b in zip(part, best))
        out.append(best if ok else part)
    return '-'.join(out)


def singular(head: str) -> str:
    h = head.lower().rstrip(': ')
    if h.replace(' ', '') == 'političkihomesari':                       # "Po litičk i ho mesa ri", the OCR's
        h = 'politički komesari'
    for p, d in SINGULAR:
        m = re.match(p, h)
        if m:
            rest = h[m.end():].strip()
            return f'{d} {rest}'.strip()
    raise ValueError(f'duty {head!r}')


def rows_of(words: list[dict]) -> list[list[dict]]:
    rows: list = []
    for w in sorted(words, key=lambda w: (round(w['top']), w['x0'])):
        if rows and abs(rows[-1][0]['top'] - w['top']) <= 3:
            rows[-1].append(w)
        else:
            rows.append([w])
    return [sorted(r, key=lambda w: w['x0']) for r in rows]


def lines_in_order(pdf) -> list[tuple]:
    """('I', words) for part I's lines, ('section', text) and ('II', words) for part II's, in reading order."""
    out, part = [], 'I'
    for n, page in enumerate(pdf.pages, 1):
        words = [{**w, 'page': n} for w in viewer_words(page, extra_attrs=['size']) if w['size'] >= 7.5]
        rows = rows_of(words)
        two_from = None                                                   # where part II starts on this page
        for r in rows:
            t = ' '.join(w['text'] for w in r)
            if t.startswith('PREGLED SASTAVA'):                          # part II's title ("II dio" is set smaller)
                two_from = r[0]['top'] if two_from is None else two_from
            if re.fullmatch(r'\d{3}', t) or t.startswith(('PREGLED', 'BRIGADE"', 'Ovaj prilog', 'gade do',
                                                          'brigade i vrijeme', 'jeli period', 'jedinica brigade',
                                                          'šina štabova')):
                for w in r:
                    words.remove(w)
        if part == 'I':
            cut = two_from if two_from is not None else 1e9
            for r in rows_of([w for w in words if w['top'] < cut and w['size'] >= 9.5]):   # not the footnote
                if ' '.join(w['text'] for w in r) not in ('I dio', 'II dio'):
                    out.append(('I', r))
            if two_from is None:
                continue
            part = 'II'
            words = [w for w in words if w['top'] > two_from + 25]
        # part II: bands between the headings across the page
        cuts = []
        for r in rows_of(words):
            t = ' '.join(w['text'] for w in r)
            c = re.match(r'^(\d)\.[ČC]?E?T?A?$', t.replace(' ', ''))   # "2. Č E TA", "1. ETA", "2. C E T A"
            if t.replace(' ', '') == 'ETA' and 100 < r[0]['x0'] <= SPLIT + 5:
                cuts.append((r[0]['top'], 'next ČETA'))                  # the PETI's "3. Č" the page lost
                for w in r:
                    words.remove(w)
            elif 100 < r[0]['x0'] < SPLIT and (c or re.search(r'BATALJON|ČETA|^\(od', t)):
                cuts.append((r[0]['top'], f'{c.group(1)}. ČETA' if c else t))
                for w in r:
                    words.remove(w)
        for w in [w for w in words if re.fullmatch(r'[A-ZČ]{1,3}', w['text'])
                  and any(abs(w['top'] - c[0]) < 8 for c in cuts)]:
            words.remove(w)                                              # the spaced heading's other pieces
        bands = [-1.0] + [c[0] for c in cuts] + [1e9]
        for i in range(len(bands) - 1):
            if i:
                out.append(('section', cuts[i - 1][1]))
            band = [w for w in words if bands[i] < w['top'] < bands[i + 1] and w['size'] >= 9.5]
            for col in ([w for w in band if w['x0'] < SPLIT], [w for w in band if w['x0'] >= SPLIT]):
                for r in rows_of(col):
                    out.append(('II', r))
    return out


NAME = re.compile(r'^((?:Dr\s+)?[A-ZČĆŽŠĐ][a-zčćžšđ]+(?:-[A-ZČĆŽŠĐ][a-zčćžšđ]+)?)\s+((?:dr\s+)?(?:[A-ZČĆŽŠĐ]\.\s+)?'
                  r'[A-ZČĆŽŠĐ][a-zčćžšđ]+(?:-[A-ZČĆŽŠĐ][a-zčćžšđ]+)?)(.*)$')


DUTY_WORDS = {'članovi', 'komandanti', 'komandiri', 'komandir', 'komesar', 'komesari', 'politički', 'zamjenici',
              'zamjenik', 'referenti', 'intendanti', 'intendami', 'upravnici', 'oficiri', 'obavještajni', 'omladinski',
              'operativci', 'pomoćnici'}


def person(text: str) -> dict | None:
    """'Radisav Jugović-Bako, od juna ...' -> given, surname (a hyphened second part kept), the rest."""
    text = text.strip().replace('^', ' ').replace('à', 'a').replace('  ', ' ')
    m = NAME.match(text)
    if not m or m.group(1).lower() in DUTY_WORDS:                        # "Članovi Politodjela brigade:"
        return None
    given, last, rest = m.group(1), m.group(2), m.group(3)
    title = ''
    if given.startswith('Dr '):
        title, given = 'dr', given[3:]
    if last.startswith('dr '):
        title, last = 'dr', last[3:]
    initial = ''
    if re.match(r'[A-ZČĆŽŠĐ]\. ', last):
        initial, last = last[:2], last[3:]
    nick = ''
    if '-' in given:
        given, nick = given.split('-', 1)
    if '-' in last:                                                      # "Crnogorac-Mićo": what he was called
        a, b = last.split('-', 1)
        if k8.known(b, 'first_name') >= 5 and k8.known(b, 'last_name') < k8.known(b, 'first_name'):
            last, nick = a, nick or b
    if k8.known(given, 'last_name') > 3 * k8.known(given, 'first_name') + 2 and \
            k8.known(last, 'first_name') > 3 * k8.known(last, 'last_name') + 2:
        given, last = last, given                                        # "Sinobad Branko", printed surname first
    rest = re.sub(r'^\s*[-,]\s*', '', rest).strip().rstrip('.,')
    return {'given': given, 'last': last, 'nick': nick, 'title': title, 'initial': initial, 'rest': rest}


def add(p: dict, duty: str, unit: str, words: list[dict]) -> None:
    POSTS.append({**p, 'given': spelled(p['given'], 'first_name'), 'last': spelled(p['last'], 'last_name'),
                  'post': f"{duty}, {p['rest']}" if p['rest'] else duty, 'unit': unit, 'page': words[0]['page'],
                  'words': words})


def names_in(text: str, words: list[dict]) -> list[tuple[dict, list[dict]]]:
    """'Stevo Pećanac i Nikola Novaković-Nina, Milorad Ivanović i' -> each man, with his words."""
    out = []
    for part in re.split(r',\s*|\s+i\s+', text):
        while part:
            p = person(part)
            if not p:
                break
            nxt = person(p['rest']) if p['rest'][:1].isupper() else None  # "Dušan Tomović Stevo Bjedov": no comma
            if nxt:
                p = {**p, 'rest': ''}
            mine = part[:len(part) - len(nxt and part.split(' ', 2)[2] or '')] if nxt else part
            ws = [w for w in words if w['text'].rstrip(',.') in mine.split()]
            out.append((p, ws or words))
            part = part.split(' ', 2)[2] if nxt else ''
    return out


def read_posts(pdf_path: str) -> None:
    with pdfplumber.open(pdf_path) as pdf:
        lines = lines_in_order(pdf)
    duty, of, label_unit, pending = '', 'brigade', None, None
    unit, bat, company = 'Štab brigade', 0, 0
    for kind, *rest in lines:
        if kind == 'section':
            t = rest[0]
            m = re.match(r'(PRVI|DRUGI|TREĆI|ČETVRTI|PETI) BATALJON', t)
            if m:
                bat, company = BATS[m.group(1)], 0
                unit, of = f'{bat}. bataljon', f'{bat}. bataljona'
            elif re.match(r'(\d)\. ČETA|next ČETA', t):
                c = company = int(re.match(r'(\d)\.', t).group(1)) if t[0].isdigit() else company + 1
                unit, of = f'{c}. četa, {bat}. bataljon', f'{c}. čete {bat}. bataljona'
            elif 'MITRALJESKA' in t or 'PRATEĆ' in t:
                kind_c = 'mitraljeska' if 'MITRALJESKA' in t else 'prateća'
                unit, of = f'{kind_c} četa, {bat}. bataljon', f"{kind_c[:-1]}e čete {bat}. bataljona"
            duty = ''
            continue
        ws = rest[0]
        t = ' '.join(w['text'] for w in ws)
        if kind == 'I':
            if pending:                                                  # "..., Milorad Ivanović i" / "Đuro Tojaga"
                t, ws = pending[0] + ' ' + t, pending[1] + ws
                pending = None
            att = next((a for a in ATTACHED if re.match(a[0], t)), None)
            if att and t.rstrip().endswith(':'):
                label_unit, duty = att[1], ''
                continue
            m = re.match(r'^([A-ZČĆŽŠĐ][^:]{2,80}?):\s*(.*)$', t)
            if m and not person(m.group(1)) or m and m.group(1).startswith(('Komandir', 'Komesar', 'Zam', 'Politi')):
                head, names = m.group(1), m.group(2)
                if not names and not head.startswith(('Komandir', 'Komesar', 'Zam', 'Politi')):
                    label_unit = None                                    # a staff duty again ("Upravnici brigadne bolnice")
                where = label_unit or ('brigadne bolnice' if 'bolnice' in head else 'brigade')
                d = singular(re.sub(r'\s+(brigade|brigadne bolnice|čete|štaba brigade)$', '', head, flags=re.I))
                d = re.sub(r' brigadne bolnice$', '', d)
                duty = f'{d} {where}' if not d.endswith(where) else d
                if names:
                    if names.rstrip().endswith(' i'):                    # the list runs on to the next line
                        pending = (t, ws)
                        continue
                    for p, pw in names_in(names, ws):
                        add(p, duty, 'Štab brigade', pw)
                continue
            if t.startswith('i ') and POSTS:                             # "i Štefica Carić-Marušić"
                t = t[2:]
            for p, pw in names_in(t, ws) if ' i ' in t and t.startswith(('Dr ', 'Ivo ')) else \
                    [(person(t), ws)] if person(t) else []:
                add(p, duty, 'Štab brigade', pw)
            continue
        # part II
        if not re.match(r'^\d+\.', t):
            if re.match(r'^[A-ZČĆŽŠĐ]', t) and not person(t.lstrip('»')):
                head = re.sub(r'\s+(bataljona|čete):?$', '', t)
                duty = f'{singular(head)} {of}'
            elif t.endswith(':') and duty:                               # "Zamjenici političkog komesara" / "čete:"
                pass
            continue
        p = person(re.sub(r'^\d+\.\s*', '', t))
        if p:
            add(p, duty, unit, ws[1:] or ws)


def extract(pdf_path: str, start_page: int, end_page: int | None) -> list[dict]:
    k8.corpus()
    read_posts(pdf_path)
    return [{'text': '§§post' + str(i), 'x': round(p['words'][0]['x0'], 1), 'y': round(p['words'][0]['top'], 1),
             'page': p['page']} for i, p in enumerate(POSTS)]


def parse(text: str) -> dict:
    p = POSTS[int(text[6:])]
    rec = _record(p['last'], p['given'], p['initial'], '')
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
            s['_posts'], s['_nicks'], s['_rects'], s['_title'] = [], [], [], p['title']
            s['unit_detail'] = p['unit']
            out.append(s)
        if p['post'] not in man['_posts']:
            man['_posts'].append(p['post'])
        if p['nick'] and p['nick'] not in man['_nicks']:
            man['_nicks'].append(p['nick'])
        if p['page'] == man['pdf_page']:
            ws = p['words']
            man['_rects'].append([round(min(w['x0'] for w in ws), 1), round(min(w['top'] for w in ws), 1),
                                  round(max(w['x1'] for w in ws), 1), round(max(w['bottom'] for w in ws), 1)])
    for s in out:
        s['additional_info'] = '; '.join(([s['_title']] if s['_title'] else []) + [f'zvani {n}' for n in s['_nicks']]
                                         + [f"{TITLE}: {'; '.join(s['_posts'])}."])
        r = s['_rects']
        s['pdf_x'], s['pdf_y'], s['pdf_x_end'], s['pdf_y_end'] = r[0]
        if len(r) > 1:
            s['pdf_rects'] = r
        s['full_name'] = ' '.join(x for x in (s['last_name'], s['middle_name'], s['first_name']) if x)
        for k in ('_post', '_posts', '_nicks', '_rects', '_title'):
            s.pop(k)
    return out


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    if not Path(PDF).exists():
        cut_pdf()
    run_parser(pdf_path=PDF, brigade_code=7, output_path=sys.argv[1] if len(sys.argv) > 1 else UNIT,
               extract_fn=extract, entry_start_re=re.compile(r'^§§'), parse_entry_fn=parse, post_fn=men,
               id_start=10001, keep_other_sources=True)
