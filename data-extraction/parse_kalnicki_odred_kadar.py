"""
Parser: Kalnički partizanski odred (brigade code 58) — its leaders, a second list.

Source: Žarko Milićević, *Kalnički partizanski odred* (znaci.org 00003/558, its PDF pp. 279-300 and 302, book pp.
        282-303 and 305)  →  website/public/pdfs/kalnicki-odred-kadar.pdf: the leaders of the first armed groups and
        partisan formations on Kalnik (1941-1942), of the odred formed in October 1942, its battalions, companies and
        platoons, and those whose unit and time could not be established. Three columns: the duty on the left, the
        name in capitals beside it, the days of the post on the right, "od" on the name's line or just above it and
        "do" under it:
    Komandanti
    Odreda:      MATE JERKOVIĆ              - od 10.10.1942.
                                              do 13.11.1942.
        A note in brackets under a name is his ("(ujedno komandant bataljona)"); "?" is a post the book could not
        fill. A man in several posts is one record with each; his box is around his name at each post on his first
        post's page. The roll is the unit's first list (IDs from 1); these get IDs from 10001. PDF p. 301 is a table of
        the companies' lifetimes, without names, and is left out.
"""
import re
import sys
from pathlib import Path

import pdfplumber

import parse_8_kordunaska_divizija as k8
from _parser_scaffold import _record, run_parser
from parse_2_dalmatinska_stabovi import rows_of
from parse_6_vojvodjanska_stabovi import respelled
from pdf_coords import viewer_words

PDF = 'website/public/pdfs/kalnicki-odred-kadar.pdf'
UNIT = 'website/public/kalnicki-odred-soldiers.json'
SOURCE = Path(__file__).parent / '.cache' / 'znaci_photos' / 'books' / '00003_558.pdf'   # znaci.org 00003/558.pdf
PAGES = list(range(279, 301)) + [302]
TITLE = 'Rukovodioci Kalničkoga partizanskog odreda'
LEFT, DATES = 225, 375                                                  # the columns' edges
# headings, spaces out and in small letters -> (the words a post takes, unit_detail, kind)
HEADS = {
    'rukovodiociprvihpartizanskihformacija': ('', 'prve formacije na Kalniku', 'top'),
    'nakalniku': None, 'oružanihgrupa:': ('oružane grupe', 'oružane grupe', 'groups'),
    'kalničkepartizanskečete:': ('Kalničke partizanske čete', 'Kalnička partizanska četa', 'sec'),
    'kalničkogaodredaformiranoguožujku1942:': ('Kalničkog odreda (formiranog u ožujku 1942)', 'Kalnički odred (1942)', 'sec'),
    'rukovodiocikalničkogapartizanskogogreda': ('Kalničkog partizanskog odreda', 'štab odreda', 'sec'),
    'formiranoguistopadu1942.': None, 'formiranogulistopadu1942.': None,
    'mitraljeskačeta': ('mitraljeske čete', 'mitraljeska četa', 'sec'),
    'zagorskaudarnačeta': ('Zagorske udarne čete', 'Zagorska udarna četa', 'sec'),
    'osiječkačeta': ('Osiječke čete', 'Osiječka četa', 'sec'), 'osuečkačeta': ('Osiječke čete', 'Osiječka četa', 'sec'),
    'međimurskačeta': ('Međimurske čete', 'Međimurska četa', 'sec'),
    'varaždinskačeta': ('Varaždinske čete', 'Varaždinska četa', 'sec'),
    'obrazovnačeta': ('Obrazovne čete', 'Obrazovna četa', 'sec'), 'terenskačeta': ('Terenske čete', 'Terenska četa', 'sec'),
    'žumberačkačeta': ('Žumberačke čete', 'Žumberačka četa', 'sec'),
    'vodpratećihoruđa': ('voda pratećih oruđa', 'vod pratećih oruđa', 'sec'),
    'vodzavezu': ('voda za vezu', 'vod za vezu', 'sec'), 'izviđačkivod': ('izviđačkog voda', 'izviđački vod', 'sec'),
    'minerskivod': ('minerskog voda', 'minerski vod', 'sec'),
    'rukovodiociuodredukojimasenuemogla': ('Kalničkog partizanskog odreda (jedinica i vrijeme nisu utvrđeni)', 'odred', 'sec'),
    'rukovodiociuodredukojimasenijemogla': ('Kalničkog partizanskog odreda (jedinica i vrijeme nisu utvrđeni)', 'odred', 'sec'),
    'utvrditijedinicunivrijemepostojanja': None, 'utvrditijedinicanivrijemepostojanja': None,
    'udarnibataljonmatijagubec': ('Udarnog bataljona »Matija Gubec«', 'Udarni bataljon »Matija Gubec«', 'bat'),
    'samostalnečeteivodovi:': None,
}
BAT = re.compile(r'^(\d)\.bataljon$')
# the groups of 1941 (page 1), by their label
GROUPS = {'osječko-kalničke': 'osječko-kalničke oružane grupe', 'varaždinsko-ludbreške': 'varaždinsko-ludbreške oružane grupe',
          'kapelske': 'kapelske oružane grupe', 'grupe bože leinera': 'grupe Bože Leinera'}
WORDS = [(r'^komandanti\b', 'komandant'), (r'^komandiri\b', 'komandir'), (r'^komesari\b', 'komesar'),
         (r'^zamjenici\b', 'zamjenik'), (r'\boficiri\b', 'oficir'), (r'^referenti\b', 'referent'), (r'^intendanti\b', 'intendant'),
         (r'^delegati\b', 'delegat'), (r'\bčeta\b', 'čete'), (r'\bvodova\b', 'voda'), (r'^četni bolničari?\b', 'četni bolničar')]
CAPS_FIX = {'MINERSKIVOD': 'MINERSKI VOD', 'HABUAN': 'HABUŠ', 'KATALEVIĆ': 'KATALENIĆ', 'LUBOMIR': 'LJUBOMIR',
            'KLJICKOVIĆ': 'KLIČKOVIĆ', 'VLAD': 'VLADO'}
DATE_WORD = re.compile(r'^[-•]?(od|do)\b|^[-•]$|^doo\d|^doli\.')
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


def date_of(text: str) -> tuple[str, str] | None:
    """'-od 10.10.1942.' -> ('od', '10. 10. 1942'); the scan's slips mended ('194Z', '16. U.', 'doli.', 'doo8.')."""
    t = text.replace('•', '').replace('194Z', '1942').replace(' U. ', ' 11. ').strip(' -')
    t = re.sub(r'^doli\.', 'do 11.', t)
    t = re.sub(r'^doo(\d)', r'do 0\1', t)
    t = re.sub(r'^-\s*', '', t)
    m = re.match(r'^(od|do)\s*(.*)$', t)
    if not m:
        return None
    d = m.group(2).replace(',', '.').strip()
    d = re.sub(r'(\d{1,2})\.\s*(\d{2})\.\s*(\d{4})\.?', lambda x: f'{int(x[1])}. {int(x[2])}. {x[3]}', d)
    return m.group(1), d.rstrip('.').strip()


def duty_of(label: str, kind: str, of: str = '') -> str:
    t = re.sub(r'\s+', ' ', label.replace('\\', 'v')).strip().rstrip(':').strip()   # "oba\ještajni"
    low = t.lower()
    for p, d in WORDS:
        low = re.sub(p, d, low)
    if kind in ('odred', 'top'):
        low = re.sub(r'\s+odreda$', '', low)
    elif kind == 'bat':
        low = re.sub(r'\s+bataljona$', '', low)
    elif kind == 'company':                                            # a company's own, a platoon's own
        low = re.sub(r'\s+čete$' if of.endswith('čete') else r'\s+voda$', '', low)
    return low


def read_posts(pdf_path: str) -> None:
    events = []                                                          # (page, top, kind, data)
    with pdfplumber.open(pdf_path) as pdf:
        for n, page in enumerate(pdf.pages, 1):
            words = [{**w, 'page': n} for w in viewer_words(page, extra_attrs=['size'])]
            for r in rows_of(words):
                t = ' '.join(w['text'] for w in r)
                key = squashed(t)
                if key in HEADS or any(key.startswith(k) for k in ('rukovodiociprvih', 'rukovodiocikalnič', 'rukovodiociuodredu')) \
                        or BAT.match(key) or (r[0]['x0'] < LEFT and re.fullmatch(r"[A-ZČĆŽŠĐ .:\-]+", t) and len(t) > 6
                                              and not any(w['x0'] >= DATES for w in r)):
                    events.append((n, r[0]['top'], 'head', CAPS_FIX.get(t.replace(' ', ''), t)))
                    continue
                left = [w for w in r if w['x0'] < LEFT]
                rest = [w for w in r if w['x0'] >= LEFT]                 # the days start at their first word ("-od",
                k = next((i for i, w in enumerate(rest) if w['x0'] > 300 and DATE_WORD.match(w['text'])), len(rest))
                mid, right = rest[:k], rest[k:]                          # "do"); a name may run past the column's edge
                while left and len(left) > 1 and re.fullmatch(r'[A-ZČĆŽŠĐ]{2,}', left[-1]['text']):
                    mid.insert(0, left.pop())                            # "Referent saniteta BOŽA PEHAREC"
                if left:
                    events.append((n, left[0]['top'], 'label', ' '.join(w['text'] for w in left)))
                if mid:
                    mt = ' '.join(w['text'] for w in mid)
                    if mt.startswith('(') or mid[0]['text'][:1].islower():
                        events.append((n, mid[0]['top'], 'note', mt))
                    elif re.fullmatch(r"[A-ZČĆŽŠĐ][a-zčćžšđ]+ [A-ZČĆŽŠĐ][a-zčćžšđ]+(?: [A-ZČĆŽŠĐ][a-zčćžšđ]+ [A-ZČĆŽŠĐ][a-zčćžšđ]+)?", mt):
                        pass                                             # a photograph's caption ("Bozo Leiner Vitko Jurec")
                    else:
                        events.append((n, mid[0]['top'], 'names', mid))
                if right:
                    d = date_of(' '.join(w['text'] for w in right))
                    if d:
                        events.append((n, right[0]['top'], 'date', d))
    # the names and their days
    of, unit, kind, label, label_open = 'Kalničkog partizanskog odreda', 'štab odreda', 'odred', '', True
    names = []                                                           # each man's post, in order
    for n, top, ev, data in events:
        if ev == 'head':
            key = squashed(data)
            b = BAT.match(key)
            h = HEADS.get(key) if key in HEADS else next((v for k, v in HEADS.items() if v and key.startswith(k)), None)
            if b:
                of, unit, kind = f'{b.group(1)}. bataljona', f'{b.group(1)}. bataljon', 'bat'
            elif h:
                of, unit = h[0], h[1]
                kind = {'top': 'top', 'groups': 'groups', 'bat': 'bat'}.get(h[2], 'odred' if 'odreda' in h[0] else 'company')
            elif key not in HEADS:
                raise ValueError(f'heading {data!r}')
            label, label_open = '', True
            continue
        if ev == 'label':
            if not label_open:
                label, label_open = '', True
            label = f'{label} {data}'.strip()
            continue
        if ev == 'note' and names:
            names[-1]['note'] = f"{names[-1].get('note', '')} {data}".strip()
            continue
        if ev == 'date':
            continue
        label_open = False
        if kind == 'groups':
            duty = 'rukovodilac ' + GROUPS[label.rstrip(':').strip().lower()]
            post = duty
        else:
            d = duty_of(label, kind, of)
            post = f'{d} {of}'.strip()
        for item in split_names(data):
            texts = [w['text'].strip(',.') for w in item]
            note = ' '.join(x for x in texts if x.startswith('('))
            texts = [x for x in texts if x and not x.startswith('(') and x != '?']
            if not texts:
                continue
            names.append({'texts': texts, 'post': post, 'unit': unit, 'page': n, 'top': top, 'words': item,
                          'note': note, 'od': '', 'do': ''})
    # each date row to the nearest man on its page: "od" at or just above his line, "do" under it
    for n, top, ev, data in events:
        if ev != 'date':
            continue
        which, day = data
        cands = [m for m in names if m['page'] == n and not m[which]
                 and (-14 <= top - m['top'] <= 14 if which == 'od' else 0 < top - m['top'] <= 30)]
        if cands:
            min(cands, key=lambda m: abs(top - m['top']))[which] = day
    for m in names:
        given, last, nick = name_of(m['texts'])
        days = ' '.join(x for x in (f"od {m['od']}" if m['od'] else '', f"do {m['do']}" if m['do'] else '') if x)
        note = m['note'].strip('() ')
        post = ', '.join(x for x in (m['post'], days, note) if x)
        POSTS.append({'given': given, 'last': last, 'nick': nick, 'post': post, 'unit': m['unit'], 'page': m['page'],
                      'words': m['words']})


def split_names(words: list[dict]) -> list[list[dict]]:
    out, cur = [], []
    for w in words:
        cur.append(w)
        if w['text'].endswith(','):
            out.append(cur)
            cur = []
    if cur:
        out.append(cur)
    return out


def name_of(texts: list[str]) -> tuple[str, str, str]:
    words = [respelled(CAPS_FIX.get(x, x), 'first_name', 'last_name') for x in texts]
    if len(words) == 1:
        return '', words[0], ''
    if len(words) == 2:
        return words[0], words[1], ''
    last = max(words[1:], key=lambda x: k8.known(x, 'last_name') - 3 * k8.known(x, 'first_name'))
    rest = [x for x in words if x is not last]
    return rest[0], last, ' '.join(rest[1:])


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
        if p['nick'] and p['nick'] not in man['_nicks']:
            man['_nicks'].append(p['nick'])
        if p['page'] == man['pdf_page']:
            ws = p['words']
            man['_rects'].append([round(min(w['x0'] for w in ws), 1), round(min(w['top'] for w in ws), 1),
                                  round(max(w['x1'] for w in ws), 1), round(max(w['bottom'] for w in ws), 1)])
    for s in out:
        s['additional_info'] = '; '.join([f'zvani {n}' for n in s['_nicks']] + [f"{TITLE}: {'; '.join(s['_posts'])}."])
        r = s['_rects']
        s['pdf_x'], s['pdf_y'], s['pdf_x_end'], s['pdf_y_end'] = r[0]
        if len(r) > 1:
            s['pdf_rects'] = r
        s['full_name'] = ' '.join(x for x in (s['last_name'], s['middle_name'], s['first_name']) if x)
        for k in ('_post', '_posts', '_nicks', '_rects'):
            s.pop(k)
    return out


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    if not Path(PDF).exists():
        cut_pdf()
    run_parser(pdf_path=PDF, brigade_code=58, output_path=sys.argv[1] if len(sys.argv) > 1 else UNIT,
               extract_fn=extract, entry_start_re=re.compile(r'^§§'), parse_entry_fn=parse, post_fn=men,
               id_start=10001, keep_other_sources=True)
