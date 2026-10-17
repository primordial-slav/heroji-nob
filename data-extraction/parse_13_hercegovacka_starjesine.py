"""
Parser: 13. hercegovačka NOU brigada (brigade code 100) — its officers, a second list.

Source: Mensur Seferović, "Trinaesta hercegovačka NOU brigada" (znaci.org 00001/270_7.pdf, its pp. 2-12, book pp.
        305-315, before the lists of the fallen and the fighters on the site)  →
        website/public/pdfs/13-hercegovacka-starjesine.pdf: "Starješinski sastav Trinaeste hercegovačke NOU brigade",
        the brigade staff, the units at the staff, and each battalion's staff and company commands, a name a line
        under each duty, given name first, the surname in capitals, with the days or a deputy's mark:
    Komandanti
    Danilo KOMNENOVIĆ (14. V 44 - 9. IX 44)
    Ilija KUKIĆ, zamjenik
        and the smaller units run on ("Komandiri: Marko KIJAC, Vlado BOŠKOVIĆ, politički delegat Džemil HAMZA").
A man in several posts is one record with each; his box is around his name at each post on his first post's page.
znaci re-typeset the book from its OCR: the capitals lost some carons ("IVANISEVIC", "UUAREVIĆ" for ULJAREVIĆ),
read back where the brigade's other lists or the corpus print the name so. The fallen and the fighters are the unit's
first list (IDs from 1); these get IDs from 10001.
"""
import re
import sys
from pathlib import Path

import pdfplumber

import parse_8_kordunaska_divizija as k8
from _parser_scaffold import _record, run_parser
from parse_6_vojvodjanska_stabovi import respelled
from pdf_coords import viewer_words

PDF = 'website/public/pdfs/13-hercegovacka-starjesine.pdf'
UNIT = 'website/public/13-hercegovacka-soldiers.json'
SOURCE = Path(__file__).parent / '.cache' / 'znaci_photos' / 'books' / '00001_270_7.pdf'   # znaci.org 00001/270_7.pdf
FIRST_PAGE, LAST_PAGE = 2, 12
TITLE = 'Starješinski sastav Trinaeste hercegovačke NOU brigade'
U, L = 'A-ZČĆŽŠĐ', 'a-zčćžšđ'
BATS = {'Prvi': 1, 'Drugi': 2, 'Treći': 3, 'Četvrti': 4}
DUTIES = {'komandanti': 'komandant', 'zamjenici komandanta': 'zamjenik komandanta',
          'politički komesari': 'politički komesar', 'politički komesar': 'politički komesar',
          'komesari čete': 'politički komesar', 'pomoćnici pol. komesara': 'pomoćnik političkog komesara',
          'pomoćnik pol. komesara': 'pomoćnik političkog komesara', 'pomoćnici komesara': 'pomoćnik političkog komesara',
          'zamjenici pol. kom.': 'zamjenik političkog komesara', 'načelnici štaba': 'načelnik štaba',
          'operativni oficir': 'operativni oficir', 'obavještajni oficiri': 'obavještajni oficir',
          'obaveštajni oficiri': 'obavještajni oficir', 'obavještajni oficir': 'obavještajni oficir',
          'načelnici veze': 'načelnik veze', 'intendanti': 'intendant', 'intendanti bataljona': 'intendant',
          'referent saniteta': 'referent saniteta', 'referenti saniteta': 'referent saniteta',
          'opunomoćstvo ozne': 'opunomoćenik OZN-e', 'omladinski rukovodioci': 'omladinski rukovodilac',
          'komandiri': 'komandir', 'sifrant štaba brigade': 'šifrant štaba brigade',
          'šef odsjeka naoružanja': 'šef odsjeka naoružanja', 'bataljonski biro skoja': 'član bataljonskog biroa SKOJ-a'}
# the smaller units at the brigade staff, whose men run on with their duties: the words their duties take
SMALL = {'propagandni odsjek štaba brigade': 'propagandnog odsjeka štaba brigade', 'omladinska četa': 'omladinske čete',
         'prateća četa': 'prateće čete', 'brigadna bolnica': 'brigadne bolnice', 'izviđački vod': 'izviđačkog voda',
         'odsjek za naoružanje': 'odsjeka za naoružanje'}
NAME_FIXES = {'UUAREVIĆ': 'ULJAREVIĆ', 'TRKUUA': 'TRKULJA', 'ĆORO VIC': 'ĆOROVIĆ', 'Sćepo': 'Šćepo', 'Fadie': 'Fadil',
              'KOVAĆEVIĆ': 'KOVAČEVIĆ', 'KUJAĆIĆ': 'KUJAČIĆ', 'ĆVORO': 'ČVORO', 'BARBIJERI': 'BARBIERI'}
# a deputy's or assistant's duty: "zamjenik komandira 1. čete", "pomoćnik političkog komesara"
OF_DUTY = {'politički komesar': 'političkog komesara', 'referent saniteta': 'referenta saniteta',
           'opunomoćenik OZN-e': 'opunomoćenika OZN-e', 'komandant': 'komandanta', 'komandir': 'komandira',
           'intendant': 'intendanta'}
# the parts of the brigade hospital, in the words the duty takes
PARTS = {'previjalište': 'previjališta', 'bolnički vod': 'bolničkog voda'}
POSTS: list = []


def cut_pdf() -> None:
    from pypdf import PdfReader, PdfWriter
    r, w = PdfReader(str(SOURCE)), PdfWriter()
    for i in range(FIRST_PAGE - 1, LAST_PAGE):
        w.add_page(r.pages[i])
    with open(PDF, 'wb') as f:
        w.write(f)


def rows_of(page) -> list[list[dict]]:
    rows: list = []
    for w in sorted(viewer_words(page, extra_attrs=['size']), key=lambda w: (round(w['top']), w['x0'])):
        if rows and abs(rows[-1][0]['top'] - w['top']) <= 3:
            rows[-1].append(w)
        else:
            rows.append([w])
    return [sorted(r, key=lambda w: w['x0']) for r in rows]


def blocks_of(pdf) -> list[dict]:
    """Each duty's lines (or a small unit's run-on lines), with the section they stand under."""
    out, unit, of, bat, block = [], 'Štab brigade', 'brigade', 0, None
    for n, page in enumerate(pdf.pages, 1):
        rows = [r for r in rows_of(page) if r[0]['size'] >= 8]
        names_x = min((r[0]['x0'] for r in rows if 45 < r[0]['x0'] < 100), default=60)
        for r in rows:
            t = ' '.join(w['text'] for w in r)
            if re.fullmatch(r'\d{3}', t) or n == 1 and r[0]['size'] > 10:
                continue                                                 # page numbers, the title
            if r[0]['x0'] > 100:                                         # a section, centred
                m = re.match(r'(Prvi|Drugi|Treći|Četvrti) bataljon', t)
                if m:
                    bat = BATS[m.group(1)]
                elif t == 'Pri Štabu brigade':
                    unit, of = 'Štab brigade', 'pri štabu brigade'
                elif re.match(r'[SŠ]tab (brigade|bataljona)', t):
                    unit, of = ('Štab brigade', 'brigade') if 'brigade' in t else (f'{bat}. bataljon', f'{bat}. bataljona')
                elif re.match(r'Komanda (\d)\. čete', t):
                    c = re.match(r'Komanda (\d)\. čete', t).group(1)
                    unit, of = f'{c}. četa, {bat}. bataljon', f'{c}. čete {bat}. bataljona'
                elif 'Prateć' in t:
                    unit, of = f'prateća četa, {bat}. bataljon', f'prateće čete {bat}. bataljona'
                else:
                    raise ValueError(f'section {t!r} on page {n}')
                block = None
                continue
            if r[0]['x0'] < names_x - 20:                                # a duty, or a small unit, at the left
                head = re.sub(r'\s*\d\)$', '', t).strip()                # "Bataljonski biro Skoja 2)": a footnote mark
                block = {'head': head.lower(), 'unit': unit, 'of': of, 'lines': []}
                out.append(block)
                continue
            block['lines'].append({'text': t, 'words': [{**w, 'page': n} for w in r]})
    return out


def items_of(block: dict) -> list[dict]:
    """The block's men: its lines joined (a word broken at a line's end is one), split at commas, semicolons and
    "i" outside brackets, each with the duty words before the name and the note in brackets or after a comma."""
    words: list = []
    for i, ln in enumerate(block['lines']):
        ws = [dict(w) for w in ln['words']]
        if words and words[-1]['text'].endswith('-'):
            last = words.pop()
            first = ws.pop(0)
            joined = {**first, 'text': last['text'][:-1] + first['text'], 'parts': last.get('parts', [last]) + [first]}
            ws.insert(0, joined)
        elif words and not words[-1]['text'].endswith((',', ';', ':')) and i and \
                not re.fullmatch(rf'[{U}][{U}-]+[,;]?', ws[0]['text']) and not ws[0]['text'][:1].islower():
            words[-1] = {**words[-1], 'text': words[-1]['text'] + ','}    # a name a line ("Rade" / "ĆORO VIC" runs on)
        words += ws
    text_words = []
    for w in words:
        t = w['text']
        for a, b in NAME_FIXES.items():
            if ' ' not in a:
                t = t.replace(a, b)
        text_words.append({**w, 'text': t})
    # split into items at , ; and " i ", not inside brackets
    items, cur, depth = [], [], 0
    for w in text_words:
        t = w['text']
        if t == 'i' and depth == 0:
            items.append(cur)
            cur = []
            continue
        depth += t.count('(') - t.count(')')
        cur.append(w)
        if depth == 0 and t.endswith((',', ';')):
            items.append(cur)
            cur = []
    if cur:
        items.append(cur)
    out, label = [], ''
    for it in items:
        text = ' '.join(w['text'] for w in it).rstrip(',;').strip()
        text = text.replace('ĆORO VIC', 'ĆOROVIĆ')
        if text in ('zamjenik', 'pomoćnik') and out:                     # "Ilija KUKIĆ, zamjenik"
            out[-1]['note'] = text
            continue
        m = re.match(r'^([A-ZČĆŽŠĐa-zčćžšđ ]+):\s*(.*)$', text)          # "Komandiri: Marko KIJAC", "Previjalište: politički ..."
        if m and not re.search(rf'\b[{U}]{{3,}}', m.group(1)):
            label, text = m.group(1).strip(), m.group(2)
            if ':' in text:                                              # "Previjalište: politički komesar ..."
                label, text = text.split(':', 1)[0].strip(), text.split(':', 1)[1].strip()
        m = re.match(rf'^((?:[{L}][{L}.]*\s+|-\s+)*)([{U}][{L}]+)\s+([{U}][{U}{L}-]+(?:\s+[{U}]{{2,}}[{U}-]*)?)\s*(.*)$', text)
        if not m:
            raise ValueError(f'item {text!r} in {block["head"]!r}')
        role = m.group(1).replace('-', '').strip()
        if '-' in m.group(1):                                            # "šefovi sekcija - Gašo MIJANOVIĆ (...), Mensur ..."
            label, role = role, ''
        note = m.group(4).strip(' ,')
        if note.startswith('(') and note.endswith(')'):
            note = note[1:-1]
        name_words = [w for w in it if w['text'].rstrip(',;') in m.group(2) + ' ' + m.group(3) or
                      w.get('parts') and w['text'].rstrip(',;') in m.group(3)]
        out.append({'given': m.group(2), 'last': m.group(3), 'role': role, 'label': label, 'note': note,
                    'words': [p for w in name_words for p in w.get('parts', [w])]})
    return out


def duty_of(block: dict, item: dict) -> str:
    head, of, note = block['head'], block['of'], item['note']
    if head in SMALL:                                                    # "Brigadna bolnica" / "Previjalište: politički komesar"
        where, label = SMALL[head], item['label'].lower()
        if label in PARTS:                                               # "Previjalište: politički komesar Hrvoje VIDOVIĆ"
            where, label = f'{PARTS[label]} {where}', ''
        role = item['role'] or label
        role = {'komandiri': 'komandir', 'komandiri kurira': 'komandir kurira', 'politički komesari': 'politički komesar',
                'članovi': 'član', 'sekretari': 'sekretar', 'šefovi sekcija': 'šef sekcije'}.get(role, role)
        if note == 'šef Odsjeka':
            role, note = 'šef', ''
        duty = f'{role} {where}' if role else head                       # "Odsjek za naoružanje: Čedo TASOVAC; ..."
    else:
        duty = DUTIES[head]
        if not duty.endswith(('brigade', 'SKOJ-a', 'naoružanja')) or 'biroa' in duty:
            duty = f'{duty} {of}'
    if re.match(r'^(zamjenik|pomoćnik|sekretar|šef Odsjeka)$', note):
        word = note.lower()
        if 'biroa' in duty:
            duty = duty.replace('član', word)
        elif word.startswith('šef'):
            duty = f'šef {duty.split(" ", 1)[1]}'
        else:                                                            # "zamjenik komandira 1. čete 1. bataljona"
            k = next((k for k in sorted(OF_DUTY, key=len, reverse=True) if duty.startswith(k)), None)
            duty = f'{word} {OF_DUTY[k]}{duty[len(k):]}' if k else f'{word} ({duty})'
        note = ''
    return f'{duty}, {note}' if note else duty


def read_posts(pdf_path: str) -> None:
    with pdfplumber.open(pdf_path) as pdf:
        blocks = blocks_of(pdf)
    for b in blocks:
        for it in items_of(b):
            unit = b['unit'] if b['head'] not in SMALL else 'Štab brigade'
            last = respelled(it['last'].replace(' ', '-'), 'last_name')        # "ŠUKIĆ MILIVOJEVIĆ": Šukić-Milivojević
            POSTS.append({'given': respelled(it['given'], 'first_name'), 'last': last,
                          'unit': unit, 'duty': duty_of(b, it), 'page': it['words'][0]['page'], 'words': it['words']})


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
            s['_posts'], s['_rects'] = [], []
            s['unit_detail'] = p['unit']
            out.append(s)
        if p['duty'] not in man['_posts']:
            man['_posts'].append(p['duty'])
        if p['page'] == man['pdf_page']:
            lines: list = []
            for w in p['words']:
                if w['page'] != p['page']:
                    continue
                if lines and abs(lines[-1][0]['top'] - w['top']) <= 3:
                    lines[-1].append(w)
                else:
                    lines.append([w])
            man['_rects'] += [[round(min(w['x0'] for w in ln), 1), round(min(w['top'] for w in ln), 1),
                               round(max(w['x1'] for w in ln), 1), round(max(w['bottom'] for w in ln), 1)] for ln in lines]
    for s in out:
        s['additional_info'] = f"{TITLE}: {'; '.join(s['_posts'])}."
        r = s['_rects']
        s['pdf_x'], s['pdf_y'], s['pdf_x_end'], s['pdf_y_end'] = r[0]
        if len(r) > 1:
            s['pdf_rects'] = r
        s['full_name'] = f"{s['last_name']} {s['first_name']}"
        for k in ('_post', '_posts', '_rects'):
            s.pop(k)
    return out


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    if not Path(PDF).exists():
        cut_pdf()
    run_parser(pdf_path=PDF, brigade_code=100, output_path=sys.argv[1] if len(sys.argv) > 1 else UNIT,
               extract_fn=extract, entry_start_re=re.compile(r'^§§'), parse_entry_fn=parse, post_fn=men,
               id_start=10001, keep_other_sources=True)
