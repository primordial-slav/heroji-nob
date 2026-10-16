"""
Parser: 1. dalmatinska proleterska brigada (brigade code 36) — "Promjene u komandnom sastavu", a fifth list.

Source: Mirko Novović, Stevan Petković, the brigade's monograph (znaci.org 00001/108, the chapter 108_20.pdf, its PDF
        pp. 3-11, book pp. 435-443, after the closing chapter and before the lists of 108_21.pdf on the site)  →
        website/public/pdfs/1-dalmatinska-komandni-sastav.pdf: "Promjene u komandnom sastavu u jedinicama 1.
        dalmatinske NOU proleterske brigade od 6. septembra 1942. do kraja rata", the brigade staff's and each
        battalion's commanders, commissars, their deputies, chiefs of staff, quartermasters, medical officers, youth
        leaders and intelligence officers, numbered under each duty, given name first, in capitals, with the days:
    Komandanti brigade
    1. PETAR CETKOVlC Pero od 6. septembra do početka novembri
    1942. godine.
A word after the name, in capitals or small letters, is what he was called ("zvani Pero;"). A man in several posts is
one record with each. znaci re-typeset the book from its OCR, so the page shows its slips: carons lost on capitals
("BOZO", "IBRAHIMPASIĆ"), l for I ("STANlClC"), 2 for Ž ("2U2ULJ"), and the line's end cut off ("novembri", "godini");
the names take back the carons the brigade's other lists and the corpus print (`spelled`), the dates their endings.
The web page's fallen are the unit's first list (IDs from 1), the monograph's lists from 10001, the women from 20001,
Borci Sutjeske from 100001; these get IDs from 30001.
"""
import json
import re
import sys
import unicodedata
from collections import Counter
from pathlib import Path

import pdfplumber

import parse_8_kordunaska_divizija as k8
from _parser_scaffold import _record, run_parser
from pdf_coords import viewer_words

PDF = 'website/public/pdfs/1-dalmatinska-komandni-sastav.pdf'
UNIT = 'website/public/1-dalmatinska-soldiers.json'
SOURCE = Path(__file__).parent / '.cache' / 'znaci_photos' / 'books' / '00001_108_20.pdf'   # znaci.org 00001/108_20.pdf
FIRST_PAGE, LAST_PAGE = 3, 11
TITLE = 'Promjene u komandnom sastavu 1. dalmatinske brigade'
CAPS = 'A-ZČĆŽŠĐÜ'
# battalion headings: the bataljon, and the words its duties take after them
SECTIONS = [(r'U 1\. BATALJONU', '1. bataljon', '1. bataljona »Ante Jonić«'),
            (r'DRUGI BATALJON', '2. bataljon', '2. bataljona »Bude Borjan«'),
            (r'2\. BATALJON FORMIRAN', '2. bataljon', '2. bataljona formiranog 1943. godine'),
            (r'3\. BATALJONA »', '3. bataljon', '3. bataljona »Josip Jurčević«'),
            (r'3\. BATALJONA OD', '3. bataljon', '3. bataljona (od 20. januara 1944.)'),
            (r'4\. BATALJONA', '4. bataljon', '4. bataljona »Tadija Anušić«')]
DUTIES = [(r'komandanti', 'komandant'), (r'politički komesar', 'politički komesar'),
          (r'zamjenici komandan', 'zamjenik komandanta'), (r'zamjenici polit', 'zamjenik političkog komesara'),
          (r'načelnici štaba', 'načelnik štaba'), (r'oficir pri štabu', 'oficir pri štabu'), (r'intendant', 'intendant'),
          (r'referent', 'referent saniteta'), (r'omladinski', 'omladinski rukovodilac'),
          (r'obavještajni', 'obavještajni oficir'), (r'politički odjel', 'rukovodilac političkog odjela'),
          (r'članovi političkog', 'član političkog odjela'), (r'brigadna muzika', 'brigadna muzika'),
          (r'žinjerijski vod', 'inžinjerijski vod')]
# a duty printed before the name, under the music's and the engineers' headings
OWN_DUTY = {'Kapelnik': 'kapelnik brigadne muzike', 'Politički komesar': 'politički komesar brigadne muzike',
            'komandir voda': 'komandir inžinjerijskog voda'}
# names the OCR broke or turned, as the brigade's other lists print them
NAME_FIXES = {'PAR MAČ': 'PARMAČ', 'PA VICA': 'PAVICA', 'PEKO BOGDAN': 'BOGDAN PEKO',
              'STRICEVIC SOLlC': 'STRIČEVIĆ-ŠOLIĆ', 'KOTORAS': 'KOTARAŠ', 'KOTARAS': 'KOTARAŠ',
              'KORILIJAN CIPIKO': 'KORIOLAN ĆIPIKO', 'SLAVKÜ': 'SLAVKO', 'JOLJĆ': 'JOLIĆ', 'INDO': 'INĐO',
              'SĆEKIĆ': 'ŠĆEKIĆ'}
KEEP = {'Kazimir'}                                   # printed right where the brigade's other list has "Kažimir"
DATE_FIXES = [(r'\bgodi[nm]\S*', 'godine'), (r'\bgod$', 'godine'), (r'\bnovembri\b', 'novembra'), (r'\bjunj\b', 'juna'),
              (r'\bvgusta\b', 'avgusta'), (r'\bja nuara\b', 'januara'), (r'\bjanu- ara\b', 'januara'),
              (r'rata\. (maja|1945)', r'rata, \1'), (r'^,\s*', '')]
POSTS: list = []
_unit: dict = {}                                     # the brigade's spellings, by surname folded


def cut_pdf() -> None:
    from pypdf import PdfReader, PdfWriter
    r, w = PdfReader(str(SOURCE)), PdfWriter()
    for i in range(FIRST_PAGE - 1, LAST_PAGE):
        w.add_page(r.pages[i])
    with open(PDF, 'wb') as f:
        w.write(f)


def fold(t: str) -> str:
    t = unicodedata.normalize('NFKD', t.lower().replace('đ', 'd'))
    return ''.join(c for c in t if not unicodedata.combining(c))


ADDS = {('c', 'č'), ('c', 'ć'), ('s', 'š'), ('z', 'ž'), ('d', 'đ')}


def only_carons(a: str, b: str) -> bool:
    """b is a with carons added: the scan loses them, it doesn't add them or change them ("PARMAČ")."""
    return len(a) == len(b) and all(x == y or (x.lower(), y.lower()) in ADDS for x, y in zip(a, b))


def spelled(word: str, field: str) -> str:
    """The brigade's own spelling of a name ("Kotaraš", "Šolić"), else the corpus's, where only carons differ."""
    out = []
    for part in word.split('-'):
        part = part[:1] + part[1:].lower() if part.isupper() else part
        if part.endswith('ič'):                                              # the -ić the OCR read as -ič ("ĐAPIČ")
            part = part[:-1] + 'ć'
        cands = _unit.get(field, {}).get(fold(part))
        best = cands.most_common(1)[0][0] if cands else k8.respell(part, field)
        out.append(best if only_carons(part, best) and part not in KEEP else part)
    return '-'.join(out)


def load_unit() -> None:
    for f in ('last_name', 'first_name'):
        _unit[f] = {}
    for s in json.load(open(UNIT, encoding='utf-8')):
        if s['soldier_id'][4:6] in ('03', '04'):                             # this list's and the formation list's own
            continue
        for f in _unit:
            for part in re.split(r'[-\s]', s[f]):
                if part:
                    _unit[f].setdefault(fold(part), Counter())[part] += 1


def is_caps(w: str) -> bool:
    return bool(re.fullmatch(rf'[{CAPS}2l—-]+,?', w)) and sum(c.isupper() for c in w) >= 2 or w in ('I',)


def rows_of(page) -> list[list[dict]]:
    rows: list = []
    for w in sorted(viewer_words(page), key=lambda w: (w['top'], w['x0'])):
        if rows and abs(w['top'] - rows[-1][0]['top']) <= 3:
            rows[-1].append(w)
        else:
            rows.append([w])
    return [sorted(r, key=lambda w: w['x0']) for r in rows]


def starts_entry(r: list[dict]) -> bool:
    if len(r) < 2 or not re.fullmatch(r'\d{1,2}\.', r[0]['text']):
        return False
    nxt = r[1]['text']
    return is_caps(nxt) and nxt not in ('BATALJON', 'SEPTEMBRA') or nxt in ('Dr', 'Kapelnik', 'Politički', 'komandir')


def read_posts(pdf_path: str) -> None:
    section, unit, duty, heading = ('', 'Štab brigade', '', '')
    current = None                                   # the post or note the next wrapped line continues
    with pdfplumber.open(pdf_path) as pdf:
        for n, page in enumerate(pdf.pages, 1):
            rows = [r for r in rows_of(page) if not (r[0]['top'] > 565 and len(r) <= 2)]   # the page numbers
            xs = Counter(round(r[0]['x0']) for r in rows if starts_entry(r))
            ex = xs.most_common(1)[0][0]
            for r in rows:
                text = ' '.join(w['text'] for w in r)
                if n == 1 and r[0]['top'] < 170:                             # the list's title
                    continue
                if re.search(r'BATALJON|KOMANDNI SASTAV', text) and not re.search(r'[a-zčćžšđ]{3}', text):
                    heading = text
                    sec = next(s for s in SECTIONS if re.search(s[0], text))
                    unit, section = sec[1], sec[2]
                    current = 'heading'
                    continue
                if current == 'heading' and not re.search(r'[a-zčćžšđ]', text):          # "DO KRAJA RATA"
                    continue
                if starts_entry(r):
                    POSTS.append({'unit': unit, 'section': section, 'duty': duty, 'page': n, 'words': r[1:],
                                  'text': ' '.join(w['text'] for w in r[1:])})
                    current = POSTS[-1]
                    continue
                if r[0]['x0'] < ex - 10:                                     # a wrapped line
                    if isinstance(current, dict):
                        current['text'] = current['text'] + ' ' + text
                    continue
                if r[0]['x0'] > ex + 30:                                     # a duty's heading, centred
                    duty = next(d for k, d in DUTIES if k in text.lower())
                    current = 'duty'
                    continue
                current = 'note'                                             # "Juna 1943. godine ovaj bataljon ..."


def name_and_when(text: str) -> dict:
    """'PETAR CETKOVlC Pero od 6. septembra ...' -> given, surname, what he was called, the days."""
    title, own = '', ''
    for k, v in OWN_DUTY.items():
        if text.startswith(k + ' '):
            own, text = v, text[len(k) + 1:]
    if text.startswith('Dr '):
        title, text = 'dr.', text[3:]
    for a, b in NAME_FIXES.items():
        text = re.sub(rf'(?<![{CAPS}]){re.escape(a)}(?![{CAPS}])', b, text)
    words = text.split()
    caps = []
    while words and is_caps(words[0]):
        caps.append(words.pop(0))
    nick = ''
    if words and re.fullmatch(r'[A-ZČĆŽŠĐ][a-zčćžšđ]+,?', words[0]) and words[0] not in ('Dr',):
        nick = words.pop(0)
    when = ' '.join(words)
    caps = [c.rstrip(',').replace('2', 'Ž').replace('l', 'I') for c in caps]
    if text.split()[len(caps) - 1].endswith(','):                           # "RISTO LEKIĆ, rukovodilac politodjela od ..."
        when = re.sub(r'^rukovodilac politodjela\s+', '', when)
    given, last = caps[0], caps[1] if len(caps) > 1 else ''
    if len(caps) > 2:
        nick = ' '.join(caps[2:])
    nick = nick.rstrip(',')
    for a, b in DATE_FIXES:
        when = re.sub(a, b, when).strip()
    return {'title': title, 'own': own, 'given': spelled(given, 'first_name'), 'last': spelled(last, 'last_name'),
            'nick': spelled(nick, 'first_name') if nick else '', 'when': when}


def post_text(p: dict) -> str:
    if p['own']:
        duty = p['own']
    elif p['duty'] in ('brigadna muzika', 'inžinjerijski vod'):
        duty = p['duty']
    elif p['section']:
        duty = f"{p['duty']} {p['section']}"
    else:
        duty = f"{p['duty']} brigade"
    return f"{duty}, {p['when']}".rstrip(', .') if p['when'] else duty


def extract(pdf_path: str, start_page: int, end_page: int | None) -> list[dict]:
    k8.corpus()
    load_unit()
    read_posts(pdf_path)
    for p in POSTS:
        p.update(name_and_when(p['text']))
        p['post'] = post_text(p)
    return [{'text': '§§post' + str(i), 'x': round(p['words'][0]['x0'], 1), 'y': round(p['words'][0]['top'], 1),
             'page': p['page']} for i, p in enumerate(POSTS)]


def parse(text: str) -> dict:
    p = POSTS[int(text[6:])]
    rec = _record(p['last'], p['given'], '', '')
    rec['_post'] = int(text[6:])
    return rec


def name_words(p: dict) -> list[dict]:
    """The name's words on the page: up to the first word of the days."""
    out = []
    for w in p['words']:
        if out and not (is_caps(w['text']) or w['text'] in ('Dr', 'Kapelnik', 'Politički', 'komesar', 'komandir', 'voda')
                        or re.fullmatch(r'[A-ZČĆŽŠĐ][a-zčćžšđ]+,?', w['text']) and len(out) <= 3):
            break
        out.append(w)
    return out


def men(soldiers: list[dict]) -> list[dict]:
    out, seen = [], {}
    for s in soldiers:
        p = POSTS[s['_post']]
        key = (fold(p['last'].split('-')[0]), fold(p['given']))             # "Ivanišević-Andrijić Vjera", "Ivanišević Vjera"
        man = seen.get(key)
        if man is None:
            man = seen[key] = s
            s['_posts'], s['_nicks'], s['_rects'], s['_title'] = [], [], [], p['title']
            s['unit_detail'] = p['unit']
            out.append(s)
        if len(p['last']) > len(man['last_name']):
            man['last_name'] = p['last']
        man['_posts'].append(p['post'])
        if p['nick'] and p['nick'] not in man['_nicks']:
            man['_nicks'].append(p['nick'])
        if p['page'] == man['pdf_page']:
            ws = name_words(p)
            man['_rects'].append([round(min(w['x0'] for w in ws), 1), round(min(w['top'] for w in ws), 1),
                                  round(max(w['x1'] for w in ws), 1), round(max(w['bottom'] for w in ws), 1)])
    for s in out:
        s['additional_info'] = '; '.join(([s['_title']] if s['_title'] else []) + [f'zvani {n}' for n in s['_nicks']]
                                         + [f"{TITLE}: {'; '.join(s['_posts'])}."])
        r = s['_rects']
        s['pdf_x'], s['pdf_y'], s['pdf_x_end'], s['pdf_y_end'] = r[0]
        if len(r) > 1:
            s['pdf_rects'] = r
        s['full_name'] = f"{s['last_name']} {s['first_name']}"
        for k in ('_post', '_posts', '_nicks', '_rects', '_title'):
            s.pop(k)
    return out


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    if not Path(PDF).exists():
        cut_pdf()
    run_parser(pdf_path=PDF, brigade_code=36, output_path=sys.argv[1] if len(sys.argv) > 1 else UNIT,
               extract_fn=extract, entry_start_re=re.compile(r'^§§'), parse_entry_fn=parse, post_fn=men,
               id_start=30001, keep_other_sources=True)
